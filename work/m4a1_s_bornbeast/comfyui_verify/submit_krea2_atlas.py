# -*- coding: utf-8 -*-
"""Submit a local Krea2 identity-edit of the CS1.6 BornBeast UV atlas.

Visual experiment only. Output is not a P4-M01 native-material candidate.
"""

from __future__ import annotations

import json
import shutil
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
VERIFY = Path(__file__).resolve().parent
COMFY = "http://127.0.0.1:8188"
COMFY_INPUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\input")
COMFY_OUTPUT = Path(r"D:\Comfy-Desktop\ComfyUI-Shared\output")

CS16 = ROOT / "work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png"
SHOP = ROOT / "work/m4a1_s_bornbeast/materials/reference/BUYWEAPON_INFO_M4A1_S_BornBeast.png"
NATIVE = ROOT / "work/m4a1_s_bornbeast/materials/decoded/bornbeast_diffuse_bgr.png"

ATLAS_NAME = "bornbeast_cs16_atlas.png"
PROMPT_TEXT = (
    "This is a video-game first-person weapon UV albedo atlas. "
    "Keep every UV island in the exact same place, scale, and packing. "
    "Do not turn this into a 3D render or a photo of a gun. "
    "Enhance it as CrossFire M4A1-S Born Beast: dark gunmetal body, "
    "red glowing energy veins, beast skull with glowing red eyes, "
    "black and red, sharp game texture, clean islands on black background."
)


def copy_inputs() -> None:
    VERIFY.mkdir(parents=True, exist_ok=True)
    COMFY_INPUT.mkdir(parents=True, exist_ok=True)
    dest = COMFY_INPUT / ATLAS_NAME
    try:
        shutil.copy2(CS16, dest)
    except PermissionError:
        if not dest.exists():
            raise
    shutil.copy2(CS16, VERIFY / "cs16_atlas.png")
    shutil.copy2(SHOP, VERIFY / "shop_icon.png")
    shutil.copy2(NATIVE, VERIFY / "native_dtx.png")


def workflow() -> dict:
    return {
        "55": {
            "class_type": "UNETLoader",
            "inputs": {
                "unet_name": "Krea2_turbo_uncensored_edit_v1.1-fp8_scaled.safetensors",
                "weight_dtype": "default",
            },
        },
        "56": {
            "class_type": "CLIPLoader",
            "inputs": {
                "clip_name": "qwen3vl_4b_fp8_scaled.safetensors",
                "type": "krea2",
                "device": "default",
            },
        },
        "57": {
            "class_type": "VAELoader",
            "inputs": {"vae_name": "qwen_image_vae.safetensors"},
        },
        "70": {
            "class_type": "ImageScale",
            "inputs": {
                "image": ["72", 0],
                "upscale_method": "lanczos",
                "width": 1024,
                "height": 1024,
                "crop": "disabled",
            },
        },
        "72": {
            "class_type": "LoadImage",
            "inputs": {"image": ATLAS_NAME},
        },
        "73": {
            "class_type": "VAEEncode",
            "inputs": {"pixels": ["70", 0], "vae": ["57", 0]},
        },
        "86": {
            "class_type": "ModelSamplingAuraFlow",
            "inputs": {"model": ["79", 0], "shift": 1.15},
        },
        "79": {
            "class_type": "Krea2EditModelPatch",
            "inputs": {
                "model": ["55", 0],
                "source_latent": ["73", 0],
                "ref_boost": 2.0,
                "ref_boost_a": 1.0,
                "fit_mode": "fit",
                "vae": ["57", 0],
                "source_image": ["70", 0],
                "target_latent": ["73", 0],
            },
        },
        "84": {
            "class_type": "Krea2EditGroundedEncode",
            "inputs": {
                "clip": ["56", 0],
                "prompt": PROMPT_TEXT,
                "image": ["70", 0],
                "grounding_px": 768,
                "system_prompt": "",
            },
        },
        "85": {
            "class_type": "Krea2EditGroundedEncode",
            "inputs": {
                "clip": ["56", 0],
                "prompt": "",
                "image": ["70", 0],
                "grounding_px": 768,
                "system_prompt": "",
            },
        },
        "53": {
            "class_type": "KSampler",
            "inputs": {
                "model": ["86", 0],
                "seed": 20260912,
                "steps": 10,
                "cfg": 1.0,
                "sampler_name": "euler",
                "scheduler": "simple",
                "positive": ["84", 0],
                "negative": ["85", 0],
                "latent_image": ["73", 0],
                "denoise": 0.45,
            },
        },
        "54": {
            "class_type": "VAEDecode",
            "inputs": {"samples": ["53", 0], "vae": ["57", 0]},
        },
        "29": {
            "class_type": "SaveImage",
            "inputs": {
                "images": ["54", 0],
                "filename_prefix": "bornbeast_comfy_atlas",
            },
        },
    }


def http_json(method: str, path: str, payload: dict | None = None) -> dict:
    data = None if payload is None else json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        COMFY + path,
        data=data,
        method=method,
        headers={"Content-Type": "application/json"} if data else {},
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def submit() -> str:
    body = {
        "prompt": workflow(),
        "client_id": "cf_to_csgo_comfyui_verify",
    }
    result = http_json("POST", "/prompt", body)
    if "error" in result:
        raise RuntimeError(json.dumps(result, ensure_ascii=False, indent=2))
    prompt_id = result.get("prompt_id")
    if not prompt_id:
        raise RuntimeError(f"no prompt_id: {result}")
    return str(prompt_id)


def wait(prompt_id: str, timeout_s: int = 600) -> dict:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            hist = http_json("GET", f"/history/{prompt_id}")
        except urllib.error.URLError:
            time.sleep(2)
            continue
        entry = hist.get(prompt_id)
        if entry:
            status = (entry.get("status") or {}).get("status_str") or entry.get("status")
            if entry.get("outputs") or status in {"success", "error"}:
                return entry
        time.sleep(2)
    raise TimeoutError(f"ComfyUI prompt {prompt_id} timed out")


def collect_images(entry: dict) -> list[Path]:
    found: list[Path] = []
    for node_out in (entry.get("outputs") or {}).values():
        for img in node_out.get("images") or []:
            name = img.get("filename")
            sub = img.get("subfolder") or ""
            if not name:
                continue
            src = COMFY_OUTPUT / sub / name if sub else COMFY_OUTPUT / name
            if src.exists():
                dest = VERIFY / "comfy_atlas.png"
                shutil.copy2(src, dest)
                found.append(dest)
    return found


def main() -> int:
    copy_inputs()
    prompt_id = submit()
    (VERIFY / "comfy_prompt_id.txt").write_text(prompt_id, encoding="utf-8")
    print(json.dumps({"submitted": True, "prompt_id": prompt_id}, ensure_ascii=False))
    entry = wait(prompt_id)
    images = collect_images(entry)
    status = {
        "prompt_id": prompt_id,
        "status": (entry.get("status") or {}),
        "images": [str(p) for p in images],
        "error": ((entry.get("status") or {}).get("messages") if not images else None),
    }
    (VERIFY / "comfy_run.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(status, ensure_ascii=False))
    if not images:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
