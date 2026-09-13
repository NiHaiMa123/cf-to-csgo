import bpy

CLIPS = [
    ("1_idle_hold", "1 持枪 idle", 54),
    ("2_shoot", "2 射击", 4),
    ("3_draw", "3 切枪 draw", 30),
    ("4_reload", "4 换弹 reload", 107),
    ("5_lookat", "5 检视 lookat", 159),
]


def _items(self, context):
    return [(name, label, "", i) for i, (name, label, _end) in enumerate(CLIPS)]


def apply_clip(self, context):
    obj = bpy.data.objects.get("CS_M4A4_Armature")
    if obj is None:
        return
    if obj.animation_data is None:
        obj.animation_data_create()
    act = bpy.data.actions.get(self.p7_clip)
    if act is None:
        return
    obj.data.pose_position = "POSE"
    obj.animation_data.action = act
    if getattr(act, "slots", None) and len(act.slots):
        obj.animation_data.action_slot = act.slots[0]
    end = 54
    for name, _label, clip_end in CLIPS:
        if name == self.p7_clip:
            end = clip_end
            break
    context.scene.frame_start = 0
    context.scene.frame_end = end
    context.scene.frame_current = 0
    context.scene.frame_set(0)


class P7_PT_clips(bpy.types.Panel):
    bl_label = "P7 clips"
    bl_idname = "P7_PT_clips"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "P7"

    def draw(self, context):
        self.layout.prop(context.scene, "p7_clip")


def register():
    if not hasattr(bpy.types.Scene, "p7_clip"):
        bpy.types.Scene.p7_clip = bpy.props.EnumProperty(name="clip", items=_items, update=apply_clip)
    try:
        bpy.utils.register_class(P7_PT_clips)
    except ValueError:
        pass


def unregister():
    if hasattr(bpy.types.Scene, "p7_clip"):
        del bpy.types.Scene.p7_clip
    try:
        bpy.utils.unregister_class(P7_PT_clips)
    except Exception:
        pass


register()
