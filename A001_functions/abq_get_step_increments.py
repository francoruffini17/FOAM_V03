"""List the increment number / time of every frame of a step in an .odb.

Must run under Abaqus Python (`abq python`), not system Python - it imports
odbAccess. Used by A001_functions/stiffness_eigen.py to know which increments
have a restart state written (see *Restart, write in the .inp) so a
*Matrix Generate restart step can be built for each one.

Usage:
    abq python A001_functions/abq_get_step_increments.py <odb_path> <step_name> <out_json_path>
"""
import sys
import json
from odbAccess import openOdb


def get_step_increments(odb_path, step_name):
    odb = openOdb(odb_path, readOnly=True)
    try:
        frames = odb.steps[step_name].frames
        out = []
        for frame in frames:
            if frame.incrementNumber == 0:
                continue  # initial (undeformed) frame - nothing to extract
            out.append({
                'frameId': frame.frameId,
                'incrementNumber': frame.incrementNumber,
                'stepTime': frame.frameValue,
            })
        return out
    finally:
        odb.close()


def main():
    odb_path, step_name, out_json_path = sys.argv[1], sys.argv[2], sys.argv[3]
    increments = get_step_increments(odb_path, step_name)
    with open(out_json_path, 'w') as f:
        json.dump(increments, f, indent=2)
    print('Wrote {} increments to {}'.format(len(increments), out_json_path))


if __name__ == '__main__':
    main()
