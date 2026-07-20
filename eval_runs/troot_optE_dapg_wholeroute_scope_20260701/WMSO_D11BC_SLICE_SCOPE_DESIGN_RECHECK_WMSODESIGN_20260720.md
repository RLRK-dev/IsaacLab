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

## 7. Verdict

**設計軸 = ✅PASS（scope prereg v1・pin `87f348540c93`）**
- 先祖返り 0 / 先走り 0 / DEFER-RECON CONCUR(rule h 完全・FOUNDATIONAL 判定妥当) / scope 完全性 GOOD(落とし 0) / must-fix 0。
- carry = C-1 / C-2（B DESIGN DRAFT 段の遵守事項・prereg 内含の loud 固定）。
- ⚠**two-key**: 本 PASS = **設計軸のみ**。**pN SCOPE CONCUR（証拠/custody 軸）を代替しない**。gate §5 = pS PASS → pN SCOPE CONCUR の two-key。D1.1-A で pN が pS PASS を 4 回 supervene した pattern を継承。

## 8. Roadmap（番人 duty #3）+ 次の一手（duty #4）

**現在地**: D1.1-A `contracts_v2` = FROZEN/CUSTODY-CLOSED（不変土台）。D1.1-B/C/slice = Rs 着手指示済 → **scope prereg 段の第 1 ゲート(pS re-check) = 本 PASS**。

**Roadmap（gate §5 / freeze §5）**:
```
[今] scope prereg → pS re-check(✅PASS) → pN SCOPE CONCUR
  → D1.1-B DESIGN doc 着手(§2 IN 駆動・C-1/C-2 遵守) → 5体 CC Debate/pre-mortem
  → design 修正 → pN DESIGN PASS-CLOSE(exact-pin) → Rs freeze 判定
  → [C 着手時] D1.1-C 詳細 prereg → 同 loop
  → [slice 着手時] slice 詳細 prereg → 同 loop
  → slice RUN レグ = impl 解錠 + clean substrate(DDR #25/#26) + 実行 gate + Rs 承認（別 prereg）
```

**次の一手**:
1. **pQ**: 本 pS PASS を受け、**pN へ SCOPE CONCUR readback dispatch**（§9 gate 順）。C-1/C-2 は pN にも共有推奨。
2. pN SCOPE CONCUR 後、pQ が D1.1-B DESIGN doc 着手（frozen v2.11.2 土台・§2 IN 実装・C-1/C-2 遵守）。
3. **pS(私)**: standby。次レグ = D1.1-B DESIGN doc の設計軸 verify（draft 完成後・§5 の「pS 設計軸 PASS」ゲート）。self-start なし。
