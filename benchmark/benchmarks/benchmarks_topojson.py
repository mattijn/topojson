# -*- coding: utf-8 -*-
"""
Module to benchmark topojson operations.
"""

from datetime import datetime
import logging
from pathlib import Path

import geopandas as gpd

from benchmarker import RunResult
import topojson

################################################################################
# Some init
################################################################################

logger = logging.getLogger(__name__)

################################################################################
# The real work
################################################################################


def _get_package() -> str:
    return "topojson"


def _get_version() -> str:
    return topojson.__version__


def _get_testdata_dir() -> Path:
    return Path(__file__).resolve().parent / "testdata"


def topology_belgium_regions(tmp_dir: Path) -> RunResult:
    # Init
    input_path = _get_testdata_dir() / "belgium_regions.gpkg"
    input_gdf = gpd.read_file(input_path)

    # Go!
    start_time = datetime.now()
    topo = topojson.Topology(input_gdf, prequantize=False, shared_coords=False)
    nb_arcs = len(topo.output["arcs"])
    print(f"nb_arcs: {nb_arcs}")

    result = RunResult(
        package=_get_package(),
        package_version=_get_version(),
        operation="topology_belgium_regions",
        secs_taken=(datetime.now() - start_time).total_seconds(),
        operation_descr=(
            "topology for detailed regions of Belgium (3 polygons, max 30.000 points)"
        ),
        run_details={"shared_coords": False, "nb_arcs": nb_arcs},
    )

    # Return
    return result


def topology_topomap_segmentation(tmp_dir: Path) -> RunResult:
    # Init
    input_path = _get_testdata_dir() / "topo1778-ferraris_05.gpkg"
    input_gdf = gpd.read_file(input_path)

    # Go!
    start_time = datetime.now()
    topo = topojson.Topology(input_gdf, prequantize=False, shared_coords=False)
    nb_arcs = len(topo.output["arcs"])
    print(f"nb_arcs: {nb_arcs}")

    result = RunResult(
        package=_get_package(),
        package_version=_get_version(),
        operation="topomap_segmentation",
        secs_taken=(datetime.now() - start_time).total_seconds(),
        operation_descr="topology for the raw result of segmentation of a topo map",
        run_details={"shared_coords": False, "nb_arcs": nb_arcs},
    )

    # Return
    return result


def topology_agriparcels_16000(tmp_dir: Path) -> RunResult:
    # Init
    input_path = _get_testdata_dir() / "lbprc_2022_16000.gpkg"
    input_gdf = gpd.read_file(input_path).head(20000)

    # Go!
    start_time = datetime.now()
    topo = topojson.Topology(input_gdf, prequantize=False, shared_coords=False)
    nb_arcs = len(topo.output["arcs"])
    print(f"nb_arcs: {nb_arcs}")

    result = RunResult(
        package=_get_package(),
        package_version=_get_version(),
        operation="agriparcels",
        secs_taken=(datetime.now() - start_time).total_seconds(),
        operation_descr="topology for agricultural parcels (16.000)",
        run_details={"shared_coords": False, "nb_arcs": nb_arcs},
    )

    # Return
    return result
