# -*- coding: utf-8 -*-
"""E1 — reference_timeline.json for the tianxi idle effect.

Source: user-provided desktop capture of a bilibili review video showing
the normal (blue) form GalilACE PhantomBeast in first person. Sampled
frames under discovery/reference/frames/; observations below are
video-derived => evidence level "inferred" (not original parameters).
"""
from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

OUT = Path(__file__).resolve().parent
SRC = r"C:\Users\Administrator\Videos\NVIDIA\Desktop\Desktop 2026.09.15 - 20.58.49.03.mp4"
FRAMES = OUT / "reference" / "frames"


def main() -> int:
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries",
         "format=duration,size:stream=codec_name,width,height,r_frame_rate",
         "-of", "json", SRC], capture_output=True, text=True)
    meta = json.loads(probe.stdout or "{}")

    doc = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "source": {
            "path": SRC,
            "kind": "desktop capture of bilibili weapon-review video (normal/blue form, first person)",
            "probe": meta,
            "caveats": [
                "bilibili recompression + 录制叠加层 (弹幕/字幕/水印) — 颜色亮度只能作近似参考",
                "画面为移速对比评测：主要是 idle/移动第一人称；采样帧未见明确开火/换弹/检视动作",
                "变形 (Chg) 形态未出现",
            ],
        },
        "frames_dir": "reference/frames/",
        "coverage": {
            "idle_moving_firstperson": True,
            "fire": False, "reload": False, "observe": False, "chg_form": False,
        },
        "observed_effects": [
            {
                "element": "muzzle/front bright glow",
                "appearance": "亮蓝白色团状光，随枪移动，有呼吸式明暗变化",
                "candidate_nodes": ["ParticleSystem;core-glow", "FlareSpriteFX;EYE-main/CORE 前方位"],
                "sockets": ["fix_effect_3"], "evidence": "inferred",
            },
            {
                "element": "side flowing ribbons",
                "appearance": "左右两条蓝色流动光带沿枪身中段缓慢流动（AURA_54/55 序列帧纹理）",
                "candidate_nodes": ["LTBModel;L-flow-front*", "LTBModel;L-flow-back",
                                    "LTBModel;R-flow-front*", "LTBModel;R-flow-back"],
                "sockets": ["fix_effect_9", "fix_effect_23"], "evidence": "inferred",
            },
            {
                "element": "rear 'eye' glow cluster",
                "appearance": "枪身中后段圆形蓝光团，中心亮核 + 外圈光晕",
                "candidate_nodes": ["FlareSpriteFX;EYE-main", "FlareSpriteFX;EYE-CORE",
                                    "FlareSpriteFX;EYE-rbw", "Sprite;EYE-prism"],
                "sockets": ["fix_effect_15", "fix_effect_16", "fix_effect_17"], "evidence": "inferred",
            },
            {
                "element": "body accent glows",
                "appearance": "机匣/瞄具附近多个小蓝点亮光，亮度随呼吸周期变化",
                "candidate_nodes": ["LTBModel;blue-parts", "LTBModel;red-parts-glow",
                                    "LTBModel;L-tragl", "LTBModel;R-tragl",
                                    "ParticleSystem;L-flow-p", "ParticleSystem;R-flow-p"],
                "sockets": ["fix_effect_5", "fix_effect_8", "fix_effect_22"], "evidence": "inferred",
            },
            {
                "element": "rear symbol/glitch marks",
                "appearance": "枪身符号位间歇闪光（采样帧中出现率低）",
                "candidate_nodes": ["LTBModel;simbol-glitch", "LTBModel;simbol-furfins",
                                    "LTBModel;simbol-additive", "LTBModel;simbol-back-glow"],
                "sockets": ["fix_effect_10", "fix_effect_11"], "evidence": "inferred",
            },
            {
                "element": "ambient sparkles near hand",
                "appearance": "握持位附近偶发小亮点",
                "candidate_nodes": ["ParticleSystem;ALL-p-big-BB", "ParticleSystem;ALL-p-big-YY",
                                    "Sprite;sharp-prism", "Sprite;core",
                                    "ParticleSystem;yellow-prism-TOP", "ParticleSystem;yellow-prism-TAIL-L"],
                "sockets": ["fix_effect_12", "fix_effect_19", "fix_effect_34", "fix_effect_35"],
                "evidence": "inferred",
            },
        ],
        "parameter_notes": [
            "所有节点 start/end=0–2 且 repeat=1：录像中光效持续存在且呼吸式周期 ≈ 2s，与把 Phase=2000ms / end_time=2.0s 理解为循环周期一致（inferred，需运行时确认）",
            "主色为蓝 (Ck 中 0,94,251 / 19,96,255)；录像未见红/黄色常驻层 — red-parts-glow/yellow-prism 可能为低频或动作触发",
            "Fix 'eye' 区在暗背景最亮；muzzle 前光团最大",
        ],
        "open_gaps": [
            "开火/换弹/切枪/检视的瞬时特效需另一段动作录像或按 FXF 63 组定义直接重建",
            "DynaLight 环境照明是否可见本录像无法判定",
        ],
    }
    dest = OUT / "reference_timeline.json"
    dest.write_text(json.dumps(doc, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"[ref] wrote {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
