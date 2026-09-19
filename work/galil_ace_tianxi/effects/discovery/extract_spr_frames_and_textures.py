# -*- coding: utf-8 -*-
"""E1d — second-pass resource closure + texture channel audit
(plan.md §7 task 2/§2.1 item 5).

1. Parse every extracted .SPR: 20B header (u32 nFrames, u32 unk, 12B zeros)
   then u16-length-prefixed DTX path per frame. Resolve each frame DTX via
   MD5-verified REZ read into assets/ and append to asset_graph.json.
2. Decode every extracted .DTX (direct refs + SPR frames) with
   CFRezManager --decode-image (handles DXT5), compute per-channel stats
   (RGBA mean/min/max, alpha coverage), and write previews/ PNGs.
Output: texture_channels.json + updated asset_graph.json
"""
from __future__ import annotations

import hashlib
import json
import lzma
import struct
import subprocess
import sys
import tempfile
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
ASSETS = OUT / "assets"
PREV = OUT / "previews"
CFREZ = _REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
GRAPH = OUT / "asset_graph.json"

try:
    from PIL import Image
except ImportError:
    Image = None


def key(p: str) -> str:
    return p.replace("\\", "/").upper()


def parse_spr(body: bytes) -> list[str]:
    # header: u32 nFrames, u32 unk, 12B zeros -> frame list at offset 20
    if len(body) < 20:
        return []
    n_frames = struct.unpack_from("<I", body, 0)[0]
    names = []
    off = 20
    for _ in range(min(n_frames, 4096)):
        if off + 2 > len(body):
            break
        ln = struct.unpack_from("<H", body, off)[0]
        if off + 2 + ln > len(body):
            break
        names.append(body[off + 2:off + 2 + ln].decode("ascii", errors="replace").rstrip("\0"))
        off += 2 + ln
    return names


def channel_stats(img) -> dict:
    rgba = img.convert("RGBA")
    bands = rgba.split()
    out = {"size": list(rgba.size)}
    for i, name in enumerate(("r", "g", "b", "a")):
        data = list(bands[i].getdata())
        n = len(data)
        out[name] = {
            "mean": round(sum(data) / max(n, 1), 2),
            "min": min(data), "max": max(data),
            "nonzero_pct": round(100.0 * sum(1 for v in data if v) / max(n, 1), 1),
        }
    return out


def main() -> int:
    PREV.mkdir(parents=True, exist_ok=True)
    graph = json.loads(GRAPH.read_text(encoding="utf-8"))
    have = {key(f["rez_path"]) for f in graph["files"]}

    # --- pass 1: SPR frame DTXs ---
    spr_index = {}
    frame_paths = set()
    for p in sorted(ASSETS.rglob("*.SPR")):
        raw = p.read_bytes()
        body = lzma.decompress(raw, format=lzma.FORMAT_ALONE) if raw[:1] == b"\x5d" else raw
        frames = parse_spr(body)
        rel = p.relative_to(ASSETS).as_posix()
        spr_index[rel] = {"frames": frames, "n_frames_declared": struct.unpack_from("<I", body, 0)[0] if len(body) >= 4 else None}
        frame_paths.update(f for f in frames if f)

    wanted = {key(f): f.replace("\\", "/") for f in frame_paths if key(f) not in have}
    print(f"[e1d] spr files={len(spr_index)} frame refs={len(frame_paths)} new={len(wanted)}")

    found = {}
    if wanted:
        for ip in extract_all.discover_index_archives(str(CF)):
            try:
                entries = extract_all.read_index_entries(ip)
            except Exception:
                continue
            for e in entries:
                k = key(e["full_path"])
                if k in wanted and is_complete_directory_md5(e.get("md5")):
                    found.setdefault(k, (ip, e))

    missing = []
    for k, rel in sorted(wanted.items()):
        if k not in found:
            missing.append(rel)
            continue
        ip, e = found[k]
        try:
            data, prov = read_verified_payload(ip, e)
        except Exception as exc:  # noqa: BLE001
            missing.append(f"{rel} (read failed: {exc})")
            continue
        dest = ASSETS / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        graph["files"].append({
            "rez_path": rel, "archive": prov["index_archive"],
            "payload_file": prov["payload_file"], "offset": prov["offset"],
            "size": prov["size"], "md5": prov["directory_md5"],
            "sha256": prov["sha256"],
            "local_path": str(dest.relative_to(OUT)).replace("\\", "/"),
            "extra_candidate": False, "spr_frame": True,
        })
        have.add(k)
    if missing:
        graph.setdefault("missing", []).extend(missing)
    graph["spr_index"] = spr_index
    graph["generated_at_utc"] = datetime.now(timezone.utc).isoformat()
    GRAPH.write_text(json.dumps(graph, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[e1d] extracted {len(wanted) - len(missing)} spr frames, missing {len(missing)}")
    for m in missing:
        print("  MISSING:", m)

    # --- pass 2: decode every DTX + channel stats ---
    tex_rows = []
    dtx_files = sorted(ASSETS.rglob("*.DTX"))
    with tempfile.TemporaryDirectory() as tmp:
        for p in dtx_files:
            rel = p.relative_to(ASSETS).as_posix()
            raw = p.read_bytes()
            try:
                body = lzma.decompress(raw, format=lzma.FORMAT_ALONE) if raw[:1] == b"\x5d" else raw
            except Exception:
                body = raw
            src = Path(tmp) / (hashlib.md5(rel.encode()).hexdigest() + ".dtx")
            src.write_bytes(body)
            safe = rel.replace("/", "_").replace("\\", "_")
            dest = PREV / (safe.rsplit(".", 1)[0] + ".png")
            row = {"rez_path": rel, "packed_bytes": len(raw), "body_bytes": len(body),
                   "preview": None, "ok": False}
            if CFREZ.is_file():
                r = subprocess.run([str(CFREZ), "--decode-image", str(src), str(dest)],
                                   capture_output=True, text=True, timeout=60)
                if r.returncode == 0 and dest.exists() and Image is not None:
                    img = Image.open(dest)
                    row.update(ok=True, preview=str(dest.relative_to(OUT)).replace("\\", "/"),
                               stats=channel_stats(img))
            tex_rows.append(row)
    doc = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "decoder": "CFRezManager --decode-image (DTX incl. DXT5)",
        "textures": tex_rows,
        "ok": sum(1 for r in tex_rows if r["ok"]),
        "total": len(tex_rows),
    }
    (OUT / "texture_channels.json").write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[e1d] decoded {doc['ok']}/{doc['total']} dtx -> previews/")
    for r in tex_rows:
        s = r.get("stats") or {}
        print(f"  {r['rez_path']:70s} ok={r['ok']} size={s.get('size')} a_nonzero={((s.get('a') or {}).get('nonzero_pct'))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
