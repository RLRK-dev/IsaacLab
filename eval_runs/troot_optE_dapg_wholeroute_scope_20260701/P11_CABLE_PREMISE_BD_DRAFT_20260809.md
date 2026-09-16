# p11 — ケーブル前提 (b)(d) 置換文言の草案 **v2（cycle 2）** ＋ (c) citation 修理 — ⚠ **未検証**（5 体検証 cycle 2 の結果は §9 に追記）

**Author** w2:p11 ARM-CONTROL-DESIGN · **Written** 2026-09-16 18:00:53 JST · Naming: **Rs1 = 人間 / Rs2 = p4**.
**系譜**: v1 = `0a13b2053a`（222 行・FAIL 印・sha256 `ee748cb8e2ece191…afc6`）→ cycle-1 verdict `P11_L3_FIVEWAY_VERDICT_CABLE_PREMISE_DRAFT_20260809.md` @ `0a13b2053a`（DECIDE FAIL・CRITICAL 3・HIGH 6・MEDIUM 9・LOW 3）。**本 v2 = その全部（C1-C3・H1-H6・M1-M8・L1-L2）＋ Rs1 の Q5/Q6 を反映した書き直し**（cycle-1 各項の処置 = §8）。v1 の本文は同 path の履歴（書き換えず）。
**依頼** = Rs1 2026-08-09「(b)(d) の草案を書いて」＋ Rs1 裁定 08-09「前提側を変更してよい（spec 未編集）」（LEDGER row 48 `:146` @ `358a1d72ad`・custody `b01cea5482`）＋ **Rs1 2026-09-14 06:00 Q5/Q6/Q7**（custody = p4 transcript `:2361`・banked verbatim = kickoff `P4_MOUNTING_C-2_CHAIN_KICKOFF_20260808.md` 09-14 06:06 節 @ `236410dd84`・当卓が blob で直読）:
- **Q5**「**現行MuJoCoセルの前提として、水平曲げ自由度を正式採用する。**」理由「8/9の『前提側を変更してよい』という裁定と整合します。**旧却下文は日付・対象環境付きの履歴として保存し、現行セルに適用する前提を明記します。**」
- **Q6**「**仕様文言の更新前に、全ケーブル結果を再実行する必要はない。**」理由「今回は、既に2自由度で動いているセルと仕様を同期する判断です。ただし、**継承する結果の環境・モデル・commitを照合し、旧1自由度の結果は隔離を維持します。条件が一致しない結果の主張には、個別の再検証が必要です。**」
- **Q7**「Q5・Q6の方針確定後、コントローラ作業と並行して開始する。」理由「対象はケーブル前提の文言草案の修正・再検証です。」
⛔ **本書は spec ではない。04-Specs は Rs1 の court（CC read-only）・着地 = Rs1。** ⛔ **run 権限なし・run 0。** ⛔ **統合文言は書かない** — (a) は所管者不在・本書は **(b)(d) ＋ (c) の 1 行修理**。§0 前提の変更 = L3 ⇒ 着地前に §運用2 [VERIFY] 5 体検証（cycle 2 = 本書・上限）。
**規約**: 数値は本書内の query 付き値のみ／行番号は **必ず rev を伴う**／build は **constructor 名と初出 commit** で呼び backend 名で呼ばない（v1 §5-4）／「測定」と「導出」を札で分ける。

---

## 0. v1 からの中心の変更 — 「選択肢＋escalation」から「採用された前提の文言」へ

- v1 の C3（B1-declined の保存）と verdict の escalation 2 問（①事実の記録 ②B1 却下の現効）は **Rs1 が答えた**: ① = row 48 が記録済（08-06/08-09）② = **Q5 で supersede**（水平曲げ DOF = 現行 MuJoCo cell の正式前提・旧却下文 = 日付・環境付き履歴）。⇒ 本書は b-1/b-2/b-3 の選択肢を置かず、**(i) 現行前提 (ii) 運用事実 (iii) 日付・環境付き履歴 (iv) 継承規則（Q6）** の 4 部構成の **1 つの文言**を出す。
- (d) は v1 の d-1（認可 = Rs 裁定に立つ・不変／`:29` の正当化 = 現行 cell では再導出待ち）を維持（§3）。
- F2b（Newton file の実行時 constructor）は **問いとして閉じた**: Q5 が対象を「現行 MuJoCo セル」= live emitter `ur15_steps_wired.py` に限定したので、Newton file 側の分岐は履歴 (iii) の中でのみ現れる。

## 1. 草案が乗っている事実（**全て live emitter と pinned blob で再測定**・C2・H4・H5）

| # | 事実 | 測定（rev つき） | 対照 |
|---|---|---|---|
| **F1** | 前提文の所在 = RS71 §4 `:69`（`:67` = 見出し `## 4. CABLE`）。§0 `:29`（工学的正当化）と `:31`（quarantine の gloss）が前提に寄りかかり、両方とも「§4 `:62`」と書く（`:62` = TABLE_HEIGHT の項目 = stale pointer） | `13a1331fc0`（RS71 の最終 commit 08-08・HEAD 同一・working tree は他卓の未 commit 変更あり = 本書は blob で読む） | `:27` 認可／`:28` 範囲／`:29` 正当化 の 3 行を直読 |
| **F2** | **現行 MuJoCo cell のケーブル** = live emitter `p4_ur15_sim_20260727/ur15_steps_wired.py` @ `22feba17a6` `:336-349`: `CABLE_N` 個の capsule link（長さ `CABLE_SEG`・半径 `CABLE_R`）・**link ごとに hinge 2 本** `cab{i}_y` axis `0 1 0`（`:344`）と `cab{i}_z` axis `0 0 1`（`:345`）・damping = `_spec.CABLE_BEND_DAMPING`・stiffness = `_spec.cable_joint_k()`（両 hinge 同一）・**range 無し**（`CABLE_JOINT_RANGE = None` cell_spec `:164` ⇒ `_RANGE = ""` `:334`） | blob 直読 | `grep -c 'cab{i}_[yz]'` = 2 行・`cab{i}` 出現行 = 6（`:341-349`） |
| **F3** | **定数（実値・H4）**: `CABLE_N = 40`・`CABLE_SEG = 0.015 m`・`CABLE_R = 0.004 m`（cell_spec `:52-57` @ `0f6b4a733e` → `task_config.py:135-137` @ `843084ae5e`）・EI = `CABLE_BEND_STIFFNESS 0.005 N·m²`（`:144`）・damping `0.01`（`:152`）・**joint K = EI / CABLE_SEG = 0.005 / 0.015 = 0.3333 N·m/rad**（`cable_joint_k()` cell_spec `:237-245`・comment が `task_config.py:146` を引く）・総長 40 × 15 mm = 600 mm（cell_spec `:1197` が SSOT 総長を検算）。⚠ wired `:721` の comment「CABLE_SEG = 30 mm」は **stale**（値は 15 mm・comment のみ） | 値は task_config HEAD・式は cell_spec blob | v1 H4 の「0.3333・16.67×」= 同値（cell/route 系 literal 0.02 との比） |
| **F4** | 前提が引く build = `add_revolute_cable`（`thread_isaac_lab/scripts/test_newton_clip_routing.py` @ `24390ebb69` **`:960`**・1 revolute/joint・vertical plane）。`:69` の行番号 `:990/:942-951/:1271` は **stale**（同 file 07-15 の版で `:990` = `seg_q = …` のみ関連・`:942` = MUJOCO_CONTACT_KE の comment・`:1271` = box）。同 file の分岐 `solver_backend == "mujoco"` = `:1088`・`add_cable_rod` = `:892` | HEAD の file 直読（8,580 行） | 関数名 grep = 各 1 |
| **F5** | Newton rod（履歴用・H3 再導出）: **installed Newton 1.5.1**（env7・09-10 更新）`builder.py:7632` `add_rod` docstring `:7657-7658` 逐語「cable joints providing **split linear stretch/shear and split angular bend/twist** degrees of freedom」。⇒ v1 §5-1 の「stretch + bend」も cycle-1 H3 の「単一・非軸分解 angular DOF」（Newton 1.4.0 の読み）も **現 版では正確でない** — 本書は **版を付けて**引く | env7 の file 直読 | `JointType.CABLE` = builder `:5278/:5397` |
| **F6** | **B1 却下の逐語**（RS71 `:69` @ `13a1331fc0`）:「B1 substrate-upgrade [add world-Z DOF, re-validates all cable results] + B3 VBD declined.」日付 = **2026-06-25**（Rs DECISION B2）・対象環境 = 当時の Newton cell（`add_revolute_cable`）。**現行 cell の `cab{i}_z` axis `0 0 1` = その「world-Z DOF」そのもの**（v1 C3・row 48） | 直読 | — |
| **F7** | **C1 開示**: 2 hinge cell の初出 commit = `bf0235cfd8` **2026-07-27 04:19:45**「Bank the **unauthorised** UR15 control sample with its inputs」— その banked note の 1 行目は「⛔ NON-AUTHORIZED PROVISIONAL SAMPLE（いかなる採用の根拠にもするな）」。⇒ 本書はこの commit を **日付の根拠にだけ**使い、topology の「採用」は **Rs1 の Q5（09-14）に立つ**（この commit にではない）。駆動された cell の初出 = `bfb517862c` 07-27 08:51 | `git log -S'cab{i}_z'` 直読 | — |
| **F8** | 年代（M4/M5）: 06-25 前提（Newton cell）→ **06-26 基盤 pivot（Newton VBD → mujoco・LEDGER row 48 が持つ 3 日付の 1 つ）** → 07-27 2 hinge cell（F7）→ 08-06 row 48 bank → 08-09 Rs1「前提側を変更してよい」→ **09-14 Rs1 Q5 採用**。⇒ 前提は banked 当日の全 build について真で、**32 日後の build に追い越された**（v1 §5-3）— caveat は §2 (iii) に置く（M4） | row 48・git log | — |
| **F9** | 運用事実（v1 §8・H5 currency 札つき）: 駆動 = grasp-drag ＋ 認可 pin ＋ **clearance-filtered candidate search**（IK 候補を scratch model で評価し腕間 clearance < `ARM_CLEARANCE` で却下）。live emitter @ `22feba17a6`: `CLEARANCE_REPORT` `:1209`・`arm_pair_min(sc, …)` `:1494`・却下 `:1496-1499`（v1 §8 は `2fba2dfd67` で読んだ・本書は `22feba17a6` で再確認 = 同じ行） | blob 直読 | — |

⛔ **未測（本書は主張しない）**: 第 2 曲げ DOF が **drag 下で routing 曲率を動的に維持できるか**（DOF が在ること ≠ 保てること・v1 d-2）。`:29` の再導出はこれに依存（§3）。

## 2. (b) 置換文言（RS71 §4 `:69` を **この 4 部**で置き換える・paste-ready・英文は spec の言語）

> **(i) Current premise — MuJoCo cell (Rs1 DECISION 2026-09-14, Q5; supersedes B2 for this cell).** The cable of the current MuJoCo cell (built by `ur15_steps_wired.py` from `ur15_cell_spec.py`; pinned `22feba17a6` / `0f6b4a733e`) is a chain of **40 capsule links × 15 mm (600 mm), radius 4 mm**, adjacent links joined by **two hinges per link — `cab{i}_y` (axis `0 1 0`) and `cab{i}_z` (axis `0 0 1`) — identically parameterized (joint stiffness = EI / link length = 0.005 / 0.015 = 0.333 N·m/rad; damping 0.01; no joint range)**. It therefore represents **vertical sag AND horizontal (in-plane) bending** plus free-root position/pose; it does **not** represent axial stretch or twist (no such DOF). ⚠ The `cab{i}_z` axis is fixed in the link frame, so "horizontal bend" is exact in the undeformed reference and composes with upstream y-deflection when the chain sags (M1); the DOF exists at every link regardless. **This statement is about representable shapes; the dynamic fidelity of horizontal curvature under grasp-drag is not measured and is not asserted here.**
> **(ii) Practice (descriptive, not a new authorization).** Horizontal routing through the staggered clips **is at present executed** by grasp-drag plus the authorized clip-retention pin (§0 #5), with arm poses chosen by a **clearance-filtered candidate search** (IK candidates evaluated on a scratch model and rejected when inter-arm clearance falls below `ARM_CLEARANCE`; `ur15_steps_wired.py` @ `22feba17a6` `:1209/:1494/:1496`). This is a **chosen execution method, not a consequence of (i)**; recording it here changes no control method (§0 #3) and grants nothing (H6: the selection stage is described, its status as a spec constraint is **pending Rs1 sign-off**).
> **(iii) History (dated, environment-tagged; retained verbatim, not deleted — Rs1 Q5).** *2026-06-25, Rs DECISION B2, Newton cell (`add_revolute_cable`, `test_newton_clip_routing.py`; 1 revolute per inter-segment joint, vertical bend plane):* the cable represented vertical sag but **not horizontal routing curvature**; horizontal routing was therefore executed kinematically; **B1 substrate-upgrade [add world-Z DOF, re-validates all cable results] and B3 VBD were DECLINED for that environment**; Stage B result (vertical sag ±0.18° / 0.78°; %2 cross-PV CONCUR) measured on that cell. *2026-06-26:* substrate pivot to MuJoCo. *2026-07-27:* the UR15 MuJoCo cell with two hinges per link first appears (`bf0235cfd8`, banked as an unauthorised provisional sample — cited for its date only). *2026-08-06/08-09:* LEDGER row 48 records that the working cell carries the structure B1 had proposed; Rs1 rules the premise side may change. *2026-09-14:* Rs1 adopts the horizontal bend DOF as the current cell's premise (Q5). **The 2026-06-25 text remains true of the build it described; it is superseded for the current MuJoCo cell only.**
> **(iv) Inheritance rule (Rs1 Q6).** Results banked under the 1-DOF premise are **not re-run wholesale**. A banked cable result is inherited by the current cell only after its **environment, model and commit** are collated against the current cell; results of the 1-DOF build (e.g., the Stage B sag numbers; the AR-routing fidelity-QUARANTINE cause) **stay quarantined as that build's results**; **any claim whose conditions do not match the current cell needs individual re-verification** before it is used for the current cell. (Pointer to the quarantine's decision-of-record: `07-Design/00-DESIGN-STATUS-LEDGER.md`, the `RL-Routing-Design.md` MIXED row — the sentence "its mechanism (spring-follow + kinematic hold) is fidelity-QUARANTINED".)

- **(i) が置き換えるもの**: `:69` の「1-DOF-per-joint PLANAR bender … NOT horizontal routing curvature … therefore KINEMATIC」の導出。**(ii) が守るもの**: 運用事実（導出が切れても宙に浮かない・§0 #3 に触れる読みを塞ぐ）。**(iii) が保存するもの**: B2 の全文と B1/B3 却下（Rs1 Q5 の要件 = 削除しない・日付と環境を付ける）。**(iv) が置くもの**: Q6 の規則（全再実行不要・照合・隔離維持・個別再検証）。
- ⚠ **(i) の数値は task_config HEAD の値**（`843084ae5e`）— spec が `task_config.py:135-137/:144/:152` を引くのは現行 `:68/:70` と同じ形。値が動けば文言でなく参照が正。

## 3. (d) §0 invariant 5 の正当化行 `:29` — **d-1 維持**（認可不変・正当化は現行 cell について再導出待ち）

- **構造（変わらない）**: `:27` 認可（Rs 裁定・`log.md:6534`）／`:28` 範囲（Rs 2026-07-15 逐語・CLIP-RETENTION ONLY）／`:29` 工学的正当化（= 前提 B2 に立つ）。**認可は前提に立っていない。前提に立っているのは `:29` だけ。**
- **(i) の採用で切れるもの**: `:29` の導出「1-DOF ⇒ 水平曲率を表現できない ⇒ routing は KINEMATIC ⇒ pin-less RL env は task を表現できない」の第 1 段。**切れるのは導出であって認可ではない。**
- **提案文（`:29` の置換・paste-ready）**:
> **Why it had to be decided** (the engineering half): recorded on 2026-07-15 against §4's 2026-06-25 premise (1-DOF planar bender ⇒ horizontal routing KINEMATIC ⇒ a pin-less RL env cannot represent the task). **For the current MuJoCo cell that premise is superseded (§4 (i), Rs1 2026-09-14): the cell carries a second bend DOF, and whether it can hold routing curvature dynamically under drag is unmeasured.** The pin's engineering justification for the current cell is therefore **pending re-derivation**; until it lands, the pin stands on Rs's rulings alone (`:27`, `:28`), which are unchanged. The 2026-06-25 derivation is retained above as the justification for the build it described.
- **d-2（新前提からの再導出）は今は書けない**（未測・probe は認可事項・当卓は要求しない）。**d-3（変更なし）は書けない**（現行 cell は 2 hinge = 測定済 F2）。
- ⛔ **§0 は Rs1 の court** — 本節は提案。

## 4. (c) `:31` の citation 修理（v1 §9 のまま・内容で指す）

- **現行** `:31`: 「…already explains the AR-routing QUARANTINE (**§4 `:62`**, B1 substrate-upgrade DECLINED)」（`:62` = TABLE_HEIGHT = stale）。
- **置換案（括弧内のみ）**: `(decision-of-record: 07-Design/00-DESIGN-STATUS-LEDGER.md, the RL-Routing-Design.md MIXED row — the sentence "its mechanism (spring-follow + kinematic hold) is fidelity-QUARANTINED"; B1 substrate-upgrade DECLINED for the 2026-06-25 Newton cell, see §4 (iii))`。内容 pin の一意性 = 出現 1（v1 §9-1 実測・本書で再確認）。**M8**: 同 LEDGER 行が辿る `LL-S1B-…md` は untracked（06-Knowledge 104 中 86 が untracked）— 本修理はその脆さを継ぐ（開示）。**L2**: `:31` の欠陥 = stale 行番号／`:69` 側の欠陥 = 複合 pointer の曖昧さ — 別種（(ii)(iv) 内で同じ内容 pin 形を使い 2 回直さない）。

## 5. 本書が触れないもの・限界

- ⛔ 04-Specs の編集（着地 = Rs1）／(a) を含む統合文言／build・probe・training／**`:29` の再導出に要る測定**（drag 下の曲率維持 = probe = 認可事項）／§6-7 の qpos 書込 census（v1・p0 の file・指摘のみ）。
- **L1**: 外部 3 文書（`SOMA.md:640`／`PIN_D_TRIGGER_CHARTER:287`／`PIN_DB_WINDOW_GATE_MATERIALS:385`）が同じ前提を stale 行番号で引く — 本書の置換で行がさらにずれる ⇒ 着地時に **各 owner が内容 pin へ**（当卓は触らない・登録 = p6）。
- **v1 §5-5**: `validate.sh` Layer 6 の cable guard（`check_cable_model_mislabel.sh`）は tracked 0 ⇒ 「guard が前提を機械検証している」とは書かない（本書も書いていない）。
- 現行 cell の定数は 2 群（v1 §5-2: cell/route 系 literal 0.02 vs steps 系 0.12 vs wired = 記号参照）— **(i) は live emitter（記号参照 = task_config 値）だけを述べ**、他 driver の literal は述べない。

## 6. gate 記録

- **[TASK] L=L3** | node = row 48 の register 行の下（p4 node `T-ROOT-Kinematic-Pin-Complete-Removal-20260719` の chain 外・Rs1 Q4 と同型で node 化しない読み = p6 の court）。
- **[L-TRIAGE] stage1**: `L_TRIAGE: {self_declared: L3, auto_escalated: L3, final: L3}` — step_1 file matches: **`04-Specs/RS71-System-Spec-SSOT.md`（提案先・本書は編集しない）**／step_2 keywords: `phase`? 0・`ik` 0・`gravity` 0・**§0 FOUNDATIONAL（invariant 5 の正当化行）に触れる提案 = 即 L3**／status READY_FOR_CHECK。
- **[DEFER-RECON]（H1・row 単位で照合）**: **#48** = 本件の register 行（Rs1 08-09 裁定・Q5-Q7 の答え欄 = 予約中 @ `358a1d72ad`〜HEAD・本書の着地 = row 48 を閉じる事象 = Rs1 の文言着地・kickoff `:1416`）⇒ **本 chunk を gate するが、Rs1 の Q5/Q6 が premise 側の disposition を与えた**（着地は Rs1）／**#66** = wired run 規則（本書 run 0）／**#69** = 認可 run（無関係・cap は `:1416`）／**#71** = node 化境界（p6・Rs1）／**#72** = 09-07 WIP（RS71 の working tree も dirty = 本書は blob で読む）／#2・#4・#12 = pin 削除 directive 波及（07-21 裁定で pin 例外復活 = 本書 §3 の認可不変と整合）。FOUNDATIONAL 未解決で塞ぐ行 = 0。
- **層4 prior-art guard（H2・本 turn）**: `scripts/check_thread_vault_prior_art.sh --fail-on-blocker --max-findings 1000 "substrate-upgrade" "world-Z" "cable-fidelity" "horizontal routing"` = **rc=2・findings 33・blockers 15**（RS71 `:29/:31`・LEDGER row 48/49/72・kickoff Q5 節・当卓 handoff）= **全て本件自身の prior art**（同じ失敗経路の再試行ではない）⇒ **新 directive = Rs1 Q5-Q7（09-14）** の下で進む（guard の指定形）。
- **[VERIFY] 5 体（事前）**: cycle 1 = FAIL @ `0a13b2053a`／**cycle 2 = 本 v2 に対し CC2-CC5 ＋ CC6 → §9**（上限 2・FAIL なら REVIEW = p4/Rs1）。**Step 8**（verification-log 永続化）= cycle 2 の後に `scripts/verification_log_build_input.py` 経路で実施（v1 で未了と明記した項目）。
- **層2 事後／層5**: 着地は Rs1 ⇒ 当卓の事後 = bank 後に blob を再読（§9）。

## 7. Rs1 へ上げる形（p4 経由・本書の受入条件）

1. **(i)-(iv) の文言**（§2）と **`:29` の置換文**（§3）と **`:31` の 1 行修理**（§4）を **着地候補**として上げる（cycle 2 の DECIDE が PASS のとき。FAIL のときは REVIEW = 第 3 cycle の可否を p4 へ）。
2. Rs1 に要る一言 = **着地**（04-Specs は Rs1 のみ）。着地時に row 48 が閉じる（cap `:1416`）・p6 が L1 の 3 文書の owner へ内容 pin を回付。
3. **問いは残さない**（Q5/Q6 で閉じた）。**未測 1 件**（drag 下の曲率維持）は §3 の「pending re-derivation」として文言に内包・probe の起票は別（認可事項）。

## 8. cycle-1 項目の処置（全受入・どこに反映したか）

| # | 内容 | v2 |
|---|---|---|
| C1 | `bf0235cfd8` = unauthorised sample の未開示 | F7 で開示・日付の根拠にのみ使用・採用は Q5 に立つ |
| C2 | dead code `ur15_cell.py` への pin | F2/F9 = live emitter `ur15_steps_wired.py` @ `22feba17a6` に再 pin |
| C3 | B1-declined の保存 | §2 (iii) に逐語・日付・環境付きで保存（Rs1 Q5 の要件と同じ）・§4 で `:31` 側も保存 |
| H1 | DEFER-RECON record 無し | §6 |
| H2 | prior-art guard 未実行 | §6（rc=2・処置つき） |
| H3 | Newton rod の DOF 記述が不正確 | F5 = installed 1.5.1 の docstring 逐語・版を付ける |
| H4 | 定数の空欄 | F3 = 0.3333 N·m/rad ほか実値 |
| H5 | currency の断定 | F4/F9 = rev 付き・「is at present」は `22feba17a6` に anchor |
| H6 | 選択段の Rs1 承認未引用 | §2 (ii)「descriptive, not a new authorization・pending Rs1 sign-off」 |
| M1 | z-hinge 軸の合成 | §2 (i) の限定句 |
| M2 | d-1 の hedge の scope | §0（F2b は Q5 の限定で閉じた）・§3 |
| M3 | `grep -c` を「occurrences」と呼んだ | 本書は行数と出現数を区別（F2） |
| M4/M5 | 年代 caveat の片側・06-26 pivot 欠落 | F8・§2 (iii) |
| M6 | 「Invariant 5 is unchanged」の見出し | §3 = 認可不変／正当化は再導出待ち を分ける |
| M7 | OPTIONS+ESCALATION を compliance 根拠に | 選択肢を置かない（§0）・根拠 = Rs1 の Q5/Q6 |
| M8 | 新引用先が untracked | §4 で開示 |
| L1 | 外部 3 文書の stale 行 | §5 |
| L2 | pointer 欠陥 2 種 | §4 |
| v1 §「次」5 | Step 8 未了 | §6（cycle 2 後に実施） |

## 9. cycle 2 の結果（append-only）
- （5 体の帰還後に追記）
