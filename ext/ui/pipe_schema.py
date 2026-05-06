"""Schema definitions and registry for pipeline operation configurations.

Provides a framework to register, extract, and apply configuration schemas
for different pipeline operations, enabling serialization and UI synchronization.
All pipes need to have a serialization and deserialization schema to dump and
load from memory, either through a json file or through a blender property.

Classes:
    PipeSchemaRegistry: Manages registration and retrieval of operation schemas.
    PipeSchema: Abstract base class for defining UI-to-config transformations.
    ScalarPropertyDrawer: Base schema for scalar/vector-based operations.
    ... other schema implementations

Example:
    >>> from ext.ui.pipe_schema import PipeSchemaRegistry
    >>> PipeSchemaRegistry.register("pipe_name")
    >>> class NewPipeSchema(PipeSchemaRegistry):
    >>> pass
"""

from .pipe_edit_widgets import *

from ..constants import PipeNames

from abc import ABC, abstractmethod
from typing import Union, Optional

wsk = WidgetSerializationKeys

class PipeSchemaRegistry:
    """Registry of all available operations."""

    _pipes_schema = {}

    @classmethod
    def register(cls, op_type: str):
        if op_type in cls._pipes_schema:
            raise RuntimeError(f"Duplicate operation type {op_type}")
        def decorator(drawer_cls):
            cls._pipes_schema[op_type] = drawer_cls
            return drawer_cls
        return decorator

    @classmethod
    def get(cls, operation_type: str) -> Optional['PipeSchema']:
        """Get a schema instance by type."""
        if operation_type not in cls._pipes_schema:
            return None
        return cls._pipes_schema[operation_type]()

    @classmethod
    def get_all_types(cls) -> list:
        """Get all available schemas types."""
        return list(cls._pipes_schema.keys())


class PipeSchema(ABC):
    """

    """

    @staticmethod
    @abstractmethod
    def extract_config_from_ui(context, operation) -> dict:
        """

        :param context:
        :param operation:
        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def apply_config_to_ui(context, operation, config) -> None:
        """

        :param context:
        :param operation:
        :param config:
        :return:
        """
        pass


@PipeSchemaRegistry.register(PipeNames.VISIBILITY.value)
class VisibilitySchema(PipeSchema):

    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        dic =  {
            "dimension": 1,
            "target": ObjectTargeter.extract_data(context),
            "distribution": SimplifiedDistributionSelector.extract_data(context, dim=1)
        }
        return dic

    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        if not config:
            ObjectTargeter.reset(context)
            SimplifiedDistributionSelector.reset(context, dim=1, name=Distribution.BERNOULLI.name)
            return

        ObjectTargeter.setup_from_config(config["target"], context)
        SimplifiedDistributionSelector.setup_from_config(config["distribution"], context, dim=1)

class ScalarPropertyDrawer(PipeSchema):

    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        dim = AxisTarget.get_selected_axis_dimension(context.scene)
        dic = {
            "dimension": dim,
            "axis": AxisTarget.extract_data(context),
            wsk.OFFSET.value: OffsetMode.extract_data(context),
            "target": ObjectTargeter.extract_data(context),
            "distribution": NodeDistributionSelector.extract_data(context, dim=dim)
        }
        return dic

    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        if not config:
            ObjectTargeter.reset(context)
            NodeDistributionSelector.reset(context)
            OffsetMode.reset(context)
            AxisTarget.reset(context)
        else:
            dimension = config["dimension"]
            AxisTarget.setup_from_config(config["axis"], context)
            ObjectTargeter.setup_from_config(config["target"], context)
            OffsetMode.setup_from_config(config[wsk.OFFSET.value], context)
            NodeDistributionSelector.setup_from_config(config["distribution"], context, dim=dimension)


@PipeSchemaRegistry.register(PipeNames.SCALE.value)
class ScaleSchema(ScalarPropertyDrawer):
    pass


@PipeSchemaRegistry.register(PipeNames.ROTATION.value)
class RotationSchema(ScalarPropertyDrawer):
    pass


@PipeSchemaRegistry.register(PipeNames.POSITION.value)
class PositionSchema(ScalarPropertyDrawer):
    pass

@PipeSchemaRegistry.register(PipeNames.MOVE.value)
class MoveSchema(PipeSchema):

    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        dic = {
            wsk.OBJECT.value: ObjectTargeter.extract_data(context),
            wsk.POSITION.value: PositionListSelector.extract_data(context)
        }
        return dic

    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        if not config:
            ObjectTargeter.reset(context)
            PositionListSelector.reset(context)
        else:
            ObjectTargeter.setup_from_config(config["target"], context)
            PositionListSelector.setup_from_config(config["positions"], context)

@PipeSchemaRegistry.register(PipeNames.TEXTURE.value)
class TextureSchema(PipeSchema):

    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        dic = {
            "node": ImageTextureTargeter.extract_data(context),
            "textures": PathListSelector.extract_data(context)
        }
        return dic

    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        if not config:
            ImageTextureTargeter.reset(context)
            PathListSelector.reset(context)
        else:
            ImageTextureTargeter.setup_from_config(config["node"], context)
            PathListSelector.setup_from_config(config["textures"], context)

@PipeSchemaRegistry.register(PipeNames.MATERIAL.value)
class MaterialSchema(PipeSchema):

    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        dic = {
            "target": ObjectTargeter.extract_data(context),
            "materials": MaterialSelector.extract_data(context)
        }
        return dic

    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        if not config:
            ObjectTargeter.reset(context)
            MaterialSelector.reset(context)
        else:
            ObjectTargeter.setup_from_config(config["target"], context)
            MaterialSelector.setup_from_config(config["materials"], context)

class MaterialSimplePropertySchema(PipeSchema):

    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        if not config:
            MaterialSelector.reset(context)
            OffsetMode.reset(context)
            NodeDistributionSelector.reset(context)
        else:
            NodeDistributionSelector.setup_from_config(config["distribution"], context, dim=1)
            MaterialSelector.setup_from_config(config["materials"], context)
            OffsetMode.setup_from_config(config[wsk.OFFSET.value], context)

    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        dic = {
            "distribution": NodeDistributionSelector.extract_data(context, dim=1),
            "materials": MaterialSelector.extract_data(context),
            wsk.OFFSET.value: OffsetMode.extract_data(context)
        }
        return dic


@PipeSchemaRegistry.register(PipeNames.METALLIC.value)
class MetallicSchema(MaterialSimplePropertySchema):
    pass

@PipeSchemaRegistry.register(PipeNames.ROUGHNESS.value)
class RoughnessSchema(MaterialSimplePropertySchema):
    pass

@PipeSchemaRegistry.register(PipeNames.INTENSITY.value)
class RandomizeNodeIntensityOperation(MaterialSimplePropertySchema):

    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        if not config:
            ValueTargeter.reset(context)
            NodeDistributionSelector.reset(context)
            OffsetMode.reset(context)
        else:
            OffsetMode.setup_from_config(config[wsk.OFFSET.value], context)
            ValueTargeter.setup_from_config(config["value"], context)
            NodeDistributionSelector.setup_from_config(config["distribution"], context, dim=1)

    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        dic = {
            wsk.VALUE.value: ValueTargeter.extract_data(context),
            "distribution": NodeDistributionSelector.extract_data(context, dim=1),
            wsk.OFFSET.value: OffsetMode.extract_data(context)
        }
        return dic

@PipeSchemaRegistry.register(PipeNames.BEZIER_LOCK.value)
class BezierLockCameraOperation(PipeSchema):

    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        """ """
        conditional = ConditionalWidget(ObjectTargeter)
        dic = {
            wsk.TYPED_OBJ.value: TypedObjectTargeter.extract_data(context),
            wsk.OBJECT.value: conditional.extract_data(context),
        }
        return dic

    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        """ """
        conditional = ConditionalWidget(ObjectTargeter)
        if not config:
            conditional.reset(context)
            TypedObjectTargeter.reset(context)
        else:
            conditional.setup_from_config(config[wsk.OBJECT.value], context)
            TypedObjectTargeter.setup_from_config(config[wsk.TYPED_OBJ.value], context )


@PipeSchemaRegistry.register(PipeNames.LINE.value)
class MoveAlongLineOperation(PipeSchema):

    @staticmethod
    def extract_config_from_ui(context, operation) -> dict:
        dic = {
            wsk.TYPED_OBJ.value: TypedObjectTargeter.extract_data(context),
            wsk.OBJECT.value: ObjectTargeter.extract_data(context),
        }
        return dic

    @staticmethod
    def apply_config_to_ui(context, operation, config) -> None:
        if not config:
            ObjectTargeter.reset(context)
            TypedObjectTargeter.reset(context)
        else:
            ObjectTargeter.setup_from_config(config[wsk.OBJECT.value], context)
            TypedObjectTargeter.setup_from_config(config[wsk.TYPED_OBJ.value], context)
