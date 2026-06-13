import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from A001_functions.Video_functions import *
import numpy as np
from typing import Callable, Optional




num_frames = 201

A1 = frame_variable()
A1.x_key_path = "['U2']['PERN-9999997']"
A1.y_key_paths = ["['RF2']['PERN-9999997']"]
A1.normalize_x = -1
A1.legends = ['Reaction force']
A1.normalized_by = 1
A1.invert_y = True
A1.xlabel = "Displacement [mm]"
A1.ylabel = "Reaction force [N]"
A1.title = None
A1.derivative = False
A1.save_path = 'frames_A/'
A1.figsize = (4.75,4)
A1.dpi = 100
A1.num_frames = num_frames
A1.plot_from_0 = True


A3 = frame_animation()
A3.title = ''
A3.num_frames = num_frames
A3.figsize = (15,15)
A3.xlim = (-4, 24)
A3.ylim = (-4, 24)
A3.color_element = 'S11 + S22'
A3.mesh_line_size = 0
A3.node_size = 0


A25 = frame_variable()
A25.x_key_path = "['U2']['PERN-9999997']"
A25.y_key_paths = ["['RF2']['PERN-9999997']"]
A25.normalize_x = -1
A25.legends = ['Reaction force']
A25.normalized_by = 1
A25.invert_y = True
A25.xlabel = "Displacement [mm]"
A25.ylabel = "Reaction force [N]"
A25.title = None
A25.derivative = True
A25.save_path = 'frames_A/'
A25.figsize = (4.75,4)
A25.dpi = 100
A25.num_frames = num_frames
A25.plot_from_0 = True


A26 = frame_variable()
A26.x_key_path = "['U2']['PERN-9999997']"
A26.y_key_paths = ["['RF2']['PERN-9999997']"]
A26.normalize_x = -1
A26.legends = ['Reaction force']
A26.normalized_by = 1
A26.invert_y = True
A26.xlabel = "Displacement [mm]"
A26.ylabel = "Reaction force [N]"
A26.title = None
A26.derivative = 2
A26.save_path = 'frames_A/'
A26.figsize = (4.75,4)
A26.dpi = 100
A26.num_frames = num_frames
A26.plot_from_0 = True
A26.ylim = (-2, 2)


A60 = frame_variable()
A60.x_key_path = "['t']"
A60.y_key_paths = ["['ALLWK']['ASSEMBLY']", "['ALLSD']['ASSEMBLY']"]
A60.legends = ['ALLWK', 'ALLSD']
A60.normalized_by = 1
A60.invert_y = False
A60.xlabel = "Time [s]"
A60.ylabel = "Energy [mJ]"
A60.title = None
A60.derivative = False
A60.save_path = 'frames_A60/'
A60.figsize = (5, 5)
A60.dpi = 100
A60.num_frames = num_frames
A60.plot_from_0 = False
A60.file_key_x = 'A'
A60.file_key_y = 'A'


A61 = frame_variable()
A61.x_key_path = "['t']"
A61.y_key_paths = []
A61.ratio_key_pairs = [("['ALLSE']['ASSEMBLY']", "['ALLWK']['ASSEMBLY']")]
A61.legends = ['ALLWK / ALLSE']
A61.normalized_by = 1
A61.invert_y = False
A61.xlabel = "Time [s]"
A61.ylabel = "ALLWK / ALLSE"
A61.title = None
A61.derivative = False
A61.save_path = 'frames_A61/'
A61.figsize = (5, 5)
A61.dpi = 100
A61.num_frames = num_frames
A61.plot_from_0 = False
A61.file_key_x = 'A'
A61.file_key_y = 'A'


VQ001 = frame_animation_Q1()
VQ001.title = ''
VQ001.num_frames = num_frames
VQ001.dpi = 300
VQ001.Q1_ext = '001'
VQ001.Q2_ext = '001'
VQ001.plot_Q1_params.color_by = ('w', (1, 1, 2, 2))

VQ002 = frame_animation_Q1()
VQ002.title = ''
VQ002.num_frames = num_frames
VQ002.dpi = 300
VQ002.Q1_ext = '002'
VQ002.Q2_ext = '002'
VQ002.plot_Q1_params.color_by = ('w', (1, 1, 2, 2))

VQ003 = frame_animation_Q1()
VQ003.title = ''
VQ003.num_frames = num_frames
VQ003.dpi = 300
VQ003.Q1_ext = '003'
VQ003.Q2_ext = '003'
VQ003.plot_Q1_params.color_by = ('w', (1, 1, 2, 2))


Q001 = frame_variable()
Q001.x_key_path = "['U2']['PERN-9999997']"
Q001.y_key_paths = ["['w_cv_area_weighted'][(1,1,2,2)]"]
Q001.normalize_x = -1
Q001.legends = ['w cv area-weighted']
Q001.normalized_by = 1
Q001.invert_y = False
Q001.xlabel = "Displacement [mm]"
Q001.ylabel = "w CV area-weighted"
Q001.title = None
Q001.derivative = False
Q001.save_path = 'frames_A/'
Q001.figsize = (4.75,4)
Q001.dpi = 100
Q001.num_frames = num_frames
Q001.plot_from_0 = False
Q001.file_key_y = 'Q2_001'
Q001.file_key_x = 'A2'
Q001.yscale = 'linear'


Q002 = frame_variable()
Q002.x_key_path = "['U2']['PERN-9999997']"
Q002.y_key_paths = ["['w_cv_area_weighted'][(1,1,2,2)]"]
Q002.normalize_x = -1
Q002.legends = ['w cv area-weighted']
Q002.normalized_by = 1
Q002.invert_y = False
Q002.xlabel = "Displacement [mm]"
Q002.ylabel = "w CV area-weighted"
Q002.title = None
Q002.derivative = False
Q002.save_path = 'frames_A/'
Q002.figsize = (4.75,4)
Q002.dpi = 100
Q002.num_frames = num_frames
Q002.plot_from_0 = False
Q002.file_key_y = 'Q2_002'
Q002.file_key_x = 'A2'
Q002.yscale = 'linear'


Q003 = frame_variable()
Q003.x_key_path = "['U2']['PERN-9999997']"
Q003.y_key_paths = ["['w_cv_area_weighted'][(1,1,2,2)]"]
Q003.normalize_x = -1
Q003.legends = ['w cv area-weighted']
Q003.normalized_by = 1
Q003.invert_y = False
Q003.xlabel = "Displacement [mm]"
Q003.ylabel = "w CV area-weighted"
Q003.title = None
Q003.derivative = False
Q003.save_path = 'frames_A/'
Q003.figsize = (4.75,4)
Q003.dpi = 100
Q003.num_frames = num_frames
Q003.plot_from_0 = False
Q003.file_key_y = 'Q2_003'
Q003.file_key_x = 'A2'
Q003.yscale = 'linear'


# ── Q2 variable helpers ───────────────────────────────────────────────────────
def _make_q2_var(file_key_y, key_path, ylabel, save_path):
    obj = frame_variable()
    obj.x_key_path = "['U2']['PERN-9999997']"
    obj.y_key_paths = [key_path]
    obj.normalize_x = -1
    obj.legends = [ylabel]
    obj.normalized_by = 1
    obj.invert_y = False
    obj.xlabel = "Displacement [mm]"
    obj.ylabel = ylabel
    obj.title = None
    obj.derivative = False
    obj.save_path = save_path
    obj.figsize = (4.75, 4)
    obj.dpi = 100
    obj.num_frames = num_frames
    obj.plot_from_0 = False
    obj.file_key_y = file_key_y
    obj.file_key_x = 'A2'
    obj.yscale = 'linear'
    return obj

Q001_wcv     = _make_q2_var('Q2_001', "['w_cv'][(1,1,2,2)]",                'w CV',                  'frames_Q001_wcv/')
Q002_wcv     = _make_q2_var('Q2_002', "['w_cv'][(1,1,2,2)]",                'w CV',                  'frames_Q002_wcv/')
Q003_wcv     = _make_q2_var('Q2_003', "['w_cv'][(1,1,2,2)]",                'w CV',                  'frames_Q003_wcv/')

Q001_wstd    = _make_q2_var('Q2_001', "['w_std'][(1,1,2,2)]",               'w std',                 'frames_Q001_wstd/')
Q002_wstd    = _make_q2_var('Q2_002', "['w_std'][(1,1,2,2)]",               'w std',                 'frames_Q002_wstd/')
Q003_wstd    = _make_q2_var('Q2_003', "['w_std'][(1,1,2,2)]",               'w std',                 'frames_Q003_wstd/')

Q001_wstd_aw = _make_q2_var('Q2_001', "['w_std_area_weighted'][(1,1,2,2)]", 'w std area-weighted',   'frames_Q001_wstd_aw/')
Q002_wstd_aw = _make_q2_var('Q2_002', "['w_std_area_weighted'][(1,1,2,2)]", 'w std area-weighted',   'frames_Q002_wstd_aw/')
Q003_wstd_aw = _make_q2_var('Q2_003', "['w_std_area_weighted'][(1,1,2,2)]", 'w std area-weighted',   'frames_Q003_wstd_aw/')

Q001_wmean   = _make_q2_var('Q2_001', "['w_mean'][(1,1,2,2)]",              'w mean',                'frames_Q001_wmean/')
Q002_wmean   = _make_q2_var('Q2_002', "['w_mean'][(1,1,2,2)]",              'w mean',                'frames_Q002_wmean/')
Q003_wmean   = _make_q2_var('Q2_003', "['w_mean'][(1,1,2,2)]",              'w mean',                'frames_Q003_wmean/')

Q001_W       = _make_q2_var('Q2_001', "['W'][(1,1,2,2)]",                   'W (total energy)',      'frames_Q001_W/')
Q002_W       = _make_q2_var('Q2_002', "['W'][(1,1,2,2)]",                   'W (total energy)',      'frames_Q002_W/')
Q003_W       = _make_q2_var('Q2_003', "['W'][(1,1,2,2)]",                   'W (total energy)',      'frames_Q003_W/')

Q001_eta     = _make_q2_var('Q2_001', "['eta']",                             'eta (mesh regularity)', 'frames_Q001_eta/')
Q002_eta     = _make_q2_var('Q2_002', "['eta']",                             'eta (mesh regularity)', 'frames_Q002_eta/')
Q003_eta     = _make_q2_var('Q2_003', "['eta']",                             'eta (mesh regularity)', 'frames_Q003_eta/')

Q001_shear_mean = _make_q2_var('Q2_001', "['shear_mean']",                  'shear mean',            'frames_Q001_shear_mean/')
Q002_shear_mean = _make_q2_var('Q2_002', "['shear_mean']",                  'shear mean',            'frames_Q002_shear_mean/')
Q003_shear_mean = _make_q2_var('Q2_003', "['shear_mean']",                  'shear mean',            'frames_Q003_shear_mean/')

Q001_gle_mean   = _make_q2_var('Q2_001', "['gle_mean']",                    'GLE mean',              'frames_Q001_gle_mean/')
Q002_gle_mean   = _make_q2_var('Q2_002', "['gle_mean']",                    'GLE mean',              'frames_Q002_gle_mean/')
Q003_gle_mean   = _make_q2_var('Q2_003', "['gle_mean']",                    'GLE mean',              'frames_Q003_gle_mean/')

Q001_edi_mean   = _make_q2_var('Q2_001', "['edi_mean']",                    'EDI mean',              'frames_Q001_edi_mean/')
Q002_edi_mean   = _make_q2_var('Q2_002', "['edi_mean']",                    'EDI mean',              'frames_Q002_edi_mean/')
Q003_edi_mean   = _make_q2_var('Q2_003', "['edi_mean']",                    'EDI mean',              'frames_Q003_edi_mean/')


T = frames_combination()
T.canvas_size = (3500, 6200)
T.title = "Deformation {-DATA['U2']['PERN-9999997'][ti]:0.2f} mm | E = {DATA_J['E']} MPa | Pi = {DATA_J['steps'][0]['Pressure_BC']} MPa | Porosity = {porosity}"
T.title_position = (1000, 10)
T.title_font = '/home/fruffini/.conda/envs/Fenv/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf'
T.title_size = 40
T.subtitle_size = 25
T.title_color = "black"
T.subtitle_color = "black"
T.dpi = (300, 300)
T.save_path = 'frames_final/'
T.canvas_color = "white"
T.size = (300,300),
T.subtitle_font = '/home/fruffini/.conda/envs/Fenv/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf'
T.subtitle_offset = 5
T.delete_after_concat = False
T.max_parallel = 20
T.frames_format = 'png'
T.num_frames = num_frames
T.vid_folder = 'Video_1003'
T.elements = [
    {
        "position": (50, 100),
        "size": (500, 500),
        "path": "frames_A1/",
        "subtitle": "Stress / E",
        "create_frames": True,
        "type": 'V',
        "object": A1,
        "replace_frames": False,
    },
    {
        "position": (50, 650),
        "size": (500, 500),
        "path": "frames_A25/",
        "subtitle": "der(Stress / E)",
        "create_frames": True,
        "type": 'V',
        "object": A25,
        "replace_frames": False,
    },
    {
        "position": (50, 1200),
        "size": (500, 500),
        "path": "frames_A60/",
        "subtitle": "ALLIE & ALLKE",
        "create_frames": True,
        "type": 'V',
        "object": A60,
        "replace_frames": False,
    },
    {
        "position": (50, 1750),
        "size": (500, 500),
        "path": "frames_A61/",
        "subtitle": "ALLSE / ALLIE",
        "create_frames": True,
        "type": 'V',
        "object": A61,
        "replace_frames": False,
    },
    {
        "position": (600, 100),
        "size": (500, 500),
        "path": "frames_VQ001/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'Q1A',
        "object": VQ001,
        "replace_frames": False,
    },
    {
        "position": (600, 650),
        "size": (500, 500),
        "path": "frames_Q001/",
        "subtitle": "Energy density variability",
        "create_frames": True,
        "type": 'V',
        "object": Q001,
        "replace_frames": False,
    },
    {
        "position": (1200, 100),
        "size": (500, 500),
        "path": "frames_VQ002/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'Q1A',
        "object": VQ002,
        "replace_frames": False,
    },
    {
        "position": (1200, 650),
        "size": (500, 500),
        "path": "frames_Q002/",
        "subtitle": "Energy density variability",
        "create_frames": True,
        "type": 'V',
        "object": Q002,
        "replace_frames": False,
    },
    {
        "position": (1800, 100),
        "size": (500, 500),
        "path": "frames_VQ003/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'Q1A',
        "object": VQ003,
        "replace_frames": False,
    },
    {
        "position": (1800, 650),
        "size": (500, 500),
        "path": "frames_Q003/",
        "subtitle": "Energy density variability",
        "create_frames": True,
        "type": 'V',
        "object": Q003,
        "replace_frames": False,
    },
    # ── w_cv ──────────────────────────────────────────────────────────────
    {
        "position": (600, 1200),
        "size": (500, 500),
        "path": "frames_Q001_wcv/",
        "subtitle": "w CV",
        "create_frames": True,
        "type": 'V',
        "object": Q001_wcv,
        "replace_frames": False,
    },
    {
        "position": (1200, 1200),
        "size": (500, 500),
        "path": "frames_Q002_wcv/",
        "subtitle": "w CV",
        "create_frames": True,
        "type": 'V',
        "object": Q002_wcv,
        "replace_frames": False,
    },
    {
        "position": (1800, 1200),
        "size": (500, 500),
        "path": "frames_Q003_wcv/",
        "subtitle": "w CV",
        "create_frames": True,
        "type": 'V',
        "object": Q003_wcv,
        "replace_frames": False,
    },
    # ── w_std ─────────────────────────────────────────────────────────────
    {
        "position": (600, 1750),
        "size": (500, 500),
        "path": "frames_Q001_wstd/",
        "subtitle": "w std",
        "create_frames": True,
        "type": 'V',
        "object": Q001_wstd,
        "replace_frames": False,
    },
    {
        "position": (1200, 1750),
        "size": (500, 500),
        "path": "frames_Q002_wstd/",
        "subtitle": "w std",
        "create_frames": True,
        "type": 'V',
        "object": Q002_wstd,
        "replace_frames": False,
    },
    {
        "position": (1800, 1750),
        "size": (500, 500),
        "path": "frames_Q003_wstd/",
        "subtitle": "w std",
        "create_frames": True,
        "type": 'V',
        "object": Q003_wstd,
        "replace_frames": False,
    },
    # ── w_std_area_weighted ───────────────────────────────────────────────
    {
        "position": (600, 2300),
        "size": (500, 500),
        "path": "frames_Q001_wstd_aw/",
        "subtitle": "w std area-weighted",
        "create_frames": True,
        "type": 'V',
        "object": Q001_wstd_aw,
        "replace_frames": False,
    },
    {
        "position": (1200, 2300),
        "size": (500, 500),
        "path": "frames_Q002_wstd_aw/",
        "subtitle": "w std area-weighted",
        "create_frames": True,
        "type": 'V',
        "object": Q002_wstd_aw,
        "replace_frames": False,
    },
    {
        "position": (1800, 2300),
        "size": (500, 500),
        "path": "frames_Q003_wstd_aw/",
        "subtitle": "w std area-weighted",
        "create_frames": True,
        "type": 'V',
        "object": Q003_wstd_aw,
        "replace_frames": False,
    },
    # ── w_mean ────────────────────────────────────────────────────────────
    {
        "position": (600, 2850),
        "size": (500, 500),
        "path": "frames_Q001_wmean/",
        "subtitle": "w mean",
        "create_frames": True,
        "type": 'V',
        "object": Q001_wmean,
        "replace_frames": False,
    },
    {
        "position": (1200, 2850),
        "size": (500, 500),
        "path": "frames_Q002_wmean/",
        "subtitle": "w mean",
        "create_frames": True,
        "type": 'V',
        "object": Q002_wmean,
        "replace_frames": False,
    },
    {
        "position": (1800, 2850),
        "size": (500, 500),
        "path": "frames_Q003_wmean/",
        "subtitle": "w mean",
        "create_frames": True,
        "type": 'V',
        "object": Q003_wmean,
        "replace_frames": False,
    },
    # ── W (total area-weighted energy) ────────────────────────────────────
    {
        "position": (600, 3400),
        "size": (500, 500),
        "path": "frames_Q001_W/",
        "subtitle": "W (total energy)",
        "create_frames": True,
        "type": 'V',
        "object": Q001_W,
        "replace_frames": False,
    },
    {
        "position": (1200, 3400),
        "size": (500, 500),
        "path": "frames_Q002_W/",
        "subtitle": "W (total energy)",
        "create_frames": True,
        "type": 'V',
        "object": Q002_W,
        "replace_frames": False,
    },
    {
        "position": (1800, 3400),
        "size": (500, 500),
        "path": "frames_Q003_W/",
        "subtitle": "W (total energy)",
        "create_frames": True,
        "type": 'V',
        "object": Q003_W,
        "replace_frames": False,
    },
    # ── eta (mesh regularity) ─────────────────────────────────────────────
    {
        "position": (600, 3950),
        "size": (500, 500),
        "path": "frames_Q001_eta/",
        "subtitle": "eta (mesh regularity)",
        "create_frames": True,
        "type": 'V',
        "object": Q001_eta,
        "replace_frames": False,
    },
    {
        "position": (1200, 3950),
        "size": (500, 500),
        "path": "frames_Q002_eta/",
        "subtitle": "eta (mesh regularity)",
        "create_frames": True,
        "type": 'V',
        "object": Q002_eta,
        "replace_frames": False,
    },
    {
        "position": (1800, 3950),
        "size": (500, 500),
        "path": "frames_Q003_eta/",
        "subtitle": "eta (mesh regularity)",
        "create_frames": True,
        "type": 'V',
        "object": Q003_eta,
        "replace_frames": False,
    },
    # ── shear_mean ────────────────────────────────────────────────────────
    {
        "position": (600, 4500),
        "size": (500, 500),
        "path": "frames_Q001_shear_mean/",
        "subtitle": "shear mean",
        "create_frames": True,
        "type": 'V',
        "object": Q001_shear_mean,
        "replace_frames": False,
    },
    {
        "position": (1200, 4500),
        "size": (500, 500),
        "path": "frames_Q002_shear_mean/",
        "subtitle": "shear mean",
        "create_frames": True,
        "type": 'V',
        "object": Q002_shear_mean,
        "replace_frames": False,
    },
    {
        "position": (1800, 4500),
        "size": (500, 500),
        "path": "frames_Q003_shear_mean/",
        "subtitle": "shear mean",
        "create_frames": True,
        "type": 'V',
        "object": Q003_shear_mean,
        "replace_frames": False,
    },
    # ── gle_mean ──────────────────────────────────────────────────────────
    {
        "position": (600, 5050),
        "size": (500, 500),
        "path": "frames_Q001_gle_mean/",
        "subtitle": "GLE mean",
        "create_frames": True,
        "type": 'V',
        "object": Q001_gle_mean,
        "replace_frames": False,
    },
    {
        "position": (1200, 5050),
        "size": (500, 500),
        "path": "frames_Q002_gle_mean/",
        "subtitle": "GLE mean",
        "create_frames": True,
        "type": 'V',
        "object": Q002_gle_mean,
        "replace_frames": False,
    },
    {
        "position": (1800, 5050),
        "size": (500, 500),
        "path": "frames_Q003_gle_mean/",
        "subtitle": "GLE mean",
        "create_frames": True,
        "type": 'V',
        "object": Q003_gle_mean,
        "replace_frames": False,
    },
    # ── edi_mean ──────────────────────────────────────────────────────────
    {
        "position": (600, 5600),
        "size": (500, 500),
        "path": "frames_Q001_edi_mean/",
        "subtitle": "EDI mean",
        "create_frames": True,
        "type": 'V',
        "object": Q001_edi_mean,
        "replace_frames": False,
    },
    {
        "position": (1200, 5600),
        "size": (500, 500),
        "path": "frames_Q002_edi_mean/",
        "subtitle": "EDI mean",
        "create_frames": True,
        "type": 'V',
        "object": Q002_edi_mean,
        "replace_frames": False,
    },
    {
        "position": (1800, 5600),
        "size": (500, 500),
        "path": "frames_Q003_edi_mean/",
        "subtitle": "EDI mean",
        "create_frames": True,
        "type": 'V',
        "object": Q003_edi_mean,
        "replace_frames": False,
    },
]


SCONF = SimulationConfig()
SCONF.vid_folder = 'Video_1003'
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = "mp4v"
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_test.mp4'
