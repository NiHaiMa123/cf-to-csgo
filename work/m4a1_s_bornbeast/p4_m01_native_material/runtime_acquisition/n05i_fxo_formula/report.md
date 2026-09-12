# N05-I — playerviewmesh.fxo formula extract

Result: **FXO_FORMULA_EXTRACTED**. P4-M01 remains **INCOMPLETE**.

Source SHA256 `d1672ba7e0a0f5b69e6a9520ec4ba0c6d4fb08b435aff1f3a3110af408bfb99c`. N05-E SHA match=True.
Load/disassemble ok=True. Unique shaders=51.

User Gate: N05-H in-game replacement was confirmed before this task. That Gate is not P4-M01 PASS.

`D3DXDisassembleEffect` failed (`ptr` null). Per-pass `ShaderBytecode.Disassemble` succeeded for 51 unique shaders.

## CFG → technique hypothesis

- EnvCubeUsage = `2`
- AlphaMapName2 present = `True`
- CubeMapTransformY = `-20`
- Selected technique (name-level): `tPlayerViewMeshAlphaAproxSnellTransformedCube`
- Shared PS of that technique: `unique/126ad72626dc1d7f_ps.asm` (all three passes)
- Grade: **HYPOTHESIS** — Name-level only: EnvCubeUsage=2 matches AproxSnell+TransformedCube techniques; AlphaMapName2 present selects the Alpha variant. Not a CShell/runtime assignment proof.

## Observed formula on that PS

Grade: **OBSERVED_ON_COMPILED_SHADER**. This is the compiled `ps_3_0` for the hypothesized technique, not proof CShell selects it.

Sampler map:

- `s0` `DiffuseMapSampler`
- `s1` `SpecularMapSampler`
- `s2` `CubeMapSampler`
- `s3` `NormalMapSampler`
- `s4` `AlphaMapSampler`
- `s5` `MaskMapSampler`

Equations (from CTAB + body, including preshader `SpecularPower * 0.25`):

- N = nrm(TBN * (2*NormalMap.xy-1) * NormalMappingFactor + vertexN)
- light = (abs(N·L * 0.5 + HalfLambertBase) ^ HalfLambertPower) * LightBrightness
- diffuse_lit = DiffuseMap.rgb * DiffuseMappingFactor * (light + DiffuseBoost) + AmbientLightColor
- preshader output exponent = SpecularPower * 0.25; PS pow uses that c3.x
- spec = SpecularMap.rgb * pow(abs(spec_term), SpecularPower*0.25) * SpecularMappingFactor
- cubeDir = ReflectionIndex * reflect(TransformedLitDirection, N) + refract_term(RefractionIndex)
- cube = texCUBE(CubeMap, cubeDir) * EnvCubeMapBrightness * EnvCubeMappingFactor
- out.rgb = diffuse_lit + spec * AlphaMap.g + cube * AlphaMap.b  (skipped if light rgb sum is 0)

AlphaMap channel split (this is the recovered TGA convention for this shader):

- `AlphaMap.r`: opacity * GlobalDiffuseAlpha -> oC0.w
- `AlphaMap.g`: multiplies spec before add
- `AlphaMap.b`: multiplies cube before add

- Ky 3x3 is used by tPlayerViewMeshTexturePanning vertex shaders, not by this hypothesized technique.
- No shader uniform named CubeMapTransformY. TransformedCube PS uses TransformedLitDirection for the cube ray; CPU-side fill of that vector remains OPEN.

## Candidate techniques (index only)

| technique | AlphaMap | ReflectionIndex | RefractionIndex | PS files |
|---|---|---|---|---|
| `tPlayerViewMesh` | no | no | no | `unique/c656cfed81d124c5_ps.asm` |
| `tPlayerViewMeshAproxSnell` | no | yes | yes | `unique/b54f90bb162fc91f_ps.asm` |
| `tPlayerViewMeshAproxSnellTransformedCube` | no | yes | yes | `unique/4651d228b07fcc98_ps.asm` |
| `tPlayerViewMeshAlpha` | yes | no | no | `unique/5a5b52f339ac03a0_ps.asm` |
| `tPlayerViewMeshAlphaAproxSnell` | yes | yes | yes | `unique/1a2fb0f9a0fde0bc_ps.asm, unique/946fe8a9001b5cda_ps.asm` |
| `tPlayerViewMeshAlphaAproxSnellTransformedCube` | yes | yes | yes | `unique/126ad72626dc1d7f_ps.asm` |

## What this proves

- Compiled effect per-pass VS/PS can be disassembled offline with D3DX on a self-built D3D9 device.
- Candidate Alpha+Snell+TransformedCube pixel shader actually samples Diffuse/Normal/Specular/Alpha/Cube.
- Alpha TGA is not a single opacity map in this shader: R opacity, G spec mix, B cube mix.
- SpecularPower is used as `pow(..., SpecularPower * 0.25)`, not as a Source 1 phong exponent.

## What this does not prove

- Which technique CShell selects for BornBeast (`EnvCubeUsage=2` is still name-level).
- Piece → sampler runtime assignment (LTB nNumTextures=0 remains).
- A numeric Source 1 `$phongexponent` / `$envmaptint` mapping. Do not copy CFG scalars into VMT.
- P4-M01 PASS.

## Limitations

- D3DX disassembly is the compiled shader, not the original HLSL.
- Technique selection from EnvCubeUsage=2 is a name-level hypothesis.
- CFG scalars are still not Source 1 phong/envmap numbers.
- This harness does not attach CrossFire or ACE.
- Raw FXO stays in data/n05i_fxo and is not committed.
