"""python -m A001_functions.Video_executorV20 --sim-num N --properties-file NAME [flags]

Flag-based video creator for FOAM_V03. Replaces the interactive Video_executor.py.
"""

import argparse
import sys

from .Video_functions import (
    create_frames_for_sim,
    concatenate_multiple_images_for_sim,
    create_vid_from_frames_for_sim,
)


def main():
    p = argparse.ArgumentParser(
        description='Create video frames and video from simulation results (FOAM_V03).',
        allow_abbrev=False)
    p.add_argument('--sim-num', '-s', type=int, required=True,
                   help='Simulation number.')
    p.add_argument('--properties-file', '-p', required=True,
                   metavar='NAME',
                   help='Video properties file name (without .py extension, e.g. Video_properties0001).')
    p.add_argument('--parallel', '-j', type=int, default=None, metavar='N',
                   help='Override max parallel frame renders from properties file.')

    args = p.parse_args()

    sim_num = args.sim_num
    properties_name = args.properties_file

    import importlib.util, os
    props_path = os.path.join('F001_Video_properties_files', properties_name + '.py')
    spec = importlib.util.spec_from_file_location('video_props', props_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    T = module.T
    SCONF = module.SCONF

    max_parallel = args.parallel if args.parallel is not None else getattr(T, 'max_parallel', None)

    create_frames_for_sim(sim_num, T, max_parallel=max_parallel,
                          frames_format=getattr(T, 'frames_format', 'png'))
    concatenate_multiple_images_for_sim(sim_num, T)
    create_vid_from_frames_for_sim(sim_num, SCONF)


if __name__ == '__main__':
    main()
