$modelname "weapons\v_pist_glock18.mdl"

$bodygroup "studio"
{
	studio "cf_native_vm.smd"
}

$surfaceprop "default"
$contents "solid"
$illumposition 2.223 -11.416 23.102
$cdmaterials "models/weapons/v_models/cf_cop357\"

$attachment "1" "v_weapon.flash" 0 0 0 rotate 0 0 0
$attachment "2" "v_weapon.shelleject" 0 0 0 rotate 0 0 0

$cbox 0 0 0 0 0 0
$bbox -30 -30 -30 30 30 30

$bonemerge "v_weapon"
$bonemerge "v_weapon.glock_Parent"
$bonemerge "v_weapon.glock_Slide"
$bonemerge "v_weapon.glock_Trigger"
$bonemerge "v_weapon.glock_Clip"
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
$bonemerge "v_weapon.flash"
$bonemerge "v_weapon.shelleject"
$bonemerge "v_weapon.stattrack"
$bonemerge "v_weapon.uid"

$animblocksize 32 nostall

$sequence "idle" {
	"v_pist_glock18_anims\idle.smd"
	activity "ACT_VM_IDLE" 1
	loop
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "shoot1" {
	"v_pist_glock18_anims\shoot1.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "shoot2" {
	"v_pist_glock18_anims\shoot2.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "shoot3" {
	"v_pist_glock18_anims\shoot3.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "shoot_empty" {
	"v_pist_glock18_anims\shoot_empty.smd"
	activity "ACT_VM_DRYFIRE" 1
	{ event 5001 0 "21" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "reload" {
	"v_pist_glock18_anims\reload.smd"
	activity "ACT_VM_RELOAD" 1
	{ event 5004 17 "Weapon_glock18.Clipout" }
	{ event 5004 108 "Weapon_glock18.Clipin" }
	{ event AE_WPN_COMPLETE_RELOAD 128 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "draw" {
	"v_pist_glock18_anims\draw.smd"
	activity "ACT_VM_DRAW" 1
	{ event 5004 2 "Weapon_glock18.Draw" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "lookat01" {
	"v_pist_glock18_anims\lookat01.smd"
	{ event 5004 2 "Weapon.WeaponMove1" }
	{ event 5004 175 "Weapon.WeaponMove3" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}
