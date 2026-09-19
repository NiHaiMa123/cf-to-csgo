# -*- coding: utf-8 -*-
"""Phase F driver: Source 1 translation for the reference weapon.

Outputs under material_v2/source_v2/:
  - composite PNGs (base+phong alpha, normal+env alpha)
  - VTF set (VTFCmd)
  - VMT set (one per material slot)
  - g_material_assignments.json (piece -> local tri -> slot material)
  - translation_report.json + f_gate.json
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import source1_material_translator as s1t  # noqa: E402

WORK = _REPO / "work" / "mauser_libra"
MV2 = WORK / "material_v2"
UP = MV2 / "upscale"
SEG = MV2 / "segmentation"
OUT = MV2 / "source_v2"

GAME = Path("D:/steam/steamapps/common/csgo legacy")
VTFCMD = _REPO / "tools" / "VTFEdit" / "VTFCmd.exe"

MATERIAL_ROOT = "models/weapons/v_models/cf_mauser"
BASE_NAME = "cf_mauser_libra"
NORMAL_NAME = "cf_mauser_libra_n"
ENV_CUBE_NAME = "cf_env_cube"
CUBE_DDS = WORK / "decode" / "maps" / "LobbyCube.DDS"
SIZE = (2048, 2048)


def vtfcmd(png: Path, dest: Path, fmt: str, flags: tuple[str, ...] = (),
           nomip: bool = False) -> None:
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(VTFCMD), "-file", str(png), "-output", str(dest.parent),
           "-format", fmt, "-alphaformat", fmt, "-version", "7.4"]
    if nomip:
        cmd.append("-nomipmaps")
    for fl in flags:
        cmd += ["-flag", fl]
    proc = subprocess.run(cmd, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")
    produced = dest.parent / (png.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed for {png.name}: {proc.stderr or proc.stdout}")
    if produced != dest:
        produced.replace(dest)


def vtf_header(path: Path) -> dict:
    b = path.read_bytes()[:80]
    import struct
    w, h = struct.unpack_from("<HH", b, 16)
    flags = struct.unpack_from("<I", b, 20)[0]
    frames = struct.unpack_from("<H", b, 24)[0]
    fmt = struct.unpack_from("<I", b, 52)[0]
    mip = b[56]
    return {"w": w, "h": h, "fmt": fmt, "flags": hex(flags),
            "frames": frames, "mips": mip}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    ir = json.loads((MV2 / "ir" / "cf_mauser_libra.material_ir.json")
                    .read_text(encoding="utf-8"))
    regions = json.loads((SEG / "triangle_materials.json")
                         .read_text(encoding="utf-8"))
    maps = {
        "diffuse": UP / "diffuse_2048.png",
        "normal": UP / "normal_2048.png",
        "specular": UP / "specular_2048.png",
        "alpha": UP / "alpha_2048.png",
    }
    transform_y = float(ir["cfg"]["flat"].get("CubeMapTransformY", 0.0) or 0.0)
    res = s1t.translate(ir, regions, maps, MATERIAL_ROOT, BASE_NAME,
                        NORMAL_NAME, OUT, SIZE, envmap_texture=ENV_CUBE_NAME)

    if s1t.UNLIT_BAKE:
        # everything folded into one bright base texture (tulong class)
        bake_stats = s1t.bake_unlit_base(
            maps, ir["cfg"]["flat"], CUBE_DDS, transform_y, SIZE,
            OUT / f"{BASE_NAME}.png")
        res["report"]["unlit_bake"] = bake_stats
        for stale in (NORMAL_NAME, f"{BASE_NAME}_lightwarp", ENV_CUBE_NAME):
            (OUT / f"{stale}.vtf").unlink(missing_ok=True)
    else:
        s1t.bake_env_cube(CUBE_DDS, transform_y, OUT / f"{ENV_CUBE_NAME}.vtf")
        base = Image.open(UP / "diffuse_2048.png").convert("RGB")
        phong = Image.open(OUT / "mask_phong.png").convert("L")
        base_rgba = base.copy()
        base_rgba.putalpha(phong)
        base_rgba.save(OUT / f"{BASE_NAME}.png")
        nrm = Image.open(UP / "normal_2048.png").convert("RGB")
        env = Image.open(OUT / "mask_env.png").convert("L")
        nrm_rgba = nrm.copy()
        nrm_rgba.putalpha(env)
        nrm_rgba.save(OUT / f"{NORMAL_NAME}.png")
        vtfcmd(OUT / f"{NORMAL_NAME}.png", OUT / f"{NORMAL_NAME}.vtf", "dxt5",
               ("TRILINEAR", "ANISOTROPIC", "NORMAL"))
        vtfcmd(OUT / f"{BASE_NAME}_lightwarp.png",
               OUT / f"{BASE_NAME}_lightwarp.vtf", "bgr888",
               ("POINTSAMPLE", "CLAMPS", "CLAMPT", "NOMIP", "NOLOD"),
               nomip=True)
    vtfcmd(OUT / f"{BASE_NAME}.png", OUT / f"{BASE_NAME}.vtf", "bgra8888",
           ("TRILINEAR", "ANISOTROPIC"))
    for slot, vmt in res["vmts"].items():
        (OUT / f"{slot}.vmt").write_text(vmt, encoding="utf-8")
    # fallback material for any triangle outside the region table
    if s1t.UNLIT_BAKE:
        fallback_vmt = s1t.unlit_vmt(MATERIAL_ROOT, BASE_NAME)
    else:
        fallback_vmt = s1t.vertexlit_vmt(
            MATERIAL_ROOT, BASE_NAME, NORMAL_NAME, BASE_NAME,
            "controlled_phong", ir["cfg"]["flat"],
            res["report"]["phong_tint"], None,
            lightwarp_name=f"{BASE_NAME}_lightwarp",
            envmap_texture=ENV_CUBE_NAME)
    (OUT / f"{BASE_NAME}.vmt").write_text(fallback_vmt, encoding="utf-8")

    # Phase G assignment table: piece -> local tri -> slot material
    region_to_slot = {s["region_id"]: s["material"] for s in res["slots"]}
    assignments = {}
    for piece, tris in regions["triangle_materials"].items():
        assignments[piece] = {t: region_to_slot[r] for t, r in tris.items()}
    (MV2 / "g_material_assignments.json").write_text(
        json.dumps(assignments, indent=1), encoding="utf-8")

    res["report"]["vtf"] = {"base": vtf_header(OUT / f"{BASE_NAME}.vtf")}
    if not s1t.UNLIT_BAKE:
        res["report"]["vtf"].update({
            "normal": vtf_header(OUT / f"{NORMAL_NAME}.vtf"),
            "lightwarp": vtf_header(OUT / f"{BASE_NAME}_lightwarp.vtf"),
            "env_cube": vtf_header(OUT / f"{ENV_CUBE_NAME}.vtf")})
    (OUT / "translation_report.json").write_text(
        json.dumps(res["report"], indent=1, ensure_ascii=False), encoding="utf-8")

    # F gate
    problems = []
    n_slots = len(res["slots"])
    if n_slots != len(regions["regions"]):
        problems.append(f"slot count {n_slots} != regions {len(regions['regions'])}")
    for slot, vmt in res["vmts"].items():
        if f'"$basetexture" "{MATERIAL_ROOT}/{BASE_NAME}"' not in vmt:
            problems.append(f"{slot}: basetexture missing")
        if '"$envmap"' in vmt and 'env_cubemap' not in vmt \
                and ENV_CUBE_NAME not in vmt:
            problems.append(f"{slot}: unexpected envmap bound")
        if "LobbyCube" in vmt:
            problems.append(f"{slot}: raw CF cubemap bound at runtime")
    if not s1t.UNLIT_BAKE:
        env_slots = [s for s in res["slots"] if s["strategy"] == "envmap_metal"]
        if not env_slots:
            problems.append("no envmap_metal slot despite env_reflective regions")
    for key in ("preserved", "approximated", "lost", "unsupported_by_source1"):
        if key not in res["report"]["tags"]:
            problems.append(f"tags missing {key}")
    gate = {"passed": not problems, "problems": problems,
            "slots": {s["material"]: s["strategy"] for s in res["slots"]}}
    (OUT / "f_gate.json").write_text(
        json.dumps(gate, indent=1, ensure_ascii=False), encoding="utf-8")
    print("F gate:", "PASS" if gate["passed"] else "FAIL", problems)
    for s in res["slots"]:
        print(f"  {s['material']}: {s['strategy']} "
              f"({s['region_label']}, {s['triangles']} tris)")
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
