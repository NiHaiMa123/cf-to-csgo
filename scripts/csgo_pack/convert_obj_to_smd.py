# -*- coding: utf-8 -*-
"""
Converts true CF M4A1-Born Beast (雷神) extracted OBJ model to Source 1 SMD mesh.
Binds vertices to weapon rig bone hierarchy so studiomdl can compile it directly.
"""

import os
from pathlib import Path

OBJ_PATH = Path(r"D:\project\cf_to_csgo\data\out\PV-M4A1_S_BornBeast_Classic.obj")
REF_SMD = Path(r"D:\project\cf_to_csgo\data\out\decompiled_ak47_beast\PV-AK-47-Beast.smd")
OUT_SMD = Path(r"D:\project\cf_to_csgo\data\out\decompiled_m4a1_bornbeast\PV-M4A1-BornBeast.smd")

def parse_obj(obj_file):
    vertices = []
    uvs = []
    normals = []
    faces = [] # list of (material, [(v_idx, uv_idx, n_idx), ...])
    
    current_mat = "pv-m4a1_s_bornbeast"
    
    with open(obj_file, "r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if parts[0] == "v":
                # OBJ coordinates: x, y, z
                # In LithTech -> Source coords: usually scaled
                vertices.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == "vt":
                uvs.append([float(parts[1]), float(parts[2])])
            elif parts[0] == "vn":
                normals.append([float(parts[1]), float(parts[2]), float(parts[3])])
            elif parts[0] == "usemtl":
                current_mat = parts[1].lower()
            elif parts[0] == "f":
                poly = []
                for p in parts[1:]:
                    vals = p.split("/")
                    v_idx = int(vals[0]) - 1
                    uv_idx = int(vals[1]) - 1 if len(vals) > 1 and vals[1] else -1
                    n_idx = int(vals[2]) - 1 if len(vals) > 2 and vals[2] else -1
                    poly.append((v_idx, uv_idx, n_idx))
                # Triangulate polygon if quad
                if len(poly) == 3:
                    faces.append((current_mat, poly))
                elif len(poly) == 4:
                    faces.append((current_mat, [poly[0], poly[1], poly[2]]))
                    faces.append((current_mat, [poly[0], poly[2], poly[3]]))
                elif len(poly) > 4:
                    for i in range(1, len(poly) - 1):
                        faces.append((current_mat, [poly[0], poly[i], poly[i+1]]))
                        
    return vertices, uvs, normals, faces

def convert():
    print(f"[+] Loading M4A1 OBJ: {OBJ_PATH}")
    verts, uvs, norms, faces = parse_obj(OBJ_PATH)
    print(f"    Loaded {len(verts)} vertices, {len(uvs)} UVs, {len(faces)} triangles")
    
    # Read nodes and skeleton header from reference SMD
    with open(REF_SMD, "r") as f:
        ref_lines = f.readlines()
        
    nodes_block = []
    skeleton_block = []
    
    in_nodes = False
    in_skel = False
    
    for l in ref_lines:
        if l.strip() == "nodes":
            in_nodes = True
            nodes_block.append(l)
            continue
        if in_nodes:
            nodes_block.append(l)
            if l.strip() == "end":
                in_nodes = False
            continue
        if l.strip() == "skeleton":
            in_skel = True
            skeleton_block.append(l)
            continue
        if in_skel:
            skeleton_block.append(l)
            if l.strip() == "end":
                in_skel = False
                break

    # Build SMD output
    out_lines = ["version 1\n"]
    out_lines.extend(nodes_block)
    out_lines.extend(skeleton_block)
    out_lines.append("triangles\n")
    
    # Bone index 2 is bone_Weapon_Main
    weapon_bone = 2
    
    for mat, tri in faces:
        out_lines.append(f"{mat}\n")
        for v_idx, uv_idx, n_idx in tri:
            v = verts[v_idx]
            n = norms[n_idx] if n_idx >= 0 and n_idx < len(norms) else [0.0, 1.0, 0.0]
            uv = uvs[uv_idx] if uv_idx >= 0 and uv_idx < len(uvs) else [0.0, 0.0]
            
            # SMD vertex format:
            # bone_id x y z nx ny nz u v num_weights bone_id weight
            out_lines.append(f"{weapon_bone} {v[0]:.6f} {v[1]:.6f} {v[2]:.6f} {n[0]:.6f} {n[1]:.6f} {n[2]:.6f} {uv[0]:.6f} {uv[1]:.6f} 1 {weapon_bone} 1.000000\n")
            
    out_lines.append("end\n")
    
    OUT_SMD.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_SMD, "w") as f:
        f.writelines(out_lines)
        
    print(f"[SUCCESS] True M4A1-Born Beast SMD generated: {OUT_SMD} ({OUT_SMD.stat().st_size / 1024:.2f} KB)")

if __name__ == "__main__":
    convert()
