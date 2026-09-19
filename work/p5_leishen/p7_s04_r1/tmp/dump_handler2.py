import bpy
text = bpy.data.texts.get("r1a_source_switcher.py")
lines = text.as_string().split("\n")
for i in range(105, 150):
    print("L%03d %s" % (i, lines[i]))
