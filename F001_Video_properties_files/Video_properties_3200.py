"""Smallest-eigenvalue diagnostic video configuration."""

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
VIDEO_FOLDER = 'Video_3200'


# The first (smallest) tangent-stiffness eigenvalue and its mode shape.
SMALLEST_EIGENMODE = frame_eigenmode()
SMALLEST_EIGENMODE.mode_index = 0
SMALLEST_EIGENMODE.num_frames = num_frames
SMALLEST_EIGENMODE.figsize = (10.5, 9)
SMALLEST_EIGENMODE.dpi = 120
SMALLEST_EIGENMODE.xlim = None
SMALLEST_EIGENMODE.ylim = None
SMALLEST_EIGENMODE.axis_padding = 1.0
SMALLEST_EIGENMODE.node_size = 0.55
SMALLEST_EIGENMODE.cavity_size = 90.0
SMALLEST_EIGENMODE.quiver_grid = 18
SMALLEST_EIGENMODE.arrow_length = 0.65
SMALLEST_EIGENMODE.sign_align = True
SMALLEST_EIGENMODE.show_eigenvalue_history = True
SMALLEST_EIGENMODE.resume_frames = True
SMALLEST_EIGENMODE.save_path = 'frames_smallest_eigenmode/'


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
REACTION_FORCE.resume_frames = True
REACTION_FORCE.file_key_x = 'A2'
REACTION_FORCE.file_key_y = 'A2'
REACTION_FORCE.save_path = 'frames_reaction_force/'


GLOBAL_EFFICIENCY = graph_property()
GLOBAL_EFFICIENCY.ppty = 'G_eff'
GLOBAL_EFFICIENCY.legends = True
GLOBAL_EFFICIENCY.grid = True
GLOBAL_EFFICIENCY.xlabel = 'Compression ratio'
GLOBAL_EFFICIENCY.ylabel = 'Global efficiency'
GLOBAL_EFFICIENCY.legend_loc = 'upper right'
GLOBAL_EFFICIENCY.dpi = 110
GLOBAL_EFFICIENCY.figsize = (5.5, 3.6)
GLOBAL_EFFICIENCY.num_frames = num_frames
GLOBAL_EFFICIENCY.file_ext = 'I3_BFS_3002'
GLOBAL_EFFICIENCY.include_allnodes = True
GLOBAL_EFFICIENCY.mark_localization = True
GLOBAL_EFFICIENCY.resume_frames = True
GLOBAL_EFFICIENCY.save_path = 'frames_global_efficiency/'


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
SHEAR_MEAN.resume_frames = True
SHEAR_MEAN.save_path = 'frames_shear_mean/'


FACTOR_F = graph_property()
FACTOR_F.ppty = 'f'
FACTOR_F.tension_compression = 'comb'
FACTOR_F.legends = True
FACTOR_F.grid = True
FACTOR_F.xlabel = 'Compression ratio'
FACTOR_F.ylabel = 'Tension / compression efficiency'
FACTOR_F.legend_loc = 'upper right'
FACTOR_F.dpi = 110
FACTOR_F.figsize = (5.5, 3.6)
FACTOR_F.num_frames = num_frames
FACTOR_F.file_ext = 'I3_BFS_3002'
FACTOR_F.yscale = 'log'
FACTOR_F.mark_localization = True
FACTOR_F.resume_frames = True
FACTOR_F.save_path = 'frames_factor_f/'


T = frames_combination()
T.canvas_size = (3000, 1800)
T.title = 'Smallest dynamic tangent-stiffness eigenvalue diagnostics'
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
T.resume_final_frames = True
T.elements = [
    {
        'position': (40, 85), 'size': (1780, 1500),
        'path': 'frames_smallest_eigenmode/', 'subtitle': 'Smallest eigenvalue and mode shape',
        'create_frames': True, 'type': 'EV', 'object': SMALLEST_EIGENMODE,
        'replace_frames': True,
    },
    {
        'position': (1900, 85), 'size': (1050, 300),
        'path': 'frames_reaction_force/', 'subtitle': 'Reaction force',
        'create_frames': True, 'type': 'V', 'object': REACTION_FORCE,
        'replace_frames': True,
    },
    {
        'position': (1900, 455), 'size': (1050, 300),
        'path': 'frames_global_efficiency/', 'subtitle': 'Tension and compression efficiency',
        'create_frames': True, 'type': 'GP', 'object': GLOBAL_EFFICIENCY,
        'replace_frames': True,
    },
    {
        'position': (1900, 825), 'size': (1050, 300),
        'path': 'frames_shear_mean/', 'subtitle': 'Shear mean',
        'create_frames': True, 'type': 'V', 'object': SHEAR_MEAN,
        'replace_frames': True,
    },
    {
        'position': (1900, 1195), 'size': (1050, 300),
        'path': 'frames_factor_f/', 'subtitle': 'Factor f',
        'create_frames': True, 'type': 'GP', 'object': FACTOR_F,
        'replace_frames': True,
    },
]


SCONF = SimulationConfig()
SCONF.vid_folder = VIDEO_FOLDER
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = 'mp4v'
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_3200.mp4'
