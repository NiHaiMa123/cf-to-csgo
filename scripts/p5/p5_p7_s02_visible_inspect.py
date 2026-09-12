"""P7-S02 — Visible Inspect on the deployed 雷神 M4A4 slot.

Restores official CS:GO M4A4 lookat sequences (lookat01 / prepare / loop)
onto the P6 雷神 mesh. P4/P6 used frozen_noop_safe idle Inspect.

This is CS inspect motion, not CF original animation. When CF anims replace
these clips, P7-S01 sound event frames must be retimed.

Does not overwrite the parked frozen addon. Does not change P7-S01 sound.
Does not rebuild the gun mesh.

Repro:
  python scripts/p5/p5_p7_s02_visible_inspect.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts", "csgo_pack"))
import _paths  # noqa: E402
from weapon_port.pipeline import mdl_header  # noqa: E402

REPO = Path(_paths.project_dir())
GAME = Path(_paths.game_dir())
P6 = REPO / "work" / "p5_leishen" / "p6"
OUT = REPO / "work" / "p5_leishen" / "p7_s02"
SOURCE1 = OUT / "source1"
ISOLATED = OUT / "isolated_game" / "csgo"
LOG_DIR = OUT / "logs"
STUDIOMDL = GAME / "bin" / "studiomdl.exe"
ADDON_NAME = "p_cf_leishen_m4a4_p6"
FROZEN_NAME = "p_cf_bornbeast_m4a4_p4_frozen_noop_01"
MIGI_ADDONS = GAME / "migi" / "csgo" / "addons"
PARK = GAME / "migi" / "csgo" / "_parked_addons"
MODEL_REL = Path("models/weapons")

OFFICIAL_LOOKAT = {
    "lookat01": '''$sequence "lookat01" {
	"v_rif_m4a1_anims\\lookat01.smd"
	{ event AE_CL_SET_STATTRAK_GLOW 0 "1" }
	{ event AE_CL_SET_STATTRAK_GLOW 92 "0" }
	{ event AE_BEGIN_TAUNT_LOOP 91 "0.306666" }
	{ event 5004 2 "Weapon_M4A1.WeaponMove1" }
	{ event 5004 92 "Weapon_M4A1.WeaponMove2" }
	{ event 5004 116 "Weapon_M4A1.WeaponMove3" }
	fadein 0.3
	fadeout 0.3
	fps 30
}''',
    "lookat01_prepare": '''$sequence "lookat01_prepare" {
	"v_rif_m4a1_anims\\lookat01_prepare.smd"
	fadein 0.2
	fadeout 0.2
	fps 30
}''',
    "lookat01_loop": '''$sequence "lookat01_loop" {
	"v_rif_m4a1_anims\\lookat01_loop.smd"
	fadein 0.2
	fadeout 0.2
	fps 15
}''',
}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def smd_frame_count(path: Path) -> int:
    times: list[int] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        stripped = line.strip()
        if stripped.startswith("time "):
            times.append(int(float(stripped.split()[1])))
    return (max(times) + 1) if times else 0


def patch_qc(qc_text: str) -> str:
    for name, block in OFFICIAL_LOOKAT.items():
        pattern = re.compile(
            rf'\$sequence\s+"{re.escape(name)}"\s*\{{.*?\n\}}',
            flags=re.IGNORECASE | re.DOTALL,
        )
        qc_text, count = pattern.subn(lambda _match, text=block: text, qc_text, count=1)
        if count != 1:
            raise RuntimeError(f"failed to replace QC sequence {name}")
    return qc_text


def main() -> int:
    p6_source = P6 / "source1"
    p6_isolated = P6 / "isolated_game" / "csgo"
    if not (p6_source / "v_rif_m4a1.qc").is_file():
        raise RuntimeError("P6 source1 QC missing")
    if not STUDIOMDL.is_file():
        raise RuntimeError(f"studiomdl missing: {STUDIOMDL}")
    frozen_live = MIGI_ADDONS / FROZEN_NAME
    if frozen_live.exists():
        raise RuntimeError("frozen addon is in MIGI addons; refuse to compile a second v_rif_m4a1")
    live = MIGI_ADDONS / ADDON_NAME
    if not live.exists():
        raise RuntimeError("P6 live addon missing")

    if OUT.exists():
        shutil.rmtree(OUT)
    for path in (OUT, SOURCE1, ISOLATED, LOG_DIR):
        path.mkdir(parents=True, exist_ok=True)
    shutil.copytree(p6_source, SOURCE1, dirs_exist_ok=True)
    shutil.copytree(p6_isolated, ISOLATED, dirs_exist_ok=True)

    frames = {
        name: smd_frame_count(SOURCE1 / "v_rif_m4a1_anims" / f"{name}.smd")
        for name in OFFICIAL_LOOKAT
    }
    if frames["lookat01"] < 117:
        raise RuntimeError(f"official lookat01 too short for events: {frames}")

    qc_path = SOURCE1 / "v_rif_m4a1.qc"
    original = qc_path.read_text(encoding="utf-8", errors="replace")
    if "lookat01_frozen.smd" not in original:
        raise RuntimeError("expected P6 QC to still use frozen inspect clips")
    qc_path.write_text(patch_qc(original), encoding="utf-8")

    compiled = ISOLATED / "models" / "weapons" / "v_rif_m4a1.mdl"
    proc = subprocess.run(
        [str(STUDIOMDL), "-game", str(ISOLATED), str(qc_path)],
        cwd=str(SOURCE1),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    (LOG_DIR / "studiomdl.stdout.log").write_text(proc.stdout or "", encoding="utf-8")
    (LOG_DIR / "studiomdl.stderr.log").write_text(proc.stderr or "", encoding="utf-8")
    if proc.returncode != 0 or not compiled.is_file():
        raise RuntimeError(
            f"studiomdl failed ({proc.returncode}): {(proc.stderr or proc.stdout or '')[-1200:]}"
        )

    header = mdl_header(compiled)
    models_dir = live / MODEL_REL
    deployed: dict[str, str] = {}
    for path in (ISOLATED / "models" / "weapons").glob("v_rif_m4a1.*"):
        dest = models_dir / path.name
        shutil.copy2(path, dest)
        deployed[path.name] = sha256_file(dest)

    report = {
        "schema": "cf2.p7.visible-inspect.v1",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P7-S02",
        "result": "P7_VISIBLE_INSPECT_DEPLOYED",
        "inspect_policy": "official_cs_lookat",
        "cf_original_animation": False,
        "sound_retime_required_when_cf_anim_replaced": True,
        "addon_name": ADDON_NAME,
        "frames": frames,
        "mdl_header": header,
        "deployed_models": deployed,
        "frozen_untouched": (PARK / FROZEN_NAME).exists() and not frozen_live.exists(),
        "sound_addon_untouched": (MIGI_ADDONS / "p_cf_leishen_m4a4_p7_sound").exists(),
        "notes": [
            "P7-S01 sound is user-accepted on CS action timing.",
            "Replacing CS clips with CF original animation still requires sound event retiming.",
            "Inspect motion is official CS:GO M4A4 lookat, not CF inspect.",
            "Not a P4-M01 PASS.",
        ],
    }
    (OUT / "execution.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "report.md").write_text(
        "\n".join(
            [
                "# P7-S02 — Visible Inspect",
                "",
                "Result: **P7_VISIBLE_INSPECT_DEPLOYED**. Inspect uses official CS:GO M4A4 lookat clips on the P6 雷神 mesh. Frozen addon not modified. P7-S01 sound not modified.",
                "",
                f"Addon models updated in `{ADDON_NAME}`.",
                f"lookat01 frames `{frames['lookat01']}`, prepare `{frames['lookat01_prepare']}`, loop `{frames['lookat01_loop']}`.",
                "",
                "This is CS inspect, not CF original animation. User 2026-09-13: P7-S01 sound is accepted on CS actions; **when CF animation replaces these clips, sound timing must be adjusted again**.",
                "",
                "Not a P4-M01 PASS. World model / CF anim / IK still open.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps({
        "result": report["result"],
        "addon": ADDON_NAME,
        "frames": frames,
        "out": rel(OUT),
    }, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
