# pZ — verdict on the four mounting C-2 edits, `0f6b4a733e`, judged by the banked seven rows

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-08-10 01:13 JST on the trigger m-p18-269. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Judged against the edit commit's own parent** `79b53c797a` — which is the commit that banked the acceptance table itself (`PZ_C2_EDIT_ACCEPTANCE_PREREGISTERED_20260810.md` @ sha `25443d920a…`): the judgment precedes the judged in git history.

## 0. Object and pins (this desk, 01:10-01:13 JST)

- `0f6b4a733e` (01:06:51, "Make C-2 the mounting defaults: spread 0.280, tilt 20.0, crown pinned"), **two files, +23/−6**.
- Content shas at the commit, third-desk verified: `ur15_cell_spec.py` = `d4f79856bd6391d08efd326f905e369fe8742c04417cc75449d619d144abbd25` · `sweep_mounting.py` = `51697f63600cee29cf1dd638cc3d1fa1e73625205d62abc1b90be8841036eb3f` — both match p0's and p18's pins. Worktree == HEAD == these blobs (status clean from repo root; blob-id equality), so the runtime checks below measured the landed content.

## 1. The seven rows

| # | row | verdict | evidence |
|---|---|---|---|
| 1 | surfaces | **holds** | exactly the two unlocked files; each parent blob **== its lock-pin blob by git blob-id** (spec@`2fba2dfd67`, sweep@`2bb1aad4e7`) |
| 2 | token 1 | **holds** | `else 0.22` → `else 0.28`; override arm byte-unchanged |
| 3 | token 2 | **holds** | `else 45.0` → `else 20.0`; the `π/2 − radians(...)` form untouched |
| 4 | token 3 | **holds** | `else YOKE_SPREAD / 2` → `else 0.110` — the literal; `"none"`, override, and Z0-derived arms all survive; the derivation is gone from the built path. The landed comment states my row's own hazard in its words: at 0.280 the old rule would mint 0.140, "a crown no sweep has ever measured"; the built 0.110 = 0.22/2 coincidence "is why the derivation ever looked like a rule" |
| 5 | grounds | **holds** | all four commissioned elements present: witness `SPREAD_TILT_SWEEP_TRIES240_KINONLY.txt:54` with numbers matching my pre-edit read of that line (L clear 5 / R clear 30 / +14.7; built 0.220/45 had L clear 0) · the #54 member condition (no column-to-mounts member modelled; C-2 widens the unsupported span to 0.178 m; re-measure WITH the member when inputs settle) · the stereo-head-ABSENT condition · D4 as carry — plus two beyond commission (settle pointer `P4_DELEGATED_DECISIONS_ITEMS7_9_DOD_20260808.md` §2; crown photo-pin #60) |
| 6 | no behavior/format change | **holds** | every hunk is a literal or a comment; override `environ.get` lines survive; the sweep's built-default labels updated **once** to `"0.280 (C-2 default)"` / `"20 (C-2 default)"` — values agree with the landed spec; closed query `"built default"` = **0/0** post-landing (reproduced here); per the banked row's own terms this is a value correction inside an unchanged format, not a format change. p0 additionally added a hand-tracking warning naming exactly this maintenance hazard |
| 7 | reproducibility | **holds** | fresh interpreter, no overrides → **0.28 / 20.0 / 0.11**; with `YOKE_SPREAD_OVERRIDE=0.22 TILT_DEG_OVERRIDE=45 CROWN_R_OVERRIDE=0.110` → **0.22 / 45.0 / 0.11** — the old cell is expressible and override precedence is intact, measured both directions at this desk |

## 2. Findings that ride along (none blocks)

- **F2, stale-history class, display-only, on a LOCKED surface**: `compare_24_vs_240.py:77-78` describes the built cell as "sweep_mounting.py's own defaults for spread and tilt; the crown follows as YOKE_SPREAD/2". As a record of what that comparison measured (0.110/0.220/45) it stays true; as a description of the current mechanism both clauses went false at this landing. The file was not opened by the word (last commit `446e291fb8`, clean) — named for the next documentation-class unlock, p0's convenience, same bucket as F1 was.
- **Row-6 label reconciliation, closed**: p18's m-p18-268 "the OTHER pair" self-corrected in m-p18-269(a); verified here — one site, read at two times, updated once in the landed commit.
- **KINONLY nomination untouched**: the instrument pins its cell via `C2_ENV` (all three overrides), so its builds never depended on the built defaults; the nominated blob `120746a49b` is immutable and its cell now equals the defaults anyway.

## 3. Verdict

All seven banked rows hold at `0f6b4a733e` against its own parent, with the runtime rows proven in both directions at this desk. The two content shas in §0 are the landing-equality pair for Rs2 (=p4). One display-only stale text on a locked third file is named (F2), nothing blocks. ⛔ Unchanged gates: DoD run and anything wired stay behind Rs1 (the human)'s authorization; dep-2 remains the grade cap; DEV-C2X's 35 mm stays unruled.

## 4. Provenance

`git show`/`rev-parse` blob-id equalities, `sha256sum`, `grep -c` closed queries, and two fresh-interpreter imports of the landed spec (config evaluation only — no mujoco, no stepping, nothing wired). Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian.**
