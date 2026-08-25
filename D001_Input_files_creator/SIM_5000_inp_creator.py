import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from D001_Input_files_creator.SIM_4000_family_common import FamilySpec, create_family


SPEC = FamilySpec(
    first_sim=5000,
    mesh_file='A1000.mesh.json',
    material_model='linear',
    description='hexagonal packing, linear elastic, 401-output high resolution',
    output_frames=400,
    output_interval=0.0025,
)


if __name__ == '__main__':
    create_family(SPEC)
