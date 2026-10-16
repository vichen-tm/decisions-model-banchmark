"""Command line: archive checks and offline reconstruction precede live execution."""

import argparse
import json
from pathlib import Path
from .archive import PACKAGE_ROOT, verify_archive


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--root", type=Path, default=PACKAGE_ROOT, help="Portable bundle root"
    )
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser(
        "verify-data", help="Check shards, hashes and request/response/corpus joins"
    )
    replay = commands.add_parser(
        "reproduce", help="Recompute all results from raw responses without API calls"
    )
    replay.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser(
        "verify-results", help="Compare regenerated results with golden references"
    )
    verify.add_argument("--output", type=Path, required=True)
    simulation = commands.add_parser(
        "simulate", help="Run all frozen counterexamples and noise/repeat diagnostics"
    )
    simulation.add_argument("--output", type=Path, required=True)
    simulation.add_argument("--repetitions", type=int, default=400)
    from .runner.cli import add_runner_commands

    add_runner_commands(commands)
    args = parser.parse_args()
    if args.command == "verify-data":
        result = verify_archive(args.root)
    elif args.command == "reproduce":
        from .analysis import replay as rebuild

        result = rebuild(args.root, args.output)
    elif args.command == "verify-results":
        from .verification import check_results

        result = check_results(args.root, args.output)
    elif args.command == "simulate":
        from .simulations import simulate

        result = simulate(args.root, args.output, args.repetitions)
    else:
        from .runner.cli import execute_runner_command

        result = execute_runner_command(args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("status") == "incomplete":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
