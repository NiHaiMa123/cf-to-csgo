import struct, zlib, os

f = open(r'D:\steam\steamapps\common\csgo legacy\migi.exe', 'rb')
d = f.read()
cookie = d.rfind(b'MEI\x0c\x0b\x0a\x0b\x0e')
print('cookie at', cookie)
magic, pkgLen, tocOff, tocLen, pyvers = struct.unpack_from('>8sIIII', d, cookie)
pkgStart = cookie + 88 - pkgLen
toc = d[pkgStart + tocOff: pkgStart + tocOff + tocLen]
o = 0
names = []
while o < len(toc):
    entryLen, off, csize, usize, cflag = struct.unpack_from('>IIIIB', toc, o)
    name = toc[o + 18:o + entryLen].rstrip(b'\x00').decode('utf8', 'replace')
    names.append((name, off, csize, usize, cflag))
    o += entryLen
print('entries:', len(names))
for n in names:
    if 'migi' in n[0].lower() or 'main' in n[0].lower() or 'particle' in n[0].lower():
        print(n)
outdir = r'work\galil_ace_tianxi\effects\probes\migi_pyz'
os.makedirs(outdir, exist_ok=True)
for name, off, csize, usize, cflag in names:
    raw = d[pkgStart + off: pkgStart + off + csize]
    if cflag:
        try:
            raw = zlib.decompress(raw)
        except Exception:
            pass
    out = os.path.join(outdir, name.replace('/', '_'))
    open(out, 'wb').write(raw)
print('extracted to', outdir)
