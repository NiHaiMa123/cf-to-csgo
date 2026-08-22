# AGENTS.md — Git 操作规范

本文件只规定本仓库的 **Git 同步、提交、分支和本地文件保护规则**。项目规划看 `plan.md`，当前执行任务看 `task.md`，角色分工看 `README.md`。

以下规则对所有 Agent / 自动化工具生效。

## 1. 权威分支

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

## 2. 修改前先同步并检查工作区

执行 Git 写操作前必须先检查：

```bash
git status --short --branch
```

如果存在本地 tracked 修改：

- 不得为了 pull 而直接丢弃；
- 不得自动选择 ours/theirs 覆盖实质冲突；
- 先保留现有工作，再有意识地同步/解决冲突。

如果 `origin/master` 已前进，先 fetch/rebase 或明确处理冲突，禁止覆盖远端历史。

## 3. `data/**` 永远 local-only

- `data/**` 不得提交或上传 GitHub。
- 不得使用 `git add -f` 绕过 ignore。
- 不得因为 Git 同步而删除、覆盖、移动、镜像或重建本地 `data/**`。
- GitHub 上没有 `data/**` 不代表本地目录应该被删除。
- 如果发现 `data/**` 被 staged 或 tracked，立即停止提交并报告。

同样，CF 原始客户端/runtime 文件（例如未经授权提交的 `.exe/.dll/.rez/.pak/.pck`）默认不得作为 raw binary 上传；如果某个二进制确实需要纳入版本控制，必须由用户明确授权。

## 4. 精确 staging

只 stage 本次任务明确需要的路径，例如：

```bash
git add -- scripts/example.py work/example/report.json task.md
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

确认没有：

- `data/**`；
- 原始 CF 客户端/runtime binary；
- secrets / credentials；
- cache / 临时文件；
- 与当前任务无关的用户修改。

## 5. 提交与 push

- commit message 应准确描述本次 scoped change。
- 正常 Agent 交接必须 push 到 `master`。
- push 前再次确认 staged diff。
- 如果远端已前进，先同步再 push。
- 不得通过重写历史来“省事”。

## 6. 默认禁止的破坏性操作

未经用户对具体范围明确授权，禁止：

```bash
git reset --hard
git clean -fd
git clean -fdx
git checkout -- .
git restore .
git push --force
```

也禁止任何可能删除本地输入的镜像/清理操作，例如：

```text
rm -rf data
robocopy /MIR
rsync --delete
整仓替换式同步
```

如果确实需要清理生成物，只允许针对明确已知的 generated path，并保护 `data/**` 和用户无关文件。

## 7. 冲突与停止条件

出现以下任一情况，停止自动 Git 操作并保留现场：

- `data/**` 被 staged / tracked；
- pull/rebase 会覆盖未处理的本地 tracked 工作；
- 发生实质 merge/rebase conflict；
- 需要 force push 才能继续；
- 操作可能删除 local-only 输入；
- 工作区混有无法安全分离的用户修改。

Git 操作的首要原则是：**不丢用户本地数据、不覆盖未交付工作、不把无关文件带入提交。**
