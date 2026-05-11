""" Utilities and interfaces for stochastic color generation.

This module defines a small hierarchy of color samplers for generating RGB and
RGBA color values using different statistical strategies. The samplers expose a
common interface through :class:`ColorSampler`, allowing interchangeable use in
rendering, procedural generation, visualization, and simulation workflows.

Color values are represented as normalized floating point tuples in the range
[0.0, 1.0].

Classes:

    ColorSampler:
        Abstract base interface for color sampling strategies.

    UniformColorSampler:
        Samples RGB values uniformly from the full color cube.

    UniformHSVColorSampler:
        Samples colors uniformly in HSV space before converting to RGB.

    GaussianRGBSampler:
        Samples colors around a base RGB value using a Gaussian distribution.

    PaletteSampler:
        Samples colors from a weighted palette.

    PresetColorSampler:
        Minimal sampler interface for vector-based sampling systems.

"""

from typing import Union, List
from abc import abstractmethod, ABCMeta
from random import gauss, random, uniform, choices
from colorsys import hsv_to_rgb


# Simple alias for an RGB tuple and RGBa tuple
rgb_color = tuple[float, float, float]
rgba_color = tuple[float, float, float, float]

class ColorSampler(metaclass=ABCMeta):
    """ Abstract interface for color samplers.

    Implementations generate random color samples represented as RGB or RGBA
    tuples with normalized floating point channels.
    """

    @staticmethod
    @abstractmethod
    def sample_color(
            use_alpha: bool = False, **kwargs) -> Union[rgba_color, rgb_color]:
        pass

class UniformColorSampler(ColorSampler):
    """ Uniform random RGB/RGBA sampler.

    Samples each color channel independently of a uniform distribution over
    the interval [0.0, 1.0].
    """

    @staticmethod
    def sample_color(use_alpha: bool = False, **kwargs) -> Union[rgba_color, rgba_color]:
        rng = (random(), random(), random())
        if use_alpha:
            return rng[0], rng[1], rng[2], random()
        else:
            return rng

class UniformHSVColorSampler(ColorSampler):
    """ HSV-based random color sampler.

    Colors are generated in HSV space using constrained saturation and value
    ranges to produce visually vivid and bright colors, then converted to RGB.
    """

    @staticmethod
    def sample_color(use_alpha: bool = False, **kwargs) -> rgb_color:
        h = random()  # Full hue circle
        s = uniform(0.5, 1.0)  # Saturation range
        v = uniform(0.7, 1.0)  # Value range
        return hsv_to_rgb(h, s, v)

class GaussianRGBSampler(ColorSampler):
    """ Gaussian-distributed RGB sampler.

    Samples RGB channels independently around a specified base color using a
    Gaussian distribution. Values are clamped to the valid interval [0.0, 1.0]
    """

    @staticmethod
    def sample_color(use_alpha: bool = False, base_color: rgb_color = (1,1,1), variance=1) -> rgb_color:
        r = max(0.0, min(1.0, gauss(base_color[0], variance)))
        g = max(0.0, min(1.0, gauss(base_color[1], variance)))
        b = max(0.0, min(1.0, gauss(base_color[2], variance)))
        return r, g, b


class PaletteSampler(ColorSampler):
    """ Weighted palette-based color sampler.

    Samples colors from a user-provided palette using weighted random
    selection.
    """

    @staticmethod
    def sample_color(use_alpha: bool = False, palette=None) -> rgb_color:
        if palette is None:
            palette = list()
        colors = [item.color for item in palette]
        weights = [item.weight for item in palette]
        return choices(colors, weights=weights, k=1)[0]


class PresetColorSampler:
    """ Minimal interface for vector-based color samplers.

    This class provides a lightweight sampling API intended for systems that
    represent colors or feature vectors as lists of floating point values.
    """

    def __init__(self):
        pass

    @property
    def has_alpha(self) -> bool:
        """ Return dimensionality of samples """
        return False

    def sample(self) -> List[float]:
        """ Sample a vector of shape (dimension,) """
        pass
