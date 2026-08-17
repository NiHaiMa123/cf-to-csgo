# -*- coding: utf-8 -*-
"""Split a B3 OBJ into the C1 weapon-only and optional CF-arm staging OBJ files."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from typing import Any


def parse_map(path: Path) -> dict[str, bool]:
    result: dict[str, bool] = {}
    current: str | None = None
    for raw in path.read_text(encoding="utf-8").splitlines():
        if match := re.match(r"^\s{2}- mesh:\s*(.+?)\s*$", raw):
            current = match.group(1).strip().strip('"')
            result[current] = True
            continue
        if current is not None and (match := re.match(r"^\s{4}export:\s*(true|false)\s*$", raw)):
            result[current] = match.group(1) == "true"
    return result


def parse_obj(path: Path) -> tuple[list[str], list[dict[str, Any]], str | None]:
    vertices: list[str] = []
    uvs: list[str] = []
    normals: list[str] = []
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    mtllib: str | None = None

    def ensure_group() -> dict[str, Any]:
        nonlocal current
        if current is None:
            current = {"name": "<implicit>", "material": None, "vertices": [], "uvs": [], "normals": [], "faces": []}
            groups.append(current)
        return current

    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("mtllib "):
            mtllib = line[7:].strip()
        elif line.startswith("g "):
            current = {"name": line[2:].strip(), "material": None, "vertices": [], "uvs": [], "normals": [], "faces": []}
            groups.append(current)
        elif line.startswith("usemtl "):
            ensure_group()["material"] = line[7:].strip()
        elif line.startswith("v "):
            vertices.append(line)
            ensure_group()["vertices"].append(len(vertices))
        elif line.startswith("vt "):
            uvs.append(line)
            ensure_group()["uvs"].append(len(uvs))
        elif line.startswith("vn "):
            normals.append(line)
            ensure_group()["normals"].append(len(normals))
        elif line.startswith("f "):
            ensure_group()["faces"].append(line)
    return [*vertices, *uvs, *normals], groups, mtllib


def parse_index(value: str, total: int) -> int:
    index = int(value)
    return index if index > 0 else total + index + 1


def split_groups(groups: list[dict[str, Any]], vertices: list[str], uvs: list[str], normals: list[str], mtllib: str | None, output: Path, source_obj: Path) -> list[dict[str, Any]]:
    output.parent.mkdir(parents=True, exist_ok=True)
    target_mtl = output.with_name(output.stem + ".mtl")
    records: list[dict[str, Any]] = []
    vertex_base = 0
    uv_base = 0
    normal_base = 0

    with output.open("w", encoding="utf-8", newline="\n") as writer:
        writer.write("# C1 split generated from B3 raw OBJ\n")
        if mtllib:
            writer.write(f"mtllib {target_mtl.name}\n")
        writer.write(f"o {output.stem}\n")
        for group in groups:
            vertex_map = {old: vertex_base + new for new, old in enumerate(group["vertices"], start=1)}
            uv_map = {old: uv_base + new for new, old in enumerate(group["uvs"], start=1)}
            normal_map = {old: normal_base + new for new, old in enumerate(group["normals"], start=1)}
            writer.write(f"g {group['name']}\n")
            if group["material"]:
                writer.write(f"usemtl {group['material']}\n")
            for old in group["vertices"]:
                writer.write(vertices[old - 1] + "\n")
            for old in group["uvs"]:
                writer.write(uvs[old - 1] + "\n")
            for old in group["normals"]:
                writer.write(normals[old - 1] + "\n")
            for face in group["faces"]:
                remapped: list[str] = []
                for token in face.split()[1:]:
                    parts = token.split("/")
                    mapped = [str(vertex_map[parse_index(parts[0], len(vertices))])]
                    if len(parts) > 1 and parts[1]:
                        mapped.append(str(uv_map[parse_index(parts[1], len(uvs))]))
                    elif len(parts) > 1:
                        mapped.append("")
                    if len(parts) > 2 and parts[2]:
                        mapped.append(str(normal_map[parse_index(parts[2], len(normals))]))
                    remapped.append("/".join(mapped))
                writer.write("f " + " ".join(remapped) + "\n")

            records.append({
                "group": group["name"],
                "material": group["material"],
                "vertices": len(group["vertices"]),
                "uvs": len(group["uvs"]),
                "normals": len(group["normals"]),
                "triangles": len(group["faces"]),
                "obj": str(output),
                "mtl": str(target_mtl) if mtllib else None,
            })
            vertex_base += len(group["vertices"])
            uv_base += len(group["uvs"])
            normal_base += len(group["normals"])

    if mtllib:
        source_mtl = source_obj.with_name(mtllib)
        if source_mtl.is_file():
            shutil.copy2(source_mtl, target_mtl)
    return records


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--obj", type=Path, required=True)
    parser.add_argument("--map", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    args = parser.parse_args()

    source_obj = args.obj.resolve()
    output_dir = args.output_dir.resolve()
    export_by_mesh = parse_map(args.map.resolve())
    lines, groups, mtllib = parse_obj(source_obj)
    # The parser keeps the three OBJ streams in order; split them back out for
    # remapping without adding a dependency on an OBJ package.
    vertex_lines = [line for line in lines if line.startswith("v ")]
    uv_lines = [line for line in lines if line.startswith("vt ")]
    normal_lines = [line for line in lines if line.startswith("vn ")]
    selected_groups: dict[str, list[dict[str, Any]]] = {"weapon_only": [], "cf_arms_optional": []}
    failures: list[str] = []
    for group in groups:
        prefix = source_obj.stem + "_"
        source_mesh = group["name"][len(prefix):] if group["name"].startswith(prefix) else group["name"]
        if source_mesh not in export_by_mesh:
            failures.append(f"group missing from map: {source_mesh}")
            continue
        bucket = "weapon_only" if export_by_mesh[source_mesh] else "cf_arms_optional"
        selected_groups[bucket].append(group)

    selected: dict[str, list[dict[str, Any]]] = {}
    for bucket, bucket_groups in selected_groups.items():
        output = output_dir / bucket / f"{source_obj.stem}_{bucket}.obj"
        records = split_groups(bucket_groups, vertex_lines, uv_lines, normal_lines, mtllib, output, source_obj)
        selected[bucket] = records
        report_path = output_dir / bucket / f"{source_obj.stem}_{bucket}.json"
        report_path.write_text(json.dumps({"bucket": bucket, "source_obj": str(source_obj), "meshes": records}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    summary = {
        "schema": "cf2.m4a1_s.c1-split.v1",
        "source_obj": str(source_obj),
        "mesh_map": str(args.map.resolve()),
        "mesh_map_sha256": hashlib.sha256(args.map.resolve().read_bytes()).hexdigest(),
        "weapon_only_mesh_count": len(selected["weapon_only"]),
        "cf_arms_optional_mesh_count": len(selected["cf_arms_optional"]),
        "weapon_only": selected["weapon_only"],
        "cf_arms_optional": selected["cf_arms_optional"],
        "failures": failures,
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / f"{source_obj.stem}_c1_split_report.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
