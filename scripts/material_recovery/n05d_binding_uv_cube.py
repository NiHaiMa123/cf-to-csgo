"""P4-M01-N05-D — PV LTB/UV binding diagnostic and named cube recovery.

Uses the N05-C verified REZ reader. Does not wrap QV onto the PV mesh,
does not treat filename similarity as binding proof, and does not
announce P4-M01 PASS.

Repro:
  python scripts/material_recovery/n05d_binding_uv_cube.py
"""
from __future__ import annotations

import hashlib
import io
import json
import lzma
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image, ImageDraw

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "cf_extract"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # noqa: E402
import extract_all  # noqa: E402
import n05a_decoder_provenance_audit as audit  # noqa: E402
from rez_verified_payload import read_verified_payload  # noqa: E402

REPO = Path(_paths.project_dir())
DATA = Path(_paths.data_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05d_binding_uv_cube"
)
STAGING = DATA / "n05d_binding"
N05B = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05b_shard_material_recovery/recovery.json"
)
CFREZ_EXE = REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
DOTNET = Path(r"C:\Program Files\dotnet\dotnet.exe")

N05B_PV_DTX_SHA = "a30c9a271612dec05cb44f44e6e9412be398350e5fb6ac93966aea4b7f56b4ba"
WANTED = {
    "pv_ltb": "PLAYERVIEW/PV-M4A1_S_BornBeast.LTB",
    "qv_ltb": "WEAPONS/QV-M4A1_S_BornBeast.LTB",
    "pv_dtx": "PLAYERVIEW/PV-M4A1_S_BornBeast.DTX",
    "qv_dtx": "WEAPONS/QV-M4A1_S_BornBeast.DTX",
    "rs_ninja": "RS/NINJATRANSLUCENT.LTB",
    "rs_pvdefault": "RS/PVMODELDEFAULT.LTB",
}
CUBE_STEM = "BLACK_SHADER03"
WEAPON_PIECE_MARK = "BORBEAST"
HAND_MARKS = ("FVIEW-HAND", "FVIEW-ARM")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def run_checked(cmd: list[str], timeout: int = 300) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout
    )
    if proc.returncode != 0:
        raise RuntimeError(f"command failed {cmd}: {proc.stderr or proc.stdout}")
    return proc


def ensure_cfrez_built() -> Path:
    run_checked([str(DOTNET), "build", str(REPO / "CFRezManager" / "CFRezManager.csproj"), "-c", "Debug"])
    if not CFREZ_EXE.is_file():
        raise FileNotFoundError(CFREZ_EXE)
    return CFREZ_EXE


def maybe_lzma(data: bytes) -> tuple[bytes, bool]:
    if data[:1] != b"\x5d":
        return data, False
    try:
        return lzma.decompress(data, format=lzma.FORMAT_ALONE), True
    except lzma.LZMAError:
        return data, False


def find_entry(entries: list[dict], logical: str) -> dict | None:
    matches = [entry for entry in entries if extract_all.logical_path_matches(entry["full_path"], logical)]
    if len(matches) > 1:
        raise ValueError(f"{logical} matched {len(matches)} entries in one archive")
    return matches[0] if matches else None


def scan_archives() -> dict:
    indexes = extract_all.discover_index_archives(str(CF))
    wanted_hits: dict[str, list] = {key: [] for key in WANTED}
    cube_hits = []
    for index_path in indexes:
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception as exc:
            wanted_hits.setdefault("_index_errors", []).append({"index": index_path, "error": str(exc)})
            continue
        for key, logical in WANTED.items():
            entry = find_entry(entries, logical)
            if entry is None:
                continue
            data, provenance = read_verified_payload(index_path, entry)
            wanted_hits[key].append({**provenance, "id": key, "index": index_path})
        for entry in entries:
            name = Path(str(entry["full_path"]).replace("\\", "/")).name.upper()
            stem = Path(name).stem.upper()
            if stem != CUBE_STEM and name != CUBE_STEM + ".DDS":
                continue
            data, provenance = read_verified_payload(index_path, entry)
            cube_hits.append({**provenance, "id": "env_cube", "index": index_path, "name": name})
    return {"wanted": wanted_hits, "cube": cube_hits, "index_count": len(indexes)}


def unique_copy_table(rows: list[dict]) -> list[dict]:
    seen = {}
    for row in rows:
        seen.setdefault(row["sha256"], []).append(row)
    out = []
    for sha, group in seen.items():
        first = dict(group[0])
        first["copy_count"] = len(group)
        first["copies"] = [
            {
                "index_archive": item["index_archive"],
                "payload_file": item["payload_file"],
                "routing": item["routing"],
                "size": item["size"],
            }
            for item in group
        ]
        out.append(first)
    return out


def decode_image_bytes(logical_path: str, data: bytes, dest: Path) -> dict:
    suffix = Path(logical_path).suffix.upper()
    dest.parent.mkdir(parents=True, exist_ok=True)
    if suffix == ".DTX":
        decoded = audit.decode_repo_pixels(data)
        if not decoded.get("ok"):
            return {"ok": False, "error": decoded}
        image = decoded["image"]
        image.save(dest)
        return {"ok": True, "preview": rel(dest), "size": list(image.size), "mode": image.mode}
    if suffix == ".TGA":
        with Image.open(io.BytesIO(data)) as source:
            source.load()
            image = source.copy()
        image.save(dest)
        return {"ok": True, "preview": rel(dest), "size": list(image.size), "mode": image.mode, "container": "TGA"}
    if suffix == ".DDS":
        src = STAGING / (dest.stem + ".dds")
        src.parent.mkdir(parents=True, exist_ok=True)
        src.write_bytes(data)
        png = dest.with_suffix(".png")
        proc = run_checked([str(CFREZ_EXE), "--decode-image", str(src), str(png)])
        with Image.open(png) as image:
            return {
                "ok": True,
                "preview": rel(png),
                "size": list(image.size),
                "mode": image.mode,
                "container": "DDS",
                "stdout": proc.stdout.strip(),
            }
    return {"ok": False, "error": f"unsupported {suffix}"}


def parse_obj(path: Path) -> list[dict]:
    groups: list[dict] = []
    current = {"name": "default", "uvs": [], "faces": []}
    all_uvs: list[tuple[float, float]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line or line.startswith("#"):
            continue
        kind, *rest = line.split()
        if kind in {"o", "g"} and rest:
            if current["faces"] or current["name"] != "default":
                groups.append(current)
            current = {"name": rest[0], "uvs": [], "faces": []}
        elif kind == "vt" and len(rest) >= 2:
            all_uvs.append((float(rest[0]), float(rest[1])))
        elif kind == "f":
            corners = []
            for token in rest:
                parts = token.split("/")
                if len(parts) < 2 or not parts[1]:
                    continue
                corners.append(int(parts[1]) - 1)
            if len(corners) >= 3:
                current["faces"].append(corners[:3])
    groups.append(current)
    for group in groups:
        uvs = []
        for face in group["faces"]:
            try:
                uvs.extend(all_uvs[index] for index in face)
            except IndexError:
                continue
        xs = [uv[0] for uv in uvs]
        ys = [uv[1] for uv in uvs]
        group["uv_count"] = len(uvs)
        group["uv_min"] = [min(xs), min(ys)] if xs else None
        group["uv_max"] = [max(xs), max(ys)] if xs else None
        group["uvs"] = uvs
        group["face_uvs"] = [[all_uvs[i] for i in face if 0 <= i < len(all_uvs)] for face in group["faces"]]
    return groups


def piece_kind(name: str) -> str:
    upper = name.upper()
    if any(mark in upper for mark in HAND_MARKS):
        return "hands"
    if WEAPON_PIECE_MARK in upper.replace("BORNBEAST", "BORBEAST") or "BORNBEAST" in upper:
        return "weapon"
    return "other"


def draw_overlay(atlas: Image.Image, groups: list[dict], kinds: set[str], dest: Path) -> dict:
    image = atlas.convert("RGBA").copy()
    draw = ImageDraw.Draw(image)
    width, height = image.size
    drawn = 0
    for group in groups:
        if piece_kind(group["name"]) not in kinds:
            continue
        color = (0, 255, 80, 220) if piece_kind(group["name"]) == "weapon" else (255, 80, 80, 220)
        for face in group["face_uvs"]:
            if len(face) < 3:
                continue
            points = []
            for u, v in face:
                x = int(round(u * (width - 1)))
                y = int(round((1.0 - v) * (height - 1)))
                points.append((x, y))
            draw.line(points + [points[0]], fill=color, width=1)
            drawn += 1
    image.save(dest)
    return {"preview": rel(dest), "triangles_drawn": drawn, "kinds": sorted(kinds), "atlas_size": [width, height]}


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    exe = ensure_cfrez_built()
    scan = scan_archives()
    copies = {key: unique_copy_table(rows) for key, rows in scan["wanted"].items() if key != "_index_errors"}
    cube_copies = unique_copy_table(scan["cube"])

    pv_dtx_rows = copies.get("pv_dtx") or []
    if not pv_dtx_rows or pv_dtx_rows[0]["sha256"] != N05B_PV_DTX_SHA:
        raise ValueError(f"Verified PV DTX SHA mismatch: {pv_dtx_rows}")
    pv_dtx = None
    for row in scan["wanted"]["pv_dtx"]:
        if row["sha256"] == N05B_PV_DTX_SHA:
            pv_dtx = read_verified_payload(row["index_archive"], {
                "full_path": row["logical_path"],
                "data_offset": row["offset"],
                "size": row["size"],
                "time": row["legacy_time_field"],
                "md5": row["directory_md5"],
            })
            break
    if pv_dtx is None:
        raise ValueError("PV DTX verified payload missing")
    pv_dtx_bytes, pv_dtx_prov = pv_dtx
    atlas_info = decode_image_bytes("pv.dtx", pv_dtx_bytes, OUT / "bornbeast_pv_dtx.png")
    if not atlas_info.get("ok"):
        raise ValueError(atlas_info)
    with Image.open(OUT / "bornbeast_pv_dtx.png") as atlas:
        atlas_image = atlas.convert("RGBA").copy()

    cube_decode = []
    for row in cube_copies:
        data, provenance = read_verified_payload(row["index_archive"], {
            "full_path": row["logical_path"],
            "data_offset": row["offset"],
            "size": row["size"],
            "time": row["legacy_time_field"],
            "md5": row["directory_md5"],
        })
        stem = Path(row["logical_path"]).stem
        decoded = decode_image_bytes(row["logical_path"], data, OUT / f"{stem}_cube.png")
        cube_decode.append({**row, "decode": decoded, "payload_sha256": provenance["sha256"]})

    inspect = None
    pv_ltb_rows = copies.get("pv_ltb") or []
    if pv_ltb_rows:
        row = scan["wanted"]["pv_ltb"][0]
        data, provenance = read_verified_payload(row["index_archive"], {
            "full_path": row["logical_path"],
            "data_offset": row["offset"],
            "size": row["size"],
            "time": row["legacy_time_field"],
            "md5": row["directory_md5"],
        })
        body, lzma_used = maybe_lzma(data)
        ltb_path = STAGING / "PV-M4A1_S_BornBeast.ltb"
        ltb_path.write_bytes(body)
        inspect_path = OUT / "pv_ltb_inspect.json"
        run_checked([str(exe), "--inspect-ltb", "--input", str(ltb_path), "--output", str(inspect_path)])
        inspect = json.loads(inspect_path.read_text(encoding="utf-8"))
        inspect_summary = {
            "payload_sha256": provenance["sha256"],
            "lzma": lzma_used,
            "decompressed_bytes": len(body),
            "mesh_count": inspect.get("geometry", {}).get("mesh_count"),
            "vertex_count": inspect.get("geometry", {}).get("vertex_count"),
            "triangle_count": inspect.get("geometry", {}).get("triangle_count"),
            "meshes": [
                {
                    "name": mesh.get("name"),
                    "kind": piece_kind(mesh.get("name") or ""),
                    "vertex_count": mesh.get("vertex_count"),
                    "triangle_count": mesh.get("triangle_count"),
                    "has_uv": mesh.get("has_uv"),
                    "uv": mesh.get("uv"),
                    "texture_path": mesh.get("texture_path"),
                    "material_hints": mesh.get("material_hints"),
                }
                for mesh in inspect.get("geometry", {}).get("meshes") or []
            ],
        }
    else:
        inspect_summary = None

    obj_export = None
    overlay = None
    rez_dir = CF / "rez"
    if rez_dir.is_dir() and inspect_summary is not None:
        obj_dir = STAGING / "obj_export"
        obj_dir.mkdir(parents=True, exist_ok=True)
        obj_path = obj_dir / "PV-M4A1_S_BornBeast.obj"
        export_proc = run_checked(
            [
                str(exe),
                "--export-obj",
                "--source-root",
                str(rez_dir),
                "--model",
                "PLAYERVIEW/PV-M4A1_S_BornBeast.LTB",
                "--output",
                str(obj_path),
                "--raw-transform",
            ],
            timeout=600,
        )
        groups = parse_obj(obj_path)
        group_summary = [
            {
                "name": group["name"],
                "kind": piece_kind(group["name"]),
                "uv_count": group["uv_count"],
                "uv_min": group["uv_min"],
                "uv_max": group["uv_max"],
                "triangle_count": len(group["faces"]),
            }
            for group in groups
        ]
        overlay = {
            "weapon": draw_overlay(atlas_image, groups, {"weapon"}, OUT / "pv_weapon_uv_on_verified_dtx.png"),
            "hands": draw_overlay(atlas_image, groups, {"hands"}, OUT / "pv_hands_uv_on_verified_dtx.png"),
            "all": draw_overlay(atlas_image, groups, {"weapon", "hands", "other"}, OUT / "pv_all_uv_on_verified_dtx.png"),
        }
        obj_export = {
            "stdout": export_proc.stdout.strip(),
            "obj": str(obj_path),
            "groups": group_summary,
            "note": "OBJ exporter texture guesses are not binding proof; overlay uses Bute PViewSkinFileName verified PV DTX only",
        }

    qv_note = {
        "main_index_qv_dtx_copies": copies.get("qv_dtx") or [],
        "qv_ltb_copies": copies.get("qv_ltb") or [],
        "kept": True,
        "wrapped_on_pv": False,
        "reason": "load order between rez QV 256 and rez2 QV 1024 is unknown; QV must not be UV-wrapped on the PV mesh as native proof",
    }

    cube_ok = any(item.get("decode", {}).get("ok") for item in cube_decode)
    uv_ok = bool(inspect_summary and any(mesh.get("has_uv") for mesh in inspect_summary["meshes"]))
    result = "MESH_UV_CUBE_DIAGNOSTIC_PARTIAL" if uv_ok else "BINDING_INCOMPLETE"
    if uv_ok and cube_ok:
        result = "MESH_UV_AND_CUBE_RECOVERED_BINDING_OPEN"
    elif uv_ok:
        result = "MESH_UV_RECOVERED_CUBE_MISSING"

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P4-M01-N05-D",
        "result": result,
        "p4_m01": "INCOMPLETE",
        "index_count": scan["index_count"],
        "verified_copies": {key: [
            {k: v for k, v in row.items() if k != "candidate_checks"}
            for row in rows
        ] for key, rows in copies.items()},
        "pv_dtx": {"sha256" : N05B_PV_DTX_SHA, "decode": atlas_info},
        "pv_ltb": inspect_summary,
        "cube": cube_decode,
        "obj_export": obj_export,
        "uv_overlay": overlay,
        "qv_copies": qv_note,
        "binding_evidence": {
            "bute_pview_skin": "PViewSkinFileName -> PLAYERVIEW/PV-M4A1_S_BornBeast.DTX",
            "ltb_nnumtextures": 0,
            "texture_slots_are_not_paths": True,
            "filename_similarity_not_used": True,
            "qv_not_applied_to_pv": True,
        },
        "limitations": [
            "LTB nNumTextures=0: piece table does not name DTX/TGA files.",
            "CFG Name2 fields are file references, not runtime technique proof.",
            "UV overlay is a native-only diagnostic of layout on the verified PV atlas.",
            "OBJ exporter guessed textures are not accepted as binding.",
        ],
    }
    (OUT / "binding.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report)
    print(json.dumps({
        "result": result,
        "cube": len(cube_decode),
        "pv_meshes": None if inspect_summary is None else len(inspect_summary["meshes"]),
        "out": str(OUT),
    }, ensure_ascii=False))
    return 0


def write_markdown(report: dict) -> None:
    ltb = report.get("pv_ltb") or {}
    lines = [
        "# N05-D — PV LTB/UV binding diagnostic and named cube",
        "",
        f"Result: **{report['result']}**. P4-M01 remains **INCOMPLETE**.",
        "",
        "PV LTB, RS and DTX were re-read through the N05-C verified resolver. QV copies are retained and were not wrapped onto the PV mesh. Filename similarity is not used as binding proof.",
        "",
        "## PV LTB",
        "",
        f"- payload SHA256: `{ltb.get('payload_sha256')}`",
        f"- meshes: {ltb.get('mesh_count')}  vertices: {ltb.get('vertex_count')}  triangles: {ltb.get('triangle_count')}",
        "",
        "| Piece | Kind | Tris | Has UV | UV min | UV max | Outside 0–1 |",
        "|---|---|---:|---|---|---|---:|",
    ]
    for mesh in ltb.get("meshes") or []:
        uv = mesh.get("uv") or {}
        lines.append(
            f"| `{mesh.get('name')}` | {mesh.get('kind')} | {mesh.get('triangle_count')} | {mesh.get('has_uv')} | "
            f"{uv.get('min')} | {uv.get('max')} | {uv.get('outside_unit_square')} |"
        )
    lines += ["", "## Cube", ""]
    if not report.get("cube"):
        lines.append("No `Black_Shader03` payload was found in scanned REZ indexes.")
    for row in report.get("cube") or []:
        dec = row.get("decode") or {}
        lines.append(
            f"- `{row.get('logical_path')}` sha256 `{row.get('sha256')}` routing `{row.get('routing')}` decode={dec.get('ok')} size={dec.get('size')}"
        )
    overlay = report.get("uv_overlay") or {}
    lines += [
        "",
        "## Native-only UV diagnostic",
        "",
        "Overlay samples the verified 1024×1024 PV DTX using UVs from the official OBJ export of the verified PV LTB. Hands and weapon pieces are drawn separately. This checks atlas layout; it is not CFG/FXO runtime proof.",
        "",
    ]
    for key, row in overlay.items():
        lines.append(f"- {key}: `{row.get('preview')}` triangles={row.get('triangles_drawn')}")
    lines += [
        "",
        "## QV copies kept",
        "",
        "Main-index QV 256 and any rez2 QV 1024 remain listed. Load order is unknown, so neither was applied to the PV mesh.",
        "",
        "## Limitations",
        "",
    ]
    for item in report.get("limitations") or []:
        lines.append(f"- {item}")
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
