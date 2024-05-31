#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from copy import deepcopy

from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile
from simpeg_drivers.electromagnetics.time_domain.params import (
    TimeDomainElectromagneticsParams,
)
from simpeg_drivers.params import InversionBaseParams
from simpeg_drivers.potential_fields.gravity.params import GravityParams


# pylint: disable=import-outside-toplevel, too-few-public-methods


class SimulationParams:
    # TODO fill in params options
    @classmethod
    def from_simpeg_group(cls, group: SimPEGGroup, workspace) -> InversionBaseParams:
        input_file = InputFile(ui_json=deepcopy(group.options), validate=False)
        if input_file.ui_json is None:
            raise ValueError("Input file must have ui_json set.")
        input_file.ui_json["mesh"]["value"] = None
        input_file.ui_json["geoh5"] = workspace
        assert input_file.data is not None, "Input file data must be set."

        if input_file.data["inversion_type"] == "gravity":
            return GravityParams(input_file=input_file, validate=False)
        if input_file.data["inversion_type"] == "tdem":
            return TimeDomainElectromagneticsParams(
                input_file=input_file, validate=False
            )
        raise NotImplementedError(
            f"Unknown inversion type: {input_file.data['inversion_type']}"
        )
