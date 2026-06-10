from multiprocessing import Pool, cpu_count
from abaqusConstants import *
from odbAccess import *
from collections import defaultdict
import csv
import os
# import time
def extract_nodes_and_sets(odb):
    # Check if any key starts with "REFERENCE_POINT" (i.e. check if there are plates)
    has_plate_up = any(key.startswith("REFERENCE_POINT_PART-PLATE_UP") for key in odb.rootAssembly.nodeSets.keys())
    has_plate_low = any(key.startswith("REFERENCE_POINT_PART-PLATE_LOW") for key in odb.rootAssembly.nodeSets.keys())
    # Dictionary to store nodes and their associated sets
    nodes_dict = defaultdict(list)
    # Iterate over all node sets in the assembly
    for set_name in odb.rootAssembly.nodeSets.keys():
        node_set = odb.rootAssembly.nodeSets[set_name]
        nodes = node_set.nodes[0]  # Access the nodes in this set
        # print(set_name)
        # Iterate over all nodes in the current set
        for node in nodes:
            node_label = str(node.label)  # Convert node label to string
            if has_plate_up:
                if "REFERENCE_POINT_PART-PLATE_UP" in set_name:
                    node_label = str(-1)
                if "SET-RP_UP" == set_name:
                    node_label = str(-1)
            if has_plate_low:
                if "REFERENCE_POINT_PART-PLATE_LOW" in set_name:
                    node_label = str(-2)
                if "SET-RP_LOW" == set_name:
                    node_label = str(-2)
            # print(node_label)
            if set_name not in nodes_dict[node_label]:
                nodes_dict[node_label].append(set_name)
    # Convert defaultdict to regular dictionary for the final output
    return dict(nodes_dict)

def extract_nodes_and_sets_part(odb):
    # Dictionary to store nodes and their associated sets
    nodes_dict = defaultdict(list)
    # Helper function to process nodes in a node set
    def process_node_set(node_set, set_name):
        for node in node_set.nodes:
            node_label = str(node.label)  # Convert node label to string
            if set_name not in nodes_dict[node_label]:
                nodes_dict[node_label].append(set_name)
    # Process instance-specific node sets from PART-1-1.nodeSets
    part_instance = odb.rootAssembly.instances['PART-1-1']
    for set_name in part_instance.nodeSets.keys():
        node_set = part_instance.nodeSets[set_name]
        process_node_set(node_set, set_name)
    # Convert defaultdict to regular dictionary for the final output
    return dict(nodes_dict)

def extract_elements_and_sets(odb):
    # Dictionary to store elements and their associated sets
    elements_dict = defaultdict(list)
    # Iterate over all element sets in the assembly
    for set_name in odb.rootAssembly.elementSets.keys():
        element_set = odb.rootAssembly.elementSets[set_name]
        elements = element_set.elements[0]  # Access the elements in this set
        # Iterate over all elements in the current set
        for element in elements:
            element_label = str(element.label)  # Convert element label to string
            if set_name not in elements_dict[element_label]:
                elements_dict[element_label].append(set_name)
    # Convert defaultdict to regular dictionary for the final output
    return dict(elements_dict)

def extract_elements_and_sets_part(odb):
    # Dictionary to store elements and their associated sets
    elements_dict = defaultdict(list)
    # Helper function to process elements in a element set
    def process_element_set(element_set, set_name):
        for element in element_set.elements:
            element_label = str(element.label)  # Convert element label to string
            if set_name not in elements_dict[element_label]:
                elements_dict[element_label].append(set_name)
    # Process instance-specific element sets from PART-1-1.elementSets
    part_instance = odb.rootAssembly.instances['PART-1-1']
    for set_name in part_instance.elementSets.keys():
        element_set = part_instance.elementSets[set_name]
        process_element_set(element_set, set_name)
    # Convert defaultdict to regular dictionary for the final output
    return dict(elements_dict)

def merge_dic(dic1, dic2):
    merged_dic = {}
    # Combine keys from both dictionaries
    all_keys = set(dic1.keys()) | set(dic2.keys())
    # Merge values for each key
    for key in all_keys:
        # Get values from both dictionaries, default to an empty list if the key is missing
        list1 = dic1.get(key, [])
        list2 = dic2.get(key, [])
        # Combine and remove duplicates
        merged_dic[key] = list(set(list1 + list2))
    return merged_dic

def remove_entries(merged_dic, entries_to_remove):
    """
    Removes specific entries from the lists in a dictionary.
    
    :param merged_dic: Dictionary with lists as values
    :param entries_to_remove: List of entries to be removed
    :return: Dictionary with the specified entries removed from the lists
    """
    for key in merged_dic:
        merged_dic[key] = [item for item in merged_dic[key] if item not in entries_to_remove]
    return merged_dic

    
def process_simulation(sim_args):
    """Process a single simulation and write results to CSV files based on output_draw."""
    simulation_number, result_folder = sim_args
    job_name = "SIM_{:03d}".format(simulation_number)  # Use Python 2.7-compatible formatting
    file_location = "E001_Simulations/{}/".format(job_name)
    odb_file = "{}{}.odb".format(file_location, job_name)
    step = 'Step-1'
        
    try:
        odb = openOdb(odb_file, readOnly=True)  # Ensure a separate ODB instance for each process
        
        # Open both files (if output_draw is True)
        output_file = "{}/RES_{}.csv".format(result_folder, job_name)
        file_main = open(output_file, 'wb')  # 'wb' for binary mode in Python 2
        csvwriter = csv.writer(file_main)

        # Create dictionaries of nodes and elements
        nodes_dict_1 = extract_nodes_and_sets(odb)
        nodes_dic = remove_entries(nodes_dict_1,[' ALL NODES', 'SET-NODES-TENSEGRITY', 'SET-X-NEGATIVE', 'SET-X-POSITIVE', 'WarnNodeBCInactiveDof'])
        
        # Process historyRegions for the main CSV file
        p = 0
        for region_name, region_object in odb.steps[step].historyRegions.items():
            type_ob = region_name.split()[0].lower() # can be assembly, node or element, elementset)
            # there are two element sets: SET-BARS and SET-CABLES (they have ALLIE, ALLSE, ETC)
            if (type_ob == 'node'):
                node_n = region_object.point.node.label
                number_of_groups = len(nodes_dic[str(node_n)])
                
                if number_of_groups > 0: 
                    csvwriter.writerow(['New node {} : {}'.format(node_n, number_of_groups)])
                    for group in nodes_dic[str(node_n)]:
                        # print(group)
                        csvwriter.writerow(['{}'.format(group)])
                    for output_name, output_object in region_object.historyOutputs.items():
                        if output_name in ['RF2','U2']:
                            if 'Repeated' not in output_name:
                                csvwriter.writerow([output_name])
                                csvwriter.writerows(output_object.data)
                            
            if (type_ob == 'element'):
                continue
            if (type_ob == 'elementset'):
                continue
            if (type_ob == 'assembly'):
                continue
                        
            if type_ob not in ['assembly','elementset', 'element', 'node']:
                print(type_ob)
    
            p += 1

        # Close files
        file_main.close()
        odb.close()

        print("Simulation {} processed successfully.".format(simulation_number))



    
    except Exception as e:
        print("Error processing simulation {}: {}".format(simulation_number, e))

def main():
    initial_simulation = int(raw_input('Initial simulation number: '))  # raw_input for Python 2
    final_simulation = int(raw_input('Final simulation number: '))    # raw_input for Python 2
    result_folder = 'Temp'        # raw_input for Python 2

    
    # List of simulations
    simulations = range(initial_simulation, final_simulation + 1)

    # Prepare arguments for parallel processing
    sim_args = [(sim, result_folder) for sim in simulations]

    # Determine the number of processors to use
    num_processors = min(cpu_count(), len(simulations))
    print("Using {} processors.".format(num_processors))

    # Parallel processing with multiprocessing.Pool
    pool = Pool(processes=num_processors)
    try:
        pool.map(process_simulation, sim_args)
    finally:
        pool.close()
        pool.join()

if __name__ == "__main__":
    main()



