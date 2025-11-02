.. pygeoops documentation master file, created by
   sphinx-quickstart on Thu Nov  5 20:17:22 2020.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. currentmodule:: pygeoops

PyGeoOps |version|
====================

PyGeoOps provides some less common or extended spatial algorithms and utility functions.

Examples are:

* :meth:`~simplify` with some advanced extra options:

  * choice in simplification algorithms: Lang (+ a variant), Ramer Douglas Peuker, Visvalingal Whyatt
  * specify points/locations where points should not be removed by the simplification
  * topologic simplification: common boundaries between input features should stay common

* :meth:`~centerline` (medialaxis) calculation for polygons
* :meth:`~buffer_by_m` to calculate a variable width buffer for geometries
* :meth:`~view_angles` to calculate the angles a polygon is visible in from a certain
  view point
* utility functions to create and split grids
  (:meth:`~create_grid`, :meth:`~split_tiles`)
* general utility functions on geometries like :meth:`~remove_inner_rings`,
  :meth:`~get_parts_recursive`,...


.. toctree::
   :maxdepth: 1

   Home <self>
   Installation <installation>
   User guide <user_guide>
   API reference <reference>
   Development <development>