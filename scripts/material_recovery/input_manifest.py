"""Generic Phase A1 input-closure builder for CF material reconstruction.

Takes a per-weapon manifest (asset roles + paths + optional acquisition
provenance) and produces ``audit/input_manifest.json`` under
``work/<weapon>/material_v2/``.

No weapon names or channel semantics live here; the caller supplies the
asset list. Provenance is joined from the acquisition record when present:
each asset keeps REZ path, archive, shard routing, directory MD5 and
SHA-256 exactly as verified at acquisition time.
"""
from __future__ import annotations

import hashlib
import json
import struct
from pathlib import Path

from PIL import Image


def sha256_file(path: Path | str) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def md5_file(path: Path | str) -> str:
    return hashlib.md5(Path(path).read_bytes()).hexdigest()


def image_meta(path: Path | str) -> dict:
    """Size / format / channel metadata for any PIL-readable image."""
    with Image.open(path) as im:
        bands = im.getbands()
        meta = {
            "kind": "image",
            "width": im.width,
            "height": im.height,
            "mode": im.mode,
            "format": im.format,
            "channels": len(bands),
            "band_names": list(bands),
        }
        extrema = im.getextrema()
        if isinstance(extrema, tuple) and extrema and isinstance(extrema[0], tuple):
            meta["extrema"] = {b: list(e) for b, e in zip(bands, extrema)}
        elif isinstance(extrema, tuple):
            meta["extrema"] = {bands[0]: list(extrema)}
    return meta


def dds_meta(path: Path | str) -> dict:
    """DDS header metadata: size, mip count, compression, cubemap faces."""
    data = Path(path).read_bytes()
    if data[:4] != b"DDS ":
        return {"kind": "dds", "valid": False, "reason": "bad magic"}
    height, width = struct.unpack("<II", data[12:20])
    mipmaps = struct.unpack("<I", data[28:32])[0]
    pf_flags = struct.unpack("<I", data[80:84])[0]
    fourcc = data[84:88].decode("ascii", errors="replace").rstrip("\x00")
    caps = struct.unpack("<I", data[108:112])[0]
    caps2 = struct.unpack("<I", data[112:116])[0]
    is_cubemap = bool(caps2 & 0x200)
    faces = []
    if is_cubemap:
        face_bits = [
            (0x400, "+X"), (0x800, "-X"), (0x1000, "+Y"),
            (0x2000, "-Y"), (0x4000, "+Z"), (0x8000, "-Z"),
        ]
        faces = [name for bit, name in face_bits if caps2 & bit]
    return {
        "kind": "dds",
        "valid": True,
        "width": width,
        "height": height,
        "mipmaps": mipmaps,
        "pixel_format_flags": pf_flags,
        "fourcc": fourcc if pf_flags & 0x4 else None,
        "is_cubemap": is_cubemap,
        "cubemap_faces": faces,
        "caps": caps,
        "caps2": caps2,
    }


def cfg_meta(path: Path | str) -> dict:
    """CFG metadata: raw section/key counts only; semantics live in the IR."""
    import material_ir  # same package; caller adds scripts/ to sys.path
    sections = material_ir.parse_cfg_full(path)
    return {
        "kind": "cfg",
        "sections": {name: len(entries) for name, entries in sections.items()},
        "keys": sum(len(e) for e in sections.values()),
    }


def skin_dump_meta(path: Path | str) -> dict:
    """Decoded LTB skin-dump identity: piece names, vertex/triangle counts."""
    dump = json.loads(Path(path).read_text(encoding="utf-8"))
    meshes = dump.get("meshes", [])
    return {
        "kind": "skin_dump",
        "schema": dump.get("schema"),
        "source": dump.get("source"),
        "skeleton_nodes": len(dump.get("skeleton", [])),
        "mesh_count": len(meshes),
        "meshes": [
            {
                "name": m.get("name"),
                "vertex_count": m.get("vertex_count"),
                "triangle_count": len(m.get("triangles", [])) // 3
                if m.get("triangles") else None,
                "has_uvs": bool(m.get("uvs")),
                "has_weights": bool(m.get("bone_weights")),
            }
            for m in meshes
        ],
    }


_META_BY_SUFFIX = {
    ".png": image_meta, ".tga": image_meta, ".jpg": image_meta,
    ".jpeg": image_meta, ".bmp": image_meta, ".dds": dds_meta,
    ".cfg": cfg_meta, ".json": None, ".ltb": None,
}


def _asset_meta(path: Path, role: str) -> dict | None:
    suffix = path.suffix.lower()
    if role == "mesh_skin" and suffix == ".json":
        return skin_dump_meta(path)
    if suffix == ".json":
        return {"kind": "json"}
    if suffix == ".ltb":
        return {"kind": "ltb"}
    reader = _META_BY_SUFFIX.get(suffix)
    return reader(path) if reader else None


def _provenance_for(asset: dict, acquisition: dict | None) -> dict | None:
    """Join an asset to its acquisition entry by logical path or filename."""
    if not acquisition:
        return None
    wanted = (asset.get("logical_path") or "").replace("/", "\\").lower()
    name = Path(asset["path"]).name.lower()
    for entry in acquisition.get("files", []):
        ep = entry.get("path", "").replace("/", "\\").lower()
        if (wanted and ep == wanted) or ep.endswith("\\" + name) or ep.endswith("/" + name):
            prov = entry.get("provenance", {})
            return {
                "rez_path": entry.get("path"),
                "index_archive": prov.get("index_archive"),
                "payload_file": prov.get("payload_file"),
                "routing": prov.get("routing"),
                "offset": prov.get("offset"),
                "directory_md5": prov.get("directory_md5"),
                "sha256": entry.get("sha256"),
                "md5": entry.get("md5"),
            }
    return None


def build_input_manifest(
    weapon: str,
    material_id: str,
    assets: list[dict],
    out_path: Path | str,
    acquisition: dict | None = None,
) -> dict:
    """Write ``audit/input_manifest.json`` and return it.

    ``assets`` entries: {"role": str, "path": str|Path,
                         "logical_path": optional str, "required": bool}
    The A1 gate passes only when every required asset exists, hashes match
    its acquisition record, and metadata decoded cleanly.
    """
    entries = []
    problems = []
    for asset in assets:
        role = asset["role"]
        path = Path(asset["path"])
        required = asset.get("required", True)
        entry: dict = {
            "role": role,
            "path": str(path),
            "logical_path": asset.get("logical_path"),
            "required": required,
            "exists": path.is_file(),
        }
        if not entry["exists"]:
            if required:
                problems.append(f"missing required asset: {role} {path}")
            entries.append(entry)
            continue
        entry["bytes"] = path.stat().st_size
        entry["sha256"] = sha256_file(path)
        entry["md5"] = md5_file(path)
        if asset.get("derived"):
            entry["derived_from"] = asset.get("derived_from")
            entry["provenance_kind"] = "decoded_output"
        else:
            prov = _provenance_for(asset, acquisition)
            if prov:
                entry["provenance"] = prov
                if prov.get("sha256") and prov["sha256"] != entry["sha256"]:
                    problems.append(
                        f"{role}: sha256 mismatch vs acquisition "
                        f"({prov['sha256']} != {entry['sha256']})")
                if prov.get("md5") and prov["md5"].lower() != entry["md5"].lower():
                    problems.append(
                        f"{role}: md5 mismatch vs acquisition "
                        f"({prov['md5']} != {entry['md5']})")
            elif required:
                problems.append(f"{role}: no acquisition provenance for {path.name}")
        try:
            entry["meta"] = _asset_meta(path, role)
        except Exception as exc:  # noqa: BLE001 - record, don't crash the gate
            entry["meta"] = {"kind": "error", "error": str(exc)}
            problems.append(f"{role}: metadata decode failed: {exc}")
        entries.append(entry)

    manifest = {
        "schema": "cf-material-input-manifest.v1",
        "weapon": weapon,
        "material_id": material_id,
        "assets": entries,
        "a1_gate": {
            "passed": not problems,
            "problems": problems,
        },
    }
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    return manifest


def load_acquisition(path: Path | str | None) -> dict | None:
    if not path:
        return None
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None
