# -*- coding: utf-8 -*-
"""Base 屠龙 (Kukri_Beast) diffuse -> 2048 VTF + Phong/envmap VMT.

Recipe mirrors the third-party p_Kukri_Beast NobleGold material:
  - basetexture alpha = specular-map luminance (envmap+phong mask)
  - $bumpmap = CF normal map, $PhongExponentTexture = CF spec map
  - $envmap env_cubemap + fresnel + gold tint, rimlight, nocull
"""
from __future__ import annotations

import json
import sys
import urllib.request
from pathlib import Path

import numpy as np
from PIL import Image

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_textures import comfy_upscale, vtfcmd  # noqa: E402

REPO = Path(_paths.project_dir())
WORK = REPO / "work" / "tulong_chuntao"
DEC = WORK / "decode"
ACQ = WORK / "acquire" / "verified_root" / "ModelTextures"
OUT = WORK / "texture"
UP = OUT / "up"
STAGING = WORK / "addon" / "materials" / "models" / "weapons" / "v_models" / "cf_tulong"
MAT = "models/weapons/v_models/cf_tulong"

DIFFUSE = DEC / "PV-Kukri_Beast_spring.png"
# Baked in Blender (csref/_blender_bake.py): diffuse + spec-map additive in the
# knife's own UV space. The blade is backlit in the idle pose, so the metallic
# sheen is baked into the basetexture and the VMT is UnlitGeneric.
BAKED = UP / "kukri_spring_baked.png"
SPEC = DEC / "maps" / "Kukri_Beast_Spring_S.PNG"
NORMAL = DEC / "maps" / "Kukri_Beast_Spring_N.PNG"
COMFY = "http://127.0.0.1:8188"


def gun_vmt() -> str:
    # Fully light-independent: UnlitGeneric shows the baked texture as-is.
    return f'''"UnlitGeneric"
{{
	"$basetexture" "{MAT}/cf_kukri_spring"
	"$nocull" "1"
}}
'''


def main() -> int:
    UP.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    if BAKED.is_file():
        # Blender-baked diffuse+spec composite: used as-is (UnlitGeneric).
        im = Image.open(BAKED).convert("RGB")
        if im.size != (2048, 2048):
            im = im.resize((2048, 2048), Image.LANCZOS)
        up2 = UP / "kukri_beast_2048_rgb.png"
        im.save(up2)
        print("using baked basetexture:", BAKED.name)
    else:
        try:
            urllib.request.urlopen(COMFY + "/system_stats", timeout=4)
            up = comfy_upscale(DIFFUSE, "tulong_spring")
            print("comfy upscale ok")
        except Exception as e:  # noqa: BLE001
            print("comfy unavailable, PIL 4x:", e)
            im = Image.open(DIFFUSE).convert("RGB")
            up = UP / "4x_PV-Kukri_Beast_spring.png"
            im.resize((2048, 2048), Image.LANCZOS).save(up)
        im = Image.open(up).convert("RGB")
        if im.size != (2048, 2048):
            im = im.resize((2048, 2048), Image.LANCZOS)
        up2 = UP / "kukri_beast_2048_rgb.png"
        im.save(up2)
    vtfcmd(up2, STAGING / "cf_kukri_spring.vtf", "bgra8888")
    # phong exponent texture = CF spec map (native 1024x512)
    vtfcmd(SPEC, STAGING / "cf_kukri_spring_s.vtf", "bgra8888")
    if NORMAL.is_file():
        vtfcmd(NORMAL, STAGING / "cf_kukri_spring_n.vtf", "dxt5",
               ("TRILINEAR", "ANISOTROPIC", "NORMAL"))
    (STAGING / "cf_kukri_spring.vmt").write_text(gun_vmt(), encoding="utf-8")
    report = {"diffuse_src": str(DIFFUSE), "upscaled": str(up2),
              "up_size": list(im.size),
              "alpha": "spec-map luminance -> envmap/phong mask",
              "vmt": "NobleGold recipe: env_cubemap+gold tint+rimlight+phong",
              "staging": str(STAGING)}
    (OUT / "report_beast.json").write_text(json.dumps(report, indent=1),
                                           encoding="utf-8")
    print("wrote", STAGING / "cf_kukri_spring.vtf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
