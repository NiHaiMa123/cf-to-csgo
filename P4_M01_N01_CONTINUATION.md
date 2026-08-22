# P4_M01_N01_CONTINUATION.md — df48 review; current entry = Phase 1 evidence repair / consumer closure

> parent_task: `P4-M01`
>
> task_id: `P4-M01-N01`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **ACTIVE / PHASE1_EVIDENCE_REWORK**
>
> 本文件是 [`P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md`](P4_M01_N01_ENGINE_CONSUMER_TASK_SPEC.md) 的当前 continuation / Review overlay。若旧 continuation 与本文件冲突，以本文件为准；`plan.md` 第 1 节继续保持项目 authoritative coarse status：P4-M01 尚未完成，P5-T02 继续暂停。

---

## 1. 最新 Review 输入

最新 Local Executor 提交：

```text
df48af65f2273772fedd7f61c8c230b2184cf8b4
P4-M01-N01: Complete Phase 1-5 consumer discovery, differential and binding closure evidence
```

该提交新增：

```text
scripts/material_recovery/n01_phase1_consumer_search.py
scripts/material_recovery/n01_phase1_to_phase5_runner.py

work/m4a1_s_bornbeast/p4_m01_native_material/n01/
  consumer_candidate_matrix.json
  consumer_search_report.md
  weapon_material_differential.json
  cfg_consumer_report.json
  channel_semantics_report.json
  engine_binding_closure.json
```

本轮实际 executor benchmark provenance（用户确认）：

```text
executor_model = Gemini 3.7 Flash
executor_harness = user-selected / unspecified
```

注意：模型信息只用于 benchmark/provenance，不改变 task acceptance criteria。

---

## 2. Chat/Sol Review 结论

```text
P4-M01-N01 df48 result = REWORK_REQUIRED
Path B closure             = NOT ACCEPTED
READY_FOR_NATIVE_MATERIAL_COMPOSITION = NOT ACCEPTED
P4-M01                     = ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P5-T02                     = PAUSED_BY_P4_M01
```

`df48` 不是无效提交。它产生了可复用的结构 evidence，尤其是 LTB post-mesh short field differential、ArmModel material positive control，以及 WeaponShader 237/237 mod-3 structural observation。

但它存在 scanner implementation bug、硬编码 evidence、内部数据冲突，以及从 structural correlation 直接升级到 engine/material semantics 的 evidence-boundary violation，因此不能作为 N01 PASS。

---

## 3. 必须修复的确定性问题

### 3.1 Phase 1 extension normalization bug

`n01_phase1_consumer_search.py` 中 extension set 使用带点形式：

```python
TEXTURE_EXT = {".dtx", ".dds", ".tga", ...}
CONFIG_EXT = {".cfg", ".ini", ".txt"}
PREFERRED_MAP_EXT = {".apf", ".cft", ...}
```

但扫描得到：

```python
ext = os.path.splitext(fn)[1].lower().lstrip(".")
```

随后执行类似：

```python
if ext in TEXTURE_EXT
if ext in CONFIG_EXT
```

因此 `dtx/cfg/txt` 与 `.dtx/.cfg/.txt` 永远不相等。内部 helper 又重复 `lstrip('.')` 后与带点集合比较。

影响：由该 scanner 产生或声称支持的 texture/config/mapping negative evidence 不能接受。

修复要求：

```text
- 全项目该 N01 scanner 内 extension representation 统一；
- 要么全部保留 leading dot，要么全部去 dot；
- 加最小 self-test/assert，至少覆盖 .dtx/.tga/.cfg/.txt/.cft；
- 修复后重新执行 Phase 1 scoped scan；
- 新报告必须记录实际 scanned file counts / categories / hit counts。
```

### 3.2 Complete runner 的 Phase 1 evidence 不能硬编码结论

`n01_phase1_to_phase5_runner.py::run_phase1_consumer_discovery()` 当前把以下内容作为 literal data 写入：

```text
BornBeast_hit = NEGATIVE
status = verified_code_behavior
CrossFire runtime uses direct directory mirroring
primary_engine_binding_mechanism
```

并直接生成 matrix/report。

这不是 evidence producer；它是预写结论生成器。

修复要求：

```text
observation/scanner output
-> normalized evidence object
-> evidence grade
-> report serialization
```

报告中的 hit/negative/count/path/status 必须来源于实际运行结果或明确引用的既有 accepted evidence，不得由目标结论反向 hardcode。

### 3.3 Phase 2 与 Phase 3 BornBeast CFG 数据冲突

`weapon_material_differential.json` 的实际文件读取结果显示 BornBeast CFG：

```text
size         492
phase        2
sample_count 164
first_offset 2
last_offset  491
min_val      6
max_val      33
sha256       78f0bd5024f70624594c6b7ebd470094a3642fce8cf7df596407d40dae0ebc87
```

但 `run_phase3_cfg_consumer()` / `cfg_consumer_report.json` 硬编码为：

```text
size         496
phase        0
sample_count 164
min_val      0
max_val      42
```

因此当前 Phase 3 report INVALID。

修复要求：

```text
- Phase 3 必须消费 Phase 2 的实测对象或重新读取同一文件；
- 禁止手填 sample_count/phase/size/min/max；
- 每个 target 保存 input relative path + SHA256；
- 增加 cross-phase consistency gate；任何同一 SHA 的 size/phase/count 不一致必须 non-zero fail。
```

---

## 4. Evidence grade 修正

### 4.1 WeaponShader CFG

保留：

```text
237/237 single-mod3 structural form   STRUCTURALLY_VERIFIED
per-file sample sequence/count        OBSERVED
same-family differences               DIFFERENTIAL_SUPPORTED where measured
```

不得当前升级：

```text
CFG = 1D Color/Intensity LUT          HYPOTHESIS
CFG = packed shader constants         HYPOTHESIS
CFG controls Phong exponent/boost     HYPOTHESIS / SOURCE1_DESIGN_CANDIDATE
CFG controls self-illum tint          HYPOTHESIS / SOURCE1_DESIGN_CANDIDATE
```

原 N01 rule 继续有效：

```text
consumer/reference evidence
> binary-value curve fitting
> preview appearance
```

没有找到真实 consumer contract 时，不得把值域、曲线、sample count 当 semantic proof。

### 4.2 LithTechObjExporter directory mirroring

当前 repo exporter 的：

```text
Models/PLAYERVIEW/PV-*.LTB
-> ModelTextures/PLAYERVIEW/PV-*.DTX
-> AlphaMap / NormalMap / SpecularMap / WeaponShader CFG
```

可以证明：

```text
TOOL_HEURISTIC / STRUCTURAL_CORRESPONDENCE
```

不能单独证明：

```text
CrossFire original runtime engine binding
```

因此以下旧 grade 必须撤销：

```text
primary_engine_binding_mechanism
STRUCTURALLY_VERIFIED_AND_ENGINE_CONSISTENT
```

除非新 evidence 找到原始 resource/config/consumer data path，或形成满足 N01 Path B 的多个独立 differential closure。

### 4.3 ArmModel positive control

保留并接受：

```text
ArmModel LZMA text material CFG structure       VERIFIED_STRUCTURAL
[Textures] auxiliary-map references            VERIFIED_STRUCTURAL
[Properties] PieceIndex                        VERIFIED_STRUCTURAL
piece-indexed multi-map shader architecture     ENGINE_FORMAT_POSITIVE_CONTROL
```

但不得直接推出 weapon 使用同一 explicit text binding format。

### 4.4 Weapon LTB post-mesh short field

`df48` 对 BornBeast / Transformers / Jewelry / UltimateGold 做出的跨样本提取可以保留：

```text
u8-prefixed short ASCII values such as "0".."8" = STRUCTURALLY_VERIFIED FIELD
```

当前命名建议：

```text
post_mesh_short_id
piece_candidate_id
```

暂时不要正式命名为：

```text
texture_slot_id
material_slot_id
```

直到 consumer / differential 能证明语义。

---

## 5. 当前唯一 substantive question

下一轮不要再次尝试“完成 Phase 1–5”。先闭合最关键的一跳：

```text
LTB mesh / post_mesh_short_id
-> piece/material identity
-> texture family / material resource
-> WeaponShader CFG role
```

当前已知但仍不足：

```text
LTB 中存在稳定 short IDs
+ basename/directory 上存在 DTX/TGA/CFG family
+ ArmModel 存在 PieceIndex + multi-map shader positive control
+ WeaponShader CFG 有稳定 structural form
```

缺失的是：

```text
short ID / piece identity -> material/texture-set consumer binding
```

只有文件名相似、目录镜像、视觉一致、sample-count fit，均不等于 direct binding。

---

## 6. 下一位 Executor 固定执行顺序

用户准备切换 executor benchmark：

```text
Model: Gemini 3.1 Pro
Harness: user-selected / unspecified
```

Task 仍保持 agent-agnostic；以上只是本轮 provenance context。

### Step 1 — 修 scanner，不扩展研究范围

修：

```text
scripts/material_recovery/n01_phase1_consumer_search.py
```

只处理 extension normalization 和由此受影响的 scan/evidence generation。

执行后重新生成：

```text
n01/consumer_candidate_matrix.json
n01/consumer_search_report.md
```

要求 raw counts 可审计。

### Step 2 — 修 Phase 2/3 data lineage

修：

```text
scripts/material_recovery/n01_phase1_to_phase5_runner.py
```

重点：

```text
- 删除 CFG target hardcode values；
- Phase 3 使用 Phase 2 实测数据；
- 加 SHA/size/phase/count consistency gate；
- 不自动运行 Phase 4/5 closure；
- runner success 不得等价于 N01 PASS。
```

重新生成：

```text
n01/weapon_material_differential.json
n01/cfg_consumer_report.json
```

### Step 3 — 专门追 binding key

优先沿 repo 现有 code/data relation：

```text
LithTechModelTextureConfigIndex.cs
LithTechTextureMappingScanner.cs
LithTechDatTextureReferenceIndex.cs
TextureReferenceResolver.cs
LithTechModelTextureLoader.cs
LithTechModelDecoder.cs
LithTechObjExporter.cs
CfgTextDecoder.cs
CfgBinaryStripDecoder.cs
```

但目标不是列类名，而是回答：

```text
谁产生 key？
谁消费 key？
key 的 raw field/string/offset 是什么？
是否实际到达 texture/material resource？
BornBeast + Transformers + Jewelry + control 是否同步成立？
```

每个 candidate 要有：

```text
candidate consumer/resource
source path
reference direction
raw key/field/offset/string
actual target hits
control hits
scan scope/count
accepted/rejected/open
evidence class
reason
```

### Step 4 — 到此 handoff，不强行 Phase 5

本轮最低合格 handoff：

```text
scanner bug fixed + rerun
CFG cross-phase inconsistency fixed
hardcoded evidence removed
binding investigation advanced with auditable evidence
```

如果找到 direct consumer，记录并继续验证。

如果仍找不到，明确：

```text
OPEN_UNRESOLVED / NEGATIVE_RESULT_SCOPED
```

然后提交 handoff；**不得为了完成 Phase 5 而生成 READY closure。**

---

## 7. 当前接受 / 拒绝矩阵

### 接受并冻结，不要重跑

```text
P4 baseline                         PASS / FROZEN
P4-M01-R1                           ACCEPTED / COMPLETE
N01 Phase 0                         ACCEPT / FROZEN
TGA formal repair                   ACCEPT
DTX no formal header / not LZMA     VERIFIED_STRUCTURAL
DTX whole-file 3-byte periodicity   VERIFIED_STRUCTURAL
DTX 1024 stride                     STRONG_HYPOTHESIS
DTX 1043/1046 statistic             VERIFIED_CORPUS_STATISTIC
CFG 237/237 mod-3 structure         VERIFIED_STRUCTURAL
ArmModel text material format       VERIFIED_STRUCTURAL
H2 pixel-index sampling fix         ACCEPT / DIAGNOSTIC_ONLY
```

### df48 可复用但需谨慎命名

```text
LTB post-mesh short ASCII field     STRUCTURALLY_VERIFIED
weapon family file co-location      OBSERVED / STRUCTURAL_CORRESPONDENCE
same-family asset differential      PARTIALLY_REUSABLE
```

### df48 当前拒绝/撤销

```text
Phase 1 scanner-derived negatives without rerun        INVALID
Phase 3 hardcoded CFG target metrics                    INVALID
CFG = LUT / fixed shader semantic conclusion            NOT ACCEPTED
ObjExporter mirroring = original engine binding proof   NOT ACCEPTED
AlphaMap = emissive mask as recovered CF semantic       NOT VERIFIED
SpecularMap = gloss/roughness semantic                  NOT VERIFIED
CFG -> Source1 Phong/selfillum mapping as recovered fact NOT VERIFIED
Path B engine_binding_closure                            NOT ACCEPTED
READY_FOR_NATIVE_MATERIAL_COMPOSITION                   NOT ACCEPTED
```

---

## 8. Git / evidence discipline

继续遵守 `AGENTS.md`：

- handoff 只认 `master`；
- `data/**` local-only，绝不上传；
- 不 broad stage；
- 不 force push / destructive reset/clean；
- 每个 negative 写 scan scope/count；
- 每个 local-only input 写 relative path / SHA / size；
- report conclusion 必须由实际结果生成，不反向 hardcode；
- Local Executor 不自行把 `plan.md` 改 P4-M01 PASS；
- 不执行 P5-T02 / final visual gate。

建议提交前运行：

```bash
git status --short --branch
git diff --cached --name-only
```

只 stage 本轮明确修改的脚本和 `n01/**` evidence。

---

## 9. 当前状态 / 下次 Review 起点

```text
P4 baseline        PASS / FROZEN
P4-M01             ACTIVE / NATIVE_MATERIAL_RECOVERY_INCOMPLETE
P4-M01-R1          ACCEPTED / COMPLETE
P4-M01-N01 Phase 0 ACCEPT / FROZEN
P4-M01-N01         ACTIVE / PHASE1_EVIDENCE_REWORK
P5-T02             PAUSED_BY_P4_M01
```

下一次 Chat/Sol Review：

```text
base = df48af65f2273772fedd7f61c8c230b2184cf8b4
review only new evidence/fixes after this commit
```

不要重新执行 Phase 0，也不要把 `df48` 已生成的 Phase 5 READY 文案当 authoritative state。
