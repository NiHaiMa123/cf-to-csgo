#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N03-H — Decode BornBeast DTX vs later-era SpecularMap controls."""
from __future__ import annotations

import hashlib
import json
import os
import struct
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402

REPO = Path(_paths.project_dir())
DATA = REPO / "data" / "rf017" / "ModelTextures"
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n03h_dtx_container_decode"
)
PREV = OUT / "previews"
N03G = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n03g_legacy_shader_fields/field_dump.json"
)
CSPROJ = REPO / "CFRezManager" / "CFRezManager.csproj"
DOTNET = Path(r"C:\Program Files\dotnet\dotnet.exe")
MAX_LEFTOVER = 200

CONTROLS_EXTRA = [
    DATA / "PLAYERVIEW" / "PV-M4A1_RoyalDragon.DTX",
    DATA / "PLAYERVIEW" / "PV-M4A1-RoyalDragon_silencer.DTX",
    DATA / "SpecularMap" / "PV-DualDE_GreenVein_S.DTX",
    DATA / "SpecularMap" / "PV-RI_M4A1-S_s.DTX",
    DATA / "SpecularMap" / "PV-RI_M14EBR_Scope01_s.DTX",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def rgb565(c: int) -> tuple[int, int, int]:
    r = ((c >> 11) & 31) * 255 // 31
    g = ((c >> 5) & 63) * 255 // 63
    b = (c & 31) * 255 // 31
    return r, g, b


def lerp(a: tuple[int, int, int], b: tuple[int, int, int], n: int, d: int) -> tuple[int, int, int]:
    return tuple((a[i] * (d - n) + b[i] * n) // d for i in range(3))  # type: ignore[return-value]


def dxt1_size(w: int, h: int) -> int:
    return ((w + 3) // 4) * ((h + 3) // 4) * 8


def dxt5_size(w: int, h: int) -> int:
    return ((w + 3) // 4) * ((h + 3) // 4) * 16


def rgb24_mip_size(w: int, h: int) -> int:
    total = 0
    while True:
        total += w * h * 3
        if w == 1 and h == 1:
            break
        w = max(1, w // 2)
        h = max(1, h // 2)
    return total


def decode_dxt1(data: bytes, offset: int, w: int, h: int) -> Image.Image:
    out = bytearray(w * h * 3)
    src = offset
    blocks_x = (w + 3) // 4
    blocks_y = (h + 3) // 4
    for by in range(blocks_y):
        for bx in range(blocks_x):
            c0 = int.from_bytes(data[src : src + 2], "little")
            c1 = int.from_bytes(data[src + 2 : src + 4], "little")
            bits = int.from_bytes(data[src + 4 : src + 8], "little")
            src += 8
            p0, p1 = rgb565(c0), rgb565(c1)
            if c0 > c1:
                palette = [p0, p1, lerp(p0, p1, 1, 3), lerp(p0, p1, 2, 3)]
            else:
                palette = [p0, p1, lerp(p0, p1, 1, 2), (0, 0, 0)]
            for py in range(4):
                for px in range(4):
                    x = bx * 4 + px
                    y = by * 4 + py
                    idx = (bits >> (2 * (py * 4 + px))) & 3
                    if x < w and y < h:
                        r, g, b = palette[idx]
                        i = (y * w + x) * 3
                        out[i : i + 3] = bytes((r, g, b))
    return Image.frombytes("RGB", (w, h), bytes(out))


def decode_dxt5(data: bytes, offset: int, w: int, h: int) -> Image.Image:
    # Color block is the last 8 bytes of each 16-byte DXT5 block.
    out = bytearray(w * h * 3)
    src = offset
    blocks_x = (w + 3) // 4
    blocks_y = (h + 3) // 4
    for by in range(blocks_y):
        for bx in range(blocks_x):
            c0 = int.from_bytes(data[src + 8 : src + 10], "little")
            c1 = int.from_bytes(data[src + 10 : src + 12], "little")
            bits = int.from_bytes(data[src + 12 : src + 16], "little")
            src += 16
            p0, p1 = rgb565(c0), rgb565(c1)
            if c0 > c1:
                palette = [p0, p1, lerp(p0, p1, 1, 3), lerp(p0, p1, 2, 3)]
            else:
                palette = [p0, p1, lerp(p0, p1, 1, 2), (0, 0, 0)]
            for py in range(4):
                for px in range(4):
                    x = bx * 4 + px
                    y = by * 4 + py
                    idx = (bits >> (2 * (py * 4 + px))) & 3
                    if x < w and y < h:
                        r, g, b = palette[idx]
                        i = (y * w + x) * 3
                        out[i : i + 3] = bytes((r, g, b))
    return Image.frombytes("RGB", (w, h), bytes(out))


def decode_bgr24(data: bytes, offset: int, w: int, h: int) -> Image.Image:
    raw = data[offset : offset + w * h * 3]
    return Image.frombytes("RGB", (w, h), raw, "raw", "BGR")


def pixel_stats(image: Image.Image) -> dict:
    rgb = image.convert("RGB")
    px = list(rgb.getdata())
    n = max(len(px), 1)
    mean = [sum(c[i] for c in px) / n for i in range(3)]
    mx = [max(c[i] for i in range(3)) for c in px]
    mn = [min(c[i] for i in range(3)) for c in px]
    sat = []
    for hi, lo, pix in zip(mx, mn, px):
        if hi == 0:
            sat.append(0.0)
        else:
            sat.append((hi - lo) / hi * 255.0)
    q = {(p[0] >> 3, p[1] >> 3, p[2] >> 3) for p in px}
    return {
        "size": list(image.size),
        "mean_rgb": [round(v, 1) for v in mean],
        "mean_sat": round(sum(sat) / n, 1),
        "unique_q5": len(q),
    }


def official_decode(src: Path, dest: Path) -> dict:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists():
        dest.unlink()
    cmd = [
        str(DOTNET),
        "run",
        "--project",
        str(CSPROJ),
        "-c",
        "Debug",
        "--no-build",
        "--",
        "--decode-image",
        str(src),
        str(dest),
    ]
    completed = subprocess.run(cmd, capture_output=True, text=True, timeout=90, check=False)
    ok = completed.returncode == 0 and dest.exists() and dest.stat().st_size > 0
    err = (completed.stderr or completed.stdout or "").strip().splitlines()
    return {
        "ok": ok,
        "returncode": completed.returncode,
        "error": err[-1] if err and not ok else None,
        "output": rel(dest) if ok else None,
    }


def list_bornbeast() -> list[dict]:
    rows = []
    for path in sorted(DATA.rglob("*")):
        if not path.is_file() or path.suffix.lower() != ".dtx":
            continue
        if "bornbeast" not in path.name.lower():
            continue
        size = path.stat().st_size
        rows.append(
            {
                "path": rel(path),
                "name": path.name,
                "size_bytes": size,
                "sha256": sha256_file(path) if size > 0 else None,
                "family": size_family(size),
                "empty": size == 0,
            }
        )
    return rows


def size_family(size: int) -> str:
    if size == 0:
        return "empty"
    if size == 524452:
        return "pv_bgr24_512x256_mip"
    if size == 32932:
        return "qv_dxt1_256x256_plus_164"
    if size == 131236:
        return "dxt1_512x512_plus_164"
    return f"other_{size}"


def specular_controls() -> list[Path]:
    found: list[Path] = []
    if N03G.exists():
        dump = json.loads(N03G.read_text(encoding="utf-8"))
        names = set()
        for row in dump.get("rows") or []:
            if not isinstance(row, dict):
                continue
            fields = row.get("fields") or {}
            for key, value in fields.items():
                if "SpecularMapName" not in key or not isinstance(value, str) or not value:
                    continue
                names.add(value.replace("\\", "/").split("/")[-1])
        spec_dir = DATA / "SpecularMap"
        for name in sorted(names):
            for cand in spec_dir.glob("*"):
                if cand.name.lower() == name.lower():
                    found.append(cand)
                    break
    spec_dir = DATA / "SpecularMap"
    if spec_dir.exists():
        for cand in sorted(spec_dir.iterdir()):
            if cand.is_file() and cand.suffix.lower() == ".dtx" and cand not in found:
                found.append(cand)
    for extra in CONTROLS_EXTRA:
        if extra.exists() and extra not in found:
            found.append(extra)
    return found


def layout_candidates(size: int) -> list[dict]:
    layouts = []
    dims = [
        (256, 256),
        (512, 256),
        (256, 512),
        (512, 512),
        (128, 128),
        (128, 256),
        (256, 128),
        (64, 256),
        (256, 64),
        (512, 64),
        (64, 512),
        (1024, 256),
        (256, 1024),
    ]
    offsets = [0, 4, 8, 12, 16, 32, 36, 160, 163, 164]
    kinds = [
        ("dxt1", dxt1_size, decode_dxt1),
        ("dxt5", dxt5_size, decode_dxt5),
        ("bgr24", lambda w, h: w * h * 3, decode_bgr24),
        ("bgr24_mip", rgb24_mip_size, decode_bgr24),
    ]
    for w, h in dims:
        for kind, sizer, decoder in kinds:
            payload = sizer(w, h)
            for offset in offsets:
                leftover = size - offset - payload
                if leftover < 0 or leftover > MAX_LEFTOVER:
                    continue
                layouts.append(
                    {
                        "kind": kind,
                        "w": w,
                        "h": h,
                        "offset": offset,
                        "payload": payload,
                        "leftover": leftover,
                        "decoder": decoder,
                    }
                )
    # Prefer exact leftover 0 then 163/164, smaller offsets first.
    layouts.sort(key=lambda item: (item["leftover"], item["offset"], item["kind"]))
    # Dedup identical decode geometry.
    seen = set()
    unique = []
    for item in layouts:
        key = (item["kind"], item["w"], item["h"], item["offset"])
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)
    return unique


def brute_decode(path: Path, stem: str, limit: int = 8) -> list[dict]:
    data = path.read_bytes()
    results = []
    for item in layout_candidates(len(data))[:limit]:
        try:
            image = item["decoder"](data, item["offset"], item["w"], item["h"])
        except Exception as exc:  # noqa: BLE001
            results.append({**{k: v for k, v in item.items() if k != "decoder"}, "ok": False, "error": str(exc)})
            continue
        name = f"{stem}_{item['kind']}_{item['w']}x{item['h']}_off{item['offset']}.png"
        dest = PREV / name
        image.save(dest)
        stats = pixel_stats(image)
        results.append(
            {
                "ok": True,
                "kind": item["kind"],
                "w": item["w"],
                "h": item["h"],
                "offset": item["offset"],
                "payload": item["payload"],
                "leftover": item["leftover"],
                "preview": rel(dest),
                "stats": stats,
            }
        )
    return results


def guess_class(stats: dict | None, official_ok: bool) -> str:
    if official_ok:
        return "official_ok"
    if not stats:
        return "undecodable"
    sat = stats.get("mean_sat") or 0
    unique = stats.get("unique_q5") or 0
    if sat >= 140 and unique < 400:
        return "scalar_or_energy"
    if sat <= 60 and unique >= 200:
        return "gun_atlas_candidate"
    if unique < 40:
        return "garbage"
    return "needs_visual"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    PREV.mkdir(parents=True, exist_ok=True)
    born = list_bornbeast()
    families = defaultdict(int)
    for row in born:
        families[row["family"]] += 1

    controls = specular_controls()
    official = []
    official_targets = []
    seen_paths = set()
    for path in [
        DATA / "WEAPONS" / "QV-M4A1_S_BornBeast.DTX",
        DATA / "PLAYERVIEW" / "PV-M4A1_S_BornBeast.DTX",
        *controls,
    ]:
        if path.exists() and str(path).lower() not in seen_paths:
            official_targets.append(path)
            seen_paths.add(str(path).lower())

    for path in official_targets:
        dest = PREV / f"official_{path.stem}.png"
        result = official_decode(path, dest)
        stats = pixel_stats(Image.open(dest)) if result["ok"] else None
        official.append(
            {
                "path": rel(path),
                "size_bytes": path.stat().st_size,
                "family": size_family(path.stat().st_size),
                "official": result,
                "stats": stats,
                "pixel_class_heuristic": guess_class(stats, result["ok"]),
            }
        )

    brute_targets = [
        DATA / "WEAPONS" / "QV-M4A1_S_BornBeast.DTX",
        DATA / "PLAYERVIEW" / "PV-M4A1-RoyalDragon_silencer.DTX",
        DATA / "SpecularMap" / "PV-DualDE_GreenVein_S.DTX",
        DATA / "PLAYERVIEW" / "PV-M4A1_RoyalDragon.DTX",
        DATA / "SpecularMap" / "PV-M4A1_RoyalDragon_s.DTX",
        DATA / "PLAYERVIEW" / "PV-M4A1_S_BornBeast.DTX",
    ]
    brute = []
    for path in brute_targets:
        if not path.exists() or path.stat().st_size == 0:
            continue
        # Skip brute if official already produced a real bitmap AND file is
        # not the QV subject. Always brute QV + 164-byte-pattern sizes.
        size = path.stat().st_size
        always = size in {32932, 131236, 524452} or path.name.upper().startswith("QV-M4A1_S_BORNBEAST")
        official_ok = any(item["path"] == rel(path) and item["official"]["ok"] for item in official)
        if official_ok and not always:
            continue
        brute.append(
            {
                "path": rel(path),
                "size_bytes": size,
                "family": size_family(size),
                "candidates": brute_decode(path, path.stem),
            }
        )

    report = {
        "schema": "cf2.p4m01.n03h-dtx-container.v1",
        "generated_at_utc": now(),
        "bornbeast_count": len(born),
        "families": dict(families),
        "official": official,
        "brute": brute,
        "note": "pixel_class_heuristic is not visual confirmation; report.md classifies after viewing previews",
    }
    (OUT / "decode.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "size_class.json").write_text(
        json.dumps({"bornbeast": born, "families": dict(families)}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"out": str(OUT), "bornbeast": len(born), "official": len(official), "brute": len(brute)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
