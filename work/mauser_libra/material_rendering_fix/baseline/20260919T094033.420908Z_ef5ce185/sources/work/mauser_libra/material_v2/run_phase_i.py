# -*- coding: utf-8 -*-
"""Phase I driver: deploy material v2 to MIGI addon + hash validation.

Stage 1 (default): addon_v2 -> MIGI addon, prune stale files, A/B SHA-256.
Stage 2 (--verify-pak): after the user runs MIGI REBUILD, parse
pak01_dir.vpk and compare every addon file's SHA-256 (B/C).
The agent never runs MIGI itself (pipeline rule).
"""
from __future__ import annotations

import hashlib
import json
import struct
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

WORK = _REPO / "work" / "mauser_libra"
MV2 = WORK / "material_v2"
STAGING = WORK / "addon_v2"
GAME = Path(_paths.game_dir())
ADDON = GAME / "migi" / "csgo" / "addons" / "p_cf_mauser_libra_p1"
PAK = GAME / "migi" / "csgo" / "pak01_dir.vpk"


def sha256(path: Path) -> str:
    d = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            d.update(chunk)
    return d.hexdigest()


def deploy() -> int:
    staged = {p.relative_to(STAGING).as_posix(): p
              for p in STAGING.rglob("*") if p.is_file()}
    for rel, src in staged.items():
        dst = ADDON / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(src.read_bytes())
    deployed = {p.relative_to(ADDON).as_posix(): p
                for p in ADDON.rglob("*") if p.is_file()}
    extras = sorted(set(deployed) - set(staged))
    for rel in extras:
        (ADDON / rel).unlink()
    deployed = {p.relative_to(ADDON).as_posix(): p
                for p in ADDON.rglob("*") if p.is_file()}
    missing = sorted(set(staged) - set(deployed))
    mismatch = sorted(rel for rel in set(staged) & set(deployed)
                      if sha256(staged[rel]) != sha256(deployed[rel]))
    manifest = {
        "staging": str(STAGING), "addon": str(ADDON),
        "files": len(staged), "removed_stale": extras,
        "missing": missing, "mismatch": mismatch,
        "ab_equal": not missing and not mismatch,
        "hashes": {rel: sha256(p) for rel, p in sorted(staged.items())},
        "next": "user runs MIGI REBUILD, then --verify-pak",
    }
    (MV2 / "i_deploy_manifest.json").write_text(
        json.dumps(manifest, indent=1), encoding="utf-8")
    print(f"A/B SHA-256: {len(staged) - len(mismatch)}/{len(staged)} equal, "
          f"removed {len(extras)} stale")
    if missing or mismatch:
        print("MISSING:", missing, "MISMATCH:", mismatch)
        return 1
    print("deployed ->", ADDON)
    print("NEXT: run MIGI REBUILD, then: python run_phase_i.py --verify-pak")
    return 0


def parse_vpk_tree(path: Path) -> dict[str, bytes]:
    """VPK v2 tree -> {relpath: file bytes} for entries in archive."""
    data = path.read_bytes()
    # v2: 28-byte header then tree; entries live in pak01_XX.vpk siblings
    off = 28
    entries = {}

    def read_cstr(pos):
        end = data.index(b"\x00", pos)
        return data[pos:end].decode("utf-8", "replace"), end + 1

    while True:
        ext, off = read_cstr(off)
        if not ext:
            break
        while True:
            pth, off = read_cstr(off)
            if not pth:
                break
            while True:
                name, off = read_cstr(off)
                if not name:
                    break
                (crc, preload, aidx, aoff, alen, term) = struct.unpack_from(
                    "<IHHIIH", data, off)
                off += 18
                rel = (f"{pth}/{name}.{ext}" if pth != " "
                       else f"{name}.{ext}")
                entries[rel] = (aidx, aoff, alen, preload, off)
                # preload bytes follow the descriptor
                off += preload
    return entries


def verify_pak() -> int:
    staged = {p.relative_to(STAGING).as_posix(): p
              for p in STAGING.rglob("*") if p.is_file()}
    tree = parse_vpk_tree(PAK)
    results, missing, mismatch = {}, [], []
    for rel, src in sorted(staged.items()):
        # VPK paths use lowercase forward slashes
        key = rel.lower().replace("\\", "/")
        if key not in tree:
            missing.append(rel)
            continue
        aidx, aoff, alen, preload, _ = tree[key]
        blob = PAK.parent / f"pak01_{aidx:03d}.vpk" if aidx != 0x7fff else PAK
        raw = blob.read_bytes()[aoff:aoff + alen]
        h = hashlib.sha256(raw).hexdigest()
        ok = h == sha256(src)
        results[rel] = {"sha256": h, "match": ok}
        if not ok:
            mismatch.append(rel)
    out = {"pak": str(PAK), "checked": len(results),
           "missing": missing, "mismatch": mismatch,
           "bc_equal": not missing and not mismatch,
           "entries": results}
    (MV2 / "i_pak_verify.json").write_text(
        json.dumps(out, indent=1), encoding="utf-8")
    print(f"B/C pak SHA-256: {len(results) - len(mismatch)}/{len(staged)} "
          f"equal, missing={len(missing)}")
    if missing:
        print("MISSING:", missing)
    if mismatch:
        print("MISMATCH:", mismatch)
    return 0 if not missing and not mismatch else 1


if __name__ == "__main__":
    if "--verify-pak" in sys.argv:
        raise SystemExit(verify_pak())
    raise SystemExit(deploy())
