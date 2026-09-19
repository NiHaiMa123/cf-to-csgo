# -*- coding: utf-8 -*-
"""Phase B driver: B1 CFG->IR, B2 channel audit for the reference weapon."""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import channel_audit  # noqa: E402
import material_ir  # noqa: E402

WORK = _REPO / "work" / "cop357_snowfox"
MV2 = WORK / "material_v2"
VERIFIED = WORK / "acquire" / "verified_root"
DECODE = WORK / "decode"
MAPS = DECODE / "maps"
SKIN = DECODE / "cf_skin_cop357_winter.json"

CFG = VERIFIED / "ModelTextures/Shader/WeaponShader/Cop357_IronBeast2_Winter.CFG"
DIFFUSE = DECODE / "PV-Cop357_IronBeast2_Winter.png"
SPECULAR = MAPS / "Cop357_IronBeast2_Winter_S.PNG"
NORMAL = MAPS / "Cop357_IronBeast2_Winter_N.PNG"
ALPHA = MAPS / "Cop357_IronBeast2_Winter_A.PNG"
CUBEMAP = MAPS / "LobbyCube.DDS"


def b1() -> dict:
    ir = material_ir.new_ir("cf_cop357_winter", shader_family="unclassified")
    sha = hashlib.sha256(CFG.read_bytes()).hexdigest()
    material_ir.attach_cfg(ir, CFG, sha256=sha)
    flat = ir["cfg"]["flat"]
    for key, value in flat.items():
        material_ir.mark_observed(
            ir, f"cfg.{key}", value,
            evidence=f"CFG raw value, sha256={sha[:16]}")

    # Prior-round conclusions are INFERRED hints only (plan: do not inherit
    # unverified); Phase C must prove or reject them on this weapon.
    material_ir.mark_inferred(
        ir, "channel_semantics.alphamap.r", "opacity",
        basis="prior shader-family research; needs Phase C re-verification",
        confidence="medium")
    material_ir.mark_inferred(
        ir, "channel_semantics.alphamap.g", "specular intensity mask",
        basis="prior shader-family research; needs Phase C re-verification",
        confidence="medium")
    material_ir.mark_inferred(
        ir, "channel_semantics.alphamap.b", "env cubemap intensity mask",
        basis="prior shader-family research; needs Phase C re-verification",
        confidence="medium")
    material_ir.mark_inferred(
        ir, "sampling_semantics.spec_exponent", "SpecularPower * 0.25",
        basis="prior compiled-shader formula; needs Phase C re-verification",
        confidence="medium")
    material_ir.mark_unknown(
        ir, "sampling_semantics.cubemap_ray",
        "exact reflect/refract ray construction and CubeMapTransformY=220 "
        "rotation semantics unproven")
    material_ir.mark_unknown(
        ir, "sampling_semantics.env_cube_usage_2",
        "EnvCubeUsage=2 selects a shader variant; exact branch unproven")
    material_ir.mark_unknown(
        ir, "sampling_semantics.reflection_refraction_mix",
        "ReflectionIndex=0.5 vs RefractionIndex=0.8 blend formula unproven")

    out = MV2 / "ir" / "cf_cop357_winter.material_ir.json"
    material_ir.save_ir(ir, out)
    print("B1:", out)
    return ir


def b2() -> dict:
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    weapon_meshes = [m["name"] for m in skin["meshes"]
                     if not m["name"].lower().startswith(("fview", "fview-"))]
    maps = {
        "diffuse": DIFFUSE,
        "normal": NORMAL,
        "specular": SPECULAR,
        "alpha": ALPHA,
    }
    try:
        maps["cubemap_face0"] = CUBEMAP
    except Exception:  # noqa: BLE001
        pass
    report = channel_audit.audit_material_maps(
        maps,
        MV2 / "reports" / "channel_audit.json",
        sheet_png=MV2 / "reports" / "channel_sheet.png",
        diffuse_role="diffuse",
        skin=skin,
        mesh_names=weapon_meshes)
    print("B2:", MV2 / "reports" / "channel_audit.json")
    return report


def main() -> int:
    ir = b1()
    report = b2()
    alpha = report["maps"]["alpha"]["channels"]
    for ch in ("R", "G", "B"):
        s = alpha[ch]
        print(f"alpha.{ch}: mean={s['mean']} modal={s['modal_value']} "
              f"modal_frac={s['modal_fraction']} unique={s['unique_values']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
