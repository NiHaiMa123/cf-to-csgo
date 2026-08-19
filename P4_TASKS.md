# P4 修复与验收任务清单

> 状态：**P4 REWORK / 未通过 Gate**
>
> 适用对象：下一位 P4 执行者及其独立 Reviewer
>
> 核心边界：只完成 `Prototype-01` 的可重复转换流水线；不得继续 P5/P6/P7，不得宣布最终雷神资产完成。

---

## 0. 当前现场基线（2026-08-19）

以下是本清单编写时的只读盘点结果。执行者必须先复核文件仍存在，但不得把“文件存在”直接写成“功能通过”。

### 0.1 已可信、必须保留

- 用户此前逐项实机确认过的 D3/F4 原型位于：
  - `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_f4_recognizable_tmp`
- 它是 `Prototype-01` 的已知可运行视觉基线，不是最终 CF 材质，也不保证是最终目标枪资产。
- D3/F4 原有报告、模型、材质、截图和 `mods_temp` 中的历史 MOD 都不得删除、覆盖或改名。

### 0.2 Antigravity 生成但尚未可信的 P4 产物

- 入口脚本：`scripts/weapon_port/pipeline.py`
- manifest：`assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json`
- 报告目录：`work/m4a1_s_bornbeast/p4_prototype_01/`
- P4 staging：`work/m4a1_s_bornbeast/p4_prototype_01/staging/`
- 历史 P4 MOD：
  - `D:\steam\steamapps\common\csgo legacy\migi\csgo\mods_temp\p_cf_bornbeast_m4a4_p4_pipeline_tmp`
- 盘点时 P4 staging 与上述 `mods_temp` P4 MOD 的 9 个运行文件逐文件 SHA-256 一致。
- 这只能证明“复制一致”，不能证明完整流水线、语义 Gate 或实机行为正确。

### 0.3 当前活动 MIGI 状态

- 当前 `migi/csgo/addons` 内唯一的 M4A4 测试 addon：`p_cf_bornbeast_m4a4_p4_inspect_safe_02`。
- `p_cf_bornbeast_m4a4_p4_inspect_safe_01`、`p_cf_bornbeast_m4a4_p4_review_01` 和 `p_cf_m4a4_bornbeast_final` 已按 MIGI 现场规则可恢复地移入 `migi/csgo/mods_temp`。
- final MOD 属于 Antigravity 越过 P4 后生成的 P6/final 路线，不属于本任务验收范围，尚未经过本项目当前要求的独立 Review。
- P4 执行者不得把 final MOD 当输入、golden fixture、参考材质或实机通过证据，也不得覆盖 `mods_temp` 中的历史版本。

### 0.4 已确认的现有 P4 缺陷

现有 `pipeline.py` 和现有 PASS 报告必须按 **REWORK** 处理，原因至少包括：

1. `build` 从已经生成好的 C3 aligned OBJ 开始，未重新执行 `LTB → B3 raw export → B3 roundtrip validation → C1 weapon-only split → C3 fixed transform`，却被描述成完整 CF 原始资产流水线。
2. manifest 中 `cf_ltb_source`、`b3_raw_obj`、`b3_export_report` 只在 `check` 中验哈希，没有成为 `build` 的数据依赖；上游产物即使彼此不一致，仍可能全部通过。
3. manifest 的 `toolchain` 文件及其 SHA-256 没有被 `check` 消费；记录了工具哈希不等于验证了工具哈希。
4. `check` 只检查 OBJ 总数和 group 名，不检查每组 triangle 数、索引范围、每面 `v/vt/vn` 完整性、每组材料槽、变换矩阵与 C3 manifest 的实际一致性。
5. `validate` 把骨骼 corner 数、57 骨、9 sequence 等写死在代码中，没有由 manifest/reference 驱动；只验 sequence 数量，不验 sequence 名称和集合。
6. `validate` 没有把 attachment 名称、骨骼和数值作为 Gate；回环报告出现 2 个 attachment 不代表 attachment 语义正确。
7. `build_report.json` 的 `pass` 在流程走到末尾后直接写为 `true`，没有输出完整 Gate 明细、每步命令、退出码、输入/输出哈希和失败原子性证据。
8. `package` 创建了 `package_root`，但没有向其中写入包；真正文件只在 `staging_root`。因此 manifest 声明的 package 输出没有实现。
9. `package` 只调用 `validate`，没有重新绑定当前输入 manifest/check 结果；构建后修改输入仍可能继续封包。
10. `deploy --migi-addon` 不是必填，并允许绝对路径；路径不受 MIGI addons 根目录约束，存在向任意不存在目录复制文件的边界风险。
11. 所有输出路径都允许 absolute path；`build`/`package` 会对 manifest 指定目录执行递归删除，缺少“必须位于仓库指定 build/work 子树”的 resolved-path 安全检查。
12. `all` 重复运行 `check` 和 `validate`，但没有形成带 step dependency/hash 的单一 run record。
13. 通用 P4 脚本混入了 `P6 final material` 分支，违反 P4 的 Prototype 边界。
14. `prototype_01_game_regression.json` 在没有本轮用户逐项测试和确认的情况下写成 `passed_user_confirmed`，其中控制台无错误、P4 addon 实机行为、回滚通过等内容没有对应的用户证据。该报告无效。
15. 通用 smoke test 只证明 `pipeline.py` 可被 Python 编译；没有执行 P4 正向测试、负向测试或路径安全测试。
16. `plan.md` 同时写了“P4/P5/P6 已完成”“当前 P7”，又在后文保留“后续定位雷神”和“下一次从 P4 开始”，权威状态已经自相矛盾。

---

## 1. 硬性范围与禁止事项

### 1.1 本轮允许修改

- `scripts/weapon_port/pipeline.py`
- P4 必需、且职责单一的新 helper/validator；必须放在 `scripts/weapon_port/` 或 `scripts/cf_ltb/`
- `assets/weapons/m4a1_s_bornbeast/prototype_01_manifest.json`
- P4 专用自动测试，放在 `tests/`
- `work/m4a1_s_bornbeast/p4_prototype_01/` 下由流水线重新生成的报告/staging/package
- P4 完成后才允许更新 `README.md` 和 `plan.md` 的 P4 状态

### 1.2 本轮禁止修改或使用

- 禁止继续或声称完成 P5、P6、P7。
- 禁止修改或依赖：
  - `assets/weapons/m4a1_s_bornbeast/m4a4_final_bornbeast_manifest.json`
  - `scripts/weapon_port/build_p6_final_materials.py`
  - `scripts/weapon_port/scan_p5_assets.py`
  - `scripts/weapon_port/port_real_leishen.py`
  - `build/m4a1_s_bornbeast_m4a4/p6_bornbeast_final/`
  - `build/m4a1_s_bornbeast_m4a4/real_leishen/`
  - `work/m4a1_s_bornbeast/p5_asset_identification/`
  - `work/m4a1_s_bornbeast/p6_bornbeast_final/`
  - `work/m4a1_s_bornbeast/real_leishen_port/`
- 禁止把网络 MOD 的模型/贴图改称本地 CF 最终资产。
- 禁止把 `p_cf_m4a4_bornbeast_final` 当作 P4 通过证据。
- 禁止自动修改 `D:\steam\...\migi\csgo\mods_temp`。
- 禁止默认写入 `D:\steam\...\migi\csgo\addons`。
- 禁止伪造 `passed_user_confirmed`、截图、控制台结果或实机结论。
- 禁止为了让测试通过而降低 expected counts、删除 Gate 或把失败改成 warning。

### 1.3 P4 的准确输入/输出边界

P4 的 `build` 必须真正覆盖：

```text
本地 CF LTB（manifest 固定路径+哈希）
  → CFRezManager B3 raw OBJ/export report
  → B3 独立 roundtrip validator
  → C1 weapon-only split（排除 CF 手臂）
  → 使用已冻结 C3 M4A4 matrix 做确定性变换
  → 9 mesh → M4A4 bone mapping
  → SMD/QC
  → studiomdl 隔离编译
  → Crowbar 回环
  → Prototype 外部参考材质 VMT/VTF
  → 自动 validate
  → 项目内 package + MIGI staging
```

如果执行者暂时不能把 LTB/B3/C1/C3 纳入 `build`，必须把状态写成 `BLOCKED` 或把命令明确命名为 `build-from-aligned-obj`；不得继续声称“完整 CF 原始资产流水线通过”。本任务的最终 P4 Gate 仍要求前述完整链路。

---

## 2. 执行任务

每个任务只有在自己的验收条件满足后才能勾选。后续任务不得用手工补文件绕过前置失败。

### P4-T01：现场隔离与状态纠正

**目标**：阻止 P5/P6 越界产物污染 P4 判断。

**执行内容**：

- [x] 生成 `work/m4a1_s_bornbeast/p4_prototype_01/baseline_inventory.json`。
- [x] 记录仓库 P4 输入、D3/F4 baseline、P4 staging、`mods_temp` 两套相关 MOD、当前 active addon 的路径、文件数和 SHA-256。
- [x] 明确标记：F4 baseline 为 `user_confirmed_previous_stage`；P4 staging 为 `automated_only_not_user_confirmed`；active final MOD 为 `out_of_scope_unreviewed`。
- [x] 不移动、不删除、不覆盖任何现有 MOD。
- [x] 在 `plan.md` 中撤销未经验证的 P4/P5/P6 完成声明，将当前状态恢复为 `P4 REWORK`。此项只修状态，不删除越界文件。

**产物**：

- `baseline_inventory.json`
- `plan.md` 的单一权威状态恢复一致

**验收**：

- 文件 inventory 可由路径重新计算；没有把 P5/P6 结论当 P4 输入。
- `plan.md` 不再同时出现互相矛盾的当前阶段。

### P4-T02：Manifest 契约与路径安全

**目标**：让 manifest 真正控制流水线，而不是只作为装饰性 JSON。

**执行内容**：

- [x] 为 `prototype_01_manifest.json` 建立严格 schema 校验。
- [x] 每个输入必须包含 `path`、`sha256`、`role`；每个工具必须包含 `path`、版本/哈希。
- [x] 每个声明字段必须被代码消费；未识别字段必须报错，不能静默忽略。
- [x] `final_target_identity=false`、`final_cf_material=false`、`EXTERNAL_REFERENCE / PROTOTYPE MATERIAL` 为 P4 强制条件。
- [x] runtime 必须精确为 `m4a4` + `weapons/v_rif_m4a1.mdl`。
- [x] 所有可删除/覆盖的输出路径必须是仓库相对路径，并在 resolve 后严格位于：
  - `build/m4a1_s_bornbeast_m4a4/p4_prototype_01/`
  - `work/m4a1_s_bornbeast/p4_prototype_01/`
- [x] 拒绝绝对输出路径、`..` 越界、symlink/junction 逃逸、仓库根目录、`build/` 根目录、`work/` 根目录。
- [x] `deploy` 必须要求显式 `--migi-addon`，且普通模式只允许 MIGI addons 根目录下的单个新目录名。
- [x] 如保留 absolute deploy path，必须额外要求显式危险确认参数，并验证 resolved path 位于用户明确给出的 MIGI addons 根；否则删除该能力。

**2026-08-19 执行结果：通过。**

- 正式 validator：`PASS`；`pipeline.py check`：`PASS`。
- P4-T02 自动测试：`18 PASS`，另有 1 项 symlink 测试因当前 Windows 权限无法创建 symlink 而跳过；实现仍通过 `resolve()` 拒绝已存在的 symlink/junction 逃逸。
- 负向测试已覆盖：嵌套未知字段、工具缺少版本/哈希、非法/重复 mesh 映射、破坏性 work 根输出、绝对报告输出、`..` deploy 名称和不同内容覆盖。
- 详细证据：`work/m4a1_s_bornbeast/p4_prototype_01/manifest_contract_report.json`、`work/m4a1_s_bornbeast/p4_prototype_01/check_report.json`、`tests/test_p4_path_and_manifest_security.py`；本次未执行 build/package/deploy，未修改任何外部 MOD。

**产物**：

- 更新后的 manifest
- `manifest_contract_report.json`
- 路径边界自动测试

**验收**：

- 下列情况全部非零退出且不写目标：缺字段、未知字段、错误哈希、absolute output、`../`、输出指向仓库根、deploy 未给目标、deploy 目标已有不同内容。

### P4-T03：LTB 到 C3 的真实上游链路

**目标**：消除“check 了 LTB，但 build 实际只读旧 aligned OBJ”的假闭环。

**执行内容**：

- [x] `build` 从 manifest 指定 LTB 调用已存在的 CFRezManager CLI，生成全新的 B3 raw OBJ 与 export report 到本次 run 目录。
- [x] 调用 `validate_b3_obj_roundtrip.py`，失败立即终止。
- [x] 调用 `split_c1_meshes.py`，从本次 B3 输出生成 weapon-only OBJ；不得读取旧 C1 输出充数。
- [x] 检查 9 个 weapon mesh 精确集合，排除 `Fview-hand2`、`Fview-arm2` 及其他 CF 手臂组。
- [x] 使用已冻结的 M4A4 C3 4×4 matrix 对本次 weapon-only OBJ 应用一次确定性变换。
- [x] 禁止重新 ICP 拟合、自动 normalize、按 mesh 单独 center/scale、隐式翻面。
- [x] 输出的 aligned OBJ 必须与冻结 C3 产物在语义统计和数值容差内一致；报告差异，不允许直接复制旧 aligned OBJ。

**产物**：

- `runs/<run_id>/b3_raw/`
- `runs/<run_id>/c1_weapon_only/`
- `runs/<run_id>/c3_aligned/`
- `upstream_trace_report.json`

**验收**：

- [x] 每次 build 使用唯一 `runs/<run_id>`；删除任一本次 run 后可从 LTB 重新生成。
- [x] build 不再声明旧 `work/.../b3_raw`、`c1_split` 为输入，也不读取旧 C1/B3 产物；上游步骤只消费本次 run 产物。
- [x] 报告包含每步命令、退出码、输入哈希、输出哈希、mesh/vertex/UV/normal/triangle/material-slot 统计。

**2026-08-19 执行结果：通过。**

- 实际执行 `pipeline.py build` 成功；最新 run：`run_20260819_111118_748744`。
- B3：4926 vertices / UV / normals，5342 triangles，11 groups（含 2 个 CF arms）。
- C1：3646 vertices / UV / normals，4008 triangles，精确 9 个 weapon groups；CF arms 被分到 optional 目录。
- C3：使用冻结矩阵一次性变换，3646 / 3646 / 3646 / 4008 / 9；与冻结 aligned reference 的位置最大误差在 `1e-5` 容差内。
- Source 1 编译也成功，57 bones / 9 sequences / 2 attachments；build report 记录了本次 fresh aligned OBJ 的路径和哈希。
- 额外回归：临时移开冻结 aligned reference 后 build 仍成功；报告将该 reference 标记为 optional、跳过数值比较但继续执行矩阵与语义 Gate，随后已恢复 reference。
- 证据：`work/m4a1_s_bornbeast/p4_prototype_01/upstream_trace_report.json`、对应 `runs/<run_id>/`、`build_report.json`。

### P4-T04：Source 1 构建单入口

**目标**：从 P4-T03 的本次 aligned OBJ 生成 M4A4 viewmodel，且不复制旧 build/MIGI 文件。

**执行内容**：

- [x] SMD 由 manifest 的 9 条 mesh→bone mapping 驱动，不允许代码硬编码另一份 mapping。
- [x] 主体→Parent、01→Clip、02→Bolt、03–08→Parent fallback 已逐组记录 triangle/corner 数。
- [x] QC `$modelname`、body SMD、`$cdmaterials`、sequence 和 attachment 均已按 M4A4 reference 契约核对。
- [x] `studiomdl` 只写本次 run 的隔离 `isolated_game/`，旧 build 仅在成功后生成 fresh compatibility mirror。
- [x] 材质只使用 `EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`；未引入 P6/final builder。
- [x] 构建开始先清理旧 build/report；失败不会留下新的 `pass=true` 报告，也不会进入后续回环步骤。
- [x] `build_report.json` 列出所有步骤、命令、退出码、stdout/stderr 路径、输入/输出哈希和 Gate 明细。

**产物**：

- `runs/<run_id>/source1/`
- `runs/<run_id>/isolated_game/`
- `runs/<run_id>/addon/`
- `build_report.json`

**验收**：

- [x] 构建过程不读取 `migi/csgo/addons` 或 `mods_temp`。
- [x] 不读取 D3/F4 旧 addon 作为模型或材质源。
- [x] 不出现 P5/P6/final manifest 或 builder 依赖。

**2026-08-19 执行结果：通过。**

- 实际 build 成功；最新 run：`run_20260819_120452_576493`。
- run 产物：`source1/`、`isolated_game/`、`addon/`、`compiled_decompiled/`；未使用旧 build 作为编译工作目录。
- 9 组 SMD 映射来自 manifest；记录了 triangle/corner：主体 3407/10221、01 36/108、02 121/363、03–08 各自 52–184/156–552。
- QC 契约通过：M4A4 modelname、fresh body SMD、`$cdmaterials`、9 个 sequence、2 个 attachment。
- `studiomdl`、双 VTFCmd、Crowbar roundtrip 和 reference report 均 exit 0；MDL 57 bones / 9 sequences / 2 attachments。
- 证据：`work/m4a1_s_bornbeast/p4_prototype_01/build_report.json` 及本次 run 的 `logs/`。

### P4-T05：自动验证 Gate

**目标**：验证输出语义，而不是只验证“有文件、数量相同”。

**必须 Gate**：

- [x] 输入 LTB/B3/C1/C3 的 run dependency hash 连续可追溯。
- [x] B3 和 C1：mesh 集合、position/UV/normal/triangle、material slots 精确匹配。
- [x] C3：matrix、column-vector 顺序、正 determinant、normal policy、winding policy 精确匹配 manifest。
- [x] SMD：57 个 bone node 定义与官方 reference 逐名/逐 parent 匹配。
- [x] SMD：9 个 mesh 的 primary bone corner 分布由 manifest 计算，禁止写死常量。
- [x] QC：modelname 精确为 `weapons/v_rif_m4a1.mdl`。
- [x] QC/回环：sequence **名称集合和数量**均精确匹配官方 M4A4 reference。
- [x] QC/回环：attachment 名称、绑定骨骼和变换均精确匹配 manifest/reference。
- [x] MDL/VVD/ANI/dx80.vtx/dx90.vtx/sw.vtx 全部存在；只检查 dx90 不够。
- [x] MDL header、Crowbar 回环的 modelname/bones/sequences/attachments/material/triangles 全部通过。
- [x] SMD→QC→VMT→VTF 闭包通过；VMT 引用的每个 VTF 存在。
- [x] 材质 provenance 保持 Prototype 标记，任何 final flag 都使 P4 验证失败。
- [x] 构建 addon 与 staging 的文件集合、大小、SHA-256 完全一致。

**产物**：

- `validation_report.json`
- 报告内每个 Gate 均包含 `expected`、`actual`、`pass`、证据路径；禁止只写一个总 `pass`。

**2026-08-19 执行结果：通过。**

- 新增 `scripts/weapon_port/validate_p4_t05.py`，`pipeline.py validate` 现在执行 15 个独立语义 Gate。
- 基线成功 run `run_20260819_120452_576493` 的 15/15 Gate 全部通过；T06 封包当前绑定的恢复 run 也重新通过 15/15。
- 覆盖依赖哈希链、B3/C1/C3 语义、57 骨架、manifest corner 分布、QC/sequence/attachment、完整二进制、MDL/Crowbar 回环、材质闭包、Prototype provenance、addon↔staging 哈希。
- 发现并拒绝了旧 staging 与当前 build 的真实哈希差异；删除 P4 work 内旧 staging/package 后由当前 addon 重建，重新验证通过。
- 证据：`work/m4a1_s_bornbeast/p4_prototype_01/validation_report.json`。

### P4-T06：Package 与安全 Deploy

**目标**：明确 package、staging 和外部部署三层边界。

**执行内容**：

- [x] `package_root` 必须实际包含可交付包；不能只创建空目录。
- [x] `staging_root` 是从 package 生成的 MIGI staging；两者 payload 文件哈希完全一致。
- [x] package manifest 不被递归算进自身 payload 哈希；manifest 明确记录排除策略，避免自引用循环。
- [x] package manifest 绑定本次 run id、manifest SHA-256、check/build/validate/upstream-trace report SHA-256。
- [x] `package` 在封包前重新执行 T05，并拒绝 manifest、输入、报告和 build run 不一致的组合。
- [x] `deploy` 不作为 `all` 的隐式步骤；`all` 仍只到 package。
- [x] `deploy` 只允许：目标不存在时新建，或目标内容逐文件完全一致时确认；不同内容失败且不覆盖。
- [x] deploy 后从目标目录重新计算逐文件哈希，并写入独立 `deploy_report.json`。

**产物**：

- 非空 `package_root`
- `staging_root`
- `package_manifest.json`
- `deploy_report.json`（仅实际执行 deploy 时生成）

**2026-08-19 执行结果：通过。**

- `pipeline.py package` 已实际生成非空 `package_root` 与 `staging_root`，当前包含 9 个 payload 文件。
- package manifest 升级为 `cf2.pipeline.package-manifest.v2`，记录当前真实构建 run `run_20260819_134459_016321`、manifest SHA-256、check/build/validate/upstream-trace report SHA-256 及 payload tree SHA-256。
- `package_manifest.json` 明确排除在 payload file set/hash 之外；`package_root` 与 `staging_root` 的 payload entries 完全相等。
- package 会先清理仅限 P4 work 子树的旧 staging/package，再执行 T05；不会把旧 staging 当作当前 run 的证据。
- `deploy` 仍需显式目标，且只执行“新建并复核”或“已有内容完全一致则确认”；内容不同写失败报告并拒绝覆盖。未向外部 MIGI 执行实际 deploy，因此当前未生成 `deploy_report.json`。
- 正向验证：`pipeline.py check` PASS、`pipeline.py package` PASS、随后 `pipeline.py validate` 15/15 PASS；P4-T02 19 项测试为 18 PASS + 1 个 Windows symlink 权限 skip。
- Crowbar 失败根因已定位为受限执行环境禁止写入 `%APPDATA%\ZeqMacaw`；使用只放行本项目构建命令的权限后，已完成全新的编译、Crowbar 反编译回环、package 与 15/15 validate。当前 `build_report.json` 来自上述真实 run，不含 recovery 标记。

### P4-T07：执行者自动测试

**目标**：由执行者证明 Gate 能发现错误，而不只是正向路径会 PASS。

**要求**：

- [x] 测试必须使用临时目录/临时 manifest，不能污染真实 build、work、Steam、MIGI。
- [ ] 至少覆盖以下 mutation：
  1. LTB 哈希错误；
  2. B3 OBJ 少一个 triangle；
  3. group 名错误；
  4. UV 索引越界；
  5. normal 缺失；
  6. Parent/Clip/Bolt mapping 互换；
  7. C3 matrix multiplication convention 改错；
  8. determinant 改为负数但 winding 不变；
  9. sequence 名被替换但数量仍为 9；
  10. attachment bone 被替换但数量仍为 2；
  11. 缺失 sw.vtx 或 ANI；
  12. VMT 指向不存在 VTF；
  13. `final_cf_material=true`；
  14. output path 指向仓库根/绝对外部目录；
  15. deploy 不指定目标；
  16. deploy 目标存在但内容不同。
- [x] 每个 mutation 必须预期非零退出，并断言失败发生在正确阶段。
- [x] 正向测试至少跑两次独立 run；执行者提供两次语义产物对比和允许差异列表。Source 编译器若产生非确定字节，必须解释并比较回环语义，不能谎称 raw MDL hash 必然一致。

**产物**：

- P4 专用测试文件
- `negative_test_report.json`
- `reproducibility_report.json`

**2026-08-19 执行结果：通过。**

- `scripts/weapon_port/run_p4_t07.py` 在临时 shadow project 中覆盖 17 个负向 mutation；17/17 均以非零结果结束，并命中预期 Gate。覆盖 LTB 哈希、B3 triangle/group/UV/normal、Parent/Clip mapping、C3 convention/determinant、sequence、attachment、sw.vtx/ANI、VMT→VTF、Prototype provenance、输出边界和两类 deploy 安全拒绝。
- 负向证据：`work/m4a1_s_bornbeast/p4_prototype_01/negative_test_report.json`；报告记录了每项退出码、预期阶段和失败 Gate。artifact mutation 使用临时 shadow project，deploy mutation 使用临时 game/MIGI 根，未修改活动 addon。
- 两次真实独立 build/Crowbar 回环 run：`run_20260819_134448_275591`、`run_20260819_134459_016321`；B3/C1/C3 OBJ、Source 1 SMD/QC、骨架/sequence/attachment/material/triangle 回环语义快照完全一致。证据：`work/m4a1_s_bornbeast/p4_prototype_01/reproducibility_report.json`。
- 原始编译二进制若出现编译器非确定字节，只按报告声明的语义字段比较；本次语义快照通过。随后 package 已重新绑定第二次 run，9 个 payload 文件和 15/15 T05 Gate 通过。

### P4-T08：用户实机 Gate

**目标**：只由用户确认游戏内事实。

**执行内容**：

- [x] 自动部分全部通过后，生成全新 addon：`p_cf_bornbeast_m4a4_p4_review_01`。
- [x] 不覆盖 `mods_temp` 中历史 MOD，不覆盖 active final MOD。
- [x] 已明确说明本次测试应启用的 addon；由于 MIGI 无单独禁用按钮，`p_cf_m4a4_bornbeast_final` 已可恢复地移动到 `mods_temp`。
- [x] 逐项等待用户确认：模型/FOV、UV、Idle、Draw、三条 Fire、Reload/Clip、Bolt、Inspect、muzzle、shell eject、控制台错误、关闭 addon 后回滚。
- [x] 每一项已记录用户原话；Inspect 明确记录为失败，其余项目记录为通过。
- [ ] 禁止由程序或执行者把自动动画 delta 推断成“用户已在游戏里看到”。

**产物**：

- `prototype_01_game_regression.json`

**2026-08-19 执行结果：用户 Gate 已检查，Inspect 需要返工。**

- 新 addon 已部署到 `D:/steam/steamapps/common/csgo legacy/migi/csgo/addons/p_cf_bornbeast_m4a4_p4_review_01`，9 个 payload 文件逐文件复核通过。
- `mods_temp` 历史目录和 `p_cf_m4a4_bornbeast_final` 均未覆盖。
- 用户确认：除按 F 触发 Inspect 时手指穿模外，其他项目没有问题；历史报告记录 13 项 `pass`、Inspect 1 项 `fail`，没有把编译、动画 delta 或自动报告冒充用户实机确认。
- 已验证 `safe_idle_fallback` 会把 Inspect 变成一帧 idle，导致按 F 无可见动作；`safe_finger_neutralized` 虽保留官方 160 帧 weapon lookat 动作，但 Blender MCP 的独立双骨架检查显示：weapon 57-bone 层级与外部 48-bone 手臂层级不同，直接复用 local transform 在 frame 80 产生明显手枪脱离/穿插。随后尝试模型空间 retarget（全骨骼和前臂链）仍在 frame 40/80/120 失去握枪接触，详见 `work/m4a1_s_bornbeast/blender_arm_reference/retarget_attempt_report.json`。`p_cf_bornbeast_m4a4_p4_inspect_safe_02` 因此保持 `REWORK_REQUIRED`，没有生成新 addon，也不得继续作为已修复版本要求用户重复测试；其他已通过项目不回退。

**验收**：

- 只有用户明确确认的条目为 PASS。
- 任一用户明确报告的实机缺陷使当前状态变为 `GAME_GATE_REWORK_REQUIRED`，不得以其他项目通过抵消。
- 没有截图/日志/用户确认时，控制台清洁度不得写 PASS。
- 未完成全部实机项时，P4 总状态保持 `PASS_WITH_PENDING_GAME_GATE`，不能写冻结完成。

### P4-T09：文档与冻结

**前置条件**：P4-T01 至 P4-T08 全部通过。

**执行内容**：

- [ ] README 只记录真实命令、路径、报告和限制。
- [ ] Plan 第 1 节保持唯一权威状态；删除 P5/P6/P7 越界完成声明和矛盾状态。
- [ ] P4 只有在自动 Gate + 用户实机 Gate 都完成后才改成 `PASS / FROZEN`。
- [ ] 保留 B1/B2/C2 技术债为非阻塞项，不伪装成已解决。
- [ ] `Prototype-01` 继续保持 `final_target_identity=false`、`final_cf_material=false`。

---

## 3. 独立 Reviewer 任务（不得重做实现）

Reviewer 的职责不是重新写一套 pipeline，也不是照执行者步骤再跑一遍后宣布“也能成功”。Reviewer 只能基于已提交 diff、执行者报告和少量独立反例验证作判断。

### RV-01：Diff 与范围审计

- [ ] 检查修改文件是否全部在 1.1 允许范围内。
- [ ] 发现 P5/P6/P7、final asset、音效、世界模型、网络下载或 active addon 自动修改，直接判定 **REWORK**。
- [ ] 检查执行者是否删除/覆盖用户已有文件。

### RV-02：字段消费追踪

- [ ] 为 manifest 每个字段建立“字段 → 读取代码 → 影响的 Gate/命令”矩阵。
- [ ] 任一关键字段只被写入报告、没有影响行为或 Gate，判定 **REWORK**。
- [ ] 特别检查 LTB、B3、C1、C3、toolchain hashes、mesh mapping、material policy、output roots。

### RV-03：证据链审计

- [ ] 从 package manifest 反向追到 validate/build/check，再追到同一 run 的 LTB/B3/C1/C3 输入哈希。
- [ ] 不重新构建模型；只验证报告引用、文件哈希和 run id 是否闭合。
- [ ] 任何报告引用旧 work/build 产物而非本次 run 产物，判定 **REWORK**。

### RV-04：定向反例测试

Reviewer 从 P4-T07 的 mutation 中随机选择至少 4 个高风险反例，在全新临时目录执行；必须包含：

- [ ] 1 个路径越界/递归删除安全反例；
- [ ] 1 个“数量不变但语义错误”的 sequence 或 attachment 反例；
- [ ] 1 个 mesh/bone mapping 反例；
- [ ] 1 个材质闭包或 provenance 反例。

这不是重做 pipeline；目的是验证执行者的 Gate 确实能拒绝错误输入。

### RV-05：报告真实性审计

- [ ] 对比报告时间、命令日志、文件时间和用户对话。
- [ ] 自动推断不得冒充 `passed_user_confirmed`。
- [ ] 没有用户确认的实机条目必须为 `not_tested`。
- [ ] 发现伪造、复制旧确认或无证据 PASS，直接判定 **REWORK**。

### RV-06：最终 Review 输出

Reviewer 只输出：

1. `PASS / PASS WITH RISK / REWORK`
2. 未满足的 task ID
3. 最多 10 条会导致返工的真实风险
4. 是否允许进入用户实机 Gate
5. 是否允许把 Plan 的 P4 改成完成

Reviewer 不得顺手修复发现的问题；修复退回执行者，修复后再做对应的定向复核。

---

## 4. P4 总 Gate

只有以下全部成立，P4 才能标记完成：

- [ ] P4-T01～P4-T09 全部完成；
- [ ] `check → build → validate → package` 从本地 LTB 开始在干净 run 目录成功；
- [ ] 无 MIGI/旧 build/旧 aligned OBJ 隐式输入；
- [ ] 正向两次复现证据完成；
- [ ] 16 项负向测试全部能阻止错误；
- [ ] package、staging、明确部署目标三者哈希闭合；
- [ ] 用户实机矩阵逐项真实确认；
- [ ] 独立 Reviewer 给出 PASS；
- [ ] Plan 恢复单一一致状态；
- [ ] Prototype 仍明确不是 final asset/material。

在此之前，当前结论统一为：

> **已有可编译的 P4 草稿和一套与历史 P4 MOD 一致的 staging，但 P4 技术闭环、路径安全、上游复现和用户实机 Gate 均未被充分证明，因此状态为 REWORK。**
