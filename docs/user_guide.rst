.. currentmodule:: pygeoops

User guide
==========

The main objective of pygeoops is to provide extra spatial algorithms that are not
available in shapely.

A full list of operations can be found in the 
:ref:`API reference<API-reference>`. 

This is how eg. a centerline can be determined for a geometry:

.. code-block:: python

    import pygeoops
    
    centerline = pygeoops.centerline(geometry='...')
