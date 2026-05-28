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

A2 = frame_animation(condition = lambda node: 8.333 < node[0] < 11.6667 and 8.333 < node[1] < 11.6667)
A2.title = ''
A2.num_frames = num_frames
A2.figsize = (15,15)
A2.xlim = (8, 12)
A2.ylim = (8, 12)
A2.color_element = 'S11 + S22'
A2.mesh_line_size = 0
A2.node_size = 0


A3 = frame_animation()
A3.title = ''
A3.num_frames = num_frames
A3.figsize = (15,15)
A3.xlim = (-4, 24)
A3.ylim = (-4, 24)
A3.color_element = 'S11 + S22'
A3.mesh_line_size = 0
A3.node_size = 0





A4 = graph_property()
A4.ppty = 'G_eff'
A4.legends = True
A4.grid = True
A4.Title = None
A4.xlabel = 'Compression Ratio'
A4.ylabel = 'Average \n global efficiency'
A4.save_path = 'frames_10/'
A4.legend_loc = 'upper right'
A4.dpi = 100
A4.figsize = (4.75,4)
A4.num_frames = num_frames
A4.file_ext = 'J3_BFS_2000'


A5 = graph_property()
A5.ppty = 'f'
A5.legends = True
A5.grid = True
A5.Title = None
A5.xlabel = 'Compression Ratio'
A5.ylabel = 'f'
A5.save_path = 'frames_10/'
A5.legend_loc = 'upper right'
A5.dpi = 100
A5.figsize = (4.75,4)
A5.num_frames = num_frames
A5.file_ext = 'J3_BFS_2000'
A5.tension_compression = 'comb'
A5.yscale = 'log'


A6 = frame_animation_graph()
A6.title = ''
A6.num_frames = num_frames
A6.dpi = 300
A6.J1_ext = '2000'
A6.key_letter = 'J'
A6.plot_ten_comp = 't'
A6.plot_ten_comp_color_bar = False


A7 = frame_animation_graph()
A7.title = ''
A7.num_frames = num_frames
A7.dpi = 300
A7.J1_ext = '2000'
A7.key_letter = 'J'
A7.plot_ten_comp = 'c'
A7.plot_ten_comp_color_bar = False



A8 = graph_property()
A8.ppty = 'G_eff'
A8.legends = True
A8.grid = True
A8.Title = None
A8.xlabel = 'Compression Ratio'
A8.ylabel = 'Average \n global efficiency'
A8.save_path = 'frames_10/'
A8.legend_loc = 'upper right'
A8.dpi = 100
A8.figsize = (4.75,4)
A8.num_frames = num_frames
A8.file_ext = 'H3_BFS_2000'


A9 = graph_property()
A9.ppty = 'f'
A9.legends = True
A9.grid = True
A9.Title = None
A9.xlabel = 'Compression Ratio'
A9.ylabel = 'f'
A9.save_path = 'frames_10/'
A9.legend_loc = 'upper right'
A9.dpi = 100
A9.figsize = (4.75,4)
A9.num_frames = num_frames
A9.file_ext = 'H3_BFS_2000'
A9.tension_compression = 'comb'
A9.yscale = 'log'




A10 = frame_animation_graph()
A10.title = ''
A10.num_frames = num_frames
A10.dpi = 300
A10.J1_ext = '2000'
A10.key_letter = 'H'
A10.plot_ten_comp = 't'
A10.plot_ten_comp_color_bar = False


A11 = frame_animation_graph()
A11.title = ''
A11.num_frames = num_frames
A11.dpi = 300
A11.J1_ext = '2000'
A11.key_letter = 'H'
A11.plot_ten_comp = 'c'
A11.plot_ten_comp_color_bar = False



A12 = frame_animation_graph()
A12.title = ''
A12.num_frames = num_frames
A12.dpi = 300
A12.J1_ext = '2000'
A12.key_letter = 'H'




A13 = graph_property()
A13.ppty = 'G_eff'
A13.legends = True
A13.grid = True
A13.Title = None
A13.xlabel = 'Compression Ratio'
A13.ylabel = 'Average \n global efficiency'
A13.save_path = 'frames_10/'
A13.legend_loc = 'upper right'
A13.dpi = 100
A13.figsize = (4.75,4)
A13.num_frames = num_frames
A13.file_ext = 'H3_BFS_2000'


A14 = graph_property()
A14.ppty = 'f'
A14.legends = True
A14.grid = True
A14.Title = None
A14.xlabel = 'Compression Ratio'
A14.ylabel = 'f'
A14.save_path = 'frames_10/'
A14.legend_loc = 'upper right'
A14.dpi = 100
A14.figsize = (4.75,4)
A14.num_frames = num_frames
A14.file_ext = 'H3_BFS_2000'
A14.tension_compression = 'comb'
A14.yscale = 'log'




A15 = frame_animation_graph()
A15.title = ''
A15.num_frames = num_frames
A15.dpi = 300
A15.J1_ext = '2000'
A15.key_letter = 'H'
A15.plot_ten_comp = 't'
A15.plot_ten_comp_color_bar = False


A16 = frame_animation_graph()
A16.title = ''
A16.num_frames = num_frames
A16.dpi = 300
A16.J1_ext = '2000'
A16.key_letter = 'H'
A16.plot_ten_comp = 'c'
A16.plot_ten_comp_color_bar = False






A17 = graph_property()
A17.ppty = 'G_eff'
A17.legends = True
A17.grid = True
A17.Title = None
A17.xlabel = 'Compression Ratio'
A17.ylabel = 'Average \n global efficiency'
A17.save_path = 'frames_10/'
A17.legend_loc = 'upper right'
A17.dpi = 100
A17.figsize = (4.75,4)
A17.num_frames = num_frames
A17.file_ext = 'I3_BFS_2000'


A18 = graph_property()
A18.ppty = 'f'
A18.legends = True
A18.grid = True
A18.Title = None
A18.xlabel = 'Compression Ratio'
A18.ylabel = 'f'
A18.save_path = 'frames_10/'
A18.legend_loc = 'upper right'
A18.dpi = 100
A18.figsize = (4.75,4)
A18.num_frames = num_frames
A18.file_ext = 'I3_BFS_2000'
A18.tension_compression = 'comb'
A18.yscale = 'log'




A19 = frame_animation_graph()
A19.title = ''
A19.num_frames = num_frames
A19.dpi = 300
A19.J1_ext = '2000'
A19.key_letter = 'I'
A19.plot_ten_comp = 't'
A19.plot_ten_comp_color_bar = False


A20 = frame_animation_graph()
A20.title = ''
A20.num_frames = num_frames
A20.dpi = 300
A20.J1_ext = '2000'
A20.key_letter = 'I'
A20.plot_ten_comp = 'c'
A20.plot_ten_comp_color_bar = False





A21 = graph_property()
A21.ppty = 'G_eff'
A21.legends = True
A21.grid = True
A21.Title = None
A21.xlabel = 'Compression Ratio'
A21.ylabel = 'Average \n global efficiency'
A21.save_path = 'frames_10/'
A21.legend_loc = 'upper right'
A21.dpi = 100
A21.figsize = (4.75,4)
A21.num_frames = num_frames
A21.file_ext = 'K3_BFS_2000'


A22 = graph_property()
A22.ppty = 'f'
A22.legends = True
A22.grid = True
A22.Title = None
A22.xlabel = 'Compression Ratio'
A22.ylabel = 'f'
A22.save_path = 'frames_10/'
A22.legend_loc = 'upper right'
A22.dpi = 100
A22.figsize = (4.75,4)
A22.num_frames = num_frames
A22.file_ext = 'K3_BFS_2000'
A22.tension_compression = 'comb'
A22.yscale = 'log'




A23 = frame_animation_graph()
A23.title = ''
A23.num_frames = num_frames
A23.dpi = 300
A23.J1_ext = '2000'
A23.key_letter = 'K'
A23.plot_ten_comp = 't'
A23.plot_ten_comp_color_bar = False


A24 = frame_animation_graph()
A24.title = ''
A24.num_frames = num_frames
A24.dpi = 300
A24.J1_ext = '2000'
A24.key_letter = 'K'
A24.plot_ten_comp = 'c'
A24.plot_ten_comp_color_bar = False



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


A30 = frame_animation_T1()
A30.title = ''
A30.num_frames = num_frames
A30.dpi = 300
A30.T1_ext = '001'
A30.plot_T1_params.color_limit = 2   # log scale [0.5, 2], red<1, white=1, blue>1
# A30.plot_T1_params.color_limit = 1.5 # log scale [0.67, 1.5]
# A30.plot_T1_params.color_limit = None # auto (original behavior)
A30.xlim = [-2, 22]
A30.ylim = [-2, 22]


A31 = frame_variable()   
A31.x_key_path = "['U2']['PERN-9999997']"
A31.y_key_paths = ["['eta']"]
A31.normalize_x = -1
A31.legends = ['Eta']
A31.normalized_by = 1
A31.invert_y = False
A31.xlabel = "Displacement [mm]"
A31.ylabel = "Eta"
A31.title = None
A31.derivative = False
A31.save_path = 'frames_A/'
A31.figsize = (4.75,4)
A31.dpi = 100
A31.num_frames = num_frames
A31.plot_from_0 = False
A31.file_key_y = 'T2_001'
A31.file_key_x = 'A2'



A32 = frame_variable()   
A32.x_key_path = "['U2']['PERN-9999997']"
A32.y_key_paths = ["['eta']"]
A32.normalize_x = -1
A32.legends = ['Eta']
A32.normalized_by = 1
A32.invert_y = False
A32.xlabel = "Displacement [mm]"
A32.ylabel = "Eta"
A32.title = None
A32.derivative = True
A32.save_path = 'frames_A/'
A32.figsize = (4.75,4)
A32.dpi = 100
A32.num_frames = num_frames
A32.plot_from_0 = False
A32.file_key_y = 'T2_001'
A32.file_key_x = 'A2'




A33 = frame_animation_T1()
A33.title = ''
A33.num_frames = num_frames
A33.dpi = 300
A33.T1_ext = '001'
A33.T2_ext = '001'
A33.plot_T1_params.color_by = 'shear'     # ½ tr(FᵀF)
A33.plot_T1_params.vmin = 0               # → red
A33.plot_T1_params.vmax = 1               # → white / transparent
A33.plot_T1_params.cmap = 'red_white'     # linear: red=0, white=1
A33.plot_T1_params.colorbar_label = 'Shear  ½ tr(FᵀF)'
A33.xlim = [-2, 22]
A33.ylim = [-2, 22]



A34 = frame_variable()   
A34.x_key_path = "['U2']['PERN-9999997']"
A34.y_key_paths = ["['shear_mean']"]
A34.normalize_x = -1
A34.legends = ['Shear_mean']
A34.normalized_by = 1
A34.invert_y = False
A34.xlabel = "Displacement [mm]"
A34.ylabel = "Shear_mean"
A34.title = None
A34.derivative = False
A34.save_path = 'frames_A/'
A34.figsize = (4.75,4)
A34.dpi = 100
A34.num_frames = num_frames
A34.plot_from_0 = False
A34.file_key_y = 'T2_001'
A34.file_key_x = 'A2'




A35 = frame_variable()   
A35.x_key_path = "['U2']['PERN-9999997']"
A35.y_key_paths = ["['shear_mean']"]
A35.normalize_x = -1
A35.legends = ['Shear_mean']
A35.normalized_by = 1
A35.invert_y = False
A35.xlabel = "Displacement [mm]"
A35.ylabel = "Shear_mean"
A35.title = None
A35.derivative = True
A35.save_path = 'frames_A/'
A35.figsize = (4.75,4)
A35.dpi = 100
A35.num_frames = num_frames
A35.plot_from_0 = False
A35.file_key_y = 'T2_001'
A35.file_key_x = 'A2'





A36 = frame_animation_T1()
A36.title = ''
A36.num_frames = num_frames
A36.dpi = 300
A36.T1_ext = '001'
A36.T2_ext = '001'
A36.plot_T1_params.color_by = 'edi'     # ½ tr(FᵀF)
A36.plot_T1_params.vmin = 0               # → red
A36.plot_T1_params.vmax = 1               # → white / transparent
A36.plot_T1_params.cmap = 'red_white'     # linear: red=0, white=1
A36.plot_T1_params.colorbar_label = 'Edi  Edge deformation index'
A36.xlim = [-2, 22]
A36.ylim = [-2, 22]



A37 = frame_variable()   
A37.x_key_path = "['U2']['PERN-9999997']"
A37.y_key_paths = ["['edi_mean']"]
A37.normalize_x = -1
A37.legends = ['edi_mean']
A37.normalized_by = 1
A37.invert_y = False
A37.xlabel = "Displacement [mm]"
A37.ylabel = "edi_mean"
A37.title = None
A37.derivative = False
A37.save_path = 'frames_A/'
A37.figsize = (4.75,4)
A37.dpi = 100
A37.num_frames = num_frames
A37.plot_from_0 = False
A37.file_key_y = 'T2_001'
A37.file_key_x = 'A2'




A38 = frame_variable()   
A38.x_key_path = "['U2']['PERN-9999997']"
A38.y_key_paths = ["['edi_mean']"]
A38.normalize_x = -1
A38.legends = ['edi_mean']
A38.normalized_by = 1
A38.invert_y = False
A38.xlabel = "Displacement [mm]"
A38.ylabel = "edi_mean"
A38.title = None
A38.derivative = True
A38.save_path = 'frames_A/'
A38.figsize = (4.75,4)
A38.dpi = 100
A38.num_frames = num_frames
A38.plot_from_0 = False
A38.file_key_y = 'T2_001'
A38.file_key_x = 'A2'






A40 = graph_property()
A40.ppty = 'G_eff'
A40.legends = True
A40.grid = True
A40.Title = None
A40.xlabel = 'Compression Ratio'
A40.ylabel = 'Average \n global efficiency'
A40.save_path = 'frames_10/'
A40.legend_loc = 'upper right'
A40.dpi = 100
A40.figsize = (4.75,4)
A40.num_frames = num_frames
A40.file_ext = 'H3_BFS_2000'


A41 = graph_property()
A41.ppty = 'f'
A41.legends = True
A41.grid = True
A41.Title = None
A41.xlabel = 'Compression Ratio'
A41.ylabel = 'f'
A41.save_path = 'frames_10/'
A41.legend_loc = 'upper right'
A41.dpi = 100
A41.figsize = (4.75,4)
A41.num_frames = num_frames
A41.file_ext = 'H3_BFS_2000'
A41.tension_compression = 'comb'
A41.yscale = 'log'




A42 = frame_animation_graph()
A42.title = ''
A42.num_frames = num_frames
A42.dpi = 300
A42.J1_ext = '2000'
A42.key_letter = 'H'
A42.plot_ten_comp = 't'
A42.plot_ten_comp_color_bar = False


A43 = frame_animation_graph()
A43.title = ''
A43.num_frames = num_frames
A43.dpi = 300
A43.J1_ext = '2000'
A43.key_letter = 'H'
A43.plot_ten_comp = 'c'
A43.plot_ten_comp_color_bar = False


A44 = graph_property()
A44.ppty = 'G_eff'
A44.legends = True
A44.grid = True
A44.Title = None
A44.xlabel = 'Compression Ratio'
A44.ylabel = 'Average \n global efficiency'
A44.save_path = 'frames_10/'
A44.legend_loc = 'upper right'
A44.dpi = 100
A44.figsize = (4.75,4)
A44.num_frames = num_frames
A44.file_ext = 'I3_BFS_2000'


A45 = graph_property()
A45.ppty = 'f'
A45.legends = True
A45.grid = True
A45.Title = None
A45.xlabel = 'Compression Ratio'
A45.ylabel = 'f'
A45.save_path = 'frames_10/'
A45.legend_loc = 'upper right'
A45.dpi = 100
A45.figsize = (4.75,4)
A45.num_frames = num_frames
A45.file_ext = 'I3_BFS_2000'
A45.tension_compression = 'comb'
A45.yscale = 'log'




A46 = frame_animation_graph()
A46.title = ''
A46.num_frames = num_frames
A46.dpi = 300
A46.J1_ext = '2000'
A46.key_letter = 'I'
A46.plot_ten_comp = 't'
A46.plot_ten_comp_color_bar = False


A47 = frame_animation_graph()
A47.title = ''
A47.num_frames = num_frames
A47.dpi = 300
A47.J1_ext = '2000'
A47.key_letter = 'I'
A47.plot_ten_comp = 'c'
A47.plot_ten_comp_color_bar = False



A50 = frame_animation_T1()
A50.title = ''
A50.num_frames = num_frames
A50.dpi = 300
A50.T1_ext = '001'
A50.T2_ext = '001'
A50.plot_T1_params.color_by = ('w', (1, 1, 2, 2))   # → t2['w'][(1,1,2,2)][eid][ti]
# A50.plot_T1_params.vmin = 0               # → red
# A50.plot_T1_params.vmax = 1               # → white / transparent
# A50.plot_T1_params.cmap = 'red_white'     # linear: red=0, white=1
# A50.plot_T1_params.colorbar_label = 'w'
# A50.xlim = [-2, 22]
# A50.ylim = [-2, 22]




A51 = frame_variable()   
A51.x_key_path = "['U2']['PERN-9999997']"
A51.y_key_paths = ["['W'][(1,1,2,2)]"]
A51.normalize_x = -1
A51.legends = ['W']
A51.normalized_by = 1
A51.invert_y = False
A51.xlabel = "Displacement [mm]"
A51.ylabel = "W"
A51.title = None
A51.derivative = False
A51.save_path = 'frames_A/'
A51.figsize = (4.75,4)
A51.dpi = 100
A51.num_frames = num_frames
A51.plot_from_0 = False
A51.file_key_y = 'T2_001'
A51.file_key_x = 'A2'
A51.yscale = 'log'




A52 = frame_variable()   
A52.x_key_path = "['U2']['PERN-9999997']"
A52.y_key_paths = ["['W'][(1,1,2,2)]"]
A52.normalize_x = -1
A52.legends = ['W']
A52.normalized_by = 1
A52.invert_y = False
A52.xlabel = "Displacement [mm]"
A52.ylabel = "W"
A52.title = None
A52.derivative = True
A52.save_path = 'frames_A/'
A52.figsize = (4.75,4)
A52.dpi = 100
A52.num_frames = num_frames
A52.plot_from_0 = False
A52.file_key_y = 'T2_001'
A52.file_key_x = 'A2'
A52.yscale = 'log'
A52.yscale = 'log'



A60 = frame_variable()
A60.x_key_path = "['t']"
A60.y_key_paths = ["['ALLIE']['ASSEMBLY']", "['ALLKE']['ASSEMBLY']"]
A60.legends = ['ALLIE', 'ALLKE']
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
A61.ratio_key_pairs = [("['ALLSE']['ASSEMBLY']", "['ALLIE']['ASSEMBLY']")]
A61.legends = ['ALLSE / ALLIE']
A61.normalized_by = 1
A61.invert_y = False
A61.xlabel = "Time [s]"
A61.ylabel = "ALLSE / ALLIE"
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
T.canvas_size = (7700, 2450)
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
T.vid_folder = 'Video_2010'
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
        "size": (500, 500),
        "path": "frames_A2/",
        "subtitle": "",
        "create_frames": False,
        "type": 'A',
        "object": A2,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (550, 100),
        "size": (1050, 1050),
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
        "position": (1650, 100),
        "size": (500, 500),
        "path": "frames_A4/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A4,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1650, 650),
        "size": (500, 500),
        "path": "frames_A5/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A5,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1650, 1200),
        "size": (500, 500),
        "path": "frames_A6/",
        "subtitle": "",
        "create_frames": False,
        "type": 'GA',
        "object": A6,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (1650, 1750),
        "size": (500, 500),
        "path": "frames_A7/",
        "subtitle": "",
        "create_frames": False,
        "type": 'GA',
        "object": A7,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2200, 100),
        "size": (500, 500),
        "path": "frames_A8/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A8,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2200, 650),
        "size": (500, 500),
        "path": "frames_A9/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A9,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2200, 1200),
        "size": (500, 500),
        "path": "frames_A10/",
        "subtitle": "",
        "create_frames": False,
        "type": 'GA',
        "object": A10,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2200, 1750),
        "size": (500, 500),
        "path": "frames_A11/",
        "subtitle": "",
        "create_frames": False,
        "type": 'GA',
        "object": A11,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (550, 1100),
        "size": (1050, 1050),
        "path": "frames_A12/",
        "subtitle": "",
        "create_frames": False,
        "type": 'GA',
        "object": A12,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2750, 100),
        "size": (500, 500),
        "path": "frames_A13/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A13,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2750, 650),
        "size": (500, 500),
        "path": "frames_A14/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A14,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2750, 1200),
        "size": (500, 500),
        "path": "frames_A15/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": A15,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (2750, 1750),
        "size": (500, 500),
        "path": "frames_A16/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": A16,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3850, 100),
        "size": (500, 500),
        "path": "frames_A17/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A17,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3850, 650),
        "size": (500, 500),
        "path": "frames_A18/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A18,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3850, 1200),
        "size": (500, 500),
        "path": "frames_A19/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": A19,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3850, 1750),
        "size": (500, 500),
        "path": "frames_A20/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": A20,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (4950, 100),
        "size": (500, 500),
        "path": "frames_A21/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A21,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (4950, 650),
        "size": (500, 500),
        "path": "frames_A22/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A22,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (4950, 1200),
        "size": (500, 500),
        "path": "frames_A23/",
        "subtitle": "",
        "create_frames": False,
        "type": 'GA',
        "object": A23,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (4950, 1750),
        "size": (500, 500),
        "path": "frames_A24/",
        "subtitle": "",
        "create_frames": False,
        "type": 'GA',
        "object": A24,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (50, 1200),
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
        "position": (50, 1750),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A26/",
        "subtitle": "der2(Stress / E)",
        "create_frames": True,
        "type": 'V',
        "object": A26,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (5500, 100),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A30/",
        "subtitle": "A/A0",
        "create_frames": True,
        "type": 'T1A',
        "object": A30,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (5500, 650),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A31/",
        "subtitle": "eta",
        "create_frames": True,
        "type": 'V',
        "object": A31,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (5500, 1200),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A32/",
        "subtitle": "der(eta)",
        "create_frames": True,
        "type": 'V',
        "object": A32,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (6050, 100),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A33/",
        "subtitle": "S",
        "create_frames": True,
        "type": 'T1A',
        "object": A33,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (6050, 650),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A34/",
        "subtitle": "S",
        "create_frames": True,
        "type": 'V',
        "object": A34,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (6050, 1200),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A35/",
        "subtitle": "der(S)",
        "create_frames": True,
        "type": 'V',
        "object": A35,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (6600, 100),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A36/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'T1A',
        "object": A36,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (6600, 650),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A37/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'V',
        "object": A37,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (6600, 1200),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A38/",
        "subtitle": "der(Edge index)",
        "create_frames": True,
        "type": 'V',
        "object": A38,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (3300, 100),
        "size": (500, 500),
        "path": "frames_A40/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A40,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3300, 650),
        "size": (500, 500),
        "path": "frames_A41/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A41,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3300, 1200),
        "size": (500, 500),
        "path": "frames_A42/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": A42,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (3300, 1750),
        "size": (500, 500),
        "path": "frames_A43/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": A43,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (4400, 100),
        "size": (500, 500),
        "path": "frames_A44/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A44,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (4400, 650),
        "size": (500, 500),
        "path": "frames_A45/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GP',
        "object": A45,
        "replace_frames": False,
        "subtitle": 'S11 + S22',
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (4400, 1200),
        "size": (500, 500),
        "path": "frames_A46/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": A46,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (4400, 1750),
        "size": (500, 500),
        "path": "frames_A47/",
        "subtitle": "",
        "create_frames": True,
        "type": 'GA',
        "object": A47,
        "replace_frames": False,
        # "subtitle_size": 1,
        # "subtitle_offset": 20,
    },
    {
        "position": (7150, 100),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A50/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'T1A',
        "object": A50,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (7150, 650),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A51/",
        "subtitle": "Edge index",
        "create_frames": True,
        "type": 'V',
        "object": A51,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (7150, 1200),
        # "size": (500, 400),
        "size": (500, 500), 
        "path": "frames_A52/",
        "subtitle": "der(Edge index)",
        "create_frames": True,
        "type": 'V',
        "object": A52,
        "replace_frames": False,
        # "subtitle_size": 40,
        # "subtitle_offset": 20,
    },
    {
        "position": (1050, 1200),
        "size": (500, 500),
        "path": "frames_A60/",
        "subtitle": "ALLIE & ALLKE",
        "create_frames": True,
        "type": 'V',
        "object": A60,
        "replace_frames": False,
    },
    {
        "position": (1050, 1750),
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
SCONF.vid_folder = 'Video_2010'
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = "mp4v"
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_test.mp4'





