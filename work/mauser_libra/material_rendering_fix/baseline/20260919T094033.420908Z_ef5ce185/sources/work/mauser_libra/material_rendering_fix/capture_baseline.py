"""Read-only P0 capture. Exclusive timestamp directories; no deployment or imports.

Evidence files are sealed read-only with a SHA-256 manifest (not OS/WORM storage).
Failed captures remain sealed and must never be used as experiment parents.
"""
import datetime as dt
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import struct
import sys
import uuid
import zlib

ROOT = Path('D:/project/cf_to_csgo')
FIX = ROOT / 'work/mauser_libra/material_rendering_fix'
A = ROOT / 'work/mauser_libra/addon_v2'
GAME = Path('D:/steam/steamapps/common/csgo legacy/migi/csgo')
B = GAME / 'addons/p_cf_mauser_libra_p1'
C = GAME / 'pak01_dir.vpk'
MV = ROOT / 'work/mauser_libra/material_v2'
CHUNK = 1024 * 1024


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def safe(path):
    path = Path(os.path.abspath(path))
    for part in [*reversed(path.parents), path]:
        if part.exists() or part.is_symlink():
            s = part.lstat()
            require(not (stat.S_ISLNK(s.st_mode) or
                         getattr(s, 'st_file_attributes', 0) & 0x400),
                    f'Link/reparse point rejected: {part}')
    return path


def stamp(path):
    s = safe(path).stat()
    require(stat.S_ISREG(s.st_mode), f'Not a regular file: {path}')
    return [s.st_size, s.st_mtime_ns, s.st_ctime_ns, s.st_dev, s.st_ino]


def digest(path):
    before = stamp(path)
    h = hashlib.sha256()
    with path.open('rb') as f:
        while block := f.read(CHUNK):
            h.update(block)
    require(before == stamp(path), f'Changed during hash: {path}')
    return {'bytes': before[0], 'sha256': h.hexdigest(), 'stat': before}


def inventory(root):
    safe(root)
    require(root.is_dir(), f'Missing directory: {root}')
    result = {}
    for base, dirs, files in os.walk(root, followlinks=False):
        for name in dirs + files:
            safe(Path(base) / name)
        for name in sorted(files):
            p = Path(base) / name
            key = p.relative_to(root).as_posix()
            require(key.lower() not in {k.lower() for k in result}, 'Case collision')
            result[key] = digest(p)
    return result


def same(x, y):
    return (x['bytes'], x['sha256']) == (y['bytes'], y['sha256'])


def exact(f, count):
    b = f.read(count)
    require(len(b) == count, 'Truncated binary data')
    return b


def parse_tree(header, tree):
    magic, version, size = struct.unpack_from('<III', header)
    require(magic == 0x55AA1234 and version in (1, 2), 'Invalid VPK header')
    require(len(tree) == size, 'Invalid VPK tree size')
    f = io.BytesIO(tree)

    def string():
        out = bytearray()
        while (ch := exact(f, 1)) != b'\0':
            out.extend(ch)
        return out.decode('utf-8')

    entries = {}
    while ext := string():
        while folder := string():
            while name := string():
                crc, preload, archive, offset, length, end = struct.unpack('<IHHIIH', exact(f, 18))
                require(end == 0xffff, 'Invalid VPK entry terminator')
                key = (('' if folder == ' ' else folder + '/') + name +
                       ('' if ext == ' ' else '.' + ext)).replace('\\', '/').lower()
                require(not key.startswith('/') and ':' not in key and
                        all(p not in ('', '.', '..') for p in key.split('/')), 'Unsafe VPK path')
                require(key not in entries, f'Duplicate VPK entry: {key}')
                entries[key] = (crc, archive, offset, length, exact(f, preload))
    require(f.tell() == len(tree), 'Trailing VPK tree bytes')
    return entries


def vpk(expected):
    watched = {str(C): stamp(C)}
    with C.open('rb') as f:
        head = exact(f, 12)
        magic, version, size = struct.unpack('<III', head)
        require(magic == 0x55AA1234 and version in (1, 2), 'Invalid VPK')
        if version == 2:
            head += exact(f, 16)
        require(size <= 128 * CHUNK, 'Unreasonable VPK tree size')
        tree = exact(f, size)
    entries = parse_tree(head, tree)
    result = {}
    for key, wanted in expected.items():
        require(key.lower() in entries, f'Missing C entry: {key}')
        crc, archive, offset, length, preload = entries[key.lower()]
        inline = archive == 0x7fff
        path = C if inline else C.with_name(f'pak01_{archive:03d}.vpk')
        absolute = len(head) + size + offset if inline else offset
        if length:
            watched.setdefault(str(path), stamp(path))
            limit = watched[str(path)][0]
            if inline and version == 2:
                limit = len(head) + size + struct.unpack_from('<I', head, 12)[0]
            require(absolute + length <= limit, f'VPK slice outside data: {key}')
        h = hashlib.sha256(preload)
        checksum = zlib.crc32(preload)
        remaining = length
        if remaining:
            with path.open('rb') as f:
                f.seek(absolute)
                while remaining:
                    block = exact(f, min(CHUNK, remaining))
                    remaining -= len(block)
                    h.update(block)
                    checksum = zlib.crc32(block, checksum)
        record = {'bytes': len(preload) + length, 'sha256': h.hexdigest(),
                  'archive': str(path), 'archive_index': archive,
                  'preload_bytes': len(preload), 'entry_offset': offset,
                  'absolute_data_offset': absolute, 'data_bytes': length, 'crc32': crc}
        require(checksum == crc, f'C CRC mismatch: {key}')
        require(same(wanted, record), f'A/C mismatch: {key}')
        result[key] = record
    require(all(stamp(Path(p)) == s for p, s in watched.items()), 'VPK changed during read')
    return {'entries': result, 'archive_stats': watched,
            'header_tree_sha256': hashlib.sha256(head + tree).hexdigest(),
            'version': version, 'header_bytes': len(head), 'tree_bytes': size}


def main():
    require(safe(Path(__file__)) == FIX / 'capture_baseline.py', 'Unexpected script root')
    parent = safe(FIX / 'baseline')
    parent.mkdir(exist_ok=True)
    out = parent / (dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S.%fZ_') + uuid.uuid4().hex[:8])
    out.mkdir(exist_ok=False)
    evidence = {'file_integrity': 'FAIL', 'runtime_loading': 'PENDING',
                'runtime_scenes': 'PENDING', 'visual_acceptance': 'PENDING',
                'baseline': str(out), 'addon_baseline': str(out / 'addon_v2'),
                'immutability': 'exclusive creation, no overwrite, read-only files, SHA-256 seal; not WORM',
                'started_utc': dt.datetime.now(dt.timezone.utc).isoformat()}

    def dest(relative):
        p = safe(out / relative)
        require(p.is_relative_to(out) and p != out, 'Output escape')
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def write(relative, obj):
        with dest(relative).open('x', encoding='utf-8', newline='\n') as f:
            json.dump(obj, f, indent=2, ensure_ascii=False)
            f.write('\n')

    tracked = {}

    def copy(src, relative):
        before = digest(src)
        with src.open('rb') as f, dest(relative).open('xb') as g:
            while block := f.read(CHUNK):
                g.write(block)
        require(before == digest(src) and same(before, digest(out / relative)), f'Copy changed: {src}')
        tracked[str(src)] = before
        return before

    try:
        pre_a, pre_b = inventory(A), inventory(B)
        require(len(pre_a) == 29, f'Expected 29 A files, got {len(pre_a)}')
        require(pre_a.keys() == pre_b.keys(), 'A/B inventory mismatch')
        require(all(same(pre_a[k], pre_b[k]) for k in pre_a), 'A/B hash mismatch')
        pre_c = vpk(pre_a)
        for key in pre_a:
            copy(A / key, 'addon_v2/' + key)
        reports = ['audit/input_manifest.json', 'source_v2/translation_report.json',
                   'segmentation/triangle_materials.json', 'ir/cf_mauser_libra.material_ir.json',
                   'reports/source_translation_report.json', 'reports/channel_audit.json',
                   'g_material_assignments.json', 'i_deploy_manifest.json', 'i_pak_verify.json']
        for rel in reports:
            copy(MV / rel, 'raw_reports/' + rel)
        manifest = json.loads((out / 'raw_reports/audit/input_manifest.json').read_text('utf-8'))
        inputs = {}
        for asset in manifest['assets']:
            p = safe(Path(asset['path']))
            require(p.is_relative_to(ROOT), f'Input outside repository: {p}')
            if not p.exists() and not asset.get('required', True):
                inputs[asset['role']] = {'missing_optional': str(p)}
                continue
            d = digest(p)
            require(d['sha256'] == asset['sha256'], f'Historical input SHA mismatch: {p}')
            tracked[str(p)] = d
            inputs[asset['role']] = {'path': str(p), **d}
        for name in ('diffuse', 'normal', 'specular', 'alpha'):
            p = MV / 'upscale' / f'{name}_2048.png'
            tracked[str(p)] = digest(p)
            inputs['upscale_' + name] = {'path': str(p), **tracked[str(p)]}
        sources = list((ROOT / 'scripts/material_recovery').glob('*.py')) + list(MV.glob('*.py'))
        sources += [Path(__file__), ROOT / 'plan.material-rendering.md', ROOT / 'pipeline.md']
        for p in sources:
            copy(p, 'sources/' + p.relative_to(ROOT).as_posix())
        references = {}
        for role, ident in [('current', 'a278daac-b12b-4a31-af11-06a0f6de0257'),
                            ('target', '8e9f670f-f7ac-41dc-ad62-515bfe046098')]:
            p = safe(Path('C:/Users/Administrator/AppData/Local/Temp') / f'codex-clipboard-{ident}.png')
            references[role] = {'source': str(p), 'present': p.exists()}
            if p.exists():
                references[role].update(copy(p, f'references/{role}.png'))
        translation = json.loads((out / 'raw_reports/source_v2/translation_report.json').read_text('utf-8'))
        regions = json.loads((out / 'raw_reports/segmentation/triangle_materials.json').read_text('utf-8'))['regions']
        require([s['region_id'] for s in translation['slots']] == list(range(6)), 'Expected six slots')
        require([s['region_id'] for s in regions] == list(range(6)), 'Expected six regions')
        materials = out / 'addon_v2/materials/models/weapons/v_models/cf_mauser'
        for slot, region in zip(translation['slots'], regions):
            require(slot['triangles'] == region['triangles'], 'Slot/region count mismatch')
            slot['actual_vmt'] = (materials / (slot['material'] + '.vmt')).read_text('utf-8')
            slot['actual_params'] = dict(re.findall(r'"(\$[^"\n]+)"\s+"([^"\n]*)"', slot['actual_vmt']))
        headers = {}
        for name in ('cf_mauser_libra', 'cf_mauser_libra_n'):
            with (materials / (name + '.vtf')).open('rb') as f:
                b = exact(f, 64)
            require(b[:4] == b'VTF\0', 'Invalid VTF signature')
            headers[name] = {'version': list(struct.unpack_from('<II', b, 4)),
                             'size': list(struct.unpack_from('<HH', b, 16)),
                             'flags': hex(struct.unpack_from('<I', b, 20)[0]),
                             'frames': struct.unpack_from('<H', b, 24)[0],
                             'format': struct.unpack_from('<I', b, 52)[0], 'mips': b[56]}
        write('material_snapshot.json', {'historical_translation': translation,
              'historical_regions': regions, 'actual_vtf_headers': headers,
              'note': 'Historical reports preserved, not new runtime or shader validation.'})
        require(inventory(A) == pre_a and inventory(B) == pre_b, 'A/B pre/post changed')
        require(vpk(pre_a) == pre_c, 'C pre/post changed')
        require(all(digest(Path(p)) == d for p, d in tracked.items()), 'Input/source/report pre/post changed')
        copied = inventory(out / 'addon_v2')
        require(copied.keys() == pre_a.keys() and all(same(pre_a[k], copied[k]) for k in pre_a), 'Baseline mismatch')
        evidence.update(file_integrity='PASS', files=29, a_root=str(A), b_root=str(B),
                        c_root=str(C), a=pre_a, b=pre_b, c=pre_c, inputs=inputs,
                        references=references, tracked_sources=tracked,
                        checks={'a_b': 'PASS 29/29', 'a_c': 'PASS 29/29',
                                'baseline_copy': 'PASS 29/29', 'pre_post': 'PASS',
                                'vpk_crc32': 'PASS 29/29'})
    except Exception as exc:
        evidence['error'] = f'{type(exc).__name__}: {exc}'
    evidence['finished_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    write('snapshot.json', evidence)
    write('seal.json', {k: {'bytes': v['bytes'], 'sha256': v['sha256']}
                        for k, v in inventory(out).items()})
    for base, _, files in os.walk(out):
        for name in files:
            safe(Path(base) / name).chmod(stat.S_IREAD)
    print(json.dumps({k: evidence[k] for k in ('file_integrity', 'baseline', 'addon_baseline')}, indent=2))
    if 'error' in evidence:
        print(evidence['error'], file=sys.stderr)
    return 0 if evidence['file_integrity'] == 'PASS' else 1


if __name__ == '__main__':
    sys.exit(main())
