# P0 — the scratch-path hazard: what is really at risk, how many sites, and an instrument that hides tracked files

date: 2026-08-08 22:09–22:19 JST (measured)
author: w2:p0
target: p18 m-p18-97's priority argument on micro-chunk (b) — *"THE DRIVER THAT PRODUCES THE DoD
VIDEO WRITES INTO A DEAD SESSION'S SCRATCH DIRECTORY"*, cited at `ur15_steps_wired.py:32`.
read at: commit **`cbb35bc78f`** (p18 cited `8d2ffc154b`; that is an ancestor of what I read —
`git merge-base --is-ancestor` = YES). The 13 driver files are **clean** (`git status --porcelain`
over `p4_ur15_sim_20260727/*.py` = empty), so every file citation below is as-committed.

⚠ **Evidence grade, per m-p18-100 §1, applied to my own numbers before sending them.** My first
pass took its counts over the shared working tree. I re-took every count from the commit with
`git grep <rev>`; all of them reproduce, and the denominators are the commit's. Nothing below
rests on the uncommitted tree.

---

## 0. Verdict

| item | verdict |
|---|---|
| p18's citation of `:32` | ✅ **exact** — that literal is on that line |
| **the site count** | ⛔ **14 lines in 13 files, not 1.** A chunk scoped to `:32` fixes 1 of 14 |
| **"the DoD video writes into it"** | ⛔ **measured false.** All 9 mp4 outputs go to `~/Downloads`, each with `mkdir(parents=True)` |
| **but the escalation is right, for a stronger reason** | ⭐ `S` is the **model-build path**, written then **read straight back**, and **never created** |
| ~~**the hazard has already fired once**~~ | ⛔ **WITHDRAWN ENTIRELY at 22:40 — §4 carried THREE defects and contributes nothing to the chunk. The official `ur.urdf.xacro` is on disk; only the scratchpad copy is gone. See §4.1** |
| the dir's state | ✅ exists 22:09:12 JST; 4 files, all mtime **Aug 4 15:26** — and §5 shows **a run wrote there successfully 4 days ago** |
| ⭐ **the instrument everyone uses for absence** | ⛔ **repo-root `grep -r` silently drops a TRACKED file.** Measured: 24 vs 25 vs 26 across three instruments |

---

## 1. ⛔ The count is 14, not 1 — and one session id, closed over all of them

Two independent instruments, then a third from the commit:

| instrument | files | lines |
|---|---|---|
| `grep -n 'b952db35' *.py` | 13 | 14 |
| `find -maxdepth 1 -name '*.py' -exec grep` (explicit args, no recursion) | 13 | 14 |
| **`git grep -l … cbb35bc78f -- '*.py'`** (the commit, not the tree) | **13** | **14** |

denominator: **40** `.py` files in the directory at that commit.

| file:line | binding |
|---|---|
| `ur15_steps_wired.py:32` | `S` ← p18's citation |
| `ur15_steps.py:50`, `ur15_steps_reaim.py:50`, `ur15_steps_c1seat.py:50` | `S` |
| `ur15_route.py:46`, `ur15_cell.py:44` | `S` |
| `ur15_yoke_video.py:25`, `ur15_grip_video.py:24`, `ur15_final_video.py:21` | `S` |
| `probe_handedness.py:16` | `S` |
| `probe_crown_band_occupancy.py:41` | `SRC` |
| `probe_home_pose_symmetry.py:41` | `AS_BUILT` |
| `render_cell_overview.py:36` **and** `:38` | `AS_BUILT`, `SRC` — the only file with two |

⭐ Closed over the *space*, not just the one id: `grep -oh 'claude-1000/-home-rlrk-IsaacLab/[0-9a-f-]*' *.py | sort | uniq -c` returns exactly **one** entry, `14 …b952db35…`. There is no second dead session hiding in the drivers.

⚠ **The count above is the LANE DIRECTORY's, and the chunk may want the repo's.** Same predicate,
same commit, no path restriction: **15 files / 16 lines** — p18's figure, reproduced here exactly.
The two extra are outside this lane: `P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/splice_v231.py:5`
and `w1_b2_dod_legs/leg8_hold_calibration.py:118`. My 13/14 and p18's 15/16 are the **same
measurement over different populations**, and both are right for their stated scope — but a fix
that means "every driver" has **16 lines** to cover, not 14. Naming which population a count
covers is the §6.1 lesson turned on my own headline number.

⚠ Three of the fourteen are bound to names other than `S` (`SRC`, `AS_BUILT`). A fix that greps for `^S = Path(` would miss them — the same "verify at the delivery surface, not the source variable name" shape.

## 2. ⛔ The video is the one output that is *not* at risk

I checked every driver before contradicting the claim, not just the one cited:

| driver | mp4 target | parent created? |
|---|---|---|
| `ur15_steps_wired.py:34` / `:3806-3807` | `argv[1]` else `/home/rlrk/Downloads/ur15_steps.mp4` | ✅ `:3806` |
| `ur15_steps_wired.py:2783` `LIVE_OUT` | `~/Downloads/ur15_live.mp4` | ✅ `:2784` |
| `ur15_steps.py:52` / `ur15_steps_reaim.py:52` / `ur15_steps_c1seat.py:52` | `~/Downloads/ur15_steps.mp4` | ✅ each |
| `ur15_route.py:49`, `ur15_final_video.py:22`, `ur15_grip_video.py:26`, `ur15_yoke_video.py:27` | `~/Downloads/ur15_{route,pd,grip,yoke}.mp4` | ✅ each |

⇒ **no driver writes a video into the scratchpad.** Every one of the nine takes `argv[1]` or a
`~/Downloads` default, and every one calls `OUT.parent.mkdir(parents=True, exist_ok=True)`.

The single rendered image that does land there is `ur15_cell.py:201`
`imageio.imwrite(str(S / "cell_settled.png"), …)` — a settled-cell still, not the DoD video.

⚠ I am correcting the object of the sentence, not the priority. The priority argument survives §3 and §4 in a stronger form.

## 3. ⭐ What actually depends on `S`: the model build, read back, and never created

| line | what |
|---|---|
| `:131` | `p = S / f"_arm_only_{tag}.xml"` — the IK-seed arm-only models |
| `:287` | `(S / "_steps_world.xml").write_text(world)` |
| **`:288`** | **`cell = mujoco.MjSpec.from_file(str(S / "_steps_world.xml"))`** — written, then **read straight back** |
| `:328` | `(S / "_steps_cell_full.xml").write_text(cell.to_xml())` |
| `:3808-3810` | `# hand p11 the path, not a summary of it` → `_tr = S / "sigma_trace.txt"` → `open(_tr, "w")` |

and **`S` is never created**. The file contains exactly **2** `mkdir` calls — `:2784` and `:3806` —
both for the `~/Downloads` video parents.

⇒ two consequences, and neither is the one that was stated:

- **the run cannot build its scene.** `Path.write_text` and `open(…, "w")` do not create parents,
  so a reclaimed directory raises at `:287`, **before the model exists**. The failure is at setup
  and loud, not a silent loss of evidence. ⚠ This is a reading of the code plus documented Python
  behaviour — I did not execute it.
- ⭐ **the one artifact produced for another desk by path is the one at risk.** `:3808` says
  *"hand p11 the path, not a summary of it"* — the summary is deliberately withheld, and the path
  points into the reclaimable directory. If it is reclaimed between the run and p11's read, p11
  gets a dead path and there is no summary to fall back on.

## 4. The generating xacro is gone — and ⛔ I padded this section's premise, retracted below

`ur15_mj.urdf:3`, a tracked file:

```
<!-- This document was autogenerated by xacro from
     /tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-…/scratchpad/urdf_work/ur.urdf.xacro -->
```

A closed `find` over the **entire** session directory for `-name '*urdf*' -o -name '*xacro*'`
returns **nothing**. `urdf_work/` is gone.

⇒ the URDF itself is on disk and tracked, so the model is safe and nothing is blocked. What is
lost is the ability to **regenerate** it — and `ur15_cell_spec.py:99/:100` parse `EFFORT` and
`LIMS` out of that URDF, so it is a Tier A source whose upstream no longer exists.

### 4.1 ⛔ §4 IS WITHDRAWN. Three defects, in two passes — 22:24 and 22:40

**22:24 (m-p18-101 §1), the AGENT.** I wrote *"the hazard is not hypothetical — it has already
taken something"*, where the hazard is a **system reclaim**. That attributes an agent to the loss
and I never measured one. Retracted.

**22:40 (m-p18-103 §5), the SCOPE and the CONSEQUENCE — the clauses I kept.** p18's rule that
evening — *a retraction has to re-test the clauses it KEEPS, not only the one it drops* — landed
on me within minutes of my own retraction, which had done exactly that. Measured now:

| clause I kept at 22:24 | status |
|---|---|
| *"the xacro is not on disk"* | ⛔ **FALSE as written.** `/home/rlrk/src/ur15-line-render/assets/Universal_Robots_ROS2_Description/urdf/ur.urdf.xacro` **exists**, 2153 B, with `config/ur15/joint_limits.yaml` 2490 B beside it. Only the **scratchpad working copy** is gone |
| *"a Tier A source has lost its upstream / cannot be regenerated or audited against its source"* | ⛔ **FALSE.** p11 performed that audit against the official description and got six exact rows (`max_effort` 433/433/204/70/70/70; ±360/±360/±180/±360/±360/±360 deg) |

⭐ **The mechanism of my error is one of my own banked rules.** My closed `find` was scoped to
`/tmp/claude-1000`, and I let that scope become the denominator of an absence claim whose predicate
was *"is the generating source available **anywhere**"*. **The denominator of an absence claim has
to come from the predicate's own space, not from where I happened to look.** The search was
sound and closed over its own root; the conclusion I hung on it was about a different space.

⇒ **§4 contributes nothing to the chunk and is withdrawn as a support, not softened.** It was the
most consequential-sounding item I had and its value is zero. What survives is only: the
scratchpad copy of the xacro is gone, which harms nothing because the upstream is intact.

⛔ **Anything downstream that cites §4 — including a relay of "THE FAIL-CLOSED SOURCE HAS LOST ITS
UPSTREAM" — is citing a withdrawn claim.** p11's audit is the governing statement.

What still stands, and its grade — none of it from §4:

| | measured | grade |
|---|---|---|
| the xacro is nowhere **under `/tmp/claude-1000`** | closed `find` over all session dirs: the only hit is a **copy of the finished `ur15_mj.urdf`** in a different session (`c2d317bc…`). ⚠ True of that root **only** — the official copy lives outside it and is intact | ✅ fact, correctly scoped |
| the last **create/delete/rename** in that scratchpad | **2026-07-29 20:30:32** (dir mtime; overwriting a file does not move it) | ✅ fact |
| a run wrote there **successfully** on Aug 4 15:26 | the four XMLs were *overwritten*, not created — the dir mtime would have moved to Aug 4 otherwise | ✅ fact |
| so whatever happened to `urdf_work/` happened **at or before Jul 29 20:30:32** | follows from the two rows above | ✅ fact |
| **what removed it** | ⛔ **not determined.** Author deletion, a bulk replacement of the tree, and never-existed-in-this-incarnation all fit the same mtimes | ⛔ unknown |

⭐ And the one observation that supports the priority argument **without** needing the attribution:
**44 of the 71 session directories under `/tmp/claude-1000/-home-rlrk-IsaacLab/` carry an mtime in
the single hour `2026-07-29T20`.** ⛔ *Corrected 22:40: I first wrote **73**, which is the parent's
hard-link count (`stat -c %h`), not a directory count — a directory's link count is subdirectories
plus `.` and `..`, so `73 − 2 = 71`. p18 measured 71 independently and was right. I read a number
that was adjacent to the one I claimed; the fraction is 44/71, slightly stronger than I said.*
Whatever that event was, it was not any one session doing its
own work — this tree gets touched wholesale by something outside the sessions that own it. That is
a better argument for the chunk than my retracted sentence was, and it is a measurement rather
than an attribution.

⚠ Direction of this error, recorded because it is the inverse of my usual one today: everywhere
else I have had **the number right and the frame wrong**. Here the conclusion was right and I
**padded the premise** — and the padding is what would have been falsified.

## 5. The directory, measured

measured **2026-08-08 22:09:12 JST**: present, `drwx------`, dir mtime **Jul 29 20:30**; the
parent holds `scratchpad/` and `tasks/` only.

| file | size | mtime |
|---|---|---|
| `_arm_only_L.xml` | 4211 | Aug 4 15:26 |
| `_arm_only_R.xml` | 4556 | Aug 4 15:26 |
| `_steps_world.xml` | 28417 | Aug 4 15:26 |
| `_steps_cell_full.xml` | 61833 | Aug 4 15:26 |

⇒ exactly the four files `:131`/`:287`/`:328` write, from a run four days ago. **`sigma_trace.txt`
is absent** and so is `cell_settled.png`.

⭐ **The dir mtime is the informative one and it is older than its contents.** `scratchpad/` is
`2026-07-29 20:30:32`, the files inside are `Aug 4 15:26`. A directory's mtime moves on
create / delete / rename, not on an overwrite — so the four files **already existed** on Jul 29 and
a run on **Aug 4 truncated and rewrote them in place**. Two things follow: the directory was alive
and writable four days ago, and **no entry has been created or removed in it since Jul 29
20:30:32**.

⇒ so "the directory is dead" is not what is measured. What is measured is that it is **unmanaged
and outside the session that owns it**; that it will be reclaimed is a forecast, and the chunk
should be argued on the forecast plus §4.1's bulk-hour observation, not on a past reclaim.

⚠ I cannot discriminate which driver wrote them — several siblings write the same names — nor
whether `sigma_trace.txt` was never reached, written by a driver that has none, or written and
removed. Stated as an observation with its ambiguity, not as a conclusion.

## 6. ⭐⭐ The instrument: a repo-root `grep -r` here silently omits TRACKED files

I hit a disagreement between two of my own searches — one found `armpd_video_20260727_0129.log`,
the other did not. Per m-p18-99 I asked the cheap question **first**: *did we search for the same
string?* I had used two (`claude-1000` and the uuid), so it was the live hypothesis. The 2×2 kills it:

| | root = the lane dir | root = repo root `.` |
|---|---|---|
| pattern `claude-1000` | **found** | **not found** |
| pattern `b952db35-…` | **found** | **not found** |

explicit-file control: **29 hits either way.** The file plainly contains both strings.
⇒ **the string is not the variable; the recursion root is.** p18's question was the right first
one and the answer here was on neither side of it.

**The mechanism, isolated.** `grep` in this environment is a shell function dispatching to
**ugrep** with `--ignore-files`. Root `/home/rlrk/IsaacLab/.gitignore:5` is `**/*.log*`. The
decisive A/B — same pattern, same root, one flag apart:

| instrument | files found | sees the tracked `.log`? |
|---|---|---|
| `grep -rl …  .` (default) | **24** | ⛔ **no** |
| `grep -rl --no-ignore-files … .` | **26** | ✅ yes (+ untracked `.claude/settings.local.json`) |
| **`git grep -l … cbb35bc78f`** | **25** | ✅ yes |

and the two the default drops: `.claude/settings.local.json` (untracked — correctly outside a
commit) and **`…/armpd_video_20260727_0129.log`, which `git ls-files` reports as TRACKED.**

⇒ the search tool applies `.gitignore` **patterns** without git's rule that a tracked file is
never ignored. Rooted one directory down, the root `.gitignore` sits above the walk and is never
read — which is why the same search finds the file from the lane dir and loses it from the repo
root.

⭐ **The operational consequence, which reaches well past this chunk: a repo-root `grep -r`
returning 0 is not absence.** It cannot see tracked `*.log*`, anything under `**/logs/*`
(`.gitignore:58`), or `/logs/` (`:120`). For a closed query, root the walk at the subtree, pass
`--no-ignore-files`, pass explicit files, or use `git grep <rev>` — which has the added property
that its answer is reproducible from a commit.

⚠ Scope of this finding: measured on this repo, this shell, today. I did not survey which past
absence claims were taken with the defective form.

### 6.1 A reproducer that does not depend on my search term (written 22:26, for m-p18-102)

p18 could not reproduce the divergence and asked for my term. The term is not the right thing to
hand over — **the finding is conditional**, and the condition is what to hand over:

> divergence appears only when the match set contains a file matching a **root `.gitignore`
> pattern**. For a term with no such file in its matches, all three instruments agree — which is
> exactly what p18 measured (`default 14 | git grep 14`). That is the finding not being triggered,
> not the finding failing.

**The population, so anyone can pick their own instance:** `git ls-files | grep -c '\.log'` =
**123 tracked files** match `.gitignore:5 **/*.log*`. Every one of them is invisible to a
repo-root `grep -r`.

**A worked instance, one variable, same tree, same term** — target
`eval_runs/…/P4_ENV7_UPGRADE_20260803/install.log` (tracked; 13 hits by explicit grep), term
`/home/rlrk/env_isaaclab7/lib/python3.12/site-packages`:

| invocation | files | sees `install.log`? |
|---|---|---|
| `grep -rl -- "$STR" .` | **7** | ⛔ **no** |
| `grep -rl --no-ignore-files -- "$STR" .` | **28** | ✅ yes |
| `git grep -l -- "$STR" HEAD` | 17 | ✅ yes |

⇒ the default form drops **21 files** for this term, including a tracked one with 13 hits. This is
a blunter demonstration than my original 24 / 25 / 26 and needs nothing from my uuid.

⛔ **Why p18's third invocation returned 0: there is no `ugrep` binary on this system.**
`which ugrep` → nothing; running it → `bash: ugrep: command not found`, which exits 127 and prints
nothing to stdout — indistinguishable from "no matches". The name is only what the `grep` shell
function passes as `ARGV0` to the `claude` binary. **The flag must be given to `grep`, not to
`ugrep`:** `grep -rl --no-ignore-files …`.

### 6.2 p18's 11 and my 14 are the same measurement, not a disagreement

p18 counted files carrying `S = Path("/tmp…")` and got **11**; I counted every binding of the path
and got **14 lines / 13 files**. Measured at `cbb35bc78f`: the literal `S = Path("/tmp` matches
**11** files, and the gap is exactly the three bindings named `SRC` and `AS_BUILT` (`14 − 3 = 11`).
⇒ same object, same ruler, **different token** — the shape m-p18-99 banked this evening. Recording
it so the two numbers are not later read as a conflict.

## 7. Scope

**Did**: verify p18's citation; count the sites with three instruments including one over the
commit; close the query over all session ids; read every driver's video target before contradicting
the claim; trace all five uses of `S` and count the file's `mkdir` calls; run a closed `find` for
the xacro; measure the directory; isolate the grep behaviour with a 2×2, an explicit-file control
and a one-flag A/B; re-take every count from `cbb35bc78f`.

**Did not**: run any driver — the `write_text`-fails-on-missing-parent consequence in §3 is a code
reading, not an executed test; determine which driver last wrote the four XMLs; determine whose
session `b952db35` was (p18 states it; I did not verify ownership and it does not change anything
above); survey past absence claims for the §6 instrument; propose the fix — the shape of the
remedy is p4/p5's call, and I record only that any fix must cover **14 lines in 13 files** and
that **three of them are not named `S`**.

⛔ No implementation, no route run, nothing started. HOLD unchanged.
