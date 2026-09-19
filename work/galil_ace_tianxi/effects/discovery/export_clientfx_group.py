# -*- coding: utf-8 -*-
"""E1a — reproducible per-group FXF export (plan.md §7 task 1).

Reads ClientFX/CLIENTFX.FXF from a hash-verified REZ payload, LZMA-decodes
it in memory (decoded blob is NOT persisted), locates one named group, and
parses every FX node with every property using the bin30 layout mirrored
from upstream clientfx_tool bin30_codec.cpp:

  file    : u32 group_count
  group   : u32 fx_count, char[128] name, u32 phase, fx[fx_count]
  fx      : char[128] fx_name, u32 fx_id, u32 linked, u32 link_id,
            char[32] link_node, f32 start, f32 end, u32 repeat,
            u32 track_id, f32 min_scale, f32 max_scale, u32 prop_count
  prop    : u8 name_len + name, u32 type_id, value by type:
            0/3/7 -> char[128] (STRING/COMBO/PATH)
            1 -> i32, 2 -> f32, 4 -> 3*f32, 5 -> 4*f32,
            6 -> f32 t + u8 r,g,b,a (CLRKEY)

Boundary checks: file group count, group name alignment, parsed node count
== header fx_count, byte-exact end offset, and the following group's
fx_count + name. Property order is preserved verbatim (duplicate names
kept) since curve data may repeat keys.

Output: effects/discovery/clientfx_group_<name>.json
"""
from __future__ import annotations

import hashlib
import json
import lzma
import struct
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO / "scripts"))
sys.path.insert(0, str(_REPO / "scripts" / "cf_extract"))
sys.path.insert(0, str(_REPO / "scripts" / "material_recovery"))

import _paths  # noqa: E402
import extract_all  # noqa: E402
from rez_verified_payload import is_complete_directory_md5, read_verified_payload  # noqa: E402

CF = Path(_paths.cf_dir())
OUT = Path(__file__).resolve().parent
GROUP_NAME = "pv_galilace_phantombeast_idle"
FXF_REZ_PATH = "ClientFX/CLIENTFX.FXF"
FCF_REZ_PATH = "ClientFX/CLIENTFX.FCF"

TYPE_KIND = {0: "STRING", 1: "INTEGER", 2: "FLOAT", 3: "COMBO", 4: "VECTOR", 5: "VECTOR4", 6: "CLRKEY", 7: "PATH"}


class Reader:
    def __init__(self, buf: bytes):
        self.buf = buf
        self.pos = 0

    def take(self, n: int) -> bytes:
        if self.pos + n > len(self.buf):
            raise ValueError(f"EOF at {self.pos}+{n}")
        b = self.buf[self.pos:self.pos + n]
        self.pos += n
        return b

    def u32(self) -> int:
        return struct.unpack_from("<I", self.take(4))[0]

    def i32(self) -> int:
        return struct.unpack_from("<i", self.take(4))[0]

    def f32(self) -> float:
        return struct.unpack_from("<f", self.take(4))[0]

    def u8(self) -> int:
        return self.take(1)[0]

    def fixed(self, n: int) -> str:
        raw = self.take(n)
        z = raw.find(b"\0")
        if z >= 0:
            raw = raw[:z]
        return raw.decode("ascii", errors="replace")


def parse_prop(r: Reader) -> dict:
    start = r.pos
    nlen = r.u8()
    name = r.take(nlen).decode("ascii", errors="replace")
    type_id = r.u32()
    kind = TYPE_KIND.get(type_id)
    if kind is None:
        raise ValueError(f"unknown prop type_id={type_id} for {name!r} at {start}")
    if type_id in (0, 3, 7):
        value = r.fixed(128)
    elif type_id == 1:
        value = r.i32()
    elif type_id == 2:
        value = r.f32()
    elif type_id == 4:
        value = [r.f32(), r.f32(), r.f32()]
    elif type_id == 5:
        value = [r.f32(), r.f32(), r.f32(), r.f32()]
    elif type_id == 6:
        t = r.f32()
        rgba = list(r.take(4))
        value = {"t": t, "rgba": rgba, "rgba01": [c / 255.0 for c in rgba]}
    return {"name": name, "type_id": type_id, "kind": kind, "value": value,
            "offset": start, "end_offset": r.pos}


def parse_fx(r: Reader) -> dict:
    start = r.pos
    fx = {
        "offset": start,
        "fx_name": r.fixed(128),
        "fx_id": r.u32(),
        "linked": r.u32(),
        "link_id": r.u32(),
        "link_node": r.fixed(32),
        "start_time": r.f32(),
        "end_time": r.f32(),
        "repeat": r.u32(),
        "track_id": r.u32(),
        "min_scale": r.f32(),
        "max_scale": r.f32(),
    }
    prop_count = r.u32()
    if prop_count > 512:
        raise ValueError(f"implausible prop_count={prop_count} at {r.pos - 4}")
    fx["property_count"] = prop_count
    fx["properties"] = [parse_prop(r) for _ in range(prop_count)]
    fx["end_offset"] = r.pos
    return fx


def find_group_offsets(buf: bytes, name: str) -> list[int]:
    """Candidate group-record starts: name bytes sitting in a fixed 128 field."""
    needle = name.encode("ascii") + b"\0"
    hits = []
    pos = 0
    while True:
        i = buf.find(needle, pos)
        if i < 0:
            break
        rec = i - 4  # u32 fx_count precedes char[128] name
        if rec >= 0:
            fx_count = struct.unpack_from("<I", buf, rec)[0]
            if 0 < fx_count <= 4096 and i + 128 <= len(buf):
                # name must be exactly the string + NUL padding in 128B
                field = buf[i:i + 128]
                if field.startswith(name.encode()) and field[len(name):].strip(b"\0") == b"":
                    hits.append(rec)
        pos = i + 1
    return hits


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # --- locate + verify FXF/FCF payloads in REZ indexes ---
    wanted = {FXF_REZ_PATH.upper(): None, FCF_REZ_PATH.upper(): None}
    for index_path in extract_all.discover_index_archives(str(CF)):
        try:
            entries = extract_all.read_index_entries(index_path)
        except Exception:
            continue
        for e in entries:
            k = e["full_path"].replace("\\", "/").upper()
            if k in wanted and is_complete_directory_md5(e.get("md5")):
                wanted[k] = (index_path, e)
    missing = [k for k, v in wanted.items() if v is None]
    if missing:
        raise SystemExit(f"missing index entries: {missing}")

    files_meta = []
    fxf_index, fxf_entry = wanted[FXF_REZ_PATH.upper()]
    fcf_index, fcf_entry = wanted[FCF_REZ_PATH.upper()]
    for index_path, e in ((fxf_index, fxf_entry), (fcf_index, fcf_entry)):
        data, prov = read_verified_payload(index_path, e)
        files_meta.append({
            "index": prov["index_archive"], "entry": prov["logical_path"],
            "stored_bytes": prov["size"], "md5": prov["directory_md5"],
            "md5_verified": True, "sha256": prov["sha256"],
            "payload_file": prov["payload_file"],
        })
        if e is fxf_entry:
            fxf_raw = data
        else:
            fcf_raw = data

    fxf = lzma.decompress(fxf_raw, format=lzma.FORMAT_ALONE)
    fcf = lzma.decompress(fcf_raw, format=lzma.FORMAT_ALONE)
    files_meta[0]["decoded_bytes"] = len(fxf)
    files_meta[1]["decoded_bytes"] = len(fcf)
    files_meta[0]["decoded_sha256"] = hashlib.sha256(fxf).hexdigest()
    files_meta[1]["decoded_sha256"] = hashlib.sha256(fcf).hexdigest()
    print(f"[e1a] fxf decoded={len(fxf)} fcf decoded={len(fcf)}")

    r = Reader(fxf)
    group_count = r.u32()
    print(f"[e1a] declared groups={group_count}")

    hits = find_group_offsets(fxf, GROUP_NAME)
    print(f"[e1a] name-field candidates for {GROUP_NAME}: {hits}")

    group = None
    for rec in hits:
        r.pos = rec
        fx_count = r.u32()
        gname = r.fixed(128)
        phase = r.u32()
        try:
            nodes = [parse_fx(r) for _ in range(fx_count)]
        except ValueError as exc:
            print(f"  candidate @{rec}: parse failed: {exc}")
            continue
        end = r.pos
        nxt_count = r.u32()
        nxt_name = r.fixed(128)
        nxt_phase = r.u32()
        group = {
            "name": gname, "phase_raw": phase, "offset": rec, "end_offset": end,
            "declared_fx_count": fx_count, "parsed_fx_count": len(nodes),
            "next_group": {"fx_count": nxt_count, "name": nxt_name, "phase_raw": nxt_phase},
            "nodes": nodes,
            "byte_sha256": hashlib.sha256(fxf[rec:end]).hexdigest(),
        }
        print(f"  candidate @{rec}: parsed {len(nodes)} nodes, next='{nxt_name}' ({nxt_count})")
        break
    if group is None:
        raise SystemExit("no parseable group found")

    # --- summaries ---
    types: dict[str, int] = {}
    attach: dict[str, int] = {}
    refs = set()
    dup_props = []
    for n in group["nodes"]:
        base = n["fx_name"].split(";")[0].strip() or n["fx_name"]
        types[base] = types.get(base, 0) + 1
        seen = {}
        for p in n["properties"]:
            seen[p["name"]] = seen.get(p["name"], 0) + 1
            if p["name"] == "AttachName":
                attach[str(p["value"])] = attach.get(str(p["value"]), 0) + 1
            if p["type_id"] == 7 and isinstance(p["value"], str) and "|" in p["value"]:
                refs.add(p["value"])
        dups = {k: v for k, v in seen.items() if v > 1}
        if dups:
            dup_props.append({"fx_name": n["fx_name"], "dups": dups})

    doc = {
        "date": datetime.now(timezone.utc).date().isoformat(),
        "method": "MD5-verified REZ read + LZMA decode (in-memory) + full bin30 group parse; decoded FXF not persisted",
        "layout_source": "https://github.com/lokea2/clientfx_tool/blob/master/ConsoleApplication10/bin30_codec.cpp",
        "files": files_meta,
        "fxf": {
            "declared_groups": group_count,
            "group": GROUP_NAME,
            "group_record": group,
            "type_histogram": types,
            "attach_names": sorted(attach),
            "attach_name_counts": attach,
            "resource_refs": sorted(refs),
            "duplicate_property_names": dup_props,
            "boundary_ok": group["parsed_fx_count"] == group["declared_fx_count"]
                             and group["next_group"]["name"] != "",
        },
    }
    out_path = OUT / f"clientfx_group_{GROUP_NAME}.json"
    out_path.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[e1a] wrote {out_path} nodes={len(group['nodes'])} types={types}")
    print(f"[e1a] attach_names={sorted(attach)}")
    print(f"[e1a] resource_refs={len(refs)} dup_props={len(dup_props)} boundary_ok={doc['fxf']['boundary_ok']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
