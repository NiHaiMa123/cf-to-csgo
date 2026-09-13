"""Read-only review of P7-S04 inputs; writes only this review's JSON.

Does not run either retargeter's main(), save Blender, export SMD, or deploy.
"""
import hashlib
import json
import lzma
import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/p5"))
import p5_p7_s04_cf_animation as a
import p5_p7_s04_fix_retarget as b


def main():
    body = a.recover_pv_ltb()
    archive = a.CF / "rez2/RF016.REZ"
    matches = [e for e in a.extract_all.read_index_entries(str(archive))
               if e["full_path"].upper() == "PLAYERVIEW/PV-M4A1_S_TRANSFORMERS.LTB"]
    if not matches:
        matches = [e for e in a.extract_all.read_index_entries(str(archive))
                   if e["full_path"].upper() == "MODELS/PLAYERVIEW/PV-M4A1_S_TRANSFORMERS.LTB"]
    if len(matches) != 1:
        raise ValueError(f"Expected one indexed PV entry, found {len(matches)}")
    packed, provenance = a.read_verified_payload(archive, matches[0])
    assert hashlib.sha256(packed).hexdigest() == a.EXPECTED_SHA
    assert lzma.decompress(packed, format=lzma.FORMAT_ALONE) == body
    header = a.parse_header(body)
    alloc = header["allocs"]
    nodes, offset = a.parse_skeleton(body, alloc["nNodes"])
    _, offset = a.parse_weight_sets(body, offset, len(nodes), alloc["nWeightSets"])
    _, offset = a.parse_child_models(body, offset, alloc["nChildModels"])
    clips, _ = a.parse_anims(body, offset, nodes, alloc["nParentAnims"])
    path = a.P7S02 / "source1/v_rif_m4a1_anims/idle.smd"
    smd = a.parse_smd_skeleton(path)
    frames = {}
    in_skeleton = False
    frame = None
    for line in path.read_text().splitlines():
        parts = line.split()
        if not parts:
            continue
        if parts[0] == "skeleton":
            in_skeleton = True
            continue
        if in_skeleton and parts[0] == "end":
            break
        if not in_skeleton:
            continue
        if parts[0] == "time":
            frame = int(parts[1])
            frames[frame] = {}
            continue
        frames[frame][int(parts[0])] = tuple(map(float, parts[1:7]))
    first, last = min(frames), max(frames)
    results = {
        "source": {"packed": provenance, "body_path": str(a.PV_LTB),
                   "body_sha256": hashlib.sha256(body).hexdigest(),
                   "packed_lzma_equals_body": True},
        "nodes": len(nodes), "clips": [],
        "rest_parser": {
            "path": str(path), "first_frame": first, "last_frame": last,
            "returns_last_frame": smd["rest"] == frames[last],
            "returns_first_frame": smd["rest"] == frames[first],
            "first_last_max_component_delta": max(
                abs(frames[first][i][j] - frames[last][i][j])
                for i in frames[first] for j in range(6)),
        },
    }
    transform = a.load_c3_mirror()
    cf_names = {n["name"]: n["index"] for n in nodes}
    idle = next(c for c in clips if c["name"] == "idle_0")
    idle_world = a.cf_worlds(nodes, idle, 0)
    for clip in clips:
        if clip["name"] not in ("select", "reload", "idle_0"):
            continue
        times = clip["times_ms"]
        count = clip["n_keyframes"]
        first_world = a.cf_worlds(nodes, clip, 0)
        last_world = a.cf_worlds(nodes, clip, count - 1)
        output = b.retarget_clip_relative(nodes, clip, smd, transform)
        pairs = {side: [smd["names"].index("v_weapon.Bip01_" + side + "_" + part)
                        for part in ("Clavicle", "UpperArm", "Forearm", "Hand")]
                 for side in ("L", "R")}
        lengths = {side: {"upper_to_fore": [], "clav_to_upper": []} for side in pairs}
        for pose in output:
            world = b.pose_worlds(smd, pose)
            for side, (clav, upper, fore, hand) in pairs.items():
                lengths[side]["upper_to_fore"].append(b.dist(world[upper], world[fore]))
                lengths[side]["clav_to_upper"].append(b.dist(world[clav], world[upper]))
        norms = [math.sqrt(sum(x*x for x in q)) for tr in clip["tracks"] for q in tr.get("quat", [])]
        results["clips"].append({
            "name": clip["name"], "times_ms": times,
            "interval_counts": dict(Counter(y-x for x, y in zip(times, times[1:]))),
            "duration_ms": clip["duration_ms"],
            "uniform_index_max_time_error_ms": max(abs(t-i*clip["duration_ms"]/(count-1)) for i,t in enumerate(times)),
            "blender_at_30fps_duration_s": (count-1)/30,
            "true_duration_s": clip["duration_ms"]/1000,
            "events": clip["events"], "quat_norm_minmax": [min(norms), max(norms)],
            "arm_lengths": {side: {key: [min(values), max(values)] for key,values in data.items()} for side,data in lengths.items()},
            "cf_gun_first_last_distance": b.dist(first_world[cf_names[b.CF_GUN]], last_world[cf_names[b.CF_GUN]]),
            "source_first_vs_idle_distances": {bone: b.dist(first_world[cf_names[bone]], idle_world[cf_names[bone]]) for bone in (b.CF_GUN, b.CF_R_HAND, b.CF_L_HAND)},
            "source_last_vs_idle_distances": {bone: b.dist(last_world[cf_names[bone]], idle_world[cf_names[bone]]) for bone in (b.CF_GUN, b.CF_R_HAND, b.CF_L_HAND)},
            "smallest_quaternion": min((math.sqrt(sum(x*x for x in q)), tr["name"], i) for tr in clip["tracks"] for i,q in enumerate(tr.get("quat", []))),
        })
    dest = Path(__file__).with_name("offline_audit.json")
    dest.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({**results, "clips": [{k:v for k,v in c.items() if k != "times_ms"} for c in results["clips"]]}, indent=2))


if __name__ == "__main__":
    main()
