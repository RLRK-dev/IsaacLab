# 独立設計レビュー依頼 — WMSO runtime spec / industrial deployment profile v0.2.7（two-key 判断の材料）

- 起草 = 2026-09-05 23:47 UTC（`date -u` 実測）・起草者 = THREAD project の CC（Claude Code）session。依頼者 = Rs。
- 宛先 = GPT-astra（外部・別系統の AI reviewer）。

## 0. 依頼の位置づけ（先に読んでください）

- 本依頼は **Rs が two-key（受理）判断を下すための独立レビュー**です。あなたの verdict は権限ではなく、Rs が判断する際の根拠として扱います（08 §6: AI レビューは準備レビューであり、pS / pY / Rs の two-key を代替しない）。これまでのレビューは全て Claude 系 agent が行ったため、**別系統の目で同じ盲点を共有していないか**を見てほしい、というのが依頼の核心です。
- 対象（review candidate・未 bank・two-key 未・gate PASS を主張しない）:
  - 05 `WMSO boundary-only runtime（TERMINAL boundary・checkpoint 切替なし）— RUNTIME SPEC (v0.2.7 REVIEW CANDIDATE)`
  - 06 `WMSO IndustrialDeploymentProfile — DEPLOYMENT PROFILE SPEC (v0.2.7 REVIEW CANDIDATE)`
  - repo `RLRK-dev/IsaacLab` branch `claude/v0-2-design-candidates-snqbmy` commit `f1393050`、path `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/WMSO_EXACT_BASELINE_REVIEW_v0.2_20260903/`
- 凍結土台（編集不可・content sha で引く）: contracts_v2 DESIGN v2.11.2 `00192d20…8aff`／ EP v1.9 md `c474acea…27e7`・JSON `e63176af…c6e`（definition hash `e7ca4309…3803`）／ tensor_binding DESIGN v13 `5a1874d3…a6`。**両 doc は凍結 schema に field を足さない（schema delta 0）が設計制約**です。
- 状態: impl / training / closed-loop authority / production / freeze / slice は全て CLOSED。これらを開く判断は求めていません。
- 経緯（事実・11_ §2 / §7 / §9 / §10）: 3 軸独立レビュー round 1（AI reviewer 5 体・verifier 5 体・80 finding・79 確定）→ v0.2.3 → round 2（35 件・33 確定）→ v0.2.4 → Rs 裁定（外部 AI GPT5.6sol の推奨を Rs が採用・11_ §8）→ v0.2.5 → round 3（41 件・39 確定）→ v0.2.6 → round 4（35 件・34 確定）→ **v0.2.7**。各 round の HIGH = 5 → 3 → 5 → 2（0 を見ていない）。round 5（v0.2.7 対象）は本依頼と並行して進行中で、その fold 後に v0.2.8 が出ます。本依頼は v0.2.7 に pin しています — v0.2.8 が出たら §1 の sha 表だけ差し替えて再発行します。
- 用語: `profile_hash` = deployment profile の content hash（lease に束縛・変更 = 新 lease）。`P_*` = profile 登録時（第 1 評価点）/ permit 発行時（第 2 評価点）の機械検査 code。`R_*` = runtime fault code。`lease` = CommandGateway が executor の command を actuation に通す権限の単位。`ISL` = IndependentSafetyLayer。`SHADOW_NON_AUTHORITY` = actuation 無しの lease mode。`two-key` = 独立 safety approver + custody approver の二者受理（06 §8.3）。

## 1. 添付ファイルと content sha（読む優先順）

| # | file（添付名） | 役割 | sha256 | bytes |
|---|---|---|---|---|
| 1 | `05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md` | **主対象**（runtime 層・約 1,050 行） | `007d753d4ece153d30168cc9b09631e758fdafed55116affe9a9dc1d75bfa9fc` | 178,856 |
| 2 | `06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md` | **主対象**（deployment 層・約 730 行） | `2d35d144e00dafdf4b0d96737ca48a614d0bab1038c59a9dcd5563782bb20da4` | 116,686 |
| 3 | `08_INDEPENDENT_REVIEW_PLAN_20260903.md` | レビュー計画・verdict 様式（§5）・AI レビューの位置づけ（§6） | `e560737a71996b934416e56892f4f48470961592341542df9fe5f21ed9157a2a` | 13,937 |
| 4 | `11_THREE_AXIS_REVIEW_RECORD_20260903.md` | これまでの全 finding と処置。**§8 = Rs 裁定**、§10.1 末尾 = 起草既定として Rs 確認待ちの項目 | `38686b681056998b71401ed6aac80b4fde32537a86e27a8953a1dec6c6042460` | 75,495 |
| 5 | `WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md` | 凍結 contracts_v2（05 が依拠する静的契約） | `00192d20ca00b654cf6cfdb9d04b03ca14adfd0b93f2105c0fea28c295ff8aff` | 105,565 |
| 6 | `WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md` | D0 architecture（authority / ISL / handoff の原則） | `1b107df59f6e42669247777ea48420022d84c1663d204bdc0b25bcc19da0f6bb` | 41,600 |
| 7 | `WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md` | 凍結 tensor_binding（rate / hold / envelope の frozen 側） | `5a1874d3be8b98b8aeaace73890d8021cbc7f9814e048741f7f58d6746f349a6` | 104,199 |
| 8 | `WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md` + `WMSO_EvidencePolicy_v1.9.json` | 凍結 EP v1.9（06 §6 が「EP の外」であることの確認用） | `c474acea7c58acc22050c2ad9944fd45a18f5c76967964b42d11922e28fa27e7` / `e63176af9bc3a246b1c32db369ec59f8d09a4c96c381bb03a3a6024bd9811c6e` | 28,596 / 25,448 |
| 9 | `04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md` | EP v1.9 は不変（definition hash 不変）という影響評価 | `61a9d24ac6aea00fe6ad43832a191c1ed8f43944f33b0f365f544f59f3a745cf` | 8,448 |
| 10 | `check_review_candidate.py` | 機械検査（FAIL = 0 が要件・v0.2.7 で Q2 強化） | `246b0644f305b87dfc691a8f2db78fb1ab432790b1b6ad884d903a19baa727e4` | — |

- 容量の都合で全部を読めない場合は **1 → 2 → 3 → 4 → 5 → 6** の順に読み、**どこまで読んだかを回答の冒頭に明記**してください（読んでいない範囲について判定しないでください）。
- RS71 §0（不変前提・`thread_isaac_lab/thread-vault/04-Specs/RS71-System-Spec-SSOT.md:23-27`・file sha `34bd6a9a…928f`）の見出しだけ転記します。値（88 mm・Y = ∓0.35 等）は **05 / 06 本文には書かない**のが規約です（本文は file:line で参照するのみ）:
  1. DUAL-ARM — cable は EVERY motion で両腕（UR15 × 2）が保持・操作する。片腕化しない。
  2. GRASP SPAN / FIXED BASES — 88 mm の two-EE grasp span・base は Y = ∓0.35 に固定（機械可読 SSOT = `task_config.py:21-22`）。
  3. CONTROL = DiffIK only。
  4. GRIPPER GEOMETRY LOCKED — finger 設計（コ字形）は human-LOCKED。
  5. NO KINEMATIC TRICK — 唯一の例外 = clip-retention pin。

## 2. 読む前に押さえてほしい前提

- 05 / 06 は **新語（runtime 層・deployment 層の型）だけを足し、凍結 schema・凍結 hash の preimage には入れない**（05 INV-16・06 §2.3）。凍結 4 file の変更を要する fix は採れません（Rs 専権）。
- 検査は全て fail-closed（評価不能 = FALSE / 違反）が既定です。「評価不能なのに既定が書かれていない」箇所は finding です。
- 陽性対照（10_ §1・欠陥 8 件を注入した複製で計器を検証）の注入欠陥は実本文には**ありません**。実本文で再現できない限り報告しないでください。
- Rs 裁定（11_ §8）の**設計方針そのもの**（案 B+・外部 CellSafetyTimingBaseline・ProfileRegistry / AcceptanceRecord・OP-19 三層）は finding にしないでください。本文がその方針を正しく・整合的に・fail-closed に実現していない点は finding です。
- 05 / 06 に「起草既定（Rs 確認待ち）」と明記した値・選択（§4 参照）は、本文が内部矛盾していない限り finding にしないでください。

## 3. 依頼内容

**A. 3 軸レビュー（08 §2–§4 と同じ軸）**
- 軸 A contract fidelity: 05 / 06 の各型・各検査が凍結 4 file の意味論を**狭める方向にしか**使われていないか（広げる経路が無いか）。frozen field を再定義していないか。hash preimage に runtime / profile 型が混入しないか。
- 軸 B runtime safety: AuthorityState / CAS / permit / lease / SafeHold / audit の線形化・総和性（totality）・fail-closed。特に (1) `RuntimeFaultCode` 全 member が §3.7 失敗表に行を持ち、各行の (fault, 状態効果, disposition) が到達可能か、(2) §3.7 head-check 行 (a)〜(e) / event 行 / deadline 行の副場合が互いに矛盾しないか、(3) permit 前提条件 (a)〜(m) と CAS 条件 1〜12 の境界（strict / non-strict）・優先順が一貫しているか、(4) SHADOW と CLOSED_LOOP で actuation 無しの保証が破れる経路が無いか、(5) AuditRecorder / registry / monitor / clock の障害の組合せで「記録なしに authority が動く」窓が無いか。
- 軸 C deployment: 実 cell（UR15 × 2）の commissioning / 保守 / 運用の立場から、profile 作者・commissioning 担当・registry 運用者・保守の機器交換が**検査をすり抜けて**危険側に動ける経路が無いか。特に v0.2.5–v0.2.7 で追加した型（`ArmSpec` / `CellKinematicLayoutRef` / `InterArmRestrictionSet` / `ProfileAcceptanceRecord` / `CellSafetyTimingBaseline` / role registry / `finger_geometry_sha256` / `FaultInjectionRequirement.trigger` / REQUIRED_DIAGNOSTIC_ITEMS）が**束縛・hash・列挙・評価点**まで閉じているか（round 3・4 の HIGH はこの型で出た）。

**B. two-key の観点（Rs が知りたいこと）**
1. v0.2.7 は「受理して良い状態」か。受理を止める CRITICAL / HIGH があるか（08 §5 の様式で verdict）。
2. 受理の前に **Rs が決めなければならない事項**は何か（本文が起草既定で置いたもの・§4 の open のうち受理を左右するもの）。
3. Claude 系 reviewer 4 round が共有していそうな盲点（同じ型の finding が繰り返している・同じ前提を疑っていない等）があれば指摘してください。
4. 前提の訂正: 本依頼文や 05 / 06 の「事実」記述に誤りがあれば、回答の冒頭で先に訂正してください（前回の外部回答では前提訂正 5 点が最も有用でした）。

## 4. 既知の open（finding にしなくてよい・Rs / RT0 の決めごと）

- 06 OPP-16 / 05 OP-20: `CellSafetyTimingBaseline` の発行主体（RT0 / cell safety court）と値（ceiling・`safety_response_budget_s`・`base_pose_tolerance_*`・`max_validity_s`・diagnostic item の周期）。
- 06 OPP-13: role の実名（pS / pY 等）と role registry head の発行者 / ACL。
- 06 OPP-17 / 05 OP-21: 「every motion で両腕」の実行適合性は composition / runtime 検査の court（本 doc は両腕能力と arm 間静的制約まで）。
- 05 OP-19 残 open: 周期診断の対象項目と周期の出所、head-check 副場合 (c) monitor 喪失 / (d) 診断失敗の disposition 既定（= HOLD）。
- 05 OP-5 note: gateway が `COMMAND_ADMITTED` の append 不能時に admission を同期 block するか。
- 11_ §10.1 末尾: `P_VALIDITY_UNBOUNDED` の kind 集合（CEM・停止性能 FI を含む）、identity 系 diagnostic item の必須化。
- 05 OP-15 / 06 OPS-3: 本 doc 自体の two-key・Rs 裁定 = 未（本依頼の対象そのもの）。

## 5. 求める出力形式

1. **冒頭**: 読了範囲（file と行範囲）・前提の訂正（あれば）。
2. **verdict**（08 §5 の様式）: PASS / PASS-WITH-CONDITIONS / HOLD と理由。HOLD なら止める finding の id を明示。
3. **findings**: 重大度降順。各 finding は次の JSON 1 object（機械処理するため厳守）:
   ```json
   {"id": "GA-01", "severity": "CRITICAL|HIGH|MEDIUM|LOW", "doc": "05" | "06" | "05 (+06)",
    "doc_line": "05:123; 06:45", "frozen_ref": "file:line or \"\"",
    "claim": "1 文の主張", "evidence": "doc:line からの引用と、失敗する具体的な手順 / interleaving",
    "fix": "凍結 schema delta 0 の最小修正（節・文・型）。Rs 専権なら 'open item (OP/OPP) として記録' と書く"}
   ```
   severity の基準: HIGH = 再現可能で fail-closed 保証・RS71 §0 の束縛・schema delta 0 のいずれかを破る。文体・好みは LOW にもしない（報告しない）。
4. **Rs が決める事項の一覧**（受理を左右する順）。
5. **主張しないこと**: 権限・gate PASS・two-key の代替を主張しない旨と、読んでいない範囲。

## 6. 制約

- 凍結 4 file の編集・CLOSED 項目（impl / training / closed-loop authority / production / freeze）の開放を前提にした fix は提案しないでください。
- 主張は doc:line（できれば引用）で裏付け、事実と推測を分けてください。数値は本文にあるものだけを使ってください（RS71 の値を 05 / 06 に書けとは言わないでください — 規約で書きません）。
- 回答は日本語で構いません（JSON の key は英語）。

---
（CC 側の処理）本回答は `review_records/rs_consult/A_GPTastra_<date>.md` に逐語で保存し、前提訂正を fact-check したうえで、finding は Claude 系 verifier（3 lens・反証優先）に掛け、confirmed 分を次版に fold します。verdict と「Rs が決める事項」は Rs に渡します。
