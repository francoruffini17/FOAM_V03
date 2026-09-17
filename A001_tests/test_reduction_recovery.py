import json
import pickle
from collections.abc import Mapping
from pathlib import Path

import numpy as np
import pytest

from A001_functions import reduction_io as rio
from A001_functions import reduction_runner as runner


def test_atomic_failed_write_preserves_previous_result(tmp_path):
    target = tmp_path / 'result.pkl'
    target.write_bytes(b'previous')
    with pytest.raises(RuntimeError):
        with rio.atomic_open(target) as stream:
            stream.write(b'incomplete')
            raise RuntimeError('injected failure')
    assert target.read_bytes() == b'previous'
    assert not list(tmp_path.glob('*.tmp'))


def test_stage_resume_and_input_invalidation(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    source = tmp_path / 'input.json'
    source.write_text('one')
    calls = []
    flags = [1] + ['n'] * 43 + ['n', 1, None, 'n']
    flags[1] = flags[2] = 'y'

    def fake_worker(command, timeout=0):
        args = json.loads(command[4])
        stage = next(k for k, v in runner.STAGES.items() if args[v] == 'y')
        calls.append(stage)
        assert sum(args[v] == 'y' for v in runner.STAGES.values()) == 1
        rio.READS.clear()
        rio.WRITES.clear()
        dependency = source if stage == 'A' else tmp_path / 'A.pkl'
        with rio.tracked_open(dependency):
            pass
        with rio.tracked_open(tmp_path / (stage + '.pkl'), 'wb') as stream:
            pickle.dump({'valid': True}, stream)
        rio.save_checkpoint(command[5], args, command[6])
        return 0

    monkeypatch.setattr(runner, 'run_command', fake_worker)
    assert runner.run_stages(flags) == 0
    assert calls == ['A', 'A2']
    assert runner.run_stages(flags) == 0
    assert calls == ['A', 'A2']
    source.write_text('changed input')
    assert runner.run_stages(flags) == 0
    assert calls == ['A', 'A2', 'A', 'A2']


def test_failed_stage_retains_csv_and_retries_only_once(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    results = tmp_path / 'I001_Results'
    results.mkdir()
    csv = results / 'RES_SIM_001.csv'
    csv.write_text('retain source')
    flags = [1] + ['n'] * 43 + ['y', 4, None, 'n', 64, 'n']
    flags[40] = 'y'
    calls = []

    def killed(command, timeout=0):
        calls.append(json.loads(command[4]))
        return -9

    monkeypatch.setattr(runner, 'run_command', killed)
    assert runner.run_stages(flags) == -9
    assert len(calls) == 2
    assert calls[-1][45] == 1
    assert calls[-1][48] == 32
    assert csv.exists()
    assert not (results / '.reduction/001_TP2.json').exists()


def assert_same(actual, expected):
    if isinstance(expected, Mapping):
        assert set(actual) == set(expected)
        for key in expected:
            assert_same(actual[key], expected[key])
    elif isinstance(expected, (list, tuple)):
        assert len(actual) == len(expected)
        for a, b in zip(actual, expected):
            assert_same(a, b)
    elif isinstance(expected, (int, float, np.number)):
        assert actual == pytest.approx(expected, abs=1e-12, rel=1e-10)
    else:
        assert actual == expected


@pytest.mark.parametrize('batch_size', [1, 2, 64])
def test_tp2_batched_matches_original_and_pickle_schema(tmp_path, monkeypatch, batch_size):
    from A001_functions.Reduce_resultsV5 import create_PKL_TP2
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv('REDUCE_TP2_BATCH_SIZE', str(batch_size))
    nodes = {1: (0., 0.), 2: (1., 0.), 3: (0., 1.),
             4: (2., 0.), 5: (4., 0.), 6: (4., 1.), 7: (2., 1.)}
    data = dict(t=[0., 1., 2.],
                nodes=[nodes, {k: (x*(1.2 if k < 4 else 1.1), y*(.9 if k < 4 else .7))
                               for k, (x,y) in nodes.items()},
                       {k: (x + .1*y, y*(1.1 if k < 4 else .9)) for k, (x,y) in nodes.items()}],
                elements={1: [0, 1, 2], 2: [3, 4, 5, 6]},
                element_types={1: 3, 2: 4},
                elements_area={1: {0: .5, 1: .54, 2: .55}, 2: {0: 2., 1: 1.54, 2: 1.8}},
                elements_area_normalized={1: {0: 1., 1: 1.08, 2: 1.1},
                                          2: {0: 1., 1: .77, 2: .9}})
    expected = create_PKL_TP2(data, _batch_internal=True, step1_start_ti=1)
    path = tmp_path / 'DATA_PICK_001_TP2.pkl'
    actual = create_PKL_TP2(data, output_path=path, step1_start_ti=1)
    assert_same(actual, expected)
    with path.open('rb') as stream:
        loaded = pickle.load(stream)
    assert isinstance(loaded['F'], dict)
    assert_same(loaded, expected)
    with path.with_name('DATA_PICK_001_TP2_L.pkl').open('rb') as stream:
        light = pickle.load(stream)
    monkeypatch.setenv('REDUCE_TP2_SUMMARY_ONLY', 'y')
    summary_path = tmp_path / 'summary_TP2.pkl'
    summary = create_PKL_TP2(data, output_path=summary_path, step1_start_ti=1)
    assert_same(summary, light)
    assert not summary_path.exists()
    assert summary_path.with_name('summary_TP2_L.pkl').exists()
