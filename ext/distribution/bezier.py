"""
Utilities for representing, evaluating, and sampling Bezier curves.

This module provides lightweight data structures and helper functions for
working with cubic Bezier splines embedded in 3D space. It includes utilities
for:

- Representing Bezier segments and spline collections
- Importing Bezier curve data from Blender curve objects
- Evaluating cubic Bezier segments
- Approximating curve and spline lengths
- Sampling points from Bezier curves using weighted distributions

Sampling weights are derived from approximate segment lengths so that longer
segments are proportionally more likely to be selected.
"""

from dataclasses import dataclass
from random import random, choices
from typing import List

from mathutils import Vector


@dataclass
class Bezier2PSegment:
    """ Representation of a cubic Bezier segment.

    :param p0: Starting control point.
    :param left_handle: Incoming handle associated with the second endpoint.
    :param right_handle: Outgoing handle associated with the first endpoint.
    :param p1: Ending control point.
    """

    p0: Vector
    left_handle: Vector
    right_handle: Vector
    p1: Vector


@dataclass
class Spline:
    """ Collection of connected Bezier segments.

    :param segments: Ordered list of cubic Bezier segments composing the spline.
    """

    segments: list[Bezier2PSegment]


@dataclass
class BezierCurve:
    """
    Container for one or more Bezier splines.

    :param splines: Collection of spline objects composing the curve.
    """
    splines: list[Spline]

    @staticmethod
    def from_blender_curve(bpy_curve) -> 'BezierCurve':
        """ Construct a BezierCurve from a Blender curve object.

        The generated curve explicitly incorporates the Blender object's world
        transformation matrix so that sampled geometry reflects global scale,
        translation, and rotation.

        :param bpy_curve: Blender Bezier curve object.

        :return: A convertedBezierCurve instance containing all Bezier
            splines found in the Blender object.
        """
        spline_list = list()
        curve = BezierCurve(spline_list)

        matrix = bpy_curve.matrix_world

        for spline in bpy_curve.data.splines:

            if spline.type != 'BEZIER':
                continue

            segments = list()
            for i in range(len(spline.bezier_points) - 1):
                # We explicitly take into account the curve's world matrix to handle
                # scales and rotations.
                p0 =  matrix @ spline.bezier_points[i].co
                handle_left =  matrix @ spline.bezier_points[i].handle_right
                handle_right =  matrix @ spline.bezier_points[i + 1].handle_left
                p1 =  matrix @ spline.bezier_points[i + 1].co

                segments.append(Bezier2PSegment(
                    p0, handle_left, handle_right, p1))
            spline_list.append(Spline(segments))
        return curve


def evaluate_bezier_segment(p0, h0_right, h1_left, p1, t) -> Vector:
    """ Evaluate a cubic Bezier segment at parameter t.
     The evaluation follows the standard cubic Bezier formulation.

     :param p0: Starting control point.
     :param h0_right: Outgoing handle associated with p0.
     :param h1_left: Incoming handle associated with p1.
     :param p1: Ending control point.
     :param t: Parametric position along the curve in the interval.

     :return: Evaluated point on the Bezier segment.
     """
    # From the definition of a (cubic) Bezièr curve.
    # https://en.wikipedia.org/wiki/B%C3%A9zier_curve
    mt = 1 - t
    return mt ** 3 * p0 + 3 * mt ** 2 * t * h0_right + 3 * mt * t ** 2 * h1_left + t ** 3 * p1


def evaluate_2p_bezier_seg(p: Bezier2PSegment, t) -> Vector:
    """ Evaluate a :class:`Bezier2PSegment` at parameter ``t``.

    :param p: Bezier segment to evaluate.
    :param t: Parametric position along the segment in the interval ``[0, 1]``.
    """
    # From the definition of a (cubic) Bezièr curve.
    # https://en.wikipedia.org/wiki/B%C3%A9zier_curve
    mt = 1 - t
    return mt ** 3 * p.p0 + 3 * mt ** 2 * t * p.right_handle + 3 * mt * t ** 2 * p.left_handle + t ** 3 * p.p1


def segment_length(p0, h0_right, h1_left, p1, samples=10):
    """ Approximate the length of a cubic Bezier segment.

    Length is estimated through uniform parametric sampling and piecewise
    linear distance accumulation.

    :param p0: Starting control point.
    :param h0_right: Outgoing handle associated with ``p0``.
    :param h1_left: incoming handle associated with ``p1``.
    :param p1: Ending control point.
    :param samples: Number of discrete samples used for approximation.

    :return: Approximate arc length of the segment.
    """
    total = 0
    prev_point = p0
    for i in range(1, samples + 1):
        t = i / samples
        point = evaluate_bezier_segment(p0, h0_right, h1_left, p1, t)
        total += (point - prev_point).length
        prev_point = point
    return total


def bezier_segment_length(s: Bezier2PSegment, samples=10):
    """ """
    return segment_length(s.p0, s.right_handle, s.left_handle, s.p1, samples)


def spline_length(spl: Spline):
    return sum(bezier_segment_length(seg) for seg in spl.segments)


def normalize_weights(weights: List[float]) -> None:
    tot = sum(weights)
    for i in range(len(weights)):
        weights[i] /= tot
    return


class BezierDistribution:
    """
    Weighted spatial distribution over a Bezier curve.

    This distribution samples random points from a Bezier curve by:

    1. Selecting a spline according to spline length
    2. Selecting a segment according to segment length
    3. Evaluating a random parameter value on the segment

    Segment and spline probabilities are proportional to their approximate
    geometric lengths.
    """

    def __init__(self, curve: BezierCurve) -> None:
        """ Initialize the Bezier distribution.  """
        self.curve = curve

        self.spline_weight = []
        self.segment_mapped_weights: dict[int, list[float]] = dict()

        self._compile()

    def _compile(self) -> None:
        """ Precompute spline and segment sampling weights.

        Segment lengths are approximated numerically and normalized to form
        probability distributions suitable for weighted random sampling.
        """
        self.segment_mapped_weights = {
            i: [bezier_segment_length(seg) for seg in spline.segments]
            for i, spline in enumerate(self.curve.splines)
        }
        self.spline_weight = [sum(segments, 0.0) for _, segments in self.segment_mapped_weights.items()]

        # Normalize the weights so that we can use the default random library
        # to sample a random index value (first to sample a spline, then to sample
        # a segment and finally to sample a point)
        normalize_weights(self.spline_weight)
        for spline in self.segment_mapped_weights:
            normalize_weights(self.segment_mapped_weights[spline])

    @property
    def dimension(self) -> int:
        """ Get dimension of the sampled space. """
        # All bezier are assumed to be embedded in 3d space, independently of their
        # collinearity.
        return 3

    def sample(self) -> List[float]:
        """ Sample a random point from the Bezier distribution.

        Sampling proceeds hierarchically using spline and segment weights
        derived from approximate geometric lengths.

        :return: A sampled 3D point represented as [x, y, z].
        """
        if not self.spline_weight or not self.segment_mapped_weights:
            return [0.0, 0.0, 0.0]

        spline_index = choices(range(len(self.spline_weight)), weights=self.spline_weight, k=1)
        spline_index = spline_index[0]
        # We now extract the spline which was selected
        spline: Spline = self.curve.splines[spline_index]
        if not self.segment_mapped_weights[spline_index]:
            return [0.0, 0.0, 0.0]

        seg_index = choices(
            range(len(self.segment_mapped_weights[spline_index])), weights=self.segment_mapped_weights[spline_index],
            k=1)
        seg_index = seg_index[0]
        # We now extract the segment that was selected.
        segment = spline.segments[seg_index]

        # Evaluate a random point (THE RANDOM VALUE IS NOT the line parameters, this is somewhat biased)
        val = random()
        point = evaluate_2p_bezier_seg(segment, val)

        return [point[0], point[1], point[2]]

