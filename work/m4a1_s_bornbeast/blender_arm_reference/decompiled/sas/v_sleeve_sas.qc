// Created by CrowbarDecompiler 0.71

$modelname "weapons/v_models/arms/sas/v_sleeve_sas.mdl"

$bodygroup "sleeve"
{
	studio "v_sleeve_ct.smd"
}


$surfaceprop "default"

$contents "solid"

$illumposition 0 10.302 -1.483

$cdmaterials "models\weapons\v_models\arms\sas\"
$cdmaterials ""

$texturegroup "skinfamilies"
{
	{ "sleeve_sas" }
}

$cbox 0 0 0 0 0 0

$bbox -20.603 -24.832 -4.724 0 24.832 1.758

$definebone "v_weapon" "" 0 0 0 0 0 -0.000015 0 0 0 0 0 0
$definebone "v_weapon.Bip01" "v_weapon" 0 0 0 -89.999968 -90.000003 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Pelvis" "v_weapon.Bip01" 0 0 0 -89.999962 -89.999927 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine" "v_weapon.Bip01_Pelvis" 3.562428 -0.816635 0.000008 -0.000083 0.045619 -0.00025 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine1" "v_weapon.Bip01_Spine" 4.003749 -0.003188 0 0 0 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine2" "v_weapon.Bip01_Spine1" 4.003753 -0.003188 0 0 0 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine3" "v_weapon.Bip01_Spine2" 4.003755 -0.003188 0 0 0 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Neck" "v_weapon.Bip01_Spine3" 5.028769 -0.763714 -0.000001 -0.000064 15.961334 -0.000005 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Clavicle" "v_weapon.Bip01_Neck" -0.99964 0.234795 1.2233 -69.622919 163.993047 0.000032 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_UpperArm" "v_weapon.Bip01_L_Clavicle" 5.773739 -0.000001 0 22.643441 0.384692 0.597517 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Forearm" "v_weapon.Bip01_L_UpperArm" 11.576873 0 0.000002 0.000003 -0.042004 0.000002 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Hand" "v_weapon.Bip01_L_Forearm" 10.295579 0 0 -2.498781 -1.242154 -89.582268 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_ForeTwist" "v_weapon.Bip01_L_UpperArm" 11.576876 0 0.000006 0.000002 -0.042005 0.391342 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Clavicle" "v_weapon.Bip01_Neck" -0.99964 0.234802 -1.223299 69.622782 163.992337 -0.000763 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_UpperArm" "v_weapon.Bip01_R_Clavicle" 5.773738 0 0.000004 -22.643426 0.384663 -0.597541 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Forearm" "v_weapon.Bip01_R_UpperArm" 11.576876 0 0.000002 0.000007 -0.042007 -0.000002 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Hand" "v_weapon.Bip01_R_Forearm" 10.29558 0 -0.000002 2.498777 -1.242154 89.582268 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_ForeTwist" "v_weapon.Bip01_R_UpperArm" 11.576878 0 0.000002 0.000005 -0.042005 -0.39134 0 0 0 0 0 0


$sequence "idle" {
	"v_sleeve_sas_anims\idle.smd"
	fadein 0.2
	fadeout 0.2
	fps 30
}

$keyvalues
{
	qc_path 
	{
		"value"		"models\weapons\v_models\arms\sas\v_sleeve_sas.qc"
	}
}
