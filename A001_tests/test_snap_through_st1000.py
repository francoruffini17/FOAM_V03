"""Geometry-level checks for the ST1000 chevron-pair foam."""

import os
import sys

import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from B001_Mesh_creator.Mesh_creator_snap_through_ST1000 import (
    SnapThroughConfig,
    SnapThroughMeshGenerator,
)


def test_st1000_geometry_has_target_porosity_and_no_overlaps():
    cfg = SnapThroughConfig()
    gen = SnapThroughMeshGenerator(cfg)

    assert len(gen.hole_centers) == cfg.n_columns * cfg.n_rows == 64
    area_fraction = np.sum(np.pi * gen.hole_radii ** 2) / cfg.domain_size ** 2
    assert np.isclose(area_fraction, cfg.porosity)
    assert gen.get_minimum_ligament() > 0.0


def test_st1000_row_pairs_form_alternating_chevrons():
    cfg = SnapThroughConfig()
    gen = SnapThroughMeshGenerator(cfg)
    centers = gen.hole_centers.reshape(cfg.n_rows, cfg.n_columns, 2)

    pair_dx = centers[1::2, 0, 0] - centers[0::2, 0, 0]
    assert np.allclose(np.abs(pair_dx), 2 * cfg.chevron_shift)
    assert np.all(pair_dx[:-1] * pair_dx[1:] < 0.0)

    paired_dy = centers[1::2, 0, 1] - centers[0::2, 0, 1]
    interpair_dy = centers[2::2, 0, 1] - centers[1:-1:2, 0, 1]
    assert np.max(paired_dy) < np.min(interpair_dy)
