"""P7-S04 Blender-only retarget fix.

Gun-driven, relative-preserving. CF Prop1 drives M4A1_Parent. Hands keep
the CS hold grip plus CF hand-vs-gun relative change, so they stay on the
weapon. Mag/bolt keep CF motion relative to the gun. Fingers keep CF
motion relative to their parents. UpperArm/Clavicle/ForeTwist stay at the
CS hold offset from the forearm so bonemerge gloves do not stretch.

Writes SMDs for the Blender scene only. Does not compile or deploy.

Repro:
  python scripts/p5/p5_p7_s04_fix_retarget.py
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = Path(__file__).resolve().parent
_PROJECT_DIR = _SCRIPT_DIR.parent.parent
sys.path.insert(0, str(_SCRIPT_DIR))
sys.path.insert(0, str(_PROJECT_DIR / "scripts"))

import p5_p7_s04_cf_animation as src  # noqa: E402

REPO = src.REPO
OUT = src.OUT
P7S02 = src.P7S02
PV_LTB = src.PV_LTB
EXPECTED_SHA = src.EXPECTED_SHA
BONE_MAP = src.BONE_MAP
SMD_DIR = OUT / "smd"
REPORT_JSON = OUT / "blender" / "fix_retarget.json"
REPORT_MD = OUT / "blender" / "fix_retarget.md"

CS_GUN = "v_weapon.M4A1_Parent"
CS_CLIP = "v_weapon.M4A1_Clip"
CS_BOLT = "v_weapon.M4A1_Bolt"
CS_R_HAND = "v_weapon.Bip01_R_Hand"
CS_L_HAND = "v_weapon.Bip01_L_Hand"
CS_R_FORE = "v_weapon.Bip01_R_Forearm"
CS_L_FORE = "v_weapon.Bip01_L_Forearm"
CS_R_UPPER = "v_weapon.Bip01_R_UpperArm"
CS_L_UPPER = "v_weapon.Bip01_L_UpperArm"
CS_R_CLAV = "v_weapon.Bip01_R_Clavicle"
CS_L_CLAV = "v_weapon.Bip01_L_Clavicle"
CS_R_TWIST = "v_weapon.Bip01_R_ForeTwist"
CS_L_TWIST = "v_weapon.Bip01_L_ForeTwist"

CF_GUN = "FvARM-bone Prop1"
CF_CLIP = "Bone06"
CF_BOLT = "Bone04"
CF_R_HAND = "FvARM-bone R Hand"
CF_L_HAND = "FvARM-bone L Hand"
CF_R_FORE = "FvARM-bone R ForeArm"
CF_L_FORE = "FvARM-bone L ForeArm"
CF_R_UPPER = "FvARM-bone R UpperArm"
CF_L_UPPER = "FvARM-bone L UpperArm"

CLIP_MAP = {
    "reload": ("reload", "reload.smd"),
    "select": ("draw", "draw.smd"),
    "idle_0": ("idle", "idle.smd"),
    "fire": ("shoot1", "shoot1.smd"),
}


def ident() -> list[list[float]]:
    return src.ident()


def mat_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    return src.mat_mul(a, b)


def mat_inv(m: list[list[float]]) -> list[list[float]]:
    return src.mat_inv(m)


def rot_only(m: list[list[float]]) -> list[list[float]]:
    out = ident()
    for i in range(3):
        for j in range(3):
            out[i][j] = m[i][j]
    return out


def conjugate(basis: list[list[float]], delta: list[list[float]]) -> list[list[float]]:
    return mat_mul(mat_mul(basis, delta), mat_inv(basis))


def rel_of(parent: list[list[float]], child: list[list[float]]) -> list[list[float]]:
    return mat_mul(mat_inv(parent), child)


def dist(a: list[list[float]], b: list[list[float]]) -> float:
    pa, pb = src.trans_of(a), src.trans_of(b)
    return math.sqrt(sum((pa[i] - pb[i]) ** 2 for i in range(3)))


def local_len(m: list[list[float]]) -> float:
    t = src.trans_of(m)
    return math.sqrt(sum(v * v for v in t))


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel_delta(parent0: list[list[float]], child0: list[list[float]], parent_f: list[list[float]], child_f: list[list[float]]) -> list[list[float]]:
    rel0 = rel_of(parent0, child0)
    relf = rel_of(parent_f, child_f)
    return mat_mul(mat_inv(rel0), relf)


def basis_cf_to_cs(cs_parent_rest: list[list[float]], transform: list[list[float]], cf_parent0: list[list[float]]) -> list[list[float]]:
    return rot_only(mat_mul(mat_inv(cs_parent_rest), mat_mul(transform, cf_parent0)))


def apply_rel_change(
    cs_parent_world: list[list[float]],
    cs_parent_rest: list[list[float]],
    cs_child_rest: list[list[float]],
    transform: list[list[float]],
    cf_parent0: list[list[float]],
    cf_child0: list[list[float]],
    cf_parent_f: list[list[float]],
    cf_child_f: list[list[float]],
) -> list[list[float]]:
    delta = rel_delta(cf_parent0, cf_child0, cf_parent_f, cf_child_f)
    basis = basis_cf_to_cs(cs_parent_rest, transform, cf_parent0)
    rest_in_parent = rel_of(cs_parent_rest, cs_child_rest)
    return mat_mul(cs_parent_world, mat_mul(rest_in_parent, conjugate(basis, delta)))


def local_with_delta(
    cs_rest_local: list[list[float]],
    cs_parent_rest: list[list[float]],
    transform: list[list[float]],
    cf_parent0: list[list[float]],
    cf_child0: list[list[float]],
    cf_parent_f: list[list[float]],
    cf_child_f: list[list[float]],
) -> list[list[float]]:
    delta = rel_delta(cf_parent0, cf_child0, cf_parent_f, cf_child_f)
    basis = basis_cf_to_cs(cs_parent_rest, transform, cf_parent0)
    return mat_mul(cs_rest_local, conjugate(basis, delta))


def follow_rest(parent_world: list[list[float]], parent_rest: list[list[float]], child_rest: list[list[float]]) -> list[list[float]]:
    return mat_mul(parent_world, rel_of(parent_rest, child_rest))


def retarget_clip_relative(
    nodes: list[dict[str, Any]],
    clip: dict[str, Any],
    smd: dict[str, Any],
    transform: list[list[float]],
) -> list[list[tuple[float, ...]]]:
    cf_name = {node["name"]: node["index"] for node in nodes}
    cs_name = {name: i for i, name in enumerate(smd["names"])}
    required = [
        CF_GUN, CF_CLIP, CF_BOLT, CF_R_HAND, CF_L_HAND, CF_R_FORE, CF_L_FORE, CF_R_UPPER, CF_L_UPPER,
        CS_GUN, CS_CLIP, CS_BOLT, CS_R_HAND, CS_L_HAND, CS_R_FORE, CS_L_FORE,
        CS_R_UPPER, CS_L_UPPER, CS_R_CLAV, CS_L_CLAV, CS_R_TWIST, CS_L_TWIST,
    ]
    for name in required:
        if name.startswith("FvARM") or name.startswith("Bone"):
            if name not in cf_name:
                raise RuntimeError(f"missing CF bone {name}")
        elif name not in cs_name:
            raise RuntimeError(f"missing CS bone {name}")

    inv_t = mat_inv(transform)
    cf0 = src.cf_worlds(nodes, clip, 0)
    rest_w = smd["rest_world"]
    rest_l = smd["rest_local"]
    parents = smd["parents"]
    names = smd["names"]
    topo = src.cs_topo(parents)

    i_gun = cs_name[CS_GUN]
    i_clip = cs_name[CS_CLIP]
    i_bolt = cs_name[CS_BOLT]
    i_rh = cs_name[CS_R_HAND]
    i_lh = cs_name[CS_L_HAND]
    i_rf = cs_name[CS_R_FORE]
    i_lf = cs_name[CS_L_FORE]
    i_ru = cs_name[CS_R_UPPER]
    i_lu = cs_name[CS_L_UPPER]
    i_rc = cs_name[CS_R_CLAV]
    i_lc = cs_name[CS_L_CLAV]
    i_rt = cs_name[CS_R_TWIST]
    i_lt = cs_name[CS_L_TWIST]

    cf_gun = cf_name[CF_GUN]
    cf_clip = cf_name[CF_CLIP]
    cf_bolt = cf_name[CF_BOLT]
    cf_rh = cf_name[CF_R_HAND]
    cf_lh = cf_name[CF_L_HAND]
    cf_rf = cf_name[CF_R_FORE]
    cf_lf = cf_name[CF_L_FORE]
    cf_ru = cf_name[CF_R_UPPER]
    cf_lu = cf_name[CF_L_UPPER]

    reverse_map = {cs: cf for cf, cs in BONE_MAP.items()}
    matching_local: dict[int, tuple[int, int]] = {}
    for cs_idx, cs_bone in enumerate(names):
        cf_bone = reverse_map.get(cs_bone)
        if cf_bone is None:
            continue
        if cs_bone in {CS_GUN, CS_CLIP, CS_BOLT, CS_R_HAND, CS_L_HAND, CS_R_FORE, CS_L_FORE}:
            continue
        cf_idx = cf_name[cf_bone]
        cf_parent = nodes[cf_idx]["parent"]
        if cf_parent < 0:
            continue
        cf_parent_name = nodes[cf_parent]["name"]
        cs_parent = parents[cs_idx]
        if cs_parent < 0:
            continue
        if BONE_MAP.get(cf_parent_name) != names[cs_parent]:
            continue
        matching_local[cs_idx] = (cf_idx, cf_parent)

    n_frames = clip["n_keyframes"]
    frames: list[list[tuple[float, ...]]] = []
    prev_eul = {i: smd["rest"][i][3:6] for i in range(len(names))}

    for frame in range(n_frames):
        cf_w = src.cf_worlds(nodes, clip, frame)
        gun_delta = mat_mul(cf_w[cf_gun], mat_inv(cf0[cf_gun]))
        gun_w = mat_mul(mat_mul(mat_mul(transform, gun_delta), inv_t), rest_w[i_gun])

        rh_w = apply_rel_change(gun_w, rest_w[i_gun], rest_w[i_rh], transform, cf0[cf_gun], cf0[cf_rh], cf_w[cf_gun], cf_w[cf_rh])
        lh_w = apply_rel_change(gun_w, rest_w[i_gun], rest_w[i_lh], transform, cf0[cf_gun], cf0[cf_lh], cf_w[cf_gun], cf_w[cf_lh])
        clip_w = apply_rel_change(gun_w, rest_w[i_gun], rest_w[i_clip], transform, cf0[cf_gun], cf0[cf_clip], cf_w[cf_gun], cf_w[cf_clip])
        bolt_w = apply_rel_change(gun_w, rest_w[i_gun], rest_w[i_bolt], transform, cf0[cf_gun], cf0[cf_bolt], cf_w[cf_gun], cf_w[cf_bolt])

        rh_local = local_with_delta(rest_l[i_rh], rest_w[i_rf], transform, cf0[cf_rf], cf0[cf_rh], cf_w[cf_rf], cf_w[cf_rh])
        lh_local = local_with_delta(rest_l[i_lh], rest_w[i_lf], transform, cf0[cf_lf], cf0[cf_lh], cf_w[cf_lf], cf_w[cf_lh])
        rf_w = mat_mul(rh_w, mat_inv(rh_local))
        lf_w = mat_mul(lh_w, mat_inv(lh_local))

        ru_w = apply_rel_change(rf_w, rest_w[i_rf], rest_w[i_ru], transform, cf0[cf_rf], cf0[cf_ru], cf_w[cf_rf], cf_w[cf_ru])
        lu_w = apply_rel_change(lf_w, rest_w[i_lf], rest_w[i_lu], transform, cf0[cf_lf], cf0[cf_lu], cf_w[cf_lf], cf_w[cf_lu])
        rc_w = follow_rest(ru_w, rest_w[i_ru], rest_w[i_rc])
        lc_w = follow_rest(lu_w, rest_w[i_lu], rest_w[i_lc])
        rt_w = follow_rest(rf_w, rest_w[i_rf], rest_w[i_rt])
        lt_w = follow_rest(lf_w, rest_w[i_lf], rest_w[i_lt])

        desired = {
            i_gun: gun_w,
            i_clip: clip_w,
            i_bolt: bolt_w,
            i_rh: rh_w,
            i_lh: lh_w,
            i_rf: rf_w,
            i_lf: lf_w,
            i_ru: ru_w,
            i_lu: lu_w,
            i_rc: rc_w,
            i_lc: lc_w,
            i_rt: rt_w,
            i_lt: lt_w,
        }

        cs_w: list[list[list[float]] | None] = [None] * len(names)
        pose: list[tuple[float, ...] | None] = [None] * len(names)
        for index in topo:
            parent = parents[index]
            parent_w = ident() if parent < 0 else cs_w[parent]
            if index in desired:
                world = desired[index]
            elif index in matching_local:
                cf_idx, cf_parent = matching_local[index]
                local = local_with_delta(
                    rest_l[index],
                    rest_w[parent],
                    transform,
                    cf0[cf_parent],
                    cf0[cf_idx],
                    cf_w[cf_parent],
                    cf_w[cf_idx],
                )
                world = mat_mul(parent_w, local)
            elif parent < 0:
                world = rest_w[index]
            else:
                world = mat_mul(parent_w, rest_l[index])
            cs_w[index] = world
            local = rel_of(parent_w, world)
            eul = src.unwrap_euler(src.mat_to_euler_xyz(local), prev_eul[index])
            prev_eul[index] = eul
            pose[index] = (*src.trans_of(local), *eul)
        frames.append(pose)  # type: ignore[arg-type]
    return frames


def pose_worlds(smd: dict[str, Any], pose: list[tuple[float, ...]]) -> list[list[list[float]]]:
    worlds = [ident() for _ in smd["names"]]
    for index, parent in enumerate(smd["parents"]):
        local = src.local_from_pos_euler(pose[index][:3], pose[index][3:6])
        worlds[index] = local if parent < 0 else mat_mul(worlds[parent], local)
    return worlds


def clip_metrics(smd: dict[str, Any], frames: list[list[tuple[float, ...]]]) -> dict[str, Any]:
    names = smd["names"]
    i_gun = names.index(CS_GUN)
    i_clip = names.index(CS_CLIP)
    i_bolt = names.index(CS_BOLT)
    i_rh = names.index(CS_R_HAND)
    i_lh = names.index(CS_L_HAND)
    i_rf = names.index(CS_R_FORE)
    i_r_f1 = names.index("v_weapon.Bip01_R_Finger1")
    i_r_f11 = names.index("v_weapon.Bip01_R_Finger11")
    rest_w = pose_worlds(smd, [smd["rest"][i] for i in range(len(names))])
    rest_gun_hand = dist(rest_w[i_gun], rest_w[i_rh])
    rest_wrist = dist(rest_w[i_rf], rest_w[i_rh])
    rest_finger = dist(rest_w[i_r_f1], rest_w[i_r_f11])
    gun_hand = []
    wrist = []
    finger = []
    mag_local = []
    bolt_local = []
    lhand_clip = []
    for pose in frames:
        worlds = pose_worlds(smd, pose)
        gun_hand.append(dist(worlds[i_gun], worlds[i_rh]))
        wrist.append(dist(worlds[i_rf], worlds[i_rh]))
        finger.append(dist(worlds[i_r_f1], worlds[i_r_f11]))
        mag_local.append(math.sqrt(sum((pose[i_clip][k] - frames[0][i_clip][k]) ** 2 for k in range(3))))
        bolt_local.append(math.sqrt(sum((pose[i_bolt][k] - frames[0][i_bolt][k]) ** 2 for k in range(3))))
        lhand_clip.append(dist(worlds[i_lh], worlds[i_clip]))
    f0 = pose_worlds(smd, frames[0])
    f0_err = {
        "gun": dist(f0[i_gun], rest_w[i_gun]),
        "r_hand": dist(f0[i_rh], rest_w[i_rh]),
        "l_hand": dist(f0[i_lh], rest_w[i_lh]),
        "r_fore": dist(f0[i_rf], rest_w[i_rf]),
    }
    return {
        "rest_gun_hand": rest_gun_hand,
        "gun_hand_min": min(gun_hand),
        "gun_hand_max": max(gun_hand),
        "gun_hand_f0": gun_hand[0],
        "wrist_rest": rest_wrist,
        "wrist_min": min(wrist),
        "wrist_max": max(wrist),
        "finger_rest": rest_finger,
        "finger_min": min(finger),
        "finger_max": max(finger),
        "mag_local_travel": max(mag_local),
        "bolt_local_travel": max(bolt_local),
        "lhand_clip_min": min(lhand_clip),
        "lhand_clip_f0": lhand_clip[0],
        "frame0_hold_error": f0_err,
    }


def main() -> int:
    body = src.recover_pv_ltb()
    header = src.parse_header(body)
    allocs = header["allocs"]
    nodes, after_skel = src.parse_skeleton(body, allocs["nNodes"])
    _weight_sets, off = src.parse_weight_sets(body, after_skel, allocs["nNodes"], allocs["nWeightSets"])
    _children, off = src.parse_child_models(body, off, allocs["nChildModels"])
    clips, _off = src.parse_anims(body, off, nodes, allocs["nParentAnims"])
    by_name = {clip["name"]: clip for clip in clips}
    for required in CLIP_MAP:
        if required not in by_name:
            raise RuntimeError(f"missing CF clip {required}: {list(by_name)}")

    rest_smd = P7S02 / "source1" / "v_rif_m4a1_anims" / "idle.smd"
    smd = src.parse_smd_skeleton(rest_smd)
    transform = src.load_c3_mirror()
    SMD_DIR.mkdir(parents=True, exist_ok=True)
    (OUT / "blender").mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {}
    for cf_name, (dst, filename) in CLIP_MAP.items():
        frames = retarget_clip_relative(nodes, by_name[cf_name], smd, transform)
        info = src.write_retargeted_smd(SMD_DIR / filename, smd, frames)
        metrics = clip_metrics(smd, frames)
        old_frames = src.retarget_clip(nodes, by_name[cf_name], smd, transform)
        old_metrics = clip_metrics(smd, old_frames)
        results[dst] = {
            **info,
            "cf_clip": cf_name,
            "fps": by_name[cf_name]["fps"],
            "new": metrics,
            "old_independent_world": old_metrics,
        }

    hold_ok = all(max(item["new"]["frame0_hold_error"].values()) < 0.05 for item in results.values())
    gun_hand_ok = all(
        item["new"]["gun_hand_max"] - item["new"]["gun_hand_min"] < 8.0
        for item in results.values()
    )
    mag_ok = results["reload"]["new"]["mag_local_travel"] > 4.0
    wrist_ok = all(
        abs(item["new"]["wrist_max"] - item["new"]["wrist_rest"]) < 2.0
        and abs(item["new"]["wrist_min"] - item["new"]["wrist_rest"]) < 2.0
        for item in results.values()
    )
    finger_ok = all(
        abs(item["new"]["finger_max"] - item["new"]["finger_rest"]) < 0.5
        for item in results.values()
    )

    report = {
        "schema": "cf2.p7.fix-retarget.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "result": "P7_CF_ANIM_RETARGET_FIXED_OFFLINE",
        "method": "gun_driven_relative_preserving",
        "deployed": False,
        "compiled": False,
        "source_ltb": str(PV_LTB).replace("\\", "/"),
        "expected_sha256": EXPECTED_SHA,
        "rest": str(rest_smd).replace("\\", "/"),
        "smd_dir": str(SMD_DIR).replace("\\", "/"),
        "gates": {
            "frame0_stays_on_p6_hold": hold_ok,
            "gun_hand_relative_stable": gun_hand_ok,
            "reload_mag_moves": mag_ok,
            "wrist_length_stable": wrist_ok,
            "finger_length_stable": finger_ok,
        },
        "clips": results,
        "notes": [
            "CS M4A1_Parent is a child of R_Hand; CF Prop1 is a sibling of the arms.",
            "Independent world-space retarget of both gun and hands is the rejected method.",
            "This pass drives the gun from CF Prop1 and places hands from CF hand-vs-gun relative change on top of the CS hold grip.",
            "Not compiled. Not deployed. Blender verify next.",
        ],
    }
    REPORT_JSON.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# P7-S04 retarget fix (Blender only)",
        "",
        "Result: **P7_CF_ANIM_RETARGET_FIXED_OFFLINE**.",
        "",
        "Gun-driven relative retarget. Hands stay on the CS hold grip plus CF hand-vs-gun change.",
        "Not compiled. Not deployed.",
        "",
        "| clip | gun-hand min/max (old) | gun-hand min/max (new) | mag travel | wrist max Δ |",
        "|---|---|---|---|---|",
    ]
    for name, item in results.items():
        old = item["old_independent_world"]
        new = item["new"]
        lines.append(
            f"| {name} | {old['gun_hand_min']:.2f}/{old['gun_hand_max']:.2f} | "
            f"{new['gun_hand_min']:.2f}/{new['gun_hand_max']:.2f} | "
            f"{new['mag_local_travel']:.2f} | {new['wrist_max'] - new['wrist_rest']:.2f} |"
        )
    lines.extend(["", f"Gates: `{json.dumps(report['gates'])}`", ""])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "result": report["result"],
        "gates": report["gates"],
        "clips": {
            name: {
                "new_gun_hand": [item["new"]["gun_hand_min"], item["new"]["gun_hand_max"]],
                "old_gun_hand": [item["old_independent_world"]["gun_hand_min"], item["old_independent_world"]["gun_hand_max"]],
                "mag": item["new"]["mag_local_travel"],
                "f0_err": item["new"]["frame0_hold_error"],
            }
            for name, item in results.items()
        },
        "smd": str(SMD_DIR).replace("\\", "/"),
    }, ensure_ascii=False, indent=2))
    if not all(report["gates"].values()):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
