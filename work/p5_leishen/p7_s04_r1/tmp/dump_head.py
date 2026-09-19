import bpy
lines = bpy.data.texts["r1a_source_switcher.py"].as_string().split("\n")
for i in range(0, 105):
    print("L%03d %s" % (i, lines[i]))
