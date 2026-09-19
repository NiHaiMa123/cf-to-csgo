import bpy, json
scn = bpy.context.scene
res = {}
cls = getattr(bpy.types, "P7_PT_clips", None)
if cls is not None:
    try:
        bpy.utils.unregister_class(cls)
        res["panel"] = "unregistered"
    except Exception as e:
        res["panel"] = "err: %s" % e
else:
    res["panel"] = "not registered"
if hasattr(bpy.types.Scene, "p7_clip"):
    del bpy.types.Scene.p7_clip
    res["enum_prop"] = "deleted"
if "p7_clip" in scn.keys():
    del scn["p7_clip"]
    res["stored_value"] = "deleted"
tb = bpy.data.texts.get("p7_clip_switcher.py")
if tb is not None:
    res["text_use_module"] = tb.use_module
    bpy.data.texts.remove(tb)
    res["text_block"] = "removed"
bpy.ops.wm.save_mainfile()
res["saved"] = bpy.data.filepath
print(json.dumps(res, ensure_ascii=False))
