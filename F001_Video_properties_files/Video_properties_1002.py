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







VT001 = frame_animation_T1()
VT001.title = ''
VT001.num_frames = num_frames
VT001.dpi = 300
VT001.T1_ext = '001'
VT001.T2_ext = '001'
VT001.plot_T1_params.color_by = ('w', (1, 1, 2, 2))   # → t2['w'][(1,1,2,2)][eid][ti]
# VT001.plot_T1_params.vmin = 0               # → red
# VT001.plot_T1_params.vmax = 1               # → white / transparent
# VT001.plot_T1_params.cmap = 'red_white'     # linear: red=0, white=1
# VT001.plot_T1_params.colorbar_label = 'w'
# VT001.xlim = [-2, 22]
# VT001.ylim = [-2, 22]


VT002 = frame_animation_T1()
VT002.title = ''
VT002.num_frames = num_frames
VT002.dpi = 300
VT002.T1_ext = '002'
VT002.T2_ext = '002'
VT002.plot_T1_params.color_by = ('w', (1, 1, 2, 2))


VT003 = frame_animation_T1()
VT003.title = ''
VT003.num_frames = num_frames
VT003.dpi = 300
VT003.T1_ext = '003'
VT003.T2_ext = '003'
VT003.plot_T1_params.color_by = ('w', (1, 1, 2, 2))





T001 = frame_variable()   
T001.x_key_path = "['U2']['PERN-9999997']"
T001.y_key_paths = ["['w_cv_area_weighted'][(1,1,2,2)]"]
T001.normalize_x = -1
T001.legends = ['w cv area-weighted']
T001.normalized_by = 1
T001.invert_y = False
T001.xlabel = "Displacement [mm]"
T001.ylabel = "w CV area-weighted"
T001.title = None
T001.derivative = False
T001.save_path = 'frames_A/'
T001.figsize = (4.75,4)
T001.dpi = 100
T001.num_frames = num_frames
T001.plot_from_0 = False
T001.file_key_y = 'T2_001'
T001.file_key_x = 'A2'
T001.yscale = 'linear'


T002 = frame_variable()   
T002.x_key_path = "['U2']['PERN-9999997']"
T002.y_key_paths = ["['w_cv_area_weighted'][(1,1,2,2)]"]
T002.normalize_x = -1
T002.legends = ['w cv area-weighted']
T002.normalized_by = 1
T002.invert_y = False
T002.xlabel = "Displacement [mm]"
T002.ylabel = "w CV area-weighted"
T002.title = None
T002.derivative = False
T002.save_path = 'frames_A/'
T002.figsize = (4.75,4)
T002.dpi = 100
T002.num_frames = num_frames
T002.plot_from_0 = False
T002.file_key_y = 'T2_002'
T002.file_key_x = 'A2'
T002.yscale = 'linear'



T003 = frame_variable()   
T003.x_key_path = "['U2']['PERN-9999997']"
T003.y_key_paths = ["['w_cv_area_weighted'][(1,1,2,2)]"]
T003.normalize_x = -1
T003.legends = ['w cv area-weighted']
T003.normalized_by = 1
T003.invert_y = False
T003.xlabel = "Displacement [mm]"
T003.ylabel = "w CV area-weighted"
T003.title = None
T003.derivative = False
T003.save_path = 'frames_A/'
T003.figsize = (4.75,4)
T003.dpi = 100
T003.num_frames = num_frames
T003.plot_from_0 = False
T003.file_key_y = 'T2_003'
T003.file_key_x = 'A2'
T003.yscale = 'linear'


# ── w_cv ──────────────────────────────────────────────────────────────────────
def _make_t2_var(file_key_y, key_path, ylabel, save_path):
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

T001_wcv              = _make_t2_var('T2_001', "['w_cv'][(1,1,2,2)]",              'w CV',                   'frames_T001_wcv/')
T002_wcv              = _make_t2_var('T2_002', "['w_cv'][(1,1,2,2)]",              'w CV',                   'frames_T002_wcv/')
T003_wcv              = _make_t2_var('T2_003', "['w_cv'][(1,1,2,2)]",              'w CV',                   'frames_T003_wcv/')

T001_wstd             = _make_t2_var('T2_001', "['w_std'][(1,1,2,2)]",             'w std',                  'frames_T001_wstd/')
T002_wstd             = _make_t2_var('T2_002', "['w_std'][(1,1,2,2)]",             'w std',                  'frames_T002_wstd/')
T003_wstd             = _make_t2_var('T2_003', "['w_std'][(1,1,2,2)]",             'w std',                  'frames_T003_wstd/')

T001_wstd_aw          = _make_t2_var('T2_001', "['w_std_area_weighted'][(1,1,2,2)]", 'w std area-weighted',  'frames_T001_wstd_aw/')
T002_wstd_aw          = _make_t2_var('T2_002', "['w_std_area_weighted'][(1,1,2,2)]", 'w std area-weighted',  'frames_T002_wstd_aw/')
T003_wstd_aw          = _make_t2_var('T2_003', "['w_std_area_weighted'][(1,1,2,2)]", 'w std area-weighted',  'frames_T003_wstd_aw/')

T001_wmean            = _make_t2_var('T2_001', "['w_mean'][(1,1,2,2)]",            'w mean',                 'frames_T001_wmean/')
T002_wmean            = _make_t2_var('T2_002', "['w_mean'][(1,1,2,2)]",            'w mean',                 'frames_T002_wmean/')
T003_wmean            = _make_t2_var('T2_003', "['w_mean'][(1,1,2,2)]",            'w mean',                 'frames_T003_wmean/')

T001_W                = _make_t2_var('T2_001', "['W'][(1,1,2,2)]",                 'W (total energy)',       'frames_T001_W/')
T002_W                = _make_t2_var('T2_002', "['W'][(1,1,2,2)]",                 'W (total energy)',       'frames_T002_W/')
T003_W                = _make_t2_var('T2_003', "['W'][(1,1,2,2)]",                 'W (total energy)',       'frames_T003_W/')

T001_eta              = _make_t2_var('T2_001', "['eta']",                           'eta (mesh regularity)',  'frames_T001_eta/')
T002_eta              = _make_t2_var('T2_002', "['eta']",                           'eta (mesh regularity)',  'frames_T002_eta/')
T003_eta              = _make_t2_var('T2_003', "['eta']",                           'eta (mesh regularity)',  'frames_T003_eta/')

T001_shear_mean       = _make_t2_var('T2_001', "['shear_mean']",                   'shear mean',             'frames_T001_shear_mean/')
T002_shear_mean       = _make_t2_var('T2_002', "['shear_mean']",                   'shear mean',             'frames_T002_shear_mean/')
T003_shear_mean       = _make_t2_var('T2_003', "['shear_mean']",                   'shear mean',             'frames_T003_shear_mean/')

T001_gle_mean         = _make_t2_var('T2_001', "['gle_mean']",                     'GLE mean',               'frames_T001_gle_mean/')
T002_gle_mean         = _make_t2_var('T2_002', "['gle_mean']",                     'GLE mean',               'frames_T002_gle_mean/')
T003_gle_mean         = _make_t2_var('T2_003', "['gle_mean']",                     'GLE mean',               'frames_T003_gle_mean/')

T001_edi_mean         = _make_t2_var('T2_001', "['edi_mean']",                     'EDI mean',               'frames_T001_edi_mean/')
T002_edi_mean         = _make_t2_var('T2_002', "['edi_mean']",                     'EDI mean',               'frames_T002_edi_mean/')
T003_edi_mean         = _make_t2_var('T2_003', "['edi_mean']",                     'EDI mean',               'frames_T003_edi_mean/')


T = frames_combination()
T.canvas_size = (3500, 6200)
# T.title = "Deformation {DATA['U2']['Y-POSITIVE'][ti]:0.2f} mm | E = {DATA_J['E']} MPa | Ei = {DATA_J['steps'][0]['Pressure_BC']} MPa"
T.title = "Deformation {-DATA['U2']['PERN-9999997'][ti]:0.2f} mm | E = {DATA_J['E']} MPa | Pi = {DATA_J['steps'][0]['Pressure_BC']} MPa | Porosity = {porosity}"
# T.title = " SIN TITULO"
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
T.vid_folder = 'Video_1002'
T.elements = [
    {
        "position": (50, 100),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A1/",
        "subtitle": "Stress / E",
        "create_frames": True,
        "type": 'V',
        "object": A1,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (50, 650),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A25/",
        "subtitle": "der(Stress / E)",
        "create_frames": True,
        "type": 'V',
        "object": A25,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
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
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_VT001/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'T1A',
        "object": VT001,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (600, 650),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_T001/",
        "subtitle": "Energy density variability",
        "create_frames": True,
        "type": 'V',
        "object": T001,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (1200, 100),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_VT002/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'T1A',
        "object": VT002,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (1200, 650),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_T002/",
        "subtitle": "Energy density variability",
        "create_frames": True,
        "type": 'V',
        "object": T002,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (1800, 100),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_VT003/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'T1A',
        "object": VT003,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (1800, 650),
        "size": (500, 500), 
        "path": "frames_T003/",
        "subtitle": "Energy density variability",
        "create_frames": True,
        "type": 'V',
        "object": T003,
        "replace_frames": False,
    },
    # ── w_cv ──────────────────────────────────────────────────────────────
    {
        "position": (600, 1200),
        "size": (500, 500),
        "path": "frames_T001_wcv/",
        "subtitle": "w CV",
        "create_frames": True,
        "type": 'V',
        "object": T001_wcv,
        "replace_frames": False,
    },
    {
        "position": (1200, 1200),
        "size": (500, 500),
        "path": "frames_T002_wcv/",
        "subtitle": "w CV",
        "create_frames": True,
        "type": 'V',
        "object": T002_wcv,
        "replace_frames": False,
    },
    {
        "position": (1800, 1200),
        "size": (500, 500),
        "path": "frames_T003_wcv/",
        "subtitle": "w CV",
        "create_frames": True,
        "type": 'V',
        "object": T003_wcv,
        "replace_frames": False,
    },
    # ── w_std ─────────────────────────────────────────────────────────────
    {
        "position": (600, 1750),
        "size": (500, 500),
        "path": "frames_T001_wstd/",
        "subtitle": "w std",
        "create_frames": True,
        "type": 'V',
        "object": T001_wstd,
        "replace_frames": False,
    },
    {
        "position": (1200, 1750),
        "size": (500, 500),
        "path": "frames_T002_wstd/",
        "subtitle": "w std",
        "create_frames": True,
        "type": 'V',
        "object": T002_wstd,
        "replace_frames": False,
    },
    {
        "position": (1800, 1750),
        "size": (500, 500),
        "path": "frames_T003_wstd/",
        "subtitle": "w std",
        "create_frames": True,
        "type": 'V',
        "object": T003_wstd,
        "replace_frames": False,
    },
    # ── w_std_area_weighted ───────────────────────────────────────────────
    {
        "position": (600, 2300),
        "size": (500, 500),
        "path": "frames_T001_wstd_aw/",
        "subtitle": "w std area-weighted",
        "create_frames": True,
        "type": 'V',
        "object": T001_wstd_aw,
        "replace_frames": False,
    },
    {
        "position": (1200, 2300),
        "size": (500, 500),
        "path": "frames_T002_wstd_aw/",
        "subtitle": "w std area-weighted",
        "create_frames": True,
        "type": 'V',
        "object": T002_wstd_aw,
        "replace_frames": False,
    },
    {
        "position": (1800, 2300),
        "size": (500, 500),
        "path": "frames_T003_wstd_aw/",
        "subtitle": "w std area-weighted",
        "create_frames": True,
        "type": 'V',
        "object": T003_wstd_aw,
        "replace_frames": False,
    },
    # ── w_mean ────────────────────────────────────────────────────────────
    {
        "position": (600, 2850),
        "size": (500, 500),
        "path": "frames_T001_wmean/",
        "subtitle": "w mean",
        "create_frames": True,
        "type": 'V',
        "object": T001_wmean,
        "replace_frames": False,
    },
    {
        "position": (1200, 2850),
        "size": (500, 500),
        "path": "frames_T002_wmean/",
        "subtitle": "w mean",
        "create_frames": True,
        "type": 'V',
        "object": T002_wmean,
        "replace_frames": False,
    },
    {
        "position": (1800, 2850),
        "size": (500, 500),
        "path": "frames_T003_wmean/",
        "subtitle": "w mean",
        "create_frames": True,
        "type": 'V',
        "object": T003_wmean,
        "replace_frames": False,
    },
    # ── W (total area-weighted energy) ────────────────────────────────────
    {
        "position": (600, 3400),
        "size": (500, 500),
        "path": "frames_T001_W/",
        "subtitle": "W (total energy)",
        "create_frames": True,
        "type": 'V',
        "object": T001_W,
        "replace_frames": False,
    },
    {
        "position": (1200, 3400),
        "size": (500, 500),
        "path": "frames_T002_W/",
        "subtitle": "W (total energy)",
        "create_frames": True,
        "type": 'V',
        "object": T002_W,
        "replace_frames": False,
    },
    {
        "position": (1800, 3400),
        "size": (500, 500),
        "path": "frames_T003_W/",
        "subtitle": "W (total energy)",
        "create_frames": True,
        "type": 'V',
        "object": T003_W,
        "replace_frames": False,
    },
    # ── eta (mesh regularity) ─────────────────────────────────────────────
    {
        "position": (600, 3950),
        "size": (500, 500),
        "path": "frames_T001_eta/",
        "subtitle": "eta (mesh regularity)",
        "create_frames": True,
        "type": 'V',
        "object": T001_eta,
        "replace_frames": False,
    },
    {
        "position": (1200, 3950),
        "size": (500, 500),
        "path": "frames_T002_eta/",
        "subtitle": "eta (mesh regularity)",
        "create_frames": True,
        "type": 'V',
        "object": T002_eta,
        "replace_frames": False,
    },
    {
        "position": (1800, 3950),
        "size": (500, 500),
        "path": "frames_T003_eta/",
        "subtitle": "eta (mesh regularity)",
        "create_frames": True,
        "type": 'V',
        "object": T003_eta,
        "replace_frames": False,
    },
    # ── shear_mean ────────────────────────────────────────────────────────
    {
        "position": (600, 4500),
        "size": (500, 500),
        "path": "frames_T001_shear_mean/",
        "subtitle": "shear mean",
        "create_frames": True,
        "type": 'V',
        "object": T001_shear_mean,
        "replace_frames": False,
    },
    {
        "position": (1200, 4500),
        "size": (500, 500),
        "path": "frames_T002_shear_mean/",
        "subtitle": "shear mean",
        "create_frames": True,
        "type": 'V',
        "object": T002_shear_mean,
        "replace_frames": False,
    },
    {
        "position": (1800, 4500),
        "size": (500, 500),
        "path": "frames_T003_shear_mean/",
        "subtitle": "shear mean",
        "create_frames": True,
        "type": 'V',
        "object": T003_shear_mean,
        "replace_frames": False,
    },
    # ── gle_mean ──────────────────────────────────────────────────────────
    {
        "position": (600, 5050),
        "size": (500, 500),
        "path": "frames_T001_gle_mean/",
        "subtitle": "GLE mean",
        "create_frames": True,
        "type": 'V',
        "object": T001_gle_mean,
        "replace_frames": False,
    },
    {
        "position": (1200, 5050),
        "size": (500, 500),
        "path": "frames_T002_gle_mean/",
        "subtitle": "GLE mean",
        "create_frames": True,
        "type": 'V',
        "object": T002_gle_mean,
        "replace_frames": False,
    },
    {
        "position": (1800, 5050),
        "size": (500, 500),
        "path": "frames_T003_gle_mean/",
        "subtitle": "GLE mean",
        "create_frames": True,
        "type": 'V',
        "object": T003_gle_mean,
        "replace_frames": False,
    },
    # ── edi_mean ──────────────────────────────────────────────────────────
    {
        "position": (600, 5600),
        "size": (500, 500),
        "path": "frames_T001_edi_mean/",
        "subtitle": "EDI mean",
        "create_frames": True,
        "type": 'V',
        "object": T001_edi_mean,
        "replace_frames": False,
    },
    {
        "position": (1200, 5600),
        "size": (500, 500),
        "path": "frames_T002_edi_mean/",
        "subtitle": "EDI mean",
        "create_frames": True,
        "type": 'V',
        "object": T002_edi_mean,
        "replace_frames": False,
    },
    {
        "position": (1800, 5600),
        "size": (500, 500),
        "path": "frames_T003_edi_mean/",
        "subtitle": "EDI mean",
        "create_frames": True,
        "type": 'V',
        "object": T003_edi_mean,
        "replace_frames": False,
    },

]


SCONF = SimulationConfig()
SCONF.vid_folder = 'Video_1002'
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = "mp4v"
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_test.mp4'









