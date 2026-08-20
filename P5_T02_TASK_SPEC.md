# P5_T02_TASK_SPEC.md — 雷神主候选几何 / 贴图视觉验证

> task_id: `P5-T02`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Luna / 本地 Codex Agent**
>
> 当前状态: **READY_FOR_LUNA**

---

## 1. Purpose

P5-T01 已完成广召回。T02 不再按 T01 原始 score 全量扩散，而是使用 Chat/Sol 新确认的身份别名信息收敛到 `M4A1_S_Transformers` 资源族，并生成可供 Chat/Sol 做视觉 / 几何身份 Review 的本地派生证据。

本任务回答：

> “本地标准 `M4A1_S_Transformers` 第一人称模型与其本地贴图资源，是否在几何结构、材质族和视觉表现上与国服 `M4A1-雷神` reference 一致？”

本任务仍 **不允许 Luna 输出 `IDENTITY_CONFIRMED`**；最终身份结论属于 P5-T04 / Chat-Sol Review。

---

## 2. Identity anchor correction after T01

目标国服 display identity：

```text
M4A1-雷神
```

官方 reference：

```text
https://cf.qq.com/cp/a20250701wqbk/index.html
```

T01 之后 Chat/Sol 补充确认的跨服 / 内部英文别名关系：

```text
M4A1-雷神  -> M4A1-S Transformers
M4A1-黑骑士 -> M4A1-S Born Beast
```

参考别名页：

```text
https://crossfirefps.fandom.com/wiki/M4A1-S_Transformers
https://crossfirefps.fandom.com/wiki/M4A1-S_Born_Beast
```

这些网页只作为 identity reference，不进入 final game asset provenance。最终模型、贴图、Shader 等仍必须来自本地 `data/**`。

因此：

- `BornBeast` 从 T01 高分候选降级为 **negative control / 黑骑士对照**；
- `M4A1_S_Transformers` 成为 T02 **primary identity candidate family**；
- T01 score 仅表示召回优先级，不再作为 T02 identity confidence。

---

## 3. Frozen candidate set

T02 **只处理以下明确候选**，不得继续全量扫描或自行增加几十个变体。

### CANDIDATE-A — PRIMARY

第一人称模型：

```text
data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB
sha256=a0ccef5deed745f1731eb93295c630f531123288055f3c3790531b99b6e401b8
```

T01 light summary：

```text
mesh_count=11
triangle_count=5250
```

同名本地资源：

```text
data/rf017/ModelTextures/PLAYERVIEW/PV-M4A1_S_Transformers.DTX
sha256=eb11343c9c4fe1bc3abcc41130c17e581bdb3ead12ff817fa06f7446bdd2f7b8

data/rf017/ModelTextures/AlphaMap/M4A1_S_Transformers_Alpha.TGA
sha256=261b2adf7fe470fd2e06fcad3d16f438720d3d4166abc81ea37abe7758c40c2c

data/rf017/ModelTextures/NormalMap/M4A1_S_Transformers_N.TGA
sha256=4a06a775b87e7046fe09b52578396e1563d0dff4f71e0d898c62762e300504cc

data/rf017/ModelTextures/SpecularMap/M4A1_S_Transformers_S.TGA
sha256=af6589df59929072d1833690bfeb7c46b21996079305f58a1ca599c56c176b5f

data/rf017/ModelTextures/Shader/WeaponShader/M4A1_S_Transformers.CFG
sha256=f53e0ea00fa3677dd77acf77570ab1ddf7944410db41e11e1d103592dea3940d
```

辅助第三人称 / QV 资源，只做 family provenance，不作为第一人称主候选：

```text
data/rf016/Models/WEAPONS/QV-M4A1_S_Transformers.LTB
sha256=3e8479d64e751c1e0270c716e82f16030f6ceb4aaf187e344a15361f0d5ee0b2

data/rf017/ModelTextures/WEAPONS/QV-M4A1_S_Transformers.DTX
sha256=6651dd76f0883dde96afbaba9dec22ba8d00241f23f78506c713da6497c3adc5
```

### CANDIDATE-B — SAME-FAMILY CONTROL

```text
data/rf016/Models/PLAYERVIEW/PV-M4A1_S_Transformers_Classic.LTB
sha256=620778d78577ed10e5dd95df5b9a066ba18d006af57b71b9bb3dcc4303fdc464
mesh_count=11
triangle_count=5250
```

用途：证明 suffix variant 与标准无 suffix 资源的关系，防止错误选择某个皮肤 / 变体为标准雷神。

### CANDIDATE-C — NEGATIVE CONTROL

```text
data/rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB
sha256=5dbcee45c4565b2026a4e4d2d639a4b7022b4f4fc1c5ef69bc8f49fd5a6c54f7
mesh_count=11
triangle_count=5342
```

用途：该资源族对应国服黑骑士，不是标准雷神；用于检查视觉 Review 能否区分两个英雄级 M4 家族。

---

## 4. Scope / safety

### 允许读取

仅：

- 第 3 节列出的候选模型 / 贴图 / Shader 文件；
- 为导出 / 渲染所需的仓库现有 parser / CFRezManager / Blender；
- P5-T01 输出；
- 当前任务文档。

### 允许写入

只写：

```text
work/p5_leishen/t02/**
scripts/p5/**   # 仅在需要新增可复用的 T02 派生/渲染脚本时
```

### 禁止

- 修改 `data/**`；
- 修改 P4 frozen pipeline / manifest / build evidence；
- Steam / MIGI deploy；
- 继续扫描整个 `data/**`；
- 自行把其他 Transformers reskin 加入 T02；
- 将网络图片或第三方 MOD 文件作为 final asset。

---

## 5. Phase A — input identity verification

执行前重新计算第 3 节所有已列输入的 SHA-256。

若任一主候选 / 主贴图 / Shader 的实际 hash 与本 spec 不同：

```text
BLOCKED_INPUT_CHANGED
```

并停止，不自行更新 hash。

输出到 `t02_identity_inputs.json`：

```text
relative_path
expected_sha256
actual_sha256
size_bytes
role
hash_match
```

---

## 6. Phase B — model export and structural evidence

使用 P4 已验证过的 CFRezManager export 能力，分别导出 A / B / C 到独立派生目录。

优先命令形式沿用当前仓库已验证 route：

```text
CFRezManager.exe --export-obj --raw-transform --root data/rf016 --model <Models/PLAYERVIEW/...LTB> --output <work/p5_leishen/t02/...obj>
```

不得修改原 LTB。

每个候选必须记录：

```text
LTB path + SHA256
OBJ path + SHA256
mesh/group names
vertex / uv / normal / triangle counts
material names / slots
bounds
obvious hand/arm groups if detectable
export command
exit code
```

生成：

```text
work/p5_leishen/t02/model_compare.json
```

如果某个 control export 失败：记录 `not_available`，但 A 主候选 export 失败则 T02 为 `BLOCKED_PRIMARY_EXPORT`。

---

## 7. Phase C — standard visual previews

### 7.1 Render rule

使用 Blender 4.5（可 GUI/MCP/headless，优先可重复脚本）为 A / B / C 各生成统一相机 / 归一化尺度的派生预览。

至少四视图：

```text
right_side
left_side
top
front_3q
```

要求：

- 背景简单；
- 不做艺术灯光；
- 相同 projection / framing / scale policy；
- 优先隐藏明显 `hand/arm/sleeve/wrist/Fview-*` 组，只比较武器本体；
- 如果无法可靠识别手臂组，同时额外保留完整模型图，但不得删除枪体；
- 不修改模型几何；
- 不做 IK / 动作 / Source retarget。

分辨率建议 1024×1024，每候选四张即可，不需要高质量 Cycles。

### 7.2 Material / texture rule

PRIMARY A 优先尝试使用 LTB export 产生的 MTL / 派生纹理进行材质预览。

同时核对 exact-match 本地资源族：

```text
PV-M4A1_S_Transformers.DTX
M4A1_S_Transformers_Alpha.TGA
M4A1_S_Transformers_N.TGA
M4A1_S_Transformers_S.TGA
M4A1_S_Transformers.CFG
```

如果仓库 / 本地已有安全 DTX 解码能力：

- 可以把 exact DTX 转为 PNG 派生预览；
- 记录 decoder/tool path + hash + command。

如果没有现成 DTX decoder：

- **不要为了 T02 临时造一个大型专有格式 decoder**；
- 标记 `direct_dtx_preview=not_available`；
- 使用 LTB export 的材质/纹理派生结果做视觉 Review；
- T03 再处理完整 DTX/Shader graph。

TGA Alpha / Normal / Specular 可以生成只读派生缩略图/contact sheet，但不要把它们误当 diffuse。

---

## 8. Phase D — local resource-family evidence

生成 `resource_family.json`，至少证明本地标准 family 同时存在：

```text
PV model: PV-M4A1_S_Transformers.LTB
PV diffuse/resource: PV-M4A1_S_Transformers.DTX
Alpha: M4A1_S_Transformers_Alpha.TGA
Normal: M4A1_S_Transformers_N.TGA
Specular: M4A1_S_Transformers_S.TGA
Shader: M4A1_S_Transformers.CFG
QV model: QV-M4A1_S_Transformers.LTB
QV texture: QV-M4A1_S_Transformers.DTX
```

字段：

```text
relative_path
sha256
size_bytes
role
family_token = M4A1_S_Transformers
exists
```

这属于 provenance evidence，不等于单独完成 identity confirmation。

---

## 9. Required outputs

统一目录：

```text
work/p5_leishen/t02/
```

必须提交：

```text
t02_identity_inputs.json
model_compare.json
resource_family.json
execution.json
review_sheet.png
```

`review_sheet.png` 必须至少包含 A/B/C 的统一视图并明确标签：

```text
A PRIMARY — M4A1_S_Transformers
B SAME-FAMILY CONTROL — Transformers_Classic
C NEGATIVE CONTROL — BornBeast / 黑骑士 family
```

允许额外提交：

```text
previews/*.png
texture_previews/*.png
scripts/p5/*.py
```

前提是均为派生证据，不是原始 `data/**` 文件复制。

---

## 10. Executor result semantics

### `EXECUTION_PASS`

仅表示：

1. 输入 hash 验证通过；
2. PRIMARY A 成功导出并形成结构摘要；
3. A/B/C 有足够统一派生预览供 Chat/Sol 审查；
4. exact `M4A1_S_Transformers` 本地 model/texture/shader family 被记录；
5. 原始 `data/**` 未修改/上传；
6. Luna 没有自行声明最终身份。

### `BLOCKED`

包括：

- 主候选 hash 已变化；
- PRIMARY A 无法导出；
- Blender / 导出环境完全不可用，无法生成任何可审查视觉证据。

### `INVALID`

包括：

- 修改了 `data/**`；
- 用第三方 MOD 替代本地 primary；
- 更换了候选集合或放宽标准而未按 spec；
- Luna 自行写 `IDENTITY_CONFIRMED`。

---

## 11. Upload allowlist

只允许：

```text
work/p5_leishen/t02/t02_identity_inputs.json
work/p5_leishen/t02/model_compare.json
work/p5_leishen/t02/resource_family.json
work/p5_leishen/t02/execution.json
work/p5_leishen/t02/review_sheet.png
work/p5_leishen/t02/previews/*.png
work/p5_leishen/t02/texture_previews/*.png
scripts/p5/*.py
```

禁止：

```text
data/**
原始 LTB / DTX / TGA / CFG
.blend 大文件（除非 Chat/Sol 后续明确要求）
Steam/MIGI 输出
无关缓存/日志
```

---

## 12. Stop rule

Luna 完成 T02 后：

1. 精确提交 allowlist 文件；
2. push `master`；
3. 返回 commit SHA；
4. **停止**；
5. 不自行执行 T03；
6. 不自行修改 `plan.md` 为 `IDENTITY_CONFIRMED`。

之后由 Chat/Sol 读取 `review_sheet.png` + JSON 证据，做 P5-T02 identity review，并决定是否进入 T03。