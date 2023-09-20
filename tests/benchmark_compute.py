import fire
import json
from time import process_time
from pathlib import Path
import geopandas
import topojson


def time_topology(data):
    t_start = process_time()
    _ = topojson.Topology(data)
    t_stop = process_time()
    return t_stop - t_start


def time_version(version):
    """
    The following list contain files are being timed. The files filed should be able to
    open by geopandas.read_file(). The characteristic of each file is as follow:
    - nybb: a few detailed long linestrings
    - naturalearth_lowres: similar alike linestrings, not too long
    - mesh2d: many very short linestrings
    """
    files_to_time = [
        "tests/files_shapefile/static_nybb.gpkg",
        "tests/files_shapefile/static_natural_earth.gpkg",
        "tests/files_geojson/mesh2d.geojson",
    ]

    # apply 3x timing to each file and collect result in list
    list_times = []
    for file_to_time in files_to_time:
        gdf_data = geopandas.read_file(file_to_time)
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
