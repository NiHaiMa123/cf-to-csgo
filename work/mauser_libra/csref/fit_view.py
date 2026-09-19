# -*- coding: utf-8 -*-
"""P3c — automatic residual VIEW fit for 毛瑟-天秤座 (reusable pattern).

H is rig-level (FvARM playerview space -> eye space) and intentionally does
NOT normalize per-weapon placement: CF authors each gun at its own offset
from Scene Root, so after H a pistol lands nearer the eye than a rifle.

Lesson learned (v3 failure): do NOT anchor CF bones to stock bones — the
rigs place body/arm differently relative to the hand, so pinning e.g. the
wrist to the stock wrist swings the arm through the camera. The CF rig is
internally consistent (hands glued to the gun); preserve it.

Correct scheme — near-translational residual about the gun's hold point:

  VIEW* = T(replace) · T(push_cloud) · T(grip) · R_fix · T(-grip)

  grip      : centroid of the nearest 10% skinned right-hand/gun surface pairs
  R_fix     : small frame correction — CF barrel PCA1 -> stock
              (flash - glock_parent), CF rig up -> +Z  (~2 deg here)
  push_cloud: stock/CF camera-side gun-cloud centroid alignment
  replace_z : align CF and stock skinned hand/gun contact-surface centroids

The arm rig rides the same residual — gun/hand/arm stay glued exactly as CF
authored; only depth/centring is corrected. No per-bone anchoring anywhere.
Writes "view_matrix" into viewmodel_transform.json (builder composes
VIEW = PUSH * ROLL * view_matrix; manual push/roll still stacks on top).
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path

import numpy as np

_REPO = Path(__file__).resolve().parents[3]
WORK = _REPO / "work" / "mauser_libra"
CSREF = WORK / "csref" / "decompiled_stock" / "v_pist_glock18"
PAYLOAD = WORK / "decode" / "reference_payload.json"
SKIN = WORK / "decode" / "cf_skin_m1896_libra.json"
ARMDUMP = _REPO / "work" / "galil_ace_tianxi" / "decode" / "nini_gr" / "cf_skin_nini_gr.json"
STOCK_GLOVE = (_REPO / "work" / "m4a1_s_bornbeast" / "blender_arm_reference" /
               "decompiled" / "glove_fullfinger" / "v_glove_fullfinger.smd")
VT = WORK / "csref" / "viewmodel_transform.json"

sys.path.insert(0, str(WORK / "csref"))
from fit_transform import PIECE_NODE, parse_smd, compose_worlds  # noqa: E402

BODY_MESH = "PV-Mauser_Libra"
RHAND_CF, RFORE_CF, RCLAV_CF = 29, 28, 26   # FvARM-bone R Hand/ForeArm/Clavicle
LHAND_CF, LFORE_CF, LCLAV_CF = 9, 8, 6      # FvARM-bone L Hand/ForeArm/Clavicle
STOCK_RHAND, STOCK_RFORE = "v_weapon.Bip01_R_Hand", "v_weapon.Bip01_R_Forearm"
STOCK_LHAND, STOCK_LFORE = "v_weapon.Bip01_L_Hand", "v_weapon.Bip01_L_Forearm"
STOCK_GUN_BONE = "v_weapon.glock_parent"
STOCK_MUZZLE = "v_weapon.flash"
GUN_BONE_IDS = {3, 4, 27, 28}  # glock_parent subtree bones that own gun verts
ARM_CHECK = {"R": (26, 27, 28, 29), "L": (6, 7, 8, 9)}


def quat_worlds(nodes, sample):
    W = []
    for i in range(len(nodes)):
        x, y, z, w = sample["quat_xyzw_world"][i]
        R = np.array([
            [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
            [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
            [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
        ])
        M = np.eye(4)
        M[:3, :3] = R
        M[:3, 3] = sample["pos"][i]
        W.append(M)
    return W


def xform(M, pts):
    hom = np.concatenate([pts, np.ones((len(pts), 1))], axis=1)
    return (M @ hom.T).T[:, :3]


def ortho_frame(e1, up):
    e1 = e1 / np.linalg.norm(e1)
    u = up - np.dot(up, e1) * e1
    e2 = u / np.linalg.norm(u)
    return np.stack([e1, e2, np.cross(e1, e2)], axis=1)


def rot_axis(axis, deg):
    ax = np.asarray(axis, float)
    ax /= np.linalg.norm(ax)
    t = math.radians(deg)
    ct, st = math.cos(t), math.sin(t)
    x, y, z = ax
    K = np.array([[0, -z, y], [z, 0, -x], [-y, x, 0]])
    return ct * np.eye(3) + (1 - ct) * np.outer(ax, ax) + st * K


def rot_between(u, v):
    """minimal rotation mapping direction u -> direction v."""
    u, v = u / np.linalg.norm(u), v / np.linalg.norm(v)
    c = float(np.clip(np.dot(u, v), -1, 1))
    if c > 0.999999:
        return np.eye(3)
    ax = np.cross(u, v)
    n = np.linalg.norm(ax)
    if n < 1e-9:
        ax = np.cross(u, [1, 0, 0])
        if np.linalg.norm(ax) < 1e-9:
            ax = np.cross(u, [0, 1, 0])
        return rot_axis(ax, 180.0)
    return rot_axis(ax / n, math.degrees(math.acos(c)))


def mat_to_axis_angle(R):
    c = float(np.clip((np.trace(R) - 1) / 2, -1, 1))
    deg = math.degrees(math.acos(c))
    if deg < 1e-4:
        return [0, 1, 0], 0.0
    ax = np.array([R[2, 1] - R[1, 2], R[0, 2] - R[2, 0], R[1, 0] - R[0, 1]])
    ax /= (2 * math.sin(math.radians(deg)))
    return ax.tolist(), deg


def smd_verts(path: Path):
    """(pos, bone_id) per vertex from the triangles section."""
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    vs, mode = [], False
    for ln in lines:
        s = ln.strip()
        if s == "triangles":
            mode = True
            continue
        if s == "end":
            if mode:
                break
            continue
        if mode:
            f = s.split()
            try:
                vs.append(([float(f[1]), float(f[2]), float(f[3])], int(f[0])))
            except (ValueError, IndexError):
                pass
    return vs


def smd_weighted_verts(path: Path):
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    out = []
    i = next(i for i, line in enumerate(lines) if line.strip() == "triangles") + 1
    while lines[i].strip() != "end":
        i += 1
        for _ in range(3):
            f = lines[i].split()
            parent = int(f[0])
            links = []
            if len(f) > 9:
                nlinks = int(f[9])
                links = [(int(f[10 + 2 * j]), float(f[11 + 2 * j]))
                         for j in range(nlinks)]
            out.append((np.array(f[1:4], float), links or [(parent, 1.0)]))
            i += 1
    return out


def surface_contact(hand, gun, fraction=0.1):
    hand = np.unique(np.round(hand, 5), axis=0)
    gun = np.unique(np.round(gun, 5), axis=0)
    dist2 = np.empty(len(hand))
    nearest = np.empty(len(hand), dtype=int)
    for start in range(0, len(hand), 256):
        stop = min(start + 256, len(hand))
        d2 = np.sum((hand[start:stop, None, :] - gun[None, :, :]) ** 2, axis=2)
        nearest[start:stop] = np.argmin(d2, axis=1)
        dist2[start:stop] = d2[np.arange(stop - start), nearest[start:stop]]
    count = max(32, int(round(len(hand) * fraction)))
    selected = np.argpartition(dist2, count - 1)[:count]
    hand_c = hand[selected].mean(0)
    gun_c = gun[nearest[selected]].mean(0)
    return (hand_c + gun_c) * 0.5, count, math.sqrt(float(dist2[selected].max()))


def ik_swing(clav, hand_cf, elbow_cf, hand_st, elbow_st):
    """rotation about clav: hand dir -> stock hand dir, elbow dir -> stock."""
    R1 = rot_between(hand_cf - clav, hand_st - clav)
    e1 = R1 @ (elbow_cf - clav)
    a = hand_st - clav
    a /= np.linalg.norm(a)
    pe = e1 - np.dot(e1, a) * a
    ps = (elbow_st - clav) - np.dot(elbow_st - clav, a) * a
    if np.linalg.norm(pe) < 1e-6 or np.linalg.norm(ps) < 1e-6:
        return R1
    sgn = np.sign(np.dot(np.cross(pe / np.linalg.norm(pe),
                                   ps / np.linalg.norm(ps)), a))
    ang = math.degrees(math.acos(float(np.clip(
        np.dot(pe / np.linalg.norm(pe), ps / np.linalg.norm(ps)), -1, 1))))
    return rot_axis(a, sgn * ang) @ R1


def main() -> int:
    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    armdump = json.loads(ARMDUMP.read_text(encoding="utf-8"))
    vt = json.loads(VT.read_text(encoding="utf-8"))
    nodes = payload["nodes"]

    s = float(vt["H"]["scale"])
    R = np.array(vt["H"]["rotation"], float)
    t = np.array(vt["H"]["translation"], float)
    H = np.eye(4)
    H[:3, :3] = s * R
    H[:3, 3] = t

    s0 = payload["clips"]["idle_0"]["samples"][0]
    W = quat_worlds(nodes, s0)

    body = None
    for m in skin["meshes"]:
        if m["name"] != BODY_MESH:
            continue
        ni = PIECE_NODE[m["name"]]
        B = np.array(nodes[ni]["bind_world"])
        D = W[ni] @ np.linalg.inv(B)
        body = xform(D, np.array(m["vertices"]).reshape(-1, 3))
    assert body is not None
    body_h = xform(H, body)
    xc = float((body_h[:, 0].min() + body_h[:, 0].max()) / 2)
    MX = np.array([[-1.0, 0, 0, 2 * xc], [0, 1.0, 0, 0], [0, 0, 1.0, 0],
                   [0, 0, 0, 1.0]])
    E = MX @ H
    HINV = np.linalg.inv(H)
    body_eye = xform(E, body)

    def eframe(wcf):
        return MX @ (H @ wcf @ HINV) @ MX

    payload_bind = {n["index"]: np.array(n["bind_world"]) for n in nodes}
    arm_bind = {n["name"]: np.array(n["bind_matrix"]).reshape(4, 4)
                for n in armdump["skeleton"]}
    name_to_idx = {n["name"]: n["index"] for n in nodes}
    arm_delta = {i: eframe(W[i]) @ np.linalg.inv(eframe(payload_bind[i]))
                 for i in name_to_idx.values()}
    hand_eye = []
    hand_mesh = next(m for m in armdump["meshes"] if "HAND" in m["name"].upper())
    arm_names = [n["name"] for n in armdump["skeleton"]]
    for vi in range(hand_mesh["vertex_count"]):
        p = np.array(hand_mesh["vertices"][3 * vi:3 * vi + 3])
        ws = list(hand_mesh["bone_weights"][3 * vi:3 * vi + 3])
        ws.append(max(0.0, 1.0 - sum(ws)))
        indices = hand_mesh["bone_indices"][4 * vi:4 * vi + 4]
        links = []
        right_weight = left_weight = 0.0
        acc = np.zeros(3)
        for ai, weight in zip(indices, ws):
            if ai == 255 or ai >= len(arm_names) or weight <= 1e-6:
                continue
            name = arm_names[ai]
            if name not in name_to_idx or name not in arm_bind:
                continue
            pi = name_to_idx[name]
            acc += weight * (payload_bind[pi] @ np.linalg.inv(arm_bind[name]) @
                             np.append(p, 1.0))[:3]
            links.append((pi, weight))
            right_weight += weight * (" R " in name)
            left_weight += weight * (" L " in name)
        if right_weight <= left_weight or not links:
            continue
        ref_point = (E @ np.append(acc, 1.0))[:3]
        posed = sum((weight * (arm_delta[pi] @ np.append(ref_point, 1.0))[:3]
                     for pi, weight in links), np.zeros(3))
        hand_eye.append(posed)
    hand_eye = np.array(hand_eye)
    contact_cf, contact_cf_count, contact_cf_radius = surface_contact(hand_eye, body_eye)

    # ---- CF landmarks ----
    rhand_cf = eframe(W[RHAND_CF])[:3, 3]
    grip_cf = contact_cf
    v0 = body_eye - body_eye.mean(0)
    _, _, vh = np.linalg.svd(v0, full_matrices=False)
    d = vh[0]
    proj = body_eye @ d
    hi = body_eye[np.argmax(proj)]
    muzzle_cf = hi if np.linalg.norm(hi - grip_cf) > np.linalg.norm(
        body_eye[np.argmin(proj)] - grip_cf) else body_eye[np.argmin(proj)]
    dir_cf = d if muzzle_cf is hi else -d
    dir_cf = dir_cf / np.linalg.norm(dir_cf)
    up_cf = E[:3, :3] @ np.array([0.0, 1.0, 0.0])
    up_cf /= np.linalg.norm(up_cf)

    # ---- stock landmarks ----
    idle = parse_smd(CSREF / "v_pist_glock18_anims" / "glock_idle.smd")
    iw = compose_worlds(idle["nodes"], idle["frames"][0])
    idx = {n[0]: i for i, n in idle["nodes"].items()}
    rhand_st = np.array(iw[idx[STOCK_RHAND]])[:3, 3]
    gbone = np.array(iw[idx[STOCK_GUN_BONE]])[:3, 3]
    flash_p = np.array(iw[idx[STOCK_MUZZLE]])[:3, 3]
    dir_st = flash_p - gbone
    dir_st /= np.linalg.norm(dir_st)
    up_st = np.array([0.0, 0.0, 1.0])
    elbows_st = {
        "R": np.array(iw[idx[STOCK_RFORE]])[:3, 3],
        "L": np.array(iw[idx[STOCK_LFORE]])[:3, 3],
    }
    hands_st = {"R": rhand_st, "L": np.array(iw[idx[STOCK_LHAND]])[:3, 3]}

    model = parse_smd(CSREF / "glock18_model.smd")
    mw = compose_worlds(model["nodes"], model["frames"][0])
    midx = {n[0]: i for i, n in model["nodes"].items()}
    # stock gun verts bind -> idle pose (per-vertex skinning W_b * B_b^-1)
    sverts = smd_verts(CSREF / "glock18_model.smd")
    gidle = []
    for p, b in sverts:
        if b in GUN_BONE_IDS and b in iw and b in mw:
            D = np.array(iw[b]) @ np.linalg.inv(np.array(mw[b]))
            gidle.append((D @ np.append(p, 1.0))[:3])
    gidle = np.array(gidle)

    glove = parse_smd(STOCK_GLOVE)
    glove_bind = compose_worlds(glove["nodes"], glove["frames"][0])
    stock_hand = []
    for p, links in smd_weighted_verts(STOCK_GLOVE):
        posed = np.zeros(3)
        right_weight = left_weight = 0.0
        for bone, weight in links:
            name = glove["nodes"][bone][0]
            if name not in idx:
                continue
            posed += weight * (np.array(iw[idx[name]]) @
                                np.linalg.inv(np.array(glove_bind[bone])) @
                                np.append(p, 1.0))[:3]
            right_weight += weight * ("_R_" in name)
            left_weight += weight * ("_L_" in name)
        if right_weight > left_weight:
            stock_hand.append(posed)
    contact_st, contact_st_count, contact_st_radius = surface_contact(
        np.array(stock_hand), gidle)

    # ---- residual: rotate about grip, then vertex-cloud framing ----
    F_cf = ortho_frame(dir_cf, up_cf)
    F_st = ortho_frame(dir_st, up_st)
    Rr = F_st @ F_cf.T

    def T(p):
        M = np.eye(4)
        M[:3, 3] = p
        return M

    ROT = np.eye(4)
    ROT[:3, :3] = Rr
    Vrot = T(grip_cf) @ ROT @ T(-grip_cf)          # rotate in place about grip

    # CF-authored lateral offset: in CF playerview space the gun sits off the
    # view axis — that off-axis *placement* is what shows the gun's flank in
    # CF renders (the CF bore itself is parallel to the view axis, like the
    # stock glock's). Scene Root is NOT the eye, so the raw atan2 overstates
    # it; the robust spec is the CF reference image's gun-centroid screen
    # position, translated through the calibrated CS projection
    # (viewmodel_fov 60 -> f = 288/tan(30deg), -x right / -y fwd / +z up).
    F_PX = 288.0 / math.tan(math.radians(30.0))
    CF_CENTROID_PX = (660.0, 430.0)   # gun body centre in the CF reference
    off_x = (CF_CENTROID_PX[0] - 512.0) / F_PX    # right = -x
    off_z = (288.0 - CF_CENTROID_PX[1]) / F_PX    # below centre = -z

    def near_centroid(verts, frac=0.4):
        """centroid of the camera-side (largest-y) fraction of a vert cloud."""
        y0, y1 = verts[:, 1].min(), verts[:, 1].max()
        near = verts[verts[:, 1] > y1 - frac * (y1 - y0)]
        return near.mean(0)

    body_rot = xform(Vrot, body_eye)
    push = near_centroid(gidle) - near_centroid(body_rot)
    VIEW = T(push) @ Vrot

    # re-place: lateral = CF-spec screen position (lateral offset is the CF
    # framing spec); vertical = skinned hand/gun surface-contact centroid.
    cen = xform(VIEW, body_eye).mean(0)
    target_x = -off_x * (-cen[1])
    contact_post = (VIEW @ np.append(contact_cf, 1.0))[:3]
    VIEW = T([target_x - cen[0], 0.0, contact_st[2] - contact_post[2]]) @ VIEW

    # ---- diagnostics ----
    body_new = xform(VIEW, body_eye)
    ang = math.degrees(math.acos(float(np.clip(np.dot(dir_cf, dir_st), -1, 1))))
    print(f"gun_center_x={xc:.4f}")
    print(f"cf  rhand={np.round(rhand_cf,2)} grip_pt={np.round(grip_cf,2)} muzzle={np.round(muzzle_cf,2)}")
    print(f"cf  dir={np.round(dir_cf,3)} up={np.round(up_cf,3)}")
    print(f"stk rhand={np.round(rhand_st,2)} gbone={np.round(gbone,2)} flash={np.round(flash_p,2)}")
    print(f"stk dir={np.round(dir_st,3)} gun_verts_idle={len(gidle)} "
          f"near_c={np.round(near_centroid(gidle),2)} cf_near={np.round(near_centroid(body_rot),2)}")
    print(f"barrel angle cf-vs-stock = {ang:.2f} deg")
    print(f"cf centroid spec px = {CF_CENTROID_PX} -> target_x {target_x:.2f} at depth {-cen[1]:.1f}")
    print(f"surface contact: cf n={contact_cf_count} r={contact_cf_radius:.3f} "
          f"pre={np.round(contact_post,2)} final={np.round((VIEW @ np.append(contact_cf,1))[:3],2)}")
    print(f"surface contact: stock n={contact_st_count} r={contact_st_radius:.3f} "
          f"target={np.round(contact_st,2)}")
    print(f"push={np.round(push,3)}")
    print(f"body bbox pre : {np.round(body_eye.min(0),2)} .. {np.round(body_eye.max(0),2)}")
    print(f"body bbox post: {np.round(body_new.min(0),2)} .. {np.round(body_new.max(0),2)}")
    print(f"grip post -> {np.round((VIEW @ np.append(grip_cf,1))[:3],2)}")
    print(f"hand post -> {np.round((VIEW @ np.append(rhand_cf,1))[:3],2)} (stk {np.round(rhand_st,2)})")
    print(f"det(R_res)={np.linalg.det(Rr):.4f}")
    # coarse frustum check on arm bones (cone ~ |x|<0.9|y|, |z|<0.7|y|, y<0)
    for i in (26, 27, 28, 29, 6, 7, 8, 9):
        p = (VIEW @ np.append(eframe(W[i])[:3, 3], 1))[:3]
        inv = (" *IN-CONE*" if p[1] < -0.5 and abs(p[0]) < -p[1] * 0.9
               and abs(p[2]) < -p[1] * 0.7 else "")
        print(f"  node{i:3d} {nodes[i]['name'][:26]:26s} {np.round(p,2)}{inv}")

    vt["view_matrix"] = VIEW.tolist()
    for k in ("view_push_x", "view_push_y", "view_push_z", "view_roll_deg"):
        vt[k] = 0.0
    for k in ("arm_rot_l_axis", "arm_rot_l_deg", "arm_rot_r_axis",
              "arm_rot_r_deg", "arm_offset_l", "arm_offset_r", "arm_pivot"):
        vt.pop(k, None)
    vt["gun_center_x"] = xc
    vt["view_fit"] = {
        "method": "barrel/rig-up rotation about the CF skinned hand-gun contact centroid, stock near-cloud depth framing, then re-place: lateral keeps the accepted CF reference x; vertical aligns the nearest 10% skinned hand-gun surface-contact centroids between CF and stock",
        "pivot_cf": "centroid of nearest 10% Nini right-hand/Mauser surface pairs in idle_0 frame 0",
        "barrel_angle_deg": round(ang, 3),
        "cf_centroid_px": list(CF_CENTROID_PX),
        "push": np.round(push, 3).tolist(),
        "centroid_target_x": round(float(target_x), 3),
        "surface_contact_stock": np.round(contact_st, 3).tolist(),
        "surface_contact_post": np.round((VIEW @ np.append(contact_cf, 1.0))[:3], 3).tolist(),
        "surface_contact_fraction": 0.1,
    }
    VT.write_text(json.dumps(vt, indent=2) + "\n", encoding="utf-8")
    print("wrote", VT)
    return 0


if __name__ == "__main__":
    sys.exit(main())
