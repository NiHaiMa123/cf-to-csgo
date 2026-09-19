# -*- coding: utf-8 -*-
"""Phase A driver for the reference weapon (material reconstruction v2).

A1: input closure -> audit/input_manifest.json (+ gate)
A2: mesh/UV/diffuse compatibility -> emission render + UV overlay + report

Blender renders go through scripts/cf_ltb/blender_mcp_exec.py execute_code.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import input_manifest  # noqa: E402

WORK = _REPO / "work" / "cop357_snowfox"
MV2 = WORK / "material_v2"
AUDIT = MV2 / "audit"
VERIFIED = WORK / "acquire" / "verified_root"
DECODE = WORK / "decode"
SKIN = DECODE / "cf_skin_cop357_winter.json"
DIFFUSE = DECODE / "PV-Cop357_IronBeast2_Winter.png"

# Pieces bound to the weapon atlas. Hand/arm meshes use a different material.
WEAPON_MESH_PREFIXES = ("Fview", "FVIEW")


def a1() -> dict:
    acquisition = input_manifest.load_acquisition(WORK / "acquire" / "acquisition.json")
    assets = [
        {"role": "mesh_ltb", "path": VERIFIED / "Models/PLAYERVIEW/PV-Cop357_IronBeast2_Winter.LTB",
         "logical_path": "Models/PLAYERVIEW/PV-Cop357_IronBeast2_Winter.LTB"},
        {"role": "diffuse_dtx", "path": VERIFIED / "ModelTextures/PLAYERVIEW/PV-Cop357_IronBeast2_Winter.DTX",
         "logical_path": "ModelTextures/PLAYERVIEW/PV-Cop357_IronBeast2_Winter.DTX"},
        {"role": "cfg", "path": VERIFIED / "ModelTextures/Shader/WeaponShader/Cop357_IronBeast2_Winter.CFG",
         "logical_path": "ModelTextures/Shader/WeaponShader/Cop357_IronBeast2_Winter.CFG"},
        {"role": "specular", "path": VERIFIED / "ModelTextures/SpecularMap/Cop357_IronBeast2_Winter_S.PNG",
         "logical_path": "ModelTextures/SpecularMap/Cop357_IronBeast2_Winter_S.PNG"},
        {"role": "normal", "path": VERIFIED / "ModelTextures/NormalMap/Cop357_IronBeast2_Winter_N.PNG",
         "logical_path": "ModelTextures/NormalMap/Cop357_IronBeast2_Winter_N.PNG"},
        {"role": "alpha", "path": VERIFIED / "ModelTextures/AlphaMap/Cop357_IronBeast2_Winter_A.PNG",
         "logical_path": "ModelTextures/AlphaMap/Cop357_IronBeast2_Winter_A.PNG"},
        {"role": "cubemap", "path": VERIFIED / "ModelTextures/EnvCubeMap/LobbyCube.DDS",
         "logical_path": "ModelTextures/EnvCubeMap/LobbyCube.DDS"},
        {"role": "diffuse_decoded", "path": DIFFUSE, "required": True,
         "derived": True, "derived_from": "diffuse_dtx"},
        {"role": "mesh_skin", "path": SKIN, "required": True,
         "derived": True, "derived_from": "mesh_ltb"},
        {"role": "mesh_ltb_bl", "path": VERIFIED / "Models/PLAYERVIEW/PV-Cop357_IronBeast2_Winter_BL.LTB",
         "logical_path": "Models/PLAYERVIEW/PV-Cop357_IronBeast2_Winter_BL.LTB", "required": False},
        {"role": "mesh_ltb_gr", "path": VERIFIED / "Models/PLAYERVIEW/PV-Cop357_IronBeast2_Winter_GR.LTB",
         "logical_path": "Models/PLAYERVIEW/PV-Cop357_IronBeast2_Winter_GR.LTB", "required": False},
    ]
    manifest = input_manifest.build_input_manifest(
        weapon="Cop357_IronBeast2_Winter", material_id="cf_cop357_winter",
        assets=assets, out_path=AUDIT / "input_manifest.json",
        acquisition=acquisition)
    print("A1 gate:", "PASS" if manifest["a1_gate"]["passed"] else "FAIL",
          manifest["a1_gate"]["problems"])
    return manifest


def _weapon_meshes(skin: dict) -> list[dict]:
    return [m for m in skin["meshes"]
            if not m["name"].lower().startswith(("fview", "fview-"))]


def a2_offline_stats() -> dict:
    """Triangle UV -> diffuse sampling statistics (no renderer needed)."""
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    diffuse = Image.open(DIFFUSE).convert("RGB")
    px = diffuse.load()
    W, H = diffuse.size
    report = {"diffuse": str(DIFFUSE), "diffuse_size": [W, H], "meshes": []}
    total_tris = 0
    black_tris = 0
    out_tris = 0
    for mesh in _weapon_meshes(skin):
        tris = mesh["triangles"]
        uvs = mesh["uvs"]
        n_tris = len(tris) // 3
        m_black = m_out = 0
        lums = []
        for t in range(n_tris):
            us, vs = [], []
            for k in range(3):
                u, v = uvs[2 * tris[3 * t + k]], uvs[2 * tris[3 * t + k] + 1]
                us.append(u)
                vs.append(1.0 - v)  # single global v flip, pipeline 4.2
            cu, cv = sum(us) / 3.0, sum(vs) / 3.0
            if not (0.0 <= cu <= 1.0 and 0.0 <= cv <= 1.0):
                m_out += 1
                continue
            r, g, b = px[min(W - 1, max(0, int(cu * W))), min(H - 1, max(0, int(cv * H)))]
            lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
            lums.append(lum)
            if lum < 8.0:
                m_black += 1
        total_tris += n_tris
        black_tris += m_black
        out_tris += m_out
        report["meshes"].append({
            "name": mesh["name"],
            "triangles": n_tris,
            "uv_out_of_range": m_out,
            "centroid_on_near_black": m_black,
            "sampled_lum_mean": round(sum(lums) / len(lums), 2) if lums else None,
            "sampled_lum_min": round(min(lums), 2) if lums else None,
            "sampled_lum_max": round(max(lums), 2) if lums else None,
        })
    report["total"] = {
        "triangles": total_tris,
        "uv_out_of_range": out_tris,
        "centroid_on_near_black": black_tris,
        "near_black_fraction": round(black_tris / max(1, total_tris), 4),
    }
    return report


def a2_uv_overlay() -> Path:
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    base = Image.open(DIFFUSE).convert("RGB")
    W, H = base.size
    overlay = base.copy()
    draw = ImageDraw.Draw(overlay)
    for mesh in _weapon_meshes(skin):
        tris, uvs = mesh["triangles"], mesh["uvs"]
        for t in range(len(tris) // 3):
            pts = []
            for k in range(3):
                u, v = uvs[2 * tris[3 * t + k]], uvs[2 * tris[3 * t + k] + 1]
                pts.append((u * W, (1.0 - v) * H))
            draw.polygon(pts, outline=(0, 255, 0))
    out = AUDIT / "uv_overlay.png"
    overlay.save(out)
    return out


def a2_gate(report: dict) -> dict:
    total = report["total"]
    problems = []
    if total["uv_out_of_range"] > 0:
        problems.append(f"{total['uv_out_of_range']} triangle centroids outside [0,1] UV")
    if total["near_black_fraction"] > 0.5:
        problems.append(
            f"{total['near_black_fraction']:.1%} of triangle centroids sample "
            "near-black atlas background; mesh/atlas pairing suspect")
    return {"passed": not problems, "problems": problems,
            "requires_visual_review": True,
            "visual_evidence": ["emission_reference.png", "uv_overlay.png"]}


def main() -> int:
    AUDIT.mkdir(parents=True, exist_ok=True)
    manifest = a1()
    if not manifest["a1_gate"]["passed"]:
        print("A1 gate failed; stop per plan.md")
        return 1
    report = a2_offline_stats()
    overlay = a2_uv_overlay()
    report["a2_gate"] = a2_gate(report)
    report["artifacts"] = {"uv_overlay": str(overlay)}
    (AUDIT / "mesh_uv_diffuse_report.json").write_text(
        json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    print("A2 offline:", json.dumps(report["total"]),
          "gate:", "PASS(auto)" if report["a2_gate"]["passed"] else "FAIL")
    print("Next: Blender emission render via blender_mcp_exec (a2_blender_emission.py)")
    return 0 if report["a2_gate"]["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
