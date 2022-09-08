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
    
    files_to_time = [
        geopandas.datasets.get_path("nybb"),
        geopandas.datasets.get_path("naturalearth_lowres"),
        #'tests/files_geojson/sample.geojson',
        'tests/files_geojson/mesh2d.geojson'
    ]
    
    list_times = []
    for file_to_time in files_to_time:
        gdf_data = geopandas.read_file(file_to_time)
        for _ in range(3):
            time_of_file = time_topology(gdf_data)
            list_times.append({'file': Path(file_to_time).stem, 'time': time_of_file, 'version':version})  

    with open(f'tests/timings_{version}.json', 'w') as f:
        json.dump(list_times, f)

if __name__ == '__main__':
    print(topojson.__version__)

    fire.Fire(time_version)