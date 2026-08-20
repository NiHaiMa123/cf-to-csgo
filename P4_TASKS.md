# P4 修复与验收任务清单

> 状态：**P4-T08 `passed_user_confirmed` / frozen-noop addon 已部署；T09 最终冻结等待独立 Reviewer**
>
> 适用对象：P4 执行 Agent、独立 Reviewer、Chat/Sol Planner/Reviewer
>
> 核心边界：只完成 `Prototype-01` 的可重复 CF → CS:GO Legacy M4A4 流水线；不得在 P4 声称完成 P5/P6/P7，也不得宣布当前候选资产就是最终雷神。

`plan.md` 第 1 节是项目唯一 authoritative progress/status；本文件是 P4 的执行、验收和 Reviewer 合同。聊天记忆、旧报告标题或旧 MOD 名称均不能覆盖这两个文件的当前状态。

---

## 0. 当前现场与 P4 边界

### 0.1 必须保留的历史基线

- D3/F4 历史可运行 Prototype：`p_cf_bornbeast_m4a4_f4_recognizable_tmp`。
- 它是用户此前确认过的视觉/运行基线，不是最终 CF 材质，也不保证是最终目标枪资产。
- 历史报告、模型、材质和 `mods_temp` 中的历史 MOD 不得删除、覆盖或改名来制造新的 PASS。

### 0.2 当前 P4 输入/输出

- Pipeline：`scripts/weapon_port/pipeline.py`
- Manifest：`assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json`
- P4 work：`work/m4a1_s_bornbeast/p4_prototype_01/`
- P4 build：`build/m4a1_s_bornbeast_m4a4/p4_prototype_01/`
- 当前测试 addon：`p_cf_bornbeast_m4a4_p4_frozen_noop_01`
- 当前 frozen/no-op run：`run_20260819_170013_270792`
- Inspect policy：`frozen_noop_safe`

MIGI 无单独禁用按钮；测试时只能启用当前目标 addon，其他冲突 M4A4 addon 放入 `mods_temp`。历史 final MOD `p_cf_m4a4_bornbeast_final` 属于越过 P4 的旧产物，不得作为 P4 输入、golden fixture 或通过证据。

### 0.3 本轮禁止事项

- 禁止继续或声称完成 P5、P6、P7。
- 禁止把网络 MOD 的模型/贴图改称本地 CF 最终资产。
- 禁止把历史 final MOD 当 P4 证据。
- 禁止默认写入或覆盖用户现有 MIGI addon。
- 禁止自动修改 `mods_temp` 来伪造测试环境。
- 禁止伪造 `passed_user_confirmed`、截图、控制台结果或实机结论。
- 禁止为了让测试通过而降低 expected counts、删 Gate、把失败改成 warning。
- Git 同步与本地 `data/` 保护遵守根目录 `AGENTS.md`。

### 0.4 历史 REWORK 缺陷说明

2026-08-19 早期版本曾确认过以下类别的问题：旧 aligned OBJ 假闭环、manifest 字段未消费、路径删除边界不足、package/deploy 绑定不足、语义 Gate 过弱、报告 provenance 不完整、用户确认被自动证据替代、Plan 多处状态互相矛盾等。

**这些是 T01～T07 的修复输入，不代表当前 HEAD 仍处于该 REWORK 状态。** 当前状态必须看本文件顶部、各 Task 的最新执行结果和 `plan.md` 第 1 节。

---

## 1. P4 准确流水线边界

P4 的完整 build 必须覆盖：

```text
manifest 指定本地 CF LTB
  → CFRezManager B3 raw OBJ/export report
  → B3 独立 roundtrip validator
  → C1 weapon-only split（排除 CF 手臂）
  → 冻结 C3 M4A4 matrix 确定性变换
  → 9 mesh → M4A4 bone mapping
  → SMD/QC
  → studiomdl 隔离编译
  → Crowbar 回环
  → Prototype 外部参考材质 VMT/VTF
  → 自动 validate
  → 项目内 package
  → MIGI staging
  → 显式 deploy（仅在明确要求时）
```

不得用旧 `work/`、旧 build、旧 MIGI addon 或手工复制的 aligned OBJ 代替上述依赖链。

---

## 2. 执行任务状态

### P4-T01：现场隔离与状态纠正 — PASS

- [x] 生成 baseline inventory。
- [x] 区分历史用户确认基线、自动 staging、越界 final MOD。
- [x] 不移动、不删除、不覆盖现有历史 MOD 作为通过手段。
- [x] `plan.md` 恢复单一 authoritative state。

### P4-T02：Manifest 契约与路径安全 — PASS

- [x] manifest 使用严格 schema；缺字段和未知字段均拒绝。
- [x] 输入包含 path/hash/role，工具包含 path/hash/version/role。
- [x] `final_target_identity=false`、`final_cf_material=false`、Prototype material provenance 为强制条件。
- [x] runtime 固定 M4A4 + `weapons/v_rif_m4a1.mdl`。
- [x] build/work 输出限制在 P4 指定子树，拒绝 absolute、`..`、根目录和 escape。
- [x] deploy 必须显式目标并执行安全边界检查。

执行证据：

- `work/m4a1_s_bornbeast/p4_prototype_01/manifest_contract_report.json`
- `work/m4a1_s_bornbeast/p4_prototype_01/check_report.json`
- `tests/test_p4_path_and_manifest_security.py`

已记录：18 PASS；1 个 Windows symlink 创建测试因权限跳过，但实现仍使用 resolved-path containment 拒绝已存在的 symlink/junction escape。此项作为 Reviewer 风险点保留，不回退为 REWORK。

### P4-T03：LTB → B3 → C1 → C3 真实上游链路 — PASS

- [x] build 从 manifest 指定 LTB 重新调用 CFRezManager。
- [x] B3 raw OBJ + export report 在本次 run 目录生成。
- [x] B3 roundtrip validator 必须通过。
- [x] C1 从本次 B3 输出分离 9 个 weapon mesh，排除 CF arms。
- [x] C3 使用冻结 M4A4 4×4 matrix 做一次确定性变换。
- [x] 不重新 ICP、不按 mesh normalize/center/scale、不隐式翻面。
- [x] 每步记录 command、exit code、input/output hash 和语义统计。

关键证据：`upstream_trace_report.json` 和各 `runs/<run_id>/`。

### P4-T04：Source 1 构建单入口 — PASS

- [x] SMD mesh→bone mapping 由 manifest 驱动。
- [x] 主体→Parent、01→Clip、02→Bolt、03–08→Parent fallback 有明确记录。
- [x] QC modelname、body、`$cdmaterials`、sequence、attachment 按 M4A4 contract 检查。
- [x] `studiomdl` 使用本次隔离 game root。
- [x] 只允许 Prototype 外部参考材质，不引入 P6/final builder。
- [x] build report 记录完整步骤、命令、退出码、日志和 hash。

Crowbar 0.71 运行时需要 `%APPDATA%\ZeqMacaw` 可写；受限 Agent 环境必须为实际构建命令提供所需权限，不能用旧产物替代执行。

### P4-T05：自动语义 Gate — PASS

当前验证报告：`work/m4a1_s_bornbeast/p4_prototype_01/validation_report.json`。

- [x] dependency chain / run id / hash 连续追溯。
- [x] B3 / C1 mesh、vertex、UV、normal、triangle、material slots 语义检查。
- [x] C3 matrix convention、determinant、normal/winding policy 检查。
- [x] 57-bone skeleton 逐名/逐 parent 检查。
- [x] mesh primary-bone corner 分布由 manifest 驱动。
- [x] modelname 精确检查。
- [x] 9 sequence 名称集合和数量检查。
- [x] attachment 名称、骨骼和变换检查。
- [x] MDL/VVD/ANI/dx80/dx90/sw.vtx 完整性检查。
- [x] Crowbar roundtrip modelname/bone/sequence/attachment/material/triangle 检查。
- [x] SMD→QC→VMT→VTF 闭包检查。
- [x] Prototype provenance / final flag 拒绝。
- [x] addon ↔ staging 文件集合、大小、SHA-256 检查。

当前 frozen/no-op run 的 **15/15 validation PASS**。

### P4-T06：Package 与安全 Deploy — PASS

- [x] package_root 实际包含 payload。
- [x] staging 从 package 生成，payload hash 闭合。
- [x] package manifest 排除自身，避免自引用 hash。
- [x] package manifest 绑定 run id、manifest SHA-256 和 check/build/validate/upstream-trace 报告。
- [x] package 前重新验证当前 run 绑定。
- [x] `all` 不隐式 deploy。
- [x] deploy 只允许新建目标，或确认已有目录与 payload 完全一致；不同内容拒绝覆盖。
- [x] deploy 后重新计算目标文件 hash 并生成 `deploy_report.json`。

当前 deployed addon：`p_cf_bornbeast_m4a4_p4_frozen_noop_01`。

### P4-T07：执行者自动测试 — PASS

当前权威报告 `negative_test_report.json` 记录 `mutation_count=17`、`passed_mutations=17`。旧清单曾把“缺 sw.vtx 或 ANI”合并写成一个要求，因此出现过“16 项”文字；现统一以实际报告的 **17 个 mutation / 17 PASS** 为准。

实际 17 项为：

1. `ltb_hash`；
2. `b3_triangle`；
3. `b3_group`；
4. `b3_uv_index`；
5. `b3_missing_normal`；
6. `mapping_parent_clip_swap`；
7. `c3_matrix_convention`；
8. `c3_negative_determinant`；
9. `sequence_name_same_count`；
10. `attachment_bone_same_count`；
11. `missing_sw_vtx`；
12. `missing_ani`；
13. `missing_vtf_material_closure`；
14. `final_cf_material`；
15. `output_repo_root`；
16. `deploy_without_target`；
17. `deploy_different_existing_content`。

- [x] 17/17 mutation 均非零退出，并命中预期阶段/Gate。
- [x] mutation 在临时 shadow project / 临时 game root 执行，不污染真实环境。
- [x] 两次独立正向 build 已完成语义复现比较。

正向 run：

- `run_20260819_134448_275591`
- `run_20260819_134459_016321`

证据：

- `work/m4a1_s_bornbeast/p4_prototype_01/negative_test_report.json`
- `work/m4a1_s_bornbeast/p4_prototype_01/reproducibility_report.json`

### P4-T08：用户实机 Gate — PASSED_USER_CONFIRMED

**P4 目标只验收 changed-runtime 安全，不再验收可见 Inspect retarget。**

当前自动证据：

- manifest：`inspect_policy=frozen_noop_safe`；
- current addon：`p_cf_bornbeast_m4a4_p4_frozen_noop_01`；
- current run：`run_20260819_170013_270792`；
- build / Crowbar roundtrip / 15/15 validation / package / staging / deploy 已完成；
- `prototype_01_game_regression.json` 已记录用户确认；该确认只覆盖本节 changed-runtime Gate，不代表 Inspect retarget 或最终资产完成。

用户只需针对新 frozen/no-op 变量明确确认：

- [x] 按 F 后没有崩溃或明显运行错误；
- [x] 无可见 Inspect 动作属于预期；
- [x] 武器状态能返回；
- [x] 按 F 后仍能射击；
- [x] 按 F 后仍能换弹；
- [x] 按 F 后仍能切枪。

此前已经确认且本次未改变的模型/FOV、UV、Idle、Draw、Fire、Reload、Bolt、muzzle、shell 等历史功能不要求为了 frozen/no-op 再完整重跑一次；Reviewer 可以检查这些历史证据是否仍与当前构建变量隔离。

Inspect 的可见动作、手指穿模、Blender frame 1/40/80/120/159 接触检查和 retarget 质量全部属于 P7，不得重新回灌 P4 blocker。

### P4-T09：文档与冻结 — PRE-CLOSE DONE / FINAL FREEZE PENDING

- [x] README 只记录真实命令、路径、报告和限制，并作为证据索引而不是第二套状态机。
- [x] `plan.md` 第 1 节保持唯一 authoritative progress/status。
- [x] P4 Inspect frozen/no-op 边界写清，真正 retarget 移入 P7。
- [x] B1/B2/C2 和 03–08 Parent fallback 保持显式技术债，不伪装成已解决。
- [x] `Prototype-01` 保持 `final_target_identity=false`、`final_cf_material=false`。
- [x] T08 用户 changed-runtime Gate 完成后更新用户证据。
- [ ] 独立 Reviewer 完成 RV-01～RV-06。
- [ ] 只有上述两项结束且无 blocker，才把 P4 改为 `PASS / FROZEN`。

---

## 3. 独立 Reviewer 任务

Reviewer 的职责不是重新实现 pipeline，也不是照执行者全流程再跑一遍后宣布“也能成功”。Reviewer 基于已提交 diff、执行者报告和少量独立高风险反例判断实现与证据是否可信。

### RV-01：Diff 与范围审计

- [ ] 检查 P4 修改是否符合本文件 scope。
- [ ] 发现 P5/P6/P7、final asset、音效、世界模型或网络 final 资源被偷偷纳入 P4，判定 **REWORK**。
- [ ] 检查是否删除/覆盖用户已有文件、历史 MOD 或本地 `data/`。

### RV-02：Manifest 字段消费追踪

- [ ] 建立关键字段 → 读取代码 → 实际行为/Gate 矩阵。
- [ ] 特别检查 LTB、toolchain hashes、mesh mapping、transform、material policy、runtime、output roots、inspect policy。
- [ ] 任一关键字段只写进报告却不影响行为/Gate，判定 **REWORK**。

### RV-03：证据链审计

- [ ] 从 package manifest 反向追 validate/build/check/upstream trace。
- [ ] 检查 run id、manifest hash、输入 hash 和输出 hash 是否绑定同一 run。
- [ ] 不重新构建模型；本项只审引用、hash 和 provenance。
- [ ] 任何当前报告依赖旧 run 产物而未声明，判定 **REWORK**。

### RV-04：定向反例测试

Reviewer 从 T07 mutation 中选择至少 4 个高风险反例，在全新临时目录实际执行。必须包含：

- [ ] 1 个路径越界/递归删除安全反例；
- [ ] 1 个“数量不变但语义错误”的 sequence 或 attachment 反例；
- [ ] 1 个 mesh/bone mapping 反例；
- [ ] 1 个材质闭包或 provenance 反例。

**执行分工允许为：Sol 设计精确测试协议 → Luna/本地 Agent 机械执行 → Sol 审原始证据。** Reviewer 不得把“设计了测试”写成“测试已执行”。

每个测试必须预先固定：baseline、mutation、禁止改变的变量、执行命令、预期失败 Gate、PASS/FAIL/INVALID 判定和所需证据。

### RV-05：报告真实性审计

- [ ] 对比 report/run id/hash/命令日志与实际状态。
- [ ] 自动推断不得冒充 `passed_user_confirmed`。
- [ ] 没有用户确认的 changed-runtime 条目必须保持 pending/not_tested/pass_with_risk 等真实状态。
- [ ] 发现复制旧确认、伪造实机证据或无证据 PASS，直接判定 **REWORK**。

### RV-06：最终 Review 输出

Reviewer 只输出：

1. `PASS / PASS WITH RISK / REWORK`
2. 未满足的 task/review ID
3. 最多 10 条真实 blocker/risk
4. T08 用户 Gate 是否满足
5. 是否允许把 `plan.md` 的 P4 改成 `PASS / FROZEN`

Reviewer 不得顺手修复发现的问题；修复退回执行者，修复后只做对应定向复核。

---

## 4. P4 总 Gate

### 已满足的自动/工程 Gate

- [x] P4-T01～P4-T07 完成；
- [x] `check → build → validate → package` 可从 manifest 指定本地 LTB 开始在 fresh run 中完成；
- [x] 无 MIGI/旧 build/旧 aligned OBJ 隐式输入；
- [x] 两次独立正向 build 语义复现证据完成；
- [x] T07 实际 17 个负向 mutation 全部被预期 Gate 阻止；
- [x] package / staging / 明确 deploy 目标形成 hash/provenance 闭环；
- [x] frozen/no-op Inspect 自动构建与 15/15 validation 通过；
- [x] Plan / README / P4 文档预收口完成；
- [x] Prototype 仍明确不是 final asset/material。

### 尚未满足

- [ ] RV-01～RV-06：独立 Reviewer 完成并允许冻结；
- [ ] P4-T09：根据真实 T08 + Reviewer 结果写入最终 `PASS / FROZEN` 状态。

在上述两项完成前，当前统一结论为：

> **P4 自动技术闭环和 T08 用户 Gate 已完成，当前为 `REVIEW_PENDING`。尚不能标记 `PASS / FROZEN`；真正 Inspect retarget 已移入 P7，不再是 P4 blocker。**
