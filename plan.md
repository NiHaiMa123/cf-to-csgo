# CF 武器 -> CS:GO Legacy Source 1 — 项目计划与唯一执行入口

> 最后更新：2026-08-22  
> **本文件是项目唯一 authoritative progress / workflow / task state。**  
> 所有 Agent 先读 `AGENTS.md`，再读本文件。  
> 历史 Task Spec / Continuation / Review 已合并到本文；需要逐轮细节时查 Git history 和 `work/**` evidence。

---

## 0. 30 秒读懂现在做到哪了

已经解决：

```text
CF LTB / 模型基础解析
-> M4A4 Source 1 skeleton / sequence / attachment contract
-> SMD / QC / VMT / VTF build
-> studiomdl / Crowbar roundtrip / validation
-> package / staging / MIGI deploy
-> changed-runtime user Gate
```

这条 **CF 武器 -> CS:GO Legacy Source 1** 技术链已经 `PASS / FROZEN`。

现在真正没解决的是：

```text
CF weapon piece / mesh
-> 原游戏 material / shader binding key
-> local DTX/TGA texture family
-> WeaponShader CFG 的真实 consumer / semantic
```

现有 repo + 已解包静态 corpus 里没有原 CF client/runtime consumer code，所以这部分已经到达当前输入的证据边界：

```text
P4-M01-N01 evidence cleanup = COMPLETE / FROZEN
P4-M01-N01 substantive      = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

**当前没有可执行的“继续扫描同一 corpus”任务。** 有意义的下一步是获得新的 CF client/runtime artifact 或同等级 documented binding contract，然后只做静态、只读逆向。

---

# 1. 唯一权威状态

| 阶段 / Task | 当前状态 | 说明 |
|---|---|---|
| P0-P3 | `DONE / HISTORICAL` | 资源处理、模型研究、Source 1 前置基础 |
| P4 baseline | **`PASS / FROZEN`** | 模型 -> Source 1 -> package -> MIGI 技术链冻结 |
| P4-M01 | **`ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE`** | BornBeast 原生 CF 材质尚未闭合 |
| P4-M01-R1 | `ACCEPTED / COMPLETE` | 早期材质 evidence 纠错已完成 |
| P4-M01-N01 Phase 0 | `ACCEPT / FROZEN` | consistency cleanup 已接受 |
| P4-M01-N01 evidence | **`COMPLETE / FROZEN`** | scanner/provenance/scope/closure 文档与代码清理完成 |
| P4-M01-N01 substantive | **`BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS`** | 缺原 CF engine/client consumer code |
| P5-T01 | `PASS / USER_REFERENCE_CONFIRMED` | M4A1-雷神官方目标图已由用户确认 |
| P5 LEGACY PRE-SCAN | `EXECUTION_PASS / PRESERVED_FOR_REUSE` | 本地候选广召回结果保留 |
| P5-T02 | **`PAUSED_BY_P4_M01`** | 等可信 native material method 后恢复 |
| P5-T03 | `BLOCKED_BY_T02` | Resource Graph / provenance closure |
| P5-T04 | `BLOCKED_BY_T03` | 最终 identity Review |
| P6 | `BLOCKED_BY_P5` | 最终替换 / 发布质量 |
| P7 | `FUTURE` | visible Inspect、IK/retarget、CF 原动画/声音等增强 |

### 当前执行决策

```text
没有新增 runtime/client artifact
    -> 不创建新的 N01 scan / CFG 猜测 / basename 搜索任务
    -> 保持 blocker

有新增 runtime/client artifact
    -> 按 §5.6 静态逆向路线重新打开 N01 substantive

未来 P4-M01 被 Review 为 NATIVE_MATERIAL_RECOVERED
    -> 恢复 P5-T02
```

---

# 2. 整体流程

```text
Track A — 资源与转换
CF REZ / local assets
-> LTB / DTX / TGA / CFG / audio extraction
-> model / UV / skeleton / animation evidence
-> Source 1 conversion
-> compile / validate / package / MIGI
-> P4 baseline PASS / FROZEN

Track B — 原生材质
BornBeast local material family
-> container/storage evidence
-> real material binding
-> CFG/render semantics
-> native-only composition
-> P4-M01 PASS / NATIVE_MATERIAL_RECOVERED

Track C — 最终雷神识别
official reference
+ preserved local candidate pool
+ validated native material method
-> Transformers/native finalists
-> user candidate Gate
-> Resource Graph
-> final identity Review
-> P6 release

Track D — 后续增强
visible Inspect / hand-finger IK / retarget
CF original animation / sound / world model
-> P7
```

当前卡点位于 **Track B 的 engine-side binding/consumer**。

---

# 3. P4 baseline — PASS / FROZEN

## 3.1 冻结身份

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

## 3.2 已证明的链

```text
local CF LTB
-> B3
-> C1
-> C3
-> Source build / Crowbar roundtrip
-> validation
-> package / staging
-> deploy
-> user changed-runtime Gate
```

P4 baseline 证明 conversion/build/package/MIGI/runtime contract 能稳定工作。

## 3.3 RV-04 独立反例

4/4 高风险 mutation 都被预定 Gate 拒绝：

```text
unsafe output root                 -> manifest_contract
same sequence count, wrong name    -> sequence_names_and_count
Parent/Clip bone semantic swap     -> smd_manifest_bone_corners
missing critical VTF               -> material_closure
```

注意：`material_closure` 只证明 Source material reference 对缺失 VTF 有 Gate，**不证明 VTF 像素来自正确 CF 原生材质语义**。

## 3.4 User Gate 与保留风险

用户历史确认 frozen/no-op addon：

```text
no crash / obvious runtime error
no visible Inspect motion (符合 frozen_noop 设计)
weapon state returned normally
Fire / Reload / Switch remained usable
```

仍未测试或未闭合：

```text
console_errors                 not_tested
rollback_after_disable         not_tested
visible Inspect / hand IK      -> P7
CLI inspect-policy override    non-blocking risk
fully manifest-driven toolchain non-blocking risk
working-tree SHA / Git blob EOL portability  provenance risk
```

P4-M01 不得为了解材质而重写这条 frozen conversion contract。

---

# 4. P4-M01 — BornBeast 原生材质恢复

## 4.1 为什么必须补做

历史 Prototype 可辨识材质曾使用：

```text
work/m4a1_s_bornbeast/materials/external/cs16_textures/02_PV-M4A1_S_BORNBEAST.bmp.png
```

因此“枪能进 CSGO”已经成立，但“CF 原版材质被正确恢复”并没有成立。

## 4.2 最终目标

只使用本地 CF：

```text
BornBeast LTB / UV
+ DTX
+ Alpha / Normal / Specular TGA
+ WeaponShader CFG
+ same-family variants
-> decode/container evidence
-> real material binding
-> CFG/render semantics
-> native-only composition
-> reproducible closure
```

最终可见材质输入只允许：

```text
local_cf
verified deterministic derivative of local_cf
verified engine/CFG semantics applied to local_cf
```

外部 MOD texture、官网图、网络图、AI 生成/补全 texture 只能 `reference_only / differential_control`，不能贡献 final pixels。

## 4.3 P4-M01 PASS Gate

只有同时满足下列核心要求，Chat/Sol 才能判：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

要求：

1. geometry / UV 来自 local CF LTB；
2. 实际使用的 base/lookup/alpha/normal/specular/emissive/detail 等都有 path + SHA；
3. mesh/piece -> material/texture binding 有结构或 direct consumer evidence；
4. CFG/render semantics 足够支持重建，而不是“能画成彩条”；
5. visible color 全部 local CF / verified semantics；
6. 0 external pixels；
7. clean output 可重复；
8. BornBeast 主要颜色分区、图案、UV、高光/能量区域稳定可辨认；
9. 外部图只参与对照。

当前由于 §5 blocker，这个 Gate 尚未满足。

---

# 5. P4-M01-N01 — 最终已接受结果

最新完整 cleanup executor commit：

```text
65292c742d545459974c56aec494d1d9c44039a8
P4-M01-N01: F3 scope guard - unified is_config_candidate predicate
```

## 5.1 N01 scanner / scope 已冻结

统一 config candidate predicate：

```python
is_config_candidate = (
    ext in CONFIG_EXT
    and is_likely_model_texture_config(rel, ext)
)
```

以下三个输出都只在同一个 predicate 内产生：

```text
config_candidates_seen
config_candidates_decoded
config_index
```

并保留 invariant：

```text
config_candidates_decoded <= config_candidates_seen
len(config_index_keys) == config_candidates_decoded
```

当前 measured scope：

```text
all_files_seen_post_low_value_filter = 102382
config_candidates_seen               = 261
config_candidates_decoded            = 18
config_index_keys                    = 18
config_index mapping tuples          = 72
raw_scan_files_seen                  = 355
raw_scan_files_decoded               = 355
```

18 个真实 mapping config 都是 ArmModel CFG。

Scoped negative：

```text
BornBeast      text-config hits = 0
Transformers   text-config hits = 0
Jewelry        text-config hits = 0
BlueDiamond    text-config hits = 0
.dat consumer hits             = 0
BornBeast derived-output hits  = 4 (DERIVED_OUTPUT_HIT only)
```

这些只是声明 scope 内的 negative，不是“整个游戏绝对不存在”的 universal negative。

## 5.2 DTX / TGA 当前证据等级

DTX：

```text
no formal LithTech -2/-3/-5 header     VERIFIED_STRUCTURAL
not LZMA                               VERIFIED_STRUCTURAL
whole-file 3-byte periodic payload     VERIFIED_STRUCTURAL
one fixed-FF byte position             VERIFIED_STRUCTURAL
1024 stride                            STRONG_HYPOTHESIS
single continuous image / no mips      STRONG_HYPOTHESIS
1043/1046 size%2048==164               VERIFIED_CORPUS_STATISTIC / NOT universal
2212-byte tail semantics               OPEN
RGB/BGR/channel order                  OPEN
```

TGA inserted repair：

```text
footerOffset = TRUEVISION signature - 8
headerOffset = footerOffset + 26
```

BornBeast Alpha/Normal/Specular formal repair 已接受为 structural evidence；map 的 shader role 仍不能仅由文件名推导。

## 5.3 WeaponShader CFG 当前证据等级

237/237 WeaponShader CFG：

```text
non-0xFF bytes occupy one fixed offset-mod-3 phase per file
other two phases are constant 0xFF
```

这是 `STRUCTURALLY_VERIFIED`。

已接受 measured samples：

```text
BornBeast      phase 2 / 164
Transformers   phase 1 / 169
Jewelry        phase 2 / 214
BlueDiamond    phase 2 / 166
```

语义仍是：

```text
CFG = 1D LUT                    HYPOTHESIS
CFG = packed shader constants   HYPOTHESIS
actual CF semantic consumer     OPEN_UNRESOLVED
Source1 Phong/selfillum mapping SOURCE1_DESIGN_CANDIDATE
```

不能把 Source 1 设计映射倒推成 CF 原引擎事实。

## 5.4 ArmModel positive control 与 weapon binding

ArmModel LZMA text material CFG 已证明 CF engine-format 能存在：

```text
[Textures] named texture references
[Techniques]
[Properties] PieceIndex
```

但这只是 **ArmModel positive control**，不能推出 weapon 使用同一 contract。

Weapon 侧当前：

```text
LTB post-mesh short ASCII field exists       STRUCTURALLY_VERIFIED
short id == texture/material slot            NOT PROVEN
repo parser semantically consumes short id   NO / TOOL-CODE OBSERVATION
repo ObjExporter Models->ModelTextures mirror TOOL_BEHAVIOR / STRUCTURAL_CORRESPONDENCE
original CF piece->texture binding           OPEN_UNRESOLVED
```

Repo exporter 的 filename/path mirroring **不是**原 CF runtime binding proof。

## 5.5 最终 blocker

`engine_binding_closure.json` 当前核心状态：

```text
closure_path          = Path B - Incomplete
status                = OPEN_UNRESOLVED
substantive_blocker   = BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
```

当前 corpus 没有发现可用于 engine-side consumer tracing 的：

```text
CF client executable
engine/render/resource DLL/module
original runtime / REZ bundle containing consumer code
compiled shader/runtime package
weapon-format material/resource table
```

所以还不能证明：

```text
post_mesh_short_id / piece identity
-> original CF material/shader resolver
-> texture family binding
-> WeaponShader CFG semantic consumer
```

**不要再换 Gemini / MiniMax / Luna 等模型重复扫描同一 corpus。** 当前缺的是输入证据，不是再做一轮相同 basename / config / curve fitting 搜索。

## 5.6 Blocker 解除条件与唯一允许路线

只有新增以下任一等级输入，才重新打开 N01 substantive：

```text
CrossFire client executable
engine / render / resource DLL/module
original runtime bundle / REZ containing consumer code
shader/runtime package
可靠 documented / reverse-engineered material-piece binding contract
```

二进制安全规则：

```text
只做 static / read-only
不执行未知 client/runtime binary
不上传 raw binary 或 data/**
提交 relative path / SHA256 / size / string offset / xref / call-chain evidence
```

重新打开后的固定路线：

```text
strings / resource names
-> static xref
-> loader / resolver call chain
-> piece / material key use
-> texture family binding
-> WeaponShader CFG consumer contract
```

找到可信 consumer 后，再回到 P4-M01 native composition / final closure；N01 本身不自动恢复 P5。

---

# 6. P5 — 最终 M4A1-雷神识别

## 6.1 P5-T01 — 已完成

```text
P5-T01 = PASS / USER_REFERENCE_CONFIRMED
Target = M4A1-雷神
```

Ground truth evidence：

```text
work/p5_leishen/t01_reference/official_reference.json
work/p5_leishen/t01_reference/reference_report.md
```

除非用户明确否决、evidence 丢失或 page/image relation 被证明错误，否则不重跑 T01。

## 6.2 Legacy pre-scan — 保留复用

历史执行 commit：

```text
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2
```

结果：

```text
data inventory       165082 files
recalled candidates    2856
LTB candidates         1281
canonical inspected     441
```

主要 evidence：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
work/p5_leishen/t01/scan_report.md
work/p5_leishen/t01/execution.json
```

旧 score 只是召回优先级，不是 identity confidence。没有 evidence 损坏就不重新扫描全部 16 万文件。

## 6.3 P5-T02 — 当前暂停

已经完成：

```text
official reference
-> legacy candidate reuse
-> M4/M4A1 PLAYERVIEW narrowing
-> exact SHA dedup
-> geometry clusters
-> C029 / C103 finalist diagnostics
```

以下仍只允许 diagnostic：

```text
C029/C103 gray geometry                       diagnostic_only
Transformers DTX headerless-BGR24             unvalidated hypothesis
raw PV DTX + UV                               diagnostic_only
Alpha/Specular scalar approximation           diagnostic_only
raw RGB strip CFG preview                     not semantic decoding
```

因此当前禁止要求用户在灰模/伪材质之间强选。

只有：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

后才恢复 T02。

恢复后的固定路线：

```text
validated P4-M01 material method
-> M4A1_S_Transformers family inventory
-> revalidate Transformers-specific DTX/TGA/CFG
-> recover Transformers material binding
-> minimal evidence-backed semantic extension if needed
-> native material acceptance Gate
-> fixed-view native-material finalist renders
-> USER LOCAL-CANDIDATE GATE
-> USER_VISUAL_MATCH_CONFIRMED
```

`USER_VISUAL_MATCH_CONFIRMED` 仍不是最终 `IDENTITY_CONFIRMED`。

## 6.4 P5-T03 / T04

T03 在 T02 后建立完整 Resource Graph：

```text
PLAYERVIEW LTB
-> base/lookup/DTX/TGA maps
-> shader/CFG/render-style
-> QV/world
-> WAV
-> animation/config
```

每个资源至少记录：

```text
relative_path
sha256
size_bytes
relation
source_class
confidence / unresolved_reason
```

T04 由 Chat/Sol 最终输出之一：

```text
IDENTITY_CONFIRMED
IDENTITY_PROBABLE_NEEDS_EVIDENCE
REWORK_CANDIDATE_SEARCH
```

只有 `IDENTITY_CONFIRMED` 才进入 P6。

---

# 7. P6 / P7

## P6 — Final replacement / release

P5 final identity 成立后才做最终资产替换、clean build/package/deploy、发布质量验证。

## P7 — Enhancement

不阻塞当前 material / identity closure：

```text
visible Inspect
hand / finger IK
Blender retarget / penetration avoidance
CF original animation
CF original sound
world model / extra polish
```

---

# 8. Agent 执行决策树

每个新 Agent：

```text
1. git status --short --branch
2. read AGENTS.md
3. read plan.md
4. confirm master
5. decide from current state, not from old chat memory
```

然后：

```text
Q1: 用户是否提供了新的 CF runtime/client artifact 或 binding contract？
  NO -> 不运行新的 N01 substantive search；说明当前 blocker。
  YES -> 只做 §5.6 静态逆向，保留 path/hash/size/xref evidence。

Q2: P4-M01 是否已经被 Chat/Sol Review 为 NATIVE_MATERIAL_RECOVERED？
  NO -> P5-T02 保持 PAUSED。
  YES -> 恢复 §6.3 Transformers/native finalist flow。

Q3: T02 是否达到 USER_VISUAL_MATCH_CONFIRMED？
  NO -> 不进入 T03/T04。
  YES -> 建 Resource Graph，再做 final identity Review。
```

Local Executor 可以更换模型/Agent，但 acceptance criteria 不随模型改变。实际 executor provenance 来自 harness/runtime 显示；commit `Co-Authored-By` footer 不是权威模型身份。

---

# 9. Evidence 索引

## P4 frozen baseline

```text
assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json
work/m4a1_s_bornbeast/p4_prototype_01/build_report.json
work/m4a1_s_bornbeast/p4_prototype_01/validation_report.json
work/m4a1_s_bornbeast/p4_prototype_01/upstream_trace_report.json
work/m4a1_s_bornbeast/p4_prototype_01/deploy_report.json
work/m4a1_s_bornbeast/p4_prototype_01/prototype_01_game_regression.json
work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json
```

## P4-M01 / N01

```text
work/m4a1_s_bornbeast/p4_m01_native_material/
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_candidate_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/consumer_search_report.md
work/m4a1_s_bornbeast/p4_m01_native_material/n01/weapon_material_differential.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/cfg_consumer_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/channel_semantics_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/engine_binding_closure.json
work/m4a1_s_bornbeast/p4_m01_native_material/n01/runtime_consumer_search.json
```

## P5

```text
work/p5_leishen/t01_reference/
work/p5_leishen/t01/
work/p5_leishen/t02/
```

`work/**` 中的 Markdown/JSON 是 evidence，可以保留；它们不是项目流程 authority。

---

# 10. 关键历史提交

只保留能帮助定位重大决策的 checkpoint；逐轮细节查 Git history：

```text
10aa99b770e575300ca3c28324ef3de3d5b70c6b  P4 frozen implementation baseline
fd61d6ae7567a01c585e1144e2cab88ddb6aa85d  RV-04 evidence
632ede449578f688cea7e6b5f40cbf03700aaaa5  P4-M01 initial material exploration
bded9e8a6f7f95997d9717eb8f35beb02619f153  R1 correction start
0dc5793b6e47cb20da9e44aebcec2195194bd6f2  R1 narrow correction
2344d61a1ba1dc84ddcd5a85eaed5b352f823d19  N01 Phase-0 cleanup
69c03d8769db2107cd94cae11accc750716466ae  scanner / lineage / binding-key repair
ea11ba143d859193213f24ab92248ff8a576b135  bounded runtime-consumer search
46fcacebbc631fc05e0d491470b5e5482bca4533  JSON/scope/provenance cleanup
95b6bb363a5f00daf01193f53e2a27cff9cea3f8  provenance parameterization / closure wording
65292c742d545459974c56aec494d1d9c44039a8  final unified config-scope guard
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2  P5 legacy candidate pre-scan
```

旧根目录 Task/Review Markdown 的有效结论已合并到本文件。删除它们不会删除 Git 历史，也不会删除 `work/**` evidence。

---

# 11. Evidence grade 约定

| Grade | 含义 |
|---|---|
| `OBSERVED` | 当前样本直接观测值 |
| `STRUCTURALLY_VERIFIED` | 二进制/格式结构已机械验证 |
| `VERIFIED_CORPUS_STATISTIC` | 在声明 corpus/scope 内可复现统计 |
| `DIFFERENTIAL_SUPPORTED` | 多个相关样本差分支持，但未必等于 engine semantic proof |
| `STRONG_HYPOTHESIS` | 强结构线索，仍有替代解释 |
| `HYPOTHESIS` | 待验证解释 |
| `TOOL_BEHAVIOR` | 本仓库工具实际行为，不等于原 CF runtime 行为 |
| `SOURCE1_DESIGN_CANDIDATE` | 为 Source 1 实现提出的映射，不是恢复出的 CF 原事实 |
| `NEGATIVE_RESULT_SCOPED` | 只在明确扫描范围内的 negative |
| `OPEN_UNRESOLVED` | 当前证据不足，保持未决 |
| `BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS` | 缺能继续证明 engine consumer 的新输入 |

禁止为了推动进度把 `HYPOTHESIS`、filename convention、视觉相似或单一统计相关升级成 `VERIFIED`。

---

# 12. Git / data / handoff

所有 Agent 严格遵守 `AGENTS.md`。核心底线：

```text
master only
never upload data/**
no git add . / -A / --all
no force push
no destructive reset/clean
no raw CF client/runtime binaries in Git
```

推荐同步：

```bash
git status --short --branch
git fetch origin
git pull --rebase origin master
```

项目状态只有本文件是 authority；`README.md` 是入口说明，`AGENTS.md` 是安全合同，`work/**` 是 evidence。