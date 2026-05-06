from .operations import PipelineOperation
from ..constants import PipeNames, WidgetSerializationKeys, DISTRO_EDITOR_NAME

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Union, Optional

import bpy

from ..utils.logger import UniqueLogger

wsk = WidgetSerializationKeys

class PipeValidator(metaclass=ABCMeta):
    """

    """
    @staticmethod
    @abstractmethod
    def validate(pipe: PipelineOperation, config: dict) -> bool:
        pass


class ValidatorRegistry:
    """Registry of all available operations."""

    _operations = {}

    @classmethod
    def register(cls, op_type: str):
        def decorator(drawer_cls):
            cls._operations[op_type] = drawer_cls
            return drawer_cls
        return decorator

    @classmethod
    def get(cls, operation_type: str) -> Optional[PipeValidator]:
        """Get an operation instance by type."""
        if operation_type not in cls._operations:
            return None
        return cls._operations[operation_type]()

    @classmethod
    def get_all_types(cls) -> list:
        """Get all available operation types."""
        return list(cls._operations.keys())

class NumericPropertyValidator(PipeValidator):

    @staticmethod
    def validate(pipe: PipelineOperation, config: dict) -> bool:
        axi_ok = AxisTargetValidator.validate(config[wsk.AXIS.value])
        obj_ok = ObjectTargeterValidator.validate(config[wsk.OBJECT.value])
        dis_ok = NodeDistributionSelectorValidator.validate(config[wsk.NODE.value])
        return axi_ok and obj_ok and dis_ok

@ValidatorRegistry.register(PipeNames.SCALE.value)
class ScaleValidator(NumericPropertyValidator):
    pass

@ValidatorRegistry.register(PipeNames.POSITION.value)
class PositionValidator(NumericPropertyValidator):
    pass

@ValidatorRegistry.register(PipeNames.ROTATION.value)
class RotationValidator(NumericPropertyValidator):
    pass

@ValidatorRegistry.register(PipeNames.MOVE.value)
class MoveValidator(PipeValidator):

    @staticmethod
    def validate(pipe: PipelineOperation,  config: dict) -> bool:
        obj_ok = ObjectTargeterValidator.validate(config[wsk.OBJECT.value])
        pos_ok = PositionListSelectorValidator.validate(config[wsk.POSITION.value])
        return obj_ok and pos_ok

@ValidatorRegistry.register(PipeNames.VISIBILITY.value)
class VisibilityValidator(PipeValidator):

    @staticmethod
    def validate(pipe: PipelineOperation,  config: dict) -> bool:
        obj_ok = ObjectTargeterValidator.validate(config[wsk.OBJECT.value])
        dis_ok = SimplifiedDistributionSelectorValidator.validate(config[wsk.SIMPLE.value])
        return obj_ok and dis_ok


@ValidatorRegistry.register(PipeNames.MATERIAL.value)
class MaterialValidator(PipeValidator):

    @staticmethod
    def validate(pipe: PipelineOperation, config: dict) -> bool:
        obj_ok = ObjectTargeterValidator.validate(config[wsk.OBJECT.value])
        mat_ok = MaterialSelectorValidator.validate(config[wsk.MATERIAL.value])
        return mat_ok and obj_ok

@ValidatorRegistry.register(PipeNames.TEXTURE.value)
class TextureValidator(PipeValidator):

    @staticmethod
    def validate(pipe: PipelineOperation, config: dict) -> bool:
        return False


@ValidatorRegistry.register(PipeNames.INTENSITY.value)
class IntensityValidator(PipeValidator):

    @staticmethod
    def validate(pipe: PipelineOperation, config: dict) -> bool:
        # Just ensure that the node does exist and ensure the distribution is OK.
        val_ok = ValueTargeterValidator.validate(partial_config=config[wsk.VALUE.value])
        dis_ok = NodeDistributionSelectorValidator.validate(partial_config=config[wsk.NODE.value])
        return val_ok and dis_ok

@ValidatorRegistry.register(PipeNames.METALLIC.value)
class MetallicValidator(PipeValidator):

    @staticmethod
    def validate(pipe: PipelineOperation, config: dict) -> bool:
        return False


@ValidatorRegistry.register(PipeNames.ROUGHNESS.value)
class RoughnessValidator(PipeValidator):

    @staticmethod
    def validate(pipe: PipelineOperation, config: dict) -> bool:
        return False


@ValidatorRegistry.register(PipeNames.BEZIER_LOCK.value)
class CameraBezierLockValidator(PipeValidator):

    @staticmethod
    def validate(pipe: PipelineOperation, config: dict) -> bool:

        obj_ok = TypedObjectValidator.validate(partial_config=config[wsk.TYPED_OBJ.value])
        conditional = ConditionalValidator(ObjectTargeterValidator)
        pos_ok = conditional.validate(partial_config=config[wsk.OBJECT.value])

        return obj_ok and pos_ok

@ValidatorRegistry.register(PipeNames.LINE.value)
class MoveAlongLineValidator(PipeValidator):


    @staticmethod
    def validate(pipe: PipelineOperation, config: dict) -> bool:

        obj_ok = TypedObjectValidator.validate(partial_config=config[wsk.TYPED_OBJ.value])
        tar_ok = ObjectTargeterValidator.validate(partial_config=config[wsk.OBJECT.value])

        return obj_ok and tar_ok


class WidgetValidator(metaclass=ABCMeta):
    """

    """
    @staticmethod
    @abstractmethod
    def validate(partial_config: dict) -> bool:
        pass


class ConditionalValidator(WidgetValidator):

    def __init__(self, target_cls):
        self.target = target_cls

    def validate(self, partial_config: dict) -> bool:
        UniqueLogger.quick_log("Validate conditional" + partial_config.__str__())
        is_enabled = partial_config[wsk.ENABLED.value]
        if is_enabled:
            return self.target.validate(partial_config)
        else:
            return True

class TypedObjectValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        obj = partial_config[wsk.TYPED_OBJ_NAME.value]
        # The pipe is not OK if it has no target. "OK" means useful and working.
        if not obj:
            return False
        try:
            obj = bpy.data.objects[obj]
        except KeyError:
            return False
        if not obj:
            return False
        return True


class AxisTargetValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        """

        :param partial_config:
        :return:
        """
        do_x = partial_config[wsk.AXIS_RANDOMIZE_PREFIX_X.value]
        do_y = partial_config[wsk.AXIS_RANDOMIZE_PREFIX_Y.value]
        do_z = partial_config[wsk.AXIS_RANDOMIZE_PREFIX_Z.value]
        return do_x or do_y or do_z


#
class ObjectTargeterValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        # We simply ensure that all the objects do exist in the bpy data.
        objects = partial_config[wsk.OBJECT_NAMES.value]
        # The pipe is noto OK if it has no target. "OK" means useful and working.
        if not objects:
            return False
        for name in objects:
            name: str
            # Note that this searches for objects in all the different scenes of the active
            # file, not just the current context.
            try:
                obj = bpy.data.objects[name]
            except KeyError:
                return False
            if not obj:
                return False
        return True

#
class ImageTextureTargeterValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        """

        :param partial_config:
        :return:
        """

        # Ensure that all specified paths exist and are properly read accessible.
        pass


#
class PathListSelectorValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        pass


#
class NodeDistributionSelectorValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:

        use_tree = partial_config['use_tree']
        if use_tree:
            name = partial_config['distribution']
            tree = next(
                (ng for ng in bpy.data.node_groups
                 if ng.bl_idname == DISTRO_EDITOR_NAME and ng.name == name),
                None
            )
            if tree is None:
                return False
        else:
            preset = partial_config['preset']
            if preset.lower() == "None":
                return False
        return True

#
class SimplifiedDistributionSelectorValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        """ Pretty much any distribution is correct by design, as the numeric attributes
        have boundaries which prevent mathematically illegal values. """
        dis_name = partial_config[wsk.SIMPLE_PRESET_NAME.value]
        if not dis_name or dis_name.lower() == "none":
            return False
        else:
            return True

#
class PositionListSelectorValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        positions = partial_config[wsk.POSITION_LIST.value]
        return len(positions) != 0

#
class MaterialSelectorValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        """

        :param partial_config:
        :return:
        """

        # We simply ensure that all the materials listed do exist in the bpy data.
        materials = partial_config[wsk.MATERIAL_LIST.value]
        if not materials:
            return False
        for mat in materials:
            mat: str
            try:
                tree = bpy.data.materials.get(mat)
            except KeyError:
                return False
            if not tree:
                return False
        return True


#
class PropertyTargeterValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        pass


class ValueTargeterValidator(WidgetValidator):

    @staticmethod
    def validate(partial_config: dict) -> bool:
        pass

