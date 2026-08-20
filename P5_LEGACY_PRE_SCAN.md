# P5_LEGACY_PRE_SCAN.md — 历史本地广召回记录

> historical execution id: `P5-T01`（旧编号）
>
> 当前语义名称：`P5 LEGACY PRE-SCAN`
>
> 状态：`EXECUTION_PASS / PRESERVED_FOR_REUSE`

此文件用于解决 P5 任务编号重构后的历史追踪问题。

在新的 P5 工作流中：

```text
P5-T01 = 官方 CF 武器百科 Web Search + 用户确认目标图
P5-T02 = 本地候选缩圈 / 去重 / 百科式侧视图比对 + 用户确认本地候选
P5-T03 = Resource Graph / provenance closure
P5-T04 = Chat/Sol final identity review
```

此前 Luna 已经以旧 `P5-T01` 名义完成过一次本地 `data/**` 广召回。该执行结果**不作废、不重跑、不改写历史 task_id**，现在统一称为 `LEGACY PRE-SCAN`，仅作为新 P5-T02 的候选池输入。

历史执行提交：

```text
ab7e2ef3394991ef0b4468f34cf4d6849b917dc2
```

历史输出：

```text
work/p5_leishen/t01/candidate_index.json
work/p5_leishen/t01/candidate_matrix.csv
work/p5_leishen/t01/scan_report.md
work/p5_leishen/t01/execution.json
```

历史结果摘要：

- `data/**` inventory：165082 files；
- recalled candidates：2856；
- LTB candidates：1281；
- canonical LTB inspected：441；
- 未把任何候选写成最终 `IDENTITY_CONFIRMED`；
- 原始 `data/**` 未上传。

重要语义：

- 旧 score 只表示召回优先级，不表示身份置信度；
- 旧任务中 `Transformers`、`BornBeast`、`Thor`、`Leishen` 等 token 都只能视为搜索线索；
- 新 T02 可以复用 candidate index/matrix 来避免重新扫描全部 16 万文件；
- 最终识别必须从新 T01 的**用户确认官方目标图**开始。

旧 `P5_T01_TASK_SPEC.md` 的完整历史版本可从 Git 提交历史读取；本文件只作为当前工作流的兼容说明。