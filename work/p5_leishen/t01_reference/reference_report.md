# P5-T01 Official Reference Evidence

## Result

`CONFIRMED` — the user confirmed that the official reference shown is **M4A1-雷神**.

## Official identity

- Display name: `M4A1-雷神`
- Item id: `2010044601`
- Official detail page: <https://cf.qq.com/cp/a20250701wqbk/page.html?itemid=2010044601>
- Actual image loaded by the official detail record: <https://mcdn.gtimg.com/bbcdn/cf/serial/C0457.png>
- CDN response: HTTP 200, `image/png`, 125896 bytes

The official list and detail API records both bind item `2010044601` to `M4A1-雷神` and `C0457.png`; the page's image prefix is `https://mcdn.gtimg.com/bbcdn/cf/serial/`. The detail description identifies the silver M4A1 with blue lightning motif.

## Search and provenance

The three mandatory official queries were attempted. Because the search index did not expose the weapon detail directly, the official page configuration and its official list/detail APIs were inspected to recover the exact record and image URL. The user confirmation is recorded in `official_reference.json` at `2026-08-21T00:20:27.5509734+08:00`.

The confirming browser inspection also observed the rendered `#weapon-name` value `M4A1-雷神` and the page's actual loaded `C0457.png` image resource.

No generated image and no third-party MOD image was used. This file is only the reference identity gate; it does not identify a local LTB/DTX candidate.
