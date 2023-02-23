.. currentmodule:: pygeoops

User guide
==========

PyGeoOps provides some more exotic spatial algorithms that are not available in shapely.

A full list of operations can be found in the 
:ref:`API reference<API-reference>`. 

This is how eg. a centerline can be determined for a polygon:

.. code-block:: python

    import pygeoops
    import shapely

    polygon = shapely.from_wkt("POLYGON ((0 0, 0 10, 2 10, 2 2, 10 2, 10 0, 0 0))")
    centerline = pygeoops.centerline(polygon)
