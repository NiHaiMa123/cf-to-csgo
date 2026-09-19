# -*- coding: utf-8 -*-
"""Orthographic UV preview of the CF BornBeast mesh with a given albedo.

CPU diagnostic only. Not a Source 1 / CF shader recreation.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

VERIFY = Path(__file__).resolve().parent
ROOT = VERIFY.parents[2]
OBJ = ROOT / (
    "work/m4a1_s_bornbeast/source_dump/c1_split/weapon_only/"
    "PV-M4A1_S_BornBeast_Classic_weapon_only.obj"
)

WIDTH = 960
HEIGHT = 420
MARGIN = 24
HEADER = 28


def parse_obj(path: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    positions: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    faces: list[tuple[tuple[int, int], tuple[int, int], tuple[int, int]]] = []
    for raw in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if raw.startswith("v "):
            _, x, y, z = raw.split()[:4]
            positions.append((float(x), float(y), float(z)))
        elif raw.startswith("vt "):
            parts = raw.split()
            uvs.append((float(parts[1]), float(parts[2])))
        elif raw.startswith("f "):
            corners = []
            for token in raw.split()[1:]:
                bits = token.split("/")
                vi = int(bits[0]) - 1
                ti = int(bits[1]) - 1 if len(bits) > 1 and bits[1] else vi
                corners.append((vi, ti))
            for i in range(1, len(corners) - 1):
                faces.append((corners[0], corners[i], corners[i + 1]))
    pos = np.asarray(positions, dtype=np.float32)
    uv = np.asarray(uvs, dtype=np.float32)
    idx = np.asarray(faces, dtype=np.int32)
    return pos, uv, idx


def project(pos: np.ndarray, view: str) -> np.ndarray:
    x, y, z = pos[:, 0], pos[:, 1], pos[:, 2]
    if view == "side":
        px, py = z, y
    elif view == "three_quarter":
        px, py = 0.82 * z + 0.55 * x, y
    elif view == "top":
        px, py = z, -x
    else:
        raise ValueError(view)
    return np.stack([px, py], axis=1)


def rasterize(pos: np.ndarray, uv: np.ndarray, faces: np.ndarray, texture: Image.Image, view: str, label: str) -> Image.Image:
    pts = project(pos, view)
    min_xy = pts.min(axis=0)
    max_xy = pts.max(axis=0)
    span = np.maximum(max_xy - min_xy, 1e-6)
    scale = min((WIDTH - 2 * MARGIN) / span[0], (HEIGHT - HEADER - 2 * MARGIN) / span[1])
    offset = np.array(
        [
            (WIDTH - span[0] * scale) / 2.0,
            HEADER + (HEIGHT - HEADER - span[1] * scale) / 2.0,
        ],
        dtype=np.float32,
    )
    screen = np.empty_like(pts)
    screen[:, 0] = offset[0] + (pts[:, 0] - min_xy[0]) * scale
    screen[:, 1] = offset[1] + (max_xy[1] - pts[:, 1]) * scale
    depth = project_depth(pos, view)

    tex = np.asarray(texture.convert("RGB"), dtype=np.uint8)
    th, tw = tex.shape[0], tex.shape[1]
    color = np.zeros((HEIGHT, WIDTH, 3), dtype=np.uint8)
    color[:] = (18, 20, 24)
    zbuf = np.full((HEIGHT, WIDTH), -1e9, dtype=np.float32)

    for a, b, c in faces:
        (ia, ta), (ib, tb), (ic, tc) = a, b, c
        pa, pb, pc = screen[ia], screen[ib], screen[ic]
        za, zb, zc = float(depth[ia]), float(depth[ib]), float(depth[ic])
        ua, va = uv[ta]
        ub, vb = uv[tb]
        uc, vc = uv[tc]
        minx = max(0, int(np.floor(min(pa[0], pb[0], pc[0]))))
        maxx = min(WIDTH - 1, int(np.ceil(max(pa[0], pb[0], pc[0]))))
        miny = max(HEADER, int(np.floor(min(pa[1], pb[1], pc[1]))))
        maxy = min(HEIGHT - 1, int(np.ceil(max(pa[1], pb[1], pc[1]))))
        if minx > maxx or miny > maxy:
            continue
        denom = (pb[1] - pc[1]) * (pa[0] - pc[0]) + (pc[0] - pb[0]) * (pa[1] - pc[1])
        if abs(denom) < 1e-8:
            continue
        xs = np.arange(minx, maxx + 1, dtype=np.float32) + 0.5
        ys = np.arange(miny, maxy + 1, dtype=np.float32) + 0.5
        grid_x, grid_y = np.meshgrid(xs, ys)
        w0 = ((pb[1] - pc[1]) * (grid_x - pc[0]) + (pc[0] - pb[0]) * (grid_y - pc[1])) / denom
        w1 = ((pc[1] - pa[1]) * (grid_x - pc[0]) + (pa[0] - pc[0]) * (grid_y - pc[1])) / denom
        w2 = 1.0 - w0 - w1
        mask = (w0 >= -1e-5) & (w1 >= -1e-5) & (w2 >= -1e-5)
        if not np.any(mask):
            continue
        zpix = w0 * za + w1 * zb + w2 * zc
        region = zbuf[miny : maxy + 1, minx : maxx + 1]
        nearer = mask & (zpix >= region)
        if not np.any(nearer):
            continue
        su = w0 * ua + w1 * ub + w2 * uc
        sv = 1.0 - (w0 * va + w1 * vb + w2 * vc)
        su = np.clip(su, 0.0, 1.0)
        sv = np.clip(sv, 0.0, 1.0)
        tx = np.clip((su * (tw - 1)).astype(np.int32), 0, tw - 1)
        ty = np.clip((sv * (th - 1)).astype(np.int32), 0, th - 1)
        sampled = tex[ty, tx]
        dest = color[miny : maxy + 1, minx : maxx + 1]
        dest[nearer] = sampled[nearer]
        region[nearer] = zpix[nearer]

    image = Image.fromarray(color, "RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.rectangle((0, 0, WIDTH, HEADER), fill=(10, 12, 14))
    draw.text((10, 8), label, fill=(230, 230, 230), font=font)
    return image


def project_depth(pos: np.ndarray, view: str) -> np.ndarray:
    if view == "side":
        return pos[:, 0]
    if view == "three_quarter":
        return 0.55 * pos[:, 2] - 0.82 * pos[:, 0]
    if view == "top":
        return pos[:, 1]
    raise ValueError(view)


def load_texture(path: Path) -> Image.Image:
    return Image.open(path).convert("RGB")


def render_set(name: str, texture_path: Path, pos, uv, faces, views: list[str]) -> list[Path]:
    out_dir = VERIFY / "renders"
    out_dir.mkdir(parents=True, exist_ok=True)
    texture = load_texture(texture_path)
    written: list[Path] = []
    for view in views:
        dest = out_dir / f"{name}_{view}.png"
        image = rasterize(pos, uv, faces, texture, view, f"{name} | {view}")
        image.save(dest)
        written.append(dest)
    return written


def make_sheet(rows: list[tuple[str, Path]]) -> Path:
    views = ["side", "three_quarter"]
    tiles: list[list[Image.Image]] = []
    for name, _tex in rows:
        row = []
        for view in views:
            path = VERIFY / "renders" / f"{name}_{view}.png"
            row.append(Image.open(path).convert("RGB"))
        tiles.append(row)
    tw, th = tiles[0][0].size
    sheet = Image.new("RGB", (tw * len(views), th * len(tiles)), (8, 8, 10))
    for r, row in enumerate(tiles):
        for c, im in enumerate(row):
            sheet.paste(im, (c * tw, r * th))
    dest = VERIFY / "comparison_sheet.png"
    sheet.save(dest)
    return dest


def main() -> int:
    pos, uv, faces = parse_obj(OBJ)
    views = ["side", "three_quarter"]
    jobs = [
        ("native_dtx", VERIFY / "native_dtx.png"),
        ("cs16_atlas", VERIFY / "cs16_atlas.png"),
        ("shop_icon", VERIFY / "shop_icon.png"),
    ]
    comfy = VERIFY / "comfy_atlas.png"
    if comfy.exists():
        jobs.append(("comfy_atlas", comfy))
    written = []
    for name, path in jobs:
        if not path.exists():
            continue
        written.extend(render_set(name, path, pos, uv, faces, views))
    sheet = make_sheet([(name, path) for name, path in jobs if path.exists()])
    report = {
        "obj": str(OBJ),
        "vertex_count": int(pos.shape[0]),
        "triangle_count": int(faces.shape[0]),
        "renders": [str(p.relative_to(ROOT)).replace("\\", "/") for p in written],
        "sheet": str(sheet.relative_to(ROOT)).replace("\\", "/"),
        "note": "visual experiment only; comfy/cs16/shop pixels are not P4-M01 native material",
    }
    (VERIFY / "render_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
