

def is_Digit(string):
    try:
        number = float(string)
        OUT = True
    except ValueError:
        OUT = False
    return OUT



def READ_DATA_RED_GRL(file_name, type = 'A'):
    DATA = {}
    i = 0
    L = 'sd'
    with open(file_name, 'r') as file:
        

        line = file.readline()
        while (L !=''):
            
            line = line.split()
            C0 = line[1] # EX: New node 1 : 3 -> Can be global, node or element.
            groups = []
            
            if C0 != 'global':
                num_groups = int(line[-1])
                node_or_elem_num = int(line[2])        

                for _ in range(num_groups):
                    groups.append(file.readline()[:-1])

            else:
                num_groups = 1
                groups = [file.readline()[:-1]]
        
            L = file.readline() #Now L can be:  " (hay que saltear), otro C3 distinto o New element
            i += 1
            if L == '':
                break
            
            VARIABLES_READ = {}


            while (L !='')&('New' not in L):
                
                C3 = L.split()[0]        # RF2, RF3, U1, COOR1, etc.
                VARIABLES_READ[C3] = []

                # Read first data line. Some files may include blank lines
                # between the variable label and the first numeric row.
                L = file.readline()
                i += 1
                while L != '' and L.strip() == '':
                    L = file.readline()
                    i += 1

                if L == '':
                    raise ValueError(
                        f"Malformed/truncated file '{file_name}': "
                        f"expected numeric 't,value' rows after variable '{C3}' (line {i})."
                    )

                t =[]
                VAL = []

                while L != '':
                    parts = L.strip().split(',', 1)
                    # if len(parts) != 2:
                    #     raise ValueError(
                    #         f"Malformed line in '{file_name}' at line {i}: "
                    #         f"expected 't,value', got {L.strip()!r}."
                    #     )

                    if not is_Digit(parts[0].strip()):
                        break

                    ti = float(parts[0])
                    VALi = float(parts[1])

                    t.append(ti)
                    VAL.append(VALi)

                    L = file.readline()
                    line = L
                    i += 1

                VARIABLES_READ[C3].append({'V' : VAL})

                        
                # IF A NODE BELONGS TO MULTIPLE GROUPS, SAVE DATA FOR EACH GROUP
                for k in range(num_groups):
                    group = groups[k]
                    C1 = []
                    if 'SET-X-POSITIVE' in group:
                        C1 = 'X-POSITIVE'
                    elif 'SET-X-NEGATIVE' in group:
                        C1 = 'X-NEGATIVE'
                    elif 'SET-Y-POSITIVE' in group:
                        C1 = 'Y-POSITIVE'
                    elif 'SET-Y-NEGATIVE' in group:
                        C1 = 'Y-NEGATIVE'
                    elif 'SET-Z-POSITIVE' in group:
                        C1 = 'Z-POSITIVE'
                    elif 'SET-Z-NEGATIVE' in group:
                        C1 = 'Z-NEGATIVE'
                    elif 'EALL' in group:
                        C1 = 'EALL'
                    elif 'FOAM' in group:
                        C1 = 'NALL'
                    elif 'SET-1' in group or 'SET-E-SEED' in group:
                        continue
                    elif 'PERN-9999997' in group:
                        C1 = 'PERN-9999997'
                    elif 'PERN-9999998' in group:
                        C1 = 'PERN-9999998'
                    elif 'PERN-9999999' in group:
                        C1 = 'PERN-9999999'
                    elif 'ASSEMBLY' in group:
                        C1 = 'ASSEMBLY'
                    else:
                        print('ERROR WHILE READING C1')
                        print(group)
                        continue
                    # VAL: list of values read
                    # C3: RF3, RF2, etc
                    # C1 X-POSITIVE, Y-NEGATIVE, etc
             
                    if type == 'A':
                        if C1 in ['X-POSITIVE','X-NEGATIVE','Y-POSITIVE','Y-NEGATIVE','Z-POSITIVE','Z-NEGATIVE', 'PERN-9999997', 'PERN-9999998', 'PERN-9999999']:
                            if C3 in ['COOR1','COOR2','COOR3']:
                                continue
                            else:
                                if C3 not in DATA.keys():
                                    DATA[C3] = {}
                                if C1 not in DATA[C3].keys():
                                    DATA[C3][C1] = {}
                                if str(node_or_elem_num) not in DATA[C3][C1].keys():
                                    DATA[C3][C1][str(node_or_elem_num)] = {}
                                            
                                DATA[C3][C1][str(node_or_elem_num)] = VAL
                        elif C1 == 'ASSEMBLY':
                            if C3 not in DATA.keys():
                                DATA[C3] = {}
                            DATA[C3]['ASSEMBLY'] = VAL



                    if type == 'B':
                        if C1 == 'EALL':   
                            if C3 not in DATA.keys():
                                DATA[C3] = {}
                            if str(node_or_elem_num) not in DATA[C3].keys():
                                DATA[C3][str(node_or_elem_num)] = []
                        
                            DATA[C3][str(node_or_elem_num)].append(VAL)


                    if type == 'C':
                        if C1 == 'NALL':
                            if C3 in ['COOR1','COOR2','COOR3']:   
                                if C3 not in DATA.keys():
                                    DATA[C3] = {}
                                if str(node_or_elem_num) not in DATA[C3].keys():
                                    DATA[C3][str(node_or_elem_num)] = {}

                                DATA[C3][str(node_or_elem_num)] = VAL

                    DATA['t'] = t


                if L == '':
                    break
            
    return DATA


file_name = './I001_Results/RES_SIM_000.csv'
CONDITIONS = None




