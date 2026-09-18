"""Three-smallest-eigenmodes diagnostic video configuration."""

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
MODE_INDICES = range(4)  # Four smallest stored modes: 0 through 3.
VIDEO_FOLDER = 'Video_3201'


def _make_eigenmode(mode_index):
    obj = frame_eigenmode()
    obj.mode_index = mode_index
    obj.num_frames = num_frames
    obj.figsize = (10.5, 9)
    obj.dpi = 120
    obj.xlim = None
    obj.ylim = None
    obj.axis_padding = 1.0
    obj.node_size = 0.55
    obj.cavity_size = 90.0
    obj.quiver_grid = 18
    obj.arrow_length = 1.10
    obj.arrow_color = '#202020'
    obj.arrow_width = 0.0048
    obj.x_data_scale = 5.0 / 20.0
    obj.sign_align = True
    obj.show_eigenvalue_history = True
    obj.resume_frames = True
    obj.save_path = f'frames_eigenmode_{mode_index:02d}/'
    return obj


EIGENMODES = [_make_eigenmode(mode) for mode in MODE_INDICES]


REACTION_FORCE = frame_variable()
REACTION_FORCE.x_key_path = "['U2']['PERN-9999997']"
REACTION_FORCE.y_key_paths = ["['RF2']['PERN-9999997']"]
REACTION_FORCE.normalize_x = -1.0 / 20.0
REACTION_FORCE.legends = None
REACTION_FORCE.normalized_by = 1
REACTION_FORCE.invert_y = True
REACTION_FORCE.xlabel = 'Strain'
REACTION_FORCE.ylabel = 'Reaction force (N)'
REACTION_FORCE.figsize = (9.0, 4.0)
REACTION_FORCE.preserve_aspect_ratio = True
REACTION_FORCE.dpi = 110
REACTION_FORCE.num_frames = num_frames
REACTION_FORCE.plot_from_0 = False
REACTION_FORCE.mark_localization = True
REACTION_FORCE.resume_frames = False
REACTION_FORCE.file_key_x = 'A2'
REACTION_FORCE.file_key_y = 'A2'
REACTION_FORCE.save_path = 'frames_reaction_force/'


GLOBAL_EFFICIENCY = graph_property()
GLOBAL_EFFICIENCY.ppty = 'G_eff'
GLOBAL_EFFICIENCY.legends = False
GLOBAL_EFFICIENCY.grid = True
GLOBAL_EFFICIENCY.xlabel = 'Strain'
GLOBAL_EFFICIENCY.x_data_scale = 5.0 / 20.0
GLOBAL_EFFICIENCY.ylabel = 'Global efficiency'
GLOBAL_EFFICIENCY.legend_loc = 'upper right'
GLOBAL_EFFICIENCY.dpi = 110
GLOBAL_EFFICIENCY.figsize = (9.0, 4.0)
GLOBAL_EFFICIENCY.preserve_aspect_ratio = True
GLOBAL_EFFICIENCY.num_frames = num_frames
GLOBAL_EFFICIENCY.file_ext = 'I3_BFS_3002'
GLOBAL_EFFICIENCY.include_allnodes = True
GLOBAL_EFFICIENCY.mark_localization = True
GLOBAL_EFFICIENCY.resume_frames = False
GLOBAL_EFFICIENCY.save_path = 'frames_global_efficiency/'


SHEAR_MEAN = frame_variable()
SHEAR_MEAN.x_key_path = "['U2']['PERN-9999997']"
SHEAR_MEAN.y_key_paths = ["['shear_mean']"]
SHEAR_MEAN.normalize_x = -1.0 / 20.0
SHEAR_MEAN.legends = None
SHEAR_MEAN.normalized_by = 1
SHEAR_MEAN.invert_y = False
SHEAR_MEAN.xlabel = 'Strain'
SHEAR_MEAN.ylabel = 'Shear mean'
SHEAR_MEAN.figsize = (9.0, 4.0)
SHEAR_MEAN.preserve_aspect_ratio = True
SHEAR_MEAN.dpi = 110
SHEAR_MEAN.num_frames = num_frames
SHEAR_MEAN.file_key_x = 'A2'
SHEAR_MEAN.file_key_y = 'TP2_L'
SHEAR_MEAN.mark_localization = True
SHEAR_MEAN.resume_frames = False
SHEAR_MEAN.save_path = 'frames_shear_mean/'


FACTOR_F = graph_property()
FACTOR_F.ppty = 'f'
FACTOR_F.tension_compression = 'comb'
FACTOR_F.legends = False
FACTOR_F.grid = True
FACTOR_F.xlabel = 'Strain'
FACTOR_F.x_data_scale = 5.0 / 20.0
FACTOR_F.ylabel = 'Tension / compression efficiency'
FACTOR_F.legend_loc = 'upper right'
FACTOR_F.dpi = 110
FACTOR_F.figsize = (9.0, 4.0)
FACTOR_F.preserve_aspect_ratio = True
FACTOR_F.num_frames = num_frames
FACTOR_F.file_ext = 'I3_BFS_3002'
FACTOR_F.yscale = 'log'
FACTOR_F.mark_localization = True
FACTOR_F.resume_frames = False
FACTOR_F.save_path = 'frames_factor_f/'


T = frames_combination()
T.canvas_size = (3600, 2400)
T.title = ('Four smallest dynamic tangent-stiffness eigenmodes\n'
           'Internal pressure: {internal_pressure:.3f} MPa | '
           '{material_model_display} | {foam_shape}')
T.title_position = (0, 18)
T.title_align = 'center'
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
T.resume_final_frames = False


_eigen_positions = [
    (40, 140), (1280, 140),
    (40, 1150), (1280, 1150),
]
T.elements = [
    {
        'position': position,
        'size': (1200, 1150),
        'path': obj.save_path,
        'subtitle': f'Mode {mode}',
        'create_frames': True,
        'type': 'EV',
        'object': obj,
        'replace_frames': True,
        'preserve_aspect_ratio': True,
    }
    for mode, position, obj in zip(MODE_INDICES, _eigen_positions, EIGENMODES)
]

T.elements.extend([
    {
        'position': (2600, 140), 'size': (900, 400),
        'path': 'frames_reaction_force/', 'subtitle': 'Strain',
        'create_frames': True, 'type': 'V', 'object': REACTION_FORCE,
        'replace_frames': True,
        'preserve_aspect_ratio': True,
    },
    {
        'position': (2600, 660), 'size': (900, 400),
        'path': 'frames_global_efficiency/', 'subtitle': 'Strain',
        'create_frames': True, 'type': 'GP', 'object': GLOBAL_EFFICIENCY,
        'replace_frames': True,
        'preserve_aspect_ratio': True,
    },
    {
        'position': (2600, 1180), 'size': (900, 400),
        'path': 'frames_shear_mean/', 'subtitle': 'Strain',
        'create_frames': True, 'type': 'V', 'object': SHEAR_MEAN,
        'replace_frames': True,
        'preserve_aspect_ratio': True,
    },
    {
        'position': (2600, 1700), 'size': (900, 400),
        'path': 'frames_factor_f/', 'subtitle': 'Strain',
        'create_frames': True, 'type': 'GP', 'object': FACTOR_F,
        'replace_frames': True,
        'preserve_aspect_ratio': True,
    },
])


SCONF = SimulationConfig()
SCONF.vid_folder = VIDEO_FOLDER
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = 'mp4v'
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_3201.mp4'
