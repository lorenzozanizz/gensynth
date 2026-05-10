# Pipeline Serialization Architecture

## Overview

The extension serializes pipeline operations in three layers: in-memory scene properties (Blender's PropertyGroup system), intermediate JSON strings within operations, and persistent file-based JSON exports. Each layer serves a distinct purpose in the workflow from user interaction to file storage.

## In-Memory Storage: PropertyGroup Foundation

Pipeline state resides in Blender's PropertyGroup system, which provides automatic serialization to `.blend` files. The `PipelineOperation` class defines the per-operation storage contract with four fields:

- `operation_type`: Identifies the operation kind (Scale, Rotation, Visibility, etc.) and determines which serialization schema applies
- `enabled`: Boolean flag controlling whether the operation executes
- `name`: User-facing display name
- `config`: JSON string containing the complete operation configuration

The `PipelineData` container holds a `CollectionProperty` of operations and tracks the active operation index, enabling ordered execution and UI selection. Blender automatically persists both structures when saving `.blend` files, eliminating manual serialization for the primary editing workflow.

## Config Extraction and Schema Application

When the user saves an operation via `SavePipeOperator`, the system retrieves the appropriate schema from `PipeSchemaRegistry` based on the operation's type. The schema provides two symmetric methods:

`extract_config_from_ui()` gathers configuration from scene properties scattered across the UI layer. It delegates to zero or more `EditorWidget` implementations that each contribute a subset of the configuration dictionary. For example, `VisibilitySchema` composes extraction results from `ObjectTargeter` (which reads object names from `scene.targeted_objects_display`) and `SimplifiedDistributionSelector` (which reads the selected distribution reference). The schema aggregates these partial dictionaries into a complete configuration and returns it.

`apply_config_to_ui()` performs the reverse operation: it loads a configuration dictionary back into scene properties. Each widget's `setup_from_config()` method reads the relevant keys and populates its corresponding scene properties. If no configuration exists (new operation), widgets can reset themselves to default states via the `reset()` method.

This dual-schema pattern decouples the operation's logical configuration from its UI representation. Adding a new operation type requires implementing a schema that knows which widgets to compose, not modifying widget code itself.

## Serialization Flow: Edit-to-Save

When the user edits an operation:

1. The UI panel displays operation configuration through registered `EditorWidget` subclasses. Each widget reads and writes its data to scene properties (e.g., `scene.targeted_objects_display`, `scene.randomize_x`).

2. User modifies values directly in the Blender UI, updating the underlying scene properties through Blender's property binding system.

3. The user clicks "Save" in the editor panel, triggering `SavePipeOperator.execute()`.

4. The operator retrieves the active operation from the pipeline and looks up its schema via `PipeSchemaRegistry.get(operation.operation_type)`.

5. The schema's `extract_config_from_ui()` method iterates through its registered widgets, calling `extract_data()` on each. Each widget reads the current state of its scene properties and returns a dictionary. The schema merges these dictionaries into a single configuration object.

6. The operator converts the configuration dictionary to JSON via `json.dumps()` and stores the string in `operation.config`.

7. On next `.blend` file save, Blender automatically persists the updated property string.

The operation's configuration is now serialized—stored as a JSON string within the PropertyGroup, ready for execution or export.

## File Serialization: Export and Reimport

`SavePipelineAsOperator` exports the entire pipeline to a standalone JSON file. It iterates through all operations in `pipeline.operations` and constructs a file-format dictionary:

```python
pipeline_dict = {
    'version': '1.0',
    'operations': [
        {
            'operation_type': op.operation_type,
            'seed': op.seed,
            'intensity': op.config,  # Raw JSON string stored in property
            'enabled': op.enabled,
        }
        for op in pipeline.operations
    ]
}
```

The operator writes this structure to JSON and saves the file path in `scene.randomizer_pipeline_save_path` for future reference. The exported JSON is a flat representation—each operation contributes its metadata and the already-serialized configuration string.

File-based serialization serves three purposes: archival (preserving pipelines external to `.blend` files), version control (diffable JSON over binary `.blend` files), and portability (sharing pipelines between projects or users without transferring `.blend` file dependencies).

## Widget Composition Pattern

Widgets inherit from `EditorWidget`, an abstract base that enforces four operations: drawing UI, extracting configuration, applying configuration, and resetting to defaults. Each widget is self-contained, reading and writing only its own scene properties.

The pattern enables reusable configuration components. For example, `ObjectTargeter` appears in multiple operation schemas (Move, Visibility, Material) but always manages `scene.targeted_objects_display` consistently. When a schema changes, only the schema needs modification so that the widget remains unaware of its consumer.

Widgets compose configuration by reading Blender properties directly. They assume scene properties exist (the properties are registered globally during addon initialization) and focus only on the logic of extraction and reconstruction. This separation allows UI designers to add new properties and widgets without coordinating with schema code.

## Configuration Scope and Limitations

The current implementation stores operation-level configuration only, so that each operation's `config` string is independent and self-contained. The extension does not track:

- Cross-operation dependencies or ordering constraints
- Global pipeline parameters (seed randomization, output format)
- Widget state or transient UI selections outside the final configuration

Those parameters are either immaterial or assumed to be set manually by the user when generating new data. 

The active operation index in `PipelineData` enables sequential execution but carries no configuration semantics. Execution order is implicit in the collection order and explicit `enabled` flags.

Configuration is operation-specific; there is no schema-level facility to validate configuration consistency across the entire pipeline. A malformed operation JSON string will fail only when that operation is deserialized for execution.

## Error Handling and Validation

The extension provides minimal validation during serialization. `SavePipeOperator` calls `extract_config_from_ui()` without catching or validating the result; if a widget extracts invalid data, the resulting JSON is still written to the property. File export (`SavePipelineAsOperator`) wraps execution in a try-except block and reports errors via the operator's `self.report()` method, but per-operation validation is absent.

Loading configuration via `apply_config_to_ui()` assumes the configuration dictionary contains expected keys. Missing keys will raise `KeyError` exceptions, which the extension does not currently handle. This defensive posture is reasonable for the current maturity level but would require hardening for production use.

## Storage Efficiency Trade-offs

Storing JSON strings in PropertyGroup fields trades storage simplicity for repetition. Each configuration is serialized on every save operation, and the serialized form is redundant with the scene properties that generated it. For a pipeline with ten operations and three configuration keys per operation, serializing each operation stores approximately 30 redundant keys.

This design prioritizes correctness and simplicity over optimization. The system guarantees that the source of truth (scene properties) and the serialized form (JSON string) can be synchronized bidirectionally without data loss. Caching or incremental serialization would introduce complexity without significant gain for typical pipeline sizes.

## (Consequent) Integration with Blender's Undo System

PropertyGroup modifications trigger Blender's undo stack automatically. When `SavePipeOperator` modifies `operation.config`, Blender records the change and enables undo/redo. File export does not modify properties and thus leaves undo history unaffected.

The extension does not implement custom undo operators or undo step grouping. Individual operations appear as separate undo steps, which may require multiple undo invocations to revert a complete operation configuration change across multiple save cycles. Future enhancements could group related changes into semantic undo steps.