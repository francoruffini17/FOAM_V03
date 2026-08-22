import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from D001_Input_files_creator.SIM_4000_family_common import FamilySpec, create_family


SPEC = FamilySpec(
    first_sim=4010,
    mesh_file='R1000.mesh.json',
    material_model='linear',
    description='random packing, linear elastic',
)


if __name__ == '__main__':
    create_family(SPEC)
