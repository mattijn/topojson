import pytest
import shapely

import topojson as tp

pl = pytest.importorskip("polars")


def squares(srid=0):
    """Two squares that share a side, as WKB (with an SRID, EWKB, as polars-st)."""
    geoms = shapely.set_srid([shapely.box(0, 0, 1, 1), shapely.box(1, 0, 2, 1)], srid)
    return pl.Series("geometry", shapely.to_wkb(geoms, include_srid=bool(srid)))


# a DataFrame with a geometry column of WKB: the shared side is one arc, the other
# columns are the properties
def test_polars_dataframe():
    frame = pl.DataFrame({"name": ["abc", "def"]}).with_columns(squares())
    topo = tp.Topology(frame, prequantize=False).to_dict()
    geometries = topo["objects"]["data"]["geometries"]

    assert len(topo["arcs"]) == 3
    assert [g["properties"] for g in geometries] == [{"name": "abc"}, {"name": "def"}]


# the same topology as from a GeoDataFrame
def test_polars_dataframe_as_geodataframe():
    geopandas = pytest.importorskip("geopandas")
    frame = pl.DataFrame({"name": ["abc", "def"]}).with_columns(squares())
    gdf = geopandas.GeoDataFrame(
        {"name": ["abc", "def"]}, geometry=shapely.from_wkb(squares().to_numpy())
    )

    assert tp.Topology(frame).to_dict() == tp.Topology(gdf).to_dict()


# a Series of WKB, and a frame of only the geometries
def test_polars_series_and_geometry_only():
    for data in [squares(), squares().to_frame()]:
        topo = tp.Topology(data, prequantize=False).to_dict()

        assert len(topo["arcs"]) == 3
        assert len(topo["objects"]["data"]["geometries"]) == 2


# the SRID of EWKB becomes the CRS, also of to_gdf
def test_polars_srid_as_crs():
    pytest.importorskip("geopandas")
    topo = tp.Topology(squares(srid=28992).to_frame())

    assert topo.to_gdf().crs.to_epsg() == 28992


# a list of DataFrames, each an object of its own
def test_polars_list_of_dataframes():
    frame = pl.DataFrame({"name": ["abc", "def"]}).with_columns(squares())
    topo = tp.Topology(
        [frame[:1], frame[1:]], object_name=["left", "right"], prequantize=False
    ).to_dict()

    assert list(topo["objects"]) == ["left", "right"]
    assert len(topo["arcs"]) == 3


# without a column of WKB the error says what is needed
def test_polars_without_geometry():
    with pytest.raises(ValueError, match="WKB"):
        tp.Topology(pl.DataFrame({"name": ["abc"]}))
