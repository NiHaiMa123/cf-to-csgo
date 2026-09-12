# -*- coding: utf-8 -*-
"""P5-T03 resource graph for USER_VISUAL_MATCH base Transformers (雷神).

Chain:
  PLAYERVIEW LTB
  -> texture / material / shader
  -> world / QV
  -> audio
  -> animation / config

Each node records path / SHA / size / relation / source / confidence.
Uses the N05-C MD5-verified reader. Does not write IDENTITY_CONFIRMED,
does not deploy, and does not treat filename Transformers as identity.
"""
from __future__ import annotations

import configparser
import hashlib
import json
import lzma
import os
import re
import struct
import sys
from collections import defaultdict
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
import n02_butes_config_triage as n02b  # noqa: E402
import n03a_bornbeast_consumer as n03a  # noqa: E402
import n03b_rez_packed_config as n03b  # noqa: E402
import n03d_ltb_piece_index as n03d  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / "work" / "p5_leishen" / "t03"
VISUAL_MATCH = REPO / "work" / "p5_leishen" / "t02_native" / "visual_match.json"
GEOM_JSON = (
    REPO / "data" / "p5_t02_native" / "geom" / "PV-M4A1_S_TRANSFORMERS_a0ccef5deed7.geometry.json"
)

IDENTITY_STEM = "M4A1_S_TRANSFORMERS"
IDENTITY_PV_LTB = "MODELS/PLAYERVIEW/PV-M4A1_S_TRANSFORMERS.LTB"
IDENTITY_PV_DTX = "MODELTEXTURES/PLAYERVIEW/PV-M4A1_S_TRANSFORMERS.DTX"
CUBE_NAME = "BLACK_SHADER02.DDS"
SHARED_RS_NAMES = {"NINJATRANSLUCENT.LTB", "PVMODELDEFAULT.LTB"}

FAMILY_RE = re.compile(r"TRANSFORMERS|LEISHEN|LEI[_-]?SHEN|THUNDER|THOR", re.I)
ANIM_HINT_RE = re.compile(
    r"(idle|fire|shoot|reload|draw|holster|inspect|select|deselect|"
    r"walk|run|sprint|melee|bash|empty|deploy|putaway|alt)",
    re.I,
)
IDENT_CHARS = set("ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-")

IMAGE_EXT = {".DTX", ".TGA", ".DDS", ".SPR"}
MODEL_EXT = {".LTB"}
SHADER_EXT = {".CFG"}
AUDIO_EXT = {".WAV", ".OGG", ".MP3", ".BANK"}
CONFIG_EXT = {".LTC", ".LTA", ".INI", ".TXT", ".CFT", ".XML"}
KEEP_EXT = IMAGE_EXT | MODEL_EXT | SHADER_EXT | AUDIO_EXT | CONFIG_EXT

PREFIXES = (
    "PV-FD_",
    "PV-BB_",
    "QV-FD_",
    "QV-BB_",
    "PV-",
    "QV-",
    "WEAPON_SELECT_FD_",
    "WEAPON_SELECT_BB_",
    "SHOT_WEAPON_FD_",
    "SHOT_WEAPON_BB_",
    "WEAPON_SELECT_",
    "SHOT_WEAPON_",
    "BUYWEAPON_INFO_",
    "BUYWEAPON_",
)

MAP_SUFFIXES = {"_S", "_N", "_ALPHA", "_ALPHAMAP"}
GENDER_SUFFIXES = {"_GR", "_BL", "_WOMAN", "_WOMAN_GR", "_WOMAN_BL", "_PREVIEW"}
WEAPON_SNAPSHOT_FIELDS = n03b.WEAPON_SNAPSHOT_FIELDS + (
    "PreViewModelFileName",
    "PreViewSkinFileName",
    "HHWeaponModel",
    "SoundFileName",
    "FireSoundFileName",
    "ReloadSoundFileName",
    "SelectSoundFileName",
    "DeselectSoundFileName",
    "EmptySoundFileName",
    "AltFireSoundFileName",
    "AnimationName",
    "PVAnimation",
    "WeaponId",
    "Id",
)
PAYLOAD_MAX = 16 * 1024 * 1024
CONFIG_RECOVER_MAX = 32 * 1024 * 1024


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def rel(path: Path | str) -> str:
    path = Path(path)
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def logical_key(value: str) -> str:
    return extract_all.logical_path_key(value)


def archive_label(index_path: str) -> str:
    try:
        return os.path.relpath(index_path, CF).replace("\\", "/")
    except ValueError:
        return os.path.basename(index_path)


def strip_prefix(stem: str) -> str:
    upper = stem.upper()
    for prefix in PREFIXES:
        if upper.startswith(prefix):
            return upper[len(prefix) :]
    return upper


def classify_role(full_path: str) -> str:
    key = logical_key(full_path)
    suffix = Path(key.replace("\\", "/")).suffix
    if "/PLAYERVIEW/" in key and suffix == ".LTB":
        return "pv_ltb"
    if "/WEAPONS/" in key and suffix == ".LTB":
        return "qv_ltb"
    if "/PLAYERVIEW/" in key and suffix == ".DTX":
        return "pv_dtx"
    if "/WEAPONS/" in key and suffix == ".DTX":
        return "qv_dtx"
    if "/NORMALMAP/" in key:
        return "normal"
    if "/SPECULARMAP/" in key:
        return "specular"
    if "/ALPHAMAP/" in key:
        return "alpha"
    if "/WEAPONSHADER/" in key and suffix == ".CFG":
        return "weapon_shader_cfg"
    if "/ENVCUBEMAP/" in key:
        return "env_cube"
    if "/WEAPONICON/" in key or "/KILLMSG/" in key or "/BUYWEAPON" in key:
        return "ui_icon"
    if suffix in AUDIO_EXT:
        return "audio"
    if suffix in CONFIG_EXT:
        if key.startswith("BUTES/") or "/BUTES/" in key:
            return "packed_bute"
        if key.startswith("TABLE/") or "/TABLE/" in key:
            return "table_config"
        return "config"
    if suffix == ".LTB":
        return "other_ltb"
    if suffix == ".DTX":
        return "other_dtx"
    return "other"


def identity_bucket(full_path: str) -> str:
    name = Path(full_path.replace("\\", "/")).name
    stem = Path(name).stem.upper()
    suffix = Path(name).suffix.upper()
    if name.upper() == CUBE_NAME or stem == Path(CUBE_NAME).stem:
        return "shared_cube"
    stripped = strip_prefix(stem)
    if stripped == IDENTITY_STEM:
        return "identity_core"
    if stripped == IDENTITY_STEM + "_PC":
        return "identity_alias"
    for map_suffix in MAP_SUFFIXES:
        if stripped == IDENTITY_STEM + map_suffix:
            return "identity_core"
    for extra in GENDER_SUFFIXES:
        if stripped == IDENTITY_STEM + extra:
            return "related_variant"
    if stripped.startswith(IDENTITY_STEM + "_") or IDENTITY_STEM in stripped:
        return "related_variant"
    if IDENTITY_STEM in logical_key(full_path):
        return "related_variant"
    if FAMILY_RE.search(full_path):
        return "family_other"
    return "unrelated"


def bounded_token_hit(text: str, token: str) -> list[dict[str, Any]]:
    return n03a.find_token_hits(text, token, "stem", cap=12)


def parse_cfg(data: bytes) -> dict[str, Any]:
    text = data.decode("ascii", errors="replace")
    parser = configparser.ConfigParser(strict=False)
    parser.optionxform = str
    parser.read_string(text)
    return {section: dict(parser[section]) for section in parser.sections()}


def maybe_lzma(data: bytes) -> tuple[bytes, bool]:
    if data[:1] != b"\x5d":
        return data, False
    try:
        return lzma.decompress(data, format=lzma.FORMAT_ALONE), True
    except lzma.LZMAError:
        return data, False


def ascii_strings(data: bytes, min_len: int = 4) -> list[str]:
    out: list[str] = []
    buf = bytearray()
    for byte in data:
        if 32 <= byte < 127:
            buf.append(byte)
        else:
            if len(buf) >= min_len:
                out.append(buf.decode("ascii"))
            buf = bytearray()
    if len(buf) >= min_len:
        out.append(buf.decode("ascii"))
    seen: set[str] = set()
    unique: list[str] = []
    for item in out:
        if item not in seen:
            seen.add(item)
            unique.append(item)
    return unique


def decode_ltc(data: bytes) -> dict[str, Any]:
    unlocked = n02b.try_unlock_crossfire_payload(data)
    if unlocked is None:
        return {
            "ok": False,
            "reason": "wrapper_no_match",
            "text": n03a.extract_ascii_and_utf16le(data),
        }
    try:
        decoded = n02b._decode_ltc_c_sharp(unlocked)
    except n02b.LtcDecodeFailure as exc:
        return {
            "ok": False,
            "reason": str(exc),
            "text": n03a.extract_ascii_and_utf16le(data),
        }
    return {
        "ok": True,
        "reason": "DECODED",
        "text": decoded.decode("latin-1", errors="replace"),
        "decoded_size": len(decoded),
    }


def should_keep_index_entry(full_path: str) -> bool:
    suffix = Path(full_path).suffix.upper()
    if suffix not in KEEP_EXT:
        return False
    key = logical_key(full_path)
    name = Path(full_path.replace("\\", "/")).name.upper()
    if name == CUBE_NAME or name in SHARED_RS_NAMES:
        return True
    if key.endswith("/" + CUBE_NAME) or key.endswith(CUBE_NAME):
        return True
    if FAMILY_RE.search(full_path):
        return True
    if suffix in CONFIG_EXT and (
        key.startswith("BUTES/") or "/BUTES/" in key or key.startswith("TABLE/") or "/TABLE/" in key
    ):
        return True
    return False


def scan_indexes() -> tuple[list[dict[str, Any]], list[dict[str, Any]], int]:
    indexes = extract_all.discover_index_archives(str(CF))
    hits: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception as exc:
            errors.append({"index": index_path, "error": str(exc)})
            continue
        for entry in entries:
            full = str(entry.get("full_path") or "")
            if not should_keep_index_entry(full):
                continue
            hits.append(
                {
                    "index_archive": index_path,
                    "archive": archive_label(index_path),
                    "full_path": full,
                    "logical_key": logical_key(full),
                    "name": Path(full.replace("\\", "/")).name,
                    "data_offset": int(entry["data_offset"]),
                    "size": int(entry["size"]),
                    "time": int(entry["time"]),
                    "directory_md5": str(entry.get("md5") or "").lower(),
                    "md5_complete": is_complete_directory_md5(entry.get("md5")),
                    "role": classify_role(full),
                    "bucket": identity_bucket(full),
                    "suffix": Path(full).suffix.upper(),
                }
            )
    return hits, errors, len(indexes)


def recover_one(hit: dict[str, Any]) -> dict[str, Any]:
    entry = {
        "full_path": hit["full_path"],
        "data_offset": hit["data_offset"],
        "size": hit["size"],
        "time": hit["time"],
        "md5": hit["directory_md5"],
    }
    data, provenance = read_verified_payload(hit["index_archive"], entry)
    body, lzma_used = maybe_lzma(data) if hit["suffix"] == ".LTB" else (data, False)
    row = {
        **hit,
        "payload_sha256": provenance["sha256"],
        "routing": provenance["routing"],
        "payload_file": provenance["payload_file"],
        "lzma": lzma_used,
        "payload_bytes": len(data),
        "decoded_bytes": len(body),
        "body": body,
        "raw": data,
    }
    return row


def recover_needed(hits: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for hit in hits:
        if hit["bucket"] in {"identity_core", "identity_alias", "shared_cube"} or hit["name"].upper() in SHARED_RS_NAMES:
            grouped[hit["directory_md5"] or f"no-md5:{hit['index_archive']}:{hit['logical_key']}"].append(hit)
        elif hit["role"] in {"audio"} and hit["bucket"] != "unrelated":
            grouped[hit["directory_md5"] or f"no-md5:{hit['index_archive']}:{hit['logical_key']}"].append(hit)
        elif hit["role"] in {"packed_bute", "table_config"}:
            if hit["size"] <= CONFIG_RECOVER_MAX:
                grouped[hit["directory_md5"] or f"no-md5:{hit['index_archive']}:{hit['logical_key']}"].append(hit)
        elif hit["role"] in {"pv_ltb", "qv_ltb"} and hit["bucket"] == "related_variant":
            stripped = strip_prefix(Path(hit["name"]).stem)
            if stripped == IDENTITY_STEM or any(stripped == IDENTITY_STEM + extra for extra in GENDER_SUFFIXES):
                grouped[hit["directory_md5"] or f"no-md5:{hit['index_archive']}:{hit['logical_key']}"].append(hit)
    recovered: list[dict[str, Any]] = []
    failures: list[dict[str, Any]] = []
    for digest, group in grouped.items():
        first = group[0]
        if not first["md5_complete"]:
            failures.append({"reason": "incomplete_directory_md5", "hit": {k: first[k] for k in first if k != "body"}})
            continue
        try:
            row = recover_one(first)
        except Exception as exc:
            failures.append({"reason": str(exc), "hit": {k: first[k] for k in first}})
            continue
        row["copy_count"] = len(group)
        row["copies"] = [
            {
                "archive": item["archive"],
                "full_path": item["full_path"],
                "payload_hint_time": item["time"],
                "size": item["size"],
                "bucket": item["bucket"],
            }
            for item in group
        ]
        recovered.append(row)
    return recovered, failures


def ltb_animation_view(body: bytes, geom_path: Path | None) -> dict[str, Any]:
    view: dict[str, Any] = {
        "header": None,
        "mesh_names": [],
        "ascii_anim_like": [],
        "ascii_other": [],
        "geometry_json": None,
    }
    try:
        header = n03d.parse_jupiter_header(body)
        view["header"] = {
            "file_type": header["file_type"],
            "file_type_name": header["file_type_name"],
            "ltb_header_version": header["ltb_header_version"],
            "model_file_version": header["model_file_version"],
            "allocs": header["allocs"],
        }
    except Exception as exc:
        view["header_error"] = str(exc)
    if geom_path and geom_path.is_file():
        document = json.loads(geom_path.read_text(encoding="utf-8"))
        meshes = document.get("meshes") or []
        view["geometry_json"] = {
            "path": rel(geom_path),
            "vertex_count": document.get("vertex_count"),
            "triangle_count": document.get("triangle_count"),
            "mesh_count": len(meshes),
        }
        view["mesh_names"] = [
            {
                "name": mesh.get("name"),
                "vertex_count": len(mesh.get("vertices") or []),
                "triangle_count": len(mesh.get("triangle_indices") or []) // 3,
            }
            for mesh in meshes
        ]
    strings = ascii_strings(body, min_len=4)
    mesh_set = {str(item["name"]) for item in view["mesh_names"] if item.get("name")}
    anim_like: list[str] = []
    other: list[str] = []
    for item in strings:
        if item in mesh_set:
            continue
        if len(item) > 64:
            continue
        if ANIM_HINT_RE.search(item):
            anim_like.append(item)
        elif re.fullmatch(r"[A-Za-z][A-Za-z0-9_\-]{2,47}", item):
            other.append(item)
    view["ascii_anim_like"] = anim_like[:80]
    view["ascii_other"] = other[:80]
    view["ascii_string_count"] = len(strings)
    return view


def search_config_payload(row: dict[str, Any], tokens: list[str]) -> dict[str, Any]:
    data = row["raw"]
    suffix = row["suffix"]
    out: dict[str, Any] = {
        "full_path": row["full_path"],
        "archive": row["archive"],
        "role": row["role"],
        "payload_sha256": row["payload_sha256"],
        "size": row["size"],
        "decode_ok": False,
        "hits": [],
        "weapon_snapshots": [],
    }
    text = ""
    if suffix == ".LTC":
        decoded = decode_ltc(data)
        out["decode_ok"] = decoded["ok"]
        out["decode_reason"] = decoded["reason"]
        text = decoded.get("text") or ""
        if decoded["ok"]:
            records = n03a.parse_lisp_all_keys(text)
            out["record_count"] = len(records)
            snapped: set[int] = set()
            for rec_i, block in enumerate(records):
                record_hit = False
                for key, value in block.items():
                    if key == "_head" or not isinstance(value, str):
                        continue
                    for token in tokens:
                        found = n03a.find_token_hits(value, token, "stem", cap=4)
                        if not found:
                            continue
                        record_hit = True
                        out["hits"].append(
                            {
                                "record_index": rec_i,
                                "head": block.get("_head", ""),
                                "field": key,
                                "value": value,
                                "token": token,
                                "identity_name": block.get("WeaponName") or block.get("Name") or "",
                                "identity_name_gbk": n03b.gbk_display(
                                    str(block.get("WeaponName") or block.get("Name") or "")
                                ),
                            }
                        )
                if record_hit and rec_i not in snapped:
                    snapped.add(rec_i)
                    snap = {"record_index": rec_i, "head": block.get("_head", "")}
                    extra_fields = [
                        key
                        for key in block
                        if key != "_head"
                        and (
                            key in WEAPON_SNAPSHOT_FIELDS
                            or "Sound" in key
                            or "Anim" in key
                            or key.endswith("FileName")
                            or key in {"WeaponId", "Id", "Name", "Description"}
                        )
                    ]
                    for field in extra_fields:
                        value = block.get(field)
                        if not isinstance(value, str):
                            continue
                        snap[field] = value
                        snap[field + "_gbk"] = n03b.gbk_display(value)
                    out["weapon_snapshots"].append(snap)
    else:
        text = n03a.extract_ascii_and_utf16le(data)
        out["decode_ok"] = True
        out["decode_reason"] = "string_scan"
    if not out["hits"]:
        for token in tokens:
            found = bounded_token_hit(text, token)
            for item in found:
                out["hits"].append({"token": token, **item})
    return out


def scan_loose_banks(tokens: list[str]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    needles = [(token, token.encode("ascii", errors="ignore")) for token in tokens if token.isascii()]
    roots = [CF / "rez" / "FMODStudio", CF / "FMODStudio"]
    for root in roots:
        if not root.is_dir():
            continue
        for path in root.rglob("*.bank"):
            size = path.stat().st_size
            digest = hashlib.sha256()
            found: set[str] = set()
            overlap = b""
            with path.open("rb") as handle:
                while True:
                    chunk = handle.read(4 * 1024 * 1024)
                    if not chunk:
                        break
                    digest.update(chunk)
                    window = overlap + chunk
                    upper = window.upper()
                    for token, needle in needles:
                        if token not in found and needle.upper() in upper:
                            found.add(token)
                    overlap = chunk[-64:]
            hits = [{"token": token, "byte_match": True} for token in sorted(found)]
            if hits or FAMILY_RE.search(path.name):
                try:
                    rel_cf = os.path.relpath(path, CF).replace("\\", "/")
                except ValueError:
                    rel_cf = str(path)
                rows.append(
                    {
                        "path": str(path),
                        "rel_cf": rel_cf,
                        "size": size,
                        "sha256": digest.hexdigest(),
                        "hit_count": len(hits),
                        "hits": hits[:12],
                    }
                )
    return rows


def prefer_identity_core_path(row: dict[str, Any]) -> dict[str, Any]:
    for copy in row.get("copies") or []:
        if copy.get("bucket") == "identity_core":
            row = dict(row)
            row["full_path"] = copy["full_path"]
            row["logical_key"] = logical_key(copy["full_path"])
            row["name"] = Path(copy["full_path"].replace("\\", "/")).name
            row["archive"] = copy.get("archive") or row.get("archive")
            row["bucket"] = "identity_core"
            return row
    if row.get("name", "").upper() in SHARED_RS_NAMES:
        for copy in row.get("copies") or []:
            copy_path = str(copy.get("full_path") or "").replace("\\", "/").upper()
            if copy_path.startswith("RS/"):
                row = dict(row)
                row["full_path"] = copy["full_path"]
                row["logical_key"] = logical_key(copy["full_path"])
                row["name"] = Path(copy["full_path"].replace("\\", "/")).name
                row["archive"] = copy.get("archive") or row.get("archive")
                return row
    return row


def canonical_bute_snapshot(snapshots: list[dict[str, Any]]) -> dict[str, Any] | None:
    exact: list[dict[str, Any]] = []
    for snap in snapshots:
        if snap.get("StandardName") != "M4A1_S_Transformers":
            continue
        if (snap.get("WeaponName_gbk") or "") != "M4A1-雷神":
            continue
        pview = (snap.get("PViewModelFileName") or "").replace("\\", "/").upper()
        if "PV-M4A1_S_TRANSFORMERS" not in pview:
            continue
        if "IRONBEAST" in pview:
            continue
        exact.append(snap)
    return exact[0] if exact else None


def public_row(row: dict[str, Any]) -> dict[str, Any]:
    skip = {"body", "raw"}
    out = {key: value for key, value in row.items() if key not in skip}
    if "payload_file" in out:
        out["payload_file"] = rel(out["payload_file"]) if os.path.isabs(str(out["payload_file"])) else out["payload_file"]
    if "index_archive" in out:
        out["index_archive"] = out.get("archive") or archive_label(out["index_archive"])
    return out


def node(
    node_id: str,
    role: str,
    path: str,
    sha256: str | None,
    size: int | None,
    relation: str,
    source: str,
    confidence: str,
    **extra: Any,
) -> dict[str, Any]:
    row = {
        "id": node_id,
        "role": role,
        "path": path,
        "sha256": sha256,
        "size": size,
        "relation": relation,
        "source": source,
        "confidence": confidence,
    }
    row.update(extra)
    return row


def edge(src: str, dst: str, relation: str, confidence: str, note: str = "") -> dict[str, Any]:
    return {"from": src, "to": dst, "relation": relation, "confidence": confidence, "note": note}


def write_report(graph: dict[str, Any]) -> str:
    lines: list[str] = []
    ident = graph["identity"]
    lines.append("# P5-T03 — 雷神 Resource Graph")
    lines.append("")
    lines.append(f"Result: **{graph['result']}**. Identity remains **not** `IDENTITY_CONFIRMED`.")
    lines.append("")
    lines.append("User 2026-09-13: base `PV-M4A1_S_Transformers` is 雷神 (`USER_VISUAL_MATCH_CONFIRMED`).")
    lines.append("Left/right swap: confirmed fixed in Blender by LTB X scale −1 + reverse faces.")
    lines.append("")
    lines.append("## Identity root")
    lines.append("")
    lines.append(f"- Official: {ident['official']['name']} / item `{ident['official']['itemid']}`")
    lines.append(f"- PV LTB: `{ident['pv_ltb']}` SHA256 `{ident['pv_ltb_sha256']}`")
    lines.append(f"- PV DTX: `{ident['pv_dtx']}` SHA256 `{ident['pv_dtx_sha256']}`")
    lines.append("- `_PC` copies of DTX/CFG are same-bytes aliases, not a second skin.")
    lines.append("")
    lines.append("## Graph")
    lines.append("")
    lines.append("```text")
    lines.append("Bute Weapon  M4A1-雷神 / StandardName M4A1_S_Transformers")
    lines.append("  PViewModelFileName -> PV-M4A1_S_Transformers.LTB")
    lines.append("  PViewSkinFileName  -> PV-M4A1_S_Transformers.DTX  (== _PC bytes)")
    lines.append("  ModelFileName      -> QV-M4A1_S_Transformers.LTB")
    lines.append("  SkinFileName       -> QV-M4A1_S_Transformers.DTX")
    lines.append("  CFG Name2          -> M4A1_S_Transformers_{S,N,alpha}.tga")
    lines.append("  CFG Name2          -> Black_Shader02.dds  (shared cube)")
    lines.append("  RS                 -> NinjaTranslucent / PVModelDefault")
    lines.append("  PreView            -> QV-M4A1_S_IronBeast_PreView.ltb  (Bute; shared, not Transformers_Preview)")
    lines.append("```")
    lines.append("")
    lines.append("## Nodes")
    lines.append("")
    lines.append("| id | role | path | sha256[:12] | size | relation | confidence |")
    lines.append("|---|---|---|---|---|---|---|")
    for item in graph["nodes"]:
        sha = (item.get("sha256") or "")[:12]
        lines.append(
            f"| `{item['id']}` | {item['role']} | `{item['path']}` | `{sha}` | {item.get('size')} | {item['relation']} | {item['confidence']} |"
        )
    lines.append("")
    lines.append("## Binding grades")
    lines.append("")
    for note in graph["binding_notes"]:
        lines.append(f"- {note}")
    lines.append("")
    lines.append("## Audio")
    lines.append("")
    audio = graph["audio"]
    lines.append(f"- Identity-core WAV/OGG/MP3/BANK: **{audio['identity_core_count']}**")
    lines.append(f"- Related variant audio (other Transformers skins): **{audio['variant_count']}**")
    lines.append(f"- Family-other (Thunder hammer/scepter etc.): **{audio['family_other_count']}**")
    lines.append(f"- Loose FMOD bank token hits: **{audio['bank_hit_count']}**")
    lines.append(f"- Status: `{audio['status']}`")
    if audio.get("identity_core_count") == 0:
        lines.append("- Canonical Bute `M4A1-雷神` has no dedicated SND/WEAPON/M4A1_S_Transformers/*.WAV in REZ. Variant skins (Qingchun/BB/Zeekr) have their own clips; those are not identity-core.")
    lines.append("")
    lines.append("## Animation / config")
    lines.append("")
    anim = graph["animation"]
    allocs = ((anim.get("pv_ltb") or {}).get("header") or {}).get("allocs") or {}
    lines.append(f"- PV LTB file type: `{((anim.get('pv_ltb') or {}).get('header') or {}).get('file_type_name')}`")
    lines.append(f"- alloc nParentAnims={allocs.get('nParentAnims')} nKeyFrames={allocs.get('nKeyFrames')} nAnimData={allocs.get('nAnimData')} nNodes={allocs.get('nNodes')} nPieces={allocs.get('nPieces')}")
    lines.append(f"- decoder mesh names: {', '.join(m['name'] for m in (anim.get('pv_ltb') or {}).get('mesh_names') or [])}")
    anim_like = (anim.get("pv_ltb") or {}).get("ascii_anim_like") or []
    if anim_like:
        lines.append(f"- ASCII anim-like strings in LTB: {', '.join(anim_like[:24])}")
    else:
        lines.append("- ASCII anim-like strings: none that passed the hint regex. Clip names remain `OPEN_UNRESOLVED` (decoder does not emit animation blocks).")
    lines.append("")
    cfg = graph["config_search"]
    lines.append(f"- Packed Bute / TABLE files recovered: **{cfg['recovered']}**")
    lines.append(f"- Token hits: **{cfg['hit_files']}** files / **{cfg['hit_count']}** hits")
    canon = cfg.get("canonical")
    if canon:
        lines.append("- Canonical packed Bute Weapon (GBK-decoded):")
        lines.append(f"  - WeaponName `{canon.get('WeaponName_gbk')}`")
        lines.append(f"  - StandardName `{canon.get('StandardName')}`")
        lines.append(f"  - PViewModelFileName `{canon.get('PViewModelFileName')}`")
        lines.append(f"  - PViewSkinFileName `{canon.get('PViewSkinFileName')}`")
        lines.append(f"  - ModelFileName `{canon.get('ModelFileName')}`")
        lines.append(f"  - SkinFileName `{canon.get('SkinFileName')}`")
        lines.append(f"  - PreViewModelFileName `{canon.get('PreViewModelFileName')}`")
        lines.append(f"  - RenderStyle `{canon.get('RenderStyleFileName')}` / `{canon.get('PViewRenderStyleFileName')}`")
        lines.append(f"  - ShotSoundName `{canon.get('ShotSoundName')}` (event name, not a REZ WAV path)")
        lines.append(f"  - GViewAnimName `{canon.get('GViewAnimName')}`")
        lines.append(f"  - source `{cfg.get('hit_files_paths')}`")
        lines.append("- Related Bute rows share the same StandardName (源-雷神 LV2–6, 高校特权) or only the Transformers token (IronBeast 雷神 skins). Those are **not** identity-core.")
    else:
        lines.append("- `NEGATIVE_RESULT_SCOPED`: no packed Bute Weapon with WeaponName 雷神 + StandardName `M4A1_S_Transformers`.")
    lines.append("")
    lines.append("## Conversion notes (not identity)")
    lines.append("")
    lines.append("- Raw CF LTB import is left/right swapped vs 图鉴. Blender / Source 1 path must apply LTB X scale −1 and reverse faces. User confirmed 2026-09-13: 「对了」.")
    lines.append("- Native PV DTX albedo is dark; 图鉴 is lit art. Do not rewrite native pixels.")
    lines.append("- Decoder V is already image-top-left. Do not apply a second `v→1-v` on LithTechModelDecoder JSON.")
    lines.append("")
    lines.append("## Not written")
    lines.append("")
    lines.append("- `IDENTITY_CONFIRMED`")
    lines.append("- P6 deploy")
    lines.append("- N05-J / frozen addon changes")
    lines.append("")
    lines.append("Reproduce:")
    lines.append("")
    lines.append("```powershell")
    lines.append("python -B scripts/p5/p5_t03_resource_graph.py")
    lines.append("```")
    lines.append("")
    return "\n".join(lines) + "\n"


def main() -> int:
    started = now()
    OUT.mkdir(parents=True, exist_ok=True)
    visual = json.loads(VISUAL_MATCH.read_text(encoding="utf-8"))
    tokens = [
        "M4A1_S_Transformers",
        "PV-M4A1_S_Transformers",
        "QV-M4A1_S_Transformers",
        "M4A1-雷神",
    ]

    hits, index_errors, index_count = scan_indexes()
    recovered, failures = recover_needed(hits)
    recovered = [prefer_identity_core_path(row) for row in recovered]

    by_key: dict[str, dict[str, Any]] = {}
    for row in recovered:
        by_key.setdefault(row["logical_key"], row)
        if row["bucket"] == "identity_core":
            by_key[row["logical_key"]] = row

    def find_role(role: str, bucket: str | None = None) -> dict[str, Any] | None:
        for row in recovered:
            if row["role"] != role:
                continue
            if bucket and row["bucket"] != bucket:
                continue
            if bucket is None and row["bucket"] not in {"identity_core", "identity_alias", "shared_cube"}:
                continue
            return row
        return None

    def find_path(logical: str) -> dict[str, Any] | None:
        return by_key.get(logical)

    pv_ltb = find_path(IDENTITY_PV_LTB) or find_role("pv_ltb", "identity_core")
    pv_dtx = find_path(IDENTITY_PV_DTX)
    if pv_dtx is None:
        for row in recovered:
            if row["role"] == "pv_dtx" and row["payload_sha256"] == visual["local_candidate"]["pv_dtx_sha256"]:
                pv_dtx = row
                break
    cfg_row = None
    for row in recovered:
        if row["role"] == "weapon_shader_cfg" and row["bucket"] in {"identity_core", "identity_alias"}:
            cfg_row = row
            if row["bucket"] == "identity_core":
                break
    if cfg_row:
        try:
            cfg_row["cfg"] = parse_cfg(cfg_row["raw"])
        except Exception as exc:
            cfg_row["cfg_error"] = str(exc)

    named_maps = {}
    if cfg_row and cfg_row.get("cfg"):
        textures = cfg_row["cfg"].get("Textures") or {}
        named_maps = {key: value for key, value in textures.items()}

    def find_named(filename: str, role: str) -> dict[str, Any] | None:
        want = logical_key(filename)
        want_stem = Path(filename).stem.upper()
        for row in recovered:
            if row["role"] != role and role != "env_cube":
                if role == "any":
                    pass
                elif row["role"] != role:
                    continue
            if logical_key(row["name"]) == want or Path(row["name"]).stem.upper() == want_stem:
                return row
        for row in recovered:
            if Path(row["name"]).stem.upper() == want_stem:
                return row
        return None

    spec = find_named(named_maps.get("SpecularMapName2") or "M4A1_S_Transformers_S.tga", "specular") or find_role("specular", "identity_core")
    norm = find_named(named_maps.get("NormalMapName2") or "M4A1_S_Transformers_N.tga", "normal") or find_role("normal", "identity_core")
    alpha = find_named(named_maps.get("AlphaMapName2") or "M4A1_S_Transformers_alpha.tga", "alpha") or find_role("alpha", "identity_core")
    cube = None
    for row in recovered:
        if row["bucket"] == "shared_cube" or Path(row["name"]).name.upper() == CUBE_NAME:
            cube = row
            break
    qv_ltb = find_role("qv_ltb", "identity_core")
    qv_dtx = find_role("qv_dtx", "identity_core")
    qv_preview = None
    for row in recovered:
        if row["role"] == "qv_ltb" and "PREVIEW" in row["name"].upper() and IDENTITY_STEM in strip_prefix(Path(row["name"]).stem):
            qv_preview = row
            break

    ui_rows = [row for row in recovered if row["role"] == "ui_icon" and row["bucket"] in {"identity_core", "identity_alias"}]
    if not ui_rows:
        ui_rows = [hit for hit in hits if hit["role"] == "ui_icon" and hit["bucket"] == "identity_core"]

    anim_view = None
    if pv_ltb:
        geom = GEOM_JSON if GEOM_JSON.is_file() else None
        anim_view = ltb_animation_view(pv_ltb["body"], geom)

    config_rows = [row for row in recovered if row["role"] in {"packed_bute", "table_config"}]
    config_searches = [search_config_payload(row, tokens) for row in config_rows]
    config_hits = [item for item in config_searches if item["hits"]]
    snapshots = [snap for item in config_searches for snap in item.get("weapon_snapshots") or []]
    canonical = canonical_bute_snapshot(snapshots)

    bank_hits = scan_loose_banks(tokens)
    rez_audio_hits = [hit for hit in hits if hit["role"] == "audio"]
    recovered_audio = [row for row in recovered if row["role"] == "audio"]
    audio_identity = [item for item in rez_audio_hits if item["bucket"] == "identity_core"]
    audio_variant = [item for item in rez_audio_hits if item["bucket"] == "related_variant"]
    audio_other = [item for item in rez_audio_hits if item["bucket"] not in {"identity_core", "related_variant"}]
    audio_status = (
        "OBSERVED"
        if audio_identity
        else "NEGATIVE_RESULT_SCOPED"
    )

    nodes: list[dict[str, Any]] = []
    edges: list[dict[str, Any]] = []

    def add_recovered(node_id: str, row: dict[str, Any] | None, relation: str, confidence: str, source: str, **extra: Any) -> None:
        if row is None:
            nodes.append(
                node(
                    node_id,
                    extra.pop("role", "missing"),
                    extra.pop("path", ""),
                    None,
                    None,
                    relation,
                    source,
                    "OPEN_UNRESOLVED",
                    missing=True,
                    **extra,
                )
            )
            return
        nodes.append(
            node(
                node_id,
                row["role"],
                row["full_path"],
                row["payload_sha256"],
                row["size"],
                relation,
                source,
                confidence,
                archive=row.get("archive"),
                routing=row.get("routing"),
                directory_md5=row.get("directory_md5"),
                copy_count=row.get("copy_count"),
                copies=row.get("copies"),
                bucket=row.get("bucket"),
                **extra,
            )
        )

    add_recovered(
        "pv_ltb",
        pv_ltb,
        "user_visual_match",
        "OBSERVED",
        "N05-C verified REZ + USER_VISUAL_MATCH_CONFIRMED",
        expected_sha256=visual["local_candidate"]["pv_ltb_sha256"],
        sha_match=bool(pv_ltb and pv_ltb["payload_sha256"] == visual["local_candidate"]["pv_ltb_sha256"]),
        display_fix="LTB X scale -1 + reverse faces; user 对了",
    )
    add_recovered(
        "pv_dtx",
        pv_dtx,
        "user_visual_match + same_stem_or_same_bytes",
        "OBSERVED",
        "N05-C verified REZ + USER_VISUAL_MATCH_CONFIRMED",
        expected_sha256=visual["local_candidate"]["pv_dtx_sha256"],
        sha_match=bool(pv_dtx and pv_dtx["payload_sha256"] == visual["local_candidate"]["pv_dtx_sha256"]),
        same_bytes_as="PV-M4A1_S_Transformers_PC.DTX",
    )
    add_recovered(
        "weapon_shader_cfg",
        cfg_row,
        "same_stem_filename_not_bute",
        "STRONG_HYPOTHESIS",
        "N05-C verified REZ CFG; Name2 is config reference, not a Bute field and not FXO technique proof",
        cfg=(cfg_row or {}).get("cfg"),
    )
    add_recovered("specular", spec, "cfg_name2", "STRONG_HYPOTHESIS", "CFG SpecularMapName2 + verified TGA")
    add_recovered("normal", norm, "cfg_name2", "STRONG_HYPOTHESIS", "CFG NormalMapName2 + verified TGA")
    add_recovered("alpha", alpha, "cfg_name2", "STRONG_HYPOTHESIS", "CFG AlphaMapName2 + verified TGA")
    add_recovered(
        "env_cube",
        cube,
        "cfg_name2_shared",
        "STRONG_HYPOTHESIS" if cube else "OPEN_UNRESOLVED",
        "CFG EnvCubeMapName2 Black_Shader02.dds; shared cube, not unique to 雷神",
    )
    add_recovered(
        "qv_ltb",
        qv_ltb,
        "packed_bute_ModelFileName" if canonical else "same_stem_filename_not_bute",
        "OBSERVED" if canonical else "HYPOTHESIS",
        "Bute ModelFileName QV-M4A1_S_Transformers.ltb" if canonical else "N05-C verified REZ; same-stem only",
    )
    add_recovered(
        "qv_dtx",
        qv_dtx,
        "packed_bute_SkinFileName" if canonical else "same_stem_filename_not_bute",
        "OBSERVED" if canonical else "HYPOTHESIS",
        "Bute SkinFileName QV-M4A1_S_Transformers.dtx" if canonical else "N05-C verified REZ; same-stem only",
    )
    if qv_preview:
        add_recovered(
            "qv_transformers_preview_ltb",
            qv_preview,
            "same_stem_preview_filename_not_bute",
            "HYPOTHESIS",
            "REZ has QV-M4A1_S_Transformers_Preview.LTB; canonical Bute PreViewModelFileName points at IronBeast_PreView instead",
        )
    rs_rows = [row for row in recovered if row["name"].upper() in SHARED_RS_NAMES]
    for row in rs_rows:
        add_recovered(
            "rs_" + Path(row["name"]).stem.lower(),
            row,
            "packed_bute_RenderStyle" if canonical else "shared_rs_filename",
            "OBSERVED" if canonical else "HYPOTHESIS",
            "Shared render style named by canonical Bute; also used by BornBeast",
        )
    for index, row in enumerate(ui_rows[:8]):
        if "payload_sha256" in row:
            add_recovered(
                f"ui_{index}",
                row,
                "ui_name_convention",
                "HYPOTHESIS",
                "UI art; supports the Transformers name, not the first-person atlas",
            )
        else:
            nodes.append(
                node(
                    f"ui_{index}",
                    "ui_icon",
                    row["full_path"],
                    None,
                    row.get("size"),
                    "ui_name_convention",
                    "REZ index (not recovered this pass)",
                    "HYPOTHESIS",
                    directory_md5=row.get("directory_md5"),
                    archive=row.get("archive"),
                )
            )

    if pv_ltb:
        edges.append(
            edge(
                "pv_ltb",
                "pv_dtx",
                "packed_bute_PViewSkinFileName" if canonical else "same_stem_filename_not_bute",
                "OBSERVED" if canonical else "HYPOTHESIS",
                "Bute PViewSkinFileName; LTB nNumTextures=0 so skin is not an embedded path",
            )
        )
        edges.append(edge("pv_ltb", "weapon_shader_cfg", "same_stem_filename_not_bute", "HYPOTHESIS"))
    if cfg_row:
        edges.append(edge("weapon_shader_cfg", "specular", "cfg_name2", "STRONG_HYPOTHESIS", named_maps.get("SpecularMapName2", "")))
        edges.append(edge("weapon_shader_cfg", "normal", "cfg_name2", "STRONG_HYPOTHESIS", named_maps.get("NormalMapName2", "")))
        edges.append(edge("weapon_shader_cfg", "alpha", "cfg_name2", "STRONG_HYPOTHESIS", named_maps.get("AlphaMapName2", "")))
        edges.append(edge("weapon_shader_cfg", "env_cube", "cfg_name2", "STRONG_HYPOTHESIS", named_maps.get("EnvCubeMapName2", "")))
    if qv_ltb:
        edges.append(
            edge(
                "pv_ltb",
                "qv_ltb",
                "packed_bute_ModelFileName" if canonical else "same_stem_world_model",
                "OBSERVED" if canonical else "HYPOTHESIS",
            )
        )
    if qv_dtx:
        edges.append(
            edge(
                "qv_ltb",
                "qv_dtx",
                "packed_bute_SkinFileName" if canonical else "same_stem_filename_not_bute",
                "OBSERVED" if canonical else "HYPOTHESIS",
            )
        )

    variant_counts: dict[str, int] = defaultdict(int)
    for hit in hits:
        if hit["bucket"] == "related_variant":
            variant_counts[hit["role"]] += 1

    family_counts: dict[str, int] = defaultdict(int)
    for hit in hits:
        family_counts[hit["role"]] += 1

    bute_status = "OBSERVED" if canonical else ("OBSERVED_RELATED_ONLY" if snapshots else "NEGATIVE_RESULT_SCOPED")

    graph = {
        "schema": "cf2.p5.t03.resource-graph.v1",
        "task_id": "P5-T03",
        "result": "RESOURCE_GRAPH_RECORDED",
        "identity_confirmed": False,
        "identity": {
            "official": visual.get("official"),
            "user_confirmation": visual.get("user_confirmation"),
            "lr_confirmed": "对了",
            "pv_ltb": visual["local_candidate"]["pv_ltb"],
            "pv_ltb_sha256": visual["local_candidate"]["pv_ltb_sha256"],
            "pv_dtx": visual["local_candidate"]["pv_dtx"],
            "pv_dtx_sha256": visual["local_candidate"]["pv_dtx_sha256"],
        },
        "nodes": nodes,
        "edges": edges,
        "binding_notes": [
            "PV LTB + PV DTX are OBSERVED and user-matched. That is USER_VISUAL_MATCH_CONFIRMED, not IDENTITY_CONFIRMED.",
            "CFG Name2 filenames exist as MD5-verified TGA/DDS. That is a config reference, not FXO technique proof. Bute does not name the TGA/CFG.",
            "QV LTB/DTX are Bute ModelFileName / SkinFileName when the canonical Weapon record is present.",
            "UI icons remain name convention only (HYPOTHESIS).",
            f"Packed Bute / TABLE search: {bute_status}.",
            f"Identity-core audio: {audio_status}.",
            "LTB animation clip names are not decoded by P5T02ModelReader; header allocs are STRUCTURALLY_VERIFIED counts.",
            "Do not treat related_variant (Classic, DS, FD, BB, GR/BL, event skins) as 雷神.",
        ],
        "animation": {
            "pv_ltb": {k: v for k, v in (anim_view or {}).items() if k != "ascii_other"} | {"ascii_other_sample": ((anim_view or {}).get("ascii_other") or [])[:20]},
            "clip_names_decoded": False,
            "confidence": "STRUCTURALLY_VERIFIED" if anim_view and anim_view.get("header") else "OPEN_UNRESOLVED",
        },
        "audio": {
            "rez_hit_count": len(rez_audio_hits),
            "identity_core_count": len(audio_identity),
            "variant_count": len(audio_variant),
            "family_other_count": len(audio_other),
            "rez_hits": [
                {
                    "full_path": item["full_path"],
                    "archive": item["archive"],
                    "size": item["size"],
                    "directory_md5": item["directory_md5"],
                    "bucket": item["bucket"],
                }
                for item in rez_audio_hits
            ],
            "recovered": [public_row(item) for item in recovered_audio if item.get("bucket") in {"identity_core", "related_variant"}],
            "bank_hit_count": len(bank_hits),
            "banks": bank_hits,
            "status": audio_status,
        },
        "config_search": {
            "recovered": len(config_rows),
            "hit_files": len(config_hits),
            "hit_files_paths": [item["full_path"] for item in config_hits],
            "hit_count": sum(len(item["hits"]) for item in config_hits),
            "canonical": canonical,
            "related_standard_names": sorted(
                {
                    str(snap.get("StandardName"))
                    for snap in snapshots
                    if snap.get("StandardName") and snap.get("StandardName") != "M4A1_S_Transformers"
                }
            ),
            "weapon_snapshots": snapshots,
            "hits": [
                {
                    "full_path": item["full_path"],
                    "archive": item["archive"],
                    "payload_sha256": item["payload_sha256"],
                    "decode_ok": item["decode_ok"],
                    "decode_reason": item.get("decode_reason"),
                    "hits": item["hits"][:20],
                }
                for item in config_hits
            ],
            "status": bute_status,
        },
        "variants_not_identity": {
            "index_hits_by_role": dict(variant_counts),
            "note": "Counted from REZ index. Not recovered as identity-core.",
        },
        "family_index_counts": dict(family_counts),
        "scan": {
            "index_count": index_count,
            "hit_count": len(hits),
            "index_errors": index_errors,
            "recover_failures": [
                {"reason": item["reason"], "path": (item.get("hit") or {}).get("full_path")}
                for item in failures
            ],
            "recovered_unique": len(recovered),
        },
        "prohibited": [
            "IDENTITY_CONFIRMED",
            "deploy / overwrite N05-J or frozen",
            "BornBeast as 雷神",
            "filename Transformers as identity",
            "related_variant as identity-core",
        ],
    }

    execution = {
        "schema": "cf2.p5.t03.execution.v1",
        "task_id": "P5-T03",
        "started_at": started,
        "completed_at": now(),
        "result": graph["result"],
        "identity_confirmed": False,
        "p4_m01": "INCOMPLETE",
        "next_action": "P5-T04 identity review from this graph; do not deploy",
        "prohibited": graph["prohibited"],
    }

    (OUT / "resource_graph.json").write_text(json.dumps(graph, indent=2) + "\n", encoding="utf-8")
    (OUT / "nodes.json").write_text(json.dumps({"nodes": nodes, "edges": edges}, indent=2) + "\n", encoding="utf-8")
    (OUT / "execution.json").write_text(json.dumps(execution, indent=2) + "\n", encoding="utf-8")
    recovered_public = [
        public_row(item)
        for item in recovered
        if item.get("bucket") in {"identity_core", "identity_alias", "shared_cube"}
        or item.get("role") in {"specular", "normal", "alpha", "weapon_shader_cfg", "ui_icon"}
        or (item.get("role") == "audio" and item.get("bucket") in {"identity_core", "related_variant"})
        or (item.get("role") == "packed_bute" and "BF005" in item.get("full_path", "").upper())
    ]
    (OUT / "recovered.json").write_text(json.dumps(recovered_public, indent=2) + "\n", encoding="utf-8")
    if canonical:
        (OUT / "bute_canonical.json").write_text(json.dumps(canonical, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (OUT / "report.md").write_text(write_report(graph), encoding="utf-8")
    print(json.dumps({
        "result": graph["result"],
        "nodes": len(nodes),
        "edges": len(edges),
        "index_hits": len(hits),
        "recovered": len(recovered),
        "bute": bute_status,
        "audio": audio_status,
        "out": rel(OUT),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
