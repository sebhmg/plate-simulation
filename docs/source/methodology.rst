.. _methodology:

Methodology
===========

In order to simulate a physical property model, we need three things: a
computational mesh, a discretization of the model within that mesh, and a
means to simulate the data.  Plate simulation relies on `discretize <https://discretize.simpeg.xyz/en/main/>`_
for the octree mesh building, and `SimPEG <https://simpeg.xyz/>`_ for finite volume based forward modeling
for the simulation.  All modelling steps are carried out withing plate simulation
itself.

create a mesh that is refined in key areas, while being coarse enough
elsewhere to efficiently carry out the modelling.  includes refinement  at the earth-air interface, in some
cases, at the transmitter and receiver sites, and in order to recover data
that accurately contains the effects of the geometry of the plate, we must
also refine the mesh around the plate.