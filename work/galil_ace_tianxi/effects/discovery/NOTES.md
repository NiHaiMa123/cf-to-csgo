# effects/discovery — 取证产物说明（2026-09-15）

## 已生成

| 文件 | 内容 | 生成脚本 |
|---|---|---|
| `clientfx_probe.json` | 首轮局部试读（selected_properties） | 手工探针（未留存脚本） |
| `clientfx_group_pv_galilace_phantombeast_idle.json` | **按组全量导出**：29 节点全属性、逐节点偏移、边界校验、组字节 sha256 | `export_clientfx_group.py` |
| `asset_graph.json` | 99 个引用资源全部 MD5 校验提取（直接引用 + SPR 帧闭包） | `extract_fx_assets.py` + `extract_spr_frames_and_textures.py` |
| `sockets.json` | `_BL` LTB 的 39 个 socket：node_index/name + rot quat + pos + scale | `parse_sockets.py` |
| `texture_channels.json` | 76 个 DTX 解码 + RGBA 通道统计 | `extract_spr_frames_and_textures.py` |
| `ltb_layers.json` + `ltb_layers/*.skin.json` | 12 个 FX LTB 网格/骨架/bbox（CFRezManager `--dump-ltb-skin`） | `dump_ltb_layers.py` |
| `previews/*.png` | 76 张贴图预览 | 同上 |
| `reference_timeline.json` + `reference/frames/` | 用户提供 B 站评测录像（24.8s 4K60）的 idle/移动外观取证：蓝色呼吸光、流光带、眼位光团 | `build_reference_timeline.py` |
| `assets/**` | 提取的原始资源（LTB/SPR/DTX/RenderStyle） | 同上 |

## 关键结论

- **FXF bin30 布局验证通过**：`u32 groups=14047` → 组 `u32 fx_count + char[128] name + u32 phase` → 节点定长头 + 变长属性表（u8 namelen + u32 type + 值）。本组 29 节点后与下一组 `pv_n_ghostbeam...` 无缝衔接。上游 clientfx_tool 全目录兼容性仍未单测。
- **曲线属性**：`Ck`（CLRKEY: f32 t + u8 RGBA）与 `Sk`（VECTOR4: [t, scale, 0, 0]）按出现顺序重复，是颜色/缩放关键帧，**禁止按名去重**。
- **fix_effect_* 的真实位置**：不在 PV 主 LTB（`nSockets=0`、无字符串），而在 `PV-GalilACE_PhantomBeast_BL.LTB`/`_GR.LTB` 的 socket 表（`nSockets=39`，布局见上游 `Model::LoadSockets`：anims 之后 `u32 n` + per-socket `u32 node + u16len name + quat + pos + scale`）。`_BL`/`_GR` 为无动画静态变体（nParentAnims=0）。
- **全组 15 个引用 socket 名全部命中**；大多数挂 `Box001`（枪根），`fix_effect_7` 挂 `Dummy008`，`fix_effect_1/6/14/18/25/26/27/30/32/33` 挂 `Scene Root`（多为环绕/地面位）。
- **SPR 格式**：20B 头（u32 nFrames, u32 unk, 12B 0）+ 每帧 `u16 len + DTX 路径`。AURA_54/55 各 24 帧（256×128 流光带），GLITCH_LINE_03 15 帧，其余单帧。
- **RenderStyle .LTB**（`FX/RS/ADDITIVE.LTB`、`RS/ADDITIVE.LTB`、`RS/FURFINS.LTB`）是 645B 二进制渲染状态块，不是几何模型；Source 侧按 additive/translucent 语义近似。
- **几何层规模**：PARTS_BLUE 68v/34t、PARTS_CORE 52v/64t（挂 Dummy008）、PARTS_RED 16v/8t、TRIANGLE_L/R 各 4v/2t、PLANE_01 双 25v/32t、PLANE_02_4/5 各 8v/6t、GLITCH 双 25v/32t、SIDE_ELEC 25v/32t。均为静态 mesh（skinned=0），骨架仅 Scene Root + 1 Dummy。
- **`UpdatePos` 全部 = 6 = PV_SocketAttach**；`Facing` 多为 2（ParentAlign），Flare 为 0（CameraFacing）。
- **组 Phase=2000、节点 start/end 0–2** 的时间单位语义仍未定（疑似秒+循环；需运行时/参考画面确认）。

## 待办（E2 起）

- `reference_timeline.json` 已录普通形态 idle/移动参考；开火/换弹/检视瞬时特效仍需动作录像（或直接按 FXF 63 组定义重建）。
- 单位语义：Phase/起止时间/EmissionInterval 的单位确认（录像支持 ~2s 呼吸循环推断）。
- RenderStyle 二进制块的逐字段解释（目前只按 additive 近似）。
- socket pos → Source 坐标：需经现有 H 变换 + 绕枪身中心镜像链路（`pipeline.md` §3 硬规则），尚未套用。
