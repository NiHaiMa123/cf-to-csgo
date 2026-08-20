# CF 武器 → CS:GO Legacy Source 1 转换流水线计划

> 最后更新：2026-08-20
>
> 当前状态：**P4-T08 `FROZEN_NOOP_SAFE / READY_FOR_USER_GATE`；P4 最终冻结等待用户最小实机确认 + 独立 Reviewer**
>
> 当前运行槽位：**M4A4**
>
> 当前技术验证样机：**`Prototype-01`**
>
> 当前内部模型名：`weapons/v_rif_m4a1.mdl`
>
> 当前核心目标：**先把一个 CF M4 `Prototype-01` 稳定、完整地转换到 CS:GO M4A4，并建立可重复流水线；P4 冻结后再准确定位真正的雷神资产并替换输入。**

本文第 1 节是项目唯一的 authoritative progress/status。README 负责工具说明和证据索引；`P4_TASKS.md` 负责 P4 的验收与 Reviewer 合同；其他旧阶段编号只用于关联历史报告，不再单独维护当前进度。

---

## 1. 唯一权威进度

### 1.1 已完成并保留的基线

1. **Source 1 官方基线与编译闭环**
   - 已完成官方模型提取、反编译、隔离编译、回环检查、MIGI 部署和 CS:GO Legacy 实机验证。
   - 当前运行目标、QC、MDL、动作和实机验收统一为 M4A4。
   - M4A4 基线为 57 骨、9 个序列、2 个 attachment、`rif_m4a1` 材质，内部名固定为 `weapons/v_rif_m4a1.mdl`。

2. **CF 静态枪模进入 Source 1**
   - 当前候选 LTB 已能导出枪体网格、分件、position、normal、UV、triangle winding 和 material slot。
   - 9 个枪体 mesh 已进入 M4A4 viewmodel：主体→Parent、01→Clip、02→Bolt、03–08→Parent 的 `Prototype-01` 静态降级。
   - 坐标、比例和 M4A4 对齐变换已固化在 `assets/weapons/m4a1_s_bornbeast/c3_alignment_m4a4_manifest.json`。

3. **动作与机械件 Prototype 闭环**
   - Idle、Draw、Fire、Reload 使用官方 M4A4 兼容动作。
   - 弹匣、枪机和主枪体已通过编译回环与此前分阶段实机检查。
   - P4 的 Inspect 不再尝试不可靠的手部 retarget，而使用显式 `frozen_noop_safe` 策略；真正可见 Inspect/手指接触属于 P7。

4. **材质引用闭环**
   - SMD → QC `$cdmaterials` → VMT → VTF 的引用验证器已经成立。
   - 当前可识别材质来自网络 GoldSrc/CS1.6 第三方移植包，必须保持 **`EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`**。
   - 它只用于 `Prototype-01` 的 UV、几何和视觉调试，不代表最终 CF 材质转换完成。

5. **MIGI 与游戏内历史闭环**
   - D3/F4 历史 Prototype 已在游戏内确认模型、贴图和主要 M4A4 动作可运行。
   - 历史可运行版本必须保留，不得作为当前 P4 自动 Gate 的替代证据，也不得被无条件覆盖。

### 1.2 当前 P4 状态

**P4：通用流水线稳定化与冻结验收。**

- **P4-T01～T07：完成。**
  - manifest 契约和路径安全已建立；
  - `build` 已从 manifest 指定本地 CF LTB 重新执行 B3 → C1 → C3，而不是读取旧 aligned OBJ 充数；
  - Source 1 build / Crowbar roundtrip / 15 个语义 Gate 已通过；
  - package / staging / deploy 边界已建立；
  - T07 实际执行 **17 个负向 mutation**，覆盖 16 类必测错误场景，17/17 均被预期 Gate 拒绝；
  - 两次独立正向 build 的语义复现证据已完成。

- **P4-T08：`READY_FOR_USER_GATE`。**
  - manifest 默认 `inspect_policy=frozen_noop_safe`；
  - 当前候选 addon：`p_cf_bornbeast_m4a4_p4_frozen_noop_01`；
  - 当前 frozen/no-op build run：`run_20260819_170013_270792`；
  - 自动构建、Crowbar 回环、15/15 validation、package/staging 和 deploy 证据已生成；
  - **尚缺用户对“变更后的 Inspect 行为”做最小实机确认。**

- **P4-T09：文档预收口完成，最终冻结未完成。**
  - README / Plan / P4 证据索引已收口；
  - P4/P5/P6/P7 的边界已重新分离；
  - P4 最终 `PASS / FROZEN` 必须等待 T08 用户确认以及独立 Reviewer 结论。

- **独立 Reviewer：尚未完成。**
  - 按 `P4_TASKS.md` 的 RV-01～RV-06 执行；
  - Reviewer 不重做实现，只审 diff、manifest 字段消费、证据链、少量高风险反例和报告真实性。

### 1.3 当前唯一需要用户执行的 P4 实机 Gate

只启用：

`p_cf_bornbeast_m4a4_p4_frozen_noop_01`

触发 Inspect（F）后确认：

1. 没有崩溃或明显运行错误；
2. frozen/no-op 没有可见 Inspect 动作属于预期，不算失败；
3. 武器状态能够正常返回；
4. 之后仍能继续射击；
5. 仍能正常换弹；
6. 仍能正常切枪。

本轮不重新验收 Inspect 的可见动作、手指穿模或 Blender retarget。它们已经明确移入 P7。

### 1.4 当前证据索引

- Manifest：`assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json`
- Pipeline：`scripts/weapon_port/pipeline.py`
- P4 验收合同：`P4_TASKS.md`
- 自动报告：`work/m4a1_s_bornbeast/p4_prototype_01/{check_report,build_report,validation_report,upstream_trace_report}.json`
- Package / staging：`work/m4a1_s_bornbeast/p4_prototype_01/{package,staging}/`
- Deploy：`work/m4a1_s_bornbeast/p4_prototype_01/deploy_report.json`
- 用户 Gate：`work/m4a1_s_bornbeast/p4_prototype_01/prototype_01_game_regression.json`
- 负向测试：`work/m4a1_s_bornbeast/p4_prototype_01/negative_test_report.json`
- 可复现性：`work/m4a1_s_bornbeast/p4_prototype_01/reproducibility_report.json`

### 1.5 下一步

1. 用户完成 1.3 的最小实机确认；
2. 更新 `prototype_01_game_regression.json`，只记录用户实际确认的事实；
3. 独立 Reviewer 执行 RV-01～RV-06；
4. 若无 blocker，将 P4-T08 / T09 / 总 Gate 改为完成，并把 P4 标记为 `PASS / FROZEN`；
5. P4 冻结后进入 P5，定位最终雷神本地 CF 资产。

---

## 2. 两条任务线必须分离

### Track A：转换技术流水线

Track A 回答“任意已知 CF 武器资产能否稳定进入 CS:GO Source 1”。

```text
CF 输入清单
  → LTB/纹理/音频检查
  → 静态 mesh/UV/normal/material slot 导出
  → Source 坐标与目标骨架映射
  → SMD/QC/VMT/VTF 生成
  → 隔离 studiomdl 编译
  → 编译后回环/结构校验
  → package / MIGI staging
  → 实机回归
```

P4 当前只负责冻结 Track A 的首个可重复 Prototype。

### Track B：最终目标资产定位

Track B 回答“真正雷神对应本地哪套 LTB/DTX/TGA/CFG/WAV”。它必须独立完成来源证明：

- 参考图、UI 图标、第一人称截图或用户提供的明确视觉证据；
- LTB mesh 轮廓、分件、顶点数和关键机械结构；
- DTX/TGA atlas 内容、UV 对应关系和 Shader 资源名；
- 同一变体的模型、材质、声音和动画资源关联；
- 原始路径和 SHA-256。

Track B 未完成时，禁止把 `Prototype-01` 改名为“最终雷神”；但不得因此回退已经通过的 Track A 技术证据。

---

## 3. 资产来源政策

### 允许

- 本地 CF 原始资源：最终模型、材质、动画和音效的唯一正式来源；
- 本地 CS:GO Legacy VPK：目标骨架、序列、attachment、QC 和运行时兼容基线；
- 网络截图、第三方 MOD、Wiki/展示页：只用于识别、对照、验证视觉方向；
- 网络 GoldSrc/CS1.6 第三方贴图：可用于 `Prototype-01` 验证链路，但必须标记为 `EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`，并记录来源、哈希和 `final=false`。

### 禁止

- 将网络第三方 MOD 的模型、贴图、动画或声音写成最终 CF 资源；
- 用第三方 MOD 成功运行来证明本地 CF parser 语义正确；
- 用改名复制其他 CS:GO 武器来满足最终验收；
- 在 manifest/report 中省略外部来源或把 `Prototype-01` 状态写成 final；
- 为了追求枪型身份准确而删除已经通过的构建/MIGI 证据。

---

## 4. 阶段定义与退出条件

本节只定义阶段，不维护当前进度；当前进度只看第 1 节。

### P0：Source 1 基线与安全构建

官方参考提取、反编译、隔离编译、回环报告、显式 MIGI deploy 和 M4A4 runtime contract。

### P1：CF 静态资源导出

当前候选 LTB 的 node hierarchy、mesh、position、normal、UV、winding 和 material slot 可导出；weapon mesh 与 CF 手臂可分离。

### P2：M4A4 Source 映射

M4A4 57-bone reference、M4A4 专用对齐变换、mesh→bone mapping、QC attachment 和官方动作兼容。

### P3：编译、材质引用、MIGI 与历史实机基线

9 mesh viewmodel 编译、官方 M4A4 sequence、VMT/VTF 引用闭包、MIGI addon 和历史游戏内可运行基线。

### P4：通用流水线稳定化

退出条件：

- authoritative manifest 完整描述 `Prototype-01` 输入和输出；
- 单入口执行 check/build/validate/package；
- 从本地 LTB 重新生成 B3/C1/C3，不隐式读取旧 MIGI/build/aligned OBJ；
- 关键失败返回非零退出码；
- 编译后语义 Gate 覆盖 model name、bones、sequences、attachments、materials 和 mesh/bone distribution；
- package/staging/deploy 证据闭合；
- 负向 mutation 与正向复现证据完成；
- changed-runtime 用户 Gate 完成；
- 独立 Reviewer 完成。

### P5：最终雷神资产定位

用户参考与本地候选轮廓/贴图特征一致；模型、贴图、Shader、声音均有本地 CF 路径与哈希；网络资源只作为 reference。

### P6：最终资产替换与发布质量

只替换 manifest 输入即可重跑冻结流水线；最终本地 CF mesh/UV/material 正确；final addon 不依赖网络 MOD 文件。

### P7：增强范围

- 真正可见的 Inspect / 手臂与手指 retarget / 接触与穿模验收；
- CF 原版动画；
- 动态红光和 Shader 近似；
- CF 音效和事件同步；
- 第三人称、落地武器、掉落弹匣；
- LOD、性能档位和批量武器转换。

---

## 5. P4 冻结合同摘要

- manifest 必须记录输入路径、哈希、M4A4 runtime、mesh→bone、transform、material policy、输出路径和工具版本；
- `final_target_identity=false`、`final_cf_material=false` 必须保持机器可读；
- `check/build/validate/package` 只写项目内受控 `work/`、`build/`；
- `deploy` 必须显式指定安全目标，不能覆盖内容不同的 addon；
- 上游失败时下游不得继续；
- 报告必须绑定 run id、manifest、输入/输出 hash 和实际 Gate；
- 自动证据不得冒充用户实机确认；
- P4 frozen/no-op Inspect 只保证状态安全，不宣称解决可见 Inspect 或穿模。

完整要求以 `P4_TASKS.md` 为准。

---

## 6. 已知技术债及阻塞级别

| 技术债 | 当前判断 | 是否阻塞 P4 `Prototype-01` | 何时修 |
|---|---|---:|---|
| B1 rigid mesh bone index 尚未正式进入 decoder/report | 报告语义不完整 | 否 | P4 后或第二种武器暴露问题时 |
| B2 bind validator 有“自己验证自己”风险 | 不能证明通用矩阵语义 | 否 | 通用化到不同骨架前 |
| B2 CF animation clips 尚未解码 | 无法使用 CF 原动作 | 否 | P7 动画阶段 |
| C2 03–08 精确机械语义未证明 | Parent fallback 可能不适合最终资产 | 否 | P5/P6 最终资产确认后 |
| 当前候选枪身份未最终确认 | 不能称为最终雷神 | 否 | P5 |
| 当前 F4 材质为 `EXTERNAL_REFERENCE / PROTOTYPE MATERIAL` | 不能计为最终 CF 材质或 final 发布 | 否 | P5/P6 |
| 世界/掉落模型仍是官方 M4A4 | 第一人称闭环不受影响 | 否 | P7 |

修债原则：只修会影响流水线复现、第二种武器复用或最终资产替换的问题；不得以“技术债存在”为由重写已通过的 `Prototype-01` 编译/MIGI 闭环。

---

## 7. 冻结的 Active Runtime 决策

- Active slot：M4A4。
- Model name：`weapons/v_rif_m4a1.mdl`。
- Reference skeleton：官方 M4A4 57 bones。
- Runtime state：只使用并验收 M4A4 原生状态集合。
- Main binding：`v_weapon.M4A1_Parent`。
- Magazine binding：`v_weapon.M4A1_Clip`。
- Bolt binding：`v_weapon.M4A1_Bolt`。
- 03–08：`Prototype-01` 阶段 Parent fallback，明确非最终语义。
- P4 Inspect：`frozen_noop_safe`；真正 retarget 在 P7。
- CF skeleton/animation：用于理解源资源和未来 CF 动画，不进入当前官方动作 Source viewmodel skeleton。
- 当前网络贴图：`EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`；`final_cf_material=false`。

任何未来修改若改变以上决定，必须显式更新 manifest/profile 和验收证据，不得悄悄切换武器槽位或状态机。

---

## 8. Definition of Done

### 8.1 P4 `Prototype-01` DoD

- 从 manifest 指定本地 LTB 可重复生成 M4A4 Source 1 addon；
- 自动 check/build/validate/package、负向测试和复现证据通过；
- 模型、UV/Prototype 材质、Idle、Fire、Reload、弹匣、枪机和 attachments 可用；
- frozen/no-op Inspect 的用户状态恢复 Gate 通过；
- 独立 Reviewer 通过或明确给出可接受的非阻塞风险；
- 候选资产身份和第三方材质明确非 final；
- 不要求 CF 原动画、真正 Inspect retarget、最终雷神材质或世界模型。

### 8.2 最终雷神 DoD

- 枪体和材质均可追溯到经确认的本地 CF 原始资源；
- 不依赖网络 MOD 模型、贴图、动画或声音；
- mesh、UV、动态件、骨骼、attachments、动作、材质和音效满足发布质量；
- 所有 `Prototype-01` fallback 已替换，或作为明确限制写入发布说明；
- 同一冻结流水线可以从 final 输入生成独立 MIGI 发布包；
- 实机证据与自动报告共同证明，不以“测试通过”替代资产身份验证。
