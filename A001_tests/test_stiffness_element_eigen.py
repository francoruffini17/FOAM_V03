import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from A001_functions.stiffness_eigen import (
    _matrix_step_lines,
    element_eigenpairs_from_mtx,
)


def test_element_matrix_step_requests_unassembled_stiffness():
    lines = _matrix_step_lines(3, ['SET-A, 1, 2, 0.0'], element_by_element=True)
    assert '*Matrix Generate, stiffness, element by element' in lines
    assert '*Matrix Output, stiffness, format=matrix input' in lines


def test_element_eigenpairs_parse_mixed_local_matrix_sizes(tmp_path):
    matrix_file = tmp_path / 'elements.mtx'
    matrix_file.write_text(
        # element, row node, row dof, column node, column dof, value
        '10, 1, 1, 1, 1, 2.0\n'
        '10, 2, 1, 1, 1, -1.0\n'
        '10, 2, 1, 2, 1, 2.0\n'
        '20, 3, 1, 3, 1, 4.0\n'
        '20, 3, 2, 3, 2, 5.0\n'
        '20, 4, 1, 4, 1, 6.0\n'
    )

    result = element_eigenpairs_from_mtx(matrix_file)

    np.testing.assert_array_equal(result['element_labels'], [10, 20])
    np.testing.assert_array_equal(result['dof_offsets'], [0, 2, 5])
    np.testing.assert_array_equal(result['dof_nodes'], [1, 2, 3, 3, 4])
    np.testing.assert_array_equal(result['dof_numbers'], [1, 1, 1, 2, 1])
    np.testing.assert_allclose(result['eigenvalues'][:2], [1.0, 3.0])
    np.testing.assert_allclose(result['eigenvalues'][2:], [4.0, 5.0, 6.0])

    first_vectors = result['eigenvectors'][
        result['eigenvector_offsets'][0]:result['eigenvector_offsets'][1]
    ].reshape(2, 2)
    first_matrix = np.array([[2.0, -1.0], [-1.0, 2.0]])
    np.testing.assert_allclose(
        first_matrix @ first_vectors,
        first_vectors * result['eigenvalues'][:2],
    )
