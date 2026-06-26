"""
SIM_870_inp_creator_random
==========================
Creates input decks for SIM_870, SIM_871, and SIM_872 — a mesh-convergence
study at P = 0.32 (identical to SIM_804) using three mesh densities:

  SIM_870  —  R200  (~27 000 elements, mesh_size = 0.004)
  SIM_871  —  R201  (~15 000 elements, mesh_size = 0.0054)
  SIM_872  —  R202  (~60 000 elements, mesh_size = 0.0027)

All solver parameters (solver type, stabilization factor, BCs, outputs)
are identical to SIM_804.
"""

import sys, os, json, shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from A001_functions.abq_inp_file_creator import *
from dataclasses import asdict


E      = 20
factor = 2e-5
P      = 0.16   # same as SIM_803

SIMS = [
    (875, 'R200.mesh.json'),
    (876, 'R201.mesh.json'),
    (877, 'R202.mesh.json'),
]

for sim_num, mesh_file in SIMS:
    os.makedirs('I001_Results/OBJ_files', exist_ok=True)

    path = f'E001_Simulations/SIM_{sim_num:03d}'
    if os.path.exists(path):
        answer = input(f"Folder '{path}' already exists. Replace it? (y/n): ").strip().lower()
        if answer == "y":
            shutil.rmtree(path)
            os.makedirs(path)
            print(f"Folder '{path}' was replaced.")
        else:
            print("Operation cancelled. Folder was not replaced.")
            continue
    else:
        os.makedirs(path)
        print(f"Folder '{path}' was created.")

    OBJ = data()
    OBJ.input_name   = f'C001_Mesh_files/{mesh_file}'
    OBJ.periodic     = 'both'
    OBJ.scale_x      = 20.0
    OBJ.scale_y      = 20.0
    OBJ.input        = f'{path}/SIM_{sim_num:03d}.inp'
    OBJ.E            = E
    OBJ.nu           = 0.3
    OBJ.t            = 1
    OBJ.ELE_TYPE_3   = "CPS3"
    OBJ.ELE_TYPE_4   = "CPS4"
    OBJ.fluid_cavity = """*Molecular Weight
        28.0e-6"""
    OBJ.physical_constants = "*Physical Constants, absolute zero=0, universal gas=8314"
    OBJ.gas_present        = True
    OBJ.fluid_cavity_ratio = 1.0
    OBJ.initial_Temp       = 273
    OBJ.initial_Pressure   = 0.101325

    step0 = StepData(
        name="Step-0",
        solver=f"""**
    *Step, name=Step-0, nlgeom=YES, inc=99999, unsymm=YES
    *Static, stabilize, factor={factor}, continue=NO
    1e-5, 1., 1e-99, 0.1
    """,
        corner_xnyn_bc=[0, 0, None, None, None, None],
        corner_xpyn_bc=[None, 0, None, None, None, None],
        Pressure_BC=P,
        time_interval_out=0.1,
        frequ_out=100,
        out_frames=100,
        restart_line='',
        ELE_OUTPUT="S11, S12, S22",
        NODES_OUTPUT="COOR1, COOR2",
        additional_outputs=[f"""** HISTORY OUTPUT: H-Set-y-negative
    *Output, history, time interval={0.005}
    *Node Output, nset=Set-y-negative
    RF2,
    """, f"""** HISTORY OUTPUT: H-Energy
    *Output, history, time interval={0.005}
    *Energy Output
    ALLKE, ALLSE, ALLIE, ALLSD, ALLWK
    """],
    )

    step1 = StepData(
        name="Step-1",
        solver=f"""**
    *Step, name=Step-1, nlgeom=YES, inc=99999, unsymm=YES
    *Static, stabilize, factor={factor}, continue=NO
    1e-5, 1., 1e-99, 0.01
    """,
        new_boundary=True,
        corner_xnyn_bc=[0, 0, None, None, None, None],
        corner_xpyn_bc=[None, 0, None, None, None, None],
        BC_9999997=[None, -5, None, None, None, None],
        time_interval_out=0.005,
        frequ_out=100,
        out_frames=100,
        restart_line='',
        ELE_OUTPUT="S11, S12, S22",
        NODES_OUTPUT="COOR1, COOR2",
        additional_outputs=[f"""** HISTORY OUTPUT: H-Set-y-negative
    *Output, history, time interval={0.005}
    *Node Output, nset=Set-y-negative
    RF2,
    """, f"""** HISTORY OUTPUT: H-Energy
    *Output, history, time interval={0.005}
    *Energy Output
    ALLKE, ALLSE, ALLIE, ALLSD, ALLWK
    """],
        holes_output="",
    )

    OBJ.steps = [step0, step1]

    with open(f'I001_Results/OBJ_files/SIM_{sim_num:03d}.json', 'w') as f:
        json.dump(asdict(OBJ), f, indent=4, separators=(",", ": "))

    print(sim_num)
    S6(OBJ.input_name, OBJ.input, OBJ)
