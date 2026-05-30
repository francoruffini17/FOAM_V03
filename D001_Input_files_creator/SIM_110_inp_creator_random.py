
# functiona. lo que da la tabla son manometros. Si le sumo la presion atmosferica, obtengo presiones absolutas


import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from A001_functions.abq_inp_file_creator import *
import json
import shutil
from dataclasses import asdict


# Estudiar E = 20 y P = 0, 0.25, 0.5, 1, 2 MPa
# Ver por que fallan las simualciones
# Creo que el 5404 con P=2MPa y E = 20 no deberia localizar
# Mejorar la tolerancia
# sino funciona, cambiar a riks
# Update graph to be weighted by the elements lenghts.


E = 20

P = 0.08


sim_num = 110



factors = [0.02, 0.002, 0.00002, 0.000002, 0.0000002]

for factor in factors:
    for i in range(1,6):
        mesh_file = f'R{i:03d}.mesh.json'
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

        # --- Global settings (not step-specific) ---
        OBJ.input_name   = f'C001_Mesh_files/{mesh_file}'
        OBJ.periodic = 'both'

        OBJ.scale_x = 20.0
        OBJ.scale_y = 20.0
        OBJ.input      = f'{path}/SIM_{sim_num:03d}.inp'
        OBJ.E          = E
        OBJ.nu         = 0.3
        OBJ.t          = 1
        OBJ.ELE_TYPE_3   = "CPS3"
        OBJ.ELE_TYPE_4   = "CPS4"
        OBJ.fluid_cavity = """*Molecular Weight
        28.0e-6"""
        OBJ.physical_constants = "*Physical Constants, absolute zero=0, universal gas=8314"
        OBJ.gas_present = True
        OBJ.fluid_cavity_ratio = 1.0 
        OBJ.initial_Temp = 273
        OBJ.initial_Pressure = 0.101325

        # ---------------------------------------------------------------
        # Create the STEP (old Step-0)
        # ---------------------------------------------------------------

        step0 = StepData(
            name="Step-0",

            # Abaqus solver block
            solver=f"""**
        *Step, name=Step-0, nlgeom=YES, inc=99999, unsymm=YES
        *Static, stabilize, factor={factor}, continue=NO
        1e-5, 1., 1e-99, 0.1
        """,

            # --- boundary conditions ---
            # BC_x_n=[None, 0, None, None, None, None],
            # BC_x_p=[None, 0, None, None, None, None],
            # BC_y_n=[0, None, None, None, None, None],
            # BC_y_p=[None, None, None, None, None, None],
            # BC_z_n=[None, None, None, None, None, None],
            # BC_z_p=[None, None, None, None, None, None],
            corner_xnyn_bc = [0, 0, None, None, None, None],
            corner_xpyn_bc = [None, 0, None, None, None, None],


            # --- pressure load ---
            # INT_P=0,# FOR NON VOLUME DEPENDENT PRESSURE
            Pressure_BC=P, # FOR VOLUME DEPENDENT PRESSURE

            # --- outputs ---
            time_interval_out = 0.1,
            frequ_out         = 100,
            out_frames        = 100,
            restart_line      = '',

            ELE_OUTPUT   = "",
            NODES_OUTPUT = "",

            holes_output = ""
        )


        # ---------------------------------------------------------------
        # Create the STEP (old Step-1)
        # ---------------------------------------------------------------

        step1 = StepData(
            name="Step-1",
            # Abaqus solver block
            solver=f"""**
        *Step, name=Step-1, nlgeom=YES, inc=99999, unsymm=YES
        *Static, stabilize, factor={factor}, continue=NO
        1e-5, 1., 1e-99, 0.01
        """,

            # --- boundary conditions ---
            new_boundary = True,
            # BC_x_n=[None, 0, None, None, None, None],
            # BC_x_p=[None, -15, None, None, None, None],
            # BC_y_n=[0, None, None, None, None, None],
            # BC_y_p=[0, None, None, None, None, None],
            # BC_z_n=[None, None, None, None, None, None],
            # BC_z_p=[None, None, None, None, None, None],
            corner_xnyn_bc = [0, 0, None, None, None, None],
            corner_xpyn_bc = [None, 0, None, None, None, None],
            BC_9999997 = [None, -5, None, None, None, None],  # prescribe DA (DOF 1) = 0.1


            # --- pressure load ---
            # INT_P=P,

            # --- outputs ---
            time_interval_out = 0.005,
            frequ_out         = 100,
            out_frames        = 100,
            restart_line      = '',

            ELE_OUTPUT   = "S11, S12, S22",
            NODES_OUTPUT = "COOR1, COOR2",
            additional_outputs = [f"""** HISTORY OUTPUT: H-Set-y-negative
        *Output, history, time interval={0.005}
        *Node Output, nset=Set-y-negative
        RF2,
        """, f"""** HISTORY OUTPUT: H-Energy
        *Output, history, time interval={0.005}
        *Energy Output
        ALLKE, ALLSE, ALLIE, ALLSD, ALLWK
        """],
            holes_output = ""
        )


        # Add step to OBJ
        OBJ.steps = [step0, step1]


        with open(f'I001_Results/OBJ_files/SIM_{sim_num:03d}.json', 'w') as f:
            json.dump(asdict(OBJ), f, indent=4, separators=(",", ": "))

        print(sim_num)
        S6(OBJ.input_name,OBJ.input, OBJ)
        sim_num += 1

    sim_num = (sim_num // 10 + 1) * 10  # Move to the next decade after finishing expansions
# sim_num = (sim_num // 100 + 1) * 100  # Move to the next decade after finishing expansions

