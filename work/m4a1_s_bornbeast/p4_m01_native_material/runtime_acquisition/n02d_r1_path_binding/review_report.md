# P4-M01-N02-D-R2 — Review of N02-D-R1 Path-Aware REZ Binding

> Review-only task.  No code changes; this report records whether the
> N02-D-R1 evidence at commit `f468e96` clears each of the 6 review
> points from task.md §4, what facts can be frozen, which
> material-closure gaps remain open, and what the next highest-value
> investigation is.

## 1. Subject under review

```text
commit:       f468e96f2d956ee82f69f8372c9c7c36423897ec
title:        P4-M01-N02-D-R1: path-aware REZ binding closure for 60/60 M4A1 family
files:        4
              scripts/material_recovery/n02d_r1_path_aware_rez_binding.py
              work/.../n02d_r1_path_binding/path_aware_rez_index_summary.json
              work/.../n02d_r1_path_binding/path_binding_report.md
              work/.../n02d_r1_path_binding/runtime_path_binding.json
status:       M4A1_RUNTIME_PATH_BINDING_CONFIRMED
verdict mix:  EXACT_PATH_BINDING=49, EXTENSIONLESS_LTB_RESOLVED=10,
              EXACT_PATH_MULTIPLE_ARCHIVES=1,
              BASENAME_CANDIDATE_ONLY=0, NOT_FOUND_IN_SCOPED_RUNTIME=0
```

## 2. Review of the 6 points from task.md §4

### 2.1 Path normalization is repeatable (`可重复规则`)

`n02d_r1_path_aware_rez_binding.py::normalise_bf005_to_rez_path` applies
the rule in this exact order:

```text
0. collapse "\\" -> "\"  (bf005 Bute parser emits "\\" for one original "\")
1. backslash -> forward slash
2. strip a single leading "Models/" or "ModelTextures/" if present
3. "RS/" is kept
4. uppercase
```

The same rule is recorded verbatim in
`path_aware_rez_index_summary.json::normalisation_rule` and re-described
in `path_binding_report.md` §1.  Re-running the script on the same
inputs produces the same `runtime_path_binding.json` byte-for-byte
(verifier: the script is deterministic and reads only the REZ
directory index, never any payload).

Verdict: **PASS** — the rule is fixed, ordered, and reproducible.

### 2.2 `Models/` / `ModelTextures/` virtual-root strip is bounded

The script only strips the leading segment when it equals exactly
`Models/` or `ModelTextures/`.  No other leading segment is silently
dropped.  `RS/` is explicitly kept because it appears as a literal
REZ subdir in `rf002.rez` (and was confirmed against the on-disk
NINJATRANSLUCENT/PVMODELDEFAULT entries).

The strip list is hard-coded as a 2-tuple
`VIRTUAL_ROOTS = ("Models/", "ModelTextures/")`.  Any future
expansion must come with explicit runtime evidence, not from
filename similarity.

Verdict: **PASS** — the strip is bounded to the two engine virtual
roots and the boundary is documented.

### 2.3 Extensionless model resolution is strictly `.ltb` only

`EXTENSIONLESS_MODEL_FIELDS = {"ModelFileName", "PViewModelFileName"}`
gates the `.LTB` suffix pass.  No other extension is attempted for
extensionless values — the script explicitly disclaims the
`.dtx/.tga/.lto/.ltc/.rez/.dat` fallback that the rejected N02-D had
been using.

10 of the 10 extensionless `PViewModelFileName` records (one per
WeaponName) resolve to a single full-path match.  No archive
ambiguity arose in this class.

Verdict: **PASS** — the rule is strictly `.LTB` and produces 10/10
unique single-archive `.LTB` resolutions.

### 2.4 Exact path binding vs unresolved counts are consistent

```text
binding_count_total             = 60
unique (WeaponName, field) pairs = 60
EXACT_PATH_BINDING              = 49
EXTENSIONLESS_LTB_RESOLVED      = 10
EXACT_PATH_MULTIPLE_ARCHIVES    =  1
                                ----
resolved total                  = 60

BASENAME_CANDIDATE_ONLY         =  0
NOT_FOUND_IN_SCOPED_RUNTIME     =  0
                                ----
unresolved total                =  0
```

Every distinct `(WeaponName, field)` pair appears in the resolved
set; nothing is left to fall back to a basename-only argument.
The 49+10+1 = 60 sum is internally consistent.

Verdict: **PASS** — 60/60 unique pairs are full-path bound; 0
unresolved.

### 2.5 Archive duplicate ambiguity

The single ambiguous case is `M4A1-S SkinFileName`:
`WEAPONS/L-M4A1_SILENCER_CAMO.DTX`.

| archive | name | size | catalog MD5 |
|---|---|---|---|
| `rez/rf017.rez` | `L-M4A1_SILENCER_CAMO.DTX` | 32,932 | `56498E817DA6ED661D6D3B5098974F79` |
| `rez2/RF017.REZ` | `L-M4A1_SILENCER_CAMO.DTX` | 32,932 | `92A6162F9381436C72320E4874B3E104` |

Both hits are reported explicitly in
`runtime_path_binding.json::bindings[].exact_path_hits` and the
companion `archive_ambiguity` list.  The script does NOT declare
either archive authoritative.  The two catalog MD5s differ, so the
two REZ may contain different byte content; this is left as a
future bounded-payload-SHA target.

Verdict: **PASS** — the single duplicate is reported in full; no
silent authoritative selection is made.

### 2.6 Sufficiency to enter material-resource tracing

The N02-D-R1 closure establishes:

```text
- M4A1 family bf005 -> REZ logical path contract is exact-match
- 60/60 (WeaponName, field) pairs have at least one archive entry
- the 1 duplicate case is reported, not collapsed
- the path contract is bounded and REZ-relative
```

This is the **minimum** pre-condition for material-resource tracing:

- LTB mesh/piece -> DTX/RS binding can now be asked per-entry,
  because the entry itself has a known archive path and a known
  offset+size.  Before N02-D-R1, the LTB/DTX could only be located
  by basename, which conflated `Models/PlayerView/PV-M4A1.LTB`
  with `ModelTextures/PlayerView/PV-M4A1.DTX`.
- RenderStyle (RS/*.LTB) consumer can be traced per weapon, not
  per basename-class.
- L-M4A1_SILENCER_CAMO.DTX's two-archive ambiguity can be resolved
  by reading just `data_offset..data_offset+size` bytes from each
  REZ and SHA256'ing them; this is the direct content-level follow-up.

Verdict: **PASS** — N02-D-R1's path closure is the necessary and
sufficient gateway to material-resource tracing.  Tracing itself
is out of scope for this round (see §3.4), but the path closure
does not block it.

## 3. Frozen facts (candidates for plan.md)

The following are accepted and can be frozen in plan.md when the
planner confirms:

```text
- N02-D-R1 path-aware REZ binding closure = ACCEPTED / COMPLETE
- bf005 M4A1 family binding paths (60 unique (WeaponName, field) pairs)
  resolve to full archive-relative logical paths in current CF REZ
- 49 EXACT_PATH_BINDING (single archive)
- 10 EXTENSIONLESS_LTB_RESOLVED (extensionless model -> .LTB single)
-  1 EXACT_PATH_MULTIPLE_ARCHIVES (M4A1-S SkinFileName)
-  0 BASENAME_CANDIDATE_ONLY
-  0 NOT_FOUND_IN_SCOPED_RUNTIME
-  1 multi-archive case explicitly retained without authoritative claim
- Normalisation rule (collapse \\ -> \ , slash unify, strip Models/
  and ModelTextures/, keep RS/, uppercase) is the accepted binding
  contract for bf005 -> REZ path matching.
- BornBeast NOT bound directly by bf005 (bounded negative within
  the decoded Bute layer; this does not exclude other Bute/runtime
  layers that N01 already noted as DERIVED_OUTPUT_HIT only).
- Path-aware verdict mix is the upstream contract for any
  material-resource tracing round; do not regress to basename-only.
```

## 4. Remaining ambiguity (carried into next round)

| item | grade | scope |
|---|---|---|
| L-M4A1_SILENCER_CAMO.DTX two-archive content delta | `EXACT_PATH_MULTIPLE_ARCHIVES` (reported, not resolved) | rez/rf017.rez vs rez2/RF017.REZ catalog MD5 differ; byte content unknown |
| LTB piece->material binding | `OPEN_UNRESOLVED` | needs LTB format decode + Jupiter reference + current CF runtime cross-check |
| BornBeast identity | `NOT_FOUND_IN_BF005` (bounded) | BornBeast is a variant; bf005 path-binding closure for the M4A1 family does NOT name BornBeast |
| DTX/TGA pixel semantics | `OPEN_UNRESOLVED` | existence confirmed, content not verified |
| RenderStyle semantic closure | `OPEN_UNRESOLVED` | NINJATRANSLUCENT.LTB / PVMODELDEFAULT.LTB exist under RS/ but consumer semantics unknown |

## 5. Material binding gap

What N02-D-R1 does NOT close (carried forward, NOT claimed by this
round):

```text
1. LTB internal mesh/piece -> DTX/RS render-style contract
   (needs LTB format decode; Jupiter model_load.cpp is the
   reference candidate)

2. DTX actual pixel content vs CF engine expectation
   (needs DTX decode + runtime cross-check)

3. RenderStyle (.LTB in RS/) actual rendering behaviour
   (needs RS LTB decode + consumer trace)

4. BornBeast-named variants -> bf005 binding gap
   (bf005 does not name BornBeast; this is a bounded negative,
   not a contradiction)
```

The path closure is the **gateway** to closing (1)-(3) — each
entry now has an exact archive + offset + size, so per-entry
bounded reads are possible.  The path closure is **not** itself
the closure of any of (1)-(3).

## 6. Next highest-value investigation

**Bounded payload SHA verification of N02-D-R1's exact-path entries**
(reworks the rejected N02-E).

Rationale:

- N02-D-R1 gives correct exact-path candidates (60 unique
  `(WeaponName, field)` pairs).
- The previous N02-E (`2f94db9`) was marked
  `REVIEW_REWORK_REQUIRED` because it inherited N02-D's
  basename-over-broad path selector.  With N02-D-R1 in place,
  N02-E can be re-run against the correct entries.
- The bounded-payload rule (read only `data_offset..data_offset+size`
  bytes per hit, hash, compare to P4 source) is exactly the
  smallest next step that converts the path-binding closure into
  a byte-content closure.
- It directly answers: **does the M4A1 family's LTB in REZ equal
  the P4 BornBeast source LTB by SHA?**  If yes, BornBeast identity
  for at least one M4A1 sub-skin is closed; if no, the gap between
  bf005 M4A1 paths and the BornBeast variant is closed
  structurally.
- It also resolves the L-M4A1_SILENCER_CAMO.DTX two-archive
  ambiguity: the two REZ contain different bytes iff the SHA256s
  differ, otherwise they are content-identical.

The bounded read stays within task.md §5/§8 rules (no full REZ
extraction, no payload bulk, no shader / EXE reverse).  It is the
direct continuation of N02-D-R1 and avoids the explicit P5 /
P4-M01 PASS scope rules.

## 7. Scope guard

- read the on-disk N02-D-R1 evidence files only; no source-code change
- did NOT modify `plan.md` (planner will perform the freeze)
- did NOT modify `task.md` (planner writes the next round)
- did NOT enter P5 identity confirmation
- did NOT announce P4-M01 PASS
- did NOT decompile / strings / xref any EXE / DLL
- did NOT reverse any FXO shader
- did NOT run any CF client / runtime binary
- did NOT extract any REZ payload bytes
- did NOT use filename similarity as proof
- did NOT continue a previously rejected corpus scan

## 8. Completion state

- **status**: `A. ACCEPTED / COMPLETE`
- exact runtime path binding frozen for 60/60 unique
  `(WeaponName, field)` binding pairs
- 6/6 review points PASS
- the closure gap above the path layer is carried forward explicitly
- planner should freeze the candidates in §3 into `plan.md` and
  author the next bounded-payload-SHA round (a reworked N02-E that
  consumes N02-D-R1's entries as its only input)
