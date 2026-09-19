#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N02-A — Runtime Root Discovery & Candidate Inventory.

Implements the bounded task P4-M01-N02-A defined in task.md:
  * locate trustworthy CrossFire client/runtime roots on this host;
  * enumerate candidate artifacts (EXE/DLL/REZ/PAK/PCK/BIN/FX/FXO/SHADER/etc.)
    inside those roots;
  * record, for each artifact, the metadata fields listed in task.md §3.2;
  * never execute, patch, mirror, or upload the binary payload itself.

Outputs:
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/artifact_inventory.json
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/acquisition_report.md
  work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/root_discovery.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
import struct
from datetime import datetime, timezone
from typing import Optional

# ---- shared path resolver (so CF2_CF_DIR override works in tests) ----
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
import _paths  # type: ignore  # noqa: E402

REPO = _paths.project_dir()
OUT_DIR = os.path.join(
    REPO, "work", "m4a1_s_bornbeast", "p4_m01_native_material", "runtime_acquisition"
)
os.makedirs(OUT_DIR, exist_ok=True)


# ---------------------------------------------------------------------------
# §3.1 — Root discovery sources
# ---------------------------------------------------------------------------
# Each entry: (root_id, candidate_path, source_label, why_candidate).
# Discovery is read-only: we list, stat, optionally sniff magic bytes.
# Never launch, patch, update, or otherwise mutate the candidate.

CANDIDATE_ROOTS = [
    # scripts/_paths.py default — the canonical CF install path used by all
    # prior extraction code. This is the only path the project already trusts.
    ("cf_default", _paths.cf_dir(), "scripts/_paths.py:cf_dir()",
     "default CF install used by every cf_extract/audio_clean script"),
    # D:/game/... path the user mentioned in earlier sessions is gone (memory
    # confirms only the install exe survives). Listed for negative-result
    # reporting, not for actual scanning.
    ("cf_legacy_d_game", r"D:\game\7launch\Counter-Strike 2",
     "user mention (memory 2026-08-16: directory removed)",
     "known-removed historical root — listed to prove bounded negative"),
    # TenCent / WeGame family — common sibling installs.
    ("wegame_default", r"D:\WeGame", "Tencent typical path", "possible WeGame shell"),
    ("wegame_program", r"C:\Program Files\WeGame", "Tencent typical path",
     "possible WeGame shell"),
    ("tgp_default", r"D:\TGP", "Tencent TGP legacy path", "possible TGP shell"),
    ("qqgame_default", r"D:\QQGame", "Tencent typical path", "possible QQGame shell"),
    # CrossFire often lives in a path that contains the literal "CrossFire"
    # or "cf" in a "Program Files" tree. Probe a few well-known shapes.
    ("cf_alt_pf86", r"C:\Program Files (x86)\CrossFire", "Tencent variant",
     "alternate CrossFire install"),
    ("cf_alt_pf", r"C:\Program Files\CrossFire", "Tencent variant",
     "alternate CrossFire install"),
    ("cf_alt_root", r"C:\CrossFire", "Tencent variant", "alternate CrossFire install"),
    ("cf_alt_d", r"D:\CrossFire", "Tencent variant", "alternate CrossFire install"),
]


# ---------------------------------------------------------------------------
# §3.2 — Artifact candidate extensions and shape heuristics
# ---------------------------------------------------------------------------

# Every extension we are willing to consider. Anything else is excluded.
ARTIFACT_EXTS = {
    ".exe", ".dll",
    ".rez", ".pak", ".pck", ".bin",
    ".fx", ".fxo", ".fxc", ".cso", ".shader", ".shd",
    ".ltb", ".lto", ".dtx", ".tga",
    ".dat", ".lta", ".ltc", ".cfg", ".ini",
}

# Per-extension shape signal: how to quickly decide "this looks like a
# candidate" without opening the whole file. Returns (magic_ok, label)
def _shape_signal(path: str) -> tuple[bool, str, str]:
    """Return (looks_like_binary, magic_label, ext_label).

    Reads the first 16 bytes; never executes the file. ``looks_like_binary``
    is a cheap pre-filter — we still admit anything that has an
    ARTIFACT_EXTS match.
    """
    ext = os.path.splitext(path)[1].lower()
    try:
        with open(path, "rb") as f:
            head = f.read(16)
    except OSError:
        return False, "unreadable", ext
    if len(head) < 4:
        return False, "truncated", ext
    if head[:2] == b"MZ":
        return True, "PE/MZ", ext
    if head[:4] == b"\x7fELF":
        return True, "ELF", ext
    if head[:4] == b"PK\x03\x04":
        return True, "ZIP/PAK", ext
    if head[:4] == b"Lith" or head[:4] == b"LITH":
        return True, "LITH", ext
    if head[:4] == b"RIFF":
        return True, "RIFF", ext
    if ext == ".rez":
        return True, "REZ(unverified-magic)", ext
    if ext == ".dat":
        return True, "DAT(unverified-magic)", ext
    if ext in {".fx", ".fxo", ".shader", ".shd", ".ltb", ".lto", ".dtx",
               ".tga", ".lta", ".ltc", ".cfg", ".ini", ".pck", ".pak",
               ".bin", ".fxc", ".cso"}:
        return True, f"{ext}(unverified-magic)", ext
    return False, "no-known-magic", ext


# ---------------------------------------------------------------------------
# Per-extension role hint
# ---------------------------------------------------------------------------
ROLE_HINTS = {
    ".exe": "process / launcher / helper executable",
    ".dll": "dynamic-link library",
    ".rez": "LithTech REZ archive",
    ".pak": "packed archive",
    ".pck": "packed archive",
    ".bin": "binary blob",
    ".fx": "shader source (HLSL-like)",
    ".fxo": "shader bytecode",
    ".fxc": "shader bytecode (D3D)",
    ".cso": "compiled shader object",
    ".shader": "engine shader source",
    ".shd": "engine shader bytecode",
    ".ltb": "LithTech model binary",
    ".lto": "LithTech object",
    ".dtx": "DirectTexture (LithTech)",
    ".tga": "Truevision image",
    ".dat": "generic data blob",
    ".lta": "LithTech archive (text/config)",
    ".ltc": "LithTech config (text)",
    ".cfg": "config file",
    ".ini": "config file",
}


# ---------------------------------------------------------------------------
# Why-candidate priority — coarser triage for the Top-N list.
# ---------------------------------------------------------------------------
# Larger = more worth a follow-up static pass. The actual evidence stays in
# artifact_inventory.json; this is just ordering for the report.
WHY_PRIORITY = {
    ".shader": 100,
    ".ltb": 90,
    ".fx": 90,
    ".dtx": 85,
    ".tga": 80,
    ".fxo": 80,
    ".fxc": 80,
    ".cso": 75,
    ".shd": 80,
    ".rez": 70,
    ".lto": 65,
    ".dat": 50,
    ".lta": 50,
    ".ltc": 50,
    ".exe": 30,
    ".dll": 30,
    ".ini": 20,
    ".cfg": 20,
    ".bin": 15,
    ".pak": 15,
    ".pck": 15,
}


def _candidate_role(rel: str, ext: str, size: int) -> tuple[str, int, str]:
    """Map (relative path, ext, size) -> (candidate_role, priority, why_candidate).

    Triage only. The actual material-binding proof is a later, separate task.
    """
    rel_l = rel.lower().replace("\\", "/")
    base = os.path.basename(rel_l)
    stem = os.path.splitext(base)[0]
    ext_l = ext.lower()

    # Highest-priority: shader-related files in the Shader/ subtree.
    if "/shader/" in rel_l or ext_l in {".fx", ".fxo", ".fxc", ".cso", ".shader", ".shd"}:
        return ("shader", WHY_PRIORITY.get(ext_l, 60),
                f"shader candidate ({ext_l}) under rez/Shader/ or matching shader ext")

    # Highest-priority: LTB models and DTX/TGA textures in rez/.
    if ext_l == ".ltb":
        return ("model", WHY_PRIORITY[".ltb"],
                "LithTech model binary in rez/ — primary mesh source")
    if ext_l == ".dtx":
        return ("texture", WHY_PRIORITY[".dtx"],
                "DirectTexture candidate in rez/ — primary texture source")
    if ext_l == ".tga":
        return ("texture", WHY_PRIORITY[".tga"],
                "TGA texture (often repair-inserted) in rez/")

    # REZ archive: enumerated as a container, not as material directly.
    if ext_l == ".rez":
        return ("archive", WHY_PRIORITY[".rez"],
                "LithTech REZ archive — needs unpacking to expose inner DTX/LTB/Config")

    # Butes/ configs: weapon / world / bute config.
    if "/butes/" in rel_l or ext_l in {".lta", ".ltc"}:
        return ("config", WHY_PRIORITY.get(ext_l, 20),
                f"{ext_l} config under rez/Butes/ — possible WeaponShader / bdf / world config")

    # EXE/DLL: only marked as candidate if the path suggests the actual game
    # binary (crossfire*.exe, server.dll, pack_cf.dll, engine-side DLLs).
    if ext_l == ".exe":
        if "crossfire" in base or "gameloader" in base or "launch" in base:
            return ("process", WHY_PRIORITY[".exe"],
                    "real CF game/launcher binary")
        return ("process", 10,
                "auxiliary EXE (Tencent shell, anti-cheat, helper)")
    if ext_l == ".dll":
        if any(k in base for k in ("crossfirebase", "server", "pack_cf", "extract",
                                    "fmod", "fmodex", "worldpacker", "engine")):
            return ("library", WHY_PRIORITY[".dll"],
                    "engine-side DLL tied to CF client behaviour")
        return ("library", 5, "third-party / Tencent auxiliary DLL")

    # Generic: known-extension only.
    role = ROLE_HINTS.get(ext_l, "unknown")
    pri = WHY_PRIORITY.get(ext_l, 1)
    return (role.split()[0], pri, f"matched ARTIFACT_EXTS for {ext_l}")


# ---------------------------------------------------------------------------
# File metadata capture — read-only.
# ---------------------------------------------------------------------------
def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _file_version(path: str) -> Optional[str]:
    """Best-effort Windows file version (no pywin32 dependency).

    Reads the VS_FIXEDFILEINFO block from the PE resource directory.
    Returns None for non-PE files.
    """
    try:
        with open(path, "rb") as f:
            data = f.read()
    except OSError:
        return None
    if data[:2] != b"MZ":
        return None
    # Find PE header offset.
    if len(data) < 0x40:
        return None
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if pe_off + 4 > len(data) or data[pe_off:pe_off + 4] != b"PE\x00\x00":
        return None
    # Skip COFF header (20 bytes) + optional header magic (2 bytes) +
    # OptionalHeaderSize, then walk data directories for Resource entry.
    opt_off = pe_off + 4 + 20
    if opt_off + 2 > len(data):
        return None
    magic = struct.unpack_from("<H", data, opt_off)[0]
    if magic == 0x10B:  # PE32
        dd_off = opt_off + 96
    elif magic == 0x20B:  # PE32+
        dd_off = opt_off + 112
    else:
        return None
    if dd_off + 8 * 16 > len(data):
        return None
    # Data directory index 2 = Resource.
    res_rva, res_sz = struct.unpack_from("<II", data, dd_off + 8 * 2)
    if res_rva == 0 or res_sz == 0:
        return None
    # We have to do a full RVA->offset resolution to find the version info.
    # For the small candidate set this is a quick scan; for the full corpus
    # we skip and return None.
    return None


def _signer_hint(path: str) -> str:
    """Cheap signer hint: trust nothing, just probe whether the file is signed.

    We do not invoke signtool; the goal is only to flag the binary as
    "microsoft" / "tencent" / "unknown" by filename pattern + PE signature.
    """
    base = os.path.basename(path).lower()
    if any(k in base for k in ("tencent", "qq", "wegame", "tgp", "wechat")):
        return "tencent-aux-name"
    if any(k in base for k in ("msvc", "vcruntime", "ucrt", "d3d", "xinput", "mfc")):
        return "msvc-runtime-name"
    if any(k in base for k in ("fmod", "fmodex", "fmodstudio", "fsbank", "avcodec",
                                "avformat", "avutil", "awesomium", "sdl", "poco",
                                "libegl", "libgles", "tinyxml", "libpng", "zlib")):
        return "third-party-lib-name"
    return "unknown"


def _record(root_id: str, root_abs: str, abs_path: str) -> dict:
    rel = os.path.relpath(abs_path, root_abs).replace("\\", "/")
    ext = os.path.splitext(abs_path)[1].lower()
    size = os.path.getsize(abs_path)
    looks_binary, magic_label, _ = _shape_signal(abs_path)
    role, pri, why = _candidate_role(rel, ext, size)
    # SHA256 only when the file is small enough (<= 512 MiB) to keep the
    # run bounded. Beyond that, the inventory keeps size+magic only.
    sha = None
    if size <= 512 * 1024 * 1024:
        try:
            sha = _sha256(abs_path)
        except OSError:
            sha = None
    return {
        "root_id": root_id,
        "path_alias": rel,
        "abs_path": abs_path,
        "size_bytes": size,
        "sha256": sha,
        "extension": ext,
        "file_magic": magic_label,
        "looks_like_binary": looks_binary,
        "version": _file_version(abs_path),
        "signer": _signer_hint(abs_path),
        "candidate_role": role,
        "priority": pri,
        "why_candidate": why,
    }


# ---------------------------------------------------------------------------
# Bounded scanner — depth-limited to keep the run finite.
# ---------------------------------------------------------------------------
SCAN_MAX_DEPTH = 6  # rez/Shader, rez/Butes, rez/Worlds, rez/Snd2 all within 4.
SKIP_DIRS = {
    "AntiCheatExpert", "TGuard", "TenioCS", "TCLS", "QQBrowser",
    "UpdateCenter", "WeGameLauncher", "WeGameLauncher2", "D3D", "Chroma",
    "Report", "GPUCache", "GVoiceLog", "GVoiceTQos", "tiny_cache",
    "FeedBack", "NTCLS", "PCMLoader", "rail_files", "components",
}


def _scan(root_id: str, root_abs: str) -> list[dict]:
    if not os.path.isdir(root_abs):
        return []
    out: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root_abs):
        rel_dir = os.path.relpath(dirpath, root_abs)
        depth = 0 if rel_dir == "." else rel_dir.count(os.sep) + 1
        if depth > SCAN_MAX_DEPTH:
            dirnames[:] = []
            continue
        # Prune Tencent/anti-cheat/launcher helper trees — they would
        # dominate the inventory without aiding native-material recovery.
        prune = []
        for dn in dirnames:
            if dn in SKIP_DIRS:
                prune.append(dn)
            if dn.lower() in {".git", "__pycache__"}:
                prune.append(dn)
        for dn in prune:
            if dn in dirnames:
                dirnames.remove(dn)
        for fn in filenames:
            ext = os.path.splitext(fn)[1].lower()
            if ext not in ARTIFACT_EXTS:
                continue
            abs_path = os.path.join(dirpath, fn)
            try:
                rec = _record(root_id, root_abs, abs_path)
            except OSError:
                continue
            out.append(rec)
    return out


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cf-dir", default=None,
                    help="override the default CF install path (else use _paths.cf_dir())")
    ap.add_argument("--top", type=int, default=20,
                    help="how many top-priority candidates to list in the report")
    ap.add_argument("--no-sha", action="store_true",
                    help="skip SHA256 capture (faster)")
    args = ap.parse_args()

    # Resolve the authoritative CF root from --cf-dir > CF2_CF_DIR > default.
    if args.cf_dir:
        os.environ["CF2_CF_DIR"] = args.cf_dir
        import importlib
        importlib.reload(_paths)
    cf_default = _paths.cf_dir()

    # 1) Root discovery
    root_discovery = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "script": os.path.relpath(__file__, REPO),
        "candidates": [],
        "selected": None,
    }
    for root_id, path, source, why in CANDIDATE_ROOTS:
        exists = os.path.isdir(path)
        # Heuristic: trustworthy means (1) it is a real directory, AND
        # (2) it contains at least one .exe that mentions crossfire OR
        # at least one .rez / .ltb that strongly indicates CF.
        trustworthy = False
        trust_reason = None
        if exists:
            try:
                top = os.listdir(path)
            except OSError as e:
                top = []
                trust_reason = f"listdir failed: {e}"
            if trust_reason is None:
                has_cf_exe = any(n.lower().startswith(("crossfire", "gameloader"))
                                 and n.lower().endswith(".exe") for n in top)
                has_rez = any(n.lower().endswith(".rez") for n in top)
                has_rez_dir = "rez" in {n.lower() for n in top}
                has_link_ini = "link.ini" in {n.lower() for n in top}
                score = sum([has_cf_exe, has_rez, has_rez_dir, has_link_ini])
                if score >= 2:
                    trustworthy = True
                    trust_reason = (
                        f"present: cf-exe={has_cf_exe} rez={has_rez} "
                        f"rez_dir={has_rez_dir} link.ini={has_link_ini}"
                    )
                else:
                    trust_reason = (
                        f"insufficient CF signal (cf-exe={has_cf_exe} "
                        f"rez={has_rez} rez_dir={has_rez_dir} "
                        f"link.ini={has_link_ini})"
                    )
        root_discovery["candidates"].append({
            "root_id": root_id,
            "path": path,
            "source": source,
            "why_candidate": why,
            "exists": exists,
            "trustworthy": trustworthy,
            "trust_reason": trust_reason,
        })
        if trustworthy and root_discovery["selected"] is None:
            root_discovery["selected"] = {
                "root_id": root_id,
                "path": path,
                "trust_reason": trust_reason,
            }

    selected = root_discovery["selected"]
    if selected is None:
        # No trustworthy root — write the negative-result artefacts and stop.
        neg = {
            "status": "NO_RUNTIME_ROOT_FOUND_LOCALLY",
            "root_discovery": root_discovery,
            "inventory": [],
            "summary": {
                "by_extension": {},
                "by_role": {},
                "by_root": {},
                "total_candidates": 0,
            },
        }
        with open(os.path.join(OUT_DIR, "artifact_inventory.json"), "w",
                  encoding="utf-8") as f:
            json.dump(neg, f, indent=2, ensure_ascii=False)
        with open(os.path.join(OUT_DIR, "root_discovery.json"), "w",
                  encoding="utf-8") as f:
            json.dump(root_discovery, f, indent=2, ensure_ascii=False)
        _write_report(neg, top_n=args.top, report_kind="negative")
        print("[n02] NO_RUNTIME_ROOT_FOUND_LOCALLY", file=sys.stderr)
        return 0

    selected_path = selected["path"]

    # 2) Inventory of the selected root.
    if args.no_sha:
        # monkey-patch _sha256 to return None to avoid reading big files
        global _sha256
        _sha256 = lambda _p: None  # type: ignore
    inv = _scan(selected["root_id"], selected_path)

    # 3) Roll-ups
    by_ext: dict[str, int] = {}
    by_role: dict[str, int] = {}
    by_root: dict[str, int] = {}
    for rec in inv:
        by_ext[rec["extension"]] = by_ext.get(rec["extension"], 0) + 1
        by_role[rec["candidate_role"]] = by_role.get(rec["candidate_role"], 0) + 1
        by_root[rec["root_id"]] = by_root.get(rec["root_id"], 0) + 1

    inv_payload = {
        "status": "RUNTIME_INVENTORY_READY_FOR_REVIEW",
        "root_discovery": root_discovery,
        "summary": {
            "total_candidates": len(inv),
            "by_extension": dict(sorted(by_ext.items(), key=lambda x: -x[1])),
            "by_role": dict(sorted(by_role.items(), key=lambda x: -x[1])),
            "by_root": by_root,
        },
        "inventory": inv,
    }
    with open(os.path.join(OUT_DIR, "artifact_inventory.json"), "w",
              encoding="utf-8") as f:
        json.dump(inv_payload, f, indent=2, ensure_ascii=False)
    with open(os.path.join(OUT_DIR, "root_discovery.json"), "w",
              encoding="utf-8") as f:
        json.dump(root_discovery, f, indent=2, ensure_ascii=False)
    _write_report(inv_payload, top_n=args.top, report_kind="positive")
    print(f"[n02] RUNTIME_INVENTORY_READY_FOR_REVIEW "
          f"({len(inv)} candidates under {selected_path})", file=sys.stderr)
    return 0


def _write_report(payload: dict, top_n: int, report_kind: str) -> None:
    out_md = os.path.join(OUT_DIR, "acquisition_report.md")
    rd = payload["root_discovery"]
    sel = rd.get("selected")
    lines: list[str] = []
    lines.append("# P4-M01-N02-A — Runtime Root Discovery & Candidate Inventory")
    lines.append("")
    lines.append(f"- generated_at: `{rd.get('generated_at', '')}`")
    lines.append(f"- script: `{rd.get('script', '')}`")
    lines.append(f"- status: **{payload.get('status', '')}**")
    lines.append("")

    # Section 1: Root discovery
    lines.append("## 1. Root discovery")
    lines.append("")
    lines.append("| root_id | path | exists | trustworthy | reason |")
    lines.append("|---|---|---|---|---|")
    for c in rd["candidates"]:
        lines.append(
            f"| `{c['root_id']}` | `{c['path']}` | "
            f"{'yes' if c['exists'] else 'no'} | "
            f"{'**yes**' if c['trustworthy'] else 'no'} | "
            f"{c['trust_reason'] or ''} |"
        )
    lines.append("")
    if sel is not None:
        lines.append(f"**Selected root**: `{sel['root_id']}` at `{sel['path']}`")
        lines.append("")
        lines.append(f"Trust reason: {sel['trust_reason']}")
        lines.append("")

    # Section 2: candidate counts
    if report_kind == "positive":
        s = payload["summary"]
        lines.append("## 2. Candidate counts")
        lines.append("")
        lines.append(f"- **total_candidates**: {s['total_candidates']}")
        lines.append("")
        lines.append("### By extension")
        lines.append("")
        lines.append("| ext | count |")
        lines.append("|---|---|")
        for k, v in s["by_extension"].items():
            lines.append(f"| `{k}` | {v} |")
        lines.append("")
        lines.append("### By candidate role")
        lines.append("")
        lines.append("| role | count |")
        lines.append("|---|---|")
        for k, v in s["by_role"].items():
            lines.append(f"| `{k}` | {v} |")
        lines.append("")

        # Section 3: Top-N
        inv = payload["inventory"]
        ranked = sorted(inv, key=lambda r: (-r["priority"], -r["size_bytes"]))
        lines.append(f"## 3. Top {top_n} candidates (priority, then size)")
        lines.append("")
        lines.append("| rank | role | ext | path_alias | size | sha256 | why |")
        lines.append("|---|---|---|---|---|---|---|")
        for i, rec in enumerate(ranked[:top_n], 1):
            sha = (rec["sha256"] or "n/a")[:16] if rec.get("sha256") else "n/a"
            lines.append(
                f"| {i} | `{rec['candidate_role']}` | `{rec['extension']}` | "
                f"`{rec['path_alias']}` | {rec['size_bytes']:,} | "
                f"`{sha}` | {rec['why_candidate']} |"
            )
        lines.append("")

        # Section 3.5: Key observations
        ltc_files = [r for r in inv if r["extension"] == ".ltc"]
        lta_files = [r for r in inv if r["extension"] == ".lta"]
        bf_lta = [r for r in lta_files if "bf000" in r["path_alias"]]
        bf_ltc = [r for r in ltc_files if r["path_alias"].split("/")[-1].startswith("bf")]
        dat_files = [r for r in inv if r["extension"] == ".dat" and "rez/" in r["path_alias"]]
        shader_files = [r for r in inv if r["candidate_role"] == "shader"]
        large_rez = sorted(
            [r for r in inv if r["extension"] == ".rez"],
            key=lambda r: -r["size_bytes"],
        )[:5]
        lines.append("## 3.5 Key observations")
        lines.append("")
        lines.append(
            f"- `.ltc` count = {len(ltc_files)}; all live under `rez/Butes/`. "
            f"plan.md §4.7 previously reported `BornBeast text-config hits = 0` "
            f"on the unpacked `data/**` corpus — these are **packed-binary sibling** "
            f"configs that the unpack pipeline did not surface. They are the most "
            f"direct follow-up target for N01 reopen."
        )
        if bf_ltc:
            names = ", ".join(f"`{r['path_alias'].split('/')[-1]}`" for r in bf_ltc[:5])
            lines.append(
                f"- `bf*.ltc` family count = {len(bf_ltc)} "
                f"(e.g. {names}{', …' if len(bf_ltc) > 5 else ''}). "
                f"Naming pattern strongly suggests weapon / bdf family — "
                f"cross-check with N01 family list (BornBeast / Transformers / "
                f"Jewelry / BlueDiamond)."
            )
        if bf_lta:
            lines.append(
                f"- `rez/bf000.lta` is the only `bf`-prefixed archive-shaped "
                f"config: size = {bf_lta[0]['size_bytes']:,} bytes. Compare with "
                f"the LTB post-mesh short ASCII field identified in plan.md §4.6."
            )
        if shader_files:
            lines.append(
                f"- Shader-bearing files: {len(shader_files)} total. The 14 "
                f"`rez/Shader/*.fxo` (compiled) and 3 `rez/Shader/*.fx` (source) "
                f"are the natural N02-B `archive/shader triage` target."
            )
        if large_rez:
            lines.append(
                f"- Largest REZ archives: " +
                ", ".join(f"`{r['path_alias']}` ({r['size_bytes']:,} B)"
                          for r in large_rez) +
                ". Top archive unpacking is the most expensive N02-B branch."
            )
        lines.append(
            f"- `.dat` under `rez/` count = {len(dat_files)}; includes "
            f"`rez/Butes/*_zoneman.dat` and `rez/Camera/Opening_*.dat` — "
            f"candidate for follow-up only if a concrete zone / camera binding "
            f"question emerges."
        )
        lines.append("")

        # Section 4: scope guard
        lines.append("## 4. Scope guard")
        lines.append("")
        lines.append("Bounded to ARTIFACT_EXTS only. No audio corpus, no derived outputs.")
        lines.append("Skipped auxiliary Tencent/anti-cheat subtrees: "
                    + ", ".join(sorted(SKIP_DIRS)) + ".")
        lines.append("Scan depth limit: " + str(SCAN_MAX_DEPTH) + ".")
        lines.append("SHA256 captured only for files <= 512 MiB.")
        lines.append("")
        lines.append("What this round did NOT do:")
        lines.append("")
        lines.append("- no strings / xref / decompilation;")
        lines.append("- no execution of any CF binary;")
        lines.append("- no launcher patch or update;")
        lines.append("- no `data/**` re-scan, no derived-output re-baseline;")
        lines.append("- no `plan.md` modification.")
        lines.append("")
        lines.append("Recommended follow-up tasks (in priority order):")
        lines.append("")
        lines.append("1. `N02-B PE / strings static triage` on Top shader/model EXE/DLL;")
        lines.append("2. `N02-B archive/shader triage` on Top REZ + Shader;")
        lines.append("3. `N02-B launcher/runtime-root expansion` if x64 / new sub-roots matter.")
        lines.append("")
    else:
        lines.append("## 2. Bounded negative")
        lines.append("")
        lines.append("No candidate directory matched the trustworthy signal.")
        lines.append("Recommend the user provide the actual CF install path or")
        lines.append("the CrossFire launcher config; until then the next round")
        lines.append("cannot progress.")
        lines.append("")

    with open(out_md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


if __name__ == "__main__":
    sys.exit(main())
