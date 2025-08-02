# CHANGELOG

## 0.5.1 (????-??-??)

### Bugs fixed

- Fix errors in `centerline` for some specific polygons (#132)

## 0.5.0 (2025-03-30)

### Improvements

- Add functions `extend_line_by_distance` and `extend_line_to_geometry`
  (#83, #89)
- Add option to function `centerline` to extend it to the polygon boundary (#87)
- Improve logging of geos warnings in `difference_all` (#77)
- Add more context to errors raised by `centerline` (#116)
- Change minimal python version to 3.10 (#121)
- Use ruff instead of black for formatting + use mypy (#78)
- Enable extra linter checks like pydocstyle and pyupgrade (#85)

### Bugs fixed

- Fix `centerline` error for very narrow polygons (#117)
- Fix `centerline` error for polygons that have points very close together (#127)

## 0.4.0 (2023-10-31)

### Improvements

- Add support to extract different primitive types per geometry in `extract_collection` (#57)
- Add `make_valid` with `keep_collapsed` parameter (#58)
- Add support for Z/M dimensions geometries in `GeometryType` (#63)
- Add support for 0 dim ndarray input (#60)
- Improve performance of `difference_all` and `difference_all_tiled` (#67)

### Bugs fixed

 - Fix `collection_extract` and `collect` creating invalid multipolygons in some cases (#65)

## 0.3.0 (2023-09-07)

### Improvements

- Add functions `difference_all`, `difference_all_tiled` and `empty` (#42, #43, #52)
- Add function `get_primitivetype_id` (#43)
- Add function `subdivide` (#49)
- Use `simplify` of `shapely` when possible as it is faster (#44)

## 0.2.0 (2023-07-27)

### Improvements

- Copy/move geometry utility functions from geofileops to pygeoops (#20)
  - extended `simplify` function (support for different algorithmns, exclude
    points/locations from removal by the simplification)
  - grid utility functions: `create_grid`, `split_tiles`
  - general geometry utility functions: `collect`, `collection_extract`, `explode`,
    `remove_inner_rings`
- Copy/move topologic simplify (preserve common boundaries) from geofilops to pygeoops
  (#24)
- Add alternative to LANG algorithm ("lang2") that avoids the (large) minimum retained
  points in output (#30)
- Add support for `GeoSeries` as input and output for functions where this is
  appropriate (#26)
- Return results in pygeoops as `NDArray[BaseGeometry]` instead of list[BaseGeometry]`
  like shapely2 does (#25)
- Use ruff as linter instead of flake8 (#22) 

### Deprecations and compatibility notes

- Results are now returned as `NDArray[BaseGeometry]` instead of `list[BaseGeometry]`
  like shapely2 does (#25)
- Changes in the `create_grid` functions, compared to the geofileops version (#28):
    - they now return `NDArray[BaseGeometry]` instead of `GeoDataFrame`
    - the `crs` parameter has been removed

## 0.1.1 (2023-04-12)

### Improvements

- Cleaner result for polygons ending in rectangular shapes (#16)

## 0.1.0 (2023-03-01)

First version. The following spatial operations are available:

- centerline: calculates the approximate centerline for a polygon (#1)
- view_angles: calculates the angles where a geometry can be seen from a viewpoint (#7, #9)
