# -*- coding: utf-8 -*-
"""Audit recovered BornBeast texture channels without assigning unsupported shader semantics."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = PROJECT_ROOT / "data" / "rf017" / "ModelTextures"
WORK = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "materials"
DECODED = WORK / "decoded"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def channel_audit(path: Path) -> dict[str, object]:
    array = np.asarray(Image.open(path).convert("RGB"))
    result: dict[str, object] = {"path": str(path), "size": list(Image.open(path).size), "channels": {}}
    for index, name in enumerate("RGB"):
        channel = array[:, :, index]
        result["channels"][name] = {
            "mean": round(float(channel.mean()), 6),
            "stddev": round(float(channel.std()), 6),
            "min": int(channel.min()),
            "max": int(channel.max()),
            "white_ratio": round(float((channel == 255).mean()), 9),
            "unique_values": int(np.unique(channel).size),
        }
    return result


def main() -> int:
    decode_report = json.loads((WORK / "material_decode_report.json").read_text(encoding="utf-8"))
    expected = {
        "alpha": (DECODED / "bornbeast_alpha_bgr.png", "G"),
        "normal": (DECODED / "bornbeast_normal_bgr.png", "B"),
        "specular": (DECODED / "bornbeast_specular_bgr.png", "R"),
    }
    audits: dict[str, object] = {}
    for role, (path, variable_channel) in expected.items():
        audit = channel_audit(path)
        fixed = [name for name in "RGB" if name != variable_channel]
        fixed_white = all(audit["channels"][name]["white_ratio"] > 0.99999 for name in fixed)
        variable_has_signal = audit["channels"][variable_channel]["stddev"] > 1.0
        audit.update({
            "variable_channel": variable_channel,
            "fixed_white_channels": fixed,
            "layout_valid": fixed_white and variable_has_signal,
        })
        audits[role] = audit

    cfg = (SOURCE_ROOT / "Shader" / "WeaponShader" / "M4A1_S_BornBeast.CFG").read_bytes()
    cfg_pixels = np.frombuffer(cfg, dtype=np.uint8).reshape(-1, 3)
    cfg_audit = {
        "bytes": len(cfg),
        "pixels": int(cfg_pixels.shape[0]),
        "variable_channel": "B",
        "r_all_white": bool(np.all(cfg_pixels[:, 0] == 255)),
        "g_all_white": bool(np.all(cfg_pixels[:, 1] == 255)),
        "b_unique_values": int(np.unique(cfg_pixels[:, 2]).size),
        "interpretation": "one-dimensional RGB lookup strip; not a text shader configuration",
    }

    reference = WORK / "reference" / "BUYWEAPON_INFO_M4A1_S_BornBeast.png"
    reference_image = Image.open(reference)
    report = {
        "schema": "cf2.bornbeast.material-audit.v1",
        "status": "pass_with_provisional_shader_mapping",
        "decode_report": str(WORK / "material_decode_report.json"),
        "decode_status": decode_report["status"],
        "auxiliary_maps": audits,
        "shader_cfg": cfg_audit,
        "official_local_reference": {
            "source": "data/rf019/TEX/UI/WEAPONICON/BUYWEAPON_INFO_M4A1_S_BornBeast.DTX",
            "decoded": str(reference),
            "sha256": sha256(reference),
            "size": list(reference_image.size),
            "observed_palette": "black/gunmetal body, silver mechanical edges, red energy accents",
        },
        "source1_mapping": {
            "alpha_g": "scalar atlas recovered; useful for visibility/albedo approximation, exact CF blend role still provisional",
            "normal_b": "scalar map only; must not be passed directly to $bumpmap as a tangent-space RGB normal",
            "specular_r": "scalar specular candidate; safe only after conservative Source phong test",
            "cfg_b_strip": "lookup ramp candidate; no direct VMT parameter equivalence proven",
            "pv_dtx": "red/pink detail or energy texture candidate with validated mip chain; animation/blend semantics provisional",
        },
        "gates": {
            "corrected_alpha_debug_ready": True,
            "direct_normal_map_use_allowed": False,
            "direct_cfg_to_vmt_translation_allowed": False,
            "final_material_claim_allowed": False,
        },
    }
    output = WORK / "f2_material_audit_report.json"
    output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if not all(item["layout_valid"] for item in audits.values()) or not cfg_audit["r_all_white"] or not cfg_audit["g_all_white"]:
        print(json.dumps({"report": str(output), "pass": False}, ensure_ascii=False))
        return 2
    print(json.dumps({"report": str(output), "pass": True}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
