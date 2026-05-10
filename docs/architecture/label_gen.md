# Labeling Format System

## Overview

The labeling format system handles serialization of synthetic annotations to standard computer vision formats. It is built around a single abstract class (`IOStrategy`) and a registry that maps format names to their implementations. The registry is the only entry point you need when selecting or adding a format.

The code lives under `ext/core/io/`:

```
ext/core/io/
├── io_strategy.py       # Abstract base class and data structures
├── registry.py          # LabelingFormatRegistry
└── strategies/
    ├── __init__.py       # SupportedFormats enum + imports
    ├── yolo_strategy.py
    ├── coco_strategy.py
    ├── pascal_strategy.py
    └── cvat_xml_strategy.py
```

---

## Core Concepts

### FormatSpecification

Each strategy declares its capabilities and requirements by returning a `FormatSpecification` from `get_specification()`. This tells the pipeline how to drive the strategy: whether to write one file per image or one global file, whether class declarations are needed, which geometry types are expected, and so on.

```python
@dataclass
class FormatSpecification:
    single_file_per_image: bool         # True for YOLO/Pascal, False for COCO
    global_metadata_required: bool      # True for COCO
    aggregation_strategy: Literal["per_image", "per_batch", "global"]
    requires_class_declaration: bool
    supports_image_metadata: bool
    requires_bbox: bool = False
    requires_polygon: bool = False
    requires_keypoints: bool = False
    requires_depth: bool = False
```

The pipeline reads this spec and calls the appropriate methods. If you implement a new strategy, this is the first thing to get right.

### IOStrategy sequence diagram

For each batch, the pipeline calls these methods in order:

1. `ensure_directories()` — create output directories before writing anything.
2. `transform_annotation(label, shot_idx, shot_config)` — convert a single canonical `Label` object into a format-specific dict. Called once per annotation.
3. `serialize_image_labels(transformed)` — used by per-image formats (YOLO, Pascal VOC) to produce file content from a list of transformed annotations for one image. Returns a collection of `(file_type, extension, content_string)` tuples.
4. `aggregate_batch(annotations, batch_metadata)` — used by global formats (COCO) to build the full batch structure from all transformed annotations.
5. `finalize(aggregated)` — called once per batch. For COCO this produces the final JSON. For YOLO it produces `data.yaml` and the image list `.txt`. Returns `(file_type, extension, content_string)` tuples.

File routing is handled by `get_subdir_for(shot_id, file_type)` and `get_filename_for(shot_id, file_type)`, which the pipeline uses to determine where to write each returned tuple.

---

## Implemented Formats

### Ultralytics YOLO

**Registry key:** `"Ultralytics YOLO"`

One `.txt` label file per image. Each line is `class_id cx cy w h` in normalized coordinates. Additionally produces a `data.yaml` (dataset config) and a `.txt` file listing image paths, both at batch finalization.

Directory layout:
```
<save_path>/
├── images/
│   └── <prefix>_<shot_id>.png
└── labels/
    └── <prefix>_<shot_id>.txt
```

With `split` set (e.g. `"train"`):
```
<save_path>/
└── train/
    ├── images/
    └── labels/
```

Config keys accepted via `format_cfg`:
- `bbox_precision` (int, default 3): decimal places for bbox coordinates.
- `split` (str, default `""`): dataset split name.

### COCO (Bounding Box)

**Registry key:** `"COCO"`

Produces a single `instances.json` per batch following the COCO detection format. Images are accumulated during `transform_annotation`, categories are built during `aggregate_batch`, and the final JSON is written in `finalize`.

Directory layout:
```
<save_path>/
├── images/
│   └── <prefix>_<shot_id>.png
└── instances.json
```

Config keys:
- `bbox_precision` (int, default 2): decimal places for bbox coordinates.
- `split` (str, default `""`): dataset split name.

### Pascal VOC

**Registry key:** `"Pascal VOC"`

One XML annotation file per image. The XML structure follows the standard Pascal VOC schema with `<annotation>`, `<object>`, and `<bndbox>` elements.

Directory layout:
```
<save_path>/
├── images/
└── annotations/
    └── <prefix>_<shot_id>.xml
```

Config keys:
- `split` (str, default `""`): dataset split name.
- `xml_indent` (int, default 2): indentation for pretty-printed XML.

### CVAT XML (Images)

**Registry key:** `"CVAT XML Images"`

Produces a single XML file compatible with CVAT's image annotation format.

---

## Registering a Custom Format

### From inside the extension (decorator)

If your strategy lives within the extension package, use the `register_strategy` decorator:

```python
from ext.core.io.registry import LabelingFormatRegistry
from ext.core.io.io_strategy import IOStrategy, FormatSpecification, StorageSpec

@LabelingFormatRegistry.register_strategy("My Custom Format")
class MyFormatter(IOStrategy):
    def __init__(self, write_config, config):
        super().__init__(write_config, config)
        # read your format-specific keys from config dict

```

### From a Blender script (Python API)

If you want to register a format at runtime from Blender's scripting tab without modifying the extension source, use `register_new`:

```python
class MyFormatter(IOStrategy):
    # ... implement all abstract methods as above ...
    pass

LabelingFormatRegistry.register_new("My Custom Format", MyFormatter)

```

`register_new` validates that the provided class is a subclass of `IOStrategy` and raises `RuntimeError` if it is not. It does not validate that all abstract methods are implemented — that will raise at instantiation time when the pipeline tries to use it.

---

## Format Configuration

Format-specific settings are passed as a plain `dict` at instantiation time, sourced from the UI config. There is no fixed schema — each strategy reads only the keys it needs via `config.get(...)`.

When implementing a new strategy, document which keys your `__init__` reads. Unrecognized keys are silently ignored since strategies use `config.get(key)` rather than direct access.

---

## Notes

- `COCO_SEGMENTATION` and `COCO_KEYPOINTS` are registered in the registry but not yet implemented (stub classes).
- The `aggregation_strategy` field in `FormatSpecification` controls which pipeline path is taken. A strategy that sets `"global"` must implement `aggregate_batch` and `finalize` meaningfully and may raise `NotImplementedError` in `serialize_image_labels` (as `COCOFormatter` does).
