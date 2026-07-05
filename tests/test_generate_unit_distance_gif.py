import unittest

from generate_unit_distance_gif import (
    frame_data_for_meshes,
    max_mesh_size,
    offsets_for_mesh,
    unit_edges_for_mesh,
)


class TestGenerateUnitDistanceGif(unittest.TestCase):
    def test_max_mesh_size_for_16x16(self) -> None:
        self.assertEqual(max_mesh_size(16), 21)

    def test_offsets_for_mesh_contains_expected_pythagorean_pairs(self) -> None:
        offsets = offsets_for_mesh(5, 16)
        self.assertIn((0, 5), offsets)
        self.assertIn((3, 4), offsets)
        self.assertIn((4, 3), offsets)
        self.assertIn((5, 0), offsets)

    def test_unit_edges_for_mesh_1_on_3x3(self) -> None:
        edges = unit_edges_for_mesh(3, 1)
        self.assertEqual(len(edges), 12)

    def test_only_pertinent_meshes_can_be_selected(self) -> None:
        frames = frame_data_for_meshes(grid_size=6, include_non_pertinent=False)
        self.assertEqual([f.mesh_size for f in frames], [1, 2, 3, 4, 5])


if __name__ == "__main__":
    unittest.main()
