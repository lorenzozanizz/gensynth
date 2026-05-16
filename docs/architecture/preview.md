# Preview System

## Overview

The preview system lets users sample one random shot from the current pipeline and immediately see what the annotations look like, all without leaving Blender and without producing any output files. The result is the standard Blender F12 render window with annotation geometry, class labels, visibility estimates, and timing statistics drawn directly over the rendered image.

The implementation lives in `ext/core/preview.py` and is driven by `PreviewOperator` in `ext/operators/core_ops.py`.

---

## Execution flow

The `PreviewGenerator` class mirrors the structure of the full `Executor` but omits the file-writing step. It compiles and executes the pipeline once, renders to a temporary file in the system temp directory, runs the labeling orchestrator (without a writer attached, so no labels are written), and then annotates the result.

The annotation step opens the rendered image in Blender's image data system and draws over its pixel array directly. No external viewer and no GUI framework are involved, so that the drawing is done entirely with `bpy.data.images` and the pixel manipulation utilities in `ext/utils/images.py`.

---

## Drawing

After the render, `display_and_render_preview` opens the F12 render window, loads the temporary image, and iterates over the `LabelData` produced by the orchestrator. For each classified object or entity, it draws:

- the annotation geometry (bounding box or polygon outline), using the class color;
- an "ideal" bounding box representing the full unoccluded 3D projection, drawn at a thinner line weight to distinguish it from the visible geometry;
- a text label combining the object name, class name or class ID, and estimated visibility percentage, sized to fit proportionally within the annotation width.

A timing summary is drawn in the bottom-left corner of the image, showing how long each phase took: pipeline compilation, rendering, label extraction, and annotation drawing. This is useful for diagnosing which step is the bottleneck in a given scene.

All text is rendered with the extension's built-in 8×8 bitmap font (defined in `ext/utils/fonts.py`). Font size is computed dynamically so that labels scale with the bounding box width rather than being fixed in pixels.

---

## Implementation notes

Because Blender's image pixel array has `y = 0` at the *bottom* of the image while annotation coordinates are produced in a top-origin convention, the preview converts all geometry through `convert_geometry_camera_to_absolute_y_inverted` before drawing. This conversion is the main coordinate-system concern in the drawing code.

The preview uses the same `LabelingOrchestrator` as the batch generator, instantiated with `writer=None` so the orchestrator performs all classification and extraction without attempting any file I/O.

Geometry rendering supports both bounding boxes (drawn as four line segments) and polygons (drawn as a closed polyline with vertex markers at each corner). The line drawing uses a Bresenham algorithm implemented in `ext/utils/images.py`, and polygon fill is available via a scanline algorithm, though the preview currently uses only the outline variant.

As a future step, the preview system will have to support many different labeling formats (e.g. depthmaps or normal maps), so 
it may be wise to pair labeling formats with preview drawing. 