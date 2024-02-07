#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from simpeg_drivers.utils.utils import active_from_xyz

if TYPE_CHECKING:
    from geoh5py.objects import Octree, Surface

# pylint: disable=too-few-public-methods


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


class Event(ABC):
    """Parameterized geological events that modify the model."""

    @abstractmethod
    def realize(self, mesh: Octree, model: np.ndarray) -> np.ndarray:
        """
        Update the model with the event realization

        :param mesh: Octree mesh on which the model is defined.
        :param model: Model to be updated by the event.
        """


class Series:
    """
    Sequence of geological events.

    :param history: Sequence of geological events.
    """

    def __init__(self, history: Sequence[Event | Series] | Geology):
        self.history = history

    def realize(self, mesh: Octree, model: np.ndarray):
        """Realize each event in the history."""

        for event in self.history:
            model = event.realize(mesh, model)

        return model


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


class Lithology(Series):
    """
    Model a sequence of sedimentary layers.

    :param history: Sequence of layers to be deposited. These should be
        ordered so that the first layer in the list is the bottom unit
        and the last layer is the top unit
    """

    # TODO: Provide an optional bottom surface to begin the deposition.

    def __init__(self, history: Sequence[Deposition]):
        super().__init__(history[::-1])

    def realize(self, mesh: Octree, model) -> np.ndarray:
        """Fills the model with the sequence of layers in the history."""
        return super().realize(mesh, model)


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
        model[~self.topography.mask(mesh, offset=-1 * self.thickness)] = self.value
        return model


class GeologyViolationError(Exception):
    """Raise when a geological history is invalid."""

    def __init__(self, message):
        super().__init__(message)


class Geology:
    """
    Ensures that a history is valid.

    :param history: Sequence of geological events to be validated.
    """

    def __init__(self, history: Sequence[Event | Series]):
        self.history = history

    def __iter__(self):
        return iter(self.history)

    @property
    def history(self):
        return self._history

    @history.setter
    def history(self, events):
        self._validate_history(events)
        self._history = events

    def _validate_history(self, events: Sequence[Event | Series]):
        """Throw exception if the history isn't valid."""
        self._validate_overburden(events)
        self._validate_topography(events)

    def _validate_overburden(self, events: Sequence[Event | Series]):
        """Throw exception if Overburden is not the second last event in the history."""

        if any(isinstance(k, Overburden) for k in events) and not isinstance(
            events[-2], Overburden
        ):
            raise GeologyViolationError(
                "Overburden events must occur before the final erosion in the history."
            )

    def _validate_topography(self, events: Sequence[Event | Series]):
        """Throw exception if the last event isn't an erosion."""

        if not isinstance(events[-1], Erosion):
            raise GeologyViolationError(
                "The last event in a geological history must be an erosion."
            )


class Scenario(Series):
    """
    Model a sequence of geological events within an Octree mesh.

    :param mesh: Octree mesh on which the model is defined.
    :param background: Initial value that will fill any areas of the model
        not covered by event realizations.
    :param history: Geological events that form the model.
    :param name: Name of the model that will be added to the mesh object.
    """

    def __init__(
        self,
        mesh: Octree,
        background: float,
        history: Sequence[Event | Series],
        name: str = "model",
    ):
        super().__init__(history)
        self.mesh = mesh
        self.background = background
        self.history = Geology(history)
        self.name = name

    @property
    def mesh(self):
        return self._mesh

    @mesh.setter
    def mesh(self, val):
        if val.n_cells is None:
            raise ValueError("Mesh must have n_cells.")
        self._mesh = val

    def geologize(self):
        """Realize the geological events in the scenario"""
        model = super().realize(self.mesh, np.ones(self.mesh.n_cells) * self.background)
        return self.mesh.add_data({self.name: {"values": model}})
