import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from A001_functions.Video_functions import (
    SimulationConfig,
    frame_eigenmode,
    frame_variable,
    frames_combination,
    graph_property,
)


num_frames = 201
MODE_INDEX = 0  # Stored modes are indexed 0 through 19.
VIDEO_FOLDER = f'Video_3100_eigenmode_{MODE_INDEX:02d}'

EV3100 = frame_eigenmode()
EV3100.mode_index = MODE_INDEX
EV3100.num_frames = num_frames
EV3100.figsize = (10.5, 9)
EV3100.dpi = 120
EV3100.xlim = (-2, 22)
EV3100.ylim = (-2, 22)
EV3100.node_size = 0.55
EV3100.cavity_size = 90.0
EV3100.quiver_grid = 18
EV3100.arrow_length = 0.65
EV3100.sign_align = True
EV3100.show_eigenvalue_history = False
EV3100.save_path = 'frames_eigenmode/'


# Reaction force versus imposed compression.
REACTION_FORCE = frame_variable()
REACTION_FORCE.x_key_path = "['U2']['PERN-9999997']"
REACTION_FORCE.y_key_paths = ["['RF2']['PERN-9999997']"]
REACTION_FORCE.normalize_x = -1
REACTION_FORCE.legends = ['Reaction force']
REACTION_FORCE.normalized_by = 1
REACTION_FORCE.invert_y = True
REACTION_FORCE.xlabel = 'Displacement (mm)'
REACTION_FORCE.ylabel = 'Reaction force (N)'
REACTION_FORCE.figsize = (5.5, 3.6)
REACTION_FORCE.dpi = 110
REACTION_FORCE.num_frames = num_frames
REACTION_FORCE.plot_from_0 = True
REACTION_FORCE.mark_localization = True
REACTION_FORCE.file_key_x = 'A2'
REACTION_FORCE.file_key_y = 'A2'
REACTION_FORCE.save_path = 'frames_reaction_force/'


# Average global efficiency of the I3002 tension/compression graphs.
GLOBAL_EFFICIENCY = graph_property()
GLOBAL_EFFICIENCY.ppty = 'G_eff'
GLOBAL_EFFICIENCY.legends = True
GLOBAL_EFFICIENCY.grid = True
GLOBAL_EFFICIENCY.xlabel = 'Step-1 time'
GLOBAL_EFFICIENCY.ylabel = 'Average global efficiency'
GLOBAL_EFFICIENCY.legend_loc = 'upper right'
GLOBAL_EFFICIENCY.dpi = 110
GLOBAL_EFFICIENCY.figsize = (5.5, 3.6)
GLOBAL_EFFICIENCY.num_frames = num_frames
GLOBAL_EFFICIENCY.file_ext = 'I3_BFS_3002'
GLOBAL_EFFICIENCY.include_allnodes = True
GLOBAL_EFFICIENCY.mark_localization = True
GLOBAL_EFFICIENCY.save_path = 'frames_global_efficiency/'


# TP2_L has the same shear_mean series as the 4.2 GB TP2 file but is tiny.
SHEAR_MEAN = frame_variable()
SHEAR_MEAN.x_key_path = "['U2']['PERN-9999997']"
SHEAR_MEAN.y_key_paths = ["['shear_mean']"]
SHEAR_MEAN.normalize_x = -1
SHEAR_MEAN.legends = ['Shear mean']
SHEAR_MEAN.normalized_by = 1
SHEAR_MEAN.invert_y = False
SHEAR_MEAN.xlabel = 'Displacement (mm)'
SHEAR_MEAN.ylabel = 'Shear mean'
SHEAR_MEAN.figsize = (5.5, 3.6)
SHEAR_MEAN.dpi = 110
SHEAR_MEAN.num_frames = num_frames
SHEAR_MEAN.file_key_x = 'A2'
SHEAR_MEAN.file_key_y = 'TP2_L'
SHEAR_MEAN.mark_localization = True
SHEAR_MEAN.save_path = 'frames_shear_mean/'


T = frames_combination()
T.canvas_size = (2800, 1700)
T.title = f'SIM 3100: dynamic tangent-stiffness eigenmode {MODE_INDEX}'
T.title_position = (45, 15)
T.title_font = '/home/fruffini/.conda/envs/Fenv/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf'
T.title_size = 38
T.subtitle_size = 24
T.title_color = 'black'
T.subtitle_color = 'black'
T.dpi = (300, 300)
T.save_path = 'frames_final/'
T.canvas_color = 'white'
T.subtitle_font = T.title_font
T.subtitle_offset = 5
T.delete_after_concat = False
T.max_parallel = 1
T.frames_format = 'png'
T.num_frames = num_frames
T.vid_folder = VIDEO_FOLDER
T.elements = [
    {
        'position': (40, 85),
        'size': (1780, 1500),
        'path': 'frames_eigenmode/',
        'subtitle': '',
        'create_frames': True,
        'type': 'EV',
        'object': EV3100,
        'replace_frames': False,
    },
    {
        'position': (1900, 85),
        'size': (820, 450),
        'path': 'frames_reaction_force/',
        'subtitle': 'Reaction force',
        'create_frames': True,
        'type': 'V',
        'object': REACTION_FORCE,
        'replace_frames': False,
    },
    {
        'position': (1900, 625),
        'size': (820, 450),
        'path': 'frames_global_efficiency/',
        'subtitle': 'Average global efficiency',
        'create_frames': True,
        'type': 'GP',
        'object': GLOBAL_EFFICIENCY,
        'replace_frames': False,
    },
    {
        'position': (1900, 1165),
        'size': (820, 450),
        'path': 'frames_shear_mean/',
        'subtitle': 'Shear mean',
        'create_frames': True,
        'type': 'V',
        'object': SHEAR_MEAN,
        'replace_frames': False,
    },
]


SCONF = SimulationConfig()
SCONF.vid_folder = VIDEO_FOLDER
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = 'mp4v'
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = f'video_eigenmode_{MODE_INDEX:02d}.mp4'
