$modelname "weapons\v_rif_galilar.mdl"

$bodygroup "studio"
{
	studio "cf_native_vm.smd"
}

$surfaceprop "default"
$contents "solid"
$illumposition -0.026 14.559 18.234
$cdmaterials "models\weapons\v_models\rif_galilar\"
$cdmaterials "models/weapons/v_models/cf_tianxi\"

$attachment "1" "v_weapon.flash" 0 0 0 rotate 0 0 0
$attachment "2" "v_weapon.shelleject" 0 0 0 rotate 0 0 0
$attachment "stattrack" "v_weapon.stattrack" 0 0 0 rotate 0 0 0
$attachment "uid" "v_weapon.uid" 0 0 0 rotate 0 0 0

$cbox 0 0 0 0 0 0
$bbox -30 -30 -30 30 30 30

$bonemerge "v_weapon"
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
$bonemerge "v_weapon.galilar_parent"
$bonemerge "v_weapon.stattrack"
$bonemerge "v_weapon.uid"

$animblocksize 32 nostall

$sequence "idle" {
	"v_rif_galilar_anims\idle.smd"
	activity "ACT_VM_IDLE" 1
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "fire1" {
	"v_rif_galilar_anims\fire1.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "fire2" {
	"v_rif_galilar_anims\fire2.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "fire3" {
	"v_rif_galilar_anims\fire3.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "reload" {
	"v_rif_galilar_anims\reload.smd"
	activity "ACT_VM_RELOAD" 1
	{ event 5004 33 "Weapon_GalilAR.Clipout" }
	{ event 5004 117 "Weapon_GalilAR.Clipin" }
	{ event 5004 140 "Weapon_GalilAR.BoltBack" }
	{ event 5004 160 "Weapon_GalilAR.BoltForward" }
	{ event AE_WPN_COMPLETE_RELOAD 120 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "draw" {
	"v_rif_galilar_anims\draw.smd"
	activity "ACT_VM_DRAW" 1
	{ event 5004 3 "Weapon_GalilAR.Draw" }
	{ event 5004 45 "Weapon_GalilAR.BoltBack" }
	{ event 5004 58 "Weapon_GalilAR.BoltForward" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 100
}

$sequence "lookat01" {
	"v_rif_galilar_anims\lookat01.smd"
	{ event 5004 7 "Weapon_GalilAR.WeaponMove1" }
	{ event 5004 43 "Weapon_GalilAR.WeaponMove2" }
	{ event 5004 100 "Weapon_GalilAR.WeaponMove3" }
	{ event 5004 203 "Weapon_GalilAR.WeaponMove1" }
	{ event 5004 377 "Weapon_GalilAR.WeaponMove2" }
	{ event 5004 473 "Weapon_GalilAR.WeaponMove3" }
	fadein 0.3
	fadeout 0.3
	fps 100
}

$sequence "lookat01_prepare" {
	"v_rif_galilar_anims\lookat01_prepare.smd"
	fadein 0.2
	fadeout 0.2
	fps 100
}

$sequence "lookat01_loop" {
	"v_rif_galilar_anims\lookat01_loop.smd"
	fadein 0.2
	fadeout 0.2
	fps 100
}
