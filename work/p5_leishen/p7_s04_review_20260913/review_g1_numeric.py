"""Independent reviewer checks; no Blender mutation, no retarget, no raw export."""
import hashlib
import json
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/p5'))
import p5_p7_s04_cf_animation as a


def main():
    body = (ROOT / 'work/p5_leishen/p6/verified_root/Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB').read_bytes()
    assert hashlib.sha256(body).hexdigest() == '511dec8d2401a1886ddecd14b4f18e17ac0afbefd943f6dc11a3fd2f82ef6b49'
    alloc = a.parse_header(body)['allocs']
    nodes, off = a.parse_skeleton(body, alloc['nNodes'])
    _, off = a.parse_weight_sets(body, off, len(nodes), alloc['nWeightSets'])
    _, off = a.parse_child_models(body, off, alloc['nChildModels'])
    clips, _ = a.parse_anims(body, off, nodes, alloc['nParentAnims'])
    flags = []
    off = body.find(b'Scene Root') - 2
    for _ in nodes:
        _, payload = a.read_string(body, off)
        flags.append(body[payload + 2])
        off = payload + 71
    assert flags == [0] * 57
    binds = np.array([n['matrix'] for n in nodes]).reshape(-1, 4, 4)
    assert np.max(np.abs(binds[:, 3, :] - [0, 0, 0, 1])) == 0

    def world(clip, frame, normalized):
        ts = {t['node']: t for t in clip['tracks']}
        ws = []
        for i, node in enumerate(nodes):
            tr = ts[i]
            assert tr['kind'] == 'full'
            q = np.array(tr['quat'][frame], dtype=float)
            if normalized:
                q /= np.linalg.norm(q)
            m = np.array(a.local_from_pos_quat(tr['pos'][frame], q))
            ws.append(m if node['parent'] < 0 else ws[node['parent']] @ m)
        return np.array(ws)

    idle = next(c for c in clips if c['name'] == 'idle_0')
    idle_unit = world(idle, 0, True)
    result = {'review_status': 'GROK_G1_V1_REJECTED_METHOD', 'flags_zero_count': 57,
              'bind_affine_bottom_row_max_error': 0.0,
              'convention': 'xyzw / column translation / parent @ local; SDK-source-supported, not inferred from bind=clip',
              'clips': {}, 'issues': [
                  'Ranking hypotheses by bind error over all clips is invalid: bind and clip poses need not coincide.',
                  'Winner row_major/row3 compares track translations against the homogeneous zero row and mixes conventions.',
                  'acos(trace(A.T @ B)) requires proper rotations; raw nonorthogonal matrices yield spurious angles.',
                  'max_world_travel is distance from first key, not the required raw-versus-normalized difference.',
                  'No first-key match does not prove parser failure; do not require a nonexistent pose as a gate.'
              ]}
    for clip in clips:
        if clip['name'] not in ('select', 'reload', 'idle_0'):
            continue
        max_delta = (-1, None, None)
        for f in range(clip['n_keyframes']):
            raw = world(clip, f, False)
            unit = world(clip, f, True)
            assert np.max(np.abs(raw - np.array(a.cf_worlds(nodes, clip, f)))) < 1e-10
            ds = np.linalg.norm(raw[:, :3, 3] - unit[:, :3, 3], axis=1)
            i = int(ds.argmax())
            if ds[i] > max_delta[0]:
                max_delta = (float(ds[i]), f, nodes[i]['name'])
        ends = {}
        for name in ('FvARM-bone Prop1', 'FvARM-bone R Hand', 'FvARM-bone L Hand'):
            i = next(n['index'] for n in nodes if n['name'] == name)
            first = world(clip, 0, True)[i]
            last = world(clip, clip['n_keyframes'] - 1, True)[i]
            angle = np.degrees(np.arccos(np.clip((np.trace(idle_unit[i, :3, :3].T @ last[:3, :3]) - 1) / 2, -1, 1)))
            ends[name] = {'first_vs_idle_pos': float(np.linalg.norm(first[:3, 3] - idle_unit[i, :3, 3])),
                          'last_vs_idle_pos': float(np.linalg.norm(last[:3, 3] - idle_unit[i, :3, 3])),
                          'last_vs_idle_angle_deg': float(angle)}
        result['clips'][clip['name']] = {'duration_ms': clip['duration_ms'],
            'raw_normalized_max_world_position_delta': {'distance': max_delta[0], 'key': max_delta[1], 'bone': max_delta[2]},
            'normalized_endpoints': ends}
    dest = Path(__file__).with_name('review_g1_numeric.json')
    dest.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
