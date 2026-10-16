"""Offline report for any prepared new run, including partial execution."""

from collections import Counter, defaultdict
from ..confidence import choose_threshold
from ..scoring import score_response
from .execution import task_state
from .journal import RunJournal


def report_run(directory):
    journal = RunJournal(directory)
    with journal.lock():
        plan = journal.load_plan()
        states = Counter()
        groups = defaultdict(list)
        accepted_costs = []
        for task in plan["tasks"]:
            state = task_state(journal, task)
            states[state] += 1
            if state != "accepted":
                continue
            for attempt in journal.attempts(task):
                path = attempt / "response.json"
                if not path.exists():
                    continue
                scored = score_response(
                    task["case"], journal.read_record(path), task["route"]
                )
                if not scored["complete"]:
                    continue
                usage = scored.get("usage") or {}
                if isinstance(usage.get("cost"), (int, float)):
                    accepted_costs.append(usage["cost"])
                for question, result in scored["results"].items():
                    key = (
                        task["key"]["model"],
                        task["key"]["language"],
                        task["case"]["suite"],
                        question,
                    )
                    groups[key].append(result)
                break
        summaries = []
        for (model, language, suite, question), rows in sorted(groups.items()):
            native = [r for r in rows if r.get("native_confidence") is not None]
            point = (
                choose_threshold(
                    [[r["native_confidence"], 1, int(r["correct"])] for r in native]
                )
                if native
                else None
            )
            summaries.append(
                {
                    "model": model,
                    "language": language,
                    "suite": suite,
                    "question": question,
                    "valid_decisions": len(rows),
                    "valid_only_accuracy": sum(r["correct"] for r in rows) / len(rows),
                    "native_confidence_decisions": len(native),
                    "operating_point": point.record() if point else None,
                    "U_at_J": (
                        float(point.utility)
                        if point and point.utility is not None
                        else None
                    ),
                }
            )
        return {
            "complete": states["accepted"] == len(plan["tasks"]),
            "states": dict(states),
            "accepted_reported_cost_usd": sum(accepted_costs),
            "cost_coverage": len(accepted_costs),
            "groups": summaries,
            "threshold_evaluation": "Descriptive: selected and evaluated on these same observations",
        }
