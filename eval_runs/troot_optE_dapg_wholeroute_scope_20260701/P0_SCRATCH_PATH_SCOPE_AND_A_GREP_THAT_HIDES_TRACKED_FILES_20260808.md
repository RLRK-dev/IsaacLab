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

⭐ **HOW TO CITE THIS FILE — added 00:19, at the top because that is where a stale pin gets made.**
This artifact took **15 commits and grew 196 → 723 lines in one evening**, so *"P0_SCRATCH_PATH…md"*
alone does not identify a version.

- **Pin the FILE by CONTENT** — `sha256sum` of this path. A commit sha is immutable but pins the
  **repo**, and the repo ref moves under other panes while this file does not (m-p18-127).
- **Cite section + content**, with the version as a **collation note**, never as the pin.
- **Sections are appended, never rewritten; numbers are never reused** (§8, narrowed by §8.3:
  corrections are written as **whole new lines**, placed beside the claim where placement helps).
- **Withdrawn claims stay visible** with the correction beside them — §4 and §6.4 are withdrawn in
  place, not deleted. If a section carries ⛔ WITHDRAWN, read the section it points to before
  quoting either.
- ⛔ **Quote-forbidden, per-claim** (each names the version that carried it): §4 in `0b9fd21dd9`
  and `aa5f0a673a`; §6.4's *"either direction"* in `6186510e91` and `bc452521e0`; §8.2's *"the clean
  one escaped by accident"* in `5000738e9c` and `cebe0248de`; §6.3(a)'s history row in `c6b740ed36`.

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
⭐ runnable, with its coverage on the predicate's own line (pZ 07:24 — a copy takes the regex and
leaves the guarantee, so the number rides with the command):
`git ls-tree --name-only cbb35bc78f:<dir> | grep -c '\.py$'` **expect 40**; `git grep -l 'b952db35…' cbb35bc78f -- '<dir>/*.py'` **expect 13**

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

> ⛔ **SUPERSEDED — this section is WITHDRAWN IN FULL. Read §4.1 immediately below before quoting anything here.** The official `ur.urdf.xacro` is on disk; only the scratchpad working copy is gone.


`ur15_mj.urdf:3`, a tracked file:

```
<!-- This document was autogenerated by xacro from
     /tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-…/scratchpad/urdf_work/ur.urdf.xacro -->
```

A closed `find` over the session directory — **N=1 session tree, 2 entries deep** (`scratchpad/`, `tasks/`) — for `-name '*urdf*' -o -name '*xacro*'`
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
| the xacro is nowhere **under `/tmp/claude-1000`** | closed `find` over **N=71 session dirs (measured 22:40, ⚠ PERISHABLE §8.20)**: the only hit is a **copy of the finished `ur15_mj.urdf`** in a different session (`c2d317bc…`). ⚠ True of that root **only** — the official copy lives outside it and is intact | ✅ fact, correctly scoped |
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
(`.gitignore:58`), or `/logs/` (`:120`).

⛔ **My remedy list here is superseded — see §6.3.** I wrote *"or use `git grep <rev>`"* as if either
route closed an absence. It does not: `git grep` is blind to everything untracked, which is the
larger population.

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

### 6.3 What replaces §6's remedy list — corroborated first-hand, not relayed (22:52)

p6 found a second, larger face of this and p18 adopted their division; p18 also warned that *a
relayed attribution that survives is still not a measurement*, so I re-ran the parts that touch my
own section.

**(a) The division, which supersedes my list.** Population picks the instrument; one run, not two:

| the claim | the instrument |
|---|---|
| "not in the working tree" | `command grep` **alone** (add `--exclude-dir=.git`) |
| ~~"not in the project at all, incl. deleted-but-committed"~~ | ⛔ **struck 23:12 — this leg does not close.** See below |
| "not in a specific tracked revision" | `git grep <rev>` **alone** |

⛔ **Row 2 is withdrawn, 13 minutes after I banked it.** pZ measured `git grep -l HEAD` → 0 / rc=1
and `git grep -l 87278086a2^` → 1 / rc=0 on the same token: **one rev does not answer a history
question, the rev has to range**, and the closed query over 6776 revs was not affordable (`git log
--all -S` killed at exit 143). pZ reported no number, which is the right output.
⇒ **the phrasing goes with it.** Never write *"not in the project at all"* — write **"not in the
working tree, and not at `<rev>`"**, naming both populations. ⭐ **The history population is
UNRESOLVED and is recorded as unresolved**, not papered over with the two instruments that do work.

**(b) I found one filter; there are three.** `--ignore-files` (mine), `-I` (skips what it judges
binary), `--exclude-dir=.git .svn .hg .bzr .jj .sl`. My §6 named the first as if it were the defect.

**(c) The intersection, measured here.** `.gitignore:101` is `/.claude/` and `git ls-files .claude/`
= **0**, so that subtree is invisible to **both** daily routes:

| for `timeouts汚染禁止` in `.claude/rules/prohibited.md` | |
|---|---|
| explicit file read | **2 hits** — predicate sound |
| wrapper `grep -rl` from repo root | **0** |
| `git grep -l HEAD` | **0** |
| `command grep -rl --exclude-dir=.git` | **1** |

⇒ the prohibition rules and **33 `SKILL.md`** sit where both routes return zero. For contrast,
`CLAUDE.md` and `AGENTS.md` are tracked at repo root and reachable by all three.

**(d) The `-z` escape hatch works, and it is fragile for a reason worth naming.** `grep -z -rl`
does find `prohibited.md` (1). But the cause is in the wrapper's own source: its case-guard lists
`-[Zz]*`, so `-z` **falls through to `command grep`**. ⇒ **it is not a search fix; it changes which
binary runs**, by tripping a fallback that exists for an unrelated reason (`-z` = NUL-separated
output). If that guard list ever changes, `-z` silently stops bypassing and the absence claims go
quietly wrong again. ⭐ **Prefer `command grep` explicitly** — it says what it does.

**(e) The discipline that already routes around this was written before anyone measured it.**
`prohibited.md:38` — *「ルール・禁止事項を引用する場合、CLAUDE.md/prohibited.md の原文を cat で確認して
から引用すること」*. `cat` takes an explicit path and never walks a tree, so the one rule governing
how these files may be quoted is **immune to the blind spot by construction**, for a different
reason than the one that makes it necessary.

**(e2) The membership filter itself is an instrument — three tools render one object three ways.**
p18 nearly published a contradiction of (c) because their membership pattern anchored on a leading
`./`, which **encodes a path form, not a path**. Measured here, one line of each tool's output for
the same search:

| tool | renders a hit as |
|---|---|
| wrapper `grep -rl` | `GOALS.md` |
| `command grep -rl … .` | `./.claude/worktrees/…/GOALS.md` |
| `git grep -l … HEAD` | **`HEAD:CLAUDE.md`** — a third form, with a `<rev>:` prefix neither other tool has |

⇒ any filter anchored at `^` breaks against all three differently. My filters happened to be bare
unanchored substrings (`grep -c 'prohibited.md'`), which match every rendering — **but I did not
check that before relying on them**, which is the actual rule. What does defend (c) is that every
row of that table runs the **same filter** and produces both a hit and a miss (`0 / 0 / 1`), so the
filter demonstrably reaches the object whenever the tool does. That is the discriminating control,
and it was there by the shape of the table rather than by my intent.

**(f) Three holes in my own instruments, disclosed.**
- ⛔ I ran two of (c)'s three cells with **`2>/dev/null`** — the stderr mask that has burned me
  before. Re-run with stderr visible and `rc` printed: wrapper `rc=0` / 0 hits, `git grep` `rc=0` /
  0 hits, `command grep` `rc=0` / 1 hit. All three commands ran; `rc=0` on the zero cells means the
  phrase was found *elsewhere*, just not in that file. The numbers stand and are now guarded.
- ⛔ My §6.3(c) first draft printed a column of counts that were *paths whose basename matched*,
  not occurrences. Reported above as reachable / not reachable instead. Same class as the
  `grep -c`-is-not-an-occurrence-count error banked earlier today.
- ⛔ My §1 claim *"neither extra file is inside the lane dir"* came from an **empty pipeline with no
  `rc`** — indistinguishable from a broken command (p18's `ugrep` 127). Re-run with the guard:
  `rc=1` from grep (ran, found nothing), a **positive control** on `ur15_steps_wired.py` in the same
  listing returns `1` with `rc=0`, and the listing is **251 paths**. The absence is measured. The
  conclusion never moved, but it was unguarded when I banked it.

### 6.4 The `--stat` header fails in BOTH directions (23:46, from m-p18-115)

p6's defect — asserting *insertion-only* four times without measuring it — sent me to check my own
nine commits tonight: `--stat` header against difflib character deletion, parent blob vs blob.

| commit | header | chars actually deleted |
|---|---|---|
| `aa5f0a673a` | `85 insertions(+), 6 deletions(-)` | 107 |
| `89d3390b92` | `43 (+), 11 (-)` | 290 |
| `c6b740ed36` | `58 (+), 3 (-)` | 140 |
| `1e260024d5` | `32 (+), 2 (-)` | 22 |
| `7a7fd3cc44` | `41 insertions(+)`, no deletions | **0** ✅ |
| **`22699a5cd6`** | **`15 (+), 1 deletion(-)`** | **0** ⭐ |

✅ **No defect of my own**: I never asserted *insertion-only* as a property, and where the header
showed no deletions, difflib agrees at character level.

⭐ **But `22699a5cd6` is the mirror of p6's case and nobody has stated this half.** The header
reports **one deletion where zero characters were removed** — a line rewritten into a superset of
itself. So the header **over-reports** as readily as it under-reports:

| direction | how it happens | what it breaks |
|---|---|---|
| **under**-reports (p6's case) | characters deleted *inside* a very long line | `-0` read as proof nothing was lost |
| **over**-reports (mine) | a line replaced by a superset | `-N` read as an **upper bound on harm** |

⛔ **The sentence that stood here is FALSE and it was mine.** I wrote *"the header is not a
conservative bound in either direction … `-0` is no more evidence of safety than `-N` is of loss."*
**The first half is wrong**, and §6.6 below — which I wrote twenty minutes later, in this same
file — **proves it wrong**: 227 of 227, `deleted = 0` ⇒ no character removed.

⚠ **m-p18-118 §3 takes the cause side for this generalisation. It is mine.** I wrote it here and
sent it in m-p0-115/116R; p18 adopted the wording from me. Correct form:

| header says | what it means |
|---|---|
| `deleted = 0` | ✅ **conclusive** — deleting characters inside a line always produces a deleted line, so nothing was removed |
| `deleted ≥ 1` | ⛔ **no information** — could be 290 characters (my `89d3390b92`) or **zero** (my `22699a5cd6`, a line rewritten into a superset) |

⇒ **the header is one-sided, not powerless.** My mirror finding broke the **second** direction only,
and I generalised it to both. ⭐ The self-inflicted part is sharper than the error: **§6.6 refutes
§6.4 and I did not notice, because I checked what my new proof ADDED and never what it KILLED.**
That is tonight's *re-test the clauses you keep*, turned inward and missed on my own file.

⚠ **And the cheap test's availability is domain-dependent** (p6's limit, measured). Where content
lives inside single huge lines, `-0` can never occur and measurement is the only route:

| desk | longest line | `-0` fired |
|---|---|---|
| p6's surfaces | map 17,922 / DDR **204,998** | **0 of 19** |
| p18's ledger | 574 | 26 of 27 |
| **my artifacts** | **183 / 267 / 295** | readily |

⇒ mine are the shortest of the three, which is why the `-0` rows exist in my table at all — and why
**the falsification test in §6.6 was even available to me.** p6 could not have run it on their
surfaces.

⛔ **Superseded by p6's variable (m-p18-119 §1), and they are right: line length is not the operative
term.** *Adding* a line fires the shortcut; *changing* one blinds it. Length only explains **why**
certain surfaces force in-place edits — a DDR row **is** a line, so no append can reach it. My table
above measured a **proxy** for the cause, which is the error I have been reporting in others all
night.

⭐⭐ **And on my own twelve commits the real variable splits them perfectly — 6 and 6:**

| `-0`, header **conclusive** | what it was |
|---|---|
| `0b9fd21dd9`, `bb52dff085`, `795c592400` | new files |
| `7a7fd3cc44`, `6186510e91`, `bc452521e0` | sections **added** |

| `-N`, header **says nothing** | what it was |
|---|---|
| `aa5f0a673a` | *I padded the one premise the conclusion did not need* |
| `89d3390b92` | *I retracted one clause and shipped the other two* |
| `c6b740ed36` | struck my own superseded remedy list |
| `1e260024d5` | struck the history leg |
| `22699a5cd6` | a line rewritten into a superset — **0 chars lost** |
| `fa5df1abf7` | *my own section refuted my own section* |

⇒ **every pure addition is conclusive; every retraction is blind** — on my surface, and on p18's
(they tested it at **30 and 1**, the one blind commit being their one in-place annotation).

⛔ **But my *explanation* is false, and p11's surface falsifies it.** I wrote *"that is what a
retraction IS: correcting text means modifying it."* It does not. Measured on p11's commits, under
the append-only convention they adopted the same evening:

| commit | numstat | |
|---|---|---|
| **`18d706b145`** — *"**Withdraw** the word 'transposition': it fits one clip of two"* | **14/0** | ✅ **CONCLUSIVE — a withdrawal that is not blind** |
| `4577f216fa` — *"Unfold the DoD…"* | 23/0 | ✅ |
| `c376d96af2`, `b8b80cbf32` | 18/0, 2/0 | ✅ |

⇒ **a correction produced `-0`.** Correcting does not require modifying — p11 withdraws by
**appending a new section**. So the blindness is a property of **the convention by which
corrections are made**, not of correction itself. My 6/6 and p18's 30/1 held only because we both
correct in place; two desks agreeing was two instances of one habit, not two independent tests.

⭐⭐ **And the corrected form is more useful than the law was.** The escape exists and was built the
same evening: *append-only, corrections as new sections, stable numbers never reused.* Under it the
cheap conclusive test becomes available **exactly where it was blind** — on the commits a reader
most wants assurance about. The limit is not something to accept; it is something a convention
removes.

⚠ And the commit carrying this correction is itself an in-place edit, hence `-N`. **I could have
appended.** I am still writing in the habit I have just finished describing.

⭐ **Forward pointer, added 00:11 as whole new lines — see §8.1 for the corrected account, and §8.3
for why this pointer is here rather than only there.** A reader arriving at §6.4 was, until this
line existed, 211 lines and one intervening §7 away from the correction, with **zero** references
pointing forward. That gap was my doing and is described in §8.3.

⭐ **So the cheap conclusive test is available precisely when nothing was withdrawn, and blind
precisely when something was.** The instrument is uninformative exactly where the risk lives.
⚠ Blind ≠ harmed: `22699a5cd6` is a correction that deleted zero characters. The point is that the
header cannot tell you which kind you are looking at, on the commits where it matters most.

### 6.5 項目 14's window: the start is content-anchorable, the end is not a boundary (23:47)

m-p18-116 §3 reports that 項目 14 re-runs a **literal** region `2639-2760` after the implementation
diff, so the anchor decays silently at the moment of use. ⚠ **I am the desk that will produce that
diff**, so I measured what the two proposed forms would actually rest on. p11 decides the form;
these are facts, not a proposal.

**The start anchor is unique — pZ's form works:**

| pattern | occurrences | line |
|---|---|---|
| `STEP table 2-18` | **1** | 2639 |
| `STEP table` | **1** | 2639 |
| `Lfinger` | **1** | 2639 |

**The end is the problem, and it is worse than "a literal number":**

- the STEP table **closes at `:2722`** (`]`), 84 lines long
- the cited window runs to **2760** — **38 lines past the table**, through `:2724 FPS, W, H = 30,
  1600, 900` and into the run-loop initialisation block
- line **2760** is `claw_min = {t: 1e9 for t in SIDES}` — one of seven near-identical initialisers
  (`sig_min`, `col_min`, `sig_where`, `col_where`, `claw_min`, `arm_gap_min`, `arm_gap_path`).
  **Nothing distinguishes it; it is not content-anchorable and it marks no boundary.**

⚠ **This does not weaken the confinement result.** A zero over a **superset** is at least as strong
as a zero over the subset — the window is 122 lines and the structure it names is 84. What is
arbitrary is where it stops, which matters for **anchoring**, not for the finding.

⇒ so a fully content-anchored window exists and is **tighter** than the current one: start at the
unique `STEP table 2-18` line, end at that list's own closing bracket. No literal line numbers on
either side, and it decays under no diff.

### 6.6 p4's numstat shortcut: I tried to break it and could not (23:52)

m-p18-117 §3 adopts p4's shortcut at two desks as a **soundness** claim — *numstat deleted-lines = 0
makes character-level deletion impossible*. A soundness claim earns a falsification attempt, not
agreement, so I ran one over 300 commits touching `*.md`/`*.py`:

| | |
|---|---|
| file-rows with `numstat` deleted-lines **= 0** | **259** |
| of those, comparable (parent blob exists — not new files) | **227** |
| **counterexamples — characters deleted anyway** | **0** |

Test: for each such row, is the parent blob an exact character subsequence of the child? Any
character of the original missing, in order, would flag. **None of the 227 did** — the denominator
is on this line because "None did" is the sentence a reader quotes, and it travels without the table.

⭐ **And the reason, which is why this is more than a sample:** a unified diff must reconstruct the
target from the source, so any original line that *changes* appears as `-old +new` — a modified line
always contributes at least one deletion. `deleted = 0` ⇒ every original line survives verbatim ⇒
no character was removed.

⚠ **Three conditions nobody has stated, and the first is the one that bites:**

1. **It is per-FILE, not per-commit.** `numstat` emits one row per path. A commit-level claim needs
   **every row summed** — reading only the row for the file of interest leaves another file's
   deletion invisible. Both desks' use is per-commit, so this is the condition that matters.
2. **Default flags only.** Under whitespace-ignoring options a whitespace-only deletion would not
   appear in the count.
3. **Binary rows say nothing** — they report `-`/`-`, and the shortcut has no content to work on.

⇒ within those conditions the shortcut is sound, and it is **cheap where difflib is not**: difflib
has now timed out twice tonight on the 1.1 MB ledger. 25 of p18's 26 commits are `-0`, so on this
result none of those 25 needed measuring at all — only the single `-1` did.

### 6.2 p18's 11 and my 14 are the same measurement, not a disagreement

p18 counted files carrying `S = Path("/tmp…")` and got **11**; I counted every binding of the path
and got **14 lines / 13 files**. Measured at `cbb35bc78f`: the literal `S = Path("/tmp` matches
**11** files, and the gap is exactly the three bindings named `SRC` and `AS_BUILT` (`14 − 3 = 11`).
⇒ same object, same ruler, **different token** — the shape m-p18-99 banked this evening. Recording
it so the two numbers are not later read as a conflict.

## 7. Scope

**Did**: verify p18's citation; count the sites with three instruments including one over the
commit; close the query over **N=1 distinct session id found in 40 `.py`**; read **N=9** drivers' video targets before contradicting
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

---

## 8. Correction by append — the convention, adopted here rather than agreed with (2026-08-09 00:0x)

m-p18-121 §1 ends: *"Neither of us has switched yet."* True, and it is the one line tonight that
names an action rather than a finding. **§8 is that switch.** From here, corrections to this
artifact are appended as new sections; earlier sections are not rewritten, and section numbers are
never reused. The predicted consequence is checkable in one command: **this commit should read `-0`
where every previous correction of mine read `-N`.**

### 8.1 Correction to §6.4 — the account of *why*, restated where it can be found

§6.4 carries its own retraction already, but the corrected form belongs in a section a reader
reaches without having to notice a strikethrough:

- the **numbers** stand — mine 6-and-6, p18's 30-and-1, p11's 4-of-4 the other way
- the **explanation** is withdrawn: correcting text does **not** mean modifying it
- ✅ the operative variable, in p4's cleanest form: **modifying an existing line** — not position
  (p4 has seven mid-file insertions reading `-0`), not line length (p6's correction of my proxy)
- ⇒ the blindness belongs to **the convention for making corrections**, and a convention removes it

### 8.2 What I contaminated tonight, measured (pZ's hazard, m-p18-121 §3)

pZ found that a token discussed in the ledger re-enters the repository and then answers its own
absence query as a quotation. That applies to my artifacts too, so I measured mine:

| token | hits in my `P0_*` artifacts | |
|---|---|---|
| `GEOM_WITNESS_5CLIP` | **1** | now a false positive for its own absence query |
| `timeouts汚染禁止` | **1** | ditto |
| `urdf_work` | **1** | ditto |
| **the full session uuid** | **0** | ✅ **uncontaminated** |

⇒ **three of four contaminated, and the one that escaped is the one that mattered** — the uuid query
whose real population is the 13 driver files. ⚠ **It escaped by accident, not by care:** I wrote the
8-character prefix throughout because it read better, which happens to be the behaviour pZ's hazard
would ask for. A habit that protects a query by luck protects the next one only by luck.

⇒ for any future absence query on a token examined tonight: **restrict the path to the population**,
and state the restriction — otherwise this file answers, and its role is a quotation.

⛔ **§8.2's "clean" was itself half-measured — corrected 00:13 from m-p18-123, as whole new lines.**
I checked **one token form** and wrote a conclusion about "the uuid query" as though there were one.
There are two, and I am a contaminant on the other:

| form, in my `P0_*` artifacts | files | occurrences |
|---|---|---|
| the **full 36-char uuid** | 0 | **0** ✅ |
| the **8-character prefix** | 1 | **5** ⛔ |

⭐ **And it is not symmetric: the full form *contains* the prefix, so a prefix query is a strict
superset** — it returns everything the full-uuid query returns **plus** every investigation
document. p18 measured 6 tracked `.md` carrying the prefix against **1** carrying the full uuid,
and the six are the six desks' own records.

⇒ so my "escaped by luck" was wrong in an instructive direction. Abbreviating an identifier in a
report is **not** the protective behaviour pZ's hazard asks for — for the prefix query it is the
*opposite*, and not by chance: once the prefix is written, a prefix query hits it **certainly**.
What was luck was that the drivers' own population is queried by the full form; what was
**guaranteed** was that I would contaminate the other one.

⇒ p18's rule supersedes mine: an absence query must state **three** things — **path population,
counting convention, and TOKEN FORM.** My §8.2 named only the first.

⛔ **Corrected again 00:21 from m-p18-128, as whole new lines. THREE further defects, all mine.**

**(a) Axis ZERO — which object. My table above says "the full session uuid" and never names it.**
There are **two** dead sessions in play, and p18 and p6 spent four minutes disagreeing because each
meant their own. Named, so this table cannot be read against the wrong one:

| object | what it is | in my artifacts |
|---|---|---|
| `b952db35…` | **p4's sim session** — the one the 13 drivers bind to. **This table is about it.** | 5 |
| `2dbed74a…` | **p6's old session** | **0** |

**(b) Axis 1 is not binary — there is a third form, and I use it.** p6 found that prose does not
merely shorten, it **substitutes a character that appears in no path** (the unicode ellipsis), so the
record's string is not a prefix of the code's but a *different string sharing a prefix*. My own
5 occurrences split:

| form | occurrences |
|---|---|
| followed by the full uuid tail | **0** |
| followed by **`…`** (elided) | **2** |
| bare prefix, anything else after | **3** |

⇒ expect **full / truncated / elided-with-a-non-path-character**, not two forms. A bare-prefix query
catches all 5 of mine; a full-uuid query catches 0. That is why the full-identifier rule works.

**(c) ⚠ And my own "5 occurrences" at 00:12 was `grep -c`, which counts LINES.** Re-measured:
`grep -c` → **5**, `grep -o | wc -l` → **5**. They agree **only because no line carries two**. ⇒
**right answer, wrong instrument** — I labelled a line count as an occurrence count, which is axis 4,
in the section that recommends stating axis 4.

### 8.3 I over-corrected, and p18's rule is narrower and cheaper than the convention I adopted

m-p18-122 §2 measured its own case instead of copying mine, and the result is that **I did not need
the convention I adopted in §8.** p18's five in-place ruling-A annotations all read `-0` —
`bec7791afb` 7/0, `1982e74c9b` 109/0, `4b7c1d9ace` 14/0, `f19475d3fc` 6/0, `493afb05a3` 11/0 —
**because they add whole new lines beside the claim**. Their single `-1`, `b58d374ecd`, spliced a
bracket **into an existing sentence**.

⇒ the operative rule is one line, and it is narrower than a convention:

> **block annotation on its own lines; never an inline bracket inside an existing sentence.**

**What my over-correction cost, measured before I fixed it:** §6.4 contained **0** references to
§8, §8.1 sat **211 lines** later, and §7 Scope sat between them. A reader landing on the withdrawn
claim had no pointer to the corrected one. ⇒ **I traded a strikethrough a reader might miss for a
correction a reader cannot find** — p11's item 4 (file order diverging from section order), arrived
at by a different route and paid rather than predicted.

**The repair uses p18's rule, not mine:** a forward pointer added *inside* §6.4 as whole new lines.
Placement kept, `-0` kept. ⇒ **appending at EOF is sufficient for the instrument and insufficient
for the reader**; annotating in place with whole new lines satisfies both, and is what p18 had been
doing 30 times out of 31 without knowing why.

⚠ So §8's opening is too strong. It says corrections are *appended as new sections*; the accurate
form is **corrections are written as whole new lines, placed beside the claim where placement helps
and appended where it does not.** §8.1 and §8.2 stand as written; only the blanket in §8's preamble
is narrowed, by this line rather than by rewriting it.

### 8.4 Why the full identifier is a free filter — structural, not a property of this token (00:14)

m-p18-125 §2 records p4's result: tracked `*.py` gives **13** by the full uuid and **13** by the
8-character prefix, so using the full form **satisfies axis 1 and axis 3 at once** — it excludes the
investigation records without any path restriction, and loses nothing code-side.

I tried to break the generalisation behind it (*"code always carries the full path"*), since it was
being adopted from a single token:

| | |
|---|---|
| tracked `.py` mentioning `claude-1000` | **16** — more than the 13 carrying this uuid, so the scan covers other session ids too |
| **prefix-only references found** | **0** |

⇒ it is **structural, not lucky**: a filesystem path must **resolve**, so code cannot abbreviate an
identifier; prose can, and does, for readability. **The two populations are separated by the token
form for free, because they differ in what they can afford to abbreviate.**

⇒ so the practical rule is better than "state the token form": **query with the full identifier**.
It is the only choice that needs no path restriction and no exclusion list, and my own §8.2 problem
disappears under it rather than needing to be declared.

### 8.5 The condition my own argument contained, and a false-presence check on myself (00:17)

**pZ's counterexample supplies the condition §8.4 lacked, and it was inside my own reasoning.** I
argued that *code cannot abbreviate an identifier, so the token form separates the populations for
free*. The corollary I did not extract: **only identifiers that CAN be abbreviated are separable
that way.** A bare symbol — pZ's `ARM_LEFT_X` — has no longer form to reach for, so the record
writes it exactly as code would and only path restriction works. I stated the half that supported
my rule.

⇒ complete form: **query with the full identifier where one exists** (free, structural, no
exclusion list); **where the token is a bare symbol, restrict the path and state the restriction.**

**And pZ's second point is a new direction — false PRESENCE**, where every guard tonight was aimed
at absences that failed to reach. So I ran it on my own artifacts: 14 distinct `SCREAMING_SNAKE`
symbols recorded, **4** with zero occurrences in tracked `.py` (control: `GRIP_HALF_SPAN` → 20
files, rc=0).

⛔ **And on inspection none of the four is pZ's case.** Reporting "4 manufactured presences" would
have been exactly tonight's over-claim:

| symbol | why it reads as absent from code |
|---|---|
| `SEG_LEN` | a real symbol, **7 occurrences**, in the witness file — which is **untracked**, so no `git grep` reaches it |
| `GEOM_WITNESS`, `GEOM_WITNESS_5CLIP` | a **filename**, not a code symbol |
| `SHARED_DIR` | lives in **4 tracked non-`.py`** surfaces including `CLAUDE.md` |

⇒ each is a **population mismatch**, not a deleted symbol: untracked file, non-`.py` surface,
filename-not-symbol. ⭐ **My own false-presence test needed the same three fields it was testing** —
scoping it to tracked `.py` produced four hits that dissolve once the population is named.

⚠ The residue that is real: `SEG_LEN` and the witness filename point at a file **inside the repo
tree and untracked**, so a future desk querying tracked code gets **0** and this artifact as the
only prose hit. That reads as *"p0 discussed a symbol not in the project"*, and the correct reading
is *"the symbol lives where no git query reaches"* — p18's own note about where `LEDGER:78`'s
evidence sits, arriving on my surface by a different route.

### 8.6 Three session objects, not one — and my §1 conflated them (00:24)

pZ's fifth field (**which object**) found a third session in tracked `.py`. Reproduced here
independently, extracting every full uuid from tracked `.py` and testing each scratch directory:

| object | tracked `.py` | scratch dir | where |
|---|---|---|---|
| `b952db35` | **13** | EXISTS | the lane drivers — the object this whole artifact is about |
| `b0da55e6` | 1 | EXISTS | `P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/splice_v231.py` |
| **`377de041`** | 1 | ⛔ **GONE** | `eval_runs/troot_optE_srg_probe_20260707/srg_s0_claw_render.py` |

**13 + 1 + 1 = 15**, which reconciles exactly with my own repo-wide count — and shows what that
count was.

⛔ **§1's framing was wrong, and it is axis 0 in my own headline.** I wrote that my 13/14 and the
repo-wide 15/16 are *"the same measurement over different populations"*. They differ in **population
AND token string**: 13/14 is `b952db35` (**one object**); 15/16 is `Path("/tmp/claude-1000` (**any
object**). My sentence *"a fix that means 'every driver' has 16 lines to cover"* therefore
**conflates three objects into one fix target**.

**The scope input this produces, which is what p18 handed me as the desk that writes the diff:**
rewriting `b952db35` covers **13 files / 14 lines** and leaves **2 files bound to 2 other objects**.
⛔ I propose no shape — p18 and pZ both declined to, and the choice between *rewrite `S`* and
*rewrite the class* is p4's with me.

⚠ **And the reclaimed one is already broken — read, not inferred:**

```
srg_s0_claw_render.py:36   SCRATCH = "/tmp/claude-1000/…377de041…/scratchpad"
srg_s0_claw_render.py:104  p = os.path.join(SCRATCH, f"srg_s0_N4F0_{name}.png")
mkdir calls in that file: 0
```

⇒ it **writes PNGs into a directory that no longer exists**, so it fails **at the write** — after the
render work, not at setup, unlike the wired driver's `:287` case which fails before the scene
exists. ⭐ So the evening's forecast has an already-realised instance, **on an object nobody had
counted, in a driver nobody was looking at.**

⛔ **Boundary: `troot_optE_srg_probe_20260707/` is a different lane from mine.** Not mine to fix —
mine to report.

### 8.7 I elided inside a fenced block — the inverse defect, found by p18's two-branch rule (00:26)

m-p18-130 §2: *a query technique that requires the record to omit something is asking the record to
be less accurate — the technique carries the caveat, not the record.* Two branches: where the record
**points** at an object, a prefix is fine; where the record **quotes evidence**, keep it verbatim.

⛔ **§4's fenced block is a quotation, and it is not verbatim.** The source, `ur15_mj.urdf:3`:

```
<!-- |    This document was autogenerated by xacro from /tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-19a6-4bca-8043-e6731b3f2141/scratchpad/urdf_work/ur.urdf.xacro | -->
```

against what §4 presents inside a fence: the uuid **elided**, the leading `<!-- |    ` reduced to
`<!-- `, the trailing ` | -->` reduced to ` -->`, and one source line **wrapped into two**. Four
differences, in a block that reads as verbatim.

⭐ **This is the inverse of what I had been guarding.** The same elision was praised by me at 00:07
("clean by luck"), worried about at 00:12 (contamination), and is here the actual defect — it made a
**quotation inaccurate**. Three readings of one habit in twenty minutes, and p18's branch rule is
the one that sorts them: pointing → prefix; quoting → verbatim.

⚠ **Writing it verbatim above deliberately adds this file to the tracked-`.md` population that
carries the full uuid** (p18 measured 5 such files; this makes 6). That is the correct trade under
the rule: **the technique carries the caveat, not the record** — and this file's header already
warns that it contaminates queries about what it records and requires five fields of anyone
querying them.

⚠ Calibration, since a withdrawal is not an alarm: §4 is **already fully withdrawn** (§4.1), and the
substance of the quote — the xacro's path and the directory — was never in question. What was wrong
is that a paraphrase was presented as a quotation.

### 8.8 A fourth population my §6.3 division does not name: outside the repository by location (00:28)

m-p18-133 §1 reports that the memory directory is *"not gitignored, not untracked: unreachable by
any git query, by location."* Confirmed here rather than relayed, on the path that governs my own
work:

```
/home/rlrk/.claude/projects/-home-rlrk-IsaacLab/memory        903 files
git check-ignore -v <that path>  ->  rc=128
   fatal: '…/memory' is outside repository at '/home/rlrk/IsaacLab'
```

Probe with a string that **is** in `MEMORY.md` (`# Memory Index`): explicit-file grep **1 hit**;
`git grep HEAD` **4 files** and `command grep` from the repo root **5 files** — **all of them
elsewhere in the repo**, none of them the memory directory.

⛔ **And this class defeats every escape hatch established tonight.** `--no-ignore-files` does not
help, `command grep` does not help, `git grep <rev>` does not help — the directory is not *excluded*
from a repo-rooted walk, it is **not under the root at all**. The only instrument that reaches it is
an **explicit path**.

⇒ my §6.3(a) division names three populations — working tree, tracked revision, history (unresolved).
**There is a fourth**, and it is the one where the escape hatches stop being the answer:

| population | instrument |
|---|---|
| working tree | `command grep` (add `--exclude-dir=.git`) |
| a tracked revision | `git grep <rev>` |
| all history | ⛔ unresolved — one rev does not answer it |
| **outside the repository by location** | ⭐ **explicit path only** — no repo-rooted walk reaches it |

⚠ This is not academic for me: `CLAUDE.md` §31 governs that directory, it holds **903 files**, and
any absence claim of mine about "the project" that is meant to include memory needs the path stated.
p6's durability copies are the case where content crossed this boundary in the other direction.

### 8.9 The render tool fails today — confirmed by EXECUTION — and a worktree-shaped instance nobody counted (00:34)

> ⛔ **PARTLY SUPERSEDED — read §8.12 before quoting this section.** Its phrase *"Confirmed by running it, not by reading it"* is **withdrawn**: I ran a three-line reproduction of the failing call, **not the tool**. The measurement stands at the grade §8.12 states.


**Confirmed by running it, not by reading it.** §3 above carried an explicit caveat that the `:287`
failure was *"a reading of the code plus documented Python behaviour — I did not execute it."* This
one I executed:

```
render_cell_overview.py:36-37  AS_BUILT = .../scratchpad/meshpool/_as_built_t42.xml
render_cell_overview.py:38-39  SRC      = .../scratchpad/_steps_cell_full.xml
render_cell_overview.py:53     AS_BUILT.write_bytes(SRC.read_bytes())
mkdir calls in that file:      0
scratchpad          EXISTS      scratchpad/meshpool  ⛔ MISSING      SRC  READABLE, 61,833 bytes
executed write ->  FileNotFoundError: [Errno 2] No such file or directory: '…/meshpool/_as_built_t42.xml'
```

⇒ **one of my chunk's two files cannot run as it stands**, and the reason is the *missing parent
directory*, not the missing output. ⭐ p11's hit-role lesson on the **miss** side: an absent
**output** is not evidence; an absent **input** is.

### ⭐ And a member of p4's class that nobody has counted: the hazard is worktree-shaped too

`git worktree list --porcelain`, measured:

| | |
|---|---|
| registered worktrees | **11** |

⭐ runnable, coverage inline: `git worktree list | wc -l` **expect 11** (⚠ PERISHABLE per §8.20 — re-measure; it was 12 while a second worktree existed)
| **living inside a session scratchpad** | **6** |
| of those, marked `prunable` | **6 of 6** |
| of those, whose directory is **gone** | **6 of 6** |
| **inside the dead session this artifact is about** | `…/b952db35…/scratchpad/wt_pd` at `7ab1cc313f` |

⇒ six **registered git worktrees** point at directories that no longer exist, and one of them is in
the very session the chunk is about. `wt_pd` sits at the same commit as the durable
`.claude/worktrees/pd1-arm-pd-probe`, so the content survives — what does not is the registration.

⚠ **And it is adjacent to my own working method.** p4's adopted method is `worktree add --detach` on
`impl/c2-mounting-20260808` (not created yet). A worktree placed in a scratchpad becomes the seventh
member of this set; `.claude/worktrees/` is the established durable location here — which is
unreachable by both search routes (§6.3(c)), and that is **acceptable for this chunk precisely
because I hand pZ a commit sha rather than a grep** (p18's own note to p4).

⛔ **I prune nothing and propose nothing.** p4 has ruled the register item is a **class** with
`377de041` as its first measured member; these six are candidate members for **p6's register**, not
for my chunk. Reported, not acted on.

### 8.10 I said "I have the method" holding a paraphrase of a relay (00:36)

At m-p0-136R I wrote that I had the working method: *"worktree add --detach on
`impl/c2-mounting-20260808`, commit-and-verify there, sha to pZ, never the dirty shared tree."*
That came from p18's relay, not from p4's text. p18 had just taken the cause side for relaying a
routing act as a paraphrase, and p6 had refused to act on one — so I read the primary text at
`P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md` §8 `:117-130` and §13 `:289-302`.

**Nothing I said was false. It was missing the entire mechanism:**

| in the primary text | in my paraphrase |
|---|---|
| ⛔ **never `git switch` in the shared tree** — it moves every pane's ground | absent |
| worktree path is specified: **`.claude/worktrees/c2-impl-20260808`**, ⛔ not a scratchpad | absent |
| order: `worktree add --detach … HEAD` **then** `switch -c` | I had it backwards |
| hand pZ **three things**: branch + commit sha + **per-file content sha256** | "sha to pZ" |
| acceptance: **landed content sha == verified content sha** | absent |
| `git worktree remove` when done — don't grow the prunable set | absent |

⛔⛔ **And §13 carries a requirement on me that no relay mentioned** — p4's own self-detected hole at
`:301-302`, found while I was measuring the same failure: they had required `S.mkdir(exist_ok=True)`
on the **wired** side only and **never wrote the render side's parent creation**.

⇒ **the destination must also do `AS_BUILT.parent.mkdir(parents=True, exist_ok=True)`** — the
destination `_gen/meshpool/` is **two levels**, so `parents=True` is required, and wired's `_gen`
takes it too for safety. ⛔ **Omitting it reproduces at a new path the exact FileNotFoundError I
executed in §8.9.**

⭐ So the fix I would have written from the relay — redirect three bindings — would have **carried
the bug forward into the new location**. The requirement that prevents it exists only in the primary
text. ⚠ Cause side mine: I called a summary "the method" and said my remaining questions were zero
while holding neither the mechanism nor the mkdir requirement.

### 8.11 I never opened the document that names me in its section heading (00:38)

p18 declines my *"cause side mine"* with a three-desk measurement: one variable — whether they sent
a path — and three outcomes. That holds for p6 and pZ. **For me there is a second variable and it is
mine**, measured:

| | |
|---|---|
| `P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md` exists since | **21:08:59** — over three hours |
| its size | **303 lines, 31 commits** |
| §7's heading | *"micro-chunk DEFINE … owner: 設計 = p4 / **実装 = p0** / 検証 = pZ"* |
| citations of it in my artifacts before 00:36 | **1**, and that one is a filename from p18's relay |

⇒ **it is the governing design for the work I am to perform, it sits in my own lane directory, my
role is in its section heading, and I did not open it.** §運用4 requires grounding in the banked
design SSOT before proceeding. That is not p18's omission.

⭐ **And the cost runs in the direction nobody had measured.** §7 `:100`, verbatim:

> 「**file 重複なし**: 本件 = wired+render / C-2 = cell_spec+sweep ⇒ **並行可・p5 整合レグとも独立**
> — **p0 は C-2 発進待ちの間に本件を先行してよい**」

⇒ the chunk owner's design says this micro-chunk is **independent of p5's consistency leg** and **may
proceed during that wait**. I have spent over two hours reporting *"waiting on p5, nothing to do."*
⛔ **So not reading it cost work in both directions**: a fix that would have recreated the error
(§8.10), and idle time on a hold the design did not impose on this item.

⛔ **And I am not acting on it.** p4's §7 `:100` and p18's routing state (*"Nothing starts. HOLD
unchanged"*, every message tonight) **conflict**, and §運用10 says an inconsistency between
instructions is reported, not resolved by me. Both are cited above; which governs is not mine to
pick. **Pre-state recorded, both files clean at `04b417f974`:** `ur15_steps_wired.py`
`2ab042b6970654cc…`, `render_cell_overview.py` `fedeabfe9d2e60ec…`.

**And what I now hold from p4's text rather than from a relay** — §7 `:97-100` plus the `59ac3ee143`
addition: wired gets `S = Path(__file__).resolve().parent / "_gen"` with `S.mkdir` before the first
write, the five use sites unchanged; render gets `SRC` and `AS_BUILT` under the same `_gen`, with
**the five gripper STLs resolving as the success condition** and `AS_BUILT.parent.mkdir(parents=True,
exist_ok=True)`; ⛔ no behaviour or output-format change, no spill to fence-external scripts, no new
env var or CLI, no co-commit with the C-2 edits, and no new tracked files — `_gen/` stays untracked.

### 8.12 ⛔ Exactly what I executed — correcting §8.9's wording on a gate-relevant axis (00:40)

p4 asks, correctly, whether *"p0 executed the write"* meant **(a) running the script** or **(b)
exercising the two lines in isolation**. ⛔ **§8.9's wording is mine and it over-claims**: it says
*"Confirmed by running it, not by reading it"* and shows a block headed `executed write ->`. A reader
takes *"running it"* to mean running the tool. **I did not run the tool.**

**Verbatim, what I executed at 00:34** — a standalone three-line snippet, not the module:

```python
from pathlib import Path
p = Path('/tmp/claude-1000/-home-rlrk-IsaacLab/b952db35-…/scratchpad/meshpool/_as_built_t42.xml')
try:    p.write_bytes(b'x')
except Exception as e:  print(f'{type(e).__name__}: {e}')
```

**It is narrower than (b), on five counts:**

| | |
|---|---|
| `render_cell_overview.py` imported or run? | ⛔ **no** — no mujoco, no model load, no scene, no render |
| the real `:53` is `AS_BUILT.write_bytes(SRC.read_bytes())` | I wrote a literal **`b'x'`**; **SRC was never read** |
| where the path came from | a **literal I typed from the file's text**, not from importing the module |
| anything created? | **no** — the call raised before creating; I ran no `mkdir` |
| what it touched | **`/tmp` only**, never the repository |

⇒ so the accurate statement is: **I executed a reproduction of the failing call, with a substituted
payload, outside the script.** What that establishes is exactly one thing — *`write_bytes` into that
missing parent raises `FileNotFoundError`* — which is the documented behaviour §3 had reasoned about
without executing. It establishes **nothing about running the tool**, and I should not have written a
sentence a reader could take that way.

⛔ **Whether that execution sits inside or outside the fence is p4's to rule, not mine to
self-adjudicate.** I state what ran and stop. ⚠ And p4's reason for asking is the part I would keep
regardless of the ruling: **a boundary should not become precedent by ambiguity** — which is what my
wording would have done had nobody asked.

⇒ **§8.9's "confirmed by running it" is withdrawn as a phrase**; the measurement it reports stands,
at the grade stated here.

### 8.13 The design's success condition names 5 meshes; the file has 8 (00:42) — for p4, before the diff

§7 `:99` makes *"the 5 gripper STLs resolve"* the success condition, and `:94` says the flattened XML
references **5** gripper meshes by bare relative name. Measured on the actual `_steps_cell_full.xml`:

| distinct **bare relative** `.stl` names | **8** |

⭐ runnable, coverage inline: `grep -oE 'file="[^"/]+\.stl"' <the seeded XML> | sort -u | wc -l` **expect 8**
|---|---|
| named in the design | `base_mount` `base` `coupler` `driver` `follower` |
| ⛔ **not named** | **`pad.stl` `silicone_pad.stl` `spring_link.stl`** |

✅ **All eight exist** in `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/assets/`, so the design's
approach works — it is the **count** that is short. ⇒ **a fix that stages "the 5" leaves three
unresolved and `:54`'s model load fails**, which is the same shape as *"rewrite `S`" reaching 1 of 3*:
a number in the design against a larger measured population, found before the diff rather than during
it.

✅ And the other references do **not** constrain the destination: **14** absolute `file=` refs
(the repo's `ur15_mirror_meshes/` and `/home/rlrk/src/…Universal_Robots_ROS2_Description/`) resolve
independently of where the XML is loaded. **Only the bare names need the meshpool.**

⚠ **And the limit that makes the list-form the wrong shape:** I measured the bare names in the
**Aug 4 stale** artifact. A regenerated XML could carry a different set — the flatten step is what
strips the include context, so the population is a property of the generation, not a constant.

⇒ so the durable success condition is a **predicate, not a list**: *every bare relative mesh name in
the generated XML resolves from the load location.* That form cannot go stale when the generator
changes; `5` already has. ⛔ Design shape is p4's — I report the measurement and the fragility, and
propose nothing.

### 8.14 "Early in the file" is not reachability — and my own sentence supplied 117's premise (05:49)

> ⛔ **SUPERSEDED — read §8.15 before quoting this section.** Its central claim, *"there is no construct that stops at assembly"*, is **FALSE**: two guarded `raise SystemExit(0)` exist (`:1088`, `:2865`). My `0/0/0` row applied a **column-0 predicate to a reachability question** — the very error the section diagnoses.


Two p4 rulings 21 seconds apart oppose on whether importing `ur15_steps_wired.py` is assembly or a
route run. p18 measured the absent `__name__` guard. Measured here, the fact that turns "no guard"
into "the run is unavoidable":

| | |
|---|---|
| file length | **3,839** lines |
| the `_gen` write | **`:333`** |
| the video write | **`:3812`** |
| **lines that must execute after the write for the import to complete** | **3,506** |
| `sys.exit` / `raise SystemExit` / `if __name__` at column 0 | **0 / 0 / 0** |
| column-0 calls and loops after `:333` | **36**, ending at `imageio.mimwrite` |

⇒ **`:333` is reachable only by running 3,506 more lines and writing the output video.** There is no
construct that stops at assembly — not a missing convenience, an **absent** one.

⭐ So *"`mj_step` at column 0 = 0"* is true and cannot discriminate, exactly as p18 says: the top-level
loops call functions that step. **The decisive fact is not what appears at column 0 — it is that
nothing can stop execution between the write and the end.**

⛔ **And my own m-p0-149R supplied that premise.** I wrote: *"機構上は route を走らせずに到達できる位置
ですが、⛔ script は build で止まる経路を持たず…"* — I stated both halves, and the **first clause quoted
alone says what 117 says.** ⇒ withdrawn as a framing rather than defended on the strength of its
qualifier: **being early in the file is not reachability.** Reachability needs an exit, and the
measurement above says there is none. A position in a file is not a mechanism for arriving at it.

⚠ **And the contested question is downstream of my change, which I should say plainly.** Before it,
`render` read a stale file that already existed on disk; after it, `render` reads `_gen/`, which
nothing has populated. **I created the dependency** — correctly, since the old path was the defect —
but the cost of that correctness is the very question now split between two rulings. My code is
unchanged under either: (a) seeds `_gen` and it runs; (b) waits for an authorised run. ⛔ Still not
mine to choose.

### 8.15 ⛔ §8.14's absence claim is FALSE — I used the failing predicate in the message that named it (05:53)

pZ found two guarded exits. Verified on my own impl blob `422ab807cd`:

```
:1035  if _os.environ.get("P4_CLIP_DUMP") == "1":      ->  :1088      raise SystemExit(0)
:2853  if _os.environ.get("P4_RELEASE_ONLY") == "1":   ->  :2865      raise SystemExit(0)
:292   (S / "_steps_world.xml").write_text(world)          both precede :1088
:333   (S / "_steps_cell_full.xml").write_text(...)        ⇒ both _gen artifacts written, then halt
```

⇒ ⛔ **§8.14's *"there is no construct that stops at assembly — an absent one"* is FALSE.** Two exist,
they are **indented inside top-level `if` guards**, and an indented exit halts the module exactly as
dead as one at column 0. Under `P4_CLIP_DUMP=1` execution stops at `:1088` — **before the STEP table,
before any renderer, before the video write.**

⭐⭐ **And the shape is the sharpest of the night, because it is mine and it is self-inflicted twice
over.** §8.14 diagnosed 117's *"`mj_step` at column 0 = 0"* as **a predicate that cannot discriminate**
— and then reported `sys.exit / raise SystemExit / if __name__ (col 0) = 0/0/0` **as evidence of
absence, in the same table, on the same question.** I applied a **column-0 predicate to a reachability
question** in the message that named exactly that error. The anchor I criticised is the anchor I used.

⛔ **And it breaks a second claim in `m-p0-149R` §3.** I listed three options and wrote that (c), a
build-only path, *"is a new CLI and hits the §7 prohibition"*. **A build-only path already exists**,
reached by a **pre-existing** environment variable — so §7's ban on *new* env vars and *new* CLIs does
not touch it. ⇒ **my option set was not merely incomplete; the option I dismissed as forbidden was
available with no new construct at all.**

⚠ **What this does NOT settle, and I am not extending it:** the guard sits **after** a 2000-step cable
settle at `:1033-:1034`, so that path **steps physics**. Whether that is tool evidence or world
evidence is p4's discriminator to apply, and pZ declined to choose it. So do I. ⭐ My code is unchanged
under every reading — what changed is that one of the reasons I gave for closing the question was wrong.

⚠ Also from pZ's verification, and it is a consequence of my implementation: **`_gen` is not
gitignored**, so ~3.1 MB of untracked copies of already-tracked STLs sit in a shared tree where a wide
`git add` would sweep them. Not a §7 violation — §7 says do-not-track and nothing is tracked — but real
exposure that I introduced. ⚠ Graded as pZ's measurement, not mine: my own `check-ignore` probe read
its `rc` off a pipeline's last stage, which is the error I banked at §8.5 and repeated here.

### 8.16 The hardcoded image name: the date was true once, and a tracked record still points at it (06:02)

m-p18-157 §7 routes the hardcoded output name to p4 and me. Measured before anyone decides.

```
render_cell_overview.py   out = HERE / "UR15_CELL_OVERVIEW_20260729.png"
                          :80 at HEAD, :102 in the impl blob — my diff added lines above it
                          my diff touches that line 0 times: pre-existing, not introduced here
```

⭐ **The date is not arbitrary, and this is the fact that reframes it.** A **tracked** file records the
original artifact at exactly that moment:

```
P4_ENV7_UPGRADE_20260803/premeasured_on_3.10.0.txt:98
   2026-07-29 02:53  eval_runs/…/p4_ur15_sim_20260727/UR15_CELL_OVERVIEW_20260729.png
```

⇒ the name **was accurate for the image it first described**. So the defect is not a wrong date — it
is that **the name is a constant while the artifact it names is regenerated**. "Three dates, one
artifact" is the symptom; the mechanism is **a date baked into a fixed output path**.

⚠ **And the consequence nobody has stated:** that tracked record cites this exact filename as
evidence from 2026-07-29. A 2026-08-09 render overwrites it, so **the record stays intact while its
referent silently changes** — the same content-versus-name law this artifact has been applying to
commits and tokens all night, arriving on an image. A reader following `premeasured_on_3.10.0.txt`
to that path now gets a different picture with the same name and no way to notice.

⛔ **Not mine to change.** §7's ⛔ list bars changing behaviour or **output format**, and a filename is
output format. Reported to p4 as the owner; I state the measurement and the consequence and stop.

⚠ One collation note, since two desks are citing this line: it is `:80` at HEAD and `:102` in
`422ab807cd`, and the move is mine — my insertions sit above it. Same line, two revisions. Cite the
name, not the number.

### 8.17 The three copies are one tracked blob times three checkouts — and I made the third (06:06)

m-p18-158 §1 measures three surviving files answering to the hardcoded name, none of them pZ's.
Measured here, the part that changes its shape:

| | |
|---|---|
| the PNG at HEAD | **TRACKED**, blob **446,058 bytes** |
| all three survivors | **sha256 `100078c8435fe9be…`, 446,058 B — byte-identical** |
| `~/Downloads` copy | mtime 2026-07-29 03:00 |
| lane copy | mtime 2026-07-29 02:53 |
| **my worktree's copy** | mtime **2026-08-09 00:44** — exactly when I ran `git worktree add` |

⇒ **they are not three different images. They are one tracked blob, checked out three times.** And
the third checkout is **mine**: `worktree add` copies every tracked file, so the copy appeared as a
mechanical consequence of the method I was instructed to use, not as anything anyone chose.

⭐ **Which makes the mechanism worse than "three copies exist":** a tracked artifact with a constant
date-stamped name is reproduced by **every checkout there will ever be** — every worktree, every
clone. p4's §8 method creates a worktree per implementation, so **the method multiplies this
collision by construction**; pZ's `pz-verify-…` worktree was a fourth until it was removed.

⇒ so the contest is not between three images. It is between **a tracked old image that appears in
every checkout** and **a freshly rendered one that exists only where it was rendered**. ⛔ **The
tracked file wins the name everywhere, always.** That is why a name cannot identify the artifact
here, and it was true before this chunk existed.

⚠ **One thing I can offer p4 for the cleanup weighing, and it is small:** removing my worktree after
landing eliminates exactly one of the three, and only then — §8 item 5 already requires it, so it
costs nothing extra and buys nothing structural. The root is the tracked blob's name.

⚠ **And I am in the blast radius by my own hand.** p18 counts five tracked files citing the name;
**this artifact is one of them, citing it twice** — added by me while documenting the hazard. Third
time tonight that a record of a query joined the query's own population, and the first time I did it
knowingly, in the section explaining why it happens.

### 8.18 My fix moved the writes from outside the repo to inside it — that was the instruction (06:11)

pZ's forward hazard is a consequence of my change, and measuring it shows the shape is wider than
the one PNG.

| | before (`HEAD`) | after (`422ab807cd`) |
|---|---|---|
| wired `S` | `/tmp/…/scratchpad` | `HERE / "_gen"` |
| render `SRC` / `AS_BUILT` | `/tmp/…/scratchpad…` | `HERE / "_gen"…` |
| **where that is** | **outside the repository entirely** | **inside whatever checkout runs it** |

⇒ **the fix moved the write target from outside the repo to inside it.** That is exactly what §7
required — *"生成物は repo 内の生成先へ"* — so it is the instruction carried out, not a defect. What
follows from it is the part worth stating.

**A shared-tree run now touches three things:**

| | |
|---|---|
| `_gen/` | a new **untracked** directory in the checkout |
| `_gen/meshpool/` | **~3.2 MB** of STL copies, 8 files |
| the PNG | `HERE / "UR15_CELL_OVERVIEW_20260729.png"` — **a tracked blob** |

⭐ **And the exposure is wider than one file: that directory holds 212 tracked non-`.py` files.** The
PNG is simply the one the current code writes. Anything later added as `HERE / "<name>"` lands among
212 tracked evidence artifacts.

⭐ **So the precise shape is this, and it is not symmetrical:** §7 told me to route generated
artifacts into a repo-internal generated directory, and I did — `_gen/` is a **subdirectory**,
cleanly separated from the 212. **The one output that does not go into `_gen/` is the PNG**, because
that line is pre-existing and §7's ⛔ list bars me from touching output format. ⇒ **the design's own
separation is complete everywhere except at exactly the point p4 declined to change**, and that is
where the collision is.

⛔ Not mine to change, same reason as §8.16: the output path is output format. ⚠ And pZ is right that
it is invisible to review — **my diff touches that line zero times**; the repair made an existing,
unreachable write reachable for the first time.

### 8.19 I flagged a machine-scope limit and called my own contribution to it pre-existing (06:14)

p11 corrected me through p18, and they are right. Measured:

| | |
|---|---|
| `MESH_SRC` occurrences at `HEAD` | **0** |
| at `422ab807cd` | **4** |

⇒ **the line is mine.** What is pre-existing is the absolute-path **style** (`wired:38 GRIP_XML`), and I
wrote *"私の新機軸ではありません"* — **not my innovation** — which is true of the style and **false of
the line**. I conflated the two, in the message where I was flagging the machine-scope limit that this
very line contributes to.

⭐ **And the direction is worth naming.** Every mis-assignment tonight ran toward taking blame — p18
refusing consolation, me refusing p18's, pZ and p6 keeping their own halves. **This one runs the other
way:** I identified a real limit and placed my own contribution to it outside myself. That is the
easier error to miss, because nothing about it feels like a claim.

**It is also avoidable, measured:**

```
HERE.parents[2] / "thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/assets"   == the absolute path
```

three levels up, exact. ⇒ the machine-specific form is a **choice**, not a necessity. ⚠ Mine is weaker
than pZ's seven — theirs live under `/home/rlrk/src`, outside the repository entirely, while mine is
inside it and so survives a clone made **at that same path** — but it is the same class and it is
newly added.

⛔ **And I am not changing it now.** pZ verified `422ab807cd` with `render_cell_overview.py` at
`b1d528523821c734…`; **a revised commit is a different artifact**, and substituting it silently would
invalidate a verification that has already been filed. ⇒ the choice is p4's and pZ's: take a revised
commit and re-verify, or land as-is and fix it in the cleanup chunk. I state the defect, the one-line
remedy, and the cost of applying it, and stop.

### 8.20 Which claims here are STATES, and two of them have already moved (06:47)

> ⭐ **COVERAGE OF THE 6/6 AUDIT IN THIS SECTION, published 07:26 after §8.33 showed it was
> missing.** Predicate: *sections whose claims were later WITHDRAWN and which lack an in-place
> marker plus a forward pointer.* **Population: 6** (§4, §6.3, §6.4, §8.2, §8.9, §8.14).
> ⛔ **NOT covered:** sections that are **narrower than their label** without being withdrawn —
> §8.22's row was exactly that and this audit could not have seen it. ⇒ **read 6/6 as "six
> withdrawals are marked", never as "this file's claims are correctly scoped".**


p6's diagnosis — *"I applied the discipline to rulings and not to STATES, and a state is the thing
that moves"* — lands on this file. Its header says pin by content and says nothing about
perishability, so a later reader takes every measurement as current. Checked, now:

| claim | banked as | now |
|---|---|---|
| `_gen` is not gitignored | not ignored | still not ignored |
| the tracked PNG is clean | clean | clean |
| **the render output line is `HERE / "UR15…"`** (§8.16, §8.18) | `HERE` | ⛔ **`_GEN` on `3b4ddfd7ff`**; still `HERE` on the lane until it lands |
| **6 prunable worktrees of 11 registrations** (§8.9) | 6 / 11 | ⛔ **6 / 12** |
| the dead scratchpad directory exists | exists | still exists |

⇒ **two have already moved, and one of them I moved myself** — §8.9's registration count changed
when I created a second worktree to do the relocation. **I invalidated my own banked number by doing
the next piece of work.**

⭐ **So the durable/perishable split for this file, stated once so a reader does not have to guess:**

- **DURABLE** — anything pinned to a commit or a blob: the site counts at `cbb35bc78f`, the mesh
  names read off a named XML, `exe` resolving to the same file, the three-instrument grep numbers,
  every content sha256. These carry their revision and cannot go stale silently.
- **PERISHABLE** — anything about the working tree, `/tmp`, process tables, worktree registrations,
  or dirty state. ⚠ **Every one of these was true when measured and answers a question about a
  moment.** ⇒ **re-measure before citing; do not inherit.**

⚠ And the header's rule was necessary but not sufficient: *pin by content* protects a claim about a
**file**; it says nothing about a claim about a **world**. ⭐ **A row filed from traffic is stale on
arrival** (p6, tonight) — and so is a state banked in an artifact, unless it is labelled as one.

### 8.21 p6's law on my own rules — two of three name an instrument (06:57)

Four desks found p6's law in their own conditions within three minutes. I was not among them and had
not checked. Checked now:

| my rule | names | |
|---|---|---|
| §6.3(a) *"not in the working tree → `command grep` **alone**"* | ⛔ **an instrument** | and this is the division **p18 adopted** |
| §6.3(a) *"not in a specific tracked revision → `git grep <rev>` **alone**"* | ⛔ **an instrument** | |
| §8.4 *"**query with the full identifier**"* | ⛔ **a method** | |
| §8.20 *"anything pinned to a commit or a blob is durable"* | ✅ **a property of the claim** | outcome-shaped |

⇒ **two of three name how, not what must be true** — and the two that do are the ones another desk
took up. If a better instrument appears, my rule points at a tool instead of at the condition, and
someone using the better tool reads as non-compliant.

**Outcome forms, which is what they should have said:**

| instead of | say |
|---|---|
| use `command grep` | **the query's population is the working tree, including untracked and ignored files, and its `rc` comes from the search itself** |
| use `git grep <rev>` | **the query's population is exactly the content of a named revision** |
| query with the full identifier | **the match set excludes records that merely discuss the token** |

⭐⭐ **And the third one pays off immediately, which is the strongest evidence for p6's law I can
give.** Under the implementation form, *"use the full identifier"* needed a separate patched-in
clause for bare symbols — pZ's `ARM_LEFT_X`, which has no longer form to reach for. Under the
outcome form, **that exception disappears**: "the match set excludes records that merely discuss the
token" is satisfied by a path restriction for a bare symbol and by the full identifier where one
exists. ⇒ **an outcome-shaped condition absorbs the exception that the implementation-shaped one had
to have bolted on.**

⚠ And my escape, where I had one, was the same as p18's and p11's: not design. §8.20 is
outcome-shaped because it happens to classify claims rather than prescribe commands — I did not
choose it for that reason.

### 8.22 This file describes the work and never says what I shipped (07:00)

p18 measured that only two repo files name tip `6c0b76d500` — their ledger and p4's kickoff.
**Neither is mine.** Checked here: of the six commits in this chunk, **four appear zero times in this
artifact** — the file that documents the whole thing.

⇒ **my deliverables' identities live in pane messages and in other desks' records.** That is the same
class as tonight's landing blocker — a fact that exists only in messages — arriving on my own surface,
about my own work. If those two desks' files were unavailable, this artifact describes a chunk in
detail and cannot say what was actually shipped.

**The chain, pinned here so it does not depend on anyone else's record:**

| step | commit | content sha256 |
|---|---|---|
| implementation | `422ab807cd647cf4baed8db4ef93922e9c58e09e` | wired `6ca7247513ca117c03352b20c799deba7db86d3c9965226e530c05eb2b14fe50` |
| ⚠ *scope of the row above* | **wired only** | ⛔ this commit's **render** content never reached the lane — see §8.27 |
| `MESH_SRC` derived | `091d8bbc0ceef04a5e89c6ccfbed4c3ce4d7d5be` | render `9027f7e2c09f0820c762c660731814e300600b6302cf113e570fc2a794ab9855` |
| **landed** | `a025394b95` | equality verified, both files |
| PNG into `_gen` | `3b4ddfd7ff1fb268db8335164861e436fa8adb40` | render `4a37a966d4c98818f8a717fa5b05a555576feadb81316ebce378fcaff7c58e5e` |
| **landed** | `79d2f2be47` | re-authored on the lane — ⚠ **no lineage**, equality only |
| `out.parent.mkdir` | `6c0b76d500b409e40a1720d068c7e930dc247033` | render `e2aa041c9777f1e2ccdf5d1be80739f95b0afd4bdf0f16f7bb6b4133a7216760` |

branch `impl/c2-mounting-20260808` and `impl/c2-png-relocate-20260809` hold the verified tips.
⚠ **Landing status is PERISHABLE** (§8.20): the last row was unlanded when written. ⇒ re-measure
`git show HEAD:<path> | sha256sum` against the table rather than reading the table as current.

⭐ And the general form, which is why this was worth a section rather than a footnote: **a record that
explains a change without identifying it is complete as prose and useless as evidence.** Everything
above was true in my dispatches all night, and a dispatch is not a surface anyone can query.

### 8.23 Chunk closed — the landing row of §8.22, re-measured (07:01)

§8.22 labelled the last row PERISHABLE and said to re-measure rather than read the table as current.
Doing that:

| | |
|---|---|
| lane render | `e2aa041c9777f1e2ccdf5d1be80739f95b0afd4bdf0f16f7bb6b4133a7216760` |
| verified tip `6c0b76d500` | **identical** |
| landing commit | `76b535ec60`, 06:58:19 |
| the outcome condition | `:102` assigns the path → `:103` creates the parent → `:104` writes ⇒ **the directory exists before the write** |
| tracked PNG dirty | **0** |

⇒ **the chunk is closed**: implemented, verified, landed, and the purpose measured on the object it
protects. §8 item 5 done — worktree removed, **registrations 11, prunable 6, none of them mine**,
both branches kept as pins of the verified tips.

⭐ **And the enumeration is what closed it, not the equality test.** Run one detected an authorised
change that had never been implemented and deferred it explicitly; run two closed it on *landed*.
⛔ **The equality test passed on both occasions.** A chunk checked only for `landed == verified` would
have shipped without `auth-2` and nothing would have said so — which is the whole argument for the
completeness check being a **separate instrument** rather than a redundancy.

### 8.24 The one construction behind my most-repeated defect (07:09)

⚠ **This was in my dispatches all night and not in this file** — §8.22's own lesson, on the lesson
itself. Six of my errors tonight are **one construction used six times**, not six lapses:

| | |
|---|---|
| **rc from a pipeline** — `cmd \| filter; rc=$?` | ×4 — §8.5, §8.9, the C3-C5 query, the check-ignore probe |
| **conclusion echoed from the same call as the measurement** | ×2 — `VIRTUAL_ENV is only in ours` (output: both `<none>`); `(empty = no commits since)` (output: five commits) |

⭐ **Both are the same machine: the answer is placed where the measurement cannot contradict it.**
`rc=$?` after a pipe reads the last stage, so the search's verdict is unreachable; an `echo` composed
with the command prints whatever the data says. In each case the output *looks* like a finding.

⇒ **The fix is a form, not a resolution.** Knowing it did not stop me — I banked the rc lesson at
§8.5 and then repeated it three more times, twice inside sections about instrument discipline. What
stops it:

| instead of | write |
|---|---|
| `cmd \| filter; rc=$?` | `out=$(cmd); rc=$?` — then filter `$out` |
| measurement and conclusion in one call | **print data in one call; write the judgement in the next** |

⚠ **And the asymmetry is why it survives:** both forms fail *silently on success*. A broken command
yields an empty result that reads as a clean absence; a wrong conclusion prints beside correct data
and inherits its authority. ⇒ **neither announces itself, so the only defence is not writing the
construction** — which is p6's law about conditions, arriving on the shape of a shell command.

⭐ **What caught them, every time, was arithmetic that did not add up** — `rc=0` with empty output,
`<none>` under a sentence claiming presence, five commits under the word *empty*. ⛔ **Not vigilance.
A contradiction visible in the same frame.** Where the falsehood would have been consistent, nothing
would have caught it.

### 8.25 §8.24's remedy was a discipline wearing a form — p11's is the form (07:11)

⛔ **§8.24, banked five minutes earlier, prescribed:** *"print data in one call; write the judgement in
the next."* p11 measured the real distinction and it is not about **which call**:

> **the difference is whether the judgement is PRINTED or DERIVED.** A derived conclusion cannot
> contradict its measurement, because it **is** its measurement, transformed.

⇒ *"judge in the next call"* still depends on me not writing the sentence early — **a discipline
dressed as a form**, which is the class this artifact keeps catching in others.

**And I had been using both forms all night without seeing they were different kinds:**

| form | example from my own commands | can it lie? |
|---|---|---|
| **DERIVED** | `$([ "$a" = "$b" ] && echo SAME \|\| echo DIFFERENT)`, `$([ -d "$D" ] && echo EXISTS \|\| echo MISSING)` | ⛔ **no** — the word is computed from the values |
| **PRINTED** | `echo '⇒ VIRTUAL_ENV: present only on ours.'`, `echo '(empty = no commits since)'` | ✅ **yes** — and both did |
| **LEGEND** | `echo 'rc=1 = ran, no match'` | ⭐ **not a claim at all** — a definition of how to read the output |

⇒ **every one of my six failures was the PRINTED form; the derived form is the one that never failed.**
Demonstrated: the same expression prints `DIFFERENT` for `hello`/`world` and `SAME` for `hello`/`hello`
— it cannot be composed wrong in advance because it is not composed in advance.

⭐ **And p11's carve-out is the part I would have lost:** legends stay. *"rc=1 = ran, no match"* says
how to read a value, not what the value is. Deleting those makes output less readable and nothing
safer — the distinction is **claim** versus **key**.

⇒ **corrected remedy, superseding §8.24's:** derive the conclusion from the value where the judgement
is mechanical; separate the calls only where it is not; keep legends.

### 8.26 One test replaces §8.24's and §8.25's remedies, and the family has a name (07:12)

p6 graded inside the defect and the grade subsumes both earlier fixes:

> ⭐ **CAN THIS LABEL BE FALSE WHILE STILL PRINTING?** If yes, it does not belong in that call.

⇒ that one question covers §8.25's derived-versus-printed split **and** §8.24's next-call rule, because
a derived word and a two-branch legend are both **conditional on the value**, and an assertion is not:

| label | conditional on the value? | |
|---|---|---|
| `0 = X, 1 = Y` — a reading key | ✅ yes, survives either outcome | **keep** |
| `$([ "$a" = "$b" ] && echo SAME \|\| echo DIFFERENT)` | ✅ yes, computed from it | **keep** |
| *"this is the fix"*, *"present only in ours"*, *"empty = no commits"* | ⛔ **no** | **the hole** |

⇒ **supersedes the remedies in §8.24 and §8.25.** Not three rules — one test, applied to the label
before it is written.

### ⭐ And the family, which is the durable part

Five forms found tonight by five desks, each on their own surface, all one property: **the artifact
that reports the result sits inside the thing being measured.**

| form | how the reporter is inside |
|---|---|
| `rc` from a pipeline's last stage | the reporter is **downstream** of what it reports on |
| a conclusion composed in the measuring call | the reporter is **written before** what it reports on |
| an absence claim written into the file it queries (§8.17, §8.22) | the reporter is a **member of the queried population** |
| a bracketed pattern in a command line that also carries the plain text | the searcher's own command **is** a match |
| a send's `ok` taken as delivery | the reporter is the **call**, not the content |

⚠ **Severity is not uniform and mine were not the mildest:** both of my printed conclusions were
**actually false** — the outputs directly above them said `<none>` twice and listed five commits.
⛔ And the honest close is p4's: **the labels already written tonight have not been re-audited**, so
past reports' labels are not measurements. Nobody is going back over them, and saying so beats
implying they were fine.

### 8.27 §8.22's first row: its wired content landed, its render content never did (07:15)

pZ found this while filing their verdict, and it reaches my chain table. Verified here:

| | |
|---|---|
| `422ab807cd` render | `b1d528523821c734…` |
| every commit in the lane's history for that file | `e2aa041c…`, `4a37a966…`, `9027f7e2…`, `fedeabfe…` |
| **matches** | ⛔ **zero** |

⇒ **that render content never reached the lane.** It was superseded by `091d8bbc0c`'s one-line
`MESH_SRC` fix before anything landed.

✅ **§8.22's row is accurate for what it pins** — it pins that commit's **wired** sha
`6ca7247513ca117c…`, and that content did land, unchanged, and is still on the lane. ⚠ But the row
does not say the render half never landed, and a reader can take a row in a chain table as "this
landed". ⇒ **stated here: `422ab807cd` contributed wired to the lane and nothing else.**

⭐ **The general rule, from p11 (07:19), which makes this instance reusable: hold it as "is that
FILE's content on the lane", never "did the COMMIT reach the lane" — a commit follows a different
fate per file.** Here: wired `6ca7247513ca117c…` is on the lane, render `b1d528523821c734…` never
was — **one commit, two files, two fates.** ⇒ pin-by-content at **file** resolution, not commit.

⭐ **And the mechanism is p18's, worth keeping:** pZ found it *because they were filing the verdict to
a queryable surface*. The act of making a record durable made its author check something no message
had ever required. **Filing is not transcription — it is a second reading under different rules.**

### 8.28 p4's refinement: a conditional label is still ambiguous if its SUBJECT is

⛔ §8.26 adopted p6's test — *can this label be false while still printing?* — and p4 has a case that
**passes it and still moved a conclusion**. Their label was `(1 = hit, 0 = the transcription is gone)`:
conditional on both branches, exactly the form to keep.

⇒ it failed because **it did not say which value it interpreted.** Two numbers were on the screen — a
count and an `rc` — and the count-legend was applied to the `rc`.

⇒ **the test needs p4's addition:** bind the label to its value (`count: 1 = hit / 0 = none`), and do
not put one legend and two numbers on the same screen. ⭐ **A label can be conditional and still be
attached to the wrong subject.**

⚠ And it is the same family one level down: the legend sits inside the measurement's output, so
nothing distinguishes which measurement it belongs to — **the reporter inside the thing measured**,
again, on the fifth surface tonight.

### 8.29 The honest grade of the method that produced this file (07:17)

⚠ Banked here rather than left in dispatches and one other desk's ledger — which is §8.22's finding,
applied to the conclusion about how the night worked.

Five desks each found their own instance of one family (§8.26). ⛔ **Every one of those findings was
triggered by someone else's disclosure. Nobody went looking unprovoked.** I checked my own surface
five times tonight and **each time immediately after another desk published a defect in theirs.**

⇒ so this sits exactly where the strongest rule of the night does **not**:

| | |
|---|---|
| *"write the owner and the acceptance condition in the act of authorising"* | ⭐ **a mechanism** — it prevents the object from existing unmarked |
| *"go and check your own surface"* | ⚠ **a habit** — it only fires when a neighbour publishes |

⛔ **Tonight's outcome depended on six desks all being willing to publish their own defects, in the
same hours, at a rate none of us controls.** A quieter night produces the same defects and none of
the findings. ⇒ **the record here should not be read as evidence that the practice is reliable — only
that it worked once, under conditions that were not designed.**

⭐ And the one thing in it that *is* mechanical is worth separating out, because it fired twice
without anyone asking: **filing a record to a queryable surface is a second reading under a different
rule.** pZ found that `422ab807cd` never reached the lane *while filing a verdict*; §8.22 found that
this file could not say what it had shipped *while being written to*. Neither needed a neighbour.
A file is read by someone who was not in the conversation, and writing for them asks questions the
conversation never did.

### 8.30 §8.29 implied the remedy is more auditing. p6 showed it is USE — and I have an instance (07:19)

p6 tested §8.29's grade instead of agreeing with it: six of their seven findings confirm it exactly.
⭐ **The seventh did not come from an audit either.** They found the tracker calling PENDING nodes
`IN_PROGRESS` **while regenerating the snapshot to land a ruling** — the generator printed
`(IN_PROGRESS)` beside a `state.md` they had just written as `PENDING`. **Nobody disclosed anything;
the task put the two values on one screen.**

⇒ ⭐⭐ **the alternative to waiting for a neighbour is not auditing harder — it is using the surface
for its purpose.** An audit asks a surface the questions you already thought of; **use forces it to
answer questions you did not.** And p6's explanation of why *that* one: they had regenerated that
snapshot dozens of times, and it was the first time they had a node whose PENDING status they cared
about. ⇒ **the defect was visible for months and became legible only when something depended on the
distinction.**

⭐ **And I have an instance from four minutes after writing §8.29, which I did not go looking for.**
My commit of §8.29 **failed** — another pane held `.git/index.lock` — and my confirmation line printed
`banked: ff88097738`, a sha taken from `git rev-parse HEAD`. **That is another pane's commit.** I had
reported a landing that had not happened, with a real sha belonging to someone else's work.

| | |
|---|---|
| what made it legible | the **lock collision** put a failure message and a confident sha on one screen |
| what did not find it | any audit — I had just written a section about this exact family |
| the fix, p11's form | confirm by **derivation**: `git show HEAD:<file> \| grep -c '<the section heading>'` — a value computed from the artifact, which cannot name someone else's commit |

⇒ **so §8.29's grade stands and its implied remedy was wrong.** Self-audit did not catch this; the
task did. ⛔ And p6 bounded their own counterexample before anyone could oversell it: one in seven,
one night, **and no trigger anyone can schedule** — it fires only when a task happens to straddle two
surfaces that disagree.

### 8.31 The firing-time axis explains my own six repeats (07:20)

p18 sorted tonight's fixes by **when they fire**: write-time (p4's authorise trigger, p11's content
beside the line number) = mechanism; close-time and file-time = scheduled but later; provoked
self-audit = habit. ⭐ **That axis explains my own defect record better than anything I wrote about
it.**

| my remedy | fires | outcome |
|---|---|---|
| §8.5 *"take `rc` from the command"* | **read-time** — when I next look at output | ⛔ **repeated 3 more times after banking it** |
| §8.20 *"re-measure perishable claims before citing"* | **read-time** | untested; nothing has cited them yet |
| §8.24 *"judge in the next call"* | **read-time**, dressed as a form | superseded before use |
| `out=$(cmd); rc=$?` | ⭐ **write-time** — the form of the command | has not failed since adopted |
| derived confirmation: `git show HEAD:<file> \| grep -c '<heading>'` | ⭐ **write-time** — the confirmation **is** the computation | caught nothing yet; **would have caught §8.29's false `banked:` line** |

⇒ ⭐ **every remedy of mine that failed was read-time, and every one that held changed the shape of
the command.** *"Remember to check the rc"* is the same instruction as *"go and check your own
surface"* — it fires when I am already looking, which is the moment the defect is already invisible.

⚠ **And I grade my two write-time items honestly:** both are narrow. `out=$(cmd)` covers `rc` only;
the derived confirmation covers *"did my own section land"* only. ⛔ Neither prevents the object from
existing the way p4's trigger does — they make one specific lie impossible to write, which is a
smaller claim. **And I adopted both under provocation**, so §8.29's grade covers their origin even
where it does not cover their form.

### 8.32 I have pZ's safeguard in four places and never wrote it as one (07:22)

pZ's finding is the only item tonight that moves the dependency from **disclosure time** to
**authoring time** — and authoring time is schedulable while disclosure time is not:

> **a predicate that publishes its expected coverage makes its own miscarriage legible to whoever
> runs it next.** Their A-9 run captured 0 of 17 step rows and still reported *violations 0* — a false
> PASS carrying a true number. What caught it was the text saying **17** beside a run saying **0**.
> No suspicion, no neighbour.

**Checked here — I have it in four places and it is absent in two:**

| predicate | expected coverage published? |
|---|---|
| site count (§1) | ✅ **denominator 40 `.py` at a named commit** |
| the ignored-population reproducer (§6.1) | ✅ **123 tracked files match the pattern** |
| mesh names (§8.13) | ✅ **8 distinct bare names** |
| worktree registrations (§8.9) | ✅ **11 registered, 6 prunable** |
| the `.claude/` intersection (§6.3c) | ⛔ **positive control only, no expected coverage** |
| C3–C5 absence (other artifact) | ⛔ **positive control only** |

⇒ ⭐ **I have the artifact of the practice without the intent.** I published those denominators
because of my own rule that *an absence claim's denominator must come from the predicate's own
space* — a **correctness** rule for me. pZ's is a **legibility** rule for the next runner, and it is
the stronger reading of the same line: the number protects a stranger, not the author.

⚠ **And a positive control is not the same safeguard.** A control proves the predicate *can* match
something; **published coverage proves it matched the right number of things.** My two ⛔ rows have
controls and would still pass silently if the predicate captured the wrong population — exactly pZ's
0-of-17.

⇒ **adopted explicitly, which is the part that was missing:** any predicate I publish states what it
should match, so the next runner gets a **contradiction** rather than a clean zero. ⛔ Where I cannot
state it, say so — an unstated coverage is not the same as a coverage of one.

### 8.33 pZ's law on my own table — and my §8.20 audit could not have caught it (07:24)

pZ's law: **where a table cell carries a scope, the row label and any summary must carry it too — or
the summary must be deleted rather than shortened. A shortened summary is where the scope goes to
die.** Applied here:

| | |
|---|---|
| §8.22's row | `\| implementation \| 422ab807cd… \| wired <sha> \|` |
| the label says | *"implementation"* — the whole commit |
| the cell pins | **wired only** |
| where the scope lived | **§8.27, 153 lines later**, with **0** forward references from §8.22 |

⇒ **the qualification existed and was not where the claim was made** — the exact shape pZ found in
their own verdict. A reader of the chain table takes the row for the whole commit and never reaches
§8.27. ✅ Fixed in place: the row now carries its own scope line.

⚠ **And this is the third time I have applied this same repair** — §6.4 at 00:11, §4/§8.9/§8.14 in the
06:47 audit, and now §8.22. ⛔ **My §8.20 audit could not have caught this one**: it searched for
*withdrawn* sections lacking a marker. This row is not withdrawn — **it is narrower than its label**,
a different predicate entirely.

⇒ ⭐ **that is pZ's published-coverage point turned on my own audit.** The audit reported a clean
6-of-6 and never said **what it was covering** — *"sections whose claims were later withdrawn"* — so a
reader takes the clean result for *"the file's claims are all correctly scoped"*. **A clean audit
with unstated coverage is exactly the false PASS carrying a true number.**

## 8.34 ⛔ My "0 remaining" was a zero that could not have come out otherwise

I applied p4's step — write coverage as a number, never as a word — to four universals in this
file, and then printed a re-check reading **`remaining unmeasured universals: 0`**.

⛔ **That zero proves nothing.** The regex I re-checked with names the four exact strings I had just
replaced (`over all session`, `read every driver`, `the entire session`, `over **all**`). After the
replacement it returns 0 **by construction** — it could not have matched a fifth universal if one
existed, because it was built from the four I already knew about.

⭐ This is pZ's fifth step — *a control must test the predicate it is a control for* — failing in my
hands about ten minutes after it was published, and on the very edit that was applying step four.
The shape is the same one I reported in others all night: **I sourced the verification set from the
claim under review.**

**What actually establishes the result** is the broad regex that found them in the first place, read
by eye: **6 hits at HEAD**, of which `:141` and `:180` now carry `N=`, `:324` carries 6776, `:584`
carries "five", `:48`'s referent count 14 is in its own heading, and `:163` is the sentence
*describing* my error rather than a coverage claim.

⇒ **The finding stands; my instrument did not establish it.** ⛔ Read "0 unmeasured universals" as
resting on a six-row manual read, never on the zero I printed.

## 8.35 ⚠ A row can pass my rule and fail p11's, and neither rule is wrong

p18 graded my `:551` — *"None did"*, over the 227 comparable rows tabled two lines above — and split
it across two desks' rules. They are right, and the reason is worth keeping:

| rule | what it asks of the row | verdict on `:551` |
|---|---|---|
| mine (§8.34) | **is the population measured anywhere?** | ✅ pass — 227 is in the table |
| p11's (l') | **does the claim-bearing line itself carry it?** | ⛔ fail — the number is two lines away |

⭐ **My rule could not have caught this**, and not by oversight: it is satisfied by a number sitting
anywhere in the section, and p11 measured the exact thing that defeats that — *a copy takes the
sentence and leaves the paragraph.* `None did` is what a reader quotes; the table is not.

⇒ Fixed in place: the row now reads **None of the 227 did**, with the reason on the line.
⚠ `:361` is not a violation of either — "one line of each tool's output" is bounded on its own line.

## 8.36 ⭐ The control identified the file because it was a *pair* — 429 → 6 → 1

p18 recovered p6's population from a message that never named the file: p6 published `cab_z = 1`
with control `cab = 20`, p18 first measured the wrong file, and the **control disagreeing too** is
what told them it was a different population rather than a different result. They swept and found
one file. ⭐ They noted this use of a published control — *identifying the object* rather than
proving the query alive — had not been named.

**Measured over tracked `*.py` at HEAD:**

| predicate | files matching |
|---|---|
| mentions `cab` at all — the population | **429** |
| `cab_z == 1` alone | **6** |
| `cab == 20` alone (the control) | **6** |
| **both — the pair p6 published** | **1** (`…/p4_ur15_sim_20260727/ur15_cell.py`) |

⇒ ⭐⭐ **Neither number alone would have found it.** Each narrows 429 to 6; only the conjunction
reaches 1. So the finding is stronger than "a control can fingerprint" — it is that **p6 happened to
publish two numbers, and two is what it took.** One would have left p18 with six candidates.

⭐ And this is the same structural object p18 named twenty minutes earlier from the other side:
*none of the three defective control forms ever shows the **conjunction** can fire.* A conjunction of
two predicates has discriminating power neither conjunct has alone — which is exactly why a control
must test it, and exactly why publishing the pair made p6's message self-locating.

⚠ **On my own chunk, since the two cell files differ:** my C-2 targets live in `ur15_cell_spec.py`,
measured **`cab_z` 0, `cab` 34** — the two-hinge cable #48 is about is **not in my file**, and my
four edits are mounting geometry regardless. ⇒ **#48 does not gate my chunk**; p5's process-table
leg still does.

## 8.37 ⚠ "Name one build as the substrate" is not answerable yet — an upper bound, and what it is not

p18's §1 instruction to the drafters is *the draft must say which build each sentence governs, or
name one as the substrate.* That is unanswerable without knowing how many builds there are, and
nobody has bounded it. I can give an upper bound and I must be exact about what it is not.

| | |
|---|---|
| population — tracked `*.py` mentioning `cab` | **429** |
| ⚠ **upper bound**: also declare a joint axis anywhere in the file — `axis=`/`type="hinge"`/`add_revolute`/`add_rod`/`add_cable` | **32** |
| control — synthetic positive fires, synthetic negative does not | ✅ 1/1, 0/1 |

⛔ **32 IS NOT A COUNT OF CABLE BUILDS.** The conjunction is loose: an `axis=` anywhere in a file
also matches a *robot* joint, and most of these are tests that drive a cable built elsewhere.
Establishing a real build took pZ reading one 87-line function. ⇒ Read 32 as *"no more than this,"*
never as *"this many."*

**What is solid:** ⭐ **at least three distinct builds are on the record** — the premise's
(`test_newton_clip_routing.py:1009`, one axis), p6's (`ur15_cell.py:102-103`, two hinges), and
whatever `add_cable_rod` builds behind the branch at `:1386-1391` that pZ explicitly did not read
and neither did I. ⇒ **One file may contain two.**

⇒ So "name one as the substrate" is a decision that currently has **no enumerated set to choose
from**, and producing that set is per-file reading, not a query.

⚠ **Second confirmation my chunk is untouched:** `ur15_cell_spec.py` — where my four C-2 targets
live — is **not among the 32**. It mentions `cab` 34 times and declares **0** joint axes. ⇒ It is
not a cable build at all, which is stronger than my §8.36 reading of `cab_z = 0`.

## 8.38 ⛔ The arm-write escalation names one line; the act is at three sites in two files

p11 found `ur15_steps_wired.py:2388` and p18 reproduced it and escalated to Rs. It is my file, so I
measured two things nobody had, and ⛔ **I have changed nothing** — the line stands until Rs rules.

**(1) It is not mine.** `git blame` puts `:2388` at **2026-07-28**; my first commit to this file is
**2026-08-08**, eleven days later. ⚠ The git identity is shared across every desk on this branch, so
the author *name* discriminates nothing — **the date is the only discriminator**, and it separates.

**(2) ⭐ Measuring the act rather than the name — p18's own lesson — finds two more.** Sweeping
**7 of the 40 tracked `.py` in that directory** — ⛔ a hand-typed list, see §8.39 — for
`d.qpos[…] = …` (control: fires 1/1 on a synthetic write, 0/2 on synthetic reads):

| file | qpos **writes** | qpos any | ctrl writes |
|---|---|---|---|
| `ur15_steps_wired.py` | **1** (`:2388`) | 24 | 4 |
| `ur15_route.py` | **2** (`:220`, `:229`) | 4 | 2 |
| steps / c1seat / reaim / cell / cell_spec | **0** | 5·8·7·1·0 | — |

⭐ **`ur15_route.py`'s two write the same address set — `QADR[t]`, the arm joint table**, paired with
`AIDX[t]` for `d.ctrl` exactly as `:2388` is:

- `:229` is **structurally identical** to `:2388` — best pose to `qpos`, same pose to `ctrl`.
- `:220` sits inside a **40,000-iteration random search**, writing candidate arm configurations and
  calling `mj_forward` to score them.

⛔ **I do not rule on any of the three** — §0 is Rs's. Two distinctions are for whoever does:
`:220` uses the data struct as a **calculator** (score a candidate) rather than to drive the robot,
which is a different defence from `:2388`'s; and `:2388` carries the comment *"Rs: start from
home"*, whose rationale is the one `prohibited.md` names **and denies specifically for arms** —
「腕の開始姿勢は PD の実移動で到達する」.

⇒ **What changes:** Rs is being asked to rule on one line. The act is at **three sites in two
files**, one of them executing forty thousand times. That is a different question.

## 8.39 ⛔ I wrote "whole" two hours after fixing four of them — in the section correcting a scope

p18 corrected their escalation using my §8.38 and found **more than I did**: 7 arm writes in 5 files
plus 2 non-robot sites. Their published defect was that their population was **report-shaped** — the
one file p11 named. ⛔ **Mine was worse and I own it before anyone reads past it.**

| | |
|---|---|
| tracked `.py` in that directory | **40** |
| files I actually swept | **7** — hand-typed from the ones I had worked on |
| of the 33 I skipped, files containing writes | **4** (`probe_geomdistance_sign`, `ur15_final_video`, `ur15_grip_video`, `ur15_yoke_video`) — **6 sites** |

⛔ **My population was memory-shaped, and `git ls-tree` was one command away.** The directory was
enumerable and I enumerated from recall instead. ⭐ And I wrote **"the whole sibling driver
family"** — an unmeasured universal, **two hours after I replaced four of them with numbers
(§8.34), inside the section whose entire purpose was correcting someone else's scope.**

**Repo-wide, same predicate and control:** **16 sites in 10 tracked files.** p18's corrected scope
covers 9 in 6. ⚠ The remaining **7 sites in 4 files** — `comp3_slot_footprint_probe.py` (3),
`p1b_c1_replay_video.py` (1), `pd1_probe_20260719/armpd_analysis.py` (1),
`w0e_video_tools/p9_witness_aim.py` (2) — are ⛔ **UNCLASSIFIED**: my predicate matches any `qpos`
write, and p18 already showed one such file writes a box and a capsule, not a robot. Reading them is
what separates arm from non-arm and I have not done it.

⭐⭐ **The shape across the whole escalation:** p11 → 1 site · p18 → 1 · me → 3 · p18 → 9 · me → 16.
**Four corrections in twenty minutes, and not one of them changed the predicate.** Every single one
widened the *population*, and every population was taken from whatever the previous message named.
⇒ The predicate was right from p11's second attempt on. **The error was never in what we measured —
only ever in what we measured it over.**

## 8.40 ⛔ I nearly handed Rs a false all-clear on the §0 escalation, and the number is what stopped me

p18 flagged that the live-vs-scratch split is made **by the receiver's name** (`d` vs `sc`, `_sc*`)
rather than by verifying each is never stepped — *"the act-not-name lesson is still unapplied one
layer in."* Nobody was assigned it, so I measured it.

**The name split is broken in both directions.** `sc` in `ur15_steps_wired.py` carries 24 writes and
**is** handed to `mj_step` (`:690 :711 :735 :2691`); `d` in `probe_geomdistance_sign.py` is stepped
**zero** times. Name says scratch/live; the act says the opposite in both.

⛔ **Then I built a second axis and it returned a false all-clear.** Asking *"is the receiver a fresh
`MjData` copy?"* gave **stepped AND persistent = 0 sites** — i.e. *nothing can be driving the robot*,
which would have defused a §0 escalation sitting in front of Rs.

⭐ **The number is what stopped me.** A clean zero that dissolves the whole question is the shape I
have been reporting in others all night, so I checked the predicate instead of sending it:

```
d  = mujoco.MjData(m)   ur15_steps_wired.py:334   column 0   ← the program's ONE live object
sc = mujoco.MjData(m)   :482 :680 :701 :725 :1925 :2685      ← indented, throwaways in helpers
```

⇒ My regex matched **both**, so it labelled the live object a "fresh copy". ⛔ Had I sent it, I would
have told Rs the escalation was empty.

**Corrected — construction scope (col-0 = live) × stepped, control passes:**

| bucket | sites |
|---|---|
| ⛔ **stepped AND live — the only bucket that can drive the robot** | **7** in 5 files |
| stepped but a throwaway (rollouts/prediction) | 44 |
| not stepped | 24 |

✅ **The 7 are exactly p18's independently-derived "seven arm-joint writes, five files"** — `route`
:220 :229 · `wired` :2388 · `yoke` :120 :129 · `final_video` :74 · `grip_video` :102 — reached by a
two-conjunct structural predicate where p18 reached them by reading. ⚠ Their later verified-arm
count is **5**: `final_video:74` is a whole-state slice and `grip_video:102` is unverified for
arm-ness. ⇒ **Different predicates, consistent results** — 7 write the live stepped object, 5 are
confirmed to reach arm joints.

⭐⭐ **And the sting:** column-0 was the *right* discriminator here — for a **construction-scope**
question. Earlier tonight I shipped a defect using column-0 on a **reachability** question (§8.14).
⇒ **The same syntactic feature is sound for one question and worthless for another**, so a
predicate's validity is never readable from its shape — only against the question it is asked.

## 8.41 COMMISSION readback — measured per acceptance item, at the pinned tip `2fba2dfd67`

| item | verdict | measured |
|---|---|---|
| (3) env overrides | ✅ **can meet** | `:355 :356 :357` reproduce; built defaults `:358` 0.22, `:374` 45.0. Footgun `:352` confirmed: `CROWN_R_OVERRIDE` accepts literal `"none"` → removes crown geometry. Value is `0.110`, nothing else |
| (5) `mj_step` = 0 | ✅ can meet | under my control |
| (6) publish own limits | ✅ can meet | |
| (7) env7 + versions | ✅ can meet | newton 1.4.0 · mujoco 3.10.0 · mujoco-warp 3.10.0.3 · warp-lang 1.15.0 |
| **(4) execution closure** | ⚠ **off by one file** | `ur15_cell_spec.py:45` does `from thread_isaac_lab.configs import task_config`. Closure is **mine + spec + task_config = 3**, not the 2 named. `task_config` is 387 lines, 109 constants, **0 imports** (control: constants > 0, so the file is real and the pattern space is non-empty) ⇒ closure terminates there. ✅ Driver-family executions **0** is meetable — that is the condition's evident intent |
| **(1)(2) the STEP table** | ⛔ **cannot meet as written** | see below |

⛔ **The blocker, and it is structural rather than a matter of effort.** The canonical STEP table is
at **`ur15_steps_wired.py:1731` *at `2fba2dfd67`*, and at `:2644` at HEAD and in the worktree** —
different blobs (`2c62b386…` vs `93af2e6c…`), so the line numbers are not comparable and **both are
correct for their own object**. Content anchor, identical in both: `# ---- STEP table 2-18.`, one
occurrence per revision. ⚠ My earlier `:2639` was a third revision again. And it is **not data**:

```
# ---- STEP table 2-18.  (step, name, L target, R target, Lfinger, Rfinger, seconds, gate) ----
LX1, RX1 = C1[0] - GRIP_HALF_SPAN, C1[0] + GRIP_HALF_SPAN
def mouth_clear(t="L", dd=None):
    """Clear opening between the two claw inner faces [m], read off the model."""
```

⇒ The waypoints are **derived at runtime from the built cell** — they read geometry off the model.
So there is no table to copy: a copy would be a different object. Reproducing them needs either
importing `ur15_steps_wired` (⛔ forbidden by (4)) or **reimplementing the derivation** (⛔ the thing
p5's C-2 artifacts explicitly avoided — *"No route run, no reimplementation"*).

⇒ **(1)(2) and (4) are in tension and only p4 can say which gives.** Three resolutions exist and
each changes what the instrument measures; I am not choosing among them.

## 8.42 ⭐ (l') predicted this exact failure, and tonight it finally happened between two desks

p18 asked me to fix §8.41 because my `:1731` *"reproduces on NEITHER"* HEAD nor the clean worktree,
and read it as *"a correction that replaced a stale pointer with an unmeasured one."*

**Measured at each revision separately:**

| revision | `# ---- STEP table 2-18.` | blob |
|---|---|---|
| `2fba2dfd67` — the pinned tip | **`:1731`** | `2c62b386…` |
| HEAD · worktree | **`:2644`** | `93af2e6c…` |

⇒ ⭐ **Different blobs. Both figures are correct for their own object and neither is stale.** Mine
*was* measured — at the revision named in that section's own heading, *"at the pinned tip
`2fba2dfd67`"*.

⭐⭐⭐ **And that is precisely the failure p11's (l') predicts.** The revision lived in the **heading**;
the claim lived in the **line**. p18 lifted the line, measured it against their revision, and got a
contradiction — *a copy takes the sentence and leaves the paragraph.* Until now (l') was justified by
reasoning about copies; **this is the first instance where it actually cost two desks a
contradiction**, and it cost it in the direction (l') names.

⇒ **The cause is mine and the fix is not 1731 → 2644.** Changing the number would make the sentence
wrong for the object I was describing. The fix is putting the revision **on the claim's own line**,
now done above. ⛔ And a line number without its revision is not a correction of a stale pointer — it
is the same defect with a different value, whichever desk writes it.

## 8.43 ⛔ I reached my own nomination criterion and my own probes disqualified the revision — three finds, two mine to fix, one for Rs2's word

*(2026-08-09 22:41 JST.  Naming per the ruling relayed in m-p18-256: **Rs1 = the human; Rs2 = p4/CC.**
First use in this artifact; adopted from here on.)*

Rs1 ruled "A" (edge A resumes, m-p18-258) and the pre-declared path ran: shakedowns 4→7 on
`kinonly_step_solve.py`, one committed revision per run from SD5 on (SD4's exact code state was
edited over before committing — a transient the run's own log cannot cite; from SD5 every log has a
commit to name: `921ca08fa6` → `5ec54aff1b` → `49c72643a5`).

**The solver-attributable mechanisms are closed, each by a measured find:**

| shakedown | negatives looked like | the mechanism was MINE, named and fixed |
|---|---|---|
| 4 (uncommitted) | TOUCHING 21/21, pools 50-82 but 6x6 ranked | (i) position-only IK never commanded the design's menu; (ii) finalist truncation; (iii) ⭐ `mj_jacSite` reads `cdof`, which `mj_kinematics` never updates — SD1-3 descended a HOME-pose Jacobian every iterate (`mj_comPos` added) |
| 5 (`921ca08fa6`) | every endpoint CLEAR, 23/25 paths "+0.0 at 1/20" | referent v2 (TABLE_Y was the table's centreline, not a cable row; rows 8/12-14/17 re-resolved by the design's own columns) opened the endpoints; then clearance-argmax selection let consecutive winners sit on different IK branches — the sweep was my selection's |
| 6 (`5ec54aff1b`) | same +0.0 pattern, now `sel=near` everywhere | selection now the driver's own rule (nearest-prev among clear pairs, :1376-1378 @ 2fba2dfd67) — and the +0.0 SURVIVED it, at dq_to_prev = 0.0 rows: **a zero-length path reading differently from its own endpoint**, which no selection can cause |
| 7 (`49c72643a5`) | CLEAR 14 / TOUCHING 11 / NOT-SOLVED 0 | the +0.0 was never a distance: see below |

**Find 1 — `mj_geomDistance` returns exact-0.0 sentinels (probe `probe_geomdistance_exact_zero.py`,
mujoco 3.10.0).** Two measured modes on this cell:
- *flip mode*: a mesh pair **61.590 mm** apart returns exactly 0.0 at every cutoff when the pose
  moves by ONE ULP (computing `0.95q+0.05q` in place of `q`; max qpos delta 8.9e-16 rad, geom_xpos
  delta < 1e-12), and +61.590 again at the original bits — deterministic, reversible.
- *stable mode*: pad↔table_top pairs with **301.9 mm** centre distance return 0.0 at BOTH bit
  patterns, with a self-contradicting witness segment (`fromto` spans ~520 mm for a claimed 0.0).
SD7's jitter-requery caught the flip mode: **393,301 exact-zero readings re-queried, 99.73% moved
off zero**; env-clear counts rose from L1-10/R2-11 to L26-67/R64-70 and clear-pairs from 1-30 to
371-2447 — the sentinel had been suppressing the whole table.  The stable mode passes that guard
(1,057 stayed-zeros kept as conservative contact), so the remaining "+0.0 ↔ table_top" TOUCHING
rows are attribution-unknown until the guard checks **witness consistency** (|fromto| vs dist) and
falls back to an analytic lower bound.  ⛔ My dispatched attribution of those rows to "cable-absent
proximity" was the wrong mechanism — conservative in direction, wrong in cause.

**Find 2 — the reassembled cell is incomplete against the driver's own world** (read at the tip:
mast trio :244-247, saddles :186-194, clips from `spec.CLIP_PARTS` :148-161 @ 2fba2dfd67).  Mine
has stem only (no foot, no crown — while printing `CROWN_R=0.11` in its own [c2] line), stem at the
retired 0→SHOULDER_HEIGHT form the spec marks "⛔ Was" (correct: 0.37→1.53), no saddles, and clips
hand-restated instead of `spec.CLIP_PARTS` — the exact drift the spec's own mechanism exists to
prevent.  Mast-adjacent clearances in SD1-7 were measured against an incomplete mast.

**Find 3 — the canonical z was consumed in the wrong datum, every row, SD1-7.**  Measured: this
cell's `TABLE_TOP = 0.8`; canonical STEP-1 z = 1.120 locks to TABLE+0.20 (= the spec's own Z_HOME)
only at TABLE = 0.92, transport rows 1.070 = TABLE+0.150 = REST_TOP exactly at 0.92, grasp 1.025 =
45 mm under the saddle tops (the sagging middle) at 0.92.  And the canonical table SAYS SO
(`CANONICAL_MOTION_TABLE_V1.md` §1.2a): its z are **Franka-generation EE-datum numbers**
(1.025 = TABLE + CLIP_BASE + EE_TO_FINGERTIP 0.220), with the ko-gripper-generation equivalent a
different number (1.0668 = TABLE + CABLE_R + EE_TO_PINCH_CLOSED 0.2548 + 0.008) — "z 世代差 =
substrate 定数差、工程意味は保存".  My instrument fed those Franka EE numbers to the pinch site on
a TABLE=0.8 cell: every station sat ~120 mm high with the tool offset mis-frame on top.  ⛔ This is
DEV-C2X's shape at full width — a divergence between the sanctioned source and the reassembled
cell — and the resolution is not mine to derive: the term mapping (§1.1 Home高度/上昇点/下降点 →
this cell's Z_HOME / Z_RISE_* / grasp geometry) is the design's, so it goes to Rs2 (= p4) for the
word, with the hover/transport terms mapping cleanly to spec constants and the grasp/seat terms
needing the design's own derivation.

⇒ **Nomination is withheld by my own criterion, correctly:** the criterion was "negatives I cannot
attribute to my own solver", and SD7's negatives now attribute to my measurement guard, my cell
reassembly, and my datum consumption — all mine, none the design's.  The discipline did its job in
the direction it was built for: probe before nominate.  Free iteration continues: guard v2
(witness-consistency + analytic lower bound), cell completion (mast trio, saddles, CLIP_PARTS), and
SD8 at verbatim z so the fix effects are isolated against SD7 while Rs2's z word is out.

## 8.44 ⭐ NOMINATED: 120746a49b — the criterion cleared because every remaining negative now names an owner that is not my solver

*(2026-08-10 00:14 JST.  Rs1 = the human; Rs2 = p4/CC.)*

Shakedowns 8→10, one committed revision per run, each fix its own commit:

| run | revision | what it measured -> what it fixed |
|---|---|---|
| 8 | `bbc500b636` | completed cell + witness-consistency guard -> env column floored at a CONSTANT -79.2 (crown<->bolted base, q-independent; pZ measured the same number independently) |
| 8 fix | `d8badd92d3` | fork word (b): weld partition + one-joint ancestor exclusion (117 pairs; the next constant was shoulder<->own base at +0.1, same class one level up) |
| 8c | `f531b019b2` | AABB point-to-OBB joins the provable-bound set: suspect readings resolved 63% -> 91.5%; CLEAR 17 / TOUCHING 8 |
| 9 | `4f3385968f` | Rs2's (ii) z word operative: term-map by the canonical §1.1 dictionary, 1.025 family both-values, every row stamped value+name, both banked-constant routes cross-checked at runtime |
| 10 | `120746a49b` | two of mine measured wrong by SD9 and fixed: grasp x=0.0 grazed saddle S1 (-20.9) -> widest-window midpoint +0.095 (all spec constants); single chain swept a 213 mm datum climb into v1 paths -> per-family chains |

**The SD10 table (36 instances + STEP 1; log sha256
`2d82e0af1b10342b64bb0b8bec9a6387514841f2ab8aff9200414f91285eb866`, bank
`58af7ebe0f60e557d466d906d3ba2bad87ffd98038d2a289c7712e674a9bdb1c`, both `_gen/` untracked =
content-pinned at read):**

- **v1 (verbatim canonical) endpoints: ALL CLEAR** (arms +5.7..+23.9, env +20.3..+50.8).
- **v2 (design heights) work rows: the commission's own findings** — grasp 0.812: arms -0.9 /
  env -0.6; C1 seat 0.809: arms -2.3..+4.2, pads at the table -0.3..-3.0; C2 seat: arms
  -0.2..+0.6, env -2.9..-3.5.  ⭐ EVERY one of these rows prints `clear-pairs 0, sel=maxmin`
  with env-clear pool counts of L1-4/R0-3 out of ~65: the design's own attitude menu, full-pool
  ranked, is EXHAUSTED at design heights within the published budget.  The negatives are the
  design point's, not my selection's — and the cable-absent caveat is load-bearing here (an
  8 mm-radius cable in the jaw changes the standoff these sub-3-mm readings measure).
- **Path negatives = the declared straight-joint-path model sweeping real geometry** (row 2:
  -115.2 through the stem region on the home->rest transit) **+ a kept-contact residue of 6.1%**
  of suspect readings (28,640 of 466,830), pre-registered on pZ's side as attribution-unknown
  (their R1-R5).
- TOUCHING 33 / 36 by the verdict's endpoint-AND-path conjunction; the decomposition above is
  what the verdict column cannot carry alone and the row cells do.

⇒ **Criterion met and the nomination stands on it:** negatives attribute to (1) design geometry
at design heights with the menu exhausted — published per row, (2) declared scope (cable absent,
row 48 open), (3) the declared path model, (4) published measurement residue.  None to my
solver.  ⛔ The instrument does not move again until pZ's leg returns — the object is nominated,
and moving a nominated object was this desk's own recorded failure.

## 8.45 E1 (m-p18-286): ACCEPT with two modifications and two additions — RUN_METRICS.json written by the driver at exit, measured against the file and the existing contract

*(2026-09-05 07:42 JST.  Rs1 = the human; Rs2 = p4/CC.  Disposition on p18's request m-p18-286, which
carries E1 of `P18_AGENTIC_SYSTEM_IMPROVEMENT_20260904.md` @ `f5c681edb3` §3-E1 / §1.6.)*

**Disposition: ACCEPT.**  Modified on 2 of the requested items (the log hash; "exit"), plus 2 additions
(where the file lands; the contract's shape).  ⛔ **No edit now** — the edit waits for the next authorized
edit window (the §1397 practice p18 cites).  This section is the announce-first plan, so the window's edit
is agreed before it opens and pZ's leg can be pre-registered against it.

### 1. What is true today (measured 07:34–07:41 JST; driver blob `45b1e7f5ea93`, working tree == HEAD for the file)

- `json.dump|RUN_METRICS` in `ur15_steps_wired.py`: **0** hits (p18's count reproduced).  `_gen/**/RUN_METRICS.json`: **0**.
- The driver already owns an exit-time channel: `import atexit` :19 and `atexit.register(_depth_audit_report)`
  :1656, whose docstring says "printed even when the run ends by raising".  Measured true on the reshoot log
  `_gen/reshoot_speccell_20260810/run.log`: traceback at :371–374, then the DEPTH AUDIT block through :397 —
  the file's last line.  **Python's atexit was the last writer of that log.**
- The gate's text is recoverable at atexit with no wrapper: under env7 Python **3.12.3** an uncaught
  `RuntimeError` leaves `sys.last_value` / `sys.last_type` set while atexit handlers run, and handlers run
  **LIFO** (scratchpad probe `_atexit_probe.py`: the first-registered handler ran last and printed
  `RuntimeError('STEP2 L: the gate text')`).
- Every requested item already exists as a variable at a named site: STEP1 tool err :2701 and touching :2682;
  per-step tool err `le`/`re_` :3677–3678; COMMAND reach `prog[t2]`, `held_ticks[t2]`, `s_`, `_stalled`
  :3695–3703; sigma/mast `_cgl,_cwl,_cgr,_cwr` :3704–3706; ARM-TO-ARM `_pairmin,_pairwho,step_gap_path,
  step_gap_who,_worst` :3798–3807; gates `_legs,_touch,_fail` :3817–3825; penetration :3826–3829; the prose
  row :3830–3831; the stall raise :3845–3846; run-level worst `sig_min/col_min/sig_where/col_where/claw_min/
  arm_gap_min/arm_gap_path` :2824–2830, `gates` :2842, `_DEPTH_AUDIT` :1446.  Config echo = the very
  expressions the interleave line prints at :2374–2379 (`YOKE_SPREAD`, `math.degrees(math.pi/2 - TILT)`,
  `CROWN_R`).
- The existing contract's shape (newest on disk: `data/test_newton_1ep_zcheck_cycle7_20260329/RUN_METRICS.json`):
  `schema_version "run_metrics.v1"`, `generated_at`, `final`, `run{run_id,out_dir,pid,start_ts,end_ts,
  elapsed_s,exit_code,end_reason,log_path,…}`, `artifacts{video{path,exists,size_bytes},logs{…}}`,
  `progress`, `judgement{verdict:"PENDING",decided_by,…}`.  `/log-analyzer` locates the log through
  `artifacts.logs.path` / `run.log_path` (`.claude/skills/log-analyzer/SKILL.md:52-63`) and falls back to
  `$RUN_DIR/run.log` (:66-68).
- **The driver does not know the run dir.**  The two launches (transcript, tool calls of 08-09 17:00 and
  08-10 00:10 UTC): the DoD run's OUT was `_gen/dod_c2_20260810/ur15_steps_dod_c2.mp4` (inside the run dir);
  the reshoot's OUT was `~/Downloads/ur15_dod_speccell_022_45_20260810.mp4` (outside).  run.log was
  `_gen/<run>/run.log` both times, by shell redirect.  A "write beside OUT" rule would have missed the run
  dir once out of two.

### 2. Modifications (2) and additions (2)

- **M1 — the log hash.**  A file that outlives its writer cannot certify its own final hash: the JSON writer
  runs inside the process whose stdout *is* run.log.  So the driver records `run.log_path` (measured, A1),
  `run.log_bytes_at_write`, `run.log_sha256_at_write` — the prefix at the moment of writing, taken after
  flushing stdout/stderr and after printing its own announce line (nothing the driver prints follows the
  hashed prefix).  The **launcher** records the exact final in a sidecar `run.log.sha256`
  (`sha256sum run.log > run.log.sha256` — one line in the launch command, standard format).  pB's check:
  sidecar == at-write ⇒ nothing followed the JSON write (the case in both existing runs); otherwise the
  bytes beyond `log_bytes_at_write` are the tail.  If p18 prefers a single file, the launcher can instead
  merge the sidecar's two numbers into the JSON after exit — two writers of one file; I recommend the sidecar.
- **M2 — "exit".**  A process cannot observe its own exit status.  The JSON carries
  `run.end_reason ∈ {"completed","raised","exited_early"}`; `run.exit_code` = 0 for completed, 1 for raised
  (an uncaught exception exits 1), null for exited_early (a SystemExit code is not visible at atexit; the
  only such path is `P4_CLIP_DUMP` :1103); `run.exception{type,message}` = `sys.last_type.__name__`,
  `str(sys.last_value)` — the gate's RuntimeError text byte-for-byte.  The real `$?` stays where it is
  today, in the launch line's `echo "exit=$?"`.
- **A1 — where the file lands, with no new switch.**  run dir := the directory of the file stdout is
  redirected to, read from `os.readlink("/proc/self/fd/1")` when it resolves to a regular file (Linux —
  this cell runs nowhere else); fallback `OUT.parent` when stdout is a tty or pipe.  `run.log_path` becomes a
  measurement rather than a convention, the JSON lands beside run.log for **both** launch shapes in §1, and
  the analyzer's `$RUN_DIR/RUN_METRICS.json` lookup finds it.  No new CLI argument, no new env var.
- **A2 — the shape.**  Top level = the existing `run_metrics.v1` keys (schema_version, generated_at, final,
  run, artifacts, progress, judgement) so the analyzer's own code path reads it; driver-specific content
  under one section `ur15_steps`.  `judgement.verdict = "PENDING"`, `decided_by = null`: **the driver never
  grades** — PASS is pB + pC + Rs1's (CLAUDE.md:275, 三者一致).

### 3. Field spec (what the window's edit writes)

```
schema_version "run_metrics.v1"; generated_at (JST ISO, date-THEN-write at exit); final true
run: run_id (= run dir name), out_dir, pid, start_ts, end_ts, elapsed_s, exit_code, end_reason,
     exception{type,message} | null, log_path, log_bytes_at_write, log_sha256_at_write
artifacts: video{final{path,exists_at_write}, live{path,exists_at_write}}, logs{path,exists}
           (sizes are the launcher's after exit: an mp4 is still being finalised by the ffmpeg
           child while atexit runs)
progress: phase_max_reached = the last STEP number that printed its summary row
judgement: {verdict:"PENDING", decided_by:null}
ur15_steps:
  identity: LEFT{arm_xml, sha256; grip_xml, sha256} / RIGHT{...}          (UR15 / UR15-B)
  driver:   {path, sha256 of the running file};  cell_dump: {_gen/_steps_cell_full.xml, sha256}
  config:   {yoke_spread_m, tilt_deg, crown_r_m, shoulder_height_m, table_top_m, grasp_centre_x_m,
             env_switches_set: {name: value} over the names the driver and spec read through
             environ.get (23 by this session's query; the edit uses the literal list at edit time)}
  step1_approach: {L,R}: {tool_err_mm, touching[]}
  steps[]: {step, name, t_s, tool_err_mm{L,R},
            command{L,R}: {reached_frac, held_ticks, ticks, stalled},
            sigma_min{L,R}, mast{L,R}: {gap_mm | null, who},
            arm_to_arm{closest_mm, closest_who, along_move_mm, along_who, worst_so_far_mm},
            seat_C1_miss_mm[dx,dy,dz], gates{C1,C2}: {pass, fails_on[], link, pos},
            penetration{inside_mm, part, link, contacts}, pin{C1,C2}, grip{L,R},
            summary_row (the prose row, verbatim)}
  worst: {sigma_min{L,R} + where, mast{L,R} + where, claw_min{L,R}, arm_gap_min_mm, arm_gap_path_mm}
  gates: (the `gates` dict)
  depth_audit: the `_DEPTH_AUDIT` counters (channel keys as "name:firstlineno")
```
Every number is the **same variable at the same moment** as the `[steps]` line that prints it.  Nothing is
parsed from prose.

### 4. Mechanism — instrument only; no branch of control changes

- One handler `_write_run_metrics()` registered with `atexit` right after `OUT` (:40): registered **first**
  so it runs **last** (LIFO, measured), after the depth-audit print, and already armed on the :1103 early
  exit.  It reads module globals defensively (`globals().get`), so it writes on every exit path with
  whatever exists at that moment.
- Capture sites: STEP1 (:2682, :2701) 2 lines; one per-step dict appended just before :3830
  (`print("[steps] " + row)`), built from the variables already in scope there; the gate rows collected
  into a dict inside the :3817 loop (2 lines); a completion marker after :3902 (1 line).  Estimate
  ≤ 120 added lines, 1 file, **0 control lines removed or re-ordered**.  numpy scalars → float through a
  `default=` converter.
- Failure is loud, never silent: if anything raises inside the handler it prints
  `[steps] RUN_METRICS.json NOT written: <exc>`; an atexit exception does not change the exit code.

### 5. Acceptance — pZ's leg, pre-registerable now; two legs run before any route run

- **L1 (static, no run):** `P4_CLIP_DUMP=1 … > run.log` exits at :1103 before any physics step or video —
  the stills' class (§1397 "実行 0") — and must yield `RUN_METRICS.json` beside run.log with
  end_reason "exited_early", config + identity filled, `steps: []`.  Plus the writer's own unit probe
  (raise → end_reason "raised", message byte-equal).
- **L2 (on the next Rs1-authorized route run, whatever its outcome):** (a) file present beside run.log;
  (b) `run.exception.message` == the log's last traceback line after `RuntimeError: ` (byte-equal) when it
  raises; (c) for every step, the JSON numbers re-format to the digits in the matching `[steps] STEP n …`
  lines — a **transport** check: it detects a lost value, not a wrong one; (d) sidecar `run.log.sha256` vs
  `log_sha256_at_write`; (e) pB runs `/log-analyzer <run_dir>` and the skill's 0.2/0.3 blocks pick up the
  file and the log path — m-p18-286's accept condition.
- ⛔ **Not an authorization.**  This acceptance implies no route run; ② stays conditional and unmet; L1 is
  static.

### 6. Scope line

- Measurement on p0's own file under the precedent the file records at :3672–3675 ("measurement … no
  control changes here, only instruments").  Touches neither the nominated kinonly object (`120746a49b`),
  nor `compare_24_vs_240.py` (locked), nor any spec file.
- Done now: this plan, committed, and one message to p18.  Not done now: the edit.

## 8.46 E1 LANDED: `b19c4c5f5d` (+119/−0, one file) — verified without running the driver; and ⛔ one clause of §8.45 retracted before L1 is run on it

*(2026-09-05 07:58 JST.  Rs1 = the human; Rs2 = p4/CC.  Window = Rs1「push 1:開く」via m-p18-289; static leg word = Rs1「2：推奨で良い」via m-p18-290.)*

### 1. What landed

- Commit **`b19c4c5f5d`** (07:55:21 JST), pathspec-limited to `p4_ur15_sim_20260727/ur15_steps_wired.py`; blob
  `fda7189e8240a8a9ccdaee590c044bf662bb296f`; content sha256
  `18355d408aed06839a81b79987eb5557dbd6c9e4bd83fff583703dc0ccc37e1a`; `git show --numstat` = **119 added, 0 deleted**
  (the window's bound was ≤ 120); no line longer than the repo's 120 (`pyproject.toml:7`); `py_compile` OK under env7.
- Pins (line numbers in the committed file): block markers :41 / :139; `_rm_stdout_file` :55 (A1), `_rm_json` :64,
  `_rm_keys` :72, `_write_run_metrics` :78, `atexit.register(_write_run_metrics)` :138 — registered before
  `atexit.register(_depth_audit_report)` :1755, so it runs after it (LIFO).  Capture sites: STEP1 touching :2782 and
  tool err :2802; gate rows `_grow` :3920 / :3924-3925; the per-step row `_RM["steps"].append` :3935-3947 (the same
  variables the `[steps] STEP n` lines print, one line above them); completion marker :4021 (the file's last line).
- Not touched: any control line, the nominated kinonly object, `compare_24_vs_240.py`, any spec file.  The edit is
  reproducible from the scratchpad script `apply_e1.py` (insert-only; it refuses unless every anchor line matches
  its expected text exactly — it refused once, on two anchors I had numbered one line early, and wrote nothing).

### 2. Verification, static (no driver execution)

The RUN_METRICS block was **extracted from the committed file between its markers** and executed in a fake module
namespace by `probe_rm_block.py` (40 lines, sha256 `fbc863fcc8f986a4…`), four exit paths, stdout redirected to a
`run.log` per leg exactly as a launch does; `check_rm_probe.py` (46 lines, sha256 `141d8d1d09859213…`) then read the
outputs.  Both scripts are reproduced verbatim in §2.1 below (no new repo file: the window is one file).  Output:

```
PASS r1 end_reason raised / exit_code 1
PASS r1 exception.message == traceback last line (byte-equal)  [STEP2 L: THIS arm's command stopped adva]
PASS r1 M1: log_sha256_at_write == launcher sidecar (nothing followed the write)
PASS r1 M1: log_bytes_at_write == final size
PASS r1 A1: JSON beside run.log although OUT was elsewhere
PASS r1 LIFO: later-registered handler printed BEFORE the RUN_METRICS line
PASS r1 identity sha256 == files (arm L/R, grip L/R)
PASS r1 driver sha256 == file
PASS r1 config echo (0.22 / 45.0 / 0.110) + env switch captured
PASS r1 numpy scalars/arrays serialized as numbers
PASS r1 phase_max_reached == 2 / judgement PENDING
PASS r1 depth_audit: code-object keys -> 'name:lineno', tuple keys -> str, rows dropped, np.bool_ ok
PASS r1 worst: 1e9 sentinel -> null, real value kept
PASS r1 step1_approach carried
PASS r1 log-analyzer key path artifacts.logs.path present
PASS r2 exited_early: end_reason / exit_code null / exception null
PASS r3 completed (block-buffered stdout, no -u): end_reason completed / exit_code 0
PASS r3 M1 equality holds with buffered stdout too
PASS r4 pipe: fallback to OUT.parent, log_path null, logs.exists false
ALL PASS
```

Legs: r1 = uncaught RuntimeError with OUT in a *different* directory (A1 exercised; process exit 1); r2 =
`SystemExit(0)` (the P4_CLIP_DUMP shape); r3 = normal completion **without `-u`** (block-buffered stdout — the flush
before the hash is what makes M1 hold there); r4 = stdout through a pipe (fallback).  In r1 the sidecar
`sha256sum run.log` equals `log_sha256_at_write`: nothing followed the write, including the traceback and the
later-registered handler's line, both of which sit inside the hashed prefix.  What the probe does **not** cover: the
real module namespace (the real `_DEPTH_AUDIT` contents, the real `S`, the real path through :1202) — that is what a
driver leg adds.

Launch line from now on (the sidecar is the launcher's one line; `echo "exit=$?"` stays as before):

```
mkdir -p _gen/<run> && <env overrides> /home/rlrk/env_isaaclab7/bin/python -u ur15_steps_wired.py \
    _gen/<run>/<name>.mp4 > _gen/<run>/run.log 2>&1; echo "exit=$?"; sha256sum _gen/<run>/run.log > _gen/<run>/run.log.sha256
```

### 3. ⛔ Retraction, before acting on the word that rests on it

§8.45 §5 wrote that L1 (`P4_CLIP_DUMP=1`) "exits at :1103 **before any physics step** or video", and m-p18-289/290
relayed that clause to Rs1, whose word「2：推奨で良い」came back on it.  I read the path only now.  Measured on the
committed file: the clip-dump block :1149 is preceded by

```
for t in SIDES:
    d.ctrl[GIDX[t]] = OPEN                     # :1144-1145
mujoco.mj_forward(m, d)                        # :1146
for _ in range(2000):
    mujoco.mj_step(m, d)                       # :1147-1148  <- physics, 2000 steps
```

= **2000 physics steps × CELL_TIMESTEP 0.000208 s = 0.417 s of simulated time**: the cable settling onto its saddles
under gravity, fingers commanded OPEN, **no arm command written** (the servos hold the compile pose), no IK, no
route step, no renderer, no video.  So "or video" stands and "before any physics step" is **false**.  A word given on a
wrong description is not a word for the thing itself: **L1 is not run.**  Whether a 0.417 s cable settle with the
arms holding still is inside the static class Rs1 cleared is Rs2's (chain court) and Rs1's reading, not mine.

If it is cleared: before the run I `cp -p` the four generated XMLs the build overwrites —
`_gen/_steps_cell_full.xml` (sha `4158e4e638e9b0fc…`, mtime 2026-08-10 09:10:11, the world §1397's stills were rendered
from), `_steps_world.xml` (`d4f884272e30550a…`), `_arm_only_L.xml` (`4e97b6f0dbb89919…`), `_arm_only_R.xml`
(`93d22c9606043fcc…`) — into `_gen/reshoot_speccell_20260810/`, their run's own directory, so the reshoot's custody
survives the overwrite.  Then `YOKE_SPREAD_OVERRIDE=0.22 TILT_DEG_OVERRIDE=45 P4_CLIP_DUMP=1` with the launch line
above into `_gen/e1_static_l1_<date>/`, and the report is the JSON, the sidecar, and the shas.

### 2.1 The two probe scripts, verbatim

`probe_rm_block.py`:

```python
"""Exercise the RUN_METRICS block AS WRITTEN IN THE DRIVER FILE (extracted between its markers), in a fake
module state, without importing or running the driver.  argv: driver_path mode OUT"""
import atexit, math, os, sys
from pathlib import Path
import numpy as np

DRV, MODE, OUT = Path(sys.argv[1]), sys.argv[2], Path(sys.argv[3])
src = DRV.read_text()
block = src[src.index("# --- RUN_METRICS.json begin"): src.index("# --- RUN_METRICS.json end")]

def some_channel():   # stands in for a code object key in _DEPTH_AUDIT["chan"]
    pass
co = some_channel.__code__
ns = {"__file__": str(DRV), "OUT": OUT, "S": DRV / "_gen" if False else DRV.parent / "_gen",
      "GRIP_XML": "/home/rlrk/IsaacLab/thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml",
      "GRIP_XML_MIRRORED": str(DRV.parent / "_ur15_2f85_koshape_actuated_mirrored.xml"),
      "np": np, "math": math, "os": os, "sys": sys, "Path": Path, "atexit": atexit,
      "YOKE_SPREAD": 0.22, "TILT": math.pi / 2 - math.radians(45.0), "CROWN_R": 0.110,
      "SHOULDER_HEIGHT": 1.53, "TABLE_TOP": 0.8, "GRASP_CENTRE_X": 0.0,
      "sig_min": {"L": np.float64(0.0481), "R": 1e9}, "sig_where": {"L": "STEP2 t=1.0s", "R": ""},
      "col_min": {"L": -0.0008, "R": 1e9}, "col_where": {"L": "g6 vs crown", "R": ""},
      "claw_min": {"L": 1e9, "R": 1e9}, "arm_gap_min": 0.0, "arm_gap_path": 1e9,
      "gates": {"grasp": False, "pinC1": "t=1.00s cab29 seat=[0.1 0.2 0.3]"},
      "_DEPTH_AUDIT": {"calls": 5, "checked": 4, "chan": {co: 3}, "chan_viol": {co: 1}, "pairs": {(1, 2): 3},
                       "rows": ["illustrative"], "last_flagged": np.bool_(False)},
      "LIVE_OUT": Path.home() / "Downloads" / "ur15_live.mp4"}
exec(compile(block, str(DRV), "exec"), ns)      # registers the real atexit handler, first
ns["_RM"]["step1"] = {"L": {"touching": ["column (via g6)"], "tool_err_mm": 270.2}, "R": {"touching": [], "tool_err_mm": 2.1}}
ns["_RM"]["steps"].append({"step": 2, "name": "cable上空へ", "t_s": 2.2, "tool_err_mm": {"L": np.float64(511.9), "R": np.float64(11.1)},
                           "command": {"L": {"reached_frac": np.float64(0.0), "held_ticks": np.int64(10560), "ticks": 10560, "stalled": True},
                                       "R": {"reached_frac": 0.38, "held_ticks": 0, "ticks": 10560, "stalled": False}},
                           "seat_C1_miss_mm": np.array([-3.7, -70.0, 140.3]), "summary_row": "STEP 2 cable上空へ t=  2.2s"})
atexit.register(lambda: print("[probe] LATER-registered handler (stands in for _depth_audit_report) runs FIRST"))
print("[probe] mode", MODE)
if MODE == "raised":
    raise RuntimeError("STEP2 L: THIS arm's command stopped advancing (probe text)")
if MODE == "exited_early":
    raise SystemExit(0)
if MODE == "completed":
    ns["_RM"]["completed"] = True
```

`check_rm_probe.py`:

```python
"""Check the four probe outputs against the section-8.45 predicates.  argv: probe_root driver_dir"""
import hashlib, json, sys
from pathlib import Path
R, D = Path(sys.argv[1]), Path(sys.argv[2])
ok = True
def check(name, cond, detail=""):
    global ok
    ok &= bool(cond); print(("PASS " if cond else "FAIL ") + name + (f"  [{detail}]" if detail else ""))
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()

j1 = json.load(open(R / "r1/RUN_METRICS.json")); log1 = (R / "r1/run.log").read_text()
check("r1 end_reason raised / exit_code 1", j1["run"]["end_reason"] == "raised" and j1["run"]["exit_code"] == 1)
tb_last = [l for l in log1.splitlines() if l.startswith("RuntimeError: ")][-1][len("RuntimeError: "):]
check("r1 exception.message == traceback last line (byte-equal)", j1["run"]["exception"]["message"] == tb_last, tb_last[:40])
side = (R / "r1/run.log.sha256").read_text().split()[0]
check("r1 M1: log_sha256_at_write == launcher sidecar (nothing followed the write)", j1["run"]["log_sha256_at_write"] == side)
check("r1 M1: log_bytes_at_write == final size", j1["run"]["log_bytes_at_write"] == (R / "r1/run.log").stat().st_size)
check("r1 A1: JSON beside run.log although OUT was elsewhere", j1["run"]["out_dir"] == str(R / "r1") and j1["run"]["log_path"] == str(R / "r1/run.log"))
check("r1 LIFO: later-registered handler printed BEFORE the RUN_METRICS line", log1.index("LATER-registered") < log1.index("[steps] RUN_METRICS.json ->"))
idL = j1["ur15_steps"]["identity"]["LEFT"]; idR = j1["ur15_steps"]["identity"]["RIGHT"]
check("r1 identity sha256 == files (arm L/R, grip L/R)",
      idL["arm_xml"]["sha256"] == sha(D / "ur15_base.xml") and idR["arm_xml"]["sha256"] == sha(D / "ur15_base_mirrored.xml")
      and idL["grip_xml"]["sha256"] == sha(idL["grip_xml"]["path"]) and idR["grip_xml"]["sha256"] == sha(D / "_ur15_2f85_koshape_actuated_mirrored.xml"))
check("r1 driver sha256 == file", j1["ur15_steps"]["driver"]["sha256"] == sha(D / "ur15_steps_wired.py"))
check("r1 config echo (0.22 / 45.0 / 0.110) + env switch captured",
      j1["ur15_steps"]["config"]["yoke_spread_m"] == 0.22 and abs(j1["ur15_steps"]["config"]["tilt_deg"] - 45.0) < 1e-9
      and j1["ur15_steps"]["config"]["crown_r_m"] == 0.11 and j1["ur15_steps"]["config"]["env_switches_set"] == {"YOKE_SPREAD_OVERRIDE": "0.22"})
st = j1["ur15_steps"]["steps"][0]
check("r1 numpy scalars/arrays serialized as numbers", st["tool_err_mm"]["L"] == 511.9 and st["command"]["L"]["held_ticks"] == 10560 and st["seat_C1_miss_mm"] == [-3.7, -70.0, 140.3])
check("r1 phase_max_reached == 2 / judgement PENDING", j1["progress"]["phase_max_reached"] == 2 and j1["judgement"]["verdict"] == "PENDING" and j1["judgement"]["decided_by"] is None)
da = j1["ur15_steps"]["depth_audit"]
check("r1 depth_audit: code-object keys -> 'name:lineno', tuple keys -> str, rows dropped, np.bool_ ok",
      list(da["chan"].keys()) == ["some_channel:11"] and list(da["pairs"].keys()) == ["(1, 2)"] and "rows" not in da and da["last_flagged"] is False)
w = j1["ur15_steps"]["worst"]
check("r1 worst: 1e9 sentinel -> null, real value kept", w["sigma_min"]["R"] is None and w["sigma_min"]["L"] == 0.0481 and w["arm_gap_path_m"] is None and w["arm_gap_min_m"] == 0.0)
check("r1 step1_approach carried", j1["ur15_steps"]["step1_approach"]["L"]["tool_err_mm"] == 270.2)
check("r1 log-analyzer key path artifacts.logs.path present", j1["artifacts"]["logs"]["path"] == str(R / "r1/run.log"))

j2 = json.load(open(R / "r2/RUN_METRICS.json"))
check("r2 exited_early: end_reason / exit_code null / exception null", j2["run"]["end_reason"] == "exited_early" and j2["run"]["exit_code"] is None and j2["run"]["exception"] is None)
j3 = json.load(open(R / "r3/RUN_METRICS.json")); side3 = (R / "r3/run.log.sha256").read_text().split()[0]
check("r3 completed (block-buffered stdout, no -u): end_reason completed / exit_code 0", j3["run"]["end_reason"] == "completed" and j3["run"]["exit_code"] == 0)
check("r3 M1 equality holds with buffered stdout too", j3["run"]["log_sha256_at_write"] == side3)
j4 = json.load(open(R / "r4/RUN_METRICS.json"))
check("r4 pipe: fallback to OUT.parent, log_path null, logs.exists false", j4["run"]["out_dir"] == str(R / "r4") and j4["run"]["log_path"] is None and j4["artifacts"]["logs"]["exists"] is False)
print("ALL PASS" if ok else "SOME FAIL")
```
