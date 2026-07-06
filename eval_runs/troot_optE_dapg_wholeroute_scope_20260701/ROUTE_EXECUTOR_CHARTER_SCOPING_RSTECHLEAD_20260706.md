# P2 部品② route-executor — CHARTER SCOPING ([DEFINE]/[L-TRIAGE]/scope) — 2026-07-06

**Author:** RS-TECH-LEAD (%12). **Date:** 2026-07-06 23:2x JST.
**Status:** PAPER-ONLY / 0-build / 0-commit-of-code (本 doc = charter [DEFINE] 審議物、env-core `P2_ROUTE_ENV_SPEC_INPUT_W0C` と同型の spec-input)。**env/reward/route-lock = Rs 専権** — 本 doc は design-gate + 5体 [VERIFY] への INPUT。
**Authorization:** staged build charter 発行授権 = Rs W0-a′ v1.1 一括承認 (LEDGER `LADDER v2` 行、`b7d7857dfc`; chain = env-core→**route-executor**→oracle→OG→trainer)。

## §0. Grounding (anchor set、§運用4 hard gate)

| Anchor | Cite | 使用 fact |
|---|---|---|
| 成否 SSOT | LEDGER `LADDER v2` 行 (`e48facd37d`) | env-core COMPLETE / staged chain / route-executor = 第2 component |
| banked spec | `P2_ROUTE_ENV_SPEC_INPUT_W0C` v1.5h §7:102 + §2-F2 + §5 | route-executor = `_run_mujoco_grasp_route` monolith の importable/phase-indexed/resumable 抽出 (byte-repro 必須) / state-bank fork (b) / oracle は**別 stage** |
| env-core build plan | `BUILD_PLAN_ENVCORE_COORD_20260706.md` §6 + §2:23-24 + §12 CC5-2 | stub 契約 v1 (reset_to_phase / step_target / grip 2-vec / is_dual_grip boolean / recorded-target-replay) + DoD⑦/⑨b/⑬ carry |
| 8 blocking carry | env-core node `state.md:62-71` (COMPLETE 節) | route-executor が discharge する 8 項の正式列挙 |
| locked runner 実体 | `scripts/test_newton_clip_routing.py:3692` (fn 2476L / file 8458L) | ⛔ ANTI-REVERT Rs-LOCKED 2026-07-01 marker (:1781) = 0.716 MOTION STANDARD source |
| goal 上位 | `SOMA.md:37` (100% qualitative) + `:717` (No T-ROOT 95% claim) | route-executor は whole-route 実 route engine、SR claim は上位 campaign |

## §1. [DEFINE]

- **goal (検証可能):** env-core (MDP skeleton、obs 62D / α-6D residual / G1-G6 predicate) が stub interface で受けている **route** を、locked `_run_mujoco_grasp_route` (0.716 canonical) を source とする**実 route engine** に置換する。成功 = env-core node の 8 blocking LOUD-CARRY のうち route-executor 段で構造的に discharge 可能な項を close + **canonical byte-repro** (0.716 baseline が抽出後も byte-identical 再現)。
- **means (leaf action):** stub 契約 v1 (§5) を満たす route module を build。core = (a) `reset_to_phase(k)` = precomputed phase-k state-bank (spec §2-F2 (b)) / (b) `step_target(t)` = 実 route の per-step base 絶対 target + phase_id + grip_cmd / (c) recorded-target-replay mode (CC5-2 iii) / (d) 実 C2 groove scene 建設 + 実 grip force。**byte-repro regression = 全 DoD の前提 guard。** locked runner への関与方式 = **§6 D-1 (Rs 決定)**。
- **success (DoD 提案、§運用29 predicate-completeness):** ①**byte-repro**: 抽出 route で canonical 81-grid → strict_v2 **58/81 EXACT** (env-core ⑨a′ の recorded-state 25/81 proxy を live で 58/81 に引き上げ) ②**⑦ handover-fidelity**: reset_to_phase(k) の qpos/qvel L∞ ≤ 提案 1mm / 1mm/s ③**⑨b online-numerator**: residual≡0 × 81 live → 58/81 (live earned-clock + contact + physics) ④**⑥ 6-phase full-fire live** (実 grip で cable carried) ⑤**58/81 wall/spacer exact predicate** (mjModel geom introspection、center-dist≤3.5mm proxy → wall-dist≤0.5mm spacer-excluded) ⑥**C2-seating 動画 gate** (Rs 約束済、実 C2 groove scene) ⑦**CABLE_XY_OFFSET per-cell wiring** ⑧**⑬ enabler** (recorded-target-replay + C1-escape non-vacuous cell 供給)。**分子 conjoin = strict_v2 (C1-retention + C2-seat 両 leg)。cover しない leg = trainer 段 (policy 学習成果) は本 node scope 外。**

## §2. [TASK] — node proposal (§3.1 子 node 作成 gate)

- **提案 node ID:** `T-ROOT-optE-route-dapg-C1C2-P2-routeexec` (parent = `T-ROOT-optE-route-dapg-C1C2`、env-core `-P2-envcore` の sibling)。
- **NEST placement:** parent の `children_nodes` に追加 (現 = `[...-P2-envcore]` のみ、`state.md:12`)。1:1 bind builder = %11 (再 bind、env-core と同)。
- **⚠ §3.1 gate:** 子 node 作成は §運用2 [DEFINE] 起動承認とは**別 gate** (CLAUDE.md NEST 注記)。staged chain は W0-a′ で authorized ゆえ formal tick だが、node 作成は本 proposal の Rs 承認で発効。

## §3. [L-TRIAGE] — L3 (自動昇格 confirmed)

- **path/keyword hit:** `_run_mujoco_grasp_route` = newton / mujoco / ik / solver / physics + `phase`/`_reset_worlds` (state-bank) + reward/success predicate (G1-G6 live) → §0 L3 diff-keyword 該当。
- **規模:** 実 route engine + 実 scene + state-bank ≥ 数百行、複数 file (route module + config + 接続) → >200 行 / ≥3 file 見込 = L3 定量該当。
- **FOUNDATIONAL INVARIANT check (最優先):** 本 node は §0 不変前提 (DUAL-ARM / 88mm span / DiffIK-only / gripper geometry / no-kinematic-trick) を**変更しない** — byte-repro が invariant 保存を構造 enforce (抽出は挙動不変が前提)。⇒ 即 STOP case には**非該当**、ただし Rs-LOCKED code 関与ゆえ high-care L3。
- **gate 帰結:** design-gate (直交) + 5体 [VERIFY] (L2 以上) + 層5 (L3) + 事後 debate (L3)。env-core と同型 chain。

## §4. scope partition — route-executor が owns / 後段へ defer

**route-executor owns (8 carry のうち 7 + ⑬ enabler):**
| carry (env-core state.md:64-71) | route-executor での discharge 機構 |
|---|---|
| 1. 58/81 wall/spacer exact-split | 実 C2 scene の mjModel geom introspection (spacer-excluded wall-dist) |
| 2. ⑥ 6-phase full-fire live | 実 grip で cable carried → G2-G6 live fire |
| 3. CABLE_XY_OFFSET per-cell | 実 route が per-cell offset を消費 (DR/⑨b 前提) |
| 4. real grip force | finger 実 actuation (grasp/lift/drop/retention 物理) |
| 5. ⑨b online-numerator | residual≡0 × 81 live → 58/81 |
| 6. ⑦ handover-fidelity | reset_to_phase(k) state-bank の qpos/qvel L∞ |
| 7. C2 groove + C2-seating 動画 | 実 C2 groove scene 建設 + 動画 gate |
| 8. ⑬ enabler | recorded-target-replay stub upgrade + C1-escape non-vacuous cell |

**後段へ defer (route-executor scope 外、loud):**
- **oracle API** (spec §5、~300-500 LOC): per-step relabel + settle re-center + in-scene IK → **oracle stage** (route-executor の次)。
- **OG 計器** (spec §6): port + composite γ⊥ + 再検証 → **OG stage**。
- **trainer 統合** (spec §7): α 交互 aux imitation + ⑫ projection-accounting + phase-conditioned σ + P4 pre-reg + curriculum start-mix → **trainer stage**。
- **⑬ の VERDICT 実行** (residual≠0 → G6==strict_v2): enabler は route-executor、**実行 stage = §6 D-2 (route-executor 合成摂動 vs trainer 実 policy)**。

## §5. core deliverable — stub 契約 v1 (env-core が既に期待、build plan §6)

```
route.reset_to_phase(k) -> None      # precomputed phase-k state-bank (spec §2-F2 (b))、qpos/qvel 復元 = ⑦
route.step_target(t) -> (target_6d,  # 実 route の per-step base 絶対 target (fork-(iv) 6D abs、非累積)
                         phase_id,    # G1-G6 live clock (base-owned)
                         grip_cmd)    # scripted 2-phase servo (action に gripper 次元なし)
# + CC5-2: per-arm scheduled grip 2-vector / is_dual_grip_window boolean (base script single-source) / recorded-target-replay mode
# byte-repro regression: 抽出 route が 0.716 canonical を byte-identical 再現 (先祖返り guard、[[feedback-port-task-faithful-to-intent-not-deleted-impl]])
```

## §6. ⭐ Rs 決定項

### D-1 (核心): locked runner 関与方式 — Rs-LOCKED code への touch 可否
`_run_mujoco_grasp_route` (⛔ ANTI-REVERT Rs-LOCKED、0.716 source) を stub 契約に載せる 3 案:

| 案 | locked file | live route (⑨b) | drift risk | 評 |
|---|---|---|---|---|
| **A** wrapper/recorded-replay + state-bank | 不触 (最安全) | ✗ open-loop replay のみ (⑨b live 不能) | なし | carry 一部が deferred のまま残る |
| **B** in-place refactor → importable/resumable | **編集** (lock 例外要) | ✓ 完全 | なし (単一 SSOT) | 最クリーンだが Rs-LOCKED 編集 = Rs 承認必須 |
| **C** faithful 抽出 → 新 module + byte-repro guard | 不触 (lock 尊重) | ✓ | 中 (二重 SSOT、byte-repro で緩和) | lock 尊重 + live 両立、drift を byte-repro が捕捉 |

**%12 推奨 = C** (lock を尊重しつつ live route 両立、byte-repro regression が先祖返りを機械捕捉; locked runner = reference oracle / route module = production engine の SSOT 分離)。ただし **B (単一 SSOT) が Rs 方針なら lock 編集を承認いただければ最短**。**A は ⑨b live-numerator を discharge できず carry が残る**ため単独 non-recommend。**決定 = Rs 専権** (Rs-LOCKED code 関与ゆえ)。

### D-2: ⑬ adversarial-numerator の VERDICT 実行 stage
recorded-target-replay + C1-escape cell 供給 = route-executor。residual≠0 rollout の実行 = (a) route-executor で合成摂動 / (b) trainer で実 policy。**推奨 = enabler を route-executor で用意、VERDICT は trainer stage に defer** (実 policy が自然な非空 source)。

## §7. gate chain plan (env-core precedent、各 ≤~800 行 L3)
[DEFINE ✓ (本 doc)] → **D-1/D-2 Rs 決定** → build plan 起草 (%11) → [DESIGN-GATE] (`/reward-design` は route/predicate 不変ゆえ軽 / `/geometric-design` C2 scene / `/pre-check`) → %12 checkpoint → [VERIFY] 5体 → [RULE-CHECK] → build → smoke (byte-repro + ⑦ + ⑨b) → 層5 + 事後 debate → **C2-seating 動画 gate (Rs)** → node COMPLETE。

## §8. risks / conservatism carries
- **Rs-LOCKED file 関与** = 最大 risk (先祖返り class)。byte-repro regression = 一次 guard、D-1 が touch surface を決める。
- **byte-repro の device 依存** ([[project-canonical-route-device-fragile-cpu-vs-cuda]]): cuda:0 canonical のみで byte-repro 判定 (cpu = read-only proof)。
- **namesake hazard** ([[reference-test-newton-legacy-vs-production-route-namesake-functions]]): production `_run_mujoco_grasp_route` を cite、legacy 同名関数を混同しない (C 案で特に)。
- **C2 groove scene 3mm proxy** = 剛体 clip 非保守 (spec §8 carry 承継)。
- **oracle/OG/trainer は本 node 非該当** — SR/学習成果 claim は route-executor では出さない (over-claim 禁止)。

*%12 — 2026-07-06。PAPER-ONLY。INVARIANTS 不触。D-1/D-2 = Rs 決定待ち。*
