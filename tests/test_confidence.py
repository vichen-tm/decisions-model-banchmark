import json
from fractions import Fraction
from pathlib import Path
import random
import unittest
from decision_benchmark.confidence import (
    OperatingPoint,
    choose_threshold,
    enumerate_points,
)
from decision_benchmark.rating import relative_quality, utility_score

FIXTURES = Path(__file__).parent / "fixtures"


class ConfidenceTests(unittest.TestCase):
    def test_ties_and_invalid_values(self):
        self.assertEqual(
            [p.retained for p in enumerate_points([[0.5, 2, 1], [0.5, 3, 2]])], [0, 5]
        )
        for values in (
            [],
            [[True, 1, 1]],
            [[float("nan"), 1, 1]],
            [[2, 1, 1]],
            [[0.5, 0, 0]],
            [[0.5, 2, 3]],
        ):
            with self.assertRaises(ValueError):
                enumerate_points(values)

    def test_five_answers_and_99_to_100(self):
        for levels in (
            [[0.5, 1995, 995], [0.99, 5, 5]],
            [[0.8, 1000, 980], [0.99, 1000, 1000]],
        ):
            point = choose_threshold(levels)
            self.assertEqual(point.retained, 2000)
            self.assertEqual(point.utility, 0)

    def test_perfect_wrong_and_no_signal(self):
        self.assertEqual(choose_threshold([[0.5, 100, 100]]).retained, 100)
        wrong = choose_threshold([[0.5, 100, 0]])
        self.assertEqual((wrong.retained, wrong.j, wrong.utility), (0, 1, None))
        self.assertEqual(choose_threshold([[0.5, 100, 80]]).retained, 100)

    def test_accepted_boundary_is_visible(self):
        before = choose_threshold([[0.9, 18, 18], [0.1, 2, 0]])
        after = choose_threshold([[0.9, 18, 18], [0.1, 2, 1]])
        self.assertEqual(
            (before.retained, before.errors, after.retained, after.errors),
            (18, 0, 20, 1),
        )

    def test_removing_only_errors_improves_objective(self):
        for good in range(6):
            for errors in range(1, 6):
                before = OperatingPoint(0.5, good + errors, good, 20, 6)
                after = OperatingPoint(0.6, good + errors - 1, good, 20, 6)
                self.assertGreater((after.j, -after.errors), (before.j, -before.errors))
                self.assertGreater(after.utility, before.utility)

    def test_all_synthetic_and_real_fixtures(self):
        cases = json.loads((FIXTURES / "cases.json").read_text())["cases"]
        real = json.loads((FIXTURES / "real.json").read_text())["cases"]
        self.assertEqual((len(cases), len(real)), (51, 60))
        for case in cases + real:
            point = choose_threshold(case["levels"])
            if case.get("expected", {}).get("n") is not None:
                self.assertEqual(point.retained, case["expected"]["n"], case["id"])
            if point.utility is not None:
                self.assertGreaterEqual(point.utility, 0)
        golden = json.loads((Path(__file__).parent / "golden/rating.json").read_text())
        by_id = {r["model"] + " / " + r["category"]: r for r in golden["categories"]}
        for case in real:
            point = choose_threshold(case["levels"])
            self.assertEqual(point.record(), by_id[case["id"]]["result"])
            self.assertEqual(
                str(point.utility), by_id[case["id"]]["confidence_utility_exact"]
            )

    def test_random_direct_set_oracle(self):
        rng = random.Random(20261016)
        for _ in range(200):
            rows = [(rng.randrange(10) / 10, rng.randrange(2)) for _ in range(60)]
            levels = [[t, 1, g] for t, g in rows]
            true = {i for i, (_, g) in enumerate(rows) if g}
            for point in enumerate_points(levels):
                chosen = {
                    i
                    for i, (t, _) in enumerate(rows)
                    if point.threshold is not None and t >= point.threshold
                }
                union = chosen | true
                expected = (
                    Fraction(len(chosen & true), len(union)) if union else Fraction(1)
                )
                self.assertEqual(point.j, expected)

    def test_rating_boundaries(self):
        self.assertEqual(relative_quality(0.9 - 0.0274, 0.9), 7)
        self.assertEqual(relative_quality(0.9 - 0.2055, 0.9), 1)
        self.assertEqual(utility_score(Fraction(1, 10)), 1)
        self.assertEqual(utility_score(Fraction(100001, 1000000)), 2)
        with self.assertRaises(ValueError):
            utility_score(None)
