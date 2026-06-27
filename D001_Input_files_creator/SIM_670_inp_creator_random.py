import sys, os, json, shutil
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from A001_functions.abq_inp_file_creator import *
from dataclasses import asdict

# Dynamic Explicit version of the A030 random-mesh sweep (analogous to SIM_600 static).
# Fix: dummy reference nodes 9999997/8/9 get concentrated mass so that *EQUATION
# constraints propagate the prescribed displacement in the Explicit time integrator.
# SMOOTH STEP amplitude eliminates the velocity discontinuity at the start of Step-1
# that was diagnosed in SIM_760-series (WarnNodeDispBCJump in the .msg file).

E      = 20
DENSITY = 1e-9   # tonne/mm³; check ALLKE/ALLIE ratio post-run for quasi-static regime

P = 0.08

sim_num = 670

mesh_files = [
    'A030_005k.mesh.json',
    'A030_010k.mesh.json',
    'A030_020k.mesh.json',
    'A030_040k.mesh.json',
    'A030_080k.mesh.json',
    'A030_160k.mesh.json',
]

for mesh_file in mesh_files:
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
    OBJ.ELE_TYPE_4   = "CPS4R"
    OBJ.density_foam = DENSITY

    # Fluid cavity: ideal gas + heat capacity for Abaqus Explicit adiabatic gas law
    OBJ.fluid_cavity = """*Molecular Weight
        28.0e-6
*Capacity, type=POLYNOMIAL
        29099,"""
    OBJ.physical_constants = "*Physical Constants, absolute zero=0, universal gas=8314"
    OBJ.gas_present        = True
    OBJ.fluid_cavity_ratio = 1.0
    OBJ.initial_Temp       = 273
    OBJ.initial_Pressure   = 0.101325

    # Fixes for Abaqus Explicit + *EQUATION periodic BCs
    OBJ.explicit_dummy_node_mass = 1e-9   # concentrated mass on nodes 9999997/8/9 (tonne)
    OBJ.bc_amplitude             = "SMOOTH STEP"  # ramp displacement 0→target over step

    step0 = StepData(
        name="Step-0",
        solver=f"""**
    *Step, name=Step-0, nlgeom=YES
    *Dynamic, Explicit
    , 1.
    """,
        corner_xnyn_bc=[0, 0, None, None, None, None],
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
    *Step, name=Step-1, nlgeom=YES
    *Dynamic, Explicit
    , 1.
    """,
        new_boundary=True,
        corner_xnyn_bc=[0, 0, None, None, None, None],
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
    sim_num += 1
