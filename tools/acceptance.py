"""Offline acceptance in any extracted bundle: sockets denied, full raw scorer replay."""

import argparse
import importlib.util
import json
from pathlib import Path
import socket
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def denied(*args, **kwargs):
    raise RuntimeError("Network access denied during offline acceptance")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--reproduce", action="store_true")
    args = parser.parse_args()
    socket.socket.connect = denied
    socket.socket.connect_ex = denied
    socket.create_connection = denied
    from decision_benchmark.archive import (
        verify_archive,
        load_corpus,
        load_routes,
        responses,
    )
    from decision_benchmark.scoring import score_response
    from decision_benchmark.encoding import write_json
    from decision_benchmark.verification import check_results

    integrity = verify_archive(ROOT)
    tests = unittest.defaultTestLoader.discover(
        str(ROOT / "tests"), pattern="test_*.py"
    )
    result = unittest.TextTestRunner(verbosity=1).run(tests)
    if not result.wasSuccessful():
        raise SystemExit(1)
    spec = importlib.util.spec_from_file_location(
        "reference_scorer", ROOT / "tests/fixtures/scorer_v1_2.py"
    )
    oracle = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(oracle)
    cases = load_corpus(ROOT)
    routes = {r["model"]: r for r in load_routes(ROOT)}
    count = decisions = 0
    for row in responses(ROOT):
        key = row["key"]
        case = cases[key["language"], key["case"]]
        route = routes[key["model"]]
        actual = score_response(case, row["raw"], route)
        expected = oracle.score_response(case, row["raw"], route)
        if actual != expected:
            raise ValueError("Scorer differs from pinned 1.2.0 oracle")
        count += 1
        decisions += len(actual["results"])
    args.output.mkdir(parents=True, exist_ok=True)
    generated = args.output / "reproduced"
    if args.reproduce:
        from decision_benchmark.analysis import replay

        replay(ROOT, generated)
    comparison = check_results(ROOT, generated if args.reproduce else ROOT / "results")
    report = {
        "integrity": integrity,
        "tests": result.testsRun,
        "oracle_requests": count,
        "oracle_decisions": decisions,
        "comparison": comparison,
        "network": "denied by socket guard",
    }
    write_json(args.output / "acceptance.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
