# -*- coding: utf-8 -*-
"""Apply real local scalar material maps to C029/C103 as a shader diagnostic.

The output is intentionally a conservative neutral-metal approximation.  It
uses only local AlphaMap/SpecularMap values with the decoded LTB UVs; it is not
declared to be the final CF diffuse/shader recreation.
"""

from __future__ import annotations

import hashlib
import json
import math
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from p5_t02_narrow_and_render import PREVIEW_DIR, ROOT, T02_DIR, decode_geometry, weapon_meshes
from p5_t02_texture_probe import barycentric


WIDTH = 768
HEIGHT = 384
MARGIN = 28
HEADER_HEIGHT = 28
ALPHA_PATH = ROOT / "data" / "rf017" / "ModelTextures" / "AlphaMap" / "M4A1_S_Transformers_Alpha.TGA"
SPEC_PATH = ROOT / "data" / "rf017" / "ModelTextures" / "SpecularMap" / "M4A1_S_Transformers_S.TGA"
TARGETS = {
    "C029": "data/rf016/Models/PLAYERVIEW/PV-M4A1_S_IronBeast_Gilt.LTB",
    "C103": "data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Transformers_Reaper.LTB",
}


def decode_map(path: Path, raw_without_tga_footer: bool = False) -> Image.Image:
    data = path.read_bytes()
    if raw_without_tga_footer:
        pixel_data = data[: 1024 * 1024 * 3]
    else:
        signature = b"TRUEVISION-XFILE"
        offset = data.find(signature)
        if offset < 0:
            raise RuntimeError(f"missing TGA footer in {path.name}")
        footer = offset - 8
        header_offset = footer + 26
        header = data[header_offset : header_offset + 18]
        pixel_data = data[:footer] + data[header_offset + 18 :]
        if header[17] & 0x20 == 0:
            image = Image.frombytes("RGB", (1024, 1024), pixel_data, "raw", "BGR")
            return image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return Image.frombytes("RGB", (1024, 1024), pixel_data, "raw", "BGR")


def sample_channel(image: Image.Image, u: float, v: float, channel: int) -> float:
    u = max(0.0, min(1.0, float(u)))
    v = max(0.0, min(1.0, 1.0 - float(v)))
    x = min(1023, max(0, int(round(u * 1023))))
    y = min(1023, max(0, int(round(v * 1023))))
    return image.getpixel((x, y))[channel] / 255.0


def render(document: dict[str, Any], output: Path, label: str, alpha: Image.Image, spec: Image.Image) -> dict[str, Any]:
    meshes = weapon_meshes(document)
    vertices_all = [vertex for mesh in meshes for vertex in mesh.get("vertices", [])]
    min_y = min(float(vertex[1]) for vertex in vertices_all)
    max_y = max(float(vertex[1]) for vertex in vertices_all)
    min_z = min(float(vertex[2]) for vertex in vertices_all)
    max_z = max(float(vertex[2]) for vertex in vertices_all)
    range_y = max(max_y - min_y, 1e-6)
    range_z = max(max_z - min_z, 1e-6)
    scale = min((WIDTH - 2 * MARGIN) / range_z, (HEIGHT - 2 * MARGIN - HEADER_HEIGHT) / range_y)
    offset_x = (WIDTH - range_z * scale) / 2.0
    offset_y = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT - range_y * scale) / 2.0
    image = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    draw.text((10, 8), label, fill=(18, 28, 40, 255), font=ImageFont.load_default())
    faces: list[tuple[float, list[tuple[float, float]], list[tuple[float, float]], list[tuple[float, float, float, float]]]] = []

    for mesh in meshes:
        vertices = mesh.get("vertices") or []
        uvs = mesh.get("texture_coordinates") or []
        if len(uvs) != len(vertices):
            continue
        projected = [(offset_x + (float(v[2]) - min_z) * scale, offset_y + (max_y - float(v[1])) * scale, float(v[0])) for v in vertices]
        indices = mesh.get("triangle_indices") or []
        for pos in range(0, len(indices) - 2, 3):
            try:
                ids = [int(indices[pos + n]) for n in range(3)]
                points = [projected[index] for index in ids]
                uv_points = [uvs[index] for index in ids]
            except (IndexError, ValueError):
                continue
            faces.append((sum(point[2] for point in points) / 3.0, [(p[0], p[1]) for p in points], [(float(uv[0]), float(uv[1])) for uv in uv_points], []))

    for _, points, uv_points, _ in sorted(faces, key=lambda item: item[0]):
        x0 = max(0, int(math.floor(min(point[0] for point in points))))
        x1 = min(WIDTH - 1, int(math.ceil(max(point[0] for point in points))))
        y0 = max(HEADER_HEIGHT, int(math.floor(min(point[1] for point in points))))
        y1 = min(HEIGHT - 1, int(math.ceil(max(point[1] for point in points))))
        for py in range(y0, y1 + 1):
            for px in range(x0, x1 + 1):
                weights = barycentric(px + 0.5, py + 0.5, points[0], points[1], points[2])
                if weights is None or min(weights) < -1e-6:
                    continue
                u = sum(weights[i] * uv_points[i][0] for i in range(3))
                v = sum(weights[i] * uv_points[i][1] for i in range(3))
                visibility = sample_channel(alpha, u, v, 1)
                highlight = sample_channel(spec, u, v, 0)
                shade = 0.30 + 0.70 * visibility
                metal = min(255, int(66 + 130 * shade + 45 * highlight))
                blue_metal = min(255, int(78 + 145 * shade + 65 * highlight))
                image.putpixel((px, py), (min(255, metal + 7), min(255, metal + 16), blue_metal, 255))
    for _, points, _, _ in sorted(faces, key=lambda item: item[0]):
        draw.line(points + [points[0]], fill=(42, 52, 65, 175), width=1, joint="curve")
    image.save(output)
    return {
        "preview_path": str(output.relative_to(ROOT)).replace("\\", "/"),
        "width": WIDTH,
        "height": HEIGHT,
        "texture_status": "scalar_map_shader_approximation_not_final_diffuse",
        "alpha_map": str(ALPHA_PATH.relative_to(ROOT)).replace("\\", "/"),
        "specular_map": str(SPEC_PATH.relative_to(ROOT)).replace("\\", "/"),
        "uv_flip": "v -> 1-v",
        "weapon_mesh_count": len(meshes),
        "triangle_count": len(faces),
        "provenance": "local LTB geometry + local AlphaMap G / SpecularMap R; no generated or external model texture",
    }


def main() -> int:
    alpha = decode_map(ALPHA_PATH, raw_without_tga_footer=True)
    spec = decode_map(SPEC_PATH)
    reports: dict[str, Any] = {}
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="p5_t02_shader_probe_") as temp:
        for cluster_id, relative in TARGETS.items():
            document, model_sha = decode_geometry(relative, Path(temp))
            output = PREVIEW_DIR / f"{cluster_id}_{Path(relative).stem}_scalar_shader_diagnostic.png"
            report = render(document, output, f"{cluster_id} | local scalar-map shader diagnostic (not final diffuse)", alpha, spec)
            report["model_sha256"] = model_sha
            reports[cluster_id] = report

    shortlist_path = T02_DIR / "visual_shortlist.json"
    shortlist = json.loads(shortlist_path.read_text(encoding="utf-8"))
    for candidate in shortlist.get("candidates", []):
        if candidate.get("cluster_id") in reports:
            candidate["shader_diagnostic"] = reports[candidate["cluster_id"]]
    shortlist["shader_probe"] = {"status": "diagnostic_only", "maps": [str(ALPHA_PATH.relative_to(ROOT)).replace("\\", "/"), str(SPEC_PATH.relative_to(ROOT)).replace("\\", "/")], "final_diffuse_available": False, "identity_status": "CANDIDATE_ONLY"}
    shortlist_path.write_text(json.dumps(shortlist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    execution_path = T02_DIR / "execution.json"
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    execution["shader_probe"] = {"status": "diagnostic_only", "reports": reports, "final_diffuse_available": False, "identity_status": "CANDIDATE_ONLY", "note": "Scalar maps improve local surface diagnostics but do not close the missing color diffuse/shader lookup mapping."}
    execution_path.write_text(json.dumps(execution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "diagnostic_only", "reports": reports}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
