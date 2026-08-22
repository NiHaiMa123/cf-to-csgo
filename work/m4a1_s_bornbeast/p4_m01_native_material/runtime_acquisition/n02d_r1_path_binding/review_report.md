# P4-M01-N02-D-R2 — Review of N02-D-R1 Path-Aware REZ Binding

> Review-only task.  No code changes; this report records whether the
> N02-D-R1 evidence at commit `f468e96` clears each of the 6 review
> points from task.md §4, what facts can be frozen, and which
> material-closure gaps remain open.

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

### 2.1 Path normalization has a documented rule

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
in `path_binding_report.md` §1.

Verdict: **PASS** — the rule is fixed, the strip list is bounded, and
the REZ-side uppercase comparison is consistent with how the on-disk
`PLAYERVIEW/...`, `WEAPONS/...`, `RS/...` directories are named.

### 2.2 Virtual-root strip is limited to the proven pair

The script only strips `Models/` and `ModelTextures/`.  No other
leading segment is silently dropped.  `RS/` is explicitly kept because
it appears as a literal REZ subdir in `rf002.rez` (and was confirmed
against the on-disk NINJATRANSLUCENT/PVMODELDEFAULT entries).

Verdict: **PASS** — the strip is scoped to the two engine virtual
roots and is documented as such in the report.

### 2.3 Extensionless model path restricted to `.ltb`

`EXTENSIONLESS_MODEL_FIELDS = {"ModelFileName", "PViewModelFileName"}`
gates the `.LTB` suffix pass.  No other extension is attempted for
extensionless values — the report explicitly disclaims the
`.dtx/.tga/.lto/.ltc/.rez/.dat` fallback that the rejected N02-D had
been using.

10 of the 10 extensionless `PViewModelFileName` records (one per
WeaponName) resolve to a single full-path match.  No archive
ambiguity arose in this class.

Verdict: **PASS** — the rule is correct and produces 10/10 unique
single-archive `.LTB` resolutions.

### 2.4 Multiple-archive paths are fully retained

The single ambiguous case is `M4A1-S SkinFileName`:
`WEAPONS/L-M4A1_SILENCER_CAMO.DTX`.

| archive | name | size | catalog MD5 |
|---|---|---|---|
| `rez/rf017.rez` | `L-M4A1_SILENCER_CAMO.DTX` | 32,932 | `56498E817DA6ED661D6D3B5098974F79` |
| `rez2/RF017.REZ` | `L-M4A1_SILENCER_CAMO.DTX` | 32,932 | `92A6162F9381436C72320E4874B3E104` |

Both hits are reported.  The script does NOT declare either archive
authoritative.  The two catalog MD5s differ, so the two REZ may
contain different byte content; this is left as a future bounded
payload SHA target.

Verdict: **PASS** — ambiguity is explicit, no authoritative
selection is claimed.

### 2.5 Exact binding count vs unresolved count

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

Verdict: **PASS** — 60/60 unique pairs are full-path bound; 0
unresolved; the 49+10+1 sum is internally consistent.

### 2.6 Material-binding closure gap

N02-D-R1 only proves **runtime artifact existence for the
bf005-bound paths**.  The following gaps remain open and are NOT
remediated by this round:

```text
1. LTB mesh/piece -> DTX/RS material binding  OPEN_UNRESOLVED
   The M4A1 family LTB files are confirmed to exist in REZ,
   but the LTB-internal piece/texture indices and render-style
   contract are not yet decoded (Jupiter reference exists, no
   runtime closure).

2. BornBeast identity                          NOT_FOUND_IN_BF005
   The bf005 M4A1 family records bind only to base/silencer
   skins; BornBeast-named resources (e.g. PV-M4A1_S_BornBeast)
   exist in REZ but are not referenced by any bf005 Weapon
   record.  This is a BOUNDED negative; BornBeast is a
   variant family, not a bf005 weapon.

3. DTX/TGA pixel semantics                     OPEN_UNRESOLVED
   L-M4A1.DTX existence is confirmed but the actual
   pixel content vs. CF engine expectation is not verified.

4. RenderStyle semantic closure                OPEN_UNRESOLVED
   NINJATRANSLUCENT.LTB / PVMODELDEFAULT.LTB exist in
   rf002.rez under RS/ but the render-style consumer
   semantics are not yet bound to a runtime behaviour.
```

Verdict: **PASS for N02-D-R1's scope**; the closure gap is
explicitly **not** claimed to be closed by this round.

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
```

The following are NOT frozen by this round (carry forward as
`OPEN_UNRESOLVED` or `NOT_FOUND_IN_BF005`):

```text
- LTB mesh/piece -> DTX/RS internal binding
- DTX/TGA pixel semantics
- RenderStyle (RS/*.LTB) consumer semantics
- BornBeast identity confirmation
- Any statement about P4-M01 PASS or P5 identity
```

## 4. Remaining blockers (carried into next round)

| blocker | grade | scope |
|---|---|---|
| LTB piece->material binding | `OPEN_UNRESOLVED` | needs LTB format decode + Jupiter reference + current CF runtime cross-check |
| BornBeast identity | `NOT_FOUND_IN_BF005` (bounded) | BornBeast is a variant; the bf005 path-binding closure for the M4A1 family does NOT name BornBeast |
| DTX/TGA pixel semantics | `OPEN_UNRESOLVED` | need DTX decode + runtime cross-check |
| RS semantic closure | `OPEN_UNRESOLVED` | need RS LTB decode + consumer trace |

## 5. Next single highest-value target

**Bounded payload SHA verification of N02-D-R1's exact-path entries.**

Rationale:

- N02-D-R1 now gives correct exact-path candidates (60 unique
  `(WeaponName, field)` pairs).
- The previous N02-E (`2f94db9`) was marked
  `REVIEW_REWORK_REQUIRED` because it inherited N02-D's
  basename-over-broad path selector.  With the rework in place,
  N02-E can be re-run against the correct entries.
- The bounded-payload rule (read only `data_offset..data_offset+size`
  bytes per hit, hash, compare to P4 source) is exactly the
  smallest next step that converts the path-binding closure into a
  byte-content closure.
- It directly answers: **does the M4A1 family's LTB in REZ equal
  the P4 BornBeast source LTB by SHA?**  If yes, BornBeast identity
  for at least one M4A1 sub-skin is closed; if no, the gap between
  bf005 M4A1 paths and the BornBeast variant is closed structurally.

The bounded read stays within task.md §5/§8 rules (no full REZ
extraction, no payload bulk, no shader / EXE reverse).  It is the
direct continuation of N02-D-R1 and avoids the explicit P5 / P4-M01
PASS scope rules.

## 6. Scope guard

- read the on-disk N02-D-R1 evidence files only; no source-code change
- did NOT modify `plan.md` (planner will do the freeze)
- did NOT modify `task.md` (planner writes the next round)
- did NOT enter P5 identity confirmation
- did NOT announce P4-M01 PASS
- did NOT decompile / strings / xref any EXE / DLL
- did NOT reverse any FXO shader
- did NOT run any CF client / runtime binary
- did NOT extract any REZ payload bytes
- did NOT use filename similarity as proof
- did NOT continue a previously rejected corpus scan

## 7. Completion state

- **status**: `A. N02-D-R1 ACCEPTED / COMPLETE`
- 60/60 unique `(WeaponName, field)` binding pairs are full-path
  bound in the current CF runtime REZ set
- no path-evidence failures; 6/6 review points PASS
- the closure gap above the path layer is carried forward explicitly
- planner should freeze the candidates in §3 into `plan.md` and
  author the next bounded-payload-SHA round (likely a reworked
  N02-E that consumes the N02-D-R1 entries as its only input)
