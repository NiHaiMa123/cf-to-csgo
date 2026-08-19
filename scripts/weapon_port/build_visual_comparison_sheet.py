# -*- coding: utf-8 -*-
"""Generate a single visual comparison sheet showing all hero M4 models and UI icons."""

from __future__ import annotations

from pathlib import Path
import pygame

PROJECT_ROOT = Path(__file__).resolve().parents[2]
WORK_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast"
ARTIFACT_DIR = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\e38afcad-92d4-47f8-80dc-cbb40a0b7bda")


def main() -> int:
    pygame.init()
    pygame.font.init()

    width, height = 1280, 960
    sheet = pygame.Surface((width, height))
    sheet.fill((18, 20, 26))

    title_font = pygame.font.SysFont("SimHei", 28, bold=True)
    sub_font = pygame.font.SysFont("SimHei", 18)
    label_font = pygame.font.SysFont("SimHei", 16)

    # Header
    title = title_font.render("穿越火线 (CF) 英雄级 M4A1 全枪型 3D 几何与官方 UI 对照表", True, (240, 240, 240))
    sheet.blit(title, (30, 25))

    sub = sub_font.render("雷神 (BornBeast) vs 黑骑士/死神 (Predator) vs 黑龙 (IronBeast) vs 千变 (Transformers) vs 武圣 (PrismBeast)", True, (160, 175, 200))
    sheet.blit(sub, (30, 65))

    # Grid columns
    cards = [
        {
            "cn_name": "M4A1-雷神 (BornBeast)",
            "icon": ARTIFACT_DIR / "BUYWEAPON_INFO_M4A1_S_BornBeast.png",
            "render": ARTIFACT_DIR / "PV-M4A1_S_BornBeast_render.png",
            "feature": "银黑机匣 / 蓝光龙眼 / 呼吸能量管 / 银色枪管",
            "color": (80, 180, 255)
        },
        {
            "cn_name": "M4A1-黑骑士 (Predator)",
            "icon": ARTIFACT_DIR / "BUYWEAPON_INFO_M4A1_Silnecer_Predator.png",
            "render": ARTIFACT_DIR / "PV-M4A1_Silencer_Predator_render.png",
            "feature": "铠甲骑士外壳 / 红色散热槽 / 猩红枪口 / 黑红配色",
            "color": (255, 70, 70)
        },
        {
            "cn_name": "M4A1-黑龙 (IronBeast)",
            "icon": ARTIFACT_DIR / "BUYWEAPON_INFO_M4A1-S-Iron Beast.png",
            "render": ARTIFACT_DIR / "PV-M4A1_S_IronBeast-NobleGold_render.png",
            "feature": "暗黑龙鳞纹理 / 猩红龙眼 / 生物骨骼枪身",
            "color": (220, 120, 50)
        },
        {
            "cn_name": "M4A1-千变 (Transformers)",
            "icon": ARTIFACT_DIR / "BUYWEAPON_INFO_M4A1_S_Transformers.png",
            "render": ARTIFACT_DIR / "PV-M4A1_S_Transformers_render.png",
            "feature": "多边形高科技模块 / 自定义多色装甲",
            "color": (180, 100, 255)
        },
        {
            "cn_name": "M4A1-武圣 (PrismBeast)",
            "icon": ARTIFACT_DIR / "BUYWEAPON_INFO_M4A1_Silencer_PrismBeast.png",
            "render": ARTIFACT_DIR / "PV-M4A1_Silencer_PrismBeast_render.png",
            "feature": "青绿鎏金龙纹 / 关羽主题 / 下挂副武器",
            "color": (60, 220, 140)
        }
    ]

    card_w = 230
    gap_x = 20
    start_x = 20
    start_y = 110

    for i, c in enumerate(cards):
        x = start_x + i * (card_w + gap_x)
        y = start_y

        # Draw card background
        card_rect = pygame.Rect(x, y, card_w, 800)
        pygame.draw.rect(sheet, (26, 30, 40), card_rect, border_radius=8)
        pygame.draw.rect(sheet, c["color"], card_rect, width=2, border_radius=8)

        # Title
        t_surf = label_font.render(c["cn_name"], True, c["color"])
        sheet.blit(t_surf, (x + 10, y + 15))

        # UI Icon
        if c["icon"].exists():
            icon_s = pygame.image.load(str(c["icon"]))
            icon_s = pygame.transform.smoothscale(icon_s, (card_w - 20, 130))
            sheet.blit(icon_s, (x + 10, y + 45))

        # 3D Model Render
        if c["render"].exists():
            render_s = pygame.image.load(str(c["render"]))
            render_s = pygame.transform.smoothscale(render_s, (card_w - 20, 260))
            sheet.blit(render_s, (x + 10, y + 190))

        # Feature text
        words = c["feature"].split(" / ")
        fy = y + 470
        for w in words:
            w_surf = sub_font.render(f"• {w}", True, (210, 220, 230))
            sheet.blit(w_surf, (x + 10, fy))
            fy += 26

    out_sheet = WORK_DIR / "m4_hero_visual_sheet.png"
    pygame.image.save(sheet, str(out_sheet))
    pygame.image.save(sheet, str(ARTIFACT_DIR / "m4_hero_visual_sheet.png"))
    print(f"[PASS] Visual sheet created -> {out_sheet}")
    return 0


if __name__ == "__main__":
    main()
