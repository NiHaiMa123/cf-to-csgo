#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""N01 Phase-0 gate self-check: verify consistency requirements."""
import json
import hashlib
import os

REPO = r"D:\project\cf_to_csgo"
R1 = os.path.join(REPO, "work/m4a1_s_bornbeast/p4_m01_native_material/r1")


def load(name):
    with open(os.path.join(R1, name), encoding="utf-8") as f:
        return json.load(f)


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


ok = True


def check(label, cond, detail=""):
    global ok
    status = "PASS" if cond else "FAIL"
    if not cond:
        ok = False
    print(f"[{status}] {label} {detail}")


# 0.1 CFG phase-origin formula arithmetic
cfg = load("cfg_reverse_r1.json")
for name in ("M4A1_S_BornBeast", "M4A1_S_Transformers", "M4A1_S_Jewelry"):
    pa = cfg["primary_accounting"][name]
    ap = pa["phase_origin"]
    n = pa["size_bytes"]
    first = ap["first_varying_offset"]
    cnt = ap["sample_count_complete"]
    trail = ap["trailing_bytes_after_last_sample"]
    lhs = first + (cnt - 1) * 3 + 1 + trail
    check(f"0.1 {name} span identity", lhs == n, f"{lhs} == {n}")
    check(f"0.1 {name} no record-size identity", "*3 +" not in ap["identity"].split("+", 1)[1].split("(")[0] or "(cnt" in ap["identity"] or f"({cnt}-1)*3" in ap["identity"], ap["identity"])

# 0.2 DTX wording
dtx = load("dtx_revalidation_r1.json")
grade = dtx["evidence_grade"]["row_stride_1024"]
check("0.2 no '>3x margin' claim", ">3x" not in json.dumps(dtx))
ndsm = dtx["width_scan_committed"].get("nearest_distinct_stride_margin")
check("0.2 nearest non-multiple stride ratio ~2.55x (2044)",
      ndsm is not None and 2.3 < ndsm["ratio_vs_winner"] < 2.8, str(ndsm))
check("0.2 dominant statistic wording", "1043/1046" in json.dumps(dtx) and "NOT universal" in json.dumps(dtx))
check("0.2 stride still STRONG_HYPOTHESIS", grade.startswith("STRONG_HYPOTHESIS"))

# 0.3 shader report metadata
sh = load("shader_hypotheses_r1.json")
h1 = sh["hypotheses"]["H1_base_flat"]
p = os.path.join(REPO, h1["preview"].replace("/", "\\"))
check("0.3 H1 preview path exists", os.path.exists(p), h1["preview"])
if os.path.exists(p):
    check("0.3 H1 preview SHA matches", sha(p) == h1["preview_sha256"])
check("0.3 H1 evidence class downgraded", "VERIFIED_DECODE_ONLY" not in h1["evidence_class"]
      and "HYPOTHESIS" in h1["evidence_class"] and "DIAGNOSTIC_LAYER_RENDER" in h1["evidence_class"],
      h1["evidence_class"])

# stale wording scan across scripts (excluding historical citations inside
# continuation_review_reason / supersedes notes, which legitimately quote old
# wording to document why it was corrected)
stale_terms = ["BGR24, width 1024", "stride-3 scalar strip", "every non-empty PV DTX",
               "anywhere in local data"]


def strip_history(src: str) -> str:
    out = []
    for line in src.splitlines():
        if any(k in line for k in ("continuation_review_reason", "supersedes",
                                   "v2's negative result", "universal 'every")):
            continue
        out.append(line)
    return "\n".join(out)


for script in ("r1_shader_closure.py", "r1_dtx_revalidate.py", "r1_stage2_binding.py",
               "r1_cfg_reverse.py"):
    src = open(os.path.join(REPO, "scripts/material_recovery", script), encoding="utf-8").read()
    body = strip_history(src)
    for t in stale_terms:
        check(f"0.x {script} free of '{t}'", t not in body)

# report JSONs must not carry the stale claims outside review_reason fields
def strip_reasons(obj_str: str) -> str:
    lines = [ln for ln in obj_str.splitlines()
             if not any(k in ln for k in ("review_reason", "supersedes", "note"))]
    return "\n".join(lines)


for jname, terms in (("cfg_reverse_r1.json", ["head_partial_bytes"]),
                     ("dtx_revalidation_r1.json", [">3x"]),
                     ("native_material_closure_r1.json", ["every non-empty", "492=2+163"])):
    txt = open(os.path.join(R1, jname), encoding="utf-8").read()
    body = strip_reasons(txt)
    for t in terms:
        check(f"0.5 {jname} free of '{t}' outside reason fields", t not in body)

# 0.5 closure alignment
clo = load("native_material_closure_r1.json")
kf = " ".join(clo["key_findings_targeted_rework"])
check("0.5 closure keeps 1043/1046 dominant-statistic framing",
      "1043/1046" in kf and "NOT universal" in kf)
check("0.5 closure dropped exact CFG framing claim", "492=2+163" not in kf)
check("0.5 closure keeps CONTINUE state",
      clo["recommended_state"].startswith("CONTINUE"))

print()
print("PHASE 0 GATE:", "PASS" if ok else "FAIL")
