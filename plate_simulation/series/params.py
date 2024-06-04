#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from pathlib import Path

from geoapps_utils.driver.data import BaseData
from geoh5py.objects import Curve, Points
from geoh5py.ui_json import InputFile
from pydantic import field_validator


class SimulationSeriesParams(BaseData):
    """
    Parameters for the generation of simulations from Points values.

    :param plate_simulation: A UIJsonGroup holding simulation parameters.
    :param point_parameters: Points with simulation parameters.
    :param output_curve: Curve object to append data to.
    :param topography: Points-like object to use as topography.
    :param save_all: Keep all simulation objects to the workspace.
    """

    plate_simulation: Path
    point_parameters: Points
    output_curve: Curve | None = None
    topography: Points | None = None
    save_all: bool = False

    @field_validator("plate_simulation", mode="before")
    @classmethod
    def validate_path(cls, v: str) -> Path:
        if not Path(v).exists():
            raise ValueError(f"File {v} does not exist.")

        ifile = InputFile.read_ui_json(v)

        if ifile.ui_json["run_command"] != "plate_simulation.driver":
            raise ValueError(
                f"Invalid input file {v}. "
                f"Expected run_command 'plate_simulation.driver' "
                f"got {ifile.ui_json['run_command']}."
            )

        return Path(v)
