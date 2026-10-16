import unittest, math
from decision_benchmark.scoring import (
    distribution,
    score_answer,
    RESPONSE_SUM_TOLERANCE,
)


class NormalizationTests(unittest.TestCase):
    def test_inclusive_symmetric_boundary(self):
        for values in ([0.49, 0.5], [0.51, 0.5], [0.3, 0.6994], [0.3, 0.6997]):
            p = distribution(values, RESPONSE_SUM_TOLERANCE)
            self.assertAlmostEqual(sum(p), 1)
            self.assertEqual(
                max(range(2), key=p.__getitem__), max(range(2), key=values.__getitem__)
            )

    def test_outside_and_malformed(self):
        for values in (
            [0.49, 0.499999],
            [0.51, 0.500001],
            [0, 0],
            [-0.01, 1],
            [float("nan"), 0.5],
            [float("inf"), 0],
            [True, 0],
            [],
        ):
            with self.assertRaises(ValueError):
                distribution(values, RESPONSE_SUM_TOLERANCE)

    def test_gold_stays_strict(self):
        with self.assertRaises(ValueError):
            distribution([0.49, 0.5])

    def test_choice_and_score_metadata(self):
        for kind, criteria, label in [
            ("choice", {"a": "A", "b": "B"}, "b"),
            ("score", ["A", "B"], 1),
        ]:
            keys = ["a", "b"] if kind == "choice" else ["0", "1"]
            ans = {"type": kind, "probabilities": dict(zip(keys, [0.49, 0.5]))}
            if kind == "choice":
                ans["choice"] = "b"
            r = score_answer(
                {"type": kind, "criteria": criteria},
                {"type": kind, "label": label},
                ans,
            )
            self.assertTrue(r["valid"])
            self.assertTrue(r["correct"])
            self.assertTrue(r["normalization"]["exceeds_previous_tolerance"])
            self.assertEqual(r["normalization"]["raw_probabilities"], [0.49, 0.5])
            self.assertAlmostEqual(r["confidence"], 0.5 / 0.99)
            self.assertAlmostEqual(r["nll"], -math.log(0.5 / 0.99))
            self.assertEqual(ans["probabilities"][keys[1]], 0.5)
