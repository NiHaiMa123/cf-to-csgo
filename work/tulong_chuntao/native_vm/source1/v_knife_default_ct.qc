$modelname "weapons\v_knife_default_ct.mdl"

$bodygroup "studio"
{
	studio "cf_native_vm.smd"
}

$surfaceprop "default"
$contents "solid"
$illumposition 8.740 -8.614 16.941
$cdmaterials "models/weapons/v_models/cf_tulong\"

$attachment "uid" "v_weapon.uid" 0 0 0 rotate 0 0 0

$cbox 0 0 0 0 0 0
$bbox -30 -30 -30 30 30 30

$bonemerge "v_weapon"
$bonemerge "v_weapon.knife"
$bonemerge "v_weapon.Bip01"
$bonemerge "v_weapon.Bip01_Pelvis"
$bonemerge "v_weapon.Bip01_Spine"
$bonemerge "v_weapon.Bip01_Spine1"
$bonemerge "v_weapon.Bip01_Spine2"
$bonemerge "v_weapon.Bip01_Spine3"
$bonemerge "v_weapon.Bip01_Neck"
$bonemerge "v_weapon.Bip01_L_Clavicle"
$bonemerge "v_weapon.Bip01_L_UpperArm"
$bonemerge "v_weapon.Bip01_L_Forearm"
$bonemerge "v_weapon.Bip01_L_Hand"
$bonemerge "v_weapon.Bip01_L_ForeTwist"
$bonemerge "v_weapon.Bip01_R_Clavicle"
$bonemerge "v_weapon.Bip01_R_UpperArm"
$bonemerge "v_weapon.Bip01_R_Forearm"
$bonemerge "v_weapon.Bip01_R_Hand"
$bonemerge "v_weapon.Bip01_R_ForeTwist"
$bonemerge "v_weapon.Bip01_L_Finger0"
$bonemerge "v_weapon.Bip01_L_Finger01"
$bonemerge "v_weapon.Bip01_L_Finger02"
$bonemerge "v_weapon.Bip01_L_Finger1"
$bonemerge "v_weapon.Bip01_L_Finger11"
$bonemerge "v_weapon.Bip01_L_Finger12"
$bonemerge "v_weapon.Bip01_L_Finger2"
$bonemerge "v_weapon.Bip01_L_Finger21"
$bonemerge "v_weapon.Bip01_L_Finger22"
$bonemerge "v_weapon.Bip01_L_Finger3"
$bonemerge "v_weapon.Bip01_L_Finger31"
$bonemerge "v_weapon.Bip01_L_Finger32"
$bonemerge "v_weapon.Bip01_L_Finger4"
$bonemerge "v_weapon.Bip01_L_Finger41"
$bonemerge "v_weapon.Bip01_L_Finger42"
$bonemerge "v_weapon.Bip01_R_Finger0"
$bonemerge "v_weapon.Bip01_R_Finger01"
$bonemerge "v_weapon.Bip01_R_Finger02"
$bonemerge "v_weapon.Bip01_R_Finger1"
$bonemerge "v_weapon.Bip01_R_Finger11"
$bonemerge "v_weapon.Bip01_R_Finger12"
$bonemerge "v_weapon.Bip01_R_Finger2"
$bonemerge "v_weapon.Bip01_R_Finger21"
$bonemerge "v_weapon.Bip01_R_Finger22"
$bonemerge "v_weapon.Bip01_R_Finger3"
$bonemerge "v_weapon.Bip01_R_Finger31"
$bonemerge "v_weapon.Bip01_R_Finger32"
$bonemerge "v_weapon.Bip01_R_Finger4"
$bonemerge "v_weapon.Bip01_R_Finger41"
$bonemerge "v_weapon.Bip01_R_Finger42"
$bonemerge "v_weapon.uid"

$animblocksize 32 nostall

$sequence "draw" {
	"v_knife_anims\draw.smd"
	activity "ACT_VM_DRAW" 1
	{ event 5004 13 "Weapon_Knife.Deploy" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "idle1" {
	"v_knife_anims\idle1.smd"
	activity "ACT_VM_IDLE" 1
	loop
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "idle2" {
	"v_knife_anims\idle2.smd"
	activity "ACT_VM_IDLE" 1
	loop
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "light_miss1" {
	"v_knife_anims\light_miss1.smd"
	activity "ACT_VM_MISSCENTER" 1
	{ event 5004 20 "Knife.Ursus.Flip.01" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "light_miss2" {
	"v_knife_anims\light_miss2.smd"
	activity "ACT_VM_MISSCENTER" 1
	{ event 5004 23 "Knife.Ursus.Flip.02" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "light_hit1" {
	"v_knife_anims\light_hit1.smd"
	activity "ACT_VM_HITCENTER" 1
	{ event 5004 20 "Knife.Ursus.Flip.01" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "light_hit2" {
	"v_knife_anims\light_hit2.smd"
	activity "ACT_VM_HITCENTER" 1
	{ event 5004 23 "Knife.Ursus.Flip.02" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "light_backstab" {
	"v_knife_anims\light_backstab.smd"
	activity "ACT_VM_SWINGHIT" 1
	{ event 5004 20 "Knife.Ursus.Flip.01" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "light_backstab2" {
	"v_knife_anims\light_backstab2.smd"
	activity "ACT_VM_SWINGHIT" 1
	{ event 5004 23 "Knife.Ursus.Flip.02" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "heavy_miss1" {
	"v_knife_anims\heavy_miss1.smd"
	activity "ACT_VM_MISSCENTER2" 1
	{ event 5004 7 "Knife.Ursus.Flip.03" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "heavy_hit1" {
	"v_knife_anims\heavy_hit1.smd"
	activity "ACT_VM_HITCENTER2" 1
	{ event 5004 7 "Knife.Ursus.Flip.03" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "heavy_backstab" {
	"v_knife_anims\heavy_backstab.smd"
	activity "ACT_VM_SWINGHARD" 1
	{ event 5004 7 "Knife.Ursus.Flip.03" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "lookat01" {
	"v_knife_anims\lookat01.smd"
	{ event 5004 2 "Weapon.WeaponMove1" }
	fadein 0.2
	fadeout 0.2
	fps 100
}
