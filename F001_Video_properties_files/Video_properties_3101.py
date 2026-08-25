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
MODE_INDICES = range(5)  # Five smallest stored modes: 0 through 4.
VIDEO_FOLDER = 'Video_3101_eigenmodes_00_04'


def _make_eigenmode(mode_index):
    obj = frame_eigenmode()
    obj.mode_index = mode_index
    obj.num_frames = num_frames
    obj.figsize = (10.5, 9)
    obj.dpi = 120
    obj.xlim = (-2, 22)
    obj.ylim = (-2, 22)
    obj.node_size = 0.55
    obj.cavity_size = 90.0
    obj.quiver_grid = 18
    obj.arrow_length = 0.65
    obj.sign_align = True
    obj.show_eigenvalue_history = True
    obj.save_path = f'frames_eigenmode_{mode_index:02d}/'
    return obj


EIGENMODES = [_make_eigenmode(mode) for mode in MODE_INDICES]


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
T.canvas_size = (3600, 2700)
T.title = 'SIM 3101: five smallest dynamic tangent-stiffness eigenmodes'
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


_eigen_positions = [
    (40, 85), (1280, 85),
    (40, 950), (1280, 950),
    (40, 1815),
]
T.elements = [
    {
        'position': position,
        'size': (1200, 800),
        'path': obj.save_path,
        'subtitle': f'Mode {mode}',
        'create_frames': True,
        'type': 'EV',
        'object': obj,
        'replace_frames': True,
    }
    for mode, position, obj in zip(MODE_INDICES, _eigen_positions, EIGENMODES)
]

T.elements.extend([
    {
        'position': (2600, 85),
        'size': (900, 650),
        'path': 'frames_reaction_force/',
        'subtitle': 'Reaction force',
        'create_frames': True,
        'type': 'V',
        'object': REACTION_FORCE,
        'replace_frames': False,
    },
    {
        'position': (2600, 900),
        'size': (900, 650),
        'path': 'frames_global_efficiency/',
        'subtitle': 'Average global efficiency',
        'create_frames': True,
        'type': 'GP',
        'object': GLOBAL_EFFICIENCY,
        'replace_frames': False,
    },
    {
        'position': (2600, 1715),
        'size': (900, 650),
        'path': 'frames_shear_mean/',
        'subtitle': 'Shear mean',
        'create_frames': True,
        'type': 'V',
        'object': SHEAR_MEAN,
        'replace_frames': False,
    },
])


SCONF = SimulationConfig()
SCONF.vid_folder = VIDEO_FOLDER
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = 'mp4v'
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_3101.mp4'
