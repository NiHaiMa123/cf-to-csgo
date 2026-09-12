# P4-M01-N04-E — crossfirebase.dll static + in-memory dump

- status: **STATIC_ONLY_NO_PROCESS**
- completion: **B**
- P4-M01: still **INCOMPLETE**

用户授权 `.tvm0` 静态和进程 dump。**未启动 CF。** 本机没有 `crossfire*` / `CShell*` 进程，因此没有 `ReadProcessMemory`。未打开 ACE 模块。

## 1. 磁盘静态

| file | size | 壳 | 导入 | WeaponShader/CFG token |
|---|---|---|---|---|
| `x64/crossfirebase.dll` | 39.8 MB | `.tvm0` 32.0 MB, entropy 7.56 | 仅 `kernel32.dll` | **0** |
| `x64/crossfire_x64base.dll` | 35.9 MB | `.tp6d` + `.tvm0` 24.6 MB | 仅 `kernel32.dll` | **0** |

`.rdata` 里有上万 ASCII 串，但没有 `WeaponShader` / `AlphaMap` / `%s.CFG`。明文消费链不在未解密的 base DLL 里。

这和 N04-D 对得上：`crossfire.exe` 是 stub，真逻辑在 Themida/WinLicense 风格 VM 节，磁盘上扫不到 CFG 路径构造。

## 2. Dump

```text
PROCESS_NOT_RUNNING
```

Dump 目录未创建。若你随后自己进游戏，再说一声可以只 dump 已加载的 `crossfirebase.dll` / `CShell_x64.dll`（仍不碰 ACE）。ACE 可能直接拒绝 `OpenProcess`。

## 3. Remaining

静态 PE 明文路线到此封顶。CFG 加载函数只可能在：

- 运行时解密后的 `crossfirebase.dll` 映像
- 或 CShell 里尚未用格式串表达的间接拼接（N04-A 已证明 CShell 没有 `WeaponShader` 明文）

**status**: `STATIC_ONLY_NO_PROCESS`
