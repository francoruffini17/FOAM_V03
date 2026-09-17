"""Bounded TP2 mechanics batches with disk-backed, legacy-compatible outputs."""
from collections.abc import MutableMapping
import os
import pickle
import sqlite3
import tempfile
from pathlib import Path
import numpy as np
from .reduction_io import tracked_open


class DiskDict(MutableMapping):
    """A temporary mapping that serializes as an ordinary dictionary."""
    def __init__(self, directory, name):
        self.directory = directory  # Keep temporary storage alive with returned data.
        self.db = sqlite3.connect(str(Path(directory.name) / (name + '.sqlite')))
        self.db.execute('CREATE TABLE entries (key BLOB PRIMARY KEY, value BLOB)')

    def __setitem__(self, key, value):
        self.db.execute('INSERT OR REPLACE INTO entries VALUES (?, ?)',
                        (pickle.dumps(key), pickle.dumps(value, protocol=4)))

    def __getitem__(self, key):
        row = self.db.execute('SELECT value FROM entries WHERE key=?', (pickle.dumps(key),)).fetchone()
        if row is None:
            raise KeyError(key)
        return pickle.loads(row[0])

    def __delitem__(self, key):
        self.db.execute('DELETE FROM entries WHERE key=?', (pickle.dumps(key),))

    def __iter__(self):
        for row in self.db.execute('SELECT key FROM entries ORDER BY rowid'):
            yield pickle.loads(row[0])

    def __len__(self):
        return self.db.execute('SELECT count(*) FROM entries').fetchone()[0]

    def items(self):
        for key, value in self.db.execute('SELECT key,value FROM entries ORDER BY rowid'):
            yield pickle.loads(key), pickle.loads(value)

    def __reduce__(self):
        return (dict, (), None, None, iter(self.items()))

    def __del__(self):
        if hasattr(self, 'db'):
            self.db.close()


class Moments:
    """Merge weighted population moments without subtracting large squared means."""
    def __init__(self):
        self.weight = 0.

    def add(self, values, weights=None):
        values = np.asarray(values, dtype=float)
        weights = np.ones(len(values)) if weights is None else np.asarray(weights)
        weight = float(weights.sum())
        if weight <= 0:
            return
        mean = np.average(values, axis=0, weights=weights)
        m2 = np.sum(weights[:, None] * (values - mean)**2, axis=0)
        minimum, maximum = values.min(axis=0), values.max(axis=0)
        if self.weight:
            delta = mean - self.mean
            total = self.weight + weight
            self.m2 += m2 + delta**2 * self.weight * weight / total
            self.mean += delta * weight / total
            self.minimum = np.minimum(self.minimum, minimum)
            self.maximum = np.maximum(self.maximum, maximum)
        else:
            self.mean, self.m2 = mean, m2
            self.minimum, self.maximum = minimum, maximum
        self.weight += weight

    @property
    def std(self):
        return np.sqrt(self.m2 / self.weight)

    def stats(self):
        return dict(min=self.minimum.tolist(), max=self.maximum.tolist(),
                    mean=self.mean.tolist(), std=self.std.tolist())


def reduce_tp2(data, compute, output_path, sim_num, params, reference):
    batch_size = int(os.environ.get('REDUCE_TP2_BATCH_SIZE', '64'))
    summary_only = os.environ.get('REDUCE_TP2_SUMMARY_ONLY', 'n').lower() == 'y'
    if batch_size < 1:
        raise ValueError('TP2 batch size must be positive')
    params = params if params is not None else [(1, 1, 1, 1), (1, 1, 2, 2)]
    ids = sorted(data['elements'])
    if not ids:
        raise ValueError('TP2 requires at least one element')
    n_t = len(data['t'])
    fields = 'edge_sizes q epsilon F shear gle edi Se J C'.split()
    per_element = fields + ['w', 'time_invariant']
    scratch = Path(os.environ.get('REDUCE_SCRATCH_DIR', 'I001_Results/.reduction/scratch'))
    scratch.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix='tp2-', dir=scratch)
    result = {}
    if not summary_only:
        result = {key: DiskDict(temporary, key) for key in fields}
        result['w'] = {p: DiskDict(temporary, 'w' + str(j)) for j, p in enumerate(params)}
        result['time_invariant'] = {k: DiskDict(temporary, 'ti_' + k)
                                    for k in ('areas', 'normalized_areas')}
    moments = {k: Moments() for k in ['areas', 'normalized_areas', 'shear', 'gle', 'edi', 'Se']}
    weighted = {k: Moments() for k in ['shear', 'gle', 'edi']}
    energy = {p: Moments() for p in params}
    weighted_energy = {p: Moments() for p in params}
    for start in range(0, len(ids), batch_size):
        batch_ids = ids[start:start + batch_size]
        subset = dict(data)
        for key in ('elements', 'element_types', 'elements_area', 'elements_area_normalized'):
            subset[key] = {eid: data[key][eid] for eid in batch_ids}
        chunk = compute(subset, w_param_sets=params, step1_start_ti=reference, _batch_internal=True)
        if start == 0:
            result.update({k: v for k, v in chunk.items() if k not in per_element})
        weights = [data['elements_area'][eid][0] for eid in batch_ids]
        for key, source in [('areas', 'elements_area'), ('normalized_areas', 'elements_area_normalized')]:
            moments[key].add([[data[source][eid][ti] for ti in range(n_t)] for eid in batch_ids])
        for key in ('shear', 'gle', 'edi', 'Se'):
            values = [[chunk[key][eid][ti] for ti in range(n_t)] for eid in batch_ids]
            moments[key].add(values)
            if key in weighted:
                weighted[key].add(values, weights)
        for p in params:
            values = [[chunk['w'][p][eid][ti] for ti in range(n_t)] for eid in batch_ids]
            energy[p].add(values)
            weighted_energy[p].add(values, weights)
        if not summary_only:
            for key in fields:
                result[key].update(chunk[key])
                result[key].db.commit()
            for p in params:
                result['w'][p].update(chunk['w'][p])
                result['w'][p].db.commit()
            for key in result['time_invariant']:
                result['time_invariant'][key].update(chunk['time_invariant'][key])
                result['time_invariant'][key].db.commit()
        del chunk, subset
        print(f'TP2: elements {min(start + batch_size, len(ids))}/{len(ids)} done', flush=True)
    result['time_variant'] = {k: moments[k].stats() for k in ('areas', 'normalized_areas')}
    result['general_information'] = dict(n_elements=len(ids),
        area_global_min=float(moments['areas'].minimum.min()),
        area_global_max=float(moments['areas'].maximum.max()),
        norm_area_global_min=float(moments['normalized_areas'].minimum.min()),
        norm_area_global_max=float(moments['normalized_areas'].maximum.max()))
    scale = 0.5 * np.sqrt(len(ids) / (len(ids) - 1)) if len(ids) > 1 else 1.
    result['eta'] = (1 - moments['normalized_areas'].std / scale).tolist()
    result['eta_shear'] = (1 - moments['Se'].std / scale).tolist()
    for key in weighted:
        result[key + '_mean'] = moments[key].mean.tolist()
        result[key + '_mean_aw'] = (weighted[key].mean if weighted[key].weight else np.zeros(n_t)).tolist()
    for key in ('w_mean', 'w_std', 'w_cv', 'w_std_area_weighted', 'w_cv_area_weighted', 'W'):
        result[key] = {}
    for p in params:
        e, we = energy[p], weighted_energy[p]
        mean = we.mean if we.weight else np.zeros(n_t)
        std = we.std if we.weight else np.zeros(n_t)
        result['w_mean'][p] = e.mean.tolist()
        result['w_std'][p] = e.std.tolist()
        result['w_cv'][p] = (e.std / (np.abs(e.mean) + 1e-30)).tolist()
        result['w_std_area_weighted'][p] = std.tolist()
        result['w_cv_area_weighted'][p] = (std / (np.abs(mean) + 1e-30)).tolist()
        result['W'][p] = (mean * we.weight).tolist()
    light = {k: v for k, v in result.items() if k not in per_element}
    if output_path is None and sim_num is not None:
        output_path = f'I001_Results/DATA_PICK_{sim_num:03d}_TP2.pkl'
    if output_path is not None:
        output_path = str(output_path)
        light_path = str(Path(output_path).with_name(Path(output_path).stem + '_L.pkl'))
        if not summary_only:
            with tracked_open(output_path, 'wb') as stream:
                pickler = pickle.Pickler(stream, protocol=4)
                # These result trees have no cycles. Avoid retaining every spilled
                # element in the pickle memo while streaming the final dictionary.
                pickler.fast = True
                pickler.dump(result)
            print(f"PKL_TP2 saved to '{output_path}'", flush=True)
        with tracked_open(light_path, 'wb') as stream:
            pickle.dump(light, stream)
        print(f"PKL_TP2_L saved to '{light_path}'", flush=True)
    return light if summary_only else result
