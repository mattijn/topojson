import geopandas
import pytest
import shapely
from shapely import geometry

import topojson
from topojson.ops import delta_decoding, delta_encoding


def natural_earth():
    return geopandas.read_file("tests/files_shapefile/static_natural_earth.gpkg")[
        ["NAME", "geometry"]
    ]


def assert_same_topology(result, reference):
    """Same geometry per feature and the same set of arcs (independent of order,
    direction and ring start)."""
    gdf_res = result.to_gdf().sort_index()
    gdf_ref = reference.to_gdf().sort_index()
    assert gdf_res.index.tolist() == gdf_ref.index.tolist()
    for a, b in zip(gdf_res.geometry, gdf_ref.geometry):
        assert shapely.normalize(a).equals_exact(shapely.normalize(b), 0)

    def arc_set(topo):
        return {
            shapely.normalize(geometry.LineString(c)).wkb
            for c in delta_decoding(topo.output["arcs"])
        }

    assert arc_set(result) == arc_set(reference)


def test_ops_delta_decoding_encoding_roundtrip():
    arcs = topojson.Topology(natural_earth()).output["arcs"]
    assert delta_encoding(delta_decoding(arcs)) == arcs


@pytest.mark.parametrize(
    "path, ids",
    [
        ("tests/files_shapefile/static_natural_earth.gpkg", [3, 50, 120]),
        ("tests/files_geojson/mesh2d.geojson", list(range(300, 340))),
    ],
)
def test_incremental_remove_equals_full_build(path, ids):
    data = geopandas.read_file(path)
    topo = topojson.Topology(data)
    transform = topo.output["transform"]
    topo.remove(ids)
    reference = topojson.Topology(data.drop(index=ids), prequantize=transform)
    assert_same_topology(topo, reference)


@pytest.mark.parametrize(
    "path, ids",
    [
        ("tests/files_shapefile/static_natural_earth.gpkg", [3, 50, 120]),
        ("tests/files_geojson/mesh2d.geojson", list(range(300, 340))),
    ],
)
def test_incremental_add_equals_full_build(path, ids):
    data = geopandas.read_file(path)
    topo = topojson.Topology(data.drop(index=ids))
    transform = topo.output["transform"]
    topo.add(data.loc[ids])
    reference = topojson.Topology(data, prequantize=transform)
    assert_same_topology(topo, reference)
    assert topo.output["bbox"] == pytest.approx(reference.output["bbox"])


def test_incremental_add_and_remove_lines():
    data = geopandas.read_file("tests/files_shapefile/rivers.gpkg", layer="rivers")
    data = data.iloc[:120]
    ids = [5, 17, 60]
    topo = topojson.Topology(data.drop(index=ids))
    transform = topo.output["transform"]
    assert_same_topology(
        topo.add(data.loc[ids]), topojson.Topology(data, prequantize=transform)
    )
    assert_same_topology(
        topo.remove([5, 17]),
        topojson.Topology(data.drop(index=[5, 17]), prequantize=transform),
    )


def test_incremental_add_and_remove_points():
    data = geopandas.GeoDataFrame(
        {"name": ["a", "b", "c"]},
        geometry=[
            geometry.Polygon([(0, 0), (2, 0), (2, 2), (0, 2)]),
            geometry.Point(1, 1),
            geometry.MultiPoint([(3, 3), (4, 4)]),
        ],
    )
    topo = topojson.Topology(data.iloc[:1])
    topo.add(data.iloc[1:])
    assert (
        topo.to_dict()["objects"]["data"]["geometries"][2]["coordinates"]
        == (
            topojson.Topology(data, prequantize=topo.output["transform"]).to_dict()[
                "objects"
            ]["data"]["geometries"][2]["coordinates"]
        )
    )
    topo.remove([1])
    gdf = topo.to_gdf()
    assert gdf.index.tolist() == [0, 2]
    assert len(topo.output["coordinates"]) == 2


def test_incremental_sync_with_state_file(tmp_path):
    data = natural_earth()
    first = data.iloc[:150]
    topo = topojson.Topology(first)
    transform = topo.output["transform"]
    topo.to_json(tmp_path / "state.json", state=True)

    # next run: some features gone, some new, one changed
    second = data.iloc[5:160].copy()
    second.loc[10, "geometry"] = second.loc[10, "geometry"].buffer(0.5)
    topo = topojson.Topology.read_json(tmp_path / "state.json")
    topo.sync(second)

    assert topo.last_sync == {"added": 10, "removed": 5, "changed": 1, "unchanged": 144}
    assert topo.options.prequantize is True
    assert_same_topology(topo, topojson.Topology(second, prequantize=transform))


def test_incremental_state_is_plain_topojson():
    topo = topojson.Topology(natural_earth())
    state = topo.to_dict(state=True)
    assert {"options", "source_hashes"} <= set(state)
    assert "source_hashes" not in topo.to_dict(options=True)
    # still a valid TopoJSON for the library
    assert len(topojson.Topology(state).output["arcs"]) == len(topo.output["arcs"])


def test_incremental_errors(tmp_path):
    data = natural_earth()
    topo = topojson.Topology(data.iloc[:10])
    with pytest.raises(ValueError, match="already in the topology"):
        topo.add(data.iloc[5:15])
    with pytest.raises(KeyError, match="not in the topology"):
        topo.remove([100])

    # without state, sync cannot know what changed
    topo.to_json(tmp_path / "plain.json")
    with pytest.raises(ValueError, match="state=True"):
        topojson.Topology.read_json(tmp_path / "plain.json").sync(data.iloc[:10])

    with pytest.raises(NotImplementedError, match="shared_coords"):
        topojson.Topology(data.iloc[:10], shared_coords=True).remove([0])
    with pytest.raises(NotImplementedError, match="unsimplified"):
        topojson.Topology(data.iloc[:10]).toposimplify(1, inplace=False).remove([0])
    with pytest.raises(ValueError, match="quantized"):
        topojson.Topology(data.iloc[:10], prequantize=False).remove([0])


def test_incremental_toposimplify_option_is_recorded():
    data = natural_earth()
    assert topojson.Topology(data, toposimplify=True).options.toposimplify is True
    topo = topojson.Topology(data)
    topo.toposimplify(1, inplace=True)
    assert topo.options.toposimplify == 1


def test_incremental_add_and_remove_geometrycollection():
    data = natural_earth()
    line = geometry.LineString([(-9, 0), (9, 3)])
    gcs = geopandas.GeoDataFrame(
        {"NAME": ["gc", "nested"]},
        geometry=[
            geometry.GeometryCollection(
                [
                    data.geometry[3].buffer(1),
                    geometry.LineString([(0, 0), (30, 30)]),
                    geometry.Point(5, 5),
                ]
            ),
            geometry.GeometryCollection(
                [
                    geometry.MultiPoint([(7, 7), (6, 6)]),
                    geometry.GeometryCollection([line]),
                ]
            ),
        ],
        index=[900, 901],
        crs=data.crs,
    )
    full = geopandas.pd.concat([data, gcs])
    topo = topojson.Topology(data)
    transform = topo.output["transform"]
    assert_same_topology(topo.add(gcs), topojson.Topology(full, prequantize=transform))
    assert_same_topology(
        topo.remove([900, 3]),
        topojson.Topology(full.drop(index=[900, 3]), prequantize=transform),
    )
