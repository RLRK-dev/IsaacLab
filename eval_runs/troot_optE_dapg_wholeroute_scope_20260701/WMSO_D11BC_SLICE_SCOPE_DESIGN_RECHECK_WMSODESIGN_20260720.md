# WMSO D1.1-B/C/slice — scope prereg 設計軸 re-check（pS / MWSO-DESIGN）

- node: `T-WMSO`; 検証者 = w2:pS (MWSO-DESIGN); 記録 = **2026-07-20 09:22 JST（実測 date-THEN-write）**
- 依頼元 = w2:pQ (RS-TECH-LEAD2)、dispatch 2026-07-20 09:11 JST（Rs 着手指示 08:42 頃受領 → scope prereg v1 + DEFER-RECON bank 後の §5 gate 順 pS レグ）
- gate 位置 = prereg v3.2.2 §9 継承の工程順「scope prereg → **pS design re-check** → pN SCOPE CONCUR」の**第 1 ゲート**（D1.1-B DESIGN doc はまだ存在しない — §9 の後段 step。本 re-check の対象 = **scope preregistration 自体の設計軸**）
- 0-commit: 本 record は pS 著作の verify artifact。bank(commit) = pQ/p6。

## 0. 検証対象 pin（HEAD `7fc04d1baa` で committed blob 独立検証・worktree == committed）

| artifact | content-sha256 | 検証 |
|---|---|---|
| `WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md` | `87f348540c93f0f2fe709251f09ce46fb741970b8b50fb609c32b99f9f4cca04` | ✅ committed==worktree==pQ 主張 |
| `WMSO_D11BC_SLICE_DEFER_RECON_RSTECHLEAD2_20260720.md` | `ff414b09fbe4cca064aaf438be4be38fa65bf7aa617892afb4694f5789ce5ccb` | ✅ committed==worktree==pQ 主張 |
| HEAD | `7fc04d1baa34bffa23043656bd846974e6b39699` | ✅ = pQ 主張・parent `65d62d15ed` (D1.1-A FROZEN+CUSTODY-CLOSED) |

## 1. 接地した統治ソース（anchor set — §運用4）

- **LEDGER row44**（成否 SSOT、`00-DESIGN-STATUS-LEDGER.md:44`）: `✅D1.1-A FROZEN`（Rs「freeze + push」2026-07-20）・freeze record `593880be6ef9` @ `9a13035626`・frozen 3 pin(DESIGN `00192d20ca00`/EP v1.9/JSON v1.9)・**register⑩ CONFIRMED**・**次 = D1.1-B/C/slice（Rs 指示待ち・self-start なし）**。
- **freeze record**（`WMSO_D11A_FREEZE_RECORD_20260720.md`、committed blob sha `593880be6ef92059…` = LEDGER 引用と独立一致）: §2 frozen pins・§4 境界(impl/gate-1/training/production/closed-loop CLOSED)・§5 後続順序(B→C→slice、着手=Rs 指示・self-start なし)。
- **pN freeze consultation (3)**（`WMSO_PN_FREEZE_CONSULTATION_TRANSCRIPT_20260719.md`、AUTHOR-CONFIRMED）: 次順序 A.D1.1-B→B.D1.1-C→C.slice + B/C/slice 要件逐語。
- **prereg v3.2.2**（`WMSO_D11_CONTRACT_V2_SCOPE_PREREG_RSTECHLEAD2_20260719.md`、committed sha `71097e58102e…` = LEDGER 一致）: §2 OUT(B/C banked 定義)・§9 gate 順。
- **frozen JSON v1.9**（`WMSO_EvidencePolicy_v1.9.json`、sha `e63176af9bc3…` = frozen、worktree==committed intact）。

## 2. 先祖返り（regression）検査 = **NONE**

| 検査軸 | 判定 | 根拠 |
|---|---|---|
| 着手順序の再順序化 | なし | prereg §1.1「B→C→slice」= pN (3) 逐語「A.D1.1-B→B.D1.1-C→C.slice」= freeze §5。三者一致。 |
| DISCARDED/ABANDONED 復活 | なし | recon §2 row7 = §FAILED/ABANDONED(S1B / env6 VBD-AC) 非該当。WMSO = mujoco-コ 上の高位契約層、env6 VBD / S1B substrate に触れない。 |
| frozen v2.11.2 の暗黙編集 | なし（保護済） | prereg §1.3 = schema delta は supersession 記録 + Rs review 経由（§10 kinematic 写像(c) と同経路）。§2-4 = EP 本文変更は EP 新版(frozen v1.9 不変)。「黙って編集しない」明記。 |
| register⑩ の逸脱 | なし | prereg §4/§6 = METHOD_REGISTRY(**data-row 拡張**)で低位学習法を許容、enum 拡張でない。freeze §1(b) の Rs CONFIRMED 範囲(method registry 化 + DAPG/DEMO_PLUS_RL 再収容)と整合。「lineage 表は実在限定」原則を carry。 |

## 3. 先走り（running ahead）検査 = **NONE**

| 検査軸 | 判定 | 根拠 |
|---|---|---|
| impl/training/authority | CLOSED 維持 | prereg §1.4 = freeze §4 逐語(別 gate + kinematic 全廃 HALT 解消が前提)。§2 OUT に impl 明記。§4 slice run レグ = impl 解錠 + clean substrate + [HIGH-COST-GATE]/production-launch-gate + Rs 実行承認に gated。 |
| C/slice scope の先取り確定 | なし | prereg §1.2 = C/slice は **banked outline**、着手時に各自 詳細 prereg(§9 loop 再適用)。本 prereg の詳細 scope は **B のみ**(§2)。 |
| gate 順の逸脱 | なし | prereg §5 = v3.2.2 §9 の design 部分を忠実再現、impl 部分(pre-check→rule-check→impl→IMPL PASS-CLOSE)を **CLOSED として fence**。fail-closed re-verify loop + lanes(dev=pQ/design=pS/evidence=pN/custody=p6) 一致。 |
| 新 file/gate/CLI の無認可追加 | なし | 認可済み D1.1-B/C/slice sequence(Rs 08:42 指示)内の設計書面。 |
| FOUNDATIONAL DDR item への premise 依存 | なし（設計 chunk） | §4 参照。 |

## 4. DEFER-RECON 評価 = **CONCUR（PASS）**

- **rule (h)（完全性）**: DDR = `LEDGER:85-110` = item **1-26（gap なし・max=26）**。recon §2 の enumeration(group1 {1,3,5-11,13-17,20-24}=19 + {2,4,12,18,19,25,26}=7 = 26)が **全 26 項被覆**。独立確認 = 私の on-disk 列挙で一致。
- **FOUNDATIONAL 依存判定の健全性**: FOUNDATIONAL = #2/#4/#12/#18/#19/#26。全て kinematic-removal rework / pin 削除 / grip-efficacy / multi-world training = **sim/run/training を gate** する項。WMSO D1.1-B/C = **型・契約を書く設計 chunk（sim を走らせない・train しない・slice を実行しない）** ゆえ、その premise(frozen v2.11.2 契約 + Rs 指示)は当該 run/train gate に非依存 = recon「非依存（設計 chunk）」判定は**妥当**。
  - control 契約の安定性: prereg §2 の control mode(LEARNED=DIFF_IK_EE_TARGET のみ)は **DiffIK-only = FOUNDATIONAL INVARIANT（rework 対象でない）**。kinematic-REMOVAL rework は substrate 実装(joint 駆動法)の話で、control 契約(DiffIK)でない → 設計 chunk の premise は安定。
  - #26（汚染 banked evidence）: recon「部分依存 → 拘束で処理(B/C design doc は旧 run 数値を正当化根拠に用いない)」= 設計 chunk が持ち得る subtle な premise 依存(汚染 run 数値の設計根拠化)を正しく塞ぐ。妥当。
  - #25（clean substrate）: 設計 非依存 / slice **run レグのみ依存** → prereg §4 実行前提に明記。妥当。

## 5. scope 完全性（under-scope 検査）= **GOOD（落とし 0）**

- **B scope §2 ⊇ v3.2.2 §2 OUT**: v3.2.2 §2 OUT(L95) TensorBindingSpec 逐語項(source offset/length・訓練時順序・normalization・scale/bias・bounds・quaternion convention・frame・history stack・sampling rate・action control mode)を prereg §2 が**全項被覆**。追加項(source field 参照・dtype/shape/unit・mask・belief/vision input・action scale・control mode 整合)は **pN (3) B 要件**由来。「逐語 ∪ pN (3)」帰属 = 正確(全項が 2 統治ソースのいずれかに trace)。
- **§2-4 frozen 土台内**: TENSOR_BINDING / CONTROL_MODE は frozen JSON v1.9 `claim_targets` の **13 ComponentKind に構造在籍**（proof_policy EXACT_TRAIN_TIME/HASH_BOUND_REPRODUCED・profiles OFFLINE_REPLAY にも）→ B は EP に component 追加不要 = frozen 土台内。DC-2 fold 済主張 = 独立確認 PASS。
- **C/slice §3/§4 ⊇ pN (3)**: §3(code/model/data/config/evaluator/EP/substrate_id exact-hash 結合 + substrate_id 必須 + silent pooling 禁止) / §4(APPROACH_CABLE→INSERT_INTO_CLIP・failure/no-chain・abstain/UNKNOWN・calibrated uncertainty・invalid handoff・stale epoch・recovery/stop・grasp/contact stability・deadline 計測必須 + PPO 非限定 + vision-belief/world model + boundary-only) = pN (3) 逐語忠実。

## 6. B DESIGN DRAFT へ carry する設計軸 CONDITION（scope prereg の欠陥でなく、次段 draft の遵守事項）

> いずれも prereg が既に内含(§1.3 / §2-7 / §6)。番人として loud に固定し draft 段で消失させない。

- **C-1（rule (g) — register⑩/METHOD_REGISTRY 境界）**: B/C design draft で低位学習法を追加する際、**method_id ROW(algorithm・例 SAC)の追加 = 認可済み data-row 拡張**だが、**新 TrainingMethodClass(enum) / 新 TrainingLineage の追加 = schema delta = Rs review 必須**（register⑩ の Rs-CONFIRMED surface に抵触）。draft は enum-vs-row 境界を明示すること。
- **C-2（U-3 drive-substrate lineage ∩ 進行中 kinematic-removal rework）**: §2-7/§6(c) の drive-substrate lineage field は、**進行中の kinematic 完全削除 rework(DDR #25/#26・Rs 絶対指示)と交差**。draft は現行(rework 前)の drive-substrate taxonomy を**前提に焼き込まない**こと。field が要ると判明したら schema delta として Rs review 経由、かつ **削除後の substrate 定義（再定義中）と整合**させる（stale substrate 前提の焼込み = 先祖返り隣接 risk）。

## 7. Verdict ⛔SUPERSEDED（2026-07-20 09:35 — 正 = §9）

> ⛔ 当初の「must-fix 0 PASS」は**誤り**。pN evidence-axis HOLD B1-B4（09:31:54）が supervene し、私は 4/4 を on-disk CONCUR（§9）。当初 verdict（下記・打消）を撤回する。訂正後 verdict = **⛔HOLD（prereg B1-B4 fold 待ち → pS 再 readback）**。

**~~設計軸 = ✅PASS（scope prereg v1・pin `87f348540c93`）~~**（SUPERSEDED → §9 HOLD）
- ~~先祖返り 0 / 先走り 0 / DEFER-RECON CONCUR(rule h 完全・FOUNDATIONAL 判定妥当) / scope 完全性 GOOD(落とし 0) / must-fix 0。~~（B1/B3 内部不整合・B2 Rs L0 mandate 未照合・B4 clean 条件 under-spec を見逃し = §9）
- carry = C-1 / C-2（B DESIGN DRAFT 段の遵守事項・prereg 内含の loud 固定）。
- ⚠**two-key**: 本 PASS = **設計軸のみ**。**pN SCOPE CONCUR（証拠/custody 軸）を代替しない**。gate §5 = pS PASS → pN SCOPE CONCUR の two-key。D1.1-A で pN が pS PASS を 4 回 supervene した pattern を継承。

## 8. Roadmap（番人 duty #3）+ 次の一手（duty #4）

**現在地**: D1.1-A `contracts_v2` = FROZEN/CUSTODY-CLOSED（不変土台）。D1.1-B/C/slice = Rs 着手指示済 → **scope prereg 段の第 1 ゲート(pS re-check) = 本 PASS**。

**Roadmap（gate §5 / freeze §5）**:
```
[今] scope prereg → pS re-check → pN SCOPE CONCUR  ⟨※ prereg B1-B4 fold 後に pS 再 readback 要 — §9⟩
  → D1.1-B DESIGN doc 着手(§2 IN 駆動・C-1/C-2 遵守) → 5体 CC Debate/pre-mortem
  → design 修正 → **pS final 設計軸 PASS**(B1 統一) → pN DESIGN PASS-CLOSE(exact-pin) → Rs freeze 判定
  → [C 着手時] D1.1-C 詳細 prereg → 同 loop
  → [slice 着手時] slice 詳細 prereg → 同 loop
  → slice RUN レグ = impl 解錠 + clean substrate(DDR #25/#26) + 実行 gate + Rs 承認（別 prereg）
```

**次の一手**:
1. **pQ**: 本 pS PASS を受け、**pN へ SCOPE CONCUR readback dispatch**（§9 gate 順）。C-1/C-2 は pN にも共有推奨。
2. pN SCOPE CONCUR 後、pQ が D1.1-B DESIGN doc 着手（frozen v2.11.2 土台・§2 IN 実装・C-1/C-2 遵守）。
3. **pS(私)**: ~~standby~~ → **§9 参照**（pN B1-B4 supervention・pQ の prereg revision 待ち → 再 readback）。self-start なし。

## 9. ⛔pN evidence-axis HOLD B1-B4 supervention — 4/4 CONCUR + own（2026-07-20 09:35 実測）

pN（w2:pN）dispatch 09:31:54: prereg `87f348540c93` evidence-axis = **HOLD B1-B4**（pQ へ逐語 dispatch 済）、私の must-fix 0 を supervene。**私は 4 項を on-disk 検証し 4/4 CONCUR。私の「must-fix 0 PASS」は誤り。** WMSO chain で pN が私の design-axis PASS を supervene した **5 度目**・うち **B1/B2/B3 は設計軸の欠陥**（evidence 軸限定でない = 私が設計軸を実際に見逃した）。

| # | pN finding | on-disk 検証 | 私の miss | 分類 |
|---|---|---|---|---|
| B1 | §2 Exit / §5 / pS roadmap の gate 順不一致 | §2 Exit(L42)「pS PASS→CC Debate→pN」vs §5(L64-67)「draft→CC Debate→修正→pN(**pS 段なし**)」= 内部不整合。私の §8 roadmap も pS-final-PASS 欠落。v3.2.2 §9 も pS 段を明記せず | **面間整合(role-lesson (a))未適用** — §2 Exit と §5 が食い違うのを通した | 設計軸 |
| B2 | slice acceptance に RL∧IL∧vision∧WM portfolio conjoin 無し・RL-only 誤通過可 | Rs L0 mandate verbatim「強化学習、模倣学習。ビジョン、ワールドモデルは必須」= conjunction。§4「RL-only 許容」を pN(3) 忠実として通したが **Rs standing mandate と未照合** | **mandate 照合 duty の失敗** | 設計軸(Rs mandate) |
| B3 | boundary-only/no-mid-skill と safe-checkpoint 切替が矛盾・今回 TERMINAL のみ | §4「boundary = skill 終端 / **安全 checkpoint** のみ」∧「mid-skill interruption なし」= 安全 checkpoint(mid-skill) が boundary-only と矛盾 | **内部矛盾を見逃し** | 設計軸 |
| B4 | F3 all-root guard `7803f58f17` で snapshot BODY3+scripts125=128・run clean = canonical Layer8=0 必須 | commit `7803f58f17`「Expand Layer 8 guard coverage」(09:23) 実在・LEDGER Layer8=128/BODY3/scripts125 一致。§4「clean substrate(DDR #25/#26)」= under-spec | **run-leg premise の精密条件(Layer8=0)欠落** | 精密化(run-leg) |

**disposition（pN 推奨に CONCUR）**:
- **prereg revision（pQ）**: B1 = gate 順を「draft → 5CC Debate → 修正 → **pS final 設計軸 PASS** → pN」に統一 + v3.2.2 delta を loud 化（§2 Exit/§5 全 surface 整合）。B2 = slice acceptance に **RL∧IL∧vision∧WM portfolio conjunction** を明記（RL-only 単独 pass 不可）。B3 = 本 slice boundary = **TERMINAL のみ**（安全 checkpoint = 別 gate）。B4 = slice run レグ clean 条件 = **canonical Layer8=0**（DDR #25/#26 完了の実測 gate）。
- **pS（私）**: prereg B1-B4 fold 後に **再 readback**（pN 明示依頼）。§8 roadmap は B1 に沿い pS-final-PASS を明記済（本 amend）。
- **own（恒久）**: role-lesson (a) 面間整合 + Rs mandate 照合を **scope-prereg re-check でも適用**する（今回は D1.1-A DESIGN doc 級の厳密さを scope 段で緩めた）。「私 PASS ≠ pN leg」= 5 度目の実証。

**訂正後 verdict = ⛔HOLD（B1-B4 CONCUR・prereg revision 待ち）**。→ §10（v1.1 fold readback）で解消。

## 10. prereg v1.1 fold readback — 設計軸検証（2026-07-20 09:41 実測）

pQ dispatch 09:36: pN SCOPE HOLD B1-B4（+N1 non-block）を prereg **v1.1** に fold・bank（HEAD `1da8503d2c`）→ pN 必要 chain（record-fix bank → **pS B1-B4 readback** → pN re-readback）の pS レグ + 私の §8 roadmap 旧 chain supersede 確認を依頼。

**検証対象 pin（committed blob @ HEAD `1da8503d2c`・独立確認）**:
| artifact | sha256 | 検証 |
|---|---|---|
| prereg v1.1 | `24af15733e4de34444a0bcc74ce8d31d71374bebb8b8c16cd9b4afe25720278a` | ✅ = pQ 主張 |
| pN HOLD transcript (`WMSO_PN_D11BC_SCOPE_HOLD_B1B4_TRANSCRIPT_20260720.md`) | `6944ee7c6b1f05473acf97ac8ec455ca7df157cbb17a37ad8391328757426178` | ✅ = pQ 主張・**custody leg CLOSED**(bank 済) |

**B1-B4 fold 忠実性（fold diff v1→v1.1 + transcript 逐語照合 — 4/4 faithful）**:
| # | v1.1 fold（diff 実測） | pN transcript 逐語(L13-16) | 判定 |
|---|---|---|---|
| B1 | §2 Exit + §5 とも「draft → 5CC → 修正 → **pS final-design PASS** → pN exact-pin PASS-CLOSE → Rs freeze」に一本化・§5 に v3.2.2 §9 明示 delta + 両軸再 verify 規則・**§8 旧 chain supersede** 明記 | 「単一 chain = draft→5体CC→修正→pS final-design PASS→pN exact-pin PASS・v3.2.2 明示 delta・全3面一致・双方再verify」 | ✅ 一致 |
| B2 | §4 に `portfolio_has_RL ∧ portfolio_has_IL ∧ vision_belief_live ∧ skill_dynamics_model_live`・1つでも false = L0/slice-success 不可・per-skill RL-only は IL leg 代替せず | 同 4-conjunct 逐語 | ✅ 一致・Rs L0 四手段(RL/IL/vision/WM)に厳密対応 |
| B3 | §4 boundary(runtime 選択点) = **TERMINAL outcome のみ**・CheckpointSpec 静的契約保持・途中切替 = Phase G・checkpoint-enabled 化 = chunk 改称+scope 再審査 | 同 逐語 | ✅ 一致 |
| B4 | §4 clean = **canonical all-thread_isaac_lab Layer-8 guard(landed successor 系譜)で LAYER8_FAIL=0**・snapshot+scripts 全 root・envs 限定 0 は不十分・128 fail = pN 測定明記 | 同 逐語 | ✅ 一致 |

**PASS 側の保持（pN concur — 私の当初評価が持った軸）**: transcript「exact pins 3/3・DEFER 26/26・frozen A 不触・design-only/impl CLOSED・C/slice 分離 = PASS」→ 私の §2(先走り)/§4(DEFER rule h)/frozen 不変 評価は**保持**（miss は B1-B4 の 4 軸のみ）。

**§8 roadmap supersede 確認（pQ 依頼）**: ✅ 私の**当初** §8 chain（pS-final-PASS 欠落）は v1.1 §5 が supersede。私は本 record §8 を既に amend 済（「design 修正 → **pS final 設計軸 PASS**(B1 統一) → pN DESIGN PASS-CLOSE」）= v1.1 canonical chain と一致。supersession を確認する。

**N1（NON-BLOCK provenance）acknowledge**: 私の record bank commit `652ff63a60` が p6 staged 5 path を co-land（pQ 非 pathspec commit）。semantic blob `bed5133fb28a` は exact-pin 不変・p6 通知済・以後 pathspec 限定 = 設計軸 issue でなく custody hygiene（pN/p6/pQ lane）・acknowledge のみ。

**指摘 N-1（minor・records-only・非 blocking）**: §5 header（v1.1 L62）が「（v3.2.2 §9 継承 — **変更なし**）」のまま。だが §5 body は「v3.2.2 §9 からの**明示 delta**（pN B1・supersession）」を記載 → **header が body と矛盾**（B1 と同種の面間不整合）。gate semantics は一貫（PASS を妨げない）が header label が stale。**推奨 = header を「v3.2.2 §9 + pN B1 delta（pS final-design PASS 追加）」等へ records-only 修正**。

## 11. Verdict（v1.1 fold）

**設計軸 = ✅PASS（prereg v1.1・pin `24af15733e4d`）** — B1-B4 fold 4/4 faithful（transcript 逐語一致）・N1 handled・§8 supersede 確認。**residual = 指摘 N-1（§5 header stale・records-only・非 blocking）のみ**。
- ⚠**two-key**: 本 PASS = **設計軸のみ**・**pN re-readback（証拠 exact-pin 軸）を代替しない**。gate = pS readback PASS → pN re-readback → pN SCOPE CONCUR。「私 PASS ≠ pN leg」= 本 chunk でも堅持（B1-B4 は pN が私の PASS を supervene して得た）。
- **design authoring / [CHANGE] = CLOSED 継続**（pN transcript・v1.1 §10）。
- dispatch = pQ（+ N-1 指摘）。次 = pN re-readback → SCOPE CONCUR。**私 = pN re-readback 待ち（self-start なし）**。
