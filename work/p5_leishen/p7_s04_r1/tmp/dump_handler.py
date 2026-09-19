import bpy, json
text = bpy.data.texts.get("r1a_source_switcher.py")
s = text.as_string()
lines = s.split("\n")
for i, ln in enumerate(lines):
    if any(k in ln for k in ["SLAM", "desired", "POS_ONLY", "LocRotScale", "matrix_basis", "rest_delta"]):
        print("L%03d %s" % (i, ln))
