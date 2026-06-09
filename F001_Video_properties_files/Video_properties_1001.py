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
A61.ratio_key_pairs = [("['ALLWK']['ASSEMBLY']", "['ALLSE']['ASSEMBLY']")]
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


HT3001 = frame_animation_graph()
HT3001.title = ''
HT3001.num_frames = num_frames
HT3001.dpi = 300
HT3001.J1_ext = '3001'
HT3001.key_letter = 'H'
HT3001.plot_ten_comp = 't'
HT3001.plot_ten_comp_color_bar = False


HC3001 = frame_animation_graph()
HC3001.title = ''
HC3001.num_frames = num_frames
HC3001.dpi = 300
HC3001.J1_ext = '3001'
HC3001.key_letter = 'H'
HC3001.plot_ten_comp = 'c'
HC3001.plot_ten_comp_color_bar = False


FH3001 = graph_property()
FH3001.ppty = 'G_eff'
FH3001.legends = True
FH3001.grid = True
FH3001.Title = None
FH3001.xlabel = 'Compression Ratio'
FH3001.ylabel = 'Average \n global efficiency'
FH3001.save_path = 'frames_10/'
FH3001.legend_loc = 'upper right'
FH3001.dpi = 100
FH3001.figsize = (4.75,4)
FH3001.num_frames = num_frames
FH3001.file_ext = 'H3_BFS_3001'


IT3001 = frame_animation_graph()
IT3001.title = ''
IT3001.num_frames = num_frames
IT3001.dpi = 300
IT3001.J1_ext = '3001'
IT3001.key_letter = 'I'
IT3001.plot_ten_comp = 't'
IT3001.plot_ten_comp_color_bar = False


IC3001 = frame_animation_graph()
IC3001.title = ''
IC3001.num_frames = num_frames
IC3001.dpi = 300
IC3001.J1_ext = '3001'
IC3001.key_letter = 'I'
IC3001.plot_ten_comp = 'c'
IC3001.plot_ten_comp_color_bar = False


FI3001 = graph_property()
FI3001.ppty = 'G_eff'
FI3001.legends = True
FI3001.grid = True
FI3001.Title = None
FI3001.xlabel = 'Compression Ratio'
FI3001.ylabel = 'Average \n global efficiency'
FI3001.save_path = 'frames_10/'
FI3001.legend_loc = 'upper right'
FI3001.dpi = 100
FI3001.figsize = (4.75,4)
FI3001.num_frames = num_frames
FI3001.file_ext = 'I3_BFS_3001'








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


HT3002 = frame_animation_graph()
HT3002.title = ''
HT3002.num_frames = num_frames
HT3002.dpi = 300
HT3002.J1_ext = '3002'
HT3002.key_letter = 'H'
HT3002.plot_ten_comp = 't'
HT3002.plot_ten_comp_color_bar = False


HC3002 = frame_animation_graph()
HC3002.title = ''
HC3002.num_frames = num_frames
HC3002.dpi = 300
HC3002.J1_ext = '3002'
HC3002.key_letter = 'H'
HC3002.plot_ten_comp = 'c'
HC3002.plot_ten_comp_color_bar = False


FH3002 = graph_property()
FH3002.ppty = 'G_eff'
FH3002.legends = True
FH3002.grid = True
FH3002.Title = None
FH3002.xlabel = 'Compression Ratio'
FH3002.ylabel = 'Average \n global efficiency'
FH3002.save_path = 'frames_10/'
FH3002.legend_loc = 'upper right'
FH3002.dpi = 100
FH3002.figsize = (4.75,4)
FH3002.num_frames = num_frames
FH3002.file_ext = 'H3_BFS_3002'


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
FI3002.figsize = (4.75,4)
FI3002.num_frames = num_frames
FI3002.file_ext = 'I3_BFS_3002'







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


HT3003 = frame_animation_graph()
HT3003.title = ''
HT3003.num_frames = num_frames
HT3003.dpi = 300
HT3003.J1_ext = '3003'
HT3003.key_letter = 'H'
HT3003.plot_ten_comp = 't'
HT3003.plot_ten_comp_color_bar = False


HC3003 = frame_animation_graph()
HC3003.title = ''
HC3003.num_frames = num_frames
HC3003.dpi = 300
HC3003.J1_ext = '3003'
HC3003.key_letter = 'H'
HC3003.plot_ten_comp = 'c'
HC3003.plot_ten_comp_color_bar = False


FH3003 = graph_property()
FH3003.ppty = 'G_eff'
FH3003.legends = True
FH3003.grid = True
FH3003.Title = None
FH3003.xlabel = 'Compression Ratio'
FH3003.ylabel = 'Average \n global efficiency'
FH3003.save_path = 'frames_10/'
FH3003.legend_loc = 'upper right'
FH3003.dpi = 100
FH3003.figsize = (4.75,4)
FH3003.num_frames = num_frames
FH3003.file_ext = 'H3_BFS_3003'


IT3003 = frame_animation_graph()
IT3003.title = ''
IT3003.num_frames = num_frames
IT3003.dpi = 300
IT3003.J1_ext = '3003'
IT3003.key_letter = 'I'
IT3003.plot_ten_comp = 't'
IT3003.plot_ten_comp_color_bar = False


IC3003 = frame_animation_graph()
IC3003.title = ''
IC3003.num_frames = num_frames
IC3003.dpi = 300
IC3003.J1_ext = '3003'
IC3003.key_letter = 'I'
IC3003.plot_ten_comp = 'c'
IC3003.plot_ten_comp_color_bar = False


FI3003 = graph_property()
FI3003.ppty = 'G_eff'
FI3003.legends = True
FI3003.grid = True
FI3003.Title = None
FI3003.xlabel = 'Compression Ratio'
FI3003.ylabel = 'Average \n global efficiency'
FI3003.save_path = 'frames_10/'
FI3003.legend_loc = 'upper right'
FI3003.dpi = 100
FI3003.figsize = (4.75,4)
FI3003.num_frames = num_frames
FI3003.file_ext = 'I3_BFS_3003'




HT3004 = frame_animation_graph()
HT3004.title = ''
HT3004.num_frames = num_frames
HT3004.dpi = 300
HT3004.J1_ext = '3004'
HT3004.key_letter = 'H'
HT3004.plot_ten_comp = 't'
HT3004.plot_ten_comp_color_bar = False


HC3004 = frame_animation_graph()
HC3004.title = ''
HC3004.num_frames = num_frames
HC3004.dpi = 300
HC3004.J1_ext = '3004'
HC3004.key_letter = 'H'
HC3004.plot_ten_comp = 'c'
HC3004.plot_ten_comp_color_bar = False


FH3004 = graph_property()
FH3004.ppty = 'G_eff'
FH3004.legends = True
FH3004.grid = True
FH3004.Title = None
FH3004.xlabel = 'Compression Ratio'
FH3004.ylabel = 'Average \n global efficiency'
FH3004.save_path = 'frames_10/'
FH3004.legend_loc = 'upper right'
FH3004.dpi = 100
FH3004.figsize = (4.75,4)
FH3004.num_frames = num_frames
FH3004.file_ext = 'H3_BFS_3004'


IT3004 = frame_animation_graph()
IT3004.title = ''
IT3004.num_frames = num_frames
IT3004.dpi = 300
IT3004.J1_ext = '3004'
IT3004.key_letter = 'I'
IT3004.plot_ten_comp = 't'
IT3004.plot_ten_comp_color_bar = False


IC3004 = frame_animation_graph()
IC3004.title = ''
IC3004.num_frames = num_frames
IC3004.dpi = 300
IC3004.J1_ext = '3004'
IC3004.key_letter = 'I'
IC3004.plot_ten_comp = 'c'
IC3004.plot_ten_comp_color_bar = False


FI3004 = graph_property()
FI3004.ppty = 'G_eff'
FI3004.legends = True
FI3004.grid = True
FI3004.Title = None
FI3004.xlabel = 'Compression Ratio'
FI3004.ylabel = 'Average \n global efficiency'
FI3004.save_path = 'frames_10/'
FI3004.legend_loc = 'upper right'
FI3004.dpi = 100
FI3004.figsize = (4.75,4)
FI3004.num_frames = num_frames
FI3004.file_ext = 'I3_BFS_3004'





HT3005 = frame_animation_graph()
HT3005.title = ''
HT3005.num_frames = num_frames
HT3005.dpi = 300
HT3005.J1_ext = '3005'
HT3005.key_letter = 'H'
HT3005.plot_ten_comp = 't'
HT3005.plot_ten_comp_color_bar = False


HC3005 = frame_animation_graph()
HC3005.title = ''
HC3005.num_frames = num_frames
HC3005.dpi = 300
HC3005.J1_ext = '3005'
HC3005.key_letter = 'H'
HC3005.plot_ten_comp = 'c'
HC3005.plot_ten_comp_color_bar = False


FH3005 = graph_property()
FH3005.ppty = 'G_eff'
FH3005.legends = True
FH3005.grid = True
FH3005.Title = None
FH3005.xlabel = 'Compression Ratio'
FH3005.ylabel = 'Average \n global efficiency'
FH3005.save_path = 'frames_10/'
FH3005.legend_loc = 'upper right'
FH3005.dpi = 100
FH3005.figsize = (4.75,4)
FH3005.num_frames = num_frames
FH3005.file_ext = 'H3_BFS_3005'


IT3005 = frame_animation_graph()
IT3005.title = ''
IT3005.num_frames = num_frames
IT3005.dpi = 300
IT3005.J1_ext = '3005'
IT3005.key_letter = 'I'
IT3005.plot_ten_comp = 't'
IT3005.plot_ten_comp_color_bar = False


IC3005 = frame_animation_graph()
IC3005.title = ''
IC3005.num_frames = num_frames
IC3005.dpi = 300
IC3005.J1_ext = '3005'
IC3005.key_letter = 'I'
IC3005.plot_ten_comp = 'c'
IC3005.plot_ten_comp_color_bar = False


FI3005 = graph_property()
FI3005.ppty = 'G_eff'
FI3005.legends = True
FI3005.grid = True
FI3005.Title = None
FI3005.xlabel = 'Compression Ratio'
FI3005.ylabel = 'Average \n global efficiency'
FI3005.save_path = 'frames_10/'
FI3005.legend_loc = 'upper right'
FI3005.dpi = 100
FI3005.figsize = (4.75,4)
FI3005.num_frames = num_frames
FI3005.file_ext = 'I3_BFS_3005'


T = frames_combination()
T.canvas_size = (3500, 3000)
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
T.vid_folder = 'Video_1001'
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
        "position": (600, 1180),
        "size": (230, 230),
        "path": "frames_HT3001/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HT3001,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (870, 1180),
        "size": (230, 230),
        "path": "frames_HC3001/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HC3001,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (600, 1450),
        "size": (500, 500),
        "path": "frames_FH3001/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FH3001,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (600, 1980),
        "size": (230, 230),
        "path": "frames_IT3001/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IT3001,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (870, 1980),
        "size": (230, 230),
        "path": "frames_IC3001/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IC3001,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (600, 2250),
        "size": (500, 500),
        "path": "frames_FI3001/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FI3001,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
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
        "position": (1200, 1180),
        "size": (230, 230),
        "path": "frames_HT3002/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HT3002,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1470, 1180),
        "size": (230, 230),
        "path": "frames_HC3002/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HC3002,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1200, 1450),
        "size": (500, 500),
        "path": "frames_FH3002/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FH3002,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1200, 1980),
        "size": (230, 230),
        "path": "frames_IT3002/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IT3002,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1470, 1980),
        "size": (230, 230),
        "path": "frames_IC3002/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IC3002,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1200, 2250),
        "size": (500, 500),
        "path": "frames_FI3002/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FI3002,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
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
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_T003/",
        "subtitle": "Energy density variability",
        "create_frames": True,
        "type": 'V',
        "object": T003,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (1800, 1180),
        "size": (230, 230),
        "path": "frames_HT3003/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HT3003,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2070, 1180),
        "size": (230, 230),
        "path": "frames_HC3003/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HC3003,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1800, 1450),
        "size": (500, 500),
        "path": "frames_FH3003/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FH3003,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1800, 1980),
        "size": (230, 230),
        "path": "frames_IT3003/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IT3003,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2070, 1980),
        "size": (230, 230),
        "path": "frames_IC3003/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IC3003,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1800, 2250),
        "size": (500, 500),
        "path": "frames_FI3003/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FI3003,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
        {
        "position": (2400, 1180),
        "size": (230, 230),
        "path": "frames_HT3004/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HT3004,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2670, 1180),
        "size": (230, 230),
        "path": "frames_HC3004/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HC3004,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2400, 1450),
        "size": (500, 500),
        "path": "frames_FH3004/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FH3004,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2400, 1980),
        "size": (230, 230),
        "path": "frames_IT3004/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IT3004,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2670, 1980),
        "size": (230, 230),
        "path": "frames_IC3004/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IC3004,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2400, 2250),
        "size": (500, 500),
        "path": "frames_FI3004/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FI3004,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3000, 1180),
        "size": (230, 230),
        "path": "frames_HT3005/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HT3005,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3270, 1180),
        "size": (230, 230),
        "path": "frames_HC3005/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": HC3005,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3000, 1450),
        "size": (500, 500),
        "path": "frames_FH3005/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FH3005,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3000, 1980),
        "size": (230, 230),
        "path": "frames_IT3005/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IT3005,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3270, 1980),
        "size": (230, 230),
        "path": "frames_IC3005/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": IC3005,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3000, 2250),
        "size": (500, 500),
        "path": "frames_FI3005/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": FI3005,
        "replace_frames": False,
        # "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },

]


SCONF = SimulationConfig()
SCONF.vid_folder = 'Video_1001'
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = "mp4v"
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_test.mp4'






SCONF = SimulationConfig()
SCONF.vid_folder = 'Video_1001'
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = "mp4v"
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_test.mp4'




