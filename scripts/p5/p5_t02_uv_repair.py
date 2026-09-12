# -*- coding: utf-8 -*-
"""Diagnose Transformers UV wrap. Historical T02 always did v->1-v.

OBJ export already writes vt as (u, 1-decoderV). Sampling decoder UVs with
another 1-v puts the mag-well island on the stock. This script renders both
conventions, overlays OBJ islands on the verified atlas, and keeps identity
CANDIDATE_ONLY.
"""
from __future__ import annotations

import json
import math
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # noqa: E402
from p5_t02_native_inventory import (  # noqa: E402
    CFREZ_EXE,
    DATA,
    DOTNET,
    OUT,
    REPO,
    WIDTH,
    HEIGHT,
    MARGIN,
    HEADER_HEIGHT,
    barycentric,
    decode_ltb_geometry,
    rel,
    weapon_meshes,
)

CF = Path(_paths.cf_dir())
UV_DIR = OUT / "uv_repair"
GATE = OUT / "gate"
STAGING_LTB = DATA / "p5_t02_native" / "ltb"
BASE_ATLAS = OUT / "atlases" / "pv_dtx_PV-M4A1_S_TRANSFORMERS_PC_7ca69f66.png"
CLASSIC_ATLAS = OUT / "atlases" / "pv_dtx_PV-M4A1_S_TRANSFORMERS_CLASSIC.png"
BASE_LTB = STAGING_LTB / "PV-M4A1_S_TRANSFORMERS_a0ccef5deed7.ltb"
CLASSIC_LTB = STAGING_LTB / "PV-M4A1_S_TRANSFORMERS_TLAND_620778d78577.ltb"
HAND_MARKS = ("FVIEW-HAND", "FVIEW-ARM", "HAND", "ARM")


def sample(texture: Image.Image, u: float, v: float, flip_v: bool) -> tuple[int, int, int]:
    width, height = texture.size
    u = max(0.0, min(1.0, float(u)))
    v = max(0.0, min(1.0, (1.0 - float(v)) if flip_v else float(v)))
    x = min(width - 1, int(round(u * (width - 1))))
    y = min(height - 1, int(round(v * (height - 1))))
    pixel = texture.getpixel((x, y))
    return int(pixel[0]), int(pixel[1]), int(pixel[2])


def render_textured(
    document: dict[str, Any],
    texture: Image.Image,
    dest: Path,
    label: str,
    flip_v: bool,
) -> dict[str, Any]:
    meshes = weapon_meshes(document)
    all_vertices = [vertex for mesh in meshes for vertex in mesh.get("vertices", [])]
    min_y = min(float(vertex[1]) for vertex in all_vertices)
    max_y = max(float(vertex[1]) for vertex in all_vertices)
    min_z = min(float(vertex[2]) for vertex in all_vertices)
    max_z = max(float(vertex[2]) for vertex in all_vertices)
    range_y = max(max_y - min_y, 1e-6)
    range_z = max(max_z - min_z, 1e-6)
    scale = min((WIDTH - 2 * MARGIN) / range_z, (HEIGHT - 2 * MARGIN - HEADER_HEIGHT) / range_y)
    offset_x = (WIDTH - range_z * scale) / 2.0
    offset_y = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT - range_y * scale) / 2.0
    buf = bytearray(WIDTH * HEIGHT * 4)
    zbuf = [-1e9] * (WIDTH * HEIGHT)
    for index in range(0, len(buf), 4):
        buf[index : index + 4] = b"\xff\xff\xff\xff"
    faces = 0
    for mesh in meshes:
        vertices = mesh.get("vertices") or []
        uvs = mesh.get("texture_coordinates") or []
        if len(uvs) != len(vertices):
            continue
        projected = []
        for x, y, z in vertices:
            projected.append(
                (
                    offset_x + (float(z) - min_z) * scale,
                    offset_y + (max_y - float(y)) * scale,
                    float(x),
                )
            )
        indices = mesh.get("triangle_indices") or []
        for pos in range(0, len(indices) - 2, 3):
            ids = [int(indices[pos + n]) for n in range(3)]
            points = [projected[index] for index in ids]
            uv_points = [(float(uvs[index][0]), float(uvs[index][1])) for index in ids]
            faces += 1
            min_x = max(0, int(math.floor(min(point[0] for point in points))))
            max_x = min(WIDTH - 1, int(math.ceil(max(point[0] for point in points))))
            min_y_box = max(HEADER_HEIGHT, int(math.floor(min(point[1] for point in points))))
            max_y_box = min(HEIGHT - 1, int(math.ceil(max(point[1] for point in points))))
            for py in range(min_y_box, max_y_box + 1):
                for px in range(min_x, max_x + 1):
                    weights = barycentric(px + 0.5, py + 0.5, points[0], points[1], points[2])
                    if weights is None or min(weights) < -1e-6:
                        continue
                    depth = sum(weights[i] * points[i][2] for i in range(3))
                    zi = py * WIDTH + px
                    if depth < zbuf[zi]:
                        continue
                    u = sum(weights[i] * uv_points[i][0] for i in range(3))
                    v = sum(weights[i] * uv_points[i][1] for i in range(3))
                    r, g, b = sample(texture, u, v, flip_v)
                    offset = zi * 4
                    buf[offset : offset + 4] = bytes((r, g, b, 255))
                    zbuf[zi] = depth
    image = Image.frombytes("RGBA", (WIDTH, HEIGHT), bytes(buf))
    draw = ImageDraw.Draw(image)
    draw.text((10, 8), label[:90], fill=(20, 30, 42, 255), font=ImageFont.load_default())
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)
    return {"preview": rel(dest), "flip_v": flip_v, "triangle_count": faces}


def parse_obj(path: Path) -> list[dict]:
    groups: list[dict] = []
    current = {"name": "default", "faces": []}
    all_uvs: list[tuple[float, float]] = []
    all_pos: list[tuple[float, float, float]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        kind, *rest = line.split()
        if kind in {"o", "g"} and rest:
            if current["faces"] or current["name"] != "default":
                groups.append(current)
            current = {"name": rest[0], "faces": []}
        elif kind == "v" and len(rest) >= 3:
            all_pos.append((float(rest[0]), float(rest[1]), float(rest[2])))
        elif kind == "vt" and len(rest) >= 2:
            all_uvs.append((float(rest[0]), float(rest[1])))
        elif kind == "f":
            corners = []
            for token in rest:
                parts = token.split("/")
                vi = int(parts[0]) - 1 if parts[0] else -1
                ti = int(parts[1]) - 1 if len(parts) > 1 and parts[1] else vi
                corners.append((vi, ti))
            if len(corners) >= 3:
                current["faces"].append(corners[:3])
    groups.append(current)
    for group in groups:
        group["all_uvs"] = all_uvs
        group["all_pos"] = all_pos
        group["is_hand"] = any(mark in group["name"].upper() for mark in HAND_MARKS)
    return groups


def overlay(atlas: Image.Image, groups: list[dict], dest: Path, use_obj_v: bool) -> dict[str, Any]:
    image = atlas.convert("RGBA").copy()
    draw = ImageDraw.Draw(image)
    width, height = image.size
    drawn = 0
    for group in groups:
        if group["is_hand"]:
            continue
        uvs = group["all_uvs"]
        for face in group["faces"]:
            points = []
            for _vi, ti in face:
                if ti < 0 or ti >= len(uvs):
                    continue
                u, v = uvs[ti]
                x = int(round(max(0.0, min(1.0, u)) * (width - 1)))
                vv = v if use_obj_v else (1.0 - v)
                y = int(round(max(0.0, min(1.0, vv)) * (height - 1)))
                points.append((x, y))
            if len(points) >= 3:
                draw.line(points + [points[0]], fill=(0, 255, 80, 220), width=1)
                drawn += 1
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)
    return {"preview": rel(dest), "triangles_drawn": drawn, "use_obj_v_as_image_y": use_obj_v}


def export_obj(logical: str, dest: Path) -> Path:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            str(CFREZ_EXE),
            "--export-obj",
            "--source-root",
            str(CF / "rez"),
            "--model",
            logical,
            "--output",
            str(dest),
            "--raw-transform",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    if proc.returncode != 0 or not dest.is_file():
        raise RuntimeError((proc.stderr or proc.stdout or "obj export failed")[:800])
    return dest


def raster_obj(groups: list[dict], texture: Image.Image, dest: Path, label: str, flip_obj_v: bool) -> dict[str, Any]:
    pos = groups[0]["all_pos"]
    uvs = groups[0]["all_uvs"]
    faces = []
    for group in groups:
        if group["is_hand"]:
            continue
        faces.extend(group["faces"])
    ys = [p[1] for p in pos]
    zs = [p[2] for p in pos]
    min_y, max_y, min_z, max_z = min(ys), max(ys), min(zs), max(zs)
    range_y = max(max_y - min_y, 1e-6)
    range_z = max(max_z - min_z, 1e-6)
    scale = min((WIDTH - 2 * MARGIN) / range_z, (HEIGHT - 2 * MARGIN - HEADER_HEIGHT) / range_y)
    offset_x = (WIDTH - range_z * scale) / 2.0
    offset_y = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT - range_y * scale) / 2.0
    buf = bytearray(WIDTH * HEIGHT * 4)
    zbuf = [-1e9] * (WIDTH * HEIGHT)
    for index in range(0, len(buf), 4):
        buf[index : index + 4] = b"\xff\xff\xff\xff"
    for face in faces:
        points = []
        uv_points = []
        for vi, ti in face:
            x, y, z = pos[vi]
            points.append((offset_x + (z - min_z) * scale, offset_y + (max_y - y) * scale, x))
            uv_points.append(uvs[ti])
        min_x = max(0, int(math.floor(min(p[0] for p in points))))
        max_x = min(WIDTH - 1, int(math.ceil(max(p[0] for p in points))))
        min_y_box = max(HEADER_HEIGHT, int(math.floor(min(p[1] for p in points))))
        max_y_box = min(HEIGHT - 1, int(math.ceil(max(p[1] for p in points))))
        for py in range(min_y_box, max_y_box + 1):
            for px in range(min_x, max_x + 1):
                weights = barycentric(px + 0.5, py + 0.5, points[0], points[1], points[2])
                if weights is None or min(weights) < -1e-6:
                    continue
                depth = sum(weights[i] * points[i][2] for i in range(3))
                zi = py * WIDTH + px
                if depth < zbuf[zi]:
                    continue
                u = sum(weights[i] * uv_points[i][0] for i in range(3))
                v = sum(weights[i] * uv_points[i][1] for i in range(3))
                r, g, b = sample(texture, u, v, flip_obj_v)
                buf[zi * 4 : zi * 4 + 4] = bytes((r, g, b, 255))
                zbuf[zi] = depth
    image = Image.frombytes("RGBA", (WIDTH, HEIGHT), bytes(buf))
    draw = ImageDraw.Draw(image)
    draw.text((10, 8), label[:90], fill=(20, 30, 42, 255), font=ImageFont.load_default())
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)
    return {"preview": rel(dest), "flip_obj_v": flip_obj_v, "faces": len(faces)}


def sheet(cells: list[tuple[Path, str]], dest: Path, title: str) -> None:
    cell_w, cell_h = 520, 300
    columns = 2
    header = 40
    rows = math.ceil(len(cells) / columns)
    image = Image.new("RGB", (columns * cell_w, header + rows * cell_h), (236, 239, 244))
    draw = ImageDraw.Draw(image)
    draw.text((12, 10), title, fill=(18, 28, 40), font=ImageFont.load_default())
    for index, (path, label) in enumerate(cells):
        left = (index % columns) * cell_w
        top = header + (index // columns) * cell_h
        tile = Image.new("RGB", (cell_w, cell_h), (255, 255, 255))
        if path.is_file():
            pic = Image.open(path).convert("RGBA")
            pic = ImageOps.contain(pic, (cell_w - 12, 250), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (cell_w, cell_h), (255, 255, 255, 255))
            canvas.alpha_composite(pic, ((cell_w - pic.width) // 2, 4))
            tile = canvas.convert("RGB")
        ImageDraw.Draw(tile).text((8, 270), label[:70], fill=(20, 30, 42), font=ImageFont.load_default())
        image.paste(tile, (left, top))
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)


def main() -> int:
    UV_DIR.mkdir(parents=True, exist_ok=True)
    work = DATA / "p5_t02_native" / "geom"
    work.mkdir(parents=True, exist_ok=True)
    reports: dict[str, Any] = {"identity_status": "CANDIDATE_ONLY"}
    jobs = [
        ("base", BASE_LTB, BASE_ATLAS, "PLAYERVIEW/PV-M4A1_S_Transformers.LTB"),
        ("classic", CLASSIC_LTB, CLASSIC_ATLAS, "PLAYERVIEW/PV-M4A1_S_Transformers_Classic.LTB"),
    ]
    for name, ltb, atlas_path, logical in jobs:
        with Image.open(atlas_path) as image:
            texture = image.convert("RGBA").copy()
        document = decode_ltb_geometry(ltb, work)
        for flip in (True, False):
            tag = "vflip" if flip else "v_as_is"
            dest = UV_DIR / f"{name}_decoder_{tag}.png"
            reports[f"{name}_{tag}"] = render_textured(
                document, texture, dest, f"{name} decoder UV {tag}", flip
            )
        obj_path = DATA / "p5_t02_native" / "obj" / f"{name}.obj"
        try:
            export_obj(logical, obj_path)
            groups = parse_obj(obj_path)
            reports[f"{name}_obj_export"] = rel(obj_path)
            reports[f"{name}_overlay_objV"] = overlay(texture, groups, UV_DIR / f"{name}_uv_overlay_objV.png", True)
            reports[f"{name}_overlay_1-objV"] = overlay(texture, groups, UV_DIR / f"{name}_uv_overlay_1minusObjV.png", False)
            reports[f"{name}_obj_sample_as_is"] = raster_obj(
                groups, texture, UV_DIR / f"{name}_obj_sample_as_is.png", f"{name} OBJ vt as-is", False
            )
            reports[f"{name}_obj_sample_flip"] = raster_obj(
                groups, texture, UV_DIR / f"{name}_obj_sample_flip.png", f"{name} OBJ vt 1-v (N05-D overlay)", True
            )
        except Exception as exc:
            reports[f"{name}_obj_error"] = str(exc)[:500]
    sheet(
        [
            (UV_DIR / "classic_decoder_vflip.png", "OLD: decoder + v->1-v (gate mesh)"),
            (UV_DIR / "classic_decoder_v_as_is.png", "decoder V as image Y (no extra flip)"),
            (UV_DIR / "classic_uv_overlay_1minusObjV.png", "OBJ islands on atlas, y=1-objV (= decoder V)"),
            (UV_DIR / "classic_obj_sample_flip.png", "OBJ raster with 1-objV (comfyui/N05-D)"),
            (UV_DIR / "base_decoder_vflip.png", "base OLD v->1-v"),
            (UV_DIR / "base_decoder_v_as_is.png", "base decoder V as-is"),
        ],
        UV_DIR / "uv_compare.png",
        "P5-T02 UV repair — CANDIDATE_ONLY. Mag-well-on-stock means extra V flip.",
    )
    (UV_DIR / "uv_repair.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": rel(UV_DIR), "keys": list(reports)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
