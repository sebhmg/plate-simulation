# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''
#  Copyright (c) 2024 Mira Geoscience Ltd.                                             '
#                                                                                      '
#  This file is part of plate-simulation package.                                      '
#                                                                                      '
#  plate-simulation is distributed under the terms and conditions of the MIT License   '
#  (see LICENSE file at the root of this source code package).                         '
# ''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''''

from abc import ABC, abstractmethod

import numpy as np
from geoh5py.objects import Octree, Surface
from simpeg_drivers.utils.utils import active_from_xyz
from trimesh import Trimesh
from trimesh.proximity import ProximityQuery


# pylint: disable=too-few-public-methods


class Event(ABC):
    """Parameterized geological events that modify the model."""

    @abstractmethod
    def realize(self, mesh: Octree, model: np.ndarray) -> np.ndarray:
        """
        Update the model with the event realization

        :param mesh: Octree mesh on which the model is defined.
        :param model: Model to be updated by the event.
        """


class Deposition(Event):
    """
    Fills model below a surface with a provided property value.

    :param surface: Surface representing the top of a sedimentary layer.
    :param value: The value given to the model below the surface.
    """

    def __init__(self, surface: Surface, value: float):
        self.surface = Boundary(surface)
        self.value = value

    def realize(self, mesh: Octree, model: np.ndarray) -> np.ndarray:
        """Fill the model below the surface with the layer's value."""
        model[self.surface.mask(mesh)] = self.value
        return model


class Overburden(Event):
    """
    Add an overburden layer below the topography surface.

    :param topography: Surface representing the topography.
    :param thickness: Thickness of the overburden layer.
    :param value: Model value given to the overburden layer.
    """

    def __init__(self, topography: Surface, thickness: float, value: float):
        self.topography = Boundary(topography)
        self.thickness = thickness
        self.value = value

    def realize(self, mesh: Octree, model: np.ndarray) -> np.ndarray:
        """Fill the model below the topography with the overburden value."""
        model[
            ~self.topography.mask(mesh, offset=-1 * self.thickness, reference="center")
        ] = self.value
        return model


class Erosion(Event):
    """
    Erode the model at a provided surface.

    :param surface: The surface above which the model will be
        eroded (filled with nan values).
    """

    def __init__(self, surface: Surface):
        self.surface = Boundary(surface)

    def realize(self, mesh: Octree, model: np.ndarray) -> np.ndarray:
        """Fill the model above the surface with nan values"""
        model[~self.surface.mask(mesh)] = np.nan
        return model


class Anomaly(Event):
    """
    Enrich or deplete the model within a close surface.

    :param surface: Closed surface within which the model will be filled
        with the anomaly value.
    :param value: Model value assigned to the anomaly.
    """

    def __init__(self, surface: Surface, value: float):
        self.body = Body(surface)
        self.value = value

    def realize(self, mesh: Octree, model: np.ndarray) -> np.ndarray:
        """Fill the model within the surface with the anomaly value."""
        model[self.body.mask(mesh)] = self.value
        return model


class Boundary:
    """
    Represents a boundary in a model.

    :param surface: geoh5py Surface object representing a boundary
        in the model.
    """

    def __init__(self, surface: Surface):
        self.surface = surface

    def vertical_shift(self, offset: float) -> np.ndarray:
        """
        Returns the surface vertices shifted vertically by offset.

        :param offset: Shifts vertices in up (positive) or down (negative).
        """

        if self.surface.vertices is None:
            raise ValueError("Surface vertices are not defined.")

        shift = np.c_[
            np.zeros(self.surface.vertices.shape[0]),
            np.zeros(self.surface.vertices.shape[0]),
            np.ones(self.surface.vertices.shape[0]) * offset,
        ]
        return self.surface.vertices + shift

    def mask(
        self, mesh: Octree, offset: float = 0.0, reference: str = "center"
    ) -> np.ndarray:
        """
        True for cells whose reference lie below the surface.

        :param mesh: Octree mesh on which the mask is computed.
        :param offset: Statically shift the surface on which the mask
            is computed.
        :param reference: Use "bottom", "center" or "top" of the cells
            in determining the mask.

        """

        return active_from_xyz(mesh, self.vertical_shift(offset), reference)


class Body:
    """
    Represents a closed surface in the model.

    :param surface: geoh5py Surface object representing a closed surface
    """

    def __init__(self, surface: Surface):
        self.surface = surface

    def mask(self, mesh: Octree) -> np.ndarray:
        """
        True for cells that lie within the closed surface.

        :param mesh: Octree mesh on which the mask is computed.
        """
        triangulation = Trimesh(
            vertices=self.surface.vertices, faces=self.surface.cells
        )
        proximity_query = ProximityQuery(triangulation)
        dist = proximity_query.signed_distance(mesh.centroids)
        return dist > 0
