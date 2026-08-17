# -*- coding: utf-8 -*-
"""
Generates a customized, elegant F-Inspect (lookat01) animation for CF Fire-Kirin (AK-47 Beast)
centered around the Dragon Receiver without buttstock clipping.
"""

import math
from pathlib import Path

DATA_OUT = Path(r"D:\project\cf_to_csgo\data\out\decompiled_ak47_beast\v_rif_ak47_anims")
IDLE_SMD = DATA_OUT / "ak47_idle.smd"
INSPECT_SMD = DATA_OUT / "lookat01_beast.smd"

def build_custom_inspect():
    # Read base rest frame from idle animation
    with open(IDLE_SMD, "r") as f:
        lines = f.readlines()
        
    header = []
    rest_nodes = {}
    
    in_nodes = False
    in_skeleton = False
    
    for l in lines:
        if l.strip() == "nodes":
            in_nodes = True
            header.append(l)
            continue
        if l.strip() == "end" and in_nodes:
            in_nodes = False
            header.append(l)
            continue
        if l.strip() == "skeleton":
            in_skeleton = True
            header.append(l)
            continue
        if in_nodes:
            header.append(l)
            continue
        if in_skeleton:
            if l.startswith("time 0"):
                continue
            if l.startswith("time 1") or l.strip() == "end":
                break
            parts = l.strip().split()
            if len(parts) == 7:
                b_id = int(parts[0])
                pos = [float(parts[1]), float(parts[2]), float(parts[3])]
                rot = [float(parts[4]), float(parts[5]), float(parts[6])]
                rest_nodes[b_id] = (pos, rot)

    # Total frames = 90 (3 seconds at 30 fps)
    total_frames = 90
    
    out_lines = []
    out_lines.extend(header)
    
    for t in range(total_frames):
        out_lines.append(f"time {t}\n")
        
        # Smooth inspect curve:
        # 0 -> 25: tilt left (show dragon head & red eye)
        # 25 -> 45: hold tilt left
        # 45 -> 70: tilt right (show golden scales)
        # 70 -> 90: return to idle
        p = t / float(total_frames)
        
        # Roll angle (rotation around forward axis): tilt left then right
        roll = math.sin(p * 2.0 * math.pi) * 0.45  # in radians (~25 degrees)
        yaw = math.sin(p * 2.0 * math.pi) * 0.20   # gentle yaw
        pitch = -math.sin(p * math.pi) * 0.15      # slight lift up
        
        # Slight positional lift so receiver is prominent
        lift_y = math.sin(p * math.pi) * 1.2
        lift_z = math.sin(p * math.pi) * 0.8

        for b_id, (pos, rot) in sorted(rest_nodes.items()):
            cur_pos = list(pos)
            cur_rot = list(rot)
            
            # If root weapon bone or weapon main bone
            if b_id == 1: # bone_Weapon
                cur_rot[0] += pitch
                cur_rot[1] += yaw
                cur_rot[2] += roll
                cur_pos[1] += lift_y
                cur_pos[2] += lift_z
            elif b_id >= 14 and b_id <= 35: # Left hand fingers / forearm
                # Relax left hand slightly during inspect
                cur_rot[1] += yaw * 0.5
                
            out_lines.append(f"{b_id} {cur_pos[0]:.6f} {cur_pos[1]:.6f} {cur_pos[2]:.6f} {cur_rot[0]:.6f} {cur_rot[1]:.6f} {cur_rot[2]:.6f}\n")
            
    out_lines.append("end\n")
    
    with open(INSPECT_SMD, "w") as f:
        f.writelines(out_lines)
        
    print(f"Successfully generated custom Centered Beast Inspect animation: {INSPECT_SMD}")

if __name__ == "__main__":
    build_custom_inspect()
