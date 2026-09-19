import json
from pathlib import Path

skin = json.loads(Path(r"D:/project/cf_to_csgo/work/mauser_libra/decode/cf_skin_m1896_libra.json").read_text(encoding="utf-8"))
for m in skin["meshes"]:
    if m["name"].lower().startswith("fview"):
        continue
    vs = m["vertices"]
    xs, ys, zs = vs[0::3], vs[1::3], vs[2::3]
    print(f"{m['name']:20s} n={len(xs):4d}  x[{min(xs):7.2f},{max(xs):7.2f}] y[{min(ys):7.2f},{max(ys):7.2f}] z[{min(zs):7.2f},{max(zs):7.2f}]")
