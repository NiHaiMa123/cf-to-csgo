import sys, struct
import numpy as np
from PIL import Image

FMT = {0: 'RGBA8888', 2: 'RGB888', 3: 'BGRA8888', 4: 'RGB888_BLUESCREEN',
       12: 'BGR565', 13: 'DXT1', 14: 'DXT3', 15: 'DXT5', 20: 'BGRX8888'}

def c565(v):
    return ((v >> 11 & 31) * 255 // 31, (v >> 5 & 63) * 255 // 63, (v & 31) * 255 // 31)

def dxt5_block(buf, o):
    a0, a1 = buf[o], buf[o + 1]
    ab = int.from_bytes(buf[o + 2:o + 8], 'little')
    al = [a0, a1]
    al += [round((a0 * (7 - i) + a1 * i) / 7) for i in range(1, 7)] if a0 > a1 else \
          [round((a0 * (5 - i) + a1 * i) / 5) for i in range(1, 5)] + [0, 255]
    alpha = np.array([al[(ab >> (3 * i)) & 7] for i in range(16)], np.uint8)
    c0, c1 = struct.unpack_from('<HH', buf, o + 8)
    pal = np.array([c565(c0), c565(c1),
                    tuple((2 * x + y) // 3 for x, y in zip(c565(c0), c565(c1))),
                    tuple((x + 2 * y) // 3 for x, y in zip(c565(c0), c565(c1)))], np.uint8)
    cb = int.from_bytes(buf[o + 12:o + 16], 'little')
    rgb = pal[[(cb >> (2 * i)) & 3 for i in range(16)]]
    return np.hstack([rgb, alpha[:, None]]).reshape(4, 4, 4)

def dxt1_block(buf, o):
    c0, c1 = struct.unpack_from('<HH', buf, o)
    pal = [c565(c0), c565(c1)]
    if c0 > c1:
        pal += [tuple((2 * x + y) // 3 for x, y in zip(pal[0], pal[1])),
                tuple((x + 2 * y) // 3 for x, y in zip(pal[0], pal[1]))]
        al = [255] * 16
    else:
        pal += [tuple((x + y) // 2 for x, y in zip(pal[0], pal[1])), (0, 0, 0)]
        al = [255] * 16
    cb = int.from_bytes(buf[o + 4:o + 8], 'little')
    idx = [(cb >> (2 * i)) & 3 for i in range(16)]
    rgb = np.array([pal[i] for i in idx], np.uint8)
    return np.hstack([rgb, np.array(al, np.uint8)[:, None]]).reshape(4, 4, 4)

def read_vtf(path):
    d = open(path, 'rb').read()
    assert d[:4] == b'VTF\x00'
    hsize = struct.unpack_from('<I', d, 12)[0]
    w, h = struct.unpack_from('<HH', d, 16)
    hifmt = FMT[struct.unpack_from('<I', d, 52)[0]]
    mipmaps = d[56]
    lowfmt = struct.unpack_from('<I', d, 57)[0]
    loww, lowh = d[61], d[62]
    off = hsize
    if loww and lowh and lowfmt != 0xFFFFFFFF:
        if FMT.get(lowfmt) == 'DXT1':
            off += ((loww + 3) // 4) * ((lowh + 3) // 4) * 8
        elif FMT.get(lowfmt) == 'DXT5':
            off += ((loww + 3) // 4) * ((lowh + 3) // 4) * 16
        elif FMT.get(lowfmt) in ('BGRA8888', 'RGBA8888', 'BGRX8888'):
            off += loww * lowh * 4
        elif FMT.get(lowfmt) == 'RGB888':
            off += loww * lowh * 3
    # mip0 (largest) is stored LAST
    for m in range(mipmaps - 1, 0, -1):
        mw, mh = max(1, w >> m), max(1, h >> m)
        if hifmt == 'DXT5':
            off += ((mw + 3) // 4) * ((mh + 3) // 4) * 16
        elif hifmt == 'DXT1':
            off += ((mw + 3) // 4) * ((mh + 3) // 4) * 8
        elif hifmt == 'RGB888':
            off += mw * mh * 3
        else:
            off += mw * mh * 4
    if hifmt in ('DXT5', 'DXT1'):
        img = np.zeros((h, w, 4), np.uint8)
        fn = dxt5_block if hifmt == 'DXT5' else dxt1_block
        for by in range(0, h, 4):
            for bx in range(0, w, 4):
                blk = fn(d, off)
                off += 16 if hifmt == 'DXT5' else 8
                img[by:by + 4, bx:bx + 4] = blk[:4 - max(0, by + 4 - h), :4 - max(0, bx + 4 - w)]
        return Image.fromarray(img)
    n = w * h
    ch = {'BGRA8888': 4, 'RGBA8888': 4, 'BGRX8888': 4, 'RGB888': 3}[hifmt]
    raw = np.frombuffer(d, np.uint8, n * ch, off).reshape(h, w, ch)
    if ch == 3:
        raw = np.dstack([raw, np.full((h, w, 1), 255, np.uint8)])
    if hifmt.startswith('BGR'):
        raw = raw[..., [2, 1, 0, 3]]
    return Image.fromarray(raw)

for f in sys.argv[1:]:
    im = read_vtf(f)
    out = f.rsplit('.', 1)[0] + '.png'
    im.save(out)
    print(f.split('/')[-1], '->', out.split('/')[-1], im.size, im.mode)
