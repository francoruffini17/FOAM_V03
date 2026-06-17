import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Triangulation_creator import triangulation_generator, plot_triangulation


mesh_path = "C001_Mesh_files/R010_T001.tri"

triangulation_generator(
    n_nodes_per_edge=51,
    file_name=mesh_path,
)

plot_triangulation(
    mesh_path,
    show_node_numbers=False,
    show_element_numbers=False,
)
