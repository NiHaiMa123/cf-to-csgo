"""Generate isolated M1/M2 material-only experiment addons from a frozen baseline.

These are single-factor ablations, not a final visual fix.
FOV, position, animation, and hands remain unchanged.

CLI:
  python build_experiments.py --baseline <frozen addon dir> --out <empty dir>
  python build_experiments.py --baseline DIR --out DIR --dry-run
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import sys
from pathlib import Path

CHUNK = 1024 * 1024
FIX_ROOT = Path(__file__).resolve().parent
MAT_REL = "materials/models/weapons/v_models/cf_mauser"
R0 = f"{MAT_REL}/cf_mauser_libra_r0.vmt"
R1 = f"{MAT_REL}/cf_mauser_libra_r1.vmt"
R2 = f"{MAT_REL}/cf_mauser_libra_r2.vmt"
R3 = f"{MAT_REL}/cf_mauser_libra_r3.vmt"
R4 = f"{MAT_REL}/cf_mauser_libra_r4.vmt"
R5 = f"{MAT_REL}/cf_mauser_libra_r5.vmt"
M4_EXPONENT = "48"
M4B_BOOST_MUL = 2.0
KNOWN_IDS = (
    "M1_r5_phong", "M2_env_off", "M6_r1_env_unmask",
    "M4_phong_exponent", "M4b_phong_boost", "M6_r1_phong_unmask",
)
PHONG_KEYS = (
    "$phong",
    "$basemapalphaphongmask",
    "$phongexponent",
    "$phongboost",
    "$phongfresnelranges",
    "$phongtint",
)
ENV_KEYS = ("$envmap", "$normalmapalphaenvmapmask", "$envmaptint")
LINE_RE = re.compile(r'^"([^"]+)"\s+"([^"]*)"$')
SHADER_RE = re.compile(r'^"([^"]+)"$')


def fail(message: str) -> None:
    raise RuntimeError(message)


def safe(path: Path) -> Path:
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        if part.exists() or part.is_symlink():
            s = part.lstat()
            if stat.S_ISLNK(s.st_mode) or getattr(s, "st_file_attributes", 0) & 0x400:
                fail(f"Link/reparse point rejected: {part}")
    return path


def require_under(path: Path, root: Path) -> Path:
    path = safe(path)
    root = safe(root)
    if path != root and root not in path.parents:
        fail(f"Path escapes root: {path}")
    return path


def digest(path: Path) -> dict:
    path = safe(path)
    s = path.stat()
    if not stat.S_ISREG(s.st_mode):
        fail(f"Not a regular file: {path}")
    h = hashlib.sha256()
    with path.open("rb") as f:
        while block := f.read(CHUNK):
            h.update(block)
    return {"bytes": s.st_size, "sha256": h.hexdigest()}


def inventory(root: Path) -> dict[str, dict]:
    root = safe(root)
    if not root.is_dir():
        fail(f"Missing directory: {root}")
    result: dict[str, dict] = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            safe(Path(base) / name)
        for name in sorted(files):
            p = Path(base) / name
            rel = p.relative_to(root).as_posix()
            if rel.lower() in {k.lower() for k in result}:
                fail(f"Case collision: {rel}")
            if any(part in ("", ".", "..") for part in rel.split("/")):
                fail(f"Unsafe relative path: {rel}")
            result[rel] = digest(p)
    return result


def parse_vmt(text: str) -> tuple[str, list[tuple[str, str]]]:
    if text.startswith("\ufeff"):
        fail("VMT BOM is not allowed")
    if "\r" in text:
        fail("VMT CR/CRLF is not allowed")
    if "\t" not in text and "\n{" in text:
        fail("Expected tab-indented VMT keys")
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines = lines[:-1]
    if len(lines) < 3:
        fail("VMT too short")
    shader_m = SHADER_RE.fullmatch(lines[0])
    if not shader_m:
        fail(f"Unexpected shader line: {lines[0]!r}")
    shader = shader_m.group(1)
    if shader != "VertexLitGeneric":
        fail(f"Unexpected shader: {shader}")
    if lines[1] != "{":
        fail("Expected opening brace")
    if lines[-1] != "}":
        fail("Expected closing brace")
    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    for line in lines[2:-1]:
        if line == "":
            fail("Empty line inside VMT")
        if not line.startswith("\t"):
            fail(f"Expected tab indent: {line!r}")
        m = LINE_RE.fullmatch(line[1:])
        if not m:
            fail(f"Unexpected VMT line: {line!r}")
        key, value = m.group(1), m.group(2)
        if not key.startswith("$"):
            fail(f"Non-parameter key: {key}")
        if key in seen:
            fail(f"Duplicate VMT key: {key}")
        seen.add(key)
        items.append((key, value))
    if not items:
        fail("VMT has no parameters")
    return shader, items


def format_vmt(shader: str, items: list[tuple[str, str]]) -> str:
    lines = [f'"{shader}"', "{"]
    for key, value in items:
        lines.append(f'\t"{key}" "{value}"')
    lines.append("}")
    return "\n".join(lines) + "\n"


def as_map(items: list[tuple[str, str]]) -> dict[str, str]:
    return dict(items)


def param_diff(before: list[tuple[str, str]], after: list[tuple[str, str]]) -> dict:
    b, a = as_map(before), as_map(after)
    return {
        "removed": {k: b[k] for k in b if k not in a},
        "added": {k: a[k] for k in a if k not in b},
        "changed": {k: [b[k], a[k]] for k in a if k in b and a[k] != b[k]},
        "order_after": [k for k, _ in after],
    }


def require_keys(items: list[tuple[str, str]], keys: tuple[str, ...], label: str) -> None:
    have = as_map(items)
    missing = [k for k in keys if k not in have]
    if missing:
        fail(f"{label} missing keys: {missing}")


def load_vmt(root: Path, rel: str) -> tuple[str, str, list[tuple[str, str]]]:
    path = require_under(root / Path(*rel.split("/")), root)
    text = path.read_text(encoding="ascii")
    shader, items = parse_vmt(text)
    if format_vmt(shader, items) != text:
        fail(f"VMT is not in the canonical format: {rel}")
    return text, shader, items


def m1_r5_phong(r0: list[tuple[str, str]], r5: list[tuple[str, str]]) -> list[tuple[str, str]]:
    r0m, r5m = as_map(r0), as_map(r5)
    require_keys(r0, PHONG_KEYS, "r0")
    if r5m.get("$phong") != "0":
        fail(f"r5 $phong must be 0, got {r5m.get('$phong')!r}")
    extra = [k for k in PHONG_KEYS[1:] if k in r5m]
    if extra:
        fail(f"r5 already has Phong keys: {extra}")
    if r0m["$phong"] != "1":
        fail(f"r0 $phong must be 1, got {r0m['$phong']!r}")
    out: list[tuple[str, str]] = []
    inserted = False
    for key, value in r5:
        if key == "$phong":
            for pk in PHONG_KEYS:
                out.append((pk, r0m[pk]))
            inserted = True
            continue
        out.append((key, value))
    if not inserted:
        fail("r5 $phong key not found")
    if any(k in as_map(out) for k in ENV_KEYS):
        fail("M1 must not add envmap keys")
    return out


def m2_env_off(items: list[tuple[str, str]], label: str) -> list[tuple[str, str]]:
    require_keys(items, ENV_KEYS, label)
    out = [(k, v) for k, v in items if k not in ENV_KEYS]
    if len(out) != len(items) - len(ENV_KEYS):
        fail(f"{label} env key count mismatch")
    remain = as_map(out)
    if any(k in remain for k in ENV_KEYS):
        fail(f"{label} still has envmap keys")
    if remain.get("$phong") != "1":
        fail(f"{label} must keep Phong enabled")
    return out


def assert_m1_diff(diff: dict) -> None:
    if diff["changed"] != {"$phong": ["0", "1"]}:
        fail(f"M1 unexpected changed keys: {diff['changed']}")
    if diff["removed"]:
        fail(f"M1 must not remove keys: {diff['removed']}")
    if set(diff["added"]) != set(PHONG_KEYS[1:]):
        fail(f"M1 unexpected added keys: {diff['added']}")


def assert_m2_diff(diff: dict, label: str) -> None:
    if set(diff["removed"]) != set(ENV_KEYS):
        fail(f"{label} unexpected removed keys: {diff['removed']}")
    if diff["added"] or diff["changed"]:
        fail(f"{label} must only remove envmap keys: {diff}")


def m6_r1_env_unmask(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    require_keys(items, ENV_KEYS, "r1")
    out = [(k, v) for k, v in items if k != "$normalmapalphaenvmapmask"]
    remain = as_map(out)
    if remain.get("$envmap") != "env_cubemap":
        fail("M6 must keep $envmap env_cubemap")
    if "$envmaptint" not in remain:
        fail("M6 must keep $envmaptint")
    if "$normalmapalphaenvmapmask" in remain:
        fail("M6 failed to remove envmap mask")
    if remain.get("$phong") != "1":
        fail("M6 must keep Phong enabled")
    return out


def assert_m6_diff(diff: dict) -> None:
    if diff["removed"] != {"$normalmapalphaenvmapmask": "1"}:
        fail(f"M6 unexpected removed keys: {diff['removed']}")
    if diff["added"] or diff["changed"]:
        fail(f"M6 must only remove the envmap mask: {diff}")


def m6_r1_phong_unmask(items: list[tuple[str, str]]) -> list[tuple[str, str]]:
    require_keys(items, ("$phong", "$basemapalphaphongmask", "$phongboost", "$phongexponent"), "r1")
    have = as_map(items)
    if have["$phong"] != "1":
        fail("M6 phong-unmask requires $phong 1")
    if have["$basemapalphaphongmask"] != "1":
        fail("M6 phong-unmask requires $basemapalphaphongmask 1")
    out = [(k, v) for k, v in items if k != "$basemapalphaphongmask"]
    remain = as_map(out)
    if "$basemapalphaphongmask" in remain:
        fail("M6 phong-unmask failed to remove the phong mask")
    if remain["$phong"] != "1" or remain["$phongboost"] != have["$phongboost"]:
        fail("M6 phong-unmask must keep Phong energy")
    return out


def assert_m6_phong_unmask_diff(diff: dict) -> None:
    if diff["removed"] != {"$basemapalphaphongmask": "1"}:
        fail(f"M6 phong-unmask unexpected removed keys: {diff['removed']}")
    if diff["added"] or diff["changed"]:
        fail(f"M6 phong-unmask must only remove the phong mask: {diff}")


def m4_set_exponent(items: list[tuple[str, str]], label: str) -> list[tuple[str, str]]:
    require_keys(items, ("$phong", "$phongexponent", "$phongboost", "$phongtint"), label)
    have = as_map(items)
    if have["$phong"] != "1":
        fail(f"{label} must already have Phong enabled")
    if have["$phongexponent"] != "4":
        fail(f"{label} $phongexponent must be 4, got {have['$phongexponent']!r}")
    out = [(k, M4_EXPONENT if k == "$phongexponent" else v) for k, v in items]
    if as_map(out)["$phongboost"] != have["$phongboost"]:
        fail(f"{label} M4 must not change boost")
    if as_map(out)["$phongtint"] != have["$phongtint"]:
        fail(f"{label} M4 must not change tint")
    return out


def assert_m4_diff(diff: dict, label: str) -> None:
    if diff["changed"] != {"$phongexponent": ["4", M4_EXPONENT]}:
        fail(f"{label} unexpected changed keys: {diff['changed']}")
    if diff["added"] or diff["removed"]:
        fail(f"{label} must only change exponent: {diff}")


def fmt_boost(value: float) -> str:
    return f"{value:.3g}"


def m4b_set_boost(items: list[tuple[str, str]], label: str) -> list[tuple[str, str]]:
    require_keys(items, ("$phong", "$phongexponent", "$phongboost", "$phongtint"), label)
    have = as_map(items)
    if have["$phong"] != "1":
        fail(f"{label} must already have Phong enabled")
    if have["$phongexponent"] != M4_EXPONENT:
        fail(f"{label} M4b parent must have $phongexponent {M4_EXPONENT}")
    old = float(have["$phongboost"])
    new = fmt_boost(old * M4B_BOOST_MUL)
    if new == have["$phongboost"]:
        fail(f"{label} boost did not change")
    out = [(k, new if k == "$phongboost" else v) for k, v in items]
    if as_map(out)["$phongexponent"] != M4_EXPONENT:
        fail(f"{label} M4b must not change exponent")
    if as_map(out)["$phongtint"] != have["$phongtint"]:
        fail(f"{label} M4b must not change tint")
    return out


def assert_m4b_diff(diff: dict, before: list[tuple[str, str]], after: list[tuple[str, str]],
                    label: str) -> None:
    old = as_map(before)["$phongboost"]
    new = as_map(after)["$phongboost"]
    if diff["changed"] != {"$phongboost": [old, new]}:
        fail(f"{label} unexpected changed keys: {diff['changed']}")
    if diff["added"] or diff["removed"]:
        fail(f"{label} must only change boost: {diff}")


def copy_tree(src: Path, dst: Path) -> None:
    src = safe(src)
    dst = safe(dst)
    inv = inventory(src)
    for rel in inv:
        s = require_under(src / Path(*rel.split("/")), src)
        d = require_under(dst / Path(*rel.split("/")), dst)
        d.parent.mkdir(parents=True, exist_ok=True)
        data = s.read_bytes()
        if len(data) != inv[rel]["bytes"]:
            fail(f"Size changed while copying: {rel}")
        d.write_bytes(data)
        if hashlib.sha256(data).hexdigest() != inv[rel]["sha256"]:
            fail(f"Hash changed while copying: {rel}")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("ascii"))


def require_empty(path: Path) -> Path:
    path = safe(path)
    if path.exists():
        if not path.is_dir():
            fail(f"--out is not a directory: {path}")
        if any(path.iterdir()):
            fail(f"Refusing to overwrite populated --out: {path}")
    return path


def seal(root: Path) -> None:
    for base, _, files in os.walk(root, followlinks=False):
        for name in files:
            safe(Path(base) / name).chmod(stat.S_IREAD)


def plan_experiments(baseline: Path, ids: list[str]) -> dict:
    baseline = safe(baseline)
    if not baseline.is_dir():
        fail(f"Missing baseline addon: {baseline}")
    inv = inventory(baseline)
    for rel in (R0, R1, R2, R3, R4, R5):
        if rel not in inv:
            fail(f"Baseline missing {rel}")
    r0_text, _, r0 = load_vmt(baseline, R0)
    r1_text, _, r1 = load_vmt(baseline, R1)
    r2_text, _, r2 = load_vmt(baseline, R2)
    r3_text, _, r3 = load_vmt(baseline, R3)
    r4_text, _, r4 = load_vmt(baseline, R4)
    r5_text, _, r5 = load_vmt(baseline, R5)
    unknown = [x for x in ids if x not in KNOWN_IDS]
    if unknown:
        fail(f"Unknown experiment ids: {unknown}")
    m1_items = m1_r5_phong(r0, r5)
    m1_text = format_vmt("VertexLitGeneric", m1_items)
    m1_diff = param_diff(r5, m1_items)
    assert_m1_diff(m1_diff)
    if m1_text == r5_text:
        fail("M1 produced no r5 text change")
    m2_r1 = m2_env_off(r1, "r1")
    m2_r4 = m2_env_off(r4, "r4")
    m2_r1_text = format_vmt("VertexLitGeneric", m2_r1)
    m2_r4_text = format_vmt("VertexLitGeneric", m2_r4)
    d1 = param_diff(r1, m2_r1)
    d4 = param_diff(r4, m2_r4)
    assert_m2_diff(d1, "r1")
    assert_m2_diff(d4, "r4")
    if m2_r1_text == r1_text or m2_r4_text == r4_text:
        fail("M2 produced no envmap text change")
    m6_items = m6_r1_env_unmask(r1)
    m6_text = format_vmt("VertexLitGeneric", m6_items)
    m6_diff = param_diff(r1, m6_items)
    assert_m6_diff(m6_diff)
    if m6_text == r1_text:
        fail("M6 produced no r1 text change")
    m4_rewrites = {}
    m4_diffs = {}
    if "M4_phong_exponent" in ids:
        for rel, items, original in (
            (R0, r0, r0_text), (R1, r1, r1_text), (R2, r2, r2_text),
            (R3, r3, r3_text), (R4, r4, r4_text),
        ):
            new_items = m4_set_exponent(items, rel)
            text = format_vmt("VertexLitGeneric", new_items)
            diff = param_diff(items, new_items)
            assert_m4_diff(diff, rel)
            if text == original:
                fail(f"M4 produced no text change: {rel}")
            m4_rewrites[rel] = text
            m4_diffs[rel] = diff
    m4b_rewrites = {}
    m4b_diffs = {}
    if "M4b_phong_boost" in ids:
        for rel, items, original in (
            (R0, r0, r0_text), (R1, r1, r1_text), (R2, r2, r2_text),
            (R3, r3, r3_text), (R4, r4, r4_text),
        ):
            new_items = m4b_set_boost(items, rel)
            text = format_vmt("VertexLitGeneric", new_items)
            diff = param_diff(items, new_items)
            assert_m4b_diff(diff, items, new_items, rel)
            if text == original:
                fail(f"M4b produced no text change: {rel}")
            m4b_rewrites[rel] = text
            m4b_diffs[rel] = diff
    m6p_text = ""
    m6p_diff = {}
    if "M6_r1_phong_unmask" in ids:
        m6p_items = m6_r1_phong_unmask(r1)
        m6p_text = format_vmt("VertexLitGeneric", m6p_items)
        m6p_diff = param_diff(r1, m6p_items)
        assert_m6_phong_unmask_diff(m6p_diff)
        if m6p_text == r1_text:
            fail("M6 phong-unmask produced no r1 text change")
    return {
        "baseline": str(baseline),
        "baseline_files": len(inv),
        "experiments": {
            "M1_r5_phong": {
                "id": "M1_r5_phong",
                "hypothesis": (
                    "r5 (1516 triangles, strategy=matte_dark, $phong 0) is incorrectly "
                    "treated as a non-specular surface. Restoring the same masked Phong "
                    "keys currently used by r0 should reveal gold edges/patterns on the "
                    "dark body without changing other slots or envmap."
                ),
                "changed_factor": (
                    "Only cf_mauser_libra_r5.vmt: replace $phong 0 with r0 Phong keys "
                    "($phong, $basemapalphaphongmask, $phongexponent, $phongboost, "
                    "$phongfresnelranges, $phongtint). No envmap, no VTF rewrite, "
                    "no global tint edit."
                ),
                "allowlist": [R5],
                "rewrites": {R5: m1_text},
                "parameter_diff": {R5: m1_diff},
                "expected_observations": (
                    "Gold trim / bright edges on the dark body appear and move with "
                    "lighting or view; the dark panels stay dark. No change: inspect "
                    "whether r5 actually loads, whether the packed phong mask is empty, "
                    "or whether VertexLitGeneric ignores this key combination. "
                    "Washout / noise: reject this r0 preset, do not raise boost."
                ),
                "readme": (
                    "M1_r5_phong is a single-factor ablation, not a final visual fix.\n"
                    "Only cf_mauser_libra_r5.vmt changes: $phong 0 is replaced with the "
                    "current r0 masked Phong keys.\n"
                    "Keep FOV, position, animation, and hands unchanged.\n"
                    "Do not stack with M2 or later experiments.\n"
                    "generation_validation only; runtime_status=PENDING; no visual PASS.\n"
                ),
            },
            "M2_env_off": {
                "id": "M2_env_off",
                "hypothesis": (
                    "Current r1/r4 $envmap env_cubemap may or may not contribute visible "
                    "view-dependent reflection. Disabling those envmap keys measures the "
                    "existing reflection contribution; it is not a candidate for a better look."
                ),
                "changed_factor": (
                    "Only cf_mauser_libra_r1.vmt and cf_mauser_libra_r4.vmt: remove "
                    "$envmap, $normalmapalphaenvmapmask, $envmaptint. All other fields "
                    "and all other files stay byte-identical."
                ),
                "allowlist": [R1, R4],
                "rewrites": {R1: m2_r1_text, R4: m2_r4_text},
                "parameter_diff": {R1: d1, R4: d4},
                "expected_observations": (
                    "Same pose/scene difference vs baseline shows whether envmap currently "
                    "adds brightness, color, or view-dependent highlights on r1/r4 regions "
                    "(badge / gold frames / brighter metal). No change does not mean "
                    "reflection is unnecessary: first check cubemap sampling and key support. "
                    "This ablation must not be kept as the improved material."
                ),
                "readme": (
                    "M2_env_off is a diagnostic ablation, not a final visual fix.\n"
                    "Only r1 and r4 VMTs change: envmap keys are removed.\n"
                    "Keep FOV, position, animation, and hands unchanged.\n"
                    "Derive from the original baseline, not from M1.\n"
                    "generation_validation only; runtime_status=PENDING; no visual PASS.\n"
                ),
            },
            "M6_r1_env_unmask": {
                "id": "M6_r1_env_unmask",
                "hypothesis": (
                    "M2 showed no visible loss after removing envmap, so either "
                    "env_cubemap does not sample on this viewmodel or the bumpmap-alpha "
                    "env mask suppresses it. Unmasking r1 while keeping env_cubemap and "
                    "the current $envmaptint tests that mask/path without changing cubemap "
                    "identity or Phong."
                ),
                "changed_factor": (
                    "Only cf_mauser_libra_r1.vmt: remove $normalmapalphaenvmapmask. "
                    "Keep $envmap env_cubemap and $envmaptint. No VTF rewrite, no r4, "
                    "no Phong edits."
                ),
                "allowlist": [R1],
                "rewrites": {R1: m6_text},
                "parameter_diff": {R1: m6_diff},
                "expected_observations": (
                    "r1 gold/light metal (badge, brighter frames) picks up map/sky "
                    "cubemap color and view-dependent reflection. That means envmap "
                    "samples and the mask was blocking. Still no change: env_cubemap is "
                    "likely inert on this viewmodel; skip M3 intensity; do not bind "
                    "LobbyCube here."
                ),
                "readme": (
                    "M6_r1_env_unmask is a diagnostic ablation, not a final visual fix.\n"
                    "Only r1 changes: envmap mask is removed; envmap and tint stay.\n"
                    "Derived from the frozen baseline, not from M1 or M2.\n"
                    "Keep FOV, position, animation, and hands unchanged.\n"
                    "generation_validation only; runtime_status=PENDING; no visual PASS.\n"
                ),
            },
            "M4_phong_exponent": {
                "id": "M4_phong_exponent",
                "hypothesis": (
                    "M1/M2/M6 showed env_cubemap is inert on this viewmodel and r5 "
                    "with the r0 Phong preset is invisible. Remaining gold is the "
                    "existing Phong path (r0-r4, exponent 4). A.8.1 metal uses 48; "
                    "changing only exponent tests highlight coverage/shape, not boost "
                    "or tint."
                ),
                "changed_factor": (
                    "Only $phongexponent 4->48 on cf_mauser_libra_r0..r4.vmt. "
                    "Keep boost, tint, fresnel, envmap keys, r5 $phong 0, and all VTFs."
                ),
                "allowlist": [R0, R1, R2, R3, R4],
                "rewrites": m4_rewrites,
                "parameter_diff": m4_diffs,
                "expected_observations": (
                    "Gold coin/frames/sight highlights become smaller and sharper and "
                    "still move with view. Dark body stays dark (r5 unchanged). "
                    "Washout or noisy coverage: reject 48. No change: Phong exponent "
                    "is not shaping the current gold, next is boost or tint on the "
                    "same path."
                ),
                "readme": (
                    "M4_phong_exponent is a single-factor ablation, not a final visual fix.\n"
                    "Only exponent changes on r0-r4. Boost, tint, envmap, r5, and VTFs stay.\n"
                    "Derived from the frozen baseline, not from M1/M2/M6.\n"
                    "Keep FOV, position, animation, and hands unchanged.\n"
                    "generation_validation only; runtime_status=PENDING; no visual PASS.\n"
                ),
            },
            "M4b_phong_boost": {
                "id": "M4b_phong_boost",
                "hypothesis": (
                    "M4 exponent 48 did not clearly reshape highlights at current energy. "
                    "Parent is M4 (exponent 48 kept). Doubling $phongboost on r0-r4 tests "
                    "whether the visible gold is energy-limited. Tint, exponent, envmap "
                    "and r5 stay."
                ),
                "changed_factor": (
                    f"Only $phongboost x{M4B_BOOST_MUL:g} on cf_mauser_libra_r0..r4.vmt. "
                    "Keep exponent 48, tint, fresnel, envmap keys, r5 $phong 0, and VTFs."
                ),
                "allowlist": [R0, R1, R2, R3, R4],
                "rewrites": m4b_rewrites,
                "parameter_diff": m4b_diffs,
                "expected_observations": (
                    "Coin, frames and sight gold get brighter and still move with view. "
                    "Dark body stays dark. Washout or noise: reject this multiplier. "
                    "No change: Phong energy is not the limiter; next is tint/albedotint "
                    "or mask packing."
                ),
                "readme": (
                    "M4b_phong_boost is a single-factor ablation from the M4 parent.\n"
                    "Only boost changes on r0-r4. Exponent 48, tint, envmap, r5, VTFs stay.\n"
                    "Keep FOV, position, animation, and hands unchanged.\n"
                    "generation_validation only; runtime_status=PENDING; no visual PASS.\n"
                ),
            },
            "M6_r1_phong_unmask": {
                "id": "M6_r1_phong_unmask",
                "hypothesis": (
                    "M4b doubled Phong boost with no clear gold change, so either the "
                    "packed base-alpha phong mask is suppressing response or Phong is "
                    "inert on this viewmodel. Removing only $basemapalphaphongmask on r1 "
                    "keeps exponent/boost/tint from the M4b parent."
                ),
                "changed_factor": (
                    "Only cf_mauser_libra_r1.vmt: remove $basemapalphaphongmask. "
                    "Keep $phong 1, exponent, boost, tint, and envmap keys. No VTF rewrite."
                ),
                "allowlist": [R1],
                "rewrites": {R1: m6p_text},
                "parameter_diff": {R1: m6p_diff},
                "expected_observations": (
                    "r1 gold/light metal becomes obviously brighter or washed and moves "
                    "with view: the packed phong mask was the limiter. Still no change: "
                    "Phong is likely inert here; visible gold is mostly diffuse, next is "
                    "base-texture/tint not more boost."
                ),
                "readme": (
                    "M6_r1_phong_unmask is a diagnostic from the M4b parent, not a final fix.\n"
                    "Only r1 changes: phong mask key is removed. Energy/tint/envmap stay.\n"
                    "Keep FOV, position, animation, and hands unchanged.\n"
                    "generation_validation only; runtime_status=PENDING; no visual PASS.\n"
                ),
            },
        },
        "inventory": inv,
    }


def emit_manifest(exp: dict, baseline: Path, addon: Path, before: dict, after: dict) -> dict:
    changed = []
    for rel in sorted(after):
        if rel not in before:
            fail(f"Candidate grew extra file: {rel}")
        if before[rel]["sha256"] != after[rel]["sha256"]:
            changed.append(rel)
    extra_missing = [rel for rel in before if rel not in after]
    if extra_missing:
        fail(f"Candidate lost files: {extra_missing}")
    if set(changed) != set(exp["allowlist"]):
        fail(f"{exp['id']} changed {changed}, expected {exp['allowlist']}")
    for rel in exp["allowlist"]:
        got = (addon / Path(*rel.split("/"))).read_text(encoding="ascii")
        if got != exp["rewrites"][rel]:
            fail(f"Written VMT mismatch: {rel}")
    unchanged = len(after) - len(changed)
    files = {}
    for rel in sorted(after):
        files[rel] = {
            "baseline_sha256": before[rel]["sha256"],
            "candidate_sha256": after[rel]["sha256"],
            "bytes": after[rel]["bytes"],
            "changed": rel in changed,
        }
    return {
        "id": exp["id"],
        "parent_baseline": str(baseline),
        "generation_validation": "PASS",
        "runtime_status": "PENDING",
        "visual_status": "NOT_EVALUATED",
        "hypothesis": exp["hypothesis"],
        "changed_factor": exp["changed_factor"],
        "allowlist": exp["allowlist"],
        "changed_files": changed,
        "unchanged_count": unchanged,
        "files": files,
        "parameter_diff": exp["parameter_diff"],
        "expected_observations": exp["expected_observations"],
        "notes": (
            "Ablation package only. Not a final material. Do not treat generation_validation "
            "as visual PASS. Use unchanged FOV, position, animation, and hands."
        ),
    }


def write_experiment(out: Path, exp: dict, baseline: Path, before: dict) -> dict:
    root = require_under(out / exp["id"], out)
    addon = require_under(root / "addon", root)
    copy_tree(baseline, addon)
    copied = inventory(addon)
    if copied != before:
        fail(f"{exp['id']} copy is not byte-identical to baseline")
    for rel, text in exp["rewrites"].items():
        dest = require_under(addon / Path(*rel.split("/")), addon)
        if rel not in before:
            fail(f"Allowlist file missing from baseline: {rel}")
        write_text(dest, text)
    after = inventory(addon)
    manifest = emit_manifest(exp, baseline, addon, before, after)
    write_text(root / "manifest.json", json.dumps(manifest, indent=2, ensure_ascii=False) + "\n")
    write_text(root / "README.txt", exp["readme"])
    write_text(root / "parameter_diff.json",
               json.dumps(exp["parameter_diff"], indent=2, ensure_ascii=False) + "\n")
    return {
        "id": exp["id"],
        "root": str(root),
        "changed_files": manifest["changed_files"],
        "unchanged_count": manifest["unchanged_count"],
        "generation_validation": "PASS",
        "runtime_status": "PENDING",
        "visual_status": "NOT_EVALUATED",
        "parameter_diff": exp["parameter_diff"],
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description=(
            "Generate M1_r5_phong and M2_env_off isolated experiment addons. "
            "These are single-factor ablations, not a final visual fix. "
            "FOV, position, animation, and hands stay unchanged."
        )
    )
    p.add_argument("--baseline", required=True, help="Frozen baseline addon directory")
    p.add_argument("--out", required=True, help="Empty output directory for selected experiments")
    p.add_argument("--ids", default="M1_r5_phong,M2_env_off",
                   help="Comma-separated experiment ids to emit")
    p.add_argument("--dry-run", action="store_true",
                   help="Parse, validate, and print planned diffs without writing")
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    baseline = safe(Path(args.baseline))
    out = safe(Path(args.out))
    if baseline == out or baseline in out.parents or out in baseline.parents:
        fail("--baseline and --out must not nest")
    if not str(out).replace("\\", "/").startswith(str(FIX_ROOT).replace("\\", "/") + "/"):
        fail(f"--out must stay under {FIX_ROOT}")
    ids = [x.strip() for x in args.ids.split(",") if x.strip()]
    if not ids:
        fail("--ids is empty")
    plan = plan_experiments(baseline, ids)
    selected = {name: plan["experiments"][name] for name in ids}
    if args.dry_run:
        summary = {
            "dry_run": True,
            "baseline": plan["baseline"],
            "baseline_files": plan["baseline_files"],
            "ids": ids,
            "experiments": {
                name: {
                    "allowlist": exp["allowlist"],
                    "parameter_diff": exp["parameter_diff"],
                    "runtime_status": "PENDING",
                    "visual_status": "NOT_EVALUATED",
                }
                for name, exp in selected.items()
            },
        }
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        return 0
    require_empty(out)
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for name in ids:
        results.append(write_experiment(out, selected[name], baseline, plan["inventory"]))
    batch = {
        "generator": str(Path(__file__).resolve()),
        "parent_baseline": str(baseline),
        "out": str(out),
        "ids": ids,
        "generation_validation": "PASS",
        "runtime_status": "PENDING",
        "visual_status": "NOT_EVALUATED",
        "note": (
            "Selected experiments are derived directly from the same frozen baseline. "
            "They must not be stacked. Not a final material candidate."
        ),
        "experiments": results,
    }
    write_text(out / "batch.json", json.dumps(batch, indent=2, ensure_ascii=False) + "\n")
    write_text(out / "README.txt", (
        "Isolated material ablations generated from a frozen baseline addon.\n"
        "Not a final visual fix. Do not change FOV, position, animation, or hands.\n"
        "Do not stack experiments. runtime_status=PENDING; no visual PASS.\n"
    ))
    seal(out)
    print(json.dumps({
        "generation_validation": "PASS",
        "runtime_status": "PENDING",
        "visual_status": "NOT_EVALUATED",
        "out": str(out),
        "experiments": [
            {"id": r["id"], "changed_files": r["changed_files"],
             "unchanged_count": r["unchanged_count"]}
            for r in results
        ],
    }, indent=2))
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
