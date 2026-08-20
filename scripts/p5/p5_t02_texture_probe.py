# -*- coding: utf-8 -*-
"""Probe real local PV DTX + UV mapping for the user-selected T02 finalists.

The CF PV DTX is preserved exactly as decoded.  This script never substitutes
the official reference or a UI icon as a model diffuse texture.  If the source
is a mask/lookup texture, the output is labelled as a diagnostic only.
"""

from __future__ import annotations

import json
import lzma
import math
import subprocess
import tempfile
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont

from p5_t02_narrow_and_render import (
    DECODER_DLL,
    DOTNET,
    PREVIEW_DIR,
    ROOT,
    RUNNER_DLL,
    T02_DIR,
    decode_geometry,
    weapon_meshes,
)


TEXTURE = ROOT / "data" / "rf017" / "ModelTextures" / "PLAYERVIEW" / "PV-M4A1_S_Transformers.DTX"
TEXTURE_WIDTH = 512
TEXTURE_HEIGHT = 256
WIDTH = 768
HEIGHT = 384
MARGIN = 28
HEADER_HEIGHT = 28


TARGETS = {
    "C029": "data/rf016/Models/PLAYERVIEW/PV-M4A1_S_IronBeast_Gilt.LTB",
    "C103": "data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Transformers_Reaper.LTB",
}


def read_pv_dtx(path: Path) -> Image.Image:
    data = path.read_bytes()
    # The repository's validated PV layout is headerless BGR24 512x256,
    # followed by mip levels and a trailer.  Only the base level is sampled.
    base_bytes = TEXTURE_WIDTH * TEXTURE_HEIGHT * 3
    if len(data) < base_bytes:
        raise RuntimeError(f"DTX too short for PV base level: {len(data)}")
    return Image.frombytes("RGB", (TEXTURE_WIDTH, TEXTURE_HEIGHT), data[:base_bytes], "raw", "BGR")


def sample(texture: Image.Image, u: float, v: float) -> tuple[int, int, int]:
    # LTB UV V is converted to image-top-left convention here.  Clamp rather
    # than wrap because the observed weapon UVs are atlas-local with a small
    # floating-point overshoot above 1.0.
    u = max(0.0, min(1.0, float(u)))
    v = max(0.0, min(1.0, 1.0 - float(v)))
    return texture.getpixel((min(TEXTURE_WIDTH - 1, int(round(u * (TEXTURE_WIDTH - 1)))), min(TEXTURE_HEIGHT - 1, int(round(v * (TEXTURE_HEIGHT - 1))))))


def barycentric(px: float, py: float, a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]) -> tuple[float, float, float] | None:
    denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(denominator) < 1e-9:
        return None
    w0 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / denominator
    w1 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / denominator
    w2 = 1.0 - w0 - w1
    return w0, w1, w2


def render_textured(document: dict[str, Any], output: Path, label: str, texture: Image.Image) -> dict[str, Any]:
    meshes = weapon_meshes(document)
    all_vertices = [vertex for mesh in meshes for vertex in mesh.get("vertices", [])]
    if not all_vertices:
        raise RuntimeError("no weapon meshes after hand/arm exclusion")
    min_y = min(float(vertex[1]) for vertex in all_vertices)
    max_y = max(float(vertex[1]) for vertex in all_vertices)
    min_z = min(float(vertex[2]) for vertex in all_vertices)
    max_z = max(float(vertex[2]) for vertex in all_vertices)
    range_y = max(max_y - min_y, 1e-6)
    range_z = max(max_z - min_z, 1e-6)
    scale = min((WIDTH - 2 * MARGIN) / range_z, (HEIGHT - 2 * MARGIN - HEADER_HEIGHT) / range_y)
    offset_x = (WIDTH - range_z * scale) / 2.0
    offset_y = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT - range_y * scale) / 2.0
    image = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 8), label, fill=(20, 30, 42, 255), font=font)
    faces: list[tuple[float, list[tuple[float, float]], list[tuple[float, float]], list[tuple[float, float, float]]]] = []

    for mesh in meshes:
        vertices = mesh.get("vertices") or []
        uvs = mesh.get("texture_coordinates") or []
        if len(uvs) != len(vertices):
            continue
        projected: list[tuple[float, float, float]] = []
        for x, y, z in vertices:
            projected.append((offset_x + (float(z) - min_z) * scale, offset_y + (max_y - float(y)) * scale, float(x)))
        indices = mesh.get("triangle_indices") or []
        for pos in range(0, len(indices) - 2, 3):
            try:
                ids = [int(indices[pos + n]) for n in range(3)]
                points = [projected[index] for index in ids]
                uv_points = [uvs[index] for index in ids]
            except (IndexError, ValueError):
                continue
            faces.append((sum(point[2] for point in points) / 3.0, [(p[0], p[1]) for p in points], [(float(uv[0]), float(uv[1])) for uv in uv_points], []))

    # Far-to-near, then per-pixel UV interpolation.  This is a deliberately
    # simple orthographic diagnostic, not a game renderer.
    for _, points, uv_points, _ in sorted(faces, key=lambda item: item[0]):
        min_x = max(0, int(math.floor(min(point[0] for point in points))))
        max_x = min(WIDTH - 1, int(math.ceil(max(point[0] for point in points))))
        min_y_box = max(HEADER_HEIGHT, int(math.floor(min(point[1] for point in points))))
        max_y_box = min(HEIGHT - 1, int(math.ceil(max(point[1] for point in points))))
        for py in range(min_y_box, max_y_box + 1):
            for px in range(min_x, max_x + 1):
                weights = barycentric(px + 0.5, py + 0.5, points[0], points[1], points[2])
                if weights is None or min(weights) < -1e-6:
                    continue
                u = sum(weights[index] * uv_points[index][0] for index in range(3))
                v = sum(weights[index] * uv_points[index][1] for index in range(3))
                r, g, b = sample(texture, u, v)
                # Preserve the source DTX appearance, with a small neutral
                # light factor so UV seams and geometry remain readable.
                image.putpixel((px, py), (r, g, b, 255))

    # A restrained outline makes the actual geometry readable over the mask.
    for _, points, _, _ in sorted(faces, key=lambda item: item[0]):
        draw.line(points + [points[0]], fill=(40, 48, 60, 170), width=1, joint="curve")
    image.save(output)
    return {"width": WIDTH, "height": HEIGHT, "texture_status": "raw_pv_dtx_uv_diagnostic_not_validated_diffuse", "texture_path": str(TEXTURE.relative_to(ROOT)).replace("\\", "/"), "weapon_mesh_count": len(meshes), "triangle_count": len(faces), "uv_flip": "v -> 1-v", "projection": "orthographic side"}


def main() -> int:
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
    texture = read_pv_dtx(TEXTURE)
    reports: dict[str, Any] = {}
    with tempfile.TemporaryDirectory(prefix="p5_t02_texture_probe_") as temp:
        for cluster_id, relative in TARGETS.items():
            document, source_sha256 = decode_geometry(relative, Path(temp))
            output = PREVIEW_DIR / f"{cluster_id}_{Path(relative).stem}_pv_dtx_uv_diagnostic.png"
            reports[cluster_id] = render_textured(document, output, f"{cluster_id} | raw PV DTX + UV diagnostic (not final diffuse)", texture)
            reports[cluster_id]["model_sha256"] = source_sha256
            reports[cluster_id]["preview_path"] = str(output.relative_to(ROOT)).replace("\\", "/")

    shortlist_path = T02_DIR / "visual_shortlist.json"
    shortlist = json.loads(shortlist_path.read_text(encoding="utf-8"))
    for candidate in shortlist.get("candidates", []):
        if candidate.get("cluster_id") in reports:
            candidate["texture_probe"] = reports[candidate["cluster_id"]]
            candidate["texture_status"] = "raw_pv_dtx_uv_diagnostic_not_validated_diffuse"
    shortlist["texture_probe"] = {"status": "inconclusive_for_final_identity", "reason": "PV DTX decodes as a one-channel/lookup-like mask under the repository's validated headerless BGR24 layout; no direct color diffuse is available", "source": str(TEXTURE.relative_to(ROOT)).replace("\\", "/"), "model_texture_mapping": "C029 exact SHA family and C103 mesh material family both point to Transformers DTX; C103 remains mapping-inferred"}
    shortlist_path.write_text(json.dumps(shortlist, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    execution_path = T02_DIR / "execution.json"
    execution = json.loads(execution_path.read_text(encoding="utf-8"))
    execution["texture_probe"] = {"status": "inconclusive_for_final_identity", "source_dtx": str(TEXTURE.relative_to(ROOT)).replace("\\", "/"), "source_dtx_sha256": __import__("hashlib").sha256(TEXTURE.read_bytes()).hexdigest(), "reports": reports, "finding": "actual local PV DTX was UV-applied to C029/C103; it is mask/lookup-like rather than a validated color diffuse, so no local identity confirmation was written"}
    execution_path.write_text(json.dumps(execution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "inconclusive_for_final_identity", "reports": reports}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
