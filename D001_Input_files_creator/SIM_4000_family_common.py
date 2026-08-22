import json
import os
import shutil
import sys
from dataclasses import asdict, dataclass

import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from A001_functions.abq_inp_file_creator import S6, StepData, data


PRESSURES = (0.0,) + tuple(0.04 * np.sqrt(2) ** i for i in range(9))
E = 20
NU = 0.3
DENSITY = 1e-6
STEP0_STABILIZATION = 2e-5
U_RAMP = -5


@dataclass(frozen=True)
class FamilySpec:
    first_sim: int
    mesh_file: str
    material_model: str
    description: str


def _prepare_simulation_directory(path, replace):
    if not os.path.exists(path):
        os.makedirs(path)
        print(f"Folder '{path}' was created.")
        return True

    should_replace = replace
    if should_replace is None:
        answer = input(f"Folder '{path}' already exists. Replace it? (y/n): ").strip().lower()
        should_replace = answer == 'y'
    if not should_replace:
        print(f"Skipped existing folder '{path}'.")
        return False

    shutil.rmtree(path)
    os.makedirs(path)
    print(f"Folder '{path}' was replaced.")
    return True


def _build_object(sim_num, pressure, spec, sim_path):
    obj = data()
    obj.input_name = f'C001_Mesh_files/{spec.mesh_file}'
    obj.periodic = 'both'
    obj.scale_x = 20.0
    obj.scale_y = 20.0
    obj.input = f'{sim_path}/SIM_{sim_num:04d}.inp'
    obj.E = E
    obj.nu = NU
    obj.material_model = spec.material_model
    obj.t = 1
    obj.ELE_TYPE_3 = 'CPS3'
    obj.ELE_TYPE_4 = 'CPS4'
    obj.density_foam = DENSITY
    obj.fluid_cavity = """*Molecular Weight
        28.0e-6"""
    obj.physical_constants = '*Physical Constants, absolute zero=0, universal gas=8314'
    obj.gas_present = True
    obj.fluid_cavity_ratio = 1.0
    obj.initial_Temp = 273
    obj.initial_Pressure = 0.101325

    step0 = StepData(
        name='Step-0',
        solver=f"""**
    *Step, name=Step-0, nlgeom=YES, inc=99999, unsymm=YES
    *Static, stabilize, factor={STEP0_STABILIZATION}, continue=NO
    1e-5, 1., 1e-99, 0.1
    """,
        corner_xnyn_bc=[0, 0, None, None, None, None],
        corner_xpyn_bc=[None, 0, None, None, None, None],
        Pressure_BC=pressure,
        time_interval_out=0.1,
        frequ_out=100,
        out_frames=100,
        restart_line='',
        ELE_OUTPUT='S11, S12, S22',
        NODES_OUTPUT='COOR1, COOR2',
        additional_outputs=["""** HISTORY OUTPUT: H-Set-y-negative
    *Output, history, time interval=0.005
    *Node Output, nset=Set-y-negative
    RF2,
    """, """** HISTORY OUTPUT: H-Energy
    *Output, history, time interval=0.005
    *Energy Output
    ALLKE, ALLSE, ALLIE, ALLSD, ALLWK
    """],
    )

    step1 = StepData(
        name='Step-1',
        solver="""**
    *Step, name=Step-1, nlgeom=YES, inc=99999, unsymm=YES
    *Dynamic, application=QUASI-STATIC, initial=NO
    1e-4, 1., 1e-99, 0.005
    """,
        new_boundary=True,
        corner_xnyn_bc=[0, 0, None, None, None, None],
        corner_xpyn_bc=[None, 0, None, None, None, None],
        BC_9999997=[None, U_RAMP, None, None, None, None],
        time_interval_out=0.005,
        frequ_out=100,
        out_frames=200,
        restart_line='',
        ELE_OUTPUT='S11, S12, S22',
        NODES_OUTPUT='COOR1, COOR2',
        additional_outputs=["""** HISTORY OUTPUT: H-Set-y-negative
    *Output, history, time interval=0.005
    *Node Output, nset=Set-y-negative
    RF2,
    """, """** HISTORY OUTPUT: H-Energy
    *Output, history, time interval=0.005
    *Energy Output
    ALLKE, ALLSE, ALLIE, ALLSD, ALLVD, ALLWK
    """],
        holes_output='',
    )
    obj.steps = [step0, step1]
    return obj


def create_family(spec, replace=None):
    """Create one ten-simulation pressure family.

    ``replace`` may be True/False for non-interactive use. When omitted, each
    existing target directory requires confirmation before replacement.
    """
    if spec.material_model not in ('linear', 'neo_hookean'):
        raise ValueError('material_model must be linear or neo_hookean')

    os.makedirs('I001_Results/OBJ_files', exist_ok=True)
    created = []
    for offset, pressure in enumerate(PRESSURES):
        sim_num = spec.first_sim + offset
        sim_path = f'E001_Simulations/SIM_{sim_num:04d}'
        if not _prepare_simulation_directory(sim_path, replace):
            continue

        obj = _build_object(sim_num, pressure, spec, sim_path)
        obj_path = f'I001_Results/OBJ_files/SIM_{sim_num:04d}.json'
        with open(obj_path, 'w') as output:
            json.dump(asdict(obj), output, indent=4, separators=(',', ': '))
        S6(obj.input_name, obj.input, obj)
        created.append(sim_num)
        print(
            f'Created SIM_{sim_num:04d}: {spec.description}, '
            f'P={pressure:.9f} MPa'
        )
    return created
