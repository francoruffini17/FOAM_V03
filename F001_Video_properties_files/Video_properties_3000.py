import sys
import os
import copy
import importlib.util

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from A001_functions.Video_functions import *  # noqa: F401,F403


_BASE_PATH = os.path.join(os.path.dirname(__file__), 'Video_properties_1010.py')
_SPEC = importlib.util.spec_from_file_location('Video_properties_1010_base', _BASE_PATH)
_BASE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_BASE)


# Reuse the 1010 layout and append one extra panel for pressure-histogram evolution.
T = copy.deepcopy(_BASE.T)
SCONF = copy.deepcopy(_BASE.SCONF)


def _make_hist(title, xlabel, save_path, file_key, quantity):
    obj = frame_pressure_histogram()
    obj.title = title
    obj.xlabel = xlabel
    obj.ylabel = 'Probability density'
    obj.figsize = (4.75, 3.75)
    obj.dpi = 100
    obj.num_frames = T.num_frames
    obj.bins = 60
    obj.density = True
    obj.grid = True
    obj.show_mean = True
    obj.mark_localization = True
    obj.save_path = save_path
    obj.file_key = file_key
    obj.quantity = quantity
    return obj


PH3000 = _make_hist(
    'Pressure histogram evolution',
    'Element pressure p = -(S11+S22)/2 (MPa)',
    'frames_PH3000/',
    'B',
    'pressure',
)
HS3000 = _make_hist(
    'Shear histogram evolution',
    'Element shear',
    'frames_HS3000/',
    'TP2',
    'shear',
)
HJ3000 = _make_hist(
    'J histogram evolution',
    'Element J',
    'frames_HJ3000/',
    'TP2',
    'J',
)
HA3000 = _make_hist(
    'Normalized area histogram evolution',
    'Normalized element area A/A0',
    'frames_HA3000/',
    'TP2',
    'normalized_areas',
)
HD3000 = _make_hist(
    'Distortion histogram evolution',
    'Distortion = shear - |J|',
    'frames_HD3000/',
    'TP2',
    'distortion',
)


T.canvas_size = (2950, 2050)
T.vid_folder = 'Video_3000'
T.elements = list(T.elements)
T.elements.append(
    {
        "position": (2400, 100),
        "size": (500, 500),
        "path": "frames_PH3000/",
        "subtitle": "Element pressure histogram evolution",
        "create_frames": True,
        "type": 'PH',
        "object": PH3000,
        "replace_frames": False,
    }
)
T.elements.extend([
    {
        "position": (50, 1650),
        "size": (500, 350),
        "path": "frames_PH3000/",
        "subtitle": "Pressure",
        "create_frames": True,
        "type": 'PH',
        "object": PH3000,
        "replace_frames": False,
    },
    {
        "position": (640, 1650),
        "size": (500, 350),
        "path": "frames_HS3000/",
        "subtitle": "Shear",
        "create_frames": True,
        "type": 'PH',
        "object": HS3000,
        "replace_frames": False,
    },
    {
        "position": (1230, 1650),
        "size": (500, 350),
        "path": "frames_HJ3000/",
        "subtitle": "J",
        "create_frames": True,
        "type": 'PH',
        "object": HJ3000,
        "replace_frames": False,
    },
    {
        "position": (1820, 1650),
        "size": (500, 350),
        "path": "frames_HA3000/",
        "subtitle": "Normalized area",
        "create_frames": True,
        "type": 'PH',
        "object": HA3000,
        "replace_frames": False,
    },
    {
        "position": (2410, 1650),
        "size": (500, 350),
        "path": "frames_HD3000/",
        "subtitle": "Distortion",
        "create_frames": True,
        "type": 'PH',
        "object": HD3000,
        "replace_frames": False,
    },
])


SCONF.vid_folder = 'Video_3000'
SCONF.delete_concat_frames_after_video = False
SCONF.frames_format = 'png'
SCONF.frame_rate = 30
SCONF.codec = "mp4v"
SCONF.frames_pattern = 'frames_final/frame_*.png'
SCONF.video_output_name = 'video_3000.mp4'
