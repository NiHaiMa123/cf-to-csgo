# M1 部署记录

日期：2026-09-19  
A/B：**29/29 SHA-256 一致**  
pak C：`PACK_VERIFY_PENDING`（等用户 MIGI REBUILD）  
视觉：**NOT_EVALUATED**

## 运行时基线画面

用户提供三张当前版本截图，已归档到 `runtime/baseline_scenes/`。

| 用户标签 | 文件 | 场景 |
|---|---|---|
| 明处正向 | `lit_front.jpg` 9:54 | Mirage 中门朝木门，枪在阳光下 |
| 明处转向 | `lit_turn.jpg` 9:03 | 转向庭院拱门／木箱，仍是阳光 |
| 暗处 | `dark.jpg` 8:48 | B 宫 palais 巷，靠墙阴影；**是室外阴影，不是室内** |

三张里枪身仍是暗橄榄／棕金，黑色主体缺少亮边。FOV／位置未改。截图时 r5 仍是基线 `$phong 0`。

## 已同步到 A/B

只复制 M1 允许的一个文件：

`materials/models/weapons/v_models/cf_mauser/cf_mauser_libra_r5.vmt`

`$phong` 0→1，并接上 r0 的受遮罩 Phong。r1/r4 envmap、VTF、模型、手膜、声音未动。冻结基线目录未写。

回滚：把冻结基线的 r5.vmt 拷回 A/B 后再 REBUILD。

## 观察要点（REBUILD 后同三处再拍）

- 黑色主体上的金纹／亮边是否出现，并随转向变化
- 暗底是否仍保持暗色
- 若整块变灰、刺眼或噪纹：拒绝该 r0 预设，不继续加 boost
- 若完全没变化：先核 pak C 是否吃到新 r5，再查遮罩／shader
