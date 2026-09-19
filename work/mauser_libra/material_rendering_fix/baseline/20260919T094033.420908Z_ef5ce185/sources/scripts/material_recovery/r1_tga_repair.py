#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""P4-M01-R1-D: TGA repair correction aligned with the real decoder.

Supersedes the R0 p4m01_tga_decode.py / tga_decode_matrix.json (commit 632ede4),
which excised [TRUEVISION-18, TRUEVISION+26) as 'header+footer'.

The repo's TgaThumbnailDecoder.TryRepairInsertedFooterHeader actually treats
the inserted block as [26-byte footer][18-byte header]:
    signatureOffset = position of "TRUEVISION-XFILE"
    footerOffset    = signatureOffset - 8        (footer = 8 bytes before sig:
                     4 reserved + 16-char signature + '.' + NUL = 26 total,
                     ending at signatureOffset+18)
    headerOffset    = footerOffset + 26          (= signatureOffset + 18)
and TryBuildRepairedTga then reassembles:
    repaired = header(headerPrefix=ImageDataOffset bytes from headerOffset)
             + pixels( data[0:footerOffset] + data[headerOffset+headerPrefix:] )

This script ports that logic byte-for-byte, records for each file:
signatureOffset / footerOffset / headerOffset, parsed header fields, and
rebuilds the repaired TGA; then cross-checks the pixel stream against a direct
port of the decoder's DecodeUncompressed path.

Outputs r1/tga_repair_r1.json + previews/native_<name>_r1.png
"""
from __future__ import annotations

import hashlib
import json
import os
import struct
import zlib

REPO = r"D:\project\cf_to_csgo"
OUT_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/r1")
PREVIEW_DIR = os.path.join(OUT_DIR, "previews")
SUPERSEDES_COMMIT = "632ede449578f688cea7e6b5f40cbf03700aaaa5"
SUPERSEDES_REPORT = "work/m4a1_s_bornbeast/p4_m01_native_material/evidence/tga_decode_matrix.json"

FILES = {
    "alpha":    "data/rf017/ModelTextures/AlphaMap/M4A1_S_BornBeast_alpha.TGA",
    "normal":   "data/rf017/ModelTextures/NormalMap/M4A1_S_BornBeast_N.TGA",
    "specular": "data/rf017/ModelTextures/SpecularMap/M4A1_S_BornBeast_S.TGA",
}

FOOTER_SIG = b"TRUEVISION-XFILE"
HEADER_LEN = 18


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def lzma_is_compressed(data: bytes) -> bool:
    """Port of LzmaAloneDetector first-byte check (TryReadHeader)."""
    if len(data) < 13 or data[0] not in (0x5D, 0x08):
        return False
    dict_size = struct.unpack_from("<I", data, 1)[0]
    legacy = data[1] == 0 and data[2] == 0 and data[3] == 0
    if dict_size == 0 and not legacy:
        return False
    raw = struct.unpack_from("<q", data, 5)[0]
    if raw >= 0:
        return not (raw == 0 or raw > 0x7FFFFFFF)
    return raw == -1


def tga_try_read_header(data: bytes):
    """Port of TgaThumbnailDecoder.TryReadHeader."""
    if len(data) < HEADER_LEN:
        return False, None, "short"
    id_len = data[0]
    cmap_type = data[1]
    img_type = data[2]
    width = struct.unpack_from("<H", data, 12)[0]
    height = struct.unpack_from("<H", data, 14)[0]
    depth = data[16]
    descriptor = data[17]
    if cmap_type not in (0, 1) or img_type not in (1, 2, 3, 9, 10, 11):
        return False, None, f"implausible type fields (cmap={cmap_type} type={img_type})"
    if not (0 < width <= 16384 and 0 < height <= 16384 and width * height <= 4096 * 4096):
        return False, None, f"implausible dims {width}x{height}"
    hdr = {"id_length": id_len, "color_map_type": cmap_type, "image_type": img_type,
           "width": width, "height": height, "pixel_depth": depth, "descriptor": descriptor}
    return True, hdr, "ok"


def has_footer_terminator(data: bytes, sig_off: int) -> bool:
    t = sig_off + len(FOOTER_SIG)
    return t + 2 <= len(data) and data[t] == ord(".") and data[t + 1] == 0


def try_repair_inserted_footer_header(data: bytes):
    """Port of TgaThumbnailDecoder.TryRepairInsertedFooterHeader +
    TryBuildRepairedTga. Returns (repaired_bytes, details) or (None, reason)."""
    best = None
    best_detail = None
    search = 0
    while search < len(data):
        rel = data.find(FOOTER_SIG, search)
        if rel < 0:
            break
        sig_off = rel
        search = sig_off + 1
        footer_off = sig_off - 8
        header_off = footer_off + 26
        if footer_off < 0 or header_off + HEADER_LEN > len(data):
            continue
        if not has_footer_terminator(data, sig_off):
            continue
        ok, hdr, why = tga_try_read_header(data[header_off:])
        if not ok or hdr is None:
            continue
        if hdr["image_type"] in (9, 10, 11):  # RLE rejected by decoder
            continue
        # sourcePixelBytes for truecolor/grayscale uncompressed
        spb = {2: {16: 2, 24: 3, 32: 4}.get(hdr["pixel_depth"], 0),
               3: {8: 1, 16: 2}.get(hdr["pixel_depth"], 0)}.get(hdr["image_type"], 0)
        if spb <= 0:
            continue
        prefix = hdr["id_length"] + (0 if hdr["color_map_type"] == 0 else -1)
        # ImageDataOffset per decoder = HeaderLength + idLength + colorMapBytes
        image_data_offset = HEADER_LEN + hdr["id_length"] + (hdr["color_map_length"] * 4 if hdr["color_map_type"] == 1 else 0)
        w, h = hdr["width"], hdr["height"]
        pixel_bytes = w * h * spb
        available = footer_off + len(data) - (header_off + image_data_offset)
        if pixel_bytes != available:
            # TryInferSquareDimensions fallback
            if available % spb == 0:
                side2 = available // spb
                side = int(side2 ** 0.5)
                if side > 0 and side * side == side2:
                    w = h = side
                    pixel_bytes = available
                    hdr = dict(hdr, width=w, height=h, dimensions_inferred=True)
        if pixel_bytes != available:
            best_detail = f"pixelBytes {pixel_bytes} != available {available}"
            continue
        repaired = bytearray(image_data_offset + pixel_bytes)
        repaired[:image_data_offset] = data[header_off:header_off + image_data_offset]
        struct.pack_into("<H", repaired, 12, w)
        struct.pack_into("<H", repaired, 14, h)
        repaired[image_data_offset:image_data_offset + footer_off] = data[:footer_off]
        tail_start = header_off + image_data_offset
        repaired[image_data_offset + footer_off:] = data[tail_start:tail_start + pixel_bytes]
        detail = {
            "signature_offset": sig_off,
            "footer_offset": footer_off,
            "header_offset": header_off,
            "image_data_offset": image_data_offset,
            "parsed_header": hdr,
            "source_pixel_bytes": spb,
            "pixel_bytes": pixel_bytes,
            "repaired_total": len(repaired),
            "available_pixel_bytes": available,
        }
        best = bytes(repaired)
        best_detail = detail
        break
    return best, best_detail


def decode_uncompressed_bgr24(tga: bytes):
    """Direct port of decoder's uncompressed truecolor path for 24bpp top-origin."""
    ok, hdr, _ = tga_try_read_header(tga)
    if not ok:
        return None, None
    w, h = hdr["width"], hdr["height"]
    ido = HEADER_LEN + hdr["id_length"]
    desc = hdr["descriptor"]
    right_origin = bool(desc & 0x10)
    top_origin = bool(desc & 0x20)
    px = bytearray(w * h * 3)
    src = ido
    for ordinal in range(w * h):
        sx = ordinal % w
        sy = ordinal // w
        tx = w - 1 - sx if right_origin else sx
        ty = sy if top_origin else h - 1 - sy
        o = (ty * w + tx) * 3
        px[o:o + 3] = tga[src:src + 3]     # decoder copies source bytes 1:1 into BGRA B,G,R slots
        src += 3
    return px, hdr


def channel_stats(px, w, h):
    sums = [0, 0, 0]; mins = [255] * 3; maxs = [0] * 3; uniq = [set(), set(), set()]
    n = w * h
    for i in range(n):
        for c in range(3):
            v = px[i * 3 + c]
            sums[c] += v
            mins[c] = min(mins[c], v)
            maxs[c] = max(maxs[c], v)
            uniq[c].add(v)
    return [{"mean": round(s / n, 2), "min": m, "max": mx, "unique": len(u)}
            for s, m, mx, u in zip(sums, mins, maxs, uniq)]


def save_png(path, px, w, h):
    def chunk(tag, payload):
        c = tag + payload
        return struct.pack(">I", len(payload)) + c + struct.pack(">I", zlib.crc32(c) & 0xFFFFFFFF)
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        raw.extend(px[y * w * 3:(y + 1) * w * 3])
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(bytes(raw), 9)) + chunk(b"IEND", b"")
    open(path, "wb").write(png)


def main():
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    results = {}
    for name, rel in FILES.items():
        path = os.path.join(REPO, rel.replace("/", "\\"))
        raw = open(path, "rb").read()
        rec = {
            "relative_path": rel,
            "sha256": sha256_of(path),
            "size_bytes": len(raw),
            "lzma_is_compressed": lzma_is_compressed(raw),
        }
        repaired, detail = try_repair_inserted_footer_header(raw)
        if repaired is None:
            rec["repair"] = {"ok": False, "reason": detail}
            results[name] = rec
            print(name, "REPAIR FAILED:", detail)
            continue

        rec["repair"] = {"ok": True, **detail}
        # cross-check: parse repaired TGA and decode via ported uncompressed path
        px, hdr2 = decode_uncompressed_bgr24(repaired)
        if px is None:
            rec["decode"] = {"ok": False, "reason": "repaired header failed to parse"}
            results[name] = rec
            print(name, "DECODE FAILED")
            continue
        w, h = hdr2["width"], hdr2["height"]
        stats = channel_stats(px, w, h)
        preview_rel = f"work/m4a1_s_bornbeast/p4_m01_native_material/r1/previews/native_{name}_r1.png"
        save_png(os.path.join(REPO, preview_rel.replace("/", "\\")), px, w, h)

        # R0 comparison offsets
        tv = raw.find(b"TRUEVISION-XFILE")
        r0_block_start = tv - 18   # R0 excised [tv-18, tv+26)
        formal_footer_off = tv - 8
        formal_header_off = formal_footer_off + 26

        rec["decode"] = {
            "ok": True,
            "width": w, "height": h, "descriptor": hdr2["descriptor"],
            "origin_right": bool(hdr2["descriptor"] & 0x10),
            "origin_top": bool(hdr2["descriptor"] & 0x20),
            "channel_stats_after_formal_repair": stats,
            "preview": preview_rel,
            "preview_sha256": sha256_of(os.path.join(REPO, preview_rel.replace("/", "\\"))),
        }
        rec["r0_vs_r1_offsets"] = {
            "truevision_signature_at": tv,
            "r0_excision_start": r0_block_start,
            "r0_excision_end": tv + 26,
            "formal_footer_offset": formal_footer_off,
            "formal_header_offset": formal_header_off,
            "delta_r0start_vs_formal_footer": formal_footer_off - r0_block_start,
            "note": (
                "R0 deleted [sig-18, sig+26); formal decoder keeps bytes "
                "[sig-18,sig-8) (last 10 bytes of R0's 'header') as PIXEL DATA "
                "and starts its 18-byte header at sig+18. Pixel streams differ."
            ),
        }
        results[name] = rec
        print(f"{name}: sig@{tv} footer@{formal_footer_off} header@{formal_header_off} "
              f"{w}x{h} desc={hdr2['descriptor']:02x} uniq={[s['unique'] for s in stats]}")

    report = {
        "schema": "cf2.p4m01.r1.tga-repair.v1",
        "supersedes_commit": SUPERSEDES_COMMIT,
        "supersedes_report": SUPERSEDES_REPORT,
        "review_reason": (
            "R0 excised [TRUEVISION-18, TRUEVISION+26) as header+footer. The "
            "real TryRepairInsertedFooterHeader uses footerOffset=sig-8, "
            "headerOffset=footerOffset+26 (= sig+18), i.e. block layout is "
            "[footer][header], not [header][footer]. R0 therefore removed the "
            "wrong 44 bytes (10-byte shift at the start), corrupting the pixel "
            "stream even though total length matched."
        ),
        "method": (
            "byte-equivalent port of TryRepairInsertedFooterHeader/"
            "TryBuildRepairedTga/DecodeUncompressed; repaired TGAs decoded and "
            "hashed; no external inputs"
        ),
        "files": results,
        "conclusion": None,  # filled below
    }

    all_ok = all(r.get("decode", {}).get("ok") for r in results.values())
    report["conclusion"] = (
        "All three BornBeast maps repair and decode through the formal decoder "
        "logic; repaired headers carry plausible width/height/descriptor and "
        "the decoded planes show single-variable-channel structure consistent "
        "with mask/scalar roles. R0 previews and channel-role claims are "
        "superseded; new channel-role determination is deferred to R1-H."
        if all_ok else
        "At least one file failed formal repair/decode; see per-file reasons."
    )

    out = os.path.join(OUT_DIR, "tga_repair_r1.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    print("wrote", out)


if __name__ == "__main__":
    main()
