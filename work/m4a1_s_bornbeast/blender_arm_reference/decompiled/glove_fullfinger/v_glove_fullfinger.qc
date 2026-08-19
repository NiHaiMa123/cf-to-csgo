// Created by CrowbarDecompiler 0.71

$modelname "weapons/v_models/arms/glove_fullfinger/v_glove_fullfinger.mdl"

$bodygroup "gloves"
{
	studio "v_glove_fullfinger.smd"
}


$surfaceprop "default"

$contents "solid"

$illumposition 0 8.828 -1.414

$cdmaterials "models\weapons\v_models\arms\bare\"
$cdmaterials "models\weapons\v_models\arms\glove_fullfinger\"
$cdmaterials "models\weapons\v_models\arms\bare\"
$cdmaterials ""

$texturegroup "skinfamilies"
{
	{ "bare_arm_133"      "glove_fullfinger" "bare_arm_55" "bare_arm_66" "bare_arm_103" "bare_arm_78" "bare_arm_pro_varf" "bare_arm_44" }
	{ "bare_arm_55"       "glove_fullfinger" "bare_arm_55" "bare_arm_66" "bare_arm_103" "bare_arm_78" "bare_arm_pro_varf" "bare_arm_44" }
	{ "bare_arm_66"       "glove_fullfinger" "bare_arm_55" "bare_arm_66" "bare_arm_103" "bare_arm_78" "bare_arm_pro_varf" "bare_arm_44" }
	{ "bare_arm_103"      "glove_fullfinger" "bare_arm_55" "bare_arm_66" "bare_arm_103" "bare_arm_78" "bare_arm_pro_varf" "bare_arm_44" }
	{ "bare_arm_78"       "glove_fullfinger" "bare_arm_55" "bare_arm_66" "bare_arm_103" "bare_arm_78" "bare_arm_pro_varf" "bare_arm_44" }
	{ "bare_arm_pro_varf" "glove_fullfinger" "bare_arm_55" "bare_arm_66" "bare_arm_103" "bare_arm_78" "bare_arm_pro_varf" "bare_arm_44" }
	{ "bare_arm_44"       "glove_fullfinger" "bare_arm_55" "bare_arm_66" "bare_arm_103" "bare_arm_78" "bare_arm_pro_varf" "bare_arm_44" }
}

$cbox 0 0 0 0 0 0

$bbox -20.603 -28.814 -4.578 2.947 28.814 1.751

$definebone "v_weapon" "" 0 0 0 0 0 -0.000015 0 0 0 0 0 0
$definebone "v_weapon.Bip01" "v_weapon" 0 0 0 -90.000003 -90.000003 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Pelvis" "v_weapon.Bip01" 0 0 0 -90.000003 -89.999921 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine" "v_weapon.Bip01_Pelvis" 3.562428 -0.816635 0.000007 -0.000079 0.045626 -0.000238 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine1" "v_weapon.Bip01_Spine" 4.00375 -0.003188 0 0 0 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine2" "v_weapon.Bip01_Spine1" 4.003753 -0.003188 0 0 0 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine3" "v_weapon.Bip01_Spine2" 4.003754 -0.003188 0 0 0 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Neck" "v_weapon.Bip01_Spine3" 5.028769 -0.763714 -0.000001 -0.000065 15.961324 -0.000007 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Clavicle" "v_weapon.Bip01_Neck" -0.999638 0.234795 1.2233 -69.622925 163.99302 0.000029 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_UpperArm" "v_weapon.Bip01_L_Clavicle" 5.773739 0 0 22.643441 0.384694 0.597525 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Forearm" "v_weapon.Bip01_L_UpperArm" 11.576879 0 0.000004 0.000003 -0.042006 0.000001 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Hand" "v_weapon.Bip01_L_Forearm" 10.295582 0 -0.000002 -2.498775 -1.242154 -89.582268 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger0" "v_weapon.Bip01_L_Hand" 1.149526 0.416498 -1.414117 18.383447 13.49188 80.63164 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger01" "v_weapon.Bip01_L_Finger0" 1.263882 0.000001 0 -0.000002 -0.000002 0.000001 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger02" "v_weapon.Bip01_L_Finger01" 1.188944 0 0 0.000002 -0.488178 0.000002 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger1" "v_weapon.Bip01_L_Hand" 3.773759 0.133217 -0.970575 8.162449 0.340439 0.5272 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger11" "v_weapon.Bip01_L_Finger1" 1.433458 0 0 -0.000003 1.448373 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger12" "v_weapon.Bip01_L_Finger11" 1.019165 0.000008 0 -0.000001 1.448377 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger2" "v_weapon.Bip01_L_Hand" 3.799514 0.014956 -0.039958 -1.985333 1.299989 -0.498669 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger21" "v_weapon.Bip01_L_Finger2" 1.774879 0.000002 0 0.000001 1.448383 -0.000002 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger22" "v_weapon.Bip01_L_Finger21" 1.008841 0.000002 0 0.000001 1.448378 -0.000002 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger3" "v_weapon.Bip01_L_Hand" 3.632764 0.05905 0.757493 -9.344711 2.459646 -0.939006 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger31" "v_weapon.Bip01_L_Finger3" 1.500134 0.000002 0 0 1.448371 -0.000003 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger32" "v_weapon.Bip01_L_Finger31" 0.905666 0 -0.000001 0 1.448375 -0.000003 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger4" "v_weapon.Bip01_L_Hand" 3.323329 0.233744 1.479075 -18.576337 1.802652 -1.857763 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger41" "v_weapon.Bip01_L_Finger4" 0.963097 0.000006 0 0.000003 1.448376 -0.000003 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger42" "v_weapon.Bip01_L_Finger41" 0.682896 0 0 0.000002 1.448368 -0.000003 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_ForeTwist" "v_weapon.Bip01_L_UpperArm" 11.576879 0 0.000004 0.000003 -0.042006 0.391343 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Clavicle" "v_weapon.Bip01_Neck" -0.999638 0.234802 -1.2233 69.622782 163.992337 -0.00076 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_UpperArm" "v_weapon.Bip01_R_Clavicle" 5.773738 0 0.000004 -22.643435 0.384664 -0.597538 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Forearm" "v_weapon.Bip01_R_UpperArm" 11.576878 0 0 0.000002 -0.042005 0.000001 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Hand" "v_weapon.Bip01_R_Forearm" 10.29558 0 0 2.498777 -1.242153 89.582268 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger0" "v_weapon.Bip01_R_Hand" 1.14952 0.416502 1.414117 -18.383447 13.491878 -80.63164 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger01" "v_weapon.Bip01_R_Finger0" 1.263883 0 -0.000006 0.000003 -0.488177 -0.000002 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger02" "v_weapon.Bip01_R_Finger01" 1.18894 -0.000002 0.000006 0.000007 -0.488178 -0.000001 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger1" "v_weapon.Bip01_R_Hand" 3.773755 0.133215 0.970574 -8.162447 0.340428 -0.527203 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger11" "v_weapon.Bip01_R_Finger1" 1.433455 0 0 0.000002 1.448365 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger12" "v_weapon.Bip01_R_Finger11" 1.019165 -0.000002 0 0.000001 1.448365 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger2" "v_weapon.Bip01_R_Hand" 3.799514 0.014957 0.039959 1.985335 1.299982 0.498667 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger21" "v_weapon.Bip01_R_Finger2" 1.774878 0 0 0.000001 1.448377 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger22" "v_weapon.Bip01_R_Finger21" 1.008842 -0.000004 0 0.000001 1.44837 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger3" "v_weapon.Bip01_R_Hand" 3.632764 0.05905 -0.757493 9.344712 2.459641 0.939004 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger31" "v_weapon.Bip01_R_Finger3" 1.500139 0 0 0.000002 1.448361 -0.000001 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger32" "v_weapon.Bip01_R_Finger31" 0.905663 -0.000002 0 0.000003 1.448361 -0.000001 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger4" "v_weapon.Bip01_R_Hand" 3.323327 0.233747 -1.479075 18.57634 1.802646 1.857761 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger41" "v_weapon.Bip01_R_Finger4" 0.963099 0.000006 0 0.000003 1.448373 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger42" "v_weapon.Bip01_R_Finger41" 0.682892 -0.000002 -0.000001 0.000005 1.44837 0.000001 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_ForeTwist" "v_weapon.Bip01_R_UpperArm" 11.576878 0 0 0.000002 -0.042005 -0.391339 0 0 0 0 0 0

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
$bonemerge "v_weapon.Bip01_L_ForeTwist"
$bonemerge "v_weapon.Bip01_R_Clavicle"
$bonemerge "v_weapon.Bip01_R_UpperArm"
$bonemerge "v_weapon.Bip01_R_Forearm"
$bonemerge "v_weapon.Bip01_R_Hand"
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
$bonemerge "v_weapon.Bip01_R_ForeTwist"


// The 32 below is a guess until further is known about the format.
$animblocksize 32

$bonesaveframe "v_weapon" position

$sequence "idle" {
	"v_glove_fullfinger_anims\idle.smd"
	fadein 0.2
	fadeout 0.2
	fps 30
}

$keyvalues
{
	qc_path 
	{
		"value"		"models\weapons\v_models\arms\glove_fullfinger\v_glove_fullfinger.qc"
	}
}
