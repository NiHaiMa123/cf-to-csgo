"""Sync one isolated experiment allowlist into staging A and MIGI addon B.

Never writes the frozen baseline or experiment packages.
Never runs MIGI REBUILD. Models/hands/sounds are not rewritten unless
they already differ, which is treated as a failure.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import sys
from pathlib import Path

CHUNK = 1024 * 1024
FIX = Path(__file__).resolve().parent
A = Path("D:/project/cf_to_csgo/work/mauser_libra/addon_v2")
B = Path("D:/steam/steamapps/common/csgo legacy/migi/csgo/addons/p_cf_mauser_libra_p1")
FROZEN = Path(
    "D:/project/cf_to_csgo/work/mauser_libra/material_rendering_fix/"
    "baseline/20260919T094033.420908Z_ef5ce185/addon_v2"
)


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
    result = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            safe(Path(base) / name)
        for name in sorted(files):
            p = Path(base) / name
            rel = p.relative_to(root).as_posix()
            result[rel] = digest(p)
    return result


def same(x: dict, y: dict) -> bool:
    return (x["bytes"], x["sha256"]) == (y["bytes"], y["sha256"])


def write_bytes(path: Path, data: bytes) -> None:
    path = safe(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        path.chmod(stat.S_IWRITE | stat.S_IREAD)
    path.write_bytes(data)


def load_manifest(exp_root: Path) -> dict:
    path = safe(exp_root / "manifest.json")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if manifest.get("generation_validation") != "PASS":
        fail("Experiment generation_validation is not PASS")
    if not manifest.get("allowlist"):
        fail("Experiment allowlist is empty")
    return manifest


def sync(exp_root: Path, out_dir: Path) -> dict:
    exp_root = safe(exp_root)
    addon = safe(exp_root / "addon")
    manifest = load_manifest(exp_root)
    allow = list(manifest["allowlist"])
    cand = inventory(addon)
    parent_root = safe(Path(manifest["parent_baseline"]))
    pre_a, pre_b, parent = inventory(A), inventory(B), inventory(parent_root)
    if set(pre_a) != set(pre_b) or set(pre_a) != set(parent) or set(pre_a) != set(cand):
        fail("A/B/parent/candidate inventories differ")
    if any(not same(pre_a[k], pre_b[k]) for k in pre_a):
        fail("A/B are not identical before sync; refusing to deploy")
    if any(not same(pre_a[k], parent[k]) for k in pre_a if k not in allow):
        fail("Non-allowlist files already drifted from parent baseline")
    planned = []
    for rel in allow:
        if rel not in cand:
            fail(f"Allowlist missing from experiment addon: {rel}")
        if rel.startswith("models/") or "nini" in rel or rel.startswith("sound/"):
            fail(f"Allowlist includes protected path: {rel}")
        if not rel.endswith(".vmt"):
            fail(f"This sync only writes VMT files, got {rel}")
        if same(pre_a[rel], cand[rel]):
            fail(f"Allowlist file already matches candidate; nothing to sync: {rel}")
        planned.append(rel)
    for rel in planned:
        data = (addon / Path(*rel.split("/"))).read_bytes()
        if hashlib.sha256(data).hexdigest() != cand[rel]["sha256"]:
            fail(f"Candidate changed while reading: {rel}")
        write_bytes(A / Path(*rel.split("/")), data)
        write_bytes(B / Path(*rel.split("/")), data)
    post_a, post_b = inventory(A), inventory(B)
    if any(not same(post_a[k], cand[k]) for k in cand):
        fail("Staging A does not match experiment addon after sync")
    if any(not same(post_b[k], cand[k]) for k in cand):
        fail("MIGI addon B does not match experiment addon after sync")
    if any(not same(post_a[k], post_b[k]) for k in post_a):
        fail("A/B mismatch after sync")
    unchanged = [k for k in post_a if k not in planned]
    if any(not same(post_a[k], parent[k]) for k in unchanged):
        fail("Protected files changed during sync")
    evidence = {
        "experiment_id": manifest["id"],
        "experiment_root": str(exp_root),
        "parent_baseline": manifest["parent_baseline"],
        "staging_a": str(A),
        "migi_b": str(B),
        "files": len(post_a),
        "copied": {rel: cand[rel] for rel in planned},
        "ab_equal": True,
        "a_matches_experiment": True,
        "b_matches_experiment": True,
        "protected_unchanged": True,
        "generation_validation": "PASS",
        "runtime_status": "PACK_VERIFY_PENDING",
        "visual_status": "NOT_EVALUATED",
        "next": "User runs MIGI REBUILD; then verify pak C vs B. Do not treat this as visual PASS.",
        "rollback": "Copy the parent baseline allowlist files back to A and B, then REBUILD.",
        "hashes": {rel: post_a[rel]["sha256"] for rel in sorted(post_a)},
    }
    out_dir = safe(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "deploy_manifest.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return evidence


def archive_scenes(out_dir: Path, items: list[tuple[str, Path, dict]]) -> dict:
    out_dir = safe(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    scenes = {}
    for name, src, meta in items:
        src = safe(src)
        if not src.is_file():
            fail(f"Missing screenshot: {src}")
        dest = out_dir / f"{name}{src.suffix.lower()}"
        data = src.read_bytes()
        dest.write_bytes(data)
        info = digest(dest)
        scenes[name] = {
            **meta,
            "file": dest.name,
            "source": str(src),
            **info,
        }
    record = {
        "captured_by": "user",
        "map": "de_mirage",
        "weapon_hud": "格洛克 18 型",
        "ammo": "20/120",
        "hp_armor": "100/100",
        "fov_position": "user-confirmed unchanged; not modified this round",
        "material_version": "frozen baseline 20260919T094033.420908Z_ef5ce185",
        "r5_sha256_at_capture": "6f58785abc3b2811fe18e771a41f2dc3fc825e366bed81b59946256fd4146155",
        "note": (
            "User labeled these 明处正向 / 明处转向 / 暗处. "
            "The dark sample is outdoor wall-shadow on Mirage B palace, not an indoor room."
        ),
        "scenes": scenes,
    }
    (out_dir / "scene.json").write_text(
        json.dumps(record, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return record


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Archive baseline scenes or sync one experiment to A/B.")
    p.add_argument("--archive-scenes", action="store_true")
    p.add_argument("--sync", metavar="EXPERIMENT_ROOT")
    p.add_argument("--out", required=True, help="Evidence output directory")
    args = p.parse_args(sys.argv[1:] if argv is None else argv)
    out = Path(args.out)
    if args.archive_scenes:
        assets = Path(
            r"C:/Users/Administrator/.grok/sessions/"
            r"D%3A%5Cproject%5Ccf_to_csgo/01a0b90b-2671-7162-817a-9fb4c4826d55/assets"
        )
        record = archive_scenes(out, [
            ("lit_front", assets / "image-eb88ad9e-27c6-4035-9bca-c9d6a439fe93.jpg", {
                "user_label": "明处正向",
                "hud_time": "9:54",
                "notes": "Mirage mid toward wooden palace gate; gun in direct sun.",
            }),
            ("lit_turn", assets / "image-b4091dfc-6850-45e5-b256-9c7d45d4f5ff.jpg", {
                "user_label": "明处转向",
                "hud_time": "9:03",
                "notes": "Turned to courtyard/arch with crates and truck; still sunlit.",
            }),
            ("dark", assets / "image-31f8956c-cc31-42d0-92c0-0c1bc0d4b76a.jpg", {
                "user_label": "暗处",
                "hud_time": "8:48",
                "notes": "B palace alley, PALAIS DE LA KASBAH sign. Outdoor shade, not indoor.",
            }),
        ])
        print(json.dumps({"archived": list(record["scenes"]), "out": str(out)}, indent=2))
        return 0
    if args.sync:
        evidence = sync(Path(args.sync), out)
        print(json.dumps({
            "experiment_id": evidence["experiment_id"],
            "copied": list(evidence["copied"]),
            "files": evidence["files"],
            "ab_equal": evidence["ab_equal"],
            "runtime_status": evidence["runtime_status"],
        }, indent=2))
        return 0
    fail("Specify --archive-scenes or --sync")
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except RuntimeError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        sys.exit(1)
