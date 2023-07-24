# CHANGELOG

## 0.2.0 (???)

### Improvements

- Copy/move geometry utility functions from geofileops to pygeoops (#20)
  - extended `simplify` function (support for different algorithmns, exclude points from removal)
  - grid utility functions: `create_grid`, `split_tiles`
  - general geometry utility functions: `collect`, `collection_extract`, `explode`, `remove_inner_rings`
- Copy/move topologic simplify (preserve common boundaries) from geofilops to pygeoops (#24)
- Add support for `GeoSeries` as input and output for functions where this is appropriate (#26)
- Return results in pygeoops as `NDArray[BaseGeometry]` instead of list[BaseGeometry]` like shapely2 does (#25)
- Use ruff as linter instead of flake8 (#22) 

### Deprecations and compatibility notes

- results are now returned as `NDArray[BaseGeometry]` instead of `list[BaseGeometry]` like shapely2 does (#25)
- for the the `create_grid` functions (#28):
    - they now return `NDArray[BaseGeometry]` instead of `GeoDataFrame`
    - the `crs` parameter has been removed

## 0.1.1 (2023-04-12)

### Improvements

- Cleaner result for polygons ending in rectangular shapes (#16)

## 0.1.0 (2023-03-01)

First version. The following spatial operations are available:

- centerline: calculates the approximate centerline for a polygon (#1)
- view_angles: calculates the angles where a geometry can be seen from a viewpoint (#7, #9)
