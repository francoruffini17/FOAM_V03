from dataclasses import dataclass, field
import os
import subprocess
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from A001_functions.mesh_functions import read_mesh_file, read_surfaces_from_inp, build_hole_surfaces, compute_hole_barycenters, compute_hole_barycenters_2
import re
from A001_functions.Hex_5 import read_mesh_json, scale_mesh, build_individual_surfaces_2


@dataclass
class StepData:
    name: str = "Step-1"
    solver: str = ""
    BC_x_n: list = field(default_factory=lambda: [None]*6)
    BC_x_p: list = field(default_factory=lambda: [None]*6)
    BC_y_n: list = field(default_factory=lambda: [None]*6)
    BC_y_p: list = field(default_factory=lambda: [None]*6)
    BC_z_n: list = field(default_factory=lambda: [None]*6)
    BC_z_p: list = field(default_factory=lambda: [None]*6)

    corner_xnyn_bc: list = field(default_factory=lambda: [None]*6)
    corner_xnyp_bc: list = field(default_factory=lambda: [None]*6)
    corner_xpyn_bc: list = field(default_factory=lambda: [None]*6)
    corner_xpyp_bc: list = field(default_factory=lambda: [None]*6)

    BC_9999997: list = field(default_factory=lambda: [None]*6)

    bound_Temp: str = None
    
    INT_P: float = 0.0

    Pressure_BC: float = None

    out_frames: int = None
    time_interval_out: float = None
    frequ_out: int = None
    restart_line: str = ""

    ELE_OUTPUT: str = ""
    NODES_OUTPUT: str = ""

    additional_outputs: list = field(default_factory=lambda: [""])

    holes_output: str = ""
    new_boundary: bool = False



@dataclass
class data:
    file: str = field(default_factory=str)
    input: str = field(default_factory=str)
    E: float = 200
    nu: float = 0.3
    ELE_TYPE_3: str = "CPE3"
    ELE_TYPE_4: str = "CPE4"
    lim_acc: float = 1e-6
    t_Inclusions: float = None
    inclusions_present: bool = False
    E_Inclusions: float = None
    nu_Inclusions: float = None
    expansion_foam: float = 0
    expansion_Inclusions: float = 0
    steps: list = field(default_factory=list)
    input_name: str = None
    initial_Temp: float = None
    initial_Pressure: float = None
    fluid_cavity: str = None
    physical_constants: str = None
    gas_present: bool = False
    fluid_cavity_ratio: float = 1.0
    scale_x: float = 1.0
    scale_y: float = 1.0
    periodic: str = 'none'



def write_step_block(file,
                     step,
                     nodes,
                     dim_nodes,
                     corner_xnyn,
                     corner_xnyp,
                     corner_xpyn,
                     corner_xpyp,
                     hole_items,
                     holes_barycenters,
                     OBJ):
    """
    Write one Abaqus *Step block (BCs, loads, outputs) using a `step` object.

    Assumes `step` has attributes:
      - name, STEP
      - BC_x_n, BC_x_p, BC_y_n, BC_y_p, BC_z_n, BC_z_p   (lists of length 6)
      - corner_xnyn_bc, corner_xnyp_bc, corner_xpyn_bc, corner_xpyp_bc  (lists of length 6)
      - bound_Temp
      - INT_P
      - restart_line
      - out_frames
      - time_interval_out
      - frequ_out
      - ELE_OUTPUT
      - NODES_OUTPUT
    """

    # -------------------------------------------------------------------------
    # STEP HEADER
    # -------------------------------------------------------------------------
    file.write("** ----------------------------------------------------------------\n")
    file.write("** \n")
    file.write(f"** STEP: {step.name}\n")
    file.write("** \n")
    file.write(step.solver)

    # -------------------------------------------------------------------------
    # BOUNDARY CONDITIONS
    # -------------------------------------------------------------------------
    file.write("** BOUNDARY CONDITIONS \n")

    Lx_max = max(L[0] for L in nodes)
    Ly_max = max(L[1] for L in nodes)
    Lx_min = min(L[0] for L in nodes)
    Ly_min = min(L[1] for L in nodes)

    DLx = Lx_max - Lx_min
    DLy = Ly_max - Ly_min

    if dim_nodes == 3:
        Lz_max = max(L[2] for L in nodes)
        Lz_min = min(L[2] for L in nodes)
        DLz = Lz_max - Lz_min
    else:
        Lz_max = 0
        Lz_min = 0
        DLz = 0

    # Face BCs (x/y/z ±)
    if step.new_boundary is True:
        file.write("*Boundary, op=NEW\n")
    else:
        file.write("*Boundary\n")

    for i in range(6):
        if step.BC_x_n[i] is not None:
            file.write(f"Set-x-negative, {i+1}, {i+1}, {step.BC_x_n[i]}\n")

        if step.BC_x_p[i] is not None:
            file.write(f"Set-x-positive, {i+1}, {i+1}, {step.BC_x_p[i]}\n")

        if step.BC_y_n[i] is not None:
            file.write(f"Set-y-negative, {i+1}, {i+1}, {step.BC_y_n[i]}\n")

        if step.BC_y_p[i] is not None:
            
            file.write(f"Set-y-positive, {i+1}, {i+1}, {step.BC_y_p[i]}\n")

        if dim_nodes == 3:
            if step.BC_z_n[i] is not None:
                file.write(f"Set-z-negative, {i+1}, {i+1}, {step.BC_z_n[i]}\n")

            if step.BC_z_p[i] is not None:
                file.write(f"Set-z-positive, {i+1}, {i+1}, {step.BC_z_p[i]}\n")

    # Corner BCs
    for i in range(6):
        if (step.corner_xnyn_bc[i] is not None) and (corner_xnyn is not None):
            file.write(f"Part-1-1.{corner_xnyn}, {i+1}, {i+1}, {step.corner_xnyn_bc[i]}\n")

        if (step.corner_xnyp_bc[i] is not None) and (corner_xnyp is not None):
            file.write(f"Part-1-1.{corner_xnyp}, {i+1}, {i+1}, {step.corner_xnyp_bc[i]}\n")

        if (step.corner_xpyn_bc[i] is not None) and (corner_xpyn is not None):
            file.write(f"Part-1-1.{corner_xpyn}, {i+1}, {i+1}, {step.corner_xpyn_bc[i]}\n")

        if (step.corner_xpyp_bc[i] is not None) and (corner_xpyp is not None):
            file.write(f"Part-1-1.{corner_xpyp}, {i+1}, {i+1}, {step.corner_xpyp_bc[i]}\n")

    # Dummy node 9999997 BCs (DA=DOF1, DB=DOF2)
    for i in range(6):
        if step.BC_9999997[i] is not None:
            file.write(f"PERN-9999997, {i+1}, {i+1}, {step.BC_9999997[i]}\n")

    # Temperature predefined field (optional)
    if step.bound_Temp is not None:
        file.write("** PREDEFINED FIELDS\n")
        file.write("** \n")
        file.write("** Name: Predefined Field-1   Type: Temperature\n")
        file.write("*Temperature\n")
        file.write(f"PART-1-1.FOAM, {step.bound_Temp}\n")



    if OBJ.gas_present is True and step.Pressure_BC is not None:
        file.write(f"** BOUNDARY CONDITIONS\n")
        file.write(f"** \n")
        file.write(f"** Name: BC-3 Type: Fluid cavity pressure\n")
        for name, (x, y) in holes_barycenters.items():
            # extract number after last hyphen
            idx = int(name.split("-")[-1])
            hole_items.append((idx, x, y))
            file.write(f"SET-{idx} , 8, 8, {step.Pressure_BC}\n")       

        file.write(f"** \n")




    # -------------------------------------------------------------------------
    # LOADS
    # -------------------------------------------------------------------------
    if step.INT_P is not None and step.INT_P > 0.0:
        file.write("** LOADS\n")
        file.write("** \n")
        file.write("** Name: Load-1   Type: Pressure\n")
        file.write("*Dsload\n")
        file.write(f"PART-1-1.SURFACE-INTERNAL, P, {step.INT_P}\n")
        file.write("** \n")

    # -------------------------------------------------------------------------
    # OUTPUT REQUESTS
    # -------------------------------------------------------------------------
    file.write("** OUTPUT REQUESTS\n")
    file.write("** \n")

    # restart line (step-specific)
    if getattr(step, "restart_line", None) is not None:
        file.write(step.restart_line)
        file.write("** \n")

    # Field output
    file.write("** FIELD OUTPUT: F-Output-1\n")
    file.write("** \n")
    file.write(f"*Output, field, variable=PRESELECT, number interval={step.out_frames}\n")

    # -------------------------------------------------------------------------
    # HISTORY OUTPUTS: RF / RM and U
    # -------------------------------------------------------------------------
    nsets_and_BCs = [
        ("Set-x-negative", step.BC_x_n),
        ("Set-x-positive", step.BC_x_p),
        ("Set-y-negative", step.BC_y_n),
        ("Set-y-positive", step.BC_y_p),
    ]

    if dim_nodes == 3:
        nsets_and_BCs.extend([
            ("Set-z-negative", step.BC_z_n),
            ("Set-z-positive", step.BC_z_p),
        ])

    # First RF / RM
    for nset_name, BC in nsets_and_BCs:
        file.write("**\n")
        for i in range(6):
            if BC[i] is not None:
                file.write("**\n")
                file.write(f"** HISTORY OUTPUT: H-{nset_name}\n")

                if step.time_interval_out is not None:
                    file.write(f"*Output, history, time interval={step.time_interval_out}\n")
                elif step.frequ_out is not None:
                    file.write(f"*Output, history, frequency={step.frequ_out}\n")
                else:
                    file.write("*Output, history\n")

                file.write(f"*Node Output, nset={nset_name}\n")

                if i < 3:
                    file.write(f"RF{i+1},\n")
                else:
                    file.write(f"RM{i+1-3},\n")

                file.write("** \n")


    for add in step.additional_outputs:
        file.write(add)

    # Then U
    for nset_name, BC in nsets_and_BCs:
        file.write("**\n")
        for i in range(6):
            if BC[i] is not None:
                file.write("**\n")
                file.write(f"** HISTORY OUTPUT: H-{nset_name}\n")

                if step.time_interval_out is not None:
                    file.write(f"*Output, history, time interval={step.time_interval_out}\n")
                elif step.frequ_out is not None:
                    file.write(f"*Output, history, frequency={step.frequ_out}\n")
                else:
                    file.write("*Output, history\n")

                file.write(f"*Node Output, nset={nset_name}\n")

                if i < 3:
                    file.write(f"U{i+1},\n")
                else:
                    file.write(f"U{i+1-3},\n")

                file.write("** \n")

    # -------------------------------------------------------------------------
    # ELEMENT HISTORY OUTPUT
    # -------------------------------------------------------------------------
    if step.ELE_OUTPUT and len(step.ELE_OUTPUT) > 0:
        file.write("** HISTORY OUTPUT: H-Output-elements\n")
        file.write("**\n")

        if step.time_interval_out is not None:
            file.write(f"*Output, history, time interval={step.time_interval_out}\n")
        elif step.frequ_out is not None:
            file.write(f"*Output, history, frequency={step.frequ_out}\n")
        else:
            file.write("*Output, history\n")

        file.write("*Element Output, elset=PART-1-1.EALL\n")
        file.write(f"{step.ELE_OUTPUT}\n")

    # -------------------------------------------------------------------------
    # NODE HISTORY OUTPUT
    # -------------------------------------------------------------------------
    if step.NODES_OUTPUT and len(step.NODES_OUTPUT) > 0:
        file.write("** HISTORY OUTPUT: H-Output-nodes\n")
        file.write("**\n")

        if step.time_interval_out is not None:
            file.write(f"*Output, history, time interval={step.time_interval_out}\n")
        elif step.frequ_out is not None:
            file.write(f"*Output, history, frequency={step.frequ_out}\n")
        else:
            file.write("*Output, history\n")

        file.write("*Node Output, nset=PART-1-1.FOAM\n")
        file.write(f"{step.NODES_OUTPUT}\n")
        


    # output cavities
    if len(step.holes_output)>0:


        for name, (x, y) in holes_barycenters.items():
            # extract number after last hyphen
            idx = int(name.split("-")[-1])

            if step.time_interval_out is not None:
                file.write(f"*Output, history, time interval={step.time_interval_out}\n")
            elif step.frequ_out is not None:
                file.write(f"*Output, history, frequency={step.frequ_out}\n")
            else:
                file.write("*Output, history\n")

            file.write(f"*Node Output, nset=SET-{idx}\n")
            file.write(f"{step.holes_output}\n")

    # -------------------------------------------------------------------------
    # DUMMY NODE 9999997 HISTORY OUTPUT (RF for constrained DOFs)
    # -------------------------------------------------------------------------
    for i in range(6):
        if step.BC_9999997[i] is not None:
            file.write("**\n")
            file.write(f"** HISTORY OUTPUT: H-PERN-9999997-RF{i+1}\n")

            if step.time_interval_out is not None:
                file.write(f"*Output, history, time interval={step.time_interval_out}\n")
            elif step.frequ_out is not None:
                file.write(f"*Output, history, frequency={step.frequ_out}\n")
            else:
                file.write("*Output, history\n")

            file.write(f"*Node Output, nset=PERN-9999997\n")
            file.write(f"RF{i+1},\n")
            file.write("** \n")


    # -------------------------------------------------------------------------
    # DUMMY NODE 9999997 HISTORY OUTPUT (RF for constrained DOFs)
    # -------------------------------------------------------------------------
    for i in range(6):
        if step.BC_9999997[i] is not None:
            file.write("**\n")
            file.write(f"** HISTORY OUTPUT: H-PERN-9999997-U{i+1}\n")

            if step.time_interval_out is not None:
                file.write(f"*Output, history, time interval={step.time_interval_out}\n")
            elif step.frequ_out is not None:
                file.write(f"*Output, history, frequency={step.frequ_out}\n")
            else:
                file.write("*Output, history\n")

            file.write(f"*Node Output, nset=PERN-9999997\n")
            file.write(f"U{i+1},\n")
            file.write("** \n")


    # -------------------------------------------------------------------------
    # END STEP
    # -------------------------------------------------------------------------
    file.write("*End Step\n")





    

def get_node_limits(nodes):
    """
    nodes: list of 2D or 3D coordinates
    returns: list of (min, max) for each coordinate
             e.g. 2D → [ (xmin, xmax), (ymin, ymax) ]
                  3D → [ (xmin, xmax), (ymin, ymax), (zmin, zmax) ]
    """

    dim = len(nodes[0])   # detect 2D or 3D automatically

    # Initialize mins/maxs
    mins = [float('inf')] * dim
    maxs = [-float('inf')] * dim

    # Loop through nodes
    for p in nodes:
        for i in range(dim):
            if p[i] < mins[i]:
                mins[i] = p[i]
            if p[i] > maxs[i]:
                maxs[i] = p[i]

    # Pack result
    limits = [(mins[i], maxs[i]) for i in range(dim)]
    return limits



def S6(input_name,output_name, OBJ):


    if not str(input_name).endswith(".mesh.json"):
        raise ValueError("Unsupported mesh file. Abaqus input creation expects a .mesh.json file.")

    nodes_raw, elements, mesh_payload = read_mesh_json(input_name, include_metadata=True)
    nodes, elements, individual_surfaces, individual_ele_sets, external_surfaces = build_individual_surfaces_2(nodes_raw, elements)
    nodes = scale_mesh(nodes, OBJ.scale_x, OBJ.scale_y, len=2)

    # Build mapping: hole_number -> B digit from node labels (format 1ABX...).
    # B=5 means complete hole; B!=5 means cut by an edge, so remove it here.
    hole_B_digit = {}
    for _, _, nid in nodes_raw:
        nid_str = str(nid)
        if len(nid_str) >= 4:
            b_digit = nid_str[2]
            hole_num = int(nid_str[3:])
            if hole_num not in hole_B_digit:
                hole_B_digit[hole_num] = b_digit

    keys_to_delete = [
        f'Surface-hole-{h}' for h, b in hole_B_digit.items() if b != '5'
    ]
    for key in keys_to_delete:
        if key in individual_surfaces:
            del individual_surfaces[key]

    holes_surfaces = individual_surfaces.copy()
    dim_nodes = len(nodes[0])
    holes_barycenters = compute_hole_barycenters_2(holes_surfaces, elements, nodes)
    



    # Create elements and nodes
    with open(output_name, "w") as file:
        file.write("*Heading\n")
        # file.write("*Preprint, echo=NO, model=NO, history=NO, contact=NO\n")
        file.write("**\n")
        file.write("** PARTS\n")
        file.write("**\n")
        file.write("*Part, name=Part-1\n")
        file.write("*Node, nset=FOAM\n")
        for i, point in enumerate(nodes):
            file.write(f"{i+1}, {point[0]}, {point[1]}\n")
        
        # Separate triangular and quadrilateral elements
        tri_elements = [(i, elem) for i, elem in enumerate(elements) if len(elem) == 3]
        quad_elements = [(i, elem) for i, elem in enumerate(elements) if len(elem) == 4]

        # Validate all elements
        for i, elem in enumerate(elements):
            if len(elem) not in (3, 4):
                raise ValueError(f"Unsupported element {i+1} with {len(elem)} nodes.")

        # Write triangular elements
        if tri_elements:
            file.write(f"*Element, type={OBJ.ELE_TYPE_3}, elset=EALL_TRI\n")
            for i, element in tri_elements:
                file.write(f"{i+1}, {element[0]}, {element[1]}, {element[2]}\n")

        # Write quadrilateral elements
        if quad_elements:
            file.write(f"*Element, type={OBJ.ELE_TYPE_4}, elset=EALL_QUAD\n")
            for i, element in quad_elements:
                file.write(f"{i+1}, {element[0]}, {element[1]}, {element[2]}, {element[3]}\n")

        # Create combined element set
        file.write("*Elset, elset=EALL\n")
        if tri_elements and quad_elements:
            file.write("EALL_TRI, EALL_QUAD\n")
        elif tri_elements:
            file.write("EALL_TRI\n")
        else:
            file.write("EALL_QUAD\n")

        file.write("*Nset, nset=Set-1, generate\n")
        file.write(f"1,  {len(nodes)},   1\n")


        

        # Print element sets in multi-line comma-separated format
        # THIS SET IS NOT USED, SO IT CAN BE SKIPPTED
        for key, values in individual_ele_sets.items():

            file.write(f"*Elset, elset={key}\n")  # print the elset name

            # Chunk values into lines of ~12–16 numbers each (adjust size if you want)
            chunk_size = 16
            for i in range(0, len(values), chunk_size):
                chunk = values[i:i+chunk_size]
                file.write(", ".join(str(v) for v in chunk) + '\n')


        keys = list(individual_ele_sets.keys())
        if OBJ.inclusions_present == True:

            file.write("*Elset, elset=Set-Foam\n")
            file.write(keys[-1] + '\n')

            file.write("*Elset, elset=Set-Inclusions\n")
            keys_to_use = keys[:-1]   # all but last
            for i in range(0, len(keys_to_use), 16):
                line = keys_to_use[i:i+16]
                file.write(", ".join(line) + '\n')

        else:
            file.write("*Elset, elset=Set-Foam, generate\n")
            file.write(f"1,  {len(elements)},    1\n")
    

        file.write("** Section: Section-Foam\n")
        file.write("*Solid Section, elset=Set-Foam, material=Material-Foam\n")
        file.write(f"{OBJ.t},\n")

        if OBJ.inclusions_present == True:
            file.write("** Section: Section-Inclusions\n")
            file.write("*Solid Section, elset=Set-Inclusions, material=Material-Inclusions\n")
            file.write(f"{OBJ.t_Inclusions},\n")

        all_ext_surfaces = sum(external_surfaces.values(), [])

        # Internal surfaces
        if len(individual_surfaces)>0:
            file.write("*Surface, name=Surface-internal, type=element\n")
        for surface_key in individual_surfaces:
            if surface_key not in all_ext_surfaces:
                for elem, surf in individual_surfaces[surface_key]:
                    file.write(f"{elem}, {surf}\n")


        file.write("*End Part\n")


        file.write("**  \n")
        file.write("**\n")



        file.write("** ASSEMBLY\n")
        file.write("**\n")
        file.write("*Assembly, name=Assembly\n")
        file.write("**  \n")
        file.write("*Instance, name=Part-1-1, part=Part-1\n")
        file.write("*End Instance\n")


        


        # --- Classify boundary nodes using the A digit of node ID (1ABX..) ---
        # A=2,5,6 → x_negative   A=4,6,7 → x_positive
        # A=1,5,7 → y_negative   A=3,6,8 → y_positive
        # Corners: A=5 → xnyn, A=7 → xnyp, A=8 → xpyn, A=6 → xpyp

        nodes_x_negative = []
        nodes_y_negative = []
        nodes_x_positive = []
        nodes_y_positive = []
        corner_xnyn = None
        corner_xnyp = None
        corner_xpyn = None
        corner_xpyp = None

        for idx, (_, _, nid) in enumerate(nodes_raw):
            nid_str = str(nid)
            if len(nid_str) < 2:
                continue
            A = nid_str[1]  # second digit of 1ABX..

            node_num = idx + 1  # 1-based node number in the output

            if A in ('2', '5', '8'):
                nodes_x_negative.append(node_num)
            if A in ('4', '6', '7'):
                nodes_x_positive.append(node_num)
            if A in ('1', '5', '7'):
                nodes_y_negative.append(node_num)
            if A in ('3', '6', '8'):
                nodes_y_positive.append(node_num)

            # Corner nodes
            if A == '5':
                corner_xnyn = node_num
            elif A == '7':
                corner_xnyp = node_num
            elif A == '8':
                corner_xpyn = node_num
            elif A == '6':
                corner_xpyp = node_num


        # Write node sets for x-negative
        file.write(f'*Nset, nset=Set-x-negative, instance=Part-1-1\n')       
        for l in range(0, len(nodes_x_negative), 16):
            STR = "".join(f"  {num:4d}," for num in nodes_x_negative[l:l+16])
            file.write(STR[:-1]+'\n')

        # Write node sets for x-positive
        file.write(f'*Nset, nset=Set-x-positive, instance=Part-1-1\n')    
        for l in range(0, len(nodes_x_positive), 16):
            STR = "".join(f"  {num:4d}," for num in nodes_x_positive[l:l+16])
            file.write(STR[:-1]+'\n')

        # Write node sets for y-negative
        file.write(f'*Nset, nset=Set-y-negative, instance=Part-1-1\n')       
        for l in range(0, len(nodes_y_negative), 16):
            STR = "".join(f"  {num:4d}," for num in nodes_y_negative[l:l+16])
            file.write(STR[:-1]+'\n')

        # Write node sets for y-positive
        file.write(f'*Nset, nset=Set-y-positive, instance=Part-1-1\n')       
        for l in range(0, len(nodes_y_positive), 16):
            STR = "".join(f"  {num:4d}," for num in nodes_y_positive[l:l+16])
            file.write(STR[:-1]+'\n')



        # write RP
        hole_items = []
        for name, (x, y) in holes_barycenters.items():
            # extract number after last hyphen
            idx = int(name.split("-")[-1])
            hole_items.append((idx, x, y))

        hole_items.sort(key=lambda t: t[0])

        file.write(f"**\n")
        file.write("*Node\n")
        for idx, x, y in hole_items:
            file.write(f"{idx:7d}, {x:12.7f}, {y:12.7f}, {0.0:12.7f}\n")

        # FFF
        #Create dummy nodes
        file.write(f"9999997, 0., 0.,\n")
        file.write(f"9999998, 0., 0.,\n")
        file.write(f"9999999, 0., 0.,\n")
            
        # Create surface for each hole
        for surf_name, entries in holes_surfaces.items():
            file.write(f"*Surface, name={surf_name}, type=element\n")
            for elem, face in entries:
                file.write(f"PART-1-1.{elem}, {face}\n")



        #Create nodeset for each RP

        for idx, x, y in hole_items:
            file.write(f"**\n")
            file.write(f"*Nset, nset=Set-{idx}\n")
            file.write(f"{idx:7d}\n")

        

        # --- Periodic BC: build matching pairs from node labels (1ABX..) ----
        #   A=1 left, A=2 bottom, A=3 right, A=4 top
        #   A=5 BL corner, A=6 TR corner, A=7 TL corner, A=8 BR corner
        # Only 'both' is supported (LR + UL simultaneously)
        # Dummy nodes: 9999997 → DA (DOF1), DB (DOF2)
        #              9999998 → DC (DOF1)
        #              9999999 → reserved
        _periodic = getattr(OBJ, 'periodic', 'none').strip().lower()
        if _periodic == 'tb':
            _periodic = 'ul'
        periodic_json = mesh_payload.get("periodic", {})
        json_pairs_lr = [tuple(pair) for pair in periodic_json.get("left_right_pairs", [])]
        json_pairs_ul = [
            (bottom, top)
            for top, bottom in periodic_json.get("top_bottom_pairs", [])
        ]

        if _periodic not in ('none', 'both', 'lr', 'ul'):
            print(f"periodic='{_periodic}' not implemented yet")

        if _periodic == 'both':
            # -- Collect edge nodes (no corners) and corner nodes ---------------
            #    Left  A=1, Right A=3   matched by y
            #    Bottom A=2, Top  A=4   matched by x
            left_nodes   = []  # (0-based idx, y_coord)
            right_nodes  = []
            bottom_nodes = []  # (0-based idx, x_coord)
            top_nodes    = []
            corner_BL = None   # A=5  (0-based idx)
            corner_TR = None   # A=6
            corner_TL = None   # A=7
            corner_BR = None   # A=8

            for idx, (x, y, nid) in enumerate(nodes_raw):
                nid_str = str(nid)
                if len(nid_str) < 2:
                    continue
                A = nid_str[1]
                if A == '1':
                    left_nodes.append((idx, y))
                elif A == '3':
                    right_nodes.append((idx, y))
                elif A == '2':
                    bottom_nodes.append((idx, x))
                elif A == '4':
                    top_nodes.append((idx, x))
                elif A == '5':
                    corner_BL = idx
                elif A == '6':
                    corner_TR = idx
                elif A == '7':
                    corner_TL = idx
                elif A == '8':
                    corner_BR = idx

            # Sort and pair LR by y, UL by x
            if json_pairs_lr:
                pairs_lr = json_pairs_lr
            else:
                left_nodes.sort(key=lambda t: t[1])
                right_nodes.sort(key=lambda t: t[1])
                if len(left_nodes) != len(right_nodes):
                    raise ValueError(
                        f"LR periodic: {len(left_nodes)} left-edge nodes "
                        f"vs {len(right_nodes)} right-edge nodes - mismatch"
                    )
                pairs_lr = [(li, ri) for (li, _), (ri, _) in zip(left_nodes, right_nodes)]

            if json_pairs_ul:
                pairs_ul = json_pairs_ul
            else:
                bottom_nodes.sort(key=lambda t: t[1])
                top_nodes.sort(key=lambda t: t[1])
                if len(bottom_nodes) != len(top_nodes):
                    raise ValueError(
                        f"UL periodic: {len(bottom_nodes)} bottom-edge nodes "
                        f"vs {len(top_nodes)} top-edge nodes - mismatch"
                    )
                pairs_ul = [(bi, ti) for (bi, _), (ti, _) in zip(bottom_nodes, top_nodes)]

            # -- Collect every node that needs a PERN nset ----------------------
            per_nodes = set()
            for a, b in pairs_lr:
                per_nodes.add(a)
                per_nodes.add(b)
            for a, b in pairs_ul:
                per_nodes.add(a)
                per_nodes.add(b)
            for c in (corner_BL, corner_TR, corner_TL, corner_BR):
                if c is not None:
                    per_nodes.add(c)

            # Write one nset per periodic mesh node (inside the Assembly block)
            for nd_0 in sorted(per_nodes):
                nd_1 = nd_0 + 1  # 0-based → 1-based
                file.write(f"*Nset, nset=PERN-{nd_1}, instance=Part-1-1\n")
                file.write(f"{nd_1}\n")

            # Nsets for the three dummy nodes
            for dn in (9999997, 9999998, 9999999):
                file.write(f"*Nset, nset=PERN-{dn}\n")
                file.write(f"{dn}\n")

            # -- Constraint equations -------------------------------------------
            file.write("** ----------------------------------------------------------------\n")
            file.write("** PERIODIC BOUNDARY CONDITIONS\n")
            file.write("** ----------------------------------------------------------------\n")
            con_n = 1

            # 1) LR edge pairs  (left A=1 ↔ right A=3, no corners)
            #    ur - ul - DA = 0   (DOF 1)
            #    vr - vl      = 0   (DOF 2)
            for li, ri in pairs_lr:
                L = li + 1
                R = ri + 1
                # ur - ul - DA = 0
                file.write(f"** Constraint: Constraint-{con_n}\n")
                file.write("*Equation\n")
                file.write("3\n")
                file.write(f"PERN-{R}, 1, 1.\n")
                file.write(f"PERN-{L}, 1, -1.\n")
                file.write(f"PERN-9999997, 1, -1.\n")
                con_n += 1

                # vr - vl = 0
                file.write(f"** Constraint: Constraint-{con_n}\n")
                file.write("*Equation\n")
                file.write("2\n")
                file.write(f"PERN-{R}, 2, 1.\n")
                file.write(f"PERN-{L}, 2, -1.\n")
                con_n += 1

            # 2) UL edge pairs  (bottom A=2 ↔ top A=4, no corners)
            #    uu - ul - DC = 0   (DOF 1)
            #    vu - vl - DB = 0   (DOF 2)
            for bi, ti in pairs_ul:
                B = bi + 1
                T = ti + 1
                # uu - ul - DC = 0
                file.write(f"** Constraint: Constraint-{con_n}\n")
                file.write("*Equation\n")
                file.write("3\n")
                file.write(f"PERN-{T}, 1, 1.\n")
                file.write(f"PERN-{B}, 1, -1.\n")
                file.write(f"PERN-9999998, 1, -1.\n")
                con_n += 1

                # vu - vl - DB = 0
                file.write(f"** Constraint: Constraint-{con_n}\n")
                file.write("*Equation\n")
                file.write("3\n")
                file.write(f"PERN-{T}, 2, 1.\n")
                file.write(f"PERN-{B}, 2, -1.\n")
                file.write(f"PERN-9999997, 2, -1.\n")
                con_n += 1

            # 3) Corner equations
            #    BL=5, BR=8, TL=7, TR=6
            BL = corner_BL + 1
            BR = corner_BR + 1
            TL = corner_TL + 1
            TR = corner_TR + 1

            # u8 - u5 - DA = 0
            file.write(f"** Constraint: Constraint-{con_n}\n")
            file.write("*Equation\n")
            file.write("3\n")
            file.write(f"PERN-{BR}, 1, 1.\n")
            file.write(f"PERN-{BL}, 1, -1.\n")
            file.write(f"PERN-9999997, 1, -1.\n")
            con_n += 1

            # v8 - v5 = 0
            file.write(f"** Constraint: Constraint-{con_n}\n")
            file.write("*Equation\n")
            file.write("2\n")
            file.write(f"PERN-{BR}, 2, 1.\n")
            file.write(f"PERN-{BL}, 2, -1.\n")
            con_n += 1

            # u7 - u5 - DC = 0
            file.write(f"** Constraint: Constraint-{con_n}\n")
            file.write("*Equation\n")
            file.write("3\n")
            file.write(f"PERN-{TL}, 1, 1.\n")
            file.write(f"PERN-{BL}, 1, -1.\n")
            file.write(f"PERN-9999998, 1, -1.\n")
            con_n += 1

            # v7 - v5 - DB = 0
            file.write(f"** Constraint: Constraint-{con_n}\n")
            file.write("*Equation\n")
            file.write("3\n")
            file.write(f"PERN-{TL}, 2, 1.\n")
            file.write(f"PERN-{BL}, 2, -1.\n")
            file.write(f"PERN-9999997, 2, -1.\n")
            con_n += 1

            # u6 - u5 - DA - DC = 0
            file.write(f"** Constraint: Constraint-{con_n}\n")
            file.write("*Equation\n")
            file.write("4\n")
            file.write(f"PERN-{TR}, 1, 1.\n")
            file.write(f"PERN-{BL}, 1, -1.\n")
            file.write(f"PERN-9999997, 1, -1.\n")
            file.write(f"PERN-9999998, 1, -1.\n")
            con_n += 1

            # v6 - v5 - DB = 0
            file.write(f"** Constraint: Constraint-{con_n}\n")
            file.write("*Equation\n")
            file.write("3\n")
            file.write(f"PERN-{TR}, 2, 1.\n")
            file.write(f"PERN-{BL}, 2, -1.\n")
            file.write(f"PERN-9999997, 2, -1.\n")
            con_n += 1

            file.write("** \n")

        # =================================================================
        # periodic = 'lr'  —  LR only (corners INCLUDED in LR pairs)
        # =================================================================
        if _periodic == 'lr':
            # Left A∈{1,5,7} ↔ Right A∈{3,8,6}  matched by y
            left_nodes  = []   # (0-based idx, y_coord)
            right_nodes = []

            for idx, (x, y, nid) in enumerate(nodes_raw):
                nid_str = str(nid)
                if len(nid_str) < 2:
                    continue
                A = nid_str[1]
                if A in ('1', '5', '7'):
                    left_nodes.append((idx, y))
                if A in ('3', '8', '6'):
                    right_nodes.append((idx, y))

            if json_pairs_lr:
                pairs_lr = json_pairs_lr
            else:
                left_nodes.sort(key=lambda t: t[1])
                right_nodes.sort(key=lambda t: t[1])
                if len(left_nodes) != len(right_nodes):
                    raise ValueError(
                        f"LR periodic: {len(left_nodes)} left-edge nodes "
                        f"vs {len(right_nodes)} right-edge nodes - mismatch"
                    )
                pairs_lr = [(li, ri) for (li, _), (ri, _) in zip(left_nodes, right_nodes)]

            # Nsets for periodic mesh nodes
            per_nodes = set()
            for a, b in pairs_lr:
                per_nodes.add(a)
                per_nodes.add(b)
            for nd_0 in sorted(per_nodes):
                nd_1 = nd_0 + 1
                file.write(f"*Nset, nset=PERN-{nd_1}, instance=Part-1-1\n")
                file.write(f"{nd_1}\n")

            # Nsets for dummy nodes
            for dn in (9999997, 9999998, 9999999):
                file.write(f"*Nset, nset=PERN-{dn}\n")
                file.write(f"{dn}\n")

            # Constraint equations
            file.write("** ----------------------------------------------------------------\n")
            file.write("** PERIODIC BOUNDARY CONDITIONS  (LR)\n")
            file.write("** ----------------------------------------------------------------\n")
            con_n = 1

            for li, ri in pairs_lr:
                L = li + 1
                R = ri + 1
                # ur - ul - DA = 0
                file.write(f"** Constraint: Constraint-{con_n}\n")
                file.write("*Equation\n")
                file.write("3\n")
                file.write(f"PERN-{R}, 1, 1.\n")
                file.write(f"PERN-{L}, 1, -1.\n")
                file.write(f"PERN-9999997, 1, -1.\n")
                con_n += 1

                # vr - vl = 0
                file.write(f"** Constraint: Constraint-{con_n}\n")
                file.write("*Equation\n")
                file.write("2\n")
                file.write(f"PERN-{R}, 2, 1.\n")
                file.write(f"PERN-{L}, 2, -1.\n")
                con_n += 1

            file.write("** \n")

        # =================================================================
        # periodic = 'ul'  —  UL only (corners INCLUDED in UL pairs)
        # =================================================================
        if _periodic == 'ul':
            # Bottom A∈{2,5,8} ↔ Top A∈{4,7,6}  matched by x
            bottom_nodes = []   # (0-based idx, x_coord)
            top_nodes    = []

            for idx, (x, y, nid) in enumerate(nodes_raw):
                nid_str = str(nid)
                if len(nid_str) < 2:
                    continue
                A = nid_str[1]
                if A in ('2', '5', '8'):
                    bottom_nodes.append((idx, x))
                if A in ('4', '7', '6'):
                    top_nodes.append((idx, x))

            if json_pairs_ul:
                pairs_ul = json_pairs_ul
            else:
                bottom_nodes.sort(key=lambda t: t[1])
                top_nodes.sort(key=lambda t: t[1])
                if len(bottom_nodes) != len(top_nodes):
                    raise ValueError(
                        f"UL periodic: {len(bottom_nodes)} bottom-edge nodes "
                        f"vs {len(top_nodes)} top-edge nodes - mismatch"
                    )
                pairs_ul = [(bi, ti) for (bi, _), (ti, _) in zip(bottom_nodes, top_nodes)]

            # Nsets for periodic mesh nodes
            per_nodes = set()
            for a, b in pairs_ul:
                per_nodes.add(a)
                per_nodes.add(b)
            for nd_0 in sorted(per_nodes):
                nd_1 = nd_0 + 1
                file.write(f"*Nset, nset=PERN-{nd_1}, instance=Part-1-1\n")
                file.write(f"{nd_1}\n")

            # Nsets for dummy nodes
            for dn in (9999997, 9999998, 9999999):
                file.write(f"*Nset, nset=PERN-{dn}\n")
                file.write(f"{dn}\n")

            # Constraint equations
            file.write("** ----------------------------------------------------------------\n")
            file.write("** PERIODIC BOUNDARY CONDITIONS  (UL)\n")
            file.write("** ----------------------------------------------------------------\n")
            con_n = 1

            for bi, ti in pairs_ul:
                B = bi + 1
                T = ti + 1
                # uu - ul = 0
                file.write(f"** Constraint: Constraint-{con_n}\n")
                file.write("*Equation\n")
                file.write("2\n")
                file.write(f"PERN-{T}, 1, 1.\n")
                file.write(f"PERN-{B}, 1, -1.\n")
                con_n += 1

                # vu - vl - DB = 0
                file.write(f"** Constraint: Constraint-{con_n}\n")
                file.write("*Equation\n")
                file.write("3\n")
                file.write(f"PERN-{T}, 2, 1.\n")
                file.write(f"PERN-{B}, 2, -1.\n")
                file.write(f"PERN-9999997, 2, -1.\n")
                con_n += 1

            file.write("** \n")



        file.write("**  \n")
        file.write("*End Assembly\n")
        file.write("** \n")


        file.write("** MATERIALS\n")
        file.write("** \n")
        file.write("*Material, name=Material-Foam\n")
        file.write("*Elastic\n")
        file.write(f"{OBJ.E}, {OBJ.nu}\n")
        file.write(f"*Expansion\n")
        file.write(f"{OBJ.expansion_foam},\n")



        if OBJ.fluid_cavity is not None:
            file.write(f"** INTERACTION PROPERTIES\n")
            file.write(f"** \n")
            file.write(f"*Fluid Behavior, name=Cavity_property\n")
            file.write(f"{OBJ.fluid_cavity}\n") 
            # https://classes.engineering.wustl.edu/2009/spring/mase5513/abaqus/docs/v6.6/books/key/default.htm?startat=ch06abk16.html#usb-kws-mfluidcavity
            # Out-of-plane thickness of the surface for two-dimensional models when the SURFACE parameter is included. If this value is left blank or is entered as zero, the default value of 1.0 will be used. Enter a blank line when the surface is defined by three-dimensional and axisymmetric elements or when the SURFACE parameter is omitted.


        if OBJ.physical_constants is not None:
            file.write(f"** PHYSICAL CONSTANTS\n")
            file.write(f"** \n")
            file.write(f"{OBJ.physical_constants}\n")


        if (OBJ.initial_Temp is not None) or (OBJ.initial_Pressure is not None):
            file.write(f"** PREDEFINED FIELDS\n")
            file.write(f"** \n")


            if OBJ.initial_Temp is not None:
                file.write(f"** Name: Predefined Field-1   Type: Temperature\n")
                file.write(f"*Initial Conditions, type=TEMPERATURE\n")
                for name, (x, y) in holes_barycenters.items():
                    # extract number after last hyphen
                    idx = int(name.split("-")[-1])
                    hole_items.append((idx, x, y))
                    file.write(f"SET-{idx} , {OBJ.initial_Temp}\n")


        if (OBJ.gas_present is True) and (OBJ.fluid_cavity is not None) and (OBJ.physical_constants is not None):
            file.write(f"** INTERACTIONS\n")
            file.write(f"** \n")

            for i in range(len(holes_surfaces)):
                file.write(f"** Interaction: Int-{i+1}\n")
                file.write(f"*Fluid Cavity, name=Int-{i+1}, behavior=Cavity_property, refnode=Set-{i+1}, surface={list(holes_surfaces.keys())[i]}, ambient pressure= {OBJ.initial_Pressure}\n")# ADIABATIC, AMBIENT TEMPERATURE= {OBJ.initial_Temp}
                # https://classes.engineering.wustl.edu/2009/spring/mase5513/abaqus/docs/v6.6/books/key/default.htm?startat=ch06abk16.html#usb-kws-mfluidcavity
                file.write(f"{OBJ.fluid_cavity_ratio} \n")



        if OBJ.inclusions_present == True:
            file.write("** MATERIALS\n")
            file.write("** \n")
            file.write("*Material, name=Material-Inclusions\n")
            file.write("*Elastic\n")
            file.write(f"{OBJ.E_Inclusions}, {OBJ.nu_Inclusions}\n")
            file.write(f"*Expansion\n")
            file.write(f"{OBJ.expansion_Inclusions},\n")


        # -------------------------------------------------------------------------
        # WRITE ALL STEPS
        # OBJ.steps is a list of step objects (e.g. StepData instances)
        # -------------------------------------------------------------------------
        for step in OBJ.steps:
            write_step_block(
                file=file,
                step=step,
                nodes=nodes,
                dim_nodes=dim_nodes,
                corner_xnyn=corner_xnyn,
                corner_xnyp=corner_xnyp,
                corner_xpyn=corner_xpyn,
                corner_xpyp=corner_xpyp,
                hole_items=hole_items,
                holes_barycenters=holes_barycenters,
                OBJ=OBJ
            )
