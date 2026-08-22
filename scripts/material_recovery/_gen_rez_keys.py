#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate rez_keys.py from the canonical C# RezCrypto.cs in this repo.

Run once at build time; the resulting rez_keys.py is a tiny module that
exposes REZ_KEYS as a 1024-byte literal, matching the C# source byte-for-
byte.
"""
import os
import re
import sys

CS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "CFRezManager", "Archives", "RezCrypto.cs",
)
OUT_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "rez_keys.py",
)


def main():
    with open(CS_PATH, "r", encoding="utf-8") as f:
        src = f.read()
    # find the array literal between [ and ]
    m = re.search(r"private static readonly byte\[\] Keys\s*=\s*\[(.*?)\];", src, re.S)
    if not m:
        print("Keys literal not found", file=sys.stderr)
        sys.exit(1)
    body = m.group(1)
    # Match the full 0xNN literal; the captured substring already includes
    # the 0x prefix, so we use it verbatim below.
    nums = re.findall(r"0x[0-9A-Fa-f]{2}", body)
    n = len(nums)
    joined = ", ".join(nums)
    py = (
        "# -*- coding: utf-8 -*-\n"
        "# AUTO-GENERATED from CFRezManager/Archives/RezCrypto.cs by\n"
        "# scripts/material_recovery/_gen_rez_keys.py — do not edit by hand.\n"
        f"REZ_KEYS = bytes([{joined}])\n"
        f"# C# source length: {n}\n"
    )
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        f.write(py)
    print(f"wrote {OUT_PATH} with {n} keys", file=sys.stderr)


if __name__ == "__main__":
    main()
