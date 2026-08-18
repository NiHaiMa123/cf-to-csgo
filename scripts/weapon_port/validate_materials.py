# -*- coding: utf-8 -*-
"""Validate the Source 1 SMD -> QC -> VMT -> VTF material reference closure."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys


def smd_materials(path: Path) -> set[str]:
    result: set[str] = set()
    lines = path.read_text(encoding="utf-8-sig", errors="replace").splitlines()
    in_triangles = False
    corner = 0
    for raw in lines:
        line = raw.strip()
        if line.lower() == "triangles":
            in_triangles = True
            corner = 0
            continue
        if in_triangles and line.lower() == "end":
            break
        if not in_triangles or not line:
            continue
        if corner == 0:
            result.add(line)
            corner = 3
        else:
            corner -= 1
    return result


def normalize_material_path(value: str) -> Path:
    return Path(*value.replace("\\", "/").strip("/").split("/"))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--qc", type=Path, required=True)
    parser.add_argument("--smd", type=Path, required=True)
    parser.add_argument("--addon", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()

    for path in (args.qc, args.smd):
        if not path.is_file():
            raise SystemExit(f"missing source material input: {path}")
    if not args.addon.is_dir():
        raise SystemExit(f"missing addon root: {args.addon}")

    qc_text = args.qc.read_text(encoding="utf-8-sig", errors="replace")
    cdmaterials = re.findall(r'\$cdmaterials\s+"([^"]+)"', qc_text, flags=re.I)
    if not cdmaterials:
        raise SystemExit("QC has no $cdmaterials")
    materials = sorted(smd_materials(args.smd))
    closure: list[dict[str, object]] = []
    all_pass = True
    for material in materials:
        candidates = []
        for directory in cdmaterials:
            relative = Path("materials") / normalize_material_path(directory) / f"{material}.vmt"
            candidate = args.addon / relative
            if candidate.is_file():
                candidates.append(candidate)
        unique_vmt = len(candidates) == 1
        references: list[dict[str, object]] = []
        if unique_vmt:
            vmt_text = candidates[0].read_text(encoding="utf-8-sig", errors="replace")
            for key, value in re.findall(
                r'"\$(basetexture|bumpmap|phongexponenttexture|selfillummask|envmapmask)"\s+"([^"]+)"',
                vmt_text,
                flags=re.I,
            ):
                relative_vtf = Path("materials") / normalize_material_path(value).with_suffix(".vtf")
                vtf = args.addon / relative_vtf
                references.append({"parameter": f"${key.lower()}", "value": value, "vtf": str(vtf), "exists": vtf.is_file()})
        material_pass = unique_vmt and bool(references) and all(bool(item["exists"]) for item in references)
        all_pass = all_pass and material_pass
        closure.append({
            "smd_material": material,
            "vmt_candidates": [str(path) for path in candidates],
            "unique_vmt": unique_vmt,
            "texture_references": references,
            "pass": material_pass,
        })

    report = {
        "schema": "cf2.source1.material-closure.v1",
        "qc": str(args.qc),
        "smd": str(args.smd),
        "addon": str(args.addon),
        "cdmaterials": cdmaterials,
        "smd_materials": materials,
        "closure": closure,
        "pass": all_pass,
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"report": str(args.report), "pass": all_pass}, ensure_ascii=False))
    return 0 if all_pass else 2


if __name__ == "__main__":
    sys.exit(main())
