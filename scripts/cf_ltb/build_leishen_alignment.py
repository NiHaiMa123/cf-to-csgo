"""Blender-side script for manually aligning M4A1-Transformers to CS:GO M4A4 skeleton."""

import os
import bpy

PROJECT = os.environ.get("CF2_PROJECT_DIR", r"D:\project\cf_to_csgo")
RAW_OBJ = os.path.join(PROJECT, "work", "m4a1_s_bornbeast", "real_leishen_port", "PV-M4A1_S_Transformers_raw.obj")
REF_SMD = os.path.join(PROJECT, "work", "m4a1_s_bornbeast", "reference_m4a4", "decompiled", "v_m4a1_model.smd")

# Clear scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
for collection in list(bpy.data.collections):
    bpy.data.collections.remove(collection)

main_col = bpy.data.collections.new("ALIGNMENT_WORKSPACE")
bpy.context.scene.collection.children.link(main_col)

# 1. Import Reference SMD (CS:GO M4A4)
before_smd = set(bpy.data.objects)
try:
    bpy.ops.import_scene.smd(filepath=REF_SMD)
except Exception as e:
    print("Warning: SMD import failed, make sure Blender Source Tools is enabled:", e)

ref_objects = [obj for obj in bpy.data.objects if obj not in before_smd]
for obj in ref_objects:
    obj.name = "REF_" + obj.name
    if obj.type == "MESH":
        obj.show_in_front = True

# 2. Import CF Transformers RAW OBJ
before_obj = set(bpy.data.objects)
try:
    bpy.ops.wm.obj_import(
        filepath=RAW_OBJ,
        use_split_objects=True,
        use_split_groups=True,
        forward_axis="Y",
        up_axis="Z",
    )
except Exception:
    bpy.ops.import_scene.obj(
        filepath=RAW_OBJ,
        use_split_objects=True,
        use_split_groups=True,
        axis_forward="Y",
        axis_up="Z",
    )

cf_objects = [obj for obj in bpy.data.objects if obj not in before_obj and obj.type == "MESH"]

# Remove arms from CF model if they exist
for obj in list(cf_objects):
    if "Fview-" in obj.name:
        bpy.data.objects.remove(obj, do_unlink=True)
        cf_objects.remove(obj)

for obj in cf_objects:
    obj.name = "CF_" + obj.name
    
# 3. Create Aligner Empty
bpy.ops.object.empty_add(type='ARROWS', align='WORLD', location=(0, 0, 0))
aligner = bpy.context.active_object
aligner.name = "Transformers_Aligner"
aligner.empty_display_size = 2.0

# 4. Parent CF objects to Aligner
for obj in cf_objects:
    obj.parent = aligner
    # Keep their current transform relative to the empty
    obj.matrix_parent_inverse = aligner.matrix_world.inverted()

# 5. Setup Materials for clarity
cf_mat = bpy.data.materials.new("CF_Material")
cf_mat.diffuse_color = (1.0, 0.2, 0.0, 1.0) # Orange/Red
for obj in cf_objects:
    if obj.data.materials:
        obj.data.materials[0] = cf_mat
    else:
        obj.data.materials.append(cf_mat)

ref_mat = bpy.data.materials.new("REF_Material")
ref_mat.diffuse_color = (0.0, 0.5, 1.0, 0.3) # Transparent Blue
for obj in ref_objects:
    if obj.type == "MESH":
        if obj.data.materials:
            obj.data.materials[0] = ref_mat
        else:
            obj.data.materials.append(ref_mat)

# Select the aligner so the user is ready to move it
bpy.ops.object.select_all(action='DESELECT')
aligner.select_set(True)
bpy.context.view_layer.objects.active = aligner

print("Scene ready! Please manually move, rotate, and scale 'Transformers_Aligner' to match the REF_ mesh.")
