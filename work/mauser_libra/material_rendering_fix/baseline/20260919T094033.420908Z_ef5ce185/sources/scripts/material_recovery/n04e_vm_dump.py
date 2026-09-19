#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-N04-E — crossfirebase.dll static + optional in-memory module dump."""
from __future__ import annotations

import ctypes
import hashlib
import json
import math
import os
import struct
import sys
from collections import Counter
from ctypes import wintypes
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # type: ignore  # noqa: E402
import n04b_pe_xref as n04b  # type: ignore  # noqa: E402

REPO = Path(_paths.project_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n04e_vm_dump"
)
DUMP_DIR = OUT / "dumps"

TARGETS = [
    "x64/crossfirebase.dll",
    "x64/crossfire_x64base.dll",
]
DUMP_NAMES = (
    "crossfirebase.dll",
    "crossfireBase.dll",
    "crossfire.exe",
    "CShell_x64.dll",
    "crossfire_x64.exe",
)
PROC_HINTS = ("crossfire", "cshell")
TOKENS = [
    "WeaponShader",
    "AlphaMap",
    "NormalMap",
    "SpecularMap",
    "playerviewmesh",
    "PlayerViewMesh",
    ".CFG",
    "%s.CFG",
    "MODELTEXTURES",
]
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_VM_READ = 0x0010
PROCESS_QUERY_LIMITED_INFORMATION = 0x1000


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def entropy(data: bytes) -> float:
    if not data:
        return 0.0
    counts = Counter(data)
    n = len(data)
    return round(-sum((c / n) * math.log2(c / n) for c in counts.values()), 4)


def extract_ascii(data: bytes, min_len: int = 6) -> list[str]:
    out: list[str] = []
    i = 0
    n = len(data)
    while i < n:
        if 32 <= data[i] < 127:
            j = i + 1
            while j < n and 32 <= data[j] < 127:
                j += 1
            if j - i >= min_len:
                out.append(data[i:j].decode("ascii"))
            i = j
        else:
            i += 1
    return out


def token_hits(strings: list[str]) -> list[dict]:
    hits = []
    for s in strings:
        sl = s.lower()
        matched = [t for t in TOKENS if t.lower() in sl]
        if matched:
            hits.append({"text": s[:240], "tokens": matched, "is_format": ("%s" in s)})
    return hits[:80]


def scan_pe(rel: str) -> dict:
    path = CF / rel.replace("/", os.sep)
    rec = {"relative": rel, "present": path.exists()}
    if not path.exists():
        return rec
    data = path.read_bytes()
    rec["size_bytes"] = len(data)
    rec["sha256"] = hashlib.sha256(data).hexdigest()
    rec["head16_hex"] = data[:16].hex()
    pe = n04b.parse_pe(data)
    rec["image_base"] = pe["image_base"]
    rec["machine"] = pe["machine"]
    sections = []
    all_hits: list[dict] = []
    for s in pe["sections"]:
        blob = data[s["raw_ptr"] : s["raw_ptr"] + s["raw_size"]]
        ent = entropy(blob[: min(len(blob), 256 * 1024)])
        strings = extract_ascii(blob) if ent < 7.2 else extract_ascii(blob[: min(len(blob), 2 * 1024 * 1024)])
        hits = token_hits(strings)
        all_hits.extend({"section": s["name"], **h} for h in hits)
        sections.append(
            {
                "name": s["name"],
                "va": s["va"],
                "vsize": s["vsize"],
                "raw_size": s["raw_size"],
                "executable": s["executable"],
                "entropy": ent,
                "ascii_strings": len(strings),
                "token_hits": len(hits),
            }
        )
    rec["sections"] = sections
    rec["token_hits"] = all_hits
    rec["has_tvm"] = any("tvm" in s["name"].lower() for s in pe["sections"])
    # imports
    pe_off = struct.unpack_from("<I", data, 60)[0]
    opt = pe_off + 24
    magic = struct.unpack_from("<H", data, opt)[0]
    dd = opt + (112 if magic == 0x20B else 96)
    imports = []
    if dd + 16 <= len(data):
        imp_rva = struct.unpack_from("<I", data, dd + 8)[0]
        off = n04b.rva_to_off(pe["sections"], imp_rva) if imp_rva else None
        while off is not None and off + 20 <= len(data) and len(imports) < 30:
            lookup, _, _, name_rva, first = struct.unpack_from("<IIIII", data, off)
            if lookup == 0 and name_rva == 0:
                break
            noff = n04b.rva_to_off(pe["sections"], name_rva)
            if noff:
                end = data.find(b"\x00", noff, noff + 80)
                if end > noff:
                    imports.append(data[noff:end].decode("ascii", errors="replace"))
            off += 20
    rec["imports"] = imports
    rec["entry_rva"] = struct.unpack_from("<I", data, opt + 16)[0]
    return rec


def list_cf_pids() -> list[dict]:
    found = []
    k32 = ctypes.windll.kernel32
    k32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    k32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.c_void_p]
    TH32CS_SNAPPROCESS = 0x2
    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [
            ("dwSize", wintypes.DWORD),
            ("cntUsage", wintypes.DWORD),
            ("th32ProcessID", wintypes.DWORD),
            ("th32DefaultHeapID", ctypes.POINTER(ctypes.c_ulong)),
            ("th32ModuleID", wintypes.DWORD),
            ("cntThreads", wintypes.DWORD),
            ("th32ParentProcessID", wintypes.DWORD),
            ("pcPriClassBase", ctypes.c_long),
            ("dwFlags", wintypes.DWORD),
            ("szExeFile", wintypes.WCHAR * 260),
        ]
    snap = k32.CreateToolhelp32Snapshot(TH32CS_SNAPPROCESS, 0)
    if snap == ctypes.c_void_p(-1).value or snap == 0:
        return found
    entry = PROCESSENTRY32W()
    entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
    ok = k32.Process32FirstW(snap, ctypes.byref(entry))
    while ok:
        name = entry.szExeFile
        low = name.lower()
        if any(h in low for h in PROC_HINTS):
            found.append({"pid": int(entry.th32ProcessID), "exe": name})
        ok = k32.Process32NextW(snap, ctypes.byref(entry))
    k32.CloseHandle(snap)
    return found


def dump_modules(pid: int) -> dict:
    k32 = ctypes.windll.kernel32
    psapi = ctypes.windll.psapi
    access = PROCESS_QUERY_INFORMATION | PROCESS_VM_READ | PROCESS_QUERY_LIMITED_INFORMATION
    handle = k32.OpenProcess(access, False, pid)
    if not handle:
        err = ctypes.GetLastError()
        return {"ok": False, "error": f"OpenProcess failed last_error={err}"}
    try:
        hmods = (ctypes.c_void_p * 1024)()
        needed = wintypes.DWORD()
        if not psapi.EnumProcessModules(handle, ctypes.byref(hmods), ctypes.sizeof(hmods), ctypes.byref(needed)):
            return {"ok": False, "error": f"EnumProcessModules last_error={ctypes.GetLastError()}"}
        count = needed.value // ctypes.sizeof(ctypes.c_void_p)
        dumped = []
        DUMP_DIR.mkdir(parents=True, exist_ok=True)
        for i in range(min(count, 1024)):
            base = hmods[i]
            buf = ctypes.create_unicode_buffer(32768)
            n = psapi.GetModuleFileNameExW(handle, base, buf, 32768)
            path = buf.value if n else ""
            name = Path(path).name
            if name.lower() not in {x.lower() for x in DUMP_NAMES}:
                continue
            info = wintypes.DWORD()
            # size via GetModuleInformation
            class MODULEINFO(ctypes.Structure):
                _fields_ = [
                    ("lpBaseOfDll", ctypes.c_void_p),
                    ("SizeOfImage", wintypes.DWORD),
                    ("EntryPoint", ctypes.c_void_p),
                ]
            mi = MODULEINFO()
            if not psapi.GetModuleInformation(handle, base, ctypes.byref(mi), ctypes.sizeof(mi)):
                dumped.append({"name": name, "error": f"GetModuleInformation {ctypes.GetLastError()}"})
                continue
            size = int(mi.SizeOfImage)
            raw = (ctypes.c_char * size)()
            read = ctypes.c_size_t()
            if not k32.ReadProcessMemory(handle, ctypes.c_void_p(base), raw, size, ctypes.byref(read)):
                dumped.append({"name": name, "error": f"ReadProcessMemory {ctypes.GetLastError()}", "size": size})
                continue
            blob = bytes(raw)[: read.value]
            dest = DUMP_DIR / f"pid{pid}_{name}"
            dest.write_bytes(blob)
            strings = extract_ascii(blob)
            dumped.append(
                {
                    "name": name,
                    "path": path,
                    "base": hex(base or 0),
                    "size": size,
                    "bytes_read": len(blob),
                    "dump": str(dest.relative_to(REPO)).replace("\\", "/"),
                    "sha256": hashlib.sha256(blob).hexdigest(),
                    "token_hits": token_hits(strings),
                    "ascii_string_count": len(strings),
                }
            )
        return {"ok": True, "module_count": count, "dumped": dumped}
    finally:
        k32.CloseHandle(handle)


def classify(static_rows: list[dict], dump: dict) -> str:
    dump_hits = []
    for row in dump.get("dumped") or []:
        dump_hits.extend(row.get("token_hits") or [])
    if any(h.get("is_format") and "weaponshader" in (h.get("text") or "").lower() for h in dump_hits):
        return "DUMP_FORMAT_HIT"
    if dump.get("error", "").startswith("OpenProcess"):
        return "DUMP_ACCESS_DENIED"
    if dump.get("status") == "PROCESS_NOT_RUNNING":
        static_useful = any(r.get("token_hits") for r in static_rows)
        return "STATIC_ONLY_NO_PROCESS"
    if dump.get("ok") and dump_hits:
        # dump ran but no format string
        if any("WeaponShader" in str(h) for h in dump_hits):
            return "DUMP_FORMAT_HIT"
        return "STATIC_ONLY_NO_PROCESS"
    return "STATIC_ONLY_NO_PROCESS"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    static_rows = [scan_pe(rel) for rel in TARGETS]
    pids = list_cf_pids()
    dump: dict
    if not pids:
        dump = {"status": "PROCESS_NOT_RUNNING", "pids": []}
    else:
        dump = {"status": "PROCESS_FOUND", "pids": pids, "attempts": []}
        for proc in pids:
            dump["attempts"].append({"pid": proc["pid"], "exe": proc["exe"], **dump_modules(proc["pid"])})
            # flatten dumped
            last = dump["attempts"][-1]
            dump["dumped"] = last.get("dumped") or []
            dump["error"] = last.get("error")
            dump["ok"] = last.get("ok")
    status = classify(static_rows, dump)
    report = {
        "schema": "cf2.p4m01.n04e-vm-dump.v1",
        "generated_at_utc": now(),
        "status": status,
        "static": static_rows,
        "dump": dump,
        "note": "Dump files must not be git-added. ACE modules were not opened. CF was not launched.",
    }
    (OUT / "scan.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "pids": dump.get("pids") or dump.get("status"), "static": len(static_rows)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
