# pZ — item 14 re-run on the **revised** instrument (my four filed verdicts pinned the superseded one)

**Author** pZ / IMPL-VERIFIER (`w2:pZ`), role brief `VERIFIER_ROLE_BRIEF_pZ_20260721.md` @ `4714493e64`
**Measured** 2026-08-09 09:33–09:36 JST · **written** 09:36 JST · **self-scheduled** (nobody asked for this re-run)
**Status** written by pZ; **not committed by pZ** — see §4.

## Why this exists

My four filed verdicts each close item 14 with the same sentence: *"transfers **on content** — `wired`'s sha is byte-identical to the artifact where violations were measured 0, instrument pinned at addendum content sha256 `e5dd8396…`."*

That pin is now **two revisions of the instrument out of date**, and one of those revisions was made **because of a defect I reported against it** (comma-tuple target lines missed). ⇒ My verdicts' item-14 leg rested on an instrument I had myself filed a defect against. p11 re-measured with the fixed instrument and got 0 — **but that is p11's measurement, and relaying it is precisely what my role forbids** (`:24`). So I ran it.

## 0. What moved under the pin (measured, insertion-only)

| | |
|---|---|
| instrument blob my verdicts pin | `e5dd839672ae7692aeb85d5b54a133a0b43472e24dbba380a26f9ecab9a1148c` = the file at commit `b8b80cbf323b6185546a4e66fb6c477431b48f0e` (08-08 23:59) |
| instrument blob now | `46eada67fbe5154e8649522ec4e394cccf66b21baf8d2be9d93435f2e084e5cd` @ `1e0a1f9a98` |
| pinned → now | `git diff --numstat` = **157 / 0** ⇒ **deleted 0, so no character of the pinned text was removed**; sections A-10 … (m) were added |
| what changed for item 14 | **A-10 (d)** revised the target-line predicate (comma-tuple + judge after comment-stripping); **A-13 (l''')** published population / expect / control for each predicate |

⚠ `deleted = 0` is conclusive in one direction only — it proves nothing was removed. It does **not** prove the added lines leave the meaning intact; that is why the predicates below were re-run rather than inherited.

## 1. The re-run — population pinned to an object, not to `HEAD`

**population** = `p4_ur15_sim_20260727/ur15_steps_wired.py` @ **`1188cb706380876f3afe90d5527c2b6f26da3c9a`** (lane tip 09:35:12), content sha256 **`6ca7247513ca117c03352b20c799deba7db86d3c9965226e530c05eb2b14fe50`** — equal to the figure in all four verdicts. The blob is stable: over the **67** lane commits since the landing `76b535ec60`, this path has **1** unique blob. Nothing was imported and nothing was executed; the bytes come from `git show`.

| predicate | expect (published) | measured | positive control |
|---|---|---|---|
| target-assign lines, comma-tuple form | **8** | **8** — `:96 :1126 :1127 :2630 :2631 :2645 :2646 :2647` | `^\s*[A-Z][A-Z0-9_]*\s*=` → **63** lines (extractor alive) |
| step rows after `STEPS = [`, blank-line terminator (A-9b `:170`) | **17** | **17**, span `:2708`–`:2726` | `STEP table` occurrences → **1** (0 would mean no anchor) |
| 12 mounting terms inside the target set | in-target **0** | **0 violations** over the **25**-line target set (8 + 17) | 10 of 12 terms occur whole-file; the 2 that do not (`CROWN_Z0`, `COLUMN_STEM_H`) are **structurally absent** (never imported) |
| **the conjunction itself** (pZ, per leg) | ≥1 each | **assign leg 1** (`CROWN_ZC`), **row leg 1** (`YOKE_SPREAD`) | negative control = untouched file → **0** |

Whole-file line counts, `\b<TERM>\b`, case-sensitive, counting **lines** not occurrences: YOKE_SPREAD 5 · TILT 4 · CROWN_R 7 · CROWN_ZC 2 · CROWN_Z0 0 · SHOULDER_HEIGHT 3 · COLUMN_R 3 · COLUMN_HZ 2 · COLUMN_STEM_BOTTOM 2 · COLUMN_STEM_H 0 · PEDESTAL_R 2 · PEDESTAL_HZ 2. Every one **in-target 0**.

⭐ **The last row is the new thing.** Until now item 14's zero was guarded by *"10 of 12 terms appear somewhere in the file"* — a **relaxation**: it shows the word side is alive and never shows that *word ∧ target-line* can fire. Two synthetic lines built to violate, one per leg, fire 1 and 1, and the untouched file fires 0. ⇒ **the 0 is discriminating, per leg.** (The three-way split of control types — different-predicate / relaxation / identity — is p18's, m-p18-207 §2; the convergent repair was reached independently by p4, p11 and me.)

## 2. Four findings about the instrument's **copyable text** (the numbers above are unaffected)

1. ⛔ **The published regex, copied literally, captures 6 — not the 8 published beside it.** A-13 `:305`/`:322` print `^\s*(Z_SEAT|GL|GR|LX[0-9]?|RX[0-9]?|RX_MID)\s*(,\s*(同)\s*)*=`. The group `(,\s*(同)\s*)*` requires the literal character 同 — **measured 0 occurrences in the blob**, with a positive control that the query can see CJK there at all (`解放` → 1) — so the comma-tuple lines **`:2645` and `:2646`** never match — **the exact two lines revision (d) was written to capture.** Measured: literal **6** `[96,1126,1127,2630,2631,2647]` vs prose-reading **8**. ⇒ The prose is right and the regex is a placeholder; a copier gets a silently narrower target set. **The published `expect 8` on the same line is what makes this visible in one run** — the rule working exactly as designed.
2. ⛔ **The published row anchor, taken literally, captures 0 rows.** A-13 `:306`/`:323` say "the consecutive `(N, …` lines **directly after** the line containing `STEP table`". That line is `:2644`; the rows begin at `:2708`, 64 lines later. Measured literally: **0 rows**. The working reading (`STEPS = [` at `:2707`, terminate on a blank line per A-9b `:170`) gives 17. ⚠ **This is the same gap I filed on 2026-08-09 as finding 3** against the pinned instrument (`PZ_VERDICT_422ab807cd_…:34`). The numbers were re-measured with the working reading; **the copyable sentence still carries the literal one.**
3. ⛔ **My own error, and the published number is what caught it.** My first implementation terminated the row scan at the first non-row line → **15** rows, span `:2708`–`:2722`. `expect 17` contradicted it. Cause: a two-line comment at `:2723`–`:2724` sits **inside** the table, so rows 17 and 18 (`解放`, `上昇`) fall after the break. A-9b `:170` publishes the correct terminator and I had not used it. ⇒ Had the expectation not been published, I would have reported a 23-line target set and a 0 that silently skipped the release rows. **This is the direction the rule was built for: it caught the reader, not the author.**
4. ⚠ **A published *control* number does not reproduce, and I cannot reconstruct it.** A-13 `:321` states the control `^\s*[A-Z][A-Z0-9_]*\s*=` matches **200+** lines of this file. Measured on the pinned blob: **63**. Neighbouring readings: no leading `\s*` **55**; unanchored **109**; tuple targets allowed **67**; lowercase allowed **599**. None is near 200. ⇒ The control's **role** still holds (63 ≫ 0 proves the extractor is alive), but its **number** is unreconciled. ⛔ I am not asserting what was run — I am reporting that the figure as published does not come back, with the four neighbours so it can be reconciled from the same object.

## 3. Disposition

- **Covered:** item 14 — the confinement predicate in its **revised** form (A-9 / A-9b / A-9c / A-10 (d)), all four published predicates, on the landed blob, with a per-leg positive control and a negative control.
- **Result:** ✅ **violations 0 over the full 25-line target set, and the 0 is now shown to be discriminating rather than merely quiet.** My four verdicts' item-14 leg **stands** — and no longer rests on a pinned instrument I had filed a defect against, nor on p11's number.
- ⛔ **Not covered, and therefore not claimed:** anything outside item 14 — §7 (ii) is still deferred by ruling; nothing here touches physical validity (Rs's court, `:28`); nothing here is a statement about C-2's four edits, which await p5's process-table leg. **"0 violations" means the 12 mounting terms do not appear in those 25 lines** — it is not a statement that the mounting change is correct.
- ⚠ The 0 is a fact about blob `6ca72475…`. Any future landing that changes `wired` requires the re-run, not this record.

## 4. Provenance and authority

Every figure computed by pZ from `git show <rev>:<path>`; no worktree needed (static scan). **Footprint, measured rather than asserted:** modifications to tracked content by pZ = **0**; ⚠ **this file itself is a change to the shared tree** — one new untracked path (`?? …/PZ_ITEM14_RERUN_REVISED_INSTRUMENT_20260809.md`). ⛔ The sentence I first wrote here was *"zero changes in the shared working tree"*, which is false at file resolution while the file making the claim sits inside the population. Script: `item14_rerun.py`, written to my scratchpad and **not durable** — the predicates, populations, expectations and controls are all transcribed above so the run can be rebuilt from this file alone. ⚠ p11's 07:29:44 case shows what a vanished script costs: it became undecidable whether a 0 was a dead query or a narrow definition. Mine is decidable from the table above because each predicate is printed with its control.

Env pin `/home/rlrk/env_isaaclab7/bin/python` (stdlib `re` only; the pin is convention here, not a dependency).

⛔ **pZ has no measured grant to commit.** `Vault Write Permissions.md` keys on directories with a generic *CC (Agent)* column and names no pane; the query for `pZ|IMPL-VERIFIER` returns 0 **and so does the control for `p4|RS-TECH-LEAD`**, so that zero is not discriminating, and `eval_runs/` is not in that matrix at all. ⇒ This file is **written, not banked**; banking is requested of a custodian. Until then it is untracked: readable by path, invisible to `git grep <rev>`, perishable.

**Grade of provocation.** The re-run is **self-scheduled**. The rules that made its defects findable are not mine: published coverage (p4/p11), *audit is a predicate* (p0), *coverage on the predicate's own line* (me, after p11 measured the copy), *coverage as a number not a word* (p4), *a control must fire its own predicate* (me), and the three-way control taxonomy (p18, m-p18-207 §2). ⛔ Four of this file's findings exist because someone else published a number I could contradict.

---

## ⛔ APPENDED 2026-08-09 10:57 JST — my row anchor is not unique, and I never checked (ruling A: nothing above rewritten)

**The defect.** §1's row predicate anchors on `STEPS = [`. That pattern **matches twice**, at both revisions:

| revision | anchor matches | lines |
|---|---|---|
| `HEAD` (= the landing lineage) | **2** | `:2707`, `:2976` |
| `2fba2dfd67` (the C-2 build target) | **2** | `:1789`, `:2058` |

My script took index `[0]` and published `17` without ever asking whether the anchor was unique.

**The result stands, and not for the reason the script assumed.** `:2976` is
`STEPS = [tuple(RELEASE if v == "RELEASE" else v for v in row) for row in STEPS]` — a comprehension that substitutes the solved release value into the existing rows, not a second table. Rows matching `^\s*\(\s*[0-9]` after it: **0**; control, the same rule after the first anchor: **17**. ⇒ the 17-row target set and the 0 violations are unaffected.

⛔ **The published control could not have caught this.** A-13 `:323` controls the row predicate with *"`STEP table` occurrences → 1"* — that counts the **comment** token, which is a **different string from the anchor the code actually uses**. A control on a neighbouring token is not a control on the predicate. ⭐ Same shape as the rest of this file, arriving on my own instrument: the number was right, the query was not sound, and only a shell error on the second match exposed it.

✅ **Corrected form of the row predicate's line**, for anyone copying it:

> `STEPS = [` → **expect: anchor matches 2, rows taken from the first, second carries 0 rows** — control: rows after the first anchor = 17, rows after the second = 0

⚠ **One provenance line above is now stale by success**: §4 says this file is *"written, not banked"*. It was true when written; a custodian banked it, and the tracked content equals what I wrote (`d416cc2562b4af01…`). The sentence stays as the record of its own moment.
