import subprocess
import os
import sys
import numpy as np
import matplotlib.pyplot as plt

def main():

    # -----------------------------------------------
    # Ask user for simulation number
    # -----------------------------------------------
    sim_num = int(input("Enter SIM number (e.g., 12): "))
    
    job_name = "SIM_{:03d}".format(sim_num)
    
    # -----------------------------------------------
    # Paths
    # -----------------------------------------------
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    abaqus_script = os.path.join(root_dir, "A001_functions", "abq_script_to_plot_V2.py")
    output_csv = os.path.join(root_dir, "RF2_U2_temp.csv")

    plot_folder = os.path.join(root_dir, "I002-Partial_plots")
    if not os.path.exists(plot_folder):
        os.makedirs(plot_folder)

    output_plot = os.path.join(plot_folder, "{}.png".format(job_name))

    # -----------------------------------------------
    # Run Abaqus extraction script
    # -----------------------------------------------
    print("\nRunning Abaqus extraction...")
    cmd = [
        "abq", 
        "python", 
        abaqus_script,
        str(sim_num),
        output_csv
    ]

    subprocess.call(cmd)
    print("Abaqus extraction finished.")

    # -----------------------------------------------
    # Load CSV data
    # -----------------------------------------------
    print("Reading CSV:", output_csv)
    data = np.loadtxt(output_csv, delimiter=",", skiprows=1)
    
    time = data[:,0]
    U2   = data[:,1]
    RF2  = data[:,2]

    # -----------------------------------------------
    # Plot RF2 vs U2
    # -----------------------------------------------
    plt.figure(figsize=(8,6))
    plt.plot(U2, RF2, "-o", markersize=3)

    plt.xlabel("U2 (average displacement)")
    plt.ylabel("RF2 (reaction force)")
    plt.title("RF2 vs U2: {}".format(job_name))
    plt.grid(True)
    plt.tight_layout()

    # Save plot
    plt.savefig(output_plot)
    print("\nSaved plot to:", output_plot)
    plt.close()

    # Delete temporary CSV
    os.remove(output_csv)


if __name__ == "__main__":
    main()
