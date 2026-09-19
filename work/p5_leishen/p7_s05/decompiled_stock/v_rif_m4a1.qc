// Created by CrowbarDecompiler 0.71

$modelname "weapons\v_rif_m4a1.mdl"

$bodygroup "studio"
{
	studio "PV-M4A1-BornBeast.smd"
}
$bodygroup "studio"
{
	studio "csgo_hands.smd"
}


$surfaceprop "default"

$contents "solid"

$illumposition 16.4 -2.125 -8.448

$cdmaterials "models\v_models\weapons\m4a1_bornbeast\"
$cdmaterials "models\weapons\v_models\rif_m4a1\"

$texturegroup "skinfamilies"
{
	{ "fview-hand2" }
}

$attachment "1" "muzzle" 0 0 0 rotate 0 0 0
$attachment "2" "shell" 0 0 0 rotate 0 0 0

$cbox 0 0 0 0 0 0

$bbox -10.001 -15.121 -31.77 55.806 11.152 5

$definebone "Scene Root" "" 0 -7.179676 11.100285 -0.000057 179.999964 -89.999982 0 0 0 0 0 0
$definebone "bone_Weapon" "Scene Root" -5.22428 13.74905 -11.345901 0 -179.999978 -179.999978 0 0 0 0 0 0
$definebone "bone_Weapon_Main" "bone_Weapon" -0.248215 -3.990622 28.963835 0 0 0 0 0 0 0 0 0
$definebone "muzzle" "bone_Weapon" -0.208309 -3.980618 28.661356 -89.111784 -0.000688 90.000897 0 0 0 0 0 0
$definebone "shell" "bone_Weapon" 0.787082 -4.457595 13.090944 -3.279611 -16.534645 91.236765 0 0 0 0 0 0


$sectionframes 30 30

$sequence "idle" {
	"v_rif_m4a1_anims\idle.smd"
	activity "ACT_VM_IDLE" 1
	fadein 0.2
	fadeout 0.2
	fps 30
	loop
}

$sequence "fire1" {
	"v_rif_m4a1_anims\fire1.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 20
}

$sequence "fire2" {
	"v_rif_m4a1_anims\fire2.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 20
}

$sequence "fire3" {
	"v_rif_m4a1_anims\fire3.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 20
}

$sequence "draw" {
	"v_rif_m4a1_anims\draw.smd"
	activity "ACT_VM_DRAW" 1
	{ event 5004 1 "Weapon_M4A1.Draw" }
	fadein 0.2
	fadeout 0.2
	snap
	fps 30
}

$sequence "reload" {
	"v_rif_m4a1_anims\reload.smd"
	activity "ACT_VM_RELOAD" 1
	{ event 5004 19 "Weapon_M4A1.Clipout" }
	{ event 5004 37 "Weapon_M4A1.Clipin" }
	{ event 5004 54 "Weapon_M4A1.BoltPull" }
	{ event AE_WPN_COMPLETE_RELOAD 35 "" }
	fadein 0.2
	fadeout 0.2
	fps 30
}

$keyvalues
{
	qc_path 
	{
		"value"		"d:\project\cf_to_csgo\data\out\decompiled_m4a1_bornbeast\v_rif_m4a1.qc"
	}
}
