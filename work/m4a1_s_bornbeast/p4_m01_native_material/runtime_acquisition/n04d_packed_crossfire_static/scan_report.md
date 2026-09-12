# P4-M01-N04-D — packed `x64/crossfire.exe` extra static

- status: **STRING_ISLAND_ONLY**
- completion: **B**
- P4-M01: still **INCOMPLETE**

用户授权更深静态。未跑脱壳器、未附加进程、未提交 PE。SHA 对上 N04-A。

## 1. 壳形态

- 8 个节全部名叫 `.std`。入口 RVA `0x7C1E3B` 落在高熵可执行节（entropy 7.999）。
- **唯一导入**：`crossfireBase.dll`（40 MB，N04-A 已见 `.tvm0`）。
- overlay 10880 B。不像 UPX；像自定义壳，把真逻辑放进 `crossfirebase.dll`。

## 2. WeaponShader 明文岛（仍无代码引用）

`MODELTEXTURES\Shader\WeaponShader\` 仍在 file offset 5896672。

- RIP-LEA：**0**
- 64-bit VA 指针：**0**
- 32-bit RVA 立即数：**0**
- XOR 1–255：没有 `WeaponShader` / `AlphaMap` 真命中（两条 `.cfg` XOR 是噪声）

同岛紧挨的 C 字符串：

```text
MODELTEXTURES\Shader\WeaponShader\
MODELTEXTURES\Shader\CharacterShader\
.cfg
temp
_Indoor
```

这是 **目录前缀 + 扩展名碎片**，不是 `WeaponShader\%s.CFG` 一条格式串。没有指针表把碎片接起来。

## 3. 其它低熵明文

LithTech 痕迹：`model-rez: client uncachemodel`、`Failed to set texture (%s)`、`advanced_shader`。  
`.cfg` 另有 `autoexec.cfg` / `display.cfg`（引擎配置，不是 WeaponShader）。

全文件仅 1466 个 RIP-LEA 目标（CShell 是百万级）：可反汇编的代码岛极小。

## 4. 结论

静态再挖 `crossfire.exe` **不能**给出 CFG 加载函数。明文岛证明客户端知道 `MODELTEXTURES\Shader\WeaponShader\` 和 `.cfg`，消费代码应在 **packed `crossfirebase.dll`（`.tvm0`）** 或运行时解密之后。

本轮 **不** 脱 `.tvm0`（任务禁止）。下一步若要 CFG consumer，需要另授权：静态对抗 `.tvm0`，或接受运行时 dump（ACE 风险）。

**status**: `STRING_ISLAND_ONLY`
