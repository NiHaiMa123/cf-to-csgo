# task.md — 当前执行任务

> 本文件只描述 **一轮可独立 Review 的当前任务**。  
> Executor 完成本文件后必须提交 evidence 并停止；由领导/Review Agent 决定哪些结果冻结进 `plan.md`，再重写下一轮 `task.md`。  
> 长期 pipeline 与冻结事实看 [`plan.md`](plan.md)。Git 操作看 [`AGENTS.md`](AGENTS.md)。

---

# 1. 当前任务

```text
Task ID: P4-M01-N02-B
Title: Runtime Butes LTC/LTA Static Decode & Target Correlation
State: ACTIVE
Parent: P4-M01-N02 Runtime Artifact Acquisition / Static Triage
Depends on: P4-M01-N02-A ACCEPTED / COMPLETE
```

目标：**优先分析 N02-A 新发现的 runtime config，而不是立即进入宽泛 EXE/DLL 反编译。判断 `rez/Butes/*.ltc` / `rez/bf000.lta` 的真实格式、可解析语义，以及它们是否能为 BornBeast / WeaponShader / model-material binding 提供直接证据。**

本轮只做静态 config triage + target correlation；完成后停止并交回 Review。

---

# 2. 已冻结输入

N02-A 已确认：

```text
trusted runtime root = D:\Program Files\CF(2)
73 x rez/Butes/*.ltc
35 x bf-prefixed .ltc within that set
rez/bf000.lta = 30,002 bytes
17 shader-bearing files
272 DLL
27 EXE
476 REZ
```

N02-A evidence：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/root_discovery.json
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/artifact_inventory.json
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/acquisition_report.md
```

N01 已冻结的旧 corpus 结论仍有效；本轮是利用 **新 runtime 输入** 做增量闭合，不重新推翻或重扫 N01。

---

# 3. 本轮必须回答

尽可能回答：

1. `rez/Butes/*.ltc` 是 plaintext、结构化文本、编译配置、编码/混淆数据，还是其他格式？
2. 这些 `.ltc` 是否共享稳定 header / record / string / key-value / table 结构？
3. `bf` 前缀文件与非 `bf` `.ltc` 是否存在可重复的结构差异或命名语义？
4. `rez/bf000.lta` 与 `bf*.ltc` 是同一 config family、索引/容器关系，还是仅文件名相似？
5. 是否能从这些 runtime config 中恢复：
   - texture / DTX / TGA / shader / model basename；
   - WeaponShader / technique / property / piece/material slot 类字段；
   - 与 N01 已知 BornBeast / Transformers / Jewelry / BlueDiamond 资源 basename 的交集；
   - 与 LTB post-mesh short ASCII field 可机械比较的 identifier；
6. 能否形成 **direct config binding evidence**，还是只能形成候选相关性？
7. 如果 config 路线没有目标证据，是否已经形成足够 bounded negative，让下一轮升级到 PE/FXO consumer tracing？

---

# 4. 推荐分析顺序

以下顺序用于控制成本，可在不破坏 scope 的情况下调整。

## 4.1 Format fingerprint

先选择小样本：

```text
若干 bf*.ltc
若干非-bf rez/Butes/*.ltc
rez/bf000.lta
必要时 1-2 个其他 .lta 作为 control
```

记录：

```text
path_alias
size
sha256
first/last bytes
magic / header candidate
ASCII / UTF-8 / UTF-16 readable strings
byte frequency / repeated stride / obvious padding
cross-file common prefix/suffix
```

优先机械证据，不先假定 `.ltc` 是 LithTech text config。

## 4.2 Deterministic decode / parse

如果出现明确结构，再实现可重复 parser/decoder。

允许：

- 基于文件结构、固定 header、长度字段、已知 encoding 的确定性解析；
- 基于多样本差分验证 field boundary；
- 抽取 strings / key-value / identifiers；
- 对已知结构做 round-trip 或 consistency check。

不要为了“解出来”而进行无证据的大范围 XOR/key brute force、随机 curve fitting 或视觉猜测。

## 4.3 Target correlation

只复用现有 N01 / manifest / report 中已经抽取的 basename、identifier、family evidence；**不要重新扫描整个 `data/**`**。

优先比较：

```text
BornBeast
Transformers
Jewelry
BlueDiamond
WeaponShader
known DTX/TGA basenames
known LTB/model basenames
LTB post-mesh short ASCII identifiers
```

所有命中必须保留：

```text
runtime source path alias
source SHA256
offset / record / field context
matched target / basename
match type
confidence / evidence grade
```

只有结构中明确表达引用/映射关系时，才能升级为 binding evidence；裸字符串共现、文件名相似、目录邻近不能算 binding proof。

---

# 5. 建议实现与输出

优先新增：

```text
scripts/material_recovery/n02_butes_config_triage.py
```

建议 evidence 目录：

```text
work/m4a1_s_bornbeast/p4_m01_native_material/runtime_acquisition/n02b_butes_config/
```

至少输出：

```text
format_inventory.json
correlation_report.json
n02b_butes_config_report.md
```

如实现 parser，可增加：

```text
parser_validation.json
```

不要提交 raw CF runtime `.ltc/.lta` 副本；仓库只保存可审计的 metadata、hash、结构描述和必要的小型 derived evidence。

---

# 6. Completion / Handoff

本轮完成后返回以下之一：

## A. 找到直接 config binding evidence

```text
RUNTIME_CONFIG_BINDING_EVIDENCE_READY
```

必须给出：

- source path alias + SHA256；
- 可重复 parse/decode 方法；
- field/record/offset 上下文；
- model/piece/material/texture/shader 之间具体关系；
- 为什么这比 filename/string coincidence 更强；
- 尚未闭合的 CFG/render semantics。

## B. 格式已解析，但没有目标 binding

```text
RUNTIME_CONFIG_FORMAT_DECODED_NO_TARGET_BINDING
```

必须给出：

- 已解析结构；
- 覆盖的 `.ltc/.lta` scope；
- target correlation 的 bounded negative；
- 下一轮最值得检查的 PE / FXO consumer target。

## C. 格式仍未闭合，但已形成 bounded negative

```text
RUNTIME_CONFIG_FORMAT_UNRESOLVED
```

必须给出：

- 已验证排除的 encoding/structure 假设；
- 多样本结构统计；
- 为什么继续在 config 上投入的信息增益已经较低；
- 下一轮应升级到哪个具体 consumer artifact，而不是泛泛写“反编译 EXE”。

完成后 **STOP**。不要自行继续 N02-C。

---

# 7. 本轮禁止事项

- 不执行任何 CF client/runtime binary；
- 不注入进程、不绕 anti-cheat、不做 memory dump；
- 不做宽泛 EXE/DLL decompile/xref；
- 不开始 FXO shader 反编译；
- 不解包大型 REZ 作为本轮主任务；
- 不重新扫描整个 `data/**`；
- 不上传 raw runtime binary/config 副本；
- 不把 `bf` 文件名、字符串共现或目录邻近当 binding proof；
- 不自行宣布 `P4-M01 = NATIVE_MATERIAL_RECOVERED`；
- 不恢复 P5-T02；
- 不修改 `plan.md`。

---

# 8. Executor 交回内容

完成后只需交回：

```text
status
commit SHA
新增/修改的 scoped files
format/parser 结论
runtime config target correlation 结论
direct evidence 或 bounded negative
建议下一轮唯一最高优先级 consumer target
需要领导 Review 的关键判断点
```

然后停止，等待下一轮 `task.md`。