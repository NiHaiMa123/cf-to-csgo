from __future__ import annotations

import csv
from concurrent.futures import ThreadPoolExecutor, as_completed
import hashlib
import json
import re
import subprocess
import sys
import tempfile
import time
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data"
OUT = ROOT / "work" / "p5_leishen" / "t01"
CFREZ = ROOT / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
TOKENS = ("M4", "M4A1", "M4A1-S", "M4A1S", "雷神", "LEISHEN", "LEI_SHEN", "THOR", "THUNDER")
TEXT_EXTS = {".cfg", ".ini", ".json", ".xml", ".lua", ".csv", ".txt", ".ifx", ".ifl", ".qci", ".qc", ".smd", ".mtl"}
TEXT_LIMIT = 8 * 1024 * 1024
KNOWN_VARIANTS = ("bornbeast", "ironbeast", "predator", "transformers", "prismbeast", "jewelry", "beast", "leishen", "thor", "thunder")


def now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", value.casefold())


def token_matches(value: str) -> list[str]:
    haystack = normalized(value)
    hits: list[str] = []
    for token in TOKENS:
        if normalized(token) in haystack:
            hits.append(token)
    return hits


def source_class(path: Path) -> str:
    parts = [part.casefold() for part in path.parts]
    return "raw_cf_asset" if len(parts) >= 2 and parts[0] == "data" and parts[1].startswith("rf") else "derived_or_unclassified_local_file"


def candidate_type(path: Path) -> str:
    ext = path.suffix.casefold()
    text = path.as_posix().casefold()
    if ext == ".ltb":
        return "model"
    if ext in {".dtx", ".tga", ".png", ".dds", ".vtf"}:
        return "texture"
    if ext == ".wav":
        return "sound"
    if ext in {".fx", ".shd", ".mat"} or "shader" in text or "material" in text:
        return "shader"
    if ext in TEXT_EXTS or ext == ".bin":
        return "config"
    if ext in {".obj", ".smd"}:
        return "model"
    return "other"


def variant_keys(path_text: str) -> set[str]:
    value = normalized(path_text)
    return {key for key in KNOWN_VARIANTS if key in value}


def is_canonical_model(path: Path) -> bool:
    if path.suffix.casefold() != ".ltb":
        return False
    stem = path.stem.casefold()
    return re.search(r"(?:^|[_-])(bl|gr|woman)(?:$|[_-])", stem) is None


def light_summary(report: dict[str, Any]) -> dict[str, Any]:
    geometry = report.get("geometry", {})
    meshes = geometry.get("meshes") or []
    names = [str(mesh.get("name") or "") for mesh in meshes]
    hand_names = [name for name in names if re.search(r"hand|arm|sleeve|wrist|fvarm", name, re.I)]
    weapon_names = [name for name in names if name not in hand_names]
    bounds_min: list[float] | None = None
    bounds_max: list[float] | None = None
    for mesh in meshes:
        bounds = mesh.get("bounds") or {}
        mn = bounds.get("min")
        mx = bounds.get("max")
        if isinstance(mn, list) and len(mn) == 3 and isinstance(mx, list) and len(mx) == 3:
            bounds_min = [min(bounds_min[i], float(mn[i])) for i in range(3)] if bounds_min else [float(v) for v in mn]
            bounds_max = [max(bounds_max[i], float(mx[i])) for i in range(3)] if bounds_max else [float(v) for v in mx]
    return {
        "status": "available",
        "mesh_count": geometry.get("mesh_count"),
        "vertex_count": geometry.get("vertex_count"),
        "triangle_count": geometry.get("triangle_count"),
        "node_count": (report.get("skeleton") or {}).get("node_count"),
        "mesh_names": names[:40],
        "weapon_mesh_count": len(weapon_names),
        "obvious_arm_hand_groups": hand_names[:20],
        "bounds": {"min": bounds_min, "max": bounds_max},
        "parser_validation": report.get("validation", {}),
    }


def inspect_ltb(path: Path, temp_dir: Path) -> tuple[dict[str, Any], str | None]:
    if not CFREZ.is_file():
        return {"status": "not_available", "reason": "CFRezManager executable not found"}, "missing_cfrez"
    output = temp_dir / (path.stem + "_inspect.json")
    try:
        proc = subprocess.run(
            [str(CFREZ), "--inspect-ltb", "--input", str(path), "--output", str(output)],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=3,
        )
    except subprocess.TimeoutExpired:
        return {"status": "not_available", "reason": "CFRezManager timeout"}, "timeout"
    deadline = time.monotonic() + 1.5
    parsed: dict[str, Any] | None = None
    while time.monotonic() < deadline:
        if output.is_file() and output.stat().st_size > 0:
            try:
                parsed = json.loads(output.read_text(encoding="utf-8"))
                break
            except (OSError, json.JSONDecodeError):
                time.sleep(0.05)
        else:
            time.sleep(0.05)
    if parsed is None:
        reason = "inspect report not produced"
        if proc.stderr.strip():
            reason += ": " + proc.stderr.strip()[-240:]
        return {"status": "not_available", "reason": reason}, "no_report"
    return light_summary(parsed), None


def main() -> int:
    started = now()
    OUT.mkdir(parents=True, exist_ok=True)
    if not DATA.is_dir():
        return 2

    inventory: list[dict[str, Any]] = []
    for path in DATA.rglob("*"):
        if not path.is_file():
            continue
        try:
            stat = path.stat()
        except OSError:
            continue
        inventory.append({
            "path": rel(path),
            "filename": path.name,
            "extension": path.suffix.casefold(),
            "size_bytes": stat.st_size,
        })
    inventory.sort(key=lambda item: item["path"])
    inventory_counts = {
        "file_count": len(inventory),
        "total_bytes": sum(item["size_bytes"] for item in inventory),
        "by_extension": dict(sorted(Counter(item["extension"] for item in inventory).items())),
    }

    candidates: list[dict[str, Any]] = []
    keyword_counts: Counter[str] = Counter()
    for item in inventory:
        path_text = item["path"]
        hits = token_matches(path_text)
        if not hits:
            continue
        for hit in hits:
            keyword_counts[hit] += 1
        path = ROOT / Path(path_text)
        ctype = candidate_type(path)
        reasons = [f"keyword:{hit}" for hit in hits]
        if ctype == "model" and "playerview" in path_text.casefold():
            reasons.append("Models/PLAYERVIEW first-person model path")
        candidates.append({
            "candidate_id": "",
            "relative_path": path_text,
            "filename": path.name,
            "extension": path.suffix.casefold(),
            "size_bytes": item["size_bytes"],
            "sha256": None,
            "candidate_type": ctype,
            "source_class": source_class(Path(path_text)),
            "recall_reasons": reasons,
            "reference_edges": [],
            "light_summary": {"status": "not_applicable", "reason": "T01 light summary is only for selected LTB model candidates"},
            "score": 0,
            "identity_status": "CANDIDATE_ONLY",
            "identity_note": "prototype_only_not_finally_proven" if "bornbeast" in normalized(path_text) else None,
        })
    candidates.sort(key=lambda item: item["relative_path"])
    for index, candidate in enumerate(candidates, 1):
        candidate["candidate_id"] = f"P5T01-C{index:05d}"

    by_path = {candidate["relative_path"]: candidate for candidate in candidates}
    by_id = {candidate["candidate_id"]: candidate for candidate in candidates}
    by_variant: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for candidate in candidates:
        for key in variant_keys(candidate["relative_path"]):
            by_variant[key].append(candidate)

    # Hash only recalled candidates, as required by the Task Spec.
    hash_errors: list[str] = []
    print(f"[T01] hashing {len(candidates)} recalled candidates", flush=True)
    with ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(sha256, ROOT / Path(candidate["relative_path"])): candidate for candidate in candidates}
        for completed, future in enumerate(as_completed(futures), 1):
            candidate = futures[future]
            try:
                candidate["sha256"] = future.result()
            except OSError as exc:
                hash_errors.append(f"{candidate['relative_path']}: {exc}")
            if completed % 250 == 0 or completed == len(candidates):
                print(f"[T01] hashed {completed}/{len(candidates)}", flush=True)

    # Build a bounded text-reference index. Binary config/resource containers are recorded as unresolved.
    text_files = [item for item in inventory if item["extension"] in TEXT_EXTS and item["size_bytes"] <= TEXT_LIMIT]
    text_contents: list[tuple[dict[str, Any], str]] = []
    for item in text_files:
        try:
            raw = (ROOT / Path(item["path"])).read_bytes()
            text = raw.decode("utf-8", errors="ignore").casefold()
            text_contents.append((item, text))
        except OSError:
            continue
    model_candidates = [c for c in candidates if c["candidate_type"] == "model" and c["extension"] == ".ltb"]
    direct_config_refs: defaultdict[str, list[dict[str, Any]]] = defaultdict(list)
    for item, text in text_contents:
        for model in model_candidates:
            stem = Path(model["relative_path"]).stem.casefold()
            needles = {stem, stem.removeprefix("pv-")}
            matched = next((needle for needle in sorted(needles, key=len, reverse=True) if len(needle) >= 8 and needle in text), None)
            if matched:
                edge = {"relation": "text_config_reference", "source_path": item["path"], "evidence": f"literal:{matched}"}
                direct_config_refs[model["relative_path"]].append(edge)
                if len(model["reference_edges"]) < 20:
                    model["reference_edges"].append(edge)

    # Associate same-variant texture/shader/sound/config names without treating this as final identity proof.
    for candidate in candidates:
        keys = variant_keys(candidate["relative_path"])
        for key in sorted(keys):
            for related in sorted(by_variant[key], key=lambda item: item["relative_path"]):
                if related is candidate or len(candidate["reference_edges"]) >= 20:
                    continue
                relation = {
                    "relation": "same_variant_filename_or_directory_token",
                    "target_candidate_id": related["candidate_id"],
                    "evidence": f"normalized_variant:{key}",
                }
                candidate["reference_edges"].append(relation)

    parser_errors: list[str] = []
    inspected = 0
    canonical_models = [c for c in model_candidates if is_canonical_model(Path(c["relative_path"]))]
    print(f"[T01] inspecting {len(canonical_models)} canonical LTB candidates", flush=True)
    with tempfile.TemporaryDirectory(prefix="p5_t01_", dir=OUT) as temp_name:
        temp_dir = Path(temp_name)
        for candidate in canonical_models:
            summary, error = inspect_ltb(ROOT / Path(candidate["relative_path"]), temp_dir)
            candidate["light_summary"] = summary
            inspected += 1
            if error:
                parser_errors.append(f"{candidate['relative_path']}: {error}")
            if inspected % 50 == 0 or inspected == len(canonical_models):
                print(f"[T01] inspected {inspected}/{len(canonical_models)}", flush=True)
        for candidate in model_candidates:
            if candidate["light_summary"].get("status") == "not_applicable":
                candidate["light_summary"] = {"status": "not_available", "reason": "non-canonical _BL/_GR/_WOMAN presentation variant not inspected in bounded T01 pass"}

    def related_counts(candidate: dict[str, Any]) -> dict[str, int]:
        counts = Counter()
        for edge in candidate["reference_edges"]:
            target = by_path.get(edge.get("source_path", "")) or by_id.get(edge.get("target_candidate_id", ""))
            if target:
                counts[target["candidate_type"]] += 1
        return {
            "config": counts["config"],
            "texture": counts["texture"],
            "shader": counts["shader"],
            "sound": counts["sound"],
        }

    for candidate in candidates:
        counts = related_counts(candidate)
        candidate["related_counts"] = counts
        score = 0
        if direct_config_refs.get(candidate["relative_path"]):
            score += 100
        if candidate["candidate_type"] == "model" and "playerview" in candidate["relative_path"].casefold():
            score += 40
        if any(normalized(token) in normalized(candidate["relative_path"]) for token in ("M4A1", "M4A1-S", "M4A1S")):
            score += 25
        if counts["texture"] or counts["shader"]:
            score += 20
        if counts["config"]:
            score += 15
        if counts["sound"]:
            score += 10
        summary = candidate["light_summary"]
        if summary.get("status") == "available" and summary.get("weapon_mesh_count", 0) > 0:
            score += 10
        if not candidate["reference_edges"] and candidate["candidate_type"] != "model":
            score -= 40
        if summary.get("status") == "available" and summary.get("weapon_mesh_count") == 0:
            score -= 80
        if candidate["source_class"] != "raw_cf_asset":
            score -= 100
        candidate["score"] = score
        candidate["next_action"] = {
            "model": "P5-T02 geometry/parts comparison",
            "texture": "P5-T02 atlas/UV comparison",
            "config": "P5-T03 resource graph closure",
            "shader": "P5-T03 material graph closure",
            "sound": "P5-T03 same-variant association",
        }.get(candidate["candidate_type"], "P5-T02 candidate review")

    ordered = sorted(candidates, key=lambda c: (-int(c["score"]), 0 if c["candidate_type"] == "model" else 1, c["relative_path"]))
    for rank, candidate in enumerate(ordered, 1):
        candidate["rank"] = rank

    candidate_index = {
        "schema": "cf2.p5.t01.candidate-index.v1",
        "task_id": "P5-T01",
        "execution_status": "EXECUTION_PASS",
        "target_identity": "M4A1-雷神",
        "official_reference_url": "https://cf.qq.com/cp/a20250701wqbk/index.html",
        "reference_type": "OFFICIAL_CF_WEAPON_HANDBOOK_REFERENCE",
        "scan_roots": ["data/**"],
        "inventory_counts": inventory_counts,
        "keyword_hits": dict(keyword_counts),
        "model_candidates": {"total": len(model_candidates), "light_inspected": inspected, "parser_errors": len(parser_errors)},
        "candidates": ordered,
        "identity_boundary": "All entries are CANDIDATE_ONLY; T01 does not confirm final Leishen identity.",
    }

    matrix_path = OUT / "candidate_matrix.csv"
    matrix_fields = ["rank", "candidate_id", "relative_path", "candidate_type", "score", "sha256", "primary_recall_reason", "config_reference_count", "related_texture_count", "related_shader_count", "related_sound_count", "mesh_count", "triangle_count", "identity_status", "next_action"]
    with matrix_path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=matrix_fields)
        writer.writeheader()
        for candidate in ordered:
            summary = candidate["light_summary"]
            writer.writerow({
                "rank": candidate["rank"],
                "candidate_id": candidate["candidate_id"],
                "relative_path": candidate["relative_path"],
                "candidate_type": candidate["candidate_type"],
                "score": candidate["score"],
                "sha256": candidate["sha256"] or "",
                "primary_recall_reason": candidate["recall_reasons"][0] if candidate["recall_reasons"] else "",
                "config_reference_count": len(direct_config_refs.get(candidate["relative_path"], [])),
                "related_texture_count": candidate["related_counts"]["texture"],
                "related_shader_count": candidate["related_counts"]["shader"],
                "related_sound_count": candidate["related_counts"]["sound"],
                "mesh_count": summary.get("mesh_count", ""),
                "triangle_count": summary.get("triangle_count", ""),
                "identity_status": candidate["identity_status"],
                "next_action": candidate["next_action"],
            })

    index_path = OUT / "candidate_index.json"
    index_path.write_text(json.dumps(candidate_index, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    top = ordered[:30]
    excluded = [c for c in ordered if c["source_class"] != "raw_cf_asset" or (c["light_summary"].get("status") == "available" and c["light_summary"].get("weapon_mesh_count") == 0)]
    report_lines = [
        "# P5-T01 Scan Report — 官方身份锚点与本地候选召回",
        "",
        "- status: `EXECUTION_PASS`",
        "- task_id: `P5-T01`",
        "- target identity: `M4A1-雷神`",
        "- official reference: https://cf.qq.com/cp/a20250701wqbk/index.html",
        "- scan root: `data/**` (read-only)",
        f"- inventory: {inventory_counts['file_count']} files / {inventory_counts['total_bytes']} bytes",
        f"- recalled candidates: {len(candidates)}; LTB candidates: {len(model_candidates)}; canonical LTB inspected: {inspected}",
        "",
        "## Search and parser boundary",
        "",
        "Keywords were used for recall only: `M4`, `M4A1`, `M4A1-S`, `M4A1S`, `雷神`, `LEISHEN`, `LEI_SHEN`, `THOR`, `THUNDER`. Text configuration was searched with literal basename references. Binary `.BIN` resources were not decoded and are marked unresolved by their path/extension. The existing CFRezManager inspect route was used only for canonical LTB light summaries; no Blender, OBJ export, or Source/MIGI changes were performed.",
        "",
        "## Top 30 candidates (priority only, not identity proof)",
        "",
        "| Rank | Type | Score | Path | Light summary | Identity boundary |",
        "|---:|---|---:|---|---|---|",
    ]
    for candidate in top:
        summary = candidate["light_summary"]
        light = f"{summary.get('mesh_count', 'n/a')} meshes/{summary.get('triangle_count', 'n/a')} tris" if summary.get("status") == "available" else summary.get("reason", "n/a")
        report_lines.append(f"| {candidate['rank']} | {candidate['candidate_type']} | {candidate['score']} | `{candidate['relative_path']}` | {light} | `CANDIDATE_ONLY` |")
    report_lines += [
        "",
        "## Exclusions and limitations",
        "",
        f"- {len(excluded)} recalled entries are derived/unclassified local outputs or non-weapon/hand-only summaries; they remain recorded for exclusion traceability.",
        f"- {len(parser_errors)} LTB inspect attempts did not yield a usable report; these candidates remain `not_available` and are not silently promoted.",
        f"- {len(hash_errors)} candidate hashes failed; details are recorded in `execution.json`.",
        "- `data/**` was not changed and no raw LTB/DTX/TGA/WAV/BIN was copied into the repository outputs.",
        "- The existing Prototype-01 BornBeast paths are retained as comparison/negative-control candidates with `prototype_only_not_finally_proven`; they are not declared final Leishen.",
        "",
        "## Recommended next action",
        "",
        "Chat/Sol should select a small set of model/texture pairs from this matrix for P5-T02 geometry and atlas comparison. T01 does not enter T02 automatically.",
    ]
    report_path = OUT / "scan_report.md"
    report_path.write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    execution = {
        "schema": "cf2.p5.t01.execution.v1",
        "task_id": "P5-T01",
        "status": "EXECUTION_PASS",
        "git_head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True, check=True).stdout.strip(),
        "started_at": started,
        "finished_at": now(),
        "commands": [
            "python scripts/p5/p5_t01_scan.py",
            "CFRezManager.exe --inspect-ltb --input <data candidate> --output <temporary report>",
        ],
        "exit_codes": {"scan_script": 0, "ltb_inspect_failures": len(parser_errors)},
        "script": {"path": "scripts/p5/p5_t01_scan.py", "sha256": sha256(Path(__file__))},
        "scan_root": "data/**",
        "inventory": inventory_counts,
        "candidate_count": len(candidates),
        "ltb_candidate_count": len(model_candidates),
        "canonical_ltb_inspected": inspected,
        "errors": hash_errors + parser_errors[:50],
        "warnings": ["T01 is recall/summary only; no candidate is final identity.", "Binary resource containers remain unresolved."],
    }
    execution["output_hashes"] = {name: sha256(OUT / name) for name in ("candidate_index.json", "candidate_matrix.csv", "scan_report.md")}
    (OUT / "execution.json").write_text(json.dumps(execution, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": "EXECUTION_PASS", "candidates": len(candidates), "ltb_candidates": len(model_candidates), "inspected": inspected, "output": rel(OUT)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
