"""P7-S04 — decode CF PV LTB clips and wire them onto the live viewmodel.

Decoder walks Jupiter Model::Load after Scene Root. Wiring retargets CF
world-space motion (clip-relative, not bind-pose local copy) onto the P6
CS M4A4 skeleton, then retimes reload/draw events to CF labels.

Does not overwrite frozen, P7-S01 sound WAVs, world/dropped, or CS inspect.

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
from weapon_port.pipeline import mdl_header  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
GAME = Path(_paths.game_dir())
OUT = REPO / "work" / "p5_leishen" / "p7_s04"
P7S02 = REPO / "work" / "p5_leishen" / "p7_s02"
SOURCE1 = OUT / "source1"
ISOLATED = OUT / "isolated_game" / "csgo"
LOG_DIR = OUT / "logs"
PV_LTB = REPO / "work" / "p5_leishen" / "p6" / "verified_root" / "Models" / "PLAYERVIEW" / "PV-M4A1_S_Transformers.LTB"
C3_MANIFEST = REPO / "assets" / "weapons" / "m4a1_s_bornbeast" / "c3_alignment_m4a4_manifest.json"
EXPECTED_SHA = "a0ccef5deed745f1731eb93295c630f531123288055f3c3790531b99b6e401b8"
STUDIOMDL = GAME / "bin" / "studiomdl.exe"
ADDON_NAME = "p_cf_leishen_m4a4_p6"
FROZEN_NAME = "p_cf_bornbeast_m4a4_p4_frozen_noop_01"
SOUND_ADDON = "p_cf_leishen_m4a4_p7_sound"
MIGI_ADDONS = GAME / "migi" / "csgo" / "addons"
PARK = GAME / "migi" / "csgo" / "_parked_addons"
MODEL_REL = Path("models/weapons")
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
    "Bone06": "v_weapon.M4A1_Clip",
    "Bone04": "v_weapon.M4A1_Bolt",
}


def ident() -> list[list[float]]:
    return [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]


def mat_mul(a: list[list[float]], b: list[list[float]]) -> list[list[float]]:
    out = [[0.0] * 4 for _ in range(4)]
    for i in range(4):
        for j in range(4):
            out[i][j] = a[i][0] * b[0][j] + a[i][1] * b[1][j] + a[i][2] * b[2][j] + a[i][3] * b[3][j]
    return out


def mat_inv(m: list[list[float]]) -> list[list[float]]:
    n = [row[:] for row in m]
    inv = ident()
    for i in range(4):
        pivot = i
        for r in range(i + 1, 4):
            if abs(n[r][i]) > abs(n[pivot][i]):
                pivot = r
        n[i], n[pivot] = n[pivot], n[i]
        inv[i], inv[pivot] = inv[pivot], inv[i]
        div = n[i][i]
        if abs(div) < 1e-12:
            raise RuntimeError("singular matrix")
        for j in range(4):
            n[i][j] /= div
            inv[i][j] /= div
        for r in range(4):
            if r == i:
                continue
            factor = n[r][i]
            for j in range(4):
                n[r][j] -= factor * n[i][j]
                inv[r][j] -= factor * inv[i][j]
    return inv


def trans_of(m: list[list[float]]) -> tuple[float, float, float]:
    return (m[0][3], m[1][3], m[2][3])


def quat_xyzw_matrix(q: tuple[float, ...]) -> list[list[float]]:
    x, y, z, w = q
    xx, yy, zz = x * x, y * y, z * z
    xy, xz, yz = x * y, x * z, y * z
    wx, wy, wz = w * x, w * y, w * z
    return [
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy), 0.0],
        [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx), 0.0],
        [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def local_from_pos_quat(pos: tuple[float, ...], quat: tuple[float, ...]) -> list[list[float]]:
    matrix = quat_xyzw_matrix(quat)
    matrix[0][3], matrix[1][3], matrix[2][3] = pos
    return matrix


def euler_xyz_to_mat(rx: float, ry: float, rz: float) -> list[list[float]]:
    cx, sx = math.cos(rx), math.sin(rx)
    cy, sy = math.cos(ry), math.sin(ry)
    cz, sz = math.cos(rz), math.sin(rz)
    return [
        [cy * cz, sx * sy * cz - cx * sz, cx * sy * cz + sx * sz, 0.0],
        [cy * sz, sx * sy * sz + cx * cz, cx * sy * sz - sx * cz, 0.0],
        [-sy, sx * cy, cx * cy, 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def local_from_pos_euler(pos: tuple[float, ...], eul: tuple[float, float, float]) -> list[list[float]]:
    matrix = euler_xyz_to_mat(eul[0], eul[1], eul[2])
    matrix[0][3], matrix[1][3], matrix[2][3] = pos
    return matrix


def mat_to_euler_xyz(m: list[list[float]]) -> tuple[float, float, float]:
    sy = -m[2][0]
    cy = math.sqrt(max(0.0, 1.0 - sy * sy))
    if cy > 1e-6:
        rx = math.atan2(m[2][1], m[2][2])
        ry = math.asin(max(-1.0, min(1.0, sy)))
        rz = math.atan2(m[1][0], m[0][0])
    else:
        rx = math.atan2(-m[0][1], m[1][1])
        ry = math.asin(max(-1.0, min(1.0, sy)))
        rz = 0.0
    return (rx, ry, rz)


def unwrap_euler(eul: tuple[float, float, float], ref: tuple[float, float, float]) -> tuple[float, float, float]:
    out = []
    for i in range(3):
        delta = eul[i] - ref[i]
        delta = (delta + math.pi) % (2.0 * math.pi) - math.pi
        out.append(ref[i] + delta)
    return (out[0], out[1], out[2])


def load_c3_mirror() -> list[list[float]]:
    c3 = json.loads(C3_MANIFEST.read_text(encoding="utf-8"))["matrix_cf_to_source"]
    mirror = ident()
    mirror[0][0] = -1.0
    return mat_mul(mirror, c3)


def parse_smd_skeleton(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    node_lines: list[str] = []
    names: list[str] = []
    parents: list[int] = []
    rest: dict[int, tuple[float, ...]] = {}
    in_nodes = in_skel = False
    for line in lines:
        stripped = line.strip()
        if stripped == "nodes":
            in_nodes = True
            node_lines.append(line)
            continue
        if stripped == "end" and in_nodes:
            node_lines.append(line)
            in_nodes = False
            continue
        if in_nodes:
            node_lines.append(line)
            match = re.match(r'\s*(\d+)\s+"([^"]+)"\s+(-?\d+)', line)
            if not match:
                raise RuntimeError(f"bad SMD node: {line}")
            names.append(match.group(2))
            parents.append(int(match.group(3)))
            continue
        if stripped == "skeleton":
            in_skel = True
            continue
        if stripped == "end" and in_skel:
            break
        if in_skel and stripped.startswith("time"):
            continue
        if in_skel:
            parts = stripped.split()
            rest[int(parts[0])] = tuple(float(v) for v in parts[1:7])
    rest_local = []
    for index in range(len(names)):
        pose = rest[index]
        rest_local.append(local_from_pos_euler(pose[:3], pose[3:6]))
    rest_world = [ident() for _ in names]
    for index, parent in enumerate(parents):
        rest_world[index] = rest_local[index] if parent < 0 else mat_mul(rest_world[parent], rest_local[index])
    return {
        "node_lines": node_lines,
        "names": names,
        "parents": parents,
        "rest": rest,
        "rest_local": rest_local,
        "rest_world": rest_world,
    }


def cf_worlds(nodes: list[dict[str, Any]], clip: dict[str, Any], frame: int) -> list[list[list[float]]]:
    tracks = {track["node"]: track for track in clip["tracks"] if track["kind"] == "full"}
    worlds: list[list[list[float]] | None] = [None] * len(nodes)
    for index in dfs_nodes(nodes):
        track = tracks.get(index)
        parent = nodes[index]["parent"]
        if track is None:
            local = ident()
        else:
            local = local_from_pos_quat(track["pos"][frame], track["quat"][frame])
        worlds[index] = local if parent < 0 else mat_mul(worlds[parent], local)
    return worlds  # type: ignore[return-value]


def cs_topo(parents: list[int]) -> list[int]:
    children: list[list[int]] = [[] for _ in parents]
    roots: list[int] = []
    for index, parent in enumerate(parents):
        if parent < 0:
            roots.append(index)
        else:
            children[parent].append(index)
    order: list[int] = []

    def walk(index: int) -> None:
        order.append(index)
        for child in children[index]:
            walk(child)

    for root in roots:
        walk(root)
    if len(order) != len(parents):
        raise RuntimeError("CS skeleton topo incomplete")
    return order


def retarget_clip(
    nodes: list[dict[str, Any]],
    clip: dict[str, Any],
    smd: dict[str, Any],
    transform: list[list[float]],
) -> list[list[tuple[float, ...]]]:
    cf_name_to_index = {node["name"]: node["index"] for node in nodes}
    cs_name_to_index = {name: i for i, name in enumerate(smd["names"])}
    mapped: dict[int, int] = {}
    for cf_name, cs_name in BONE_MAP.items():
        if cf_name not in cf_name_to_index or cs_name not in cs_name_to_index:
            raise RuntimeError(f"missing bone map {cf_name} -> {cs_name}")
        mapped[cs_name_to_index[cs_name]] = cf_name_to_index[cf_name]
    inv_t = mat_inv(transform)
    n_frames = clip["n_keyframes"]
    cf0 = cf_worlds(nodes, clip, 0)
    inv_cf0 = [mat_inv(world) for world in cf0]
    topo = cs_topo(smd["parents"])
    frames: list[list[tuple[float, ...]]] = []
    prev_eul = {i: smd["rest"][i][3:6] for i in range(len(smd["names"]))}
    for frame in range(n_frames):
        cf_w = cf_worlds(nodes, clip, frame)
        cs_w: list[list[list[float]] | None] = [None] * len(smd["names"])
        pose: list[tuple[float, ...] | None] = [None] * len(smd["names"])
        for index in topo:
            parent = smd["parents"][index]
            if index in mapped:
                cf_index = mapped[index]
                delta = mat_mul(cf_w[cf_index], inv_cf0[cf_index])
                world = mat_mul(mat_mul(mat_mul(transform, delta), inv_t), smd["rest_world"][index])
            elif parent < 0:
                world = smd["rest_world"][index]
            else:
                world = mat_mul(cs_w[parent], smd["rest_local"][index])
            cs_w[index] = world
            parent_world = ident() if parent < 0 else cs_w[parent]
            local = mat_mul(mat_inv(parent_world), world)
            eul = unwrap_euler(mat_to_euler_xyz(local), prev_eul[index])
            prev_eul[index] = eul
            pose[index] = (*trans_of(local), *eul)
        frames.append(pose)  # type: ignore[arg-type]
    return frames


def write_retargeted_smd(dest: Path, smd: dict[str, Any], frames: list[list[tuple[float, ...]]]) -> dict[str, Any]:
    out = ["version 1"] + smd["node_lines"] + ["skeleton"]
    for frame, pose in enumerate(frames):
        out.append(f"  time {frame}")
        for index, values in enumerate(pose):
            out.append("    " + " ".join([str(index)] + [f"{v:.6f}" for v in values]))
    out.append("end")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(out) + "\n", encoding="utf-8")
    mag = None
    parent = None
    names = smd["names"]
    try:
        clip_i = names.index("v_weapon.M4A1_Clip")
        parent_i = names.index("v_weapon.M4A1_Parent")
        mag = max(
            math.sqrt(sum((frames[f][clip_i][k] - frames[0][clip_i][k]) ** 2 for k in range(3)))
            for f in range(len(frames))
        )
        parent = max(
            math.sqrt(sum((frames[f][parent_i][k] - frames[0][parent_i][k]) ** 2 for k in range(3)))
            for f in range(len(frames))
        )
    except ValueError:
        pass
    return {"smd": str(dest).replace("\\", "/"), "frames": len(frames), "clip_travel": mag, "parent_travel": parent}


def replace_sequence(qc_text: str, name: str, block: str) -> str:
    pattern = re.compile(rf'\$sequence\s+"{re.escape(name)}"\s*\{{.*?\n\}}', flags=re.IGNORECASE | re.DOTALL)
    updated, count = pattern.subn(lambda _match, text=block: text, qc_text, count=1)
    if count != 1:
        raise RuntimeError(f"failed to replace QC sequence {name}")
    return updated


def sequence_block(name: str, smd: str, fps: float, extra_lines: list[str]) -> str:
    body = "\n".join(["\t" + line for line in extra_lines])
    extra = ("\n" + body) if extra_lines else ""
    return (
        f'$sequence "{name}" {{\n'
        f'\t"{smd}"{extra}\n'
        f"\tfadein 0.2\n"
        f"\tfadeout 0.2\n"
        f"\tsnap\n"
        f"\tfps {fps:.6g}\n"
        f"}}"
    )


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


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def patch_qc(qc_text: str, clips: dict[str, dict[str, Any]]) -> str:
    reload = clips["reload"]
    select = clips["select"]
    idle = clips["idle_0"]
    fire = clips["fire"]
    clipout = clip_event_frame(reload, "WeaponClipOut")
    clipin = clip_event_frame(reload, "WeaponClipIn")
    cliphit = clip_event_frame(reload, "WeaponReload")
    boltback = clip_event_frame(select, "WeaponReload")
    if None in (clipout, clipin, cliphit, boltback):
        raise RuntimeError(f"missing CF labels: {reload.get('events')} {select.get('events')}")
    sequences = {
        "idle": sequence_block(
            "idle",
            r"v_rif_m4a1_anims\idle.smd",
            idle["fps"],
            ['activity "ACT_VM_IDLE" 1'],
        ),
        "shoot1": sequence_block(
            "shoot1",
            r"v_rif_m4a1_anims\shoot1.smd",
            fire["fps"],
            ['activity "ACT_VM_PRIMARYATTACK" 1', '{ event 5001 0 "1" }', '{ event AE_CLIENT_EJECT_BRASS 0 "" }'],
        ),
        "shoot2": sequence_block(
            "shoot2",
            r"v_rif_m4a1_anims\shoot2.smd",
            fire["fps"],
            ['activity "ACT_VM_PRIMARYATTACK" 1', '{ event 5001 0 "1" }', '{ event AE_CLIENT_EJECT_BRASS 0 "" }'],
        ),
        "shoot3": sequence_block(
            "shoot3",
            r"v_rif_m4a1_anims\shoot3.smd",
            fire["fps"],
            ['activity "ACT_VM_PRIMARYATTACK" 1', '{ event 5001 0 "1" }', '{ event AE_CLIENT_EJECT_BRASS 0 "" }'],
        ),
        "reload": sequence_block(
            "reload",
            r"v_rif_m4a1_anims\reload.smd",
            reload["fps"],
            [
                'activity "ACT_VM_RELOAD" 5',
                f'{{ event 5004 {clipout} "Weapon_M4A1.Clipout" }}',
                f'{{ event 5004 {clipin} "Weapon_M4A1.Clipin" }}',
                f'{{ event 5004 {cliphit} "Weapon_M4A1.ClipHit" }}',
                f'{{ event AE_WPN_COMPLETE_RELOAD {clipin} "" }}',
            ],
        ),
        "draw": sequence_block(
            "draw",
            r"v_rif_m4a1_anims\draw.smd",
            select["fps"],
            [
                'activity "ACT_VM_DRAW" 1',
                '{ event 5004 0 "Weapon_M4A1.Draw" }',
                f'{{ event 5004 {boltback} "Weapon_M4A1.BoltBack" }}',
            ],
        ),
    }
    for name, block in sequences.items():
        qc_text = replace_sequence(qc_text, name, block)
    return qc_text


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    if not STUDIOMDL.is_file():
        raise RuntimeError(f"studiomdl missing: {STUDIOMDL}")
    frozen_live = MIGI_ADDONS / FROZEN_NAME
    if frozen_live.exists():
        raise RuntimeError("frozen addon is in MIGI addons; refuse to compile a second v_rif_m4a1")
    live = MIGI_ADDONS / ADDON_NAME
    if not live.exists():
        raise RuntimeError("P6 live addon missing")
    rest_smd = P7S02 / "source1" / "v_rif_m4a1_anims" / "idle.smd"
    if not rest_smd.is_file():
        raise RuntimeError("P7-S02 idle.smd missing")

    body = recover_pv_ltb()
    header = parse_header(body)
    allocs = header["allocs"]
    nodes, after_skel = parse_skeleton(body, allocs["nNodes"])
    weight_sets, off = parse_weight_sets(body, after_skel, allocs["nNodes"], allocs["nWeightSets"])
    children, off = parse_child_models(body, off, allocs["nChildModels"])
    clips, off = parse_anims(body, off, nodes, allocs["nParentAnims"])
    by_name = {clip["name"]: clip for clip in clips}
    for required in ("reload", "select", "idle_0", "fire"):
        if required not in by_name:
            raise RuntimeError(f"missing CF clip {required}: {list(by_name)}")

    transform = load_c3_mirror()
    smd = parse_smd_skeleton(rest_smd)
    roundtrip = unwrap_euler(mat_to_euler_xyz(smd["rest_local"][0]), smd["rest"][0][3:6])
    if max(abs(roundtrip[i] - smd["rest"][0][3 + i]) for i in range(3)) > 1e-4:
        raise RuntimeError(f"SMD euler convention roundtrip failed: {roundtrip} vs {smd['rest'][0][3:6]}")

    for path in (SOURCE1, ISOLATED, LOG_DIR, OUT / "smd"):
        if path.exists():
            shutil.rmtree(path)
        path.mkdir(parents=True, exist_ok=True)
    shutil.copytree(P7S02 / "source1", SOURCE1, dirs_exist_ok=True)
    shutil.copytree(P7S02 / "isolated_game" / "csgo", ISOLATED, dirs_exist_ok=True)

    anim_dir = SOURCE1 / "v_rif_m4a1_anims"
    smd_info: dict[str, Any] = {}
    mapping = {
        "reload": ("reload", "reload.smd"),
        "select": ("draw", "draw.smd"),
        "idle_0": ("idle", "idle.smd"),
        "fire": ("shoot1", "shoot1.smd"),
    }
    for cf_name, (dst, filename) in mapping.items():
        frames = retarget_clip(nodes, by_name[cf_name], smd, transform)
        smd_info[dst] = write_retargeted_smd(anim_dir / filename, smd, frames)
        smd_info[dst]["cf_clip"] = cf_name
        smd_info[dst]["fps"] = by_name[cf_name]["fps"]
    shutil.copy2(anim_dir / "shoot1.smd", anim_dir / "shoot2.smd")
    shutil.copy2(anim_dir / "shoot1.smd", anim_dir / "shoot3.smd")
    shutil.copy2(anim_dir / "reload.smd", OUT / "smd" / "reload.smd")
    shutil.copy2(anim_dir / "draw.smd", OUT / "smd" / "draw.smd")
    shutil.copy2(anim_dir / "idle.smd", OUT / "smd" / "idle.smd")
    shutil.copy2(anim_dir / "shoot1.smd", OUT / "smd" / "shoot1.smd")

    qc_path = SOURCE1 / "v_rif_m4a1.qc"
    original = qc_path.read_text(encoding="utf-8", errors="replace")
    if "lookat01.smd" not in original:
        raise RuntimeError("expected P7-S02 QC with official lookat clips")
    qc_path.write_text(patch_qc(original, by_name), encoding="utf-8")

    compiled = ISOLATED / "models" / "weapons" / "v_rif_m4a1.mdl"
    proc = subprocess.run(
        [str(STUDIOMDL), "-game", str(ISOLATED), str(qc_path)],
        cwd=str(SOURCE1),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=300,
    )
    (LOG_DIR / "studiomdl.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "studiomdl.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0 or not compiled.is_file():
        raise RuntimeError(
            f"studiomdl failed ({proc.returncode}): {(proc.stderr or proc.stdout or '')[-1200:]}"
        )
    header_mdl = mdl_header(compiled)
    if header_mdl["bone_count"] != 57:
        raise RuntimeError(f"compiled bone_count {header_mdl['bone_count']} != 57")
    if header_mdl["internal_name"].replace("\\", "/") != "weapons/v_rif_m4a1.mdl":
        raise RuntimeError(f"internal model name mismatch: {header_mdl['internal_name']}")

    models_dir = live / MODEL_REL
    deployed: dict[str, str] = {}
    for path in (ISOLATED / "models" / "weapons").glob("v_rif_m4a1.*"):
        dest = models_dir / path.name
        shutil.copy2(path, dest)
        deployed[path.name] = sha256_file(dest)
    world_untouched = sorted(
        p.name for p in models_dir.glob("w_rif_m4a1*") if p.is_file()
    )

    reload = by_name["reload"]
    select = by_name["select"]
    report = {
        "schema": "cf2.p7.cf-animation-wire.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P7-S04",
        "result": "P7_CF_ANIM_VIEWMODEL_DEPLOYED",
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
        "retarget": {
            "method": "world_space_clip_relative",
            "transform": "C3 then Source X mirror through 0",
            "bone_map": BONE_MAP,
            "rest": "P7-S02 idle.smd time 0; each clip frame 0 stays on that rest",
            "mag_bone": "Bone06",
            "bolt_bone": "Bone04",
            "smd": smd_info,
        },
        "events": {
            "reload": {
                "fps": reload["fps"],
                "clipout": clip_event_frame(reload, "WeaponClipOut"),
                "clipin": clip_event_frame(reload, "WeaponClipIn"),
                "cliphit": clip_event_frame(reload, "WeaponReload"),
            },
            "draw": {
                "fps": select["fps"],
                "boltback": clip_event_frame(select, "WeaponReload"),
            },
        },
        "mdl_header": header_mdl,
        "addon_name": ADDON_NAME,
        "deployed_models": deployed,
        "world_files_present": world_untouched,
        "frozen_untouched": (PARK / FROZEN_NAME).exists() and not frozen_live.exists(),
        "sound_addon_untouched": (MIGI_ADDONS / SOUND_ADDON).exists(),
        "inspect_untouched": True,
        "notes": [
            "CF reload/select/idle/fire wired onto the P6 CS skeleton.",
            "P7-S01 WAV files unchanged; QC event frames now follow CF labels.",
            "CS lookat inspect kept. World/dropped kept. Frozen addon not modified.",
            "Not a P4-M01 PASS.",
        ],
    }
    (OUT / "execution.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    event_lines = []
    for clip in clips:
        events = ", ".join(f"{e['label']}@{e['time_ms']}ms/f{e['frame']}" for e in clip.get("events") or [])
        event_lines.append(
            f"- `{clip['name']}`: {clip['n_keyframes']} keys, {clip['duration_ms']} ms, "
            f"{clip['compression_name']}, ~{clip['fps']:.1f} fps. {events}"
        )
    (OUT / "report.md").write_text(
        "\n".join(
            [
                "# P7-S04 — CF original animation on the viewmodel",
                "",
                "Result: **P7_CF_ANIM_VIEWMODEL_DEPLOYED**.",
                "",
                "Reload / 切枪 / idle / fire use CF PV LTB clips retargeted in world space onto the P6 CS M4A4 skeleton. Sound QC events follow CF labels (`WeaponClipOut` / `ClipIn` / `WeaponReload`). P7-S01 WAV files are unchanged.",
                "",
                *event_lines,
                "",
                f"- reload Clipout@f{report['events']['reload']['clipout']} Clipin@f{report['events']['reload']['clipin']} ClipHit@f{report['events']['reload']['cliphit']} fps `{reload['fps']:.3f}`",
                f"- draw BoltBack@f{report['events']['draw']['boltback']} fps `{select['fps']:.3f}`",
                "- mag bone `Bone06`, bolt bone `Bone04`, gun root `FvARM-bone Prop1`",
                "- inspect stays official CS lookat; world/dropped untouched; frozen untouched",
                "",
                "Not a P4-M01 PASS.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({
        "result": report["result"],
        "addon": ADDON_NAME,
        "events": report["events"],
        "deployed": deployed,
        "out": rel(OUT),
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
