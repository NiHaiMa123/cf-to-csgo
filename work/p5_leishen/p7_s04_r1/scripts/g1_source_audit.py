"""G1 offline numeric/convention audit. Parse-only; no Blender, no main/retarget."""
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
OUT_DIR = ROOT / "work/p5_leishen/p7_s04_r1/source"
EXPECTED_BYTES = 604808
EXPECTED_SHA = "511dec8d2401a1886ddecd14b4f18e17ac0afbefd943f6dc11a3fd2f82ef6b49"
KEY_BONES = ["FvARM-bone Prop1", "FvARM-bone R Hand", "FvARM-bone L Hand"]
FOCUS_CLIPS = ("select", "reload", "idle_0")
ANIM_CONV = {
    "layout": "row_major_m_ij",
    "quat": "xyzw",
    "translation": "col3",
    "multiply": "parent_at_local",
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


def reshape16(flat, layout):
    m = np.array(flat, dtype=np.float64).reshape(4, 4)
    return m if layout == "row_major_m_ij" else m.T


def translation_of(m, how):
    return m[:3, 3].copy() if how == "col3" else m[3, :3].copy()


def quat_to_R(q, convention):
    q = np.array(q, dtype=np.float64)
    if convention == "xyzw":
        x, y, z, w = q
    elif convention == "wxyz":
        w, x, y, z = q
    elif convention == "xyzw_conj":
        x, y, z, w = q
        x, y, z = -x, -y, -z
    elif convention == "wxyz_conj":
        w, x, y, z = q
        x, y, z = -x, -y, -z
    else:
        raise ValueError(convention)
    return np.array(
        [
            [1.0 - 2.0 * (y * y + z * z), 2.0 * (x * y - w * z), 2.0 * (x * z + w * y)],
            [2.0 * (x * y + w * z), 1.0 - 2.0 * (x * x + z * z), 2.0 * (y * z - w * x)],
            [2.0 * (x * z - w * y), 2.0 * (y * z + w * x), 1.0 - 2.0 * (x * x + y * y)],
        ],
        dtype=np.float64,
    )


def local_matrix(pos, quat, convention, trans_how, normalize):
    q = np.array(quat, dtype=np.float64)
    n = float(np.linalg.norm(q))
    if normalize and n > 0:
        q = q / n
    M = np.eye(4, dtype=np.float64)
    M[:3, :3] = quat_to_R(q, convention)
    p = np.array(pos, dtype=np.float64)
    if trans_how == "col3":
        M[:3, 3] = p
    else:
        M[3, :3] = p
    return M


def compose_worlds(nodes, locals_, mul):
    worlds = [None] * len(nodes)
    for index in a.dfs_nodes(nodes):
        parent = nodes[index]["parent"]
        loc = locals_[index]
        if parent < 0:
            worlds[index] = loc
        elif mul == "parent_at_local":
            worlds[index] = worlds[parent] @ loc
        else:
            worlds[index] = loc @ worlds[parent]
    return worlds


def rot_angle_deg(A, B):
    R = A.T @ B
    c = float(np.clip((np.trace(R) - 1.0) * 0.5, -1.0, 1.0))
    return math.degrees(math.acos(c))


def orthonormality(R):
    err = float(np.max(np.abs(R.T @ R - np.eye(3))))
    det = float(np.linalg.det(R))
    return err, det


def clip_tracks(clip):
    return {tr["node"]: tr for tr in clip["tracks"] if tr.get("kind") == "full"}


def locals_for_frame(nodes, clip, frame, convention, trans_how, normalize):
    tracks = clip_tracks(clip)
    out = []
    for index, node in enumerate(nodes):
        tr = tracks.get(index)
        if tr is None:
            out.append(np.eye(4, dtype=np.float64))
        else:
            out.append(local_matrix(tr["pos"][frame], tr["quat"][frame], convention, trans_how, normalize))
    return out


def worlds_for_clip(nodes, clip, convention, trans_how, mul, normalize):
    return [
        compose_worlds(nodes, locals_for_frame(nodes, clip, frame, convention, trans_how, normalize), mul)
        for frame in range(clip["n_keyframes"])
    ]


def bone_index(nodes, name):
    for node in nodes:
        if node["name"] == name:
            return node["index"]
    raise KeyError(name)


def subtree(nodes, root_index):
    ids = []

    def walk(i):
        ids.append(i)
        for child in nodes[i]["children"]:
            walk(child)

    walk(root_index)
    return ids


def parse_flags(body, n_nodes):
    marker = body.find(b"Scene Root")
    position = marker - 2
    flags = []
    for _ in range(n_nodes):
        name, payload = a.read_string(body, position)
        flags.append({"name": name, "index": a.u16(body, payload), "flags": body[payload + 2]})
        position = payload + 71
    return flags


def match_stats(errs_pos, errs_ang, pos_tol=1e-4, ang_tol=0.1):
    n = len(errs_pos)
    n_pos = int(sum(p < pos_tol for p in errs_pos))
    n_ang = int(sum(x < ang_tol for x in errs_ang))
    n_both = int(sum(p < pos_tol and x < ang_tol for p, x in zip(errs_pos, errs_ang)))
    return {
        "n_bones": n,
        "n_pos_lt_1e4": n_pos,
        "n_ang_lt_0p1deg": n_ang,
        "n_both": n_both,
        "max_pos_err": float(max(errs_pos) if errs_pos else 0.0),
        "max_ang_deg": float(max(errs_ang) if errs_ang else 0.0),
        "all_57_match": n_both == n and n == 57,
    }


def compare_world_to_bind(nodes, worlds, binds, trans_how):
    pos, ang, rows = [], [], []
    for i, node in enumerate(nodes):
        pe = float(np.linalg.norm(translation_of(worlds[i], trans_how) - translation_of(binds[i], trans_how)))
        ae = rot_angle_deg(binds[i][:3, :3], worlds[i][:3, :3])
        pos.append(pe)
        ang.append(ae)
        rows.append({"index": i, "name": node["name"], "pos_err": pe, "ang_deg": ae})
    return match_stats(pos, ang), rows


def first_clip_hypothesis(nodes, clip, binds, layout, convention, trans_how, mul, compare):
    locals_ = locals_for_frame(nodes, clip, 0, convention, trans_how, False)
    if compare == "world":
        mats = compose_worlds(nodes, locals_, mul)
        stats, _ = compare_world_to_bind(nodes, mats, binds, trans_how)
    else:
        pos, ang = [], []
        for i, node in enumerate(nodes):
            parent = node["parent"]
            fp = binds[i] if parent < 0 else np.linalg.inv(binds[parent]) @ binds[i]
            pe = float(np.linalg.norm(translation_of(locals_[i], trans_how) - translation_of(fp, trans_how)))
            ae = rot_angle_deg(fp[:3, :3], locals_[i][:3, :3])
            pos.append(pe)
            ang.append(ae)
        stats = match_stats(pos, ang)
    return {
        "layout": layout,
        "quat": convention,
        "translation": trans_how,
        "multiply": mul,
        "compare_bind_to": compare,
        **stats,
        "score": (57 - stats["n_both"]) + stats["max_pos_err"] + stats["max_ang_deg"] / 1000.0,
    }


def endpoint_vs_idle(nodes, clips_by_name, name, convention, trans_how, mul, normalize):
    idle = clips_by_name["idle_0"]
    clip = clips_by_name[name]
    idle_w = worlds_for_clip(nodes, idle, convention, trans_how, mul, normalize)[0]
    first_w = worlds_for_clip(nodes, clip, convention, trans_how, mul, normalize)[0]
    last_w = worlds_for_clip(nodes, clip, convention, trans_how, mul, normalize)[-1]
    rows = {}
    for bone in KEY_BONES:
        i = bone_index(nodes, bone)
        rows[bone] = {
            "first_vs_idle_pos": float(np.linalg.norm(translation_of(first_w[i], trans_how) - translation_of(idle_w[i], trans_how))),
            "last_vs_idle_pos": float(np.linalg.norm(translation_of(last_w[i], trans_how) - translation_of(idle_w[i], trans_how))),
            "first_vs_idle_ang_deg": rot_angle_deg(idle_w[i][:3, :3], first_w[i][:3, :3]),
            "last_vs_idle_ang_deg": rot_angle_deg(idle_w[i][:3, :3], last_w[i][:3, :3]),
            "first_pos": translation_of(first_w[i], trans_how).tolist(),
            "last_pos": translation_of(last_w[i], trans_how).tolist(),
            "idle_pos": translation_of(idle_w[i], trans_how).tolist(),
        }
    return rows


def max_world_travel(nodes, clip, convention, trans_how, mul, normalize):
    ws = worlds_for_clip(nodes, clip, convention, trans_how, mul, normalize)
    out = {}
    for bone in KEY_BONES:
        i = bone_index(nodes, bone)
        pts = np.stack([translation_of(w[i], trans_how) for w in ws])
        out[bone] = {
            "max_from_first": float(np.max(np.linalg.norm(pts - pts[0], axis=1))),
            "max_adjacent": float(np.max(np.linalg.norm(np.diff(pts, axis=0), axis=1))) if len(pts) > 1 else 0.0,
        }
    all_max = 0.0
    for i in range(len(nodes)):
        pts = np.stack([translation_of(w[i], trans_how) for w in ws])
        all_max = max(all_max, float(np.max(np.linalg.norm(pts - pts[0], axis=1))))
    out["_all_bones_max_from_first"] = all_max
    return out


def quat_stats(clips):
    per_clip = []
    all_norms, rtr_raw, det_raw, rtr_unit, det_unit = [], [], [], [], []
    lhs96 = None
    for clip in clips:
        norms = []
        for tr in clip["tracks"]:
            if tr.get("kind") != "full":
                continue
            for i, q in enumerate(tr["quat"]):
                qn = np.array(q, dtype=np.float64)
                n = float(np.linalg.norm(qn))
                norms.append(n)
                all_norms.append(n)
                err, det = orthonormality(quat_to_R(qn, "xyzw"))
                rtr_raw.append(err)
                det_raw.append(det)
                q_u = qn / n if n else qn
                err_u, det_u = orthonormality(quat_to_R(q_u, "xyzw"))
                rtr_unit.append(err_u)
                det_unit.append(det_u)
                if clip["name"] == "reload" and tr["name"] == "FvARM-bone L Hand" and i == 96:
                    lhs96 = {
                        "clip": "reload",
                        "bone": tr["name"],
                        "key": 96,
                        "time_ms": clip["times_ms"][96],
                        "frame_100fps": clip["times_ms"][96] / 10.0,
                        "raw_xyzw": [float(x) for x in qn],
                        "norm": n,
                        "normalized_xyzw": [float(x) for x in q_u],
                        "R_raw_RTR_err": err,
                        "R_raw_det": det,
                        "R_unit_RTR_err": err_u,
                        "R_unit_det": det_u,
                    }
        per_clip.append({
            "name": clip["name"],
            "n_quats": len(norms),
            "norm_min": min(norms) if norms else None,
            "norm_max": max(norms) if norms else None,
        })
    return {
        "per_clip": per_clip,
        "all_norm_min": min(all_norms),
        "all_norm_max": max(all_norms),
        "xyzw_raw_RTR_max_abs": max(rtr_raw),
        "xyzw_raw_det_minmax": [min(det_raw), max(det_raw)],
        "xyzw_unit_RTR_max_abs": max(rtr_unit),
        "xyzw_unit_det_minmax": [min(det_unit), max(det_unit)],
        "reload_L_Hand_key96": lhs96,
    }


def synthetic_quat_tests():
    ident = np.array([0.0, 0.0, 0.0, 1.0])
    q90 = np.array([0.0, 0.0, math.sin(math.pi / 4.0), math.cos(math.pi / 4.0)])
    R_id = quat_to_R(ident, "xyzw")
    R90 = quat_to_R(q90, "xyzw")
    expected90 = np.array([[0.0, -1.0, 0.0], [1.0, 0.0, 0.0], [0.0, 0.0, 1.0]])
    x_axis = np.array([1.0, 0.0, 0.0])
    return {
        "identity_xyzw_R_vs_I_maxabs": float(np.max(np.abs(R_id - np.eye(3)))),
        "plus90Z_xyzw_R_vs_expected_maxabs": float(np.max(np.abs(R90 - expected90))),
        "plus90Z_maps_X_to": (R90 @ x_axis).tolist(),
        "q_and_negq_same_R_maxabs": float(np.max(np.abs(R90 - quat_to_R(-q90, "xyzw")))),
        "note": "Right-hand column-vector +90deg Z sends X to Y. Matches existing quat_xyzw_matrix.",
    }


def bind_layout_check(nodes):
    row_major = [reshape16(n["matrix"], "row_major_m_ij") for n in nodes]
    last_rows = [m[3].tolist() for m in row_major]
    last_cols = [m[:, 3].tolist() for m in row_major]
    homog_row = all(abs(r[0]) < 1e-8 and abs(r[1]) < 1e-8 and abs(r[2]) < 1e-8 and abs(r[3] - 1) < 1e-8 for r in last_rows)
    dets = [float(np.linalg.det(m[:3, :3])) for m in row_major]
    return {
        "n": len(nodes),
        "last_row_is_0001_for_all": homog_row,
        "translation_in_col3_not_row3": homog_row,
        "det3_minmax": [min(dets), max(dets)],
        "scene_root_row_major": row_major[0].tolist(),
        "scene_root_is_180Y_diag": row_major[0][:3, :3].tolist(),
        "sample_last_col_FvARM": last_cols[1],
        "sample_last_row_FvARM": last_rows[1],
    }


def partition_reload0(nodes, clip, binds):
    tracks = clip_tracks(clip)
    locals_ = locals_for_frame(nodes, clip, 0, "xyzw", "col3", False)
    worlds = compose_worlds(nodes, locals_, "parent_at_local")
    rows = []
    for i, node in enumerate(nodes):
        parent = node["parent"]
        fp = binds[i] if parent < 0 else np.linalg.inv(binds[parent]) @ binds[i]
        anim_pos = np.array(tracks[i]["pos"][0], dtype=np.float64)
        bind_world_pos = binds[i][:3, 3]
        fp_pos = fp[:3, 3]
        world_pos = worlds[i][:3, 3]
        row = {
            "index": i,
            "name": node["name"],
            "parent": parent,
            "anim_local_pos": anim_pos.tolist(),
            "world_vs_bind_pos": float(np.linalg.norm(world_pos - bind_world_pos)),
            "world_vs_bind_ang_deg": rot_angle_deg(binds[i][:3, :3], worlds[i][:3, :3]),
            "local_vs_fromparent_pos": float(np.linalg.norm(anim_pos - fp_pos)),
            "local_vs_fromparent_ang_deg": rot_angle_deg(fp[:3, :3], locals_[i][:3, :3]),
            "anim_pos_is_zero": float(np.linalg.norm(anim_pos)) < 1e-6,
        }
        rows.append(row)
    gun_ids = set(subtree(nodes, bone_index(nodes, "FvARM-bone Prop1")))
    world_match = [r["name"] for r in rows if r["world_vs_bind_pos"] < 1e-4]
    fp_rot_match = [r["name"] for r in rows if r["local_vs_fromparent_ang_deg"] < 0.1]
    fp_pos_match = [r["name"] for r in rows if r["local_vs_fromparent_pos"] < 1e-4]
    return {
        "world_vs_bind_pos_match": world_match,
        "fromparent_pos_match": fp_pos_match,
        "fromparent_rot_match": fp_rot_match,
        "gun_subtree_all_world_match": all(rows[i]["world_vs_bind_pos"] < 1e-4 for i in gun_ids),
        "gun_subtree_count": len(gun_ids),
        "pelvis": rows[bone_index(nodes, "FvARM-bone Pelvis")],
        "scene_root": rows[0],
        "FvARM-bone": rows[1],
        "per_bone": rows,
    }


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    body = BODY_PATH.read_bytes()
    if len(body) != EXPECTED_BYTES:
        raise RuntimeError("body size %s != %s" % (len(body), EXPECTED_BYTES))
    sha = hashlib.sha256(body).hexdigest()
    if sha != EXPECTED_SHA:
        raise RuntimeError("body sha %s != %s" % (sha, EXPECTED_SHA))

    offline = json.loads(OFFLINE_AUDIT.read_text(encoding="utf-8"))
    packed = offline["source"]["packed"]
    provenance = {
        "body_path": str(BODY_PATH),
        "body_bytes": len(body),
        "body_sha256": sha,
        "assert_bytes": EXPECTED_BYTES,
        "assert_sha256": EXPECTED_SHA,
        "compressed_layer_from": str(OFFLINE_AUDIT).replace("\\", "/"),
        "packed_sha256": packed.get("sha256"),
        "packed_size": packed.get("size"),
        "directory_md5": packed.get("directory_md5"),
        "index_archive": packed.get("index_archive"),
        "logical_path": packed.get("logical_path"),
        "packed_lzma_equals_body": offline["source"].get("packed_lzma_equals_body"),
        "note": "Compressed payload SHA and decompressed body SHA are different layers; both already verified in offline_audit.json.",
    }

    header = a.parse_header(body)
    alloc = header["allocs"]
    nodes, offset = a.parse_skeleton(body, alloc["nNodes"])
    weight_sets, offset = a.parse_weight_sets(body, offset, len(nodes), alloc["nWeightSets"])
    child_models, offset = a.parse_child_models(body, offset, alloc["nChildModels"])
    clips, _ = a.parse_anims(body, offset, nodes, alloc["nParentAnims"])
    if len(nodes) != 57 or len(clips) != 8:
        raise RuntimeError("expected 57 nodes / 8 clips, got %s / %s" % (len(nodes), len(clips)))
    flags = parse_flags(body, len(nodes))

    parent_chain = []
    for node in nodes:
        chain = [node["name"]]
        p = node["parent"]
        while p >= 0:
            chain.append(nodes[p]["name"])
            p = nodes[p]["parent"]
        parent_chain.append({
            "index": node["index"],
            "name": node["name"],
            "parent": node["parent"],
            "parent_name": nodes[node["parent"]]["name"] if node["parent"] >= 0 else None,
            "children": node["children"],
            "chain_rootward": chain,
        })

    clip_summaries = []
    timeline_clips = []
    for clip in clips:
        times = list(clip["times_ms"])
        frames_100 = [t / 10.0 for t in times]
        summary = {
            "name": clip["name"],
            "n_keyframes": clip["n_keyframes"],
            "duration_ms": clip["duration_ms"],
            "compression": clip["compression"],
            "compression_name": clip.get("compression_name"),
            "interpolation_ms": clip.get("interpolation_ms"),
            "times_ms": times,
            "events": clip.get("events") or [],
            "fps_diagnostic_100": {
                "formula": "frame = time_ms / 10",
                "frames": frames_100,
                "duration_frames": (clip["duration_ms"] / 10.0) if clip["duration_ms"] else 0.0,
            },
            "interval_counts": {str(k): v for k, v in Counter(y - x for x, y in zip(times, times[1:])).items()},
            "true_duration_s": clip["duration_ms"] / 1000.0 if clip["duration_ms"] else 0.0,
            "blender_30fps_index_duration_s": (clip["n_keyframes"] - 1) / 30.0 if clip["n_keyframes"] else 0.0,
        }
        clip_summaries.append(summary)
        if clip["name"] in FOCUS_CLIPS:
            timeline_clips.append(summary)

    qstats = quat_stats(clips)
    synthetic = synthetic_quat_tests()
    layout_check = bind_layout_check(nodes)
    first_clip = clips[0]
    binds = [reshape16(n["matrix"], "row_major_m_ij") for n in nodes]
    partition = partition_reload0(nodes, first_clip, binds)

    hypotheses = []
    for layout in ("row_major_m_ij", "transpose"):
        binds_h = [reshape16(n["matrix"], layout) for n in nodes]
        for convention in ("xyzw", "wxyz", "xyzw_conj", "wxyz_conj"):
            for trans_how in ("col3", "row3"):
                for mul in ("parent_at_local", "local_at_parent"):
                    for compare in ("world", "fromparent_local"):
                        hypotheses.append(first_clip_hypothesis(
                            nodes, first_clip, binds_h, layout, convention, trans_how, mul, compare
                        ))
    hypotheses.sort(key=lambda h: (h["score"], -h["n_both"], h["max_pos_err"]))
    ranked = []
    seen = set()
    for h in hypotheses:
        key = (h["layout"], h["quat"], h["translation"], h["multiply"], h["compare_bind_to"])
        if key in seen:
            continue
        seen.add(key)
        ranked.append({k: h[k] for k in (
            "layout", "quat", "translation", "multiply", "compare_bind_to",
            "n_both", "n_pos_lt_1e4", "n_ang_lt_0p1deg", "max_pos_err", "max_ang_deg", "all_57_match",
        )})
        if len(ranked) >= 10:
            break

    anim_worlds_reload0 = compose_worlds(
        nodes, locals_for_frame(nodes, first_clip, 0, "xyzw", "col3", False), "parent_at_local"
    )
    anim_vs_bind, anim_vs_bind_rows = compare_world_to_bind(nodes, anim_worlds_reload0, binds, "col3")

    clips_by_name = {c["name"]: c for c in clips}
    raw_end, unit_end, raw_travel, unit_travel = {}, {}, {}, {}
    for name in ("select", "reload"):
        raw_end[name] = endpoint_vs_idle(nodes, clips_by_name, name, "xyzw", "col3", "parent_at_local", False)
        unit_end[name] = endpoint_vs_idle(nodes, clips_by_name, name, "xyzw", "col3", "parent_at_local", True)
        raw_travel[name] = max_world_travel(nodes, clips_by_name[name], "xyzw", "col3", "parent_at_local", False)
        unit_travel[name] = max_world_travel(nodes, clips_by_name[name], "xyzw", "col3", "parent_at_local", True)
    idle_travel_raw = max_world_travel(nodes, clips_by_name["idle_0"], "xyzw", "col3", "parent_at_local", False)

    i_gun = bone_index(nodes, "FvARM-bone Prop1")
    mw = a.cf_worlds(nodes, clips_by_name["select"], 0)
    ours = worlds_for_clip(nodes, clips_by_name["select"], "xyzw", "col3", "parent_at_local", False)[0]
    module_pos = np.array([mw[i_gun][0][3], mw[i_gun][1][3], mw[i_gun][2][3]])
    module_cross = {
        "compared": True,
        "select_f0_gun_module_pos": module_pos.tolist(),
        "select_f0_gun_numpy_pos": translation_of(ours[i_gun], "col3").tolist(),
        "pos_delta": float(np.linalg.norm(translation_of(ours[i_gun], "col3") - module_pos)),
    }

    any_57 = any(h["all_57_match"] for h in hypotheses)
    status = "G1_NUMERIC_AUDIT_READY_FOR_REVIEW" if any_57 else "G1_CONVENTION_OPEN"
    interpolation_open = [
        "Engine key interpolation (lerp vs slerp/squad, shortest-arc, q/-q continuity) is not in this file; interpolation_ms is stored but unread as a runtime rule.",
        "100 FPS fractional frames are diagnostic (frame=ms/10), not CF native sampling.",
        "Normalized quats are diagnostic only; raw values are retained.",
    ]
    next_step = (
        "Do not mix bind translation into animation locals yet. Next single check: "
        "compose idle_0 and select frame0 with bind-relative locals "
        "local(t)=FromParent(bind) @ inv(local_reload0) @ local(t) and compare all 57 worlds to bind. "
        "If arms still miss, bind is a modelling rest not equal to clip0; G1 visible overlay must draw "
        "two prefixed skeletons (R1A_CF_ANIM_* from tracks, R1A_CF_BIND_* from node.matrix) at reload frame0."
    )

    source_audit = {
        "task_id": "P7-S04-R1-A",
        "stage": "G1_NUMERIC_AUDIT",
        "status": status,
        "reference_kind": "SKELETON_ONLY_REFERENCE",
        "has_weights_in_geometry_json": False,
        "skinned_mesh_claimed": False,
        "compiled": False,
        "deployed": False,
        "user_accepted": False,
        "provenance": provenance,
        "parse_order": ["parse_header", "parse_skeleton", "parse_weight_sets", "parse_child_models", "parse_anims"],
        "header": header,
        "n_nodes": len(nodes),
        "n_clips": len(clips),
        "n_weight_sets": len(weight_sets),
        "weight_sets": [{"name": w["name"], "count": w["count"], "nonzero": w["nonzero"]} for w in weight_sets],
        "child_models": child_models,
        "node_flags": {
            "unique": sorted({f["flags"] for f in flags}),
            "nonzero": [f for f in flags if f["flags"]],
            "note": "m_Flags parsed as the byte after uint16 index; all zero, so MNODE_ROTATIONONLY is not set.",
        },
        "parent_chain": parent_chain,
        "clips": [{k: v for k, v in c.items() if k != "fps_diagnostic_100"} | {
            "diagnostic_100fps_frames": c["fps_diagnostic_100"]["frames"],
        } for c in clip_summaries],
        "first_exported_clip_in_file": first_clip["name"],
        "jupiter_comment": (
            "ModelNode global transform is documented as the first frame of the first exported animation; "
            "treated as a testable hypothesis. Empirically true for the 11-bone gun subtree plus FvARM-bone "
            "position at reload frame0, false for Pelvis/arm chain and Scene Root rotation."
        ),
        "bind_matrix_layout": layout_check,
        "animation_track_convention_used_for_endpoints": ANIM_CONV,
        "matrix_quat_search": {
            "ranked_on": "reload (first file clip) frame0, all 57 bones",
            "n_hypotheses": len(hypotheses),
            "any_all_57_match": any_57,
            "animation_world_vs_bind": anim_vs_bind,
            "ranked_head": ranked,
            "partition_reload0": {
                "world_vs_bind_pos_match": partition["world_vs_bind_pos_match"],
                "fromparent_pos_match_count": len(partition["fromparent_pos_match"]),
                "fromparent_rot_match_count": len(partition["fromparent_rot_match"]),
                "gun_subtree_all_world_match": partition["gun_subtree_all_world_match"],
                "gun_subtree_count": partition["gun_subtree_count"],
                "scene_root": partition["scene_root"],
                "FvARM-bone": partition["FvARM-bone"],
                "pelvis": partition["pelvis"],
            },
            "module_cf_worlds_crosscheck": module_cross,
        },
        "quaternion_findings": {
            **qstats,
            "synthetic": synthetic,
            "interpolation_open": interpolation_open,
        },
        "source_end_vs_idle": {
            "convention": ANIM_CONV,
            "raw_unnormalized": raw_end,
            "normalized_diagnostic": unit_end,
        },
        "max_world_travel": {
            "raw_unnormalized": raw_travel,
            "normalized_diagnostic": unit_travel,
            "idle_0_raw": idle_travel_raw,
        },
        "enough_for_skeleton_visible_reference": False,
        "enough_for_animation_track_overlay_with_open_bind": True,
        "next_verification_step": next_step,
        "open_items": interpolation_open + [
            "No hypothesis matched all 57 bones of bind vs first-exported-frame.",
            "Pelvis reload[0] local translation is zero while bind FromParent translation is not; arm world therefore diverges from bind.",
            "Scene Root bind is 180deg about Y; animation quat is identity.",
        ],
    }

    timeline = {
        "task_id": "P7-S04-R1-A",
        "diagnostic_fps": 100,
        "mapping": "frame = time_ms * 100 / 1000 = time_ms / 10",
        "note": "100 FPS is a diagnostic choice for this task, not CF native sampling.",
        "interpolation": {
            "position": "linear in source time (not applied in this checkpoint)",
            "rotation": "unit quaternion shortest-arc slerp with q/-q continuity proposed after convention check; engine habit OPEN",
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

    parsed = {
        "reference_kind": "SKELETON_ONLY_REFERENCE",
        "convention": ANIM_CONV,
        "bind_not_equal_all_57": True,
        "nodes": [
            {
                "index": n["index"],
                "name": n["name"],
                "parent": n["parent"],
                "children": n["children"],
                "bind_matrix_16_row_major_m_ij": list(n["matrix"]),
            }
            for n in nodes
        ],
        "clips": [],
    }
    for clip in clips:
        tracks = []
        for tr in clip["tracks"]:
            if tr.get("kind") != "full":
                tracks.append({"node": tr["node"], "name": tr["name"], "kind": tr.get("kind")})
                continue
            tracks.append({
                "node": tr["node"],
                "name": tr["name"],
                "kind": "full",
                "pos": [[float(x) for x in p] for p in tr["pos"]],
                "quat_raw_file_order": [[float(x) for x in q] for q in tr["quat"]],
            })
        parsed["clips"].append({
            "name": clip["name"],
            "times_ms": list(clip["times_ms"]),
            "events": clip.get("events") or [],
            "tracks": tracks,
        })

    (OUT_DIR / "source_audit.json").write_text(json.dumps(jsonable(source_audit), indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "timeline.json").write_text(json.dumps(jsonable(timeline), indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "parsed_tracks.json").write_text(json.dumps(jsonable(parsed), indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / "bind_vs_reload0_per_bone.json").write_text(
        json.dumps(jsonable(partition["per_bone"]), indent=2) + "\n", encoding="utf-8"
    )

    print(json.dumps({
        "status": status,
        "body_sha": sha,
        "nodes": len(nodes),
        "clips": [c["name"] for c in clips],
        "any_57_match": any_57,
        "anim_world_vs_bind": anim_vs_bind,
        "ranked_head": ranked[:4],
        "gun_subtree_match": partition["gun_subtree_all_world_match"],
        "reload_L_Hand_key96_norm": qstats["reload_L_Hand_key96"]["norm"],
        "select_gun_first_vs_idle": raw_end["select"]["FvARM-bone Prop1"]["first_vs_idle_pos"],
        "select_gun_last_vs_idle": raw_end["select"]["FvARM-bone Prop1"]["last_vs_idle_pos"],
        "wrote": [
            str(OUT_DIR / "source_audit.json"),
            str(OUT_DIR / "timeline.json"),
            str(OUT_DIR / "parsed_tracks.json"),
        ],
    }, indent=2))


if __name__ == "__main__":
    main()
