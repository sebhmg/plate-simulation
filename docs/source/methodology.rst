.. _methodology:

Methodology
===========

In order to simulate geohpysical data from a physical property model, we
need three things: a computational mesh, a discretization of the model
within that mesh, and a means to simulate the data.  Plate simulation
relies on `discretize <https://discretize.simpeg.xyz/en/main/>`_ for
octree mesh creation, and `SimPEG <https://simpeg.xyz/>`_ for finite
volume based forward modeling.  Plate simulation includes a module for
generating basement + overburden + plate models within octree meshes. In
this section, we will discuss all three of these components, and their
interface exposed by the ui.json file.

.. contents::

.. toctree::
   :maxdepth: 3

Octree Mesh
-----------

In order to accurately simulate our earth model, we need a mesh
that is refined in key areas, while being coarse enough elsewhere to
efficiently simulate data.  The plate simulation package includes
refinements at the earth-air interface, the transmitter and receiver
sites, and within the plate.

.. figure:: /images/methodology/mesh/refinement.png
   :align: center

   *Octree mesh refinement for earth-air interface, receiver sites,
   and within the mesh.*

The meshing can be controlled by options exposed in the ui.json.
Compared with the `octree-creation-app <https://octree-creation-app.readthedocs.io/en/latest/>`_
, the options are significantly reduced since we have tailored many
of the parameters to suit the needs of plate simulation.

.. figure:: /images/methodology/mesh/mesh_options.png
   :align: center

   *Octree mesh parameters exposed in the ui.json.*

Geological Model
----------------

The plate simulation package includes a module for generating
basement + overburden + plate models within octree meshes.
There are many permutations of this simple geological model
scenario so the ui.json interface for this component is more
complex that the meshing and simulation components.  For this
reason, we will break the discussion down sub-sections, guided
by the options in the ui.json. The bulk of the complexity comes
from the choices pertaining to the plate, so we'll save those
for last.  The basement and overburden options can be considered
together as background model options that we'll discuss next

Background
~~~~~~~~~~

All model values within plate-simulation are to be provided in
Ohm-meters.  The basement resistivity is actually closer to a
halfspace in the sense that it fills the model anywhere outside
of the overburden and plate.  So the basement resistivity should
be chosen as an effective resistivity for the whole geological
section.  This should be quite reasonable for most applications
where the differences in resistivity between layers is much smaller
than the difference between overburden and any anomalous bodies
(plates).

.. figure:: /images/methodology/model/basement_options.png
   :align: center

   *Basement resistivity option.*

The overburden is discretized by the resistivity and the thickness
of the layer.  The thickness is referenced to the earth-air interface.
In this way, the overburden layer is the first layer in the model
below the air and extends into the earth by the amount specified
in the thickness parameter.

.. figure:: /images/methodology/model/overburden_options.png
    :align: center

    *Overburden resistivity and thickness options.*

.. figure:: /images/methodology/model/overburden_and_basement.png
    :align: center

    *Model section highlighting the overburden and basement boundary.*

Plates
~~~~~~~~

In this section we will discuss the various plate options available
through the ui.json and their impact on the resulting discretized
model.

.. figure:: /images/methodology/model/plate_options.png
    :align: center

    *Plate options available in the ui.json.*

Due to the complexity of the interface, we will again break this down
into sub-sections.  The first set of options allows the user to
specify the number of plates and their spacing.

.. figure:: /images/methodology/model/n_plates_options.png
    :align: center

    *Number of plates and spacing options.*

For all choices of ``n>1``, the plates will be evenly spaced at the requested
spacing.  All the plates will have the same parameters chosen later in
the interface.  That is, they will all share the same resistivity, size,
location and orientation.

.. figure:: /images/methodology/model/three_plates.png
    :align: center

    *Model created by choosing three plates spaced at 200m.*

The plate resistivity should be self-explanatory by now.

.. figure:: /images/methodology/model/plate_resistivity_option.png
    :align: center

    *Plate resistivity option.*

The shape of the plate is given as a 'thickness', 'strike length', and
'dip length'.


.. figure:: /images/methodology/model/plate_size.png
    :align: center

    *A dipping plate striking northeast with annotations for it's thickness,
    strike length and dip length.*

The orientation of the plate(s) is provided in terms of a

.. figure:: /images/methodology/model/plate_orientation.png
    :align: center

    *Plate orientation options.*

Data Simulation
---------------
