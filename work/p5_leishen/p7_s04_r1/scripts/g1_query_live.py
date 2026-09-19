import json
import bpy

try:
    import numpy
    numpy_ok = numpy.__version__
except Exception as exc:
    numpy_ok = "ERR:%s" % exc

obj_names = sorted(o.name for o in bpy.data.objects)
result = {
    "filepath": bpy.data.filepath,
    "is_dirty": bool(bpy.data.is_dirty),
    "blender": bpy.app.version_string,
    "numpy": numpy_ok,
    "object_count": len(bpy.data.objects),
    "objects": obj_names,
    "scenes": [s.name for s in bpy.data.scenes],
    "fps": bpy.context.scene.render.fps,
    "frame": bpy.context.scene.frame_current,
}
out = r"D:\project\cf_to_csgo\work\p5_leishen\p7_s04_r1\review\g1_live_query.json"
with open(out, "w", encoding="utf-8") as handle:
    json.dump(result, handle, indent=2)
    handle.write("\n")
result
