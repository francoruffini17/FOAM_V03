from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from A001_functions.pkl_forward import PickleForwarder


def test_dependency_is_kept_until_last_enabled_consumer(tmp_path):
    results = tmp_path / "results"
    destination = tmp_path / "forwarded"
    results.mkdir()
    (results / "AAA_fwd").write_text(str(destination))
    a = results / "DATA_PICK_007_A.pkl"
    a2 = results / "DATA_PICK_007_A2.pkl"
    a.write_bytes(b"A")
    a2.write_bytes(b"A2")

    mover = PickleForwarder({"A", "A2"}, 7, {"A": {"A2"}}, results)
    mover.complete("A")
    assert a.exists()
    assert list(destination.iterdir()) == []

    mover.complete("A2")
    assert not a.exists()
    assert not a2.exists()
    assert (destination / a.name).read_bytes() == b"A"
    assert (destination / a2.name).read_bytes() == b"A2"


def test_indexed_and_sidecar_pickles_are_forwarded(tmp_path):
    results = tmp_path / "results"
    destination = tmp_path / "forwarded"
    results.mkdir()
    (results / "AAA_fwd").write_text(str(destination))
    t1 = results / "DATA_PICK_012_T1_003.pkl"
    t2 = results / "DATA_PICK_012_T2_003.pkl"
    t2_l = results / "DATA_PICK_012_T2_L_003.pkl"
    for path in (t1, t2, t2_l):
        path.write_bytes(path.name.encode())
    unrelated = results / "DATA_PICK_012_A.pkl"
    unrelated.write_bytes(b"unrelated")

    mover = PickleForwarder({"T1", "T2"}, 12, {"T1": {"T2"}}, results)
    mover.complete("T1")
    assert t1.exists()
    mover.complete("T2")
    assert {path.name for path in destination.iterdir()} == {t1.name, t2.name, t2_l.name}
    assert unrelated.exists()


def test_forwarding_requires_an_absolute_destination(tmp_path):
    results = tmp_path / "results"
    results.mkdir()
    (results / "AAA_fwd").write_text("relative/path\n")
    with pytest.raises(ValueError, match="must be absolute"):
        PickleForwarder({"A"}, 1, {}, results)


def test_terminal_dynamic_pickles_can_be_forwarded(tmp_path):
    results = tmp_path / "results"
    destination = tmp_path / "forwarded"
    results.mkdir()
    (results / "AAA_fwd").write_text(str(destination))
    dynamic = results / "PKL_DYN_009_force.pkl"
    velocity = results / "DYN_VEL_009.pkl"
    dynamic.write_bytes(b"dynamic")
    velocity.write_bytes(b"velocity")

    mover = PickleForwarder(set(), 9, {}, results)
    mover.forward_globs("PKL_DYN_009_*.pkl", "DYN_VEL_009.pkl")
    assert {path.name for path in destination.iterdir()} == {dynamic.name, velocity.name}
