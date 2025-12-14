.. currentmodule:: pygeoops

User guide
==========

PyGeoOps provides some less common or extended spatial algorithms and utility functions.

A full list of functionalities can be found in the 
:ref:`API reference<api-reference>`. 

As a quick start, here are some examples on how PyGeoOps can be used.

Determine the :meth:`~centerline` for polygons
----------------------------------------------

.. code-block:: python

    # For a single polygon
    wkt = "POLYGON ((0 0, 0 8, -2 10, 4 10, 2 8, 2 2, 10 2, 10 0, 0 0))"
    polygon = shapely.from_wkt(wkt)
    centerline = pygeoops.centerline(polygon)

    # For a Geopandas dataframe with polygons
    gdf = gpd.GeoDataFrame(geometry=[polygon])
    centerlines_gdf = gdf.copy()
    centerlines_gdf.geometry = pygeoops.centerline(gdf.geometry)

.. plot:: code/centerline_basic.py


Calculate a variable width buffer with :meth:`~buffer_by_m`
-----------------------------------------------------------

Calculates a buffer where the width at each vertex is determined by the Z or M dimension
of the geometry. If an M dimension is present, it is used. Otherwise, the Z dimension is
used.

.. code-block:: python

    # For a line with the Z dimension already included
    line = shapely.LineString([[0, 6, 1], [0, 0, 2], [10, 0, 2], [13, 5, 4]])
    buffer_geom = pygeoops.buffer_by_m(line)

    # If the distances are separately available, they can be added like this
    line = shapely.LineString([[0, 6], [0, 0], [10, 0], [13, 5]])
    distances = [1, 2, 2, 4]
    line_with_m = shapely.LineString(
        [[x, y, m] for (x, y), m in zip(line.coords, distances)]
    )
    buffer_geom = pygeoops.buffer_by_m(line_with_m)


.. plot:: code/buffer_by_m_different_cases.py


Determine :meth:`~view_angles` from a viewpoint towards polygons
----------------------------------------------------------------

.. code-block:: python
    
    viewpoint = shapely.Point(10, 20)
    polygons = [
        shapely.from_wkt("POLYGON((1 0, 1 1, 2 1, 2 0, 1 0))"),
        shapely.from_wkt("POLYGON((-1 0, -1 1, -2 1, -2 0, -1 0))")
    ]
    visible_geoms_gdf = geopandas.GeoDataFrame(geometry=polygons)
    )
    angles_df = pandas.DataFrame(
        pygeoops.view_angles(viewpoint, visible_geoms_gdf.geometry.values),
        columns=["angle_start", "angle_end"],
        index=visible_geoms_gdf.index,
    )
