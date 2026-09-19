import bpy, json
new_map = {
 "FvARM-bone": "v_weapon.Bip01",
 "FvARM-bone Pelvis": "v_weapon.Bip01_Pelvis",
 "FvARM-bone Spine": "v_weapon.Bip01_Spine",
 "FvARM-bone Spine1": "v_weapon.Bip01_Spine1",
 "FvARM-bone Neck": "v_weapon.Bip01_Neck",
 "FvARM-bone L Clavicle": "v_weapon.Bip01_L_Clavicle",
 "FvARM-bone L UpperArm": "v_weapon.Bip01_L_UpperArm",
 "FvARM-bone R Clavicle": "v_weapon.Bip01_R_Clavicle",
 "FvARM-bone R UpperArm": "v_weapon.Bip01_R_UpperArm",
}
fn = None
for h in bpy.app.handlers.frame_change_post:
    if getattr(h, "__name__", "") == "r1a_apply":
        fn = h; break
assert fn, "r1a_apply not registered"
bm = fn.__globals__["BONE_MAP"]
before = len(bm)
bm.update(new_map)
fn.__globals__["_CACHE"].clear()

# persist: patch the text block source too
tb = bpy.data.texts.get("r1a_source_switcher.py")
assert tb is not None
src = "\n".join(l.body for l in tb.lines)
marker = '    "Bone04": "v_weapon.M4A1_Bolt",\n}'
assert marker in src, "marker not found"
add = "".join('    "%s": "%s",\n' % kv for kv in new_map.items())
src = src.replace(marker, '    "Bone04": "v_weapon.M4A1_Bolt",\n' + add + '}')
tb.clear(); tb.write(src)
tb.use_module = True

# unhide arms
for n in ["R1A_VIEW_GLOVE","R1A_VIEW_SLEEVE"]:
    bpy.data.objects[n].hide_viewport = False
    bpy.data.objects[n].hide_render = False

scn = bpy.context.scene
scn.frame_set(scn.frame_current)
bpy.context.view_layer.update()
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\fullarms.png"
bpy.ops.render.render(write_still=True)
print(json.dumps({"map_size": [before, len(bm)], "clip": scn.r1a_source_clip, "frame": scn.frame_current}))
