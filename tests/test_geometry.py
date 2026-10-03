"""Independent examples for the subtle Block counting rules in V0.3."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from architecture import Architecture


class GeometryTests(unittest.TestCase):
    def setUp(self):
        self.a = Architecture.__new__(Architecture)
        self.a.width, self.a.height = 12, 12
        self.a.blocks = [{'id': 0, 'left': 5, 'right': 6, 'lower': 2, 'upper': 5,
                          'horizontal crossable': True, 'horizontal cross delay': 55,
                          'vertical crossable': False, 'vertical cross delay': 0}]
        self.a.lines = [{'direction': 'vertical', 'site': 3, 'delay': 7},
                        {'direction': 'horizontal', 'site': 5, 'delay': 15}]
        self.a.sites = {(x, y): '' for x in range(12) for y in range(12) if not (5 <= x <= 6 and 2 <= y <= 5)}

    def test_crossable_block_skips_coordinates(self):
        self.assertEqual(self.a.move(7, 5, -1, 0), ((4, 5), 55))
        self.assertEqual(self.a.move(7, 5, -2, 0), ((3, 5), 62))
        self.assertEqual(self.a.move(3, 5, 2, 0), ((7, 5), 62))

    def test_non_crossable_block_counts_coordinates(self):
        self.assertIsNone(self.a.move(5, 1, 0, 1))
        self.assertIsNone(self.a.move(5, 1, 0, 4))
        self.assertEqual(self.a.move(5, 1, 0, 8), ((5, 9), 15))

    def test_grid_and_line_boundaries(self):
        self.assertIsNone(self.a.move(0, 0, -1, 0))
        self.assertEqual(self.a.move(3, 0, 1, 0), ((4, 0), 7))
        self.assertEqual(self.a.move(4, 0, -1, 0), ((3, 0), 7))
        self.assertEqual(self.a.move(4, 0, 1, 0), ((5, 0), 0))


if __name__ == '__main__':
    unittest.main()
