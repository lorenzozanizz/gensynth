# Pipeline Execution

## Overview

The pipeline execution system is the part of the codebase responsible for taking a configured sequence of randomization operations, compiling them into executable objects, running them for each rendered shot, and restoring the scene state afterwards. It lives primarily in `ext/pipeline/` and `ext/core/`.

---

## Operations and the registry

Each randomization stage is represented by a `PipelineOperation` subclass: one class per pipe type. Operations are registered with `OperationRegistry` via a class decorator:

```python
@OperationRegistry.register(PipeNames.SCALE.value)
class RandomizeScaleOperation(NumericRandomOperation):
    ...
```

The registry maps pipe type names (which are also the keys in the serialized JSON config) to operation classes. When the pipeline is compiled, the registry is the only place queried to instantiate operations.

---

## Compile before Execute

Every operation has two separate concerns: `compile` and `execute`.

`compile(context, config)` is called once before generation begins. It reads the operation's JSON config, resolves Blender object references, and sets up whatever state the operation needs: target object names, sampled node references, a compiled distribution sampler. Compilation is intentionally separate from execution so that expensive lookups (finding materials, locating nodes, setting up distribution objects) happen once per batch rather than once per frame.

`execute(context)` is called once per rendered frame. It samples the distribution and applies the result to the target Blender properties. It is designed to be fast: by the time `execute` is called, everything has already been resolved.

---

## Context managers and state restoration

One of the more careful aspects of the execution system is how scene state is restored between renders. Without restoration, each pipe's changes would accumulate across shots, and the "before" state for offset-mode pipes would drift.

Every operation provides two context managers:

- `get_global_context()` returns a context that is entered once at the start of a batch and exited once at the end. It captures the pre-generation state of whatever the operation targets.
- `get_frame_context()` returns a context that is entered and exited once per frame. For operations running in offset mode, this is the mechanism that resets the accumulated delta after each render so the next frame starts from the original value. Operations that do not use offset mode can return `None` here.

These are collected by `NestedPipelineContext` and `FrameContext` respectively. The execution loop then looks like:

```
with NestedPipelineContext:       # global context entered
    for each shot:
        with FrameContext:        # per-frame context entered
            execute all ops
            render
        # per-frame context exits, offset deltas reset
    # global context exits, original values restored
```

This two-level context structure means the system handles both absolute randomization (where each frame is fully independent) and offset-based randomization (where each frame starts from the original value and adds a random delta) using the same mechanism.

---

## ExecutablePipeline

`ext/core/executable_pipeline.py` wraps the list of compiled operations and handles the compilation phase: it reads the `PipelineData` Blender property, iterates over the operation entries, retrieves each operation class from the registry, calls `compile`, and builds the nested context manager. It also records compilation time for the preview's timing display.

Operations whose configs fail to parse or whose target objects cannot be found are skipped with a warning rather than aborting the batch.

---

## Executor and PreviewGenerator

`Executor` (in `ext/core/generation.py`) drives batch generation. It owns an `ExecutablePipeline`, an `OutputWriter`, and a `LabelingOrchestrator`. Its `execute` method seeds the random number generator with the user's seed, computes the starting file index (supporting append mode), and runs the outer/inner context loop above.

`PreviewGenerator` (in `ext/core/preview.py`) follows the same structure but renders exactly one frame and passes `writer=None` to the orchestrator. It then passes the resulting `LabelData` to the annotation drawing routines.

---

## Pipeline serialization

The pipeline configuration is stored in Blender's property system as JSON strings on each operation entry. Each `PipelineOperation` entry in the `pipeline_data.operations` collection carries an `operation_type` string (the registry key), an `enabled` flag, a `name`, and a `config` field holding the serialized JSON dict.

`PipelineSerializer` and `PipelineLoader` in `ext/operators/io_ops.py` handle reading and writing this representation to and from disk. The serialized format also includes the labeling configuration and generation settings (seed, amount), making the JSON file a complete, portable description of a dataset generation run.

Pipeline validity is checked by `PipelineScanner` in `ext/pipeline/integrity.py`, which walks the loaded operations and calls registered validators to flag pipes with dangling object references or missing configuration.
