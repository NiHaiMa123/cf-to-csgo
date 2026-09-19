# -*- coding: utf-8 -*-
"""P7-S05 — pure-CF first-person viewmodel mod.

Builds weapons/v_rif_m4a1.mdl where the whole model is CF-native:

- CF skeleton (FvARM-bone hierarchy + gun nodes) carries:
    * 9 rigid gun pieces weighted to their verified nodes
    * FoxHowl Renewal BL first-person arm/hand meshes, re-posed from the
      ArmModel bind pose into the gun bind pose (per-vertex LBS re-pose,
      equivalent to the Blender R1A_CF_DEFORM_ARMS bake)
- All animation comes from the decoded CF clips (reference_payload.json),
  mapped into viewmodel space by the similarity transform H recovered by
  ICP-fitting the CF idle-posed gun mesh onto the verified-working P6
  build's posed mesh (work/p5_leishen/p7_s05/viewmodel_transform.json):
  verts v' = H @ v_cf; bone rest worlds R' = H @ B_cf @ inv(H) and anim
  worlds W'(t) = H @ W_cf(t) @ inv(H). Proper rotation -> no winding flip.
- CS arm/glove bones (v_weapon + Bip01 set) are kept in the skeleton but
  pinned to a far-away translation every frame. The game's bonemerge'd
  sleeve/glove models then sink 500 units below the camera -> CS arms
  hidden. (Identity collapse does NOT work: merged verts land in their
  bind-relative space at the model origin = at the camera = shards.)
  No third-person asset is touched; w_rif_* files are not rebuilt.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "cf_ltb"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "material_recovery"))

import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
OUT = REPO / "work" / "p5_leishen" / "p7_s05"
SOURCE1 = OUT / "source1"
ANIMS = SOURCE1 / "v_rif_m4a1_anims"
ISOLATED = OUT / "isolated_game" / "csgo"
STAGING = OUT / "addon"
LOG_DIR = OUT / "logs"

PAYLOAD = REPO / "work/p5_leishen/p7_s04_r1/source/reference_payload.json"
ARMDUMP = REPO / "work/p5_leishen/p7_s04_r1/source/cf_skin_foxhowl_renewal_bl.json"
GUNDUMP = REPO / "work/p5_leishen/p7_s04_r1/source/cf_skin_dump.json"
ARMTEX = REPO / "work/p5_leishen/p7_s04_r1/source/armtex"
VM_TRANSFORM = OUT / "viewmodel_transform.json"
STOCK_REF_SMD = OUT / "decompiled_stock" / "PV-M4A1-BornBeast.smd"
STOCK_IDLE_SMD = OUT / "decompiled_stock" / "v_rif_m4a1_anims" / "idle.smd"
P6_ADDON = GAME / "migi/csgo/addons/p_cf_leishen_m4a4_p6"

STUDIOMDL = GAME / "bin" / "studiomdl.exe"
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"
CROWBAR = REPO / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe"

ARM_DIR_VMT = "models/weapons/v_models/cf_leishen"

# rigid piece -> payload node index (verified 2026-09-13, cf_native_preview report)
PIECE_NODE = {
    "M4A1_transformers_Body": 47,      # Dummy01
    "M4A1_transformers_MAG": 56,       # Bone06
    "M4A1_transformers_Reload01": 55,  # Bone04
    "M4A1_transformers_Reload02": 49,  # Box001
    "M4A1_transformers_part01": 51,    # Box003
    "M4A1_transformers_part02": 54,    # Box004
    "M4A1_transformers_part03": 52,    # Box005
    "M4A1_transformers_part04": 53,    # Box006
    "M4A1_transformers_part05": 50,    # Box002
}

# CS bones that the arm/glove models bonemerge onto. All collapsed.
CS_BONES = (
    ["v_weapon.Bip01", "v_weapon.Bip01_Pelvis", "v_weapon.Bip01_Spine",
     "v_weapon.Bip01_Spine1", "v_weapon.Bip01_Spine2", "v_weapon.Bip01_Spine3",
     "v_weapon.Bip01_Neck"]
    + [f"v_weapon.Bip01_{s}_{b}" for s in ("L", "R") for b in
       ("Clavicle", "UpperArm", "Forearm", "Hand", "ForeTwist")]
    + [f"v_weapon.Bip01_{s}_Finger{f}{x}" for s in ("L", "R")
       for f in range(5) for x in ("", "1", "2")]
)

CLIP_TO_SEQ = {
    "idle": "idle_0",
    "fire1": "fire", "fire2": "fire", "fire3": "fire",
    "reload": "reload",
    "draw": "select",
    "lookat01": None, "lookat01_prepare": None, "lookat01_loop": None,
}


# ---------- matrix helpers (numpy-free, lists) ----------

def mmul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def minv(m):
    # rigid/affine inverse via augmented solve (scale-safe general inverse)
    n = 4
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[piv] = aug[piv], aug[col]
        d = aug[col][col]
        aug[col] = [v / d for v in aug[col]]
        for r in range(n):
            if r != col and aug[r][col]:
                f = aug[r][col]
                aug[r] = [v - f * w for v, w in zip(aug[r], aug[col])]
    return [row[n:] for row in aug]


def mapply(m, p):
    return [sum(m[r][c] * p[c] for c in range(3)) + m[r][3] for r in range(3)]


def flat16(m16):
    return [[m16[0], m16[1], m16[2], m16[3]],
            [m16[4], m16[5], m16[6], m16[7]],
            [m16[8], m16[9], m16[10], m16[11]],
            [m16[12], m16[13], m16[14], m16[15]]]


def quat_to_mat(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0.0],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0.0],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def sample_world(sample, i):
    m = quat_to_mat(sample["quat_xyzw_world"][i])
    m[0][3], m[1][3], m[2][3] = sample["pos"][i]
    return m


def mat_to_euler(m):
    # Source SMD convention: R = Rz(rz) @ Ry(ry) @ Rx(rx), radians.
    sy = -m[2][0]
    sy = max(-1.0, min(1.0, sy))
    ry = math.asin(sy)
    cy = math.cos(ry)
    if abs(cy) > 1e-6:
        rx = math.atan2(m[2][1], m[2][2])
        rz = math.atan2(m[1][0], m[0][0])
    else:
        rx = math.atan2(-m[1][2], m[1][1])
        rz = 0.0
    return rx, ry, rz


def unwrap_euler(e, prev):
    out = []
    for a, p in zip(e, prev):
        while a - p > math.pi:
            a -= 2 * math.pi
        while a - p < -math.pi:
            a += 2 * math.pi
        out.append(a)
    return tuple(out)


def norm3(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return [c / l for c in v]


# ---------- load ----------

def main() -> int:
    for d in (SOURCE1, ANIMS, ISOLATED, STAGING, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)

    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    armdump = json.loads(ARMDUMP.read_text(encoding="utf-8"))
    gundump = json.loads(GUNDUMP.read_text(encoding="utf-8"))
    vt = json.loads(VM_TRANSFORM.read_text(encoding="utf-8"))

    # H: similarity transform CF space -> viewmodel space, ICP-fitted on
    # CF idle-posed gun verts vs the verified-working P6 build's posed verts
    # (s=1.7856, proper rotation, med residual 0.017). The whole model --
    # verts, rest bones, anim worlds -- is just the CF scene mapped by H.
    hs = vt["H"]["scale"]
    HR = vt["H"]["rotation"]
    HT = vt["H"]["translation"]
    H = [[HR[r][c] * hs for c in range(3)] + [HT[r]] for r in range(3)] \
        + [[0, 0, 0, 1.0]]
    HINV = minv(H)
    # In-game the raw CF handedness renders mirrored. Mirror about the
    # viewmodel x-plane through the gun's own centre so the gun stays on
    # the right side of the screen while left/right details swap.
    GUN_XC = -4.85
    MX = [[-1.0, 0, 0, 2 * GUN_XC], [0, 1.0, 0, 0], [0, 0, 1.0, 0],
          [0, 0, 0, 1.0]]
    MXR = [[-1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]  # rot part of MX
    I = [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]]
    MXH = mmul(MX, H)   # vertex transform (improper: triangles get flipped)
    # Bonemerge collapse target: -y is downrange (visible as a distant
    # blob); +y is behind the camera so merged arm verts are never drawn.
    FAR = [[1.0, 0, 0, 0.0], [0, 1.0, 0, 500.0], [0, 0, 1.0, 0.0],
           [0, 0, 0, 1.0]]

    def rest_world(b):
        # R' = Mx @ H @ B_cf @ inv(H) @ inv(Mx) -- rigid, det +1
        return mmul(MX, mmul(mmul(H, mmul(b, HINV)), MX))

    def anim_world(wcf, binv=None, rp=None):
        # W' = Mx @ H @ W_cf @ inv(H) @ inv(Mx) -- rigid, det +1
        return mmul(MX, mmul(mmul(H, mmul(wcf, HINV)), MX))

    def mir_attach(w):
        # attachment world under mirror: p' = Mx p, R' = MxR R MxR (proper)
        r = [[sum(MXR[i][k] * w[k][j] for k in range(3)) for j in range(3)]
             for i in range(3)]
        r = [[sum(r[i][k] * MXR[k][j] for k in range(3)) for j in range(3)]
             for i in range(3)]
        p = mapply(MX, [w[0][3], w[1][3], w[2][3]])
        return [r[0] + [p[0]], r[1] + [p[1]], r[2] + [p[2]], [0, 0, 0, 1.0]]

    nodes = payload["nodes"]
    name2idx = {n["name"]: n["index"] for n in nodes}
    B = {n["index"]: n["bind_world"] for n in nodes}
    parent_cf = {n["index"]: n["parent"] for n in nodes}

    # arm bind matrices (flat16, same layout) keyed by payload index via name
    a_by_name = {n["name"]: n for n in armdump["skeleton"]}
    BARM = {name2idx[n["name"]]: flat16(n["bind_matrix"]) for n in armdump["skeleton"]}
    BARM_INV = {i: minv(m) for i, m in BARM.items()}

    # --- attachment targets: bone worlds in the verified P6 build's idle
    # frame 0 (official-positioned muzzle/shell/stattrack/uid) ---
    attach_targets = vt["attach_worlds_p6"]
    gun_root = 47  # Dummy01
    clips_by_name = payload["clips"]
    W_gun0 = anim_world(sample_world(clips_by_name["idle_0"]["samples"][0], gun_root))
    attach_offsets = {}
    for bname in ("v_weapon.flash", "v_weapon.shelleject",
                  "v_weapon.stattrack", "v_weapon.uid"):
        # local offset under Dummy01 so the bone sits at the P6 world at f0
        # (mirrored consistently with the rest of the model)
        attach_offsets[bname] = mmul(minv(W_gun0),
                                     mir_attach(attach_targets[bname]))

    # --- SMD node table ---
    # 0 = v_weapon (root), 1..46 CS collapse bones, then CF nodes 1..56,
    # then 4 attachment bones parented to CF Dummy01.
    smd_nodes: list[tuple[str, int]] = [("v_weapon", -1)]
    smd_nodes += [(n, 0) for n in CS_BONES]
    cf_base = len(smd_nodes)
    cf_node_ids = [n["index"] for n in nodes if n["index"] != 0]
    cf_to_smd = {}
    for i in cf_node_ids:
        p = parent_cf[i]
        smd_parent = 0 if p <= 0 else cf_to_smd[p]
        cf_to_smd[i] = len(smd_nodes)
        smd_nodes.append((nodes[i]["name"], smd_parent))
    attach_base = len(smd_nodes)
    gun_smd = cf_to_smd[gun_root]
    for k, bname in enumerate(("v_weapon.flash", "v_weapon.shelleject",
                             "v_weapon.stattrack", "v_weapon.uid")):
        smd_nodes.append((bname, gun_smd))

    nbones = len(smd_nodes)
    print(f"[s05] bones={nbones} (1+{len(CS_BONES)} cs + {len(cf_node_ids)} cf + 4 attach)")

    # reference pose worlds: CF bones rest at R' = F @ B_cf @ inv(S)
    ref_world = [I] * nbones
    for i in range(1, 1 + len(CS_BONES)):
        ref_world[i] = FAR
    for i in cf_node_ids:
        ref_world[cf_to_smd[i]] = rest_world(B[i])
    for k, bname in enumerate(attach_offsets):
        ref_world[attach_base + k] = mmul(ref_world[gun_smd], attach_offsets[bname])

    def locals_of(worlds):
        out = []
        for i, (name, p) in enumerate(smd_nodes):
            w = worlds[i]
            out.append(mmul(minv(worlds[p]), w) if p >= 0 else w)
        return out

    ref_locals = locals_of(ref_world)

    def write_nodes(f):
        f.write("version 1\nnodes\n")
        for i, (name, p) in enumerate(smd_nodes):
            f.write(f'  {i} "{name}" {p}\n')
        f.write("end\n")

    def write_frame(f, t, worlds, prev_e):
        f.write(f"  time {t}\n")
        for i, loc in enumerate(locals_of(worlds)):
            e = mat_to_euler(loc)
            if prev_e[i] is not None:
                e = unwrap_euler(e, prev_e[i])
            prev_e[i] = e
            x, y, z = loc[0][3], loc[1][3], loc[2][3]
            f.write(f"    {i} {x:.6f} {y:.6f} {z:.6f} {e[0]:.6f} {e[1]:.6f} {e[2]:.6f}\n")

    # ---------- mesh ----------
    # rest verts in Source space; normals computed post-transform.
    verts: list[list[float]] = []
    tris: list[tuple[str, list[list]]] = []  # (material, [(v, uv, [(bone,w)])x3])
    nmap: dict[int, list[float]] = {}

    def add_tri(mat, i0, i1, i2):
        tris.append((mat, [i0, i1, i2]))

    def add_vert(pos, uv, links):
        vid = len(verts)
        verts.append((pos, uv, links))
        return vid

    # gun rigid pieces
    gun_meshes = {m["name"]: m for m in gundump["meshes"]}
    for name, node_idx in PIECE_NODE.items():
        m = gun_meshes[name]
        nv = m["vertex_count"]
        vs = m["vertices"]
        uvs = m["uvs"]
        ids = []
        for vi in range(nv):
            p = mapply(MXH, vs[3 * vi:3 * vi + 3])
            ids.append(add_vert(p, (uvs[2 * vi], 1.0 - uvs[2 * vi + 1]),
                                [(cf_to_smd[node_idx], 1.0)]))
        for t in range(0, len(m["triangles"]), 3):
            a, b, c = m["triangles"][t:t + 3]
            add_tri("rif_m4a1", ids[a], ids[c], ids[b])  # mirrored verts -> flipped winding

    # arm skinned meshes: re-pose arm-bind -> gun-bind via per-vert LBS
    arm_names = [n["name"] for n in armdump["skeleton"]]
    for m in armdump["meshes"]:
        matname = "cf_foxhand_bl" if "HAND" in m["name"].upper() else "cf_foxarm_bl"
        nv = m["vertex_count"]
        vs, uvs = m["vertices"], m["uvs"]
        bw, bi = m["bone_weights"], m["bone_indices"]
        ids = []
        for vi in range(nv):
            v = vs[3 * vi:3 * vi + 3]
            w0, w1, w2 = bw[3 * vi:3 * vi + 3]
            w3 = max(0.0, 1.0 - w0 - w1 - w2)
            acc = [0.0, 0.0, 0.0]
            links = []
            for ni, w in zip(bi[4 * vi:4 * vi + 4], (w0, w1, w2, w3)):
                if ni == 255 or ni >= len(arm_names) or w <= 1e-6:
                    continue
                pidx = name2idx[arm_names[ni]]
                repose = mmul(B[pidx], BARM_INV[pidx])
                pt = mapply(repose, v)
                for c in range(3):
                    acc[c] += w * pt[c]
                links.append((cf_to_smd[pidx], w))
            ids.append(add_vert(mapply(MXH, acc),
                                (uvs[2 * vi], 1.0 - uvs[2 * vi + 1]), links))
        for t in range(0, len(m["triangles"]), 3):
            a, b, c = m["triangles"][t:t + 3]
            add_tri(matname, ids[a], ids[c], ids[b])  # mirrored verts -> flipped winding

    # smooth normals on final source-space geometry
    for _mat, tri in tris:
        p0, p1, p2 = (verts[i][0] for i in tri)
        u = [p1[c] - p0[c] for c in range(3)]
        v = [p2[c] - p0[c] for c in range(3)]
        fn = norm3([u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0]])
        for i in tri:
            nmap.setdefault(i, [0.0, 0.0, 0.0])
            for c in range(3):
                nmap[i][c] += fn[c]
    norms = {i: norm3(n) for i, n in nmap.items()}

    model_smd = SOURCE1 / "cf_native_vm.smd"
    with model_smd.open("w", encoding="utf-8") as f:
        write_nodes(f)
        f.write("skeleton\n")
        write_frame(f, 0, ref_world, [None] * nbones)
        f.write("end\ntriangles\n")
        for mat, tri in tris:
            f.write(mat + "\n")
            for i in tri:
                pos, uv, links = verts[i]
                n = norms[i]
                ls = " ".join(f"{b} {w:.6f}" for b, w in links)
                f.write(f"  {links[0][0]} {pos[0]:.6f} {pos[1]:.6f} {pos[2]:.6f} "
                        f"{n[0]:.6f} {n[1]:.6f} {n[2]:.6f} {uv[0]:.6f} {uv[1]:.6f} "
                        f"{len(links)} {ls}\n")
        f.write("end\n")

    # ---------- anim SMDs ----------
    clips = clips_by_name
    seq_frames = {}
    for seq, clip in CLIP_TO_SEQ.items():
        out = ANIMS / f"{seq}.smd"
        if clip is None:  # frozen idle for inspect trio
            samples = [clips["idle_0"]["samples"][0]]
        else:
            samples = clips[clip]["samples"]
        worlds_per_frame = []
        for s in samples:
            w = [I] * nbones
            for i in range(1, 1 + len(CS_BONES)):
                w[i] = FAR
            for i in cf_node_ids:
                a = sample_world(s, i)
                w[cf_to_smd[i]] = anim_world(a, minv(B[i]), ref_world[cf_to_smd[i]])
            for k, off in enumerate(attach_offsets.values()):
                w[attach_base + k] = mmul(w[gun_smd], off)
            worlds_per_frame.append(w)
        with out.open("w", encoding="utf-8") as f:
            write_nodes(f)
            f.write("skeleton\n")
            prev_e = [None] * nbones
            for t, w in enumerate(worlds_per_frame):
                write_frame(f, t, w, prev_e)
            f.write("end\n")
        seq_frames[seq] = len(worlds_per_frame)
        print(f"[s05] {seq}: {len(worlds_per_frame)} frames")

    write_qc(seq_frames)
    build_materials()
    compile_model()
    stage_and_deploy()
    print("[s05] DONE")


# ---------- SMD reference parsing ----------

def parse_smd(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    nodes = {}
    frames = []
    mode = None
    cur = None
    for ln in lines:
        s = ln.strip()
        if s == "nodes":
            mode = "n"; continue
        if s == "skeleton":
            mode = "s"; continue
        if s == "end":
            mode = None
            if cur is not None:
                frames.append(cur); cur = None
            continue
        if s == "triangles":
            if cur is not None:
                frames.append(cur); cur = None
            break
        if mode == "n":
            m = s.split('"')
            idx = int(s.split()[0])
            nodes[idx] = (m[1], int(s.rsplit('"', 1)[1]))
        elif mode == "s":
            if s.startswith("time"):
                if cur is not None:
                    frames.append(cur)
                cur = {}
            else:
                parts = s.split()
                cur[int(parts[0])] = tuple(float(v) for v in parts[1:7])
    if cur is not None:
        frames.append(cur)
    return {"nodes": nodes, "frames": frames}


def euler_to_mat(e):
    rx, ry, rz = e
    cx, sx, cy, sy, cz, sz = (math.cos(rx), math.sin(rx), math.cos(ry),
                             math.sin(ry), math.cos(rz), math.sin(rz))
    # R = Rz @ Ry @ Rx
    return [
        [cz * cy, cz * sy * sx - sz * cx, cz * sy * cx + sz * sx, 0],
        [sz * cy, sz * sy * sx + cz * cx, sz * sy * cx - cz * sx, 0],
        [-sy, cy * sx, cy * cx, 0],
        [0, 0, 0, 1],
    ]


def compose_worlds(nodes, frame):
    worlds = {}
    def world(i):
        if i in worlds:
            return worlds[i]
        pos, e = frame[i][:3], frame[i][3:]
        m = euler_to_mat(e)
        m[0][3], m[1][3], m[2][3] = pos
        name, p = nodes[i]
        worlds[i] = mmul(world(p), m) if p >= 0 else m
        return worlds[i]
    for i in nodes:
        world(i)
    return worlds


# ---------- QC / materials / compile / deploy ----------

def write_qc(seq_frames):
    qc = f'''$modelname "weapons\\v_rif_m4a1.mdl"

$bodygroup "studio"
{{
	studio "cf_native_vm.smd"
}}

$surfaceprop "default"
$contents "solid"
$illumposition 16.4 -2.125 -8.448
$cdmaterials "models\\weapons\\V_models\\rif_m4a1\\"
$cdmaterials "{ARM_DIR_VMT}\\"

$attachment "1" "v_weapon.flash" 0 0 0 rotate 0 0 0
$attachment "2" "v_weapon.shelleject" 0 0 0 rotate 0 0 0
$attachment "stattrack" "v_weapon.stattrack" 0 0 0 rotate 0 0 0
$attachment "uid" "v_weapon.uid" 0 0 0 rotate 0 0 0

$cbox 0 0 0 0 0 0
$bbox -30 -30 -30 30 30 30

$bonemerge "v_weapon"
''' + "\n".join(f'$bonemerge "{n}"' for n in CS_BONES) + '''

$animblocksize 32 nostall

$sequence "idle" {
	"v_rif_m4a1_anims\\idle.smd"
	activity "ACT_VM_IDLE" 1
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "fire1" {
	"v_rif_m4a1_anims\\fire1.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "fire2" {
	"v_rif_m4a1_anims\\fire2.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "fire3" {
	"v_rif_m4a1_anims\\fire3.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "reload" {
	"v_rif_m4a1_anims\\reload.smd"
	activity "ACT_VM_RELOAD" 1
	{ event 5004 19 "Weapon_M4A1.Clipout" }
	{ event 5004 72 "Weapon_M4A1.Clipin" }
	{ event 5004 134 "Weapon_M4A1.BoltBack" }
	{ event AE_WPN_COMPLETE_RELOAD 121 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "draw" {
	"v_rif_m4a1_anims\\draw.smd"
	activity "ACT_VM_DRAW" 1
	{ event 5004 1 "Weapon_M4A1.Draw" }
	{ event 5004 30 "Weapon_M4A1.BoltBack" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "lookat01" {
	"v_rif_m4a1_anims\\lookat01.smd"
	fadein 0.3
	fadeout 0.3
	fps 100
}

$sequence "lookat01_prepare" {
	"v_rif_m4a1_anims\\lookat01_prepare.smd"
	fadein 0.2
	fadeout 0.2
	fps 100
}

$sequence "lookat01_loop" {
	"v_rif_m4a1_anims\\lookat01_loop.smd"
	fadein 0.2
	fadeout 0.2
	fps 100
}
'''
    (SOURCE1 / "v_rif_m4a1.qc").write_text(qc, encoding="utf-8")


def vtfcmd(png: Path, dest: Path, fmt: str):
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(VTFCMD), "-file", str(png), "-output", str(dest.parent),
         "-format", fmt, "-version", "7.4"],
        capture_output=True, text=True, encoding="utf-8", errors="replace")
    produced = dest.parent / (png.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed for {png.name}: {proc.stderr or proc.stdout}")
    if produced != dest:
        produced.replace(dest)


def build_materials():
    mat_dir = ISOLATED / "materials" / "models/weapons/v_models/cf_leishen"
    vtfcmd(ARMTEX / "4x_up_hand_00001_.png", mat_dir / "cf_foxhand_bl.vtf", "dxt1")
    vtfcmd(ARMTEX / "4x_up_arm_00001_.png", mat_dir / "cf_foxarm_bl.vtf", "dxt1")
    vtfcmd(ARMTEX / "FVIEW_HAND_Foxhowl_Renewal_BL_N.PNG", mat_dir / "cf_foxhand_bl_n.vtf", "dxt5")
    vtfcmd(ARMTEX / "FVIEW_ARM_Foxhowl_Renewal_BL_N.PNG", mat_dir / "cf_foxarm_bl_n.vtf", "dxt5")
    vmt_tpl = '''"VertexLitGeneric"
{
	"$basetexture" "%s/%s"
	"$bumpmap" "%s/%s_n"
	"$phong" "1"
	"$phongexponent" "8"
	"$phongboost" "0.6"
	"$phongfresnelranges" "[0.1 0.5 1]"
	"$nocull" "0"
}
'''
    for name in ("cf_foxhand_bl", "cf_foxarm_bl"):
        (mat_dir / f"{name}.vmt").write_text(
            vmt_tpl % (ARM_DIR_VMT, name, ARM_DIR_VMT, name), encoding="utf-8")


def compile_model():
    shutil.copy2(GAME / "csgo" / "gameinfo.txt", ISOLATED / "gameinfo.txt")
    # gun material dir must exist in isolated game for studiomdl material lookups
    src_mat = P6_ADDON / "materials/models/weapons/v_models/rif_m4a1"
    dst_mat = ISOLATED / "materials/models/weapons/v_models/rif_m4a1"
    if src_mat.is_dir():
        shutil.copytree(src_mat, dst_mat, dirs_exist_ok=True)
    proc = subprocess.run(
        [str(STUDIOMDL), "-game", str(ISOLATED), str(SOURCE1 / "v_rif_m4a1.qc")],
        cwd=str(SOURCE1), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300)
    (LOG_DIR / "studiomdl.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "studiomdl.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    compiled = ISOLATED / "models" / "weapons" / "v_rif_m4a1.mdl"
    if proc.returncode != 0 or not compiled.is_file():
        raise RuntimeError(f"studiomdl failed: {(proc.stderr or proc.stdout or '')[-1500:]}")
    print("[s05] compiled", compiled)


def stage_and_deploy():
    models_rel = Path("models/weapons")
    mats_rel = Path("materials/models/weapons/v_models/cf_leishen")
    stage_models = STAGING / models_rel
    stage_models.mkdir(parents=True, exist_ok=True)
    for f in (ISOLATED / models_rel).glob("v_rif_m4a1.*"):
        shutil.copy2(f, stage_models / f.name)
    stage_mats = STAGING / mats_rel
    stage_mats.mkdir(parents=True, exist_ok=True)
    for f in (ISOLATED / mats_rel).glob("*"):
        shutil.copy2(f, stage_mats / f.name)
    # deploy: only v_rif_* + arm materials inside the existing p6 addon;
    # w_rif_* (third-person) and sound addon remain untouched.
    target = P6_ADDON
    for f in stage_models.glob("*"):
        dst = target / models_rel / f.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    for f in stage_mats.glob("*"):
        dst = target / mats_rel / f.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    print(f"[s05] deployed v_rif_m4a1 + arm materials into {target}")


if __name__ == "__main__":
    sys.exit(main())
