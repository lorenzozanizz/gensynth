""" A module containing the interface for the extractor, which is the interface designed
to extract and pack geometry data for objects and entities from the scene. Geometry is unified
into a single Label interface.

Classes: Extractor
"""


from abc import abstractmethod, ABCMeta
from typing import Any, Dict, Callable
from collections.abc import Iterable

from .data_structure import *

class Extractor(metaclass=ABCMeta):
    """
    The main interface for geometry extractors from the render scene, which use ray casting
    inside the camera frustum to generate labels, grouping points reached by rays and imputing them
    to objects and entities. Different extractors may extract different geometries in general.  """

    @abstractmethod
    def extract(self,
            visible_objects,
            classifier,
            entity_data,
            camera,
            estimate_visibility: bool = True, **kwargs
        ) -> LabelData:
        """ Extract the geometry of the identified objects and label from the scene, the data is
        then packed into LabelData objects which are iterables over a list of labels including geometry data,
        class data.

        Note: LabelData is not specific to the format, but different formats may decide to employ
        different extractors to reduce the computational burden of finding the geometry from the scene
        :return:
        """
        pass

    @abstractmethod
    def get_estimated_visibility(self) -> dict[ str | Any, float]:
        """ Get the estimated visibility for entities and objects """
        pass

    @abstractmethod
    def get_visible_entities(self) -> Iterable[Any]:
        """ Get the entities which are visible in the scene, e.g. those which are
        reachable by ray-casting inside the camera frustum.

        :returns: An iterable over the visible Blender objects
        """
        pass

    def get_labeling_time(self) -> float:
        """ Get the time it took to compute the boxes and the visible objects """
        pass

    def get_visible_objects(self) -> Iterable[Any]:
        """ Get the visible objects """
        pass

    def map_boxes(self, conv_func: Callable = None) -> Iterable[Any]:
        """ Get the camera centered bounding boxes """
        pass

    def get_bbox_objects(self) -> Dict:
        """ Get the mappings from object to bounding boxes """
        pass

    def get_bbox_entities(self) -> Dict:
        """ Get the mappings from object to bounding boxes """
        pass

    @staticmethod
    def ray_casting_needs() -> dict[str, Any]:
        return {}

