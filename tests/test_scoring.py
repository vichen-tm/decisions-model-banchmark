import copy, json, math, tempfile, unittest
from pathlib import Path
from decision_benchmark.scoring import *
from decision_benchmark.archive import PACKAGE_ROOT, load_corpus, load_routes

ROOT = PACKAGE_ROOT


def load_frozen():
    return [
        c for (language, _), c in load_corpus().items() if language == "en"
    ], load_routes()


class ContractTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.cases, cls.routes = load_frozen()

    def test_full_inventory(self):
        self.assertEqual(len(self.cases), 2050)
        self.assertEqual(sum((len(c["gold"]) for c in self.cases)), 3650)
        self.assertEqual(
            Counter(
                (
                    q["type"]
                    for c in self.cases
                    for q in c["request"]["questions"].values()
                )
            ),
            {"choice": 1650, "noul": 1000, "score": 1000},
        )

    def test_all_cases_validate_and_payload_has_no_gold(self):
        for c in self.cases:
            self.assertTrue(validate_case(c))
            body = request_body(c, self.routes[0])
            self.assertEqual(set(body), {"model", "provider", "state", "questions"})
            self.assertEqual(set(body["state"]), {"text"})

    def test_request_copy_preserves_order_and_isolation(self):
        c = next((c for c in self.cases if c["suite"] == "banking77"))
        b = request_body(c, self.routes[0])
        self.assertEqual(
            list(b["questions"]["intent"]["criteria"]),
            list(c["request"]["questions"]["intent"]["criteria"]),
        )
        b["questions"].clear()
        self.assertTrue(c["request"]["questions"])

    def test_noul_boundary(self):
        q = {"type": "noul"}
        g = {"label": 1}
        for p, want in [(0, 0), (0.499999, 0), (0.5, 1), (1, 1)]:
            self.assertEqual(
                score_answer(q, g, {"type": "noul", "noul": p})["prediction"], want
            )

    def test_noul_invalid(self):
        for p in [-0.1, 1.1, "0.5", True, None, float("nan"), float("inf")]:
            self.assertFalse(
                score_answer(
                    {"type": "noul"}, {"label": 1}, {"type": "noul", "noul": p}
                )["valid"]
            )

    def test_choice_native_not_dictionary_order(self):
        r = score_answer(
            {"type": "choice", "criteria": {"b": "B", "a": "A"}},
            {"label": "a"},
            {"type": "choice", "choice": "a", "probabilities": {"a": 0.8, "b": 0.2}},
        )
        self.assertTrue(r["correct"])
        self.assertEqual(r["confidence"], 0.8)

    def test_choice_without_probability_not_fabricated(self):
        r = score_answer(
            {"type": "choice", "criteria": {"a": "A", "b": "B"}},
            {"label": "a"},
            {"type": "choice", "choice": "a"},
        )
        self.assertTrue(r["valid"])
        self.assertIsNone(r["probabilities"])
        self.assertNotIn("brier", r)

    def test_choice_conflict_and_partial_distribution(self):
        q = {"type": "choice", "criteria": {"a": "A", "b": "B"}}
        for probs in [{"a": 1}, {"a": 0.7, "b": 0.7}, {"a": float("nan"), "b": 1}]:
            self.assertFalse(
                score_answer(
                    q,
                    {"label": "a"},
                    {"type": "choice", "choice": "a", "probabilities": probs},
                )["valid"]
            )

    def test_choice_conflict_keeps_native_answer_and_metrics(self):
        q = {"type": "choice", "criteria": {"a": "A", "b": "B"}}
        a = {"type": "choice", "choice": "a", "probabilities": {"a": 0.1, "b": 0.9}}
        for gold, correct in [("a", True), ("b", False)]:
            r = score_answer(q, {"label": gold}, a)
            self.assertTrue(r["valid"])
            self.assertEqual(r["correct"], correct)
            self.assertEqual(r["prediction"], "a")
            self.assertEqual(r["confidence"], 0.1)
            self.assertEqual(r["choice_probability_conflict"]["argmax"], ["b"])
            self.assertEqual(r["probabilities"], [0.1, 0.9])
            self.assertAlmostEqual(r["nll"], -math.log(0.1 if correct else 0.9))
        self.assertEqual(a["choice"], "a")

    def test_score_mode_not_rounded_expectation(self):
        q = {"type": "score", "criteria": ["low", "mid", "high"]}
        r = score_answer(
            q,
            {"label": 0},
            {
                "type": "score",
                "score": 1.05,
                "probabilities": {"2": 0.4, "0": 0.45, "1": 0.15},
            },
        )
        self.assertTrue(r["correct"])
        self.assertEqual(r["prediction"], 0)
        self.assertAlmostEqual(r["expected_index"], 0.95)
        self.assertAlmostEqual(r["score_mae"], 0.95)

    def test_score_zero_based_and_ties(self):
        q = {"type": "score", "criteria": ["low", "high"]}
        r = score_answer(
            q, {"label": 0}, {"type": "score", "probabilities": {"0": 0.5, "1": 0.5}}
        )
        self.assertEqual(r["prediction"], 0)
        for p in [{"1": 0.5, "2": 0.5}, {"0": 1}]:
            self.assertFalse(
                score_answer(q, {"label": 0}, {"type": "score", "probabilities": p})[
                    "valid"
                ]
            )

    def test_score_no_rounding_fallback(self):
        self.assertFalse(
            score_answer(
                {"type": "score", "criteria": ["a", "b"]},
                {"label": 1},
                {"type": "score", "score": 1},
            )["valid"]
        )

    def test_soft_gold_and_metrics(self):
        r = score_answer(
            {"type": "choice", "criteria": {"a": "A", "b": "B"}},
            {"label": "a", "dist": [0.75, 0.25]},
            {"type": "choice", "choice": "a", "probabilities": {"a": 0.75, "b": 0.25}},
        )
        self.assertAlmostEqual(r["soft_kl"], 0)
        self.assertEqual(r["soft_gold_at_prediction"], 0.75)
        self.assertAlmostEqual(r["brier"], 0.125)
        self.assertAlmostEqual(r["nll"], -math.log(0.75))

    def test_missing_http_provider_and_question(self):
        c = self.cases[0]
        route = self.routes[0]
        for raw in [
            None,
            {"status": 429},
            {"status": 200, "response_text": "{"},
            {
                "status": 200,
                "response_text": json.dumps(
                    {
                        "provider": "wrong",
                        "model": route["expected_version"],
                        "answers": {},
                    }
                ),
            },
        ]:
            self.assertFalse(score_response(c, raw, route)["complete"])

    def test_all_gold_perfect_through_actual_parser(self):
        route = self.routes[0]
        scored = []
        for c in self.cases:
            answers = {}
            for qid, q in c["request"]["questions"].items():
                g = c["gold"][qid]
                keys = options(q)
                a = {"type": q["type"]}
                if q["type"] == "noul":
                    a["noul"] = float(g["label"])
                else:
                    key = g["label"] if q["type"] == "choice" else str(g["label"])
                    a["probabilities"] = {k: float(k == key) for k in keys}
                    if q["type"] == "choice":
                        a["choice"] = key
                answers[qid] = a
            raw = {
                "status": 200,
                "response_text": json.dumps(
                    {
                        "provider": route["expected_provider"],
                        "model": route["expected_version"],
                        "answers": answers,
                    }
                ),
            }
            scored.append(score_response(c, raw, route))
        self.assertTrue(all(row["complete"] for row in scored))
        self.assertTrue(
            all(
                answer["correct"]
                for row in scored
                for answer in row["results"].values()
            )
        )
