import importlib.util
import sys
from .Video_functions import *

# Get sim_num and property_file from command-line arguments
# Usage: python -m A001_functions.Video_executor <sim_num> <properties_id> [max_parallel]
#        python -m A001_functions.Video_executor <sim_num> <properties_id> --parallel <n>
sim_num = int(sys.argv[1])
file_name = f"F001_Video_properties_files/Video_properties_{sys.argv[2]}.py"

# Accept max_parallel as either a positional 3rd argument or --parallel <n> flag
max_parallel_override = None
if '--parallel' in sys.argv:
    idx = sys.argv.index('--parallel')
    max_parallel_override = int(sys.argv[idx + 1])
elif len(sys.argv) > 3 and sys.argv[3].lstrip('-').isdigit():
    max_parallel_override = int(sys.argv[3])

# Load the module dynamically
spec = importlib.util.spec_from_file_location("video_properties", file_name)
module = importlib.util.module_from_spec(spec)
sys.modules["video_properties"] = module
spec.loader.exec_module(module)

# Extract T_C and SCONF from the imported module
T = module.T  # Corrected from T_C1 to T_C
SCONF = module.SCONF


max_parallel = max_parallel_override if max_parallel_override is not None else T.max_parallel

create_frames_for_sim(sim_num, T, max_parallel=max_parallel, frames_format=T.frames_format)
concatenate_multiple_images_for_sim(sim_num,T)
create_vid_from_frames_for_sim(sim_num, SCONF)
