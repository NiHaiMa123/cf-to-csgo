"""Generic CF -> Source material intermediate representation (Material IR).

The IR is the single auditable record of what we know about a CF material:
raw CFG sections, texture channel semantics, sampling semantics, and every
claim tagged OBSERVED / INFERRED / APPROXIMATED / UNKNOWN.

Rules (plan.md v2):
- No weapon names, paths, thresholds, or channel assumptions live here.
- A filename never implies semantics ("SpecularMap" is not assumed to be a
  Source specular mask); semantics are recorded with an explicit status.
- B1 parses CFG completely; conversion to target-engine parameters happens
  only in later translators, never inside this module.
"""
from __future__ import annotations

import configparser
import json
from pathlib import Path

SCHEMA = "cf-material-ir.v1"

STATUS_OBSERVED = "OBSERVED"
STATUS_INFERRED = "INFERRED"
STATUS_APPROXIMATED = "APPROXIMATED"
STATUS_UNKNOWN = "UNKNOWN"
_STATUSES = {
    STATUS_OBSERVED,
    STATUS_INFERRED,
    STATUS_APPROXIMATED,
    STATUS_UNKNOWN,
}

CONFIDENCE_HIGH = "high"
CONFIDENCE_MEDIUM = "medium"
CONFIDENCE_LOW = "low"


def parse_cfg_full(path: Path | str) -> dict:
    """Parse every CFG section without converting semantics.

    Returns {section: {key: {"raw": str, "value": float|str}}} so callers can
    keep the literal text and a best-effort numeric coercion side by side.
    """
    parser = configparser.ConfigParser(strict=False, interpolation=None)
    parser.optionxform = str
    parser.read_string(Path(path).read_text(encoding="utf-8-sig", errors="replace"))
    sections: dict = {}
    for section in parser.sections():
        entries: dict = {}
        for key, raw in parser.items(section):
            raw = raw.strip()
            try:
                value: float | str = float(raw)
            except ValueError:
                value = raw
            entries[key] = {"raw": raw, "value": value}
        sections[section] = entries
    return sections


def new_ir(material_id: str, shader_family: str = "unclassified") -> dict:
    return {
        "schema": SCHEMA,
        "material_id": material_id,
        "shader_family": shader_family,
        "source_assets": {},
        "cfg": {"textures": {}, "techniques": {}, "properties": {}, "extra_sections": {}},
        "channel_semantics": {},
        "sampling_semantics": {},
        "observations": {},
        "inferences": {},
        "approximations": {},
        "unknowns": {},
        "evidence": {},
        "confidence": {},
    }


def _put(ir: dict, bucket: str, key: str, entry: dict) -> None:
    ir[bucket][key] = entry


def mark_observed(ir: dict, key: str, value, evidence: str | None = None,
                  confidence: str = CONFIDENCE_HIGH) -> None:
    """Record a directly verified fact (measurement, decoded field, dump)."""
    _put(ir, "observations", key, {
        "status": STATUS_OBSERVED,
        "value": value,
        "evidence": evidence,
        "confidence": confidence,
    })


def mark_inferred(ir: dict, key: str, value, basis: str | None = None,
                  confidence: str = CONFIDENCE_MEDIUM) -> None:
    """Record a reasoned conclusion that is not directly proven."""
    _put(ir, "inferences", key, {
        "status": STATUS_INFERRED,
        "value": value,
        "basis": basis,
        "confidence": confidence,
    })


def mark_approximated(ir: dict, key: str, value, basis: str | None = None,
                      confidence: str = CONFIDENCE_MEDIUM) -> None:
    """Record a deliberately simplified stand-in for the real behaviour."""
    _put(ir, "approximations", key, {
        "status": STATUS_APPROXIMATED,
        "value": value,
        "basis": basis,
        "confidence": confidence,
    })


def mark_unknown(ir: dict, key: str, reason: str) -> None:
    """Record something we do not know. Never silently fill in values."""
    _put(ir, "unknowns", key, {
        "status": STATUS_UNKNOWN,
        "reason": reason,
    })


def attach_cfg(ir: dict, cfg_path: Path | str, sha256: str | None = None) -> None:
    """B1: store the complete parsed CFG inside the IR, unconverted."""
    sections = parse_cfg_full(cfg_path)
    known = {"textures": "textures", "techniques": "techniques", "properties": "properties"}
    ir["cfg"]["path"] = str(cfg_path)
    if sha256:
        ir["cfg"]["sha256"] = sha256
    for section, entries in sections.items():
        bucket = known.get(section.lower(), "extra_sections")
        ir["cfg"][bucket][section] = entries
    # flattened numeric view for downstream readers
    ir["cfg"]["flat"] = {
        key: entry["value"]
        for section in sections.values()
        for key, entry in section.items()
    }


def attach_source_asset(ir: dict, role: str, manifest_entry: dict) -> None:
    ir["source_assets"][role] = manifest_entry


def add_evidence(ir: dict, name: str, path: str, note: str | None = None) -> None:
    ir["evidence"][name] = {"path": path, "note": note}


def validate_ir(ir: dict) -> list[str]:
    """Return a list of schema problems; empty means OK."""
    problems: list[str] = []
    if ir.get("schema") != SCHEMA:
        problems.append(f"schema != {SCHEMA}")
    for key in ("material_id", "shader_family", "source_assets", "cfg",
                "channel_semantics", "sampling_semantics", "observations",
                "inferences", "approximations", "unknowns", "evidence",
                "confidence"):
        if key not in ir:
            problems.append(f"missing key: {key}")
    for bucket in ("observations", "inferences", "approximations", "unknowns"):
        for name, entry in ir.get(bucket, {}).items():
            if entry.get("status") not in _STATUSES:
                problems.append(f"{bucket}.{name}: bad status {entry.get('status')!r}")
    return problems


def save_ir(ir: dict, path: Path | str) -> None:
    problems = validate_ir(ir)
    if problems:
        raise ValueError(f"IR schema problems: {problems}")
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(ir, indent=1, ensure_ascii=False), encoding="utf-8")


def load_ir(path: Path | str) -> dict:
    ir = json.loads(Path(path).read_text(encoding="utf-8"))
    problems = validate_ir(ir)
    if problems:
        raise ValueError(f"IR schema problems in {path}: {problems}")
    return ir
