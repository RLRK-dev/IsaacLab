# p11 — ケーブル前提 (b)(d) 置換文言の草案 **v3（cycle 2 の union 適用・REVIEW packet）** ＋ (c) `:31` の行番号修理 — ⚠ **未検証**（5 体検証 cycle 2 = FAIL・上限到達 ⇒ 本 v3 は検証を通していない・cycle 3 は Rs1 の許可事項）

**Author** w2:p11 ARM-CONTROL-DESIGN · **Written** 2026-09-16 18:41:46 JST · Naming: **Rs1 = 人間 / Rs2 = p4**.
**系譜**: v1 = `0a13b2053a`（222 行・FAIL 印・sha256 `ee748cb8e2ece1916e549f439ab63a3b1a2071e61d1e2c1ba1c2a43b939ce6f8`）→ cycle-1 verdict `P11_L3_FIVEWAY_VERDICT_CABLE_PREMISE_DRAFT_20260809.md` §1-§4 @ `0a13b2053a`（FAIL・C3/H6/M9/L3）→ **v2** = `b9f9830b3d`（107 行・sha256 `8f3a0a574602ab666c73d4cfcd119650ee3f4d20c59d72ea1f5048b339528ebf`）→ **cycle-2 verdict = 同 verdict file §5**（FAIL・accepted CRITICAL 5・HIGH 14・union U1-U30）→ **本 v3 = U1-U30 を全て適用した REVIEW packet**（各項の処置 = §8）。v1/v2 本文は同 path の履歴（書き換えず）。
**依頼** = Rs1 2026-08-09「(b)(d) の草案を書いて」（custody = `P11_SERVO_START_DESIGN_CONFIRMATION_20260809.md:299` @ `05f1ed692c`）＋ Rs1 裁定 08-09「前提側を変更してよい（spec 未編集）」（LEDGER row 48 `:146` @ `358a1d72ad`・custody `b01cea5482`）＋ **Rs1 2026-09-14 06:00 Q5/Q6/Q7**（custody = p4 transcript `:2361`・banked verbatim = kickoff `P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md` 09-14 06:06 節 `:2408-2421` @ `236410dd84`・当卓が blob で直読）:
- **Q5**「**現行MuJoCoセルの前提として、水平曲げ自由度を正式採用する。**」理由「8/9の『前提側を変更してよい』という裁定と整合します。**旧却下文は日付・対象環境付きの履歴として保存し、現行セルに適用する前提を明記します。**」（内側の括弧は引用の入れ子のため『』に置換・原文は「」）
- **Q6**「**仕様文言の更新前に、全ケーブル結果を再実行する必要はない。**」理由「今回は、既に2自由度で動いているセルと仕様を同期する判断です。ただし、**継承する結果の環境・モデル・commitを照合し、旧1自由度の結果は隔離を維持します。条件が一致しない結果の主張には、個別の再検証が必要です。**」
- **Q7**「Q5・Q6の方針確定後、コントローラ作業と並行して開始する。」理由「対象はケーブル前提の文言草案の修正・再検証です。待つ技術的依存はなく、先に整えることで動画評価時の前提不一致を解消できます。」
⛔ **本書は spec ではない。04-Specs は Rs1 の court（CC read-only）・着地 = Rs1。** ⛔ **run 権限なし・run 0。** ⛔ **court の開示**: 当卓は (b)(d) を受諾し **(a)(c) を辞退**した（`02-Workflow/HANDOFF_p11_armcontrol.md:53`・`P11_CABLE_PREMISE_OWNERSHIP_ANSWER_20260809.md` §1）。⇒ §1/§2 (i) の DOF・定数は **emitted XML の測定**であって構築の設計判断ではない（(a) 所管者不在のまま・当卓は指名しない）。(c) は **`:31` の stale 行番号の修理のみ**（quarantine の裁定は書かない）。§0 前提の変更 = L3 ⇒ 着地前に §運用2 [VERIFY] 5 体検証（cycle 1・2 = FAIL・上限）。
**規約**: 数値は本書内の query 付き値のみ／行番号は **必ず rev を伴い blob で読む**（working tree は dirty・U1/U2 の再発防止）／build は constructor 名と初出 commit で呼ぶ／「測定」「導出」「推論」を札で分ける／人間の決定についての推論は **inference** と札を付ける。

---

## 0. v2 からの中心の変更

- **構造は同じ**（(i) 現行前提 (ii) 運用事実 (iii) 履歴 (iv) 継承規則）。変わったのは **中身の根拠の取り方**: 全行番号を blob で再測定（U1/U2）・(iii) を `:69` の逐語ブロックに（U3）・(ii) を 1 文に縮約し選択段の記述を §7 の ESCALATION へ（U6）・(iv) を Q6 の射程どおりに（U5）・`:68/:71` の修理案を追加（U4）・測定されていないことの開示（U7）・consumer 表（U10）・[DEFER-RECON] を FOUNDATIONAL 列から導出（U9）。
- **d-1 維持**（§3）。§7 は「問いを残さない」をやめ、Rs1 の open item と p6 への carry を書く（U12/U18）。

## 1. 草案が乗っている事実（全て **blob** で再測定・rev 付き）

| # | 事実 | 測定（rev） | 対照 |
|---|---|---|---|
| **F1** | 前提文の所在 = RS71 §4 `:69`（`:67` = `## 4. CABLE`）。§0 `:29`（工学的正当化）と `:31`（quarantine の gloss）が前提に寄りかかり、両方「§4 `:62`」と書く（`:62` = `**Surface:** TABLE_HEIGHT` = stale）。同 §4 の `:68`（Model 行）`:71`（Impl 行 = `add_revolute_cable`・`test:830/1066`）も 1-DOF Newton build を現行として述べる（U4） | `13a1331fc0`（RS71 最終 commit 08-08・HEAD 同一・working tree は他卓の未 commit 変更あり） | `:27` 認可／`:28` 範囲／`:29` 正当化 を直読 |
| **F2** | **現行 MuJoCo cell のケーブル（emitted XML）** = `p4_ur15_sim_20260727/ur15_steps_wired.py` @ `22feba17a6`（4,022 行）`:336-349`: `cab0` body に `<freejoint name="cable_free"/>`（`:338`）・`cab1..cab39` に **hinge 2 本ずつ** `cab{i}_y` axis `0 1 0`（`:344`）と `cab{i}_z` axis `0 0 1`（`:345`）・両 hinge とも `damping="{_spec.CABLE_BEND_DAMPING:.5f}" stiffness="{_spec.cable_joint_k():.5f}"`・range 無し（`CABLE_JOINT_RANGE = None` cell_spec `:164` @ `0f6b4a733e` ⇒ `_RANGE = ""` `:334`）。**DOF 数 = 39 inter-link joint × 2 hinge = 78 ＋ free root 6 = nv 84**（U15） | blob 直読 | `grep -c 'cab{i}_[yz]'` = 2 行（`:344/:345`）・`cab{i}` = 6 行 file-wide（`:343-346`＋`:454-455`・build span `:341-349` 内 4）（U30） |
| **F3** | **定数**: `CABLE_N = 40`・`CABLE_SEG = 0.015 m`・`CABLE_R = 0.004 m`（cell_spec `:52-57` @ `0f6b4a733e` → `task_config.py:135-137` @ `843084ae5e` = 同 file の最終 commit・HEAD と blob 同一）・EI = `CABLE_BEND_STIFFNESS 0.005 N·m²`（`:144`）・damping `0.01`（`:152`）・joint K = EI / CABLE_SEG = 0.005 / 0.015 = **0.33333 N·m/rad（XML literal・`{:.5f}`）**（`task_config.py:147` は `0.333`）。⚠ producer は **宣言済の runtime override** `CABLE_BEND_STIFFNESS_OVERRIDE` を読む（`bend_ei_in_force()` cell_spec `:196-204`・docstring「do not forbid the second source, declare it」）（U28）。総長 40 × 15 mm = **600 mm（centreline / joint spacing 長・capsule cap 分は含まない）**。wired `:721` comment「CABLE_SEG = 30 mm」= stale | 値 = blob | v1 H4 の「16.67×」= cell/route 系 literal 0.02 との比・同値 |
| **F4** | 前提 `:69` が引く build = `add_revolute_cable`（`thread_isaac_lab/scripts/test_newton_clip_routing.py` **blob `24390ebb69` = 8,550 行**: `add_cable_rod` `:868`・`add_revolute_cable` `:936`・axis 行 `:1009`「local-X bend axis ⟂ cable → vertical sag plane」・`solver_backend == "mujoco"` 分岐 `:1064`）。⚠ **v2 の `:892/:960/:1088`・8,580 行は dirty working tree の読みだった**（U1・開示）。`:69` の `:990/:942-951/:1271` は blob でも stale（`:990` = `b,`・`:942` = bend spring comment・`:1271` = pad indices）。同 blob `:920/:943` の docstring は「k = EI/L = 66.67」= stale 定数（CC4 L4-4・履歴のまま） | blob 直読 | LEDGER row 48 `:146` の 3R 測定（`:868`・`:936-1022`・`:1009`）と一致 |
| **F5** | Newton rod（履歴用）: installed **Newton 1.5.1**（env7）`builder.py:7632` `add_rod`・`:7657-7658` 逐語「cable joints providing split linear stretch/shear and split angular bend/twist degrees of freedom」・`JointType.CABLE` `:5278/:5397`・enums `dof_count` = 4 slot。cycle-1 H3 の「単一 angular DOF」は **Newton 1.4.0**（`/home/rlrk/env_isaaclab7_latest/lib/python3.12/site-packages/newton/_src/sim/builder.py:4966`）の読み。v1 §5-1 の「stretch + bend」は THREAD 自身の `test_newton_clip_routing.py` docstring の引用で Newton 版に依らない（U30） | env7 / env7_latest 直読 | — |
| **F6** | **B1 却下の逐語**（RS71 `:69` @ `13a1331fc0`）:「B1 substrate-upgrade [add world-Z DOF, re-validates all cable results] + B3 VBD declined.」日付 = 2026-06-25（Rs DECISION B2）・環境 = 当時の Newton cell。現行 cell の `cab{i}_z` axis `0 0 1` = link frame の z（undeformed で world-Z）= B1 の「world-Z DOF」に相当（測定 F2・v1 C3・row 48） | 直読 | — |
| **F7** | **C1 開示**: `cab{i}_z` の初出 commit = `bf0235cfd8` 2026-07-27 04:19:45「Bank the unauthorised UR15 control sample with its inputs」。その note の 1 行目 = `# UR15 制御側の測定記録 — ⛔ **NON-AUTHORIZED PROVISIONAL SAMPLE**`・制限句 `:11`「⛔ いかなる採用の根拠にもしてはならない。」⇒ 日付の根拠にだけ使う。⚠ **同 commit のケーブルは別物**（`ur15_cell.py:41-42` `CABLE_SEG = 0.030`（1,200 mm）・`CABLE_R = 0.005`・`:83-84` hinge range `-1.2 1.2`）= 「2 hinge 鎖の初出」であって現行定数の初出ではない（**現行 40 × 15 mm・range 無しの初出 commit は未測**）（U17）。駆動された cell の初出 = `bfb517862c` 07-27 08:51 | `git log -S'cab{i}_z'`・blob | — |
| **F8** | 年代: 06-25 前提（Newton cell）→ **06-26 基盤 pivot**（custody = LEDGER `:207/:209`「1確定 2確定 3 ACのあと」・`843084ae5e` 06-26 18:18）→ 07-27 2 hinge 鎖（F7）→ 08-06 row 48 bank → 08-09 Rs1「前提側を変更してよい」→ 09-14 Rs1 Q5 採用 | row 48・LEDGER・git log | — |
| **F9** | 運用事実（記述・currency の断定なし）: producer `ur15_steps_wired.py` @ `22feba17a6` **として読んだ限り**、駆動 = grasp-drag ＋ 認可 pin ＋ clearance-filtered candidate search（`CLEARANCE_REPORT = {}` `:1369`・`def arm_pair_min` `:1937`・呼出 `:2170`・`< ARM_CLEARANCE` 却下 `:2187/:2197`）。⚠ **v2 の `:1209/:1494/:1496` は v1（`2fba2dfd67`・2,911 行）の番号で「再確認 = 同じ行」は誤りだった**（U2・撤回）。最後の認可 run がこの版だったかは本書では主張しない（cycle-1 H5） | blob 直読 | working tree は別（`:1578/:2237`）= 読まない |
| **F10** | Stage B の環境札（U13）: `eval_runs/troot_clamp_cable_state_space_20260624/stage_b_vertsag_measure.py:75` `solver_backend="mujoco"`（Newton ModelBuilder ＋ SolverMuJoCo backend）・結果 JSON `head = eac2fbaf75` | 直読 | — |
| **F11** | **開示（U7）**: 第 2 hinge（`cab{i}_z`）が **非零の角になった banked 記録は無い** — `cable settled` 行は全て y[+0.280,+0.280]（T43 trace `:24`・CC6 repo-wide 検索 0）。⇒ (i) は XML topology から「表現できる」を述べ、動的挙動は述べない | 直読 | — |

⛔ **未測（本書は主張しない）**: 第 2 曲げ DOF が **drag 下で routing 曲率を動的に維持できるか**（DOF が在ること ≠ 保てること）。`:29` の再導出はこれに依存（§3・§7 carry）。

## 2. (b) 置換文言（RS71 §4 `:69` を **この 4 部**で置き換え・`:68/:71` を 1 行ずつ修理・paste-ready・英文は spec の言語）

> **(i) Current premise — MuJoCo cell (Rs1 DECISION 2026-09-14, Q5: the horizontal bend DOF is adopted as this cell's premise; custody = `P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md` section "2026-09-14 06:06" @ `236410dd84`, LEDGER row 48).** As emitted by `ur15_steps_wired.py` (`22feba17a6`) from `ur15_cell_spec.py` (`0f6b4a733e`) — one of six emitters in that directory; the others are not the current cell — the cable is a chain of **40 capsule links × 15 mm (600 mm centreline), radius 4 mm**, with a free root and **39 inter-link joints, each carrying two hinges — `cab{i}_y` (axis `0 1 0`) and `cab{i}_z` (axis `0 0 1`) — with identical stiffness (EI / link length = 0.005 / 0.015 = 0.33333 N·m/rad as emitted; the producer honours a declared runtime override `CABLE_BEND_STIFFNESS_OVERRIDE`), identical damping (0.01) and no joint range** (78 hinge DOF + 6 root DOF). It therefore *can represent* vertical sag **and horizontal (out-of-plane, in this section's own terms) bending**; it has no axial-stretch DOF and no per-joint twist DOF (twist of the whole chain enters only through the free root). Hinge isotropy holds to first order (equal per-hinge stiffness; second-order coupling through the composed axes). ⚠ The `cab{i}_z` axis is body-fixed: its world direction is carried by its own link's `cab{i}_y` rotation and by every upstream rotation, so under a cumulative sag Φ its tilt from world Z equals Φ and the in-horizontal-plane component of a z-hinge rotation falls as cos Φ (cycle-2 CC4: at a 300 mm free half the accumulated inclination is 31.5°, i.e. 52.3% of the rotation leaves the horizontal plane; at the 600 mm cantilever bound 83.2°). **This statement is about representable shapes: no banked record shows the second hinge at a non-zero angle, and the dynamic fidelity of horizontal curvature under grasp-drag is not measured and is not asserted here.**
> **(ii) Practice.** Horizontal routing is executed by grasp-drag plus the clip-retention pin authorized in §0 #5, as read in the producer at `22feba17a6`; this sentence records practice and neither changes a control method (§0 #3) nor grants anything.
> **(iii) History — 2026-06-25, Rs DECISION B2, Newton cell (`add_revolute_cable`, `test_newton_clip_routing.py` @ `24390ebb69` `:936`; Stage B measured with Newton ModelBuilder + SolverMuJoCo backend, `stage_b_vertsag_measure.py:75`, head `eac2fbaf75`). Retained verbatim (Rs1 Q5); true of the build it described; superseded for the current MuJoCo cell by (i).** The 2026-06-25 line reads, in full:
> > - **⚠ FIDELITY BOUNDARY (Rs DECISION B2, 2026-06-25):** the cable is a **1-DOF-per-joint PLANAR bender** built with the bend plane **VERTICAL (sag)** — 39 inter-segment joints each a single revolute about local-X→world-X (`test_newton_clip_routing.py:990` + seg_q `:942-951`, direction=(0,1,0) `build_scene:1271`). → it dynamically represents **vertical SAG + position (free root) + free-root pose**, but **NOT horizontal routing curvature** (the 5-clip 千鳥 X-Y curvature would need a 2nd bend DOF/joint). **Horizontal routing through the staggered clips is therefore KINEMATIC** (grasp-drag + the AUTHORIZED clip-retention pin, §2 / `log.md:6534`), NOT a dynamically-curved cable. This is a **banked sim2real fidelity limitation** (Rs-accepted, NOT a defect) that EXPLAINS the AR routing fidelity-QUARANTINE (LEDGER `RL-Routing-Design.md` MIXED). Cable-SHAPE robustness is trainable/validatable in-sim only for **vertical sag**, not horizontal routing curvature. (Escalation + decision: `log.md` 2026-06-25 02:27 / 10:57 / 11:05; B1 substrate-upgrade [add world-Z DOF, re-validates all cable results] + B3 VBD declined.) **✅ Stage B RESULT (2026-06-25, %2 §運用28 cross-PV CONCUR):** the REPRESENTABLE vertical sag at the grasp-local segment is SMALL — REST (on-table gravity settle) ±0.18° / 50mm-lift-held 0.78° (2-seg secant; %2 quaternion-orientation 0.45° all-30 worst) ≪ yaw-Z 12° tol → the clamp is LOCAL (sag absorbed by the free arm BEYOND the grasp) → fixed-cable banking is CONSERVATIVELY COVERED for the both-arms-lift vertical sag (**NO new held-rate needed**); the deeper Stage-D mid-air re-grasp +9..12° sag (`06-Knowledge/GD-KoShape-Finger.md:126-128`) = SEPARATE gap (tilt-follow N>1 sweep 2026-06-25, %2 cross-PV CONCUR → HOLDS narrow spec-50mm 8.6° N=5 / SLIPS >~9-11° / worst-tilt UNSWEPT = mechanism-validated low-end, robust-bank pending Y-sweep [⚠ 88mm INVARIANT #2 Rs-Q]; see §0 INVARIANT 4 + `log.md` 15:26). BONUS: horiz out-of-plane tangent ≤0.173° across all 30 held configs RE-CONFIRMS the vertical-sag-only premise on REAL data (not just the construction grep). Evidence: `eval_runs/troot_clamp_cable_state_space_20260624/stage_b_vertsag_measure.{py,json}` + `stage_b_vertsag_crosspv_opssup.*` (%2); `log.md` 2026-06-25 12:43.
> *2026-06-26:* substrate pivot to MuJoCo (LEDGER `:207/:209`; `843084ae5e`). *2026-07-27:* a two-hinge chain first appears in `bf0235cfd8` (an unauthorised provisional sample, cited for its date only; its cable constants differ from the current cell). *2026-08-06/08-09:* LEDGER row 48 records that the working cell carries the structure B1 had proposed; Rs1 rules the premise side may change. *2026-09-14:* Rs1 adopts the horizontal bend DOF as the current cell's premise (Q5).
> **(iv) Inheritance rule (Rs1 Q6, 2026-09-14).** Updating this wording does not by itself require re-running all cable results. A result banked under the 2026-06-25 premise is used for the current cell only after its **environment, model and commit** have been collated against the current cell; results of that build remain that build's results and are kept apart from the current cell's claims; any claim whose conditions do not match the current cell needs individual re-verification. This wording changes no result's status. (The collation duty is registered in the DDR with an owner — see the landing packet; until that row exists this sentence has no enforcement path.)

- **`:68` 修理案**（Model 行・現行「40 segments × 15 mm = 600 mm; CABLE_RADIUS 0.004 … Rigid-capsule CABLE-joint chain (NOT a Cosserat rod — validate.sh Layer 6 guard)」）: 数値は現行 cell と同じなので残し、「CABLE-joint chain」を「hinge chain (MuJoCo cell: two hinges per inter-link joint, see (i); the Newton CABLE-joint chain is the 2026-06-25 build, see (iii))」へ。Layer 6 guard の scan root は `thread_isaac_lab/{configs,envs}` で現行 cell の dir（`eval_runs/…/p4_ur15_sim_20260727/`）は範囲外 — 「guard が現行 cell を検証している」とは書かない（U29）。
- **`:71` 修理案**（Impl 行・現行「`task_config.py`, cable build (`add_revolute_cable`, `test:830/1066`)」）: 「**Impl:** `task_config.py` (constants); cable build of the current MuJoCo cell = `ur15_steps_wired.py` `:336-349` @ `22feba17a6` (from `ur15_cell_spec.py` @ `0f6b4a733e`); the 2026-06-25 build = `add_revolute_cable` (`test_newton_clip_routing.py` @ `24390ebb69` `:936`)」。⛔ どちらも Rs1 の一語事項（04-Specs）。
- **(i) が置き換えるもの**: `:69` の導出「1-DOF-per-joint PLANAR bender … NOT horizontal routing curvature … therefore KINEMATIC」。**(ii) が守るもの**: 運用事実が導出と一緒に落ちない。**(iii) が保存するもの**: `:69` の全文（Rs1 Q5 = 削除しない・日付と環境）。**(iv) が置くもの**: Q6 の規則（射程 = 本更新・照合・隔離維持・個別再検証）。
- 「supersedes B2」という語は使わない（Rs1 の語でない・v2 の推論 = U30）。(i) の数値は task_config の値の転記（`843084ae5e` = file 最終 commit・HEAD 同一）— 値が動けば参照が正。

## 3. (d) §0 invariant 5 の正当化行 `:29` — **d-1 維持**（認可不変・正当化は現行 cell について再導出待ち）

- **構造**: `:27` 認可（Rs 裁定・`log.md:6534`）／`:28` 範囲（Rs 2026-07-15 逐語・CLIP-RETENTION ONLY・「permanently wired into the learning env」）／`:29` 工学的正当化（= 前提 B2 に立つ）。**認可は前提に立っていない。前提に立っているのは `:29` だけ。**
- **(i) の採用で切れるもの**: `:29` の導出の第 1 段（1-DOF ⇒ 水平曲率を表現できない）。切れるのは導出であって認可ではない。
- **提案文（`:29` の置換・paste-ready）**:
> **Why it had to be decided** (the engineering half): recorded on 2026-07-15 against §4's 2026-06-25 premise (1-DOF planar bender ⇒ horizontal routing KINEMATIC ⇒ a pin-less RL env cannot represent the task). **For the current MuJoCo cell that premise is superseded (§4 (i), Rs1 2026-09-14): the cell carries a second bend DOF, and whether it can hold routing curvature dynamically under drag is unmeasured.** The pin's engineering justification for the current cell is therefore **pending re-derivation**; until it lands, the pin stands on Rs's rulings alone (`:27`, `:28`), which are unchanged. The 2026-06-25 derivation is retained in §4 (iii) as the justification for the build it described.
- ⚠ **これは問いを開く**（U12）: env に恒久配線された pin（`:28`）の工学的必要性が「再導出待ち」になる。**Rs1 への open item = §7-3**。d-2（新前提からの再導出）は未測で書けない・d-3（変更なし）は測定 F2 に反する。
- ⛔ §0 は Rs1 の court — 本節は提案。

## 4. (c) `:31` の stale 行番号修理（**測定のみ**・quarantine の裁定は書かない・(c) court の辞退は冒頭で開示）

- **現行** `:31`: 「…already explains the AR-routing QUARANTINE (**§4 `:62`**, B1 substrate-upgrade DECLINED)」（`:62` = TABLE_HEIGHT = stale）。
- **置換案（括弧内のみ）**: `(decision-of-record: 07-Design/00-DESIGN-STATUS-LEDGER.md, the RL-Routing-Design.md MIXED row — the sentence "its mechanism (spring-follow + kinematic hold) is **fidelity-QUARANTINED**"; B1 substrate-upgrade DECLINED for the 2026-06-25 Newton cell, see §4 (iii))`。**content pin の一意性（query 付き・U11）**: `grep -cF 'is **fidelity-QUARANTINED**' 00-DESIGN-STATUS-LEDGER.md` = 1（`:63`）・`grep -nF 'spring-follow + kinematic hold'` = 2 行（`:63`・`:146` = row 48 の引用）・`**` 無しでは 0。**M8**: 同行が辿る `LL-S1B-…-2026-06-04.md` は untracked（06-Knowledge 104 中 86）— 本修理はその脆さを継ぐ。**L2**: `:31` = stale §-pointer／`:69` = stale code pointer ＋ 複合 doc-pointer — 重なる（別種ではない・U30）。

## 5. 影響面（consumer 表・U10/U29）と限界

**closed query** `git grep -l -I "1-DOF-per-joint" HEAD -- '*.md'` @ HEAD `00a36b340d` = **10 file**（ARM_CONTROL_DESIGN_GROUNDING… `:103`・DAPG_WHOLEROUTE_C1C2_SCOPING_COORD2 `:23`・本書・P18_CLAMP_COURT… `:6138/:44537`・kickoff `:1405`・P4_TEMPLATE_RULE… `:14`・P5_UR15_CELL_CONSTANTS_SPEC `:319`・P5_UR15_CLIP_DETAIL_DESIGN `:7596`・RS71 `:29/:69`・LEDGER `:72`）。**現行として前提を述べる面（着地と一緒に動く）**:

| surface | line | 何を運ぶか | owner | 着地時 |
|---|---|---|---|---|
| RS71 `:29` `:31` `:68` `:69` `:71` | @ `13a1331fc0` | 本体（§2-§4） | Rs1 | 本 packet |
| RS71 `:40`（§0-A） | `sag` ×7・`horizontal` ×1・`1-DOF`/`B2` literal 0 | sag 記述（逐語依存ではない） | Rs1 | 着地時に読む |
| `04-Specs/SOMA.md:28` | `horizontal routing curvature = KINEMATIC (… Rs DECISION B2, RS71 §4)` | 目標 SSOT の deploy 要件 | **Rs1**（04-Specs） | 本 packet に同梱（p6 は触れない・U23） |
| `07-Design/00-DESIGN-STATUS-LEDGER.md:72` | 🟢 row「pin 無しでは C1 は保持されない」が `RS71:62` と逐語前提に接地 | 成否 SSOT 行 | p6 | 内容 pin へ（§運用4 mandate） |
| LEDGER `:63`（RL-Routing MIXED 行）・row 48 `:146` | quarantine の decision-of-record・本件の register 行 | 成否 SSOT | p6 | row 48 を閉じる（cap = kickoff `:1416`・actor = **p6**） |
| `docs/logical_decomposition.html:174/:225` | 「banked spec RS71 §4 (B2) が pin を routing 機構として NAME」 | 現在 frame 地図 | p6 | 内容 pin へ |
| `…/T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild/state.md:106-107/:264`・`…/T-L1C-PerSkill-RL/state.md:6` | 前提の引用・quarantine 由来 gate | node state | p6 | 内容 pin へ |
| `PIN_DB_WINDOW_GATE_MATERIALS_RSTECHLEAD_20260717.md:61`（file 203 行）・`PIN_D_TRIGGER_CHARTER_VTDESIGN_20260717.md:287` | FIDELITY BOUNDARY の引用 | p4 / p5 | 各 owner | 内容 pin へ |
| `02-Workflow/HANDOFF_p11_armcontrol.md:46/:67`・`HANDOFF_p5_vtdesign.md` | 前提を行番号で pin | p11 / p5 | 各 owner | p11 = 着地後に自分で直す |
| `P5_CABLE_PREMISE_DEPENDENCY_OF_43STEP_20260809.md`・`P5_UR15_CELL_CONSTANTS_SPEC_20260727.md:319/:321`・`P4_TEMPLATE_RULE_AND_THE_CABLE_STRUCTURE_20260727.md:14` | 43-step 下流・cell 定数 spec・template rule（日付付き narrative） | p5 / p4 | 各 owner | 日付付き履歴として残せる |
| `docs/nest-tracker/nest-snapshot.json:774`・`scripts/gen_gantt.py:61/:92` | 生成物・script 内 label `fidelity-QUARANTINE` | generator / repo | — | 前提でなく label・不変 |
| `ITEM5_SPEC_LANDING_PREPARED_RS71_PATCH_20260808.patch`（`ac780d3dc1`） | RS71 用の prepared patch = 本 packet で **dead**（+9 行・`:62` 系を含む） | p4 | 開示のみ |

- **Layer 6 guard（U29）**: tracked wrapper = `scripts/validations/check_cable_model.sh`（`validate.sh:122`・tracked `b83c574220` 07-02）・delegate `scripts/check_cable_model_mislabel.sh` = untracked（wrapper は fail-closed）・scan root = `thread_isaac_lab/{configs,envs}` ⇒ 現行 cell（`eval_runs/…/p4_ur15_sim_20260727/`）は範囲外。(i) は Layer 6 が走査しない cable についての最初の §4 記述。
- ⛔ 触れないもの: 04-Specs の編集／(a) を含む統合文言／build・probe・training／`:29` の再導出に要る測定／`task_config.py:148` の較正記録の再現性（CC4 L4-5・task_config = Rs court・記録のみ）／他 5 emitter の literal。

## 6. gate 記録（U9/U18/U20/U21/U22/U27）

- **[TASK] L=L3** | node_id = **無し**。DDR **#71**（`:175` @ HEAD・Rs1 09-05 11:07）= 「file を作る・共有面を変える卓 task だけ node 化（p6 起票・都度 Rs1 の作成承認）」。本件は file（本書・08-09 作成 = #71 より前）と共有面変更の提案（RS71）の両方 ⇒ **#71 の下では node 化対象**。当卓は自己 disposition しない ⇒ §7-4 の open item（p6 起票・Rs1 承認）。
- **[L-TRIAGE] stage1**（rule-check skill Step 5/7 の形）:
  ```yaml
  L_TRIAGE: {self_declared: L3, auto_escalated: L3, final: L3}
  evidence:
    step_1_file_matches: [{path: "thread-vault/04-Specs/RS71-System-Spec-SSOT.md", pattern: "04-Specs (proposal target; not edited)"}, {path: "thread-vault/04-Specs/SOMA.md", pattern: "04-Specs (consumer :28; not edited)"}]
    step_2_diff_keywords:  # measured on the v2 blob b9f9830b3d with grep -ci; self-references marked
      - {keyword: ik, hits: 3, context: ":32 :39 (IK candidates, descriptive) :70 (self-ref)"}
      - {keyword: newton, hits: 8, context: "history (iii) / F5 / F10"}
      - {keyword: solver, hits: 1, context: "F4 solver_backend branch"}
      - {keyword: phase, hits: 1, context: "self-ref :70"}
      - {keyword: gravity, hits: 1, context: "self-ref :70"}
      - {keyword: reward|success|terminated|time_outs|vbd|featherstone|physx|diffik|episode_length|_reset_worlds, hits: 0}
    step_3_quantitative: {estimated_lines: ">200 (this file)", estimated_files: 3}
    step_4_skill_variant: "verification-subagent (5-way, cycle cap 2)"
    foundational_touch: "§0 invariant 5 rationale line :29 (proposal only) => L3"
  notification: "auto_escalated = self_declared (L3); no demotion requested"
  ```
  `[L-TRIAGE RESULT] final_L: L3 | confidence: high | evidence_summary: 04-Specs proposal target + §0 rationale line + keywords ik/newton/solver present | required_gates: [DEFER-RECON, VERIFY 5-way (cap 2, done: FAIL×2), RULE-CHECK stage2, 層2 事後 (Rs1 着地後), 層5] | status: REVIEW (cap reached)`
- **[DEFER-RECON]**（DDR @ HEAD `00a36b340d`・LEDGER clean・**FOUNDATIONAL 列を読んだ**: ⭐FOUNDATIONAL = rows 2, 4, 12, 18, 19, 26, 38, 44, 45, 48, 49, 68）:
  | row | 依存判定 |
  |---|---|
  | **#48**（FOUNDATIONAL・本件の register 行） | **gate する** — premise 側の disposition = Rs1 Q5/Q6（09-14）・閉じる事象 = Rs1 の着地（kickoff `:1416`）・actor = p6 |
  | #2 / #4 / #12（pin 削除 directive 波及） | 依存なし — 07-21 裁定で pin 例外復活・§3 は認可不変 |
  | #18（grip-efficacy SRG・execution HOLD） | 文言は run しない ⇒ 本 chunk を塞がない。**#18 の cap は別軸・不変**（`:1416`）— §3 の再導出に要る probe は #18 の HOLD 下 |
  | #19（ENV-MULTIWORLD freeze・env7 worlds 1-3 cable frozen） | 別 object（env7 multi-world Newton env）。(i) は単一 world の MuJoCo emitted cell の記述に限定 ⇒ 依存なし・境界として明記 |
  | #26（arm actuator 綱引き） | arm 側・cable 前提に依存なし |
  | #38（robot premise UR5e→UR15・spec 未反映） | (i) は robot 名を主張しない（file 名のみ）⇒ 依存なし・同 file の pending 着地として Rs1 が束ねうる |
  | #44 / #45（§0 #4/#2 の未着地 divergence・同 file） | 前提独立。同 RS71 に **≥3 件の Rs1 着地待ち**（#44/#45/#68 ＋ 本件）— 順序は Rs1 |
  | #49（整定未到達で動く腕の数値・§0 #1） | (i) の数値は XML 定数（run 測定でない）⇒ 依存なし。将来の第 2 hinge 測定は #49 を継ぐ |
  | #68（UR15-B premise・spec 未反映） | 同 file の pending 着地・cable 前提と独立 |
  | #46（UR15 cell のクリップは自作・権威実装と別物） | (ii) は clip 形状を主張しない・(i) は「staggered clips」語を使わない ⇒ 依存なし |
  | #64（5-clip「幾何的に可能」は現 cell で未確立） | (ii) は 5-clip 完遂を主張しない（practice の記述のみ）⇒ 依存なし |
  | #66（§0 違反→fix→受入） | 軸どおり: 引用 emitter commit `22feba17a6`（09-05）> 受入 fix `0f6b4a733e`（08-10）> 受入報告 `839b6df6de`（08-09）⇒ 引用版は受入後。残 4 file scope の閉否は当卓未確認（本書は run 0） |
  | #69（条件つき run 認可・未発火） | 無関係（cap = `:1416`） |
  | #71（node 化規則） | **open**（§7-4） |
  | #72（共有 tree の author 無し WIP・`358a1d72ad` には無く HEAD `:176`） | 本書は blob で読む ⇒ 依存なし |
  **premise を塞ぐ FOUNDATIONAL 未解決行 = #48 のみ**（Rs1 が premise 側を disposition 済・着地待ち）。
- **層4 prior-art guard**: verdict §5-D（18:25:25 JST・rc=2・findings 43・blockers 19・lessons 14・dirty 3,388・自己捕捉開示）。
- **[VERIFY] 5 体（事前）**: cycle 1 = FAIL @ `0a13b2053a`／cycle 2 = FAIL（verdict §5・上限）⇒ **REVIEW = Rs1**（skill Step 7 `:441`）。本 v3 は検証を通していない。
- **[DESIGN-GATE] = 非該当**（判定文 = verdict §5-E）／**[RULE-CHECK] stage2 Tier 0-3 = PASS**（verdict §5-E）／**Step 8** = cycle 2 は pipeline で永続化（verdict §5-F）・cycle 1 は body 未保存で記録不能（欠陥として残す）。
- **層2 事後／層5**: 着地は Rs1 ⇒ 当卓の事後 = bank 後に blob を再読。

## 7. Rs1 へ上げる形（**REVIEW packet**・経路 = p18 → p4 → Rs1・U23/U26）

1. **判定** = cycle 2 FAIL・上限到達 ⇒ **本書は着地候補ではなく REVIEW**。Rs1 の選択肢: **A** LEDGER ＋ RS71 §4 に 1 行の supersession flag のみ／**B** (iii)(iv) のみ着地（Q5/Q6 の指定そのもの）／**C** v3 の 4 部＋`:29`＋`:31`＋`:68/:71` を着地（未検証のまま着地しない ⇒ D と組む）／**D** v3 に対する cycle 3 を Rs1 が許可（卓は許可しない・自発しない）。当卓の推奨 = **B、または D→C**。
2. **ESCALATION（spec に書くか Rs1 が決める・(ii) から外した記述）**: 現行 producer の腕姿勢選択段 = **clearance-filtered candidate search**（IK 候補を scratch model で評価し腕間 clearance < `ARM_CLEARANCE` で却下・`ur15_steps_wired.py` @ `22feba17a6` `:1369/:1937/:2170/:2187/:2197`）。これを RS71 に載せるか・どの節か・spec 拘束とするか = Rs1。
3. **open item（U12）**: `:29` の置換で env 配線 pin（`:28`）の工学的必要性が「再導出待ち」になる — **pin はその間も立つか・期限は** = Rs1。
4. **open item（U18）**: DDR #71 の下で本 task を node 化するか（p6 起票・Rs1 承認）。
5. **p6 への依頼（着地時・U8/U10/U23）**: (a) row 48 を閉じる（actor = p6・cap `:1416`）／(b) **DDR 行を起票**: (iv) の照合義務 — owner・trigger =「2026-09-14 より前の build から継承する cable claim」・受入条件 = 環境・モデル・commit の照合記録／(c) carry 2 件を DDR へ: `:29` の再導出・drag 下の曲率維持の測定（probe = 認可事項・#18 HOLD 下）／(d) §5 表の p6 owner 行（LEDGER `:72`・地図・state.md）を内容 pin へ。
6. **Rs1 packet に同梱**（p6 が触れない 04-Specs）: `SOMA.md:28` の内容 pin 化。
7. 当卓が要らないもの = 着地の一語のみ。本書は 04-Specs を編集しない・run 0・cycle 3 を自発しない。

## 8. cycle-1 / cycle-2 項目の処置（**受入と未了を分ける**）

| # | 内容 | v3 での処置 | 状態 |
|---|---|---|---|
| c1 C1 | `bf0235cfd8` unauthorised sample | F7（1 行目・`:11` を正しく引用・別ケーブルを開示） | 受入 |
| c1 C2 | dead code への pin | F2/F9 = `22feba17a6` blob 実測（U2 訂正） | 受入 |
| c1 C3 | B1-declined の保存 | (iii) 逐語ブロック | 受入 |
| c1 H1 | DEFER-RECON | §6 = 列から導出 | 受入 |
| c1 H2 | guard | verdict §5-D | 受入 |
| c1 H3 | Newton rod DOF | F5（1.5.1 / 1.4.0 の path・THREAD docstring を分離） | 受入 |
| c1 H4 | 定数 | F3 | 受入 |
| c1 H5 | currency 断定 | (ii)/F9 = 「as read in the producer at 22feba17a6」・最後の認可 run は主張しない | **受入（v2 は未実装だった）** |
| c1 H6 | 選択段の Rs1 承認 | (ii) から外し §7-2 ESCALATION へ | 受入（v2 の fence 内置きは撤回） |
| c1 M1 | z-hinge 軸合成 | (i) 閉形式 ＋ CC4 数値 | 受入 |
| c1 M2 / M6 / M7 | hedge scope・見出し・OPTIONS 根拠 | §0 / §3 / 根拠 = Rs1 Q5/Q6 | 受入 |
| c1 M3 | grep -c の呼び方 | F2（行数 file-wide・span 内） | 受入 |
| c1 M4 / M5 | 年代 caveat・06-26 pivot | F8（custody 付き） | 受入 |
| c1 M8 / L2 | untracked 引用先・pointer 欠陥 | §4 | 受入 |
| c1 L1 | 外部文書の stale 行 | §5 表（cycle-1 の pointer 自体が誤りだった = U10） | 受入 |
| c1 §「次」5 | Step 8 | cycle 2 = 実施・cycle 1 = **記録不能** | **未了（恒久）** |
| c2 U1-U30 | verdict §5-A | 各行の「処置 → v3」欄のとおり | 受入（本 v3 は未検証） |

## 9. cycle 2 の結果
- verdict file §5（DECIDE = FAIL・上限 ⇒ REVIEW = Rs1・union U1-U30・REBUT 3・層4・DESIGN-GATE/stage2・Step 8）。本 v3 = その処置を適用した REVIEW packet。**cycle 3 は Rs1 の許可事項**。
