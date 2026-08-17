# -*- coding: utf-8 -*-
"""Build a canonical Source 1 skeleton manifest and provisional C2 bind plan."""

from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any


REQUIRED_BONES = [
    "v_weapon",
    "v_weapon.M4A1_s_Parent",
    "v_weapon.M4A1_Clip",
    "v_weapon.M4A1_Bolt",
    "v_weapon.M4A1_Trigger",
    "v_weapon.M4A1_Silencer",
    "v_weapon.flash",
    "v_weapon.shelleject",
]


def scalar(value: str) -> Any:
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


def parse_mesh_map(path: Path) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if raw.startswith("  - mesh:"):
            current = {"mesh": scalar(raw.split(":", 1)[1])}
            entries.append(current)
            continue
        if current is None:
            continue
        if raw.startswith("    ") and not raw.startswith("      ") and ":" in raw:
            key, value = raw.strip().split(":", 1)
            current[key] = scalar(value)
    return entries


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-report", type=Path, required=True)
    parser.add_argument("--mesh-map", type=Path, required=True)
    parser.add_argument("--skeleton-output", type=Path, required=True)
    parser.add_argument("--binding-output", type=Path, required=True)
    args = parser.parse_args()

    reference_path = args.reference_report.resolve()
    map_path = args.mesh_map.resolve()
    reference = json.loads(reference_path.read_text(encoding="utf-8"))
    hierarchy = reference.get("bones", {}).get("hierarchy", [])
    names = [bone.get("name") for bone in hierarchy]
    failures: list[str] = []
    if len(names) != reference.get("bones", {}).get("count"):
        failures.append("reference bone count does not match hierarchy length")
    if len(set(names)) != len(names):
        failures.append("reference hierarchy contains duplicate bone names")
    for required in REQUIRED_BONES:
        if required not in names:
            failures.append(f"required mechanical bone missing: {required}")

    skeleton = {
        "schema": "cf2.m4a1_s.c2-canonical-skeleton.v1",
        "source_report": str(reference_path),
        "source_report_sha256": hashlib.sha256(reference_path.read_bytes()).hexdigest(),
        "model": reference.get("target", {}).get("internal_modelname"),
        "bone_count": len(hierarchy),
        "required_mechanical_bones": REQUIRED_BONES,
        "hierarchy": hierarchy,
        "status": "canonical_reference_locked" if not failures else "invalid",
        "failures": failures,
    }

    entries = parse_mesh_map(map_path)
    bindings: list[dict[str, Any]] = []
    for entry in entries:
        if entry.get("export") is not True:
            bindings.append(
                {
                    "mesh": entry.get("mesh"),
                    "export": False,
                    "bodygroup": entry.get("bodygroup"),
                    "binding_status": "excluded_official_source1_arms",
                }
            )
            continue
        visual_candidate = entry.get("visual_candidate_bone")
        provisional = entry.get("source_bone")
        bindings.append(
            {
                "mesh": entry.get("mesh"),
                "export": True,
                "role": entry.get("role"),
                "binding_mode": "rigid_single_bone_candidate",
                "temporary_bone": provisional,
                "candidate_bone": visual_candidate or provisional,
                "candidate_confidence": "visual_review" if visual_candidate else "parent_fallback",
                "weight_policy": "100_percent_single_bone_after_C2_validation",
                "finalized": False,
            }
        )

    binding_plan = {
        "schema": "cf2.m4a1_s.c2-binding-plan.v1",
        "status": "provisional_candidates",
        "skeleton_manifest": str(args.skeleton_output.resolve()),
        "mesh_map": str(map_path),
        "mesh_map_sha256": hashlib.sha256(map_path.read_bytes()).hexdigest(),
        "rules": {
            "weapon_body": "v_weapon.M4A1_s_Parent",
            "magazine_candidate": "v_weapon.M4A1_Clip",
            "bolt_candidate": "v_weapon.M4A1_Bolt",
            "unresolved_components": "keep v_weapon.M4A1_s_Parent until animation confirms a dedicated bone",
            "arms": "excluded from default path; use official Source 1 arms/gloves",
        },
        "bindings": bindings,
        "finalization_blockers": [
            "CF animation clips are not decoded",
            "M4A1S_BornBeast03-08 semantic roles are unresolved open fragments",
            "candidate bone motion has not been validated against an exported animation",
        ],
    }

    for output, payload in ((args.skeleton_output, skeleton), (args.binding_output, binding_plan)):
        output = output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = {
        "skeleton_status": skeleton["status"],
        "bone_count": len(hierarchy),
        "required_bones": len(REQUIRED_BONES),
        "binding_count": len(bindings),
        "exported_bindings": sum(1 for item in bindings if item.get("export") is True),
        "excluded_bindings": sum(1 for item in bindings if item.get("export") is False),
        "failures": failures,
        "skeleton_output": str(args.skeleton_output.resolve()),
        "binding_output": str(args.binding_output.resolve()),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
