# -*- coding: utf-8 -*-
"""Validate the C1 CF mesh split map against B3 and the official reference."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any


def field(record: dict[str, Any], name: str) -> Any:
    if name in record:
        return record[name]
    pascal = name[0].upper() + name[1:]
    if pascal in record:
        return record[pascal]
    return record.get(name.replace("_", ""))


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value == "null":
        return None
    if value == "true":
        return True
    if value == "false":
        return False
    return value


def parse_mesh_entries(path: Path) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    top: dict[str, Any] = {}
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if match := re.match(r"^\s{2}- mesh:\s*(.+?)\s*$", raw):
            current = {"mesh": parse_scalar(match.group(1))}
            entries.append(current)
            continue
        if current is not None:
            match = re.match(r"^\s{4}([A-Za-z_]+):\s*(.*?)\s*$", raw)
            if match:
                current[match.group(1)] = parse_scalar(match.group(2))
                continue
        match = re.match(r"^([A-Za-z_]+):\s*(.*?)\s*$", raw)
        if match:
            top[match.group(1)] = parse_scalar(match.group(2))
    return top, entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--b3-report", type=Path, required=True)
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    map_path = args.map.resolve()
    b3_report = json.loads(args.b3_report.resolve().read_text(encoding="utf-8"))
    reference_report = json.loads(args.reference_report.resolve().read_text(encoding="utf-8"))
    top, entries = parse_mesh_entries(map_path)
    report_meshes = field(b3_report, "meshes") or []
    report_by_name = {field(mesh, "meshName"): mesh for mesh in report_meshes}
    entry_by_name = {entry.get("mesh"): entry for entry in entries}
    failures: list[str] = []

    if top.get("status") != "provisional_c1":
        failures.append("map status must remain provisional_c1 until semantic part review is complete")
    if len(entries) != len(report_meshes):
        failures.append(f"map entries {len(entries)} != B3 mesh count {len(report_meshes)}")
    if set(entry_by_name) != set(report_by_name):
        failures.append("map mesh names do not exactly match B3 report")

    official_materials = reference_report.get("materials", {}).get("smd_materials", [])
    if "rif_m4a1_s" not in official_materials:
        failures.append("official reference report does not contain rif_m4a1_s material")

    for name, entry in entry_by_name.items():
        if name not in report_by_name:
            continue
        expected_group = field(report_by_name[name], "groupName")
        if entry.get("group") != expected_group:
            failures.append(f"{name}: group does not match B3 report")
        for required in ("role", "export", "source_bone", "source_material_slot", "binding_status", "review_required"):
            if required not in entry:
                failures.append(f"{name}: missing {required}")
        if name in {"Fview-hand2", "Fview-arm2"}:
            if entry.get("export") is not False or entry.get("bodygroup") != "cf_arms_optional":
                failures.append(f"{name}: CF arm/hand must be excluded into cf_arms_optional")
            if entry.get("source_bone") is not None:
                failures.append(f"{name}: excluded CF arm/hand must not claim a Source bone")
        else:
            if entry.get("export") is not True:
                failures.append(f"{name}: weapon mesh must be exported")
            if entry.get("source_bone") != "v_weapon.M4A1_s_Parent":
                failures.append(f"{name}: missing provisional rigid bone candidate")
            if entry.get("source_material_slot") != "rif_m4a1_s":
                failures.append(f"{name}: material slot must use official rif_m4a1_s")
            if entry.get("review_required") is not True:
                failures.append(f"{name}: semantic review must remain required before C2")

    output = args.output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)
    result = {
        "schema": "cf2.m4a1_s.c1-mesh-map-validation.v1",
        "map": str(map_path),
        "map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest(),
        "b3_report": str(args.b3_report.resolve()),
        "reference_report": str(args.reference_report.resolve()),
        "passed": not failures,
        "mesh_count": len(entries),
        "cf_arm_meshes_excluded": sorted(name for name in ("Fview-hand2", "Fview-arm2") if entry_by_name.get(name, {}).get("export") is False),
        "weapon_meshes_exported": sum(1 for entry in entries if entry.get("export") is True),
        "semantic_part_review_pending": sum(1 for entry in entries if entry.get("review_required") is True),
        "official_material": "rif_m4a1_s" if "rif_m4a1_s" in official_materials else None,
        "failures": failures,
    }
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
