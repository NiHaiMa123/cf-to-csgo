# -*- coding: utf-8 -*-
"""Create the machine-readable A2 report for a Crowbar-decompiled M4A1-S."""

from __future__ import annotations

import json
import argparse
import re
import shlex
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REFERENCE_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "reference_m4a1_s"
DECOMPILED_DIR = REFERENCE_DIR / "decompiled"


def qc_block(lines: list[str], start: int) -> tuple[list[str], int]:
    """Return a brace-delimited QC block and the first line after it."""
    block: list[str] = []
    depth = 0
    seen = False
    for index in range(start, len(lines)):
        line = lines[index]
        block.append(line)
        depth += line.count("{") - line.count("}")
        if "{" in line:
            seen = True
        if seen and depth <= 0:
            return block, index + 1
    return block, len(lines)


def parse_qc(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    modelname = next((m.group(1) for line in lines if (m := re.match(r'^\$modelname\s+"([^"]+)"', line, re.I))), None)
    cdmaterials = [m.group(1) for line in lines if (m := re.match(r'^\$cdmaterials\s+"([^"]+)"', line, re.I))]
    attachments = []
    definebones = []
    bonemerge = []
    bodygroups = []
    texturegroups = []
    animations = []
    sequences = []
    bbox = None
    for line in lines:
        if m := re.match(r'^\$attachment\s+"([^"]+)"\s+"([^"]+)"\s+(.+)$', line, re.I):
            attachments.append({"name": m.group(1), "bone": m.group(2), "transform": m.group(3).strip()})
        elif m := re.match(r'^\$definebone\s+"([^"]+)"\s+"([^"]*)"\s+(.+)$', line, re.I):
            definebones.append({"name": m.group(1), "parent": m.group(2) or None, "transform": m.group(3).strip()})
        elif m := re.match(r'^\$bonemerge\s+"([^"]+)"', line, re.I):
            bonemerge.append(m.group(1))
        elif m := re.match(r'^\$bbox\s+(.+)$', line, re.I):
            try:
                numbers = [float(token) for token in m.group(1).split()]
                if len(numbers) == 6:
                    bbox = {"min": numbers[:3], "max": numbers[3:]}
            except ValueError:
                pass

    index = 0
    while index < len(lines):
        line = lines[index].strip()
        if re.match(r'^\$(bodygroup|texturegroup)\b', line, re.I):
            match = re.match(r'^\$(bodygroup|texturegroup)\s+"([^"]+)"', line, re.I)
            block, index = qc_block(lines, index)
            if match:
                entries = [re.sub(r'^\s*(studio|blank)\s+', r'\1 ', item.strip(), flags=re.I)
                           for item in block if re.match(r'^\s*(studio|blank)\b', item, re.I)]
                quoted = re.findall(r'"([^"]+)"', "\n".join(block))
                record = {"name": match.group(2), "entries": entries, "quoted": quoted}
                (bodygroups if match.group(1).lower() == "bodygroup" else texturegroups).append(record)
            continue
        if m := re.match(r'^\$(animation|sequence)\s+"([^"]+)"(?:\s+"([^"]+)")?', line, re.I):
            kind, name, direct_path = m.groups()
            block, index = qc_block(lines, index)
            if kind.lower() == "animation":
                animations.append({"name": name, "path": direct_path, "options": [x.strip() for x in block[1:] if x.strip()]})
            else:
                block_text = "\n".join(block)
                refs = re.findall(r'"([^"\n]+\.(?:smd|dmx))"', block_text, re.I)
                # Sequences commonly refer to a named $animation without an
                # extension (for example "idle_masked_silencer_m4a4").
                # Capture those first quoted lines too, while excluding the
                # sequence name itself and quoted event parameters.
                for item in block[1:]:
                    candidate = re.match(r'^\s*"([^"]+)"\s*$', item)
                    if candidate and candidate.group(1) not in refs:
                        refs.append(candidate.group(1))
                activity = re.search(r'^\s*activity\s+([^\s]+)\s+([^\s]+)', block_text, re.I | re.M)
                fps_match = re.search(r'^\s*fps\s+([-+\d.]+)', block_text, re.I | re.M)
                events = []
                for event in re.finditer(r'\{\s*event\s+([^\s]+)\s+([-+\d.]+)\s+"([^"]*)"\s*\}', block_text, re.I):
                    events.append({"event": event.group(1), "frame": float(event.group(2)), "parameter": event.group(3)})
                sequences.append({
                    "name": name,
                    "references": refs,
                    "activity": {"name": activity.group(1), "weight": activity.group(2)} if activity else None,
                    "fps": float(fps_match.group(1)) if fps_match else None,
                    "events": events,
                    "options": [item.strip() for item in block if item.strip() and not item.strip().startswith("$")],
                })
            continue
        index += 1
    return {
        "path": path.relative_to(REFERENCE_DIR).as_posix(),
        "modelname": modelname,
        "cdmaterials": cdmaterials,
        "attachments": attachments,
        "bones": definebones,
        "bone_count": len(definebones),
        "bonemerge": bonemerge,
        "bodygroups": bodygroups,
        "texturegroups": texturegroups,
        "bbox": bbox,
        "animations": animations,
        "sequences": sequences,
    }


def parse_smd(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    nodes: list[dict[str, Any]] = []
    times: list[int] = []
    materials: Counter[str] = Counter()
    vertices = 0
    triangles = 0
    bounds_min = [float("inf")] * 3
    bounds_max = [float("-inf")] * 3
    section = ""
    triangle_vertex_count = 0
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower()
        if lower in {"nodes", "skeleton", "triangles"}:
            section = lower
            continue
        if lower == "end":
            section = ""
            triangle_vertex_count = 0
            continue
        if section == "nodes":
            if m := re.match(r'^(\d+)\s+"([^"]+)"\s+(-?\d+)', stripped):
                nodes.append({"index": int(m.group(1)), "name": m.group(2), "parent_index": int(m.group(3))})
        elif section == "skeleton":
            if m := re.match(r'^time\s+(\d+)', stripped, re.I):
                times.append(int(m.group(1)))
        elif section == "triangles":
            tokens = stripped.split()
            is_vertex = len(tokens) >= 9
            if is_vertex:
                try:
                    int(tokens[0])
                    xyz = [float(tokens[1]), float(tokens[2]), float(tokens[3])]
                    vertices += 1
                    triangle_vertex_count += 1
                    for axis in range(3):
                        bounds_min[axis] = min(bounds_min[axis], xyz[axis])
                        bounds_max[axis] = max(bounds_max[axis], xyz[axis])
                    if triangle_vertex_count == 3:
                        triangles += 1
                        triangle_vertex_count = 0
                    continue
                except (ValueError, IndexError):
                    pass
            if stripped and not is_vertex:
                materials[stripped] += 1
    return {
        "path": path.relative_to(REFERENCE_DIR).as_posix(),
        "kind": "mesh" if triangles else "animation",
        "node_count": len(nodes),
        "nodes": nodes,
        "frame_count": len(times),
        "frames": times,
        "vertex_count": vertices,
        "triangle_count": triangles,
        "materials": sorted(materials),
        "bounds": {"min": bounds_min, "max": bounds_max} if vertices else None,
    }


def main() -> int:
    global REFERENCE_DIR, DECOMPILED_DIR
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reference-dir", type=Path, default=REFERENCE_DIR)
    args = parser.parse_args()
    REFERENCE_DIR = args.reference_dir.resolve()
    candidate = REFERENCE_DIR / "decompiled"
    DECOMPILED_DIR = candidate if candidate.is_dir() else REFERENCE_DIR
    qc_path = next(DECOMPILED_DIR.glob("*.qc"), None)
    if qc_path is None:
        raise SystemExit(f"no QC found under {DECOMPILED_DIR}")
    qc = parse_qc(qc_path)
    smds = [parse_smd(path) for path in sorted(DECOMPILED_DIR.rglob("*.smd"))]
    smd_by_name = {Path(item["path"]).name.lower(): item for item in smds}
    animation_by_name = {item["name"].lower(): item for item in qc["animations"]}
    for sequence in qc["sequences"]:
        sequence["resolved_frames"] = None
        sequence["resolved_files"] = []
        for reference in sequence["references"]:
            ref_name = Path(reference.replace("\\", "/")).name.lower()
            animation = animation_by_name.get(Path(ref_name).stem.lower())
            if animation and animation.get("path"):
                ref_name = Path(animation["path"].replace("\\", "/")).name.lower()
            if ref_name in smd_by_name:
                item = smd_by_name[ref_name]
                sequence["resolved_files"].append(item["path"])
                sequence["resolved_frames"] = item["frame_count"]

    text_files = [path for path in DECOMPILED_DIR.rglob("*") if path.is_file() and path.suffix.lower() in {".qc", ".smd", ".dmx"}]
    ak_hits = []
    for path in text_files:
        text = path.read_text(encoding="utf-8", errors="replace")
        if re.search(r"ak[-_]?47|ak47", text, re.I):
            ak_hits.append(path.relative_to(REFERENCE_DIR).as_posix())
    report = {
        "schema": "cf2.m4a1_s.reference-report.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "toolchain": {
            "decompiler": "CrowbarDecompiler 0.71 CMD edition (tools/CrowbarDecompiler/CrowbarDecompiler(1.1).exe)",
            "source_format": "Source 1 MDL/VVD/VTX/ANI",
            "decompiler_output_format": "SMD + QC",
            "dmx_files": [],
            "dmx_note": "Fixed CrowbarDecompiler command edition emitted SMD/QC for this model; official source ANI is preserved under source_vpk.",
        },
        "source_manifest": "extraction_manifest.json",
        "target": {
            "weapon": "M4A1-S",
            "internal_modelname": qc["modelname"],
            "expected_modelname": "weapons\\v_rif_m4a1_s.mdl",
            "first_person": True,
        },
        "bones": {"count": qc["bone_count"], "hierarchy": qc["bones"]},
        "attachments": qc["attachments"],
        "materials": {"cdmaterials": qc["cdmaterials"], "texturegroups": qc["texturegroups"], "smd_materials": sorted({m for item in smds for m in item["materials"]})},
        "bodygroups": qc["bodygroups"],
        "bounds": {"qc_bbox": qc["bbox"], "smd_mesh_bounds": [item for item in smds if item["kind"] == "mesh"]},
        "animations": qc["animations"],
        "sequences": qc["sequences"],
        "smd_files": smds,
        "validation": {
            "internal_name_is_m4a1_s": str(qc["modelname"]).replace("\\", "/").lower() == "weapons/v_rif_m4a1_s.mdl",
            "unexplained_ak_references": ak_hits,
            "ak_reference_used": False,
            "has_reference_mesh": any(item["kind"] == "mesh" for item in smds),
            "has_animation_smd": any(item["kind"] == "animation" for item in smds),
        },
    }
    output = REFERENCE_DIR / "reference_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
