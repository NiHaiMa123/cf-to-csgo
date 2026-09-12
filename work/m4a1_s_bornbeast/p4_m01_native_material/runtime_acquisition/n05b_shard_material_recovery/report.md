# N05-A Review / N05-B — RF017 numbered-part recovery

Result: **PV_DTX_AND_TEXT_CFG_RECOVERED_FROM_NUMBERED_PARTS**. P4-M01 remains **INCOMPLETE**: native input recovery is verified; final piece/sampler selection and rendering still need validation.

Reviewed executor commit: `32d2ec2e72439be28c471139e6f2e5805ae73729`.

## Root cause

The directory of `rez/rf017.rez` contains entries whose legacy `time` field is a small integer. For the nine tested material entries, reading the same offset and size from the sibling `rf017_<time>.rez` produces the **exact directory MD5**. Reading that range from the directory-bearing main file does not.

Example: `PLAYERVIEW/PV-M4A1_S_BornBeast.DTX` has field value 8, offset 186436476, size 524452. Its verified bytes are in `rez/rf017_8.rez`, with SHA256 `a30c9a271612dec05cb44f44e6e9412be398350e5fb6ac93966aea4b7f56b4ba`. They are a standard Jupiter version -5 DXT1 image: 1024×1024, one mip, 164-byte header, 524288-byte payload.

The main file is 196985580 bytes; 155 of its 4417 parsed entries extend beyond that file if interpreted as main-file ranges. This initially looked like an input-integrity problem. **It does not establish corruption**: bounds must be checked against the selected numbered part. The new helper verifies both bounds and MD5 and rejects zero or multiple matching candidates. The field is not globally renamed to a shard index: normal archives can still use it as a timestamp, and main-file data remains an eligible candidate.

## Verified recovery

All nine targets have exactly one hash-matching candidate. Full offsets, hashes, candidate checks and output paths are in [recovery.json](recovery.json).

| Target | Part field | Recovered format |
|---|---:|---|
| BornBeast PV | 8 | DXT1, 1024×1024 |
| BornBeast QV (main-index entry) | 13 | DXT1, 256×256 |
| RoyalDragon PV | 8 | DXT1, 1024×1024 |
| RoyalDragon Specular | 12 | DXT1, 1024×1024 |
| GreenVein Specular | 12 | DXT1, 512×512 |
| BornBeast Alpha | 2 | Standard TGA, 1024×1024; no repair |
| BornBeast Normal | 6 | Standard TGA, 1024×1024; no repair |
| BornBeast Specular | 12 | Standard TGA, 1024×1024; no repair |
| BornBeast CFG | 9 | ASCII INI-style text; 492 bytes |

The PV PNG from Python and the existing compiled CFRezManager image decoder has **identical RGBA pixels**. That decoder works once it receives the correct bytes. The image is naturally dark; it has not been brightened, recolored or supplemented with external pixels.

The parsed [CFG](bornbeast_cfg.json) has `[Textures]`, `[Techniques]` and `[Properties]`, including:

- `SpecularMapName2=M4A1_S_BornBeast_S.tga`
- `NormalMapName2=M4A1_S_BornBeast_N.tga`
- `AlphaMapName2=M4A1_S_BornBeast_alpha.tga`
- `EnvCubeMapName2=Black_Shader03.dds`
- mapping enable switches and brightness/specular/refraction/reflection parameters.

These are direct config references, not proof of runtime technique selection or the meaning of the `2` suffix. The cube texture is not yet recovered by this nine-target experiment.

## N05-A review corrections

1. `scan_local_control_dtx()` passed only 64 bytes to a parser requiring a complete 164-byte LT2 header plus payload. A known valid synthetic file reproduces the false negative. The scanner now probes the version with 8 bytes and parses the full file only for plausible candidates. Two regression tests cover a valid DTX, a truncated lookalike and unsupported bytes.
2. The corrected scan still returns 0/3258 under the **old extracted** `data/rf017/ModelTextures` scope. This is not a negative over correctly routed installation resources. No old input was overwritten to make this result change.
3. The recovered 1024×1024 QV from `rez2/RF017.REZ` remains a valid positive; its two persisted PNGs also have identical RGBA pixels. It is a different copy from the 256×256 QV in main-index part 13. No load-order authority is asserted.
4. N05-A's `dtx_Create=True` is a Python port of structural gates, not execution of the upstream C++ tools. Synthetic quadrant checks do not establish all alpha or mip behavior.
5. Earlier whole-file RGB/FF phase measurements remain observations of their recorded SHA inputs. Those inputs were read from the wrong physical file for the tested indexed resources. They cannot be used to infer current native DTX/TGA/CFG semantics. Native CFG is not the previously proposed binary LUT, and these TGA files do not require inserted-header repair.

## Reproduce and validation

```powershell
python -B -m unittest discover -s tests -p test_n05a_control_scan.py -v
python -B -m unittest discover -s tests -p test_rez_verified_payload.py -v
python -B scripts/material_recovery/n05b_shard_material_recovery.py
```

On this host, Python is available at `C:\Users\Administrator\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe`.

Seven regression tests passed. The five payload tests cover a valid range in the wrong file, a part range beyond the main file, a normal unsplit file with a timestamp, an incorrect part hash, and ambiguous matching candidates. The recovery command verified 9/9 directory MD5 values and PV pixel agreement. Only metadata, parsed config and diagnostic PNGs are saved; raw client binaries and `data/**` are unchanged.

## Remaining work

The verified reader is currently used by the new material-recovery command. The old bulk extractor and CFRezManager archive read paths still assume payloads are in the main file; they must not regenerate final inputs until integration is complete. In particular, CFRezManager's main-file bounds check can discard valid part-backed entries before extraction. That is the next engineering task, with cache invalidation and sibling-part fixtures.

After integration, rebuild only a separate BornBeast staging set, verify model/UV provenance, resolve the named cube resource, and validate the CFG-to-shader mapping. P4 frozen outputs remain intact. This experiment does not claim native material PASS or deploy a new addon.
