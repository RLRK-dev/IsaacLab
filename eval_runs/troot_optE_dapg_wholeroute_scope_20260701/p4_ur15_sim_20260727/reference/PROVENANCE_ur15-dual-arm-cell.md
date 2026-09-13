# Provenance — reference bundle `ur15-dual-arm-cell/` (20 files)

**Written** 2026-09-14 06:06 JST by w2:p4 RS-TECH-LEAD (Rs2). **Authority** = Rs1 (the human), answer to Q3 on 2026-09-14 06:00:22 JST: 「取り込む。検証がDownloadsやrepo外のコピーに依存する状態を解消します。コピー間の同一性を照合し、reference/へ一式を保存。コピー元・由来・各ファイルのSHA256を記録します。」 Custody = p4 transcript `ad899cc6-2451-4364-ba3c-910b67075aa4.jsonl` line 2361; recorded in `P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md` @ `236410dd84`.

## Why this copy exists
The mounting/pose reference for the UR15 dual-arm cell used to live only at `/home/rlrk/Downloads/ur15-dual-arm-cell/`, which is **absent** (measured 2026-09-13 22:07 and again at this writing). `ur15_mirror_acceptance.py:48-49` @ `38678f5946` still points there. The legs of the UR15-B controller chain (pZ R1, reference on-yoke poses) read the JSON from this directory instead.

## Sources compared (all outside git)
| # | path | file mtime (all 20 files) |
|---|---|---|
| 1 | `/home/rlrk/src/ur15-op010-cameras-20260906/inputs/UR15_monocular_camera_v01/source/ur15-dual-arm-cell/` | 2026-09-06 06:57 |
| 2 | `/home/rlrk/src/ur15-op020-connector-20260906/inputs/UR15_monocular_camera_v01/source/ur15-dual-arm-cell/` | 2026-09-06 06:57 |
| 3 | `/home/rlrk/src/ur15-op010-controller-clearance-20260906/inputs/UR15_monocular_camera_v01/source/ur15-dual-arm-cell/` | 2026-09-06 06:57 |
| 4 | `/home/rlrk/src/ur15-line-refinement-v3-20260906/handoff/UR15_CODEX_HANDOFF/working_v2/source/` | 2026-09-06 03:05 (json) |

- **Identity**: for each source, sha256 of every file by relative path, sorted → the four lists are **byte-identical** (20 files, 12,479,609 bytes each). Copied from source 1 with `cp -rp`; the copy's list equals all four.
- **Anchor to the original location**: `P5_UR15_CLIP_DETAIL_DESIGN_20260727.md` §22-1 (`:1605-1608`, introduced in `939fdb90b0` 2026-07-28) records sha256 of 4 files **measured at `~/Downloads/ur15-dual-arm-cell/`**: `ur15-dual-arm-cell.urdf` `7f6828df8e27…`, `.json` `20ac0935c707…`, `.md` `0783285b626e…`, `views/front.png` `da43d68b9a83…` — **all 4 match this copy**. ⚠ The other 16 files have no earlier recorded hash: they are shown identical across the four 09-06 copies, **not** shown identical to the 07-28 Downloads originals.
- The origin before `~/Downloads` is not recorded in git (the md file names the cell; who produced the bundle is not stated in it).

## Storage note
`.gitattributes` at the repo root routes `*.dae` through Git LFS; git-lfs is **not installed** on this machine and the repo holds 0 LFS files. So that the committed blob of every file equals its bytes (and `MANIFEST_ur15-dual-arm-cell.sha256` can be checked from git alone), `reference/.gitattributes` unsets the LFS filter for `*.dae` in this directory only.

## Files
`MANIFEST_ur15-dual-arm-cell.sha256` (sha256sum format, paths relative to `ur15-dual-arm-cell/`). Check: `cd ur15-dual-arm-cell && sha256sum -c ../MANIFEST_ur15-dual-arm-cell.sha256`.
