"""Tests for oneirometer — synthetic nights only, no wing required."""

import json
import math
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from oneirometer import (check_night, load_submit, marginals, meter,
                         parse_recall, shannon_entropy)


class TestEntropy(unittest.TestCase):
    def test_uniform_is_five_bits(self):
        counts = {format(i, "05b"): 32 for i in range(32)}
        self.assertAlmostEqual(shannon_entropy(counts), 5.0, places=9)

    def test_collapsed_is_zero(self):
        self.assertEqual(shannon_entropy({"11111": 1024}), 0.0)


class TestMeter(unittest.TestCase):
    def test_uniform_night(self):
        counts = {format(i, "05b"): 32 for i in range(32)}
        m = meter(counts)
        self.assertEqual(m["shots"], 1024)
        self.assertEqual(m["unique_outcomes"], 32)
        self.assertAlmostEqual(m["effective_outcomes"], 32.0, places=9)
        self.assertAlmostEqual(m["heavy_share"], 256 / 1024, places=9)
        for v in m["marginals"].values():
            self.assertAlmostEqual(v, 0.5, places=9)
        self.assertEqual(m["pole"]["points_from_flip"], 0.0)

    def test_collapsed_night(self):
        m = meter({"11111": 1024})
        self.assertEqual(m["entropy_bits"], 0.0)
        self.assertEqual(m["top"][0]["string"], "11111")
        self.assertEqual(m["top"][0]["count"], 1024)
        self.assertEqual(m["heavy_share"], 1.0)
        self.assertEqual(m["pole"]["p_one"], 1.0)

    def test_bit_convention_rightmost_is_q0(self):
        # only q[0] (rightmost bit) fires
        m = marginals({"00001": 100})
        self.assertEqual(m[0], 1.0)
        self.assertEqual(m[1], 0.0)
        # only q[4] (leftmost bit) fires
        m = marginals({"10000": 100})
        self.assertEqual(m[4], 1.0)
        self.assertEqual(m[0], 0.0)

    def test_tie_order_is_deterministic(self):
        counts = {"00000": 10, "11111": 10, "00001": 5}
        first = meter(counts)["top"]
        second = meter(counts)["top"]
        self.assertEqual([t["string"] for t in first],
                         [t["string"] for t in second])


class TestRecallCheck(unittest.TestCase):
    RECALL = """# Dream recall — 2026-01-01

## What the night showed

- `11111`: 100 (50.0%)
- `00000`: 100 (50.0%)

Total shots: 200, unique outcomes: 2

## Reading

A coin, flipped by the dark.
"""

    def write_pair(self, directory, recall_text=RECALL, counts=None):
        counts = counts or {"11111": 100, "00000": 100}
        submit = os.path.join(directory, "2026-01-01.submit.json")
        recall = os.path.join(directory, "2026-01-01.recall.md")
        with open(submit, "w") as f:
            json.dump({"backend": "test", "shots": 200,
                       "counts": counts}, f)
        with open(recall, "w") as f:
            f.write(recall_text)
        return submit, recall

    def test_parse_recall(self):
        with tempfile.TemporaryDirectory() as d:
            _, recall = self.write_pair(d)
            top, unique = parse_recall(recall)
            self.assertEqual(top, [("11111", 100), ("00000", 100)])
            self.assertEqual(unique, 2)

    def test_agreeing_night_passes(self):
        with tempfile.TemporaryDirectory() as d:
            submit, recall = self.write_pair(d)
            report = check_night(submit, recall)
            self.assertTrue(all(c["ok"] for c in report["checks"]),
                            report["checks"])

    def test_tampered_recall_is_caught(self):
        bad = self.RECALL.replace("`11111`: 100", "`11111`: 99")
        with tempfile.TemporaryDirectory() as d:
            submit, recall = self.write_pair(d, recall_text=bad)
            report = check_night(submit, recall)
            top = [c for c in report["checks"]
                   if c["name"] == "top-8-list"][0]
            self.assertFalse(top["ok"])

    def test_missing_recall_is_reported(self):
        with tempfile.TemporaryDirectory() as d:
            submit, _ = self.write_pair(d)
            os.remove(os.path.join(d, "2026-01-01.recall.md"))
            report = check_night(
                submit, os.path.join(d, "2026-01-01.recall.md"))
            self.assertFalse(all(c["ok"] for c in report["checks"]))


if __name__ == "__main__":
    unittest.main()
