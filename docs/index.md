# Rendersynth

**Current Version 1.0.0** , Tested on Blender 4.5.0

Rendersynth is a Blender extension for generating synthetic image datasets with automatic annotations for computer vision tasks. It integrates directly into Blender's 3D viewport sidebar and drives the full generation pipeline: randomization, rendering, labeling, and export, without leaving the application or requiring any external tooling.

The extension lets you define a *pipeline* of randomization stages (object transforms, material swaps, lighting adjustments, camera movement, and more), configure a labeling scheme, and produce a batch of rendered images with corresponding annotations in standard formats such as Ultralytics YOLO, COCO, Pascal VOC, and CVAT XML.

---

## What it does

At its core, Rendersynth separates three concerns cleanly: *what to randomize*, *how to label the result*, and *where to write the output*.

**Randomization** is expressed as an ordered sequence of "pipes," each targeting a specific Blender property: object position, rotation, scale, visibility, material, shader node value, texture, light power, focal length, and more. Each pipe draws samples from a configurable probability distribution (uniform, Gaussian, Beta, Bernoulli, categorical, and several multivariate variants). For advanced use, any distribution parameter can be driven by a node graph in Blender's own node editor rather than a fixed preset.

**Labeling** is built on a camera-space ray casting pass that identifies which objects are visible in a given render and to what degree they are occluded. Objects are mapped to user-defined classes either directly, via naming rules, or via collection membership. Multi-object entities can be defined so that several scene objects are jointly annotated as a single label. Geometry is currently extracted as axis-aligned bounding boxes, with a convex hull extractor also present.

**Output** is written through a strategy pattern: each supported annotation format implements a common interface, and the writer calls into it per-image or per-batch depending on the format's requirements. Images are saved via Blender's own render pipeline; no external image library is involved.

A *preview* mode renders a single sample from the pipeline and overlays the annotation geometry, class labels, and timing statistics directly on the rendered image all inside Blender, with no external viewer.

---

## Capabilities at a glance

- Pipeline-based randomization of object transforms, materials, textures, shader properties, lights, and cameras
- Arbitrary probability distributions configurable from the sidebar, with an optional visual node editor for complex distributions
- Class assignment via direct mapping, naming rules, or Blender collections
- Multi-object entity support for jointly-annotated composite objects
- Visibility estimation via 3D bounding box projection vs. ray-traced visible area
- Annotation export in Ultralytics YOLO, COCO (detection), Pascal VOC, and CVAT XML formats
- In-Blender annotated preview with timing diagnostics
- Pipeline serialization to and from JSON for reuse and version control
- Optional structured logging of stochastic outputs for reproducibility analysis
- Zero external Python dependencies: everything runs on Blender's bundled Python environment

---

## Changelog

**[1.0.0]** - Current release
- First stable public release.

**[0.9.1]** - 13 May 2026
- Implementation of randomization stages for material, lights, and cameras.
- Implementation of color randomization for shaders.

**[0.9.0]** - 29 April 2026
- Implementation of COCO polygon labels.
- Implementation of CVAT XML format.
- Implementation of Pascal VOC XML format.
- Fixed a bug where the YOLO format would not generate the aggregated `.yaml` and `data.txt`.

---

## Contributing

Rendersynth is open source under the MIT license. Contributions or bug reports, feature proposals, new labeling format implementations, or additional randomization stages are all welcome via the [GitHub repository](https://github.com/lorenzozanizz/rendersynth).

If you wish to add a new stage to the pipeline, before opening a pull request, please check that any new operator is registered in `operators/names.py` using the `Labels` enum (rather than as a raw string), and that any new pipe type has a corresponding entry in `OperationRegistry`, `OperationDrawerRegistry`, and `PipeSchemaRegistry`. The architecture documentation describes these registries in more detail.

For questions or discussion, please open an issue or contact my email.
