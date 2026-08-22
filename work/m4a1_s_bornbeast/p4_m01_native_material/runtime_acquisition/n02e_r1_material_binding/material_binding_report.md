# P4-M01-N02-E-R1 — LTB Material Resource Binding Report

- status: **MATERIAL_BINDING_PARTIAL**
- script: `scripts/material_recovery/n02e_r1_material_binding.py`

## 1. Answers to task.md §3 evidence questions

**1. LTB 是否包含 material/texture slot relation?**

**NO** (in the LTB-internal LTA-atom sense).

All 8 N02-D-R1 LTB hits were LZMA-decompressed and
scanned for the canonical Jupiter LTA atoms `(piece`,
`(texture`, `(renderstyle`, `(material`, `(lt-model` and
the inline substrings `.dtx`, `.tga`, `texture`,
`renderstyle`.  No hits were found.  This is consistent
with the Jupiter LTB standard (compressed binary model,
piece table is a separate consumer artefact) and with
the `CFRezManager/Decoders/LithTech/Models/LithTechModelDecoder.cs`
fallback path that decodes the LTA wrapper only when the
outer LZMA layer is missing.

**2. piece index 与 texture reference 是否存在确定关系?**

**NO LTB-internal relation.**  The LTB mesh/bone/anim
names that DO exist in the decompressed body are pure
ASCII names (`Fview-hand2`, `Fview-arm2`, `M4-A1`,
`Bone02`, `BaseTracker`, `WeaponReload`, …) with no
associated texture/material slot.

The closest *runtime-side* relation is the bf005 weapon
record's pair `(ModelFileName, SkinFileName)` and
`(PViewModelFileName, PViewSkinFileName)`.  This is
**consumer-inferred** (N02-C / N02-D-R1 evidence), not
LTB-decoded, and so cannot be cited as piece->texture
binding closure.

**3. runtime resource graph 能否从 model 延伸到材质资源?**

**PARTIAL** — extending the graph is possible through
two consumer-inferred edges (see §2 below), but the
LTB-internal piece->DTX/TGA edge is OPEN_UNRESOLVED.

**4. 哪些关系只能保持 OPEN_UNRESOLVED?**

- LTB internal piece -> DTX/TGA binding (per mesh piece)
- LTB internal piece -> RenderStyle (per mesh piece)
- LTB internal skeleton -> animation binding (bones have
  ASCII names but no explicit animation index table)
- DTX actual pixel content vs. CF engine expectation
- RenderStyle (.LTB in RS/) actual rendering behaviour

## 2. Resource graph candidate (per weapon)

Edges are typed as `exact_path_binding` (N02-D-R1),
`ltb_internal_name` (this round), `consumer_inferred`
(bf005 pair), or `open_unresolved`.

### M4A1

- exact_path_bindings: 24
- LTB internal mesh names: ['Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone09', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 6
  - WEAPONS/M4A1.LTB  ->  WEAPONS/L-M4A1.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1.LTB  ->  PLAYERVIEW/PV-M4A1.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

### M4A1-B

- exact_path_bindings: 24
- LTB internal mesh names: ['Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone09', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 6
  - WEAPONS/M4A1.LTB  ->  WEAPONS/L-M4A1.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1.LTB  ->  PLAYERVIEW/PV-M4A1.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

### M4A1-A

- exact_path_bindings: 24
- LTB internal mesh names: ['M4A1_SILENCER', 'Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone09', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 6
  - WEAPONS/M4A1_SILENCER.LTB  ->  WEAPONS/L-M4A1_SILENCER.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1_SILENCER.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  PLAYERVIEW/PV-M4A1.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

### M4A1-S

- exact_path_bindings: 28
- LTB internal mesh names: ['M4A1_SILENCER', 'Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone09', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 7
  - WEAPONS/M4A1_SILENCER.LTB  ->  WEAPONS/L-M4A1_SILENCER_CAMO.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1_SILENCER.LTB  ->  WEAPONS/L-M4A1_SILENCER_CAMO.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1_SILENCER.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  PLAYERVIEW/PV-M4A1-CAMO.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

### M4A1-QQ»áÔ±

- exact_path_bindings: 24
- LTB internal mesh names: ['M4A1_SILENCER', 'Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone09', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 6
  - WEAPONS/M4A1_SILENCER.LTB  ->  WEAPONS/M4A1_QQ.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1_SILENCER.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  PLAYERVIEW/PV-M4A1_QQ.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

### M4A1-Custom

- exact_path_bindings: 24
- LTB internal mesh names: ['Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone01', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 6
  - WEAPONS/M4A1-CUSTOM.LTB  ->  WEAPONS/L-M4A1.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1-CUSTOM.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1-CUSTOM.LTB  ->  PLAYERVIEW/PV-M4A1.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1-CUSTOM.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1-CUSTOM.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1-CUSTOM.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1-CUSTOM.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1-CUSTOM.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

### »Æ½ðM4A1

- exact_path_bindings: 24
- LTB internal mesh names: ['Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone09', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 6
  - WEAPONS/M4A1.LTB  ->  WEAPONS/QV-RI_M4A1_GOLD.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1.LTB  ->  PLAYERVIEW/PV-RI_M4A1_GOLD.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

### ÇàÍ­M4A1-A

- exact_path_bindings: 24
- LTB internal mesh names: ['M4A1_SILENCER', 'Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone09', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 6
  - WEAPONS/M4A1_SILENCER.LTB  ->  WEAPONS/QV-RI_M4A1_SILENCER_BRONZE.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1_SILENCER.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  PLAYERVIEW/PV-RI_M4A1_SILENCER_BRONZE.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

### ÒøÉ«M4A1-A

- exact_path_bindings: 24
- LTB internal mesh names: ['M4A1_SILENCER', 'Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone09', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 6
  - WEAPONS/M4A1_SILENCER.LTB  ->  WEAPONS/QV-RI_M4A1_SILENCER_SILVER.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1_SILENCER.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  PLAYERVIEW/PV-RI_M4A1_SILENCER_SILVER.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

### Ë®¾§M4A1-A

- exact_path_bindings: 24
- LTB internal mesh names: ['M4A1_SILENCER', 'Fview-hand2', 'Fview-arm2', 'M4-A1']
- LTB internal bone names: ['Bone09', 'FvARM-bone', 'FvARM-bone Pelvis', 'FvARM-bone Spine', 'FvARM-bone Spine1', 'FvARM-bone Neck', 'FvARM-bone L Clavicle', 'FvARM-bone L UpperArm', 'FvARM-bone L ForeArm', 'FvARM-bone L Hand', 'FvARM-bone L Finger0', 'FvARM-bone L Finger01', 'FvARM-bone L Finger02', 'FvARM-bone L Finger1', 'FvARM-bone L Finger11', 'FvARM-bone L Finger12', 'FvARM-bone L Finger2', 'FvARM-bone L Finger21', 'FvARM-bone L Finger22', 'FvARM-bone L Finger3', 'FvARM-bone L Finger31', 'FvARM-bone L Finger32', 'FvARM-bone L Finger4', 'FvARM-bone L Finger41', 'FvARM-bone L Finger42', 'FvARM-bone L ForeTwist', 'FvARM-bone R Clavicle', 'FvARM-bone R UpperArm', 'FvARM-bone R ForeArm', 'FvARM-bone R Hand', 'FvARM-bone R Finger0', 'FvARM-bone R Finger01', 'FvARM-bone R Finger02', 'FvARM-bone R Finger1', 'FvARM-bone R Finger11', 'FvARM-bone R Finger12', 'FvARM-bone R Finger2', 'FvARM-bone R Finger21', 'FvARM-bone R Finger22', 'FvARM-bone R Finger3', 'FvARM-bone R Finger31', 'FvARM-bone R Finger32', 'FvARM-bone R Finger4', 'FvARM-bone R Finger41', 'FvARM-bone R Finger42', 'FvARM-bone R ForeTwist', 'FvARM-bone Prop1', 'Dummy01', 'Bone02', 'Bone04', 'Bone06', 'BaseTracker']
- LTB internal anim names: ['WeaponReload', 'WeaponClipOut', 'WeaponClipIn', 'WeaponFinish']
- closed_material_edges: 6
  - WEAPONS/M4A1_SILENCER.LTB  ->  WEAPONS/QV-RI_M4A1_SILENCER_CRYSTAL.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - WEAPONS/M4A1_SILENCER.LTB  ->  RS/NINJATRANSLUCENT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  PLAYERVIEW/PV-RI_M4A1_SILENCER_CRYSTAL.DTX
    grade: CONSUMER_INFERRED_FROM_BF005
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  RS/PVMODELDEFAULT.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/NINJATRANSLUCENT.LTB  ->  WEAPONS/M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
  - RS/PVMODELDEFAULT.LTB  ->  PLAYERVIEW/PV-M4A1_SILENCER.LTB
    grade: CONSUMER_INFERRED_FROM_BF005
- open_material_edges: 4
  - WEAPONS/M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - PLAYERVIEW/PV-M4A1_SILENCER.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/NINJATRANSLUCENT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED
  - RS/PVMODELDEFAULT.LTB  ->  DTX/TGA piece binding (LTB-internal piece index)
    grade: OPEN_UNRESOLVED

## 3. Completion state (per task.md §6)

**A. MATERIAL_BINDING_CONFIRMED** — would require LTB-
internal piece->material evidence; not observed.

**B. MATERIAL_BINDING_PARTIAL** — current state.
LTB structure is decoded (mesh/bone/anim names);
the consumer-inferred resource graph is built; the
piece->DTX/TGA material edge remains OPEN_UNRESOLVED.

**C. REWORK_REQUIRED** — not triggered.  N02-D-R1's
exact-path entries were sufficient as input; the LZMA
decompression succeeded on all 8 hits; the LTB header
parse anchored against CFRezManager offsets as expected.
