from typing import Iterable, Any, Union, Callable

import bpy

from .. import Extractor, LabelData
from ..class_engine import ClassificationEngine
from ...utils.timer import TimingContext

from ..ray_casting import (union_bounding_boxes, compute_camera_space_boxes, get_minimal_bounding_box_fast,
                           estimate_visibility_3d, compute_bbox_area, compute_area_ratio)
from ..class_engine import ClassificationEngine

from .extractor import Extractor
from .data_structure import *

class PixelMapExtractor(Extractor):

    def __init__(self, context):
        self.ctx = context

        self.timings: dict[str, float] = dict()
        self.visible_objects = dict()
        self.visible_entities = dict()
        self.estimated_visibility = dict()

        # Per pixel data map. This will be lazily initialized as a numpy array with required
        # pixel information.
        self.data_map = None

    def extract(self,
        visible_objects: dict[Any, list],
        classifier: ClassificationEngine,
        entity_data,
        camera,
        estimate_visibility: bool = True, **kwargs
    ) -> LabelData:
        """

        :param visible_objects:
        :param classifier:
        :param entity_data:
        :param camera:
        :param estimate_visibility:
        :param kwargs:
        :return:
        """
        ret_data = LabelData()

        if self.data_map is None:

            pass
        else:
            # just a quick check, ensure the dimensions are still the same, just as a
            # sanity check.
            if img := bpy.data.images.get(self.path):
                bpy.data.images.remove(img)
            elif img := bpy.data.images.get(self._preview_name):
                bpy.data.images.remove(img)
            bpy.ops.image.open(filepath=self.path)

        with (TimingContext(self.timings, 'labeling')):
            pass

        return ret_data

    def get_estimated_visibility(self) -> dict[Union[str, Any], float]:
        """ Get the estimated visibility for entities and objects """
        return self.estimated_visibility

    def get_visible_entities(self):
        return self.visible_entities.keys()

    def get_labeling_time(self) -> float:
        """ Get the time it took to compute the boxes and the visible objects """
        return self.timings['labeling']

    def get_visible_objects(self) -> Iterable[Any]:
        """ Get the visible objects """
        return self.visible_objects.keys()

    def map_boxes(self, conv_func: Callable = None) -> Iterable[Any]:
        """ Get the camera centered bounding boxes """
        if not conv_func:
            return self.visible_objects.values()
        else:
            return (conv_func(bbox) for bbox in self.visible_objects.values())

    def get_bbox_objects(self) -> dict:
        """ Get the mappings from object to bounding boxes """
        return self.visible_objects

    def get_bbox_entities(self) -> dict:
        """ Get the mappings from object to bounding boxes """
        return self.visible_entities

    def ray_casting_needs(self):
        pass