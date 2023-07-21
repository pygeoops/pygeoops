# CHANGELOG

## 0.2.0 (???)

### Improvements

- Copy/move geometry utility functions from geofileops to pygeoops (#20)
  - extended `simplify` function (support for different algorithmns, exclude points from removal)
  - grid utility functions: `create_grid`, `split_tiles`
  - general geometry utility functions: `collect`, `collection_extract`, `numberpoints`, `remove_inner_rings`

## 0.1.1 (2023-04-12)

### Improvements

- Cleaner result for polygons ending in rectangular shapes (#16)

## 0.1.0 (2023-03-01)

First version. The following spatial operations are available:

- centerline: calculates the approximate centerline for a polygon (#1)
- view_angles: calculates the angles where a geometry can be seen from a viewpoint (#7, #9)
