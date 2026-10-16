"""Scan expanded package content; report filenames only, never matched values."""

import argparse
import base64
import gzip
import json
from pathlib import Path
import re

PATTERNS = {
    "credential": re.compile(r"sk-(?:or-|ant-)?[A-Za-z0-9_-]{12,}"),
    "bearer_value": re.compile(r"Bearer\s+[A-Za-z0-9_.-]{16,}"),
    "home_path": re.compile(r"/Users/[A-Za-z0-9_.-]+/"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    "account_identifier": re.compile(
        r'"(?:guardrail_id|budget_id|user_id)"\s*:\s*"[^"<>]+"'
    ),
}


def scan(root):
    findings = []
    files = 0
    decoded = 0
    for path in Path(root).rglob("*"):
        if not path.is_file() or "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        files += 1
        data = (
            gzip.decompress(path.read_bytes())
            if path.suffix == ".gz"
            else path.read_bytes()
        )
        text = data.decode("utf-8", "replace")
        for name, pattern in PATTERNS.items():
            if pattern.search(text):
                findings.append({"path": str(path.relative_to(root)), "kind": name})
        if path.name.endswith(".jsonl.gz"):
            for line in text.splitlines():
                row = json.loads(line)
                raw = row.get("raw", {})
                if raw.get("response_base64"):
                    decoded += 1
                    body = base64.b64decode(
                        raw["response_base64"], validate=True
                    ).decode("utf-8", "replace")
                    for name, pattern in PATTERNS.items():
                        if pattern.search(body):
                            findings.append(
                                {
                                    "path": str(path.relative_to(root)),
                                    "kind": "decoded_" + name,
                                }
                            )
    return {
        "files_scanned": files,
        "decoded_base64_bodies": decoded,
        "findings": findings,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", type=Path)
    args = parser.parse_args()
    result = scan(args.root)
    print(json.dumps(result, indent=2))
    raise SystemExit(bool(result["findings"]))
