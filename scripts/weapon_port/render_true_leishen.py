# -*- coding: utf-8 -*-
"""Render detailed 3D preview of authentic 雷神 (PV-M4A1_S_Transformers)."""

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
ARTIFACT_DIR = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\e38afcad-92d4-47f8-80dc-cbb40a0b7bda")


def parse_weapon_obj(obj_path: Path):
    vertices = []
    faces = []
    current_g = "default"

    for line in obj_path.read_text(encoding="utf-8", errors="ignore").splitlines():
        if line.startswith("g "):
            current_g = line.split()[1]
        elif line.startswith("v "):
            parts = line.split()
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif line.startswith("f "):
            if "hand" not in current_g.lower() and "arm" not in current_g.lower():
                parts = line.split()[1:]
                corners = [int(p.split("/")[0]) - 1 for p in parts]
                if len(corners) >= 3:
                    faces.append((current_g, corners[:3]))
    return vertices, faces


def main() -> int:
    pygame.init()
    pygame.font.init()

    obj_path = WORK_DIR / "PV-M4A1_S_Transformers_inspect.obj"
    verts, faces = parse_weapon_obj(obj_path)

    # Filter to vertices used by weapon faces
    used_v_indices = set()
    for _, f in faces:
        used_v_indices.update(f)

    w_verts = [verts[i] for i in used_v_indices]
    idx_map = {old_i: new_i for new_i, old_i in enumerate(used_v_indices)}
    w_faces = [(g, [idx_map[c] for c in f]) for g, f in faces]

    min_x = min(v[0] for v in w_verts)
    max_x = max(v[0] for v in w_verts)
    min_y = min(v[1] for v in w_verts)
    max_y = max(v[1] for v in w_verts)
    min_z = min(v[2] for v in w_verts)
    max_z = max(v[2] for v in w_verts)

    cx = (min_x + max_x) / 2.0
    cy = (min_y + max_y) / 2.0
    cz = (min_z + max_z) / 2.0
    scale = max(max_x - min_x, max_y - min_y, max_z - min_z)

    # Render multiple camera angles
    for angle_name, yaw_deg, pitch_deg in [("side", 75, -5), ("quarter", 40, -15), ("fpv", 15, -10)]:
        yaw = math.radians(yaw_deg)
        pitch = math.radians(pitch_deg)
        cos_y, sin_y = math.cos(yaw), math.sin(yaw)
        cos_p, sin_p = math.cos(pitch), math.sin(pitch)

        width, height = 900, 560
        zoom = min(width, height) * 0.9 / scale
        v_proj = []

        for vx, vy, vz in w_verts:
            dx, dy, dz = vx - cx, vy - cy, vz - cz
            x1 = dx * cos_y + dz * sin_y
            y1 = dy
            z1 = -dx * sin_y + dz * cos_y

            x2 = x1
            y2 = y1 * cos_p - z1 * sin_p
            z2 = y1 * sin_p + z1 * cos_p

            sx = width / 2.0 + x2 * zoom
            sy = height / 2.0 - y2 * zoom
            v_proj.append((sx, sy, z2))

        surf = pygame.Surface((width, height))
        surf.fill((16, 18, 24))

        # Grid
        for gx in range(0, width, 45):
            pygame.draw.line(surf, (25, 30, 40), (gx, 0), (gx, height))
        for gy in range(0, height, 45):
            pygame.draw.line(surf, (25, 30, 40), (0, gy), (width, gy))

        # Depth sort
        face_depths = []
        for g, f in w_faces:
            z_avg = (v_proj[f[0]][2] + v_proj[f[1]][2] + v_proj[f[2]][2]) / 3.0
            face_depths.append((z_avg, g, f))
        face_depths.sort(key=lambda x: x[0])

        lx, ly, lz = 0.5, 0.7, 0.5
        l_len = math.sqrt(lx*lx + ly*ly + lz*lz)
        lx, ly, lz = lx/l_len, ly/l_len, lz/l_len

        for _, g, f in face_depths:
            p0 = w_verts[f[0]]
            p1 = w_verts[f[1]]
            p2 = w_verts[f[2]]

            ax, ay, az = p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2]
            bx, by, bz = p2[0] - p0[0], p2[1] - p0[1], p2[2] - p0[2]

            nx = ay * bz - az * by
            ny = az * bx - ax * bz
            nz = ax * by - ay * bx
            n_len = math.sqrt(nx*nx + ny*ny + nz*nz)
            if n_len > 1e-6:
                nx, ny, nz = nx/n_len, ny/n_len, nz/n_len
                diffuse = max(0.2, nx * lx + ny * ly + nz * lz)
            else:
                diffuse = 0.5

            # Highlight energy parts (part01-05, eyes) with Cyan/Electric Blue
            if "part" in g.lower() or "reload" in g.lower():
                color = (
                    int(min(255, 30 * diffuse + 20)),
                    int(min(255, 180 * diffuse + 70)),
                    int(min(255, 255 * diffuse + 50))
                )
            elif "mag" in g.lower():
                color = (
                    int(min(255, 90 * diffuse + 30)),
                    int(min(255, 95 * diffuse + 30)),
                    int(min(255, 105 * diffuse + 35))
                )
            else:
                # Silver / gunmetal body
                color = (
                    int(min(255, 170 * diffuse + 50)),
                    int(min(255, 185 * diffuse + 55)),
                    int(min(255, 205 * diffuse + 60))
                )

            pts = [(v_proj[idx][0], v_proj[idx][1]) for idx in f]
            pygame.draw.polygon(surf, color, pts)
            pygame.draw.polygon(surf, (30, 40, 55), pts, 1)

        font = pygame.font.SysFont("SimHei", 22, bold=True)
        txt = font.render(f"真正的 CF 正版 M4A1-雷神 (代码: Transformers) - 视角: {angle_name}", True, (240, 240, 240))
        surf.blit(txt, (20, 15))

        out_render = WORK_DIR / f"true_leishen_{angle_name}.png"
        pygame.image.save(surf, str(out_render))
        pygame.image.save(surf, str(ARTIFACT_DIR / f"true_leishen_{angle_name}.png"))
        print(f"[*] Generated true leishen render -> {out_render.name}")

    print("[PASS] True leishen renders complete!")
    return 0


if __name__ == "__main__":
    main()
