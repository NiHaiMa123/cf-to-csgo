import struct, hashlib, os

DIR = r'D:\steam\steamapps\common\csgo legacy\migi\csgo\pak01_dir.vpk'
BASE = os.path.dirname(DIR)
ADDON = r'D:\steam\steamapps\common\csgo legacy\migi\csgo\addons\p_cf_tianxi_galilar_p1'

dd = open(DIR, 'rb').read()
o = 28
entries = {}
while True:
    e = dd.index(b'\x00', o); ext = dd[o:e].decode('latin1'); o = e + 1
    if not ext: break
    while True:
        e = dd.index(b'\x00', o); p = dd[o:e].decode('latin1'); o = e + 1
        if not p: break
        while True:
            e = dd.index(b'\x00', o); fn = dd[o:e].decode('latin1'); o = e + 1
            if not fn: break
            crc, pre, aidx, offt, ln, term = struct.unpack_from('<IHHIIH', dd, o); o += 18
            rel = (p + '/' + fn + '.' + ext) if p != ' ' else fn + '.' + ext
            entries[rel] = (aidx, offt, ln)

arch = {}
def read_entry(rel):
    aidx, offt, ln = entries[rel]
    if aidx not in arch:
        arch[aidx] = open(os.path.join(BASE, f'pak01_{aidx:03d}.vpk'), 'rb').read()
    return arch[aidx][offt:offt + ln]

same, diff, missing = [], [], []
for root, _, files in os.walk(ADDON):
    for f in files:
        ap = os.path.join(root, f)
        rel = os.path.relpath(ap, ADDON).replace('\\', '/')
        ah = hashlib.sha256(open(ap, 'rb').read()).hexdigest()
        if rel not in entries:
            missing.append(rel)
            continue
        ch = hashlib.sha256(read_entry(rel)).hexdigest()
        (same if ah == ch else diff).append(rel)

print(f'SAME={len(same)} DIFF={len(diff)} MISSING={missing}')
for r in diff: print('  DIFF:', r)

# manifest check: does packed particles_manifest.txt contain our pcf?
if 'particles/particles_manifest.txt' in entries:
    man = read_entry('particles/particles_manifest.txt').decode('latin1')
    print('--- packed manifest tail ---')
    print(man[-400:])
    print('cf_tianxi_galilar_p1 in manifest:', 'cf_tianxi_galilar_p1' in man)
