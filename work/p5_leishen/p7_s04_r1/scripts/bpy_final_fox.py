import bpy
sc = bpy.context.scene
t = bpy.data.texts.get("cf_native_switcher.py")
t.from_string('''import bpy\n\nCLIPS = ["idle_0","select","reload","fire","prefire","postfire","run","knife-attack"]\nCLIP_LEN = {"idle_0":300,"select":64,"reload":160,"fire":9,"prefire":50,"postfire":50,"run":65,"knife-attack":66}\nPAIRS = [("R1A_CF_DEFORM","R1A_CFD_"),("R1A_CF_DEFORM_ARMS","R1A_CFDA_"),("R1A_CF_ANIM","R1A_CF_")]\n\ndef _apply(scene, clip):\n    for obname, prefix in PAIRS:\n        ob = bpy.data.objects.get(obname)\n        a = bpy.data.actions.get(prefix+clip)\n        if ob and a:\n            if ob.animation_data is None: ob.animation_data_create()\n            ob.animation_data.action = a\n            if a.slots: ob.animation_data.action_slot = a.slots[0]\n    scene.frame_end = CLIP_LEN.get(clip, 100)\n\ndef _update(self, context):\n    _apply(context.scene, self.cfd_clip)\n    context.scene.frame_set(0)\n\nclass CFN_PT_panel(bpy.types.Panel):\n    bl_label = "CF native preview"\n    bl_space_type = "VIEW_3D"; bl_region_type = "UI"; bl_category = "CF"\n    def draw(self, ctx):\n        self.layout.prop(ctx.scene, "cfd_clip")\n\ndef register():\n    bpy.types.Scene.cfd_clip = bpy.props.EnumProperty(\n        name="CF clip",\n        items=[(c,c,"") for c in CLIPS],\n        update=_update)\n    try: bpy.utils.unregister_class(CFN_PT_panel)\n    except Exception: pass\n    bpy.utils.register_class(CFN_PT_panel)\n    scene = bpy.context.scene\n    try: cur = scene.cfd_clip\n    except Exception:\n        cur = "idle_0"; scene.cfd_clip = cur\n    _apply(scene, cur)\n\nregister()\n''')
ns={}
exec(t.as_string(), ns)
sc.cfd_clip = "idle_0"
sc.frame_set(10)
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, check_existing=False)
print("SAVED", bpy.data.filepath)
