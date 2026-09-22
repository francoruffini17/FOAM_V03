"""Reduce filtered ``RES_SIM_*_LITE.csv.gz`` files for Video_3200.

Outputs are written below ``I001_Results/LITE/SIM_NNN/`` and never replace
the legacy ``DATA_PICK_*`` products.  The four products deliberately separate
small curves, deforming geometry, lattice metadata, and the independently
generated smallest eigenmode.
"""

import argparse
import csv
import gzip
import json
import os
from pathlib import Path

import numpy as np

from .Hex_5 import read_mesh_json
from .Reduce_resultsV5 import (
    _mesh_artifact_path,
    _mesh_prefix_for_sim,
    create_PKL_G2_exact,
    create_PKL_H2,
    create_PKL_J1,
)


FORMAT = 'FOAM_LITE_CSV_V1'


def _write_npz(path, **arrays):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('wb') as stream:
        np.savez_compressed(stream, **arrays)
    os.replace(temporary, path)


def _write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + '.tmp')
    with temporary.open('w', encoding='utf-8') as stream:
        json.dump(payload, stream, indent=2, sort_keys=True)
    os.replace(temporary, path)


def read_lite_csv(path):
    """Read one compact extraction in a single streaming pass."""
    coordinates = {}
    references = {'U2': [], 'RF2': []}
    stresses = {'S11': {}, 'S22': {}, 'S12': {}, 'S21': {}}
    times = None
    ended = False
    with gzip.open(path, 'rt', newline='') as stream:
        reader = csv.reader(stream)
        first = next(reader, None)
        if first != [FORMAT]:
            raise ValueError(f'{path} is not a {FORMAT} file')
        for row in reader:
            if not row:
                continue
            kind = row[0]
            if kind == 'NODE':
                node_id, field = int(row[1]), row[2]
                coordinates.setdefault(node_id, {})[field] = np.asarray(row[3:], dtype=np.float64)
            elif kind == 'REF':
                field = row[2]
                if field in references:
                    references[field].append(np.asarray(row[3:], dtype=np.float64))
            elif kind == 'ELEM':
                element_id, occurrence, field = int(row[1]), int(row[2]), row[3]
                if field in stresses:
                    stresses[field].setdefault(element_id, {})[occurrence] = np.asarray(
                        row[4:], dtype=np.float64)
            elif kind == 'TIME':
                times = np.asarray(row[1:], dtype=np.float64)
            elif kind == 'END':
                ended = True
    if times is None or not ended:
        raise ValueError(f'{path} is incomplete (TIME or END row missing)')
    if not coordinates or not references['U2'] or not references['RF2']:
        raise ValueError(f'{path} lacks coordinates or reference U2/RF2')
    for field in ('S11', 'S22'):
        if not stresses[field]:
            raise ValueError(f'{path} lacks required {field} histories')
    if not stresses['S12'] and not stresses['S21']:
        raise ValueError(f'{path} lacks required S12/S21 histories')

    node_ids = np.asarray(sorted(coordinates), dtype=np.int64)
    n_t = len(times)
    coordinate_array = np.empty((n_t, len(node_ids), 2), dtype=np.float64)
    for column, node_id in enumerate(node_ids):
        record = coordinates[node_id]
        for component, field in enumerate(('COOR1', 'COOR2')):
            values = record.get(field)
            if values is None or len(values) != n_t:
                raise ValueError(f'node {node_id} has invalid {field} history')
            coordinate_array[:, column, component] = values

    u2 = np.mean(np.stack(references['U2']), axis=0)
    rf2 = np.sum(np.stack(references['RF2']), axis=0)
    if len(u2) != n_t or len(rf2) != n_t:
        raise ValueError('reference histories do not match TIME')

    stress_out = {}
    for field, per_element in stresses.items():
        if not per_element:
            continue
        stress_out[field] = {
            str(element_id): [values.tolist() for _, values in sorted(occurrences.items())]
            for element_id, occurrences in per_element.items()
        }
    stress_out['t'] = times.tolist()
    return times, node_ids, coordinate_array, u2, rf2, stress_out


def _padded_rows(rows, dtype=np.int64, fill=-1):
    width = max((len(row) for row in rows), default=0)
    result = np.full((len(rows), width), fill, dtype=dtype)
    lengths = np.zeros(len(rows), dtype=np.int16)
    for index, row in enumerate(rows):
        lengths[index] = len(row)
        result[index, :len(row)] = row
    return result, lengths


def _shear_mean(coordinates, elements, batch_size=512):
    """Compute the exact TP2 ``shear_mean`` without materializing TP1/TP2."""
    total = np.zeros(coordinates.shape[0], dtype=np.float64)
    count = 0
    b_quad = np.asarray([[-0.25, 0.25, 0.25, -0.25],
                         [-0.25, -0.25, 0.25, 0.25]], dtype=np.float64)
    for node_count in (3, 4):
        selected = np.asarray([row for row in elements if len(row) == node_count], dtype=np.int64)
        if not len(selected):
            continue
        for start in range(0, len(selected), batch_size):
            indices = selected[start:start + batch_size]
            points = coordinates[:, indices, :]
            if node_count == 3:
                dx = np.stack((points[:, :, 1] - points[:, :, 0],
                               points[:, :, 2] - points[:, :, 0]), axis=-1)
                reference = dx[0]
                reference_inv = np.linalg.pinv(reference)
                deformation = np.einsum('fbij,bjk->fbik', dx, reference_inv)
            else:
                jacobian = np.einsum('an,fbnd->fbad', b_quad, points)
                reference_inv_t = np.linalg.pinv(np.swapaxes(jacobian[0], 1, 2))
                deformation = np.einsum(
                    'fbij,bjk->fbik', np.swapaxes(jacobian, 2, 3), reference_inv_t)
            total += (0.5 * np.sum(deformation * deformation, axis=(2, 3))).sum(axis=1)
            count += len(indices)
    if not count:
        raise ValueError('mesh contains no supported triangle or quadrilateral elements')
    return total / count


def _legacy_c2(times, node_ids, coordinates, elements):
    expected = np.arange(1, len(node_ids) + 1)
    if not np.array_equal(node_ids, expected):
        raise ValueError('lite I3 currently requires consecutive 1-based foam node IDs')
    nodes_time = []
    for frame in coordinates:
        nodes_time.append({str(i + 1): tuple(frame[i]) for i in range(len(node_ids))})
    return {
        't': times.tolist(),
        'nodes_time': nodes_time,
        'elements': {str(i + 1): [int(node) + 1 for node in row]
                     for i, row in enumerate(elements)},
    }


def _metadata(sim_num, simulation_json, mesh_json, mesh_path, elements, holes):
    geometry = mesh_json.get('geometry', {})
    steps = simulation_json.get('steps', [])
    pressure = next(
        (step.get('Pressure_BC') for step in steps if step.get('Pressure_BC') is not None),
        next((step.get('INT_P') for step in steps if step.get('INT_P') is not None),
             simulation_json.get('initial_Pressure')),
    )
    return {
        'format': 'FOAM_VIDEO_3200_LITE_V1',
        'simulation': int(sim_num),
        'source_mesh': str(mesh_path),
        'simulation_parameters': simulation_json,
        'mesh_information': {
            key: value for key, value in mesh_json.items()
            if key not in ('nodes', 'elements', 'hole_boundary_nodes')
        },
        'lattice': {
            'geometry': geometry,
            'mesh_kind': geometry.get('mesh_kind'),
            'porosity': geometry.get('porosity'),
            'number_of_nodes': len(mesh_json.get('nodes', [])),
            'number_of_elements': len(elements),
            'number_of_holes': len(holes),
            'internal_pressure': pressure,
            'material_model': simulation_json.get('material_model', 'linear'),
        },
    }


def reduce_one(sim_num, results_dir='I001_Results', grid_index=3002,
               n_workers=1, max_memory_gb=None, delete_csv=False):
    source = Path(results_dir) / f'RES_SIM_{sim_num:03d}_LITE.csv.gz'
    if not source.is_file():
        raise FileNotFoundError(source)
    times, node_ids, coordinates, u2, rf2, stresses = read_lite_csv(source)

    obj_path = Path(results_dir) / 'OBJ_files' / f'SIM_{sim_num:03d}.json'
    with obj_path.open(encoding='utf-8') as stream:
        simulation_json = json.load(stream)
    mesh_path = Path(simulation_json['input_name'])
    with mesh_path.open(encoding='utf-8') as stream:
        mesh_json = json.load(stream)
    reference_nodes_raw, elements_raw = read_mesh_json(str(mesh_path))
    reference_nodes = np.asarray(
        [[float(node[0]), float(node[1])] for node in reference_nodes_raw],
        dtype=np.float64,
    )
    reference_node_labels = np.asarray(
        [str(node[2]) for node in reference_nodes_raw], dtype='U32')
    elements = [[int(node) for node in row] for row in elements_raw]
    holes = [[int(node) for node in row] for row in mesh_json.get('hole_boundary_nodes', [])]

    shear_mean = _shear_mean(coordinates, elements)
    c2 = _legacy_c2(times, node_ids, coordinates, elements)
    graph_path = _mesh_artifact_path(_mesh_prefix_for_sim(sim_num), 'I', grid_index,
                                     'gridhex.json')
    i1 = create_PKL_J1(stresses, c2, graph_path, sim_num=sim_num)
    i2 = create_PKL_H2(i1, sim_num=sim_num)
    i3 = create_PKL_G2_exact(i2, n_workers=n_workers,
                             max_memory_gb=max_memory_gb, algorithm='bfs')
    del c2, i1, i2, stresses

    output_dir = Path(results_dir) / 'LITE' / f'SIM_{sim_num:03d}'
    _write_npz(
        output_dir / 'curves.npz',
        t=times,
        u2=u2,
        rf2=rf2,
        shear_mean=shear_mean,
        global_ef_t=np.asarray(i3['global_ef_t'], dtype=np.float64),
        global_ef_c=np.asarray(i3['global_ef_c'], dtype=np.float64),
        global_ef_t_allnodes=np.asarray(i3['global_ef_t_allnodes'], dtype=np.float64),
        global_ef_c_allnodes=np.asarray(i3['global_ef_c_allnodes'], dtype=np.float64),
        n_nodes_total=np.asarray(i3['n_nodes_total'], dtype=np.int64),
    )
    element_array, element_lengths = _padded_rows(elements)
    hole_array, hole_lengths = _padded_rows(holes)
    _write_npz(
        output_dir / 'geometry.npz',
        t=times,
        node_ids=node_ids,
        coordinates=coordinates.astype(np.float32),
        reference_node_labels=reference_node_labels,
        reference_coordinates=reference_nodes,
        elements=element_array,
        element_lengths=element_lengths,
        element_types=np.asarray(
            mesh_json.get('element_types', element_lengths), dtype=np.int16),
        hole_boundary_nodes=hole_array,
        hole_boundary_lengths=hole_lengths,
    )
    _write_json(output_dir / 'metadata.json',
                _metadata(sim_num, simulation_json, mesh_json, mesh_path, elements, holes))
    if delete_csv:
        source.unlink()
    print(f'SIM_{sim_num:03d}: wrote Video_3200 lite data to {output_dir}')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, allow_abbrev=False)
    parser.add_argument('sim_start', type=int)
    parser.add_argument('sim_end', type=int)
    parser.add_argument('--results-folder', default='I001_Results')
    parser.add_argument('--grid-index', type=int, default=3002)
    parser.add_argument('--n-workers', type=int, default=1)
    parser.add_argument('--max-memory-gb', type=float, default=None)
    parser.add_argument('--delete-csv', action='store_true')
    args = parser.parse_args(argv)
    if args.sim_end < args.sim_start:
        parser.error('sim_end must be greater than or equal to sim_start')
    for sim_num in range(args.sim_start, args.sim_end + 1):
        reduce_one(sim_num, args.results_folder, args.grid_index, args.n_workers,
                   args.max_memory_gb, args.delete_csv)


if __name__ == '__main__':
    main()
