# task.md — 当前执行任务

> 本文件只描述当前一轮可独立 Review 的执行任务。
> Executor 完成后提交 evidence 并停止。
> 长期 pipeline 与冻结事实见 plan.md。

# 1. Current Task

```text
Task ID: P4-M01-N03-H
Title: Decode remaining BornBeast DTX vs later-era SpecularMap DTX controls
State: ACTIVE
Parent: P4-M01 Native Material Recovery
Depends on: P4-M01-N03-G
```

# 2. Previous execution status

N03-G：`LightCorrectionLegacyShader` 全是整数 `1`，不是 CFG 名。`SpecularMapName` 是后期武器的 `SpecularMap\*.dtx`。黑骑士两条都没有。Bute 字段路线到此关闭。

ComfyUI/CS1.6 只证明网格 UV 需要 512×512 枪件 atlas；本机 PV DTX 解出来是能量层。QV DTX 官方 `--decode-image` 失败，尚未按体积做 DXT 布局。

# 3. Current goal

回答：本机还有没有一张 **看起来像枪** 的原生 DTX。

```text
later SpecularMap *.dtx
  -> CFRezManager official DTX header decode works? pixels look like a real map?
QV-M4A1_S_BornBeast.DTX (32932 B)
  -> official fail; size-fit DXT/BGR layouts; gun albedo or energy or garbage?
*BornBeast*.DTX size classes
  -> 524452 energy family / 32932 QV family / other 512-class albedo?
```

# 4. Required Work

只读本地 `data/rf017` DTX（加 N03-G 已列出的 `SpecularMapName` 路径）。

1. 列出全部 `*BornBeast*.DTX` 的 path / size / SHA / 体积族。
2. 对 N03-G 里 unique `SpecularMapName` 的 `.dtx`（至少 `PV-M4A1_RoyalDragon_s.DTX` 和一张非 M4 对照）跑 CFRezManager `--decode-image`。
3. 对 `QV-M4A1_S_BornBeast.DTX` 和官方解码失败的 BornBeast DTX：只试 **体积 exact-fit 或 leftover ≤ 200 B** 的 DXT1/DXT5/BGR 布局（含小 header offset），导出 PNG。
4. 输出预览 + 分类：`gun_atlas` / `scalar_or_energy` / `garbage` / `official_ok` / `undecodable`。分类必须看像素，禁止 filename similarity。

输出：

```text
work/.../n03h_dtx_container_decode/
```

至少包含 size 表、official decode 结果、QV 布局候选、previews、remaining ambiguity。

# 5. Forbidden

- 不宣布 P4-M01 PASS；
- 不把 CS1.6 / ComfyUI / 图鉴像素当 native；
- 不进入 DLL/EXE/FXO reverse；
- 不扫描全部 CFG；
- 不进入 P5 identity；
- 不修改历史 accepted evidence；
- 不把「解得出来」当成「第一人称消费合同」。

# 6. Completion State

```text
A. NATIVE_GUN_ALBEDO_FOUND
   QV or another BornBeast DTX pixels are a recognizable gun atlas
   (local_cf only; not CS1.6)

B. CONTROL_OK_BORNBEAST_SPECIAL
   later SpecularMap/control DTX official-decode as real maps;
   BornBeast QV/PV remain energy/special or non-standard container

C. SCOPED_NEGATIVE
   official+size-fit both fail to produce a gun atlas from BornBeast DTX;
   controls also fail or are absent locally

D. REWORK_REQUIRED
   cannot read local DTX / decoder cannot run
```

完成后 STOP。
