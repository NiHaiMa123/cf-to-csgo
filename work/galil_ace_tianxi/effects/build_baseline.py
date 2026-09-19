# -*- coding: utf-8 -*-
"""E0 — baseline manifest for the accepted 天袭 addon before effect work.

Records SHA-256 for every file of staging addon A
(work/galil_ace_tianxi/addon/) and the live MIGI addon B
(<game>/migi/csgo/addons/p_cf_tianxi_galilar_p1/), plus per-file A==B
equality so the pre-effect accepted state can be restored or diffed later.

Read-only on both trees. Output: effects/baseline/manifest.json
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))

import _paths  # noqa: E402

WORK = Path(__file__).resolve().parent.parent          # work/galil_ace_tianxi
OUT = Path(__file__).resolve().parent / "baseline"     # effects/baseline
ADDON_A = WORK / "addon"
ADDON_NAME = "p_cf_tianxi_galilar_p1"
ADDON_B = Path(_paths.game_dir()) / "migi" / "csgo" / "addons" / ADDON_NAME

PROVENANCE = [
    WORK / "acquire" / "acquisition.json",
    WORK / "decode" / "reference_payload.json",
    WORK / "decode" / "cf_skin_galilace.json",
    WORK / "csref" / "viewmodel_transform.json",
    WORK / "texture" / "report_v2.json",
    WORK / "native_vm" / "build_galilace_vm.py",
    WORK / "texture" / "build_textures_v2.py",
]


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def tree(root: Path) -> list[dict]:
    rows = []
    if not root.is_dir():
        return rows
    for p in sorted(root.rglob("*")):
        if p.is_file():
            rows.append({
                "rel": p.relative_to(root).as_posix(),
                "size": p.stat().st_size,
                "sha256": sha256(p),
            })
    return rows


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    a = {r["rel"]: r for r in tree(ADDON_A)}
    b = {r["rel"]: r for r in tree(ADDON_B)}
    rows = []
    for rel in sorted(set(a) | set(b)):
        ra, rb = a.get(rel), b.get(rel)
        rows.append({
            "rel": rel,
            "a": ra,
            "b": rb,
            "a_eq_b": bool(ra and rb and ra["sha256"] == rb["sha256"]),
        })
    prov = []
    for p in PROVENANCE:
        prov.append({
            "path": str(p),
            "exists": p.is_file(),
            "sha256": sha256(p) if p.is_file() else None,
        })
    doc = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "weapon": "galil_ace_tianxi",
        "addon_name": ADDON_NAME,
        "accepted_state": "pipeline.md P8 PASS 2026-09-14 (model/hands/anim/sound user-verified); materials v7",
        "staging_a": str(ADDON_A),
        "migi_b": str(ADDON_B),
        "a_files": len(a),
        "b_files": len(b),
        "a_eq_b_count": sum(1 for r in rows if r["a_eq_b"]),
        "a_only": [r["rel"] for r in rows if r["a"] and not r["b"]],
        "b_only": [r["rel"] for r in rows if r["b"] and not r["a"]],
        "hash_mismatch": [r["rel"] for r in rows if r["a"] and r["b"] and not r["a_eq_b"]],
        "files": rows,
        "provenance_inputs": prov,
        "game_dir": str(Path(_paths.game_dir())),
        "note": "E0 baseline per plan.md §5. C-layer pak hash check is a separate PACK_VERIFY step; this manifest covers A/B only.",
    }
    (OUT / "manifest.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[e0] A={len(a)} B={len(b)} eq={doc['a_eq_b_count']} a_only={doc['a_only']} b_only={doc['b_only']} mismatch={doc['hash_mismatch']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
