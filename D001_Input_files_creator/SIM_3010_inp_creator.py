import sys, os, json, shutil
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from A001_functions.abq_inp_file_creator import *
from dataclasses import asdict

# ---------------------------------------------------------------------------
# SIM_3010's — instability-friendly re-run of the SIM_2010's sweep.
#
# Same mesh / material / pressure sweep as SIM_2010's (neo-Hookean foam,
# R1000, P = 0, 0.04*sqrt(2)^i).  Only the Step-1 solution procedure changes.
#
# WHY:
#   The 2010's used  *Static, stabilize, factor=2e-5  in the compression step.
#   Every one of them aborted between t = 0.58 and t = 0.93 of the ramp
#   (U2 = -2.8 .. -4.6 out of the -5 target) while the macroscopic load
#   RF2(PERN-9999997) was still rising monotonically — i.e. the solver died
#   at the first bifurcation and never wrote the post-buckling branch.
#   Meanwhile ALLSD/ALLSE stayed at 0.05-1.9%, so the artificial viscous
#   damping was far too weak to push through the instability but still
#   present enough to pollute the localization it was meant to capture.
#   Raising `factor` would trade the crash for smeared localization, which
#   is exactly what we do NOT want here.
#
# WHAT CHANGED (Step-1 only):
#   1. *Static, stabilize  ->  *Dynamic, application=QUASI-STATIC, initial=NO
#      Inertia (not artificial viscosity) regularizes the bifurcation, so the
#      snap-through is integrated through instead of diverged on.  The
#      localization band is a physical outcome, not a damping artefact.
#   2. No stabilization at all in Step-1 -> ALLSD stays flat at its Step-0
#      value (measured: 9.1e-5, i.e. 4.7e-6 of strain energy).
#      NOTE: ALLVD is requested but is NOT a measure of the HHT numerical
#      damping -- it reports material/dashpot viscous dissipation only, and
#      reads exactly 0 here. `application=QUASI-STATIC` uses HHT-alpha with
#      alpha ~ -0.41421 (MAXIMUM algorithmic dissipation), and that dissipation
#      is not reported by any ALL* variable. It is the one artificial ingredient
#      in this family that is not directly quantified -- validate it with a
#      sensitivity run (see below) rather than by reading ALLVD.
#   3. Mass scaling (see DENSITY below) so the snap has a resolvable duration.
#   4. Field output 100 -> 200 frames (every 0.005 of the step) so the instant
#      of localization is actually sampled in space.  History output stays at
#      0.005 as in the 2010's: `*Output, ..., time interval` forces Abaqus onto
#      exact time points, so the history interval is what really caps the
#      increment size.  Keeping it at 0.005 (and setting max increment to match)
#      doubles the field frames at the SAME increment cost as the 2010's.
#
#   Step-0 (pressurization) is left EXACTLY as in the 2010's: all nine runs
#   cleared it without trouble, and keeping it static isolates the change.
#
# ACCEPTANCE CHECK after running:
#   - ALLKE/ALLIE at the end of Step-1 should stay small (~1e-2 or below).
#     If it is larger, the run is no longer quasi-static -> lower DENSITY.
#   - SENSITIVITY CHECK for the two artificial ingredients (mass scaling and
#     HHT numerical damping): re-run one sim with DENSITY/10, or with
#     `application=TRANSIENT FIDELITY` (alpha = -0.05, far less algorithmic
#     damping), and compare shear_mean(eps) and eps*. If eps* moves by only a
#     few percent, neither ingredient is driving the result.
#     Validated so far: over the strain range where the 2010's static runs
#     survived (eps <= 0.148-0.167), shear_mean(eps) of 3011-3014 matches its
#     2010's twin to <0.007% -- so the procedure change does not alter the
#     physics pre-bifurcation. Post-bifurcation has no static reference by
#     construction; that is the part the sensitivity run covers.
#   - If a run still aborts at roughly the same strain as its 2010's twin,
#     the failure is NOT the bifurcation: inspect the .msg (do NOT run
#     run_abq_clean.sh first).  Element distortion / negative Jacobian there
#     points at hole-wall interpenetration, which needs self-contact on the
#     hole surfaces rather than more solver tuning.
# ---------------------------------------------------------------------------

E         = 20
sim_num   = 3010
mesh_file = 'R1000.mesh.json'

# Density in tonne/mm^3 (unit system mm-N-MPa-tonne). Required by *Dynamic.
#
# This is a deliberate MASS SCALING, not the physical wall density (~1e-9).
# Sizing: from the 2010's, secant macroscopic stiffness is E_eff ~ 1.65 MPa
# (RF2 = 6.1 N over a 20x1 mm face at 18.6% strain).  With solid fraction
# ~0.4, rho_eff = 0.4*DENSITY, so the acoustic transit time over the 20 mm
# cell is L/sqrt(E_eff/rho_eff) ~ 0.01 s, i.e. ~1% of the 1 s step.  That
# makes the snap event last ~10-30 output frames instead of falling entirely
# between two of them (which is what rho = 1e-9 would give: transit ~1e-4 s).
# Raise it if runs still stall at the bifurcation; lower it if ALLKE/ALLIE
# comes back too high.
DENSITY = 1e-6

# Step-0 stabilization is unchanged from the 2010's.
factor = 2e-5

U_RAMP = -5

# Applied macroscopic compression on the periodic driver node, in mm (cell is
# 20 mm, so -5 = 25% nominal strain, same as the 2010's).
#
# PAPER_PLAN.md sec.7: the bar is not "reach t = 1", it is that argmin(shear_mean)
# lands INTERIOR so eps* is measurable.  SIM_2010 (P=0) hit its limit by 18.6%
# strain, but SIM_2016 reached 22.8% with the minimum still on the last frame --
# so for the mid-pressure runs the limit is past 22.8% and may be past 25%.
# If the pilot completes the ramp and shear_mean still bottoms out on the last
# frame, extend this (SIM_1100's uses -8) and regenerate.

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
    ALLKE, ALLSE, ALLIE, ALLSD, ALLVD, ALLWK
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
