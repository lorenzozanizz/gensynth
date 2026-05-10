from .panels import RandomizerPanel, SettingsPanel, InfoPanel
from .pipeline_list_viewer import (RegistrationPanel, AddCameraCategoryPipeMenu, AddLightingCategoryPipeMenu,
                                   AddObjectCategoryPipeMenu, AddMaterialCategoryPipeMenu, AddConstraintCategoryPipeMenu,
                                   PipelineOperationsList, AddExperimentalCategoryPipeMenu)
from .properties import ext_ui_properties, distribution_settings, operation_properties
from .pipe_editor import (DistributionTreeList, PathsUIList, ImagePath, PositionsUIList, ObjectName, TypedNodeProperty,
                          ObjectPosition, MaterialListItem, MaterialUIList)
from .labeling_panel import LabelingPanel, LabelClassesUIList, ObjectLabelsUIList, LabelRulesUIList, NamedEntitiesUIList
from .formatting_config import LabelConfigDataProperty

from .handlers import sync_distribution_handler


import bpy

def register_handlers():
    """Register all scene handlers."""
    bpy.app.handlers.depsgraph_update_post.append(sync_distribution_handler)


def unregister_handlers():
    """Unregister all scene handlers."""
    if sync_distribution_handler in bpy.app.handlers.depsgraph_update_post:
        bpy.app.handlers.depsgraph_update_post.remove(sync_distribution_handler)


classes = (
    RandomizerPanel, SettingsPanel, InfoPanel, RegistrationPanel, LabelingPanel, AddCameraCategoryPipeMenu,
    AddLightingCategoryPipeMenu, AddObjectCategoryPipeMenu, PipelineOperationsList, AddExperimentalCategoryPipeMenu,
    AddMaterialCategoryPipeMenu, AddConstraintCategoryPipeMenu, DistributionTreeList, PathsUIList,
    ImagePath, PositionsUIList, ObjectPosition, MaterialListItem, MaterialUIList, ObjectName, TypedNodeProperty,
    LabelClassesUIList, ObjectLabelsUIList, LabelRulesUIList, NamedEntitiesUIList, LabelConfigDataProperty
)

# Update the main UI properties of the pipeline with settings for the configuration of each pipe's distributions
# and properties regarding the pipeline operations
ext_ui_properties.update(operation_properties)
ext_ui_properties.update(distribution_settings)

properties = ext_ui_properties