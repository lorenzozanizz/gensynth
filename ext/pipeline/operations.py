"""



"""

from .operation_registry import OperationRegistry
from .context import *

from ..constants import PipeNames, WidgetSerializationKeys
from ..utils.logger import UniqueLogger
from ..distribution.computation import SamplerCompiler, Distribution
from ..distribution.bezier import BezierDistribution, BezierCurve

from typing import Any, List, Tuple
from abc import ABCMeta, abstractmethod

import bpy

wsk = WidgetSerializationKeys

class PipelineOperation(DoubleFramedPipe, metaclass=ABCMeta):
    """Base class for all pipeline operations."""

    operation_type: str  # "randomize_position", "randomize_rotation", etc.

    @abstractmethod
    def compile(self, context, config: dict):
        """

        :param config:
        :return:
        """
        pass

    @abstractmethod
    def execute(self, context):
        """

        :param context:
        :return:
        """
        pass

class AxisSetMask:

    def __init__(self, config: dict[str, Any]):
        self.dimensions = config[wsk.DIMENSION.value]
        self.x = config[wsk.AXIS_RANDOMIZE_PREFIX_X.value]
        self.y = config[wsk.AXIS_RANDOMIZE_PREFIX_Y.value]
        self.z = config[wsk.AXIS_RANDOMIZE_PREFIX_Z.value]

    def dimensions(self):
        return self.dimensions

    def assign(self, vector_attribute: Any, value: Any):
        """

        :param vector_attribute:
        :param value:
        :return:
        """
        axes = [ax for ax in ['x', 'y', 'z'] if getattr(self, ax)]
        for axis, val in zip(axes, value):
            setattr(vector_attribute, axis, val)

    def increment(self, vector_attribute: Any, value: Any):
        """

        :param vector_attribute:
        :param value:
        :return:
        """
        UniqueLogger.quick_log("Value is: " + value.__str__())
        idx = 0
        if self.x:
            vector_attribute.x += value[idx]
            idx += 1
        if self.y:
            vector_attribute.y += value[idx]
            idx += 1
        if self.z:
            vector_attribute.z += value[idx]
        return


class NumericRandomOperation(PipelineOperation, metaclass=ABCMeta):
    """

    """

    def __init__(self):

        self.offset_mode    = None
        self.dimension      = None
        self.distribution   = None
        self.axis           = None
        self.targets        = None

    def compile(self, context, config: dict):
        """

        :param context:
        :param config:
        :return:
        """

        # Simply extract the value from the config
        self.dimension = int(config[wsk.DIMENSION.value])
        # The distribution will be compiled (either a node or a preset distribution)
        self.distribution = SamplerCompiler.compile(config[wsk.NODE_DISTRIBUTION.value], self.dimension)

        # Extract the axis and the targets. the axis object is a simple interface for
        # assigning on different dimensions
        self.axis = AxisSetMask(config[wsk.AXIS.value])
        self.targets = config[wsk.OBJECT.value][wsk.OBJECT_NAMES.value]

        # This is a boolean value
        self.offset_mode = config[wsk.OFFSET.value][wsk.OFFSET_MODE.value]

    @abstractmethod
    def get_context(self):
        """

        :return:
        """
        pass

    def get_global_context(self):
        return self.get_context()

    def get_frame_context(self):
        """

        :return:
        """
        if self.offset_mode:
            return self.get_context()
        else:
            return None

@OperationRegistry.register(PipeNames.SCALE.value)
class RandomizeScaleOperation(NumericRandomOperation):

    def execute(self, context):
        result = self.distribution.sample()
        for item in self.targets:
            obj = bpy.data.objects[item]
            if self.offset_mode:
                self.axis.increment(obj.scale, result)
            else:
                self.axis.assign(obj.scale, result)

    class ScaleContext(ContextManager):

        def __init__(self, items):
            self.items = items
            self.scales = []

        def __enter__(self):
            # Clear to avoid polluting and damaging the values
            self.scales.clear()
            for item in self.items:
                self.scales.append(tuple(bpy.data.objects[item].scale))

        def __exit__(self, exc_type, exc_val, exc_tb):
            for item, scale in zip(self.items, self.scales):
                bpy.data.objects[item].scale = scale

    def get_context(self):
        return RandomizeScaleOperation.ScaleContext(self.targets)


@OperationRegistry.register(PipeNames.INTENSITY.value)
class RandomizeIntensityOperation(PipelineOperation):

    def compile(self, context, config: dict):
        # Note: the value is assumed to be scalar!... for now
        # The distribution will be compiled (either a node or a preset distribution)
        self.distribution = SamplerCompiler.compile(config[wsk.NODE_DISTRIBUTION.value], dim=1)
        self.targets = config[wsk.OBJECT.value][wsk.OBJECT_NAMES.value]
        # This is a boolean value
        self.offset_mode = config[wsk.OFFSET.value][wsk.OFFSET_MODE.value]

    def execute(self, context):
        pass


    class PropertyValueContext:

        def __enter__(self):
            pass

        def __exit__(self, exc_type, exc_val, exc_tb):
            pass

    def get_global_context(self):
        pass

    def get_frame_context(self):
        pass


@OperationRegistry.register(PipeNames.POSITION.value)
class RandomizePositionOperation(NumericRandomOperation):

    def execute(self, context):
        result = self.distribution.sample()
        for item in self.targets:
            obj = bpy.data.objects[item]
            if self.offset_mode:
                self.axis.increment(obj.location, result)
            else:
                self.axis.assign(obj.location, result)

    class PositionContext(ContextManager):

        def __init__(self, items):
            self.items = items
            self.location = []

        def __enter__(self):
            # Clear to avoid polluting and damaging the values
            self.location.clear()
            for item in self.items:
                self.location.append(tuple(bpy.data.objects[item].location))

        def __exit__(self, exc_type, exc_val, exc_tb):
            for item, location in zip(self.items, self.location):
                bpy.data.objects[item].location = location

    def get_context(self):
        return RandomizePositionOperation.PositionContext(self.targets)


@OperationRegistry.register(PipeNames.MOVE.value)
class RandomizeMoveOperation(PipelineOperation):

    def __init__(self):

        self.distribution   = None
        self.targets        = None
        self.positions      = None

    def get_frame_context(self):
        return RandomizePositionOperation.PositionContext(self.targets)

    def get_global_context(self):
        return RandomizePositionOperation.PositionContext(self.targets)

    def compile(self, context, config: dict):
        self.targets = config[wsk.OBJECT.value][wsk.OBJECT_NAMES.value]
        # The distribution will be compiled ( a discrete uniform )
        self.positions = config[wsk.POSITION.value][wsk.POSITION_LIST.value]
        self.distribution = SamplerCompiler.make_distribution(
        Distribution.CATEGORICAL_UNIFORM.value, 1)

    def execute(self, context):
        # One dimensional result, a discrete uniform variable
        result = min(max(0, self.distribution.sample()[0]), len(self.targets))

        # Extract a position randomly:
        position = self.positions[result]
        for item in self.targets:
            obj = bpy.data.objects[item]
            obj.location = position


@OperationRegistry.register(PipeNames.ROTATION.value)
class RandomizeRotationOperation(NumericRandomOperation):

    def execute(self, context):
        result = self.distribution.sample()
        for item in self.targets:
            obj = bpy.data.objects[item]
            if self.offset_mode:
                self.axis.increment(obj.rotation_euler, result)
            else:
                self.axis.assign(obj.rotation_euler, result)

    class RotationContext(ContextManager):

        def __init__(self, items):
            self.items = items
            self.rotations = []

        def __enter__(self):
            # Clear to avoid polluting and damaging the values
            self.rotations.clear()
            for item in self.items:
                self.rotations.append(tuple(bpy.data.objects[item].rotation_euler))

        def __exit__(self, exc_type, exc_val, exc_tb):
            for item, rot in zip(self.items, self.rotations):
                bpy.data.objects[item].rotation_euler  = rot

    def get_context(self):
        return RandomizeRotationOperation.RotationContext(self.targets)


@OperationRegistry.register(PipeNames.VISIBILITY.value)
class RandomizeVisibilityOperation(PipelineOperation):

    def get_global_context(self):
        return RandomizeVisibilityOperation.VisibilityContext(self.targets)

    def get_frame_context(self):
        return RandomizeVisibilityOperation.VisibilityContext(self.targets)

    def compile(self, context, config: dict):
        self.targets = config[wsk.OBJECT.value][wsk.OBJECT_NAMES.value]
        # The distribution will be compiled ( a bernoulli )
        self.distribution = SamplerCompiler.compile(config[wsk.NODE_DISTRIBUTION.value], dim=1)

    def __init__(self):

        self.distribution   = None
        self.targets        = None

    def execute(self, context):
        # One dimensional result, a bernoulli

        result = self.distribution.sample()[0]
        for item in self.targets:
            obj = bpy.data.objects[item]
            if result > 0.5:
                self.hide(obj)

    @staticmethod
    def hide(obj) -> None:
        obj.hide_render = True
        obj.visible_camera = False
        obj.visible_diffuse = False
        obj.visible_glossy = False
        obj.visible_shadow = False
        obj.visible_transmission = False
        obj.visible_volume_scatter = False
        obj.hide_set(True)

    class VisibilityContext(ContextManager):

        def __init__(self, items):
            self.items = items
            # We actually need to change multiple attributes per object: not only are we
            # interested in the general render visibility, but also to the transparency to
            # rays and other computations that are required for labeling in general.
            self.visibilities: List[tuple] = []

        def __enter__(self):
            # Clear to avoid polluting and damaging the values
            self.visibilities.clear()
            for item in self.items:
                obj = bpy.data.objects[item]
                self.visibilities.append(self.extract(obj))

        def __exit__(self, exc_type, exc_val, exc_tb):
            for item, state in zip(self.items, self.visibilities):
                obj = bpy.data.objects[item]
                self.restore(obj, state)

        @staticmethod
        def restore(obj, state) -> None:
            obj.hide_render = state[0]
            obj.visible_camera = state[1]
            obj.visible_diffuse = state[2]
            obj.visible_glossy = state[3]
            obj.visible_shadow = state[4]
            obj.visible_transmission = state[5]
            obj.visible_volume_scatter = state[6]
            obj.hide_set( state[7] )

        @staticmethod
        def extract(obj) -> Tuple:
            return (
                obj.hide_render, obj.visible_camera, obj.visible_diffuse, obj.visible_glossy,
                obj.visible_shadow, obj.visible_transmission, obj.visible_volume_scatter, obj.hide_get()
            )

@OperationRegistry.register(PipeNames.LINE.value)
class MoveLineOperation(PipelineOperation):

    def compile(self, context, config: dict):
        pass

    def execute(self, context):
        pass

    def get_frame_context(self):
        pass

    def get_global_context(self):
        pass


@OperationRegistry.register(PipeNames.FOCAL_LEN.value)
class FocalLengthOperation(PipelineOperation):
    def compile(self, context, config: dict):
        pass

    def execute(self, context):
        pass

    def get_global_context(self):
        pass

    def get_frame_context(self):
        pass


@OperationRegistry.register(PipeNames.BEZIER_LOCK.value)
class BezierLockOperation(PipelineOperation):

    def __init__(self):
        self.target_camera = None
        self.bezier_distribution = None

        self.enable_lock = False
        self.lock_target = None

    def compile(self, context, config: dict):
        self.target_camera = context.scene.camera

        self.enable_lock = config[wsk.OBJECT.value][wsk.ENABLED.value]

        curve = config[wsk.TYPED_OBJ.value][wsk.TYPED_OBJ_NAME.value]
        curve_obj = bpy.data.objects[curve]

        if self.enable_lock:
            obj_names = config[wsk.OBJECT.value][wsk.OBJECT_NAMES.value]
            first_obj = obj_names[0]
            self.lock_target = bpy.data.objects[first_obj]

        self.bezier_distribution = BezierDistribution(
            BezierCurve.from_blender_curve(curve_obj),
        )

    def execute(self, context):

        point = self.bezier_distribution.sample()
        self.target_camera.location = point


    def get_global_context(self):
        return BezierLockOperation.BezierLockContext(self.target_camera, self.lock_target, do_lock=self.enable_lock)

    def get_frame_context(self):
        return None

    class BezierLockContext(ContextManager):

        def __init__(self, target, virtual_obj, do_lock: bool):
            self.target = target
            self.constraint = None

            self.do_lock = do_lock
            self.virtual_object = virtual_obj
            self.initial_camera_pos = None
            self.initial_camera_rot = None

        def __enter__(self):
            self.initial_camera_pos = self.target.location
            self.initial_camera_rot = self.target.rotation_euler
            if self.do_lock:
                self.constraint = self.target.constraints.new(type='TRACK_TO')
                self.constraint.target = self.virtual_object

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.do_lock:
                self.target.constraints.remove(self.constraint)
            self.target.location = self.initial_camera_pos
            self.target.rotation_euler = self.initial_camera_rot

@OperationRegistry.register(PipeNames.LINE.value)
class MoveAlongLineOperation(PipelineOperation):

    def __init__(self):
        self.targets = None
        self.bezier_distribution = None

    def compile(self, context, config: dict):
        self.targets = config[wsk.OBJECT.value][wsk.OBJECT_NAMES.value]
        curve = config[wsk.TYPED_OBJ.value][wsk.TYPED_OBJ_NAME.value]
        curve_obj = bpy.data.objects[curve]

        self.bezier_distribution = BezierDistribution(
            BezierCurve.from_blender_curve(curve_obj),
        )

    def execute(self, context):
        point = self.bezier_distribution.sample()
        for item in self.targets:
            obj = bpy.data.objects[item]
            obj.location = point

    def get_global_context(self):
        return RandomizePositionOperation.PositionContext(self.targets)

    def get_frame_context(self):
        return RandomizePositionOperation.PositionContext(self.targets)

