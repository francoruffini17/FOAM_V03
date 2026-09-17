"""Supervise isolated reductions without Pool's lost-task hang after SIGKILL.

Linux/POSIX: each simulation owns a process group, including graph workers.
Ranges run sequentially; simctl controls parallelism between simulations.
"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from .reduction_io import checkpoint_valid, code_version

# Tuple positions in the legacy and V20 interfaces, in dependency order.
STAGES = dict(zip(
    ('A A2 B C C2 D T1 T2 J1 J2 J3 H1 H2 H3 I1 I2 I3 K1 K2 K3 Q1 Q2 TP1 TP2 DEFC1 DEFC2 E').split(),
    (1, 2, 3, 4, 5, 6, 7, 8, 11, 12, 13, 17, 18, 19, 23, 24, 25, 29, 30, 31, 35, 36, 39, 40, 41, 42, 43)))


def memory_report(pid):
    try:
        import psutil
        root = psutil.Process(pid)
        processes = [root] + root.children(recursive=True)
        rss = sum(p.memory_info().rss for p in processes if p.is_running()) / 2**30
        available = psutil.virtual_memory().available / 2**30
        return f'process-tree RSS={rss:.1f} GiB, available={available:.1f} GiB'
    except Exception:
        return 'memory unavailable'


def run_stages(args, timeout=0, resume=True):
    """One fresh process per stage; serialize reducers sharing this results folder."""
    import fcntl
    root = Path('I001_Results/.reduction')
    root.mkdir(parents=True, exist_ok=True)
    print(f'SIM_{args[0]:03d}: waiting for reduction memory slot', flush=True)
    with (root / 'memory.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        started = time.monotonic()
        version = code_version()
        outputs = set()
        for stage, index in STAGES.items():
            if str(args[index]).lower() != 'y':
                continue
            stage_args = list(args[:47]) + ['n']
            stage_args.extend(args[48:])
            for flag_index in STAGES.values():
                stage_args[flag_index] = 'n'
            stage_args[index] = 'y'
            stage_args[44] = 'n'  # Only delete CSV after all stages succeed.
            stage_args[45] = args[45] or 1
            checkpoint = root / f'{args[0]:03d}_{stage}.json'
            if resume and checkpoint_valid(checkpoint, stage_args, version):
                print(f'SIM_{args[0]:03d} {stage}: checkpoint valid; skipped', flush=True)
                outputs.update(json.loads(checkpoint.read_text())['outputs'])
                continue
            remaining = max(0, timeout - (time.monotonic() - started)) if timeout else 0
            if timeout and not remaining:
                return 124
            print(f'SIM_{args[0]:03d} {stage}: starting', flush=True)
            stage_start = time.monotonic()
            command = [sys.executable, '-u', '-m', 'A001_functions.reduction_runner',
                       json.dumps(stage_args), str(checkpoint), version]
            status = run_command(command, timeout=remaining)
            # One bounded resource retry; ordinary exceptions are not retried.
            if status == -signal.SIGKILL and (stage_args[45] > 1 or stage == 'TP2'):
                stage_args[45] = 1
                if len(stage_args) <= 48:
                    stage_args.extend([64, 'n'])
                stage_args[48] = max(1, int(stage_args[48]) // 2)
                remaining = max(0, timeout - (time.monotonic() - started)) if timeout else 0
                if timeout and not remaining:
                    return 124
                print(f'SIM_{args[0]:03d} {stage}: one SIGKILL retry with one graph worker '
                      f'and TP2 batch size {stage_args[48]}', flush=True)
                command[4] = json.dumps(stage_args)
                status = run_command(command, timeout=remaining)
            if status:
                print(f'SIM_{args[0]:03d} {stage}: failed ({status}); checkpoint not committed', flush=True)
                return status
            outputs.update(json.loads(checkpoint.read_text())['outputs'])
            print(f'SIM_{args[0]:03d} {stage}: completed in {time.monotonic()-stage_start:.1f}s', flush=True)
        # Forward only once all consumers have finished. Missing forwarded files
        # invalidate checkpoints on the next run, rather than skipping absent inputs.
        if len(args) > 47 and str(args[47]).lower() == 'y':
            from .pkl_forward import PickleForwarder
            forwarder = PickleForwarder(set(), args[0], {})
            for path in sorted(outputs):
                forwarder._move(Path(path))
        if str(args[44]).lower() == 'y':
            Path(f'I001_Results/RES_SIM_{args[0]:03d}.csv').unlink(missing_ok=True)
    return 0


def run_command(command, timeout=0, heartbeat=60):
    """Return the child's status; always clean up its entire process group.

    A negative status identifies a signal (e.g. -9 after an OOM kill).
    Timeout returns 124. Output is inherited, so tracebacks reach simctl logs.
    """
    process = subprocess.Popen(command, start_new_session=True)
    start = time.monotonic()
    next_report = start + heartbeat
    try:
        while True:
            try:
                return process.wait(timeout=0.2)
            except subprocess.TimeoutExpired:
                now = time.monotonic()
                if timeout and now - start >= timeout:
                    print(f"Reduction timed out after {timeout:g} seconds", flush=True)
                    return 124
                if heartbeat and now >= next_report:
                    print(f"Reduction worker PID {process.pid} alive; "
                          f"elapsed {now - start:.0f}s; {memory_report(process.pid)} "
                          "(not a progress guarantee)", flush=True)
                    next_report = now + heartbeat
    finally:
        # The worker can die while its own children are still running.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        else:
            time.sleep(0.2)
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        process.wait()


def _interrupted(signum, frame):
    raise SystemExit(128 + signum)


def run_reductions(args_list, timeout=0, resume=True):
    """Continue after failed simulations, returning 1 if any failed."""
    previous = {sig: signal.signal(sig, _interrupted)
                for sig in (signal.SIGTERM, signal.SIGINT)}
    failures = []
    try:
        for args in args_list:
            sim = args[0]
            print(f"SIM_{sim:03d}: reduction starting", flush=True)
            status = run_stages(args, timeout=timeout, resume=resume) if len(args) >= 47 else run_command(
                [sys.executable, '-u', '-m', 'A001_functions.reduction_runner',
                 json.dumps(args)], timeout=timeout)
            if status:
                failures.append(sim)
                reason = f"signal {-status}" if status < 0 else f"exit {status}"
                print(f"SIM_{sim:03d}: reduction FAILED ({reason}); "
                      "retaining CSV; check incomplete outputs before retrying. "
                      "Continuing to next simulation.", flush=True)
            else:
                print(f"SIM_{sim:03d}: reduction completed", flush=True)
    finally:
        for sig, handler in previous.items():
            signal.signal(sig, handler)
    if failures:
        print(f"Failed reductions: {failures}", flush=True)
    return int(bool(failures))


if __name__ == '__main__':
    # Keep heavy scientific imports out of the supervising parent.
    from .Reduce_resultsV5 import process_simulation
    from . import reduction_io
    # Instrument local data readers as well as writers, including mesh helpers.
    for name, module in list(sys.modules.items()):
        if name.startswith('A001_functions.') and module is not reduction_io:
            module.open = reduction_io.tracked_open
    args = tuple(json.loads(sys.argv[1]))
    if len(args) > 48:
        os.environ['REDUCE_TP2_BATCH_SIZE'] = str(args[48])
        os.environ['REDUCE_TP2_SUMMARY_ONLY'] = str(args[49])
    process_simulation(args)
    import resource
    print(f'Stage worker peak RSS: {resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 2**20:.2f} GiB', flush=True)
    if len(sys.argv) > 2:
        reduction_io.save_checkpoint(sys.argv[2], args, sys.argv[3])
