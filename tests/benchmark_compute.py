import json
from pathlib import Path
from time import process_time

import fire
import geopandas

import topojson

# The files differ in what drives the computation time: the number of lines, their
# length, how many lines share paths and how many vertices there are in total. A
# change can speed up one kind of input and slow down another, so each kind is timed.
# Counts are of the extracted lines (rings and linestrings) before quantization.
FILES_TO_TIME = {
    # Boroughs of New York: 5 multipolygons, 106 rings with 76k vertices, the longest
    # ring 16k vertices. Few pairs of lines (173) and few junctions (60): time goes to
    # work along long lines, such as cutting and comparing long rings.
    "tests/files_shapefile/static_nybb.gpkg": {},
    # Countries of the world: 177 (multi)polygons, 289 rings of ~20 vertices (10k in
    # total) with shared borders (321 junctions). A mix of pairwise and per vertex work.
    "tests/files_shapefile/static_natural_earth.gpkg": {},
    # A mesh of 2202 cells of 5 vertices, all borders shared: 10k pairs of lines, 1.9k
    # junctions and 4k arcs for only 10k vertices. Time goes to the overhead per line
    # and per pair.
    "tests/files_geojson/mesh2d.geojson": {},
    # Rivers of the world: 364 open linestrings with 104k vertices (median 122 per
    # line) that hardly share a path (no or a few junctions, depending on the grid).
    # Little topology to find, so time goes to handling the vertices.
    "tests/files_shapefile/rivers.gpkg": {"layer": "rivers"},
    # A tessellation of 3826 cells around buildings with 824k vertices (median 187 per
    # ring), all borders shared: 13k pairs of lines, 7k junctions and 11k arcs. Large in
    # both the number of pairs and the number of vertices.
    "tests/files_geojson/sample.geojson": {},
}


def time_topology(data):
    t_start = process_time()
    _ = topojson.Topology(data)
    t_stop = process_time()
    return t_stop - t_start


def time_version(version):
    # log which topojson is imported, to verify the intended version is benchmarked
    print(
        f"benchmarking {version}: topojson {topojson.__version__} "
        f"from {topojson.__file__}"
    )

    # apply 3x timing to each file and collect result in list
    list_times = []
    for file_to_time, read_options in FILES_TO_TIME.items():
        gdf_data = geopandas.read_file(file_to_time, **read_options)
        for _ in range(3):
            time_of_file = time_topology(gdf_data)
            list_times.append(
                {
                    "file": Path(file_to_time).stem,
                    "time": time_of_file,
                    "version": version,
                }
            )

    # save timings within test folder, these files will not be kept, but only used to
    # create a visualization in benchmark_visz.py
    with open(f"tests/timings_{version}.json", "w") as f:
        json.dump(list_times, f)


if __name__ == "__main__":
    fire.Fire(time_version)
