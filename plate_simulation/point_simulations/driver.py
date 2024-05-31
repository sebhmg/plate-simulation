#  Copyright (c) 2024 Mira Geoscience Ltd.
#
#  This file is part of plate-simulation package.
#
#  All rights reserved.
#

from __future__ import annotations

from pathlib import Path

from geoh5py.groups import SimPEGGroup
from geoh5py.ui_json import InputFile

from plate_simulation.params import PlateSimulationParams
from plate_simulation.point_simulations.params import PointsSimulationParams


class PointsSimulationDriver:
    """
    Driver for simulating background + plate + overburden model.

    :param params: Parameters for plate simulation (mesh, model and
        point_simulations).
    """

    def __init__(self, params: PointsSimulationParams):
        self.params = params

    def run(self) -> SimPEGGroup:
        """Create octree mesh, fill model, and simulate."""

        simulation_params = PlateSimulationParams.build(self.params.simulation.options)

    @staticmethod
    def start(ifile: str | Path | InputFile):
        """Run the plate simulation driver from an input file."""

        if isinstance(ifile, str):
            ifile = Path(ifile)

        if isinstance(ifile, Path):
            ifile = InputFile.read_ui_json(ifile)

        if ifile.data is None:  # type: ignore
            raise ValueError("Input file has no data loaded.")

        with ifile.geoh5.open():  # type: ignore
            params = PointsSimulationParams.build(ifile)

        return PointsSimulationDriver(params).run()


if __name__ == "__main__":
    # file = Path(sys.argv[1])
    file = Path(r"C:\Users\dominiquef\Desktop\Working\validation.ui.json")
    PointsSimulationDriver.start(file)
