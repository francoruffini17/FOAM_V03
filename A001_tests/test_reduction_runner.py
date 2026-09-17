"""Failure injection for the reducer's process supervision."""
import ast
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest

from A001_functions import reduction_runner as runner


def command(code):
    return [sys.executable, '-u', '-c', code]


def test_sigkill_does_not_hang():
    start = time.monotonic()
    status = runner.run_command(command(
        'import os, signal; os.kill(os.getpid(), signal.SIGKILL)'), timeout=5)
    assert status == -signal.SIGKILL
    assert time.monotonic() - start < 5


def test_failed_simulation_does_not_prevent_next(monkeypatch, tmp_path):
    original = runner.run_command
    marker = tmp_path / 'next_completed'

    def injected(cmd, timeout=0):
        import json
        sim = json.loads(cmd[-1])[0]
        code = ('import os, signal; os.kill(os.getpid(), signal.SIGKILL)'
                if sim == 1 else
                f'from pathlib import Path; Path({str(marker)!r}).touch()')
        return original(command(code), timeout=5)

    monkeypatch.setattr(runner, 'run_command', injected)
    assert runner.run_reductions([(1,), (2,)]) == 1
    assert marker.exists()


@pytest.mark.parametrize('kill_parent', [False, True])
def test_timeout_or_dead_worker_cleans_descendants(tmp_path, kill_parent):
    marker = tmp_path / 'child_pid'
    code = (
        'import subprocess, sys, os, signal, time\n'
        'from pathlib import Path\n'
        'child = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(60)"])\n'
        f'Path({str(marker)!r}).write_text(str(child.pid))\n'
        + ('os.kill(os.getpid(), signal.SIGKILL)\n' if kill_parent else 'time.sleep(60)\n')
    )
    status = runner.run_command(command(code), timeout=1)
    assert status == (-signal.SIGKILL if kill_parent else 124)
    child_pid = int(marker.read_text())
    for _ in range(30):
        stat = Path(f'/proc/{child_pid}/stat')
        if not stat.exists() or stat.read_text().split(') ')[1].startswith('Z'):
            break
        time.sleep(0.1)
    else:
        os.kill(child_pid, signal.SIGKILL)
        pytest.fail('Descendant survived supervisor cleanup')


def reducer_functions():
    # Exercise the real orchestration without importing scientific packages.
    source = Path('A001_functions/Reduce_resultsV5.py').read_text()
    tree = ast.parse(source)
    functions = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                 and n.name in ('process_simulation', '_load_pickle_or_skip')]
    namespace = {}
    exec(compile(ast.Module(body=functions, type_ignores=[]), '<reducer>', 'exec'), namespace)
    return namespace


def test_missing_dependency_is_fatal():
    namespace = reducer_functions()
    with pytest.raises(RuntimeError, match='Cannot reduce'):
        namespace['_load_pickle_or_skip']('/no/such/dependency.pkl', 'I3')


def test_stage_failure_stops_before_later_stages_and_csv_deletion(tmp_path, monkeypatch):
    namespace = reducer_functions()
    monkeypatch.chdir(tmp_path)
    results = tmp_path / 'I001_Results'
    results.mkdir()
    csv = results / 'RES_SIM_001.csv'
    csv.write_text('keep me')
    flags = ['n'] * 48
    flags[0] = 1
    flags[41] = flags[42] = flags[44] = 'y'  # DEFC1, DEFC2, delete-csv
    namespace['os'] = os

    class Forwarder:
        @classmethod
        def disabled(cls):
            return cls()

        def complete(self, *args):
            pass

    def fail(**kwargs):
        raise ValueError('injected DEFC1 failure')

    namespace['PickleForwarder'] = Forwarder
    namespace['create_PKL_DEFC1'] = fail
    namespace['create_PKL_DEFC2'] = lambda *a, **k: pytest.fail('Ran later stage')
    with pytest.raises(ValueError, match='injected DEFC1'):
        namespace['process_simulation'](flags)
    assert csv.read_text() == 'keep me'


def test_cli_reports_failure_but_completes_following_simulation(tmp_path):
    import json
    root = Path(__file__).resolve().parents[1]
    results = tmp_path / 'I001_Results'
    results.mkdir()
    (results / 'DATA_PICK_002_EIG.json').write_text(json.dumps([
        {'time': 0, 'matrix_index': 2, 'eigenvalues': [1.0, 2.0]}]))
    flags = []
    for flag in ['A', 'A2', 'B', 'C', 'C2', 'D',
                 'J1', 'J2', 'J3', 'H1', 'H2', 'H3',
                 'I1', 'I2', 'I3', 'K1', 'K2', 'K3']:
        flags.extend(['--' + flag, 'n'])
    result = subprocess.run(
        [sys.executable, '-m', 'A001_functions.Reduce_resultsV20', '1', '2',
         *flags, '--E', 'y'], cwd=tmp_path,
        env={**os.environ, 'PYTHONPATH': str(root),
             'MPLCONFIGDIR': str(tmp_path / 'mpl')},
        capture_output=True, text=True, timeout=60)
    assert result.returncode == 1, result.stdout + result.stderr
    assert 'SIM_001: reduction FAILED' in result.stdout
    assert 'SIM_002: reduction completed' in result.stdout
    assert (results / 'DATA_PICK_002_E.pkl').exists()
