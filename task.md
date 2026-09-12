# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N03-E
Title: Parse canonical RenderStyle LTBs as Jupiter LTB_D3D_RENDERSTYLE_FILE
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N03-D
```

# 2. Previous execution status

N03-D：PV LTB piece 表是 Jupiter 合同，但 `nNumTextures=0`，LTB 不带贴图文件名。

# 3. Current goal

解开 N03-C 已 bind 的两条 RenderStyle LTB：

```text
rez/rf002.rez  RS/NINJATRANSLUCENT.LTB   111 B compressed
rez/rf002.rez  RS/PVMODELDEFAULT.LTB     119 B compressed
```

回答：

```text
Jupiter CD3DRenderStyle::Load_LTBData
  -> decompressed RS body
  -> fileType / version / pass count / TextureParam per stage
  -> any CFG/FX/TGA/DTX string or shader ID
```

# 4. Required Work

只读 `rez/rf002.rez` 这两条（可用 N03-C 的 SHA/offset）。LZMA-alone 解压后按 jsj2008/lithtech：

```text
runtime/render_a/src/sys/d3d/d3d_renderstyle.cpp  Load_LTBData
sdk/inc/ltrenderstyle.h
RENDERSTYLE_D3D_VERSION = 3
LTB_D3D_RENDERSTYLE_FILE = 5
```

至少报告：

1. `LTB_Header` fileType/version（相对 20-byte aligned model header 的 CF delta 也要写明）
2. `iTotalSize` / `iRenStyleCnt` / `iRenderPasses`
3. 每个 pass 每个 texture stage 的 `TextureParam`（NOTEXTURE vs USE_TEXTURE1..4）
4. Vertex/pixel shader 或 EffectShader 标志与 ID（若流里有）
5. 解压体内 exact `.cfg/.fx/.tga/.dtx` 字符串扫描（没有就 scoped negative）

不要把 RS 里的 texture *slot* 说成 TGA 路径。不要冻结 CFG shader 语义。

输出：

```text
work/.../n03e_renderstyle_ltb/
```

至少包含：

```text
RS parse report
header + pass/stage table
string scan
confirmed relations
remaining ambiguity
```

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不把 TextureParam slot 当 DTX/TGA 路径；
- 不冻结 CFG shader semantics；
- 不进入 DLL/EXE/FXO reverse；
- 不扫描全部 RS LTB；
- 不进入 P5 identity；
- 不修改历史 accepted evidence。

# 6. Completion State

```text
A. RENDERSTYLE_STRUCTURAL
   both RS files parse as type-5 renderstyle; stage TextureParam recorded

B. CANDIDATE_ONLY
   header matches but pass/stage layout is a scored CF delta

C. REWORK_REQUIRED
   cannot re-read or decompress the two RS LTBs
```

完成后返回 status / commit SHA / changed files / confirmed relations / remaining blockers / next highest-value target。

完成后 STOP，等待 Planner/Reviewer。
