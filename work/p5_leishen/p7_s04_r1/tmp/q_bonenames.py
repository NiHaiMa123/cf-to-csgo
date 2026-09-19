import bpy, json
view = bpy.data.objects["R1A_VIEW_ARM"]
cs_bones = [b.name for b in view.data.bones]
import json as _j
p = _j.load(open(r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\source\reference_payload.json", encoding="utf-8"))
cf_names = [n["name"] for n in p["nodes"]]
import sys
mods = [m for m in sys.modules if "r1a" in m.lower() or "p7" in m.lower()]
T = [list(r) for r in view["r1a_T"]] if "r1a_T" in view else None
out = {"cs_bones": cs_bones, "cf_names": cf_names, "r1a_module": mods, "r1a_T": T}
print(json.dumps(out, ensure_ascii=False, indent=1))
