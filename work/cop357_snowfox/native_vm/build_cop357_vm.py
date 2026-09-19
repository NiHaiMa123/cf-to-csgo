# -*- coding: utf-8 -*-
"""P5 — CF COP357-雪域霜狐 (M1896_Libra) first-person viewmodel for v_pist_glock18.

Same native recipe as tulong/galilace: CF skeleton + Nini GR LBS arms + MXH,
CS Bip01* pinned (0,+500,0). 10 rigid CF pieces bound per PIECE_NODE
(Hungarian assignment on bind-local mean radius). No idle FX this round.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO / "scripts"))
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
WORK = REPO / "work" / "cop357_snowfox"
OUT = WORK / "native_vm"
SOURCE1 = OUT / "source1"
ANIMS = SOURCE1 / "v_pist_glock18_anims"
ISOLATED = OUT / "isolated_game" / "csgo"
STAGING = WORK / "addon"
LOG_DIR = OUT / "logs"

# material v2 mode: --v2 / MAUSER_V2=1 uses material_v2 slots + per-tri
# assignment; staging goes to addon_v2 and MIGI deploy is deferred to Phase I.
V2 = "--v2" in sys.argv or os.environ.get("MAUSER_V2") == "1"
V2_DIR = WORK / "material_v2" / "source_v2"
V2_ASSIGN = WORK / "material_v2" / "g_material_assignments.json"
STAGING_V2 = WORK / "addon_v2"

PAYLOAD = WORK / "decode" / "reference_payload.json"
SKIN = WORK / "decode" / "cf_skin_cop357_dominator.json"
ARMDUMP = REPO / "work" / "galil_ace_tianxi" / "decode" / "nini_gr" / "cf_skin_nini_gr.json"
ARMTEX = REPO / "work" / "galil_ace_tianxi" / "decode" / "nini_gr"
VM_TRANSFORM = WORK / "csref" / "viewmodel_transform.json"
DEPLOY_ADDON = GAME / "migi" / "csgo" / "addons" / "p_cf_cop357_winter_p1"

STUDIOMDL = GAME / "bin" / "studiomdl.exe"
VTFCMD = REPO / "tools" / "VTFEdit" / "VTFCmd.exe"
MAT_DIR_VMT = "models/weapons/v_models/cf_cop357"

GUN_MAT = "cf_cop357_snowfox"
# mesh -> CF node index (bind-local Hungarian assignment, see csref/fit_transform.py)
PIECE_NODE = {
    "Plane032": 46,      # Box001 gun root (main body 4204v)
    "Plane029": 47,      # Box003 reload/cylinder assembly
    "Cylinder024": 48,   # Box007 barrel
    "Object806": 49,     # Box006 barrel
    "Object805": 50,     # Box005 barrel
    "Object804": 51,     # Box004 barrel
    "Object451": 52,     # Box008
    "Object455": 53,     # Box009
}
GUN_ROOT = 46  # Box001 — attachments/extra bones parent here
# pieces near the gun used for $illumposition (bullets excluded: too small)
ILLUM_PIECES = {"Plane032", "Plane029", "Object451", "Object455"}

CS_BONES = (
    ["v_weapon.Bip01", "v_weapon.Bip01_Pelvis", "v_weapon.Bip01_Spine",
     "v_weapon.Bip01_Spine1", "v_weapon.Bip01_Spine2", "v_weapon.Bip01_Spine3",
     "v_weapon.Bip01_Neck"]
    + [f"v_weapon.Bip01_{s}_{b}" for s in ("L", "R") for b in
       ("Clavicle", "UpperArm", "Forearm", "Hand", "ForeTwist")]
    + [f"v_weapon.Bip01_{s}_Finger{f}{x}" for s in ("L", "R")
       for f in range(5) for x in ("", "1", "2")]
)
EXTRA_GUN_BONES = ("v_weapon.glock_Parent", "v_weapon.glock_Slide",
                   "v_weapon.glock_Trigger", "v_weapon.glock_Clip")
ATTACH_BONES = ("v_weapon.flash", "v_weapon.shelleject",
                "v_weapon.stattrack", "v_weapon.uid")

# stock v_pist_glock18 sequence names -> CF clip
CLIP_TO_SEQ = {
    "idle": "idle_0",
    "shoot1": "fire",
    "shoot2": "fire",
    "shoot3": "fire",
    "shoot_empty": "prefire",
    "reload": "reload",
    "draw": "select",
    "lookat01": "idle_0",
}
SEQ_ACT = {
    "idle": "ACT_VM_IDLE",
    "shoot1": "ACT_VM_PRIMARYATTACK",
    "shoot2": "ACT_VM_PRIMARYATTACK",
    "shoot3": "ACT_VM_PRIMARYATTACK",
    "shoot_empty": "ACT_VM_DRYFIRE",
    "reload": "ACT_VM_RELOAD",
    "draw": "ACT_VM_DRAW",
}


def mmul(a, b):
    return [[sum(a[r][k] * b[k][c] for k in range(4)) for c in range(4)] for r in range(4)]


def minv(m):
    n = 4
    aug = [row[:] + [1.0 if i == j else 0.0 for j in range(n)] for i, row in enumerate(m)]
    for col in range(n):
        piv = max(range(col, n), key=lambda r: abs(aug[r][col]))
        aug[col], aug[piv] = aug[piv], aug[col]
        d = aug[col][col]
        aug[col] = [v / d for v in aug[col]]
        for r in range(n):
            if r != col and aug[r][col]:
                f = aug[r][col]
                aug[r] = [v - f * w for v, w in zip(aug[r], aug[col])]
    return [row[n:] for row in aug]


def mapply(m, p):
    return [sum(m[r][c] * p[c] for c in range(3)) + m[r][3] for r in range(3)]


def flat16(m16):
    return [[m16[0], m16[1], m16[2], m16[3]],
            [m16[4], m16[5], m16[6], m16[7]],
            [m16[8], m16[9], m16[10], m16[11]],
            [m16[12], m16[13], m16[14], m16[15]]]


def quat_to_mat(q):
    x, y, z, w = q
    n = math.sqrt(x * x + y * y + z * z + w * w) or 1.0
    x, y, z, w = x / n, y / n, z / n, w / n
    return [
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w), 0.0],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w), 0.0],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y), 0.0],
        [0.0, 0.0, 0.0, 1.0],
    ]


def sample_world(sample, i):
    m = quat_to_mat(sample["quat_xyzw_world"][i])
    m[0][3], m[1][3], m[2][3] = sample["pos"][i]
    return m


def mat_to_euler(m):
    sy = max(-1.0, min(1.0, -m[2][0]))
    ry = math.asin(sy)
    cy = math.cos(ry)
    if abs(cy) > 1e-6:
        rx = math.atan2(m[2][1], m[2][2])
        rz = math.atan2(m[1][0], m[0][0])
    else:
        rx = math.atan2(-m[1][2], m[1][1])
        rz = 0.0
    return rx, ry, rz


def unwrap_euler(e, prev):
    out = []
    for a, p in zip(e, prev):
        while a - p > math.pi:
            a -= 2 * math.pi
        while a - p < -math.pi:
            a += 2 * math.pi
        out.append(a)
    return tuple(out)


def norm3(v):
    l = math.sqrt(sum(c * c for c in v)) or 1.0
    return [c / l for c in v]


def sha256(path: Path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def arm_oil_vmt(name: str) -> str:
    return f'''"VertexLitGeneric"
{{
	"$basetexture" "{MAT_DIR_VMT}/{name}"
	"$bumpmap" "{MAT_DIR_VMT}/{name}_n"
	"$phong" "1"
	"$phongexponent" "5"
	"$phongboost" "1.2"
	"$phongfresnelranges" "[0.15 0.55 1]"
	"$phongalbedotint" "1"
	"$nocull" "0"
}}
'''


def vtfcmd(png: Path, dest: Path, fmt: str, flags: tuple[str, ...] = ()):
    dest.parent.mkdir(parents=True, exist_ok=True)
    cmd = [str(VTFCMD), "-file", str(png), "-output", str(dest.parent),
           "-format", fmt, "-version", "7.4"]
    for fl in flags:
        cmd += ["-flag", fl]
    proc = subprocess.run(
        cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    produced = dest.parent / (png.stem + ".vtf")
    if not produced.is_file():
        raise RuntimeError(f"VTFCmd failed for {png.name}: {proc.stderr or proc.stdout}")
    if produced != dest:
        produced.replace(dest)


def write_qc(illum, seq_frames):
    # events at 100fps frame numbers; CF clip times_ms / 10
    seq_blocks = []
    for seq in CLIP_TO_SEQ:
        act = SEQ_ACT.get(seq)
        extra = ""
        if seq == "idle":
            extra = "\n\tloop"
        elif seq in ("shoot1", "shoot2", "shoot3"):
            extra = ('\n\t{ event 5001 0 "1" }'
                     '\n\t{ event AE_CLIENT_EJECT_BRASS 0 "" }')
        elif seq == "shoot_empty":
            extra = '\n\t{ event 5001 0 "21" }'
        elif seq == "draw":
            # CF select: Extra01SoundName@0ms, clip 400ms -> Draw@2
            extra = '\n\t{ event 5004 2 "Weapon_Glock.Draw" }'
        elif seq == "reload":
            # CF reload: ClipOut@172ms, ClipIn@1084ms, WeaponReload@1281ms
            extra = ('\n\t{ event 5004 17 "Weapon_Glock.Clipout" }'
                     '\n\t{ event 5004 108 "Weapon_Glock.Clipin" }'
                     '\n\t{ event 5004 128 "Weapon_Glock.Sliderelease" }'
                     '\n\t{ event AE_WPN_COMPLETE_RELOAD 128 "" }')
        elif seq == "lookat01":
            extra = ('\n\t{ event 5004 2 "Weapon.WeaponMove1" }'
                     '\n\t{ event 5004 175 "Weapon.WeaponMove3" }')
        act_line = f'\n\tactivity "{act}" 1' if act else ""
        seq_blocks.append(f'''$sequence "{seq}" {{
	"v_pist_glock18_anims\\{seq}.smd"{act_line}{extra}
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}}
''')
    qc = f'''$modelname "weapons\\v_pist_glock18.mdl"

$bodygroup "studio"
{{
	studio "cf_native_vm.smd"
}}

$surfaceprop "default"
$contents "solid"
$illumposition {illum[0]:.3f} {illum[1]:.3f} {illum[2]:.3f}
$cdmaterials "{MAT_DIR_VMT}\\"

$attachment "1" "v_weapon.flash" 0 0 0 rotate 0 0 0
$attachment "2" "v_weapon.shelleject" 0 0 0 rotate 0 0 0

$cbox 0 0 0 0 0 0
$bbox -30 -30 -30 30 30 30

$bonemerge "v_weapon"
''' + "\n".join(f'$bonemerge "{n}"' for n in EXTRA_GUN_BONES) + "\n" \
        + "\n".join(f'$bonemerge "{n}"' for n in CS_BONES) + "\n" \
        + "\n".join(f'$bonemerge "{n}"' for n in ATTACH_BONES) + '''

$animblocksize 32 nostall

''' + "\n".join(seq_blocks)
    (SOURCE1 / "v_pist_glock18.qc").write_text(qc, encoding="utf-8")


def build_materials():
    mat_dir = ISOLATED / "materials" / MAT_DIR_VMT
    mat_dir.mkdir(parents=True, exist_ok=True)
    if V2:
        for source in V2_DIR.glob("*.vmt"):
            shutil.copy2(source, mat_dir / source.name)
        for source in V2_DIR.glob("*.vtf"):
            shutil.copy2(source, mat_dir / source.name)
    else:
        v7_dir = STAGING / "materials" / MAT_DIR_VMT
        for source in v7_dir.glob(GUN_MAT + "*"):
            shutil.copy2(source, mat_dir / source.name)

    def arm_diffuse(stem: str) -> Path:
        hd = ARMTEX / "up" / f"4x_{stem}.png"
        return hd if hd.is_file() else ARMTEX / f"{stem}.png"

    filt = ("TRILINEAR", "ANISOTROPIC")
    hand_dif = arm_diffuse("FVIEW_HAND_Nini_GR")
    arm_dif = arm_diffuse("FVIEW_ARM_Nini_GR")
    vtfcmd(hand_dif, mat_dir / "cf_nini_hand_gr.vtf",
           "bgra8888" if "4x_" in hand_dif.name else "dxt1", filt)
    vtfcmd(arm_dif, mat_dir / "cf_nini_arm_gr.vtf",
           "bgra8888" if "4x_" in arm_dif.name else "dxt1", filt)
    vtfcmd(ARMTEX / "FVIEW_HAND_Nini_GR_N.PNG", mat_dir / "cf_nini_hand_gr_n.vtf",
           "dxt5", filt + ("NORMAL",))
    vtfcmd(ARMTEX / "FVIEW_ARM_Nini_GR_N.PNG", mat_dir / "cf_nini_arm_gr_n.vtf",
           "dxt5", filt + ("NORMAL",))
    for name in ("cf_nini_hand_gr", "cf_nini_arm_gr"):
        (mat_dir / f"{name}.vmt").write_text(arm_oil_vmt(name), encoding="utf-8")


def compile_models():
    shutil.copy2(GAME / "csgo" / "gameinfo.txt", ISOLATED / "gameinfo.txt")
    proc = subprocess.run(
        [str(STUDIOMDL), "-game", str(ISOLATED), str(SOURCE1 / "v_pist_glock18.qc")],
        cwd=str(SOURCE1), capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=300)
    (LOG_DIR / "studiomdl_v_pist_glock18.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "studiomdl_v_pist_glock18.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    compiled = ISOLATED / "models" / "weapons" / "v_pist_glock18.mdl"
    if proc.returncode != 0 or not compiled.is_file():
        raise RuntimeError(
            f"studiomdl failed: {(proc.stderr or proc.stdout or '')[-1500:]}")
    print("[cop357] compiled", compiled)


def stage_and_deploy():
    staging = STAGING_V2 if V2 else STAGING
    models_rel = Path("models/weapons")
    mats_rel = Path("materials") / MAT_DIR_VMT
    stage_models = staging / models_rel
    stage_models.mkdir(parents=True, exist_ok=True)
    for f in (ISOLATED / models_rel).glob("v_pist_glock18.*"):
        shutil.copy2(f, stage_models / f.name)
    stage_mats = staging / mats_rel
    stage_mats.mkdir(parents=True, exist_ok=True)
    for f in (ISOLATED / mats_rel).glob("*"):
        shutil.copy2(f, stage_mats / f.name)
    if V2:
        if (STAGING / "sound").is_dir():
            for f in (STAGING / "sound").rglob("*.wav"):
                rel = f.relative_to(STAGING)
                dst = staging / rel
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dst)
        staged = {p.relative_to(staging).as_posix(): p
                  for p in staging.rglob("*") if p.is_file()}
        isolated = {p.relative_to(ISOLATED).as_posix(): p
                    for p in ISOLATED.rglob("*") if p.is_file()
                    and p.suffix in (".mdl", ".vvd", ".vtx", ".vtf", ".vmt",
                                     ".phy", ".ani")}
        mismatch = sorted(rel for rel in isolated.keys() & staged.keys()
                          if sha256(staged[rel]) != sha256(isolated[rel]))
        if mismatch:
            raise RuntimeError(f"v2 staging mismatch: {mismatch}")
        print(f"[cop357] v2 staged {len(staged)} files -> {staging}")
        print("[cop357] v2 MIGI deploy deferred to Phase I")
        return
    target = DEPLOY_ADDON
    for f in stage_models.glob("*"):
        dst = target / models_rel / f.name
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, dst)
    tgt_mats = target / mats_rel
    tgt_mats.mkdir(parents=True, exist_ok=True)
    for f in stage_mats.glob("*"):
        shutil.copy2(f, tgt_mats / f.name)
    if (STAGING / "sound").is_dir():
        for f in (STAGING / "sound").rglob("*.wav"):
            rel = f.relative_to(STAGING)
            dst = target / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(f, dst)
    staged = {p.relative_to(STAGING).as_posix(): p for p in STAGING.rglob("*") if p.is_file()}
    deployed = {p.relative_to(target).as_posix(): p for p in target.rglob("*") if p.is_file()}
    missing = sorted(staged.keys() - deployed.keys())
    extra = sorted(deployed.keys() - staged.keys())
    mismatch = sorted(rel for rel in staged.keys() & deployed.keys()
                      if sha256(staged[rel]) != sha256(deployed[rel]))
    if missing or extra or mismatch:
        raise RuntimeError(f"A/B deploy mismatch: missing={missing}, extra={extra}, mismatch={mismatch}")
    print(f"[cop357] A/B SHA-256 equal: {len(staged)}/{len(staged)} files")
    print(f"[cop357] deployed into {target}")


def main() -> int:
    for d in (SOURCE1, ANIMS, ISOLATED, STAGING, LOG_DIR):
        d.mkdir(parents=True, exist_ok=True)

    payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))
    skin = json.loads(SKIN.read_text(encoding="utf-8"))
    v2_assign = (json.loads(V2_ASSIGN.read_text(encoding="utf-8"))
                 if V2 else {})
    armdump = json.loads(ARMDUMP.read_text(encoding="utf-8"))
    vt = json.loads(VM_TRANSFORM.read_text(encoding="utf-8"))

    hs = vt["H"]["scale"]
    HR = vt["H"]["rotation"]
    HT = vt["H"]["translation"]
    H = [[HR[r][c] * hs for c in range(3)] + [HT[r]] for r in range(3)] \
        + [[0, 0, 0, 1.0]]
    HINV = minv(H)
    GUN_XC = float(vt.get("gun_center_x", 0.0))
    APPLY_MIRROR = bool(vt.get("apply_mirror", True))
    if APPLY_MIRROR:
        MX = [[-1.0, 0, 0, 2 * GUN_XC], [0, 1.0, 0, 0], [0, 0, 1.0, 0],
              [0, 0, 0, 1.0]]
        MXR = [[-1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
    else:
        MX = [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0],
              [0, 0, 0, 1.0]]
        MXR = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
    VIEW_PUSH_X = float(vt.get("view_push_x", 0.0))
    VIEW_PUSH_Y = float(vt.get("view_push_y", 0.0))
    VIEW_PUSH_Z = float(vt.get("view_push_z", 0.0))
    VIEW_ROLL_DEG = float(vt.get("view_roll_deg", 0.0))
    rad = math.radians(VIEW_ROLL_DEG)
    cr, sr = math.cos(rad), math.sin(rad)
    ROLL = [[cr, 0.0, sr, 0.0], [0.0, 1.0, 0.0, 0.0], [-sr, 0.0, cr, 0.0],
            [0.0, 0.0, 0.0, 1.0]]
    PUSH = [[1.0, 0, 0, VIEW_PUSH_X], [0, 1.0, 0, VIEW_PUSH_Y],
            [0, 0, 1.0, VIEW_PUSH_Z], [0, 0, 0, 1.0]]
    _vmat = vt.get("view_matrix")
    VIEW = mmul(PUSH, mmul(ROLL, _vmat)) if _vmat else mmul(PUSH, ROLL)
    ARM_OFF = {"FvARM-bone L ": [float(c) for c in vt.get("arm_offset_l", [0, 0, 0])],
               "FvARM-bone R ": [float(c) for c in vt.get("arm_offset_r", [0, 0, 0])]}
    ARM_ANCHOR = {"FvARM-bone L Clavicle", "FvARM-bone R Clavicle"}
    # Prop1 must NOT take arm mods: the gun chain stays at the VIEW fit while
    # the arm chain gets its own IK swing (fit_view.py P3c)
    ARM_WEAPON: set = set()
    ARM_PIVOT = [float(c) for c in vt.get("arm_pivot", [0, 0, 0])]
    ARM_ROT_L_AXIS = [float(c) for c in vt.get("arm_rot_l_axis", [0, 1, 0])]
    ARM_ROT_L_DEG = float(vt.get("arm_rot_l_deg", 0.0))
    ARM_ROT_R_AXIS = [float(c) for c in vt.get("arm_rot_r_axis", [0, 1, 0])]
    ARM_ROT_R_DEG = float(vt.get("arm_rot_r_deg", 0.0))

    def rot_axis(axis, deg):
        ax = norm3(axis)
        t = math.radians(deg)
        ct, st = math.cos(t), math.sin(t)
        k = [[0.0, -ax[2], ax[1]], [ax[2], 0.0, -ax[0]], [-ax[1], ax[0], 0.0]]
        return [[(ct if i == j else 0.0) + (1 - ct) * ax[i] * ax[j]
                 + st * k[i][j] for j in range(3)] for i in range(3)]

    def arm_mod(off, axis, deg):
        r = rot_axis(axis, deg)
        t = [off[i] + ARM_PIVOT[i]
             - sum(r[i][k] * ARM_PIVOT[k] for k in range(3))
             for i in range(3)]
        return [[r[i][j] for j in range(3)] + [t[i]]
                for i in range(3)] + [[0.0, 0.0, 0.0, 1.0]]

    ARM_MOD_L = arm_mod(ARM_OFF["FvARM-bone L "], ARM_ROT_L_AXIS, ARM_ROT_L_DEG)
    ARM_MOD_R = arm_mod(ARM_OFF["FvARM-bone R "], ARM_ROT_R_AXIS, ARM_ROT_R_DEG)

    def arm_off(i):
        nm = nodes[i]["name"]
        if nm in ARM_ANCHOR:
            return None
        if nm in ARM_WEAPON:
            return ARM_MOD_R
        if nm.startswith("FvARM-bone L "):
            return ARM_MOD_L
        if nm.startswith("FvARM-bone R "):
            return ARM_MOD_R
        return None
    print(f"[cop357] apply_mirror={APPLY_MIRROR} gun_center_x={GUN_XC:.4f} "
          f"push=({VIEW_PUSH_X:.3f},{VIEW_PUSH_Y:.3f},{VIEW_PUSH_Z:.3f}) "
          f"roll={VIEW_ROLL_DEG:.1f} view_matrix={_vmat is not None}")
    I = [[1.0, 0, 0, 0], [0, 1.0, 0, 0], [0, 0, 1.0, 0], [0, 0, 0, 1.0]]
    MXH = mmul(VIEW, mmul(MX, H))
    FAR = [[1.0, 0, 0, 0.0], [0, 1.0, 0, 500.0], [0, 0, 1.0, 0.0],
           [0, 0, 0, 1.0]]

    def rest_world(b):
        return mmul(VIEW, mmul(MX, mmul(mmul(H, mmul(b, HINV)), MX)))

    def anim_world(wcf):
        return mmul(VIEW, mmul(MX, mmul(mmul(H, mmul(wcf, HINV)), MX)))

    def mir_attach(w):
        r = [[sum(MXR[i][k] * w[k][j] for k in range(3)) for j in range(3)]
             for i in range(3)]
        r = [[sum(r[i][k] * MXR[k][j] for k in range(3)) for j in range(3)]
             for i in range(3)]
        p = mapply(VIEW, mapply(MX, [w[0][3], w[1][3], w[2][3]]))
        return [r[0] + [p[0]], r[1] + [p[1]], r[2] + [p[2]], [0, 0, 0, 1.0]]

    nodes = payload["nodes"]
    B = {n["index"]: n["bind_world"] for n in nodes}
    parent_cf = {n["index"]: n["parent"] for n in nodes}
    name2idx = {n["name"]: n["index"] for n in nodes}
    BARM = {name2idx[n["name"]]: flat16(n["bind_matrix"]) for n in armdump["skeleton"]
            if n["name"] in name2idx}
    BARM_INV = {i: minv(m) for i, m in BARM.items()}

    attach_targets = vt["attach_worlds_p6"]
    clips_by_name = payload["clips"]
    W_gun0 = anim_world(sample_world(clips_by_name["idle_0"]["samples"][0], GUN_ROOT))
    attach_offsets = {}
    for bname in ATTACH_BONES:
        attach_offsets[bname] = mmul(minv(W_gun0), mir_attach(attach_targets[bname]))

    smd_nodes: list[tuple[str, int]] = [("v_weapon", -1)]
    smd_nodes += [(n, 0) for n in CS_BONES]
    cf_node_ids = [n["index"] for n in nodes if n["index"] != 0]
    cf_to_smd = {}
    for i in cf_node_ids:
        p = parent_cf[i]
        smd_parent = 0 if p <= 0 else cf_to_smd[p]
        cf_to_smd[i] = len(smd_nodes)
        smd_nodes.append((nodes[i]["name"], smd_parent))
    gun_smd = cf_to_smd[GUN_ROOT]
    attach_base = len(smd_nodes)
    for bname in ATTACH_BONES + EXTRA_GUN_BONES:
        smd_nodes.append((bname, gun_smd))

    nbones = len(smd_nodes)
    print(f"[cop357] bones={nbones} (1+{len(CS_BONES)} cs + {len(cf_node_ids)} cf + "
          f"{len(ATTACH_BONES)} attach + {len(EXTRA_GUN_BONES)} extra)")

    ref_world = [I] * nbones
    for i in range(1, 1 + len(CS_BONES)):
        ref_world[i] = FAR
    for i in cf_node_ids:
        ref_world[cf_to_smd[i]] = rest_world(B[i])
    for k, bname in enumerate(ATTACH_BONES):
        ref_world[attach_base + k] = mmul(ref_world[gun_smd], attach_offsets[bname])
    for k in range(len(EXTRA_GUN_BONES)):
        ref_world[attach_base + len(ATTACH_BONES) + k] = ref_world[gun_smd]

    def locals_of(worlds):
        out = []
        for i, (name, p) in enumerate(smd_nodes):
            w = worlds[i]
            out.append(mmul(minv(worlds[p]), w) if p >= 0 else w)
        return out

    def write_nodes(f):
        f.write("version 1\nnodes\n")
        for i, (name, p) in enumerate(smd_nodes):
            f.write(f'  {i} "{name}" {p}\n')
        f.write("end\n")

    def write_frame(f, t, worlds, prev_e):
        f.write(f"  time {t}\n")
        for i, loc in enumerate(locals_of(worlds)):
            e = mat_to_euler(loc)
            if prev_e[i] is not None:
                e = unwrap_euler(e, prev_e[i])
            prev_e[i] = e
            x, y, z = loc[0][3], loc[1][3], loc[2][3]
            f.write(f"    {i} {x:.6f} {y:.6f} {z:.6f} {e[0]:.6f} {e[1]:.6f} {e[2]:.6f}\n")

    verts: list[tuple] = []
    tris: list[tuple[str, list]] = []
    nmap: dict[int, list[float]] = {}
    illum_pts: list[list[float]] = []

    def add_vert(pos, uv, links):
        verts.append((pos, uv, links))
        return len(verts) - 1

    # rigid CF pieces: verts are bind-world -> MXH, single link to their node
    for m in skin["meshes"]:
        ni = PIECE_NODE.get(m["name"])
        if ni is None:
            continue
        ids = []
        for vi in range(m["vertex_count"]):
            p = mapply(MXH, m["vertices"][3 * vi:3 * vi + 3])
            u, v = m["uvs"][2 * vi:2 * vi + 2]
            ids.append(add_vert(p, (u, 1.0 - v), [(cf_to_smd[ni], 1.0)]))
            if m["name"] in ILLUM_PIECES:
                illum_pts.append(p)
        for t in range(0, len(m["triangles"]), 3):
            a, b, c = m["triangles"][t:t + 3]
            order = [ids[a], ids[c], ids[b]] if APPLY_MIRROR else [ids[a], ids[b], ids[c]]
            matname = GUN_MAT
            if V2:
                matname = v2_assign.get(m["name"], {}).get(str(t // 3), GUN_MAT)
            tris.append((matname, order))
        print(f"[cop357] piece {m['name']}: {m['vertex_count']}v -> node {ni} "
              f"({nodes[ni]['name']})")

    arm_names = [n["name"] for n in armdump["skeleton"]]
    unmatched_bones = set()
    for m in armdump["meshes"]:
        matname = "cf_nini_hand_gr" if "HAND" in m["name"].upper() else "cf_nini_arm_gr"
        bw, bi = m["bone_weights"], m["bone_indices"]
        ids = []
        for vi in range(m["vertex_count"]):
            v = m["vertices"][3 * vi:3 * vi + 3]
            w0, w1, w2 = bw[3 * vi:3 * vi + 3]
            w3 = max(0.0, 1.0 - w0 - w1 - w2)
            acc = [0.0, 0.0, 0.0]
            links = []
            for ni, w in zip(bi[4 * vi:4 * vi + 4], (w0, w1, w2, w3)):
                if ni == 255 or ni >= len(arm_names) or w <= 1e-6:
                    continue
                aname = arm_names[ni]
                if aname not in name2idx or name2idx[aname] not in BARM_INV:
                    unmatched_bones.add(aname)
                    continue
                pidx = name2idx[aname]
                repose = mmul(B[pidx], BARM_INV[pidx])
                pt = mapply(repose, v)
                for c in range(3):
                    acc[c] += w * pt[c]
                links.append((cf_to_smd[pidx], w))
            if not links:
                links = [(cf_to_smd[GUN_ROOT], 1.0)]
            p = mapply(MXH, acc)
            illum_pts.append(p)
            ids.append(add_vert(p,
                                (m["uvs"][2 * vi], 1.0 - m["uvs"][2 * vi + 1]), links))
        for t in range(0, len(m["triangles"]), 3):
            a, b, c = m["triangles"][t:t + 3]
            order = [ids[a], ids[c], ids[b]] if APPLY_MIRROR else [ids[a], ids[b], ids[c]]
            tris.append((matname, order))
        print(f"[cop357] arm mesh {m['name']}: {m['vertex_count']} verts -> {matname}")
    if unmatched_bones:
        print("[cop357] unmatched arm bones skipped:", sorted(unmatched_bones))

    for _mat, tri in tris:
        p0, p1, p2 = (verts[i][0] for i in tri)
        u = [p1[c] - p0[c] for c in range(3)]
        v = [p2[c] - p0[c] for c in range(3)]
        fn = norm3([u[1] * v[2] - u[2] * v[1],
                    u[2] * v[0] - u[0] * v[2],
                    u[0] * v[1] - u[1] * v[0]])
        for i in tri:
            nmap.setdefault(i, [0.0, 0.0, 0.0])
            for c in range(3):
                nmap[i][c] += fn[c]
    norms = {i: norm3(n) for i, n in nmap.items()}

    model_smd = SOURCE1 / "cf_native_vm.smd"
    with model_smd.open("w", encoding="utf-8") as f:
        write_nodes(f)
        f.write("skeleton\n")
        write_frame(f, 0, ref_world, [None] * nbones)
        f.write("end\ntriangles\n")
        for mat, tri in tris:
            f.write(mat + "\n")
            for i in tri:
                pos, uv, links = verts[i]
                n = norms[i]
                ls = " ".join(f"{b} {w:.6f}" for b, w in links)
                f.write(f"  {links[0][0]} {pos[0]:.6f} {pos[1]:.6f} {pos[2]:.6f} "
                        f"{n[0]:.6f} {n[1]:.6f} {n[2]:.6f} {uv[0]:.6f} {uv[1]:.6f} "
                        f"{len(links)} {ls}\n")

    xs = [p[0] for p in illum_pts]
    ys = [p[1] for p in illum_pts]
    zs = [p[2] for p in illum_pts]
    illum = [(min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2, (min(zs) + max(zs)) / 2]
    print(f"[cop357] illumposition {illum}")

    seq_frames = {}
    for seq, clip in CLIP_TO_SEQ.items():
        out = ANIMS / f"{seq}.smd"
        samples = clips_by_name[clip]["samples"]
        with out.open("w", encoding="utf-8") as f:
            write_nodes(f)
            f.write("skeleton\n")
            prev_e = [None] * nbones
            for ti, s in enumerate(samples):
                w = [I] * nbones
                for i in range(1, 1 + len(CS_BONES)):
                    w[i] = FAR
                for i in cf_node_ids:
                    wm = anim_world(sample_world(s, i))
                    mod = arm_off(i)
                    if mod is not None:
                        wm = mmul(mod, wm)
                    w[cf_to_smd[i]] = wm
                for k, off in enumerate(attach_offsets.values()):
                    w[attach_base + k] = mmul(w[gun_smd], off)
                for k in range(len(EXTRA_GUN_BONES)):
                    w[attach_base + len(ATTACH_BONES) + k] = w[gun_smd]
                write_frame(f, ti, w, prev_e)
            f.write("end\n")
        seq_frames[seq] = len(samples)
        print(f"[cop357] anim {seq} <- {clip} frames={len(samples)}")

    write_qc(illum, seq_frames)
    build_materials()
    compile_models()
    stage_and_deploy()
    print("[cop357] DONE")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
