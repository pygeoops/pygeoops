import shapely
from packaging import version


GEOS_GTE_3_12_0 = version.parse(shapely.geos_version_string) >= version.parse("3.12.0")

SHAPELY_GTE_2_1_0 = version.parse(shapely.__version__) >= version.parse("2.1.0")
