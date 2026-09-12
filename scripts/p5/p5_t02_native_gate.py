# -*- coding: utf-8 -*-
"""Curate P5-T02 user-gate images. Does not write IDENTITY_CONFIRMED."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont, ImageOps

from p5_t02_native_inventory import (  # noqa: E402
    BORNBEAST_ATLAS,
    DATA,
    MESH_DIR,
    OUT,
    REPO,
    decode_ltb_geometry,
    rel,
    render_textured,
)

GATE = OUT / "gate"
STAGING_LTB = DATA / "p5_t02_native" / "ltb"
BASE_ATLAS = OUT / "atlases" / "pv_dtx_PV-M4A1_S_TRANSFORMERS_PC_7ca69f66.png"
CLASSIC_ATLAS = OUT / "atlases" / "pv_dtx_PV-M4A1_S_TRANSFORMERS_CLASSIC.png"
BUYWEAPON = OUT / "atlases" / "other_dtx_BUYWEAPON_INFO_M4A1_S_TRANSFORMERS.png"
SHOT = OUT / "atlases" / "other_dtx_SHOT_WEAPON_M4A1_S_TRANSFORMERS.png"
OFFICIAL = OUT / "official_C0457.png"
BASE_LTB = STAGING_LTB / "PV-M4A1_S_TRANSFORMERS_a0ccef5deed7.ltb"
CLASSIC_LTB = STAGING_LTB / "PV-M4A1_S_TRANSFORMERS_TLAND_620778d78577.ltb"


def copy(src: Path, dest: Path) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)


def render_one(ltb: Path, atlas: Path, dest: Path, label: str) -> dict:
    work = DATA / "p5_t02_native" / "geom"
    work.mkdir(parents=True, exist_ok=True)
    document = decode_ltb_geometry(ltb, work)
    with Image.open(atlas) as image:
        texture = image.convert("RGBA").copy()
    dest.parent.mkdir(parents=True, exist_ok=True)
    return render_textured(document, texture, dest, label)


def sheet(rows: list[tuple[Path, str]], dest: Path) -> None:
    cell_w, cell_h = 640, 340
    columns = 2
    header = 56
    rows_n = (len(rows) + columns - 1) // columns
    image = Image.new("RGB", (columns * cell_w, header + rows_n * cell_h), (236, 239, 244))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((16, 10), "P5-T02 user gate — CANDIDATE_ONLY  (M4A1-雷神 = official C0457.png)", fill=(18, 28, 40), font=font)
    draw.text((16, 28), "BornBeast is 黑骑士 negative control. Filename Transformers is not identity.", fill=(18, 28, 40), font=font)
    for index, (path, label) in enumerate(rows):
        left = (index % columns) * cell_w
        top = header + (index // columns) * cell_h
        tile = Image.new("RGB", (cell_w, cell_h), (255, 255, 255))
        tile_draw = ImageDraw.Draw(tile)
        if path.is_file():
            pic = Image.open(path).convert("RGBA")
            pic = ImageOps.contain(pic, (cell_w - 16, 292), Image.Resampling.LANCZOS)
            canvas = Image.new("RGBA", (cell_w, cell_h), (255, 255, 255, 255))
            canvas.alpha_composite(pic, ((cell_w - pic.width) // 2, 8))
            tile = canvas.convert("RGB")
            tile_draw = ImageDraw.Draw(tile)
        tile_draw.text((10, 312), label[:78], fill=(20, 30, 42), font=font)
        image.paste(tile, (left, top))
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)


def main() -> int:
    GATE.mkdir(parents=True, exist_ok=True)
    MESH_DIR.mkdir(parents=True, exist_ok=True)
    copy(OFFICIAL, GATE / "official_C0457.png")
    copy(BUYWEAPON, GATE / "buyweapon_M4A1_S_TRANSFORMERS.png")
    copy(SHOT, GATE / "shot_M4A1_S_TRANSFORMERS.png")
    copy(BASE_ATLAS, GATE / "pv_dtx_base_Transformers.png")
    copy(CLASSIC_ATLAS, GATE / "pv_dtx_Classic.png")
    copy(BORNBEAST_ATLAS, GATE / "neg_bornbeast_NOT_leishen.png")
    base_mesh = MESH_DIR / "PV-M4A1_S_TRANSFORMERS_base.png"
    classic_mesh = MESH_DIR / "PV-M4A1_S_TRANSFORMERS_CLASSIC.png"
    reports = {
        "base_mesh": render_one(
            BASE_LTB, BASE_ATLAS, base_mesh, "base PV-M4A1_S_Transformers LTB + verified DTX"
        ),
        "classic_mesh": render_one(
            CLASSIC_LTB, CLASSIC_ATLAS, classic_mesh, "Classic LTB SHA family + Classic DTX"
        ),
    }
    copy(base_mesh, GATE / "mesh_base_Transformers.png")
    copy(classic_mesh, GATE / "mesh_Classic.png")
    sheet(
        [
            (GATE / "official_C0457.png", "OFFICIAL 图鉴 C0457.png  M4A1-雷神  (user T01 confirmed)"),
            (GATE / "buyweapon_M4A1_S_TRANSFORMERS.png", "CF buy-menu icon  M4A1.S.TRANSFORMERS  (UI, not PV diffuse)"),
            (GATE / "pv_dtx_base_Transformers.png", "Verified PV DTX  base==PC  SHA 7ca69f66  (native albedo)"),
            (GATE / "mesh_base_Transformers.png", "Base PV LTB SHA a0ccef5d + base DTX  (orthographic UV wrap)"),
            (GATE / "pv_dtx_Classic.png", "Verified PV DTX  Classic  (brighter silver/blue same layout)"),
            (GATE / "mesh_Classic.png", "Classic geometry family + Classic DTX"),
            (GATE / "neg_bornbeast_NOT_leishen.png", "NEG  BornBeast PV DTX  黑骑士  NOT 雷神"),
            (GATE / "shot_M4A1_S_TRANSFORMERS.png", "CF kill-icon  Transformers  (tiny HUD, supporting only)"),
        ],
        GATE / "gate_sheet.png",
    )
    reports["gate_sheet"] = rel(GATE / "gate_sheet.png")
    reports["identity_status"] = "CANDIDATE_ONLY"
    reports["note"] = (
        "Base PV DTX MD5 matches Transformers_PC; rf017 numbered-part and rez3 main-file are the same bytes. "
        "Classic LTB SHA matches TLand cluster 620778d7. UI icons are not PV diffuse."
    )
    (GATE / "gate.json").write_text(json.dumps(reports, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"out": rel(GATE), "base_mesh": reports["base_mesh"]["preview"], "classic_mesh": reports["classic_mesh"]["preview"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
