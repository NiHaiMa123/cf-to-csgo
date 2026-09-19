# -*- coding: utf-8 -*-
"""Galil ACE-天袭 P5 — pure-CF first-person viewmodel for weapons/v_rif_galilar.mdl.

Adapted from scripts/p5/p5_p7_s05_cf_native_vm.py with these differences:

- Gun pieces come from PV-GalilACE_PhantomBeast. Hands/sleeves are
  Arm_Nini_GR.LTB (妮妮-保卫者), LBS-reposed from arm bind into the
  gun bind (same FvARM bone names), then MXH. Roxana GR is frozen at
  work/galil_ace_tianxi/arms/roxana_gr_frozen/.
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

import hashlib
import json
import math
import shutil
import struct
import subprocess
import sys
from pathlib import Path

from PIL import Image

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
SOCKETS_JSON = WORK / "effects" / "discovery" / "sockets.json"
FX_SKIN_DIR = WORK / "effects" / "discovery" / "ltb_layers"
FX_TEX_DIR = WORK / "effects" / "discovery" / "previews"
ARMDUMP = WORK / "decode" / "nini_gr" / "cf_skin_nini_gr.json"
ARMTEX = WORK / "decode" / "nini_gr"
VM_TRANSFORM = WORK / "csref" / "viewmodel_transform.json"
DEPLOY_ADDON = GAME / "migi" / "csgo" / "addons" / "p_cf_tianxi_galilar_p1"

STUDIOMDL = GAME / "bin" / "studiomdl.exe"
DMXCONVERT = GAME / "bin" / "dmxconvert.exe"
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
ARM_MESHES = ("Fview-hand2", "Fview-arm2")  # unused; Nini ArmModel replaces these

# ---- idle FX layers, frozen 2026-09-16 (pipeline.md appendix B).
# Do not add ParticleSystem leftovers or re-enable eye quads unless asked.
FX_LTBS = WORK / "effects" / "discovery" / "assets" / "Models" / "PLAYERVIEW"
# fx mesh layers: (skin dump stem, socket name, material name, object scale,
# original offset, Source-space calibration after in-game review)
# L-flow Y/Z fudge is the in-game calibration from rounds 2–3; R-flow uses the
# same Source-space shift because both strips share MXH. Body-part layers stay
# at original socket origin (ICP: translation + Sk only).
FLOW_CAL = (0.0, 4.0, -1.8)
# PCF eye+halo on fx16. Source -Z is down (same axis as FLOW_CAL).
# 2026-09-17: -2.5 overshot (halo sat on the hand); user asked for 1/10.
EYE_CAL = (0.0, 0.0, -0.25)
FX_LAYERS = (
    ("SGFX_BD_PLANE_02_4", "fix_effect_9",
     "fx_galilace_l_flow_front", 0.026000000536441803,
     (0.0, 1.0, 0.0), FLOW_CAL),
    ("SGFX_BD_PLANE_02_4", "fix_effect_9",
     "fx_galilace_l_flow_front_copy", 0.026000000536441803,
     (0.0, 1.0, 0.0), FLOW_CAL),
    ("SGFX_BD_PLANE_02_5", "fix_effect_9",
     "fx_galilace_l_flow_back", 0.03700000047683716,
     (0.0, 1.0, 0.0), FLOW_CAL),
    ("SGFX_BD_PLANE_02_4", "fix_effect_23",
     "fx_galilace_l_flow_front", 0.027799999341368675,
     (1.0, 1.0, 0.0), FLOW_CAL),
    ("SGFX_BD_PLANE_02_4", "fix_effect_23",
     "fx_galilace_l_flow_front_copy", 0.027799999341368675,
     (1.0, 1.0, 0.0), FLOW_CAL),
    ("SGFX_BD_PLANE_02_5", "fix_effect_23",
     "fx_galilace_l_flow_back", 0.03669999912381172,
     (1.0, 1.0, 0.0), FLOW_CAL),
    ("SGFX_BD_GUN_GALILACE_PHANTOMBEAST_PARTS_BLUE", "fix_effect_5",
     "fx_galilace_parts_blue", 0.15000000596046448,
     (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ("SGFX_BD_GUN_GALILACE_PHANTOMBEAST_PARTS_RED", "fix_effect_5",
     "fx_galilace_parts_red", 0.15000000596046448,
     (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ("SGFX_BD_GUN_GALILACE_PHANTOMBEAST_PARTS_TRIANGLE_L", "fix_effect_5",
     "fx_galilace_tragl_l", 0.15000000596046448,
     (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ("SGFX_BD_GUN_GALILACE_PHANTOMBEAST_PARTS_TRIANGLE_R", "fix_effect_5",
     "fx_galilace_tragl_r", 0.15000000596046448,
     (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    # CF Offset (0,2,0) was being added in CF world axes; CF Y maps to Source
    # +Z and lifts these ~4 units above the gun (wall spec). Sit on the socket.
    ("SGFX_BD_PLANE_01", "fix_effect_10",
     "fx_galilace_simbol", 0.0020000000949949026,
     (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ("SGFX_BD_PLANE_01", "fix_effect_11",
     "fx_galilace_simbol_glow", 0.01600000075995922,
     (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
    ("SGFX_BD_GUN_GALILACE_PHANTOMBEAST_GLITCH", "fix_effect_10",
     "fx_galilace_glitch", 0.004800000227987766,
     (0.0, 0.0, 0.0), (0.0, 0.0, 0.0)),
)
ENABLE_EYE_GEOMETRY = False  # rejected quads; orbs unused — PCF eye is back
# sockets to turn into Source bones (all names used by the idle group)
FX_SOCKET_BONES = [f"fix_effect_{n}" for n in
                   (3, 5, 8, 9, 10, 11, 12, 15, 16, 17, 19, 22, 23, 34, 35)]
# attachment exposed for the PCF probe (core-glow socket)
FX_PROBE_ATTACH = "fx_fix_effect_3"

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


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


# ---------- build ----------

def main() -> int:
    for d in (SOURCE1, ANIMS, ISOLATED, STAGING, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)

    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    armdump = json.loads(ARMDUMP.read_text(encoding="utf-8"))
    vt = json.loads(VM_TRANSFORM.read_text(encoding="utf-8"))
    sockets = json.loads(SOCKETS_JSON.read_text(encoding="utf-8"))

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
    name2idx = {n["name"]: n["index"] for n in nodes}
    BARM = {name2idx[n["name"]]: flat16(n["bind_matrix"]) for n in armdump["skeleton"]
            if n["name"] in name2idx}
    BARM_INV = {i: minv(m) for i, m in BARM.items()}

    attach_targets = vt["attach_worlds_p6"]
    gun_root = 46  # Box001
    clips_by_name = payload["clips"]

    # ---- fx sockets from the _BL variant LTB socket table ----
    # socket record: {node_index, node_name, name, rot_quat, pos, scale}
    # CF-space local = T(pos) * R(quat) * S(scale) in the parent's node frame.
    # (_BL skeleton bind matrices verified identical to the base PV LTB rig,
    #  so payload B[] doubles as the socket-parent bind.)
    def socket_local(s):
        m = quat_to_mat(s["rot_quat"])
        for r in range(3):
            for c in range(3):
                m[r][c] *= s["scale"][c]
        m[0][3], m[1][3], m[2][3] = s["pos"]
        return m

    # name -> (parent_node_idx, cf-space socket world)
    fx_socks = {}
    for s in sockets["sockets"]:
        if s["name"] not in FX_SOCKET_BONES + ["gunfire"]:
            continue
        pb = B.get(s["node_index"], I)
        fx_socks[s["name"]] = (s["node_index"], mmul(pb, socket_local(s)))
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

    # ---- fx socket bones ----
    # bone "fx_<socket>" hangs under the socket's parent node bone; its local
    # transform is C(socket_local) (constant), so it rides the gun rigidly.
    fx_base = len(smd_nodes)
    fx_bone = {}          # socket name -> smd bone index
    fx_local = []         # bone-local matrix per fx bone
    for sname in FX_SOCKET_BONES:
        if sname not in fx_socks:
            continue
        pidx, w_cf = fx_socks[sname]
        p_smd = cf_to_smd.get(pidx, 0)          # Scene Root -> v_weapon
        fx_bone[sname] = len(smd_nodes)
        smd_nodes.append((f"fx_{sname}", p_smd))
        # Runtime attachment origin = bone world translation. anim_world()'s
        # conjugated translation is offset by H^-1*MX*0 (the mirror pivot is
        # not at the origin), which lands socket bones ~5 units off the gun.
        # Keep anim_world's rotation but force the translation to the same
        # point map the mesh uses: MXH @ socket_world_cf.translation.
        w_des = anim_world(w_cf)
        tp = mapply(MXH, [w_cf[0][3], w_cf[1][3], w_cf[2][3]])
        if sname == "fix_effect_16":
            tp = [tp[i] + EYE_CAL[i] for i in range(3)]
        w_des[0][3], w_des[1][3], w_des[2][3] = tp
        if pidx == 0:
            fx_local.append(w_des)              # v_weapon world == I
        else:
            fx_local.append(mmul(minv(anim_world(B[pidx])), w_des))
    fx_at_gun = [n for n in FX_SOCKET_BONES
                 if n in fx_socks and fx_socks[n][0] == gun_root]
    print(f"[galil] fx bones={len(fx_bone)} (on gun: {len(fx_at_gun)})")

    nbones = len(smd_nodes)
    print(f"[galil] bones={nbones} (1+{len(CS_BONES)} cs + {len(cf_node_ids)} cf + {len(ATTACH_BONES)} attach + {len(EXTRA_GUN_BONES)} extra + {len(fx_bone)} fx)")

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
    for k, sname in enumerate([n for n in FX_SOCKET_BONES if n in fx_bone]):
        ps = smd_nodes[fx_bone[sname]][1]
        ref_world[fx_bone[sname]] = mmul(ref_world[ps], fx_local[k])

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

    # Nini GR ArmModel: re-pose arm-bind -> gun-bind via per-vert LBS
    arm_names = [n["name"] for n in armdump["skeleton"]]
    unmatched_bones = set()
    for m in armdump["meshes"]:
        matname = "cf_nini_hand_gr" if "HAND" in m["name"].upper() else "cf_nini_arm_gr"
        bw, bi = m["bone_weights"], m["bone_indices"]
        ids = []
        for vi in range(m["vertex_count"]):
            v = m["vertices"][3 * vi:3 * vi + 3]
            w0, w1, w2 = bw[3 * vi:3 * vi + 3]
            w3 = max(0.0, 1.0 - w0 - w1 - w2)
            acc = [0.0, 0.0, 0.0]
            links = []
            for ni, w in zip(bi[4 * vi:4 * vi + 4], (w0, w1, w2, w3)):
                if ni == 255 or ni >= len(arm_names) or w <= 1e-6:
                    continue
                aname = arm_names[ni]
                if aname not in name2idx or name2idx[aname] not in BARM_INV:
                    unmatched_bones.add(aname)
                    continue
                pidx = name2idx[aname]
                repose = mmul(B[pidx], BARM_INV[pidx])
                pt = mapply(repose, v)
                for c in range(3):
                    acc[c] += w * pt[c]
                links.append((cf_to_smd[pidx], w))
            if not links:
                links = [(cf_to_smd[gun_root], 1.0)]
            ids.append(add_vert(mapply(MXH, acc),
                                (m["uvs"][2 * vi], 1.0 - m["uvs"][2 * vi + 1]), links))
        for t in range(0, len(m["triangles"]), 3):
            a, b, c = m["triangles"][t:t + 3]
            tris.append((matname, [ids[a], ids[c], ids[b]]))
        print(f"[galil] arm mesh {m['name']}: {m['vertex_count']} verts -> {matname}")
    if unmatched_bones:
        print("[galil] unmatched arm bones skipped:", sorted(unmatched_bones))

    # ---- E2 probe: FX LTBModel mesh layers, socketed like CF does ----
    # CF chain: v_model = ParentBind x SocketLocal x v_ltb; verts stored in
    # that posed space, then mapped by MXH like every other vert, and skinned
    # 1.0 to the socket bone so they ride its (rigid) parent motion.
    for stem, sname, matname, scale, offset, source_adjust in FX_LAYERS:
        dump_p = FX_SKIN_DIR / f"{stem}.skin.json"
        if sname not in fx_bone or not dump_p.is_file():
            print(f"[galil] WARN: fx layer {stem} skipped "
                  f"(socket={sname in fx_bone}, dump={dump_p.is_file()})")
            continue
        fd = json.loads(dump_p.read_text(encoding="utf-8"))
        w = fx_socks[sname][1]
        anchor = [w[i][3] + offset[i] for i in range(3)]
        w_fx = [[scale, 0, 0, anchor[0]], [0, scale, 0, anchor[1]],
                [0, 0, scale, anchor[2]], [0, 0, 0, 1.0]]
        for fm in fd.get("meshes", []):
            ids = []
            for vi in range(fm["vertex_count"]):
                p = mapply(MXH, mapply(w_fx, fm["vertices"][3 * vi:3 * vi + 3]))
                p = [p[i] + source_adjust[i] for i in range(3)]
                u = fm["uvs"][2 * vi] if fm.get("uvs") else 0.0
                v = 1.0 - fm["uvs"][2 * vi + 1] if fm.get("uvs") else 0.0
                ids.append(add_vert(p, (u, v), [(fx_bone[sname], 1.0)]))
            for t in range(0, len(fm["triangles"]), 3):
                a, b, c = fm["triangles"][t:t + 3]
                tris.append((matname, [ids[a], ids[c], ids[b]]))
            print(f"[galil] fx layer {stem} ({fm['name']}): "
                  f"{fm['vertex_count']} verts -> socket {sname}")

    # Dragon eye as additive spheres on fx16. PCF on this viewmodel also
    # draws in world space (ground/wall star); mesh stays on the gun.
    # Not the rejected crossed-quad cards: UV sits on the flare core so
    # each shell reads as a glowing orb from any angle.
    if ENABLE_EYE_GEOMETRY and "fix_effect_16" in fx_bone:
        w16 = fx_socks["fix_effect_16"][1]
        c = mapply(MXH, [w16[0][3], w16[1][3], w16[2][3]])
        c[0] -= 0.35

        def glow_sphere(center, radius, bone, stacks=5, slices=8):
            rings = []
            for i in range(stacks + 1):
                phi = math.pi * i / stacks
                sp, cp = math.sin(phi), math.cos(phi)
                ring = []
                for j in range(slices):
                    th = 2.0 * math.pi * j / slices
                    p = [center[0] + radius * sp * math.cos(th),
                         center[1] + radius * sp * math.sin(th),
                         center[2] + radius * cp]
                    ring.append(add_vert(p, (0.5, 0.5), [(bone, 1.0)]))
                rings.append(ring)
            out = []
            for i in range(stacks):
                for j in range(slices):
                    jn = (j + 1) % slices
                    a, b = rings[i][j], rings[i][jn]
                    d, e = rings[i + 1][j], rings[i + 1][jn]
                    if i != 0:
                        out.append([a, b, e])
                    if i != stacks - 1:
                        out.append([a, e, d])
            return out

        bone = fx_bone["fix_effect_16"]
        for t in glow_sphere(c, 3.0, bone):
            tris.append(("fx_galilace_eye_halo", t))
        for t in glow_sphere(c, 2.1, bone):
            tris.append(("fx_galilace_eye", t))
        for t in glow_sphere(c, 0.85, bone, stacks=4, slices=6):
            tris.append(("fx_galilace_eye_core", t))
        print(f"[galil] dragon-eye orbs -> fx16 at {[round(x, 2) for x in c]}")

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
            for k, sname in enumerate([n for n in FX_SOCKET_BONES if n in fx_bone]):
                ps = smd_nodes[fx_bone[sname]][1]
                w[fx_bone[sname]] = mmul(w[ps], fx_local[k])
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
    if "--skip-materials" not in sys.argv:
        build_materials()
    compile_pcf()
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
$attachment "fx3" "fx_fix_effect_3" 0 0 0 rotate 0 0 0
$attachment "fx5" "fx_fix_effect_5" 0 0 0 rotate 0 0 0
$attachment "fx15" "fx_fix_effect_15" 0 0 0 rotate 0 0 0
$attachment "fx16" "fx_fix_effect_16" 0 0 0 rotate 0 0 0
$attachment "fx34" "fx_fix_effect_34" 0 0 0 rotate 0 0 0

$cbox 0 0 0 0 0 0
$bbox -30 -30 -30 30 30 30

$bonemerge "v_weapon"
''' + "\n".join(f'$bonemerge "{n}"' for n in CS_BONES) + '''
$bonemerge "v_weapon.galilar_parent"
$bonemerge "v_weapon.stattrack"
$bonemerge "v_weapon.uid"

$keyvalues
{
	"particles"
	{
		"effect"
		{
			"name" "cf_tianxi_eye"
			"attachment_type" "follow_attachment"
			"attachment_point" "fx16"
		}
	}
}

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


def arm_oil_vmt(name: str) -> str:
    # Phong-only oil. CF Silver_map02 envcube on the viewmodel blew the
    # sleeve to noisy white (same class as the frozen gun envmap wash).
    # Boost 1.2 after user halved 2.4; exponent 5 = broader satin lobe.
    return f'''"VertexLitGeneric"
{{
	"$basetexture" "{MAT_DIR_VMT}/{name}"
	"$bumpmap" "{MAT_DIR_VMT}/{name}_n"
	"$phong" "1"
	"$phongexponent" "5"
	"$phongboost" "1.2"
	"$phongfresnelranges" "[0.15 0.55 1]"
	"$phongalbedotint" "1"
	"$nocull" "0"
}}
'''


def vtfcmd(png: Path, dest: Path, fmt: str, flags: tuple[str, ...] = ()):
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(VTFCMD), "-file", str(png), "-output", str(dest.parent),
           "-format", fmt, "-version", "7.4"]
    for fl in flags:
        cmd += ["-flag", fl]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    produced = dest.parent / (png.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed for {png.name}: {proc.stderr or proc.stdout}")
    if produced != dest:
        produced.replace(dest)


def write_animated_vtf(frames: list[Path], dest: Path):
    if not frames:
        raise RuntimeError("animated VTF requires at least one frame")
    pixels = []
    width = height = None
    for frame in frames:
        with Image.open(frame) as source:
            image = source.convert("RGBA")
            if width is None:
                width, height = image.size
            elif image.size != (width, height):
                raise RuntimeError(f"animated VTF frame size mismatch: {frame}")
            pixels.append(image.tobytes("raw", "BGRA"))
    header = bytearray(80)
    header[:4] = b"VTF\x00"
    struct.pack_into("<II", header, 4, 7, 2)
    struct.pack_into("<I", header, 12, len(header))
    struct.pack_into("<HH", header, 16, width, height)
    struct.pack_into("<I", header, 20, 0x30C)
    struct.pack_into("<HH", header, 24, len(frames), 0)
    struct.pack_into("<fff", header, 32, 0.5, 0.5, 0.5)
    struct.pack_into("<f", header, 48, 1.0)
    struct.pack_into("<I", header, 52, 12)
    header[56] = 1
    struct.pack_into("<I", header, 57, 0xFFFFFFFF)
    struct.pack_into("<H", header, 63, 1)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(bytes(header) + b"".join(pixels))


def build_materials():
    mat_dir = ISOLATED / "materials" / MAT_DIR_VMT
    # NOTE: cf_galilace_pb.* (diffuse vtf + vmt) and the arm VMTs are owned by
    # texture/build_textures_v2.py (v7: 2048 BGRA diffuse + selfillum mask +
    # phongalbedotint). This script must NOT regenerate them.
    v7_dir = STAGING / "materials" / MAT_DIR_VMT
    for pattern in ("cf_galilace_pb*", "cf_gold_cube.vtf"):
        for source in v7_dir.glob(pattern):
            shutil.copy2(source, mat_dir / source.name)
    def arm_diffuse(stem: str) -> Path:
        hd = ARMTEX / "up" / f"4x_{stem}.png"
        return hd if hd.is_file() else ARMTEX / f"{stem}.png"
    filt = ("TRILINEAR", "ANISOTROPIC")
    hand_dif = arm_diffuse("FVIEW_HAND_Nini_GR")
    arm_dif = arm_diffuse("FVIEW_ARM_Nini_GR")
    vtfcmd(hand_dif, mat_dir / "cf_nini_hand_gr.vtf",
           "bgra8888" if "4x_" in hand_dif.name else "dxt1", filt)
    vtfcmd(arm_dif, mat_dir / "cf_nini_arm_gr.vtf",
           "bgra8888" if "4x_" in arm_dif.name else "dxt1", filt)
    vtfcmd(ARMTEX / "FVIEW_HAND_Nini_GR_N.PNG", mat_dir / "cf_nini_hand_gr_n.vtf",
           "dxt5", filt + ("NORMAL",))
    vtfcmd(ARMTEX / "FVIEW_ARM_Nini_GR_N.PNG", mat_dir / "cf_nini_arm_gr_n.vtf",
           "dxt5", filt + ("NORMAL",))
    for name in ("cf_nini_hand_gr", "cf_nini_arm_gr"):
        (mat_dir / f"{name}.vmt").write_text(arm_oil_vmt(name), encoding="utf-8")
    for stale in (list(mat_dir.glob("cf_fox*")) + list(mat_dir.glob("cf_roxana*"))
                  + list(mat_dir.glob("cf_silver_cube*"))):
        stale.unlink()

    # ---- E2 probes: fx textures/materials ----
    # Mesh materials must NOT set $vertexcolor/$vertexalpha — SMD tris carry
    # no vertex color, so those flags zero the additive output.
    glow_png = FX_TEX_DIR / "FX_SGFX_BD_GLOW_02.png"
    if glow_png.is_file():
        vtfcmd(glow_png, mat_dir / "cf_fx_glow02.vtf", "dxt5")
    simbol_png = FX_TEX_DIR / "FX_SGFX_BD_GUN_GALILACE_PHANTOMBEAST_SIMBOL_B.png"
    if simbol_png.is_file():
        vtfcmd(simbol_png, mat_dir / "cf_fx_simbol.vtf", "dxt5")
    flr_png = FX_TEX_DIR / "FX3_FLR0030.png"
    if flr_png.is_file():
        vtfcmd(flr_png, mat_dir / "cf_fx_flr0030.vtf", "dxt5")

    def write_mesh_vmt(name, texture, color, sine_min="0.35", frame_rate=None):
        proxies = ""
        frame_line = ""
        if frame_rate is not None:
            frame_line = '\n\t"$frame" "0"'
            proxies = '''
	"Proxies"
	{
		"AnimatedTexture"
		{
			"animatedTextureVar" "$basetexture"
			"animatedTextureFrameNumVar" "$frame"
			"animatedTextureFrameRate" "%s"
		}
		"Sine"
		{
			"sineperiod" "2"
			"sinemin" "%s"
			"sinemax" "1.0"
			"timeoffset" "0"
			"resultvar" "$alpha"
		}
	}''' % (frame_rate, sine_min)
        else:
            proxies = '''
	"Proxies"
	{
		"Sine"
		{
			"sineperiod" "2"
			"sinemin" "%s"
			"sinemax" "1.0"
			"timeoffset" "0"
			"resultvar" "$alpha"
		}
	}''' % sine_min
        text = '''"UnlitGeneric"
{
	"$basetexture" "%s/%s"%s
	"$additive" "1"
	"$translucent" "1"
	"$nocull" "1"
	"$nofog" "1"
	"$color" "%s"%s
}
''' % (MAT_DIR_VMT, texture, frame_line, color, proxies)
        (mat_dir / f"{name}.vmt").write_text(text, encoding="utf-8")

    write_mesh_vmt("fx_galilace_parts_blue", "cf_fx_glow02",
                   "[0.074510 0.376471 1.0]")
    write_mesh_vmt("fx_galilace_parts_red", "cf_fx_glow02",
                   "[1.0 0.074510 0.074510]")
    write_mesh_vmt("fx_galilace_tragl_l", "cf_fx_glow02",
                   "[0.839216 0.086275 0.003922]")
    write_mesh_vmt("fx_galilace_tragl_r", "cf_fx_glow02",
                   "[0.839216 0.592157 0.003922]")
    write_mesh_vmt("fx_galilace_simbol", "cf_fx_simbol",
                   "[0.384314 0.686275 1.0]")
    write_mesh_vmt("fx_galilace_simbol_glow", "cf_fx_flr0030",
                   "[0.019608 0.192157 0.466667]")

    aura54 = [FX_TEX_DIR / f"FX_SPRITES_AURA_54_sgfx_bd_aura_54_{i:02d}.png"
              for i in range(24)]
    missing_aura54 = [str(frame) for frame in aura54 if not frame.is_file()]
    if missing_aura54:
        raise RuntimeError(f"AURA_54 frames missing: {missing_aura54}")
    write_animated_vtf(aura54, mat_dir / "cf_fx_aura54.vtf")
    flow_vmt = '''"UnlitGeneric"
{
	"$basetexture" "%s/%s"
	"$frame" "0"
	"$additive" "1"
	"$translucent" "1"
	"$nocull" "1"
	"$nofog" "1"
	"$color" "%s"
	"Proxies"
	{
		"AnimatedTexture"
		{
			"animatedTextureVar" "$basetexture"
			"animatedTextureFrameNumVar" "$frame"
			"animatedTextureFrameRate" "%s"
		}
	}
}
'''
    for name, texture, color in (
        ("fx_galilace_l_flow_front", "cf_fx_aura54", "[0.313725 0.658824 1.0]"),
        ("fx_galilace_l_flow_front_copy", "cf_fx_aura54", "[0.0 0.329412 0.666667]"),
    ):
        (mat_dir / f"{name}.vmt").write_text(
            flow_vmt % (MAT_DIR_VMT, texture, color, "11"), encoding="utf-8")
    aura55 = [FX_TEX_DIR / f"FX_SPRITES_AURA_55_sgfx_bd_aura_55_{i:02d}.png"
              for i in range(24)]
    missing_aura55 = [str(frame) for frame in aura55 if not frame.is_file()]
    if missing_aura55:
        raise RuntimeError(f"AURA_55 frames missing: {missing_aura55}")
    write_animated_vtf(aura55, mat_dir / "cf_fx_aura55.vtf")
    (mat_dir / "fx_galilace_l_flow_back.vmt").write_text(
        flow_vmt % (MAT_DIR_VMT, "cf_fx_aura55", "[0.349020 0.274510 0.976471]", "10"),
        encoding="utf-8")
    # particle material (referenced by cf_tianxi_fx.pcf): particles supply
    # per-particle color/alpha as vertex data -> $vertexcolor/$vertexalpha
    # REQUIRED here (opposite of the mesh material above).
    pmat = '''"UnlitGeneric"
{
	"$basetexture" "%s/cf_fx_glow02"
	"$additive" "1"
	"$translucent" "1"
	"$vertexcolor" "1"
	"$vertexalpha" "1"
	"$nocull" "1"
	"$nofog" "1"
}
''' % MAT_DIR_VMT
    (mat_dir / "cf_fx_glow02.vmt").write_text(pmat, encoding="utf-8")

    # ---- dragon-eye (long yan) flare sprites: CF idle group EYE cluster ----
    # EYE-main (FlareSpriteFX, SGFX_WK_SHINE_06) + EYE-CORE (SGFX_JY_SHINE_03)
    # at fix_effect_15/16. Same particle-material requirements as glow02.
    eye_vmt = '''"UnlitGeneric"
{
	"$basetexture" "%s/%s"
	"$additive" "1"
	"$translucent" "1"
	"$vertexcolor" "1"
	"$vertexalpha" "1"
	"$nocull" "1"
	"$nofog" "1"
}
'''
    for png_name, tex_name in (
        ("FX_SGFX_wk_shine_06", "cf_fx_shine06"),
        ("FX_SGFX_JY_SHINE_03", "cf_fx_jyshine03"),
        ("FX_sgfx_cy_kar98_light_14", "cf_fx_kar98_14"),
        ("FX_sgfx_cy_kar98_light05_2", "cf_fx_kar98_05"),
    ):
        src = FX_TEX_DIR / f"{png_name}.png"
        if src.is_file():
            vtfcmd(src, mat_dir / f"{tex_name}.vtf", "dxt5")
        (mat_dir / f"{tex_name}.vmt").write_text(
            eye_vmt % (MAT_DIR_VMT, tex_name), encoding="utf-8")

    glitch_frames = [
        FX_TEX_DIR / f"FX3_SPRITES_GLITCH_LINE03_sgfx_jy_glitch_line_03_{i:02d}.png"
        for i in range(15)
    ]
    if all(frame.is_file() for frame in glitch_frames):
        write_animated_vtf(glitch_frames, mat_dir / "cf_fx_glitch.vtf")
        write_mesh_vmt("fx_galilace_glitch", "cf_fx_glitch",
                       "[0.266667 0.047059 0.647059]", frame_rate="12")

    # dragon-eye geometry quads: additive mesh material (NO vertexcolor —
    # SMD tris carry none). Sine proxy drives the CF breathing (~2s period).
    eye_mesh_vmt = '''"UnlitGeneric"
{
	"$basetexture" "%s/cf_fx_shine06"
	"$additive" "1"
	"$translucent" "1"
	"$nocull" "1"
	"$nofog" "1"
	"$color" "[0.35 0.9 2.2]"
	"Proxies"
	{
		"Sine"
		{
			"sineperiod" "2"
			"sinemin" "0.45"
			"sinemax" "1.0"
			"timeoffset" "0"
			"resultvar" "$alpha"
		}
	}
}
''' % MAT_DIR_VMT
    (mat_dir / "fx_galilace_eye.vmt").write_text(eye_mesh_vmt, encoding="utf-8")
    eye_halo_vmt = '''"UnlitGeneric"
{
	"$basetexture" "%s/cf_fx_kar98_14"
	"$additive" "1"
	"$translucent" "1"
	"$nocull" "1"
	"$nofog" "1"
	"$color" "[0.25 0.55 1.4]"
	"Proxies"
	{
		"Sine"
		{
			"sineperiod" "2"
			"sinemin" "0.25"
			"sinemax" "0.7"
			"timeoffset" "0.4"
			"resultvar" "$alpha"
		}
	}
}
''' % MAT_DIR_VMT
    (mat_dir / "fx_galilace_eye_halo.vmt").write_text(eye_halo_vmt, encoding="utf-8")
    eye_core_vmt = '''"UnlitGeneric"
{
	"$basetexture" "%s/cf_fx_jyshine03"
	"$additive" "1"
	"$translucent" "1"
	"$nocull" "1"
	"$nofog" "1"
	"$color" "[1.6 1.7 2.2]"
	"Proxies"
	{
		"Sine"
		{
			"sineperiod" "2"
			"sinemin" "0.6"
			"sinemax" "1.0"
			"timeoffset" "0"
			"resultvar" "$alpha"
		}
	}
}
''' % MAT_DIR_VMT
    (mat_dir / "fx_galilace_eye_core.vmt").write_text(eye_core_vmt, encoding="utf-8")


def compile_pcf():
    src = WORK / "effects" / "probes" / "cf_tianxi_fx.txt"
    dst = WORK / "effects" / "probes" / "cf_tianxi_galilar_p1.pcf"
    if not DMXCONVERT.is_file():
        raise RuntimeError(f"dmxconvert missing: {DMXCONVERT}")
    proc = subprocess.run(
        [str(DMXCONVERT), "-i", str(src), "-o", str(dst),
         "-oe", "binary", "-of", "pcf"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        timeout=60)
    (LOG_DIR / "dmxconvert.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "dmxconvert.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0 or not dst.is_file():
        raise RuntimeError(
            f"dmxconvert failed: {(proc.stderr or proc.stdout or '')[-1500:]}")
    print("[galil] compiled", dst)


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
    for stale in (list(stage_mats.glob("cf_fox*")) + list(stage_mats.glob("cf_roxana*"))
                  + list(stage_mats.glob("cf_silver_cube*"))):
        stale.unlink()
    target = DEPLOY_ADDON
    for f in stage_models.glob("*"):
        dst = target / models_rel / f.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    tgt_mats = target / mats_rel
    tgt_mats.mkdir(parents=True, exist_ok=True)
    for f in stage_mats.glob("*"):
        dst = tgt_mats / f.name
        shutil.copy2(f, dst)
    for stale in (list(tgt_mats.glob("cf_fox*")) + list(tgt_mats.glob("cf_roxana*"))
                  + list(tgt_mats.glob("cf_silver_cube*"))):
        stale.unlink()
    # ---- E2 probe: custom particle file. MIGI merges addon particles by
    # convention: the .pcf must be named <folder-minus-prefix>.pcf, i.e.
    # cf_tianxi_galilar_p1.pcf for p_cf_tianxi_galilar_p1. It auto-appends
    # "!particles/<name>.pcf" to the manifest — do NOT ship our own manifest
    # (verified: MIGI regenerates it and drops non-conforming names).
    probes = WORK / "effects" / "probes"
    pcf = probes / "cf_tianxi_galilar_p1.pcf"
    if pcf.is_file():
        for root in (STAGING, target):
            pd = root / "particles"
            pd.mkdir(parents=True, exist_ok=True)
            shutil.copy2(pcf, pd / "cf_tianxi_galilar_p1.pcf")
            man = pd / "particles_manifest.txt"
            if man.is_file():
                man.unlink()
        print("[galil] deployed particles/cf_tianxi_galilar_p1.pcf")
    staged = {p.relative_to(STAGING).as_posix(): p for p in STAGING.rglob("*") if p.is_file()}
    deployed = {p.relative_to(target).as_posix(): p for p in target.rglob("*") if p.is_file()}
    missing = sorted(staged.keys() - deployed.keys())
    extra = sorted(deployed.keys() - staged.keys())
    mismatch = sorted(rel for rel in staged.keys() & deployed.keys()
                      if sha256(staged[rel]) != sha256(deployed[rel]))
    if missing or extra or mismatch:
        raise RuntimeError(f"A/B deploy mismatch: missing={missing}, extra={extra}, mismatch={mismatch}")
    print(f"[galil] A/B SHA-256 equal: {len(staged)}/{len(staged)} files")
    print(f"[galil] deployed v_rif_galilar + materials into {target}")


if __name__ == "__main__":
    sys.exit(main())
