import numpy as np

from A001_functions.stiffness_eigen import (
    _schedule_from_replay_inp,
    _write_eig_spectrum_lite,
    build_replay_inp,
)
from Z001_Results_Analizer.analyze_refined_5150 import tracked_branches


def test_late_refinement_preserves_loading_path(tmp_path):
    source = tmp_path / 'input.inp'
    source.write_text('''** STEP: Step-0
*Step, name=Step-0
*Static
0.1, 1., 1e-8, 0.1
*End Step
** STEP: Step-1
*Step, name=Step-1
*Dynamic, application=QUASI-STATIC
0.01, 1., 1e-8, 0.1
*Boundary
NODE, 2, 2, -5
*End Step
''')
    replay = tmp_path / 'replay.inp'
    times = build_replay_inp(source, replay, n_segments=4,
                             late_start=0.5, late_refine=4)
    np.testing.assert_allclose(times,
                               [0, 0.25, 0.5, 0.5625, 0.625, 0.6875,
                                0.75, 0.8125, 0.875, 0.9375, 1.0])
    content = replay.read_text()
    assert content.count('name=EIGSEG-') == 10
    assert 'NODE, 2, 2, -5.0' in content
    np.testing.assert_allclose(_schedule_from_replay_inp(replay), times)


def test_spectrum_tracks_same_mode_across_eigenvalue_reordering(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    basis = np.eye(3, dtype=np.float32)
    results = [
        {'time': 0.0, 'matrix_index': 2, 'eigenvalues': [0.1, 0.2],
         'eigenvectors': basis[:, :2]},
        {'time': 0.5, 'matrix_index': 4, 'eigenvalues': [-0.1, 0.15],
         'eigenvectors': basis[:, [1, 0]]},
        {'time': 1.0, 'matrix_index': 6, 'eigenvalues': [-0.2, 0.1],
         'eigenvectors': basis[:, [1, 0]]},
    ]
    path = _write_eig_spectrum_lite(5150, results)
    with np.load(path, allow_pickle=False) as spectrum:
        np.testing.assert_array_equal(spectrum['tracked_index'], [0, 1, 1])
        np.testing.assert_allclose(spectrum['tracked_eigenvalue'], [0.1, 0.15, 0.1])
        np.testing.assert_allclose(spectrum['tracked_overlap'], [1, 1, 1])
        branches, confidence = tracked_branches(
            spectrum['eigenvalues'], spectrum['mode_overlap'])
        np.testing.assert_allclose(branches[:, 0], [0.1, 0.15, 0.1])
        np.testing.assert_allclose(confidence[:, 0], [1, 1, 1])
