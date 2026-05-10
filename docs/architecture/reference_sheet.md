# Quick Reference Guide

## File Navigation Cheat Sheet

#### How operations are stored
→ `ext/pipeline/data.py` — PropertyGroup definitions, using Blender property system

#### How operations are executed
→ `ext/pipeline/operations.py` — Operation classes with execute(), pipes are compiled and then executed in sequence for every frame. 

#### How to add a new operation
→ See [Adding a New Operation](#adding-a-new-operation-step-by-step)

#### How the UI works
→ `ext/ui/panels.py` (main panels)  side bar panels (except labeling and pipeline editor) 
→ `ext/ui/pipeline_list_viewer.py` (operation list and tabs) pipeline editor
→ `ext/ui/labeling_panel.py` labeling assignment 

#### How to draw operation config UI
→ `ext/ui/pipe_editor.py` (registries and drawer classes)  
→ `ext/ui/pipe_edit_widgets.py` (reusable components)

#### How to validate a pipe after saving it
→ `ext/pipeline/integrity.py` validation registry and pipe validators

#### How to save/load operation config
→ `ext/ui/pipe_schema.py` (serialization registry) and pipe schema implementations

#### How operators work
→ `ext/operators/` (all operator classes)  
→ `ext/operators/names.py` (operator identifiers) used as references to avoid dangling references

#### How (node) distributions work [WORK IN PROGRESS]
→ `ext/distribution/nodes.py` (node definitions)  
→ `ext/distribution/__init__.py` (node categories/menu)

#### Where configuration constants live
→ `ext/constants.py` (enums, URLs, versions)

#### Where objects and entities are assigned labels
→ `ext/labeling/class_engine.py` assignment of classes

---

## Key Classes at a Glance

### Data Storage
| Class | File | Purpose |
|-------|------|---------|
| `PipelineData` | `pipeline/data.py` | Collection container |
| `PipelineOperation` | `pipeline/data.py` | Single operation item |

### Execution
| Class | File | Purpose |
|---|---|---|
| `PipelineOperation` (ABC) | `pipeline/operations.py` | Base class for executable ops |
| `RandomizeScaleOperation` | `pipeline/operations.py` | Concrete scale implementation |
| `OperationRegistry` | `pipeline/registry.py` | Lookup table for operations |
| `CompiledPipeline` | `core/executable_pipeline.py` | How pipes are compiled and executed in sequence  |


### UI Rendering
| Class | File | Purpose |
|---|---|---|
| `RandomizerPanel` | `ui/panels.py` | Main panel |
| `RegistrationPanel` | `ui/pipeline_list_viewer.py` | Pipeline editor panel |
| `PipelineOperationsList` | `ui/pipeline_list_viewer.py` | UIList renderer |
| `PipeDrawer` (ABC) | `ui/pipe_editor.py` | Base for UI drawers |
| `RandomizeScaleOperation` | `ui/pipe_editor.py` | UI drawer for scale |
| `OperationDrawerRegistry` | `ui/pipe_editor.py` | UI drawer lookup |

### Config Serialization
| Class | File | Purpose |
|---|---|---|
| `PipeSchema` (ABC) | `ui/pipe_schema.py` | Base for serialization |
| `VisibilitySchema` | `ui/pipe_schema.py` | Concrete schema |
| `PipeSchemaRegistry` | `ui/pipe_schema.py` | Schema lookup |

### Operators

The following are only some pipeline operators to add, remove, edit and save pipes. They follow the standard Blender interface for Operators. 
| Class | File | Purpose |
|---|---|---|
| `PipeAddOperator` | `operators/pipeline_ops.py` | Add operation |
| `PipeRemoveOperator` | `operators/pipeline_ops.py` | Remove operation |
| `EditPipeOperator` | `operators/pipeline_ops.py` | Edit operation |
| `SavePipeOperator` | `operators/pipeline_ops.py` | Save operation config |

### Distribution [ WORK IN PROGRESS ]
| Class | File | Purpose |
|---|---|---|
| `DistributionNodeTree` | `distribution/nodes.py` | Custom node editor |
| `ConstantSampler` | `distribution/computation.py` | Fixed value node, Normal distribution etc... |
| `BezierDistribution` | `distribution/bezier.py` | Sampling a point on a curve in space |

---

## Code Navigation Patterns

### Finding where a UI button is created
1. Find button label in `ext/ui/` files
2. Look for `.operator()` call
3. The operator call uses a name defined in the `operators/names.py` module which contains the correct file name. 

**Example**: "Add" button in pipeline list
```python
# ext/ui/pipeline_list_viewer.py
col.operator(Labels.ADD_MENU_LIST_.value, ...)

# ext/operators/names.py
ADD_MENU_LIST_ = "randomizer.add_menu_list"

# ext/operators/graphical_ops.py
class MenuOperator(Operator):
    bl_idname = Labels.ADD_MENU_LIST_.value
```

### Finding where a property is defined
1. Search property name in UI code
2. Find `.prop()` call referencing it
3. Look in `ext/ui/properties.py` for definition
4. Property is attached to `bpy.types.Scene` in `__init__.py`

**Example**: Finding where randomizer_amount is defined
```python
# In panel
layout.prop(scene, "randomizer_amount")

# In properties.py
ext_ui_properties = {
    "randomizer_amount": IntProperty(default=10, min=1),
    ...
}

# Attached in __init__.py
setattr(bpy.types.Scene, "randomizer_amount", IntProperty(...))
```

Most UI properties are defined inside `ui/properties.py`. Certain special properties which handle
the storage of the pipeline itself are instead defined in `pipeline/data.py`

### Adding a new UI panel
1. Create Panel subclass in `ext/ui/panels.py`
2. Add to `classes` tuple in `ext/ui/__init__.py`
3. It auto-registers in `__init__.py` during addon registration

### Adding a new operator
1. Create Operator subclass in appropriate file in `ext/operators/`
2. Add to tuple in `ext/operators/__init__.py`
3. Add entry to `Labels` enum in `ext/operators/names.py`
4. It auto-registers in `__init__.py`

---

## Adding a New Operation

### Step 1: Add to PipeNames enum

The label will be used around the code to refer to the same pipe in multiple registries. 
**File**: `ext/constants.py`
```python
class PipeNames(Enum):
    # ... existing ...
    MY_NEW_OP = "My New Operation"
```

### Step 2: Define execution class

This class will be executed in sequence with other pipes, and thus handles and operates on Blender objects. 
**File**: `ext/pipeline/operations.py`
```python
@OperationRegistry.register(PipeNames.MY_NEW_OP.value)
class MyNewOperation(PipelineOperation):
    
    def from_config(self) -> dict:
        pass
    
    def execute(self, scene, objects):
        # Actual implementation of the operator
        pass
    ...
```

This internally registers the operator (a pipe) as executable. Now there is a need to add the pipe to the UI which allows
 the user to create it. 

### Step 3: Define UI drawer

This editor is drawn when the user clicks on "edit pipe" button in the pipe editor. 
**File**: `ext/ui/pipe_editor.py`
```python
# -----------------------------    Same label as the PipelineOperation implementation
@OperationDrawerRegistry.register(PipeNames.MY_NEW_OP.value)
class MyNewOperationDrawer(PipeDrawer):
    
    @staticmethod
    def draw_editor(layout, context) -> None:
        # Draw configuration UI
        ObjectTargeter.draw(layout, context)  # Use existing widgets
        layout.separator()
        # Add custom widgets as needed
```

### Step 4: Define config schema

Now the pipe is added to the pipeline but needs to be able to be serializable in a human-readable JSON. For 
this purpose we create a schema which encodes the pipe into a dictionary, or prepares the editor when the pipe 
is to be edited, reading from the configuration. 

**File**: `ext/ui/pipe_schema.py`
```python
@PipeSchemaRegistry.register(PipeNames.MY_NEW_OP.value)
class MyNewOperationSchema(PipeSchema):
    
    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        pass
    
    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        pass
```

### Step 5: Add to menu (optional)

The pipe now needs to be added to the UI menu to be selected by the user. Either add it to an existing menu section 
or create a new menu section. 

**File**: `ext/ui/pipeline_list_viewer.py`
```python
class AddCustomCategoryPipeMenu(Menu):
    bl_label = 'Custom'
    bl_idname = 'AddCustomCategoryPipeMenu'
    
    def draw(self, context):
        layout = self.layout
        layout.operator(Labels.ADD_PIPE.value, text="My New Operation",
                       icon='MY_ICON').op_name = PipeNames.MY_NEW_OP.value
```

### Step 6: Add scene properties (if needed)

Properties should be all kept separated into the properties.py module. If a property has a special meaning 
or structure, it could be put in some other module, as long as its correctly registered to the blender API. 
**File**: `ext/ui/properties.py`
```python
operation_properties = {
    "my_param1": ...
}
```

---

## Common Tasks

### How to get current pipeline
```python
scene = bpy.context.scene
pipeline = scene.pipeline_data
active_op = pipeline.operations[pipeline.active_operation_index]
```

### How to get all operations
```python
scene = bpy.context.scene
for operation in scene.pipeline_data.operations:
    print(f"{operation.name} ({operation.operation_type})")
```

### How to parse operation config
```python
import json
operation = scene.pipeline_data.operations[0]
config = json.loads(operation.config)
min_val = config.get('min_value', 0)
```
