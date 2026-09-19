# 屠龙（Kukri_Beast 基版）贴图问题现状记录

## 2026-09-18 独立复核：主要根因已定位，离线验证通过，未部署

**之前“UV 正确，只差 shader”和“刀面横向断层是真实悬浮几何”两条结论错误，撤销。**

现有构建取无后缀 `PV-Kukri_Beast.LTB` 的 `objObject03000`（1128 顶点 / 896 三角形）。这份网格的 UV 与当前 `PV-Kukri_Beast.DTX` 图集不匹配；刀尖采到了握柄红眼，刀面多处采到图集黑底。八种 UV 翻转/交换组合均不能恢复连续龙纹。白色 Emission 几何渲染显示刀面连续，所谓横向“间隙”是错贴黑底，不能当成悬浮设计。

从 CF 的 REZ 重新按 MD5 校验提取：

| 模型候选 | 刀网格 | 顶点 / 三角形 | 同一原始 diffuse 的结果 |
|---|---|---|---|
| 无后缀 `PV-Kukri_Beast.LTB`（当前构建） | `objObject03000` | 1128 / 896 | 错位、红眼出现在刀尖、黑色横带 |
| 基版 `PV-Kukri_Beast_GR.LTB` | `Object066` | 1181 / 1878 | 金色刀尖、连续龙纹、兽头与红眼握柄位置正确 |
| 春桃 `PV-Kukri_Beast_Spring_GR.LTB` | `Object066` | 1626 / 1890 | 用同一基版贴图也可正确映射；本次基版优先取基版 GR |

基版 BL 已提取/解码（`Object066` 1204 / 1890），尚未单独渲染验收。**不把 `_BL/_GR` 当成只换手臂的等价文件**；本轮证明刀身网格/UV 也不同。此处证明的是离线资产兼容性，不是已捕获 CF 运行时选模逻辑。

### 可复现证据

目录：`csref/_diag/mapping_audit/`。

- `before_after.png`：同一相机、同一 diffuse、同一 Emission shader，左旧网格，右基版 GR。没有增亮或替换贴图。
- `solid_geometry.png`：旧网格白色渲染，排除“横向悬浮间隙”。
- `variant_acquisition.json`：四份 `_BL/_GR` 的来源、分片、MD5 与 SHA-256。
- `skin_base_gr.json` / `skin_gr.json`：独立解码结果。
- `audit.json` / `skin_base_gr/audit.json`：渲染输入哈希、顶点数、相机和重绑矩阵。
- `skin_base_gr/diffuse_preview.blend`：正确 UV 的基版 GR 离线场景。
- 脚本 `csref/audit_texture_mapping.py`：独立后台 Blender；每次从 JSON 重建，无实时场景残留；测试结束恢复 `(u, 1-v)`。

复现：`blender --background --factory-startup --python work/tulong_chuntao/csref/audit_texture_mapping.py`；末尾加 `-- work/tulong_chuntao/csref/_diag/mapping_audit/skin_base_gr.json` 测正确候选。

额外审计：无后缀刀身原始 LTB stream 为 rigid type 4，flags `0x13`，32 字节/顶点，Box01=47；原始位置/UV 与 dump 全量最大误差均为 0。布局交叉参考 [io_scene_lithtech reader_ltb_pc.py](https://github.com/haekb/io_scene_lithtech/blob/master/src/reader_ltb_pc.py) 的 rigid reader。没有证据支持为这份模型修改全局 UV 解码器。

### 后续修复边界

1. 保留已验收动画、手臂与 `viewmodel_transform.json`。只替换刀身输入为基版 GR 的 `Object066`。
2. 两模型 bind 不同，不能直接把新网格坐标塞进旧骨架。应先 `v_old_bind = B_old_Box01 @ inverse(B_GR_Box01) @ v_GR`，再走现有 MXH/蒙皮。此次对比已使用该重绑，并固定同一相机；骨空间闭合误差约 `2.5e-15`。
3. `(u, 1-v)` 一次翻转在正确候选上成立，不再排列组合碰运气。
4. 正确原始 diffuse 仍偏暗，这是后续材质层问题。恢复金色反射需另核 `_S`、CF cubemap 和 CFG 的实际语义；此轮未声称已还原截图的亮金光照。
5. 当前 addon / 游戏包 / 生产构建脚本均未改。此次仅保存离线复核脚本、证据和文档更正；无需 MIGI REBUILD。

旧记录另有两处问题：`_blender_tex.py` 最终停在 flipuv，而 `_blender_tex2.py` 不重置 UV，混合测试会继承错误状态；下面的旧 VMT 摘要也已过时，实际 `gun_vmt()` 与 staging VMT 是 boost `.3`、albedoboost `30`、PhongExponentTexture，**不是 48/8**。

## 以下为此前记录（历史；与上述复核冲突处作废）

### 用户反馈

- **位置/朝向：已验收通过**，变换关系已固化（见下方"已定稿变换"）。
- **贴图：仍不对**。游戏内刀面呈暗红/发黑，与 CF 实机的亮金+红龙观感不符。
- 用户确认：`PV-Kukri_Beast.DTX` 解码图（暗金底+红龙+红兽头，512²）是**正确的源贴图**，图本身没错。
- 用户要求：先在 Blender 里排列组合复原贴图显示，**不要直接更新进游戏**；材质素材必须全部用 CF 解包资源，第三方 mod 只能参考参数。

## 已定稿变换（不要再动）

`work/tulong_chuntao/csref/viewmodel_transform.json`：

- view_push = (-4, -11, -6.5)，pivot = 两肩点中点 (-4.506, -16.135, -8.361)
- 累计旋转等效 view 轴 ≈ (-0.67, 0.35, -0.66) 转 20.1°
- arm_offset_l = (6, 4, -4)，arm_offset_r = (-1, 0, -1)（武器子树 Prop1+Box01 跟右手）
- arm_rot_l：绕肩点中点、用户系 x 顺时针 20°（view 空间绕 [0,-1,0] 转 20°）
- flip_knife_v = true（已验证：Source 采样 PNG 行 = 1-v_smd = v_raw）

## 已验证的事实

1. **UV 映射正确**。Blender 中 4 种 UV 组合（asis/flipv/flipu/flipuv）对比，`asis` 面正确显示：红尖+暗红分段刀身+金爪+红龙纹。其它三种采到图集错误区域。两面（±X）UV 共享同一岛，内容一致。
2. **刀面分段间隙是真实几何**（Beast 系列悬浮分段设计），不是贴图 bug。
3. **Diffuse 源图正确**（用户亲自确认），游戏内偏暗不是图错。
4. CF 原版"亮金"来自 `Kukri_Beast.CFG` 的 shader 组合，不是漫反射亮度：
   - DiffuseMapping + **SpecularMap(Kukri_Beast_s)** + **EnvCubeMap(RoyalDragon3.dds, 亮度×3)** + NormalMap + AlphaMap
   - 高光图本身就是亮金+红龙底图，是亮金观感的主要贡献层
5. **第三方 p_Kukri_Beast 对比**（仅参考）：其 basetexture 是 1024×512 DXT5，RGB 为亮金+红龙、alpha 存高光亮度掩码；VMT 用 `env_cubemap + envmaptint[.4 .3 .15] + PhongExponentTexture + rimlight + nocull`。其 RGB 与基版/NobleGold 解包图都不完全一致（疑似自定义重制）。
6. Blender 已渲 dif/spec/mix50/add 四种材质组合对比（`_diag/blender_mix_sheet.png`），差异细微，刀面均为暗红分段+红龙——映射对、观感暗。
7. Lside 首次渲黑是相机矩阵错误，修正后两面均正常。

## 当前 VMT 状态（已写入 addon，未经实测验收）

`cf_kukri_beast.vmt`（全 CF 素材，第三方仅参考参数）：

- `cf_kukri_beast.vtf`：2048 diffuse，alpha 通道=CF 高光图亮度（作 envmap/phong 掩码）
- `cf_kukri_beast_s.vtf`：CF `Kukri_Beast_s.PNG` → `$PhongExponentTexture`
- `cf_kukri_beast_n.vtf`：CF `Kukri_Beast_N.PNG` → `$bumpmap`
- VMT：env_cubemap + envmapfresnel + envmaptint[.4 .3 .15] + phong 48/8 + halflambert + rimlight + nocull

## 未验证 / 候选排查方向（按可能性排序）

1. **新 VMT 未实测**：当前部署的 envmap 版 VMT 还没经游戏验证，"还是不对"可能基于旧印象或缺 MIGI REBUILD。
2. **envmaptint/强度不够**：CF 用 envcube 亮度×3，Source 侧 `[.4 .3 .15]` 可能偏暗 → 可调亮或加 `$envmapmask` 直接指 `cf_kukri_beast_s`。
3. **缺真正的 CF 环境图**：`RoyalDragon3.dds` 尚未提取接入，现在用的是引擎 env_cubemap 采样，色调不同。
4. **AlphaMap 用途未用**：`Kukri_Beast_alpha.PNG`（1024×512 布局）可能是透明/分层掩码，目前没进 VMT。
5. **S 图通道用法**：可能不是亮度掩码而是 RGB 直接叠加（CF shader 语义不同）。

## 关键文件

- 变换：`work/tulong_chuntao/csref/viewmodel_transform.json`
- 构建：`work/tulong_chuntao/native_vm/build_tulong_vm.py`
- 贴图：`work/tulong_chuntao/texture/build_textures_beast.py`
- 素材：`work/tulong_chuntao/decode/PV-Kukri_Beast.png`、`decode/maps/{Kukri_Beast_s,Kukri_Beast_N,Kukri_Beast_alpha}.png`
- Blender 脚本：`csref/_blender_tex.py`、`_blender_tex2.py`、`_blender_send.py`
- 渲染对比：`csref/_diag/blender_mix_sheet.png`、`blender_tex_sheet*.png`、`lside_check.png`
