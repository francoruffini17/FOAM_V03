import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from A001_functions.Video_functions import *
import numpy as np
from typing import Callable, Optional


num_frames = 201

# ── Reaction force ─────────────────────────────────────────────────────────────
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
A1.save_path = 'frames_A1/'
A1.figsize = (4.75, 4)
A1.dpi = 100
A1.num_frames = num_frames
A1.plot_from_0 = True


# ── Derivative of reaction force ───────────────────────────────────────────────
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
A25.save_path = 'frames_A25/'
A25.figsize = (4.75, 4)
A25.dpi = 100
A25.num_frames = num_frames
A25.plot_from_0 = True


# ── ALLSD / ALLWK ──────────────────────────────────────────────────────────────
A61b = frame_variable()
A61b.x_key_path = "['t']"
A61b.y_key_paths = []
A61b.ratio_key_pairs = [("['ALLSD']['ASSEMBLY']", "['ALLWK']['ASSEMBLY']")]
A61b.legends = ['ALLSD / ALLWK']
A61b.normalized_by = 1
A61b.invert_y = False
A61b.xlabel = "Time [s]"
A61b.ylabel = "ALLSD / ALLWK"
A61b.title = None
A61b.derivative = False
A61b.save_path = 'frames_A61b/'
A61b.figsize = (5, 5)
A61b.dpi = 100
A61b.num_frames = num_frames
A61b.plot_from_0 = False
A61b.ylim = (-0.01, 0.05)
A61b.file_key_x = 'A'
A61b.file_key_y = 'A'


# ── Q2_001 animated mesh (coloured by energy density w) ───────────────────────
VQ001 = frame_animation_Q1()
VQ001.title = ''
VQ001.num_frames = num_frames
VQ001.dpi = 300
VQ001.Q1_ext = '001'
VQ001.Q2_ext = '001'
VQ001.plot_Q1_params.color_by = ('w', (1, 1, 2, 2))


# ── TP1 animated mesh (coloured by A/A₀) ──────────────────────────────────────
VTP1 = frame_animation_TP1()
VTP1.title = ''
VTP1.num_frames = num_frames
VTP1.dpi = 300
VTP1.TP1_ext = ''
VTP1.TP2_ext = None
VTP1.plot_TP1_params.color_by = 'area'


# ── Q2_001 scalar time-series ──────────────────────────────────────────────────
def _make_q2_var(key_path, ylabel, save_path):
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
    obj.file_key_y = 'Q2_001'
    obj.file_key_x = 'A2'
    obj.yscale = 'linear'
    return obj

Q_eta    = _make_q2_var("['eta']",                            'eta',               'frames_Q_eta/')
Q_shear  = _make_q2_var("['shear_mean']",                     'shear mean',         'frames_Q_shear/')
Q_gle    = _make_q2_var("['gle_mean']",                       'GLE mean',           'frames_Q_gle/')
Q_edi    = _make_q2_var("['edi_mean']",                       'EDI mean',           'frames_Q_edi/')
Q_wcv    = _make_q2_var("['w_cv'][(1,1,2,2)]",               'w CV',               'frames_Q_wcv/')
Q_wcv_aw = _make_q2_var("['w_cv_area_weighted'][(1,1,2,2)]", 'w CV area-weighted', 'frames_Q_wcv_aw/')


# ── TP2 scalar time-series (mirrors Q2 panel) ──────────────────────────────────
def _make_tp2_var(key_path, ylabel, save_path):
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
    obj.file_key_y = 'TP2'
    obj.file_key_x = 'A2'
    obj.yscale = 'linear'
    return obj

TP_eta    = _make_tp2_var("['eta']",                            'eta (TP)',               'frames_TP_eta/')
TP_shear  = _make_tp2_var("['shear_mean']",                     'shear mean (TP)',         'frames_TP_shear/')
TP_gle    = _make_tp2_var("['gle_mean']",                       'GLE mean (TP)',           'frames_TP_gle/')
TP_edi    = _make_tp2_var("['edi_mean']",                       'EDI mean (TP)',           'frames_TP_edi/')
TP_wcv    = _make_tp2_var("['w_cv'][(1,1,2,2)]",               'w CV (TP)',               'frames_TP_wcv/')
TP_wcv_aw = _make_tp2_var("['w_cv_area_weighted'][(1,1,2,2)]", 'w CV area-weighted (TP)', 'frames_TP_wcv_aw/')


# ── Canvas layout  (3510 × 1500, 8 cols × 3 rows, 400 × 400 per cell) ─────────
#   Left group  (Q2):  col x = 50   470   890  1310
#   Right group (TP2): col x = 1800 2220  2640 3060
#   Row y: 80  530  980

T = frames_combination()
T.canvas_size = (3510, 1500)
T.title = "Deformation {-DATA['U2']['PERN-9999997'][ti]:0.2f} mm | E = {DATA_J['E']} MPa | Pi = {DATA_J['steps'][0]['Pressure_BC']} MPa | Porosity = {porosity}"
T.title_position = (50, 10)
T.title_font = '/home/fruffini/.conda/envs/Fenv/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf'
T.title_size = 32
T.subtitle_size = 22
T.title_color = "black"
T.subtitle_color = "black"
T.dpi = (300, 300)
T.save_path = 'frames_final/'
T.canvas_color = "white"
T.size = (300, 300),
T.subtitle_font = '/home/fruffini/.conda/envs/Fenv/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf'
T.subtitle_offset = 5
T.delete_after_concat = False
T.max_parallel = 20
T.frames_format = 'png'
T.num_frames = num_frames
T.vid_folder = 'Video_1005'
T.elements = [
    # ── Left: Row 0 — global curves + Q2 mesh animation ──────────────────
    {
        "position": (50, 80),
        "size": (400, 400),
        "path": "frames_A1/",
        "subtitle": "Reaction force",
        "create_frames": True,
        "type": 'V',
        "object": A1,
        "replace_frames": False,
    },
    {
        "position": (470, 80),
        "size": (400, 400),
        "path": "frames_A25/",
        "subtitle": "d(RF) / d(U)",
        "create_frames": True,
        "type": 'V',
        "object": A25,
        "replace_frames": False,
    },
    {
        "position": (890, 80),
        "size": (400, 400),
        "path": "frames_A61b/",
        "subtitle": "ALLSD / ALLWK",
        "create_frames": True,
        "type": 'V',
        "object": A61b,
        "replace_frames": False,
    },
    {
        "position": (1310, 80),
        "size": (400, 400),
        "path": "frames_VQ001/",
        "subtitle": "Q2_001 — energy density w",
        "create_frames": True,
        "type": 'Q1A',
        "object": VQ001,
        "replace_frames": False,
    },
    # ── Left: Row 1 — Q2 mesh quality / deformation metrics ───────────────
    {
        "position": (50, 530),
        "size": (400, 400),
        "path": "frames_Q_eta/",
        "subtitle": "eta",
        "create_frames": True,
        "type": 'V',
        "object": Q_eta,
        "replace_frames": False,
    },
    {
        "position": (470, 530),
        "size": (400, 400),
        "path": "frames_Q_shear/",
        "subtitle": "shear mean",
        "create_frames": True,
        "type": 'V',
        "object": Q_shear,
        "replace_frames": False,
    },
    {
        "position": (890, 530),
        "size": (400, 400),
        "path": "frames_Q_gle/",
        "subtitle": "GLE mean",
        "create_frames": True,
        "type": 'V',
        "object": Q_gle,
        "replace_frames": False,
    },
    {
        "position": (1310, 530),
        "size": (400, 400),
        "path": "frames_Q_edi/",
        "subtitle": "EDI mean",
        "create_frames": True,
        "type": 'V',
        "object": Q_edi,
        "replace_frames": False,
    },
    # ── Left: Row 2 — Q2 energy variability ───────────────────────────────
    {
        "position": (50, 980),
        "size": (400, 400),
        "path": "frames_Q_wcv/",
        "subtitle": "w CV",
        "create_frames": True,
        "type": 'V',
        "object": Q_wcv,
        "replace_frames": False,
    },
    {
        "position": (470, 980),
        "size": (400, 400),
        "path": "frames_Q_wcv_aw/",
        "subtitle": "w CV area-weighted",
        "create_frames": True,
        "type": 'V',
        "object": Q_wcv_aw,
        "replace_frames": False,
    },
    # ── Right: Row 0 — TP1 mesh animation + TP2 metrics ───────────────────
    {
        "position": (1800, 80),
        "size": (400, 400),
        "path": "frames_VTP1/",
        "subtitle": "TP1 — A/A₀",
        "create_frames": True,
        "type": 'TP1A',
        "object": VTP1,
        "replace_frames": False,
    },
    {
        "position": (2220, 80),
        "size": (400, 400),
        "path": "frames_TP_eta/",
        "subtitle": "eta (TP)",
        "create_frames": True,
        "type": 'V',
        "object": TP_eta,
        "replace_frames": False,
    },
    {
        "position": (2640, 80),
        "size": (400, 400),
        "path": "frames_TP_shear/",
        "subtitle": "shear mean (TP)",
        "create_frames": True,
        "type": 'V',
        "object": TP_shear,
        "replace_frames": False,
    },
    {
        "position": (3060, 80),
        "size": (400, 400),
        "path": "frames_TP_gle/",
        "subtitle": "GLE mean (TP)",
        "create_frames": True,
        "type": 'V',
        "object": TP_gle,
        "replace_frames": False,
    },
    # ── Right: Row 1 — more TP2 metrics ───────────────────────────────────
    {
        "position": (1800, 530),
        "size": (400, 400),
        "path": "frames_TP_edi/",
        "subtitle": "EDI mean (TP)",
        "create_frames": True,
        "type": 'V',
        "object": TP_edi,
        "replace_frames": False,
    },
    {
        "position": (2220, 530),
        "size": (400, 400),
        "path": "frames_TP_wcv/",
        "subtitle": "w CV (TP)",
        "create_frames": True,
        "type": 'V',
        "object": TP_wcv,
        "replace_frames": False,
    },
    {
        "position": (2640, 530),
        "size": (400, 400),
        "path": "frames_TP_wcv_aw/",
        "subtitle": "w CV area-weighted (TP)",
        "create_frames": True,
        "type": 'V',
        "object": TP_wcv_aw,
        "replace_frames": False,
    },
]


SCONF = SimulationConfig()
SCONF.vid_folder = 'Video_1005'
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = "mp4v"
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_test.mp4'
