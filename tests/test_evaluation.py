import math
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from evaluate import metrics


class ScoringTests(unittest.TestCase):
    def row(self, delay):
        return {'From':'a','To':'b','delay':str(delay)}

    def test_relative_error_symmetry(self):
        for pred in (75,125):
            self.assertAlmostEqual(metrics([self.row(100)],[self.row(pred)])['positive_delay_score'],100*(1-math.tanh(1)))

    def test_zero_separated_and_exact(self):
        m=metrics([self.row(0),self.row(100)],[self.row(0),self.row(100)])
        self.assertEqual((m['positive_delay_score'],m['zero_golden_rows'],m['zero_exact_matches']),(100,1,1))

    def test_order_must_match(self):
        with self.assertRaises(ValueError):
            metrics([self.row(100)],[{'From':'b','To':'a','delay':'100'}])

if __name__=='__main__':
    unittest.main()
