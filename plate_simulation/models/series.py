#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

import numpy as np
from geoh5py import Workspace
from geoh5py.data import FloatData
from geoh5py.objects import Octree
from geoh5py.shared.utils import fetch_active_workspace

from .events import Anomaly, Erosion, Overburden


if TYPE_CHECKING:
    from .events import Deposition, Event


# pylint: disable=too-few-public-methods


class Series:
    """
    Sequence of geological events.

    :param history: Sequence of geological events.
    """

    def __init__(self, history: Sequence[Event | Series] | Geology):
        self.history = history

    def realize(self, mesh: Octree, model: np.ndarray) -> np.ndarray:
        """
        Realize each event in the history.

        :param mesh: Octree mesh on which the model is defined.
        :param model: Model to be updated by the events in the history.
        """

        for event in self.history:
            model = event.realize(mesh, model)

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
        """
        Fills the model with the sequence of layers in the history.

        :param mesh: Octree mesh on which the model is defined.
        :param model: Model to be updated by the events in the history.
        """
        return super().realize(mesh, model)


class DikeSwarm(Series):
    """
    Model a set of dike intrusions.

    :param history: Sequence of intrusions represented by Anomaly objects.
    """

    def __init__(self, history: Sequence[Anomaly]):
        super().__init__(history)


class Scenario(Series):
    """
    Model a sequence of geological events within an Octree mesh.

    :param workspace: Workspace in which the model will be created.
    :param mesh: Octree mesh on which the model is defined.
    :param background: Initial value that will fill any areas of the model
        not covered by event realizations.
    :param history: Geological events that form the model.
    :param name: Name of the model that will be added to the mesh object.
    """

    def __init__(
        self,
        workspace: Workspace,
        mesh: Octree,
        background: float,
        history: Sequence[Event | Series],
        name: str = "model",
    ):
        super().__init__(history)
        self.workspace = workspace
        self.mesh = mesh
        self.background = background
        self.history = Geology(history)
        self.name = name

    @property
    def mesh(self) -> Octree:
        """Octree mesh on which the model is defined."""
        return self._mesh

    @mesh.setter
    def mesh(self, val: Octree):
        if val.n_cells is None:
            raise ValueError("Mesh must have n_cells.")
        self._mesh = val

    def geologize(self) -> FloatData:
        """Realize the geological events in the scenario"""
        with fetch_active_workspace(self.workspace, mode="r+"):
            if self.mesh.n_cells is None:
                raise ValueError("Mesh must have n_cells.")
            geology = (
                super().realize(self.mesh, np.ones(self.mesh.n_cells) * self.background)
                ** -1.0
            )
            model: FloatData = self.mesh.add_data(  # type: ignore
                {self.name: {"values": geology}}
            )

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
    def history(self) -> Sequence[Event | Series]:
        """Sequence of geological events."""
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
