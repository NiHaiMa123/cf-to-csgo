import bpy
bpy.ops.wm.save_as_mainfile(filepath=bpy.data.filepath, check_existing=False)
print("SAVED", bpy.data.filepath)
