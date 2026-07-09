import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from A001_functions.Video_functions import *
import numpy as np
from typing import Callable, Optional

# Subset of Video_properties_1009: reaction force, foam animation (S11+S22),
# tension/compression graphs, average global efficiency, tension/compression
# efficiency ratio, EDI mean, shear mean, eta_C^A and eta_C^R.
# Same panel naming/conventions as 1009; every curve/scalar panel marks the
# localization point (frame index of the minimum of TP2_L's shear_mean).

num_frames = 201

# ── Foam mesh animation (coloured by S11+S22) ──────────────────────────────────
A3 = frame_animation()
A3.title = ''
A3.num_frames = num_frames
A3.figsize = (15, 15)
A3.xlim = (-4, 24)
A3.ylim = (-4, 24)
A3.color_element = 'S11 + S22'
A3.mesh_line_size = 0
A3.node_size = 0


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
A1.mark_localization = True


# ── I3002 — tension / compression graph animations ────────────────────────────
IT3002 = frame_animation_graph()
IT3002.title = ''
IT3002.num_frames = num_frames
IT3002.dpi = 300
IT3002.J1_ext = '3002'
IT3002.key_letter = 'I'
IT3002.plot_ten_comp = 't'
IT3002.plot_ten_comp_color_bar = False


IC3002 = frame_animation_graph()
IC3002.title = ''
IC3002.num_frames = num_frames
IC3002.dpi = 300
IC3002.J1_ext = '3002'
IC3002.key_letter = 'I'
IC3002.plot_ten_comp = 'c'
IC3002.plot_ten_comp_color_bar = False


# ── I3002 — average global efficiency ─────────────────────────────────────────
FI3002 = graph_property()
FI3002.ppty = 'G_eff'
FI3002.legends = True
FI3002.grid = True
FI3002.Title = None
FI3002.xlabel = 'Compression Ratio'
FI3002.ylabel = 'Average \n global efficiency'
FI3002.save_path = 'frames_10/'
FI3002.legend_loc = 'upper right'
FI3002.dpi = 100
FI3002.figsize = (4.75, 4)
FI3002.num_frames = num_frames
FI3002.file_ext = 'I3_BFS_3002'
FI3002.include_allnodes = True
FI3002.mark_localization = True


# ── I3002 — tension / compression efficiency ratio ────────────────────────────
FFI3002 = graph_property()
FFI3002.ppty = 'f'
FFI3002.tension_compression = 'comb'
FFI3002.legends = True
FFI3002.grid = True
FFI3002.Title = None
FFI3002.xlabel = 'Compression Ratio'
FFI3002.ylabel = 'Tension / Compression \n efficiency'
FFI3002.save_path = 'frames_10/'
FFI3002.legend_loc = 'upper right'
FFI3002.dpi = 100
FFI3002.figsize = (4.75, 4)
FFI3002.num_frames = num_frames
FFI3002.file_ext = 'I3_BFS_3002'
FFI3002.yscale = 'log'
FFI3002.mark_localization = True


# ── TP2 scalar time-series ─────────────────────────────────────────────────────
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
    obj.mark_localization = True
    return obj

TP_edi   = _make_tp2_var("['edi_mean']",   'EDI mean (TP)',   'frames_TP_edi/')
TP_shear = _make_tp2_var("['shear_mean']", 'shear mean (TP)', 'frames_TP_shear/')


# ── DEFC2 — hole localization indices ─────────────────────────────────────────
#
# Column 4: η_C^A  — original | 1st derivative | 2nd derivative
# Column 5: η_C^R  — original | 1st derivative | 2nd derivative

def _make_defc_var(key, label, save_path, deriv_order=False):
    obj = frame_variable()
    obj.x_key_path = "['displacement']"
    obj.y_key_paths = [f"['{key}']"]
    obj.normalize_x = -1
    obj.legends = [label]
    obj.normalized_by = 1
    obj.invert_y = False
    obj.xlabel = "Step-1 compression [mm]"
    obj.ylabel = label
    obj.title = None
    obj.derivative = deriv_order
    obj.save_path = save_path
    obj.figsize = (4.75, 4)
    obj.dpi = 100
    obj.num_frames = num_frames
    obj.plot_from_0 = True
    obj.file_key_x = 'DEFC2'
    obj.file_key_y = 'DEFC2'
    obj.yscale = 'linear'
    obj.mark_localization = True
    return obj

# η_C^A
DEFC_etaCA    = _make_defc_var('etaC_A', r'$\eta_C^A$',                'frames_DEFC_etaCA/')

# η_C^R
DEFC_etaCR    = _make_defc_var('etaC_R', r'$\eta_C^R$',                'frames_DEFC_etaCR/')


# ── Canvas layout ──────────────────────────────────────────────────────────────
#
#   Column 1 (x=50):   A1, A3                          — reaction force, foam animation
#   Column 2 (x=600):  IT3002+IC3002, FI3002, FFI3002  — I3002 graphs + efficiencies
#   Column 3 (x=1200): TP_edi, TP_shear                — TP2
#   Column 4 (x=1800): etaCA, etaCR                     — η_C^A, η_C^R
#
#   Canvas: 2350 × 1580 (column 2 is tallest: IT/IC3002, FI3002, FFI3002)
#
#   All 'V' and 'GP' panels above additionally mark the localization point
#   (frame index of min shear_mean) with a green diamond.

T = frames_combination()
T.canvas_size = (2350, 1580)
T.title = "Deformation {-DATA['U2']['PERN-9999997'][ti]:0.2f} mm | E = {DATA_J['E']} MPa | Pi = {DATA_J['steps'][0]['Pressure_BC']:0.3f} MPa | Porosity = {porosity}"
T.title_position = (50, 10)
T.title_font = '/home/fruffini/.conda/envs/Fenv/lib/python3.11/site-packages/matplotlib/mpl-data/fonts/ttf/DejaVuSans.ttf'
T.title_size = 40
T.subtitle_size = 25
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
T.vid_folder = 'Video_1010'
T.elements = [
    # ── Column 1: reaction force + foam animation ────────────────────────────
    {
        "position": (50, 100),
        "size": (500, 500),
        "path": "frames_A1/",
        "subtitle": "Reaction force",
        "create_frames": True,
        "type": 'V',
        "object": A1,
        "replace_frames": False,
    },
    {
        "position": (50, 650),
        "size": (500, 500),
        "path": "frames_A3/",
        "subtitle": "Foam animation (S11+S22)",
        "create_frames": True,
        "type": 'A',
        "object": A3,
        "replace_frames": False,
    },
    # ── Column 2: I3002 graph animations + efficiencies ──────────────────────
    {
        "position": (600, 100),
        "size": (230, 230),
        "path": "frames_IT3002/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IT3002,
        "replace_frames": False,
    },
    {
        "position": (870, 100),
        "size": (230, 230),
        "path": "frames_IC3002/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IC3002,
        "replace_frames": False,
    },
    {
        "position": (600, 380),
        "size": (500, 500),
        "path": "frames_FI3002/",
        "subtitle": "I3002 avg global efficiency",
        "create_frames": True,
        "type": 'GP',
        "object": FI3002,
        "replace_frames": False,
    },
    {
        "position": (600, 930),
        "size": (500, 500),
        "path": "frames_FFI3002/",
        "subtitle": "I3002 tension/compression ratio",
        "create_frames": True,
        "type": 'GP',
        "object": FFI3002,
        "replace_frames": False,
    },
    # ── Column 3: TP2 ─────────────────────────────────────────────────────────
    {
        "position": (1200, 100),
        "size": (500, 500),
        "path": "frames_TP_edi/",
        "subtitle": "EDI mean (TP)",
        "create_frames": True,
        "type": 'V',
        "object": TP_edi,
        "replace_frames": False,
    },
    {
        "position": (1200, 650),
        "size": (500, 500),
        "path": "frames_TP_shear/",
        "subtitle": "shear mean (TP)",
        "create_frames": True,
        "type": 'V',
        "object": TP_shear,
        "replace_frames": False,
    },
    # ── Column 4: η_C^A + η_C^R ───────────────────────────────────────────────
    {
        "position": (1800, 100),
        "size": (500, 500),
        "path": "frames_DEFC_etaCA/",
        "subtitle": "η_C^A — area localization",
        "create_frames": True,
        "type": 'V',
        "object": DEFC_etaCA,
        "replace_frames": False,
    },
    {
        "position": (1800, 650),
        "size": (500, 500),
        "path": "frames_DEFC_etaCR/",
        "subtitle": "η_C^R — aspect-ratio localization",
        "create_frames": True,
        "type": 'V',
        "object": DEFC_etaCR,
        "replace_frames": False,
    },
]


SCONF = SimulationConfig()
SCONF.vid_folder = 'Video_1010'
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = "mp4v"
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_test.mp4'
