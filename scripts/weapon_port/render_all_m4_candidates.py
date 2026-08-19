# -*- coding: utf-8 -*-
"""Render and compare all candidate M4 hero weapon models and textures."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"
CFREZ_EXE = PROJECT_ROOT / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
WORK_DIR = PROJECT_ROOT / "work" / "m4a1_s_bornbeast" / "m4_hero_comparison"
WORK_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACT_DIR = Path(r"C:\Users\Administrator\.gemini\antigravity\brain\e38afcad-92d4-47f8-80dc-cbb40a0b7bda")


def main() -> int:
    # 1. Search for all hero M4 LTB models
    candidates = [
        ("PV-M4A1_S_BornBeast", "rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast.LTB"),
        ("PV-M4A1_S_BornBeast2", "rf016/Models/PLAYERVIEW/PV-M4A1_S_BornBeast2.LTB"),
        ("PV-M4A1_Silencer_Predator", "rf016/Models/PLAYERVIEW/PV-M4A1_Silencer_Predator.LTB"),
        ("PV-M4A1_S_IronBeast-NobleGold", "rf016/Models/PLAYERVIEW/PV-M4A1_S_IronBeast-NobleGold.LTB"),
        ("PV-M4A1_Silencer_PrismBeast", "rf016/Models/PLAYERVIEW/PV-M4A1_Silencer_PrismBeast.LTB"),
        ("PV-M4A1_S_Transformers", "rf016/Models/PLAYERVIEW/PV-M4A1_S_Transformers.LTB"),
        ("PV-M4A1_S_Jewelry", "rf016/Models/PLAYERVIEW/PV-M4A1_S_Jewelry.LTB"),
    ]

    print("[*] 1. Inspecting LTB candidate structures...")
    results = {}
    for name, rel_path in candidates:
        ltb_file = DATA_DIR / rel_path
        if not ltb_file.exists():
            print(f"  Missing: {rel_path}")
            continue

        inspect_json = WORK_DIR / f"{name}_inspect.json"
        subprocess.run([str(CFREZ_EXE), "--inspect-ltb", "--input", str(ltb_file), "--output", str(inspect_json)], capture_output=True, text=True)

        obj_file = WORK_DIR / f"{name}.obj"
        rf_root = DATA_DIR / rel_path.split("/")[0]
        subprocess.run([
            str(CFREZ_EXE), "--export-obj",
            "--root", str(rf_root),
            "--model", str(Path(*Path(rel_path).parts[1:])),
            "--output", str(obj_file)
        ], capture_output=True, text=True)

        info = {}
        if inspect_json.exists():
            data = json.loads(inspect_json.read_text(encoding="utf-8"))
            info["nodes"] = len(data.get("Nodes", []))
            info["node_names"] = [n.get("NodeName") for n in data.get("Nodes", [])][:15]
            info["meshes"] = len(data.get("Meshes", []))
            info["mesh_names"] = [m.get("MeshName") for m in data.get("Meshes", [])]
            info["total_verts"] = sum(m.get("VertexCount", 0) for m in data.get("Meshes", []))
            info["total_tris"] = sum(m.get("TriangleCount", 0) for m in data.get("Meshes", []))
            info["animations"] = [a.get("AnimationName") for a in data.get("Animations", [])]
        results[name] = info
        print(f"  -> {name}: meshes={info.get('meshes')}, mesh_names={info.get('mesh_names')}")

    # 2. Search all textures in data/ for each hero weapon
    print("[*] 2. Searching and decoding all hero weapon textures...")
    tex_dir = WORK_DIR / "textures"
    tex_dir.mkdir(parents=True, exist_ok=True)

    dtxs = list(DATA_DIR.rglob("*BornBeast*.DTX")) + list(DATA_DIR.rglob("*Predator*.DTX")) + list(DATA_DIR.rglob("*IronBeast*.DTX"))
    for dtx in set(dtxs):
        if "WEAPON" in dtx.as_posix() or "PLAYERVIEW" in dtx.as_posix() or "ModelTextures" in dtx.as_posix():
            out_png = tex_dir / f"{dtx.stem}.png"
            subprocess.run([str(CFREZ_EXE), "--decode-image", str(dtx), str(out_png)], capture_output=True, text=True)
            if out_png.exists() and out_png.stat().st_size > 0:
                print(f"  Decoded: {dtx.name} ({out_png.stat().st_size} bytes)")

    out_summary = WORK_DIR / "candidate_analysis.json"
    out_summary.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"[PASS] Done! Analysis written to {out_summary}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
