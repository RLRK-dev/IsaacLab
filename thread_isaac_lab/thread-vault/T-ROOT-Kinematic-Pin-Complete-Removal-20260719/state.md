---
node_id: T-ROOT-Kinematic-Pin-Complete-Removal-20260719
node_name: kinematic / pin 完全削除 — arm-control remediation task (d)
goal: "【2026-07-21 Rs 裁定 B で範囲縮小】active 実行面から kinematic による物理バイパスを除去し（⛔ただし clip-retention pin = クリップのケーブル固定 は Rs 許可の例外として除去対象から外れる） physics-faithful な制御へ置換して、RS71 §0 不変前提 #3 (DiffIK-only) / #5 (no-kinematic-trick) が機械検証で成立する状態にする。"
goal_verification: |
  (すべて既存 SSOT に接地。本 node は新しい acceptance を発明しない)
  1. Layer 8 canonical census = 0 — F3 拡張後の all-root scan (全 thread_isaac_lab Python root) 基準。
     ⚠ 現在地 = 35 (A 27 + D aerial 5 + skills-snapshot 3)。旧 restricted-root 基準の「128→125」は別 measurement surface。
  2. guard が fail-closed (既知=WARN の baseline 廃止済、scripts/validations/check_control_method.sh)。
  3. 各 chunk が two-key (機構軸 p5 + 証拠軸 pN)。片軸 PASS は充足でない。
  4. 各 stage が charter §6 の gate を通過 (L3 chain + Rs sign-off + video leg)。
  5. landing / HALT 解除は本 goal に含まれない (別 GO)。
status: IN_PROGRESS
parent_node: T-ROOT
children_nodes: []
dependencies:
  precedent: []
  blocker:
    - "DDR #25 carry ①: Z-Check gate の env7-mujoco 移植が未実装 (VBD retire は移植検証後)"
    - "DDR #25 carry ②: B0/B1 旧 artifact = HISTORICAL / NOT_COMPARABLE ⇒ fresh 再取得必須"
    - "DDR #25 carry ③: CLAUDE.md :271 / :85 は移植検証後に Rs 承認で更新予定・現在未更新・CC 編集不可"
    - "DDR #26: P0 substrate defect (隠れ綱引き) — banked evidence の継続利用可否"
session_history:
  - id: T-ROOT-Kinematic-Pin-Complete-Removal-20260719#s1
    status: active
    started_at: 2026-07-20T20:01:09+09:00
    note: "Rs 承認 (node 作成 + 起動、2026-07-20) により起票。[DEFINE] = 00-Project-Management/node-proposal-T-ROOT-Kinematic-Pin-Complete-Removal-20260719.md @ 14a891d256。既往 c4-c48 は §3 adopted_existing_arc provenance であり本 session の成果ではない。起票時点 = step2 CLOSE / step3 docs-records-only OPEN。"
created: 2026-07-20T20:01:09+09:00
last_updated: 2026-07-21T02:14:53+09:00
spec_version: LTM-1 v1.2
---

# T-ROOT-Kinematic-Pin-Complete-Removal-20260719 — task (d) kinematic / pin 完全削除

## 0. 起票の経緯

**IN_PROGRESS。** Rs 前提「**sim は現実世界・kinematic 完全削除 (pin 含む)**」(2026-07-19。⚠**§5-A で範囲縮小済 — 本行は起票時の経緯であって現行前提ではない**) に発する arc を、
pN (T-ROOT-OPS-SUPERVISOR-CODEX) の NEST 整合裁定 (2026-07-20 13:02) に従って node 化したもの。

裁定の骨子 = 本 arc は post-07-19 の新 task で **独立 goal・多 session・repo 横断 scope・HALT/acceptance 条件・
p4/p5/pN/p6 の分業**を持つため、LEDGER 行 + DDR #25 だけでは **構造的に不可視**（cascade 判定が参照できない）。

⚠ 対照: `T-ROOT-RS-TECH-LEAD` は **role label であって node ではない**（同裁定）。本 node は role の起票ではない。

## 1. 責任分離（lane）

- **design owner:** p5 VT-DESIGN — charter `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md`
- **build / execute:** p4 RS-TECH-LEAD（worktree `probe/pd1-arm-pd`）
- **independent verifier:** pN OPS-SUP-CODEX（証拠・custody 軸）
- **Vault / current-state custody:** p6 PLAN-KEEPER

## 2. means（workstream）

charter `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md` — 現行 **v2.27**（c47 `4dc72baf08`・sha256 `8543c880365b`・p6 実測）の stage 定義に従う。**B0/B1 移管の acceptance 条件 = c48 `bb68cb3c0f`**。〔v2.25 = c42 `01d3011f5e` は superseded〕 identified な workstream:

- **GATE-MIGRATE** — Fingertip Z-Check Gate を env7-mujoco へ移植 → 検証後に VBD copy retire（Rs 裁定 c36）
- **B0B1-MIGRATE** — B0/B1 evaluator を env7-mujoco へ移管（Rs 承認済）・旧 artifact は fresh 再取得必須
- **A-group rewrite** — routing_utils / clip_routing（残 27）
- **D aerial**（残 5）/ **skills-snapshot**（残 3・disposition = DELETE 確定、c27 `bfc35ca87c`）

⚠ **GATE-MIGRATE と B0B1-MIGRATE は別 workstream**（p4 2026-07-20 16:54）。単一 task に畳まない。
⚠ **子 node 化は §3.1 の別 gate**。必要になった時点で再帰適用する（本 node は leaf 起票）。

## 3. provenance — `adopted_existing_arc`

本 node は **既存 arc の採録**。既往作業を session として遡及生成していない（`#s1` = 起票時点）。
既往の実体は以下を参照（node の成果ではなく node 化以前の記録）:

- **chunk chain c4 … c48** — `probe/pd1-arm-pd`（2026-07-20 20:12 時点 tip `bb68cb3c0f` = c48）。
  ⚠ 本 branch (`rlrk/optE-s2-substrate-swap`) には **未着地**
- **Rs 裁定** = c36 `eefad77773`（逐語「1：a 2:承認」）
- **[DEFINE]** = `00-Project-Management/node-proposal-T-ROOT-Kinematic-Pin-Complete-Removal-20260719.md` @ `14a891d256`

## 4. SSOT の分担（二重管理の防止 — pN 裁定）

- **結果・判定の SSOT = `07-Design/00-DESIGN-STATUS-LEDGER.md` の (d) 行 + `§DDR #25` + charter。**
  本 state.md へ複製しない。
- **本 state.md が持つのは lifecycle / goal / pointers のみ。**

## 5. ⛔ authority fence（node 化で一切変わらない）

**source / `[CHANGE]` / RUN / landing / push / training / `CLAUDE.md` 編集 = CLOSED。**
step4 以降は step3 two-key + 別 GO まで不可。**node の起票は実行の許可ではない。**

⚠ R-SEQ = **A-first → affected B0/B1 reacquire → その後 #18 裁定**
（charter §14 TOP PREMISE :3 + §14.9。旧「#18 impl 先行」は SUPERSEDED）。
`#18` は相互作用があるが **GATE ではない**（charter design §0.3）。

## 5-A. ⚠ 2026-07-21 Rs 裁定 B — 本 node の goal 範囲が縮小

Rs 逐語 2 段「**kinematic は使用するなよ**」→「**ただし、クリップのケーブル固定だけは kinematic を使用する**」（適用範囲確認に Rs「ok」）。⇒ **2026-07-19 の「kinematic 完全削除（pin 含む）」を上書き**し、**clip-retention pin 例外が復活**（`RS71-System-Spec-SSOT.md:27` §0#5 の状態へ復帰）。

- **除去対象から外れた** = クリップのケーブル固定 pin のみ
- ⛔**除去対象のまま** = 腕関節角の直接書込 / 指の kinematic close / FK→physics の body 複写（`update_kinematic_bodies`）/ weld・attachment
- ⇒ **census 35 の各サイト class を再判定する必要**がある（**class 裁定 = 設計軸**。本 node の custody では行わない）
- custody = `STEP43_CONTROLLER_REALIZATION_BASELINE_RSTECHLEAD_20260721.md` sha256 `f1ea5e5a0109` @ c69 `183c1bb5dc`
- ⭐**rule-file 反映 = `35029056bd`**（2026-07-21 02:05・`CLAUDE.md:72`・p4・Rs 承認）。⚠p4 relay の前提「:72 は pin も禁止していた」は **on-disk と不一致**（:72 は 07-19 07:32 以降ずっと「唯一の認可例外 = clip-retention pin」を保持・directive 期間中 無変更）⇒ 本 commit = 復元ではなく **明確化**。⚠**逐語 mismatch**（:72 の「ケーブルクランプ」は repo 内で当該行のみ／banked 逐語 = 「ケーブル固定」）= owner Rs/p4 へ訂正要請。詳細 = LEDGER §governance 裁定 B 項（§4 に従い本 state.md へ複製しない）

⚠⚠**node ID `…-Kinematic-Pin-Complete-Removal-…` の「Pin-Complete」部分は、本裁定により実態と食い違う**。ただし **NEST §1 で node ID は永続**ゆえ改名しない。**ID を goal の要約として読まないこと** — goal は上記のとおり縮小済。

## 6. 現在地（起票時点 2026-07-20 20:01）

**step2 = CLOSE / step3 = docs-records-only OPEN**（pN final readback 16:52:34）。
step3 で許可されるのは manifest v2.x + ruled-class 差替 prereg の authoring / bank / readback のみ・
disposition / status だけ・**census = 35 固定**。
