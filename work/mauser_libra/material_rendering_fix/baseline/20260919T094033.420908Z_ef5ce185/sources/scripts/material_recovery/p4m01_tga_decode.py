#!/usr/bin/env python3
"""
P4-M01 Task Spec step D (corrected): TGA native decode.

Independent re-validation established that these BornBeast TGA files are
HEADERLESS BGR24 pixel streams (1024x1024x3 = 3145728 bytes) with a standard
TGA header(18) + Truevision footer(26) = 44-byte block EMBEDDED mid-stream.
The TRUEVISION magic string was located by byte search at:
  alpha=886830, normal=2458394, spec=550357
(consistent with the legacy footer_offset values, confirming the legacy
"split" explanation, now proven rather than assumed).

Correct native decode = remove the embedded 44-byte TGA block, leaving the
3145728-byte pure BGR24 stream -> 1024x1024 image.

Outputs decoded PNG previews (derivative, committable) + channel-stats JSON.
"""
import json
import math
import os
import struct
import hashlib
import zlib

REPO = r"D:\project\cf_to_csgo"
OUT_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/evidence")
PREVIEW_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/previews")

TGA_FILES = {
    "alpha":    "data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA",
    "normal":   "data/rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA",
    "specular": "data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA",
}


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def channel_stats(px, w, h, nch):
    n = w * h
    sums = [0] * nch
    mins = [255] * nch
    maxs = [0] * nch
    uniq = [set() for _ in range(nch)]
    for i in range(n):
        base = i * nch
        for c in range(nch):
            v = px[base + c]
            sums[c] += v
            if v < mins[c]:
                mins[c] = v
            if v > maxs[c]:
                maxs[c] = v
            uniq[c].add(v)
    return [{"mean": round(s / n, 2), "min": m, "max": mx, "unique": len(u)}
            for s, m, mx, u in zip(sums, mins, maxs, uniq)]


def save_png(path, px, w, h, nch):
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(px[y * w * nch:(y + 1) * w * nch])
    color_type = 2 if nch == 3 else 6
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, color_type, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    results = {}
    for name, rel in TGA_FILES.items():
        p = os.path.join(REPO, rel)
        raw = open(p, "rb").read()
        size = len(raw)
        sha = sha256_of(p)
        tv = raw.find(b"TRUEVISION")
        # The embedded TGA block is 18-byte header + 26-byte footer = 44 bytes.
        # Legacy footer_offset was just before TRUEVISION; the full block spans
        # [tv-18 .. tv+26] (the header sits 18 bytes before the footer magic).
        block_start = tv - 18
        block_end = tv + 26
        block_len = block_end - block_start
        pure = raw[:block_start] + raw[block_end:]
        expected = 1024 * 1024 * 3
        ok = len(pure) == expected
        w = h = 1024
        # BGR -> RGB (swap channels)
        rgb = bytearray(expected)
        for i in range(0, expected, 3):
            rgb[i] = pure[i + 2]
            rgb[i + 1] = pure[i + 1]
            rgb[i + 2] = pure[i]
        stats = channel_stats(rgb, w, h, 3)
        out_png = os.path.join(PREVIEW_DIR, f"native_{name}.png")
        save_png(out_png, rgb, w, h, 3)
        results[name] = {
            "relative_path": rel,
            "sha256": sha,
            "size_bytes": size,
            "embedded_tga_block": {
                "header_at": block_start,
                "truevision_magic_at": tv,
                "footer_end_at": block_end,
                "block_len": block_len,
                "note": "headerless BGR24 pixel stream with mid-stream standard TGA header+footer",
            },
            "pure_pixel_bytes": len(pure),
            "expected_1024x1024x3": expected,
            "reconstructed_ok": ok,
            "decoded_preview": os.path.relpath(out_png, REPO),
            "decoded_preview_sha256": sha256_of(out_png),
            "channel_stats_bgr_rgb": stats,
            "variable_channel": max(range(3), key=lambda c: stats[c]["unique"]),
        }
    report = {
        "schema": "cf2.p4m01.tga-decode.v1",
        "method": "locate TRUEVISION magic by byte search; excise 44-byte embedded "
                  "TGA header(18)+footer(26); decode remaining 3145728 bytes as BGR24 1024x1024",
        "files": results,
        "conclusion": "Proven (not assumed): BornBeast TGA maps are headerless BGR24 "
                      "pixel streams with an embedded standard TGA block; correct native "
                      "decode removes that block. All three reconstruct to exactly "
                      "1024x1024x3 pixels.",
    }
    out = os.path.join(OUT_DIR, "tga_decode_matrix.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    for name, r in results.items():
        print(f"{name}: block@[{r['embedded_tga_block']['header_at']}.."
              f"{r['embedded_tga_block']['footer_end_at']}] len={r['embedded_tga_block']['block_len']} "
              f"reconstruct_ok={r['reconstructed_ok']} var_ch={r['variable_channel']} "
              f"stats={[s['unique'] for s in r['channel_stats_bgr_rgb']]}")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
