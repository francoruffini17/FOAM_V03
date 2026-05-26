

import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import matplotlib.pyplot as plt
from A001_functions.plot_mesh_functions import (
    plot_mesh_json,
    plot_graph_mesh,
    plot_mesh_json_and_graph,
    plot_mesh_json_periodic,
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    plot_mesh_json_and_graph(
        "C001_Mesh_files/A2000_hexagonal_mesh.mesh.json",
        "C001_Mesh_files/A3000_K2002.gridhex.json",
        boundary_only=False,
        show=False,
    )


    plt.show()
