"""Convert CF LobbyCube DDS faces to an equirect PNG for Blender."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(r"D:/project/cf_to_csgo")
sys.path.insert(0, str(ROOT / "scripts" / "material_recovery"))
import cf_reference_renderer as cfrr  # noqa: E402

DDS = ROOT / "work/mauser_libra/decode/maps/LobbyCube.DDS"
OUT = ROOT / "work/mauser_libra/material_rendering_fix/blender_lookdev/lobbycube_equirect.png"


def cubemap_to_equirect(faces: dict[str, np.ndarray], width: int = 1024) -> np.ndarray:
    height = width // 2
    ys, xs = np.mgrid[0:height, 0:width].astype(np.float32)
    theta = (xs + 0.5) / width * (2.0 * np.pi) - np.pi
    phi = 0.5 * np.pi - (ys + 0.5) / height * np.pi
    dirs = np.stack([
        np.cos(phi) * np.sin(theta),
        np.sin(phi),
        np.cos(phi) * np.cos(theta),
    ], axis=-1).reshape(-1, 3)
    rgb = cfrr.cube_sample(faces, dirs).reshape(height, width, 3)
    return np.clip(rgb, 0.0, 1.0)


def main() -> int:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    faces = cfrr.dds_faces(DDS)
    img = cubemap_to_equirect(faces)
    Image.fromarray(np.uint8(np.round(img * 255.0)), "RGB").save(OUT)
    print("wrote", OUT, img.shape)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
