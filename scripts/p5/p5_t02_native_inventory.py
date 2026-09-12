# -*- coding: utf-8 -*-
"""P5-T02 native inventory: verified Transformers family DTX/TGA/CFG/LTB.

Uses the N05-C MD5-verified REZ reader. Historical T02 gray previews and the
headerless BGR24 probe on data/rf017 are not reused as native pixels.

This is an evidence producer. It does not write IDENTITY_CONFIRMED, does not
treat filename Transformers as 雷神, and does not deploy or change the M4A4
diagnostic addon.
"""
from __future__ import annotations

import configparser
import hashlib
import io
import json
import lzma
import math
import os
import re
import subprocess
import sys
import urllib.request
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "cf_extract"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "material_recovery"))
import _paths  # noqa: E402
import extract_all  # noqa: E402
import n05a_decoder_provenance_audit as audit  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

from p5_t02_narrow_and_render import (  # noqa: E402
    DECODER_DLL,
    DOTNET,
    EXCLUDED_MESH_RE,
    RUNNER_DLL,
    T01_REFERENCE,
    weapon_meshes,
)

REPO = Path(_paths.project_dir())
DATA = Path(_paths.data_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / "work" / "p5_leishen" / "t02_native"
STAGING = DATA / "p5_t02_native"
ATLAS_DIR = OUT / "atlases"
MESH_DIR = OUT / "mesh"
CFG_DIR = OUT / "cfg"
BORNBEAST_ATLAS = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05b_shard_material_recovery/bornbeast_pv_dtx.png"
)
CFREZ_EXE = REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
OFFICIAL_URL = "https://mcdn.gtimg.com/bbcdn/cf/serial/C0457.png"
OFFICIAL_BYTES = 125896

FAMILY_RE = re.compile(r"TRANSFORMERS|LEISHEN|LEI[_-]?SHEN|THUNDER|THOR", re.I)
HAND_RE = EXCLUDED_MESH_RE
IMAGE_EXT = {".DTX", ".TGA", ".DDS"}
MODEL_EXT = {".LTB"}
CFG_EXT = {".CFG"}
KEEP_EXT = IMAGE_EXT | MODEL_EXT | CFG_EXT
MESH_RENDER_CAP = 12
WIDTH = 768
HEIGHT = 384
MARGIN = 28
HEADER_HEIGHT = 28


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def logical_key(value: str) -> str:
    return extract_all.logical_path_key(value)


def classify(full_path: str) -> dict[str, Any]:
    key = logical_key(full_path)
    name = Path(key.replace("\\", "/")).name
    stem = Path(name).stem
    suffix = Path(name).suffix
    role = "other"
    if "/PLAYERVIEW/" in key and suffix == ".LTB":
        role = "pv_ltb"
    elif "/WEAPONS/" in key and suffix == ".LTB":
        role = "qv_ltb"
    elif "/PLAYERVIEW/" in key and suffix == ".DTX":
        role = "pv_dtx"
    elif "/WEAPONS/" in key and suffix == ".DTX":
        role = "qv_dtx"
    elif "/NORMALMAP/" in key and suffix in {".TGA", ".DTX"}:
        role = "normal"
    elif "/SPECULARMAP/" in key and suffix in {".TGA", ".DTX"}:
        role = "specular"
    elif "/ALPHAMAP/" in key and suffix in {".TGA", ".DTX"}:
        role = "alpha"
    elif "/WEAPONSHADER/" in key and suffix == ".CFG":
        role = "weapon_shader_cfg"
    elif "/ENVCUBEMAP/" in key and suffix == ".DDS":
        role = "env_cube"
    elif suffix == ".LTB":
        role = "other_ltb"
    elif suffix == ".DTX":
        role = "other_dtx"
    return {
        "role": role,
        "name": name,
        "stem": stem,
        "suffix": suffix,
        "view": "pv" if "/PLAYERVIEW/" in key else "qv" if "/WEAPONS/" in key else "other",
    }


def maybe_lzma(data: bytes) -> tuple[bytes, bool]:
    if data[:1] != b"\x5d":
        return data, False
    try:
        return lzma.decompress(data, format=lzma.FORMAT_ALONE), True
    except lzma.LZMAError:
        return data, False


def color_stats(image: Image.Image) -> dict[str, Any]:
    rgba = image.convert("RGBA")
    # Downsample for stats only; native PNG previews keep full resolution.
    sample_img = rgba if max(rgba.size) <= 256 else rgba.resize((256, 256), Image.Resampling.BOX)
    raw = sample_img.tobytes("raw", "RGBA")
    count = len(raw) // 4
    if count == 0:
        return {"pixel_count": 0}
    lums = []
    sum_r = sum_g = sum_b = 0
    dark = blueish = reddish = 0
    for index in range(0, len(raw), 4):
        r, g, b = raw[index], raw[index + 1], raw[index + 2]
        lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
        lums.append(lum)
        sum_r += r
        sum_g += g
        sum_b += b
        if lum < 16:
            dark += 1
        if b > r + 8 and b > g + 8:
            blueish += 1
        if r > b + 8 and r > g + 8:
            reddish += 1
    lums.sort()
    mid = lums[len(lums) // 2]
    return {
        "pixel_count": count,
        "sampled": True,
        "size": list(rgba.size),
        "median_luminance": round(mid, 2),
        "mean_luminance": round(sum(lums) / count, 2),
        "mean_rgb": [round(sum_r / count, 2), round(sum_g / count, 2), round(sum_b / count, 2)],
        "fraction_lum_lt_16": round(dark / count, 4),
        "fraction_blueish": round(blueish / count, 4),
        "fraction_reddish": round(reddish / count, 4),
        "silhouette_risk": bool(mid < 20 and dark / count > 0.45),
    }


def decode_image_bytes(logical_path: str, data: bytes, dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    suffix = Path(logical_path).suffix.upper()
    if suffix == ".DTX":
        decoded = audit.decode_repo_pixels(data)
        if decoded.get("ok"):
            image = decoded["image"]
            image.save(dest)
            header = decoded.get("header") or {}
            return {
                "ok": True,
                "decoder": "python_n05a",
                "format": decoded.get("format"),
                "preview": rel(dest),
                "size": list(image.size),
                "mode": image.mode,
                "dtx_header": {
                    "ok": header.get("ok"),
                    "width": header.get("width"),
                    "height": header.get("height"),
                    "bytes_per_pixel_field": header.get("bytes_per_pixel_field"),
                    "flags": header.get("flags"),
                },
                "color": color_stats(image),
            }
        if not CFREZ_EXE.is_file():
            return {"ok": False, "decoder": "python_n05a", "error": decoded}
        src = STAGING / "decode" / (dest.stem + ".dtx")
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(data)
        proc = subprocess.run(
            [str(CFREZ_EXE), "--decode-image", str(src), str(dest)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if proc.returncode != 0 or not dest.is_file():
            return {
                "ok": False,
                "decoder": "cfrez_fallback",
                "python_error": decoded,
                "stderr": (proc.stderr or proc.stdout or "").strip()[:500],
            }
        with Image.open(dest) as image:
            copied = image.convert("RGBA").copy()
        return {
            "ok": True,
            "decoder": "cfrez_fallback",
            "preview": rel(dest),
            "size": list(copied.size),
            "mode": copied.mode,
            "python_error": {k: decoded.get(k) for k in ("ok", "reason") if k in decoded},
            "color": color_stats(copied),
        }
    if suffix == ".TGA":
        with Image.open(io.BytesIO(data)) as source:
            source.load()
            container = source.format or "TGA"
            image = source.copy()
        image.save(dest)
        return {
            "ok": True,
            "decoder": "pillow_tga",
            "container": container,
            "preview": rel(dest),
            "size": list(image.size),
            "mode": image.mode,
            "repair_applied": False,
            "color": color_stats(image),
        }
    if suffix == ".DDS":
        if not CFREZ_EXE.is_file():
            return {"ok": False, "error": "CFRezManager missing for DDS"}
        src = STAGING / "decode" / (dest.stem + ".dds")
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(data)
        proc = subprocess.run(
            [str(CFREZ_EXE), "--decode-image", str(src), str(dest)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if proc.returncode != 0 or not dest.is_file():
            return {"ok": False, "decoder": "cfrez_dds", "stderr": (proc.stderr or proc.stdout or "").strip()[:500]}
        with Image.open(dest) as image:
            copied = image.convert("RGBA").copy()
        return {
            "ok": True,
            "decoder": "cfrez_dds",
            "preview": rel(dest),
            "size": list(copied.size),
            "mode": copied.mode,
            "color": color_stats(copied),
        }
    return {"ok": False, "error": f"unsupported {suffix}"}


def parse_cfg(data: bytes) -> dict[str, Any]:
    text = data.decode("ascii", errors="replace")
    parser = configparser.ConfigParser(strict=False)
    parser.optionxform = str
    parser.read_string(text)
    return {section: dict(parser[section]) for section in parser.sections()}


def fetch_official(dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    request = urllib.request.Request(OFFICIAL_URL, headers={"User-Agent": "cf2-p5-t02/native"})
    with urllib.request.urlopen(request, timeout=30) as response:
        blob = response.read()
        content_type = response.headers.get("Content-Type", "")
        status = getattr(response, "status", 200)
    if status != 200 or len(blob) != OFFICIAL_BYTES:
        raise RuntimeError(f"official C0457.png unexpected: status={status} bytes={len(blob)} type={content_type}")
    dest.write_bytes(blob)
    with Image.open(io.BytesIO(blob)) as image:
        image.load()
        copied = image.convert("RGBA").copy()
    return {
        "url": OFFICIAL_URL,
        "path": rel(dest),
        "sha256": sha256_bytes(blob),
        "bytes": len(blob),
        "content_type": content_type,
        "size": list(copied.size),
        "color": color_stats(copied),
    }


def scan_indexes() -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    indexes = extract_all.discover_index_archives(str(CF))
    hits: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception as exc:
            errors.append({"index": index_path, "error": str(exc)})
            continue
        for entry in entries:
            full = str(entry.get("full_path") or "")
            suffix = Path(full).suffix.upper()
            if suffix not in KEEP_EXT:
                continue
            if not FAMILY_RE.search(full):
                continue
            meta = classify(full)
            hits.append(
                {
                    "index_archive": index_path,
                    "full_path": full,
                    "logical_key": logical_key(full),
                    "data_offset": int(entry["data_offset"]),
                    "size": int(entry["size"]),
                    "time": int(entry["time"]),
                    "directory_md5": str(entry.get("md5") or "").lower(),
                    "md5_complete": is_complete_directory_md5(entry.get("md5")),
                    **meta,
                }
            )
    return hits, errors, len(indexes)


def recover_unique(hits: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        grouped[hit["directory_md5"] or f"no-md5:{hit['index_archive']}:{hit['full_path']}"].append(hit)
    recovered: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for digest, group in grouped.items():
        first = group[0]
        if not first["md5_complete"]:
            failures.append({"reason": "incomplete_directory_md5", "hit": first})
            continue
        entry = {
            "full_path": first["full_path"],
            "data_offset": first["data_offset"],
            "size": first["size"],
            "time": first["time"],
            "md5": first["directory_md5"],
        }
        try:
            data, provenance = read_verified_payload(first["index_archive"], entry)
        except Exception as exc:
            failures.append({"reason": str(exc), "hit": first})
            continue
        body, lzma_used = maybe_lzma(data) if first["suffix"] == ".LTB" else (data, False)
        row = {
            **first,
            "copy_count": len(group),
            "copies": [
                {
                    "index_archive": item["index_archive"],
                    "full_path": item["full_path"],
                    "payload_hint_time": item["time"],
                    "size": item["size"],
                }
                for item in group
            ],
            "payload_sha256": provenance["sha256"],
            "routing": provenance["routing"],
            "payload_file": provenance["payload_file"],
            "lzma": lzma_used,
            "payload_bytes": len(data),
            "decoded_bytes": len(body),
        }
        safe = re.sub(r"[^A-Za-z0-9._-]+", "_", first["stem"])[:80]
        if first["suffix"] in IMAGE_EXT:
            dest = ATLAS_DIR / f"{first['role']}_{safe}.png"
            # Collision: keep sha suffix.
            if dest.exists():
                dest = ATLAS_DIR / f"{first['role']}_{safe}_{provenance['sha256'][:8]}.png"
            row["decode"] = decode_image_bytes(first["full_path"], data, dest)
        elif first["suffix"] == ".CFG":
            try:
                parsed = parse_cfg(data)
            except Exception as exc:
                row["cfg_error"] = str(exc)
                recovered.append(row)
                continue
            dest = CFG_DIR / f"{safe}.json"
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(json.dumps(parsed, indent=2) + "\n", encoding="utf-8")
            row["cfg"] = parsed
            row["cfg_path"] = rel(dest)
        elif first["suffix"] == ".LTB":
            row["ltb_staging"] = None
            if first["role"] in {"pv_ltb", "qv_ltb"}:
                staging = STAGING / "ltb" / f"{safe}_{provenance['sha256'][:12]}.ltb"
                staging.parent.mkdir(parents=True, exist_ok=True)
                staging.write_bytes(body)
                row["ltb_staging"] = str(staging)
        recovered.append(row)
    return recovered, failures


def barycentric(
    px: float, py: float, a: tuple[float, float], b: tuple[float, float], c: tuple[float, float]
) -> tuple[float, float, float] | None:
    denominator = (b[1] - c[1]) * (a[0] - c[0]) + (c[0] - b[0]) * (a[1] - c[1])
    if abs(denominator) < 1e-9:
        return None
    w0 = ((b[1] - c[1]) * (px - c[0]) + (c[0] - b[0]) * (py - c[1])) / denominator
    w1 = ((c[1] - a[1]) * (px - c[0]) + (a[0] - c[0]) * (py - c[1])) / denominator
    w2 = 1.0 - w0 - w1
    return w0, w1, w2


def sample(texture: Image.Image, u: float, v: float) -> tuple[int, int, int]:
    width, height = texture.size
    # LithTechModelDecoder UVs are already image-top-left (D3D). CFRezManager
    # OBJ export writes vt as (u, 1-v); do not flip decoder JSON a second time.
    u = max(0.0, min(1.0, float(u)))
    v = max(0.0, min(1.0, float(v)))
    x = min(width - 1, int(round(u * (width - 1))))
    y = min(height - 1, int(round(v * (height - 1))))
    pixel = texture.getpixel((x, y))
    return int(pixel[0]), int(pixel[1]), int(pixel[2])


def decode_ltb_geometry(staging_path: Path, work_dir: Path) -> dict[str, Any]:
    json_path = work_dir / (staging_path.stem + ".geometry.json")
    command = [str(DOTNET), str(RUNNER_DLL), str(DECODER_DLL), str(staging_path), str(json_path)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=90, check=False)
    if completed.returncode != 0 or not json_path.exists():
        detail = (completed.stderr or completed.stdout or "decoder returned no detail").strip()
        raise RuntimeError(detail[:800])
    return json.loads(json_path.read_text(encoding="utf-8"))


def render_textured(document: dict[str, Any], texture: Image.Image, dest: Path, label: str) -> dict[str, Any]:
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
    buf = bytearray(WIDTH * HEIGHT * 4)
    for index in range(0, len(buf), 4):
        buf[index : index + 4] = b"\xff\xff\xff\xff"
    faces: list[tuple[float, list[tuple[float, float]], list[tuple[float, float]]]] = []
    skipped_no_uv = 0
    for mesh in meshes:
        vertices = mesh.get("vertices") or []
        uvs = mesh.get("texture_coordinates") or []
        if len(uvs) != len(vertices):
            skipped_no_uv += 1
            continue
        projected: list[tuple[float, float, float]] = []
        for _x, y, z in vertices:
            projected.append(
                (
                    offset_x + (float(z) - min_z) * scale,
                    offset_y + (max_y - float(y)) * scale,
                    float(_x),
                )
            )
        indices = mesh.get("triangle_indices") or []
        for pos in range(0, len(indices) - 2, 3):
            try:
                ids = [int(indices[pos + n]) for n in range(3)]
                points = [projected[index] for index in ids]
                uv_points = [(float(uvs[index][0]), float(uvs[index][1])) for index in ids]
            except (IndexError, ValueError, TypeError):
                continue
            faces.append((sum(point[2] for point in points) / 3.0, [(p[0], p[1]) for p in points], uv_points))
    for _depth, points, uv_points in sorted(faces, key=lambda item: item[0]):
        min_x = max(0, int(math.floor(min(point[0] for point in points))))
        max_x = min(WIDTH - 1, int(math.ceil(max(point[0] for point in points))))
        min_y_box = max(HEADER_HEIGHT, int(math.floor(min(point[1] for point in points))))
        max_y_box = min(HEIGHT - 1, int(math.ceil(max(point[1] for point in points))))
        for py in range(min_y_box, max_y_box + 1):
            row = py * WIDTH * 4
            for px in range(min_x, max_x + 1):
                weights = barycentric(px + 0.5, py + 0.5, points[0], points[1], points[2])
                if weights is None or min(weights) < -1e-6:
                    continue
                u = sum(weights[index] * uv_points[index][0] for index in range(3))
                v = sum(weights[index] * uv_points[index][1] for index in range(3))
                r, g, b = sample(texture, u, v)
                offset = row + px * 4
                buf[offset : offset + 4] = bytes((r, g, b, 255))
    image = Image.frombytes("RGBA", (WIDTH, HEIGHT), bytes(buf))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 8), label[:90], fill=(20, 30, 42, 255), font=font)
    image.save(dest)
    with Image.open(dest) as saved:
        stats = color_stats(saved)
    return {
        "preview": rel(dest),
        "weapon_mesh_count": len(meshes),
        "triangle_count": len(faces),
        "skipped_meshes_without_uv": skipped_no_uv,
        "uv_flip": "decoder_v_as_image_y",
        "projection": "orthographic side; world Z horizontal, world Y vertical",
        "texture_status": "verified_pv_dtx_uv_not_identity",
        "color": stats,
    }


def pair_dtx(recovered: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_stem: dict[str, dict[str, Any]] = {}
    for row in recovered:
        if row["role"] == "pv_dtx" and (row.get("decode") or {}).get("ok"):
            by_stem[row["stem"].upper()] = row
    return by_stem


def render_meshes(recovered: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    if not RUNNER_DLL.is_file() or not DECODER_DLL.is_file() or not DOTNET.is_file():
        return [], [{"reason": "ltb_runner_missing", "runner": str(RUNNER_DLL), "decoder": str(DECODER_DLL)}]
    dtx_by_stem = pair_dtx(recovered)
    base = dtx_by_stem.get("PV-M4A1_S_TRANSFORMERS")
    pv_ltbs = [row for row in recovered if row["role"] == "pv_ltb" and row.get("ltb_staging")]
    # Prefer exact-stem DTX, then unique LTB SHA, cap count.
    chosen: list[dict[str, Any]] = []
    seen_sha: set[str] = set()
    exact = [row for row in pv_ltbs if row["stem"].upper() in dtx_by_stem]
    inferred = [row for row in pv_ltbs if row["stem"].upper() not in dtx_by_stem]
    for pool in (exact, inferred):
        for row in sorted(pool, key=lambda item: item["stem"]):
            sha = row["payload_sha256"]
            if sha in seen_sha:
                continue
            seen_sha.add(sha)
            chosen.append(row)
            if len(chosen) >= MESH_RENDER_CAP:
                break
        if len(chosen) >= MESH_RENDER_CAP:
            break
    reports: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    work_dir = STAGING / "geom"
    work_dir.mkdir(parents=True, exist_ok=True)
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    for row in chosen:
        stem = row["stem"].upper()
        dtx = dtx_by_stem.get(stem) or base
        mapping = "exact_stem" if stem in dtx_by_stem else "filename_base_transformers_inferred"
        if dtx is None:
            errors.append({"stem": row["stem"], "reason": "no_pv_dtx"})
            continue
        atlas_path = REPO / dtx["decode"]["preview"]
        try:
            document = decode_ltb_geometry(Path(row["ltb_staging"]), work_dir)
            with Image.open(atlas_path) as atlas:
                texture = atlas.convert("RGBA").copy()
            dest = MESH_DIR / f"{row['stem']}.png"
            report = render_textured(
                document,
                texture,
                dest,
                f"{row['stem']} | {mapping} | verified DTX",
            )
            report.update(
                {
                    "ltb_logical": row["full_path"],
                    "ltb_sha256": row["payload_sha256"],
                    "dtx_logical": dtx["full_path"],
                    "dtx_sha256": dtx["payload_sha256"],
                    "mapping": mapping,
                    "mapping_grade": "filename_convention_not_bute"
                    if mapping != "exact_stem"
                    else "same_stem_filename_not_bute",
                    "identity_status": "CANDIDATE_ONLY",
                }
            )
            reports.append(report)
        except Exception as exc:
            errors.append({"stem": row["stem"], "reason": str(exc)[:500]})
    return reports, errors


def make_contact_sheet(
    official: dict[str, Any],
    recovered: list[dict[str, Any]],
    mesh_reports: list[dict[str, Any]],
    dest: Path,
) -> dict[str, Any]:
    atlases = [
        row
        for row in recovered
        if row["role"] == "pv_dtx" and (row.get("decode") or {}).get("ok")
    ]
    cell_w, cell_h = 360, 220
    columns = 3
    official_h = 240
    mesh_rows = math.ceil(max(len(mesh_reports), 1) / columns)
    atlas_rows = math.ceil(max(len(atlases) + 1, 1) / columns)  # +1 BornBeast control
    width = columns * cell_w
    height = official_h + 36 + atlas_rows * cell_h + 28 + mesh_rows * cell_h
    sheet = Image.new("RGBA", (width, height), (235, 239, 244, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((14, 8), "P5-T02 native Transformers inventory — CANDIDATE_ONLY", fill=(18, 28, 40, 255), font=font)
    draw.text(
        (14, 24),
        "Official 图鉴 C0457.png = M4A1-雷神. BornBeast is 黑骑士 negative control. Filename is not identity.",
        fill=(18, 28, 40, 255),
        font=font,
    )
    official_img = Image.open(REPO / official["path"]).convert("RGBA")
    official_img = ImageOps.contain(official_img, (width - 28, official_h - 50), Image.Resampling.LANCZOS)
    sheet.alpha_composite(official_img, ((width - official_img.width) // 2, 44))

    def paste_tile(image_path: Path, label: str, index: int, origin_y: int) -> None:
        left = (index % columns) * cell_w
        top = origin_y + (index // columns) * cell_h
        tile = Image.new("RGBA", (cell_w, cell_h), (255, 255, 255, 255))
        if image_path.is_file():
            pic = Image.open(image_path).convert("RGBA")
            pic = ImageOps.contain(pic, (cell_w - 12, 172), Image.Resampling.LANCZOS)
            tile.alpha_composite(pic, ((cell_w - pic.width) // 2, 4))
        tile_draw = ImageDraw.Draw(tile)
        tile_draw.text((6, 180), label[:58], fill=(20, 30, 42, 255), font=font)
        sheet.alpha_composite(tile, (left, top))

    atlas_origin = official_h + 8
    draw.text((14, atlas_origin - 16), "Verified PV DTX atlases (native pixels)", fill=(18, 28, 40, 255), font=font)
    paste_tile(BORNBEAST_ATLAS, "NEG 黑骑士 BornBeast PV — NOT 雷神", 0, atlas_origin)
    for index, row in enumerate(atlases, start=1):
        paste_tile(REPO / row["decode"]["preview"], f"PV DTX {row['stem']}", index, atlas_origin)
    mesh_origin = atlas_origin + atlas_rows * cell_h + 20
    draw.text((14, mesh_origin - 16), "Verified DTX UV-wrapped on verified PV LTB", fill=(18, 28, 40, 255), font=font)
    if not mesh_reports:
        paste_tile(Path("_missing"), "no mesh render this run", 0, mesh_origin)
    for index, report in enumerate(mesh_reports):
        paste_tile(REPO / report["preview"], Path(report["preview"]).stem, index, mesh_origin)
    dest.parent.mkdir(parents=True, exist_ok=True)
    sheet.convert("RGB").save(dest)
    return {"path": rel(dest), "atlas_count": len(atlases), "mesh_count": len(mesh_reports)}


def write_report(
    execution: dict[str, Any],
    recovered: list[dict[str, Any]],
    mesh_reports: list[dict[str, Any]],
    dest: Path,
) -> None:
    pv_dtx = [row for row in recovered if row["role"] == "pv_dtx"]
    cfg = [row for row in recovered if row["role"] == "weapon_shader_cfg"]
    lines = [
        "# P5-T02 — Transformers native inventory",
        "",
        f"Result: **{execution['result']}**. Identity remains **CANDIDATE_ONLY**.",
        "",
        "Official 图鉴 is still the user visual gate: M4A1-雷神 / item `2010044601` / `C0457.png` (silver + blue lightning).",
        "Filename `Transformers` is recall only. M4A1-黑骑士 / BornBeast is a negative control, not 雷神.",
        "",
        "## What changed from historical T02",
        "",
        "- Historical T02 used gray geometry and a headerless BGR24 read of old `data/rf017` Transformers DTX.",
        "- This pass reads REZ through the N05-C MD5-verified numbered-part reader and decodes standard DTX/TGA.",
        "- No `IDENTITY_CONFIRMED`. No addon deploy. N05-J diagnostic addon and parked frozen addon were not touched.",
        "",
        "## Inventory",
        "",
        f"- Index archives scanned: {execution['index_count']}",
        f"- Family hits: {execution['hit_count']}",
        f"- Unique MD5-verified payloads: {len(recovered)}",
        f"- Recover failures: {len(execution.get('recover_failures') or [])}",
        "",
        "### Unique PV DTX",
        "",
    ]
    if not pv_dtx:
        lines.append("No Transformers PV DTX recovered.")
    for row in pv_dtx:
        decode = row.get("decode") or {}
        color = decode.get("color") or {}
        lines.append(
            f"- `{row['full_path']}` SHA `{row['payload_sha256'][:16]}…` "
            f"routing `{row['routing']}` decode `{decode.get('decoder')}` "
            f"size `{decode.get('size')}` median lum `{color.get('median_luminance')}` "
            f"blueish `{color.get('fraction_blueish')}` silhouette `{color.get('silhouette_risk')}`"
        )
        if decode.get("preview"):
            lines.append(f"  - preview: `{decode['preview']}`")
    lines += ["", "### WeaponShader CFG", ""]
    if not cfg:
        lines.append("No Transformers WeaponShader CFG recovered.")
    for row in cfg:
        textures = (row.get("cfg") or {}).get("Textures") or {}
        lines.append(f"- `{row['full_path']}` SHA `{row['payload_sha256'][:16]}…`")
        for key in ("SpecularMapName2", "NormalMapName2", "AlphaMapName2", "EnvCubeMapName2"):
            if key in textures:
                lines.append(f"  - `{key}` = `{textures[key]}`")
    lines += ["", "### Mesh UV wraps", ""]
    if not mesh_reports:
        lines.append("No mesh wrap this run.")
    for report in mesh_reports:
        lines.append(
            f"- `{report.get('ltb_logical')}` + `{report.get('dtx_logical')}` "
            f"mapping `{report.get('mapping')}` tris `{report.get('triangle_count')}` "
            f"preview `{report.get('preview')}`"
        )
    lines += [
        "",
        "## Binding grade",
        "",
        "- CFG `Name2` map names are config references, not runtime technique proof.",
        "- Same-stem LTB↔DTX is filename convention, not Bute `PViewSkinFileName`.",
        "- Historical packed Bute layer did not hit Transformers; this pass does not invent that binding.",
        "",
        "## User gate",
        "",
        "Compare verified PV DTX atlases and mesh wraps against official `C0457.png`.",
        "Do not confirm identity from filename. Do not treat BornBeast as 雷神.",
        "",
        "Reproduce:",
        "",
        "```powershell",
        "python -B scripts/p5/p5_t02_native_inventory.py",
        "```",
        "",
    ]
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    started = now()
    OUT.mkdir(parents=True, exist_ok=True)
    ATLAS_DIR.mkdir(parents=True, exist_ok=True)
    CFG_DIR.mkdir(parents=True, exist_ok=True)
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    reference = json.loads(T01_REFERENCE.read_text(encoding="utf-8"))
    if reference.get("user_confirmation") != "confirmed":
        raise RuntimeError("T01 official reference is not user-confirmed")
    official = fetch_official(OUT / "official_C0457.png")
    hits, index_errors, index_count = scan_indexes()
    recovered, recover_failures = recover_unique(hits)
    mesh_reports, mesh_errors = render_meshes(recovered)
    contact = make_contact_sheet(official, recovered, mesh_reports, OUT / "contact_sheet.png")
    unique_payloads = []
    for row in recovered:
        unique_payloads.append(
            {
                "role": row["role"],
                "full_path": row["full_path"],
                "payload_sha256": row["payload_sha256"],
                "routing": row["routing"],
                "directory_md5": row["directory_md5"],
                "size": row["size"],
                "copy_count": row["copy_count"],
                "decode": {k: v for k, v in (row.get("decode") or {}).items() if k != "dtx_header"} or None,
                "cfg_path": row.get("cfg_path"),
                "cfg_textures": ((row.get("cfg") or {}).get("Textures") if row.get("cfg") else None),
            }
        )
    pv_ok = sum(1 for row in recovered if row["role"] == "pv_dtx" and (row.get("decode") or {}).get("ok"))
    result = "NATIVE_TRANSFORMERS_INVENTORY_READY_FOR_USER_GATE" if pv_ok else "TRANSFORMERS_FAMILY_SCANNED_NO_PV_DTX"
    execution = {
        "schema": "cf2.p5.t02.native-inventory.v1",
        "task_id": "P5-T02",
        "started_at": started,
        "completed_at": now(),
        "result": result,
        "identity_status": "CANDIDATE_ONLY",
        "p4_m01": "INCOMPLETE",
        "official_reference": {
            "itemid": 2010044601,
            "name": "M4A1-雷神",
            "image": OFFICIAL_URL,
            "local": official,
        },
        "index_count": index_count,
        "hit_count": len(hits),
        "index_errors": index_errors,
        "recover_failures": [
            {"reason": item["reason"], "path": (item.get("hit") or {}).get("full_path")}
            for item in recover_failures
        ],
        "mesh_errors": mesh_errors,
        "contact_sheet": contact,
        "next_action": "user compares verified PV DTX / mesh wraps to C0457.png; do not write IDENTITY_CONFIRMED",
        "prohibited": [
            "IDENTITY_CONFIRMED",
            "USER_VISUAL_MATCH_CONFIRMED without explicit user choice",
            "BornBeast as 雷神",
            "filename Transformers as identity",
            "deploy / overwrite frozen or N05-J addon",
        ],
    }
    (OUT / "inventory.json").write_text(
        json.dumps(
            {
                "schema": "cf2.p5.t02.native-hits.v1",
                "hit_count": len(hits),
                "hits": [
                    {
                        "role": item["role"],
                        "full_path": item["full_path"],
                        "index_archive": item["index_archive"],
                        "directory_md5": item["directory_md5"],
                        "size": item["size"],
                        "time": item["time"],
                    }
                    for item in hits
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (OUT / "unique_payloads.json").write_text(json.dumps(unique_payloads, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "mesh_reports.json").write_text(json.dumps(mesh_reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "execution.json").write_text(json.dumps(execution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_report(execution, recovered, mesh_reports, OUT / "report.md")
    print(
        json.dumps(
            {
                "result": result,
                "hits": len(hits),
                "unique": len(recovered),
                "pv_dtx_ok": pv_ok,
                "mesh": len(mesh_reports),
                "out": rel(OUT),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
