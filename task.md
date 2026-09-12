# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N03-D
Title: Jupiter-vs-CF piece/texture-index differential on canonical PV LTB
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N03-C
```

# 2. Previous execution status

N03-C 已把 Bute FileName 图扩完。

```text
BUTE_MATERIAL_GRAPH_EXPANDED
```

TGA/CFG **不是** Weapon 文件路径字段。下一步是 LTB 内部 piece 槽，而不是再扫 Bute。

# 3. Current goal

对 **N03-C SHA 已验证** 的

```text
rez/RF016.REZ / PLAYERVIEW/PV-M4A1_S_BornBeast.LTB
```

做 Jupiter 标准 LTB piece/texture-index 合同 vs 本机 CF artifact 的差分。

回答：

```text
Jupiter ModelPiece::Load contract
  -> CF decompressed LTB
  -> per-piece name / nLODs / m_nNumTextures / m_iTextures[4] / m_iRenderStyle
  -> whether those indices are STRUCTURALLY_VERIFIED on this file
```

# 4. Required Work

只读已 bind 的 archive：`rez/RF016.REZ`（canonical PV LTB）。可选差分：`rez2/RF016.REZ` 的 QV LTB（N03-C 与 local data SHA 一致的那份）。不要扫全部 475 REZ。

1. bounded read + LZMA-alone 解压（与 N02-E-R1 相同）。
2. 按 jsj2008/lithtech `model_load.cpp` / `ltb.h` / `modelallocations.cpp` 的 **REFERENCE_IMPLEMENTATION** 走：
   - `LTB_Header`（D3D model file type 1, version 9）
   - `m_FileVersion`
   - 15 个 uint32 allocations（含 `m_nPieces`）
   - command string / visRadius / num_obb / nPieces
   - 每个 piece：name, nLODs, LOD dists, 然后 per-LOD：`m_nNumTextures`, `m_iTextures[MAX_PIECE_TEXTURES=4]`, `m_iRenderStyle`, `m_nRenderPriority`, `render_object_type`
3. 若 CF 在 piece-LOD 头之后与 Jupiter 不对齐，记录 **CF delta**（哪个字段、offset、候选 layout），用可评分的少量 layout 尝试；不要从零发明整套格式。
4. 不得把 `m_iTextures[i]` 升级成 DTX/TGA 路径；没有同文件 name table 就停在 index。
5. 对比 repo `LithTechModelDecoder` 的 Cote-Duke LTB2X 偏移，只作为 secondary candidate，不是 Jupiter 合同。

输出：

```text
work/.../n03d_ltb_piece_index/
```

至少包含：

```text
header/allocation dump
piece table (name, lods, texture indices, render style)
Jupiter vs CF delta
confidence / remaining ambiguity
```

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不把 texture index 当 DTX/TGA 路径 proof；
- 不使用 filename similarity 作为 proof；
- 不进入 DLL/EXE/FXO reverse；
- 不扫描全部 LTB / 全部 REZ；
- 不冻结 CFG shader semantics；
- 不进入 P5 雷神 identity；
- 不修改历史 accepted evidence。

# 6. Completion State

```text
A. PIECE_TEXTURE_INDEX_STRUCTURAL
   Jupiter contract maps onto this CF LTB; per-piece indices recorded
   (still not path identity)

B. CANDIDATE_ONLY
   header/nPieces/names match but LOD/texture layout is a scored CF delta

C. REWORK_REQUIRED
   cannot re-read or decompress the canonical PV LTB
```

完成后返回：

```text
status
commit SHA
changed files
confirmed relations
remaining blockers
next highest-value target
```

完成后 STOP，等待 Planner/Reviewer。
