"""P4-M01-N05-C — wire the MD5-verified REZ reader into official extract paths.

Repro:
  python scripts/material_recovery/n05c_verified_reader_integration.py
"""
from __future__ import annotations

import configparser
import hashlib
import io
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "cf_extract"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # noqa: E402
import extract_all  # noqa: E402
import n02e_r2_payload_hash as n02er2  # noqa: E402
import n05a_decoder_provenance_audit as audit  # noqa: E402
from rez_verified_payload import read_verified_payload  # noqa: E402

REPO = Path(_paths.project_dir())
DATA = Path(_paths.data_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05c_verified_reader_integration"
)
N05B = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05b_shard_material_recovery/recovery.json"
)
STAGING = DATA / "n05c_verified_extract"
CFREZ_EXE = REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
DOTNET = Path(r"C:\Program Files\dotnet\dotnet.exe")
INDEX = CF / "rez" / "rf017.rez"

DEPRECATED_ENTRIES = [
    {
        "entry": "n02e_r2_payload_hash.read_payload_bytes(path, offset, size) without entry",
        "reason": "Unauthenticated main-file slice; no numbered-part routing; must not claim verified recovery",
    },
    {
        "entry": "scripts/material_recovery/n03a_bornbeast_consumer.py and n03b–n03g payload reads",
        "reason": "Still call the unauthenticated n02e helper; historical reports were not rewritten",
    },
    {
        "entry": "scripts/material_recovery/n02d_rez_asset_lookup.py",
        "reason": "Basename-oriented historical index helper; not a payload resolver",
    },
    {
        "entry": "pre-N05-C CFRezManager ArchiveFile.DataOffset seeks",
        "reason": "Replaced by RezVerifiedPayloadReader; leftover seeks are writer/cache metadata only",
    },
    {
        "entry": "data/rf017 and other historical extract trees",
        "reason": "Old main-file extracts; this round writes only data/n05c_verified_extract",
    },
]


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


def load_n05b_targets() -> list[dict]:
    blob = json.loads(N05B.read_text(encoding="utf-8"))
    rows = []
    for sample in blob["samples"]:
        rows.append({
            "id": sample["id"],
            "logical_path": sample["logical_path"],
            "sha256": sample["sha256"],
            "directory_md5": sample["directory_md5"],
            "routing": sample["routing"],
            "payload_file": sample["payload_file"],
            "size": sample["size"],
            "image_size": sample.get("image_size"),
            "sections": sample.get("sections"),
        })
    if len(rows) != 9:
        raise ValueError(f"N05-B freeze expected 9 samples, found {len(rows)}")
    return rows


def run_checked(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"command failed {cmd}: {proc.stderr or proc.stdout}")
    return proc


def ensure_cfrez_built() -> Path:
    run_checked([str(DOTNET), "build", str(REPO / "CFRezManager" / "CFRezManager.csproj"), "-c", "Debug"])
    if not CFREZ_EXE.is_file():
        raise FileNotFoundError(CFREZ_EXE)
    return CFREZ_EXE


def parse_hash_output(text: str) -> dict[str, str]:
    parsed = {}
    for line in text.splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            parsed[key.strip()] = value.strip()
    return parsed


def diagnose(logical_path: str, data: bytes, dest_stem: Path) -> dict:
    suffix = Path(logical_path).suffix.upper()
    info: dict = {"bytes": len(data)}
    if suffix == ".DTX":
        header = audit.repo_dtx_try_read_header(data)
        decoded = audit.decode_repo_pixels(data)
        if not decoded.get("ok"):
            raise ValueError(f"DTX decode failed: {logical_path}")
        image = decoded["image"]
        png = dest_stem.with_suffix(".png")
        image.save(png)
        info.update(header=header, image_size=list(image.size), preview=rel(png))
    elif suffix == ".TGA":
        with Image.open(io.BytesIO(data)) as source:
            source.load()
            image = source.copy()
        png = dest_stem.with_suffix(".png")
        image.save(png)
        info.update(container=image.format, image_size=list(image.size), preview=rel(png), repair_applied=False)
    elif suffix == ".CFG":
        parser = configparser.ConfigParser()
        parser.optionxform = str
        parser.read_string(data.decode("ascii"))
        sections = {section: dict(parser[section]) for section in parser.sections()}
        info.update(sections=sections, section_names=list(parser.sections()))
    return info


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    targets = load_n05b_targets()
    index = INDEX
    if not index.is_file():
        raise FileNotFoundError(index)
    entries = {entry["full_path"].upper(): entry for entry in audit.read_rez_index_mmap(index)}
    logicals = [row["logical_path"] for row in targets]
    exe = ensure_cfrez_built()

    python_staging = STAGING / "extract_all" / "rez" / "rf017"
    if python_staging.exists():
        for leftover in python_staging.rglob("*"):
            if leftover.is_file():
                leftover.unlink()
    python_written = extract_all.extract_archive(str(index), str(python_staging), logicals)
    python_by_path = {}
    for row in python_written:
        matches = [path for path in logicals if extract_all.logical_path_matches(row["logical_path"], path)]
        if len(matches) != 1:
            raise ValueError(f"extract_all row {row['logical_path']} matched {matches}")
        python_by_path[matches[0].upper()] = row

    cfrez_staging = STAGING / "cfrez_extract_file"
    cfrez_rows = []
    hash_rows = []
    audit_rows = []
    diagnostics = []
    compared = []

    for target in targets:
        logical = target["logical_path"]
        entry = entries.get(logical.upper())
        if entry is None:
            raise ValueError(f"Missing index entry: {logical}")
        expected = target["sha256"]

        py_row = python_by_path[logical.upper()]
        py_path = Path(py_row["destination"])
        py_sha = sha256_file(py_path)

        dest = cfrez_staging / logical.replace("/", os.sep)
        dest.parent.mkdir(parents=True, exist_ok=True)
        extract_proc = run_checked([str(exe), "--extract-file", str(index), logical, str(dest)])
        cfrez_sha = sha256_file(dest)
        cfrez_rows.append({
            "logical_path": logical,
            "destination": str(dest),
            "sha256": cfrez_sha,
            "stdout": extract_proc.stdout.strip(),
        })

        hash_proc = run_checked([str(exe), "--read-hash", str(index), logical])
        parsed = parse_hash_output(hash_proc.stdout)
        hash_rows.append(parsed)

        audit_bytes = n02er2.read_payload_bytes(
            str(index), entry["data_offset"], entry["size"], entry
        )
        audit_sha = sha256_bytes(audit_bytes)
        verified_bytes, provenance = read_verified_payload(index, entry)
        audit_rows.append({
            "logical_path": logical,
            "n02e_sha256": audit_sha,
            "resolver_sha256": provenance["sha256"],
            "payload_file": provenance["payload_file"],
            "routing": provenance["routing"],
        })

        diag = diagnose(logical, verified_bytes, OUT / target["id"])
        diagnostics.append({"id": target["id"], "logical_path": logical, **diag})

        compared.append({
            "id": target["id"],
            "logical_path": logical,
            "expected_sha256": expected,
            "extract_all_sha256": py_sha,
            "cfrez_extract_file_sha256": cfrez_sha,
            "cfrez_read_hash_sha256": parsed.get("sha256"),
            "n02e_verified_sha256": audit_sha,
            "match": expected == py_sha == cfrez_sha == parsed.get("sha256") == audit_sha,
            "routing": provenance["routing"],
            "payload_file": provenance["payload_file"],
        })

    pv = next(row for row in diagnostics if row["id"] == "bornbeast_pv_dtx")
    cfg = next(row for row in diagnostics if row["id"] == "bornbeast_cfg")
    failures = [row["logical_path"] for row in compared if not row["match"]]
    result = "VERIFIED_READER_INTEGRATED" if not failures else "VERIFIED_READER_PARTIAL"
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P4-M01-N05-C",
        "result": result,
        "p4_m01": "INCOMPLETE",
        "index_archive": str(index),
        "n05b_recovery": rel(N05B),
        "staging": str(STAGING),
        "official_entries_exercised": [
            "scripts/cf_extract/extract_all.py extract_archive",
            "CFRezManager --extract-file (RezArchiveReader.ExtractFile)",
            "CFRezManager --read-hash (RezVerifiedPayloadReader.Read)",
            "n02e_r2_payload_hash.read_payload_bytes(..., entry=entry) used by N05-A",
        ],
        "not_used_as_proof": ["scripts/material_recovery/n05b_shard_material_recovery.py"],
        "sha256_comparison": compared,
        "python_extract": python_written,
        "cfrez_extract_file": cfrez_rows,
        "cfrez_read_hash": hash_rows,
        "n02e_audit_reads": audit_rows,
        "diagnostics": diagnostics,
        "pv_dtx": {"image_size": pv.get("image_size"), "header": pv.get("header")},
        "cfg_sections": cfg.get("section_names"),
        "failures": failures,
        "deprecated_entries": DEPRECATED_ENTRIES,
        "cache_verification": "CFRezManager.Tests directory cold/hot plus thumbnail key change after numbered-part mutation",
        "commands": {
            "python_tests": "python -B -m unittest discover -s tests -p test_rez_verified_payload.py -v; python -B -m unittest discover -s tests -p test_extract_all_verified.py -v",
            "csharp_tests": "dotnet test CFRezManager.Tests/CFRezManager.Tests.csproj -c Debug",
            "this_script": "python scripts/material_recovery/n05c_verified_reader_integration.py",
        },
    }
    (OUT / "integration.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report, targets)
    print(json.dumps({"result": result, "failures": failures, "out": str(OUT)}, ensure_ascii=False))
    if failures:
        raise SystemExit(1)
    return 0


def write_markdown(report: dict, targets: list[dict]) -> None:
    lines = [
        "# N05-C — Verified REZ reader integration",
        "",
        f"Result: **{report['result']}**. P4-M01 remains **INCOMPLETE**.",
        "",
        "Official extract/preview entries now share `rez_verified_payload.py` / `RezVerifiedPayloadReader`. Directory `time` is only a candidate numbered-part hint; bounds, length and MD5 are checked per candidate. Missing parts, truncated parts, wrong hashes and two matching candidates error. Archives without a complete directory MD5 cannot claim verification or guess a part.",
        "",
        "## Official entries",
        "",
    ]
    for entry in report["official_entries_exercised"]:
        lines.append(f"- `{entry}`")
    lines += [
        "",
        "N05-B helper `n05b_shard_material_recovery.py` was **not** used as proof that the official entries work.",
        "",
        "## 9/9 SHA256 vs N05-B freeze",
        "",
        "| Target | extract_all | CFRez extract-file | CFRez read-hash | N05-A n02e | Match |",
        "|---|---|---|---|---|---|",
    ]
    for row in report["sha256_comparison"]:
        mark = "yes" if row["match"] else "NO"
        lines.append(
            f"| `{row['logical_path']}` | `{row['extract_all_sha256'][:12]}…` | `{row['cfrez_extract_file_sha256'][:12]}…` | `{row['cfrez_read_hash_sha256'][:12]}…` | `{row['n02e_verified_sha256'][:12]}…` | {mark} |"
        )
    pv = report["pv_dtx"]
    lines += [
        "",
        f"BornBeast PV DTX decodes as {pv['image_size'][0]}×{pv['image_size'][1]}. CFG sections: {', '.join(report['cfg_sections'] or [])}. TGA files parse without inserted-header repair.",
        "",
        "## Cache",
        "",
        report["cache_verification"] + ". Directory cache is v2; thumbnail cache is v2 and includes numbered-part path/length/mtime so changing a part cannot reuse the old image.",
        "",
        "## Staging",
        "",
        f"Raw bytes for this round: `{report['staging']}` (local `data/**`, not committed). Diagnostic PNGs and this report: `{rel(OUT)}`. Historical `data/rf017` was not overwritten.",
        "",
        "## Still deprecated",
        "",
    ]
    for row in report["deprecated_entries"]:
        lines.append(f"- `{row['entry']}` — {row['reason']}")
    lines += [
        "",
        "## Reproduce",
        "",
        "```powershell",
        report["commands"]["python_tests"],
        report["commands"]["csharp_tests"],
        report["commands"]["this_script"],
        "```",
        "",
        "P4 frozen build, deploy and shader tuning were not touched.",
        "",
    ]
    (OUT / "report.md").write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
