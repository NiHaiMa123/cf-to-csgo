# CF to CS:GO Modding Toolkit

将 **CrossFire（穿越火线）资源**提取、分析并转换为 **CS:GO Legacy Source 1 / MIGI** 可用 Mod 的工具与研究仓库。

仓库同时包含 REZ/音频处理、LTB 模型分析、Source 1 构建、MIGI 部署、原生材质逆向和最终武器资产定位工作。

## 从哪里开始读

根目录只保留 3 个 Markdown，避免多个 Task/Review 文档互相覆盖：

```text
README.md   你正在看的项目入口与工具概览
AGENTS.md   所有 Agent 必须遵守的 Git / data / evidence 安全规则
plan.md     唯一权威的项目状态、完整流程、当前 blocker 与后续执行协议
```

**人阅读：** `README.md -> plan.md`  
**Agent 执行：** `AGENTS.md -> plan.md`

不要根据旧聊天记录猜当前任务；状态只看最新 `master` 的 `plan.md`。

## 当前进度，一句话说明

**CF 枪模 -> Source 1 编译 -> MIGI 部署这条技术链已经跑通并冻结；现在卡在“如何证明 CF 原游戏真实地把 weapon piece、贴图族和 WeaponShader CFG 绑定/消费起来”。**

当前静态资源已经分析到现有证据边界，但仓库/本地已解包 corpus 中没有原 CF client/runtime consumer code。因此当前不是继续换模型重复扫描，而是等待新的 CF runtime/client artifact 或同等级 binding contract，再做静态逆向。

详细状态、已证明/未证明内容、恢复条件全部见 [`plan.md`](plan.md)。

## 主流程

```text
CF 原始资源
  -> REZ / 音频 / LTB / DTX / TGA / CFG 提取与解析
  -> 武器模型 / UV / 骨骼 / 动作关系
  -> CS:GO Source 1 SMD / QC / VMT / VTF
  -> studiomdl / validation / package
  -> MIGI deploy / runtime Gate
  -> CF 原生材质恢复
  -> 最终雷神资产确认
  -> 发布质量
  -> Inspect / IK / CF 原动画等增强
```

目前：

```text
Source 1 conversion baseline       PASS / FROZEN
BornBeast native material          INCOMPLETE
engine-side material consumer      BLOCKED_BY_MISSING_RUNTIME_ARTIFACTS
Leishen candidate flow             PAUSED waiting for material method
```

## 主要目录

```text
CFRezManager/              C# CF 资源管理器、LTB/DTX/TGA/CFG 等 decoder/inspection
scripts/
  cf_extract/              CF REZ / FMOD 等提取
  audio_clean/             音频修复、清洗、分类
  cf_ltb/                  LTB 诊断与模型研究辅助
  weapon_port/             CF weapon -> Source 1 构建流水线
  material_recovery/       BornBeast / N01 原生材质研究脚本
  csgo_pack/               CS:GO / MIGI 打包相关
  gsi/                     游戏状态联动
assets/weapons/            可审计的武器 manifest / mapping
work/                      受版本控制的运行报告、evidence、派生结果
data/                      本地 CF 原始/解包数据；永不上传 GitHub
migi_tools/                MIGI 工具链
 tools/                     第三方工具
 tests/                     冒烟 / 回归测试
```

## 常用入口

项目级冒烟检查：

```powershell
python tests/run_smoke.py
```

构建 CFRezManager：

```powershell
dotnet build .\CFRezManager\CFRezManager.csproj --no-restore
```

武器 Source 1 流水线入口：

```text
scripts/weapon_port/pipeline.py
```

原生材质研究入口：

```text
scripts/material_recovery/
```

具体要不要执行、执行哪一段、哪些结果已经冻结，**先看 `plan.md`，不要直接从脚本名推断当前任务。**

## 数据与证据规则

`data/**` 是本地输入，永远不得上传。提交的 evidence 应使用相对路径、SHA-256、size、run id、git commit 等描述输入身份，而不是提交 CF 原始资产。

外部 MOD 贴图、官网图片、网络图片和 AI 生成图片只能作为参考，不能进入最终 CF 原生材质像素。完整安全规则见 [`AGENTS.md`](AGENTS.md)。

## 文档策略

过去根目录存在大量 `P4_*`、`P5_*`、`*_TASK_SPEC.md`、`*_CONTINUATION.md` 和 Review 文档。它们的有效结论已经合并到 `plan.md`，旧文件从当前树删除；需要追溯某一次历史协议或 Review 时使用 Git history 和对应 evidence commit。

`work/**` 下的 Markdown/JSON 报告属于运行 evidence，不按“根目录流程文档”清理。