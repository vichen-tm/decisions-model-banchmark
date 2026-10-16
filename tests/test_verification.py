import json
from pathlib import Path
import shutil
import tempfile
import unittest
from decision_benchmark.encoding import sha256
from decision_benchmark.verification import check_results
from decision_benchmark.analysis import replay

ROOT = Path(__file__).resolve().parents[1]


class VerificationTests(unittest.TestCase):
    def test_missing_or_duplicate_rating_row_fails_even_with_new_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            for name in json.loads((ROOT / "results/complete.json").read_text())[
                "files"
            ]:
                # Large immutable outputs can be hard-linked; only rating is edited.
                if name == "rating.json":
                    shutil.copy2(ROOT / "results" / name, output / name)
                else:
                    (output / name).hardlink_to(ROOT / "results" / name)
            completion = json.loads((ROOT / "results/complete.json").read_text())
            original = json.loads((output / "rating.json").read_text())
            for mutation in ("missing", "duplicate"):
                rating = json.loads(json.dumps(original))
                if mutation == "missing":
                    del rating["overall"][0]["scores"]
                else:
                    rating["overall"].append(rating["overall"][0])
                (output / "rating.json").write_text(json.dumps(rating))
                completion["files"]["rating.json"] = sha256(
                    (output / "rating.json").read_bytes()
                )
                (output / "complete.json").write_text(json.dumps(completion))
                with self.assertRaises((ValueError, KeyError)):
                    check_results(ROOT, output)

    def test_replay_refuses_control_data_and_existing_output(self):
        for target in (ROOT / "tests/golden", ROOT / "results", ROOT / "data"):
            with self.assertRaises(ValueError):
                replay(ROOT, target)
