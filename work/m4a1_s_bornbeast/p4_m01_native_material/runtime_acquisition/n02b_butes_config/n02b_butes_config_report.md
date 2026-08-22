# P4-M01-N02-B — LTC decoder validation & Bute semantic correlation

- generated_at: `2026-08-22T14:13:31.104065+00:00`
- status: **CF_LTC_VARIANT_CONFIRMED**
- script: `scripts\material_recovery\n02_butes_config_triage.py`

## 1. Decoder under test

- source: `CFRezManager/Decoders/LithTech/LithTechLtcNativeDecoder.cs`
- ported 1:1 to Python in this script (no behaviour change).
- decoder requires first 4 input bytes == `00 00 00 00`.
- decoder constants: `WINDOW_SIZE=4096`, `MIN_MATCH_LEN=2`, `HEADER_BYTES=4`, `MAX_DECODED=268435456`

## 2. Sample coverage

- total samples enumerated: **78**
- all samples are read from `D:\Program Files\CF(2)` (cf_default)

### By status

| status | count |
|---|---|
| `FAILED` | 78 |

### By first-4-byte magic

| magic | count |
|---|---|
| `5483b2e1` | 73 |
| `0d0a5265` | 4 |
| `c7004400` | 1 |

### By failure mode

| failure_mode | count |
|---|---|
| `LtcHeaderInvalid (expected 00 00 00 00)` | 78 |

## 3. Verdict on existing decoder

The C# LithTechLtcNativeDecoder requires first-4 bytes == 00 00 00 00. All 73 rez/Butes/*.ltc share magic 5483b2e1, and the rez/bf000.lta sample uses magic c7004400ffff0000. The 4 rez/Worlds/*.lta have a 100-byte ASCII header + binary body. No sample satisfies the decoder precondition, so the decoder is incompatible with the current CF runtime's Bute/LTA wire format. This is a confirmed LTC variant, not a decoder bug.

## 4. bf000.lta vs bf*.ltc relationship

- `rez/bf000.lta` magic = `c7004400`
- `bf*.ltc` shared magic = `5483b2e1`
- `bf*.ltc` count = **35**; size range = 56 .. 81283 bytes
- magic differential = **True** (the two formats are *not* the same wire format)
- without a working decoder for either format, no shared tag/key/grammar comparison is possible — filename prefix is the only signal, and filename similarity is explicitly **not** a binding proof per task.md §4.

## 5. Bute/LTA grammar verdict

- total decoded: `0`
- total parsed as Bute grammar: `0`
- parsed list is empty because the decoder returned 0 successful decodes.

## 6. Target / resource correlation

Scope reused from existing evidence only (BornBeast / Transformers / Jewelry / BlueDiamond).

| family | binding_evidence_count | reason |
|---|---|---|
| `BornBeast` | 0 | decoder could not produce Bute-parseable output for any rez/Butes/*.ltc |
| `Transformers` | 0 | decoder could not produce Bute-parseable output for any rez/Butes/*.ltc |
| `Jewelry` | 0 | decoder could not produce Bute-parseable output for any rez/Butes/*.ltc |
| `BlueDiamond` | 0 | decoder could not produce Bute-parseable output for any rez/Butes/*.ltc |

## 7. Recommended next single consumer

CF_LTC_VARIANT_CONFIRMED: the real Bute/LTC wire format is not the format the C# decoder implements. The single highest-value next consumer is the CF game DLL that loads bute configs at runtime — specifically crossfireBase.dll and server.dll. Targeted strings / xref on these two DLLs is the only way to recover the real LTC header and bitstream. EXE / broad decompile is explicitly out of scope per task.md §6.

## 8. Scope guard

- did not re-scan `data/**`;
- did not execute any CF binary, no anti-cheat bypass, no memory dump;
- did not decompile any EXE/DLL this round;
- did not touch FXO shaders;
- did not unpack large REZ as main task;
- did not modify `plan.md`;
- did not rewrite or fork the C# decoder without evidence (per task.md §5 / §8).
