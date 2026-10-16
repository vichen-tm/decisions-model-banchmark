"""One command: validate data, prepare, send through OpenRouter, write report."""

import argparse
import json
import os
from pathlib import Path
from ..archive import PACKAGE_ROOT, load_routes
from ..encoding import write_json
from .dataset import load_dataset
from .execution import prepare, run
from .report import report_run
from .transport import OpenRouterTransport


def parser():
    result = argparse.ArgumentParser(description=__doc__)
    result.add_argument(
        "--output", type=Path, required=True, help="New empty run directory"
    )
    result.add_argument(
        "--dataset", type=Path, help="Custom JSONL or JSONL.gz; default: bundled corpus"
    )
    result.add_argument("--model", action="append", help="Model ID; can be repeated")
    result.add_argument("--all-models", action="store_true")
    result.add_argument("--language", action="append")
    result.add_argument("--suite", action="append")
    result.add_argument("--repeats", type=int)
    result.add_argument(
        "--campaign",
        action="store_true",
        help="All bundled models/cases: five EN passes, one for other languages",
    )
    result.add_argument(
        "--concurrency", type=int, default=1, help="Shared limit per provider"
    )
    result.add_argument(
        "--routes", type=Path, help="Pinned model/provider/version configuration"
    )
    result.add_argument(
        "--send",
        action="store_true",
        help="Send paid API calls; otherwise only prepare",
    )
    result.add_argument("--allow-env-proxy", action="store_true")
    return result


def execute(args, root=PACKAGE_ROOT, transport_factory=OpenRouterTransport):
    root, target = Path(root).resolve(), args.output.resolve()
    if target == root or any(
        (root / part) == target or (root / part) in target.parents
        for part in (
            "data",
            "tests",
            "results",
            "docs",
            "tools",
            "decision_benchmark",
            "examples",
        )
    ):
        raise ValueError("Use an output directory outside the package inputs")
    if args.campaign and any(
        (
            args.dataset,
            args.model,
            args.language,
            args.suite,
            args.repeats is not None,
            args.all_models,
        )
    ):
        raise ValueError(
            "--campaign cannot be combined with dataset/model/language/suite/repeats selection"
        )
    if args.model and args.all_models:
        raise ValueError("Choose --model or --all-models")
    routes = json.loads(args.routes.read_text()) if args.routes else load_routes(root)
    models = (
        [route["model"] for route in routes]
        if args.campaign or args.all_models
        else args.model
    )
    if not models:
        raise ValueError("Select --model, --all-models or --campaign")
    cases = load_dataset(args.dataset) if args.dataset else None
    languages = args.language or (
        sorted({key[0] for key in cases}) if cases else ["en"]
    )
    repeat_by_language = None
    if args.campaign:
        languages = ["en", "uk", "ar", "es", "zh"]
        repeat_by_language = {"en": 5}
    if args.send and not os.environ.get("OPENROUTER_API_KEY"):
        raise ValueError("Set OPENROUTER_API_KEY before --send")
    prepared = prepare(
        root,
        args.output,
        models,
        languages,
        args.suite,
        args.repeats if args.repeats is not None else 1,
        args.concurrency,
        routes,
        cases,
        repeat_by_language,
    )
    print(json.dumps({"prepared": prepared, "sending": args.send}), flush=True)
    if not args.send:
        return prepared
    transport = transport_factory(
        os.environ["OPENROUTER_API_KEY"], args.allow_env_proxy
    )
    outcome = run(args.output, transport)
    report = report_run(args.output)
    write_json(args.output / "report.json", report)
    return {**outcome, "report": str(args.output / "report.json")}


def main():
    args = parser().parse_args()
    try:
        result = execute(args)
    except (ValueError, OSError) as error:
        raise SystemExit(str(error)) from None
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") == "incomplete":
        raise SystemExit(2)
