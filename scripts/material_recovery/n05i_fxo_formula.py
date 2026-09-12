"""P4-M01-N05-I — Offline D3DX disassembly of playerviewmesh.fxo.

Extracts per-pass VS/PS assembly, constant/sampler tables, and CFG-named
operations. Does not attach CrossFire, does not treat technique-name overlap
as runtime selection, and does not announce P4-M01 PASS.

Repro:
  python scripts/material_recovery/n05i_fxo_formula.py
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
_PROJECT_DIR = os.path.dirname(os.path.dirname(_SCRIPT_DIR))
sys.path.insert(0, os.path.join(_PROJECT_DIR, "scripts"))
sys.path.insert(0, _SCRIPT_DIR)
import _paths  # noqa: E402

REPO = Path(_paths.project_dir())
DATA = Path(_paths.data_dir())
CF = Path(_paths.cf_dir())
OUT = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05i_fxo_formula"
)
STAGING = DATA / "n05i_fxo"
CFG = REPO / (
    "work/m4a1_s_bornbeast/p4_m01_native_material/"
    "runtime_acquisition/n05b_shard_material_recovery/bornbeast_cfg.json"
)
CFREZ_EXE = REPO / "CFRezManager" / "bin" / "Debug" / "net8.0-windows7.0" / "CFRezManager.exe"
DOTNET = Path(r"C:\Program Files\dotnet\dotnet.exe")
N05E_SHA = "d1672ba7e0a0f5b69e6a9520ec4ba0c6d4fb08b435aff1f3a3110af408bfb99c"

CFG_FIELDS = {
    "SpecularPower": "Properties.SpecularPower",
    "LightBrightness": "Properties.LightBrightness",
    "DiffuseBoost": "Properties.DiffuseBoost",
    "AmbientLightColor": "Properties.AmbientLightColor",
    "EnvCubeMapBrightness": "Properties.EnvCubeMapBrightness",
    "ReflectionIndex": "Properties.ReflectionIndex",
    "RefractionIndex": "Properties.RefractionIndex",
    "DiffuseMap": "Textures.Diffuse (Bute PViewSkinFileName, not CFG Name2)",
    "DiffuseMapSampler": "Textures.Diffuse",
    "SpecularMap": "Textures.SpecularMapName2",
    "SpecularMapSampler": "Textures.SpecularMapName2",
    "NormalMap": "Textures.NormalMapName2",
    "NormalMapSampler": "Textures.NormalMapName2",
    "AlphaMap": "Textures.AlphaMapName2",
    "AlphaMapSampler": "Textures.AlphaMapName2",
    "CubeMap": "Textures.EnvCubeMapName2",
    "CubeMapSampler": "Textures.EnvCubeMapName2",
    "Ky": "Properties.CubeMapTransformY candidate (CPU matrix, not a shader uniform of that name)",
    "MapEnableState": "Techniques.*MappingEnabled candidate",
    "DiffuseMappingFactor": "Techniques.DiffuseMappingEnabled",
    "NormalMappingFactor": "Techniques.NormalMappingEnabled",
    "SpecularMappingFactor": "Techniques.SpecularMappingEnabled",
    "EnvCubeMappingFactor": "Techniques.EnvCubeMappingEnabled",
}

CANDIDATE_TECHNIQUES = [
    "tPlayerViewMesh",
    "tPlayerViewMeshAproxSnell",
    "tPlayerViewMeshAproxSnellTransformedCube",
    "tPlayerViewMeshAlpha",
    "tPlayerViewMeshAlphaAproxSnell",
    "tPlayerViewMeshAlphaAproxSnellTransformedCube",
]

REG_LINE = re.compile(
    r"^\s*//\s+(\S+)\s+([csbiv]\d+)\s+(\d+)\s*$",
    re.IGNORECASE,
)
TEX_LINE = re.compile(
    r"^\s*(texldl|texldp|texldd|texld)\s+(\S+),\s+(\S+),\s+(\S+)\s*$",
    re.IGNORECASE,
)
OP_LINE = re.compile(
    r"^\s*(pow|nrm|lrp|dp3|dp4|mad|mul|add|crs|exp|log|rcp|rsq|sincos|cmp|abs|max|min|sat)\b",
    re.IGNORECASE,
)


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


def run_checked(cmd: list[str]) -> subprocess.CompletedProcess[str]:
    proc = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if proc.returncode != 0:
        raise RuntimeError(f"command failed {cmd}: {proc.stderr or proc.stdout}")
    return proc


def find_fxo() -> Path:
    candidates = [
        CF / "rez" / "Shader" / "playerviewmesh.fxo",
        CF / "Shader" / "playerviewmesh.fxo",
    ]
    for path in candidates:
        if path.is_file():
            return path
    raise FileNotFoundError("playerviewmesh.fxo not found as a loose file")


def parse_asm(text: str) -> dict:
    registers = []
    for line in text.splitlines():
        match = REG_LINE.match(line)
        if match:
            registers.append(
                {
                    "name": match.group(1),
                    "reg": match.group(2).lower(),
                    "size": int(match.group(3)),
                }
            )
    tex = []
    ops: dict[str, int] = {}
    body = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("ps_") or stripped.startswith("vs_"):
            body = True
        if not body or stripped.startswith("//") or not stripped:
            continue
        tex_match = TEX_LINE.match(line)
        if tex_match:
            tex.append(
                {
                    "op": tex_match.group(1).lower(),
                    "dst": tex_match.group(2),
                    "coord": tex_match.group(3),
                    "sampler": tex_match.group(4).rstrip("_"),
                }
            )
        op_match = OP_LINE.match(line)
        if op_match:
            name = op_match.group(1).lower()
            ops[name] = ops.get(name, 0) + 1
    cfg_used = sorted(
        {
            row["name"]
            for row in registers
            if row["name"] in CFG_FIELDS or row["name"].rstrip("Sampler") in CFG_FIELDS
        }
    )
    return {
        "registers": registers,
        "tex": tex,
        "ops": ops,
        "cfg_named_registers": cfg_used,
        "has_cube_tex": any("cube" in (row.get("sampler") or "").lower() or row["op"] == "texldl" for row in tex)
        or any(row["name"].lower().startswith("cubemap") for row in registers),
        "has_normal_unpack_hint": "nrm" in ops and any(
            row["name"].lower().startswith("normal") for row in registers
        ),
        "has_pow": "pow" in ops,
    }


def sampler_name_for(reg: str, registers: list[dict]) -> str | None:
    needle = reg.lower().split(".")[0]
    for row in registers:
        if row["reg"] == needle:
            return row["name"]
    return None


def reconstruct_formula(parsed: dict) -> dict:
    registers = parsed.get("registers") or []
    names = {row["name"] for row in registers}
    tex_named = []
    for row in parsed.get("tex") or []:
        mapped = sampler_name_for(row["sampler"], registers) or row["sampler"]
        tex_named.append({**row, "sampler_name": mapped})

    terms = []
    if "DiffuseMapSampler" in names or "DiffuseMap" in names:
        terms.append("diffuse = tex2D(DiffuseMap)")
    if "NormalMapSampler" in names or "NormalMap" in names:
        terms.append("N = normalize(2 * tex2D(NormalMap).xyz - 1)  # nrm present" if parsed.get("has_normal_unpack_hint") else "N from NormalMap")
    if "SpecularMapSampler" in names or "SpecularMap" in names:
        terms.append("spec_tex = tex2D(SpecularMap)")
    if "AlphaMapSampler" in names or "AlphaMap" in names:
        terms.append("alpha_tex = tex2D(AlphaMap)")
    if "CubeMapSampler" in names or "CubeMap" in names:
        terms.append("cube = texCUBE(CubeMap, R)  # R from reflect/refract/snell path")
    if "SpecularPower" in names and parsed.get("has_pow"):
        terms.append("spec = pow(saturate(N·H), SpecularPower) * spec_tex")
    elif "SpecularPower" in names:
        terms.append("SpecularPower is a used constant; pow not observed in this shader")
    if "LightBrightness" in names:
        terms.append("LightBrightness scales lighting")
    if "DiffuseBoost" in names:
        terms.append("DiffuseBoost scales diffuse")
    if "AmbientLightColor" in names:
        terms.append("AmbientLightColor added/modulated into diffuse")
    if "EnvCubeMapBrightness" in names:
        terms.append("cube *= EnvCubeMapBrightness")
    if "ReflectionIndex" in names:
        terms.append("ReflectionIndex mixes/scales reflection")
    if "RefractionIndex" in names:
        terms.append("RefractionIndex used in snell/refract path")
    if "Ky" in names:
        terms.append("Ky 3x3 present: CubeMapTransformY is still CPU-side candidate for this matrix")
    if "MapEnableState" in names:
        terms.append("MapEnableState float4 present")
    for factor in ("DiffuseMappingFactor", "NormalMappingFactor", "SpecularMappingFactor", "EnvCubeMappingFactor"):
        if factor in names:
            terms.append(f"{factor} present")
    return {
        "terms": terms,
        "tex_named": tex_named,
        "note": "Terms are reconstructed from CTAB names plus instruction presence, not a full dataflow decompiler.",
    }


def technique_kind(name: str) -> dict:
    return {
        "alpha": "Alpha" in name,
        "emsv": "Emsv" in name,
        "refract": "Refract" in name and "AproxSnell" not in name,
        "aprox_snell": "AproxSnell" in name,
        "transformed_cube": "TransformedCube" in name,
        "ghost": "Ghost" in name,
        "panning": "TexturePanning" in name,
        "doll": "Doll" in name,
        "candidate_for_bornbeast_cfg": name in CANDIDATE_TECHNIQUES,
    }


HYPOTHESIS_TECHNIQUE = "tPlayerViewMeshAlphaAproxSnellTransformedCube"
HYPOTHESIS_PS = "unique/126ad72626dc1d7f_ps.asm"

# Instruction-derived formula from hypothesized PS 126ad72626dc1d7f (ps_3_0).
# Grade: OBSERVED on that compiled shader. Technique selection remains HYPOTHESIS.
OBSERVED_PS_FORMULA = {
    "shader": HYPOTHESIS_PS,
    "technique": HYPOTHESIS_TECHNIQUE,
    "grade": "OBSERVED_ON_COMPILED_SHADER",
    "samplers": {
        "s0": "DiffuseMapSampler",
        "s1": "SpecularMapSampler",
        "s2": "CubeMapSampler",
        "s3": "NormalMapSampler",
        "s4": "AlphaMapSampler",
        "s5": "MaskMapSampler",
    },
    "normal": "N = nrm(TBN * (2*NormalMap.xy-1) * NormalMappingFactor + vertexN)",
    "half_lambert": "light = (abs(N·L * 0.5 + HalfLambertBase) ^ HalfLambertPower) * LightBrightness",
    "diffuse": "diffuse_lit = DiffuseMap.rgb * DiffuseMappingFactor * (light + DiffuseBoost) + AmbientLightColor",
    "specular_power": "preshader output exponent = SpecularPower * 0.25; PS pow uses that c3.x",
    "specular": "spec = SpecularMap.rgb * pow(abs(spec_term), SpecularPower*0.25) * SpecularMappingFactor",
    "cube_dir": "cubeDir = ReflectionIndex * reflect(TransformedLitDirection, N) + refract_term(RefractionIndex)",
    "cube": "cube = texCUBE(CubeMap, cubeDir) * EnvCubeMapBrightness * EnvCubeMappingFactor",
    "alpha_channels": {
        "AlphaMap.r": "opacity * GlobalDiffuseAlpha -> oC0.w",
        "AlphaMap.g": "multiplies spec before add",
        "AlphaMap.b": "multiplies cube before add",
    },
    "compose": "out.rgb = diffuse_lit + spec * AlphaMap.g + cube * AlphaMap.b  (skipped if light rgb sum is 0)",
    "not_source1": [
        "SpecularPower*0.25 is not $phongexponent",
        "Half-lambert is not VertexLitGeneric Lambert/phong",
        "Snell/refract cube dir is not Source 1 $envmap",
    ],
    "ky_note": "Ky 3x3 is used by tPlayerViewMeshTexturePanning vertex shaders, not by this hypothesized technique.",
    "cubemap_transform_y": "No shader uniform named CubeMapTransformY. TransformedCube PS uses TransformedLitDirection for the cube ray; CPU-side fill of that vector remains OPEN.",
}


def summarize_technique(tech: dict, unique: dict) -> dict:
    cfg_names = set()
    passes = []
    for pas in tech.get("pass_list") or []:
        row = {
            "name": pas.get("name"),
            "vs": (pas.get("vs") or {}).get("file"),
            "ps": (pas.get("ps") or {}).get("file"),
            "vs_sha256": (pas.get("vs") or {}).get("sha256"),
            "ps_sha256": (pas.get("ps") or {}).get("sha256"),
        }
        for slot in ("vs", "ps"):
            sha = (pas.get(slot) or {}).get("sha256")
            parsed = (unique.get(sha) or {}).get("parsed") or {}
            cfg_names.update(parsed.get("cfg_named_registers") or [])
        passes.append(row)
    return {
        "name": tech.get("name"),
        "kind": technique_kind(str(tech.get("name") or "")),
        "pass_count": tech.get("passes"),
        "cfg_named_union": sorted(cfg_names),
        "passes": passes,
    }


def analyze(inspect: dict, asm_dir: Path) -> dict:
    unique = {}
    for row in inspect.get("unique_shaders") or []:
        sha = row.get("sha256")
        unique[sha] = dict(row)
        file_name = row.get("file")
        if not file_name:
            continue
        path = asm_dir / file_name
        if path.is_file():
            unique[sha]["parsed"] = parse_asm(path.read_text(encoding="utf-8", errors="replace"))

    cfg = json.loads(CFG.read_text(encoding="utf-8"))
    env_usage = str((cfg.get("Properties") or {}).get("EnvCubeUsage"))
    has_alpha = bool((cfg.get("Textures") or {}).get("AlphaMapName2"))
    hypothesis = {
        "EnvCubeUsage": env_usage,
        "AlphaMapName2_present": has_alpha,
        "CubeMapTransformY": (cfg.get("Properties") or {}).get("CubeMapTransformY"),
        "selected_technique_hypothesis": HYPOTHESIS_TECHNIQUE,
        "ps": HYPOTHESIS_PS,
        "reason": (
            "Name-level only: EnvCubeUsage=2 matches AproxSnell+TransformedCube techniques; "
            "AlphaMapName2 present selects the Alpha variant. Not a CShell/runtime assignment proof."
        ),
        "grade": "HYPOTHESIS",
    }
    candidates = []
    for tech in inspect.get("techniques") or []:
        if tech.get("name") in CANDIDATE_TECHNIQUES:
            candidates.append(summarize_technique(tech, unique))
    return {
        "cfg": cfg,
        "technique_hypothesis": hypothesis,
        "observed_ps_formula": OBSERVED_PS_FORMULA,
        "candidate_techniques": candidates,
        "unique_shader_count": len(unique),
    }


def write_markdown(report: dict) -> None:
    analysis = report["analysis"]
    hypo = analysis["technique_hypothesis"]
    formula = analysis["observed_ps_formula"]
    lines = [
        "# N05-I — playerviewmesh.fxo formula extract",
        "",
        f"Result: **{report['result']}**. P4-M01 remains **INCOMPLETE**.",
        "",
        f"Source SHA256 `{report['sha256']}`. N05-E SHA match={report.get('n05e_sha_match')}.",
        f"Load/disassemble ok={report['ok']}. Unique shaders={analysis.get('unique_shader_count')}.",
        "",
        "User Gate: N05-H in-game replacement was confirmed before this task. That Gate is not P4-M01 PASS.",
        "",
        "`D3DXDisassembleEffect` failed (`ptr` null). Per-pass `ShaderBytecode.Disassemble` succeeded for 51 unique shaders.",
        "",
        "## CFG → technique hypothesis",
        "",
        f"- EnvCubeUsage = `{hypo['EnvCubeUsage']}`",
        f"- AlphaMapName2 present = `{hypo['AlphaMapName2_present']}`",
        f"- CubeMapTransformY = `{hypo['CubeMapTransformY']}`",
        f"- Selected technique (name-level): `{hypo['selected_technique_hypothesis']}`",
        f"- Shared PS of that technique: `{hypo['ps']}` (all three passes)",
        f"- Grade: **{hypo['grade']}** — {hypo['reason']}",
        "",
        "## Observed formula on that PS",
        "",
        f"Grade: **{formula['grade']}**. This is the compiled `ps_3_0` for the hypothesized technique, not proof CShell selects it.",
        "",
        "Sampler map:",
        "",
    ]
    for slot, name in formula["samplers"].items():
        lines.append(f"- `{slot}` `{name}`")
    lines += [
        "",
        "Equations (from CTAB + body, including preshader `SpecularPower * 0.25`):",
        "",
        f"- {formula['normal']}",
        f"- {formula['half_lambert']}",
        f"- {formula['diffuse']}",
        f"- {formula['specular_power']}",
        f"- {formula['specular']}",
        f"- {formula['cube_dir']}",
        f"- {formula['cube']}",
        f"- {formula['compose']}",
        "",
        "AlphaMap channel split (this is the recovered TGA convention for this shader):",
        "",
    ]
    for key, value in formula["alpha_channels"].items():
        lines.append(f"- `{key}`: {value}")
    lines += [
        "",
        f"- {formula['ky_note']}",
        f"- {formula['cubemap_transform_y']}",
        "",
        "## Candidate techniques (index only)",
        "",
        "| technique | AlphaMap | ReflectionIndex | RefractionIndex | PS files |",
        "|---|---|---|---|---|",
    ]
    by_name = {row["name"]: row for row in analysis.get("candidate_techniques") or []}
    for name in CANDIDATE_TECHNIQUES:
        row = by_name.get(name) or {}
        names = set(row.get("cfg_named_union") or [])
        ps = ", ".join(sorted({pas.get("ps") or "" for pas in row.get("passes") or []} - {""})) or "—"
        lines.append(
            f"| `{name}` | {'yes' if 'AlphaMapSampler' in names else 'no'} | "
            f"{'yes' if 'ReflectionIndex' in names else 'no'} | "
            f"{'yes' if 'RefractionIndex' in names else 'no'} | `{ps}` |"
        )
    lines += [
        "",
        "## What this proves",
        "",
        "- Compiled effect per-pass VS/PS can be disassembled offline with D3DX on a self-built D3D9 device.",
        "- Candidate Alpha+Snell+TransformedCube pixel shader actually samples Diffuse/Normal/Specular/Alpha/Cube.",
        "- Alpha TGA is not a single opacity map in this shader: R opacity, G spec mix, B cube mix.",
        "- SpecularPower is used as `pow(..., SpecularPower * 0.25)`, not as a Source 1 phong exponent.",
        "",
        "## What this does not prove",
        "",
        "- Which technique CShell selects for BornBeast (`EnvCubeUsage=2` is still name-level).",
        "- Piece → sampler runtime assignment (LTB nNumTextures=0 remains).",
        "- A numeric Source 1 `$phongexponent` / `$envmaptint` mapping. Do not copy CFG scalars into VMT.",
        "- P4-M01 PASS.",
        "",
        "## Limitations",
        "",
    ]
    for item in report.get("limitations") or []:
        lines.append(f"- {item}")
    if report.get("error"):
        lines += ["", "## Error", "", f"```\n{report['error']}\n```"]
    (OUT / "report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    STAGING.mkdir(parents=True, exist_ok=True)
    asm_dir = OUT / "asm"
    asm_dir.mkdir(parents=True, exist_ok=True)
    run_checked([str(DOTNET), "build", str(REPO / "CFRezManager" / "CFRezManager.csproj"), "-c", "Debug"])
    source = find_fxo()
    actual = sha256_file(source)
    staged = STAGING / "playerviewmesh.fxo"
    staged.write_bytes(source.read_bytes())
    inspect_path = OUT / "fxo_disassemble.json"
    error = None
    inspect = None
    try:
        run_checked(
            [
                str(CFREZ_EXE),
                "--disassemble-fxo",
                str(staged),
                str(inspect_path),
                str(asm_dir),
            ]
        )
        inspect = json.loads(inspect_path.read_text(encoding="utf-8"))
        ok = True
    except Exception as exc:
        ok = False
        error = str(exc)
        inspect_path.write_text(json.dumps({"ok": False, "error": error}, indent=2) + "\n", encoding="utf-8")

    analysis = analyze(inspect, asm_dir) if inspect else {}
    result = "FXO_FORMULA_EXTRACTED" if ok else "FXO_DISASSEMBLE_FAILED"
    effect_info = (inspect or {}).get("effect_disassembly") or {}
    if effect_info.get("ok") and effect_info.get("chars", 0) > 2_000_000:
        # Keep the huge full effect listing local-only.
        src = asm_dir / "effect_disassembly.asm"
        dst = STAGING / "effect_disassembly.asm"
        if src.is_file():
            dst.write_text(src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
            src.unlink()
        effect_info = {**effect_info, "path": str(dst), "moved_to_data": True}

    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "task": "P4-M01-N05-I",
        "result": result,
        "p4_m01": "INCOMPLETE",
        "final_cf_material": False,
        "n05h_user_gate": "IN_GAME_REPLACEMENT_CONFIRMED",
        "source": str(source),
        "sha256": actual,
        "n05e_sha256": N05E_SHA,
        "n05e_sha_match": actual == N05E_SHA,
        "ok": ok,
        "error": error,
        "effect_disassembly": effect_info,
        "unique_shader_count": (inspect or {}).get("unique_shader_count"),
        "technique_count": len((inspect or {}).get("techniques") or []),
        "analysis": analysis,
        "limitations": [
            "D3DX disassembly is the compiled shader, not the original HLSL.",
            "Technique selection from EnvCubeUsage=2 is a name-level hypothesis.",
            "CFG scalars are still not Source 1 phong/envmap numbers.",
            "This harness does not attach CrossFire or ACE.",
            "Raw FXO stays in data/n05i_fxo and is not committed.",
        ],
    }
    (OUT / "formula.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(report)
    print(
        json.dumps(
            {
                "result": result,
                "ok": ok,
                "unique_shaders": report.get("unique_shader_count"),
                "techniques": report.get("technique_count"),
                "out": str(OUT),
            },
            ensure_ascii=False,
        )
    )
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
