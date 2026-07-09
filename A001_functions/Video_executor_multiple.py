import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed


sim_nums =  [1003, 1005, 1008, 1009, 1013, 1015, 1018, 1109] #004, 6005, 6006, 6007, 6008]#4000, 4001, 4002]#, 2003, 2004]#, 2005, 2006, 2007, 2008]

# 1200, 1201, 1202, 1203, 1204, 1205, 1206, 1207, 1208, 1209,
            # 1210, 1211, 1212, 1213, 1214, 1215, 1216, 1217, 1218, 1219]



# sim_nums = [ 1100, 1101, 1102, 1103, 1104, 1105, 1106, 1107, 1108, 1109,
#             1110, 1111, 1112, 1113, 1114, 1115, 1116, 1117, 1118, 1119,
#             1120, 1121, 1122, 1123, 1124, 1125, 1126, 1127, 1128, 1129,
#             1130, 1131, 1132, 1133, 1134, 1135, 1136, 1137, 1138, 1139]

#[7520, 7521, 7522, 7523, 7524, 7525, 7526, 7527,7528, 7529,7530]
            # 6010, 6011, 6012, 6013, 6014, 6015,
            # 6020, 6021, 6022, 6023, 6024, 6025,
            # 6030, 6031, 6032, 6033, 6034, 6035,
            # 6040, 6041, 6042, 6043, 6044, 6045,
            # 6050, 6051, 6052, 6053, 6054, 6055]



def run_simulation(sim_num):
    print(f"Running simulation {sim_num}...")
    try:
        process = subprocess.Popen(
            ["python", "-m", "A001_functions.Video_executor", str(sim_num), "F001_Video_properties_files/Video_properties_1010"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        stdout, stderr = process.communicate()
        result = f"Finished simulation {sim_num}\n{'-'*40}\n"
        if stdout:
            result += stdout
        if stderr:
            result += f"Error: {stderr}\n"
    except Exception as e:
        result = f"An error occurred while running simulation {sim_num}: {e}\n"
        
    return result

if __name__ == "__main__":
    num_cores = 1  # Set this to the number of cores you want to use

    with ProcessPoolExecutor(max_workers=num_cores) as executor:
        futures = [executor.submit(run_simulation, sim_num) for sim_num in sim_nums]
        for future in as_completed(futures):
            print(future.result())
