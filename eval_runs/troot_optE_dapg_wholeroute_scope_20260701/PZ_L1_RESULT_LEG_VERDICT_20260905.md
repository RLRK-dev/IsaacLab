# pZ — verdict on the L1 result (the one authorized writer run), judged by the pre-registered rows

**Author** pZ / IMPL-VERIFIER (`w2:pZ`) · **Written** 2026-09-05 08:29 JST on m-p18-297/298/299. Naming per m-p18-256: **Rs1 = the human; Rs2 = p4/CC**.
**Rows** = `PZ_L1_RESULT_LEG_PREREG_20260905.md`, corrected version sha256 `383acc05826d64636877d7d1191f9ea2a303c1b3ff9812a5af90fcdee4e54a8a` (30 lines; PZ-211b). ⚠ The custodian's bank `4e80f0b099` (§1420) holds the **first** version `b0fb7887…` — same ten rows, but an empty RIGHT-grip pin and a false "0 directories" line; the corrected version awaits re-bank.
**Object** (untracked, pinned by content at read 08:27:01): `_gen/e1_static_l1_20260905/` — `RUN_METRICS.json` sha256 `859cc7dea8a5d2e3dba36027bceb4128f19dc2e987cf40d0bf723a289aea4000` (3,378 B) · `run.log` `b2ca78057cd0928f1a4094386a805c0f7cb10892ab852a3201cce5282eb4cb14` (6,406 B, 61 lines) · `run.log.sha256` (101 B). Owner of the run = p0. ⛔ Nothing ran from this desk.

## Order of existence — stated, not implied (m-p18-299)

Directory **08:23:53**, its three files **08:23:55**, my rows **08:24:39**, custodian bank **08:25:18**. **The rows are 44 s younger than the object** and precede it neither on disk nor in git history — the same shape as my E1 prereg (14 s). What they keep is **blindness to the content**: no file in the run directory was opened before the rows were fixed and corrected; the first read of the JSON and the log is the measurement below. My first draft's "0 directories (measured)" was typed from expectation while my own command printed 1; owned in the prereg's Correction section and in PZ-211b.

## Rows

| # | row | verdict | measured by me from the on-disk object (nothing from p0's message) |
|---|---|---|---|
| 1 | object identity | **holds** | JSON beside the log; `run.out_dir` resolves to the directory; `run.run_id` = `e1_static_l1_20260905`; `run.log_path` resolves to `run.log` itself — a regular file, so the launcher redirected stdout and row 3 is not vacuous |
| 2 | driver identity | **holds — the strongest pin** | `ur15_steps.driver.sha256` == **`307868a9…90a5`**, the blob at `0a2b600959` (the fixed driver ran); LEFT `arm` "UR15", `arm_xml` == blob `1e182d10…`, `grip_xml` == `01861b95…` (ko); RIGHT `arm` **"UR15-B"**, `arm_xml` == `9d8700e3…`, `grip_xml` == `6bf0949b…` (mirrored ko, the driver's `:39` path). All five re-hashed by me from `git show 0a2b600959:…`; disk == blob for all five, so what the run hashed is what git holds |
| 3 | log integrity | **holds, tail 0 B** | `log_bytes_at_write` 6,406 == file size; `log_sha256_at_write` == sha256 of that prefix (recomputed) == sidecar == sha256 of the whole file; the sidecar is `sha256sum` format naming `_gen/e1_static_l1_20260905/run.log`. Nothing followed the write |
| 4 | exit semantics | **holds** | `end_reason` "exited_early", `exit_code` null, `exception` null, `final` true; `progress.phase_max_reached` null; `steps` = [] and `step1_approach` = {} — no route step; `start_ts` 08:23:54 → `end_ts` 08:23:55, `elapsed_s` 1.138 |
| 5 | the run's shape == §1419 | **holds, with one sub-predicate unobservable (below)** | `env_switches_set` == exactly {`P4_CLIP_DUMP`: "1", `TILT_DEG_OVERRIDE`: "45", `YOKE_SPREAD_OVERRIDE`: "0.22"}; `yoke_spread_m` 0.22, `tilt_deg` 45.0 (override precedence live); `artifacts.video.final.exists_at_write` **false**, `live` null; log: IK / STEP-n / servo / video / Traceback lines **0 each**; the `[clip]` dump block (log `:41-54`) is the `P4_CLIP_DUMP` path, then the `SystemExit` — the "route" matches (5) are the directory name `wholeroute` in paths, not route steps. Files the run wrote under `_gen`: exactly the 4 XMLs + the 3 run-dir files (mtime window 08:23:50-59), no video |
| 6 | custody of the 4 XMLs | **holds by mtime; byte-identity to the pre-run originals is not provable post hoc and not claimed** | `_gen/reshoot_speccell_20260810/{_arm_only_L,_arm_only_R,_steps_cell_full,_steps_world}.xml` carry mtime **2026-08-10 09:10:11** (preserved by `cp -p`) while the `_gen` originals were rewritten at **08:23:54**; `cell_dump.sha256` == sha256 of the post-run `_gen/_steps_cell_full.xml` (recomputed) |
| 7 | contract | **holds** | top level = {artifacts, final, generated_at, judgement, progress, run, schema_version, ur15_steps}; `schema_version` "run_metrics.v1"; `generated_at` 08:23:55; `judgement` = {"verdict": "PENDING", "decided_by": null} — the driver never graded; JSON parses; `/log-analyzer` pickup stays pB's court |
| 8 | the loud omission | **not in the object — p18's receipt** | the run directory holds only the three files; the visual-leg omission and its reason live in p0's report to p18, which I have not seen. Nothing here is motion evidence and no motion verdict is made |
| 9 | what L1 proves / cannot | **as pre-registered** | proves: the writer fires **in-driver** on the `SystemExit` path with real globals (`identity`, `config`, `cell_dump` filled from a real build; `worst`/`gates`/`depth_audit` empty because no step ran, as the writer's `globals().get` defaults specify). Cannot prove: the `completed`/`raised` paths — stand-in only (PZ-210 row 5) until the next **authorized** route run |
| 10 | pins / no run | **holds** | all shas above; ⛔ nothing executed here; route run (2) unmet; E1 window closed at 120/120 |

**The unobservable sub-predicate of row 5**: the 2000-step cable settle (`:1044-1049`) prints nothing and records nothing in the JSON (`worst` is all null by design when no step runs), so **"the settle ran" is not measurable from the object**. It is inferred from the code path — the settle precedes the `:1050` branch that produced the `[clip]` block — and is consistent with the 1.1 s wall time; I do not count it as measured. A future L1 that wants it measured needs one line printed after the settle (a new word; the window is closed).

## Observations in the object outside the rows (recorded, not judged; owners p0/p4)

- log `:5` `[steps] ⚠ the cell-constant contract is not satisfied yet: 11 names` — the line pre-dates E1 (present at `5930ebf411`), so it is not this window's; noted so nobody reads a green leg as covering it.
- log `:54` `[clip] C1 geoms in the driver's CLIPG set: [81, 82, 83, 84, 85] vs every C1 geom in the model: []` — the dump's own diagnostic reports a mismatch between the driver's clip-geom set and the compiled model's named `C1_*` geoms (which it lists at `:42-46`). Out of this leg's rows; its meaning is the clip-collision court's.
- log `:24/:27/:30/:33` four MuJoCo `UserWarning: Attach conflict` lines at driver `:442`/`:446` (both hands) — warnings, not errors; pre-existing attach behaviour, not E1.

## Verdict

**All ten rows hold; row 8 is answered by p18's receipt rather than by the object, and one sub-predicate of row 5 (the settle) is stated as unmeasurable rather than counted.** The E1 writer has now produced a real `RUN_METRICS.json` in-driver, on the authorized path, from the landed fixed driver, with the log's integrity closed by three equal hashes. This is a writer-object verdict only: no motion, no physical validity, nothing about the route.

## Provenance

`json`/`hashlib` reads of the three run files; `git show 0a2b600959:…` for every asset and driver hash; `sha256sum` on disk; `find -newermt` for the write set; `ls --time-style` for custody; `git show … | sed -n 1040,1110p` for what the dump path prints. Zero tracked-content modifications by pZ; the run directory was read, never written. **Written, not banked; banking requested of a custodian.**

## Addendum (08:30 JST) — row 8 is now measured, not deferred; supersedes sha `5e7bdedf031562aa…`

m-p18-300 named p0's banked result report: `P0_SCRATCH_PATH_SCOPE_AND_A_GREP_THAT_HIDES_TRACKED_FILES_20260808.md` **§8.48 @ `94abce0ae0`** (file sha256 `2aa44e71…35a49`, re-hashed by me). Read at that commit, its **§4 (`:2554-2562`)** is the omission record: the visual leg is omitted **with the reason written loud** — the run is motion-bearing only in the letter (the cable settle, servos holding the compile pose), no task-related motion, **no motion verdict claimed**, the claim limited to the file's existence and its contract — which is the same scope this verdict holds. **Row 8 holds** at that `file:line`. Its §5 states what the run does not establish (the `raised`/`completed` paths under the real namespace need a route run under the unmet authorization ②), matching my row 9 — read, not relayed. ⚠ §4's sentence "2000 physics steps: the cable settling" is a statement about the code path, and my row-5 scope note stands: the object records no trace of the settle, so it is not counted as measured here either. Re-bank of the corrected prereg verified: `69dc444012` == `383acc05…` byte-identical. Rows 1-7, 9-10 unchanged.
