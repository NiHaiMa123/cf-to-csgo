# CHAT_REVIEW.md — Chat/Sol Planner / Reviewer 合同

> 本文件只给 **ChatGPT 对话中的 Chat/Sol** 使用。
>
> 项目唯一权威进度以 [`plan.md`](plan.md) 第 1 节为准。Git/GitHub 与本地 `data/` 安全规则以 [`AGENTS.md`](AGENTS.md) 为准。
>
> **默认 Planner / Reviewer = Chat/Sol；Codex/Luna = 本地执行与证据生产。**

---

## 1. 当前阶段

截至 2026-08-20：

- P4：**`PASS / FROZEN`**；
- P4 最终 Review：**`PASS WITH RISK`，允许冻结**；
- P5：**`READY_TO_START` — 最终雷神资产定位**；
- P6：等待 P5 final asset identity；
- P7：visible Inspect / 手臂手指 retarget / CF 原动画等增强范围。

P4 最终证据：

- [`P4_STATUS.md`](P4_STATUS.md)
- [`P4_REVIEW_RESULT.md`](P4_REVIEW_RESULT.md)
- [`P4_RV04_TEST_SPECS.md`](P4_RV04_TEST_SPECS.md)
- `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json`

除非发现 P4 frozen contract 自身回归，否则 Chat/Sol 不因 P5 资产身份或 P7 视觉问题重新打开 P4。

---

## 2. Chat/Sol 的默认职责

Chat/Sol 负责：

- 每轮先读取最新 GitHub authoritative state；
- 设计阶段 Plan、Task Spec、Test Spec 和 acceptance criteria；
- 静态审查代码、manifest、report、hash 和 provenance；
- 决定哪些步骤必须交给本地 Luna 执行；
- 审查 Luna 返回的 raw evidence；
- 输出阶段 Review：`PASS / PASS WITH RISK / REWORK`；
- 只有证据满足 Gate 后才更新 authoritative status。

Chat/Sol 不得：

- 未执行就声称运行过 Blender/Crowbar/studiomdl/MIGI/本地 `data/**`；
- 把 Test Spec 设计完成写成测试已通过；
- 把 Luna 的“我做完了”当作唯一证据；
- 为了得到 PASS 临时降低 Gate；
- 用聊天记忆覆盖最新仓库状态。

---

## 3. 与 Luna / Codex 的职责分离

标准闭环：

```text
Chat/Sol 读最新 GitHub
  -> 设计任务 / 测试 / 验收
  -> Luna 在本地环境和 data/** 执行
  -> Luna push 代码/报告/证据，不上传 data 原资产
  -> Chat/Sol 重读 GitHub
  -> 判定 / 下一轮任务
```

需要本地执行时，Chat/Sol 应把推理结果编译成机械执行协议，而不是让 Luna 自己决定“测什么算通过”。

Codex Sol 只有用户明确点名做额外 independent audit / milestone audit 时才进入 Reviewer 角色；不是默认 Gate。

---

## 4. 当前 P5 目标

P5 回答：

> **真正雷神对应本地 CF 哪套 LTB / DTX / TGA / CFG / Shader / WAV / 动画资源？**

P5 不允许“看起来像”直接升级为 final。必须建立多证据身份链：

1. 原始本地路径与 SHA-256；
2. 模型轮廓和关键机械件；
3. mesh / 分件 / 顶点等结构特征；
4. 贴图 atlas 的雷神视觉特征；
5. UV 与 atlas 对应关系；
6. Shader / CFG / material 资源关联；
7. 同变体声音/动画命名和目录关联；
8. 候选排除原因。

网络截图、Wiki、第三方 MOD 只能作为 visual reference，不能作为 final source provenance。

---

## 5. P5 推荐任务结构

Chat/Sol 应先把 P5 拆成可独立验收的任务，例如：

```text
P5-T01  参考特征定义
P5-T02  本地候选路径/命名扫描
P5-T03  LTB 几何候选摘要与排序
P5-T04  DTX/TGA atlas 候选关联
P5-T05  模型 ↔ 贴图 ↔ Shader/CFG 交叉闭包
P5-T06  声音/动画/同变体目录关联
P5-T07  candidate matrix + 排除证据
P5-T08  Chat/Sol final identity Review
```

实际任务编号和细节以 Chat/Sol 下一次写入的 P5 Task Spec 为准，Luna 不自行创造替代 Gate。

---

## 6. P5 本地 Task Spec 最低字段

交给 Luna 的每个任务至少写清：

```text
task_id
purpose / hypothesis
scope
allowed local roots
search / extraction operation
must_preserve
expected output schema
candidate ranking rule
evidence fields
PASS / FAIL / INVALID 或 COMPLETE / INCOMPLETE
forbidden changes
upload allowlist
```

如果要生成候选预览，必须明确允许的输出形式；不要要求上传 `data/**` 原始资产。

---

## 7. P5 Review 判定原则

### 可以 PASS 的证据

- 多条独立本地证据指向同一变体；
- 模型和贴图不是仅靠文件名猜测，而有轮廓/机械结构/UV/atlas 支撑；
- final path/hash 可重复定位；
- candidate matrix 记录高相似候选和排除理由；
- 网络 reference 与本地 asset provenance 明确分离。

### 必须 REWORK 的情况

- 只靠名称包含 `Thor/Leishen/BornBeast` 等字样就宣称 final；
- 把外部 GoldSrc/CS1.6 MOD 资源写成 CF final；
- 无 hash / 原始路径；
- 不记录被排除候选，导致下轮 Agent 重复猜测；
- 模型和贴图来自不同变体却被拼成同一 final；
- Luna 自行降低身份 Gate。

---

## 8. P4 冻结风险的处理

P4 最终保留的非阻塞风险继续记录，但不阻塞 P5：

- CLI Inspect-policy override；
- toolchain 尚未完全 manifest-driven；
- console clean 未单独用户测试；
- addon-disable rollback 未单独用户测试；
- manifest byte hash 的 checkout/EOL 可移植性。

只有当这些风险在 P5/P6 实际触发错误时，才创建最小 hardening task；不要预防性重写整个 P4。

---

## 9. 当前下一步

Chat/Sol 的下一步不是继续 Review P4，而是：

> **设计并写入 P5 的第一轮资产定位 Task Spec，然后交 Luna 在本地 `data/**` 执行候选扫描与证据生产。**
