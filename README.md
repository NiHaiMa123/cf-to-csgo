# CF to CS:GO Modding Toolkit

将 **CrossFire（穿越火线）资源**提取、分析并转换为 **CS:GO Legacy Source 1 / MIGI** 可用 Mod 的工具与研究仓库。

仓库包含 REZ/音频处理、LTB 模型分析、Source 1 构建、MIGI 部署、原生材质逆向和武器资产移植工作。

---

# 1. 文档结构

根目录只保留两份 Markdown：

```text
README.md     项目介绍 + 协作方式 + Git 规则（本文件）
pipeline.md   武器移植 pipeline：通用方法（附录 A）+ 资产图 + 阶段开关 + 当前执行状态
```

2026-09-14 文档清理：`AGENTS.md`（Git 规则并入本文件 §5）、`plan.md`/`task.md`（M4A1 修复期规划，旧状态见 git history）、`CF_NATIVE_PIPELINE.md`（通用方法并入 `pipeline.md` 附录 A）已删除。

归属约定：

```text
入口 / 协作 / Git 规则       -> README.md
移植方法 + 当前武器状态       -> pipeline.md（§4 活状态，§5 复现索引，附录 A 通用方法）
运行细节 / evidence / 报告   -> work/<weapon>/
历史逐轮过程                  -> Git history
```

不要再新增 `P4_TASKS.md` / `REVIEW_FINAL_2.md` 这类一次性文档。

---

# 2. 当前状态

活状态只维护在 `pipeline.md` §4。冻结摘要：

```text
P4 Source 1 / MIGI baseline            PASS / FROZEN
M4A1-雷神（v_rif_m4a1）                 模型+声音已部署并被用户验收；CF 动画改造 REJECTED，旧动画冻结
Galil ACE-天袭（v_rif_galilar）         P0–P8 全部 PASS，2026-09-14 用户游戏内验收
```

---

# 3. 协作流程

```text
用户指定武器替换任务
-> agent 在 pipeline.md 写/更新该武器的资产图与阶段开关
-> 按 pipeline.md §5 逐阶段执行，每阶段产 evidence 到 work/<weapon>/
-> addon 落盘到 migi/csgo/addons/ 后，提醒用户手动执行 MIGI UPDATE
-> 用户游戏内验收（P8 Gate）
-> agent 精确 commit + push master
```

关键约束：

- 每阶段必须产出可审计 evidence（json/report/log），不以口头结论代替。
- Blender 预览默认跳过（仅拟合质量存疑时跑轻量模式）。
- MIGI UPDATE 由用户手动执行，agent 不代操作。
- 一把武器一个 `work/<name>/` 目录，状态写进 `pipeline.md`。
- 未经验证的猜测不写进 pipeline 冻结结论。

---

# 4. 主要目录

```text
CFRezManager/              C# CF resource manager / decoder / inspection
scripts/
  cf_extract/              CF REZ / FMOD extraction
  audio_clean/             audio repair / cleanup
  cf_ltb/                  LTB diagnostics
  weapon_port/             CF weapon -> Source 1 pipeline
  material_recovery/       native material / runtime evidence research
  csgo_pack/               CS:GO / MIGI packaging
  gsi/                     game-state integration
assets/weapons/            auditable weapon manifests / mappings
work/                      tracked reports / evidence / derived outputs
data/                      local CF inputs; never upload
migi_tools/                MIGI toolchain
tools/                     third-party tools
tests/                     smoke / regression tests
```

---

# 5. Git 规则（原 AGENTS.md，2026-09-14 并入）

以下规则对所有 Agent / 自动化工具生效。

## 5.1 权威分支

- `master` 是 Agent 之间唯一正常交接分支。
- 正常工作直接同步、提交、推送到 `master`。
- 不使用 feature/topic branch 或 PR 作为常规 Agent handoff，除非用户明确要求。
- 非 `master` 上未合入的工作视为尚未交付。
- 禁止 force push，除非用户明确授权具体操作。

推荐同步：

```bash
git status --short --branch
git fetch origin
git pull --rebase origin master
```

## 5.2 修改前先同步并检查工作区

执行 Git 写操作前必须先检查：

```bash
git status --short --branch
```

如果存在本地 tracked 修改：

- 不得为了 pull 而直接丢弃；
- 不得自动选择 ours/theirs 覆盖实质冲突；
- 先保留现有工作，再有意识地同步/解决冲突。

如果 `origin/master` 已前进，先 fetch/rebase 或明确处理冲突，禁止覆盖远端历史。

## 5.3 `data/**` 永远 local-only

- `data/**` 不得提交或上传 GitHub。
- 不得使用 `git add -f` 绕过 ignore。
- 不得因为 Git 同步而删除、覆盖、移动、镜像或重建本地 `data/**`。
- GitHub 上没有 `data/**` 不代表本地目录应该被删除。
- 如果发现 `data/**` 被 staged 或 tracked，立即停止提交并报告。

同样，CF 原始客户端/runtime 文件（例如未经授权提交的 `.exe/.dll/.rez/.pak/.pck`）默认不得作为 raw binary 上传；如果某个二进制确实需要纳入版本控制，必须由用户明确授权。

## 5.4 精确 staging

只 stage 本次任务明确需要的路径，例如：

```bash
git add -- scripts/example.py work/example/report.json
```

禁止：

```bash
git add .
git add -A
git add --all
```

提交前至少检查：

```bash
git diff --cached --name-only
git diff --cached
```

确认没有：`data/**`；原始 CF 客户端/runtime binary；secrets / credentials；cache / 临时文件；与当前任务无关的用户修改。

## 5.5 提交与 push

- commit message 应准确描述本次 scoped change。
- 正常 Agent 交接必须 push 到 `master`。
- push 前再次确认 staged diff。
- 如果远端已前进，先同步再 push。
- 不得通过重写历史来"省事"。

## 5.6 默认禁止的破坏性操作

未经用户对具体范围明确授权，禁止：

```bash
git reset --hard
git clean -fd
git clean -fdx
git checkout -- .
git restore .
git push --force
```

也禁止任何可能删除本地输入的镜像/清理操作，例如：`rm -rf data`、`robocopy /MIR`、`rsync --delete`、整仓替换式同步。

如果确实需要清理生成物，只允许针对明确已知的 generated path，并保护 `data/**` 和用户无关文件。

## 5.7 冲突与停止条件

出现以下任一情况，停止自动 Git 操作并保留现场：

- `data/**` 被 staged / tracked；
- pull/rebase 会覆盖未处理的本地 tracked 工作；
- 发生实质 merge/rebase conflict；
- 需要 force push 才能继续；
- 操作可能删除 local-only 输入；
- 工作区混有无法安全分离的用户修改。

Git 操作的首要原则是：**不丢用户本地数据、不覆盖未交付工作、不把无关文件带入提交。**
