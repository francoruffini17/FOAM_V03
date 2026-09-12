"""Dependency-aware forwarding of completed reducer pickle files."""

from pathlib import Path
import errno
import os
import shutil


class PickleForwarder:
    """Move a simulation's PKLs after their enabled consumers are finished."""

    def __init__(self, enabled, sim_num, dependencies, results_dir="I001_Results"):
        self.enabled = {name for name in enabled}
        self.completed = set()
        self.dependencies = {
            name: set(consumers) for name, consumers in dependencies.items()
        }
        self.results_dir = Path(results_dir)
        self.sim_num = sim_num
        self.destination = self._read_destination()
        kinds = set(self.enabled) | set(self.dependencies)
        for consumers in self.dependencies.values():
            kinds.update(consumers)
        self.kinds = sorted(kinds, key=len, reverse=True)
        self.managed = set(self.enabled)
        for kind, consumers in self.dependencies.items():
            if consumers & self.enabled:
                self.managed.add(kind)

    @classmethod
    def disabled(cls):
        obj = cls.__new__(cls)
        obj.enabled = set()
        obj.completed = set()
        obj.dependencies = {}
        obj.results_dir = Path("I001_Results")
        obj.sim_num = -1
        obj.destination = None
        obj.kinds = []
        obj.managed = set()
        return obj

    def _read_destination(self):
        marker = self.results_dir / "AAA_fwd"
        if not marker.is_file():
            raise FileNotFoundError(
                "PKL forwarding requested but {} does not exist".format(marker)
            )
        lines = [line.strip() for line in marker.read_text().splitlines()
                 if line.strip() and not line.lstrip().startswith("#")]
        if not lines:
            raise ValueError("PKL forwarding destination is empty in {}".format(marker))
        destination = Path(lines[0]).expanduser()
        if not destination.is_absolute():
            raise ValueError("PKL forwarding destination must be absolute: {}".format(destination))
        destination.mkdir(parents=True, exist_ok=True)
        if destination.resolve() == self.results_dir.resolve():
            raise ValueError("PKL forwarding destination cannot be the local results directory")
        return destination

    def _kind(self, path):
        prefix = "DATA_PICK_{:03d}_".format(self.sim_num)
        if not path.name.startswith(prefix) or path.suffix != ".pkl":
            return None
        suffix = path.name[len(prefix):-4]
        for kind in self.kinds:
            if suffix == kind or suffix.startswith(kind + "_"):
                return kind
        return None

    def complete(self, *stages):
        if self.destination is None:
            return
        self.completed.update(stages)
        pattern = "DATA_PICK_{:03d}_*.pkl".format(self.sim_num)
        for source in sorted(self.results_dir.glob(pattern)):
            kind = self._kind(source)
            if kind is None or kind not in self.managed:
                continue
            producer_ready = kind not in self.enabled or kind in self.completed
            pending = (self.dependencies.get(kind, set()) & self.enabled) - self.completed
            if producer_ready and not pending:
                self._move(source)

    def _move(self, source):
        target = self.destination / source.name
        try:
            os.replace(str(source), str(target))
        except OSError as exc:
            if exc.errno != errno.EXDEV:
                raise
            temporary = target.with_name(".{}.{}.tmp".format(target.name, os.getpid()))
            try:
                shutil.copy2(str(source), str(temporary))
                os.replace(str(temporary), str(target))
                source.unlink()
            finally:
                if temporary.exists():
                    temporary.unlink()
        print("Forwarded {} -> {}".format(source, target))

    def forward_globs(self, *patterns):
        """Forward terminal pickle families that do not use stage dependencies."""
        if self.destination is None:
            return
        for pattern in patterns:
            for source in sorted(self.results_dir.glob(pattern)):
                if source.suffix != ".pkl":
                    continue
                self._move(source)
