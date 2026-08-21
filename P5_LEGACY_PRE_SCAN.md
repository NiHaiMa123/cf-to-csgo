# P5_LEGACY_PRE_SCAN.md — 历史本地广召回记录

> historical execution id: `P5-T01`（旧编号）
>
> 当前语义名称：`P5 LEGACY PRE-SCAN`
>
> 状态：`EXECUTION_PASS / PRESERVED_FOR_REUSE`

此文件只解决 P5 任务编号重构后的历史追踪问题，不是当前执行入口。

当前 P5 语义：

```text
P5-T01 = 官方 CF 武器百科 Web Search + 用户确认目标图                    PASS
P5-T02 = 本地候选 + native material finalist + 用户确认                  PAUSED_BY_P4_M01
P5-T03 = Resource Graph / provenance closure                            BLOCKED_BY_T02
P5-T04 = Chat/Sol final identity review                                 BLOCKED_BY_T03
```

当前实际执行任务是：

```text
P4-M01 = BornBeast native material recovery benchmark
```

此前 Luna 以旧 `P5-T01` 名义完成过一次本地 `data/**` 广召回。该执行结果**不作废、不重跑、不改写历史 task_id**，现在统一称为 `LEGACY PRE-SCAN`，仅作为新 P5-T02 的候选池输入。

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
- `Transformers`、`BornBeast`、`Thor`、`Leishen` 等 token 只能视为搜索线索；
- T02 恢复后继续复用 candidate index/matrix，不重新扫描全部 16 万文件；
- 当前候选证据保持有效，但 native material 方法先由 P4-M01 验证；
- 最终识别仍必须同时满足 official reference、native material、用户 candidate Gate 和 T03/T04 provenance Review。

当前 official-reference T01 协议见 [`P5_T01_TASK_SPEC.md`](P5_T01_TASK_SPEC.md)；当前执行入口见 [`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md)。
