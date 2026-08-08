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
| **IKCHORD_GRIPSLIP_FORCEDESIGN_VTDESIGN_…0718（v2.2 設計本体）** | ⚠ ~~UNTRACKED / 0-commit~~ **→ banked `e9a5cc7f3c`（10:05・custody not validity）** | A1/A2/A3 改訂設計（§10.10-10.12） |
| IKCHORD_GRIPSLIP_FORCEDESIGN_ESCALATION_…0718 | ⚠ ~~UNTRACKED~~ **→ banked `e9a5cc7f3c`（同上）** | escalation 記録 |

- **全 evidence は kinematic 基盤 ＋ UR5e cell 上の測定** ⇒ P4・P5・P6 の 3 重 caveat が乗る。
- ~~⚠ **設計本体 v2.2 が唯一 0-commit** — disposition が何であれ、**歴史 record として bank するか消えるに任せるか**は決め所~~〔✅ **discharged 10:05** — 両 file とも `e9a5cc7f3c` で bank（owner 判断 = p5・commit message に custody-not-validity 明記）。本 bullet は 10:00 時点の記述〕。
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
**Q3. 順序** — #18-last（pN 07-20）を維持するか。前提: **(d) arc 自体が Rs PLAN_STATUS review で HOLD**（row `:60` ①-⑤: records fix / status 分離 / B1・B2 owner 確定 / L-P0 REQUIRED / PASS@4⇒@10）〔⛔ **訂正 2026-08-08 10:35（§9）: この ①-⑤ 列挙は stale だった** — 同じ row の後段で **①③④ は 07-19 中に解消**（v1.4 `e32c75c3a4` = B1 裁定＋L-P0 REQUIRED 昇格 → P-D1 prereg 凍結 → **P-D1 evidence 完了 bank `e5d2dc214a`**・video leg 13:44 納品済）。行の途中で読みを止めた読み〕。⇒ #18 の位置は **gate chain 再構成の中で** (d) P-D1 の後に確定するのが自然（維持 = 現行どおり）。
**Q4. 新 DoD の骨格**（数値設計は再定義後に p5 が導出 — ここでは決めない）: 旧 DoD「ik_chord が FF に match」は**両 drive とも消滅**。候補骨格 = PD closed-loop で **grip 保持のまま C1 seat（g3）到達**・**C2_REGRASP を含む** coverage・視覚レグ必須（numeric 単独 PASS 禁止）。
**Q5. lane 境界の確認** — row 18 owner = `p5/force-design`。ただし新枠組みでは **PD 駆動の性質（p11 = arm-control 設計 owner）**に測定が依存。提案分担: **測定系・DoD 設計 = p5 ／ PD 駆動側前提の供給 = p11 ／ 実測・実装 = lead lane**（Rs 確定要）。

## §6 連鎖の全体像（1 行）

**Rs 本再裁定（Q1-Q5）→ gate chain 再構成 → (d) P-D1 probe（HOLD 解除条件 ①-⑤）→ PD 基盤 evidence 取り直し → #18 re-debate → impl（Rs sign-off）→ (d-b) → training-ready。**〔⛔ **訂正 2026-08-08 10:35（§9）**: 「P-D1 probe（HOLD 解除条件 ①-⑤）」は stale — **P-D1 は 07-19 に走行済・evidence banked `e5d2dc214a`**。残る鎖 = **gate chain 再構成 ＋ UR15 基盤での再取得**。〕

## §7 sources（全て実読・as-read 2026-08-08 09:5x-10:00）

- `thread_isaac_lab/thread-vault/07-Design/00-DESIGN-STATUS-LEDGER.md` @ `4856da33ca` — row 18 `:122`（全文）・row 25 `:129`・row (d) `:60`・row 38 `:142`・row 26 `:130`
- `eval_runs/…/P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/charter_v231.md:351-352/:360-361`（tracked）
- `eval_runs/…/ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md:211`（⚠共有 tree で dirty — 引用行のみ）
- `thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_p5_vtdesign.md:132` @ `88e778acdf`（v2.2 dispatch 記録）＋ §30-31（row 18 訂正 arc）
- `CLAUDE.md` §0#5（pin 例外 custody）・DiffIK 節（PD charter Rs 承認 07-26）
- ⚠ 行番号は **untracked/伸長 file では引くたび再解決**（本 doc の LEDGER pin は commit 併記で恒久化）

---

## §8 裁定記録（2026-08-08 10:09 JST 受領・first-hand）

**Rs 発話（p5 session 直接・verbatim）**: 「**Q1-Q5 は所見どおりで良い**」（2026-08-08 10:0x・本 doc §5 への応答）。

**resolution（各 Q が何に確定したか）**:
| Q | 確定内容 | 等級 |
|---|---|---|
| Q1 | **(a) succession 再定義** — row 18 を「**PD 基盤での grip-efficacy 実測**」として継続（FOUNDATIONAL 維持・GATES (d-b) 連鎖保存・旧機構 M-b2 は kinematic 固有ゆえ基盤ごと消滅、と注記） | 所見 = 明示 (a) ⇒ 直接確定 |
| Q2 | **(a) #26 と同型の表現** — 旧 evidence は「直ちに無効とはしない・継続利用可否は L-P0 判断と一括」 | ⚠ **§5 Q2 には所見 marker が無かった** ⇒ (a)（precedent 併記の第 1 案）への解決は **p5 の resolution（inference・loud）**。Rs は無費用で flip 可（§5 記載どおり実務差 = 小） |
| Q3 | **#18-last 維持**（gate chain 再構成の中で (d) P-D1 の後に位置確定） | 所見 = 明示 ⇒ 直接確定 |
| Q4 | **DoD 骨格 採用**: PD closed-loop で **grip 保持のまま g3（C1 seat）到達**・**C2_REGRASP を含む coverage**・**視覚レグ必須**（numeric 単独 PASS 禁止）。数値設計は再定義後に p5 が導出 | 候補骨格 = 唯一提示 ⇒ 採用 |
| Q5 | **lane 確定**: 測定系・DoD 設計 = **p5** ／ PD 駆動側前提の供給 = **p11** ／ 実測・実装 = **lead lane** | 提案 = 明示 ⇒ 直接確定 |

**本裁定が決めて *いない* こと（over-read 防止）**:
- ⛔ **execution HOLD の解除は含まれない** — Q3 採用により #18 の実行位置は「(d) P-D1（現在 probe HOLD・Rs review ①-⑤）→ gate chain 再構成」の**後**のまま。[CHANGE]/probe fence は継続。
- ⛔ **DoD の数値**は未設計（Q4 は骨格のみ）。導出は succession row の commission 後・かつ **(d) の B1/B2（actuator disposition）確定が入力に要る**（PD 駆動の性質に依存するため）。
- 旧 evidence の最終 disposition は **L-P0 判断（Rs）と一括**のまま（Q2 (a) の中身そのもの）。

**反映経路**: 本 §8 bank（p18）→ p18 が p6 へ回付 → p6 が row 18 へ着地（succession 再定義 note・「待ち = Rs 再裁定」の discharge・close 条件更新は p6/Rs 側）。07-Design は p5 read-only ゆえ直接編集しない。

## §9 B1/B2 確定状況（Rs 照会 2026-08-08 10:31:11 JST〔⛔当初 header は「10:30」= 未実測の丸め・p18 first-hand 訂正 `m-p18-73`〕への回答・as-read 10:31-10:35）

**結論: B1/B2（imported actuator disposition）は 2026-07-19 に裁定済み・同日 実証済み。**
- **裁定** = design **v1.4** `e32c75c3a4`（版表 `:14`・row `:60`）: **B1（strip-at-import）= PRIMARY**（Rs 推奨に concur）／ **B2（inert 零化 nu=28）= strip 不可時の fallback のみ**（動的 force≡0 試験 REQUIRED）。⚠当時の probe 実装は B2 形 → B1 再実装要、と同 note に記録。
- **実証** = P-D1 prereg v1.2 凍結（`32617b119a`・**Rs canonical R0-R4 matrix**・R1 = **B1-clean** 走行）→ **evidence 完了 bank `e5d2dc214a`**・video leg 13:44 Rs 納品。結果 = **R1（clean）全滅** ⇒ choreography-blocked・re-sequencing = Rs surface（= L-P0 evidence・DDR #26 の「L-P0 測定済」と同一物）。
- **残り（bounded）**: (a) review v4 の「B2 STOP-gate 化」の最終 fold — 現 doc（v2.30 `031ca0dc95`・⚠worktree dirty as-read）に文字列 `STOP-gate` は **0 hit**（⛔この query での不在まで・改名の可能性は排除できない — 確定は版表 40+ 行の実読要）。(b) ⭐ **UR15 premise 変更（#38・07-27）後の適用** — nu=16/28 は `ur5e.xml` の数。**UR15 cell における余剰 actuator の有無・strip 対象は別 model の再測定**（推測・ラベル付き — B1 の*原則*は生きる）。
- ⛔ **本 doc 自身の訂正 2 件を claim 位置に埋込**（§5 Q3・§6）: 「(d) HOLD ①-⑤」「P-D1 probe HOLD」は**行の途中で読みを止めた stale read**だった — ①③④ は 07-19 中に解消・P-D1 は走行済。⇒ **p5 の DoD 設計の前提は「B1/B2 の choice 待ち」ではなく「commission ＋ UR15 基盤での B1 適用確認」に更新**。

## §10 UR15 基盤での B1 適用確認（Rs 照会 2026-08-08 10:38 台への回答・as-read 10:39-10:41）

**結論: UR15 基盤（p4_ur15_sim_20260727 driver 系列）では B1 は *構造的に* 満たされている — ただし「strip 機構が在る」のではなく「持ち込む物が無い」による（vacuous satisfaction）。**

**実測（全て on-disk・run 不要）**:
1. **arm source = actuator 0 個**: `ur15_base.xml` / `ur15_base_mirrored.xml`（両方 tracked）— actuator 要素 **0**・include **0**。⇒ ur5e で綱引きを起こした「vendor `<actuator>` block が model と一緒に乗る」経路に、**乗る物が存在しない**。
2. **gripper source = 意図された 1 個/側のみ**: `_ur15_2f85_koshape_actuated.xml` の `<general>` 2 件のうち **:25 は `<default class="2f85">` 内の defaults 記入（instance でない）**・実 actuator は **`fingers_actuator` 1 個**（:198・tendon「split」）。
3. **arm servo 12 本は composer が明示生成**: `ur15_steps_wired.py:308-315` — `J6`×2 側、`{L,R}_{joint}_act`、PD affine（gain kp / bias −kp, −kp·KVR・wrist/arm で kp 別）、**forcerange = ±EFFORT・ctrllimited=1**。
4. **合計 nu = 12 + 2 = 14 が runtime で成立**: run log 実測 `[steps] … nu=14`（07-27 08:50 / 10:41 / t43 trace 07-29 ほか複数・nq は cable 構成で 97/113 と動くが **nu=14 は不変**）。
5. **全 14 本が駆動される**: `:678-683` — arm slot に qarm・gripper slot に ctrl_g。**ctrl≡0 で放置される actuator は無い**（ur5e の綱引き条件 = 「undriven なのに存在」が成立しない）。

**⛔ 等級と残る穴（2 点・loud）**:
- **(a) B1 は「機構」としては未実装**: attach 経路（`attach_body`）は **source に actuator が在れば黙って持ち込む**（gripper の `{tag}g_fingers_actuator` が prefix 付きで来ている事実がその証明）。今日の充足は **source file の中身**に依存しており、`ur15_base*.xml` を actuator 付き vendor MJCF に差し替えると **ur5e の失敗機構がそのまま再現**する。driver に **nu==14 の assert は無い**（`:351` は print のみ・`AN.index()` は不足で落ちるが**余剰は素通し**）。⇒ 将来 guard 候補（提案であって実装ではない — §運用24）。
- **(b) scope 限定**: 確認したのは **p4_ur15_sim_20260727 の driver 系列**（現行 UR15 実行系・log 実測 07-27〜07-29）。別の UR15 loader が生まれた場合は別途。

**⇒ p5 の DoD 設計前提への帰結**: 「UR15 基盤での B1 適用確認」は **本 § で discharge**（構造的充足＋(a) の穴の明示まで）。残る前提 = **commission のみ**。
