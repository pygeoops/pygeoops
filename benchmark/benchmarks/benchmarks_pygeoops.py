"""Module to benchmark pygeoops operations."""

import inspect
import logging
import os
from datetime import datetime
from pathlib import Path

os.environ["USE_PYGEOS"] = "0"
import geopandas as gpd
import shapely

import pygeoops
from benchmark.benchmarker import RunResult
from benchmark.benchmarks import testdata

logger = logging.getLogger(__name__)
nb_rows_simplify = 50000


def _get_package() -> str:
    return "pygeoops"


def _get_version() -> str:
    return pygeoops.__version__


def simplify_lang(tmp_dir: Path) -> RunResult:
    """Simplify geometries using Lang algorithm with pygeoops."""
    # Init
    function_name = inspect.currentframe().f_code.co_name  # type: ignore[union-attr]
    input_path = testdata.TestFile.AGRIPRC_2018.get_file(tmp_dir)
    geoms_gdf = gpd.read_file(input_path, rows=nb_rows_simplify, engine="pyogrio")
    input_filtered_path = tmp_dir / f"input_{nb_rows_simplify}rows.gpkg"
    if not input_filtered_path.exists():
        geoms_gdf.to_file(input_filtered_path, engine="pyogrio")

    # Go!
    start_time = datetime.now()
    geoms_gdf.geometry = pygeoops.simplify(
        geometry=geoms_gdf.geometry, tolerance=1, algorithm="lang"
    )
    operation_descr = (
        f"{function_name} on agri parcel layer BEFL (~{nb_rows_simplify} polygons)"
    )
    result = RunResult(
        package=_get_package(),
        package_version=_get_version(),
        operation=function_name,
        secs_taken=(datetime.now() - start_time).total_seconds(),
        operation_descr=operation_descr,
        run_details=None,
    )

    geoms_gdf.to_file(tmp_dir / f"{function_name}_output.gpkg")

    # Cleanup and return
    return result


def simplify_lang_plus(tmp_dir: Path) -> RunResult:
    """Simplify geometries using Lang+ algorithm with pygeoops."""
    # Init
    function_name = inspect.currentframe().f_code.co_name  # type: ignore[union-attr]
    input_path = testdata.TestFile.AGRIPRC_2018.get_file(tmp_dir)
    geoms_gdf = gpd.read_file(input_path, rows=nb_rows_simplify, engine="pyogrio")
    input_filtered_path = tmp_dir / f"input_{nb_rows_simplify}rows.gpkg"
    if not input_filtered_path.exists():
        geoms_gdf.to_file(input_filtered_path, engine="pyogrio")

    # Go!
    start_time = datetime.now()
    geoms_gdf.geometry = pygeoops.simplify(
        geometry=geoms_gdf.geometry, tolerance=1, algorithm="lang+"
    )
    operation_descr = (
        f"{function_name} on agri parcel layer BEFL (~{nb_rows_simplify} polygons)"
    )
    result = RunResult(
        package=_get_package(),
        package_version=_get_version(),
        operation=function_name,
        secs_taken=(datetime.now() - start_time).total_seconds(),
        operation_descr=operation_descr,
        run_details=None,
    )

    geoms_gdf.to_file(tmp_dir / f"{function_name}_output.gpkg")

    # Cleanup and return
    return result


def simplify_rdp(tmp_dir: Path) -> RunResult:
    """Simplify geometries using RDP algorithm with pygeoops."""
    # Init
    function_name = inspect.currentframe().f_code.co_name  # type: ignore[union-attr]
    input_path = testdata.TestFile.AGRIPRC_2018.get_file(tmp_dir)
    geoms_gdf = gpd.read_file(input_path, rows=nb_rows_simplify, engine="pyogrio")
    input_filtered_path = tmp_dir / f"input_{nb_rows_simplify}rows.gpkg"
    if not input_filtered_path.exists():
        geoms_gdf.to_file(input_filtered_path, engine="pyogrio")

    # Go!
    start_time = datetime.now()
    geoms_gdf.geometry = pygeoops.simplify(
        geometry=geoms_gdf.geometry, tolerance=1, algorithm="rdp"
    )
    operation_descr = (
        f"{function_name} on agri parcel layer BEFL (~{nb_rows_simplify} polygons)"
    )
    result = RunResult(
        package=_get_package(),
        package_version=_get_version(),
        operation=function_name,
        secs_taken=(datetime.now() - start_time).total_seconds(),
        operation_descr=operation_descr,
        run_details=None,
    )

    geoms_gdf.to_file(tmp_dir / f"{function_name}_output.gpkg")

    # Cleanup and return
    return result


def simplify_rdp_keep_points_on(tmp_dir: Path) -> RunResult:
    """Simplify geometries using RDP algorithm with keep_points_on."""
    # Init
    function_name = inspect.currentframe().f_code.co_name  # type: ignore[union-attr]
    input_path = testdata.TestFile.AGRIPRC_2018.get_file(tmp_dir)
    geoms_gdf = gpd.read_file(input_path, rows=nb_rows_simplify, engine="pyogrio")
    input_filtered_path = tmp_dir / f"input_{nb_rows_simplify}rows.gpkg"
    if not input_filtered_path.exists():
        geoms_gdf.to_file(input_filtered_path, engine="pyogrio")

    keep_points_on = shapely.LineString(
        [
            (150000, 150000),
            (150000, 200000),
            (200000, 200000),
            (200000, 150000),
            (150000, 150000),
        ]
    )

    # Go!
    start_time = datetime.now()
    geoms_gdf.geometry = pygeoops.simplify(
        geometry=geoms_gdf.geometry,
        tolerance=1,
        algorithm="rdp",
        keep_points_on=keep_points_on,
    )
    operation_descr = (
        f"{function_name} on agri parcel layer BEFL (~{nb_rows_simplify} polygons)"
    )
    result = RunResult(
        package=_get_package(),
        package_version=_get_version(),
        operation=function_name,
        secs_taken=(datetime.now() - start_time).total_seconds(),
        operation_descr=operation_descr,
        run_details=None,
    )

    geoms_gdf.to_file(tmp_dir / f"{function_name}_output.gpkg")

    # Cleanup and return
    return result


def simplify_rdp_geopandas(tmp_dir: Path) -> RunResult:
    """Simplify geometries using RDP algorithm with GeoPandas."""
    # Init
    function_name = inspect.currentframe().f_code.co_name  # type: ignore[union-attr]
    input_path = testdata.TestFile.AGRIPRC_2018.get_file(tmp_dir)
    geoms_gdf = gpd.read_file(input_path, rows=nb_rows_simplify, engine="pyogrio")
    input_filtered_path = tmp_dir / f"input_{nb_rows_simplify}rows.gpkg"
    if not input_filtered_path.exists():
        geoms_gdf.to_file(input_filtered_path, engine="pyogrio")

    # Go!
    start_time = datetime.now()
    geoms_gdf.geometry = geoms_gdf.geometry.simplify(tolerance=1)
    operation_descr = (
        f"{function_name} on agri parcel layer BEFL (~{nb_rows_simplify} polygons)"
    )
    result = RunResult(
        package=_get_package(),
        package_version=_get_version(),
        operation=function_name,
        secs_taken=(datetime.now() - start_time).total_seconds(),
        operation_descr=operation_descr,
        run_details=None,
    )

    geoms_gdf.to_file(tmp_dir / f"{function_name}_output.gpkg")

    # Cleanup and return
    return result
