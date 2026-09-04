# WMSO v0.2 — 同一完全 pin 参照の 3 軸独立設計レビュー計画 (v0.2.3 REVIEW CANDIDATE)

- node: `T-WMSO`; 起草 = Claude Code web session（review candidate 起草・**authority 無し**・凍結物へ非接触）; 作成 = 2026-09-03（UTC・`date -u` 実測）
- status: **REVIEW CANDIDATE v0.2.3（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.2 = 3 軸独立レビュー finding A-08 の fold（§10）
- 土台（凍結・編集しない・4 file）: contracts_v2 DESIGN v2.11.2 `00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff` @ `54f90a7de1e02fb14eaf793bf3c60d9503d0d82e` ／ EP v1.9 md `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` ／ EP JSON v1.9 `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e`（definition hash `e7ca43093084c167a209b008533a66d26a1fd3223d2a3c11274d28306c3ff803`）／ tensor_binding DESIGN v13 `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` @ `07250f4a0208b3bbd27eae6fef7d980743c4b538`
- 対象 = 本 package の 05（runtime spec v0.2）・06（industrial profile v0.2）・02/03（matrix）・04（EP 影響）・07（後継判断）。⛔ impl / training / closed-loop authority / production / push / freeze / slice = CLOSED 継続。`$D` = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701`。

## 0. 中心構造（目的）

```text
同じ exact pin（4 frozen file の full sha256 + bank commit）を全 reviewer が自分で再測した上で、
  軸 A contract-fidelity（凍結との忠実性・schema delta 0）
  軸 B runtime-safety（authority state machine の反証）
  軸 C deployment（profile の単調性・envelope・evidence 分離）
を互いに独立に行い、finding は反証検証（3 lens）を通ったものだけを fold する。
判定語彙 = PASS / PASS-WITH-CONDITIONS / HOLD。open = 0 を宣言しない。
```

## 1. 共通前提（全 reviewer 必須）

1. **pin 再測**: repo root で `bash $D/WMSO_EXACT_BASELINE_REVIEW_v0.2_20260903/verify_exact_baseline_pins.sh` を素の bash / python3 で実行し 11/11 PASS を自分の記録に残す（`./isaaclab.sh -p` 経由は不可 — D1.1-B H2 の exit-code mask hazard）。
2. **content sha で引く**: 版 label（v0.2 等）は照合用の注記。候補文書の sha256 は `SHA256SUMS.txt` を自分で再計算する。
3. **機械検査を先に走らせる**: `python3 $D/WMSO_EXACT_BASELINE_REVIEW_v0.2_20260903/check_review_candidate.py <doc> [--runtime]` で FAIL = 0 を確認してから読む（FAIL があれば読む前に HOLD）。CSV（02 / 03）は同 script が拡張子 `.csv` で CSV mode に入る（H1 / S1 非適用・header と行数 40 / 14 の assert・`disposition_v0_2` / `verdict` が removed / not_adopted の行は F1 免除・C1 は同じ）— v0.2.2（A-08）。
4. **finding の型**: `{id, 軸, severity ∈ {CRITICAL, HIGH, MEDIUM, LOW}, 候補 doc:line, 凍結 file:line（矛盾 or 欠落の根拠）, 再現手順 or 反例, 最小修正案}`。根拠の無い finding は受理しない。
5. **陽性対照（positive control）**: 各 reviewer の計器は、欠陥を注入した候補文書の複製（例: 旧 epoch 拒否を post-transfer ACK まで遅延させる／permit を再使用可にする／削除済みの v0.1 belief 参照型（05 版歴の 削除 項目）を再導入する／profile に action bounds field を足す）を**盲検**で読み、注入欠陥を検出できたことを先に示す。検出できない計器の verdict は採用しない（「存在 ≠ 十分」「弁別できない述語は証拠でない」）。
6. **手続の独立**: 各軸の reviewer は他軸の finding を読む前に自分の finding を確定する。同意は独立確認ではない。

## 2. 軸 A — contract fidelity（設計軸・pS 相当）

| id | checklist | 判定材料 |
|---|---|---|
| A1 | 凍結型（SkillDefinition / ExecutionBundle / ArtifactSlot / TensorBindingSpec / ObsBinding / ActionBinding / TimingSpec / ActionTimingSpec / EvidenceRecord / ProofItem / certificate 型 / HandoffOffer / SkillInvocation / SkillOutcome / TransitionRecord / SchemaVersionStamp / RuntimeSnapshot / BeliefRef）に field の追加・削除・改名が無い | 05 §1・§11 項 3、06 §9 項 3 |
| A2 | 凍結 enum（ProducerOutcome / ControlMode / TrainingLineage / ProofKind / Dtype / FeatureSource / ActionHold / ExprKind …）に member 追加が無い。`NO_CHAIN` 等は runtime enum のみ | 05 §7 |
| A3 | `BeliefRef`（value: SnapshotRef \| HashRef・`$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151`）を再利用し、v0.1 の重複 belief 参照型（05 版歴で 削除 済）が無い | 05 §1 表・§4.1 |
| A4 | 全 `file:line` 引用が正しい（機械検査 + 手動 sed ≥ 15 件） | 全 doc |
| A5 | authority state machine が contracts_v2 §5B（`validate_handoff(…, authority_epoch_snapshot)` = 等値検査・`E_HANDOFF_EPOCH_STALE`・責務分離 `:382`）と §5A3（`granted == True` = 必要条件・UNKNOWN = DENY）に整合 | 05 §1・§3.6・§4.4 |
| A6 | `max_obs_staleness_s` = 訓練時仮定、runtime 鮮度 = frozen FreshnessPolicy + 明示 `now` | 05 §4.2 |
| A7 | hash 面（SkillDefinitionHash / SkillActionId / ExecutionBundleHash / BehaviorSignature / tensor_binding_hash / evidence_policy_definition_hash）に何も入らず、runtime 記録は U14 defer と明記 | 03 matrix・05 §8 |
| A8 | EP evidence profile / deployment profile / execution profile の 3 軸を混同せず、SHADOW = 非 authority の帰属が凍結逐語のみ | 05 §4.4・06 §1.1・04 §5 |
| A9 | 凍結の委譲・carry（U-1 / U-4 / D1.1-C carry / 合成 = pX court / execution 軸 = Rs）を再決定していない | 05 §11・06 §7・07 |
| A10 | 主張しないこと・Open points（≠ 0）・header pin・authority 非主張 | 全 doc |
| A11 | 07 / 04 の論理が凍結の codec / hash 規則（`:385`・`:159`・`:218`・EP `:163`）から導かれている | 07 §3・04 §1 |
| A12 | CSV: 行数（40 / 14）・語彙・引用の正しさ・05/06 との矛盾なし | 02・03 |

## 3. 軸 B — runtime safety（反証軸）

| id | checklist |
|---|---|
| B1 | 二重所有: 2 executor が同時に command authority を持つ瞬間が構成できるか（ReadinessAck → CommitPermit → AuthorityCas の tuple 等値・旧 epoch 拒否の線形化点） |
| B2 | 所有不在: 出力 owner も SafeHold も無い瞬間が構成できるか（CAS 事後条件の SafeHold 活性・失敗経路） |
| B3 | stale / replay: 旧 epoch command・`handoff_offer_id` 再使用・permit 二重使用・失効後使用・stale ACK に束縛された permit |
| B4 | crash matrix: 新 executor が CAS 後 HealthConfirmation 前に crash／AuthorityManager が CAS 中に再起動／gateway 再起動／転送窓内の safety override／permit 発行後の Orchestrator crash — 各々が名前付き disposition と SafeHold に落ち、旧 owner が黙って復活しない |
| B5 | lease: 活性 lease はちょうど 1・profile hash / AuthorityDecision ref / 初期化 / AcceptedEnvelope / timing を束縛・変更 = 新 CAS・無効化 trigger 列挙・SHADOW lease は command を出さない・CLOSED_LOOP は `granted == True` + 外部 gate |
| B6 | boundary-only: mid-skill switching 経路が無い・再選択は TERMINAL boundary で新 BeliefRef + 明示 now から・InterruptOutcome は受理 + HOLD（切替無効）・continuation/recovery assessment は非 certified |
| B7 | safety 優先: IndependentSafetyLayer が WM 推論を待たず override（D0 §F `:319`）・HOLD 解除権の定義・deadline miss の disposition |
| B8 | disposition / fault の完全性: §3–§6 の全失敗経路が code を持ち fail-closed・ProducerOutcome 不変・写像表が total |
| B9 | audit: 全遷移（permit issue/consume/expire・CAS success/fail・lease activate/invalidate・HOLD・disposition・health）に record・epoch と lease id を持つ・hash 方式 = U14 defer |
| B10 | timing: rate / hold は D1.1-B と等値・timeout は profile parameter で数値定数なし |

## 4. 軸 C — deployment（産業用プロファイル）

| id | checklist |
|---|---|
| C1 | monotone strengthening が field 単位で機械検査可能（bounds は field 無し・rate/hold/control_mode 等値・initiation = AND のみ・freshness stricter-or-equal・escalation は SAFE_STOP 側のみ）— 検査を通る「広げる」profile を構成できるか |
| C2 | AcceptedEnvelope: 4 項の出所・空 = fail-closed・D1.1-B bounds は hash 参照のみ・単位 / frame と空間別評価 |
| C3 | lease 束縛: profile hash が lease に入る・変更 = 新 lease・in-place 更新無し・反循環（自己 hash 無し） |
| C4 | cell / controller / tool / payload: 識別・版・evidence 束縛・calibration・gateway config・health check の fail-closed |
| C5 | DeploymentEvidencePolicy: EP v1.9 と名前空間を共有しない・kind の網羅（cell / controller / tool / calibration / gateway / fault injection）・lease / audit との join・未認証範囲の明示 |
| C6 | composition OUT: v0.1 の並行実行 profile（06 版歴で 削除 済）/ `ParallelRegion` / arity / dual-arm 意味論が無く、court への pointer がある |
| C7 | 3 軸（EP evidence / deployment / execution）の分離・execution 軸を決めていない |
| C8 | initiation 強化が frozen predicate / required_control_resources を緩められず FreshnessPolicy を迂回できない |
| C9 | code 名（P_*）が frozen E_* と衝突しない・validation / test plan が設計宣言のみ |
| C10 | header・境界・open points・fold-map・review anchors |

## 5. 判定様式

- **PASS** = 未反証 CRITICAL / HIGH が 0・MEDIUM 以下は open として記録。
- **PASS-WITH-CONDITIONS** = MEDIUM 以上の finding があるが fold 案が明確で schema delta を要さない。
- **HOLD** = CRITICAL / HIGH が残る、または pin 再測・機械検査・陽性対照のいずれかが未達。
- **反証検証**: 各 finding を text / logic / impact の 3 lens で独立に反証する。既定 = refuted。過半が未反証の finding のみ fold。
- **fold** = 候補文書の新版（v0.2.1）として 版歴 / fold-map に finding id → 節 → 変更を 1 行ずつ記録し、機械検査 FAIL = 0 を再確認する。凍結物は編集しない。
- 同じ finding が再発した場合は根本原因（型・順序・語彙）を直す。回数上限で止めない。

## 6. 本 session の AI 3 軸レビューの位置づけ

- 本 package の `10_*` / `11_*` に記録する AI reviewer（別 context の agent）による 3 軸レビューは **準備レビュー**であり、pS（設計軸）／pY・pN（evidence 軸）／Rs の two-key を代替しない。
- AI レビューは §1 の全前提（pin 再測・機械検査・陽性対照・独立手続）に従う。結果の verdict 語彙は §5 と同じだが、gate を flip しない。
- 05 の起草は single-draft + critic fold であり judge panel を経ていない（05 §13 synthesis record）— 軸 B の反証はこの弱点を狙う。

## 7. Escalation（Rs へ上げるもの）

- 凍結物の編集・freeze・scope 変更・制御方式変更（Rs 専権 — `thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_pQ_rstechlead2_wmso.md:68`）。
- execution profile 軸（boundary-only / real-time）の裁定（`$D/WMSO_RS_C3_RULING_SLICE_PROFILE_20260720.md:65`）。
- checkpoint 切替の有効化（chunk 改称 + scope 再審査・`$D/WMSO_D11BC_SLICE_SCOPE_PREREG_RSTECHLEAD2_20260720.md:59`）。
- contracts_v3 / EP 後継の起票（07・04）。
- 合成（pX court / Rs 専権 OPEN・`$D/WMSO_RS_D11C_SCOPE_APPROVAL_CUSTODY_20260721.md:36-38`）。

## 8. 主張しないこと（境界）

1. 本計画は review の**手順**であり、verdict を先取りしない。
2. two-key・Rs 裁定・freeze・gate PASS を主張しない。
3. impl / training / closed-loop authority を解錠しない。

## 9. Open points（⛔ open = 0 を宣言しない）

- OPR-1: 陽性対照に用いる注入欠陥の集合（本 doc の例 4 件）の十分性。
- OPR-2: AI reviewer と human reviewer の finding の突合手続（重複・supersession の管理）。
- OPR-3: 本 doc 自体の採否 = 未。

## 10. 版歴 / fold-map

- v0.1（前 package・参照不能）→ v0.2（本 doc）。handoff 決定 H（3 軸独立レビュー）を根拠に再構成。陽性対照・独立手続・AI レビューの位置づけ（§1 項 5-6・§6）は本 session の改良として追加。旧 v0.1 の識別子は本 doc に無い（05/06 で 削除）。
- v0.2 → **v0.2.2**（2026-09-04 15:41 UTC）: A-08（CSV の機械検査手順）を §1 項 3 に反映。checklist は不変。実施記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`（A-08=CONFIRMED（LOW）/ v0.2.2 fold = RESOLVED）。

## 11. Review anchors

1. 全 reviewer が同一 pin を再測する手順 — §1 項 1（verifier script）。
2. finding の型と反証検証の既定（refuted）— §1 項 4・§5。
3. 陽性対照の要求 — §1 項 5。
4. 3 軸 checklist が 05/06/02/03/04/07 の節を網羅 — §2–§4。
5. Escalation 先が Rs 専権行為と一致 — §7 ↔ `thread_isaac_lab/thread-vault/02-Workflow/HANDOFF_pQ_rstechlead2_wmso.md:68`。
