# Third-party components

This directory is reserved for tools that are required by a reproducible build
but are not part of the repository's own source code.

## LTB conversion tools

`ltb2lta_v2.4/` is an intentionally empty staging/registration directory.
No converter executable is currently vendored. The reproducible B2 path is the
native `CFRezManager --inspect-ltb` decoder, so a missing external converter does
not block the geometry, skin-index, skeleton, or bind-pose checks.

If a legally redistributable converter is added later, keep its files isolated
in the versioned directory and add a manifest containing:

- exact version and download/source URL;
- SHA-256 for every executable/archive;
- license/redistribution status;
- a command-line smoke test and representative output report.

Do not copy third-party binaries into `data/`, `build/`, the Steam directory, or
the MIGI addon. Deployment outputs belong under the dedicated staging paths.
