import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from decision_benchmark.runner.benchmark import parser, execute
from decision_benchmark.runner.dataset import load_dataset
from decision_benchmark.archive import PACKAGE_ROOT
from test_runner import FakeTransport, task


class SingleCommandTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.dataset = self.directory / "own.jsonl"
        self.dataset.write_text(json.dumps(task()["case"]) + "\n")
        self.routes = self.directory / "routes.json"
        self.routes.write_text(json.dumps([task()["route"]]))

    def args(self, *extra):
        return parser().parse_args(
            [
                "--output",
                str(self.directory / "run"),
                "--dataset",
                str(self.dataset),
                "--model",
                "m",
                "--routes",
                str(self.routes),
                *extra,
            ]
        )

    def test_custom_data_full_flow_and_report(self):
        transport = FakeTransport()
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-credential"}):
            result = execute(
                self.args("--send"), transport_factory=lambda *a: transport
            )
        report = json.loads(Path(result["report"]).read_text())
        self.assertEqual(result["status"], "complete")
        self.assertEqual(transport.calls, 1)
        self.assertEqual(report["groups"][0]["valid_only_accuracy"], 1)
        self.assertNotIn(
            "test-credential", (self.directory / "run/plan.json").read_text()
        )

    def test_without_send_never_constructs_transport(self):
        def forbidden(*args):
            self.fail("Dry run constructed a live transport")

        self.assertEqual(execute(self.args(), transport_factory=forbidden)["sent"], 0)

    def test_invalid_and_duplicate_data_rejected_before_plan(self):
        line = self.dataset.read_text()
        self.dataset.write_text(line * 2)
        with self.assertRaises(ValueError):
            execute(self.args())
        self.assertFalse((self.directory / "run").exists())
        self.dataset.write_text('{"id":"1"}\n')
        with self.assertRaises(ValueError):
            load_dataset(self.dataset)

    def test_builtin_same_executor_without_api(self):
        args = parser().parse_args(
            [
                "--output",
                str(self.directory / "builtin"),
                "--model",
                "liquid/d1",
                "--suite",
                "ag_news",
            ]
        )
        result = execute(args)
        self.assertEqual(result["prepared_requests"], 200)
        self.assertEqual(result["sent"], 0)

    def test_full_campaign_has_original_repeat_counts(self):
        args = parser().parse_args(
            ["--output", str(self.directory / "full"), "--campaign"]
        )
        captured = {}

        def capture(
            root,
            directory,
            models,
            languages,
            suites,
            repeats,
            concurrency,
            routes,
            cases,
            repeat_by_language,
        ):
            captured.update(
                models=models,
                languages=languages,
                repeats=repeats,
                repeat_by_language=repeat_by_language,
            )
            return {"sent": 0}

        with patch("decision_benchmark.runner.benchmark.prepare", side_effect=capture):
            execute(args)
        self.assertEqual(len(captured["models"]), 10)
        self.assertEqual(len(captured["languages"]), 5)
        self.assertEqual(captured["repeat_by_language"], {"en": 5})
        self.assertEqual(captured["repeats"], 1)

    def test_incomplete_send_is_reported(self):
        with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-credential"}):
            result = execute(
                self.args("--send"), transport_factory=lambda *a: FakeTransport([503])
            )
        self.assertEqual(result["status"], "incomplete")
        self.assertFalse(json.loads(Path(result["report"]).read_text())["complete"])

    def test_missing_key_sends_nothing_and_writes_no_plan(self):
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(ValueError):
                execute(self.args("--send"))
        self.assertFalse((self.directory / "run").exists())
