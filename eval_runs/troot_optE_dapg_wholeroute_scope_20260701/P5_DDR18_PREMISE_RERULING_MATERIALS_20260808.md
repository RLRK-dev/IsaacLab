# DDR #18 前提再裁定 — 判断材料（p5 作成・2026-08-08 10:00 JST）

**地位**: 本 doc は **判断材料のみ**。裁定は Rs 専権（`prohibited.md` 方針変更禁止・LEDGER row 18 close 条件）。作成 = p5 SKILL-DETAIL-DESIGN（#18 の設計 lane 当事者）。**依頼 = Rs 直接指示 2026-08-08**（「#18 前提再裁定の材料をまとめて」）。
**接地**: 全 pin は as-read 2026-08-08 09:5x–10:00。moving file は commit 併記。LEDGER = `4856da33ca`（row 18 全文実読）・row 25 `:129`・row 38 `:142`・charter = `charter_v231.md`（tracked）実読・(d) design doc `:211` 実読。

---

## §1 #18 とは（現在の登録簿の姿）

`00-DESIGN-STATUS-LEDGER.md:122` @ `4856da33ca`・**FOUNDATIONAL**:
- **item** = grip-efficacy SRG @ 4-substep（NEW blocker）。**GATES (d-b)** 〔#18→(d-b)→training-ready〕— つまり **training 開始の前提連鎖の一部**。
- **機構（確定済・L3 5/5 airtight）**: M2 = drive-dependent cable displacement CONFIRMED — 同一 target pose で FF は右指先 6.3mm 把持・ik_chord は 22mm 未把持（右腕 4.324rad **別 IK branch**）→ cable ~16mm 変位 → 左単腕保持 → drop@267。M1（IK iters 不足）= REFUTED（ik_resid 0.24mm 両 drive）。
- **L3 verdict = FAIL-revise（abandon ではない）**: 残 gap = ①branch/flip guard 欠落 ③route coverage ~40%（C2_REGRASP @~step500 = fresh 右腕 branch 選択 = 最高 risk 未測）。②necessity は analysis で discharge 済（**pin は seat 時発火・slip は seat 前 ⇒ pin は drop を rescue できない** = pin 有無は #18 の必要性を変えない）。
- **p5 改訂 v2.2** = 上記 ①③ に対応する設計・**design-side READY・2026-07-19 02:35 dispatch 済**（`HANDOFF_p5_vtdesign.md:132` @ `3cd13da681`）。
- **status** = IN-RESOLUTION（⛔execution HOLD — [CHANGE]/probe fenced）＋ 2026-08-08 状態句訂正（待ち = 本再裁定）。

## §2 supersede された前提（何が、何によって）

| # | 旧前提 | supersede した decision | custody |
|---|---|---|---|
| P1 | 「#18 impl を**現 kinematic 基盤**で land」（R-SEQ） | Rs 絶対指示 kinematic 完全削除（07-19）⇒ **superseded 確定**・R-SEQ §7 = WITHDRAWN（c5 17:16） | row 18 末尾 verbatim |
| P2 | 順序「#18 **先行**」 | **#18-last**（pN 裁定 2026-07-20 10:13） | row (d) `:60`（⚠「(d)」名の行は 2 本・`:129` と混同注意） |
| P3 | （07-19 の）「pin 含む完全削除」 | **Rs 裁定 B（07-21）= clip-retention pin 例外 復活**（clip 側がケーブルを保持する機構のみ・gripper 把持ではない） | row 25 `:129` の 07-21 注記・`CLAUDE.md` §0#5 |
| P4 | 駆動基盤 = kinematic arm drive（#18 の機構 M-b2 = その **warm-start branch 選択**） | **PD-arm charter**（Rs 承認 07-26・`probe/pd1-arm-pd` 実装済）: t=0 = vendor keyframe のみ・runtime arm joint_q/qd 書込 **全廃**・全姿勢変化 = **PD 物理過程**・reset re-pose 3 site 削除（reset-init 例外 = 失効） | `charter_v231.md:351-352/:360-361`（tracked・実読） |
| P5 | robot = UR5e cell（#18 の全測定の土台） | **UR15 ×2 + Robotiq 2F-85 へ premise 変更**（07-27 Rs 訂正） | DDR #38 `:142`（status = PENDING・Rs 専権） |
| P6 | substrate 健全性 | **DDR #26 隠れ綱引き**（imported arm actuator 12 本・ctrl≡0 飽和 torque・kinematic 上書きが隠蔽）= **全 banked evidence 共通の caveat**。L-P0 感度測定は**測定済 banked**（`e5d2dc214a`）・継続利用可否は Rs 判断待ち | DDR #26 `:130` |

**要点**: P4 により **#18 の根本機構（ik_chord warm-start の branch 選択）は、機構ごと消える**。v2.2 の fix（A1 branch/flip guard 等）は kinematic drive 内の設計であり、**PD 基盤にはその surface が存在しない**。逆順条件として (d) design doc `:211` が既に明文化: 「**#18 の全 evidence を PD 基盤で取り直すこと（現 evidence の substrate が変わるため）**」。

## §3 生きている決定（本再裁定で触らなくてよいもの）

- **GO-now evidence package = pN PASS-CLOSE（07-18 19:03・再 sim 不要）**: M1 necessity CLOSE・M3 B5a CLOSE・three-state INCONCLUSIVE accepted。
- **substrate-gap（fork-B golden 非再現）= UNPROVEN・ACCEPT-AND-CLOSE**（reopen 条件 3 つ明記済）。**DDR foundational row 追加なし**は p6/Rs custody 決定済。
- **training authority 不変**（#18 の disposition と独立に CLOSED のまま）。
- **#18-last の順序**は pN 裁定として現行（Rs はいつでも上書き可 — 触るなら Q3）。

## §4 evidence 目録と等級

| artifact（eval_runs/troot_optE_…/） | git | 確立したもの |
|---|---|---|
| GRIP_SUBSTEP_L3_DEBATE_VERDICT_…0718 | tracked | substep 4→10 は fix でない（REFUTED） |
| IKCHORD_GRIPSLIP_DIAGNOSTIC_RESULT_…0718 | tracked | M2 CONFIRMED / M1 REFUTED |
| IKCHORD_GRIPSLIP_FIX_L3_PROPOSE / _VERDICT …0718 | tracked | lever 方向 sound・as-specified FAIL-revise（gap ①③） |
| IKCHORD_GRIPSLIP_GONOW_PREREG / _EVIDENCE_RESULT …0718 | tracked | B4-shadow・B5a・pN PASS-CLOSE |
| **IKCHORD_GRIPSLIP_FORCEDESIGN_VTDESIGN_…0718（v2.2 設計本体）** | ⚠ **UNTRACKED / 0-commit** | A1/A2/A3 改訂設計（§10.10-10.12） |
| IKCHORD_GRIPSLIP_FORCEDESIGN_ESCALATION_…0718 | ⚠ **UNTRACKED** | escalation 記録 |

- **全 evidence は kinematic 基盤 ＋ UR5e cell 上の測定** ⇒ P4・P5・P6 の 3 重 caveat が乗る。
- ⚠ **設計本体 v2.2 が唯一 0-commit** — disposition が何であれ、**歴史 record として bank するか消えるに任せるか**は決め所（昨夜の実測: untracked file は消えても無記録）。
- **基盤が変わっても残る設計知見**（v2.2 から継承価値のあるもの）: (i) 「右腕接触喪失 → 左単腕 → 高速横 escape」という failure class と、joint-delta ∧ EE-vs-chord ∧ cable-motion の **3 量相関 discriminator**（1 量は confound）(ii) IK の**離散 branch/basin 選択**という自由度の存在（PD でも DiffIK target 生成側に残る概念）(iii) coverage 教訓 = **C2_REGRASP（fresh branch 選択点）が最高 risk**。

## §5 Rs が決める問い（options ＋ 帰結）

**Q1. row 18 の存続形**
- (a) **再定義 = 「PD 基盤での grip-efficacy 実測」として succession**（row 継続・FOUNDATIONAL 維持・GATES (d-b) 連鎖保存・旧機構 M-b2 は「kinematic 固有・基盤ごと消滅」と注記）
- (b) CLOSED-as-superseded ＋ 新 row 起票（実質 (a) と同等だが provenance が切れる）
- (c) 現状維持（HOLD のまま保留継続）
- p5 所見: **(a) が gate 連鎖と provenance を切らない**（NEST の「DISCARDED→復活禁止・復活は新 node + provenance」規則とも整合し、(b) はその手間を増やすだけ）。
**Q2. 旧 evidence の disposition**
- (a) **#26 と同型の表現**（「直ちに無効とはしない・継続利用可否は L-P0 判断と一括」— Rs 自身の precedent）
- (b) 一括 TRACE/歴史 grade へ格下げ（PD 基盤で全数取り直しが §2 P4 で確定しているため、実務差は小）
- (c) 設計知見（§4 末尾 3 点）のみ明示継承・数値は全て無効
**Q3. 順序** — #18-last（pN 07-20）を維持するか。前提: **(d) arc 自体が Rs PLAN_STATUS review で HOLD**（row `:60` ①-⑤: records fix / status 分離 / B1・B2 owner 確定 / L-P0 REQUIRED / PASS@4⇒@10）。⇒ #18 の位置は **gate chain 再構成の中で** (d) P-D1 の後に確定するのが自然（維持 = 現行どおり）。
**Q4. 新 DoD の骨格**（数値設計は再定義後に p5 が導出 — ここでは決めない）: 旧 DoD「ik_chord が FF に match」は**両 drive とも消滅**。候補骨格 = PD closed-loop で **grip 保持のまま C1 seat（g3）到達**・**C2_REGRASP を含む** coverage・視覚レグ必須（numeric 単独 PASS 禁止）。
**Q5. lane 境界の確認** — row 18 owner = `p5/force-design`。ただし新枠組みでは **PD 駆動の性質（p11 = arm-control 設計 owner）**に測定が依存。提案分担: **測定系・DoD 設計 = p5 ／ PD 駆動側前提の供給 = p11 ／ 実測・実装 = lead lane**（Rs 確定要）。

## §6 連鎖の全体像（1 行）

**Rs 本再裁定（Q1-Q5）→ gate chain 再構成 → (d) P-D1 probe（HOLD 解除条件 ①-⑤）→ PD 基盤 evidence 取り直し → #18 re-debate → impl（Rs sign-off）→ (d-b) → training-ready。**

## §7 sources（全て実読・as-read 2026-08-08 09:5x-10:00）

- `thread_isaac_lab/thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md` @ `4856da33ca` — row 18 `:122`（全文）・row 25 `:129`・row (d) `:60`・row 38 `:142`・row 26 `:130`
- `eval_runs/…/P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/charter_v231.md:351-352/:360-361`（tracked）
- `eval_runs/…/ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md:211`（⚠共有 tree で dirty — 引用行のみ）
- `thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_p5_vtdesign.md:132` @ `88e778acdf`（v2.2 dispatch 記録）＋ §30-31（row 18 訂正 arc）
- `CLAUDE.md` §0#5（pin 例外 custody）・DiffIK 節（PD charter Rs 承認 07-26）
- ⚠ 行番号は **untracked/伸長 file では引くたび再解決**（本 doc の LEDGER pin は commit 併記で恒久化）
