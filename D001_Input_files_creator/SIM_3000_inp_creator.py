import sys, os, json, shutil
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from A001_functions.abq_inp_file_creator import *
from dataclasses import asdict

# ---------------------------------------------------------------------------
# SIM_3000's — SIM_1000's mesh/pressure sweep, run with the SIM_3010's solver.
#
# Same mesh (A1000) and pressure sweep as SIM_1000's (P = 0, 0.04*sqrt(2)^i),
# but Step-1 and the material model are taken from SIM_3010's instead of the
# static-stabilize / linear-elastic setup SIM_1000's used for stiffness-
# eigenvalue extraction:
#   - material: linear elastic -> neo-Hookean (*Hyperelastic, neo hooke)
#   - Step-1:   *Static, stabilize, factor=2e-5
#               -> *Dynamic, application=QUASI-STATIC, initial=NO, with mass
#                  scaling (DENSITY below) so the snap-through has a
#                  resolvable duration instead of diverging at the first
#                  bifurcation. See SIM_3010_inp_creator.py for the full
#                  rationale.
#   - Step-1 outputs: 100 -> 200 field frames, ALLVD added to energy output.
#
# This family does NOT do stiffness-eigenvalue extraction (that pipeline,
# A001_functions/stiffness_eigen.py, assumes Step-1 is *Static and does not
# support a *Dynamic base step) - outputs are the plain A/A2/B/C/C2/D
# (+ I/TP/DEFC after a reduce pass) set, identical in shape to SIM_3010's.
# ---------------------------------------------------------------------------

E         = 20
sim_num   = 3000
mesh_file = 'A1000.mesh.json'

# Density in tonne/mm^3 (unit system mm-N-MPa-tonne). Required by *Dynamic.
# Same mass-scaling value as SIM_3010's — see that script for the sizing
# rationale (acoustic transit time ~1% of the 1 s step).
DENSITY = 1e-6

# Step-0 stabilization is unchanged from SIM_1000's.
factor = 2e-5

U_RAMP = -5

Ps = [0.0] + [0.04 * (np.sqrt(2) ** i) for i in range(9)]


for P in Ps:
    os.makedirs('I001_Results/OBJ_files', exist_ok=True)

    path = f'E001_Simulations/SIM_{sim_num:03d}'
    if os.path.exists(path):
        answer = input(f"Folder '{path}' already exists. Replace it? (y/n): ").strip().lower()
        if answer == 'y':
            shutil.rmtree(path)
            os.makedirs(path)
            print(f"Folder '{path}' was replaced.")
        else:
            print("Operation cancelled. Folder was not replaced.")
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
    OBJ.material_model = 'neo_hookean'
    OBJ.t            = 1
    OBJ.ELE_TYPE_3   = "CPS3"
    OBJ.ELE_TYPE_4   = "CPS4"
    OBJ.density_foam = DENSITY
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
        ELE_OUTPUT="S11, S12, S22",
        NODES_OUTPUT="COOR1, COOR2",
        additional_outputs=[f"""** HISTORY OUTPUT: H-Set-y-negative
    *Output, history, time interval={0.005}
    *Node Output, nset=Set-y-negative
    RF2,
    """, f"""** HISTORY OUTPUT: H-Energy
    *Output, history, time interval={0.005}
    *Energy Output
    ALLKE, ALLSE, ALLIE, ALLSD, ALLVD, ALLWK
    """],
        holes_output="",
    )

    OBJ.steps = [step0, step1]

    with open(f'I001_Results/OBJ_files/SIM_{sim_num:03d}.json', 'w') as f:
        json.dump(asdict(OBJ), f, indent=4, separators=(",", ": "))

    print(sim_num)
    S6(OBJ.input_name, OBJ.input, OBJ)
    sim_num += 1
