import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from A001_functions.Video_functions import _eigenmode_plot_limits, _mode_signs


def test_mode_signs_preserve_orientation_after_raw_sign_flip():
    direction = np.array([1.0, -2.0, 0.5])
    raw_signs = [1.0, -1.0, -1.0, 1.0]
    eigenvectors = [(raw_sign * direction)[:, None] for raw_sign in raw_signs]

    signs = _mode_signs(eigenvectors, mode_index=0)
    plotted = [matrix[:, 0] * sign for matrix, sign in zip(eigenvectors, signs)]

    assert np.array_equal(signs, [1.0, -1.0, -1.0, 1.0])
    assert all(np.dot(plotted[0], vector) > 0.0 for vector in plotted[1:])


def test_eigenmode_plot_limits_cover_all_frames_with_constant_padding():
    data_C = {
        'COOR1': {'1': [0.0, -2.0], '2': [10.0, 12.5]},
        'COOR2': {'1': [1.0, 0.5], '2': [8.0, 7.0]},
    }
    settings = type('Settings', (), {
        'xlim': None,
        'ylim': None,
        'axis_padding': 1.5,
    })()

    xlim, ylim = _eigenmode_plot_limits(data_C, np.array([1, 2]), settings)

    assert xlim == (-3.5, 14.0)
    assert ylim == (-1.0, 9.5)
