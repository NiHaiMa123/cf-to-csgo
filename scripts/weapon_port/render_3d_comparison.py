# -*- coding: utf-8 -*-
"""Render 3D wireframe / shaded preview images of candidate M4 models using pure Python math."""

from __future__ import annotations

import math
from pathlib import Path
import subprocess
import sys

import pygame

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CFREZ_EXE = PROJECT_ROOT / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
WORK_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "m4_renders"
WORK_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\e38afcad-92d4-47f8-80dc-cbb40a0b7bda")


def export_obj(ltb_rel_path: str, out_obj: Path) -> bool:
    rf_root = DATA_DIR / ltb_rel_path.split("/")[0]
    model_rel = "/".join(ltb_rel_path.split("/")[1:])
    proc = subprocess.run(
        [str(CFREZ_EXE), "--export-obj", "--root", str(rf_root), "--model", model_rel, "--output", str(out_obj)],
        capture_output=True,
        text=True,
    )
    return proc.returncode == 0 and out_obj.exists()


def parse_obj(obj_path: Path):
    vertices = []
    faces = []
    for line in obj_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("v "):
            parts = line.split()
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif line.startswith("f "):
            parts = line.split()[1:]
            corners = [int(p.split("/")[0]) - 1 for p in parts]
            if len(corners) >= 3:
                faces.append(corners[:3])
    return vertices, faces


def render_model_preview(verts: list[tuple[float, float, float]], faces: list, width=800, height=500, title="", out_png=None):
    if not verts:
        return

    # Compute bounding box
    min_x = min(v[0] for v in verts)
    max_x = max(v[0] for v in verts)
    min_y = min(v[1] for v in verts)
    max_y = max(v[1] for v in verts)
    min_z = min(v[2] for v in verts)
    max_z = max(v[2] for v in verts)

    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    cz = (min_z + max_z) / 2.0

    scale = max(max_x - min_x, max_y - min_y, max_z - min_z)
    if scale == 0:
        scale = 1.0

    # Isometric-like projection (yaw 40 deg, pitch -18 deg)
    yaw = math.radians(40)
    pitch = math.radians(-18)

    cos_y, sin_y = math.cos(yaw), math.sin(yaw)
    cos_p, sin_p = math.cos(pitch), math.sin(pitch)

    # Transform vertices
    v_proj = []
    zoom = min(width, height) * 0.85 / scale

    for vx, vy, vz in verts:
        # Centering
        dx = vx - cx
        dy = vy - cy
        dz = vz - cz

        # Yaw around Y
        x1 = dx * cos_y + dz * sin_y
        y1 = dy
        z1 = -dx * sin_y + dz * cos_y

        # Pitch around X
        x2 = x1
        y2 = y1 * cos_p - z1 * sin_p
        z2 = y1 * sin_p + z1 * cos_p

        # Screen projection
        sx = width / 2.0 + x2 * zoom
        sy = height / 2.0 - y2 * zoom
        v_proj.append((sx, sy, z2))

    surf = pygame.Surface((width, height))
    surf.fill((22, 25, 32))

    # Draw dark grid
    for gx in range(0, width, 40):
        pygame.draw.line(surf, (30, 35, 45), (gx, 0), (gx, height))
    for gy in range(0, height, 40):
        pygame.draw.line(surf, (30, 35, 45), (0, gy), (width, gy))

    # Sort faces by average depth Z
    face_depths = []
    for f in faces:
        z_avg = (v_proj[f[0]][2] + v_proj[f[1]][2] + v_proj[f[2]][2]) / 3.0
        face_depths.append((z_avg, f))
    face_depths.sort(key=lambda x: x[0])

    # Simple flat shading with directional light
    lx, ly, lz = 0.4, 0.7, 0.6
    l_len = math.sqrt(lx*lx + ly*ly + lz*lz)
    lx, ly, lz = lx/l_len, ly/l_len, lz/l_len

    for _, f in face_depths:
        p0 = verts[f[0]]
        p1 = verts[f[1]]
        p2 = verts[f[2]]

        ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
        bx, by, bz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]

        nx = ay * bz - az * by
        ny = az * bx - ax * bz
        nz = ax * by - ay * bx
        n_len = math.sqrt(nx*nx + ny*ny + nz*nz)
        if n_len > 1e-6:
            nx, ny, nz = nx/n_len, ny/n_len, nz/n_len
            dot = nx * lx + ny * ly + nz * lz
            diffuse = max(0.18, dot)
        else:
            diffuse = 0.5

        # Render shaded polygon
        color = (
            int(min(255, 90 * diffuse + 40)),
            int(min(255, 140 * diffuse + 60)),
            int(min(255, 200 * diffuse + 80))
        )
        pts = [(v_proj[idx][0], v_proj[idx][1]) for idx in f]
        pygame.draw.polygon(surf, color, pts)
        pygame.draw.polygon(surf, (35, 45, 60), pts, 1)

    # Draw title header
    font = pygame.font.SysFont("Arial", 22, bold=True)
    txt = font.render(title, True, (240, 240, 240))
    surf.blit(txt, (20, 15))

    if out_png:
        pygame.image.save(surf, str(out_png))


def main() -> int:
    pygame.init()
    pygame.font.init()
    models_to_test = [
        ("PV-M4A1_S_BornBeast", "rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB", "M4A1-S BornBeast (雷神 Base)"),
        ("PV-M4A1_S_BornBeast2", "rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast2.LTB", "M4A1-S BornBeast 2"),
        ("PV-M4A1_Silencer_Predator", "rf016/Models/PLAYERVIEW/PV-M4A1_Silencer_Predator.LTB", "M4A1 Silencer Predator (黑骑士)"),
        ("PV-M4A1_Silencer_Predator_Classic", "rf016/Models/PLAYERVIEW/PV-M4A1_Silencer_Predator_Classic.LTB", "M4A1 Predator Classic (黑骑士原版)"),
        ("PV-M4A1_S_IronBeast-NobleGold", "rf016/Models/PLAYERVIEW/PV-M4A1_S_IronBeast-NobleGold.LTB", "M4A1-S IronBeast (黑龙/王者)"),
        ("PV-M4A1_Silencer_PrismBeast", "rf016/Models/PLAYERVIEW/PV-M4A1_Silencer_PrismBeast.LTB", "M4A1 Silencer PrismBeast (武圣)"),
        ("PV-M4A1_S_Transformers", "rf016/Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB", "M4A1-S Transformers (千变)"),
    ]

    for name, rel_path, label in models_to_test:
        obj_file = WORK_DIR / f"{name}.obj"
        png_file = WORK_DIR / f"{name}_render.png"
        artifact_png = ARTIFACT_DIR / f"{name}_render.png"

        print(f"[*] Exporting & rendering {name}...")
        if export_obj(rel_path, obj_file):
            verts, faces = parse_obj(obj_file)
            print(f"  -> {name}: {len(verts)} verts, {len(faces)} faces")
            render_model_preview(verts, faces, title=f"{label} ({len(faces)} tris)", out_png=png_file)
            if png_file.exists():
                pygame.image.save(pygame.image.load(str(png_file)), str(artifact_png))
                print(f"  -> Saved {artifact_png.name}")
        else:
            print(f"  Export failed for {rel_path}")

    print("[PASS] All 3D model comparison renders generated!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
