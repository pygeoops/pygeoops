# -*- coding: utf-8 -*-
"""
Tests for functionalities in vector_util, regarding geometry operations.
"""

import geopandas as gpd
import shapely

import pygeoops


def test_geopandas():
    # Prepare test data
    test_gdf = gpd.GeoDataFrame(
        data=[
            {
                "uidn": 1,
                "geometry": shapely.Polygon(
                    shell=[(0, 0), (0, 10), (1, 10), (10, 10), (10, 0), (0, 0)],
                    holes=[[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
                ),
            },
            {
                "uidn": 2,
                "geometry": shapely.Polygon(
                    shell=[(0, 0), (0, 10), (1, 10), (10, 10), (10, 0), (0, 0)],
                    holes=[[(2, 2), (2, 8), (8, 8), (8, 2), (2, 2)]],
                ),
            },
        ],
        crs=31370,
    )

    simplified_gdf = test_gdf.copy()
    simplified_gdf.geometry = pygeoops.simplify(
        test_gdf.geometry.array, tolerance=1, algorithm="lang"
    )
    assert len(simplified_gdf) == len(test_gdf)
    for idx in range(len(simplified_gdf)):
        assert isinstance(simplified_gdf.geometry.iloc[idx], shapely.Polygon)
        assert len(simplified_gdf.geometry.iloc[idx].exterior.coords) < len(
            test_gdf.geometry.iloc[idx].exterior.coords
        )
        assert len(simplified_gdf.geometry.iloc[idx].interiors[0].coords) == len(
            test_gdf.geometry.iloc[idx].interiors[0].coords
        )
