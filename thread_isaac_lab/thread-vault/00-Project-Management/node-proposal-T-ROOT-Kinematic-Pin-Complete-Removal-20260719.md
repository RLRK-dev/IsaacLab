---
title: "[DEFINE] node 作成提案 — T-ROOT-Kinematic-Pin-Complete-Removal-20260719"
doc_type: node-creation-proposal
status: PROPOSAL — Rs の node 作成承認 + 起動承認 待ち
drafted_by: w2:p6 (PLAN-KEEPER)
drafted_at: 2026-07-20T19:48:36+09:00
spec: operational-rule-LTM-1.md (LTM-1 v1.2) §2.1 / §3.1
ruling: w2:pN (T-ROOT-OPS-SUPERVISOR-CODEX) NEST 整合裁定 2026-07-20 13:02
---

# [DEFINE] node 作成提案 — task (d) kinematic / pin 完全削除 arc

## §0 本提案が **していない** こと（fence — pN 裁定 13:02 準拠）

本 file は **提案のみ**。Rs 承認まで以下は一切行っていない。

- ⛔ node folder (`thread-vault/T-ROOT-Kinematic-Pin-Complete-Removal-20260719/`) を作成していない
- ⛔ `project-tree-manifest.md` に行を追加していない・`T-ROOT` の `children_nodes` に edge を張っていない
- ⛔ status を `IN_PROGRESS` にしていない（提案上の初期値 = `PENDING`）
- ⛔ 既往 session を遡及して捏造していない（§3 の `adopted_existing_arc` provenance として記録するのみ）

**Rs 承認後に初めて**、folder + manifest 行 + `T-ROOT` edge を **atomic に**起票し、その時点から `IN_PROGRESS`。

## §1 起票の根拠（なぜ node が要るか）

task (d) は 2026-07-19 以降の新 task でありながら、**tree 上に存在しない**。現状の可視面は
`07-Design/00-DESIGN-STATUS-LEDGER.md` の (d) 行と `§DDR #25` のみで、`project-tree-manifest.md §2` には
arm-control / control-method / kinematic のいずれの行も無い（p6 実測 2026-07-20）。

一方で本 arc は既に **独立 goal・多 session・repo 横断 scope・HALT/acceptance 条件・p4/p5/pN/p6 の分業**を
持つ。LTM-1 §0 / §2 / §6 の下では LEDGER + DDR だけでは **構造的に不可視**であり、
親 COMPLETE の cascade 判定（§3.3 #6 / §3.5）が本 arc を参照できない。

⚠ 対照として `T-ROOT-RS-TECH-LEAD` は **role label であって node ではない**（pN 裁定）。
非対称は意図的であり、本提案は **role label の起票ではなく、goal を持つ実 task の起票**である。

## §2 8 必須要素（LTM-1 §2.1）

| # | 要素 | 提案値 |
|---|---|---|
| 1 | **node ID** | `T-ROOT-Kinematic-Pin-Complete-Removal-20260719` |
| 2 | **goal** | §2.1 参照 |
| 3 | **means** | §2.2 参照 |
| 4 | **status** | `PENDING`（Rs 起動承認で `IN_PROGRESS`） |
| 5 | **parent_node** | `T-ROOT` — §2.4 に判断の根拠と Rs 確認事項 |
| 6 | **children_nodes** | `[]`（leaf 起票）— §2.3 に将来の分割方針 |
| 7 | **dependencies** | §2.5 参照（`precedent` / `blocker` のみ） |
| 8 | **session_history** | `[]`（初 session = `#s1` は Rs 承認後）— 既往は §3 provenance |

### §2.1 goal（1 文 + 検証可能条件）

> **active 実行面から kinematic / pin による物理バイパスを完全に除去し、physics-faithful な制御へ置換して、
> `RS71-System-Spec-SSOT.md` §0 不変前提 #3（DiffIK-only）/ #5（no-kinematic-trick）が
> 機械検証で成立する状態にする。**

**検証可能条件**（すべて既存 SSOT に接地。本提案は新しい acceptance を発明しない）:

1. **Layer 8 canonical census = 0** — F3 で拡張した all-root scan（全 `thread_isaac_lab` Python root）基準。
   現在地 = **35**（内訳 = A 27 + D aerial 5 + skills-snapshot 3。census 128→35 は c19-c23 実行の結果）。
   ⚠ 旧 restricted-root 基準の「128→125」とは **別 measurement surface**。版を明示せずに引用しない。
2. **guard が fail-closed** — 既知=WARN の baseline 廃止済（`scripts/validations/check_control_method.sh`）。
3. **各 chunk が two-key** — 機構軸（p5）+ 証拠軸（pN）。片軸 PASS は充足でない。
4. **各 stage が charter §6 の gate を通過** — L3 chain + Rs sign-off + **video leg**。
5. **landing / HALT 解除は本 goal に含まれない** — 別 GO（§4 の authority fence）。

### §2.2 means（leaf 内 action description）

charter `ARM_CONTROL_REMEDIATION_D_CONTROLDESIGN_VTDESIGN_20260719.md`（現行 **v2.25** = c42 `01d3011f5e`）の
stage 定義に従って実行する。現在 identified な workstream:

- **GATE-MIGRATE** — Fingertip Z-Check Gate を env7-mujoco へ移植 → 検証後に VBD copy を retire（Rs 裁定 c36）
- **B0B1-MIGRATE** — B0/B1 evaluator を env7-mujoco へ移管（Rs 承認済）。⚠ 旧 artifact は
  **HISTORICAL / NOT_COMPARABLE** ゆえ **fresh 再取得が必須**
- **A-group rewrite** — routing_utils / clip_routing（残 27）。⚠ 現 `routing_utils` は
  inv_mass・inertia = 0 / arm POSITION wiring・qd map 無 / clip runner は no-PD control ⇒
  **target write helper 単独では物理駆動不能**（pN c29 R2 = CRITICAL）
- **D aerial**（残 5）/ **skills-snapshot**（残 3・disposition = **DELETE 確定**、c27 `bfc35ca87c`）

⚠ **GATE-MIGRATE と B0B1-MIGRATE は別 workstream**（p4 2026-07-20 16:54）。単一 task に畳まない。

### §2.3 children_nodes = `[]` で起票する理由

workstream は上記のとおり既に分離しているが、**子 node 化は本提案では提案しない**。
理由 = 子 node 作成は §3.1 の別 gate であり、親 node の起票と同時に決めると
「親の承認で子まで通った」形になるため。分割が必要になった時点で §3.1 を再帰適用する。

### §2.4 parent_node = `T-ROOT` — 判断根拠と ⚠ Rs 確認事項

pN 裁定（13:02）が `T-ROOT` を指定。理由 = **scope が route / WMSO / scripts を横断する**ため、
route 系の子にすると scope を実際より狭く見せてしまう。

⚠ **確認いただきたい点**: Rs 優先順位裁定（2026-07-20 13:04:29）は
「**(d) は WMSO-enabling な前提・carry であって競合する top-level goal ではない**」とする。
p6 の判断では **両者は両立する** — 優先順位裁定は *順序付け* の話、parent は *tree 構造* の話で軸が異なる。
よって本提案は「**parent = `T-ROOT`（構造）＋ WMSO への従属は goal 記述と carry で表現（順序）**」とした。
**この解釈が Rs 意図と異なる場合、承認時に parent を差し替えてください。**
（構造と順序を混同すると、後で親の付け替えが必要になるため明示的に書いた。）

### §2.5 dependencies

- **precedent（完了必須）**: なし。本 arc は既に進行中の作業を採録するものであり、
  完了を待つべき先行 node は識別されていない。
- **blocker（並行制約）**:
  - `DDR #25` carry ① — Z-Check gate の env7-mujoco 移植が未実装（VBD retire は移植検証後）
  - `DDR #25` carry ② — B0/B1 旧 artifact = HISTORICAL / NOT_COMPARABLE ⇒ fresh 再取得必須
  - `DDR #25` carry ③ — `CLAUDE.md` `:271`（Z-Check Gate）/ `:85`（test 参照）は
    **移植検証後に Rs 承認で更新予定・現在未更新・CC は編集しない**
  - `DDR #26` — P0 substrate defect（隠れ綱引き）: banked evidence の継続利用可否
- ⚠ **`#18`（grip-efficacy SRG）は相互作用があるが GATE ではない**（charter design §0.3）。
  R-SEQ = **A-first → affected B0/B1 reacquire → その後 #18 裁定**
  （charter §14 TOP PREMISE :3 + §14.9 による。旧「#18 impl 先行」は SUPERSEDED）。

## §3 provenance — `adopted_existing_arc`（遡及 session 捏造の禁止）

本 node は **既存 arc の採録**であり、既往作業を session として遡及生成しない。
`session_history` は空で起票し、初 session は Rs 承認後の `#s1`。

既往の実体は以下を **provenance として参照**する（node の成果ではなく、node 化以前の記録）:

- **chunk chain c4 … c48**（`probe/pd1-arm-pd`、2026-07-20 19:48 時点 tip = `bb68cb3c0f`）
  — ⚠ 本 branch（`rlrk/optE-s2-substrate-swap`）には **未着地**
- **判定 SSOT** = `07-Design/00-DESIGN-STATUS-LEDGER.md` (d) 行 + `§DDR #25`
- **設計 SSOT** = charter v2.25（c42 `01d3011f5e`）
- **Rs 裁定** = c36 `eefad77773`（逐語「1：a 2:承認」）
- **現在地**（pN final readback 2026-07-20 16:52:34）= **step2 CLOSE / step3 = docs-records-only OPEN**

## §4 SSOT の分担（二重管理の防止 — pN 裁定）

- **結果・判定は LEDGER (d) 行 + DDR #25 + 設計 doc が SSOT のまま**。node state.md へ複製しない。
- **node state.md が持つのは lifecycle / goal / pointers のみ**。
- ⛔ **authority fence（node 化で一切変わらない）**: source / `[CHANGE]` / RUN / landing / push /
  training / `CLAUDE.md` 編集 = **CLOSED**。step4 以降は step3 two-key + 別 GO まで不可。
  **node を起票することは実行の許可ではない。**

## §5 prior-art / no-repeat disposition

`scripts/check_thread_vault_prior_art.sh` は本 keyword 群で blocker context を返す（pN 実測 30 件）。
pN 裁定の disposition = **本件は失敗経路の再実行ではなく、Rs 指示による governance visibility の是正**。
実験・source 変更は伴わない（本提案は文書のみ）。

## §6 Rs にお願いする承認（2 件・LTM-1 §3.1 #4）

1. **node 作成承認** — 上記 8 要素での起票可否（⚠ §2.4 の parent 解釈を含む）
2. **起動承認**（`PENDING` → `IN_PROGRESS`）— §3.1 では別 gate

承認後の p6 執行手順（atomic・explicit-path commit）:
folder + `state.md` 配置 → `project-tree-manifest.md §2` を生成器経由で再生成 → `T-ROOT` edge →
`status: IN_PROGRESS` → sidecar hash pin。
