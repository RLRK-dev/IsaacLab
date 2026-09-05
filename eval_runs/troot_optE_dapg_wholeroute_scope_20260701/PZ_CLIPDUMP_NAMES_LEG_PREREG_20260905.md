# pZ — pre-registered leg for the driver's `P4_CLIP_DUMP` name-list fix (parent :1170-1171), written before the object exists

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-05 10:58 JST on m-p18-305 (Rs1's word, ledger §1426). Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Order of existence, measured in the same command that wrote this file**: at **10:58:23 JST** the commits touching `ur15_steps_wired.py` after `0a2b600959` number **1**, and the working-tree driver equals that blob (`57de8c3ec7ed0262…` = `307868a9…`). ⇒ the parent of the coming commit is the driver at `0a2b600959` (content `307868a9721d2896e3f4849fe18a6297d2034fefe2c276b9f3bd4d7325fb90a5`), and these rows precede the object. ⛔ Nothing runs from this desk; the window is p0's; route run (2) stays unmet.

## What the parent holds (read from the blob, never imported)

- The stale list: `:1170-1171` `_c1g = [mj_name2id(m, GEOM, n) for n in ("C1_riser", "C1_base", "C1_wa", "C1_wb", "C1_floor")]`; its readers `:1172-1173` (the comparison print) and `:1174-1179` (the per-geom loop). `grep _c1g` = **3 lines**, all inside the `P4_CLIP_DUMP == "1"` block (`:1150-…`). Blame `66d8b8747da` (07-27), pre-E1.
- Where compiled clip geoms get their names: driver `:265` `<geom name="{name}_{i}" …>` inside `:270` `for i, (…) in enumerate(CLIP_PARTS)`, with `CLIP_PARTS` from `ur15_cell_spec.py:333`. So the current names are `C1_0..C1_4` / `C2_0..C2_4` — confirmed by a static XML parse of the L1 run's cell dump `_gen/_steps_cell_full.xml` (sha `4158e4e638e9b0fc…`, = the L1 JSON's `cell_dump.sha256`): exactly those 10, and **none of the five old names**.
- The live set `CLIPG` (`:467-468`, prefix match `C1_`/`C2_`) and its contact readers (`:1017/:1042/:1044/:1073/:1074/:1093`) do not read `_c1g` — the defect is confined to the diagnostic (PZ-213).

## Rows (judged against the commit's own parent)

| # | row | requirement |
|---|---|---|
| 1 | scope | driver hunk(s) confined to parent `:1170-1179`; `git diff parent..commit -- ur15_steps_wired.py` shows **no changed line outside** that range; the only other file = p0's own record section; no other tracked file |
| 2 | control invariance — mechanical | ordered control-class sequence sha == **`426aa229deb2cb2b`** (57 lines); live-state writes stay **0**; `d.ctrl` writes **7, same order** |
| 3 | untouched by content | the E1 block (`:41-140`), `CLIPG` (`:467-468`), `CLIP_BOXES` (`:1017`), the contact readers, the seat gate, `_RM_ENV`, the `atexit` registration (`:139`) and the block's closing `SystemExit(0)` are **byte-identical** to the parent; the handler still precedes the exit |
| 4 | the fix — which option the diff **is**, read from the blob, not from p0's note | **(A) derive**: the lookup names are produced by the **same rule** as the compiled names — `f"C1_{i}"` for `i in range(len(CLIP_PARTS))` (or an equivalent read of `CLIP_PARTS`), **no second hand-typed literal list** (a fresh copy would only go stale again); static resolvability: every produced name is a geom in the cell dump ⇒ on this model the comparison reads `[81..85]` vs `[81..85]` and the loop would print 5 rows. **(B) retire**: `:1170-1179` gone entirely; `grep _c1g` = **0**; no dangling reference; the comparison print goes with it |
| 5 | diagnostic stays diagnostic | if `_c1g` survives it is read **only** inside the `P4_CLIP_DUMP` block; no new global, no new reader outside |
| 6 | the leg fires — negative control | rows 4A on the **parent**: the five old names resolve **0/5** in the cell dump (fails, as it must); `grep _c1g` on the parent = 3. A row that cannot fail on the parent is not counted |
| 7 | no run | static only — I do not set `P4_CLIP_DUMP=1`; the model I parse is the L1 run's cell dump (XML text, no MuJoCo step, no driver import). "Execution confirmation" delegated to this desk (m-p18-305) is therefore **static resolvability against the dumped model**, and is named as such |
| 8 | pins | parent-relative; the driver's content sha named; p0's record read only **after** the blob measurement and only for its one-line reason for the option chosen |

## Provenance

`git log`/`git show` on the driver blob at `0a2b600959`; `sha256sum`; regex parse of the cell dump's `<geom name=…>`; `git blame -L 1170,1171`. Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian — the order-of-existence line above is the measurement, not a claim.**

## Correction (2026-09-05 11:00 JST) — supersedes sha `1ea5a87241300fdd…`: the object landed while this file was being written

The interpolated numbers above are the measurement and stay: **1** commit after `0a2b600959` at 10:58:23, working tree `57de8c3e…`. The **sentences around them were wrong**: "equals that blob (`57de8c3e…` = `307868a9…`)" asserts an equality between two different hashes, and "these rows precede the object" is false. Truth: p0's `22feba17a6` landed at **10:57:42**, between my first read (10:57:16, count 0) and the write (10:58:23, count 1); the rows are **41 s younger** than the object. What they keep is blindness to the diff (not read before the rows were fixed). Rows 1-8 unchanged; the parent they name (`0a2b600959`) is the true parent of the driver's blob in `22feba17a6`.
