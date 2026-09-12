# -*- coding: utf-8 -*-
"""Lift base Transformers wrap for identity reading only.

Does not rewrite native DTX, does not change VMT, does not confirm identity.
"""
from __future__ import annotations

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "work" / "p5_leishen" / "t02_native"
GATE = OUT / "gate"
MESH = GATE / "mesh_base_Transformers.png"
ATLAS = GATE / "pv_dtx_base_Transformers.png"
OFFICIAL = GATE / "official_C0457.png"
BUY = GATE / "buyweapon_M4A1_S_TRANSFORMERS.png"
DEST = GATE / "expose"


def is_background(rgb: tuple[int, int, int], floor: int = 245) -> bool:
    return rgb[0] >= floor and rgb[1] >= floor and rgb[2] >= floor


def expose(image: Image.Image, gain: float, skip_white: bool) -> Image.Image:
    src = image.convert("RGBA")
    out = src.copy()
    pixels = out.load()
    width, height = out.size
    for y in range(height):
        for x in range(width):
            r, g, b, a = pixels[x, y]
            if skip_white and is_background((r, g, b)):
                continue
            pixels[x, y] = (
                min(255, int(round(r * gain))),
                min(255, int(round(g * gain))),
                min(255, int(round(b * gain))),
                a,
            )
    return out


def stretch_gun(image: Image.Image, skip_white: bool) -> Image.Image:
    src = image.convert("RGBA")
    lums = []
    pixels_in = list(src.getdata()) if hasattr(src, "getdata") else []
    raw = src.tobytes("raw", "RGBA")
    count = len(raw) // 4
    gun = []
    for i in range(count):
        r, g, b = raw[i * 4], raw[i * 4 + 1], raw[i * 4 + 2]
        if skip_white and is_background((r, g, b)):
            continue
        if r + g + b < 12:
            continue
        lums.append(0.2126 * r + 0.7152 * g + 0.0722 * b)
        gun.append(i)
    if len(lums) < 16:
        return src
    lums.sort()
    lo = lums[int(len(lums) * 0.05)]
    hi = lums[int(len(lums) * 0.98)]
    span = max(hi - lo, 1.0)
    out = bytearray(raw)
    for i in gun:
        r, g, b, a = raw[i * 4 : i * 4 + 4]
        t = (0.2126 * r + 0.7152 * g + 0.0722 * b - lo) / span
        t = 0.0 if t < 0 else 1.0 if t > 1 else t
        scale = (18 + t * 210) / max(0.2126 * r + 0.7152 * g + 0.0722 * b, 1.0)
        out[i * 4] = min(255, int(round(r * scale)))
        out[i * 4 + 1] = min(255, int(round(g * scale)))
        out[i * 4 + 2] = min(255, int(round(b * scale)))
    return Image.frombytes("RGBA", src.size, bytes(out))


def crop(image: Image.Image, box: tuple[int, int, int, int], dest: Path, label: str) -> None:
    piece = image.crop(box)
    piece = ImageOps.contain(piece, (420, 220), Image.Resampling.NEAREST)
    canvas = Image.new("RGB", (420, 248), (255, 255, 255))
    canvas.paste(piece.convert("RGB"), ((420 - piece.width) // 2, 8))
    ImageDraw.Draw(canvas).text((8, 228), label, fill=(20, 30, 42), font=ImageFont.load_default())
    dest.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(dest)


def sheet(cells: list[tuple[Path, str]], dest: Path, title: str) -> None:
    cell_w, cell_h = 640, 320
    columns = 2
    header = 48
    rows = (len(cells) + 1) // 2
    image = Image.new("RGB", (columns * cell_w, header + rows * cell_h), (236, 239, 244))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((14, 8), title, fill=(18, 28, 40), font=font)
    draw.text((14, 24), "Preview gain only. Native DTX unchanged. CANDIDATE_ONLY.", fill=(18, 28, 40), font=font)
    for index, (path, label) in enumerate(cells):
        left = (index % columns) * cell_w
        top = header + (index // columns) * cell_h
        tile = Image.new("RGB", (cell_w, cell_h), (255, 255, 255))
        if path.is_file():
            pic = Image.open(path).convert("RGBA")
            pic = ImageOps.contain(pic, (cell_w - 16, 268), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (cell_w, cell_h), (255, 255, 255, 255))
            canvas.alpha_composite(pic, ((cell_w - pic.width) // 2, 8))
            tile = canvas.convert("RGB")
        ImageDraw.Draw(tile).text((10, 292), label[:78], fill=(20, 30, 42), font=font)
        image.paste(tile, (left, top))
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)


def main() -> int:
    DEST.mkdir(parents=True, exist_ok=True)
    mesh = Image.open(MESH).convert("RGBA")
    atlas = Image.open(ATLAS).convert("RGBA")
    g2 = expose(mesh, 2.2, skip_white=True)
    g3 = expose(mesh, 3.2, skip_white=True)
    stretched = stretch_gun(mesh, skip_white=True)
    atlas3 = expose(atlas, 3.0, skip_white=False)
    g2.save(DEST / "mesh_base_gain2.png")
    g3.save(DEST / "mesh_base_gain3.png")
    stretched.save(DEST / "mesh_base_stretch.png")
    atlas3.save(DEST / "atlas_base_gain3.png")
    # Side-view gun is roughly x 40-730, y 70-330 on 768x384.
    crop(g3, (40, 80, 200, 300), DEST / "zoom_stock.png", "stock / Autobot mark  (gain 3.2, not native)")
    crop(g3, (200, 90, 430, 330), DEST / "zoom_receiver.png", "receiver / mag  (gain 3.2, not native)")
    crop(g3, (420, 110, 720, 280), DEST / "zoom_dragon.png", "barrel dragon  (gain 3.2, not native)")
    sheet(
        [
            (OFFICIAL, "OFFICIAL C0457.png  M4A1-雷神"),
            (BUY, "CF buy-menu  M4A1.S.TRANSFORMERS"),
            (MESH, "native wrap  (dark albedo, UV corrected)"),
            (DEST / "mesh_base_gain3.png", "SAME wrap  preview gain 3.2x  (not native pixels)"),
            (DEST / "zoom_dragon.png", "dragon zoom"),
            (DEST / "zoom_stock.png", "stock zoom"),
        ],
        DEST / "expose_sheet.png",
        "P5-T02 base Transformers — exposure for identity reading only",
    )
    report = {
        "identity_status": "CANDIDATE_ONLY",
        "native_pixels_changed": False,
        "purpose": "user could not confirm dark wrap; lift preview only",
        "gains": [2.2, 3.2, "percentile_stretch"],
        "sheet": "work/p5_leishen/t02_native/gate/expose/expose_sheet.png",
    }
    (DEST / "expose.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
