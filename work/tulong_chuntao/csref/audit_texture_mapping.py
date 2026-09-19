"""Independent Blender UV audit. Outputs only to csref/_diag/mapping_audit.

Run with blender --background --factory-startup --python <this file>.
Uses the original decoded mesh; no live Blender scene or addon is modified.
"""
import bpy
import json
import hashlib
import sys
from pathlib import Path
import numpy as np
from mathutils import Vector, Matrix

WORK = Path(__file__).resolve().parents[1]
OUT = WORK / 'csref/_diag/mapping_audit'
args = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
if args:
    OUT = OUT / Path(args[0]).stem
OUT.mkdir(parents=True, exist_ok=True)
skin_path = Path(args[0]) if args else WORK / 'decode/cf_skin_kukri_spring.json'
skin = json.loads(skin_path.read_text())
m = next(m for m in skin['meshes'] if m['bone_weights'] is None)
vs = np.array(m['vertices']).reshape(-1, 3)
reference = json.loads((WORK / 'decode/cf_skin_kukri_spring.json').read_text())
ref_mesh = next(x for x in reference['meshes'] if x['bone_weights'] is None)
ref_vs = np.array(ref_mesh['vertices']).reshape(-1, 3)
def box_bind(document):
    return np.array(next(n for n in document['skeleton'] if n['name'] == 'Box01')['bind_matrix']).reshape(4, 4)
rebind = box_bind(reference) @ np.linalg.inv(box_bind(skin))
vs = (rebind @ np.column_stack((vs, np.ones(len(vs)))).T).T[:, :3]
uvs = np.array(m['uvs']).reshape(-1, 2)
tris = np.array(m['triangles']).reshape(-1, 3)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
me = bpy.data.meshes.new('original_cf_mesh')
me.from_pydata(vs.tolist(), [], tris.tolist())
ob = bpy.data.objects.new('knife', me)
bpy.context.collection.objects.link(ob)
uvl = me.uv_layers.new()
mt = bpy.data.materials.new('unlit_uv_only')
mt.use_nodes = True
nt = mt.node_tree
nt.nodes.clear()
t = nt.nodes.new('ShaderNodeTexImage')
t.image = bpy.data.images.load(str(WORK / 'decode/PV-Kukri_Beast.png'))
em = nt.nodes.new('ShaderNodeEmission')
o = nt.nodes.new('ShaderNodeOutputMaterial')
nt.links.new(t.outputs['Color'], em.inputs['Color'])
nt.links.new(em.outputs[0], o.inputs['Surface'])
me.materials.append(mt)
center = (ref_vs.min(0) + ref_vs.max(0)) / 2
_, _, axes = np.linalg.svd(ref_vs - ref_vs.mean(0))
normal = axes[-1]
up = axes[0] * (1 if axes[0, 1] > 0 else -1)
right = np.cross(up, normal)
camd = bpy.data.cameras.new('audit_camera')
camd.type = 'ORTHO'
camd.ortho_scale = float(np.linalg.norm(ref_vs.max(0) - ref_vs.min(0))) * 1.15
cam = bpy.data.objects.new('audit_camera', camd)
bpy.context.collection.objects.link(cam)
camera_matrix = np.eye(4)
camera_matrix[:3, :3] = np.column_stack((right, up, normal))
camera_matrix[:3, 3] = center + normal * 20
cam.matrix_world = Matrix(camera_matrix)
sc = bpy.context.scene
sc.camera = cam
sc.render.engine = 'CYCLES'
sc.cycles.samples = 1
sc.render.resolution_x = 640
sc.render.resolution_y = 700
sc.render.resolution_percentage = 100
sc.world.color = (0.03, 0.03, 0.03)
sc.view_settings.view_transform = 'Standard'
sc.view_settings.look = 'None'
sc.render.image_settings.file_format = 'PNG'
variants = {}
for swap in (False, True):
    for fu, fv in ((False, False), (False, True), (True, False), (True, True)):
        # Inputs use decoded coordinates; Blender V starts at image bottom.
        uv = uvs[:, ::-1].copy() if swap else uvs.copy()
        if fu:
            uv[:, 0] = 1 - uv[:, 0]
        if fv:
            uv[:, 1] = 1 - uv[:, 1]
        for poly in me.polygons:
            for li in poly.loop_indices:
                uvl.data[li].uv = uv[me.loops[li].vertex_index]
        tag = ('swap_' if swap else '') + ('flip_u' if fu else 'u') + '_' + ('flip_v' if fv else 'v')
        sc.render.filepath = str(OUT / (tag + '.png'))
        bpy.ops.render.render(write_still=True)
        variants[tag] = {'swap': swap, 'flip_u': fu, 'flip_v': fv}
# Leave the scene in the actual pipeline convention, not the final test variant.
for poly in me.polygons:
    for li in poly.loop_indices:
        u, v = uvs[me.loops[li].vertex_index]
        uvl.data[li].uv = (u, 1 - v)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT / 'diffuse_preview.blend'))
nt.links.remove(em.inputs['Color'].links[0])
em.inputs['Color'].default_value = (0.5, 0.5, 0.5, 1)
sc.render.filepath = str(OUT / 'solid_geometry.png')
bpy.ops.render.render(write_still=True)
(OUT / 'audit.json').write_text(json.dumps({
    'skin_sha256': hashlib.sha256(skin_path.read_bytes()).hexdigest(),
    'vertices': len(vs), 'triangles': len(tris),
    'mesh_name': m['name'], 'rebind_to_original_Box01': rebind.tolist(),
    'camera_matrix': camera_matrix.tolist(),
    'variants': variants, 'shader': 'Emission; no lighting, no specular',
}, indent=2))
