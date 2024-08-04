"""
Module to benchmark pygeoops operations.
"""

from datetime import datetime
import inspect
import logging
from pathlib import Path

import geopandas as gpd

from benchmark.benchmarker import RunResult
from benchmark.benchmarks import testdata

logger = logging.getLogger(__name__)


def _get_package() -> str:
    return "alternatives"


def _get_version() -> str:
    return 1.0


def collection_extract(tmp_dir: Path) -> RunResult:
    # Init
    function_name = inspect.currentframe().f_code.co_name  # type: ignore[union-attr]
    input_path = testdata.TestFile.AGRIPRC_2018.get_file(tmp_dir)
    geoms_gdf = gpd.read_file(input_path, engine="pyogrio")

    # Go!
    start_time = datetime.now()
    # This is a (private) implementation in geopandas
    geoms_gdf = _collection_extract(geoms_gdf, geom_type="Polygon")
    operation_descr = f"{function_name} on agri parcel layer BEFL (~500k polygons)"
    result = RunResult(
        package=_get_package(),
        package_version=_get_version(),
        operation=function_name,
        secs_taken=(datetime.now() - start_time).total_seconds(),
        operation_descr=operation_descr,
        run_details=None,
    )

    # geoms_gdf.to_file(tmp_dir / f"{function_name}_output.gpkg", engine="pyogrio")

    # Cleanup and return
    return result


def _collection_extract(df, geom_type):
    # Check input
    if geom_type in ["Polygon", "MultiPolygon"]:
        geom_types = ["Polygon", "MultiPolygon"]
    elif geom_type in ["LineString", "MultiLineString", "LinearRing"]:
        geom_types = ["LineString", "MultiLineString", "LinearRing"]
    elif geom_type in ["Point", "MultiPoint"]:
        geom_types = ["Point", "MultiPoint"]
    else:
        raise TypeError(f"`geom_type` does not support {geom_type}.")

    result = df.copy()

    # First we filter the geometry types inside GeometryCollections objects
    # (e.g. GeometryCollection([polygon, point]) -> polygon)
    # we do this separately on only the relevant rows, as this is an expensive
    # operation (an expensive no-op for geometry types other than collections)
    is_collection = result.geom_type == "GeometryCollection"
    if is_collection.any():
        geom_col = result._geometry_column_name
        collections = result[[geom_col]][is_collection]

        exploded = collections.reset_index(drop=True).explode(index_parts=True)
        exploded = exploded.reset_index(level=0)

        exploded.loc[~exploded.geom_type.isin(geom_types), geom_col] = None

        # level_0 created with above reset_index operation
        # and represents the original geometry collections
        # TODO avoiding dissolve to call union_all in this case could further
        # improve performance (we only need to collect geometries in their
        # respective Multi version)
        dissolved = exploded.dissolve(by="level_0")
        result.loc[is_collection, geom_col] = dissolved[geom_col].values

    # Now we filter all geometries (in theory we don't need to do this
    # again for the rows handled above for GeometryCollections, but filtering
    # them out is probably more expensive as simply including them when this
    # is typically about only a few rows)
    result = result.loc[result.geom_type.isin(geom_types)]

    return result
