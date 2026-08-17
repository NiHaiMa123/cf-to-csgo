// Created by CrowbarDecompiler 0.71

$modelname "weapons\v_rif_m4a1_s.mdl"

$bodygroup "studio"
{
	studio "v_rif_m4a1_s.smd"
}
$bodygroup "silencer"
{
	studio "v_rif_m4a1_s_silencer.smd"
	blank
}
$bodygroup "magazine"
{
	blank
	blank
}
$bodygroup "clamped1"
{
	studio "body3_model0.smd"
}


$surfaceprop "default"

$contents "solid"

$illumposition 2.44 -2.722 3.35

$cdmaterials "models\weapons\V_models\rif_m4a1_s\"

$texturegroup "skinfamilies"
{
	{ "rif_m4a1_s" }
}

$attachment "1" "v_weapon.flash" 0 0 0 rotate 0 0 0
$attachment "2" "v_weapon.shelleject" 0 0 0 rotate 0 0 0
$attachment "muzzle_flash2" "v_weapon.flash" 9.5 0 0 rotate 0 0 0

$cbox 0 0 0 0 0 0

$bbox -2.718 -3.938 -19.918 8.162 8.818 26.619

$definebone "v_weapon" "" 0 0 0 0 0 89.999982 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Forearm" "" -6.304863 4.049507 -12.285725 -34.76347 -73.179432 -118.017268 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Hand" "v_weapon.Bip01_R_Forearm" 10.29558 -0.000001 0 5.472155 32.455365 110.86985 0 0 0 0 0 0
$definebone "v_weapon.M4A1_s_Parent" "v_weapon.Bip01_R_Hand" 4.482179 1.199705 -0.715071 -3.705267 92.93751 97.453802 0 0 0 0 0 0
$definebone "v_weapon.M4A1_Clip" "v_weapon.M4A1_s_Parent" 0 1.83024 4.10786 0.000002 -0.000001 -89.999982 0 0 0 0 0 0
$definebone "v_weapon.flash" "v_weapon.M4A1_s_Parent" -0.336013 5.244593 23.040905 -89.980215 -89.999982 0 0 0 0 0 0 0
$definebone "v_weapon.shelleject" "v_weapon.M4A1_s_Parent" -0.719085 5.300996 3.836283 -0.000001 160.000009 0.000002 0 0 0 0 0 0
$definebone "v_weapon.stattrack" "v_weapon.M4A1_s_Parent" 0.540478 4.961051 0.579782 -0.285274 -1.939578 -90.156974 0 0 0 0 0 0
$definebone "v_weapon.uid" "v_weapon.M4A1_s_Parent" 0.214788 6.100204 0.357018 -0.274846 1.670572 -90.174685 0 0 0 0 0 0
$definebone "v_weapon.M4A1_Silencer" "v_weapon.M4A1_s_Parent" -0.231368 5.196647 23.662256 0.000002 -0.000001 -89.999982 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Forearm" "" 3.520265 -8.79537 -7.450874 -22.48527 -121.490665 -84.433125 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Hand" "v_weapon.Bip01_L_Forearm" 10.295583 0.000001 0 -13.353578 21.596951 -150.192062 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger0" "v_weapon.Bip01_L_Hand" 1.149519 0.416497 -1.414117 21.852835 17.46966 132.445783 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger01" "v_weapon.Bip01_L_Finger0" 1.263878 0 0 -6.871531 13.791718 -46.867494 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger02" "v_weapon.Bip01_L_Finger01" 1.188944 0 0 0.114372 14.402268 -0.564654 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger1" "v_weapon.Bip01_L_Hand" 3.773752 0.133216 -0.970574 -13.985837 -3.626131 5.558486 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger11" "v_weapon.Bip01_L_Finger1" 1.433456 0 0.000001 0.000003 11.623139 -0.000002 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger12" "v_weapon.Bip01_L_Finger11" 1.019161 0 0 0.000005 41.210045 -0.000001 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger2" "v_weapon.Bip01_L_Hand" 3.799511 0.014954 -0.039958 -12.335554 17.720388 -2.537974 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger21" "v_weapon.Bip01_L_Finger2" 1.774881 0.000004 0.000001 0.563962 34.753321 -0.924186 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger22" "v_weapon.Bip01_L_Finger21" 1.008846 0.000002 0 0.525295 32.383225 -0.946641 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger3" "v_weapon.Bip01_L_Hand" 3.632761 0.05905 0.757493 -6.842719 25.077157 -13.663554 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger31" "v_weapon.Bip01_L_Finger3" 1.500138 -0.000002 -0.000001 1.877762 41.612374 -3.914907 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger32" "v_weapon.Bip01_L_Finger31" 0.905663 0 0.000001 1.80402 40.538303 -3.949454 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger4" "v_weapon.Bip01_L_Hand" 3.323328 0.233746 1.479075 7.198637 40.280996 -15.063002 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger41" "v_weapon.Bip01_L_Finger4" 0.963099 0 0 0.506489 30.97736 -5.497071 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Finger42" "v_weapon.Bip01_L_Finger41" 0.682895 0 0 0.506551 30.978391 -5.497073 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_ForeTwist" "" 3.520265 -8.79537 -7.450874 -22.485253 -121.490692 -138.424493 0 0 0 0 0 0
$definebone "v_weapon.M4A1_Trigger" "v_weapon.M4A1_s_Parent" 0 2.627978 0.988427 0.000002 -0.000001 -89.999982 0 0 0 0 0 0
$definebone "v_weapon.M4A1_Bolt" "v_weapon.M4A1_s_Parent" 0 6.086905 -2.262868 0.000002 -0.000001 -89.999982 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger0" "v_weapon.Bip01_R_Hand" 1.149523 0.416497 1.414115 -11.599357 45.391784 -101.413413 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger01" "v_weapon.Bip01_R_Finger0" 1.263876 0.000001 0 10.862357 31.816234 -1.964217 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger02" "v_weapon.Bip01_R_Finger01" 1.188942 0 0 0 16.914402 -0.000009 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger1" "v_weapon.Bip01_R_Hand" 3.773754 0.133215 0.970573 -1.459208 -6.952621 -0.02418 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger11" "v_weapon.Bip01_R_Finger1" 1.433458 0 0 -0.56207 48.567754 0.83159 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger12" "v_weapon.Bip01_R_Finger11" 1.019161 0 -0.000001 -0.506321 47.889137 0.829531 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger2" "v_weapon.Bip01_R_Hand" 3.799514 0.014952 0.039957 9.828861 63.22241 16.023629 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger21" "v_weapon.Bip01_R_Finger2" 1.774881 -0.000001 0 -2.296532 79.017878 0.890089 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger22" "v_weapon.Bip01_R_Finger21" 1.008846 0.000001 0 -1.529395 48.580004 1.930751 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger3" "v_weapon.Bip01_R_Hand" 3.632764 0.059049 -0.757494 3.758947 79.467543 21.166842 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger31" "v_weapon.Bip01_R_Finger3" 1.500137 0.000001 0.000001 -3.188051 64.471201 3.503525 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger32" "v_weapon.Bip01_R_Finger31" 0.905663 0 0 -1.326284 38.449761 4.546425 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger4" "v_weapon.Bip01_R_Hand" 3.323329 0.233745 -1.479076 -1.044673 81.405159 25.96158 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger41" "v_weapon.Bip01_R_Finger4" 0.963099 -0.000001 -0.000001 -0.354141 37.605587 3.224779 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Finger42" "v_weapon.Bip01_R_Finger41" 0.682895 0 0 -1.323531 55.400201 2.962138 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_ForeTwist" "" -6.304863 4.049507 -12.285725 -34.76347 -73.179432 -95.769723 0 0 0 0 0 0
$definebone "v_weapon.v_weapon" "" 0 0 0 0 0 89.999989 0 0 0 0 0 0
$definebone "v_weapon.Bip01" "" 3.706409 5.104027 -19.918226 2.780724 -131.511304 0.478134 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Pelvis" "v_weapon.Bip01" -0.000001 0 0 -89.999989 -89.999811 0 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine" "v_weapon.Bip01_Pelvis" 3.562498 -0.816636 -0.000028 -0.230236 1.226121 0.561817 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine1" "v_weapon.Bip01_Spine" 4.004025 -0.003178 -0.000071 0.268366 4.900142 1.25917 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine2" "v_weapon.Bip01_Spine1" 4.004029 -0.003176 -0.000071 0.268822 4.898323 1.266267 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Spine3" "v_weapon.Bip01_Spine2" 4.003753 -0.003188 0 0.000003 0 -0.000036 0 0 0 0 0 0
$definebone "v_weapon.Bip01_Neck" "v_weapon.Bip01_Spine3" 5.029974 -0.763043 -0.000584 3.716921 39.117695 9.483527 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_Clavicle" "v_weapon.Bip01_Neck" -0.905726 0.793273 1.051288 -60.362384 131.888562 10.176113 0 0 0 0 0 0
$definebone "v_weapon.Bip01_L_UpperArm" "v_weapon.Bip01_L_Clavicle" 5.773743 0.000002 -0.000001 9.354253 -75.645083 -68.067958 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_Clavicle" "v_weapon.Bip01_Neck" -0.747116 0.391016 -1.3568 77.463641 163.985001 23.734334 0 0 0 0 0 0
$definebone "v_weapon.Bip01_R_UpperArm" "v_weapon.Bip01_R_Clavicle" 5.773743 -0.000002 0 -39.34385 -68.452955 16.299473 0 0 0 0 0 0

$bonemerge "v_weapon"
$bonemerge "v_weapon.Bip01_R_Forearm"
$bonemerge "v_weapon.Bip01_R_Hand"
$bonemerge "v_weapon.M4A1_s_Parent"
$bonemerge "v_weapon.stattrack"
$bonemerge "v_weapon.uid"
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
$bonesaveframe "v_weapon.Bip01_R_Forearm" position
$bonesaveframe "v_weapon.M4A1_Clip" position
$bonesaveframe "v_weapon.M4A1_Silencer" position
$bonesaveframe "v_weapon.Bip01_L_Forearm" position
$bonesaveframe "v_weapon.Bip01_L_ForeTwist" position
$bonesaveframe "v_weapon.M4A1_Bolt" position
$bonesaveframe "v_weapon.Bip01_R_ForeTwist" position
$bonesaveframe "v_weapon.v_weapon" position
$bonesaveframe "v_weapon.Bip01" position

$sectionframes 30 34

$weightlist "weights_idle_reposition_difference" {
	 "v_weapon" 1
	 "v_weapon.Bip01_R_Forearm" 1
	 "v_weapon.Bip01_R_Hand" 1
	 "v_weapon.M4A1_s_Parent" 1
	 "v_weapon.M4A1_Clip" 1
	 "v_weapon.flash" 1
	 "v_weapon.shelleject" 1
	 "v_weapon.stattrack" 1
	 "v_weapon.uid" 1
	 "v_weapon.M4A1_Silencer" 0
	 "v_weapon.Bip01_L_Forearm" 1
	 "v_weapon.Bip01_L_Hand" 1
	 "v_weapon.Bip01_L_Finger0" 1
	 "v_weapon.Bip01_L_Finger01" 1
	 "v_weapon.Bip01_L_Finger02" 1
	 "v_weapon.Bip01_L_Finger1" 1
	 "v_weapon.Bip01_L_Finger11" 1
	 "v_weapon.Bip01_L_Finger12" 1
	 "v_weapon.Bip01_L_Finger2" 1
	 "v_weapon.Bip01_L_Finger21" 1
	 "v_weapon.Bip01_L_Finger22" 1
	 "v_weapon.Bip01_L_Finger3" 1
	 "v_weapon.Bip01_L_Finger31" 1
	 "v_weapon.Bip01_L_Finger32" 1
	 "v_weapon.Bip01_L_Finger4" 1
	 "v_weapon.Bip01_L_Finger41" 1
	 "v_weapon.Bip01_L_Finger42" 1
	 "v_weapon.Bip01_L_ForeTwist" 1
	 "v_weapon.M4A1_Trigger" 1
	 "v_weapon.M4A1_Bolt" 1
	 "v_weapon.Bip01_R_Finger0" 1
	 "v_weapon.Bip01_R_Finger01" 1
	 "v_weapon.Bip01_R_Finger02" 1
	 "v_weapon.Bip01_R_Finger1" 1
	 "v_weapon.Bip01_R_Finger11" 1
	 "v_weapon.Bip01_R_Finger12" 1
	 "v_weapon.Bip01_R_Finger2" 1
	 "v_weapon.Bip01_R_Finger21" 1
	 "v_weapon.Bip01_R_Finger22" 1
	 "v_weapon.Bip01_R_Finger3" 1
	 "v_weapon.Bip01_R_Finger31" 1
	 "v_weapon.Bip01_R_Finger32" 1
	 "v_weapon.Bip01_R_Finger4" 1
	 "v_weapon.Bip01_R_Finger41" 1
	 "v_weapon.Bip01_R_Finger42" 1
	 "v_weapon.Bip01_R_ForeTwist" 1
	 "v_weapon.v_weapon" 0
	 "v_weapon.Bip01" 0
	 "v_weapon.Bip01_Pelvis" 0
	 "v_weapon.Bip01_Spine" 0
	 "v_weapon.Bip01_Spine1" 0
	 "v_weapon.Bip01_Spine2" 0
	 "v_weapon.Bip01_Spine3" 0
	 "v_weapon.Bip01_Neck" 0
	 "v_weapon.Bip01_L_Clavicle" 0
	 "v_weapon.Bip01_L_UpperArm" 0
	 "v_weapon.Bip01_R_Clavicle" 0
	 "v_weapon.Bip01_R_UpperArm" 0
}

$animation "idle_masked_silencer_corrective_animation" "v_rif_m4a1_s_anims\idle_masked_silencer_corrective_animation.smd" {
}

$animation "idle_masked_silencer_corrective_animation" "v_rif_m4a1_s_anims\idle_masked_silencer_corrective_animation.smd" {
	fps 30
}

$animation "idle_masked_silencer" "v_rif_m4a1_s_anims\idle_masked_silencer.smd" {
	fps 30
	// Crowbar writes this subtract option to prevent jigglebone and poseparameter problems when delta sequences are recompiled.
	subtract "idle_masked_silencer_corrective_animation" 0
	weightlist "weights_idle_reposition_difference"
}

$animation "idle_masked_silencer_m4a4" "v_rif_m4a1_s_anims\idle_masked_silencer_m4a4.smd" {
	fps 60
	weightlist "weights_idle_reposition_difference"
}

$animation "silencer_masked_inspect" "v_rif_m4a1_s_anims\silencer_masked_inspect.smd" {
	fps 30
	weightlist "weights_idle_reposition_difference"
}

$sequence "idle_reposition_difference" {
	"idle_masked_silencer"
	delta
	fadein 0.2
	fadeout 0.2
}

$sequence "idle" {
	"idle_masked_silencer_m4a4"
	activity "ACT_VM_IDLE" 1
	fadein 0.2
	fadeout 0.2
	addlayer "idle_reposition_difference"
	snap
}

$sequence "attach" {
	"v_rif_m4a1_s_anims\attach.smd"
	activity "ACT_VM_ATTACH_SILENCER" 1
	{ event AE_CL_HIDE_SILENCER 0 "" }
	{ event AE_CL_SHOW_SILENCER 21 "" }
	{ event AE_CL_ATTACH_SILENCER_COMPLETE 103 "" }
	{ event 5004 3 "Weapon_M4A1.SilencerWeaponMove1" }
	{ event 5004 33 "Weapon_M4A1.SilencerScrewOnStart" }
	{ event 5004 47 "Weapon_M4A1.SilencerScrew1" }
	{ event 5004 65 "Weapon_M4A1.SilencerScrew2" }
	{ event 5004 77 "Weapon_M4A1.SilencerScrew3" }
	{ event 5004 89 "Weapon_M4A1.SilencerScrew4" }
	{ event 5004 98 "Weapon_M4A1.SilencerScrew5" }
	{ event 5004 120 "Weapon_M4A1.SilencerWeaponMove3" }
	fadein 0.2
	fadeout 0.2
	blendlayer "idle_reposition_difference" 134 136 146 146
	blendlayer "idle_reposition_difference" 0 0 1 2
	snap
	fps 30
}

$sequence "detach" {
	"v_rif_m4a1_s_anims\detach.smd"
	activity "ACT_VM_DETACH_SILENCER" 1
	{ event AE_CL_SHOW_SILENCER 0 "" }
	{ event AE_CL_HIDE_SILENCER 124 "" }
	{ event AE_CL_DETACH_SILENCER_COMPLETE 98 "" }
	{ event 5004 3 "Weapon_M4A1.SilencerWeaponMove1" }
	{ event 5004 24 "Weapon_M4A1.SilencerScrew1" }
	{ event 5004 43 "Weapon_M4A1.SilencerScrew2" }
	{ event 5004 54 "Weapon_M4A1.SilencerScrew3" }
	{ event 5004 66 "Weapon_M4A1.SilencerScrew4" }
	{ event 5004 76 "Weapon_M4A1.SilencerScrew5" }
	{ event 5004 88 "Weapon_M4A1.SilencerScrew1" }
	{ event 5004 91 "Weapon_M4A1.SilencerScrewOffEnd" }
	{ event 5004 105 "Weapon_M4A1.SilencerWeaponMove3" }
	fadein 0.2
	fadeout 0.2
	blendlayer "idle_reposition_difference" 134 136 146 146
	blendlayer "idle_reposition_difference" 0 0 1 2
	snap
	fps 30
}

$sequence "shoot1" {
	"v_rif_m4a1_s_anims\shoot1.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	addlayer "idle_reposition_difference"
	snap
	fps 20
}

$sequence "shoot2" {
	"v_rif_m4a1_s_anims\shoot2.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	addlayer "idle_reposition_difference"
	snap
	fps 20
}

$sequence "shoot3" {
	"v_rif_m4a1_s_anims\shoot3.smd"
	activity "ACT_VM_PRIMARYATTACK" 1
	{ event 5001 0 "1" }
	{ event AE_CLIENT_EJECT_BRASS 0 "" }
	fadein 0.2
	fadeout 0.2
	addlayer "idle_reposition_difference"
	snap
	fps 20
}

$sequence "reload" {
	"v_rif_m4a1_s_anims\reload.smd"
	activity "ACT_VM_RELOAD" 1
	{ event 5004 11 "Weapon_M4A1.Clipout" }
	{ event 5004 35 "Weapon_M4A1.Clipin" }
	{ event 5004 57 "Weapon_M4A1.ClipHit" }
	{ event AE_WPN_COMPLETE_RELOAD 41 "" }
	fadein 0.2
	fadeout 0.2
	addlayer "idle_reposition_difference"
	snap
	fps 30
}

$sequence "draw" {
	"v_rif_m4a1_s_anims\draw.smd"
	activity "ACT_VM_DRAW_SILENCED" 1
	{ event AE_CL_SHOW_SILENCER 0 "" }
	{ event 5004 0 "Weapon_M4A1.Draw" }
	{ event 5004 10 "Weapon_M4A1S.BoltForward" }
	{ event 5004 17 "Weapon_M4A1S.BoltBack" }
	fadein 0.2
	fadeout 0.2
	addlayer "idle_reposition_difference"
	snap
	fps 30
}

$sequence "draw_silenced" {
	"v_rif_m4a1_s_anims\draw_silenced.smd"
	activity "ACT_VM_DRAW" 1
	{ event AE_CL_HIDE_SILENCER 0 "" }
	{ event 5004 0 "Weapon_M4A1.Draw" }
	{ event 5004 10 "Weapon_M4A1S.BoltForward" }
	{ event 5004 17 "Weapon_M4A1S.BoltBack" }
	fadein 0.2
	fadeout 0.2
	addlayer "idle_reposition_difference"
	snap
	fps 30
}

$sequence "lookat01" {
	"silencer_masked_inspect"
	{ event AE_CL_SET_STATTRAK_GLOW 0 "1" }
	{ event AE_CL_SET_STATTRAK_GLOW 92 "0" }
	{ event AE_BEGIN_TAUNT_LOOP 91 "0.306666" }
	{ event 5004 2 "Weapon_M4A1.WeaponMove1" }
	{ event 5004 92 "Weapon_M4A1.WeaponMove2" }
	{ event 5004 116 "Weapon_M4A1.WeaponMove3" }
	fadein 0.3
	fadeout 0.3
	addlayer "idle_reposition_difference"
}

$sequence "lookat01_prepare" {
	"v_rif_m4a1_s_anims\lookat01_prepare.smd"
	fadein 0.2
	fadeout 0.2
	fps 30
	weightlist "weights_idle_reposition_difference"
}

$sequence "lookat01_loop" {
	"v_rif_m4a1_s_anims\lookat01_loop.smd"
	fadein 0.2
	fadeout 0.2
	fps 15
	weightlist "weights_idle_reposition_difference"
}

$keyvalues
{
	qc_path 
	{
		"value"		"models\weapons\v_models\rif_m4a1_s\v_rif_m4a1_s.qc"
	}
	qc_path 
	{
		"value"		"d:\project\cf_to_csgo\work\m4a1_s_bornbeast\reference_m4a1_s\decompiled\v_rif_m4a1_s.qc"
	}
}
