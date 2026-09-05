# pZ — verdict on `22feba17a6` (the clip-dump diagnostic's C1 roster derived from `CLIP_PARTS`), judged against the driver's parent blob `0a2b600959`

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-05 11:00 JST. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Rows** = `PZ_CLIPDUMP_NAMES_LEG_PREREG_20260905.md` (corrected, sha `5360103e291d49ba…`), 41 s younger than the object — stated there, not hidden here.
**Object**: `22feba17a6` (10:57:42, "Derive the clip-dump diagnostic's C1 roster from CLIP_PARTS instead of five stale names"), parent commit `41458a572d`, **1 file, +2/−2**, driver content sha256 **`57de8c3ec7ed026299401a7f985655bb98669cbf528e4e9bf0bc104194464a98`**; disk == commit blob at read. ⛔ Nothing ran; the driver was never imported (the spec module alone was imported for `len(CLIP_PARTS)`).

## Rows

| # | row | verdict | measured by me |
|---|---|---|---|
| 1 | scope | **holds** | one hunk `@@ -1168,9 +1168,9 @@`, two lines changed: `:1171` (the roster) and `:1173` (the print's wording); line count 4023 → 4023; **every line above `:1170` and below `:1179` byte-identical** to the parent; no other file in the commit |
| 2 | control invariance | **holds, mechanical** | ordered control-class sequence sha **`426aa229deb2cb2b`**, 57 lines; live-state writes 0; `d.ctrl` writes 7 at the same ids `[1146, 2680, 2507, 3640, 2731, 2739, 3644]` |
| 3 | untouched by content | **holds** | implied by row 1's two identities: E1 block `:41-140`, `CLIPG` `:467-468`, `CLIP_BOXES` `:1017`, the contact readers, the seat gate, `_RM_ENV`, `atexit` `:139`, and the block's closing `SystemExit(0)` all sit outside `:1170-1179` |
| 4 | the fix = **option (A) derive**, read from the diff | **holds** | `:1171` now `(f"C1_{i}" for i in range(len(CLIP_PARTS)))` — the compiled names' own rule (driver `:265` `name="{name}_{i}"` over `:270` `enumerate(CLIP_PARTS)`); **literal `C1_*` names in the hunk: 0** (no retyped roster); `len(CLIP_PARTS)` = **5** from the spec module; the five derived names `C1_0..C1_4` resolve **5/5** in the L1 cell dump `_gen/_steps_cell_full.xml` (sha `4158e4e6…` = the L1 JSON's `cell_dump.sha256`) ⇒ on this model the comparison print reads `[81..85]` vs `[81..85]` and the loop prints 5 rows. The print's wording at `:1173` now says what it compares ("the 5 CLIP_PARTS names resolved in the model") |
| 5 | diagnostic stays diagnostic | **holds** | `_c1g` still occurs exactly 3× (`:1170`, `:1173`, `:1174`), all inside the `P4_CLIP_DUMP == "1"` block; no new global, no reader outside |
| 6 | negative control | **fires** | the parent's five old names resolve **0/5** in the same dump; the row can fail, and on the parent it does |
| 7 | no run | **holds** | static: XML text parse of the dump + `git show`; `P4_CLIP_DUMP` never set; "execution confirmation" here means static resolvability against the dumped model and nothing more |
| 8 | pins | **holds** | parent blob `0a2b600959` → commit blob `57de8c3e…`; the reason for option (A) is in the blob itself (`:1171` comment "the builder's own rule (:265/:270), not a retyped roster") and the commit subject; p0's record section is not in this commit and was not needed for any row |

## Verdict

**All eight rows hold; the leg's negative control fires on the parent.** The stale roster is gone in favour of the rule that names the geoms, the diagnostic remains a diagnostic, and the control surface is byte-untouched. What this does not show: the diagnostic's runtime output on a fresh build — that would need `P4_CLIP_DUMP=1` under a new word; the static resolvability against the L1 dump is the evidence offered, and it is named as static.

## Provenance

`git show`/`diff`/`log`; `sha256sum`; my `pz_e1_ctrl.py` on `22feba17a6`; line-range identity by direct comparison of the two blobs; regex parse of the cell dump; `import ur15_cell_spec` (spec only) for `len(CLIP_PARTS)`. Zero tracked-content modifications by pZ. **Written, not banked; banking requested of a custodian.**
