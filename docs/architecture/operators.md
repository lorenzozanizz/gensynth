# Operators

All Blender operators for the extension live under `ext/operators/`. The directory is organized by functional domain rather than by any architectural distinction, each file groups operators that belong to the same area of the interface.

- `core_ops.py` contains the two primary execution operators: one that compiles the pipeline and runs a full generation batch, and one that triggers a single preview render.
- `pipeline_ops.py` contains operators that manage the pipeline editor, adding and removing pipes, editing and saving pipe configurations, capturing objects and shader nodes from the scene, and scanning the pipeline for validity errors.
- `labeling_ops.py` contains operators for the labeling panel: creating and removing label classes, assigning objects to classes, managing label rules, and defining multi-object entities.
- `io_ops.py` contains operators for file-level operations: saving and loading pipeline JSON, setting up the logger directory, and opening the log output folder.
- `graphical_ops.py` contains operators that manage UI state without directly affecting scene data, switching tabs in the pipeline editor, reordering pipes in the list, managing distribution node trees, and toggling between labeling sections.
- `distribution_ops.py` contains operators for managing the distribution-related UI lists: image paths, material pools, color palettes, and gradient entries.
- `node_ops.py` contains operators for working with the shader node editor specifically.

All operator identifiers (`bl_idname` values) are defined centrally in `names.py` as members of the `Labels` enum. No operator string is written more than once; every place that needs to invoke or draw an operator references `Labels.NAME.value`. This prevents dead-link operators and makes it straightforward to trace where any given operator is used.
