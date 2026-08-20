# CF 武器 → CS:GO Legacy Source 1 转换流水线计划

> 最后更新：2026-08-20
>
> 当前状态：**P4 `PASS / FROZEN`；P5 `READY_TO_START`**
>
> 当前运行槽位：**M4A4**
>
> 冻结技术样机：**`Prototype-01`**
>
> 当前内部模型名：`weapons/v_rif_m4a1.mdl`
>
> 当前核心目标：**P4 已冻结转换技术流水线；现在进入 P5，准确定位真正雷神对应的本地 CF 模型、贴图、Shader、声音等原始资产，然后在 P6 只替换输入重跑冻结流水线。**

本文第 1 节是项目唯一 authoritative progress/status。README 负责工具说明和证据索引；`CODEX_TASKS.md` 负责本地执行 Agent；`CHAT_REVIEW.md` 负责 Chat/Sol 的计划、Review 和测试设计；`P4_STATUS.md` / `P4_REVIEW_RESULT.md` 保留 P4 冻结证据。

---

## 1. 唯一权威进度

### 1.1 P4 — PASS / FROZEN

P4：通用流水线稳定化与冻结验收，已完成。

#### 自动技术闭环

- P4-T01～T07：完成；
- manifest 契约、输入/工具 hash、输出路径与 destructive-operation guard 已建立；
- `build` 从 manifest 指定本地 CF LTB fresh 执行 B3 → C1 → C3，不以旧 aligned OBJ / MIGI / build 充数；
- Source 1 build、Crowbar roundtrip、15 个语义 Gate 通过；
- package / staging / deploy provenance 闭合；
- T07 执行 17 个负向 mutation，17/17 被预期 Gate 拒绝；
- 两次独立正向 build 的语义 snapshot 一致。

#### P4-T08 用户 Gate

状态：`passed_user_confirmed`。

当前冻结 addon：

`p_cf_bornbeast_m4a4_p4_frozen_noop_01`

冻结 build run：

`run_20260819_170013_270792`

用户已确认 frozen/no-op Inspect：

- 无崩溃或明显运行错误；
- 无可见 Inspect 动作符合当前策略预期；
- 武器状态正常返回；
- 之后仍可射击、换弹、切枪。

不把以下内容伪装成已完成：

- `console_errors`：`not_tested`；
- addon 停用后的 rollback：`not_tested`；
- 真正可见 Inspect、手指接触/穿模、Blender retarget：P7。

#### 独立 Review

Chat/Sol 最终 Review：**`PASS WITH RISK`，允许 P4 `PASS / FROZEN`。**

- RV-01：PASS；
- RV-02：PASS WITH NON-BLOCKING RISK；
- RV-03：PASS；
- RV-04：PASS，4/4 独立高风险反例精准命中预定 Gate；
- RV-05：PASS WITH NON-BLOCKING RISK；
- RV-06：PASS WITH RISK，允许冻结。

Implementation Review baseline：

`10aa99b770e575300ca3c28324ef3de3d5b70c6b`

RV-04 evidence commit：

`fd61d6ae7567a01c585e1144e2cab88ddb6aa85d`

最终 Review：[`P4_REVIEW_RESULT.md`](P4_REVIEW_RESULT.md)

P4 最终快照：[`P4_STATUS.md`](P4_STATUS.md)

#### P4 冻结边界

P4 冻结只证明：

> 一个已知 CF M4 Prototype 可以通过当前 manifest-driven 流水线稳定进入 CS:GO Legacy M4A4，并形成可追踪、可验证、可部署的 Source 1 addon。

P4 冻结**不证明**：

- 当前候选就是最终雷神；
- 当前网络参考材质是最终 CF 材质；
- CF 原动画已接入；
- visible Inspect / 手指 retarget 已解决；
- 世界模型/掉落模型已经最终化。

除非后续发现 frozen contract 本身回归，否则 P5/P7 问题不得重新打开 P4。

### 1.2 P5 — READY_TO_START

P5：**最终雷神资产定位。**

目标不是继续改流水线，而是在本地 `data/**` 中建立最终资产身份链：

```text
用户/参考视觉特征
  -> 本地 CF 候选文件扫描
  -> 模型轮廓 / mesh / 机械件特征比对
  -> DTX/TGA atlas / UV / Shader 名称比对
  -> 同变体声音/动画/配置关联
  -> 原始路径 + SHA-256 + 证据
  -> 最终雷神资产集合
```

P5 退出条件：

1. 最终第一人称枪模候选有明确本地 CF 原始路径与 SHA-256；
2. 模型轮廓、关键机械结构、mesh/分件与雷神参考相符；
3. 最终贴图/atlas 有本地 CF 路径与 SHA-256，视觉特征与模型 UV 可以对应；
4. Shader/CFG/材质关联可追溯；
5. 与该变体关联的声音/动画资源至少完成路径级关联和来源说明；
6. 网络截图、第三方 MOD、Wiki 只能作为识别 reference，不能进入 final asset provenance；
7. 形成 P5 candidate matrix，排除项必须记录排除原因，避免 Agent 下一轮重新搜索已否决候选；
8. Chat/Sol Review 允许把最终资产集合交给 P6。

当前下一步：**Chat/Sol 先设计 P5 的 candidate-scan / evidence task；Luna 再在本地 `data/**` 执行。**

---

## 2. 两条任务线必须分离

### Track A：转换技术流水线

回答“任意已知 CF 武器资产能否稳定进入 CS:GO Source 1”。

```text
CF 输入清单
  -> LTB/纹理/音频检查
  -> mesh/UV/normal/material slot 导出
  -> Source 坐标与目标骨架映射
  -> SMD/QC/VMT/VTF
  -> 隔离 studiomdl
  -> 编译后回环/语义校验
  -> package / staging / deploy
  -> 实机回归
```

Track A 的首个 Prototype 已在 P4 冻结。

### Track B：最终目标资产定位

回答“真正雷神对应本地哪套 LTB/DTX/TGA/CFG/WAV”。

Track B 当前由 P5 执行。未完成时禁止把 `Prototype-01` 改名为“最终雷神”，但不得因此回退 P4 已通过的 Track A 证据。

---

## 3. 资产来源政策

### 正式允许

- 本地 CF 原始资源：最终模型、材质、动画和音效的唯一正式来源；
- 本地 CS:GO Legacy VPK：目标 skeleton、sequence、attachment、QC 和 runtime 兼容基线。

### 只允许作为 reference

- 网络截图；
- Wiki / 展示页；
- 第三方 MOD；
- 网络 GoldSrc/CS1.6 贴图。

这些可用于候选识别、UV/视觉方向判断和 Prototype 调试，但必须保持 reference/prototype 标签。

### 禁止

- 将第三方 MOD 模型、贴图、动画或声音写成最终 CF 资产；
- 用第三方 MOD 成功运行证明本地 CF parser 语义正确；
- 用改名复制其他 CS:GO 武器满足最终验收；
- 在 manifest/report 中省略外部来源；
- 为了资产身份准确而删除/重写 P4 已通过的技术闭环。

---

## 4. 阶段定义与退出条件

本节只定义阶段；当前进度只看第 1 节。

### P0：Source 1 基线与安全构建

官方参考提取、反编译、隔离编译、回环报告、安全 MIGI deploy 和 M4A4 runtime contract。

### P1：CF 静态资源导出

LTB node/mesh、position、normal、UV、winding、material slot 可导出，weapon mesh 与 CF 手臂可分离。

### P2：M4A4 Source 映射

M4A4 57-bone reference、对齐变换、mesh→bone mapping、attachment 和官方动作兼容。

### P3：编译、材质引用、MIGI 与历史实机基线

9 mesh viewmodel、官方 M4A4 sequence、VMT/VTF 引用闭包、MIGI 和历史游戏内基线。

### P4：通用流水线稳定化 — FROZEN

manifest-driven fresh build、语义 Gate、package/deploy、negative mutation、reproducibility、用户 Gate、独立 Review。

### P5：最终雷神资产定位 — ACTIVE NEXT

本地候选模型/贴图/Shader/声音身份确认与 provenance。

### P6：最终资产替换与发布质量

只替换 manifest final 输入重跑冻结流水线；最终本地 CF mesh/UV/material 正确；final addon 不依赖网络 MOD 文件。

### P7：增强范围

- visible Inspect；
- 手臂/手指 retarget、接触与穿模；
- CF 原版动画；
- 动态红光 / Shader 近似；
- CF 音效与事件同步；
- 第三人称/落地模型/掉落弹匣；
- LOD、性能档位与批量武器转换。

---

## 5. P4 冻结合同

- manifest 记录输入路径/hash、M4A4 runtime、mesh→bone、transform、material policy、输出路径和工具 provenance；
- `final_target_identity=false`、`final_cf_material=false` 保持机器可读；
- `check/build/validate/package` 只写受控 `work/`、`build/`；
- `deploy` 必须显式安全目标，不能覆盖内容不同的 addon；
- 上游失败下游不得继续；
- 报告绑定 run id、manifest、输入/输出 hash 和实际 Gate；
- 自动证据不得冒充用户实机确认；
- P4 frozen/no-op Inspect 只保证状态安全，不宣称 visual retarget。

后续阶段只能在明确版本化变更时修改该合同。

---

## 6. 已知技术债与阻塞级别

| 技术债 | 当前判断 | 阻塞 P5？ | 计划处理 |
|---|---|---:|---|
| B1 rigid mesh bone index 尚未正式进入 decoder/report | 通用语义不完整 | 否 | 第二种武器/最终资产需要时 |
| B2 bind validator 有自验证风险 | 不能单独证明通用矩阵 | 否 | 不同骨架前 |
| CF animation clips 尚未完整解码 | 无法直接使用 CF 原动作 | 否 | P7 |
| 03–08 精确机械语义未证明 | Parent fallback 仅适合 Prototype | 否 | P5/P6 根据 final asset 修正 |
| CLI Inspect policy 可 override manifest | contract 可进一步硬化 | 否 | 通用化/下一轮 pipeline hardening |
| toolchain 未完全 manifest-driven | provenance 可追踪但契约不完全 | 否 | 通用化前 |
| manifest byte SHA 跨 checkout/EOL 有歧义 | provenance 可读性问题 | 否 | 增加 canonical hash / Git blob identity |
| 当前候选身份未最终确认 | 不能称最终雷神 | **是 P5 核心任务** | P5 |
| 当前材质是外部 reference | 不能用于 final 发布 | **是 P5/P6 核心任务** | P5/P6 |
| world/drop model 仍为官方 M4A4 | 第一人称 P4 不受影响 | 否 | P7 |

修债原则：只修会影响当前阶段 Gate、final asset 替换或跨武器复用的问题；不得因为技术债存在就重写 P4 frozen 基线。

---

## 7. 冻结 Active Runtime 决策

- Active slot：M4A4；
- Model name：`weapons/v_rif_m4a1.mdl`；
- Reference skeleton：官方 M4A4 57 bones；
- Main：`v_weapon.M4A1_Parent`；
- Clip：`v_weapon.M4A1_Clip`；
- Bolt：`v_weapon.M4A1_Bolt`；
- 03–08：Prototype Parent fallback；
- P4 Inspect：`frozen_noop_safe`；
- visible Inspect / hand retarget：P7；
- 当前网络贴图：`EXTERNAL_REFERENCE / PROTOTYPE MATERIAL`；
- 当前 Prototype：`final_target_identity=false`、`final_cf_material=false`。

任何未来修改若改变这些决定，必须显式版本化 manifest/profile 与证据，不得静默切换 slot、skeleton 或状态机。

---

## 8. Definition of Done

### 8.1 P4 Prototype-01 — DONE

- manifest 指定本地 LTB 可重复生成 M4A4 Source 1 addon；
- check/build/validate/package、negative mutation、reproducibility 通过；
- model/UV/Prototype material、Idle/Fire/Reload/Clip/Bolt/attachments 可用；
- frozen/no-op 用户状态恢复 Gate 通过；
- 独立 Review `PASS WITH RISK`，风险明确且非阻塞；
- 候选身份和第三方材质明确非 final。

### 8.2 P5 Asset Identity DoD

- 最终模型、贴图、Shader、声音等均有可信本地 CF provenance；
- candidate matrix 能解释为什么最终候选胜出以及其他高相似候选为何排除；
- 模型轮廓、关键机械件和 UV/atlas 形成互相支持的身份链；
- Chat/Sol Review 允许进入 P6。

### 8.3 最终雷神 DoD

- 枪体和材质均来自经确认的本地 CF 原始资源；
- 不依赖网络 MOD final 文件；
- mesh、UV、动态件、骨骼、attachments、动作、材质和音效达到发布质量；
- Prototype fallback 被替换或作为明确限制写入发布说明；
- 冻结流水线可从 final 输入生成独立 MIGI 发布包；
- 自动报告与实机证据共同成立，且资产身份有独立 provenance。
