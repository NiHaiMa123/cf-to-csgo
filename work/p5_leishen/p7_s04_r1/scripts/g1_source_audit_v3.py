"""G1 v3 offline audit.

Keeps v1 source_audit.json as rejected-method evidence. Does not rank
matrix conventions by bind-vs-clip0, does not force bind=clip0, and does
not add pelvis/root compensation.

Convention is taken from public LithTech SDK plus local affine checks:
xyzw, column-3 translation, parent @ local. SDK mirror is not the current
CF runtime.
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(r"D:\project\cf_to_csgo")
sys.path.insert(0, str(ROOT / "scripts" / "p5"))
import p5_p7_s04_cf_animation as a  # noqa: E402

BODY_PATH = ROOT / "work/p5_leishen/p6/verified_root/Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB"
OFFLINE_AUDIT = ROOT / "work/p5_leishen/p7_s04_review_20260913/offline_audit.json"
PLANNER_NUMERIC = ROOT / "work/p5_leishen/p7_s04_review_20260913/review_g1_numeric.json"
OUT_DIR = ROOT / "work/p5_leishen/p7_s04_r1/source"
V1_AUDIT = OUT_DIR / "source_audit.json"

EXPECTED_BYTES = 604808
EXPECTED_SHA = "511dec8d2401a1886ddecd14b4f18e17ac0afbefd943f6dc11a3fd2f82ef6b49"
KEY_BONES = ["FvARM-bone Prop1", "FvARM-bone R Hand", "FvARM-bone L Hand", "Bone06", "Bone04"]
FOCUS_CLIPS = ("select", "reload", "idle_0")
DIAGNOSTIC_FPS = 100

CONVENTION = {
    "quat": "xyzw",
    "translation": "col3",
    "multiply": "parent_at_local",
    "bind_layout": "row_major_m_ij with last row 0001, translation in column 3",
    "source": "public LithTech SDK + local verification; NOT inferred from bind=clip0",
    "sdk_urls": [
        "https://raw.githubusercontent.com/jsj2008/lithtech/master/sdk/inc/ltrotation.h",
        "https://raw.githubusercontent.com/jsj2008/lithtech/master/runtime/model/src/transformmaker.cpp",
        "https://raw.githubusercontent.com/jsj2008/lithtech/master/sdk/inc/ltquatbase.h",
    ],
    "sdk_boundary": (
        "jsj2008/lithtech documents xyzw, ConvertToMatrix/Slerp, parent*local, "
        "and rotation-only nodes taking bind parent offset. This file has flags=0 "
        "so rotation-only is unused. The public mirror is not a line-by-line proof "
        "of the current CF runtime interpolator."
    ),
}

PLANNER_DELTA = {
    "reload": {"distance": 0.048451956732605696, "key": 96, "bone": "FvARM-bone L Finger12"},
    "select": {"distance": 3.5901666205131555e-05, "key": 15, "bone": "FvARM-bone L Finger12"},
    "idle_0": {"distance": 3.350985981888164e-05, "key": 38, "bone": "FvARM-bone L Finger12"},
}


def jsonable(obj):
    if isinstance(obj, dict):
        return {k: jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [jsonable(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, (np.floating, np.integer)):
        return obj.item()
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    return obj


def bone_index(nodes, name):
    for node in nodes:
        if node["name"] == name:
            return node["index"]
    raise KeyError(name)


def reshape16(flat):
    return np.array(flat, dtype=np.float64).reshape(4, 4)


def quat_to_R(q, normalize):
    q = np.array(q, dtype=np.float64)
    n = float(np.linalg.norm(q))
    if normalize and n > 0:
        q = q / n
    x, y, z, w = q
    return np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - w * z), 2.0 * (x * z + w * y)],
            [2.0 * (x * y + w * z), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - w * x)],
            [2.0 * (x * z - w * y), 2.0 * (y * z + w * x), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def local_matrix(pos, quat, normalize):
    M = np.eye(4, dtype=np.float64)
    M[:3, :3] = quat_to_R(quat, normalize)
    M[:3, 3] = np.array(pos, dtype=np.float64)
    return M


def compose_worlds(nodes, locals_):
    worlds = [None] * len(nodes)
    for index in a.dfs_nodes(nodes):
        parent = nodes[index]["parent"]
        loc = locals_[index]
        worlds[index] = loc if parent < 0 else worlds[parent] @ loc
    return worlds


def orthonormality(R):
    err = float(np.max(np.abs(R.T @ R - np.eye(3))))
    det = float(np.linalg.det(R))
    return err, det


def polar_rotation(A):
    """Closest rotation via SVD polar decomposition. Labeled extracted rotation."""
    U, _s, Vt = np.linalg.svd(A)
    R = U @ Vt
    if np.linalg.det(R) < 0:
        U = U.copy()
        U[:, -1] *= -1.0
        R = U @ Vt
    return R


def rot_angle_deg(A, B, *, require_rotation):
    if require_rotation:
        ea, da = orthonormality(A)
        eb, db = orthonormality(B)
        if ea > 1e-6 or eb > 1e-6 or abs(da - 1.0) > 1e-6 or abs(db - 1.0) > 1e-6:
            raise ValueError("rot_angle_deg on non-rotation; use polar path")
        R0, R1 = A, B
    else:
        R0, R1 = polar_rotation(A), polar_rotation(B)
    R = R0.T @ R1
    c = float(np.clip((np.trace(R) - 1.0) * 0.5, -1.0, 1.0))
    return math.degrees(math.acos(c))


def R_to_quat_xyzw(R):
    """Unit xyzw from a rotation matrix (Shepperd)."""
    t = float(np.trace(R))
    if t > 0:
        s = math.sqrt(t + 1.0) * 2.0
        w = 0.25 * s
        x = (R[2, 1] - R[1, 2]) / s
        y = (R[0, 2] - R[2, 0]) / s
        z = (R[1, 0] - R[0, 1]) / s
    elif R[0, 0] > R[1, 1] and R[0, 0] > R[2, 2]:
        s = math.sqrt(1.0 + R[0, 0] - R[1, 1] - R[2, 2]) * 2.0
        w = (R[2, 1] - R[1, 2]) / s
        x = 0.25 * s
        y = (R[0, 1] + R[1, 0]) / s
        z = (R[0, 2] + R[2, 0]) / s
    elif R[1, 1] > R[2, 2]:
        s = math.sqrt(1.0 + R[1, 1] - R[0, 0] - R[2, 2]) * 2.0
        w = (R[0, 2] - R[2, 0]) / s
        x = (R[0, 1] + R[1, 0]) / s
        y = 0.25 * s
        z = (R[1, 2] + R[2, 1]) / s
    else:
        s = math.sqrt(1.0 + R[2, 2] - R[0, 0] - R[1, 1]) * 2.0
        w = (R[1, 0] - R[0, 1]) / s
        x = (R[0, 2] + R[2, 0]) / s
        y = (R[1, 2] + R[2, 1]) / s
        z = 0.25 * s
    q = np.array([x, y, z, w], dtype=np.float64)
    n = float(np.linalg.norm(q))
    return q / n if n else q


def parse_flags(body, n_nodes):
    marker = body.find(b"Scene Root")
    position = marker - 2
    flags = []
    for _ in range(n_nodes):
        name, payload = a.read_string(body, position)
        flags.append({"name": name, "index": a.u16(body, payload), "flags": body[payload + 2]})
        position = payload + 71
    return flags


def clip_tracks(clip):
    return {tr["node"]: tr for tr in clip["tracks"] if tr.get("kind") == "full"}


def locals_for_frame(nodes, clip, frame, normalize):
    tracks = clip_tracks(clip)
    out = []
    for index, _node in enumerate(nodes):
        tr = tracks.get(index)
        if tr is None:
            out.append(np.eye(4, dtype=np.float64))
        else:
            out.append(local_matrix(tr["pos"][frame], tr["quat"][frame], normalize))
    return out


def worlds_for_frame(nodes, clip, frame, normalize):
    return compose_worlds(nodes, locals_for_frame(nodes, clip, frame, normalize))


def np_from_module_worlds(module_ws):
    return [np.array(m, dtype=np.float64) for m in module_ws]


def normalize_quat(q):
    q = np.array(q, dtype=np.float64)
    n = float(np.linalg.norm(q))
    return q / n if n else q


def quat_dot(a, b):
    return float(np.dot(a, b))


def make_continuous(quats):
    out = [normalize_quat(quats[0])]
    for q in quats[1:]:
        u = normalize_quat(q)
        if quat_dot(out[-1], u) < 0:
            u = -u
        out.append(u)
    return out


def slerp(q0, q1, t):
    q0 = normalize_quat(q0)
    q1 = normalize_quat(q1)
    d = quat_dot(q0, q1)
    if d < 0:
        q1 = -q1
        d = -d
    d = min(1.0, max(-1.0, d))
    if d > 0.9995:
        q = (1.0 - t) * q0 + t * q1
        return normalize_quat(q)
    theta = math.acos(d)
    s = math.sin(theta)
    return (math.sin((1.0 - t) * theta) * q0 + math.sin(t * theta) * q1) / s


def lerp(a, b, t):
    a = np.array(a, dtype=np.float64)
    b = np.array(b, dtype=np.float64)
    return (1.0 - t) * a + t * b


class ClipSampler:
    """Diagnostic sampler. Position: linear in source ms. Rotation: unit
    shortest-arc SLERP after q/-q continuity. Not claimed to be CF runtime."""

    def __init__(self, nodes, clip):
        self.nodes = nodes
        self.clip = clip
        self.times = [float(t) for t in clip["times_ms"]]
        self.tracks = clip_tracks(clip)
        self.pos = {}
        self.quat_raw = {}
        self.quat_unit_cont = {}
        for index, node in enumerate(nodes):
            tr = self.tracks[index]
            if tr.get("kind") != "full":
                raise RuntimeError("node %s is not a full track" % node["name"])
            self.pos[index] = [np.array(p, dtype=np.float64) for p in tr["pos"]]
            raw = [np.array(q, dtype=np.float64) for q in tr["quat"]]
            self.quat_raw[index] = raw
            self.quat_unit_cont[index] = make_continuous(raw)

    def _bracket(self, time_ms):
        times = self.times
        for i, t in enumerate(times):
            if abs(time_ms - t) <= 1e-9:
                return i, i, 0.0
        if time_ms < times[0]:
            return 0, 0, 0.0
        if time_ms > times[-1]:
            last = len(times) - 1
            return last, last, 0.0
        for i in range(len(times) - 1):
            if times[i] <= time_ms <= times[i + 1]:
                span = times[i + 1] - times[i]
                alpha = 0.0 if span <= 0 else (time_ms - times[i]) / span
                return i, i + 1, alpha
        raise RuntimeError("time %s not in clip" % time_ms)

    def local_at(self, time_ms):
        i0, i1, alpha = self._bracket(time_ms)
        locals_ = []
        for index in range(len(self.nodes)):
            if i0 == i1:
                pos = self.pos[index][i0]
                quat = self.quat_unit_cont[index][i0]
            else:
                pos = lerp(self.pos[index][i0], self.pos[index][i1], alpha)
                quat = slerp(self.quat_unit_cont[index][i0], self.quat_unit_cont[index][i1], alpha)
            locals_.append(local_matrix(pos, quat, False))
        return locals_

    def worlds_at(self, time_ms):
        return compose_worlds(self.nodes, self.local_at(time_ms))

    def component_linear_local_at(self, time_ms):
        """Four-component LINEAR on unit continuous quats, then normalize.
        This is the thing we must not claim equals SLERP."""
        i0, i1, alpha = self._bracket(time_ms)
        locals_ = []
        for index in range(len(self.nodes)):
            if i0 == i1:
                pos = self.pos[index][i0]
                quat = self.quat_unit_cont[index][i0]
            else:
                pos = lerp(self.pos[index][i0], self.pos[index][i1], alpha)
                quat = normalize_quat(lerp(self.quat_unit_cont[index][i0], self.quat_unit_cont[index][i1], alpha))
            locals_.append(local_matrix(pos, quat, False))
        return locals_


def parse_body(body):
    header = a.parse_header(body)
    alloc = header["allocs"]
    nodes, offset = a.parse_skeleton(body, alloc["nNodes"])
    weight_sets, offset = a.parse_weight_sets(body, offset, len(nodes), alloc["nWeightSets"])
    child_models, offset = a.parse_child_models(body, offset, alloc["nChildModels"])
    clips, _ = a.parse_anims(body, offset, nodes, alloc["nParentAnims"])
    if len(nodes) != 57 or len(clips) != 8:
        raise RuntimeError("expected 57 nodes / 8 clips, got %s / %s" % (len(nodes), len(clips)))
    flags = parse_flags(body, len(nodes))
    if any(f["flags"] != 0 for f in flags):
        raise RuntimeError("expected all flags=0")
    return header, nodes, weight_sets, child_models, clips, flags


def compare_to_cf_worlds(nodes, clips):
    max_abs = 0.0
    worst = None
    n_compared = 0
    for clip in clips:
        for frame in range(clip["n_keyframes"]):
            ours = worlds_for_frame(nodes, clip, frame, False)
            module = np_from_module_worlds(a.cf_worlds(nodes, clip, frame))
            for i, node in enumerate(nodes):
                delta = float(np.max(np.abs(ours[i] - module[i])))
                n_compared += 1
                if delta > max_abs:
                    max_abs = delta
                    worst = {"clip": clip["name"], "key": frame, "bone": node["name"], "max_abs": delta}
    return {"n_compared_matrices": n_compared, "max_abs": max_abs, "worst": worst}


def raw_unit_world_delta(nodes, clip):
    max_delta = -1.0
    worst = None
    for frame in range(clip["n_keyframes"]):
        raw = worlds_for_frame(nodes, clip, frame, False)
        unit = worlds_for_frame(nodes, clip, frame, True)
        for i, node in enumerate(nodes):
            d = float(np.linalg.norm(raw[i][:3, 3] - unit[i][:3, 3]))
            if d > max_delta:
                max_delta = d
                worst = {"distance": d, "key": frame, "time_ms": clip["times_ms"][frame], "bone": node["name"]}
    return worst


def endpoint_vs_idle(nodes, clips_by_name, name, normalize):
    idle_w = worlds_for_frame(nodes, clips_by_name["idle_0"], 0, normalize)
    clip = clips_by_name[name]
    first_w = worlds_for_frame(nodes, clip, 0, normalize)
    last_w = worlds_for_frame(nodes, clip, clip["n_keyframes"] - 1, normalize)
    rows = {}
    for bone in KEY_BONES:
        i = bone_index(nodes, bone)
        how = "unit_rotation" if normalize else "polar_extracted_rotation"
        rows[bone] = {
            "first_vs_idle_pos": float(np.linalg.norm(first_w[i][:3, 3] - idle_w[i][:3, 3])),
            "last_vs_idle_pos": float(np.linalg.norm(last_w[i][:3, 3] - idle_w[i][:3, 3])),
            "first_vs_idle_ang_deg": rot_angle_deg(idle_w[i][:3, :3], first_w[i][:3, :3], require_rotation=normalize),
            "last_vs_idle_ang_deg": rot_angle_deg(idle_w[i][:3, :3], last_w[i][:3, :3], require_rotation=normalize),
            "angle_method": how,
            "first_pos": first_w[i][:3, 3].tolist(),
            "last_pos": last_w[i][:3, 3].tolist(),
            "idle_pos": idle_w[i][:3, 3].tolist(),
        }
    return rows


def bind_vs_clip0_result(nodes, clip, binds):
    """Record bind vs this clip's frame 0. Not a decoder gate."""
    locals_ = locals_for_frame(nodes, clip, 0, False)
    worlds = compose_worlds(nodes, locals_)
    rows = []
    n_fp_pos = n_fp_ang = n_world_pos = 0
    for i, node in enumerate(nodes):
        parent = node["parent"]
        fp = binds[i] if parent < 0 else np.linalg.inv(binds[parent]) @ binds[i]
        pe_fp = float(np.linalg.norm(locals_[i][:3, 3] - fp[:3, 3]))
        ae_fp = rot_angle_deg(fp[:3, :3], locals_[i][:3, :3], require_rotation=False)
        pe_w = float(np.linalg.norm(worlds[i][:3, 3] - binds[i][:3, 3]))
        ae_w = rot_angle_deg(binds[i][:3, :3], worlds[i][:3, :3], require_rotation=False)
        if pe_fp < 1e-4:
            n_fp_pos += 1
        if ae_fp < 0.1:
            n_fp_ang += 1
        if pe_w < 1e-4:
            n_world_pos += 1
        rows.append({
            "index": i,
            "name": node["name"],
            "parent": parent,
            "local_vs_fromparent_pos": pe_fp,
            "local_vs_fromparent_ang_deg_polar": ae_fp,
            "world_vs_bind_pos": pe_w,
            "world_vs_bind_ang_deg_polar": ae_w,
        })
    gun_ids = []

    def walk(i):
        gun_ids.append(i)
        for c in nodes[i]["children"]:
            walk(c)

    walk(bone_index(nodes, "FvARM-bone Prop1"))
    return {
        "clip": clip["name"],
        "n_fromparent_pos_lt_1e4": n_fp_pos,
        "n_fromparent_ang_lt_0p1deg_polar": n_fp_ang,
        "n_world_pos_lt_1e4": n_world_pos,
        "gun_subtree_world_pos_match": all(rows[i]["world_vs_bind_pos"] < 1e-4 for i in gun_ids),
        "gun_subtree_count": len(gun_ids),
        "note": (
            "Bind is a modelling rest. Matching 53/57 parent-relative translations "
            "at reload0 is evidence the parent-local tracks are the same format as "
            "bind, not authorization to add pelvis/root offsets or retarget onto bind."
        ),
        "per_bone": rows,
    }


def quat_key_stats(clips):
    all_norms = []
    rtr_raw = []
    det_raw = []
    rtr_unit = []
    det_unit = []
    lhs96 = None
    for clip in clips:
        for tr in clip["tracks"]:
            if tr.get("kind") != "full":
                continue
            for i, q in enumerate(tr["quat"]):
                qn = np.array(q, dtype=np.float64)
                n = float(np.linalg.norm(qn))
                all_norms.append(n)
                err, det = orthonormality(quat_to_R(qn, False))
                rtr_raw.append(err)
                det_raw.append(det)
                err_u, det_u = orthonormality(quat_to_R(qn, True))
                rtr_unit.append(err_u)
                det_unit.append(det_u)
                if clip["name"] == "reload" and tr["name"] == "FvARM-bone L Hand" and i == 96:
                    lhs96 = {
                        "clip": "reload",
                        "bone": tr["name"],
                        "key": 96,
                        "time_ms": clip["times_ms"][96],
                        "frame_100fps": clip["times_ms"][96] / 10.0,
                        "raw_xyzw": qn.tolist(),
                        "norm": n,
                        "normalized_xyzw": (qn / n).tolist(),
                        "R_raw_RTR_err": err,
                        "R_raw_det": det,
                        "R_unit_RTR_err": err_u,
                        "R_unit_det": det_u,
                        "angle_on_raw_forbidden": True,
                    }
    return {
        "all_norm_min": min(all_norms),
        "all_norm_max": max(all_norms),
        "xyzw_raw_RTR_max_abs": max(rtr_raw),
        "xyzw_raw_det_minmax": [min(det_raw), max(det_raw)],
        "xyzw_unit_RTR_max_abs": max(rtr_unit),
        "xyzw_unit_det_minmax": [min(det_unit), max(det_unit)],
        "reload_L_Hand_key96": lhs96,
        "raw_tracks_unmodified": True,
    }


def linear_vs_slerp_midpoints(nodes, sampler):
    times = sampler.times
    max_pos = 0.0
    max_ang = 0.0
    worst_pos = None
    worst_ang = None
    n = 0
    for k in range(len(times) - 1):
        if times[k + 1] <= times[k]:
            continue
        mid = 0.5 * (times[k] + times[k + 1])
        ws = compose_worlds(nodes, sampler.local_at(mid))
        wl = compose_worlds(nodes, sampler.component_linear_local_at(mid))
        for i, node in enumerate(nodes):
            d = float(np.linalg.norm(ws[i][:3, 3] - wl[i][:3, 3]))
            ang = rot_angle_deg(ws[i][:3, :3], wl[i][:3, :3], require_rotation=True)
            n += 1
            if d > max_pos:
                max_pos = d
                worst_pos = {"time_ms": mid, "key_lo": k, "key_hi": k + 1, "bone": node["name"], "pos_err": d}
            if ang > max_ang:
                max_ang = ang
                worst_ang = {"time_ms": mid, "key_lo": k, "key_hi": k + 1, "bone": node["name"], "ang_deg": ang}
    return {
        "n_midpoint_bones": n,
        "max_pos_err": max_pos,
        "max_ang_deg": max_ang,
        "worst_pos": worst_pos,
        "worst_ang": worst_ang,
        "note": "Component-LINEAR of unit quats is not SLERP. Visible reference uses SLERP.",
    }


def diagnostic_frames(duration_ms):
    n = int(math.floor(duration_ms * DIAGNOSTIC_FPS / 1000.0 + 1e-9))
    frames = list(range(n + 1))
    return frames


def sample_clip_payload(nodes, sampler):
    duration = sampler.clip["duration_ms"]
    frames = diagnostic_frames(duration)
    times_ms = sampler.times
    key_by_ms = {int(t): i for i, t in enumerate(times_ms)}
    samples = []
    all_pos = []
    for frame in frames:
        time_ms = frame * 1000.0 / DIAGNOSTIC_FPS
        if time_ms > duration:
            time_ms = float(duration)
        worlds = sampler.worlds_at(time_ms)
        pos = []
        quat = []
        for i in range(len(nodes)):
            p = worlds[i][:3, 3]
            q = R_to_quat_xyzw(worlds[i][:3, :3])
            pos.append([float(p[0]), float(p[1]), float(p[2])])
            quat.append([float(q[0]), float(q[1]), float(q[2]), float(q[3])])
            all_pos.append(p)
        nearest_key = None
        rounded = int(round(time_ms))
        if rounded in key_by_ms and abs(time_ms - rounded) < 1e-6:
            nearest_key = key_by_ms[rounded]
        else:
            for i, t in enumerate(times_ms):
                if abs(t - time_ms) < 1e-6:
                    nearest_key = i
                    break
        samples.append({
            "frame_100": frame,
            "time_ms": time_ms,
            "source_key": nearest_key,
            "pos": pos,
            "quat_xyzw_world": quat,
        })
    arr = np.stack(all_pos)
    bbox = {"min": arr.min(axis=0).tolist(), "max": arr.max(axis=0).tolist()}
    return samples, bbox


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if not V1_AUDIT.exists():
        raise RuntimeError("keep v1 source_audit.json as failed evidence; missing %s" % V1_AUDIT)

    body = BODY_PATH.read_bytes()
    if len(body) != EXPECTED_BYTES:
        raise RuntimeError("body size %s != %s" % (len(body), EXPECTED_BYTES))
    sha = hashlib.sha256(body).hexdigest()
    if sha != EXPECTED_SHA:
        raise RuntimeError("body sha mismatch")

    offline = json.loads(OFFLINE_AUDIT.read_text(encoding="utf-8"))
    planner = json.loads(PLANNER_NUMERIC.read_text(encoding="utf-8"))
    packed = offline["source"]["packed"]
    header, nodes, weight_sets, child_models, clips, flags = parse_body(body)
    clips_by_name = {c["name"]: c for c in clips}
    binds = [reshape16(n["matrix"]) for n in nodes]
    bind_last_row_err = float(max(np.max(np.abs(m[3] - [0, 0, 0, 1])) for m in binds))

    module_cross = compare_to_cf_worlds(nodes, clips)
    if module_cross["max_abs"] >= 1e-10:
        raise RuntimeError("v3 worlds diverge from cf_worlds: %s" % module_cross)

    qstats = quat_key_stats(clips)
    lhs = qstats["reload_L_Hand_key96"]
    if abs(lhs["R_raw_det"] - 0.9276306731) > 1e-9 or abs(lhs["R_raw_RTR_err"] - 0.0723688076) > 1e-9:
        raise RuntimeError("reload L Hand key96 raw matrix stats drifted: %s" % lhs)

    raw_unit = {}
    planner_match = {}
    for name in FOCUS_CLIPS:
        got = raw_unit_world_delta(nodes, clips_by_name[name])
        raw_unit[name] = got
        exp = PLANNER_DELTA[name]
        ok = (
            got["bone"] == exp["bone"]
            and got["key"] == exp["key"]
            and abs(got["distance"] - exp["distance"]) < 1e-12
        )
        planner_match[name] = {"ok": ok, "got": got, "planner": exp}
        if not ok:
            raise RuntimeError("raw-vs-unit world delta mismatch vs planner for %s: %s" % (name, planner_match[name]))

    unit_end = {}
    polar_end = {}
    for name in ("select", "reload"):
        unit_end[name] = endpoint_vs_idle(nodes, clips_by_name, name, True)
        polar_end[name] = endpoint_vs_idle(nodes, clips_by_name, name, False)

    select_gun_first = unit_end["select"]["FvARM-bone Prop1"]["first_vs_idle_pos"]
    select_gun_last = unit_end["select"]["FvARM-bone Prop1"]["last_vs_idle_pos"]
    if abs(select_gun_first - 4.981884111601881) > 1e-12:
        raise RuntimeError("select gun first-vs-idle drifted: %s" % select_gun_first)
    if select_gun_last >= 1e-4:
        raise RuntimeError("select last vs idle pos not closed: %s" % select_gun_last)

    bind_reload0 = bind_vs_clip0_result(nodes, clips_by_name["reload"], binds)
    bind_idle0 = bind_vs_clip0_result(nodes, clips_by_name["idle_0"], binds)
    bind_select0 = bind_vs_clip0_result(nodes, clips_by_name["select"], binds)

    samplers = {name: ClipSampler(nodes, clips_by_name[name]) for name in [c["name"] for c in clips]}
    slerp_vs_linear = {name: linear_vs_slerp_midpoints(nodes, samplers[name]) for name in FOCUS_CLIPS}

    # Sampler at exact keys must match unit-normalized composition.
    sampler_vs_unit_key = {}
    for name in FOCUS_CLIPS:
        sampler = samplers[name]
        clip = clips_by_name[name]
        max_pos = 0.0
        max_ang = 0.0
        for k, t in enumerate(clip["times_ms"]):
            ws = sampler.worlds_at(float(t))
            wu = worlds_for_frame(nodes, clip, k, True)
            for i in range(len(nodes)):
                max_pos = max(max_pos, float(np.linalg.norm(ws[i][:3, 3] - wu[i][:3, 3])))
                max_ang = max(max_ang, rot_angle_deg(ws[i][:3, :3], wu[i][:3, :3], require_rotation=True))
        sampler_vs_unit_key[name] = {"max_pos_err": max_pos, "max_ang_deg": max_ang}
        if max_pos > 1e-8 or max_ang > 1e-4:
            raise RuntimeError("sampler at keys != unit composition for %s: %s" % (name, sampler_vs_unit_key[name]))

    synthetic = {
        "identity_xyzw_R_vs_I_maxabs": float(np.max(np.abs(quat_to_R([0, 0, 0, 1], False) - np.eye(3)))),
        "plus90Z_maps_X_to": (quat_to_R([0, 0, math.sin(math.pi / 4), math.cos(math.pi / 4)], False) @ np.array([1.0, 0.0, 0.0])).tolist(),
        "q_and_negq_same_R": True,
        "polar_of_unit_is_itself_reload_key0_maxabs": None,
    }
    w0 = worlds_for_frame(nodes, clips_by_name["reload"], 0, True)
    synthetic["polar_of_unit_is_itself_reload_key0_maxabs"] = float(
        max(np.max(np.abs(polar_rotation(w[:3, :3]) - w[:3, :3])) for w in w0)
    )

    clip_summaries = []
    timeline_clips = []
    for clip in clips:
        times = list(clip["times_ms"])
        summary = {
            "name": clip["name"],
            "n_keyframes": clip["n_keyframes"],
            "duration_ms": clip["duration_ms"],
            "compression": clip["compression"],
            "compression_name": clip.get("compression_name"),
            "interpolation_ms": clip.get("interpolation_ms"),
            "times_ms": times,
            "events": clip.get("events") or [],
            "diagnostic_100fps": {
                "formula": "frame = time_ms * 100 / 1000",
                "duration_frames": clip["duration_ms"] / 10.0,
                "integer_frames": diagnostic_frames(clip["duration_ms"]),
            },
            "interval_ms_counts": {str(k): v for k, v in Counter(y - x for x, y in zip(times, times[1:])).items()},
            "true_duration_s": clip["duration_ms"] / 1000.0,
            "wrong_blender_30fps_index_duration_s": (clip["n_keyframes"] - 1) / 30.0 if clip["n_keyframes"] else 0.0,
        }
        clip_summaries.append(summary)
        if clip["name"] in FOCUS_CLIPS:
            timeline_clips.append(summary)

    payload_clips = {}
    bbox_all = None
    for clip in clips:
        samples, bbox = sample_clip_payload(nodes, samplers[clip["name"]])
        payload_clips[clip["name"]] = {
            "duration_ms": clip["duration_ms"],
            "times_ms": list(clip["times_ms"]),
            "events": clip.get("events") or [],
            "n_samples": len(samples),
            "samples": samples,
            "bbox": bbox,
        }
        mins = np.array(bbox["min"])
        maxs = np.array(bbox["max"])
        if bbox_all is None:
            bbox_all = {"min": mins, "max": maxs}
        else:
            bbox_all["min"] = np.minimum(bbox_all["min"], mins)
            bbox_all["max"] = np.maximum(bbox_all["max"], maxs)

    bind_worlds = []
    bind_pos = []
    bind_quat = []
    for m in binds:
        R = polar_rotation(m[:3, :3])
        q = R_to_quat_xyzw(R)
        bind_worlds.append(m.tolist())
        bind_pos.append(m[:3, 3].tolist())
        bind_quat.append(q.tolist())

    payload = {
        "reference_kind": "SKELETON_ONLY_REFERENCE",
        "sampler_label": (
            "DIAGNOSTIC: linear position in source ms; unit quaternion shortest-arc "
            "SLERP after q/-q continuity. Original file quats retained in v3 audit. "
            "Not a CF runtime interpolator proof."
        ),
        "convention": CONVENTION,
        "bbox_all_clips": {"min": bbox_all["min"].tolist(), "max": bbox_all["max"].tolist()},
        "nodes": [
            {
                "index": n["index"],
                "name": n["name"],
                "parent": n["parent"],
                "children": n["children"],
                "bind_world": bind_worlds[n["index"]],
                "bind_pos": bind_pos[n["index"]],
                "bind_quat_xyzw_polar": bind_quat[n["index"]],
            }
            for n in nodes
        ],
        "clips": payload_clips,
    }

    v1_rejected = {
        "path": str(V1_AUDIT).replace("\\", "/"),
        "kept_as": "FAILED_METHOD_EVIDENCE",
        "rejected_next_verification_step": (
            "B_local @ inverse(A_reload0) @ A(t) is an identity at t=0 and retargets "
            "the clip onto another pose; it is not a format check."
        ),
        "rejected_auto_winner": True,
        "rejected_bind_equals_clip0_gate": True,
        "rejected_pelvis_compensation": True,
        "rejected_raw_trace_angles": True,
        "rejected_max_world_travel_as_raw_vs_unit": True,
    }

    open_items = [
        "interpolation_ms is stored (0 on these clips) but unread as a CF runtime rule.",
        "100 FPS is a diagnostic grid, not CF native sampling.",
        "Visible skeleton has no LTB weights / inverse bind; SKELETON_ONLY_REFERENCE.",
        "Public SDK Slerp matches this diagnostic sampler's intent, not a CF binary proof.",
    ]
    # If LINEAR vs SLERP is large, say so explicitly.
    lin_max = max(v["max_ang_deg"] for v in slerp_vs_linear.values())
    if lin_max > 0.05:
        open_items.append(
            "Component-LINEAR vs SLERP max angle is %.4f deg; do not key Blender quaternion channels as LINEAR and call it SLERP."
            % lin_max
        )

    source_audit = {
        "task_id": "P7-S04-R1-A",
        "stage": "G1_SOURCE_AUDIT_V3",
        "status": "G1_NUMERIC_V3_READY_FOR_VISIBLE_REFERENCE",
        "reference_kind": "SKELETON_ONLY_REFERENCE",
        "has_weights_in_geometry_json": False,
        "skinned_mesh_claimed": False,
        "compiled": False,
        "deployed": False,
        "user_accepted": False,
        "v1_rejected_method": v1_rejected,
        "convention": CONVENTION,
        "provenance": {
            "body_path": str(BODY_PATH),
            "body_bytes": len(body),
            "body_sha256": sha,
            "packed_sha256": packed.get("sha256"),
            "directory_md5": packed.get("directory_md5"),
            "packed_lzma_equals_body": offline["source"].get("packed_lzma_equals_body"),
            "planner_numeric": str(PLANNER_NUMERIC).replace("\\", "/"),
        },
        "n_nodes": 57,
        "n_clips": 8,
        "clip_names": [c["name"] for c in clips],
        "n_weight_sets": len(weight_sets),
        "weight_sets": [{"name": w["name"], "count": w["count"], "nonzero": w["nonzero"]} for w in weight_sets],
        "child_models": child_models,
        "node_flags": {
            "unique": sorted({f["flags"] for f in flags}),
            "nonzero": [f for f in flags if f["flags"]],
            "all_zero": True,
            "rotation_only_enabled": False,
        },
        "header": header,
        "bind_affine_bottom_row_max_error": bind_last_row_err,
        "module_cf_worlds_crosscheck": module_cross,
        "quaternion_findings": {
            **qstats,
            "synthetic": synthetic,
            "angle_policy": "trace formula only on unit/polar rotations; raw reports RTR/det only",
        },
        "raw_vs_normalized_world_position": {
            "definition": "same clip/frame/bone, raw quat matrix vs unit quat matrix, world translation delta",
            "per_focus_clip": raw_unit,
            "matches_planner_review_g1_numeric": planner_match,
        },
        "source_end_vs_idle": {
            "unit_normalized": unit_end,
            "polar_extracted_on_raw": polar_end,
            "select_keeps_entry_motion": True,
            "select_first_gun_vs_idle_cf_units": select_gun_first,
            "end_closure_pos_lt_1e4": {
                "select_gun": select_gun_last < 1e-4,
                "select_rhand": unit_end["select"]["FvARM-bone R Hand"]["last_vs_idle_pos"] < 1e-4,
                "select_lhand": unit_end["select"]["FvARM-bone L Hand"]["last_vs_idle_pos"] < 1e-4,
                "reload_gun": unit_end["reload"]["FvARM-bone Prop1"]["last_vs_idle_pos"] < 1e-4,
                "reload_rhand": unit_end["reload"]["FvARM-bone R Hand"]["last_vs_idle_pos"] < 1e-4,
                "reload_lhand": unit_end["reload"]["FvARM-bone L Hand"]["last_vs_idle_pos"] < 1e-4,
            },
        },
        "bind_vs_clip0_recorded_not_gated": {
            "reload": {k: v for k, v in bind_reload0.items() if k != "per_bone"},
            "idle_0": {k: v for k, v in bind_idle0.items() if k != "per_bone"},
            "select": {k: v for k, v in bind_select0.items() if k != "per_bone"},
        },
        "diagnostic_sampler": {
            "position": "linear in source milliseconds",
            "rotation": "unit quaternion shortest-arc SLERP after q/-q continuity",
            "not_equivalent_to": "four-component LINEAR F-curves",
            "at_source_keys_vs_unit_composition": sampler_vs_unit_key,
            "component_linear_vs_slerp_midpoints": slerp_vs_linear,
        },
        "clips": clip_summaries,
        "enough_for_skeleton_visible_reference": True,
        "open_items": open_items,
        "next_step": (
            "Build CF_SOURCE_REFERENCE with prefixed objects: R1A_CF_ANIM from sampler "
            "tracks, R1A_CF_BIND from node.matrix, not overlaid by a compensating transform. "
            "Save to source/source_reference.blend after asserting working path and frozen hashes."
        ),
    }

    timeline = {
        "task_id": "P7-S04-R1-A",
        "diagnostic_fps": DIAGNOSTIC_FPS,
        "mapping": "frame = time_ms * 100 / 1000",
        "note": "100 FPS is a diagnostic choice, not CF native sampling.",
        "interpolation": {
            "position": "linear in source time (applied in v3 sampler)",
            "rotation": "unit quaternion shortest-arc slerp with q/-q continuity (applied in v3 sampler)",
            "engine_runtime": "OPEN; SDK TransformMaker uses Slerp+lerp for uncompressed keys, not proven for this CF build",
            "blender_fcurve_linear_not_equal_slerp": True,
        },
        "clips": timeline_clips,
        "markers": [],
    }
    for clip in clips:
        if clip["name"] not in FOCUS_CLIPS:
            continue
        for ev in clip.get("events") or []:
            timeline["markers"].append({
                "clip": clip["name"],
                "source_key_index": ev.get("frame"),
                "time_ms": ev.get("time_ms"),
                "frame_100fps": (ev.get("time_ms") or 0) / 10.0,
                "label": ev.get("label"),
            })

    (OUT_DIR / "source_audit_v3.json").write_text(json.dumps(jsonable(source_audit), indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "timeline_v3.json").write_text(json.dumps(jsonable(timeline), indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "reference_payload.json").write_text(json.dumps(jsonable(payload), indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "bind_vs_reload0_per_bone_v3.json").write_text(
        json.dumps(jsonable(bind_reload0["per_bone"]), indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "status": source_audit["status"],
        "body_sha": sha,
        "cf_worlds_max_abs": module_cross["max_abs"],
        "flags_zero": True,
        "planner_raw_unit_match": {k: v["ok"] for k, v in planner_match.items()},
        "reload_L_Hand_key96_det": lhs["R_raw_det"],
        "select_gun_first_vs_idle": select_gun_first,
        "select_gun_last_vs_idle": select_gun_last,
        "reload0_fromparent_pos_match": bind_reload0["n_fromparent_pos_lt_1e4"],
        "linear_vs_slerp_max_ang": {k: v["max_ang_deg"] for k, v in slerp_vs_linear.items()},
        "wrote": [
            str(OUT_DIR / "source_audit_v3.json"),
            str(OUT_DIR / "timeline_v3.json"),
            str(OUT_DIR / "reference_payload.json"),
        ],
        "did_not_overwrite": str(V1_AUDIT),
    }, indent=2))


if __name__ == "__main__":
    main()
