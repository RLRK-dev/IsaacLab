# WMSO v0.2 レビュー package — 利用者向け要約（日本語）

- 記録 = 2026-09-06 08:43 UTC（`date -u` 実測・v0.2.9 で更新）。本 file は package の読み方の案内であり、規範文書ではない。
- 状態: **REVIEW CANDIDATE v0.2.9・未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない**。impl / training / closed-loop authority / production / freeze / slice = CLOSED のまま。

## 1. 何が入っているか

| file | 役割 |
|---|---|
| `01_BASELINE_CUSTODY_VERIFICATION_20260903.md` + `verify_exact_baseline_pins.sh` + `09_BASELINE_PIN_20260903.json` | 凍結 4 file（contracts_v2 DESIGN v2.11.2・EP v1.9 md / JSON・tensor_binding DESIGN v13）の exact pin と再測手順（11/11 PASS） |
| `02_…csv` / `03_…csv` | 旧 v0.1 の項目が凍結物と重なるか（home matrix）／ 変更 class が hash 面を動かすか（identity impact） |
| `04_…md` | EP v1.9 は不変（definition hash 不変）という影響評価 |
| `05_WMSO_RUNTIME_SPEC_…md` | **runtime spec v0.2.9**（boundary-only・TERMINAL boundary・checkpoint 切替なし。AuthorityManager / CommandGateway / CAS / lease / SafeHold / audit） |
| `06_WMSO_INDUSTRIAL_PROFILE_…md` | **industrial deployment profile v0.2.9**（cell 固有条件を content-addressed にし、凍結意味論を狭める方向にしか使えない） |
| `07_…md` | 後継静的契約は今は作らない（`contracts_v3` は静的意味論の認証時のみ）という判断 |
| `08_…md` | 3 軸独立レビュー計画（contract / runtime / deployment） |
| `10_…md` + `review_records/PC_*` | 陽性対照（欠陥を注入した複製で計器を検証。7/8 検出・盲点は checker O3 で機械化） |
| `11_THREE_AXIS_REVIEW_RECORD_20260903.md` + `review_records/AXIS_*` / `VERIFY_*` | **3 軸レビューの実施記録**（round 1: reviewer 5 体・verifier 5 体・80 finding／ round 2（v0.2.3 再レビュー・§7）: reviewer 2 体・verifier 2 体・35 finding／ round 3（v0.2.5 再レビュー・§9）: reviewer 2 体・verifier 2 体・41 finding／ round 4（v0.2.6 再レビュー・§10）: reviewer 2 体・verifier 2 体・35 finding／ round 5（v0.2.7 再レビュー・§11）: reviewer 2 体・verifier 2 体・44 finding／ 外部レビュー（v0.2.8・§12）: GPT-astra 7 finding・verifier 1 体） |
| `review_records/fold/*` | v0.2.1 → … → v0.2.9 の fold を再現する script と verifier verdict の JSON |
| `check_review_candidate.py` / `SHA256SUMS.txt` | 機械検査（FAIL = 0 が要件）／ content sha（版 label でなく sha で引く） |

## 2. レビューの結果（事実・数値は 11_ §2 から）

- finding 総数 80（A 12 / A2 12 / B 21 / B2 17 / C 18）。independent verifier（3 lens: text / logic / impact）が 80 件全てを判定。
- confirmed 79・refuted 1（A2-09 = 反循環文の文言のみ・NOT_A_DEFECT）。
- v0.2.2 の fold 状態（A/A2/B/B2 の 61 件）: RESOLVED 49・PARTIAL 12・NOT_RESOLVED 0。PARTIAL 12 件の残差は v0.2.3 で処置。
- 軸 C（deployment）は v0.2.2 を対象に 18 件（reviewer: HIGH 4 / MEDIUM 6 / LOW 8 → verifier: HIGH 3 / MEDIUM 8 / LOW 7）。全件 v0.2.3 で fold。
- 主な設計変更（v0.2.2 → v0.2.3）: timeout の相対順序検査 `P_TIMEOUT_ORDER`／ clearance role の被覆 `P_CLEARANCE_ROLE_MISSING`／ evidence の失効・subject 単位執行 `P_EVIDENCE_EXPIRED`／ predicate・evaluator の content hash／ lease の時間上限 `lease_max_duration_s`／ health check に identity 確認／ 閉じた enum（calibration kind・zone kind）／ envelope の空虚化防止。
- 機械検査: 全 doc / csv で FAIL = 0（11_ §6 に実測出力）。v0.2.3 で横断整合検査（fault code の失敗表 total・id 連番・条件 10 と §5.4 の集合等値・timeout field の 05/06 対応・P_* の列挙）を checker に追加。
- **round 2（v0.2.3 本文への再レビュー → v0.2.4）**: reviewer R1（runtime spec）16 件・R2（industrial profile）19 件 = 35 件。verifier V1 / V2 が 33 件 confirmed・2 件 refuted（R1-11・R2-10）。confirmed 33 件を v0.2.4 に fold。主な変更: content hash 照合を profile の全宣言 hash へ一般化、timeout の計時範囲、ZOH でも線分評価、SAFEHOLD の同 tier 遷移と `safehold_disposition`、SAFETY の clearance role 必須化、**DUAL-ARM cell を表現する `ArmSpec`（Rs 確認事項 OPP-15）**、profile の失効経路、ISL の identity、evidence policy の循環検査。

## 3. 何を主張していないか（読み手が誤解しやすい点）

- reviewer / verifier は AI（別 context の subagent）。**human two-key（pS / pY / Rs）ではない**。08 §6 の位置づけ = 予備レビュー。
- **Rs 裁定（2026-09-04・§11 §8）**: 残っていた Rs 確認事項 4 件（OPP-15 / OPP-11 / OPP-13 / OP-19）は外部 AI（GPT5.6sol）の推奨を Rs が全件採用し v0.2.5 に fold。主な追加: DUAL-ARM cell の base transform と arm 間制約（`CellKinematicLayoutRef` / `InterArmRestrictionSet`・INTER_ARM 項）、timeout の絶対上限を外部 `CellSafetyTimingBaseline` で検査（`P_TIMEOUT_CEILING`）、permit の実効失効（decision age を CAS で再検査）、append-only `ProfileRegistry`（CLOSED_LOOP 受理 = two-key・SUSPENDED = one-key）、活性 lease の `validity_deadline_mono` + event 無効化（`SafeHoldReason.VALIDITY_EXPIRED`）。
- **round 3（v0.2.5 → v0.2.6・§11 §9）**: reviewer R3（runtime spec）22 件 + R4（industrial profile）19 件 = 41 件。verifier V3 / V4 が 39 件 confirmed・2 件 refuted（R3-15・R4-19）。confirmed 分を v0.2.6 に fold。主な変更: INTER_ARM 項を「同一 command の両腕提案線分の対」で評価（`GatewayCommand.arm_targets`）、content hash 照合の列挙を 06 §2.1 の全 hash field に一致させ checker Q2 で機械検査、negative control を `DeploymentEvidencePolicy.negative_controls` で執行、two-key を閉じた role 語彙 + operator 相異 + role registry で機械検査、`validity_deadline_source` と VALIDITY_EXPIRED の disposition 表、manager 側 head-check（monitor 非依存）、clock 異常検査 `R_CLOCK_ANOMALY`、BASE_POSE_VERIFY、baseline の cell 束縛と supersession。
- **round 4（v0.2.6 → v0.2.7・§11 §10）**: reviewer R5（runtime spec）14 件 + R6（industrial profile）21 件 = 35 件。verifier V5 / V6 が 34 件 confirmed・1 件 refuted（R5-11）。confirmed 分を v0.2.7 に fold。主な変更: SHADOW lease も deadline / event / head-check で無効化（mode を問わず・保守側に統一）、head-check 行を副場合ごとに fault / disposition まで total 化、permit 前提条件 (m)（監視系の生存）、`safehold_disposition` を lease 活性時に reset、`R_AUDIT_UNAVAILABLE`（記録が先）、CAS 条件の境界を厳密化、FAULT payload の trigger 語彙を SSOT 化（`FaultInjectionRequirement.trigger`）、gripper finger geometry（RS71 §0 #4）を `finger_geometry_sha256` で束縛（`P_TOOL_GEOMETRY_MISMATCH`）、`P_FAULT_EVIDENCE_UNVERIFIED` の subject 文法、one-key SUSPENDED record の検査分離、role registry（1 head）と clearance record の資格照合、`base_pose_tolerance_*` / `max_validity_s`、REQUIRED_DIAGNOSTIC_ITEMS（`P_BASELINE_INCOMPLETE`）、登録 = PROPOSED record の文脈、checker Q2 の強化。
- **round 5（v0.2.7 → v0.2.8・§11 §11）**: reviewer R7（runtime spec）19 件 + R8（industrial profile）25 件 = 44 件。**HIGH 0**（初めて）。verifier V7 / V8 が 37 件 confirmed・7 件 refuted（R7-19・R8-04 / 19 / 21 / 22 / 24 / 25 — Rs 専権の設計選択や既知 defer で本文欠陥ではないもの）。confirmed 分を v0.2.8 に fold。主な変更: head-check を owner を問わず周期実行（SAFEHOLD からの permit deadlock を閉じる）、authority head（PROPOSED を除く）の定義、role registry の supersession 検出（同一 batch の SUSPENDED 義務 + head-check (f)）、manager 不読時に SafeStop を保持する gateway 局所 `last_disposition`、`arm_targets ⊆ lease.ownership` の admission 節、`P_VALIDITY_UNBOUNDED` の 3 節化（CalibrationRef 側の評価不能を解消）、MIN_FAULT_INJECTION を (code, trigger) で列挙、baseline registry head の書込時 / permit / CAS 照合、`P_ACCEPTANCE_RECORD_INVALID` の PROPOSED / generation 規則の統一、SHADOW 受理の資格照合、role 語彙検査を `P_CLEARANCE_ROLE_MISSING` へ、第 1 評価点を閉じた list に（checker Q3）、期限境界の統一。
- **外部レビュー（v0.2.8 → v0.2.9・§11 §12）**: Rs の指示で別系統の AI（GPT-astra）に v0.2.8 を独立レビューさせた（依頼文 = `review_records/rs_consult/Q_GPTastra_20260906_v028.md`・回答一式 = `A_GPTastra_20260906/`）。外部 verdict = **HOLD**（HIGH 4 / MEDIUM 3）。Claude verifier V9 が 7 件全て confirmed（severity は HIGH 3 / MEDIUM 3 / LOW 1 に再付値・前提 7/7 正確）。confirmed 分を v0.2.9 に fold。主な変更: gateway 局所 `stop_latch`（自ら出した SafeStop を manager 不読中に失わない）、certificate / lease / invocation を SkillDefinitionHash で束縛（ActionId 一致は本文一致の代用にならない）、開始判断の belief 鮮度を permit / CAS に束縛、兄弟停止の key を構成 hash から物理 cell の安定 id `(site_id, cell_id)` へ、PROPOSED を挟んだ停止 event の対象を authority record に固定、INV-02 / 証明 E を CasKind 別に、baseline に `clock_drift_tolerance_s`。外部 reviewer が指摘した Claude 側の盲点 3 点（記述の存在 ≠ 検証対象の一致・時系列をまたぐ結合・構成 hash ≠ 操作対象 id）は 11_ §12.1 に記録。
- **v0.2.9 本文への再レビュー・再 verify は未実施**。Claude round の HIGH は 5 → 3 → 5 → 2 → 0 だったが、別系統の外部レビューは v0.2.8 に HIGH 4 を出した（Claude 系 5 round が共有していた盲点）。「open = 0」は宣言しない。「open = 0」は宣言しない（05 §12・06 §10 に open が残る）。
- 前 package（v0.1）は本 sandbox に無く、handoff 決定から再構成した（01 §で honest に記録）。judge panel（3 draft × 2 judge）は session 上限で未実施。
- 凍結 4 file には触れていない（pin 再測 11/11 PASS）。schema delta 0。

## 4. 次に人が判断すること（提案・Rs 専権）

1. v0.2.9 の扱い: 外部レビュー（GPT-astra）の HOLD は v0.2.8 への判定で、v0.2.9 で解消したとは主張できない。選択肢 = (a) v0.2.9 を GPT-astra に再発行して再判定を得る（推奨・同じ手続で「修正前後で差が出ること」を確認）、(b) 人間 two-key へ回す、(c) Claude round 6 を挟む。
2. 外部 reviewer が「Rs が決める事項」とした 4 点（11_ §12.1 末尾）: 物理 cell id の custody と停止 / 解除の管理主体（OPP-18）、manager 不読時の停止既定（R7-04）、`clock_drift_tolerance_s` の値と時計対応の前提（OPP-16）、検証手続に trace 検証を足すか。
3. round 4 / 5 で起草既定として置いた値・選択の確認（11_ §10.1 / §11.1 末尾に一覧: head-check 副場合の disposition・`P_VALIDITY_UNBOUNDED` の kind 集合・base pose 許容 / validity 上限の値・identity 系 diagnostic item の必須化・role registry head の発行者・gateway の audit 同期 block）。
4. 裁定後に残る open: OPP-16（timing baseline の発行主体 = RT0 / cell safety court と値の根拠）・OPP-17 / 05 OP-21（「every motion で両腕」の実行適合性は composition court）・OPP-13 の role 実名（pS / pY 等の割当）・OP-19 の周期診断項目（baseline の diagnostic_items）。
5. `contracts_v3` を起票しない判断（07）の追認。
