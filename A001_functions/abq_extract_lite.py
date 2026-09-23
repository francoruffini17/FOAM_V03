"""Filtered Abaqus ODB extraction for the Video_3200 workflow.

Run with Abaqus Python::

    abq python A001_functions/abq_extract_lite.py 6000 6009

The legacy extractor is intentionally untouched.  This writer emits a compact,
gzip-compressed CSV containing only the histories needed by Reduce_results_lite:
reference-node U2/RF2, foam-node COOR1/COOR2, and element S11/S22/S12/S21.
"""
from __future__ import print_function

import argparse
import csv
import gzip
import os
import sys
import traceback
from multiprocessing import Pool, cpu_count

from odbAccess import openOdb

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from abq_scriptV9 import (  # noqa: E402 -- Abaqus-only import
    extract_elements_and_sets,
    extract_elements_and_sets_part,
    extract_nodes_and_sets,
    extract_nodes_and_sets_part,
    merge_dic,
)


FORMAT = 'FOAM_LITE_CSV_V1'
REFERENCE_SET = 'PERN-9999997'
NODE_FIELDS = set(('COOR1', 'COOR2'))
REFERENCE_FIELDS = set(('U2', 'RF2'))
STRESS_FIELDS = set(('S11', 'S22', 'S12', 'S21'))


def _clean_groups(groups):
    # Abaqus can expose a set membership as None in a partially completed ODB.
    return set(str(group).strip().upper() for group in (groups or ()))


def _history_values(output):
    raw_data = output.data
    # HistoryOutput.data is documented as a sequence, but Abaqus returns None
    # for histories that were registered and never populated (for example when
    # a later analysis step aborts before its first converged increment).
    if raw_data is None:
        return None
    data = list(raw_data)
    if not data:
        return None
    return [float(pair[0]) for pair in data], [float(pair[1]) for pair in data]


def _same_times(left, right):
    if len(left) != len(right):
        return False
    return all(abs(a - b) <= 1e-9 * max(1.0, abs(a), abs(b))
               for a, b in zip(left, right))


def extract_one(task):
    sim_num, results_dir, delete_odb = task
    job = 'SIM_{:03d}'.format(sim_num)
    odb_path = os.path.join('E001_Simulations', job, job + '.odb')
    output_path = os.path.join(results_dir, 'RES_{}_LITE.csv.gz'.format(job))
    temporary_path = output_path + '.tmp'
    odb = None
    stream = None
    try:
        odb = openOdb(odb_path, readOnly=True)
        step = odb.steps['Step-1']
        node_groups = merge_dic(extract_nodes_and_sets(odb),
                                extract_nodes_and_sets_part(odb))
        element_groups = merge_dic(extract_elements_and_sets(odb),
                                   extract_elements_and_sets_part(odb))

        stream = gzip.open(temporary_path, 'wb')
        writer = csv.writer(stream)
        writer.writerow([FORMAT])
        canonical_times = None
        written = 0
        skipped_unavailable = 0
        element_occurrence = {}

        for region_name, region in step.historyRegions.items():
            kind = region_name.split()[0].lower()
            if kind == 'node':
                node_id = int(region.point.node.label)
                groups = _clean_groups(node_groups.get(str(node_id), []))
                is_foam = any('FOAM' in group for group in groups)
                is_reference = any(REFERENCE_SET in group for group in groups)
                if not is_foam and not is_reference:
                    continue
                for field, output in region.historyOutputs.items():
                    if 'Repeated' in field:
                        continue
                    field = str(field).strip().upper()
                    row_kind = None
                    if is_foam and field in NODE_FIELDS:
                        row_kind = 'NODE'
                    elif is_reference and field in REFERENCE_FIELDS:
                        row_kind = 'REF'
                    if row_kind is None:
                        continue
                    history = _history_values(output)
                    if history is None:
                        skipped_unavailable += 1
                        continue
                    times, values = history
                    if canonical_times is None:
                        canonical_times = times
                    elif not _same_times(canonical_times, times):
                        raise ValueError('{} has a non-aligned {} history'.format(job, field))
                    writer.writerow([row_kind, node_id, field] + values)
                    written += 1

            elif kind == 'element':
                element_id = int(region.point.element.label)
                groups = _clean_groups(element_groups.get(str(element_id), []))
                if 'EALL' not in groups:
                    continue
                occurrence = element_occurrence.get(element_id, 0)
                element_occurrence[element_id] = occurrence + 1
                for field, output in region.historyOutputs.items():
                    if 'Repeated' in field:
                        continue
                    field = str(field).strip().upper()
                    if field not in STRESS_FIELDS:
                        continue
                    history = _history_values(output)
                    if history is None:
                        skipped_unavailable += 1
                        continue
                    times, values = history
                    if canonical_times is None:
                        canonical_times = times
                    elif not _same_times(canonical_times, times):
                        raise ValueError('{} has a non-aligned {} history'.format(job, field))
                    writer.writerow(['ELEM', element_id, occurrence, field] + values)
                    written += 1

        if canonical_times is None or not written:
            raise ValueError('No required histories were found in {}'.format(odb_path))
        writer.writerow(['TIME'] + canonical_times)
        writer.writerow(['END', written])
        stream.close()
        stream = None
        if os.path.exists(output_path):
            os.remove(output_path)
        os.rename(temporary_path, output_path)
        print('{}: wrote {} filtered histories to {}'.format(job, written, output_path))
        if skipped_unavailable:
            print('{}: skipped {} unavailable/empty histories from the partial ODB'.format(
                job, skipped_unavailable), file=sys.stderr)
        if delete_odb:
            odb.close()
            odb = None
            os.remove(odb_path)
        return 0
    except Exception as exc:
        print('{}: lite extraction failed: {}'.format(job, exc), file=sys.stderr)
        traceback.print_exc()
        return 1
    finally:
        if stream is not None:
            stream.close()
        if odb is not None:
            odb.close()
        if os.path.exists(temporary_path):
            os.remove(temporary_path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('sim_start', type=int)
    parser.add_argument('sim_end', type=int)
    parser.add_argument('--results-folder', default='I001_Results')
    parser.add_argument('--workers', type=int, default=None)
    parser.add_argument('--delete-odb', action='store_true')
    args = parser.parse_args(argv)
    if args.sim_end < args.sim_start:
        parser.error('sim_end must be greater than or equal to sim_start')
    if not os.path.isdir(args.results_folder):
        os.makedirs(args.results_folder)
    tasks = [(number, args.results_folder, args.delete_odb)
             for number in range(args.sim_start, args.sim_end + 1)]
    workers = args.workers or min(cpu_count(), len(tasks))
    pool = Pool(processes=workers)
    try:
        statuses = pool.map(extract_one, tasks)
    finally:
        pool.close()
        pool.join()
    return 1 if any(statuses) else 0


if __name__ == '__main__':
    sys.exit(main())
