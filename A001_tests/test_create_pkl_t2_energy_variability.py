import os
import sys

import numpy as np
import pytest


sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from A001_functions.Reduce_resultsV5 import create_PKL_T2


def test_create_pkl_t2_energy_density_variability_metrics():
    data_t1 = {
        "t": [0.0, 1.0],
        "nodes": [
            {
                1: (0.0, 0.0, 1),
                2: (1.0, 0.0, 1),
                3: (0.0, 1.0, 1),
                4: (10.0, 0.0, 1),
                5: (12.0, 0.0, 1),
                6: (10.0, 1.0, 1),
            },
            {
                1: (0.0, 0.0, 1),
                2: (2.0, 0.0, 1),
                3: (0.0, 1.0, 1),
                4: (10.0, 0.0, 1),
                5: (12.0, 0.0, 1),
                6: (10.0, 1.0, 1),
            },
        ],
        "elements": {
            1: [0, 1, 2],
            2: [3, 4, 5],
        },
        "elements_area": {
            1: {0: 0.5, 1: 1.0},
            2: {0: 1.0, 1: 1.0},
        },
        "elements_area_normalized": {
            1: {0: 1.0, 1: 2.0},
            2: {0: 1.0, 1: 1.0},
        },
    }

    t2 = create_PKL_T2(data_t1)
    params = (1, 1, 1, 1)

    vals = np.array([
        t2["w"][params][1][1],
        t2["w"][params][2][1],
    ])
    areas0 = np.array([0.5, 1.0])
    expected_mean = float(np.mean(vals))
    expected_std = float(np.std(vals))
    expected_cv = expected_std / (abs(expected_mean) + 1e-30)
    expected_weighted_mean = float(np.sum(areas0 * vals) / np.sum(areas0))
    expected_weighted_std = float(np.sqrt(
        np.sum(areas0 * (vals - expected_weighted_mean) ** 2) / np.sum(areas0)
    ))
    expected_weighted_cv = (
        expected_weighted_std / (abs(expected_weighted_mean) + 1e-30)
    )

    assert t2["w_mean"][params][1] == pytest.approx(expected_mean)
    assert t2["w_std"][params][1] == pytest.approx(expected_std)
    assert t2["w_cv"][params][1] == pytest.approx(expected_cv)
    assert t2["w_std_area_weighted"][params][1] == pytest.approx(expected_weighted_std)
    assert t2["w_cv_area_weighted"][params][1] == pytest.approx(expected_weighted_cv)
    assert t2["w_std"][params][0] == 0.0
    assert t2["w_cv"][params][0] == 0.0
