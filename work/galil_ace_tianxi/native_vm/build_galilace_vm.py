# -*- coding: utf-8 -*-
"""Galil ACE-天袭 P5 — pure-CF first-person viewmodel for weapons/v_rif_galilar.mdl.

Adapted from scripts/p5/p5_p7_s05_cf_native_vm.py with these differences:

- Gun + CF hands come from ONE LTB (PV-GalilACE_PhantomBeast): the arm meshes
  Fview-hand2/Fview-arm2 are skinned to the same 56-node rig, so no separate
  arm bind/re-pose is needed -- verts go through MXH, weighted to CF nodes.
- H (CF->viewmodel similarity) is ICP-fitted against the STOCK v_rif_galilar
  idle-posed gun verts (work/galil_ace_tianxi/csref/viewmodel_transform.json,
  s=2.0025, proper rotation, symmetric trimmed mean 0.353).
- Event timing uses the LTB's authoritative keyframe event labels:
  reload WeaponClipOut @kf10 -> sample 33, WeaponClipIn @kf35 -> sample 117
  (100 fps resampled payload). BoltBack/Forward approximated from the
  secondary receiver-part motion window; retime after runtime review.
- Deploys to a NEW addon p_cf_tianxi_galilar_p1; the leishen addons and all
  third-person assets are untouched.
"""

from __future__ import annotations

import json
import math
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_ltb"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))

import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
WORK = REPO / "work" / "galil_ace_tianxi"
OUT = WORK / "native_vm"
SOURCE1 = OUT / "source1"
ANIMS = SOURCE1 / "v_rif_galilar_anims"
ISOLATED = OUT / "isolated_game" / "csgo"
STAGING = WORK / "addon"
LOG_DIR = OUT / "logs"

PAYLOAD = WORK / "decode" / "reference_payload.json"
SKIN = WORK / "decode" / "cf_skin_galilace.json"
GUN_TEX = WORK / "decode" / "PV-GalilACE_PhantomBeast.png"
GUN_NRM = WORK / "decode" / "maps" / "GalilACE_PhantomBeast_N.PNG"
GUN_SPE = WORK / "decode" / "maps" / "GalilACE_PhantomBeast_S.PNG"
ARMTEX = REPO / "work" / "p5_leishen" / "p7_s04_r1" / "source" / "armtex"
VM_TRANSFORM = WORK / "csref" / "viewmodel_transform.json"
DEPLOY_ADDON = GAME / "migi" / "csgo" / "addons" / "p_cf_tianxi_galilar_p1"

STUDIOMDL = GAME / "bin" / "studiomdl.exe"
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"

MAT_DIR_VMT = "models/weapons/v_models/cf_tianxi"

# rigid piece -> payload node index (verified by centroid<->bindpos proximity)
PIECE_NODE = {
    "Body": 46,        # Box001 (gun root)
    "Mag": 49,         # Mag_Dummy
    "Core01": 55,      # Dummy008
    "Core02": 53,      # Dummy006
    "Core03": 54,      # Dummy007
    "Object489": 50,   # Dummy001
    "Object490": 51,   # Dummy002
    "Object491": 52,   # Dummy003
    "Stock": 47,       # Dummy004
    "Object492": 48,   # Dummy005
}
ARM_MESHES = ("Fview-hand2", "Fview-arm2")

# CS bones that bonemerged arm/glove models ride on. All collapsed far away.
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
    "lookat01": "observe", "lookat01_prepare": None, "lookat01_loop": None,
}

# extra bones parented to the gun root for stock cosmetic compatibility
EXTRA_GUN_BONES = ("v_weapon.galilar_parent",)
ATTACH_BONES = ("v_weapon.flash", "v_weapon.shelleject",
                "v_weapon.stattrack", "v_weapon.uid")


# ---------- matrix helpers (numpy-free, lists) ----------

def mmul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def minv(m):
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
    # Source SMD convention: R = Rz(rz) @ Ry(ry) @ Rx(rz), radians.
    sy = max(-1.0, min(1.0, -m[2][0]))
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


# ---------- build ----------

def main() -> int:
    for d in (SOURCE1, ANIMS, ISOLATED, STAGING, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)

    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    vt = json.loads(VM_TRANSFORM.read_text(encoding="utf-8"))

    hs = vt["H"]["scale"]
    HR = vt["H"]["rotation"]
    HT = vt["H"]["translation"]
    H = [[HR[r][c] * hs for c in range(3)] + [HT[r]] for r in range(3)] \
        + [[0, 0, 0, 1.0]]
    HINV = minv(H)
    # raw CF handedness renders mirrored in-game; mirror about the gun's own
    # viewmodel x-centre (fitted bbox centre x = -5.223).
    GUN_XC = -5.223
    MX = [[-1.0, 0, 0, 2 * GUN_XC], [0, 1.0, 0, 0], [0, 0, 1.0, 0],
          [0, 0, 0, 1.0]]
    MXR = [[-1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
    I = [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]]
    MXH = mmul(MX, H)
    FAR = [[1.0, 0, 0, 0.0], [0, 1.0, 0, 500.0], [0, 0, 1.0, 0.0],
           [0, 0, 0, 1.0]]

    def rest_world(b):
        return mmul(MX, mmul(mmul(H, mmul(b, HINV)), MX))

    def anim_world(wcf, binv=None, rp=None):
        return mmul(MX, mmul(mmul(H, mmul(wcf, HINV)), MX))

    def mir_attach(w):
        r = [[sum(MXR[i][k] * w[k][j] for k in range(3)) for j in range(3)]
             for i in range(3)]
        r = [[sum(r[i][k] * MXR[k][j] for k in range(3)) for j in range(3)]
             for i in range(3)]
        p = mapply(MX, [w[0][3], w[1][3], w[2][3]])
        return [r[0] + [p[0]], r[1] + [p[1]], r[2] + [p[2]], [0, 0, 0, 1.0]]

    nodes = payload["nodes"]
    B = {n["index"]: n["bind_world"] for n in nodes}
    parent_cf = {n["index"]: n["parent"] for n in nodes}

    attach_targets = vt["attach_worlds_p6"]
    gun_root = 46  # Box001
    clips_by_name = payload["clips"]
    W_gun0 = anim_world(sample_world(clips_by_name["idle_0"]["samples"][0], gun_root))
    attach_offsets = {}
    for bname in ATTACH_BONES:
        attach_offsets[bname] = mmul(minv(W_gun0),
                                     mir_attach(attach_targets[bname]))

    # --- SMD node table ---
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
    gun_smd = cf_to_smd[gun_root]
    attach_base = len(smd_nodes)
    for bname in ATTACH_BONES + EXTRA_GUN_BONES:
        smd_nodes.append((bname, gun_smd))

    nbones = len(smd_nodes)
    print(f"[galil] bones={nbones} (1+{len(CS_BONES)} cs + {len(cf_node_ids)} cf + {len(ATTACH_BONES)} attach + {len(EXTRA_GUN_BONES)} extra)")

    ref_world = [I] * nbones
    for i in range(1, 1 + len(CS_BONES)):
        ref_world[i] = FAR
    for i in cf_node_ids:
        ref_world[cf_to_smd[i]] = rest_world(B[i])
    for k, bname in enumerate(ATTACH_BONES):
        ref_world[attach_base + k] = mmul(ref_world[gun_smd], attach_offsets[bname])
    # galilar_parent: coincident with gun root at rest
    for k in range(len(EXTRA_GUN_BONES)):
        ref_world[attach_base + len(ATTACH_BONES) + k] = ref_world[gun_smd]

    def locals_of(worlds):
        out = []
        for i, (name, p) in enumerate(smd_nodes):
            w = worlds[i]
            out.append(mmul(minv(worlds[p]), w) if p >= 0 else w)
        return out

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
    verts: list[tuple] = []
    tris: list[tuple[str, list]] = []
    nmap: dict[int, list[float]] = {}

    def add_vert(pos, uv, links):
        verts.append((pos, uv, links))
        return len(verts) - 1

    meshes = {m["name"]: m for m in skin["meshes"]}
    for name, node_idx in PIECE_NODE.items():
        m = meshes[name]
        ids = []
        for vi in range(m["vertex_count"]):
            p = mapply(MXH, m["vertices"][3 * vi:3 * vi + 3])
            ids.append(add_vert(p, (m["uvs"][2 * vi], 1.0 - m["uvs"][2 * vi + 1]),
                                [(cf_to_smd[node_idx], 1.0)]))
        for t in range(0, len(m["triangles"]), 3):
            a, b, c = m["triangles"][t:t + 3]
            tris.append(("cf_galilace_pb", [ids[a], ids[c], ids[b]]))

    # arm skinned meshes: bone_indices index the skeleton array == node index
    skel_index = {i: s["index"] for i, s in enumerate(skin["skeleton"])}
    for m in skin["meshes"]:
        if m["name"] not in ARM_MESHES:
            continue
        matname = "cf_foxhand_bl" if "HAND" in m["name"].upper() else "cf_foxarm_bl"
        bw, bi = m["bone_weights"], m["bone_indices"]
        ids = []
        for vi in range(m["vertex_count"]):
            w0, w1, w2 = bw[3 * vi:3 * vi + 3]
            w3 = max(0.0, 1.0 - w0 - w1 - w2)
            links = []
            for si, w in zip(bi[4 * vi:4 * vi + 4], (w0, w1, w2, w3)):
                if si == 255 or si >= len(skel_index) or w <= 1e-6:
                    continue
                links.append((cf_to_smd[skel_index[si]], w))
            if not links:
                links = [(cf_to_smd[gun_root], 1.0)]
            p = mapply(MXH, m["vertices"][3 * vi:3 * vi + 3])
            ids.append(add_vert(p, (m["uvs"][2 * vi], 1.0 - m["uvs"][2 * vi + 1]), links))
        for t in range(0, len(m["triangles"]), 3):
            a, b, c = m["triangles"][t:t + 3]
            tris.append((matname, [ids[a], ids[c], ids[b]]))

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

    xs = [v[0][0] for v in verts]
    ys = [v[0][1] for v in verts]
    zs = [v[0][2] for v in verts]
    illum = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2]

    # ---------- anim SMDs ----------
    seq_frames = {}
    seq_fps = {}
    for seq, clip in CLIP_TO_SEQ.items():
        out = ANIMS / f"{seq}.smd"
        if clip is None:
            samples = [clips_by_name["idle_0"]["samples"][0]]
        else:
            samples = clips_by_name[clip]["samples"]
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
            for k in range(len(EXTRA_GUN_BONES)):
                w[attach_base + len(ATTACH_BONES) + k] = w[gun_smd]
            worlds_per_frame.append(w)
        with out.open("w", encoding="utf-8") as f:
            write_nodes(f)
            f.write("skeleton\n")
            prev_e = [None] * nbones
            for t, w in enumerate(worlds_per_frame):
                write_frame(f, t, w, prev_e)
            f.write("end\n")
        seq_frames[seq] = len(worlds_per_frame)
        seq_fps[seq] = 100
        print(f"[galil] {seq}: {len(worlds_per_frame)} frames")

    write_qc(seq_frames, seq_fps, illum)
    build_materials()
    compile_model()
    stage_and_deploy()
    print("[galil] DONE")
    return 0


# ---------- QC / materials / compile / deploy ----------

def write_qc(seq_frames, seq_fps, illum):
    qc = f'''$modelname "weapons\\v_rif_galilar.mdl"

$bodygroup "studio"
{{
	studio "cf_native_vm.smd"
}}

$surfaceprop "default"
$contents "solid"
$illumposition {illum[0]:.3f} {illum[1]:.3f} {illum[2]:.3f}
$cdmaterials "models\\weapons\\v_models\\rif_galilar\\"
$cdmaterials "{MAT_DIR_VMT}\\"

$attachment "1" "v_weapon.flash" 0 0 0 rotate 0 0 0
$attachment "2" "v_weapon.shelleject" 0 0 0 rotate 0 0 0
$attachment "stattrack" "v_weapon.stattrack" 0 0 0 rotate 0 0 0
$attachment "uid" "v_weapon.uid" 0 0 0 rotate 0 0 0

$cbox 0 0 0 0 0 0
$bbox -30 -30 -30 30 30 30

$bonemerge "v_weapon"
''' + "\n".join(f'$bonemerge "{n}"' for n in CS_BONES) + '''
$bonemerge "v_weapon.galilar_parent"
$bonemerge "v_weapon.stattrack"
$bonemerge "v_weapon.uid"

$animblocksize 32 nostall

$sequence "idle" {
	"v_rif_galilar_anims\\idle.smd"
	activity "ACT_VM_IDLE" 1
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "fire1" {
	"v_rif_galilar_anims\\fire1.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "fire2" {
	"v_rif_galilar_anims\\fire2.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "fire3" {
	"v_rif_galilar_anims\\fire3.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "reload" {
	"v_rif_galilar_anims\\reload.smd"
	activity "ACT_VM_RELOAD" 1
	{ event 5004 33 "Weapon_GalilAR.Clipout" }
	{ event 5004 117 "Weapon_GalilAR.Clipin" }
	{ event 5004 140 "Weapon_GalilAR.BoltBack" }
	{ event 5004 160 "Weapon_GalilAR.BoltForward" }
	{ event AE_WPN_COMPLETE_RELOAD 120 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "draw" {
	"v_rif_galilar_anims\\draw.smd"
	activity "ACT_VM_DRAW" 1
	{ event 5004 3 "Weapon_GalilAR.Draw" }
	{ event 5004 45 "Weapon_GalilAR.BoltBack" }
	{ event 5004 58 "Weapon_GalilAR.BoltForward" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "lookat01" {
	"v_rif_galilar_anims\\lookat01.smd"
	{ event 5004 7 "Weapon_GalilAR.WeaponMove1" }
	{ event 5004 43 "Weapon_GalilAR.WeaponMove2" }
	{ event 5004 100 "Weapon_GalilAR.WeaponMove3" }
	{ event 5004 203 "Weapon_GalilAR.WeaponMove1" }
	{ event 5004 377 "Weapon_GalilAR.WeaponMove2" }
	{ event 5004 473 "Weapon_GalilAR.WeaponMove3" }
	fadein 0.3
	fadeout 0.3
	fps 100
}

$sequence "lookat01_prepare" {
	"v_rif_galilar_anims\\lookat01_prepare.smd"
	fadein 0.2
	fadeout 0.2
	fps 100
}

$sequence "lookat01_loop" {
	"v_rif_galilar_anims\\lookat01_loop.smd"
	fadein 0.2
	fadeout 0.2
	fps 100
}
'''
    (SOURCE1 / "v_rif_galilar.qc").write_text(qc, encoding="utf-8")


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
    mat_dir = ISOLATED / "materials" / MAT_DIR_VMT
    vtfcmd(GUN_TEX, mat_dir / "cf_galilace_pb.vtf", "dxt1")
    vtfcmd(GUN_NRM, mat_dir / "cf_galilace_pb_n.vtf", "dxt5")
    vtfcmd(ARMTEX / "4x_up_hand_00001_.png", mat_dir / "cf_foxhand_bl.vtf", "dxt1")
    vtfcmd(ARMTEX / "4x_up_arm_00001_.png", mat_dir / "cf_foxarm_bl.vtf", "dxt1")
    vtfcmd(ARMTEX / "FVIEW_HAND_Foxhowl_Renewal_BL_N.PNG", mat_dir / "cf_foxhand_bl_n.vtf", "dxt5")
    vtfcmd(ARMTEX / "FVIEW_ARM_Foxhowl_Renewal_BL_N.PNG", mat_dir / "cf_foxarm_bl_n.vtf", "dxt5")
    gun_vmt = '''"VertexLitGeneric"
{
	"$basetexture" "%s/cf_galilace_pb"
	"$bumpmap" "%s/cf_galilace_pb_n"
	"$phong" "1"
	"$phongexponent" "24"
	"$phongboost" "0.8"
	"$phongfresnelranges" "[0.15 0.5 1]"
	"$nocull" "0"
}
''' % (MAT_DIR_VMT, MAT_DIR_VMT)
    (mat_dir / "cf_galilace_pb.vmt").write_text(gun_vmt, encoding="utf-8")
    arm_vmt = '''"VertexLitGeneric"
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
            arm_vmt % (MAT_DIR_VMT, name, MAT_DIR_VMT, name), encoding="utf-8")


def compile_model():
    shutil.copy2(GAME / "csgo" / "gameinfo.txt", ISOLATED / "gameinfo.txt")
    proc = subprocess.run(
        [str(STUDIOMDL), "-game", str(ISOLATED), str(SOURCE1 / "v_rif_galilar.qc")],
        cwd=str(SOURCE1), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300)
    (LOG_DIR / "studiomdl.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "studiomdl.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    compiled = ISOLATED / "models" / "weapons" / "v_rif_galilar.mdl"
    if proc.returncode != 0 or not compiled.is_file():
        raise RuntimeError(f"studiomdl failed: {(proc.stderr or proc.stdout or '')[-1500:]}")
    print("[galil] compiled", compiled)


def stage_and_deploy():
    models_rel = Path("models/weapons")
    mats_rel = Path("materials") / MAT_DIR_VMT
    stage_models = STAGING / models_rel
    stage_models.mkdir(parents=True, exist_ok=True)
    for f in (ISOLATED / models_rel).glob("v_rif_galilar.*"):
        shutil.copy2(f, stage_models / f.name)
    stage_mats = STAGING / mats_rel
    stage_mats.mkdir(parents=True, exist_ok=True)
    for f in (ISOLATED / mats_rel).glob("*"):
        shutil.copy2(f, stage_mats / f.name)
    target = DEPLOY_ADDON
    for f in stage_models.glob("*"):
        dst = target / models_rel / f.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    for f in stage_mats.glob("*"):
        dst = target / mats_rel / f.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    print(f"[galil] deployed v_rif_galilar + materials into {target}")


if __name__ == "__main__":
    sys.exit(main())
