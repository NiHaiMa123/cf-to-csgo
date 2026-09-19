# P0 file baseline — 2026-09-19

File integrity: **PASS only**. Runtime P0, actual loading identity, fixed scenes and visual acceptance: **PENDING**. Game is currently absent per user; no launch, deployment or game changes performed.

## Frozen experiment parent

`D:/project/cf_to_csgo/work/mauser_libra/material_rendering_fix/baseline/20260919T094033.420908Z_ef5ce185/addon_v2`

Grok generator must copy from this directory into its own experiment output; never edit the frozen parent.

Evidence root: `D:/project/cf_to_csgo/work/mauser_libra/material_rendering_fix/baseline/20260919T094033.420908Z_ef5ce185`

- `snapshot.json`: current input/source/report SHA-256, A/B/C records, reference image hashes, pre/post checks and pending runtime status.
- `material_snapshot.json`: six historical slot/region records, actual frozen VMT text/parameters and weapon VTF headers. Historical shader claims are preserved evidence, not newly validated conclusions.
- `raw_reports/`: unchanged copies of old reports, including the stale historical pak report; current verification is in `snapshot.json`.
- `sources/`: frozen capture script, material scripts/drivers and both plans.
- `references/current.png` and `references/target.png`: both supplied clipboard PNGs found and copied.
- `seal.json`: SHA-256/size inventory of 114 evidence files, independently rechecked with PowerShell; zero failures, all listed files read-only.

## Checks

| Check | Result |
| --- | --- |
| A staging vs B MIGI addon, exact inventory and SHA-256 | PASS 29/29 |
| A staging vs C VPK entries, size and SHA-256 | PASS 29/29 |
| C entry CRC32, including preload | PASS 29/29 |
| Frozen addon copy vs A | PASS 29/29 |
| A/B inventories, C tree and relevant slices, inputs/sources/reports pre/post | PASS |
| Historical input manifest SHA vs current inputs | PASS |
| Independent evidence seal verification | PASS 114/114 |

A: `D:/project/cf_to_csgo/work/mauser_libra/addon_v2`

B: `D:/steam/steamapps/common/csgo legacy/migi/csgo/addons/p_cf_mauser_libra_p1`

C: `D:/steam/steamapps/common/csgo legacy/migi/csgo/pak01_dir.vpk` and referenced archive slices.

VPK reading includes preload bytes, uses header size + tree size + entry offset for inline data, and uses entry offset for external archive data. Reads are chunked; huge archives are not loaded wholesale. The parser supports versions 1/2; execution validates the actual package, not every possible synthetic layout.

Executed with `C:/Users/Administrator/AppData/Local/Python/pythoncore-3.14-64/python.exe -B work/mauser_libra/material_rendering_fix/capture_baseline.py`; exit 0. Initial sandbox executable access was denied; authorized elevated execution succeeded.

Each run exclusively creates a new UTC timestamp/UUID directory, refuses output overwrite and symlink/reparse traversal, detects discrepancies and retains failed evidence with FAIL status. Sealing is application-level immutability plus read-only attributes and hashes, not OS-enforced WORM storage. Pre/post checks cannot prove absence of transient changes reverted between observations.

No FOV, position, model, hands, animation, original reports, other scripts, Git state or installed game files were modified. Full addon files are copied only to preserve the exact baseline.
