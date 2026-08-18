#!/usr/bin/env python3
"""Validate a D2 preflight report and return nonzero when the selected profile is blocked."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--profile", choices=("r1_static", "r2_full"), required=True)
    args = parser.parse_args()
    report_path = args.report.resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    failures = []
    if report.get("schema") != "cf2.m4a1_s.d2-preflight.v1":
        failures.append("unexpected D2 report schema")
    for label, record in report.get("inputs", {}).items():
        path = Path(record.get("path", ""))
        if not path.is_file():
            failures.append(f"missing input artifact: {label}")
        elif sha256(path) != record.get("sha256"):
            failures.append(f"input SHA-256 changed after D2 preflight: {label}")
    scene = Path(report.get("scene", ""))
    if not scene.is_file() or sha256(scene) != report.get("scene_sha256"):
        failures.append("D1 blend is missing or changed after D2 preflight")
    profile = report.get("profiles", {}).get(args.profile, {})
    failures.extend(profile.get("failures", []))
    result = {
        "schema": "cf2.m4a1_s.d2-validation.v1",
        "profile": args.profile,
        "passed": profile.get("passed") is True and not failures,
        "reported_result": profile.get("result"),
        "failures": failures,
        "advisories": profile.get("advisories", []),
    }
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
