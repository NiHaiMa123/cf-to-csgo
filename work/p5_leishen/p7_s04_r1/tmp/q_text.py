import bpy, json
for tname in ["r1a_source_switcher.py"]:
    t = bpy.data.texts.get(tname)
    if t:
        src = "\n".join(l.body for l in t.lines)
        print("===== "+tname+" ("+str(len(src))+" chars) =====")
        print(src[:6000])
