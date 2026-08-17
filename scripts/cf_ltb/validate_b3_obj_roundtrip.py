# -*- coding: utf-8 -*-
"""Validate a B3 OBJ export against its exporter report.

The validator checks that mesh groups, material slots, vertex/UV/normal counts,
triangle counts, and raw-coordinate checksums survive the text OBJ round-trip.
It does not claim that OBJ preserves skinning or CF animation data; those remain
in the LTB diagnostic report.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import struct
from pathlib import Path
from typing import Any


def field(record: dict[str, Any], name: str) -> Any:
    """Read either the .NET PascalCase or a future camel/snake case report."""
    if name in record:
        return record[name]
    pascal = name[0].upper() + name[1:]
    if pascal in record:
        return record[pascal]
    snake = ""
    for char in name:
        snake += f"_{char.lower()}" if char.isupper() else char
    return record.get(snake)


def double_checksum(values: list[float]) -> str:
    payload = b"".join(struct.pack("<d", value) for value in values)
    return hashlib.sha256(payload).hexdigest()


def parse_index(token: str, total: int) -> int | None:
    try:
        value = int(token)
    except ValueError:
        return None
    if value < 0:
        value = total + value + 1
    return value if 1 <= value <= total else None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--obj", type=Path)
    args = parser.parse_args()

    report_path = args.report.resolve()
    report = json.loads(report_path.read_text(encoding="utf-8"))
    obj_path = (args.obj or Path(field(report, "objPath"))).resolve()
    if not obj_path.is_file():
        raise SystemExit(f"OBJ not found: {obj_path}")

    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    normals: list[tuple[float, float, float]] = []
    groups: list[dict[str, Any]] = []
    current: dict[str, Any] | None = None
    invalid_faces = 0

    def ensure_group() -> dict[str, Any]:
        nonlocal current
        if current is None:
            current = {"name": "<implicit>", "material": None, "vertices": [], "uvs": [], "normals": [], "faces": 0}
            groups.append(current)
        return current

    for raw_line in obj_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("g "):
            current = {"name": line[2:].strip(), "material": None, "vertices": [], "uvs": [], "normals": [], "faces": 0}
            groups.append(current)
            continue
        if line.startswith("usemtl "):
            ensure_group()["material"] = line[7:].strip()
            continue
        if line.startswith("v "):
            values = [float(value) for value in line.split()[1:4]]
            if len(values) != 3:
                raise SystemExit(f"invalid vertex line: {line}")
            vertices.append(tuple(values))
            ensure_group()["vertices"].append(len(vertices))
            continue
        if line.startswith("vt "):
            values = [float(value) for value in line.split()[1:3]]
            if len(values) != 2:
                raise SystemExit(f"invalid UV line: {line}")
            uvs.append(tuple(values))
            ensure_group()["uvs"].append(len(uvs))
            continue
        if line.startswith("vn "):
            values = [float(value) for value in line.split()[1:4]]
            if len(values) != 3:
                raise SystemExit(f"invalid normal line: {line}")
            normals.append(tuple(values))
            ensure_group()["normals"].append(len(normals))
            continue
        if line.startswith("f "):
            group = ensure_group()
            tokens = line.split()[1:]
            if len(tokens) != 3:
                invalid_faces += 1
                continue
            for token in tokens:
                fields = token.split("/")
                if parse_index(fields[0], len(vertices)) is None:
                    invalid_faces += 1
                    break
                if len(fields) > 1 and fields[1] and parse_index(fields[1], len(uvs)) is None:
                    invalid_faces += 1
                    break
                if len(fields) > 2 and fields[2] and parse_index(fields[2], len(normals)) is None:
                    invalid_faces += 1
                    break
            group["faces"] += 1

    expected_meshes = field(report, "meshes") or []
    expected_totals = field(report, "totals") or {}
    failures: list[str] = []
    if len(groups) != len(expected_meshes):
        failures.append(f"group count {len(groups)} != report {len(expected_meshes)}")
    if len(vertices) != field(expected_totals, "vertexCount"):
        failures.append(f"vertex count {len(vertices)} != report {field(expected_totals, 'vertexCount')}")
    if len(uvs) != field(expected_totals, "uvCount"):
        failures.append(f"UV count {len(uvs)} != report {field(expected_totals, 'uvCount')}")
    if len(normals) != field(expected_totals, "normalCount"):
        failures.append(f"normal count {len(normals)} != report {field(expected_totals, 'normalCount')}")
    if sum(group["faces"] for group in groups) != sum(field(mesh, "triangleCount") for mesh in expected_meshes):
        failures.append("triangle count differs from report")
    if invalid_faces:
        failures.append(f"invalid face references: {invalid_faces}")

    vertex_cursor = 0
    uv_cursor = 0
    transform = field(report, "transform") or {}
    transform_mode = field(report, "transformMode") or "raw"
    for index, (group, expected) in enumerate(zip(groups, expected_meshes, strict=False)):
        expected_group = field(expected, "groupName")
        if group["name"] != expected_group:
            failures.append(f"mesh {index} group {group['name']!r} != {expected_group!r}")
        if group["material"] != field(expected, "materialName"):
            failures.append(f"mesh {index} material {group['material']!r} != {field(expected, 'materialName')!r}")
        if len(group["vertices"]) != field(expected, "vertexCount"):
            failures.append(f"mesh {index} vertex count differs")
        if group["faces"] != field(expected, "triangleCount"):
            failures.append(f"mesh {index} triangle count differs")
        if len(group["normals"]) != field(expected, "normalCount"):
            failures.append(f"mesh {index} normal count differs")

        mesh_vertices = vertices[vertex_cursor:vertex_cursor + len(group["vertices"])]
        mesh_uvs = uvs[uv_cursor:uv_cursor + len(group["uvs"])]
        scale = float(field(transform, "scale") or 1)
        center = [float(field(transform, key) or 0) for key in ("centerX", "centerY", "centerZ")]
        raw_values = []
        for vertex in mesh_vertices:
            raw_values.extend((vertex[0] / scale + center[0], vertex[1] / scale + center[1], vertex[2] / scale + center[2]))
        raw_uv_values = []
        for uv in mesh_uvs:
            raw_uv_values.extend((uv[0], 1.0 - uv[1]))
        if transform_mode == "raw":
            if double_checksum(raw_values) != field(expected, "rawVertexChecksum"):
                failures.append(f"mesh {index} raw vertex checksum differs")
        elif float(field(expected, "maxPositionRoundTripError") or 0) > 1e-12:
            failures.append(f"mesh {index} legacy position round-trip error exceeds tolerance")
        if double_checksum(raw_uv_values) != field(expected, "rawUvChecksum"):
            failures.append(f"mesh {index} raw UV checksum differs")
        vertex_cursor += len(group["vertices"])
        uv_cursor += len(group["uvs"])

    result = {
        "report": str(report_path),
        "obj": str(obj_path),
        "passed": not failures,
        "groups": len(groups),
        "vertices": len(vertices),
        "uvs": len(uvs),
        "normals": len(normals),
        "faces": sum(group["faces"] for group in groups),
        "failures": failures,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
