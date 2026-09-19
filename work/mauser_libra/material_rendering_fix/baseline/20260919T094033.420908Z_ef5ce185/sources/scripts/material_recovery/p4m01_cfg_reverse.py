#!/usr/bin/env python3
"""
P4-M01 Task Spec step F: WeaponShader CFG binary semantic reverse.

Findings so far (byte-level):
  - 492 bytes = 164 records of 3 bytes each.
  - Each 3-byte record is BGR color ('ff ff 0f' = R=0f G=ff B=ff pale cyan,
    'ff ff 0e' = yellow). NOT text, NOT float (float reinterpretation = NaN/garbage).
  - Entropy ~4.65, low -> ordered color ramp, not compressed/random.
  => The CFG is a 1-D RGB color lookup strip / gradient ramp, consistent with
     the repo's CfgBinaryStripDecoder (raw RGB strip renderer) BUT that tool is
     only a visualizer; per spec F it is NOT a semantic decode.

This script:
  1. Decodes each weapon CFG into its RGB ramp.
  2. Extracts the ramp color sequence + first/last/dominant colors.
  3. Byte-level differential across skins (BornBeast vs Transformers vs a
     traditional skin Jewelry) to locate which skins share / diverge in ramp.
  4. Records evidence; does NOT assert a Source1 VMT parameter mapping (that
     remains unproven per the legacy f2 gate).
"""
import json
import os
import struct
import hashlib

REPO = r"D:\project\cf_to_csgo"
OUT_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/evidence")
PREVIEW_DIR = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/previews")

CFG_FILES = {
    # hero skins
    "BornBeast":  "data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_BornBeast.CFG",
    "Transformers": "data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_Transformers.CFG",
    "Jewelry":    "data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_Jewelry.CFG",
}

PREVIEW_TARGETS = ["BornBeast", "Transformers", "Jewelry"]


def sha256_of(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def decode_ramp(b):
    n = len(b) // 3
    ramp = []
    for i in range(n):
        r, g, bl = b[i * 3], b[i * 3 + 1], b[i * 3 + 2]
        ramp.append((r, g, bl))
    return ramp


def ramp_summary(ramp):
    colors = set(ramp)
    # direction: compare first vs last
    first, last = ramp[0], ramp[-1]
    # count dominant channel per pixel to classify ramp hue family
    hue = {}
    for (r, g, bl) in colors:
        if r >= g and r >= bl:
            h = "R"
        elif g >= r and g >= bl:
            h = "G"
        else:
            h = "B"
        hue[h] = hue.get(h, 0) + 1
    return {
        "pixel_count": len(ramp),
        "unique_colors": len(colors),
        "first_color_bgr": list(first),
        "last_color_bgr": list(last),
        "dominant_channel_family": max(hue, key=hue.get),
        "monotonic_rgb_delta": [last[i] - first[i] for i in range(3)],
        "sample_sequence_first12_bgr": [list(ramp[i]) for i in range(min(12, len(ramp)))],
    }


def byte_diff(a, b):
    n = min(len(a), len(b))
    diff = sum(1 for i in range(n) if a[i] != b[i])
    return {
        "len_a": len(a), "len_b": len(b),
        "compared_bytes": n,
        "differing_bytes": diff,
        "diff_ratio": round(diff / n, 4) if n else None,
    }


def save_ramp_png(path, ramp):
    import zlib as _z
    w = len(ramp)
    h = 8
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for (r, g, bl) in ramp:
            raw.extend((r, g, bl))
    png = b"\x89PNG\r\n\x1a\n"
    def chunk(tag, data):
        c = tag + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", _z.crc32(c) & 0xffffffff)
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", _z.compress(bytes(raw), 9))
    png += chunk(b"IEND", b"")
    with open(path, "wb") as f:
        f.write(png)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    os.makedirs(PREVIEW_DIR, exist_ok=True)
    decoded = {}
    for name, rel in CFG_FILES.items():
        p = os.path.join(REPO, rel)
        raw = open(p, "rb").read()
        ramp = decode_ramp(raw)
        summary = ramp_summary(ramp)
        rec = {
            "relative_path": rel,
            "sha256": sha256_of(p),
            "size_bytes": len(raw),
            "record_size_bytes": 3,
            "record_count": len(ramp),
            "interpretation": "rgb_color_lookup_ramp (164 px * 3-byte BGR)",
            "is_text": False,
            "is_float": False,
            "ramp_summary": summary,
        }
        if name in PREVIEW_TARGETS:
            out = os.path.join(PREVIEW_DIR, f"cfg_ramp_{name}.png")
            save_ramp_png(out, ramp)
            rec["ramp_preview"] = os.path.relpath(out, REPO)
            rec["ramp_preview_sha256"] = sha256_of(out)
        decoded[name] = (raw, rec)

    diffs = {}
    names = list(CFG_FILES.keys())
    for i in range(len(names)):
        for j in range(i + 1, len(names)):
            a, b = names[i], names[j]
            diffs[f"{a}_vs_{b}"] = byte_diff(decoded[a][0], decoded[b][0])

    report = {
        "schema": "cf2.p4m01.cfg-reverse.v1",
        "method": "3-byte BGR record decode; ramp color-sequence extraction; "
                  "byte-level differential across skins",
        "cfgs": {n: r for n, (_, r) in decoded.items()},
        "differential": diffs,
        "conclusion": (
            "Each weapon CFG is a 164-pixel RGB color lookup ramp (3-byte BGR "
            "records), not text and not float. Per spec F this is a visualizable "
            "ramp, not a proven Source1 shader-parameter mapping; the precise "
            "engine binding of this ramp (tint/emissive/energy gradient) requires "
            "the LTB material-binding evidence (step E), which is currently "
            "MISSING in the LTB decoder. Differential across skins quantifies "
            "how hero skins (BornBeast/Transformers) relate to a traditional "
            "skin (Jewelry) at the byte level."
        ),
        "semantic_binding_status": "PROVISIONAL_NOT_PROVEN",
    }
    out = os.path.join(OUT_DIR, "cfg_reverse_report.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    for n, (_, r) in decoded.items():
        s = r["ramp_summary"]
        print(f"{n}: {r['record_count']} px, first={s['first_color_bgr']} "
              f"last={s['last_color_bgr']} dom={s['dominant_channel_family']} "
              f"uniq={s['unique_colors']}")
    for k, v in diffs.items():
        print(f"diff {k}: {v['differing_bytes']}/{v['compared_bytes']} "
              f"({v['diff_ratio']})")
    print(f"\nWrote {out}")


if __name__ == "__main__":
    main()
