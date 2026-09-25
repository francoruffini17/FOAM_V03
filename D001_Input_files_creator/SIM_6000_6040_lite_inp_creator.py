"""Create five neo-Hookean pressure sweeps with lite-only ODB histories.

SIM 6000/6010/6020/6030/6040 correspond to 5100/5110/5120/5130/5140.
Each family contains ten pressure cases. Existing simulation directories are
left untouched; the older, unrelated SIM_6000 and SIM_6010 creators remain
available under their original filenames.
"""

from D001_Input_files_creator.SIM_4000_family_common import FamilySpec, create_family


FAMILIES = (
    (6000, 'A1000.mesh.json', 'hexagonal packing'),
    (6010, 'R1000.mesh.json', 'random packing'),
    (6020, 'S1000.mesh.json', 'square packing'),
    (6030, 'RH1000.mesh.json', 'rhombic packing'),
    (6040, 'ST1000.mesh.json', 'chevron-pair snap-through packing'),
)


def main():
    for first_sim, mesh_file, packing in FAMILIES:
        create_family(FamilySpec(
            first_sim=first_sim,
            mesh_file=mesh_file,
            material_model='neo_hookean',
            description=f'{packing}, neo-Hookean, lite histories',
            output_frames=400,
            output_interval=0.0025,
            lite_only=True,
        ), replace=False)


if __name__ == '__main__':
    main()
