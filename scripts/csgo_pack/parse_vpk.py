import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from _paths import game_dir
def parse_vpk(filepath, target_path):
    with open(filepath, 'rb') as f:
        sig, ver, tree_size = struct.unpack('<III', f.read(12))
        if ver == 2:
            f.read(16)
        while True:
            ext = b''
            while True:
                c = f.read(1)
                if not c or c == b'\x00': break
                ext += c
            if not ext: break
            while True:
                path = b''
                while True:
                    c = f.read(1)
                    if not c or c == b'\x00': break
                    path += c
                if not path: break
                while True:
                    name = b''
                    while True:
                        c = f.read(1)
                        if not c or c == b'\x00': break
                        name += c
                    if not name: break
                    f.read(18)
                    p_str = path.decode('latin1', 'ignore')
                    if p_str == target_path:
                        n_str = name.decode('latin1', 'ignore')
                        e_str = ext.decode('latin1', 'ignore')
                        print(f'{n_str}.{e_str}')
parse_vpk(os.path.join(game_dir(), "csgo", "pak01_dir.vpk"), 'sound/player/vo/jungle_fem_epic')
