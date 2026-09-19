#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N04-C — Read-only strings/metadata from playerviewmesh.fxo."""
from __future__ import annotations

import hashlib
import json
import lzma
import os
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n04c_playerviewmesh_fxo"
)
INVENTORY = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/artifact_inventory.json"
)

TARGETS = [
    "rez/Shader/playerviewmesh.fxo",
    "rez/Shader/playermesh.fxo",
]

TOKENS = [
    "WeaponShader",
    "AlphaMap",
    "NormalMap",
    "SpecularMap",
    "PlayerViewMesh",
    "playerviewmesh",
    "tPlayerViewMesh",
    ".CFG",
    ".cfg",
    ".TGA",
    ".tga",
    ".DTX",
    ".dtx",
    "MODELTEXTURES",
    "ModelTextures",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def inventory_sha(rel: str) -> str | None:
    if not INVENTORY.exists():
        return None
    dump = json.loads(INVENTORY.read_text(encoding="utf-8"))
    needle = rel.replace("\\", "/").lower()
    for row in dump.get("inventory") or []:
        alias = str(row.get("path_alias") or "").replace("\\", "/").lower()
        if alias == needle:
            return row.get("sha256")
    return None


def try_lzma(data: bytes) -> tuple[bytes, str]:
    if data[:4] == b"DXBC" or data[:4] == b"DXBC"[::-1]:
        return data, "raw"
    # CF often wraps with LZMA-alone
    for fmt, label in ((lzma.FORMAT_ALONE, "lzma_alone"), (lzma.FORMAT_AUTO, "lzma_auto")):
        try:
            out = lzma.decompress(data, format=fmt)
            if out:
                return out, label
        except lzma.LZMAError:
            continue
    # skip 4/8 byte size prefix
    for skip in (4, 8):
        if len(data) <= skip:
            continue
        try:
            out = lzma.decompress(data[skip:], format=lzma.FORMAT_ALONE)
            if out:
                return out, f"lzma_alone_skip{skip}"
        except lzma.LZMAError:
            continue
    return data, "raw"


def extract_ascii(data: bytes, min_len: int = 4) -> list[str]:
    out: list[str] = []
    i = 0
    n = len(data)
    while i < n:
        if 32 <= data[i] < 127:
            j = i + 1
            while j < n and 32 <= data[j] < 127:
                j += 1
            if j - i >= min_len:
                out.append(data[i:j].decode("ascii"))
            i = j
        else:
            i += 1
    return out


def extract_utf16le(data: bytes, min_len: int = 4) -> list[str]:
    out: list[str] = []
    i = 0
    n = len(data)
    while i + 1 < n:
        if 32 <= data[i] < 127 and data[i + 1] == 0:
            chars = [data[i]]
            j = i + 2
            while j + 1 < n and 32 <= data[j] < 127 and data[j + 1] == 0:
                chars.append(data[j])
                j += 2
            if len(chars) >= min_len:
                out.append(bytes(chars).decode("ascii"))
            i = j
        else:
            i += 1
    return out


def interesting(s: str) -> bool:
    sl = s.lower()
    keys = (
        "shader",
        "texture",
        "sampler",
        "alpha",
        "normal",
        "specular",
        "weapon",
        "player",
        "view",
        "mesh",
        "cfg",
        "tga",
        "dtx",
        "map",
        "emissive",
        "diffuse",
        "slot",
        "cbuffer",
        "tplayer",
        "g_",
        "tx",
    )
    return any(k in sl for k in keys)


def token_hits(strings: list[str]) -> list[dict]:
    hits = []
    for s in strings:
        sl = s.lower()
        matched = [t for t in TOKENS if t.lower() in sl]
        if matched:
            hits.append({"text": s[:240], "tokens": matched})
    return hits


def dxbc_info(data: bytes) -> dict:
    magic = data[:4]
    info = {"magic": magic.decode("latin-1", errors="replace"), "is_dxbc": magic == b"DXBC"}
    if magic == b"DXBC" and len(data) >= 32:
        info["file_size_field"] = struct.unpack_from("<I", data, 24)[0]
        info["chunk_count"] = struct.unpack_from("<I", data, 28)[0]
        count = min(info["chunk_count"], 16)
        chunks = []
        for i in range(count):
            off = 32 + i * 4
            if off + 4 > len(data):
                break
            chunk_off = struct.unpack_from("<I", data, off)[0]
            if chunk_off + 8 <= len(data):
                fourcc = data[chunk_off : chunk_off + 4].decode("latin-1", errors="replace")
                size = struct.unpack_from("<I", data, chunk_off + 4)[0]
                chunks.append({"fourcc": fourcc, "offset": chunk_off, "size": size})
        info["chunks"] = chunks
    return info


def scan_file(rel: str) -> dict:
    path = CF / rel.replace("/", os.sep)
    rec = {"relative": rel, "present": path.exists()}
    if not path.exists():
        rec["status"] = "missing"
        return rec
    raw = path.read_bytes()
    rec["size_bytes"] = len(raw)
    rec["sha256"] = hashlib.sha256(raw).hexdigest()
    rec["inventory_sha256"] = inventory_sha(rel)
    rec["sha_matches_inventory"] = rec["sha256"] == rec["inventory_sha256"]
    rec["head16_hex"] = raw[:16].hex()
    body, wrap = try_lzma(raw)
    rec["unwrap"] = wrap
    rec["unwrapped_size"] = len(body)
    rec["unwrapped_head16_hex"] = body[:16].hex()
    rec["dxbc"] = dxbc_info(body)
    ascii_s = extract_ascii(body)
    utf_s = extract_utf16le(body)
    rec["ascii_string_count"] = len(ascii_s)
    rec["utf16_string_count"] = len(utf_s)
    rec["token_hits"] = token_hits(ascii_s + utf_s)
    interesting_s = [s for s in ascii_s if interesting(s)]
    # unique preserve
    seen = set()
    uniq = []
    for s in interesting_s:
        if s in seen:
            continue
        seen.add(s)
        uniq.append(s[:200])
    rec["interesting_strings"] = uniq[:80]
    rec["path_like"] = [
        s[:200]
        for s in ascii_s
        if ("\\" in s or "/" in s) and any(x in s.lower() for x in ("shader", "texture", "map", "cfg", "tga", "dtx"))
    ][:40]
    return rec


def classify(rows: list[dict]) -> str:
    if not rows or all(r.get("status") == "missing" for r in rows):
        return "REWORK_REQUIRED"
    pv = next((r for r in rows if "playerviewmesh" in r["relative"].lower()), rows[0])
    if pv.get("status") == "missing":
        return "REWORK_REQUIRED"
    hits = pv.get("token_hits") or []
    pathish = False
    generic = False
    for h in hits:
        joined = " ".join(h.get("tokens") or [])
        text = h.get("text") or ""
        if any(t in joined for t in ("WeaponShader", "AlphaMap", "NormalMap", "SpecularMap")) and any(
            x in text for x in ("\\", "/", ".CFG", ".cfg", ".TGA", ".tga", ".DTX", ".dtx")
        ):
            pathish = True
        if "WeaponShader" in joined or "AlphaMap" in joined:
            if "\\" in text or "/" in text or ".CFG" in text or ".cfg" in text:
                pathish = True
        if any(t in joined for t in ("PlayerViewMesh", "playerviewmesh", "tPlayerViewMesh")):
            generic = True
        if "WeaponShader" in joined:
            pathish = True
    if pathish:
        return "FXO_NAMES_WEAPONSHADER"
    if generic or pv.get("interesting_strings"):
        return "FXO_NAMES_GENERIC"
    return "FXO_NO_USEFUL_STRINGS"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = [scan_file(rel) for rel in TARGETS]
    status = classify(rows)
    report = {
        "schema": "cf2.p4m01.n04c-playerviewmesh-fxo.v1",
        "generated_at_utc": now(),
        "status": status,
        "files": rows,
        "note": "FXO binaries are not copied into the repo. Bytecode is not decompiled.",
    }
    (OUT / "fxo_scan.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "files": [r["relative"] for r in rows]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
