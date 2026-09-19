import bpy
lines = bpy.data.texts["r1a_source_switcher.py"].as_string().split("\n")
for i in range(129, 137):
    print("L%03d %r" % (i, lines[i]))
