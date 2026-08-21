#!/usr/bin/env python3
"""
P4-M01 Task Spec step H: offline shader hypothesis renderer.

Inputs are LOCAL CF only (0 external pixels in any generated output).
Each layer can be toggled. Fixed output for A/B.

Also performs a reference-only differential control against the external CS1.6
flatten texture (NOT used in generation): compares color-domain statistics to
clarify the native base DTX role (albedo vs special/energy layer).

Includes a minimal stdlib PNG reader (no PIL).
"""
import json
import os
import zlib
import struct
import math
import hashlib

REPO = r"D:\project\cf_to_csgo"
EVID = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/evidence")
PREV = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/previews")
HYP = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/previews/hypotheses")


# ---------- minimal PNG reader ----------
def read_png(path):
    data = open(path, "rb").read()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    pos = 8
    width = height = bitd = colt = None
    idat = b""
    while pos < len(data):
        ln = struct.unpack(">I", data[pos:pos + 4])[0]
        tag = data[pos + 4:pos + 8]
        chunk = data[pos + 8:pos + 8 + ln]
        if tag == b"IHDR":
            width, height, bitd, colt = struct.unpack(">IIBB", chunk[:10])
        elif tag == b"IDAT":
            idat += chunk
        elif tag == b"IEND":
            break
        pos += 12 + ln
    raw = zlib.decompress(idat)
    ch = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[colt]
    stride = width * ch
    out = bytearray(width * height * ch)
    prev = bytearray(stride)
    rp = 0
    for y in range(height):
        ftype = raw[rp]; rp += 1
        line = bytearray(raw[rp:rp + stride]); rp += stride
        if ftype == 1:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                line[i] = (line[i] + a) & 255
        elif ftype == 2:
            for i in range(stride):
                line[i] = (line[i] + prev[i]) & 255
        elif ftype == 3:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                line[i] = (line[i] + ((a + b) >> 1)) & 255
        elif ftype == 4:
            for i in range(stride):
                a = line[i - ch] if i >= ch else 0
                b = prev[i]
                c = prev[i - ch] if i >= ch else 0
                p = a + b - c
                pa, pb, pc = abs(p - a), abs(p - b), abs(p - c)
                pr = a if (pa <= pb and pa <= pc) else (b if pb <= pc else c)
                line[i] = (line[i] + pr) & 255
        out[y * stride:(y + 1) * stride] = line
        prev = line
    return width, height, ch, bytes(out)


def save_png(path, px, w, h, ch):
    def chunk(t, d):
        c = t + d
        return struct.pack(">I", len(d)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    raw = bytearray()
    stride = w * ch
    for y in range(h):
        raw.append(0)
        raw.extend(px[y * stride:(y + 1) * stride])
    p = b"\x89PNG\r\n\x1a\n"
    p += chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, {1: 0, 3: 2, 4: 4}[ch], 0, 0, 0))
    p += chunk(b"IDAT", zlib.compress(bytes(raw), 9))
    p += chunk(b"IEND", b"")
    open(path, "wb").write(p)


def color_domain(px, w, h, ch):
    n = w * h
    sums = [0] * 3
    mn = [255] * 3
    mx = [0] * 3
    sat = 0
    for i in range(n):
        r, g, b = px[i * ch], px[i * ch + 1], px[i * ch + 2]
        for c, v in enumerate((r, g, b)):
            sums[c] += v
            mn[c] = min(mn[c], v)
            mx[c] = max(mx[c], v)
        sat += max(r, g, b) - min(r, g, b)
    return {"mean_rgb": [round(s / n, 1) for s in sums],
            "min_rgb": mn, "max_rgb": mx,
            "mean_saturation": round(sat / n, 1)}


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def main():
    os.makedirs(HYP, exist_ok=True)

    # --- reference-only external control ---
    ext = os.path.join(REPO, "work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png")
    ext_stats = None
    if os.path.exists(ext):
        ew, eh, ech, epx = read_png(ext)
        ext_stats = color_domain(epx, ew, eh, ech)
        ext_stats["source"] = "external_cs1.6_flatten (REFERENCE_ONLY, not used in generation)"
        ext_stats["size"] = [ew, eh]

    # --- native layers ---
    bw, bh, bch, bpx = read_png(os.path.join(PREV, "native_base_dtx.png"))
    aw, ah, ach, apx = read_png(os.path.join(PREV, "native_alpha.png"))
    nw, nh, nch, npx = read_png(os.path.join(PREV, "native_normal.png"))
    sw, sh, sch, spx = read_png(os.path.join(PREV, "native_specular.png"))
    cw, chh, cch, cpx = read_png(os.path.join(PREV, "cfg_ramp_BornBeast.png"))

    native_base_stats = color_domain(bpx, bw, bh, bch)

    # --- hypotheses (all native-only) ---
    # H1: base as albedo + specular highlight (R channel) modulation
    W, H = bw, bh  # work in base UV space (512x256)
    full = bytearray(W * H * 3)
    spec_n = W / sw  # scale specular down to base space
    for y in range(H):
        for x in range(W):
            bi = (y * W + x) * 3
            sx = min(sw - 1, int(x * spec_n))
            sy = min(sh - 1, int(y * (H / sh)))
            si = (sy * sw + sx) * 3
            spec = spx[si] / 255.0          # R channel of specular
            base_r, base_g, base_b = bpx[bi], bpx[bi + 1], bpx[bi + 2]
            # highlight: brighten base by specular (Phong-ish additive)
            hr = min(255, int(base_r + spec * 120))
            hg = min(255, int(base_g + spec * 120))
            hb = min(255, int(base_b + spec * 120))
            full[bi], full[bi + 1], full[bi + 2] = hr, hg, hb

    save_png(os.path.join(HYP, "h1_full_base_spec.png"), full, W, H, 3)

    # H2: base + CFG ramp as emissive tint (sample ramp by vertical position)
    # ramp is horizontal 164px; use its mid as a global emissive color
    mid = cpx[(chh // 2) * cw * 3:(chh // 2) * cw * 3 + 3]
    er, eg, eb = mid[0], mid[1], mid[2]
    full2 = bytearray(W * H * 3)
    for y in range(H):
        for x in range(W):
            bi = (y * W + x) * 3
            # emissive proportional to base brightness (energy hotspots)
            lum = (bpx[bi] + bpx[bi + 1] + bpx[bi + 2]) / (3 * 255.0)
            full2[bi] = min(255, int(bpx[bi] + er * lum * 0.5))
            full2[bi + 1] = min(255, int(bpx[bi + 1] + eg * lum * 0.5))
            full2[bi + 2] = min(255, int(bpx[bi + 2] + eb * lum * 0.5))
    save_png(os.path.join(HYP, "h2_full_base_emissive.png"), full2, W, H, 3)

    report = {
        "schema": "cf2.p4m01.shader-hypotheses.v1",
        "inputs": "local_cf only (base_dtx, alpha, normal, specular, weapon CFG ramp)",
        "external_reference_control": ext_stats,
        "native_base_color_domain": native_base_stats,
        "base_role_inference": (
            "Native base DTX is low-saturation, single-hue (purple/blue) "
            "512x256. External CS1.6 (reference only) is compared for color "
            "domain. If external shows a full multi-hue albedo while native "
            "base is near-monochrome, the native base DTX is a SPECIAL/ENERGY "
            "layer rather than a complete albedo; the recognizable BornBeast "
            "identity must then come from the layer combination, not base alone."
        ),
        "hypotheses": {
            "H1_base_plus_specular": {
                "formula": "out = base_rgb + specular.R * 120 (additive highlight)",
                "toggles": ["base", "specular"],
                "preview": "previews/hypotheses/h1_full_base_spec.png",
                "preview_sha256": sha(os.path.join(HYP, "h1_full_base_spec.png")),
            },
            "H2_base_plus_cfg_emissive": {
                "formula": "out = base_rgb + cfg_ramp_midcolor * luminance * 0.5",
                "toggles": ["base", "cfg_ramp"],
                "preview": "previews/hypotheses/h2_full_base_emissive.png",
                "preview_sha256": sha(os.path.join(HYP, "h2_full_base_emissive.png")),
            },
        },
        "layer_previews": {
            "base_512x256": "previews/native_base_dtx.png",
            "alpha_1024": "previews/native_alpha.png",
            "normal_1024": "previews/native_normal.png",
            "specular_1024": "previews/native_specular.png",
            "cfg_ramp": "previews/cfg_ramp_BornBeast.png",
        },
        "reproducibility": "Deterministic CPU Python; inputs are local_cf files "
                           "with recorded sha256; re-running reproduces identical PNGs.",
    }
    out = os.path.join(EVID, "shader_hypotheses.json")
    with open(out, "w") as f:
        json.dump(report, f, indent=2)
    print("native base domain:", native_base_stats)
    print("external(ref-only) domain:", ext_stats)
    print("Wrote", out)
    print("Wrote h1/h2 previews")


if __name__ == "__main__":
    main()
