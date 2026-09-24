"""Create the SIM_5150--5159 pressure sweep for refined eigen analysis.

The physical model matches SIM_5140--5149; the eigen replay uses additional
late-loading samples and multiple nearby modes.
"""

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from D001_Input_files_creator.SIM_4000_family_common import FamilySpec, create_family


SPEC = FamilySpec(
    first_sim=5150,
    mesh_file='ST1000.mesh.json',
    material_model='neo_hookean',
    description='chevron-pair snap-through, refined late eigen sampling',
    output_frames=400,
    output_interval=0.0025,
)


if __name__ == '__main__':
    create_family(SPEC, replace=False)
