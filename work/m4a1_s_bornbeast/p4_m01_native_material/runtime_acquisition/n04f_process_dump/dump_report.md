# P4-M01-N04-F — running `crossfire.exe` module dump

- status: **DUMP_ACCESS_DENIED**
- completion: **C**
- P4-M01: still **INCOMPLETE**

CF 已在跑。未注入、未提权、未打开 ACE 模块、未提交映像。

## 1. Process

```text
PID           33100
image         D:\Program Files\CF(2)\x64\crossfire.exe
WorkingSet    ~5.5 GiB
children      WebViewProcess_x64.exe x5, FeedBack.exe
```

`QueryFullProcessImageNameW` 在 `PROCESS_QUERY_LIMITED_INFORMATION` 下成功。这就是 N04-D 分析过的 packed stub。

## 2. Access

| API | result |
|---|---|
| `OpenProcess(PROCESS_VM_READ)` | handle=0, last_error=**5** (ACCESS_DENIED) |
| `OpenProcess(PROCESS_QUERY_INFORMATION)` | last_error=**5** |
| `CreateToolhelp32Snapshot(SNAPMODULE)` | INVALID, last_error=**5** |
| `OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION)` | 成功，只能问路径 |

没有模块列表，没有 `ReadProcessMemory`，没有 dump 文件。

这是 ACE/进程保护拒绝 VM 读，不是脚本路径写错。本轮不调用 `NtReadVirtualMemory`、不调 SeDebug、不打补丁。

## 3. Remaining

磁盘静态 + 被拒绝的进程读，都拿不到解密后的 `crossfirebase.dll` 映像。CFG 加载函数仍在 VM 后面。

**status**: `DUMP_ACCESS_DENIED`
