# P5_T02_TASK_SPEC.md — 雷神本地候选与原生材质确认

> task_id: `P5-T02`
>
> Planner / Reviewer: **Chat/Sol**
>
> Executor: **Any user-selected Local Executor Agent with local repository/data/tool access**
>
> 当前状态: **PAUSED_BY_P4_M01**

> 本 Task 不绑定 Luna、Codex 或任何具体模型/Agent。恢复执行时，由用户当前选择的 Local Executor 从最新 `master` 和已有 evidence 继续。

---

## 1. 当前不要执行 T02

P5-T02 已完成候选缩圈和几何诊断，但 native CF material method 尚未验证。

当前先执行：

```text
P4_M01_TASK_SPEC.md
```

只有 Chat/Sol 明确判定：

```text
P4-M01 = PASS / NATIVE_MATERIAL_RECOVERED
```

后，T02 才恢复为 ACTIVE。

当前 Local Executor 不得：

- 继续让用户在 C029/C103 灰模间强选；
- 重跑 T01 Web Search；
- 用 external MOD texture 构造雷神 finalist；
- 把未验证的 headerless BGR24 / scalar map / raw CFG strip 当作正确材质。

---

## 2. T02 已完成的前置工作

### T01 official reference

已完成：

```text
P5-T01 = PASS / USER_REFERENCE_CONFIRMED
```

Ground Truth：

```text
work/p5_leishen/t01_reference/official_reference.json
```

除非用户明确否决或 evidence 损坏，不重跑。

### Legacy candidate pool

复用：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
```

不无必要重扫全部 `data/**`。

### 已完成 narrowing

```text
M4/M4A1 PLAYERVIEW filter
-> exact SHA dedup
-> geometry signature cluster
-> finalist diagnostics
```

现有主要 evidence：

```text
work/p5_leishen/t02/candidate_clusters.json
work/p5_leishen/t02/visual_shortlist.json
work/p5_leishen/t02/execution.json
work/p5_leishen/t02/contact_sheet.png
```

### 当前已知 diagnostic-only 结果

```text
C029/C103 gray geometry                    diagnostic_only
PV-M4A1_S_Transformers.DTX headerless BGR24  unvalidated hypothesis
raw PV DTX + UV                            diagnostic_only
Alpha/Specular approximation               diagnostic_only
raw RGB strip CFG preview                  not semantic decoding
```

这些不能完成 `USER_VISUAL_MATCH_CONFIRMED`。

---

## 3. P4-M01 handoff 输入

T02 恢复时，必须先读取 P4-M01 closure 和可复用实现，至少包括：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/provenance_audit.json
work/m4a1_s_bornbeast/p4_m01_native_material/native_material_inventory.json
work/m4a1_s_bornbeast/p4_m01_native_material/dtx_decode_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/tga_decode_matrix.json
work/m4a1_s_bornbeast/p4_m01_native_material/material_binding_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/cfg_reverse_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/variant_diff_report.json
work/m4a1_s_bornbeast/p4_m01_native_material/shader_hypotheses.json
work/m4a1_s_bornbeast/p4_m01_native_material/native_material_closure.json
```

以及实际提交到仓库的 decoder/inspection/render code。

T02 不得只读取“P4-M01 PASS”字符串；必须使用其具体方法和 evidence。

---

## 4. T02 恢复后的目标

T02 的问题是：

> **本地 CF `data/**` 中，哪一个 M4A1 第一人称 candidate 在使用已验证/扩展后的 native material method 后，与用户已确认的 M4A1-雷神官方 reference 一致？**

恢复后的固定流程：

```text
P4-M01 validated material method
-> Transformers family native material inventory
-> validate Transformers-specific DTX/TGA/CFG/container differences
-> recover Transformers LTB material binding
-> extend CFG/render-style semantics only where evidence requires
-> render native-material finalists
-> USER LOCAL-CANDIDATE GATE
```

---

## 5. Transformers-specific material recovery

P4-M01 验证的是 BornBeast benchmark，不允许机械假设 Transformers 完全同格式。

T02 必须对 Transformers 再验证：

1. DTX container/pixel format 是否同 P4-M01；
2. TGA packed/scalar semantics 是否同 P4-M01；
3. LTB slot/index/render-style binding 是否同结构；
4. WeaponShader CFG record/field semantics 是否可迁移；
5. 是否存在 Transformers 特有 lookup/emissive/detail/effect；
6. 同 geometry skin variants 的 differential 是否支持该 binding。

如果某项不同：

- 允许在 P4-M01 已验证方法基础上做最小 extension；
- 新 extension 必须有同等级结构/differential evidence；
- 不允许退回“文件名看起来对”或“图片看起来像”的弱证明。

---

## 6. Candidate identity 与 C029/C103

现有 C029/C103 只保持 `candidate_only`，直到 native material render 成立。

T02 可以继续利用：

- exact SHA family；
- geometry signature；
- canonical basename；
- variant relation；
- material binding；
- official visual reference。

但不得仅凭任一单项直接写最终 identity。

最终用户 Gate 只展示**通过 native material acceptance gate 的 finalist**。

---

## 7. Native material acceptance gate

某个 Transformers finalist 要进入用户 Gate，必须满足：

1. geometry 来自本地 LTB；
2. UV 来自该 LTB；
3. visible color 输入全部来自 local CF / verified semantics；
4. base/lookup/alpha/normal/specular/emissive/detail 等实际使用资源都有 path + SHA-256；
5. material binding 有结构证据；
6. CFG/render-style 语义为已验证或有明确 extension evidence；
7. 0 external pixels；
8. clean-output 可重复；
9. 统一正交 render 在颜色分区、纹理图案、能量/高光位置和机械结构上足以人工识别。

未满足时状态：

```text
NATIVE_TEXTURE_RECOVERY_INCOMPLETE
```

继续 T02，不进入用户 Gate。

---

## 8. USER LOCAL-CANDIDATE GATE

只有至少一个 finalist 通过 §7 后，Local Executor 才展示：

```text
confirmed official reference
+
native-material finalist render(s)
```

用户可以：

- 确认某个 candidate；
- 要求放大/分层；
- 否决全部并要求继续恢复/缩圈。

等待状态：

```text
AWAITING_USER_LOCAL_CANDIDATE_CONFIRMATION
```

用户明确确认后：

```text
USER_VISUAL_MATCH_CONFIRMED
```

这仍不是最终 `IDENTITY_CONFIRMED`。

---

## 9. Required outputs

继续使用：

```text
work/p5_leishen/t02/
```

必须保持/更新：

```text
candidate_clusters.json
visual_shortlist.json
contact_sheet.png
execution.json
native_material_inventory.json
native_shader_hypotheses.json
```

恢复执行后建议增加：

```text
material_method_transfer_report.json
transformers_dtx_decode_matrix.json
transformers_tga_decode_matrix.json
transformers_material_binding_report.json
transformers_cfg_extension_report.json
previews/native_hypotheses/*.png
```

用户确认后：

```text
user_visual_confirmation.json
```

所有输出继续遵守 `AGENTS.md`，不上传 `data/**` 原始资产。

---

## 10. Completion criteria

### PASS / USER_VISUAL_MATCH_CONFIRMED

必须满足：

- P4-M01 已经 Chat/Sol Review PASS；
- P4-M01 material method 已实际迁移/扩展到 Transformers；
- finalist native material gate 通过；
- 用户看到 native-material candidate 并明确确认；
- candidate path/SHA/material evidence 已记录；
- 没有 external pixels；
- Local Executor 没有自行写最终 identity。

### BLOCKED / RETURN CHAT-SOL

- P4-M01 尚未 PASS；
- P4-M01 方法对 Transformers 完全不可迁移，且需要重设 Task Spec；
- 本地必要 Transformers assets 实际缺失；
- 多条独立 extension 路线仍无可验证进展。

### INVALID

- 绕过 P4-M01 继续当前 T02；
- external MOD texture 进入 final render；
- 用未验证 headerless/raw interpretation 直接 PASS；
- 用 AI 生成/补全纹理；
- 修改/上传 `data/**`；
- 灰模强制用户确认；
- Local Executor 自行写 `IDENTITY_CONFIRMED`。

---

## 11. Handoff

T02 完成后：

```text
USER_VISUAL_MATCH_CONFIRMED
-> push scoped evidence to master
-> P5-T03 Resource Graph / provenance closure
-> P5-T04 Chat/Sol final identity review
```
