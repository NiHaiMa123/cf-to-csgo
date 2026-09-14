import json, subprocess, shutil, vpk
from pathlib import Path
STAGE = Path(r'D:\project\cf_to_csgo\work\galil_ace_tianxi\deploy\pak01')
VPK_EXE = Path(r'D:\project\cf_to_csgo\migi_tools\migi.exe_extracted\migi-data\utils\vpk.exe')
MIGI = Path(r'D:\steam\steamapps\common\csgo legacy\migi\csgo')
aj = STAGE / 'addons.json'
a = json.loads(aj.read_text(encoding='utf-8'))
a = [x for x in a if 'tianxi' not in x]
a.append('./migi/csgo/addons\\p_cf_tianxi_galilar_p1\\')
aj.write_text(json.dumps(a), encoding='utf-8')
print('staging addons.json fixed:', a)
for old in STAGE.parent.glob('pak01_*.vpk'):
    old.unlink()
p = subprocess.run([str(VPK_EXE), '-M', str(STAGE)], cwd=str(STAGE.parent),
                   capture_output=True, text=True, timeout=600)
print('vpk rc', p.returncode, (p.stdout or '')[-200:])
for f in sorted(STAGE.parent.glob('pak01_*.vpk')):
    shutil.copy2(f, MIGI / f.name)
chk = vpk.open(str(MIGI / 'pak01_dir.vpk'))
print('final addons.json:', chk['addons.json'].read())
