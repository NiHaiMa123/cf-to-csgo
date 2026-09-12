"""P7-S04 — decode CF original animation clips from PV-M4A1_S_Transformers.LTB.

Walks the Jupiter Model::Load tail after the already-decoded Scene Root
skeleton: weight sets, child models, then parent anims. Does not overwrite
frozen, P7-S01 sound, or the live viewmodel until clips decode cleanly.

Repro:
  python scripts/p5/p5_p7_s04_cf_animation.py
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import re
import shutil
import struct
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "cf_extract"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "material_recovery"))
import _paths  # noqa: E402
import extract_all  # noqa: E402
from rez_verified_payload import read_verified_payload  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / "work" / "p5_leishen" / "p7_s04"
PV_LTB = REPO / "work" / "p5_leishen" / "p6" / "verified_root" / "Models" / "PLAYERVIEW" / "PV-M4A1_S_Transformers.LTB"
EXPECTED_SHA = "a0ccef5deed745f1731eb93295c630f531123288055f3c3790531b99b6e401b8"
ALLOC_NAMES = [
    "nKeyFrames", "nParentAnims", "nNodes", "nPieces", "nChildModels",
    "nTris", "nVerts", "nVertexWeights", "nLODs", "nSockets",
    "nWeightSets", "nStrings", "StringLengths", "VertAnimDataSize", "nAnimData",
]
ANCMPRS = {0: "NONE", 1: "REL", 2: "REL_16", 3: "REL_16_ROT_ONLY"}


def u16(buf: bytes, off: int) -> int:
    return struct.unpack_from("<H", buf, off)[0]


def u32(buf: bytes, off: int) -> int:
    return struct.unpack_from("<I", buf, off)[0]


def f32(buf: bytes, off: int) -> float:
    return struct.unpack_from("<f", buf, off)[0]


def read_string(buf: bytes, off: int) -> tuple[str, int]:
    ln = u16(buf, off)
    if ln > 1024 or off + 2 + ln > len(buf):
        raise ValueError(f"bad string at {off} len={ln}")
    raw = buf[off + 2 : off + 2 + ln]
    if raw.endswith(b"\x00"):
        raw = raw[:-1]
    return raw.decode("ascii", errors="replace"), off + 2 + ln


def looks_like_name(text: str) -> bool:
    if not text or len(text) > 256:
        return False
    return all(32 <= ord(ch) < 127 for ch in text)


def parse_header(buf: bytes) -> dict[str, Any]:
    file_type = buf[0]
    version = u16(buf, 2)
    file_version = u32(buf, 20)
    allocs = list(struct.unpack_from("<15I", buf, 24))
    return {
        "file_type": file_type,
        "ltb_header_version": version,
        "model_file_version": file_version,
        "allocs": dict(zip(ALLOC_NAMES, allocs)),
    }


def parse_skeleton(buf: bytes, expected_nodes: int) -> tuple[list[dict[str, Any]], int]:
    marker = buf.find(b"Scene Root")
    if marker < 2:
        raise RuntimeError("Scene Root not found")
    position = marker - 2
    nodes: list[dict[str, Any]] = []
    for node_index in range(expected_nodes):
        name, payload = read_string(buf, position)
        index = u16(buf, payload)
        if index != node_index:
            raise RuntimeError(f"node index {index} != {node_index} at {payload}")
        matrix = list(struct.unpack_from("<16f", buf, payload + 3))
        child_count = u32(buf, payload + 67)
        if child_count > expected_nodes:
            raise RuntimeError(f"child_count {child_count} at node {node_index}")
        nodes.append({"index": index, "name": name, "child_count": child_count, "matrix": matrix, "parent": -1})
        position = payload + 71
    stack: list[tuple[int, int]] = []
    for index, node in enumerate(nodes):
        while stack and stack[-1][1] == 0:
            stack.pop()
        if stack:
            parent, remaining = stack.pop()
            node["parent"] = parent
            stack.append((parent, remaining - 1))
        stack.append((index, node["child_count"]))
    if any(remain != 0 for _, remain in stack):
        raise RuntimeError("skeleton child counts did not exhaust")
    children: list[list[int]] = [[] for _ in nodes]
    for index, node in enumerate(nodes):
        if node["parent"] >= 0:
            children[node["parent"]].append(index)
    for index, kids in enumerate(children):
        nodes[index]["children"] = kids
    return nodes, position


def dfs_nodes(nodes: list[dict[str, Any]]) -> list[int]:
    order: list[int] = []

    def walk(index: int) -> None:
        order.append(index)
        for child in nodes[index]["children"]:
            walk(child)

    roots = [i for i, node in enumerate(nodes) if node["parent"] < 0]
    for root in roots:
        walk(root)
    return order


def parse_weight_sets(buf: bytes, off: int, n_nodes: int, expected: int) -> tuple[list[dict[str, Any]], int]:
    n_sets = u32(buf, off)
    off += 4
    if expected and n_sets != expected:
        # CF may still be valid; record and continue if small.
        if n_sets > 64:
            raise RuntimeError(f"nWeightSets {n_sets} looks wrong at {off-4}")
    sets = []
    for _ in range(n_sets):
        name, off = read_string(buf, off)
        n_weights = u32(buf, off)
        off += 4
        if n_weights != n_nodes:
            raise RuntimeError(f"weight set {name} has {n_weights} != nNodes {n_nodes}")
        weights = list(struct.unpack_from(f"<{n_weights}f", buf, off))
        off += n_weights * 4
        sets.append({"name": name, "count": n_weights, "nonzero": sum(1 for w in weights if abs(w) > 1e-6)})
    return sets, off


def parse_child_models(buf: bytes, off: int, expected: int) -> tuple[list[str], int]:
    n_child = u32(buf, off)
    off += 4
    names = ["SELF"]
    if expected and n_child != expected:
        if n_child == 0 or n_child > 32:
            raise RuntimeError(f"nChildModels {n_child} at {off-4}")
    for _ in range(max(0, n_child - 1)):
        name, off = read_string(buf, off)
        names.append(name)
    return names, off


def parse_anim_node(buf: bytes, off: int, n_frames: int, compression: int) -> tuple[dict[str, Any], int]:
    if compression == 0:
        is_vertex = buf[off]
        off += 1
        if is_vertex:
            verts = []
            for _ in range(n_frames):
                count = u32(buf, off)
                off += 4
                off += count * 12
                verts.append(count)
            return {"kind": "vertex", "frames": verts}, off
        pos = [struct.unpack_from("<3f", buf, off + i * 12) for i in range(n_frames)]
        off += n_frames * 12
        quat = [struct.unpack_from("<4f", buf, off + i * 16) for i in range(n_frames)]
        off += n_frames * 16
        return {"kind": "full", "pos": pos, "quat": quat}, off
    if compression in (1, 2, 3):
        num_pos = u32(buf, off)
        off += 4
        pos_size = 6 if compression == 2 else 12
        off += num_pos * pos_size
        num_quat = u32(buf, off)
        off += 4
        quat_size = 8 if compression in (2, 3) else 16
        off += num_quat * quat_size
        return {"kind": ANCMPRS[compression], "pos": num_pos, "quat": num_quat}, off
    raise RuntimeError(f"unknown compression {compression}")


def parse_anims(buf: bytes, off: int, nodes: list[dict[str, Any]], expected_anims: int) -> tuple[list[dict[str, Any]], int]:
    n_anims = u32(buf, off)
    off += 4
    if expected_anims and n_anims != expected_anims:
        raise RuntimeError(f"nAnims {n_anims} != alloc {expected_anims} at {off-4}")
    order = dfs_nodes(nodes)
    clips = []
    for _ in range(n_anims):
        dims = list(struct.unpack_from("<3f", buf, off))
        off += 12
        name, off = read_string(buf, off)
        compression = u32(buf, off)
        interpolation_ms = u32(buf, off + 4)
        n_frames = u32(buf, off + 8)
        off += 12
        times = []
        strings = []
        for _frame in range(n_frames):
            times.append(u32(buf, off))
            off += 4
            label, off = read_string(buf, off)
            strings.append(label)
        node_tracks = []
        for node_index in order:
            track, off = parse_anim_node(buf, off, n_frames, compression)
            node_tracks.append({"node": node_index, "name": nodes[node_index]["name"], **track})
        duration_ms = max(times) if times else 0
        events = [
            {"frame": i, "time_ms": times[i], "label": strings[i]}
            for i, label in enumerate(strings)
            if label
        ]
        clips.append({
            "name": name,
            "dims": dims,
            "compression": compression,
            "compression_name": ANCMPRS.get(compression, str(compression)),
            "interpolation_ms": interpolation_ms,
            "n_keyframes": n_frames,
            "times_ms": times,
            "key_strings": strings,
            "events": events,
            "duration_ms": duration_ms,
            "fps": (1000.0 * (n_frames - 1) / duration_ms) if duration_ms else None,
            "vertex_nodes": sum(1 for t in node_tracks if t["kind"] == "vertex"),
            "full_nodes": sum(1 for t in node_tracks if t["kind"] == "full"),
            "tracks": node_tracks,
        })
    return clips, off


BONE_MAP = {
    "FvARM-bone L ForeArm": "v_weapon.Bip01_L_Forearm",
    "FvARM-bone L Hand": "v_weapon.Bip01_L_Hand",
    "FvARM-bone L Finger0": "v_weapon.Bip01_L_Finger0",
    "FvARM-bone L Finger01": "v_weapon.Bip01_L_Finger01",
    "FvARM-bone L Finger02": "v_weapon.Bip01_L_Finger02",
    "FvARM-bone L Finger1": "v_weapon.Bip01_L_Finger1",
    "FvARM-bone L Finger11": "v_weapon.Bip01_L_Finger11",
    "FvARM-bone L Finger12": "v_weapon.Bip01_L_Finger12",
    "FvARM-bone L Finger2": "v_weapon.Bip01_L_Finger2",
    "FvARM-bone L Finger21": "v_weapon.Bip01_L_Finger21",
    "FvARM-bone L Finger22": "v_weapon.Bip01_L_Finger22",
    "FvARM-bone L Finger3": "v_weapon.Bip01_L_Finger3",
    "FvARM-bone L Finger31": "v_weapon.Bip01_L_Finger31",
    "FvARM-bone L Finger32": "v_weapon.Bip01_L_Finger32",
    "FvARM-bone L Finger4": "v_weapon.Bip01_L_Finger4",
    "FvARM-bone L Finger41": "v_weapon.Bip01_L_Finger41",
    "FvARM-bone L Finger42": "v_weapon.Bip01_L_Finger42",
    "FvARM-bone L ForeTwist": "v_weapon.Bip01_L_ForeTwist",
    "FvARM-bone R ForeArm": "v_weapon.Bip01_R_Forearm",
    "FvARM-bone R Hand": "v_weapon.Bip01_R_Hand",
    "FvARM-bone R Finger0": "v_weapon.Bip01_R_Finger0",
    "FvARM-bone R Finger01": "v_weapon.Bip01_R_Finger01",
    "FvARM-bone R Finger02": "v_weapon.Bip01_R_Finger02",
    "FvARM-bone R Finger1": "v_weapon.Bip01_R_Finger1",
    "FvARM-bone R Finger11": "v_weapon.Bip01_R_Finger11",
    "FvARM-bone R Finger12": "v_weapon.Bip01_R_Finger12",
    "FvARM-bone R Finger2": "v_weapon.Bip01_R_Finger2",
    "FvARM-bone R Finger21": "v_weapon.Bip01_R_Finger21",
    "FvARM-bone R Finger22": "v_weapon.Bip01_R_Finger22",
    "FvARM-bone R Finger3": "v_weapon.Bip01_R_Finger3",
    "FvARM-bone R Finger31": "v_weapon.Bip01_R_Finger31",
    "FvARM-bone R Finger32": "v_weapon.Bip01_R_Finger32",
    "FvARM-bone R Finger4": "v_weapon.Bip01_R_Finger4",
    "FvARM-bone R Finger41": "v_weapon.Bip01_R_Finger41",
    "FvARM-bone R Finger42": "v_weapon.Bip01_R_Finger42",
    "FvARM-bone R ForeTwist": "v_weapon.Bip01_R_ForeTwist",
    "FvARM-bone Prop1": "v_weapon.M4A1_Parent",
}


def recover_pv_ltb() -> bytes:
    if PV_LTB.is_file():
        return PV_LTB.read_bytes()
    raise RuntimeError(f"P6 verified PV LTB missing: {PV_LTB}")


def clip_event_frame(clip: dict[str, Any], label: str) -> int | None:
    for event in clip.get("events") or []:
        if event["label"] == label:
            return int(event["frame"])
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def patch_sequence_fps_and_events(qc_text: str, name: str, fps: float, events: list[tuple[int, str]]) -> str:
    pattern = rf'(\$sequence\s+"{re.escape(name)}"\s*\{{)(.*?)(\n\}})'

    def repl(match: re.Match[str]) -> str:
        body = match.group(2)
        body = re.sub(r'\n\t\{ event 5004 \d+ "[^"]+" \}', "", body)
        body = re.sub(r'\n\tfps [0-9.]+', f"\n\tfps {fps:.6g}", body)
        event_block = "".join(f'\n\t{{ event 5004 {frame} "{sound}" }}' for frame, sound in events)
        # insert events after the smd path line
        body = re.sub(r'(activity[^\n]*\n)', r"\1" + event_block.lstrip("\n") + "\n", body, count=1)
        if "{ event 5004" not in body and event_block:
            body = body.replace("\n\tfadein", event_block + "\n\tfadein", 1)
        return match.group(1) + body + match.group(3)

    updated, count = re.subn(pattern, repl, qc_text, count=1, flags=re.I | re.S)
    if count != 1:
        raise RuntimeError(f"failed to patch sequence {name}")
    return updated


def write_cf_smd(
    dest: Path,
    nodes: list[dict[str, Any]],
    clip: dict[str, Any],
    rest_smd: Path,
) -> dict[str, Any]:
    """Write a CS-skeleton SMD with mapped CF locals copied onto matching bones."""
    rest_lines = rest_smd.read_text(encoding="utf-8", errors="replace").splitlines()
    node_lines: list[str] = []
    rest_pose: dict[int, tuple[float, ...]] = {}
    in_nodes = in_skel = False
    cs_names: list[str] = []
    for line in rest_lines:
        s = line.strip()
        if s == "nodes":
            in_nodes = True
            node_lines.append(line)
            continue
        if s == "end" and in_nodes:
            node_lines.append(line)
            in_nodes = False
            continue
        if in_nodes:
            node_lines.append(line)
            match = re.match(r'\s*(\d+)\s+"([^"]+)"\s+(-?\d+)', line)
            if match:
                cs_names.append(match.group(2))
            continue
        if s == "skeleton":
            in_skel = True
            continue
        if s == "end" and in_skel:
            break
        if in_skel and s.startswith("time"):
            continue
        if in_skel:
            parts = s.split()
            if parts and parts[0].isdigit():
                rest_pose[int(parts[0])] = tuple(float(v) for v in parts[1:7])
    cf_by_name = {track["name"]: track for track in clip["tracks"] if track["kind"] == "full"}
    extra = {}
    for cf_name, cs_name in list(BONE_MAP.items()):
        if cf_name in cf_by_name:
            extra[cs_name] = cf_name
    # mag / bolt guessed by travel on Box/Bone nodes
    gun_tracks = [
        track for track in clip["tracks"]
        if track["kind"] == "full" and track["name"].startswith(("Box", "Bone", "Dummy"))
    ]
    def travel(track: dict[str, Any]) -> float:
        pts = track["pos"]
        return math.sqrt(sum((pts[-1][i] - pts[0][i]) ** 2 for i in range(3)))
    gun_tracks.sort(key=travel, reverse=True)
    if gun_tracks:
        extra["v_weapon.M4A1_Clip"] = gun_tracks[0]["name"]
    if len(gun_tracks) > 1:
        extra["v_weapon.M4A1_Bolt"] = gun_tracks[1]["name"]
    n_frames = clip["n_keyframes"]
    out = ["version 1"] + node_lines + ["skeleton"]
    for frame in range(n_frames):
        out.append(f"  time {frame}")
        for bone_index, rest in rest_pose.items():
            name = cs_names[bone_index] if bone_index < len(cs_names) else ""
            cf_name = extra.get(name)
            if cf_name and cf_name in cf_by_name:
                pos = cf_by_name[cf_name]["pos"][frame]
                # CF X mirror to match P6 viewmodel
                values = (-pos[0], pos[1], pos[2], rest[3], rest[4], rest[5])
            else:
                values = rest
            out.append("    " + " ".join([str(bone_index)] + [f"{v:.6f}" for v in values]))
    out.append("end")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    return {"smd": str(dest).replace("\\", "/"), "frames": n_frames, "mapped": extra}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    body = recover_pv_ltb()
    header = parse_header(body)
    allocs = header["allocs"]
    nodes, after_skel = parse_skeleton(body, allocs["nNodes"])
    weight_sets, off = parse_weight_sets(body, after_skel, allocs["nNodes"], allocs["nWeightSets"])
    children, off = parse_child_models(body, off, allocs["nChildModels"])
    clips, off = parse_anims(body, off, nodes, allocs["nParentAnims"])
    report = {
        "schema": "cf2.p7.cf-animation-decode.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P7-S04",
        "result": "P7_CF_ANIM_CLIPS_DECODED" if clips else "P7_CF_ANIM_DECODE_FAILED",
        "source": {
            "path": str(PV_LTB).replace("\\", "/"),
            "bytes": len(body),
            "expected_sha256_compressed": EXPECTED_SHA,
        },
        "header": header,
        "skeleton": [{"index": n["index"], "name": n["name"], "parent": n["parent"], "children": n["children"]} for n in nodes],
        "after_skeleton": after_skel,
        "weight_sets": weight_sets,
        "child_models": children,
        "clips": [{k: v for k, v in clip.items() if k != "tracks"} for clip in clips],
        "stream_after_anims": off,
        "bytes_remaining": len(body) - off,
        "notes": [
            "Decoder follows Jupiter Model::Load after Scene Root. Mesh pieces are skipped by seeking to Scene Root.",
            "Not deployed. CS sequences and P7-S01 sound are unchanged.",
            "SOUND_RETIME_REQUIRED_ON_CF_ANIM still applies when these clips replace CS actions.",
        ],
    }
    rest_smd = REPO / "work" / "p5_leishen" / "p7_s02" / "source1" / "v_rif_m4a1_anims" / "idle.smd"
    smd_info: dict[str, Any] = {}
    if rest_smd.is_file():
        by_name = {clip["name"]: clip for clip in clips}
        anim_dir = OUT / "smd"
        for src, dst in (("reload", "reload"), ("select", "draw"), ("idle_0", "idle"), ("fire", "shoot1")):
            if src in by_name:
                smd_info[dst] = write_cf_smd(anim_dir / f"{dst}.smd", nodes, by_name[src], rest_smd)
    report["smd_preview"] = smd_info
    report["deployed"] = False
    (OUT / "execution.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# P7-S04 — CF original animation decode",
        "",
        f"Result: **{report['result']}**.",
        "",
        f"Nodes `{len(nodes)}`, clips `{len(clips)}`, weight sets `{len(weight_sets)}`.",
        "",
    ]
    for clip in clips:
        events = ", ".join(f"{e['label']}@{e['time_ms']}ms/f{e['frame']}" for e in clip.get("events") or [])
        lines.append(
            f"- `{clip['name']}`: {clip['n_keyframes']} keys, {clip['duration_ms']} ms, "
            f"{clip['compression_name']}, ~{clip['fps']:.1f} fps. {events}"
        )
    lines.extend(["", "Not a P4-M01 PASS. Frozen addon untouched.", ""])
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")
    print(json.dumps({
        "result": report["result"],
        "nodes": [n["name"] for n in nodes],
        "clips": [
            {
                "name": c["name"],
                "keys": c["n_keyframes"],
                "ms": c["duration_ms"],
                "comp": c["compression_name"],
                "strings": [s for s in c["key_strings"] if s],
                "events": c.get("events"),
            }
            for c in clips
        ],
        "remaining": report["bytes_remaining"],
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
