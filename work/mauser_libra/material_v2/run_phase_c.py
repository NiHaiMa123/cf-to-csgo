# -*- coding: utf-8 -*-
"""Phase C driver: CF reference renderer + Gate A for the reference weapon.

C1: recovered shader family on real mesh/maps (software renderer)
C2: directional cubemap check on test sphere/plane/weapon
C3: fixed scene variants (camera/light/exposure in manifest)
Gate A: CF semantic validation metrics
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
from PIL import Image

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))
import cf_reference_renderer as cfrr  # noqa: E402
import material_ir  # noqa: E402

WORK = _REPO / "work" / "mauser_libra"
MV2 = WORK / "material_v2"
DECODE = WORK / "decode"
MAPS = DECODE / "maps"
REF = MV2 / "reference_cf"

SKIN = DECODE / "cf_skin_m1896_libra.json"
IR_PATH = MV2 / "ir" / "cf_mauser_libra.material_ir.json"

SIZE = 512
FOV = 45.0


def load_inputs():
    ir = material_ir.load_ir(IR_PATH)
    params = cfrr.params_from_cfg_flat(ir["cfg"]["flat"])
    meshes = cfrr.load_skin_meshes(SKIN, skip_prefixes=("fview",))
    maps = {
        "diffuse": cfrr.load_rgb(DECODE / "PV-M1896_Libra.png"),
        "normal": cfrr.load_rgb(MAPS / "M1896_Libra_N.TGA"),
        "specular": cfrr.load_rgb(MAPS / "M1896_Libra_S.TGA"),
        "alpha": cfrr.load_rgb(MAPS / "M1896_Libra_alpha.TGA"),
        "cubemap": cfrr.dds_faces(MAPS / "LobbyCube.DDS"),
    }
    return ir, params, meshes, maps


def gun_center(meshes: list[dict]) -> tuple[np.ndarray, float]:
    for m in meshes:
        if "mauser" in m["name"].lower() or "libra" in m["name"].lower():
            v = m["verts"]
            lo, hi = v.min(0), v.max(0)
            return (lo + hi) / 2, float((hi - lo).max())
    v = np.concatenate([m["verts"] for m in meshes])
    lo, hi = v.min(0), v.max(0)
    return (lo + hi) / 2, float((hi - lo).max())


def render_suite(params, meshes, maps):
    """C3 fixed scene: camera/light/exposure recorded in manifest."""
    center, extent = gun_center(meshes)
    dist = extent * 1.6
    scenes = {
        "neutral":      {"eye_off": (-0.6, -1.0, 0.45), "light": (-0.3, -0.5, 0.8)},
        "front_lit":    {"eye_off": (-0.6, -1.0, 0.45), "light": (-0.2, -0.9, 0.4)},
        "side_lit":     {"eye_off": (-0.6, -1.0, 0.45), "light": (0.95, -0.2, 0.25)},
        "back_dark":    {"eye_off": (-0.6, -1.0, 0.45), "light": (0.2, 0.9, 0.4)},
        "rotated_view": {"eye_off": (0.9, -0.7, 0.5), "light": (-0.3, -0.5, 0.8)},
    }
    outputs = {}
    for name, sc in scenes.items():
        eye = center + np.asarray(sc["eye_off"], np.float32) * dist
        img, comp = cfrr.render_full(meshes, maps, params, eye, center,
                                     sc["light"], SIZE, FOV)
        cfrr.save_png(img, REF / f"{name}.png")
        outputs[name] = {"eye": [float(x) for x in eye],
                         "eye_off": sc["eye_off"], "light_dir": sc["light"]}
        if name == "neutral":
            hit = img.sum(-1) > 0
            for cname, arr in comp.items():
                cfrr.save_png(arr, REF / f"component_{cname}.png")
            outputs["neutral"]["hit_fraction"] = round(
                float(hit.mean()), 5)
            outputs["neutral"]["components"] = {
                c: {"mean": round(float(a.mean()), 5),
                    "hit_mean": round(float(a[hit].mean()), 5)
                    if hit.any() else 0.0,
                    "max": round(float(a.max()), 4)}
                for c, a in comp.items()}
    return outputs, center, dist


def render_test_objects(params, maps):
    """C2: test sphere + plane through the same shader path."""
    sphere = cfrr.make_sphere(8.0)
    plane = cfrr.make_plane(16.0)
    outs = {}
    eye = np.array((0, -30, 8), np.float32)
    img, comp = cfrr.render_full([sphere], maps, params, eye,
                                 (0, 0, 0), (-0.3, -0.5, 0.8), SIZE, FOV)
    cfrr.save_png(img, REF / "test_sphere.png")
    for cname, arr in comp.items():
        cfrr.save_png(arr, REF / f"test_sphere_{cname}.png")
    outs["sphere"] = comp
    eye2 = np.array((20, -22, 10), np.float32)
    img2, comp2 = cfrr.render_full([sphere], maps, params, eye2,
                                   (0, 0, 0), (-0.3, -0.5, 0.8), SIZE, FOV)
    cfrr.save_png(img2, REF / "test_sphere_rotated.png")
    outs["sphere_rotated"] = comp2
    eye3 = np.array((0, -26, 14), np.float32)
    img3, _ = cfrr.render_full([plane], maps, params, eye3,
                               (0, 0, 0), (-0.3, -0.5, 0.8), SIZE, FOV)
    cfrr.save_png(img3, REF / "test_plane.png")
    return outs


def gate_a(test_outs, scene_outputs, ir) -> dict:
    """CF semantic validation — behavioral checks, not pixel matches."""
    checks = {}
    cube = test_outs["sphere"]["cubemap"]
    cube_rot = test_outs["sphere_rotated"]["cubemap"]
    hit = cube.sum(-1) > 0
    hit_rot = cube_rot.sum(-1) > 0
    # 1. cubemap varies spatially on the sphere (directional sampling works)
    spatial_std = float(cube[hit].std()) if hit.any() else 0.0
    checks["cubemap_varies_with_normal"] = {
        "metric": round(spatial_std, 5), "pass": spatial_std > 0.005}
    # 2. cubemap response is view-dependent (not static UV color)
    both = hit & hit_rot
    if both.any():
        a = cube[both] - cube[both].mean()
        b = cube_rot[both] - cube_rot[both].mean()
        denom = float(np.linalg.norm(a) * np.linalg.norm(b))
        corr = float((a * b).sum() / denom) if denom > 1e-9 else 0.0
    else:
        corr = 0.0
    checks["cubemap_view_dependent"] = {
        "metric": round(corr, 4), "pass": corr < 0.95}
    # 3. diffuse term exists and keeps base regions (mean over hit pixels)
    dl = scene_outputs["neutral"]["components"]["diffuse_lit"]
    checks["diffuse_base_present"] = {
        "metric": dl["hit_mean"], "pass": dl["hit_mean"] > 0.003}
    # 4. specular response is spatially bounded (not whole-frame wash)
    sp = scene_outputs["neutral"]["components"]["specular"]
    checks["specular_bounded"] = {
        "metric": {"hit_mean": sp["hit_mean"], "max": sp["max"]},
        "pass": 0.0 < sp["hit_mean"] < 0.5 and sp["max"] > 0.02}
    # 5. cube term nonzero on metal areas of weapon
    cb = scene_outputs["neutral"]["components"]["cubemap"]
    checks["cubemap_term_on_weapon"] = {
        "metric": {"hit_mean": cb["hit_mean"], "max": cb["max"]},
        "pass": cb["max"] > 0.05}
    # 6. unknowns explicitly listed
    checks["unknowns_declared"] = {
        "metric": len(ir["unknowns"]), "pass": len(ir["unknowns"]) > 0}
    passed = all(c["pass"] for c in checks.values())
    return {"passed": passed, "checks": checks,
            "note": "behavioral validation only; not a pixel-match to CF runtime"}


def main() -> int:
    REF.mkdir(parents=True, exist_ok=True)
    ir, params, meshes, maps = load_inputs()
    scene_outputs, center, dist = render_suite(params, meshes, maps)
    test_outs = render_test_objects(params, maps)
    gate = gate_a(test_outs, scene_outputs, ir)

    manifest = {
        "renderer": "software numpy rasterizer (cf_reference_renderer.py)",
        "reason_not_blender": "transformed/refract cubemap ray cannot be "
                              "expressed in Blender shader nodes; software "
                              "renderer keeps one auditable code path for "
                              "sphere/plane/mesh",
        "size": SIZE, "fov_deg": FOV,
        "params": params,
        "shader_family": ir["shader_family"],
        "formula_status": {
            "diffuse_lit": "INFERRED: albedo*(ambient+LightBrightness*lambert+DiffuseBoost)",
            "spec_term": "INFERRED: Blinn pow(N.H, SpecularPower*0.25)",
            "cube_ray": "INFERRED: mix(reflect,refract,ReflectionIndex)->rotY(CubeMapTransformY)",
            "channel_semantics": "INFERRED: alpha.g=spec mask, alpha.b=cube mask",
        },
        "scenes": scene_outputs,
        "gun_center": [float(x) for x in center],
        "gate_a": gate,
        "limitation": "Blender/software preview is diagnostic only; "
                      "not CS:GO runtime ground truth",
    }
    (REF / "reference_manifest.json").write_text(
        json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print("Gate A:", "PASS" if gate["passed"] else "FAIL")
    for k, v in gate["checks"].items():
        print(f"  {k}: {v['metric']} -> {'PASS' if v['pass'] else 'FAIL'}")
    return 0 if gate["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
