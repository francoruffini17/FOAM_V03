import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from A001_functions.Reduce_resultsV5 import create_PKL_T1


def test_create_pkl_t1_snaps_triangulation_nodes_to_fem_nodes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)

    mesh_path = tmp_path / "tiny.mesh.json"
    mesh_path.write_text(json.dumps({
        "type": "mesh",
        "nodes": [
            {"x": 0.0, "y": 0.0, "label": "1"},
            {"x": 1.0, "y": 0.0, "label": "1"},
            {"x": 0.0, "y": 1.0, "label": "1"},
            {"x": 1.0, "y": 1.0, "label": "1"},
        ],
        "elements": [],
    }))

    obj_dir = tmp_path / "I001_Results" / "OBJ_files"
    obj_dir.mkdir(parents=True)
    (obj_dir / "SIM_042.json").write_text(json.dumps({
        "scale_x": 1.0,
        "scale_y": 1.0,
        "input_name": str(mesh_path),
    }))

    tri_path = tmp_path / "snap.tri"
    tri_path.write_text(
        "3\n"
        "0.05 0.05 1\n"
        "0.95 0.10 2\n"
        "0.10 0.95 1\n"
        "1\n"
        "0 1 2\n"
    )

    data_c2 = {
        "t": [0.0, 1.0],
        "nodes_time": [
            {
                "1": (0.0, 0.0),
                "2": (1.0, 0.0),
                "3": (0.0, 1.0),
                "4": (1.0, 1.0),
            },
            {
                "1": (10.0, 20.0),
                "2": (11.0, 20.0),
                "3": (10.0, 21.0),
                "4": (11.0, 21.0),
            },
        ],
        "elements": {},
    }

    output_path = tmp_path / "DATA_PICK_042_T1.pkl"
    t1 = create_PKL_T1(
        DATA_C2=data_c2,
        triangulation_file=str(tri_path),
        sim_num=42,
        output_path=str(output_path),
    )

    assert output_path.exists()
    assert t1["node_matches"] == {1: 1, 2: 2, 3: 3}
    assert t1["nodes"][0][1][:2] == (0.0, 0.0)
    assert t1["nodes"][0][2][:2] == (1.0, 0.0)
    assert t1["nodes"][0][3][:2] == (0.0, 1.0)
    assert t1["nodes"][1][1][:2] == (10.0, 20.0)
    assert t1["nodes"][1][2][:2] == (11.0, 20.0)
    assert t1["nodes"][1][3][:2] == (10.0, 21.0)
    assert t1["elements_area"][1][0] == pytest.approx(0.5)
    assert t1["elements_area_normalized"][1][1] == pytest.approx(1.0)
