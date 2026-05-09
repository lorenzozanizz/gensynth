from typing import Union

from ..operators.names import Labels
from ..distribution.computation import Distribution
from ..distribution.nodes import get_tree_dimensionality
from ..constants import WidgetSerializationKeys
from ..utils.logger import UniqueLogger

from abc import ABC, abstractmethod

import bpy
from bpy.props import StringProperty, FloatVectorProperty, PointerProperty
from bpy.types import UIList, PropertyGroup, Material

wsk = WidgetSerializationKeys

class TextureNodeProperty(PropertyGroup):
    """ A property to contain the name of a material and a texture. """
    mat_name: StringProperty(name="Material")                   # type: ignore
    node_label: StringProperty(name="Label")                    # type: ignore

class ValueNodeProperty(PropertyGroup):
    """ A property to contain the name of a material and a value node. """
    mat_name: StringProperty(name="Material")                   # type: ignore
    node_label: StringProperty(name="Label")                    # type: ignore

class ObjectName(PropertyGroup):
    """ Single object name. """
    obj_name: StringProperty(name="Name")                       # type: ignore

class ImagePath(PropertyGroup):
    """Single image file path"""
    path: StringProperty(name="Path", subtype='FILE_PATH')      # type: ignore


class PathsUIList(UIList):
    """UIList for individual image paths"""

    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_propname, index):
        row = layout.row(align=True)
        sub = row.row(align=True)
        sub.scale_x = 0.3
        sub.label(text=f"{index + 1}")
        row.label(text=item.path, icon='IMAGE_DATA')


class ObjectPosition(PropertyGroup):
    """Single image file path"""
    pos: FloatVectorProperty(name="Position", size=3, default=(0, 0, 0))  # type: ignore


class PositionsUIList(UIList):
    """UIList for individual image paths"""

    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_propname, index):
        row = layout.row(align=True)
        sub = row.row(align=True)
        sub.scale_x = 0.3
        sub.label(text=f"{index + 1}")
        row.prop(item, "pos", text="Position", emboss=False)


class MaterialListItem(PropertyGroup):
    """Single material in list"""
    material: PointerProperty(  # type: ignore
        type=Material,
        name="Material"
    )


class MaterialUIList(UIList):
    """UIList for materials"""

    @staticmethod
    def draw_item(self, _context, layout, _data, item, _icon, _active_data, _active_propname, index):
        mat = item.material

        if mat:
            row = layout.row(align=True)
            sub = row.row()
            sub.label(text=f"{index + 1}")
            sub.scale_x = 0.3
            row.label(text=mat.name, icon='MATERIAL')
        else:
            row = layout.row()
            row.label(text="(Empty)")

class DistributionTreeList(UIList):

    def draw_item(self, _context, layout, _data, item, icon, active_data, active_propname, index):
        """Draw each distribution tree."""

        distribution_item = item

        row = layout.row(align=True)
        # Middle: Tree name with icon, also allows the user to change the name from the item
        row.prop(distribution_item, "Name", icon='NODETREE', emboss=False)

        # Right: Dimensionality
        if distribution_item.node_tree:
            dims = get_tree_dimensionality(distribution_item.node_tree)
            row.label(text=f"{dims}D", icon='EMPTY_ARROWS')
        else:
            # Tree pointer is broken
            row.label(text="Broken Tree Link", icon='ERROR')



class EditorWidget(ABC):
    """

    """

    @staticmethod
    @abstractmethod
    def draw(layout, context) -> None:
        """

        :param layout:
        :param context:
        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def extract_data(context) -> dict:
        """

        :return:
        """
        pass

    @staticmethod
    @abstractmethod
    def setup_from_config(config: dict, context) -> None:
        pass


    @staticmethod
    @abstractmethod
    def reset(context) -> None:
        pass
#

class OffsetMode(EditorWidget):

    @staticmethod
    def draw(layout, context) -> None:
        layout = layout
        scene = context.scene

        row = layout.row(align=True)
        row.prop(scene, "do_offset")

    @staticmethod
    def extract_data(context) -> dict:
        scene = context.scene
        return {
            wsk.OFFSET_MODE.value: scene.do_offset
        }

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        scene = context.scene
        scene.do_offset = config[wsk.OFFSET_MODE.value]

    @staticmethod
    def reset(context) -> None:
        scene = context.scene
        scene.do_offset = True


class AxisTarget(EditorWidget):

    @staticmethod
    def reset(context) -> None:
        scene = context.scene
        scene.randomize_x = False
        scene.randomize_y = False
        scene.randomize_z = False

    @staticmethod
    def draw(layout, context):
        layout = layout
        scene = context.scene

        # 3 checkboxes in a row, one for each dimension
        row = layout.row(align=True)
        row.label(text="Axis:")

        sub = row.row(align=True)
        # Shrink to 30% width to avoid cluttering the GUI
        sub.scale_x = 0.7
        sub.prop(scene, "randomize_x", text="X", toggle=True)
        sub.prop(scene, "randomize_y", text="Y", toggle=True)
        sub.prop(scene, "randomize_z", text="Z", toggle=True)
        row.separator()
        row.label(text=f"({AxisTarget.get_selected_axis_dimension(scene)} Dims.)")

    @staticmethod
    def extract_data(context) -> dict:
        scene = context.scene
        return {
            "randomize_x": scene.randomize_x,
            "randomize_y": scene.randomize_y,
            "randomize_z": scene.randomize_z,
            "dimension": AxisTarget.get_selected_axis_dimension(context.scene),
        }

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        scene = context.scene
        scene.randomize_x = config["randomize_x"]
        scene.randomize_y = config["randomize_y"]
        scene.randomize_z = config["randomize_z"]

    @staticmethod
    def get_selected_axis_dimension(scene):
        """

        :param scene:
        :return:
        """
        is_x = 1 if scene.randomize_x else 0
        is_y = 1 if scene.randomize_y else 0
        is_z = 1 if scene.randomize_z else 0
        return is_x + is_y + is_z
#

class ObjectTargeter(EditorWidget):

    @staticmethod
    def reset(context) -> None:
        scene = context.scene
        scene.targeted_objects_display.clear()

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        scene = context.scene
        scene.targeted_objects_display.clear()
        for name in config["names"]:
            nm = scene.targeted_objects_display.add()
            nm.obj_name = name

    @staticmethod
    def draw(layout, context):
        """

        :param layout:
        :param context:
        :return:
        """
        scene = context.scene
        box = layout.box().row()
        sub = box.row(align=True)
        sub.scale_x = 0.5
        sub.label(text="Target(s):")

        # Concatenate the captured names together to get a string representation of the capture objects.
        text_label = str([n_prop.obj_name for n_prop in scene.targeted_objects_display]) \
             if len(scene.targeted_objects_display) != 0 else "None"
        box.label(text=text_label, icon='OBJECT_DATA')
        box.operator(Labels.CAPTURE_OBJECTS.value, text="Capture Selected", icon='EYEDROPPER')
        view = box.operator(Labels.VIEW_TARGET_SELECTED.value, text="", icon='VIS_SEL_10')
        view.collection_attribute = 'targeted_objects_display'
        view.name_attribute = 'obj_name'

    @staticmethod
    def extract_data(context) -> dict:
        scene = context.scene
        return {
            "names": [name.obj_name for name in scene.targeted_objects_display]
        }

#
class ImageTextureTargeter(EditorWidget):

    @staticmethod
    def reset(context) -> None:
        scene = context.scene
        scene.targeted_texture_node.mat_name = ""
        scene.targeted_texture_node.node_label = ""

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        scene = context.scene
        scene.targeted_texture_node.mat_name = config["material"]
        scene.targeted_texture_node.node_label = config["label"]

    @staticmethod
    def extract_data(context) -> dict:
        scene = context.scene
        return {
            "material": scene.targeted_texture_node.mat_name,
            "label": scene.targeted_texture_node.node_label,
        }

    @staticmethod
    def draw(layout, context):
        """

        :param layout:
        :param context:
        :return:
        """
        scene = context.scene
        box = layout.box().row()
        box.label(text="Texture:")

        mat_prop = scene.targeted_texture_node
        text_label = f"{mat_prop.mat_name} > {mat_prop.node_label}" if (mat_prop.mat_name and mat_prop.node_label) else "None"
        box.label(text=text_label, icon='OBJECT_DATA')
        box.operator(Labels.CAPTURE_TEXTURE_NODE.value, text="Capture", icon='EYEDROPPER')

#
class PathListSelector(EditorWidget):

    @staticmethod
    def reset(context) -> None:
        scene = context.scene
        scene.image_paths.clear()
        scene.selected_image_path_index = 0

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        scene = context.scene
        scene.use_folder_mode = config["use_folder"]
        if scene.use_folder_mode:
            scene.image_folder = config["folder"]
        else:
            ls = scene.image_paths
            ls.clear()
            for file in config["files"]:
                fl = ls.add()
                fl.path = file

    @staticmethod
    def extract_data(context) -> dict:
        scene = context.scene
        ret = { "use_folder": scene.use_folder_mode }
        if scene.use_folder_mode:
            ret["folder"] = scene.image_folder
        else:
            ret["files"] = [
                file.path for file in scene.image_paths
            ]
        return ret

    @staticmethod
    def draw(layout, context):
        scene = context.scene
        # Toggle button
        layout.prop(scene, "use_folder_mode", text="Use Folder Mode")

        if scene.use_folder_mode:
            box = layout.box()
            box.label(text="Folder Selection")
            box.prop(scene, "image_folder", text="")

        else:
            box = layout.box()
            box.label(text="Individual Files")

            row = box.row()
            row.template_list(
                PathsUIList.__name__,
                "image_paths_list",
                scene, "image_paths",
                scene, "selected_image_path_index"
            )

            # +/- buttons
            col = row.column()
            col.operator(Labels.ADD_IMAGE_PATH_POOL.value, icon='ADD', text='')
            col.operator(Labels.REMOVE_IMAGE_PATH_POOL.value, icon='REMOVE', text='')

#
class NodeDistributionSelector(EditorWidget):

    @staticmethod
    def reset(context) -> None:

        # Initially, target the X axis. there is no need for this to have any preference.
        SimplifiedDistributionSelector.reset(context, dim=1, name=Distribution.UNIFORM.name)
        context.scene.selected_image_path_index = 0

    @staticmethod
    def setup_from_config(config: dict, context, dim: int = 0) -> None:
        scene = context.scene
        scene.use_distribution_tree = config["use_tree"]
        if scene.use_distribution_tree:
            # Load the selected user defined distribution
            distributions = scene.available_distributions
            index = next((idx for idx in range(len(distributions)) if
                         scene.available_distributions[idx].name == config["distribution"]), 0)
            scene.selected_distribution_index = index
        else:
            # Otherwise load the preset distribution
            SimplifiedDistributionSelector.setup_from_config(config, context, dim=dim)

    @staticmethod
    def extract_data(context, dim: int = 0) -> dict:
        scene = context.scene
        ret = { "use_tree": scene.use_distribution_tree }
        if scene.use_distribution_tree:
            distributions = scene.available_distributions
            selected = distributions[scene.selected_distribution_index]
            # Compile the distribution tree to a string
            ret["distribution"] = selected.name
        else:
            data = SimplifiedDistributionSelector.distribution_data(context, dim=dim)
            ret.update(data)
        return ret

    @staticmethod
    def draw(layout, context, dim: int = 0):
        """

        :param dim:
        :param layout:
        :param context:
        :return:
        """
        scene = context.scene
        layout.prop(scene, "use_distribution_tree")

        if scene.use_distribution_tree:
            box = layout.box()
            box.label(text="Saved Distributions")
            row = box.row()
            row.template_list(
                DistributionTreeList.__name__,
                "distribution_trees",
                scene, "available_distributions",  # Will populate this
                scene, "selected_distribution_index"
            )

            # Add/Remove buttons
            col = row.column()
            col.operator(Labels.ADD_DISTRIBUTION.value, icon='ADD', text='')
            col.operator(Labels.REMOVE_DISTRIBUTION.value, icon='REMOVE', text='')

            if len(scene.available_distributions) == 0:
                return
            # Error message space
            if scene.distribution_dimension_error:
                box.label(text="Dimension mismatch", icon='ERROR')
                box.label(text=scene.distribution_dimension_error)
            else:
                box.label(text="Valid distribution", icon='CHECKMARK')
        else:
            SimplifiedDistributionSelector.draw(layout, context, dim=dim)

#
class SimplifiedDistributionSelector(EditorWidget):

    # Keep this shorter!
    d_e = Distribution

    # A map which assigns the correct properties to each distribution. This
    # may reuse multiple times the same properties (e.g. probability 'p') and is to be used both for
    # serializing and drawing.
    _distribution_map = {
        d_e.UNIFORM.name: ['min', 'max'],
        d_e.MULTIVARIATE_UNIFORM.name: ['min_vec', 'max_vec'],
        d_e.BETA.name: ['alpha', 'beta', 'min', 'max'],
        d_e.GEOMETRIC.name: ['p'],
        d_e.BERNOULLI.name: ['p'],
        d_e.BINOMIAL.name: ['n', 'p'],
        d_e.GAUSSIAN.name: ['mean', 'std'],
        d_e.MULTIVARIATE_GAUSSIAN.name: ['mean_vec', 'cov_matrix'],
        d_e.MULTIVARIATE_ISOTROPIC_GAUSSIAN.name: ['mean_vec', 'variance'],
        d_e.CATEGORICAL_UNIFORM.name: ['n']
    }

    _vectors = frozenset({"mean_vec", "min_vec", "max_vec"})
    _value = frozenset({"p", "min", "max", "alpha", "beta", "n", "mean", "std"})

    # This prefix is applied to all property names, used for clarity
    _name_prefix = "dist_"

    @staticmethod
    def reset(context, dim: int = 0, name="") -> None:
        scene = context.scene
        if name:
            p_name = SimplifiedDistributionSelector.enum_name_from_dim(dim)
            setattr(scene, p_name, name.upper())
        for prop in SimplifiedDistributionSelector._vectors:
            name = SimplifiedDistributionSelector._name_prefix + prop
            setattr(scene, name, (0, 0, 0))
        for prop in SimplifiedDistributionSelector._value:
            name = SimplifiedDistributionSelector._name_prefix + prop
            setattr(scene, name, 0)
        for attr in ("do_discretize", "do_clamp"):
            setattr(scene, attr, False)
        scene.clamping_factors = (0, 0)

    @staticmethod
    def setup_from_config(config: dict, context, dim: int = 0) -> None:
        scene = context.scene
        for attr in ("do_discretize", "do_clamp", "clamping_factors"):
            setattr(scene, attr, config[attr])
        preset_name = config["preset"]
        params = config["parameters"]

        p_name = SimplifiedDistributionSelector.enum_name_from_dim(dim)
        setattr(scene, p_name, preset_name)

        properties = SimplifiedDistributionSelector._get_properties(dim, scene)
        for property_name in properties:
            extended_name = SimplifiedDistributionSelector._name_prefix + property_name
            setattr(scene, extended_name, params[property_name])

    @staticmethod
    def extract_data(context, dim: int = 0) -> dict:
        # If the user is calling Simplified... . extract_data, he is using the default.
        ret = { "use_tree": False }
        ret.update(SimplifiedDistributionSelector.distribution_data(context, dim=dim))
        return ret

    @staticmethod
    def distribution_data(context, dim = 0) -> dict:
        scene = context.scene
        p_name = SimplifiedDistributionSelector.enum_name_from_dim(dim)
        dist = (getattr(scene, p_name, "") or "").upper()
        return {
            "preset": dist,
            "do_discretize": scene.do_discretize,
            "do_clamp": scene.do_clamp,
            "clamping_factors": tuple(scene.clamping_factors),
            "parameters": SimplifiedDistributionSelector.extract_parameters(context, dim)
        }

    @staticmethod
    def extract_parameters(context, dim: int = 0) -> dict:

        # We extract the correct name for the enum property, then select all the interested
        # subproperties (e.g. those in the _distribution_map associated with the name.
        # Those properties are then serialized.
        scene = context.scene
        interested_properties = SimplifiedDistributionSelector._get_properties(dim, scene)

        ret = {}
        # Vector properties need to change with dimension.
        for property_name in interested_properties:
            extended_name = SimplifiedDistributionSelector._name_prefix + property_name
            if 'vec' in property_name:
                ret[property_name] = tuple(getattr(scene, extended_name))
            else:
                ret[property_name] = getattr(scene, extended_name)
        return ret

    @staticmethod
    def enum_name_from_dim(dim: int) -> str:
        if 0 <= dim <= 3:
            return f"simple_distribution_enum_{dim}d"
        return ""

    @staticmethod
    def draw(layout, context, dim: int = 0):
        """

        :param dim:
        :param layout:
        :param context:
        :return:
        """
        scene = context.scene
        box = layout.box()
        box.label(text="Preset Distributions")

        p_name = SimplifiedDistributionSelector.enum_name_from_dim(dim)
        box.prop(scene, p_name)

        SimplifiedDistributionSelector.draw_for(
            box, context,
            dist_name=(getattr(scene, p_name, "") or "").upper(),
            num_dims=dim,
            show_cmds=True
        )

    @staticmethod
    def draw_for(layout, context, dist_name: str, label: str = None, num_dims: int = 1, show_cmds: bool = False):
        """

        :param label:
        :param layout:
        :param context:
        :param num_dims:
        :param dist_name:
        :param show_cmds:
        :return:
        """

        scene = context.scene

        if dist_name == "NONE":
            layout.label(text="No distribution.")
            return

        box = layout.box()
        if label and label != "":
            box.label(text=label)

        interested_properties = SimplifiedDistributionSelector._distribution_map[dist_name]

        # Vector properties need to change with dimension.
        for property_name in interested_properties:
            extended_name = SimplifiedDistributionSelector._name_prefix + property_name
            if "vec" in property_name:
                row = box.row(align=True)

                # These are used to visualize the distribution names properly
                vector_names = {
                    "dist_mean_vec": "Mean Vector",
                    "dist_min_vec": "Minimum Vector",
                    "dist_max_vec": "Maximum Vector"
                }

                row.label(text=vector_names[extended_name])
                row.prop(scene, extended_name, index=0, text="X")
                if num_dims >= 2:
                    row.prop(scene, extended_name, index=1, text="Y")
                if num_dims >= 3:
                    row.prop(scene, extended_name, index=2, text="Z")
            else:
                box.prop(context.scene, extended_name)
        if show_cmds:
            SimplifiedDistributionSelector._draw_options(box, context)

    @staticmethod
    def _draw_options(layout, context):
        """

        :param layout:
        :param context:
        :return:
        """
        row = layout.row(align=True)
        row.prop(context.scene, "do_discretize")

        row = layout.row(align=True)
        row.prop(context.scene, "do_clamp")
        row.prop(context.scene, "clamping_factors")

    @staticmethod
    def _get_properties(dim, scene) -> list[str]:
        p_name = SimplifiedDistributionSelector.enum_name_from_dim(dim)
        dist_name = (getattr(scene, p_name, "") or "").upper()
        # There is no corresponding property for no distribution obviously
        if dist_name == "NONE":
            return []
        return SimplifiedDistributionSelector._distribution_map[dist_name]


#

class PositionListSelector(EditorWidget):

    @staticmethod
    def reset(context) -> None:
        scene = context.scene
        scene.position_collection.clear()

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        scene = context.scene
        # We have to clear the current positions list and repopulate it with the
        # correct values.
        scene.position_collection.clear()
        for item in config["positions"]:
            new_pos = scene.position_collection.add()
            new_pos.pos = item
        scene.selected_position_index = 0

    @staticmethod
    def extract_data(context) -> dict:
        scene = context.scene
        return {
            wsk.POSITION_LIST.value: [ tuple(item.pos) for item in scene.position_collection ]
        }

    @staticmethod
    def draw(layout, context):
        scene = context.scene

        box = layout.box()
        box.label(text="Saved Positions")
        row = box.row()
        row.template_list(
            PositionsUIList.__name__,
            "selected_positions",
            scene, "position_collection",  # Will populate this
            scene, "selected_position_index"
        )

        # Add/Remove buttons
        col = row.column()
        col.operator(Labels.ADD_POSITION_POOL.value, icon='ADD', text='')
        col.operator(Labels.REMOVE_POSITION_POOL.value, icon='REMOVE', text='')
        col.operator(Labels.CAPTURE_OBJ_POSITION.value, icon='EYEDROPPER', text='')
        col.operator(Labels.ADD_CURSOR_POS.value, icon='PIVOT_CURSOR', text='')

#
class MaterialSelector(EditorWidget):

    @staticmethod
    def reset(context) -> None:
        scene = context.scene
        scene.material_list.clear()

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        # We have to search in the list of materials for the one with the given name to
        # repopulate the material list editor.
        scene = context.scene
        names = config["materials"]
        scene.material_list.clear()
        for name in names:
            mat = bpy.data.materials.get(name)
            if not mat:
                continue
            new_item = scene.material_list.add()
            new_item.material = mat

    @staticmethod
    def extract_data(context) -> dict:
        scene = context.scene
        return {
            wsk.MATERIAL_LIST.value: [
                mat.material.name for mat in scene.material_list
            ]
        }

    @staticmethod
    def draw(layout, context):
        scene = context.scene

        # List
        layout.label(text="Select target materials:")
        row = layout.row()
        row.template_list(
            MaterialUIList.__name__,
            "material_list",
            scene, "material_list",
            scene, "material_list_index"
        )

        # +/- buttons
        col = row.column()
        col.operator(Labels.ADD_MATERIAL_POOL.value, icon='ADD', text='')
        col.operator(Labels.REMOVE_MATERIAL_POOL.value, icon='REMOVE', text='')

#
class PropertyTargeter(EditorWidget):

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        pass

    @staticmethod
    def extract_data(context) -> dict:
        pass

    @staticmethod
    def draw(layout, context):
        scene = context.scene
        box = layout.box().row()
        box.label(text="Target:")
        box.label(text=scene.targeted_objects_display.obj_name, icon='OBJECT_DATA')
        box.operator(Labels.CAPTURE_GENERAL_NODE.value, text="Capture Selected", icon='EYEDROPPER')

        selected_node_property = True
        if selected_node_property:
            pass

class ValueTargeter(EditorWidget):

    @staticmethod
    def reset(context) -> None:
        scene = context.scene
        scene.targeted_value_node.mat_name = ""
        scene.targeted_value_node.node_label = ""

    @staticmethod
    def draw(layout, context):
        scene = context.scene
        box = layout.box().row()
        box.label(text="Value Node:")

        mat_prop = scene.targeted_value_node
        text_label = f"{mat_prop.mat_name} > {mat_prop.node_label}" if (mat_prop.mat_name and mat_prop.node_label) else "None"
        box.label(text=text_label, icon='OBJECT_DATA')
        box.operator(Labels.CAPTURE_VALUE_NODE.value, text="Capture Selected", icon='EYEDROPPER')

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        scene = context.scene
        scene.targeted_value_node.mat_name = config["material"]
        scene.targeted_value_node.node_label = config["label"]

    @staticmethod
    def extract_data(context) -> dict:
        scene = context.scene
        return {
            wsk.VALUE_MATERIAL.value: scene.targeted_value_node.mat_name,
            wsk.VALUE_LABEL.value: scene.targeted_value_node.node_label,
        }


class ConditionalWidget(EditorWidget):

    def __init__(self, sub_widget: type[EditorWidget], ask_text: str = "Enable", *args, **kwargs) -> None:

        self.widget = sub_widget
        self.ask_text = ask_text

        # This should be saved to be inputted to intermediate widget functions.
        self._sub_init_args = args
        self._sub_init_kwargs = kwargs

    def draw(self, layout, context) -> None:
        scene = context.scene
        layout.prop(scene, 'reusable_checkbox', text=self.ask_text)
        if scene.reusable_checkbox:
            self.widget.draw(layout, context)

    def extract_data(self, context) -> dict:
        scene = context.scene
        enabled = {
            wsk.ENABLED.value : scene.reusable_checkbox
        }
        enabled.update(self.widget.extract_data(context))
        return enabled

    def reset(self, context) -> None:
        scene = context.scene
        scene.reusable_checkbox = False
        self.widget.reset(context)

    def setup_from_config(self, config: dict, context) -> None:
        scene = context.scene
        enabled = config[ wsk.ENABLED.value ]
        scene.reusable_checkbox = enabled
        if enabled:
            self.widget.setup_from_config(config, context)


class TypedObjectTargeter(EditorWidget):

    def __init__(self, obj_type: str):
        self.obj_type = obj_type

    def draw(self, layout, context) -> None:
        scene = context.scene
        box = layout.box().row()
        sub = box.row(align=True)
        sub.scale_x = 0.5
        sub.label(text="Target(s):")

        # Concatenate the captured names together to get a string representation of the capture objects.
        text_label = str(scene.typed_object.obj_name) if scene.typed_object.obj_name else "None"
        box.label(text=text_label, icon='OBJECT_DATA')

        box.operator(Labels.TYPED_SINGLE_OBJ_CAPT.value,
                text=f"Capture {self.obj_type.title()}", icon='EYEDROPPER').select_type = self.obj_type

    @staticmethod
    def extract_data(context) -> dict:
        scene = context.scene
        return {
            wsk.TYPED_OBJ_NAME.value: scene.typed_object.obj_name
        }

    @staticmethod
    def setup_from_config(config: dict, context) -> None:
        scene = context.scene
        name = config[wsk.TYPED_OBJ_NAME.value]
        scene.typed_object.obj_name = name

    @staticmethod
    def reset(context) -> None:
        scene = context.scene
        scene.typed_object.obj_name = ""

