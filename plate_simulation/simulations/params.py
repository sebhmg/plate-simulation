#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile

# pylint: disable=import-outside-toplevel, too-few-public-methods


class SimulationParams:
    @classmethod
    def from_simpeg_group(cls, group: SimPEGGroup):
        input_file = InputFile(ui_json=group.options, validate=False)
        assert input_file.data is not None, "Input file data must be set."
        if input_file.data["inversion_type"] == "gravity":
            from simpeg_drivers.potential_fields.gravity.params import GravityParams

            return GravityParams(input_file=input_file)

        raise NotImplementedError(
            f"Unknown inversion type: {input_file.data['inversion_type']}"
        )
