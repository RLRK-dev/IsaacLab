# pZ — independent collation of the reference bundle `p4_ur15_sim_20260727/reference/` (Rs1 Q3, m-p18-353)

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-16 17:50 JST. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**. Rs1's word (custody p4 transcript :2361, 2026-09-14 06:00:22 JST, relayed m-p18-353): 「取り込む。」— collate the copies, keep one set under `reference/`, record origin and per-file SHA256. p4 did the import at `e6172b2e3b` (23 files, +2,280); this is the verifier's independent check, every number re-measured here.

| # | check | result |
|---|---|---|
| 1 | manifest | `MANIFEST_ur15-dual-arm-cell.sha256` (sha256 `3e7c1ce62cb78ae0da49b0ce2f5f3e5d9afa0adbfed49b0a1f6f39dec862d89f`, 20 lines, `sha256sum` format, paths relative to `ur15-dual-arm-cell/`): `sha256sum -c` from that directory → **20 OK, 0 failed**; the directory holds exactly **20 files, 12,479,609 bytes** |
| 2 | blob == bytes | every tracked file under `reference/` (23 = 20 + manifest + provenance + `.gitattributes`): `git show e6172b2e3b:<f>` sha256 == on-disk sha256, **23/23**; `HEAD:reference/` tree id == `e6172b2e3b:reference/` (unchanged since) |
| 3 | LFS bypass | root `.gitattributes:5` routes `*.dae` to LFS; `reference/.gitattributes:1` = `*.dae -filter -diff` → `git check-attr` on `meshes/base.dae`: filter **unset**; `git lfs` is not installed; blob size 353,221 == file size ⇒ the `.dae` blobs are the bytes, not pointers |
| 4 | the four sources in PROVENANCE | per-file sha256 by relative path, sorted, hashed as a list: `reference/ur15-dual-arm-cell/` = `4ebfa0f4c29c6fbb…`; sources 1-3 (`~/src/ur15-op010-cameras-…`, `ur15-op020-connector-…`, `ur15-op010-controller-clearance-…/…/source/ur15-dual-arm-cell`) and source 4 (`ur15-line-refinement-v3-20260906/handoff/UR15_CODEX_HANDOFF/working_v2/source`) → **all four IDENTICAL** (20 files, 12,479,609 bytes each) |
| 5 | anchor to the original `~/Downloads` location | `~/Downloads/ur15-dual-arm-cell/` is **absent** today (measured). `P5_UR15_CLIP_DETAIL_DESIGN_20260727.md:1605-1608` @ `939fdb90b0` records four sha256 measured there on 07-28 (`.urdf` `7f6828df…`, `.json` `20ac0935…`, `.md` `0783285b…`, `views/front.png` `da43d68b…`) → **all four present in the copy** with those exact hashes |
| 6 | tie to this desk's own pins | the copy's `ur15-dual-arm-cell.json` sha256 = `20ac0935c707757c35a974f4c7adc9b9412ed18a04905f06b34dc76affa3990d` = the JSON this desk read on 08-10 (`PZ_ARM_MIRROR_LEG_RESULT_20260810.md` B1/B2 @ `cf0a14cea3`, cited by v3 R1) ⇒ the 08-10 arm-mirror re-derivation and the reference cell's exact mirror (0.0000 mm, 24 poses) were computed on **these bytes** |

## Observation (recorded, not judged; owner p0 / disposition p4)
`ur15_mirror_acceptance.py:49-50` at HEAD still reads `REF_DIR = Path("/home/rlrk/Downloads/ur15-dual-arm-cell")` — an absent path — so the 07-29 acceptance instrument cannot run today as committed; repointing it to `reference/` is a one-line code change that needs its own word (v3 R1 "copy は p4 へ提案" is now satisfied on the data side only). The 08-10 isolated re-run happened while `~/Downloads` still existed.

## Disposition of the other two items in m-p18-353 (pZ)
- **D4 leg (`cb787871f0`) + R3 (`98d8e63173`)**: run when p0 lands D4. At writing, commits touching the driver after `22feba17a6` = **0** (HEAD `5762f891b8`); the working-tree driver is still the 09-07 uncommitted set — not an object.
- **R0 and the B line**: pre-registered after p11's spec lands in v3 (latest `8f70edad4e`, 224 lines, no R0 「収束のみ」 wording nor a B-line field spec yet). R0 will be reported as convergence only, never as collision / grasp / dynamic tracking (Rs1 Q1). Per supplement a, every leg of mine reports an **instrument stop** separately from a **controller failure**; per supplement b, "fix landed" and "accepted after verification" are separate lines.

## Provenance
`sha256sum`, `git show`/`ls-tree`/`rev-parse`/`check-attr`/`cat-file -s`, `find` over the four source directories, P5 lines read from the blob at `939fdb90b0`. Zero tracked-content modifications by pZ. Committed by pZ under the standing custody form (m-p18-344), pathspec-limited, --no-verify, no push.
