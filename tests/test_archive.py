import json
from pathlib import Path
import tempfile
import unittest
from decision_benchmark.archive import verify_files
from decision_benchmark.encoding import sha256
from decision_benchmark.verification import compare_values


class ArchiveMutationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        data = self.root / "data"
        data.mkdir()
        self.shard = data / "sample.json"
        self.shard.write_text('{"gold":1}')
        manifest = {
            "files": {
                "data/sample.json": {
                    "bytes": self.shard.stat().st_size,
                    "sha256": sha256(self.shard.read_bytes()),
                }
            }
        }
        (data / "manifest.json").write_text(json.dumps(manifest))

    def test_changed_byte_or_gold_fails(self):
        verify_files(self.root)
        self.shard.write_text('{"gold":0}')
        with self.assertRaises(ValueError):
            verify_files(self.root)

    def test_missing_shard_fails(self):
        self.shard.unlink()
        with self.assertRaises(ValueError):
            verify_files(self.root)

    def test_extra_nested_manifest_fails(self):
        nested = self.root / "data/extra"
        nested.mkdir()
        (nested / "manifest.json").write_text("{}")
        with self.assertRaises(ValueError):
            verify_files(self.root)

    def test_reference_difference_fails(self):
        with self.assertRaises(ValueError):
            compare_values({"correct": 99}, {"correct": 100})
        with self.assertRaises(ValueError):
            compare_values({"cost": 0.9}, {"cost": 1.0})
