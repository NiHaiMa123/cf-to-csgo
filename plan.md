# CF 武器 -> CS:GO Legacy Source 1 — 静态项目蓝图

> 本文件定义长期稳定的 **pipeline、阶段关系、Gate、已冻结事实和关键技术结论**。  
> 它不是当前任务单，不应因为每一轮执行而频繁改写。  
> 当前下一步永远看 [`task.md`](task.md)。Git 操作规则看 [`AGENTS.md`](AGENTS.md)。

---

# 1. 总体目标

把 CrossFire 本地资源可靠转换为 CS:GO Legacy Source 1 / MIGI 可用武器 Mod，并最终完成目标武器身份、原生材质、发布质量与后续动画/IK增强。

完整主链：

```text
CF 原始资源
-> REZ / LTB / DTX / TGA / CFG / audio 提取与解析
-> 武器模型 / UV / 骨骼 / 动作关系
-> Source 1 SMD / QC / VMT / VTF
-> compile / validate / package / MIGI
-> CF 原生材质恢复
-> 最终目标资产确认
-> release-quality replacement
-> Inspect / IK / CF 原动画/声音等增强
```

---

# 2. 阶段 Pipeline

## P0-P3 — 前置基础

包含资源解包、音频工具、LTB 基础研究、Source 1 兼容性与 M4A4 映射等历史基础工作。

状态：`DONE / HISTORICAL`。

## P4 — Source 1 conversion baseline

目标：证明 CF 第一人称武器能稳定进入 Source 1 构建与 MIGI runtime。

固定链：

```text
local CF LTB
-> mesh / UV / normal / bone mapping
-> SMD / QC
-> Source 1 material references
-> studiomdl
-> Crowbar roundtrip
-> validation
-> package / staging
-> MIGI deploy
-> user runtime Gate
```

### P4 冻结结论

```text
P4 baseline = PASS / FROZEN
```

冻结身份：

```text
Implementation baseline : 10aa99b770e575300ca3c28324ef3de3d5b70c6b
Frozen build run        : run_20260819_170013_270792
RV-04 evidence commit   : fd61d6ae7567a01c585e1144e2cab88ddb6aa85d
Frozen addon            : p_cf_bornbeast_m4a4_p4_frozen_noop_01
Runtime slot            : M4A4
Internal model          : weapons/v_rif_m4a1.mdl
Inspect policy          : frozen_noop_safe
final_target_identity   : false
final_cf_material       : false
```

已证明：

- fresh local CF LTB 能进入完整 Source 1 构建；
- M4A4 skeleton / sequence / attachment contract 可工作；
- mesh-to-bone、SMD/QC、studiomdl、roundtrip、validation、package、deploy 可闭环；
- runtime changed-state 用户 Gate 通过。

P4 从未证明：

- Prototype 就是最终雷神；
- CF 原生材质已经正确恢复；
- external texture 可作为 final；
- visible Inspect / hand-finger IK 已完成；
- CF 原动画、声音、world model 已最终化。

### RV-04 冻结反例

4/4 高风险 mutation 被预定 Gate 拒绝：

```text
unsafe output root              -> manifest_contract
same sequence count/wrong name -> sequence_names_and_count
bone semantic swap             -> smd_manifest_bone_corners
missing critical VTF           -> material_closure
```

`material_closure` 只证明 Source 1 引用闭合，不证明上游 CF 像素语义正确。

---

# 3. P4-M01 — Native Material Recovery

目的：补齐 P4 从未证明的 CF 原生材质 fidelity。

历史 Prototype 曾使用 external CS1.6 BornBeast texture，因此必须把原生材质作为独立 hard requirement。

目标链：

```text
BornBeast local LTB / UV
+ DTX
+ Alpha / Normal / Specular TGA
+ WeaponShader CFG
+ same-family variants
-> container / storage evidence
-> real mesh/piece material binding
-> CFG / render semantics
-> native-only composition
-> reproducible Source 1 mapping
```

最终可见材质只能来自：

```text
local_cf
verified deterministic derivative of local_cf
verified engine/CFG semantics applied to local_cf
```

禁止 final pixels 来自：

- external MOD texture；
- 官网/网络图片；
- AI 生成/补全贴图；
- 从 reference 反采样后回写的颜色。

### P4-M01 PASS Gate

只有同时满足：

1. geometry / UV 来自 local CF；
2. 实际材质资源都有 path + SHA；
3. mesh/piece -> material/texture binding 有结构或 direct consumer evidence；
4. CFG/render semantics 足够解释真实消费方式；
5. visible color 100% local CF / verified semantics；
6. 0 external pixels；
7. clean output 可重复；
8. BornBeast native result 可稳定辨认；

才能判：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

---

# 4. P4-M01-R1 / N01 — 冻结技术结论

## 4.1 R1

R1 已完成早期材质 evidence 纠错，状态：

```text
P4-M01-R1 = ACCEPTED / COMPLETE
```

## 4.2 DTX

```text
no formal LithTech -2/-3/-5 header     VERIFIED_STRUCTURAL
not LZMA                               VERIFIED_STRUCTURAL
whole-file 3-byte periodic payload     VERIFIED_STRUCTURAL
one fixed-FF byte position             VERIFIED_STRUCTURAL
1024 stride                            STRONG_HYPOTHESIS
single continuous image / no mips      STRONG_HYPOTHESIS
1043/1046 size%2048==164               VERIFIED_CORPUS_STATISTIC
2212-byte tail semantics               OPEN
RGB/BGR/channel order                  OPEN
```

## 4.3 TGA

Formal inserted repair：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

BornBeast Alpha/Normal/Specular repair 已结构验证；文件名不等于 shader role 证明。

## 4.4 WeaponShader CFG

237/237 文件满足：

```text
non-0xFF bytes occupy one fixed offset-mod-3 phase per file
other two phases are constant 0xFF
```

已接受测量：

```text
BornBeast      phase 2 / 164
Transformers   phase 1 / 169
Jewelry        phase 2 / 214
BlueDiamond    phase 2 / 166
```

证据等级：

```text
single-mod3 structure          STRUCTURALLY_VERIFIED
per-file measured sequence     OBSERVED
cross-skin differences         DIFFERENTIAL_SUPPORTED
CFG = 1D LUT                   HYPOTHESIS
CFG = packed shader constants  HYPOTHESIS
actual semantic consumer       OPEN_UNRESOLVED
Source1 mapping                SOURCE1_DESIGN_CANDIDATE
```

## 4.5 ArmModel positive control

ArmModel text CFG 已证明 engine-format 中存在：

```text
[Textures]
[Techniques]
[Properties] PieceIndex
```

但不能直接推出 weapon 使用相同 contract。

## 4.6 Weapon binding

```text
LTB post-mesh short ASCII field exists        STRUCTURALLY_VERIFIED
short id == texture/material slot             NOT PROVEN
repo parser semantic material use             NOT PROVEN
ObjExporter Models->ModelTextures mirroring   TOOL_BEHAVIOR
original CF piece->texture binding            OPEN_UNRESOLVED
```

Repo exporter 的路径镜像不是原 CF runtime proof。

## 4.7 N01 scope freeze

最终 scanner scope：

```text
all_files_seen_post_low_value_filter = 102382
config_candidates_seen               = 261
config_candidates_decoded            = 18
config_index_keys                    = 18
config_index mapping tuples          = 72
raw_scan_files_seen                  = 355
raw_scan_files_decoded               = 355
```

统一 predicate：

```python
is_config_candidate = (
    ext in CONFIG_EXT
    and is_likely_model_texture_config(rel, ext)
)
```

Scoped negative：

```text
BornBeast      text-config hits = 0
Transformers   text-config hits = 0
Jewelry        text-config hits = 0
BlueDiamond    text-config hits = 0
.dat consumer hits             = 0
BornBeast derived-output hits  = 4 / DERIVED_OUTPUT_HIT only
```

状态：

```text
P4-M01-N01 evidence    = COMPLETE / FROZEN
N01 substantive        = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
engine binding closure = OPEN_UNRESOLVED
```

这意味着旧 corpus 已达到当前证据边界；它不意味着项目没有后续路径。具体下一步由 `task.md` 定义。

---

# 5. P5 — 最终 M4A1-雷神资产识别

## P5-T01 — Official reference

```text
P5-T01 = PASS / USER_REFERENCE_CONFIRMED
Target = M4A1-雷神
```

Ground truth：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

## Legacy pre-scan

历史 commit：

```text
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2
```

保留统计：

```text
data inventory       165082 files
recalled candidates    2856
LTB candidates         1281
canonical inspected     441
```

旧 score 只表示召回优先级，不表示 identity confidence。

## P5-T02

依赖 P4-M01 native material method。

恢复后 pipeline：

```text
validated material method
-> Transformers family inventory
-> Transformers-specific DTX/TGA/CFG revalidation
-> material binding
-> native finalist render
-> USER LOCAL-CANDIDATE GATE
-> USER_VISUAL_MATCH_CONFIRMED
```

`USER_VISUAL_MATCH_CONFIRMED` 仍不等于最终 `IDENTITY_CONFIRMED`。

## P5-T03

建立最终 Resource Graph：

```text
PLAYERVIEW LTB
-> texture/material/shader resources
-> world/QV
-> audio
-> animation/config
```

记录 path / SHA / size / relation / source / confidence。

## P5-T04

最终 Review 输出：

```text
IDENTITY_CONFIRMED
IDENTITY_PROBABLE_NEEDS_EVIDENCE
REWORK_CANDIDATE_SEARCH
```

只有 `IDENTITY_CONFIRMED` 才进入 P6。

---

# 6. P6 — Final replacement / release

在最终 identity 和 native material closure 都成立后：

```text
final assets
-> clean build
-> validation
-> package
-> deploy
-> release-quality runtime verification
```

---

# 7. P7 — Enhancement

不阻塞前述 closure：

```text
visible Inspect
hand / finger IK
Blender retarget / penetration avoidance
CF original animation
CF original sound
world model / extra polish
```

---

# 8. Evidence 等级约定

| Grade | 含义 |
|---|---|
| `OBSERVED` | 当前样本直接观测 |
| `STRUCTURALLY_VERIFIED` | 格式/二进制结构机械验证 |
| `VERIFIED_CORPUS_STATISTIC` | 在明确 corpus/scope 内可复现统计 |
| `DIFFERENTIAL_SUPPORTED` | 多样本差分支持 |
| `STRONG_HYPOTHESIS` | 强线索但仍有替代解释 |
| `HYPOTHESIS` | 待验证解释 |
| `TOOL_BEHAVIOR` | 本仓库工具行为，不等于原 CF runtime |
| `SOURCE1_DESIGN_CANDIDATE` | Source 1 实现候选，不等于 CF 原语义 |
| `NEGATIVE_RESULT_SCOPED` | 仅在声明范围内成立的 negative |
| `OPEN_UNRESOLVED` | 当前未闭合 |
| `BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS` | 缺 engine consumer 新输入 |

禁止把 filename convention、视觉相似、单一统计或 hypothesis 直接升级为 verified fact。

---

# 9. 关键 Evidence / Checkpoint 索引

## P4

```text
assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json
work/m4a1_s_bornbeast/p4_prototype_01/
```

## P4-M01 / N01

```text
work/m4a1_s_bornbeast/p4_m01_native_material/
work/m4a1_s_bornbeast/p4_m01_native_material/n01/
```

## P5

```text
work/p5_leishen/t01_reference/
work/p5_leishen/t01/
work/p5_leishen/t02/
```

关键历史提交：

```text
10aa99b770e575300ca3c28324ef3de3d5b70c6b  P4 frozen baseline
fd61d6ae7567a01c585e1144e2cab88ddb6aa85d  RV-04 evidence
632ede449578f688cea7e6b5f40cbf03700aaaa5  P4-M01 initial exploration
0dc5793b6e47cb20da9e44aebcec2195194bd6f2  R1 narrow correction
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19  N01 Phase-0 cleanup
69c03d8769db2107cd94cae11accc750716466ae  scanner/lineage repair
ea11ba143d859193213f24ab92248ff8a576b135  runtime-consumer bounded search
46fcacebbc631fc05e0d491470b5e5482bca4533  evidence cleanup
95b6bb363a5f00daf01193f53e2a27cff9cea3f8  provenance/closure cleanup
65292c742d545459974c56aec494d1d9c44039a8  final config-scope guard
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2  P5 legacy pre-scan
```

---

# 10. 文档职责

```text
README.md  项目介绍、角色分工、阅读入口
AGENTS.md  只规定 Git 操作
plan.md    本文件：长期 pipeline + 冻结事实 + Gate
task.md    当前动态任务 + 可尝试实现路径 + 验收要求
```

领导/规划 Agent 在每轮 Review 后主要更新 `task.md`；只有 pipeline、Gate 或冻结事实发生长期变化时才更新 `plan.md`。
