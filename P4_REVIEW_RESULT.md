# P4 Independent Review Result

> Reviewer: **Chat/Sol**
>
> Review date: 2026-08-20
>
> Implementation baseline: `10aa99b770e575300ca3c28324ef3de3d5b70c6b`
>
> RV-04 evidence commit: `fd61d6ae7567a01c585e1144e2cab88ddb6aa85d`

> **Historical applicability note (2026-08-21):** 本文件是 2026-08-20 P4 baseline 的历史最终 Review，不是当前执行入口。其 `PASS / FROZEN` 继续适用于 conversion/build/package/MIGI/runtime contract。2026-08-21 用户明确授权的 [`P4_M01_TASK_SPEC.md`](P4_M01_TASK_SPEC.md) 是一个 post-freeze native-material corrective task，用于补做当时未声明为已通过的 CF 原生材质 fidelity；它不追溯性撤销本 Review，也不受本文件“当时无需 reopen P4”措辞的禁止。当前状态只看 [`plan.md`](plan.md) 第 1 节。

## Final result

**`PASS WITH RISK`**

**P4 baseline may be marked `PASS / FROZEN`.**

At the time of this Review, no identified risk required reopening the reviewed conversion baseline before entering P5. The remaining items were explicit technical/provenance debt or out-of-scope runtime checks and must not be silently reclassified as solved.

## RV-01 — PASS

Scope/diff audit passed.

- P4 stabilization stayed on the Prototype pipeline, manifest, P4 build/work evidence and documentation.
- No final Leishen asset, P6 release builder, P7 visible Inspect retarget, CF sound or world-model scope was smuggled into the P4 Gate.
- `data/**` was not uploaded as Review evidence.
- Deploy evidence shows creation of the frozen/no-op addon rather than destructive overwrite of a different historical addon.

## RV-02 — PASS WITH NON-BLOCKING RISK

Manifest fields materially participate in execution or Gates:

- `cf_ltb_source` -> fresh CFRezManager export + input hash Gate;
- `mesh_map` / `mesh_bone_mapping` -> C1 expected groups, SMD binding and triangle/corner Gates;
- C3 alignment manifest / matrix policies -> fixed transform command + contract Gates;
- runtime modelname / sequences / attachments -> QC and post-build semantic Gates;
- material policy / Prototype flags -> validation/package policy Gates;
- output roots -> containment/destructive-operation guards;
- `inspect_policy` -> build policy default and frozen/no-op sequence generation.

Non-blocking risks:

1. CLI `--inspect-policy` can still explicitly override the manifest default; T05 does not independently assert `effective inspect policy == manifest inspect_policy`.
2. The manifest `toolchain` section contains some historical/provenance tools while `studiomdl`, Crowbar, VTFCmd and some helper paths are resolved by the pipeline and recorded in run evidence rather than being fully manifest-driven.

These do not invalidate the reviewed frozen artifact but should be tightened before claiming broader cross-weapon generality.

## RV-03 — PASS

Evidence chain is closed around:

`run_20260819_170013_270792`

Verified chain:

```text
local CF LTB
  -> B3
  -> C1
  -> C3
  -> Source build / Crowbar roundtrip
  -> validation
  -> package / staging
  -> deploy
  -> user changed-runtime Gate
```

Build, validation, package and deploy bind the same run identity and payload; package/staging/deployed payload hashes close. No evidence was found that the current build secretly used an old MIGI addon or old aligned OBJ instead of the fresh upstream run.

This chain did **not** establish that the visible material pixels were produced by a correct native CF material decode; that claim was outside the reviewed baseline and is now handled by P4-M01.

## RV-04 — PASS

New independent local execution was performed from the Chat/Sol-fixed protocol in `P4_RV04_TEST_SPECS.md`.

Evidence:

- `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_report.json`
- `work/m4a1_s_bornbeast/p4_prototype_01/rv04_chat_review_stdout.log`

All 4 required high-risk cases passed and hit the exact expected Gate:

1. output-root containment -> `manifest_contract` rejected unsafe `work` root;
2. sequence count preserved but name changed -> `sequence_names_and_count` rejected it;
3. Parent/Clip mesh-bone mapping semantics swapped -> `smd_manifest_bone_corners` rejected it;
4. critical VTF removed -> `material_closure` rejected it.

Each case exited non-zero for the target reason. The report records `case_count=4`, `passed_cases=4`, `pass=true`, and `critical_diff_from_base=false`.

Important: RV04-04 proved that Source material references reject a missing VTF. It did **not** prove the VTF's pixels or upstream CF material interpretation were semantically correct.

## RV-05 — PASS WITH NON-BLOCKING RISK

The user Gate is recorded without promoting untested claims:

- frozen/no-op Inspect has no visible motion by design;
- user confirmed no crash/obvious runtime error, state return, and continued Fire/Reload/Switch;
- visible Inspect retarget / hand penetration remains explicitly deferred to P7;
- `console_errors` remains `not_tested`;
- `rollback_after_disable` remains `not_tested`.

The latter two are retained as risk and were not part of the reduced changed-runtime P4 blocker set.

## Provenance note

Historical build/package reports record one byte-level manifest SHA while the later Windows working tree used for RV-04 records another. Git comparison shows the manifest itself did not change between the frozen implementation commit and Review baseline, and RV-04 reports no critical implementation diff. The most plausible cause is working-tree byte normalization such as EOL handling.

This does not invalidate the semantic frozen artifact, but future provenance tooling should prefer a canonical/normalized manifest hash (or record both Git blob identity and working-tree SHA-256) so cross-checkout line-ending differences cannot create ambiguity.

## RV-06 — FINAL HISTORICAL BASELINE RESULT

1. **Conclusion:** `PASS WITH RISK`
2. **Unmet blocker IDs:** none for the reviewed baseline
3. **Non-blocking risks at Review time:**
   - explicit CLI Inspect-policy override is not independently pinned by T05;
   - toolchain contract is not yet fully manifest-driven;
   - `console_errors` not separately user-tested;
   - addon-disable rollback not separately user-tested;
   - byte-level manifest hash portability should be normalized for future provenance.
4. **T08 user Gate:** satisfied for the defined frozen/no-op changed-runtime scope.
5. **Allow P4 baseline `PASS / FROZEN`:** **YES**.
6. **Historical next phase at 2026-08-20:** P5 final Leishen asset identification.
7. **2026-08-21 scoped correction:** native material fidelity is now explicitly handled by P4-M01 while the reviewed conversion baseline remains frozen.
