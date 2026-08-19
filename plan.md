# CF 武器 → CS:GO Legacy Source 1 转换流水线计划

> 最后更新：2026-08-19
>
> 当前状态：**P4-T08 Inspect REWORK_REQUIRED；Blender 已确认 safe_02 的外部手臂层级错位，P4 总 Gate 仍未完成**
>
> 当前运行槽位：**M4A4**
>
> 当前技术验证样机：**`Prototype-01`**
>
> 当前内部模型名：`weapons/v_rif_m4a1.mdl`
>
> 当前核心目标：**先把一个 CF M4 `Prototype-01` 稳定、完整地转换到 CS:GO M4A4，并建立可重复流水线；之后再准确定位真正的雷神资产并替换输入。**

本文第 1 节是项目唯一的 authoritative progress/status。README 负责工具说明和证据索引；旧阶段编号只用于关联已有报告，不再维护状态。第 4 节仅定义路线和退出条件，不重复声明进度。

---

## 1. 唯一权威进度

### 已完成并冻结

1. **Source 1 官方基线与编译闭环**
   - 已完成官方模型提取、反编译、隔离编译、回环检查、MIGI 部署和 CS:GO Legacy 实机验证。
   - 早期旧槽位官方基线只保留为工具链证据；当前运行目标、QC、MDL、动作和实机验收统一为 M4A4。
   - M4A4 基线为 57 骨、9 个序列、2 个 attachment、`rif_m4a1` 材质，内部名固定为 `weapons/v_rif_m4a1.mdl`。

2. **CF 静态枪模进入 Source 1**
   - 当前候选 LTB 已能导出枪体网格、分件、position、normal、UV、triangle winding 和 material slot。
   - 9 个枪体 mesh 已进入 M4A4 viewmodel：主体→Parent、01→Clip、02→Bolt、03–08→Parent 的 `Prototype-01` 静态降级。
   - 坐标、比例和 M4A4 对齐变换已固化在 `assets/weapons/m4a1_s_bornbeast/c3_alignment_m4a4_manifest.json`。

3. **动作与机械件 `Prototype-01` 闭环**
   - 使用官方 M4A4 Idle、Draw、Fire、Reload 和 Inspect/Lookat 序列。
   - 弹匣、枪机和主枪体已通过编译回环与分阶段实机检查。
   - 当前只验收 M4A4 原生状态集合，不引入其他武器槽位的附加状态机。

4. **材质引用闭环**
   - SMD → QC `$cdmaterials` → VMT → VTF 的引用验证器已经成立。
   - 当前可识别材质来自网络 GoldSrc/CS1.6 第三方移植包，必须标记为 **`EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`**。
   - 它只用于 `Prototype-01` 的 UV、几何和视觉调试；可证明 VTF/VMT、自发光和 MIGI 材质链可运行，但不代表最终 CF 材质转换完成。

5. **MIGI 与游戏内闭环**
   - 当前游戏内能正常看到 CF 枪模、贴图和官方 M4A4 动作。
   - 构建目录与活动 MIGI addon 已做逐文件哈希一致性检查。
   - 当前唯一活动测试 addon：`p_cf_bornbeast_m4a4_p4_inspect_safe_02`（MIGI 不提供单独禁用按钮；旧版本已移入 `mods_temp`）。
   - 上述实机可运行版本正式冻结为 **`Prototype-01`**：它是技术验证样机，不保证资产身份就是最终“雷神”，也可能是黑骑士或其他 M4 变体；当前阶段不再以枪型准确性为主线。

### 当前正在做

**P4：通用流水线稳定化与 REWORK 修复（执行 `P4_TASKS.md` 验收清单）。**

- **当前权威状态**：`P4-T08 GAME_GATE_REWORK_REQUIRED / P4 总 Gate 未完成`。
- **现场基线状态**：
  - D3/F4 原型 (`p_cf_bornbeast_m4a4_f4_recognizable_tmp`)：`user_confirmed_previous_stage`（已知可运行视觉基线，必须保留）；
  - P4 staging (`work/m4a1_s_bornbeast/p4_prototype_01/staging`)：`automated_only_not_user_confirmed`（虽与历史 MOD 一致，但完整流水线、语义 Gate 和实机行为未经证明）；
  - 历史 final MOD (`p_cf_m4a4_bornbeast_final`)：`mods_temp/out_of_scope_unreviewed`（已按 MIGI 现场规则停用，不属于 P4 验收范围，不得作为输入或通过证据）。
- **已完成**：P4-T01 至 P4-T07。T05 的 15 个语义 Gate、T06 的 package/staging/deploy 安全边界、T07 的 17 个负向 mutation 和双 run 语义可复现性均已通过。
  - **当前正在做**：P4 自动 Gate 已通过；safe_01 的 idle 回退导致按 F 无可见动作。safe_02 虽保留了官方 160 帧 weapon Inspect，但 Blender MCP 检查显示直接复制 local transform 会错位；进一步尝试模型空间 retarget 后，frame 40/80/120 仍不能保持双手握枪，因此没有生成新的生产 addon。
  - **下一步**：基于实际枪体接触点重新设计 Inspect retarget，或明确采用 Prototype 的冻结/无动作 Inspect；在 Blender 的 frame 1/40/80/120/159 通过接触检查前，不再要求用户重复测试游戏 addon。其他已通过项目保持冻结。
- **后续再做**：Blender 检查通过后重新生成唯一测试 addon，再进行一次用户实机 Inspect Gate；通过后才进入 P4-T09 文档与冻结。
- **已知技术债**：冻结 C3 aligned OBJ 仅作为可选回归参考；缺失时仍执行矩阵/语义 Gate，但数值比较会在报告中标记为 skipped。B1/B2/C2 技术债和 03–08 Parent fallback 仍不阻塞 Prototype 主线。Crowbar 0.71 启动时要求 `%APPDATA%\ZeqMacaw` 可写；受限自动化环境执行 T04 时必须授予该目录写权限。当前真实构建 run `run_20260819_134459_016321` 已完成 Crowbar 回环且不含 recovery 标记。

### 下一步

1. 修复并在 Blender 中验证 Inspect 的手臂/手指 retarget（safe_02 当前不接受）；
2. 生成新的隔离 addon 后再完成一次 Inspect 实机确认；
3. 经独立 Reviewer 审计通过后，进入 P4-T09 文档与冻结；
4. 在 Inspect 返工通过前，保持 `REWORK_REQUIRED`，不宣称 Prototype 冻结。

### 后续再做

- **P5：最终雷神资产定位与来源确认**（在本地 CF 原始资源中定位真正目标雷神的 LTB/DTX/TGA/CFG/WAV 并完成来源证明）；
- **P6：最终官方雷神资产替换与发布闭环**（用最终本地 CF 资产替换 `Prototype-01` 输入并重跑同一流水线，完成最终材质与发布包）；
- **P7：增强特性**（CF 原版动画、音效集成、第三人称/落地武器/掉落弹匣模型与自定义 Inspect 等）。

### 当前 `Prototype-01` 与“最终雷神”的区别

| 项目 | 当前 `Prototype-01` | 最终雷神 |
|---|---|---|
| 运行槽位 | M4A4 | M4A4 |
| 模型输入 | 本地 CF 候选 LTB；身份暂不作最终承诺 | 经参考图/纹理/几何反查确认的本地 CF 原始 LTB |
| 动作 | 官方 M4A4 动作 | 官方 M4A4 fallback 或经证明的 CF 原动作 |
| 材质 | `EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`，仅用于 UV、几何、视觉与链路调试 | 本地 CF DTX/TGA/CFG 转换结果 |
| 分件绑定 | 主体/Clip/Bolt 已工作；03–08 为 `Prototype-01` Parent fallback | 每个动态件有最终语义和正确骨骼绑定 |
| 目标 | 证明流水线稳定、可重复 | 证明资产身份准确并达到发布质量 |

---

## 2. 两条任务线必须分离

### Track A：转换技术流水线

Track A 回答“任意已知 CF 武器资产能否稳定进入 CS:GO Source 1”。它包含：

```text
CF 输入清单
  → LTB/纹理/音频检查
  → 静态 mesh/UV/normal/material slot 导出
  → Source 坐标与目标骨架映射
  → SMD/QC/VMT/VTF 生成
  → 隔离 studiomdl 编译
  → 编译后回环/结构校验
  → MIGI staging
  → 实机回归
```

当前项目优先完成 Track A。输入枪模是不是最终雷神，不影响 Track A 继续稳定化。

### Track B：最终目标资产定位

Track B 回答“真正雷神对应本地哪套 LTB/DTX”。它必须独立完成来源证明：

- 参考图、UI 图标、第一人称截图或用户提供的明确贴图；
- LTB mesh 轮廓、分件、顶点数和关键机械结构；
- DTX/TGA atlas 内容、UV 对应关系和 Shader 资源名；
- 同一变体的模型、材质、声音和动画资源关联；
- 原始路径和 SHA-256。

Track B 未完成时，禁止把 `Prototype-01` 改名为“最终雷神”，但也禁止因此回退 Track A 的技术闭环。

---

## 3. 资产来源政策

### 允许

- 本地 CF 原始资源：最终模型、材质、动画和音效的唯一正式来源；
- 本地 CS:GO Legacy VPK：目标骨架、序列、attachment、QC 和运行时兼容基线；
- 网络截图、第三方 MOD、Wiki/展示页：只用于识别、对照、验证视觉方向；
- 网络 GoldSrc/CS1.6 第三方贴图：可放在 `work/.../reference` 或 `Prototype-01` build 中验证链路，但必须标记为 `EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`，并记录来源、哈希和 `final=false`。

### 禁止

- 将网络第三方 MOD 的模型、贴图、动画或声音写成最终 CF 资源；
- 用第三方 MOD 成功运行来证明本地 CF parser 语义正确；
- 用改名复制其他 CS:GO 武器来满足最终验收；
- 在 manifest/report 中省略外部来源或把 `Prototype-01` 状态写成 final；
- 为了追求当前枪型身份准确而删除已经通过的构建/MIGI 证据。

当前 F4 网络材质必须继续保持 `EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`；它不是本地 CF 原始材质，不能计入最终 CF 材质转换完成或 final 发布。

---

## 4. 阶段定义与证据映射（不单独维护进度）

本节只定义各阶段内容、证据和退出条件；当前状态一律以第 1 节为准。

### P0：Source 1 基线与安全构建

成果：官方参考提取、反编译、编译和回环报告；隔离 build/work；显式 MIGI deploy；M4A4 runtime contract 已确定。

旧 A1/A2/A3 映射到本阶段。早期旧槽位产物只作为历史工具验证，不是 active runtime。

### P1：CF 静态资源导出

成果：当前候选 LTB 的 node hierarchy、mesh、position、normal、UV、winding 和 material slot 已能导出；9 个 weapon mesh 已与 CF 手臂分离；raw export 和报告可供 Source 构建使用。

旧 B1/B2/B3/C1 映射到本阶段。rigid bone index、bind matrix 独立证据和 CF clip 解码仍是技术债，但不阻塞 `Prototype-01`。

### P2：M4A4 Source 映射

成果：M4A4 57-bone reference；M4A4 专用坐标/比例变换；主体→Parent、01→Clip、02→Bolt、03–08→Parent fallback；QC attachment 和官方动作兼容。

旧 C2/C3/D1/D2 映射到本阶段。active gate 只接受 M4A4 runtime contract。

### P3：编译、材质引用、MIGI 与实机

成果：9 mesh viewmodel 编译；官方 M4A4 sequence 保留；VMT/VTF 引用闭包；MIGI addon 生成与逐文件一致性；游戏内模型、贴图和动作可见。

旧 D3/F1–F4 映射到本阶段。F4 只代表 `Prototype-01` 可识别材质，不代表最终 CF 材质完成；当前实机可运行版本必须保留，不得回滚。

### P4：通用流水线稳定化

退出条件：

- 一个 authoritative manifest 能完整描述 `Prototype-01` 输入和输出；
- 一个入口能执行 check/build/validate/package；
- 干净构建无需引用 MIGI 旧文件或手工复制；
- 所有关键工具失败都返回非零退出码；
- 编译后报告验证 model name、bones、sequences、attachments、materials 和 mesh/bone distribution；
- MIGI staging 与 build addon 逐文件一致；
- 完整实机矩阵通过并保存证据。

### P5：最终雷神资产定位

退出条件：用户参考与本地候选轮廓/贴图特征一致；模型、贴图、Shader 和声音均有本地 CF 路径与哈希；网络资源只留在 reference；生成可审计的资产选择报告。

### P6：最终资产替换与发布质量

退出条件：只替换 manifest 输入即可重跑 P4；最终本地 CF mesh/UV/material 在游戏中正确；动态件、attachments、动作和材质无未说明的 `Prototype-01` fallback；final addon 不依赖网络 MOD 文件。

### P7：增强范围

- CF 原版动画和自定义 Inspect；
- 动态红光和 Shader 近似；
- CF 音效和事件同步；
- 第三人称、落地武器、掉落弹匣；
- LOD、性能档位和批量武器转换。

---

## 5. P4 当前执行清单

### 5.1 Manifest 收敛

- 只保留一个 `Prototype-01` 构建 manifest 作为入口；现有 mesh/alignment/material JSON 作为被引用的证据文件，不各自声明总进度。
- manifest 必须记录输入路径、哈希、M4A4 runtime、mesh→bone、transform、material policy、输出路径和工具版本。
- `final_target_identity=false`、`final_cf_material=false` 必须是机器可读字段。

### 5.2 单入口流水线

计划接口：

```powershell
python scripts/weapon_port/pipeline.py check    --manifest <prototype-manifest>
python scripts/weapon_port/pipeline.py build    --manifest <prototype-manifest>
python scripts/weapon_port/pipeline.py validate --manifest <prototype-manifest>
python scripts/weapon_port/pipeline.py package  --manifest <prototype-manifest>
python scripts/weapon_port/pipeline.py deploy   --manifest <prototype-manifest> --migi-addon <new-addon>
```

约束：

- `check/build/validate/package` 只写项目内 `work/`、`build/`；
- `deploy` 必须显式指定全新或内容完全相同的 MIGI addon；
- 不覆盖内容不同的已部署 addon；
- 不改写 CS:GO 核心 models/materials；
- 上游失败时下游不得运行或打印成功。

### 5.3 自动 Gate

- LTB 输入存在且哈希匹配；
- mesh 数、position/triangle/UV/normal 数量符合 manifest；
- 没有 CF 手臂泄漏到 weapon-only 输出；
- SMD 的材料和骨骼名均可解析；
- QC model name 必须是 M4A4 `weapons/v_rif_m4a1.mdl`；
- sequence 集合与 M4A4 reference 兼容；
- `muzzle`/`muzzle_flash2`/`shell` attachment 存在且数值来自 manifest；
- 编译后 MDL/VVD/VTX 完整，回环骨骼和 mesh 分布符合预期；
- 所有 VMT 引用的 VTF 存在；
- build addon 与 MIGI staging 文件集和哈希一致。

### 5.4 `Prototype-01` 实机矩阵

- 模型整体、FOV、手持位置无明显问题；
- UV 不随机错位，`EXTERNAL_REFERENCE / PROTOTYPE MATERIAL` 可识别；
- Idle 无漂移，Draw 能正常进入 Idle；
- 三条 Fire 可播放，枪口效果和抛壳位置可接受；
- Reload 中弹匣取出/插入正常；
- Bolt/拉机柄按当前官方动作表现，无错误绑定；
- Inspect/Lookat 可进入并返回；
- 控制台无 missing model/material、bad sequence 或 bone 错误；
- MIGI 关闭或移除 addon 后可完全回滚。

---

## 6. 已知技术债及阻塞级别

| 技术债 | 当前判断 | 是否阻塞 P4 `Prototype-01` | 何时修 |
|---|---|---:|---|
| B1 rigid mesh bone index 尚未正式进入 decoder/report | 报告语义不完整 | 否 | P4 后或第二种武器暴露问题时 |
| B2 bind validator 有“自己验证自己”风险 | 不能证明通用矩阵语义 | 否 | 通用化到不同骨架前 |
| B2 CF animation clips 尚未解码 | 无法使用 CF 原动作 | 否 | P7 动画阶段 |
| C2 03–08 精确机械语义未证明 | Parent fallback 可能不适合最终资产 | 否 | P5/P6 最终资产确认后 |
| 当前候选枪身份未最终确认 | 不能称为最终雷神 | 否 | P5 |
| 当前 F4 材质为 `EXTERNAL_REFERENCE / PROTOTYPE MATERIAL` | 不能计为最终 CF 材质转换或进入 final 发布 | 否 | P5/P6 用本地 CF 材质替换 |
| 世界/掉落模型仍是官方 M4A4 | 第一人称闭环不受影响 | 否 | P7 |

修债原则：只修会影响流水线复现、第二种武器复用或最终资产替换的问题；不得以“技术债存在”为由重写已通过的 `Prototype-01` 编译/MIGI 闭环。

---

## 7. 冻结的 Active Runtime 决策

- Active slot：M4A4。
- Model name：`weapons/v_rif_m4a1.mdl`。
- Reference skeleton：官方 M4A4 57 bones。
- Active sequences：官方 M4A4 9 sequences。
- Runtime state：只使用并验收 M4A4 原生状态集合。
- Main binding：`v_weapon.M4A1_Parent`。
- Magazine binding：`v_weapon.M4A1_Clip`。
- Bolt binding：`v_weapon.M4A1_Bolt`。
- 03–08：`Prototype-01` 阶段 Parent fallback，明确非最终语义。
- CF 57-node skeleton：用于理解源资源和未来 CF 动画，不进入当前使用官方动作的 Source viewmodel skeleton。
- 当前网络贴图：`EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`；`final_cf_material=false`。

任何未来修改若改变以上决定，必须新建 manifest/profile，不得悄悄切换到其他武器槽位或状态机。

---

## 8. 两套 Definition of Done

### 8.1 流水线 `Prototype-01` DoD

- 从仓库输入可重复生成 M4A4 Source 1 addon；
- 模型、UV/材质、Idle、Fire、Reload、弹匣、枪机和 attachments 可用；
- 编译、回环、材质引用和 MIGI staging 自动校验通过；
- 游戏内完整回归通过；
- 明确标记候选资产身份和第三方材质均非 final；
- 不要求 CF 原动画、最终雷神材质或世界模型。

### 8.2 最终雷神 DoD

- 枪体和材质均可追溯到经确认的本地 CF 原始资源；
- 不依赖网络 MOD 模型、贴图、动画或声音；
- mesh、UV、动态件、骨骼、attachments、动作、材质和音效满足发布质量；
- 所有 `Prototype-01` fallback 已替换，或作为明确限制写入发布说明；
- 同一 manifest 流水线可以从 final 输入生成独立 MIGI 发布包；
- 实机证据与自动报告共同证明，不以“测试通过”替代资产身份验证。

---

## 9. 后续执行方向摘要

```text
现在：冻结当前可运行 M4A4 Prototype-01
  ↓
P4：统一 manifest + 单入口 + 自动 Gate + 完整实机回归
  ↓
冻结首个可重复 CF→Source1 流水线样本
  ↓
P5：根据用户参考，在本地 CF 资源中定位最终雷神
  ↓
P6：只替换输入资产，重跑同一流水线并完成最终材质/绑定
  ↓
P7：CF 动画、音效、动态特效、世界模型与批量化
```

下一次实现应从 **P4 Manifest 收敛** 开始，而不是继续调整当前枪型外观或切换武器槽位。
