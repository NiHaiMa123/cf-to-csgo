"""P6 — Identity replacement of M4A1-雷神 onto the CS:GO M4A4 slot.

Uses P5-T04 IDENTITY_CONFIRMED assets (base PV-M4A1_S_Transformers).
Applies the user-confirmed LTB X scale −1 (plus reverse faces) before the
frozen P4 C3 matrix. Materials follow the N05-J formula channel wiring
(AlphaMap.b as $envmapmask). CFG scalars are not copied as Source phong.

Does not overwrite the parked frozen addon. Parks the live N05-J diagnostic
so this addon can load. Not a P4-M01 PASS. final_cf_material=false.

Repro:
  python scripts/p5/p5_p6_identity_replacement.py
"""
from __future__ import annotations

import hashlib
import io
import json
import lzma
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "cf_extract"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "material_recovery"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "cf_ltb"))
import _paths  # noqa: E402
import extract_all  # noqa: E402
import n05a_decoder_provenance_audit as n05a  # noqa: E402
from apply_c3_fixed_transform import normalize_rotation, transform_lines  # noqa: E402
from rez_verified_payload import read_verified_payload  # noqa: E402
from weapon_port.pipeline import apply_inspect_policy, mdl_header, smd_prefix  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
GAME = Path(_paths.game_dir())
OUT = REPO / "work" / "p5_leishen" / "p6"
STAGING = OUT / "addon"
PNG_DIR = OUT / "_png"
MESH_DIR = OUT / "mesh"
LOG_DIR = OUT / "logs"
SOURCE1 = OUT / "source1"
ISOLATED = OUT / "isolated_game" / "csgo"
VERIFIED_ROOT = OUT / "verified_root"
IDENTITY = REPO / "work" / "p5_leishen" / "t04" / "identity_review.json"
GRAPH = REPO / "work" / "p5_leishen" / "t03" / "resource_graph.json"
C3_MANIFEST = REPO / "assets" / "weapons" / "m4a1_s_bornbeast" / "c3_alignment_m4a4_manifest.json"
REF_DIR = REPO / "work" / "m4a1_s_bornbeast" / "reference_m4a4"
CFREZ = REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"
STUDIOMDL = GAME / "bin" / "studiomdl.exe"
CROWBAR = REPO / "tools" / "CrowbarDecompiler" / "CrowbarDecompiler(1.1).exe"
ADDON_NAME = "p_cf_leishen_m4a4_p6"
PREV_ADDON = "p_cf_bornbeast_m4a4_n05j_formula_diag"
FROZEN_NAME = "p_cf_bornbeast_m4a4_p4_frozen_noop_01"
MIGI_ADDONS = GAME / "migi" / "csgo" / "addons"
PARK = GAME / "migi" / "csgo" / "_parked_addons"
MAT_REL = Path("materials/models/weapons/v_models/rif_m4a1")
MODEL_REL = Path("models/weapons")
LAYER_SMD = "cf_leishen_m4a4.smd"

EXPECTED_SHA = {
    "pv_ltb": "a0ccef5deed745f1731eb93295c630f531123288055f3c3790531b99b6e401b8",
    "pv_dtx": "7ca69f66d229a942752edd327fde145e45c2c00d65b570f5e5a6b6ac68d52555",
    "specular": "84694eb4f6df52e4781133f6843f545efaa04e2a88760078ae50c4b23b84084e",
    "normal": "882c4561f55e9d07163e3f7137b7097c209fcfbab50cbe4dc96f67ed42ba7f9d",
    "alpha": "9b66c835a190797e722b50cf2cf98d64b17d5cccd141cbd7b092795c7ab9cb7e",
    "cube": "c64014afe4b358b857a45aa025b05af81a3e6273ad203426afba0535191e9c8f",
}

WANTED_KEYS = {
    "pv_ltb": "MODELS/PLAYERVIEW/PV-M4A1_S_TRANSFORMERS.LTB",
    "pv_dtx": "MODELTEXTURES/PLAYERVIEW/PV-M4A1_S_TRANSFORMERS.DTX",
    "specular": "MODELTEXTURES/SPECULARMAP/M4A1_S_TRANSFORMERS_S.TGA",
    "normal": "MODELTEXTURES/NORMALMAP/M4A1_S_TRANSFORMERS_N.TGA",
    "alpha": "MODELTEXTURES/ALPHAMAP/M4A1_S_TRANSFORMERS_ALPHA.TGA",
    "cube": "MODELTEXTURES/ENVCUBEMAP/BLACK_SHADER02.DDS",
}

INDEX_RELS = (
    "rez2/RF016.REZ",
    "rez/RF016.REZ",
    "rez/rf017.rez",
    "rez3/RF017.REZ",
)

BONE_PARENT = (3, "v_weapon.M4A1_Parent")
BONE_CLIP = (4, "v_weapon.M4A1_Clip")
BONE_BOLT = (29, "v_weapon.M4A1_Bolt")

VMT = '''"VertexLitGeneric"
{
	"$basetexture" "models/weapons/v_models/rif_m4a1/rif_m4a1"
	"$bumpmap" "models/weapons/v_models/rif_m4a1/rif_m4a1_normal"
	"$phong" "1"
	"$phongexponent" "16"
	"$phongboost" "1"
	"$phongfresnelranges" "[0.05 0.5 1]"
	"$phongalbedotint" "1"
	"$envmap" "models/weapons/v_models/rif_m4a1/rif_m4a1_cube"
	"$envmapmask" "models/weapons/v_models/rif_m4a1/rif_m4a1_envmask"
	"$nocull" "0"
}
'''


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


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


def logical_key(full_path: str) -> str:
    return full_path.replace("\\", "/").upper()


def maybe_lzma(data: bytes) -> tuple[bytes, bool]:
    if data[:1] != b"\x5d":
        return data, False
    try:
        return lzma.decompress(data, format=lzma.FORMAT_ALONE), True
    except lzma.LZMAError:
        return data, False


def resolve_cf_file(relative: str) -> Path | None:
    direct = CF / relative
    if direct.is_file():
        return direct
    needle = Path(relative.replace("\\", "/"))
    parts = list(needle.parts)
    current = CF
    for part in parts:
        if not current.is_dir():
            return None
        matches = [child for child in current.iterdir() if child.name.casefold() == part.casefold()]
        if len(matches) != 1:
            return None
        current = matches[0]
    return current if current.is_file() else None


def tree_hashes(root: Path) -> dict[str, str]:
    rows: dict[str, str] = {}
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        rows[path.relative_to(root).as_posix()] = sha256_file(path)
    return rows


def channel_stats(image: Image.Image) -> dict[str, Any]:
    rows: dict[str, Any] = {}
    for name, band in zip(image.getbands(), image.split(), strict=True):
        extrema = band.getextrema()
        hist = band.histogram()
        total = image.size[0] * image.size[1]
        mean = sum(index * count for index, count in enumerate(hist)) / total
        rows[name] = {"min": extrema[0], "max": extrema[1], "mean": mean}
    return rows


def classify_group(name: str) -> str | None:
    lower = name.lower()
    if "fview" in lower or "hand" in lower or "arm" in lower:
        return None
    if "mag" in lower:
        return "clip"
    if "reload" in lower:
        return "bolt"
    return "parent"


def bone_for_kind(kind: str) -> tuple[int, str]:
    if kind == "clip":
        return BONE_CLIP
    if kind == "bolt":
        return BONE_BOLT
    return BONE_PARENT


def recover_payloads() -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    wanted_by_key = {value: role for role, value in WANTED_KEYS.items()}
    found: dict[str, list[dict[str, Any]]] = {role: [] for role in WANTED_KEYS}
    scanned: list[str] = []
    for relative in INDEX_RELS:
        index_path = resolve_cf_file(relative)
        if index_path is None:
            continue
        scanned.append(str(index_path))
        for entry in extract_all.read_index_entries(str(index_path)):
            key = logical_key(str(entry.get("full_path") or ""))
            role = wanted_by_key.get(key)
            if role is None:
                continue
            found[role].append({"index_archive": str(index_path), "entry": entry, "logical_key": key})

    recovered: dict[str, dict[str, Any]] = {}
    for role, expected in EXPECTED_SHA.items():
        candidates = found[role]
        if not candidates:
            raise RuntimeError(f"no index hit for {role} {WANTED_KEYS[role]}")
        matched = None
        errors: list[str] = []
        for candidate in candidates:
            try:
                data, provenance = read_verified_payload(candidate["index_archive"], candidate["entry"])
            except Exception as exc:
                errors.append(f"{candidate['index_archive']}: {exc}")
                continue
            digest = provenance["sha256"]
            if digest != expected:
                errors.append(f"{candidate['index_archive']} sha {digest} != {expected}")
                continue
            matched = {
                "role": role,
                "logical_key": candidate["logical_key"],
                "full_path": candidate["entry"]["full_path"],
                "raw": data,
                "sha256": digest,
                "size": len(data),
                "routing": provenance["routing"],
                "payload_file": provenance["payload_file"],
                "index_archive": provenance["index_archive"],
                "directory_md5": provenance["directory_md5"],
                "offset": provenance["offset"],
                "legacy_time_field": provenance["legacy_time_field"],
            }
            break
        if matched is None:
            raise RuntimeError(f"failed to recover {role}: {errors}")
        recovered[role] = matched
    return recovered, {"scanned": scanned}


def decode_payload(role: str, row: dict[str, Any], dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    data = row["raw"]
    suffix = Path(row["full_path"]).suffix.upper()
    if suffix == ".LTB":
        body, lzma_used = maybe_lzma(data)
        dest.write_bytes(body)
        return {
            "ok": True,
            "path": rel(dest),
            "bytes": len(body),
            "lzma": lzma_used,
            "sha256_raw": row["sha256"],
            "sha256_body": sha256_bytes(body),
        }
    if suffix == ".DTX":
        decoded = n05a.decode_repo_pixels(data)
        if not decoded.get("ok"):
            raise RuntimeError(f"DTX decode failed for {role}: {decoded}")
        image = decoded["image"].convert("RGBA")
        image.save(dest)
        return {
            "ok": True,
            "path": rel(dest),
            "size": list(image.size),
            "mode": image.mode,
            "format": decoded.get("format"),
            "png_sha256": sha256_file(dest),
        }
    if suffix == ".TGA":
        with Image.open(io.BytesIO(data)) as source:
            source.load()
            image = source.copy()
        image.save(dest)
        return {
            "ok": True,
            "path": rel(dest),
            "size": list(image.size),
            "mode": image.mode,
            "png_sha256": sha256_file(dest),
        }
    if suffix == ".DDS":
        src = dest.with_suffix(".dds")
        src.write_bytes(data)
        proc = subprocess.run(
            [str(CFREZ), "--decode-image", str(src), str(dest)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if proc.returncode != 0 or not dest.is_file():
            raise RuntimeError(f"DDS decode failed: {(proc.stderr or proc.stdout or '')[:500]}")
        with Image.open(dest) as image:
            copied = image.convert("RGBA").copy()
        copied.save(dest)
        return {
            "ok": True,
            "path": rel(dest),
            "size": list(copied.size),
            "mode": copied.mode,
            "png_sha256": sha256_file(dest),
            "stdout": (proc.stdout or "").strip()[:300],
        }
    raise RuntimeError(f"unsupported suffix {suffix} for {role}")


def export_obj(ltb_rel: str, dest: Path) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [
            str(CFREZ),
            "--export-obj",
            "--raw-transform",
            "--root",
            str(VERIFIED_ROOT),
            "--model",
            ltb_rel,
            "--output",
            str(dest),
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    (LOG_DIR / "cfrez_export.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "cfrez_export.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0 or not dest.is_file():
        raise RuntimeError(f"CFRezManager OBJ export failed: {(proc.stderr or proc.stdout or '')[:800]}")
    return {"obj": rel(dest), "sha256": sha256_file(dest), "bytes": dest.stat().st_size}


def mirror_x_obj(lines: list[str]) -> list[str]:
    out: list[str] = []
    for line in lines:
        if line.startswith("v "):
            parts = line.split()
            x, y, z = (float(parts[1]), float(parts[2]), float(parts[3]))
            out.append(f"v {-x:.9f} {y:.9f} {z:.9f}")
        elif line.startswith("vn "):
            parts = line.split()
            nx, ny, nz = (float(parts[1]), float(parts[2]), float(parts[3]))
            out.append(f"vn {-nx:.9f} {ny:.9f} {nz:.9f}")
        elif line.startswith("f "):
            corners = line.split()[1:]
            if len(corners) < 3:
                raise ValueError(f"invalid face: {line}")
            reversed_corners = [corners[0], *reversed(corners[1:])]
            out.append("f " + " ".join(reversed_corners))
        else:
            out.append(line)
    return out


def parse_weapon_obj(path: Path) -> tuple[
    list[tuple[float, float, float]],
    list[tuple[float, float]],
    list[tuple[float, float, float]],
    list[tuple[str, str, list[tuple[int, int, int]]]],
    dict[str, int],
    list[str],
]:
    vertices: list[tuple[float, float, float]] = []
    uvs: list[tuple[float, float]] = []
    normals: list[tuple[float, float, float]] = []
    faces: list[tuple[str, str, list[tuple[int, int, int]]]] = []
    triangles: dict[str, int] = {}
    skipped: list[str] = []
    group = ""
    material = "rif_m4a1"
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        parts = raw.split()
        if not parts:
            continue
        if parts[0] == "v":
            vertices.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "vt":
            uvs.append((float(parts[1]), float(parts[2])))
        elif parts[0] == "vn":
            normals.append((float(parts[1]), float(parts[2]), float(parts[3])))
        elif parts[0] == "g":
            group = parts[1] if len(parts) > 1 else ""
        elif parts[0] == "usemtl":
            material = parts[1] if len(parts) > 1 else "rif_m4a1"
        elif parts[0] == "f":
            kind = classify_group(group)
            if kind is None:
                if group not in skipped:
                    skipped.append(group)
                continue
            refs: list[tuple[int, int, int]] = []
            for token in parts[1:]:
                fields = token.split("/")
                if len(fields) != 3 or not all(fields):
                    raise ValueError(f"need v/vt/vn faces, got: {raw}")
                refs.append(tuple(int(value) - 1 for value in fields))
            if len(refs) != 3:
                raise ValueError(f"need triangles, got {len(refs)} corners in {group}")
            faces.append((group, material, refs))
            triangles[group] = triangles.get(group, 0) + 1
    if not faces:
        raise RuntimeError("no weapon triangles after dropping hands/arms")
    return vertices, uvs, normals, faces, triangles, skipped


def write_smd(
    aligned_obj: Path,
    reference_smd: Path,
    dest: Path,
) -> dict[str, Any]:
    vertices, uvs, normals, faces, triangles, skipped = parse_weapon_obj(aligned_obj)
    mapping: list[dict[str, Any]] = []
    kinds_seen = {classify_group(group) for group in triangles}
    if "parent" not in kinds_seen or "clip" not in kinds_seen:
        raise RuntimeError(f"weapon mapping missing body/mag: {triangles}")
    lines = smd_prefix(reference_smd)
    lines.append("triangles")
    for group, _material, refs in faces:
        kind = classify_group(group)
        assert kind is not None
        bone_index, bone_name = bone_for_kind(kind)
        lines.append("rif_m4a1")
        for vi, ti, ni in refs:
            pos = vertices[vi]
            norm = normals[ni]
            uv = uvs[ti]
            lines.append(
                f"  {bone_index} "
                + " ".join(f"{value:.9f}" for value in (*pos, *norm, uv[0], uv[1]))
                + f" 1 {bone_index} 1.000000"
            )
    lines.append("end")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("\n".join(lines) + "\n", encoding="utf-8")
    for group, count in sorted(triangles.items()):
        kind = classify_group(group)
        bone_index, bone_name = bone_for_kind(kind or "parent")
        mapping.append(
            {
                "group": group,
                "kind": kind,
                "bone_index": bone_index,
                "bone": bone_name,
                "triangles": count,
            }
        )
    return {
        "smd": rel(dest),
        "sha256": sha256_file(dest),
        "triangles": sum(triangles.values()),
        "groups": mapping,
        "skipped_arm_groups": skipped,
        "kinds": sorted(kind for kind in kinds_seen if kind),
    }


def vtfcmd(png: Path, dest: Path, fmt: str) -> dict[str, Any]:
    dest.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(VTFCMD), "-file", str(png), "-output", str(dest.parent), "-format", fmt, "-version", "7.4"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    generated = dest.parent / f"{png.stem}.vtf"
    if proc.returncode != 0 or not generated.is_file():
        raise RuntimeError(f"VTFCmd failed {png}: {proc.stderr or proc.stdout}")
    if generated != dest:
        if dest.exists():
            dest.unlink()
        generated.replace(dest)
    return {
        "png": rel(png),
        "png_sha256": sha256_file(png),
        "vtf": rel(dest),
        "vtf_sha256": sha256_file(dest),
        "format": fmt,
        "png_size": list(Image.open(png).size),
        "vtf_bytes": dest.stat().st_size,
    }


def save_rgb(source: Path, dest: Path) -> Path:
    image = Image.open(source).convert("RGB")
    dest.parent.mkdir(parents=True, exist_ok=True)
    image.save(dest)
    return dest


def park_previous() -> dict[str, Any]:
    live = MIGI_ADDONS / PREV_ADDON
    parked = PARK / PREV_ADDON
    result = {
        "src": str(live),
        "parked_dst": str(parked),
        "action": "absent",
        "frozen_modified": False,
    }
    if parked.exists() and not live.exists():
        result["action"] = "already_parked"
        return result
    if not live.exists():
        return result
    PARK.mkdir(parents=True, exist_ok=True)
    if parked.exists():
        shutil.rmtree(parked)
        result["parked_replaced"] = True
    shutil.move(str(live), str(parked))
    result["action"] = "moved_outside_addons"
    result["note"] = "N05-J diagnostic folder moved out of MIGI addons so P6 can load. Files were not edited."
    return result


def frozen_status() -> dict[str, Any]:
    frozen = MIGI_ADDONS / FROZEN_NAME
    parked = PARK / FROZEN_NAME
    return {
        "frozen_in_addons": frozen.exists(),
        "frozen_parked": parked.exists(),
        "frozen_modified": False,
        "parked_dst": str(parked),
    }


def deploy_addon(staging_hashes: dict[str, str]) -> dict[str, Any]:
    target = MIGI_ADDONS / ADDON_NAME
    if target.exists():
        existing = tree_hashes(target)
        if existing == staging_hashes:
            return {"target": str(target), "action": "verified_existing", "hashes": existing}
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    for relative in staging_hashes:
        src = STAGING / relative
        dst = target / relative
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    deployed = tree_hashes(target)
    if deployed != staging_hashes:
        raise RuntimeError("post-deploy hash mismatch")
    return {"target": str(target), "action": "created", "hashes": deployed}


def run_studiomdl(qc_path: Path) -> dict[str, Any]:
    compiled = ISOLATED / "models" / "weapons" / "v_rif_m4a1.mdl"
    proc = subprocess.run(
        [str(STUDIOMDL), "-game", str(ISOLATED), str(qc_path)],
        cwd=str(SOURCE1),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    (LOG_DIR / "studiomdl.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "studiomdl.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0 or not compiled.is_file():
        raise RuntimeError(
            f"studiomdl failed ({proc.returncode}): {(proc.stderr or proc.stdout or '')[-1200:]}"
        )
    return {"mdl": rel(compiled), "exit_code": proc.returncode, "sha256": sha256_file(compiled)}


def main() -> int:
    identity = json.loads(IDENTITY.read_text(encoding="utf-8"))
    if not identity.get("identity_confirmed"):
        raise RuntimeError("P5-T04 is not IDENTITY_CONFIRMED")
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    c3 = json.loads(C3_MANIFEST.read_text(encoding="utf-8"))
    if OUT.exists():
        shutil.rmtree(OUT)
    for path in (OUT, STAGING, PNG_DIR, MESH_DIR, LOG_DIR, SOURCE1, ISOLATED, VERIFIED_ROOT):
        path.mkdir(parents=True, exist_ok=True)

    recovered, scan_meta = recover_payloads()
    decoded: dict[str, Any] = {}
    ltb_rel = "Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB"
    ltb_path = VERIFIED_ROOT / Path(ltb_rel)
    decoded["pv_ltb"] = decode_payload("pv_ltb", recovered["pv_ltb"], ltb_path)
    decoded["pv_dtx"] = decode_payload("pv_dtx", recovered["pv_dtx"], PNG_DIR / "diffuse.png")
    decoded["normal"] = decode_payload("normal", recovered["normal"], PNG_DIR / "normal_src.png")
    decoded["specular"] = decode_payload("specular", recovered["specular"], PNG_DIR / "specular_src.png")
    decoded["alpha"] = decode_payload("alpha", recovered["alpha"], PNG_DIR / "alpha_src.png")
    decoded["cube"] = decode_payload("cube", recovered["cube"], PNG_DIR / "cube_face0.png")

    raw_obj = MESH_DIR / "PV-M4A1_S_Transformers_raw.obj"
    export_info = export_obj(ltb_rel.replace("\\", "/"), raw_obj)
    raw_lines = raw_obj.read_text(encoding="utf-8", errors="replace").splitlines()
    mirrored_lines = mirror_x_obj(raw_lines)
    mirrored_obj = MESH_DIR / "PV-M4A1_S_Transformers_x_mirror.obj"
    mirrored_obj.write_text("\n".join(mirrored_lines) + "\n", encoding="utf-8")
    matrix = c3["matrix_cf_to_source"]
    rotation = normalize_rotation(matrix, c3["uniform_scale"])
    aligned_lines = transform_lines(mirrored_lines, matrix, rotation)
    aligned_obj = MESH_DIR / "PV-M4A1_S_Transformers_c3_aligned.obj"
    aligned_obj.write_text("\n".join(aligned_lines) + "\n", encoding="utf-8")

    shutil.copytree(REF_DIR / "decompiled", SOURCE1, dirs_exist_ok=True)
    shutil.copy2(GAME / "csgo" / "gameinfo.txt", ISOLATED / "gameinfo.txt")
    ref_materials = REF_DIR / "source_vpk" / "materials"
    if ref_materials.is_dir():
        shutil.copytree(ref_materials, ISOLATED / "materials", dirs_exist_ok=True)

    smd_info = write_smd(aligned_obj, SOURCE1 / "v_m4a1_model.smd", SOURCE1 / LAYER_SMD)
    qc_path = SOURCE1 / "v_rif_m4a1.qc"
    qc_text = qc_path.read_text(encoding="utf-8", errors="replace")
    qc_text, count = re.subn(r'studio\s+"v_m4a1_model\.smd"', f'studio "{LAYER_SMD}"', qc_text, count=1, flags=re.I)
    if count != 1:
        raise RuntimeError("failed to replace QC bodygroup reference exactly once")
    qc_text, inspect_report = apply_inspect_policy(qc_text, "frozen_noop_safe", SOURCE1)
    qc_path.write_text(qc_text, encoding="utf-8")
    sequences = re.findall(r'\$sequence\s+"([^"]+)"', qc_text, flags=re.I)
    expected_sequences = ["idle", "shoot1", "shoot2", "shoot3", "reload", "draw", "lookat01", "lookat01_prepare", "lookat01_loop"]
    if sequences != expected_sequences:
        raise RuntimeError(f"QC sequences mismatch: {sequences}")

    compile_info = run_studiomdl(qc_path)
    header = mdl_header(ISOLATED / "models" / "weapons" / "v_rif_m4a1.mdl")
    if header["bone_count"] != 57:
        raise RuntimeError(f"compiled bone_count {header['bone_count']} != 57")
    if header["internal_name"].replace("\\", "/") != "weapons/v_rif_m4a1.mdl":
        raise RuntimeError(f"internal model name mismatch: {header['internal_name']}")

    models_dir = STAGING / MODEL_REL
    models_dir.mkdir(parents=True, exist_ok=True)
    compiled_models: dict[str, str] = {}
    for path in (ISOLATED / "models" / "weapons").glob("v_rif_m4a1.*"):
        dest = models_dir / path.name
        shutil.copy2(path, dest)
        compiled_models[path.name] = sha256_file(dest)

    alpha_image = Image.open(PNG_DIR / "alpha_src.png").convert("RGB")
    stats = channel_stats(alpha_image)
    _r, _g, blue = alpha_image.split()
    envmask = Image.merge("RGB", (blue, blue, blue))
    envmask_png = PNG_DIR / "envmask_from_alpha_b.png"
    envmask.save(envmask_png)

    mat_dir = STAGING / MAT_REL
    vtfs = {
        "diffuse": vtfcmd(save_rgb(PNG_DIR / "diffuse.png", PNG_DIR / "diffuse_rgb.png"), mat_dir / "rif_m4a1.vtf", "dxt1"),
        "normal": vtfcmd(save_rgb(PNG_DIR / "normal_src.png", PNG_DIR / "normal_rgb.png"), mat_dir / "rif_m4a1_normal.vtf", "dxt5"),
        "cube": vtfcmd(save_rgb(PNG_DIR / "cube_face0.png", PNG_DIR / "cube_rgb.png"), mat_dir / "rif_m4a1_cube.vtf", "dxt1"),
        "envmask": vtfcmd(envmask_png, mat_dir / "rif_m4a1_envmask.vtf", "dxt1"),
    }
    vmt_path = mat_dir / "rif_m4a1.vmt"
    vmt_path.write_text(VMT.replace("\n", "\r\n"), encoding="ascii")

    staging_hashes = tree_hashes(STAGING)
    frozen = frozen_status()
    if frozen["frozen_in_addons"]:
        raise RuntimeError("frozen addon is still in MIGI addons; refuse to deploy a second v_rif_m4a1")
    previous = park_previous()
    deploy = deploy_addon(staging_hashes)

    recovered_public = {
        role: {
            "full_path": row["full_path"],
            "sha256": row["sha256"],
            "size": row["size"],
            "routing": row["routing"],
            "index_archive": row["index_archive"],
            "payload_file": row["payload_file"],
            "directory_md5": row["directory_md5"],
        }
        for role, row in recovered.items()
    }
    report = {
        "schema": "cf2.p6.identity-replacement.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P6",
        "result": "P6_IDENTITY_REPLACEMENT_DEPLOYED",
        "identity_confirmed": True,
        "final_target_identity": True,
        "final_cf_material": False,
        "p4_m01": "INCOMPLETE",
        "official": identity.get("official"),
        "local": identity.get("local"),
        "addon_name": ADDON_NAME,
        "inspect_policy": inspect_report,
        "recovered": recovered_public,
        "decoded": decoded,
        "scan": scan_meta,
        "export": export_info,
        "mirror": {
            "axis": "LTB X",
            "operation": "scale.x=-1 plus reverse faces, then frozen C3 matrix",
            "user_confirmation": "对了",
            "raw_obj": rel(raw_obj),
            "mirrored_obj": rel(mirrored_obj),
            "aligned_obj": rel(aligned_obj),
            "aligned_sha256": sha256_file(aligned_obj),
        },
        "smd": smd_info,
        "compile": compile_info,
        "mdl_header": header,
        "compiled_models": compiled_models,
        "alpha_channel_stats": stats,
        "vtfs": vtfs,
        "vmt_sha256": sha256_file(vmt_path),
        "staging": rel(STAGING),
        "staging_hashes": staging_hashes,
        "previous_diagnostic": {k: v for k, v in previous.items()},
        "park_frozen": frozen,
        "deploy": {k: v for k, v in deploy.items() if k != "hashes"} | {"file_count": len(deploy["hashes"])},
        "cfg_recorded_not_copied": next(
            (node.get("cfg") for node in graph.get("nodes", []) if node.get("id") == "weapon_shader_cfg"),
            None,
        ),
        "notes": [
            "Identity is base PV-M4A1_S_Transformers / M4A1-雷神. BornBeast is not this weapon.",
            "LTB X mirror is the user-confirmed left/right fix; C3 is the frozen P4 M4A4 alignment.",
            "VMT follows N05-J: AlphaMap.b as $envmapmask. $phongexponent 16 is still a placeholder.",
            "Cube is first DDS face only. CFG scalars were not copied as Source phong/envmap numbers.",
            "Inspect stays frozen_noop_safe; visible Inspect is P7.",
            "Not a P4-M01 PASS. Lighting/feel remain deferred.",
        ],
    }
    (OUT / "execution.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "mapping.json").write_text(json.dumps({
        "addon_name": ADDON_NAME,
        "result": report["result"],
        "smd": smd_info,
        "vtfs": {name: {"vtf": row["vtf"], "vtf_sha256": row["vtf_sha256"]} for name, row in vtfs.items()},
        "compiled_models": compiled_models,
        "vmt_sha256": report["vmt_sha256"],
        "staging_hashes": staging_hashes,
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.md").write_text(
        "\n".join(
            [
                "# P6 — M4A1-雷神 identity replacement",
                "",
                "Result: **P6_IDENTITY_REPLACEMENT_DEPLOYED**. `final_target_identity=true`. `final_cf_material=false`. P4-M01 remains **INCOMPLETE**.",
                "",
                f"Addon: `{ADDON_NAME}`",
                f"Deploy: `{deploy['target']}` ({deploy['action']})",
                f"Previous N05-J: `{previous['action']}`",
                f"Frozen parked: `{frozen['frozen_parked']}` (not modified)",
                "",
                "Local identity is base `PV-M4A1_S_Transformers` (user 是雷神 + Bute WeaponName M4A1-雷神). Mesh is compiled from the verified PV LTB, not the P4 BornBeast prototype mesh.",
                "",
                "Left/right: LTB X scale −1 + reverse faces, then the frozen C3 M4A4 matrix. User already confirmed the Blender preview 「对了」.",
                "",
                "Materials reuse the N05-J formula: AlphaMap.b → `$envmapmask`. `$phongexponent 16` is still a placeholder. Cube is face0 only. CFG scalars were not copied.",
                "",
                f"Compiled MDL internal name `{header['internal_name']}`, bones `{header['bone_count']}`, sequences `{header['local_sequence_count']}`.",
                "",
                "This is not P4-M01 PASS and not a lighting match. In-game look still needs a user Gate.",
                "",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    print(json.dumps({
        "result": report["result"],
        "addon": ADDON_NAME,
        "deploy": deploy["action"],
        "previous": previous["action"],
        "triangles": smd_info["triangles"],
        "groups": [item["group"] for item in smd_info["groups"]],
        "out": rel(OUT),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
