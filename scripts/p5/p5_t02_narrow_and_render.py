# -*- coding: utf-8 -*-
"""P5-T02: narrow legacy M4 PLAYERVIEW candidates and render real LTB geometry.

This is an evidence producer, not an identity resolver.  It deliberately keeps
the official reference separate from the local-model previews and leaves the
user visual gate open.
"""

from __future__ import annotations

import hashlib
import json
import lzma
import math
import re
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageFont, ImageOps


ROOT = Path(__file__).resolve().parents[2]
T01_INDEX = ROOT / "work" / "p5_leishen" / "t01" / "candidate_index.json"
T01_MATRIX = ROOT / "work" / "p5_leishen" / "t01" / "candidate_matrix.csv"
T01_REFERENCE = ROOT / "work" / "p5_leishen" / "t01_reference" / "official_reference.json"
T02_DIR = ROOT / "work" / "p5_leishen" / "t02"
PREVIEW_DIR = T02_DIR / "previews"
DECODER_DLL = ROOT / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.dll"
RUNNER_DLL = T02_DIR / ".runner" / "bin" / "Release" / "net8.0" / "P5T02ModelReader.dll"
DOTNET = Path("C:/Program Files/dotnet/dotnet.exe")
OFFICIAL_BROWSER_ASSET = Path(
    "C:/Users/Administrator/AppData/Local/Temp/browser-use/assets/"
    "04922947-a092-4555-a1a3-81212d07e68e/3c5856b6cc3646aa.png"
)

WIDTH = 768
HEIGHT = 384
MARGIN = 28
HEADER_HEIGHT = 28
EXCLUDED_MESH_RE = re.compile(r"(hand|arm|sleeve|glove|wrist|view[-_]?body)", re.I)
EXCLUDED_FILE_RE = re.compile(r"(_BL|_GR|WOMAN|SPRINT|RUN|JUMP|RELOAD|INSPECT|ANIM)", re.I)
TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def path_parts(record: dict[str, Any]) -> tuple[str, str]:
    return str(record.get("relative_path", "")).replace("\\", "/"), str(record.get("filename", ""))


def is_weapon_body_candidate(record: dict[str, Any]) -> bool:
    relative_path, filename = path_parts(record)
    upper_path = relative_path.upper()
    upper_name = filename.upper()
    summary = record.get("light_summary") or {}
    return (
        str(record.get("extension", "")).lower() == ".ltb"
        and "/MODELS/PLAYERVIEW/" in upper_path
        and "M4" in upper_name
        and not EXCLUDED_FILE_RE.search(upper_name)
        and "/QV/" not in upper_path
        and "/WEAPONS/" not in upper_path
        and int(summary.get("weapon_mesh_count", 0) or 0) > 0
    )


def variant_tokens(filename: str) -> list[str]:
    ignored = {"PV", "M4", "M4A1", "S", "LTB", "PLAYERVIEW"}
    return sorted({token for token in TOKEN_RE.findall(Path(filename).stem) if token.upper() not in ignored})


def cluster_candidates(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for record in records:
        grouped.setdefault(str(record["sha256"]).lower(), []).append(record)

    clusters: list[dict[str, Any]] = []
    for index, digest in enumerate(
        sorted(grouped, key=lambda key: min(int(item.get("rank", 10**9)) for item in grouped[key])),
        start=1,
    ):
        members = sorted(grouped[digest], key=lambda item: int(item.get("rank", 10**9)))
        representative = members[0]
        paths = [str(item["relative_path"]).replace("\\", "/") for item in members]
        tokens = sorted({token for item in members for token in variant_tokens(str(item["filename"]))})
        summary = representative.get("light_summary") or {}
        clusters.append(
            {
                "cluster_id": f"C{index:03d}",
                "representative_ltb": paths[0],
                "member_paths": paths,
                "sha256": [digest],
                "geometry_signature": None,
                "variant_tokens": tokens,
                "exclusion_reason": None,
                "identity_status": "CANDIDATE_ONLY",
                "legacy_rank": int(representative.get("rank", 10**9)),
                "legacy_light_summary": summary,
                "member_count": len(paths),
            }
        )
    return clusters


def choose_shortlist(clusters: list[dict[str, Any]], limit: int = 15) -> list[dict[str, Any]]:
    ranked = sorted(clusters, key=lambda item: item["legacy_rank"])
    selected: list[dict[str, Any]] = ranked[:10]

    # Rank is recall evidence, not identity evidence.  Add a few late-rank
    # samples so a legacy score cannot silently decide the local candidate.
    for fraction in (0.25, 0.50, 0.75):
        if len(selected) >= limit:
            break
        candidate = ranked[min(len(ranked) - 1, int(len(ranked) * fraction))]
        if candidate not in selected:
            selected.append(candidate)

    # Keep the known late-rank Transformers geometry in the visual audit only
    # as a recall sanity check.  It is not treated as confirmed identity.
    late_rank_sanity = next(
        (
            item
            for item in ranked
            if any(Path(member).name.upper() == "PV-M4A1_S_TRANSFORMERS.LTB" for member in item["member_paths"])
        ),
        None,
    )
    if late_rank_sanity is not None and late_rank_sanity not in selected and len(selected) < limit:
        selected.append(late_rank_sanity)

    for candidate in ranked:
        if len(selected) >= limit:
            break
        if candidate not in selected:
            selected.append(candidate)
    return selected[:limit]


def decode_geometry(
    relative_path: str,
    work_dir: Path,
) -> tuple[dict[str, Any], str]:
    source = ROOT / Path(relative_path)
    raw_path = work_dir / (source.stem + ".raw")
    json_path = work_dir / (source.stem + ".geometry.json")
    raw_path.write_bytes(lzma.decompress(source.read_bytes(), format=lzma.FORMAT_ALONE))
    command = [str(DOTNET), str(RUNNER_DLL), str(DECODER_DLL), str(raw_path), str(json_path)]
    completed = subprocess.run(command, capture_output=True, text=True, timeout=90, check=False)
    if completed.returncode != 0 or not json_path.exists():
        detail = (completed.stderr or completed.stdout or "decoder returned no detail").strip()
        raise RuntimeError(f"{relative_path}: {detail}")
    return load_json(json_path), sha256_file(source)


def weapon_meshes(document: dict[str, Any]) -> list[dict[str, Any]]:
    meshes: list[dict[str, Any]] = []
    for mesh in document.get("meshes", []):
        name = str(mesh.get("name", ""))
        if EXCLUDED_MESH_RE.search(name):
            continue
        vertices = mesh.get("vertices") or []
        indices = mesh.get("triangle_indices") or []
        if len(vertices) < 3 or len(indices) < 3:
            continue
        meshes.append(mesh)
    return meshes


def geometry_signature(document: dict[str, Any]) -> str:
    descriptors: list[tuple[Any, ...]] = []
    for mesh in weapon_meshes(document):
        vertices = mesh.get("vertices") or []
        xs = [float(vertex[0]) for vertex in vertices]
        ys = [float(vertex[1]) for vertex in vertices]
        zs = [float(vertex[2]) for vertex in vertices]
        descriptors.append(
            (
                len(vertices),
                len(mesh.get("triangle_indices") or []) // 3,
                tuple(round(max(values) - min(values), 4) for values in (xs, ys, zs)),
            )
        )
    payload = json.dumps(sorted(descriptors), separators=(",", ":"), ensure_ascii=True).encode("ascii")
    return "geomsha256:" + hashlib.sha256(payload).hexdigest()


def project_points(vertices: list[list[float]], min_x: float, min_y: float, min_z: float, scale: float) -> list[tuple[float, float, float]]:
    center_z = min_z
    center_y = min_y
    projected: list[tuple[float, float, float]] = []
    for x, y, z in vertices:
        screen_x = MARGIN + (z - center_z) * scale
        screen_y = HEIGHT - MARGIN - (y - center_y) * scale
        projected.append((screen_x, screen_y, float(x)))
    return projected


def render_side(document: dict[str, Any], output_path: Path, label: str) -> dict[str, Any]:
    meshes = weapon_meshes(document)
    all_vertices = [vertex for mesh in meshes for vertex in mesh.get("vertices", [])]
    if not all_vertices:
        raise RuntimeError("no weapon meshes remain after hand/arm exclusion")
    min_x = min(float(vertex[0]) for vertex in all_vertices)
    max_x = max(float(vertex[0]) for vertex in all_vertices)
    min_y = min(float(vertex[1]) for vertex in all_vertices)
    max_y = max(float(vertex[1]) for vertex in all_vertices)
    min_z = min(float(vertex[2]) for vertex in all_vertices)
    max_z = max(float(vertex[2]) for vertex in all_vertices)
    range_z = max(max_z - min_z, 1e-6)
    range_y = max(max_y - min_y, 1e-6)
    scale = min((WIDTH - 2 * MARGIN) / range_z, (HEIGHT - 2 * MARGIN - HEADER_HEIGHT) / range_y)
    offset_x = (WIDTH - (range_z * scale)) / 2.0
    offset_y = HEADER_HEIGHT + (HEIGHT - HEADER_HEIGHT - (range_y * scale)) / 2.0

    image = Image.new("RGBA", (WIDTH, HEIGHT), (255, 255, 255, 255))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    draw.text((10, 8), label, fill=(25, 35, 48, 255), font=font)
    face_records: list[tuple[float, list[tuple[float, float]], tuple[int, int, int]]] = []

    for mesh in meshes:
        vertices = mesh.get("vertices") or []
        projected: list[tuple[float, float, float]] = []
        for vertex in vertices:
            x, y, z = (float(value) for value in vertex)
            projected.append(
                (
                    offset_x + (z - min_z) * scale,
                    offset_y + (max_y - y) * scale,
                    x,
                )
            )
        indices = mesh.get("triangle_indices") or []
        for position in range(0, len(indices) - 2, 3):
            try:
                a, b, c = (int(indices[position + offset]) for offset in range(3))
                pa, pb, pc = projected[a], projected[b], projected[c]
            except (IndexError, ValueError):
                continue
            ax, ay, az = vertices[b][0] - vertices[a][0], vertices[b][1] - vertices[a][1], vertices[b][2] - vertices[a][2]
            bx, by, bz = vertices[c][0] - vertices[a][0], vertices[c][1] - vertices[a][1], vertices[c][2] - vertices[a][2]
            nx, ny, nz = ay * bz - az * by, az * bx - ax * bz, ax * by - ay * bx
            normal_length = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
            light = max(0.15, min(1.0, (nx * 0.55 + ny * 0.75 + nz * 0.35) / normal_length))
            base = (158, 169, 182)
            color = tuple(int(min(245, channel * (0.62 + 0.38 * light))) for channel in base)
            face_records.append(((pa[2] + pb[2] + pc[2]) / 3.0, [(pa[0], pa[1]), (pb[0], pb[1]), (pc[0], pc[1])], color))

    # Far-to-near painter order gives a stable orthographic silhouette.
    for _, polygon, color in sorted(face_records, key=lambda item: item[0]):
        draw.polygon(polygon, fill=color + (255,))
        draw.line(polygon + [polygon[0]], fill=(55, 67, 82, 255), width=1, joint="curve")

    image.save(output_path)
    return {
        "render_width": WIDTH,
        "render_height": HEIGHT,
        "weapon_mesh_count": len(meshes),
        "rendered_triangle_count": len(face_records),
        "excluded_mesh_names": [str(mesh.get("name", "")) for mesh in document.get("meshes", []) if mesh not in meshes],
        "projection": "orthographic side; world Z horizontal, world Y vertical, world X depth",
        "texture_status": "not_available",
    }


def fit_reference(image_path: Path, width: int, height: int) -> Image.Image:
    source = Image.open(image_path).convert("RGBA")
    source.thumbnail((width - 20, height - 20), Image.Resampling.LANCZOS)
    panel = Image.new("RGBA", (width, height), (248, 250, 252, 255))
    panel.alpha_composite(source, ((width - source.width) // 2, (height - source.height) // 2))
    return panel


def make_contact_sheet(reference: dict[str, Any], shortlist: list[dict[str, Any]], official_image: Path, output_path: Path) -> None:
    columns = 3
    cell_width = 360
    cell_height = 215
    header_height = 232
    rows = math.ceil(len(shortlist) / columns)
    sheet = Image.new("RGBA", (columns * cell_width, header_height + rows * cell_height), (235, 239, 244, 255))
    draw = ImageDraw.Draw(sheet)
    font = ImageFont.load_default()
    draw.text((14, 10), "P5-T02 local geometry shortlist (actual LTB decode; gray fallback)", fill=(18, 28, 40, 255), font=font)
    draw.text((14, 28), "Official reference: M4A1-雷神 / C0457.png — local candidate identity remains unconfirmed", fill=(18, 28, 40, 255), font=font)
    reference_panel = fit_reference(official_image, sheet.width - 28, 178)
    sheet.alpha_composite(reference_panel, (14, 48))

    for index, item in enumerate(shortlist):
        image = Image.open(ROOT / item["preview_path"]).convert("RGBA")
        image = ImageOps.contain(image, (cell_width - 12, 172), Image.Resampling.LANCZOS)
        left = (index % columns) * cell_width
        top = header_height + (index // columns) * cell_height
        tile = Image.new("RGBA", (cell_width, cell_height), (255, 255, 255, 255))
        tile.alpha_composite(image, ((cell_width - image.width) // 2, 4))
        label = f"{item['cluster_id']} | rank {item['legacy_rank']} | {Path(item['representative_ltb']).name}"
        draw_tile = ImageDraw.Draw(tile)
        draw_tile.text((6, 179), label[:60], fill=(20, 30, 42, 255), font=font)
        sheet.alpha_composite(tile, (left, top))

    sheet.convert("RGB").save(output_path)


def main() -> int:
    started = now()
    reference = load_json(T01_REFERENCE)
    if reference.get("user_confirmation") != "confirmed":
        raise RuntimeError("T01 official reference is not user-confirmed")
    if not T01_INDEX.exists() or not T01_MATRIX.exists():
        raise RuntimeError("legacy T01 candidate evidence is missing")
    if not RUNNER_DLL.exists() or not DECODER_DLL.exists():
        raise RuntimeError("required local decoder helper is missing")
    if not OFFICIAL_BROWSER_ASSET.exists():
        raise RuntimeError(f"confirmed official browser asset is missing: {OFFICIAL_BROWSER_ASSET}")

    index_document = load_json(T01_INDEX)
    records = [record for record in index_document.get("candidates", []) if is_weapon_body_candidate(record)]
    clusters = cluster_candidates(records)
    shortlist = choose_shortlist(clusters)
    T02_DIR.mkdir(parents=True, exist_ok=True)
    PREVIEW_DIR.mkdir(parents=True, exist_ok=True)

    decoded: dict[str, dict[str, Any]] = {}
    render_reports: dict[str, dict[str, Any]] = {}
    errors: list[str] = []
    with tempfile.TemporaryDirectory(prefix="p5_t02_ltb_") as temporary:
        temporary_path = Path(temporary)
        for item in shortlist:
            try:
                document, source_sha256 = decode_geometry(item["representative_ltb"], temporary_path)
                signature = geometry_signature(document)
                item["geometry_signature"] = signature
                item["decoded_geometry"] = {
                    "vertex_count": int(document.get("vertex_count", 0)),
                    "triangle_count": int(document.get("triangle_count", 0)),
                    "weapon_mesh_count": len(weapon_meshes(document)),
                    "storage_description": document.get("storage_description"),
                }
                preview_name = f"{item['cluster_id']}_{Path(item['representative_ltb']).stem}.png"
                preview_path = PREVIEW_DIR / preview_name
                render_reports[item["cluster_id"]] = render_side(
                    document,
                    preview_path,
                    f"{item['cluster_id']} | rank {item['legacy_rank']} | local LTB geometry",
                )
                item["preview_path"] = str(preview_path.relative_to(ROOT)).replace("\\", "/")
                item["model_sha256_verified"] = source_sha256
                decoded[item["cluster_id"]] = document
            except Exception as error:  # evidence records the failure; one bad candidate must not hide the rest
                errors.append(f"{item['cluster_id']} {item['representative_ltb']}: {error}")
                item["preview_path"] = None
                item["decode_status"] = "failed"

    shortlisted_records: list[dict[str, Any]] = []
    for item in shortlist:
        shortlisted_records.append(
            {
                "cluster_id": item["cluster_id"],
                "representative_ltb": item["representative_ltb"],
                "model_sha256": item["sha256"][0],
                "legacy_rank": item["legacy_rank"],
                "member_count": item["member_count"],
                "variant_tokens": item["variant_tokens"],
                "geometry_signature": item.get("geometry_signature"),
                "preview_path": item.get("preview_path"),
                "texture_status": "not_available",
                "visual_gate_role": "comparison_candidate_only",
                "identity_status": "CANDIDATE_ONLY",
                "render_report": render_reports.get(item["cluster_id"]),
            }
        )

    make_contact_sheet(reference, shortlisted_records, OFFICIAL_BROWSER_ASSET, T02_DIR / "contact_sheet.png")

    for item in clusters:
        # Only shortlisted representatives were decoded; the rest remain explicit
        # nullable geometry evidence rather than inferred identity.
        item.pop("legacy_light_summary", None)

    (T02_DIR / "candidate_clusters.json").write_text(
        json.dumps(
            {
                "schema": "cf2.p5.t02.candidate-clusters.v1",
                "task_id": "P5-T02",
                "status": "AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION",
                "official_reference_page": reference["official_page_url"],
                "official_reference_image": reference["official_image_url"],
                "deduplication": {"primary": "exact_sha256", "geometry_signature": "computed_for_shortlisted_representatives_when_decoded"},
                "filter": {"source": "legacy_candidate_index_and_matrix", "models_scope": "PLAYERVIEW M4/M4A1 family weapon-body candidates", "excluded": ["_BL", "_GR", "WOMAN", "SPRINT/RUN/ANIM derived views", "QV/WEAPONS/world/third-person", "hand/arm/sleeve-only"]},
                "candidate_count_before_exact_sha_dedup": len(records),
                "cluster_count_after_exact_sha_dedup": len(clusters),
                "clusters": clusters,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    (T02_DIR / "visual_shortlist.json").write_text(
        json.dumps(
            {
                "schema": "cf2.p5.t02.visual-shortlist.v1",
                "task_id": "P5-T02",
                "status": "AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION",
                "official_reference": {"page": reference["official_page_url"], "image": reference["official_image_url"], "user_confirmation": reference["user_confirmation"]},
                "selection_policy": "legacy rank top-10 plus rank-stratified late samples and one late-rank sanity sample; no filename-only identity lock",
                "texture_policy": "UV/material hints were not available through this decoder pass; previews are explicitly gray geometry fallback and cannot alone confirm final local identity",
                "candidates": shortlisted_records,
                "user_gate": {"required": True, "state": "AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION", "identity_confirmed": False},
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    execution = {
        "schema": "cf2.p5.t02.execution.v1",
        "task_id": "P5-T02",
        "status": "AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION" if not errors else "AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION_WITH_DECODE_ERRORS",
        "started_at": started,
        "completed_at": now(),
        "preconditions": {"t01_user_reference": reference.get("user_confirmation"), "official_page_present": bool(reference.get("official_page_url")), "official_image_present": bool(reference.get("official_image_url")), "legacy_index_present": T01_INDEX.exists(), "legacy_matrix_present": T01_MATRIX.exists()},
        "inputs": {"official_reference_json": str(T01_REFERENCE.relative_to(ROOT)).replace("\\", "/"), "official_reference_sha256": sha256_file(T01_REFERENCE), "candidate_index": str(T01_INDEX.relative_to(ROOT)).replace("\\", "/"), "candidate_index_sha256": sha256_file(T01_INDEX), "candidate_matrix": str(T01_MATRIX.relative_to(ROOT)).replace("\\", "/"), "candidate_matrix_sha256": sha256_file(T01_MATRIX)},
        "narrowing": {"filtered_records": len(records), "exact_sha_clusters": len(clusters), "shortlist_count": len(shortlist), "source_rescan": False, "data_modified": False},
        "decoder": {"component": "CFRezManager LithTechModelDecoder via temporary reflection runner", "outer_compression": "standard Python LZMA FORMAT_ALONE decompression before decoder", "runner_path_local_only": str(RUNNER_DLL.relative_to(ROOT)).replace("\\", "/")},
        "render": {"width": WIDTH, "height": HEIGHT, "background": "white", "camera": "orthographic side", "animation": False, "ik": False, "retarget": False, "complex_lighting": False, "cycles": False, "texture_status": "not_available", "provenance": "actual local LTB geometry; no AI/generated image"},
        "outputs": {"candidate_clusters": "work/p5_leishen/t02/candidate_clusters.json", "visual_shortlist": "work/p5_leishen/t02/visual_shortlist.json", "contact_sheet": "work/p5_leishen/t02/contact_sheet.png", "previews": "work/p5_leishen/t02/previews/*.png"},
        "decode_errors": errors,
        "identity_status": "CANDIDATE_ONLY",
        "next_action": "show contact_sheet.png and visual_shortlist.json to user; wait for explicit local candidate confirmation; do not write IDENTITY_CONFIRMED",
    }
    (T02_DIR / "execution.json").write_text(json.dumps(execution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": execution["status"], "filtered_records": len(records), "clusters": len(clusters), "shortlist": len(shortlist), "errors": errors}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
