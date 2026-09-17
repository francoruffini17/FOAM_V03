"""Atomic reducer outputs and inexpensive, conservative checkpoint provenance."""
import builtins
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import tempfile

READS = {}
WRITES = {}


def fingerprint(path):
    stat = Path(path).stat()
    return [stat.st_size, stat.st_mtime_ns, stat.st_ctime_ns, stat.st_ino]


def code_version():
    digest = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob('*.py')):
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


@contextmanager
def atomic_open(path, mode='wb', **kwargs):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temporary = tempfile.mkstemp(prefix='.' + path.name + '.', suffix='.tmp', dir=path.parent)
    try:
        with os.fdopen(fd, mode, **kwargs) as stream:
            yield stream
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


@contextmanager
def tracked_open(file, mode='r', *args, **kwargs):
    """Used by reducer modules; preserve ordinary reads, atomically publish PKLs."""
    path = str(Path(file).resolve())
    if mode == 'wb' and path.endswith('.pkl'):
        with atomic_open(path, mode, **kwargs) as stream:
            yield stream
        WRITES[path] = fingerprint(path)
    else:
        if 'r' in mode:
            READS.setdefault(path, fingerprint(path))
        with builtins.open(file, mode, *args, **kwargs) as stream:
            yield stream


def checkpoint_valid(path, args, version):
    try:
        record = json.loads(Path(path).read_text())
        return (record['args'] == list(args) and record['code'] == version
                and bool(record['outputs'])
                and all(fingerprint(p) == value
                        for group in ('inputs', 'outputs')
                        for p, value in record[group].items()))
    except (OSError, ValueError, KeyError, TypeError):
        return False


def save_checkpoint(path, args, version):
    if not WRITES:
        raise RuntimeError('Stage produced no outputs; refusing to mark it complete')
    if any(fingerprint(p) != value for p, value in READS.items() if p not in WRITES):
        raise RuntimeError('An input changed while the stage was running')
    with atomic_open(path, 'w') as stream:
        json.dump({'args': list(args), 'code': version,
                   'inputs': {p: v for p, v in READS.items() if p not in WRITES},
                   'outputs': WRITES}, stream, indent=2)
