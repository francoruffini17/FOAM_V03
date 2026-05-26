import importlib.util
import sys
from .Video_functions import *

# Ask the user for the filename
sim_num = int(input("Simulation number: "))
file_name = input("Enter the filename containing T_C and SCONF (default: F001_Video_properties_files/Video_properties0031): ") or "F001_Video_properties_files/Video_properties0031"
file_name = file_name + ".py"

# Load the module dynamically
spec = importlib.util.spec_from_file_location("video_properties", file_name)
module = importlib.util.module_from_spec(spec)
sys.modules["video_properties"] = module
spec.loader.exec_module(module)

# Extract T_C and SCONF from the imported module
T = module.T  # Corrected from T_C1 to T_C
SCONF = module.SCONF


create_frames_for_sim(sim_num,T,  max_parallel=T.max_parallel, frames_format=T.frames_format)
concatenate_multiple_images_for_sim(sim_num,T)
create_vid_from_frames_for_sim(sim_num, SCONF)
