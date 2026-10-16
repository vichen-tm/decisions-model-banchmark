"""The only command path constructing a live provider transport."""

import json
import os
from pathlib import Path


def add_runner_commands(commands):
    prepare = commands.add_parser("prepare", help="Freeze a new run; sends nothing")
    prepare.add_argument("--run-dir", type=Path, required=True)
    prepare.add_argument("--model", action="append", required=True)
    prepare.add_argument("--language", action="append", default=None)
    prepare.add_argument("--suite", action="append", default=None)
    prepare.add_argument("--repeats", type=int, default=1)
    prepare.add_argument(
        "--concurrency", type=int, default=1, help="Per provider, shared across models"
    )
    prepare.add_argument("--routes", type=Path, help="New pinned routes configuration")
    run = commands.add_parser("run", help="Resume prepared run; --send required")
    run.add_argument("--run-dir", type=Path, required=True)
    run.add_argument("--send", action="store_true")
    run.add_argument("--retry-technical", action="store_true")
    run.add_argument("--allow-env-proxy", action="store_true")
    report = commands.add_parser("report-run", help="Offline summary of a prepared run")
    report.add_argument("--run-dir", type=Path, required=True)
    resolve = commands.add_parser(
        "resolve-unknown", help="Manually resolve uncertain execution"
    )
    resolve.add_argument("--run-dir", type=Path, required=True)
    resolve.add_argument("--task-id", required=True)
    resolve.add_argument("--action", choices=("retry", "abandon"), required=True)

    failed = commands.add_parser(
        "resolve-failed",
        help="Explicit decision after repairing a failed run configuration",
    )
    failed.add_argument("--run-dir", type=Path, required=True)
    failed.add_argument("--task-id", required=True)
    failed.add_argument("--action", choices=("retry", "abandon"), required=True)


def execute_runner_command(args):
    from .execution import prepare, run, resolve_unknown

    if args.command == "prepare":
        root, target = args.root.resolve(), args.run_dir.resolve()
        protected = [root / name for name in (
            "data", "tests", "results", "docs", "tools", "decision_benchmark", "examples"
        )]
        if target == root or any(p == target or p in target.parents for p in protected):
            raise ValueError("New runs must be outside the package inputs")
        routes = json.loads(args.routes.read_text()) if args.routes else None
        return prepare(
            args.root,
            args.run_dir,
            args.model,
            args.language or ["en"],
            args.suite,
            args.repeats,
            args.concurrency,
            routes,
        )
    if args.command == "report-run":
        from .report import report_run

        return report_run(args.run_dir)
    if args.command == "resolve-unknown":
        return resolve_unknown(args.run_dir, args.task_id, args.action)
    if args.command == "resolve-failed":
        from .execution import resolve_attempt

        return resolve_attempt(args.run_dir, args.task_id, args.action, "failed")
    if args.command != "run":
        raise ValueError("Unknown runner command")
    if not args.send:
        raise ValueError("No requests sent: explicit --send required")
    from .transport import OpenRouterTransport

    return run(
        args.run_dir,
        OpenRouterTransport(os.environ.get("OPENROUTER_API_KEY"), args.allow_env_proxy),
        args.retry_technical,
    )
