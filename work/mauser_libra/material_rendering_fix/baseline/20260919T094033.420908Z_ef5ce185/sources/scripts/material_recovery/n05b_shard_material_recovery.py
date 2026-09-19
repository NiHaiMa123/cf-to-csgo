"""Reproduce the N05-A review finding: RF017 payloads live in numbered parts.

Writes metadata, decoded diagnostic PNGs and parsed CFG only. No raw client
binary is copied, and no game or original data directory is modified.
"""
from __future__ import annotations

import configparser
import io
import json
import tempfile
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from PIL import Image
import n05a_decoder_provenance_audit as audit
from rez_verified_payload import read_verified_payload

OUT = audit.REPO / "work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n05b_shard_material_recovery"


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    index = audit.CF / "rez/rf017.rez"
    entries = audit.read_rez_index_mmap(index)
    targets = {s["logical_path"].upper(): s["id"] for s in audit.SAMPLES}
    targets.update({"NORMALMAP/M4A1_S_BORNBEAST_N.TGA": "bornbeast_normal_tga",
                    "SPECULARMAP/M4A1_S_BORNBEAST_S.TGA": "bornbeast_specular_tga"})
    counts = Counter(e["full_path"].upper() for e in entries)
    rows = []
    cfg = None
    for entry in entries:
        logical = entry["full_path"].upper()
        if logical not in targets:
            continue
        if counts[logical] != 1:
            raise ValueError(f"Ambiguous logical path: {logical}")
        data, row = read_verified_payload(index, entry)
        row["id"] = targets[logical]
        extension = Path(logical).suffix
        image = None
        if extension == ".DTX":
            row["header"] = audit.repo_dtx_try_read_header(data)
            row["structural_gate"] = audit.dtx_create_structural(data)
            decoded = audit.decode_repo_pixels(data)
            if not decoded.get("ok"):
                raise ValueError(f"DTX decode failed: {logical}")
            image = decoded["image"]
        elif extension == ".TGA":
            with Image.open(io.BytesIO(data)) as source:
                source.load()
                row["container"] = source.format
                image = source.copy()
            row["repair_applied"] = False
        elif extension == ".CFG":
            parser = configparser.ConfigParser()
            parser.optionxform = str
            parser.read_string(data.decode("ascii"))
            cfg = {section: dict(parser[section]) for section in parser.sections()}
            row["sections"] = cfg
        if image is not None:
            dest = OUT / f"{row['id']}.png"
            image.save(dest)
            row.update(preview=audit.rel(dest), image_size=list(image.size), image_mode=image.mode)
            if row["id"] == "bornbeast_pv_dtx":
                # Also exercise the existing compiled repo decoder on the
                # verified bytes; it does not need to understand REZ routing.
                with tempfile.TemporaryDirectory() as tmp:
                    src = Path(tmp) / "pv.dtx"
                    src.write_bytes(data)
                    tool_dest = OUT / "bornbeast_pv_cfrez.png"
                    tool = audit.cfrez_decode_image(src, tool_dest)
                tool.pop("cmd", None)  # avoid non-reproducible temporary paths
                if not tool.get("ok"):
                    raise RuntimeError(f"Repo DTX decoder failed: {tool}")
                with Image.open(tool_dest) as tool_image:
                    equal = image.size == tool_image.size and image.convert("RGBA").tobytes() == tool_image.convert("RGBA").tobytes()
                row["repo_decoder"] = {**tool, "exact_rgba_match": equal}
                if not equal:
                    raise ValueError("Python / CFRezManager PV pixels differ")
        rows.append(row)
    if len(rows) != len(targets):
        raise ValueError("Missing target input")
    # Re-run only the corrected control discovery, without overwriting N05-A.
    audit.PREV = OUT
    controls = audit.scan_local_control_dtx()
    old_previews = audit.OUT / "previews"
    with Image.open(old_previews / "bornbeast_qv_dtx_rez2_RF017_REZ_raw_python.png") as x, \
         Image.open(old_previews / "bornbeast_qv_dtx_rez2_RF017_REZ_raw_cfrez.png") as y:
        comparison = {"same_dimensions": x.size == y.size,
                      "exact_rgba_match": x.convert("RGBA").tobytes() == y.convert("RGBA").tobytes()}
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "reviewed_commit": "32d2ec2e72439be28c471139e6f2e5805ae73729",
        "result": "PV_DTX_AND_TEXT_CFG_RECOVERED_FROM_NUMBERED_PARTS",
        "p4_m01": "INCOMPLETE", "samples": rows,
        "corrected_loose_control_scan": controls, "n05a_qv_preview_comparison": comparison,
        "index_file_length": index.stat().st_size, "index_entry_count": len(entries),
        "ranges_outside_main_file_only": sum(e["data_offset"] + e["size"] > index.stat().st_size for e in entries),
        "warning": "Main-file-only bounds do not establish corruption: numbered-part ranges use the part's length.",
    }
    (OUT / "recovery.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "bornbeast_cfg.json").write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"result": report["result"], "md5_verified": len(rows), "out": str(OUT), "controls": controls}, ensure_ascii=False))


if __name__ == "__main__":
    main()
