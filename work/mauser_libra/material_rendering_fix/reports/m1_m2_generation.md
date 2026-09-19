# M1 / M2 实验包生成记录

日期：2026-09-19  
状态：generation_validation **PASS**；runtime_status **PENDING**；visual_status **NOT_EVALUATED**

对照用户提供的 CS 当前截图与 CF 目标图：枪身整体偏暗橄榄／棕金，黑色主体缺少金属亮边。本批只生成隔离实验包，不覆盖当前 addon，不通知 REBUILD。

## 基线

父基线（只读）：`work/mauser_libra/material_rendering_fix/baseline/20260919T094033.420908Z_ef5ce185/addon_v2`

独立核验：当前 `addon_v2` 与冻结基线 29/29 SHA-256 一致。模型、手膜、声音、全部 VTF 未改。

生成器：`work/mauser_libra/material_rendering_fix/build_experiments.py`  
产物：`work/mauser_libra/material_rendering_fix/experiments/20260919T095005.350493Z`

两项实验均直接从同一冻结基线复制，互不叠加。

## M1_r5_phong

| 项 | 内容 |
|---|---|
| 假设 | r5（1516 三角，`matte_dark`，`$phong 0`）被错误当成无高光表面 |
| 唯一改变 | 仅 `cf_mauser_libra_r5.vmt` |
| 参数 | `$phong` 0→1；补齐 r0 的 `$basemapalphaphongmask` / exponent 4 / boost 1.57 / fresnel `[1 1 1]` / tint `[1 0.765 0.529]` |
| 未改 | 28 个文件，含 r1/r4 envmap、全部 VTF、模型、手膜 |
| r5 sha256 | `6f58785a…` → `58c40b9c…` |
| 预期 | 黑色主体上的金纹／亮边随受光或视角出现，暗底仍暗 |
| 回滚 | 重新同步冻结基线 addon，不要在 M1 上叠加 M2 |

独立核对：M1 的 r1/r4 与基线字节相同。

## M2_env_off

| 项 | 内容 |
|---|---|
| 假设 | 现有 r1/r4 `$envmap env_cubemap` 可能没有可见反射贡献 |
| 唯一改变 | 仅 `cf_mauser_libra_r1.vmt`、`cf_mauser_libra_r4.vmt` |
| 参数 | 删除 `$envmap` / `$normalmapalphaenvmapmask` / `$envmaptint`；Phong 与 boost 2.51 保留 |
| 未改 | 27 个文件，含 r5 `$phong 0`、全部 VTF、模型、手膜 |
| 预期 | 同场景差图显示 envmap 原先贡献的亮度／颜色／视角变化；无变化不能证明不需要反射 |
| 回滚 | 回到冻结基线。本实验不是改善画面的候选 |

独立核对：M2 的 r5 与基线字节相同。

## 未做

- 未写入 `work/mauser_libra/addon_v2`
- 未写入 MIGI addon `p_cf_mauser_libra_p1`
- 未改通用翻译器、VTF、UV、模型、FOV、位置、动画、手套
- 未采集明处正向／明处转向／暗处运行时基线截图
- 不把 generation_validation 当作视觉 PASS

## 下一步（需用户）

1. 用当前已部署版本进入测试图，保持现有 FOV／持枪，拍明处正向、明处转向、暗处三张基线。
2. 主代理审核通过后，只把 **M1** 同步到 A/B，哈希 29/29 后再请用户 MIGI REBUILD。
3. M1 采集完成并判断生效后，从原基线同步 **M2**（不要叠在 M1 上），再 REBUILD 采集。
