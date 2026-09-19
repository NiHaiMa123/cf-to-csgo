import bpy, json
scn = bpy.context.scene
# current state render
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\now_state.png"
bpy.ops.render.render(write_still=True)
# unhide glove+sleeve meshes AND their armatures' deform (already constraints), render
for n in ["R1A_VIEW_GLOVE","R1A_VIEW_SLEEVE"]:
    o = bpy.data.objects.get(n)
    o.hide_viewport = False; o.hide_render = False
scn.render.filepath = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\tmp\now_with_arms.png"
bpy.ops.render.render(write_still=True)
# positions of hand bones in view arm (world) at current frame
dg = bpy.context.evaluated_depsgraph_get()
arm = bpy.data.objects["R1A_VIEW_ARM"].evaluated_get(dg)
aw = bpy.data.objects["R1A_VIEW_ARM"].matrix_world
out = {}
for b in ["v_weapon.Bip01_L_Hand","v_weapon.Bip01_R_Hand","v_weapon.M4A1_Parent","v_weapon.Bip01_R_Forearm","v_weapon.Bip01_L_Forearm"]:
    pb = arm.pose.bones.get(b)
    if pb: out[b] = [round(v,2) for v in (aw @ pb.matrix).translation]
# glove mesh world bbox
gl = bpy.data.objects["R1A_VIEW_GLOVE"]
import mathutils
dgg = bpy.context.evaluated_depsgraph_get()
gle = gl.evaluated_get(dgg)
me = gle.to_mesh()
xs=[v.co.x for v in me.vertices]; ys=[v.co.y for v in me.vertices]; zs=[v.co.z for v in me.vertices]
out["glove_bbox_local"] = [[round(min(xs),1),round(min(ys),1),round(min(zs),1)],[round(max(xs),1),round(max(ys),1),round(max(zs),1)]]
out["glove_world"] = [round(v,2) for v in gl.matrix_world.translation]
print(json.dumps({"clip": scn.r1a_source_clip, "frame": scn.frame_current, "bones": out}, ensure_ascii=False, indent=1))
