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
A61.ratio_key_pairs = [("['ALLSD']['ASSEMBLY']", "['ALLWK']['ASSEMBLY']")]
A61.legends = ['ALLSD / ALLWK']
A61.normalized_by = 1
A61.invert_y = False
A61.xlabel = "Time [s]"
A61.ylabel = "ALLSD / ALLWK"
A61.title = None
A61.derivative = False
A61.save_path = 'frames_A61/'
A61.figsize = (5, 5)
A61.dpi = 100
A61.num_frames = num_frames
A61.plot_from_0 = False
A61.file_key_x = 'A'
A61.file_key_y = 'A'




T = frames_combination()
T.canvas_size = (2200, 1100)
# T.title = "Deformation {DATA['U2']['Y-POSITIVE'][ti]:0.2f} mm | E = {DATA_J['E']} MPa | Ei = {DATA_J['steps'][0]['Pressure_BC']} MPa"
T.title = "Deformation {-DATA['U2']['PERN-9999997'][ti]:0.2f} mm | E = {DATA_J['E']} MPa | Pi = {DATA_J['steps'][0]['Pressure_BC']} MPa | Porosity = {porosity}"
# T.title = " SIN TITULO"
T.title_position = (400, 10)
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
T.vid_folder = 'Video_1000'
T.elements = [
    {
        "position": (1100, 100),
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
        "position": (50, 100),
        "size": (1000, 1000),
        "path": "frames_A3/",
        "subtitle": "",
        "create_frames": True,
        "type": 'A',
        "object": A3,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1100, 650),
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
        "position": (1650, 100),
        "size": (500, 500),
        "path": "frames_A60/",
        "subtitle": "ALLIE & ALLKE",
        "create_frames": True,
        "type": 'V',
        "object": A60,
        "replace_frames": False,
    },
    {
        "position": (1650, 650),
        "size": (500, 500),
        "path": "frames_A61/",
        "subtitle": "ALLSE / ALLIE",
        "create_frames": True,
        "type": 'V',
        "object": A61,
        "replace_frames": False,
    },


]


SCONF = SimulationConfig()
SCONF.vid_folder = 'Video_1000'
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = "mp4v"
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_test.mp4'




