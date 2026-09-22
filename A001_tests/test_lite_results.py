import csv
import gzip

import numpy as np

from A001_functions.Reduce_results_lite import FORMAT, _shear_mean, read_lite_csv
from A001_functions.Video_functions import _load_lite_result_for_legacy_path
from A001_functions.stiffness_eigen import _write_eig_lite


def test_read_lite_csv(tmp_path):
    path = tmp_path / 'RES_SIM_001_LITE.csv.gz'
    with gzip.open(path, 'wt', newline='') as stream:
        writer = csv.writer(stream)
        writer.writerow([FORMAT])
        writer.writerow(['NODE', 1, 'COOR1', 0.0, 0.1])
        writer.writerow(['NODE', 1, 'COOR2', 0.0, 0.0])
        writer.writerow(['NODE', 2, 'COOR1', 1.0, 1.1])
        writer.writerow(['NODE', 2, 'COOR2', 0.0, 0.0])
        writer.writerow(['REF', 9, 'U2', 0.0, -0.5])
        writer.writerow(['REF', 9, 'RF2', 0.0, 2.0])
        for field in ('S11', 'S22', 'S12'):
            writer.writerow(['ELEM', 1, 0, field, 0.0, 1.0])
        writer.writerow(['TIME', 0.0, 1.0])
        writer.writerow(['END', 9])

    times, nodes, coordinates, u2, rf2, stresses = read_lite_csv(path)
    np.testing.assert_allclose(times, [0.0, 1.0])
    np.testing.assert_array_equal(nodes, [1, 2])
    assert coordinates.shape == (2, 2, 2)
    np.testing.assert_allclose(u2, [0.0, -0.5])
    np.testing.assert_allclose(rf2, [0.0, 2.0])
    assert stresses['S11']['1'][0] == [0.0, 1.0]


def test_shear_mean_matches_tp2_definition_for_tri_and_quad():
    reference = np.asarray([
        [0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 1.0],
    ])
    deformed = reference.copy()
    deformed[:, 1] *= 0.5
    coordinates = np.stack((reference, deformed))

    triangle = _shear_mean(coordinates, [[0, 1, 3]])
    quadrilateral = _shear_mean(coordinates, [[0, 1, 2, 3]])
    np.testing.assert_allclose(triangle, [1.0, 0.625])
    np.testing.assert_allclose(quadrilateral, [1.0, 0.625])


def test_video_loader_adapts_lite_curves(tmp_path, monkeypatch):
    result_dir = tmp_path / 'I001_Results' / 'LITE' / 'SIM_007'
    result_dir.mkdir(parents=True)
    np.savez_compressed(
        result_dir / 'curves.npz',
        t=np.asarray([0.0, 1.0]),
        u2=np.asarray([0.0, -2.0]),
        rf2=np.asarray([0.0, 3.0]),
        shear_mean=np.asarray([1.0, 0.7]),
        global_ef_t=np.asarray([0.0, 0.2]),
        global_ef_c=np.asarray([0.0, 0.4]),
        global_ef_t_allnodes=np.asarray([0.0, 0.1]),
        global_ef_c_allnodes=np.asarray([0.0, 0.3]),
        n_nodes_total=np.asarray(12),
    )
    monkeypatch.chdir(tmp_path)
    a2 = _load_lite_result_for_legacy_path('I001_Results/DATA_PICK_007_A2.pkl')
    tp2 = _load_lite_result_for_legacy_path('I001_Results/DATA_PICK_007_TP2_L.pkl')
    i3 = _load_lite_result_for_legacy_path(
        'I001_Results/DATA_PICK_007_I3_BFS_3002.pkl')
    np.testing.assert_allclose(a2['RF2']['PERN-9999997'], [0.0, 3.0])
    np.testing.assert_allclose(tp2['shear_mean'], [1.0, 0.7])
    assert i3['n_nodes_total'] == 12


def test_lite_eigen_writer_and_video_adapter(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results = [
        {'time': 0.0, 'matrix_index': 2, 'eigenvalues': [0.5],
         'eigenvectors': np.asarray([[1.0], [0.0]])},
        {'time': 1.0, 'matrix_index': 4, 'eigenvalues': [-0.1],
         'eigenvectors': np.asarray([[0.8], [0.2]])},
    ]
    _write_eig_lite(7, results, [(1, 1), (1, 2)])
    loaded = _load_lite_result_for_legacy_path(
        'I001_Results/DATA_PICK_007_EIGV.pkl')
    assert np.asarray(loaded['eigenvalues']).shape == (2, 1)
    assert np.asarray(loaded['eigenvectors'][0]).shape == (2, 1)
    np.testing.assert_allclose(loaded['eigenvalues'][:, 0], [0.5, -0.1])
