# DQ7 (iii) DAgger scoping — OPS-SUPERVISOR (%9) independent cross-PV (major design input, pre-Rs)

**Written: 2026-07-03 18:20 JST (same-turn `date`).** Author: %9 OPS-SUPERVISOR.
**Object:** `DQ7_III_DAGGER_SCOPING_COORD2.md` (%10) + %12 review(SOUND、commit 0841c2f17b、1 citation flag)。
**Note:** 私の expert-dependency 核心が組み込まれた doc ゆえ、その operationalization を特に精査。非 block。0-commit / rollout 禁止 / read-only + this file + log.md。

## 0. Grounding — code claim を独立裏取り

| claim | 独立検証 | 結果 |
|---|---|---|
| **{0-3} = frozen-target**(expert perturbation-invariant の根拠) | {0-3} hook 領域 `test:3888-3932`(post-build)を grep → **per-frame cable argmin / cbq / cable_xyz なし** | ✅ frozen-target 確認({11} grip-lane argmin と対照) |
| **citation flag**(%12) | `test:2805` = 「Targets are wrist_3 world Z (**no cable in this infra smoke**)」= infra-smoke(probe_smoke_geom、table-clearing) | ✅ %10 の :2806-2808 は誤 cite、**claim SOUND / cite wrong**(production `_run_mujoco_grasp_route` {0-3} を cite せよ; banked memory `reference-test-newton-legacy-vs-production-route-namesake-functions` と一致) |
| LOCKED markers {11} 領域 | 既確認(:4477/4493/4593 = C2_REGRASP、{0-3} scope 外) | ✅ DAgger {0-3} は LOCKED から構造的に clear |
| (ii) baseline γ⊥ | 既 §運用28 独立抽出(CP-(ii)-5): {0}1.744/{1}1.056/{2}1.055/{3}1.034 | ✅ §9 baseline 一致 |

**prior-art(%9 独立確認)**: %10 の「THREAD 初 DAgger、blocker 全 self-referential + un-executed LoRA fallback」= §2 disposition 妥当(genuine prior DAgger failure なし)。

---

## 1. 判定 (1)-(4)

### (1) coverage-vs-representation crux(§4)— **CONCUR + ~0-GPU capacity pre-test を enhancement 提案**
- **framing は excellent + honest**: optimistic(distribution/coverage: (ii) の injected states ≠ policy 自身の drift 分布 → DAgger が on-policy 分布を match)vs pessimistic(representation-attractor: scale-invariance 2mm≈10mm + 19× collapse が γ⊥≈1 の representation 定着を示唆 → DAgger も plateau)を両論併記、ambiguity を genuinely OPEN と明記、§9 abort で guarded。**「DAgger は state 分布のみ変える(同 expert・同 network)」の理解は正しい**。
- **私の refinement は §4 に既収録**: (ii) は scripted off-path coverage を既提供 → DAgger は「on-policy/distribution-matched coverage が scripted coverage の届かなかった plateau を破るか」を test(§4 optimistic mechanism が正確にこれ)。
- **⚠ enhancement 提案(cheapest-falsifier-first、rollout GPU 前)**: **~0-GPU の representation-capacity pre-test** — fork-(iv) arch を **idealized synthetic restoring set**(phase {1} の obs=ee 摂動 + label=固定 grasp target、on-path budget 競合なし・model-consistency 制約なし)で train(~90s)→ γ⊥ 測定。**capacity FAIL(isolated でも γ⊥≈1)= representation-attractor 確定 → DAgger rollout GPU を spend せず (i) RL へ**(NECESSARY-condition screen)。**capacity PASS(arch は restoring 表現可)= 失敗は data-correlation(ee↔target)→ DAgger の on-policy relabel が correlation を破る → DAgger justified**。(iv) と別物: (iv) は route data に混ぜ budget 競合、本 pre-test は isolated capacity のみ。→ 1.5-5h rollout の前に 90s で pessimistic 仮説を反証可能。§R step 1(rollout-free build)に同梱推奨。

### (2) §9 falsification thresholds — **CONCUR(operationalization 妥当)**
- **私の expert-dependency 疑問を正しく operationalize**: plateau → (i) RL は「expert-weakness か representation か」を問わず正しく route(両者とも plateau → BC-family 尽き → RL)。**かつ {0-3} では expert-weakness は起こりにくい**(§3: frozen waypoint = 復元 label 正当)ため、{0-3} plateau は representation 寄り、{11} expert-weakness は別 thread に除外 = 私の 2-thread 分離と整合。
- **K_min=3 妥当**: DAgger は coverage-limited なら数 round で収束(§5)、3 は marginal trend を見る最小、conjunction(γ⊥>0.7 ∧ 10× collapse ∧ projected>10iter)は 3 signal 要求で premature abort を guard。minor: **projected-iters 外挿は 2-point 線形でなく全 K の robust fit**(noisy γ⊥ の誤外挿回避)。
- **conservatism 方向 正**: OG offline easy → γ⊥≤0.5 = NECESSARY・non-conservative(rollout SR 要)/ plateau>0.5 = conservative-definite FAIL(bank)= CP-(ii)-5 と同 calibration。✅
- **anti-confound(§9)**: null/base composition を iter 間固定(私の CP-(ii)-5 composition-confound 指摘を pre-register 反映)= 採用確認。

### (3) perturbation-invariance SOUND({0-3} frozen-target)— **CONCUR(独立確認)+ citation 是正**
- {0-3} が frozen-target = **独立確認**(§0: {0-3} 領域に per-frame cable argmin なし)。かつ **pre-contact ゆえ cable static**(arm は把持前で cable 非接触)→ entry-derived target が {0-3} 全体で valid frozen → expert は valid **かつ trivial**(stored constant lookup、route 再実行不要 = §3、DAgger が cheap な根本理由)。{11}(grip-lane argmin per-frame = obs-mismatch)と構造的に別 = 除外正当。
- **citation 是正必須**: %10 の :2806-2808 は infra-smoke("no cable in this infra smoke" :2805)→ production `_run_mujoco_grasp_route` {0-3} を cite。claim 不変・cite 誤(%12 flag CONCUR)。

### (4) 別 pitfall — **2 件 + 1 positive**
- **⚠ Pitfall A(%10/%12 未明示、build-item)= reach-infeasible DAgger states**: BC(γ⊥≈1)policy は off-path drift、DAgger は its visited states を収集。canonical route は reach-fragile(cpu 83mm / cuda 0.9mm、memory `project-canonical-route-device-fragile`)→ policy が **IK-infeasible / joint-limit / reach-wall states** へ drift すれば、expert の「go to waypoint」label が un-followable(target 到達不能)→ **D を poison**。§5 の β-mixing(β↓)は早期 near-manifold で partial 緩和だが feasibility filter でない。**追加推奨: DAgger 収集 states に feasibility filter**(expert target が IK-infeasible な state を drop、CP-C validity + fix-⑤ reach-screen 再利用)。B1′ 教訓(unreachable-target ≠ IK-fail)ゆえ「IK 制約で到達不能」state の label は noise。
- **Pitfall B(expert-query 実装)= 解決済を確認**: 私が当初懸念した「imperative expert は clean state→action oracle でない」は **doc §3 が解決**(expert = entry-frozen T*_p の stored constant lookup、route 再実行なし)。これが DAgger を cheap にする核 = well-designed。affirm。
- **⭐ Positive(%9 追加、DAgger の (ii) 超え advantage)**: **DAgger は {2,3}(CLOSE/LIFT)を covers** — (ii) は {2,3} を SKIP(close-servo / WR-drop で injection 不可)だったが、DAgger は rollout で {2,3} states を**自然 visit**(injection でなく policy 実行 → injection-drop risk なし)+ expert relabel(固定 schedule target = valid)→ **{2,3} restoring を教えられる**。これは私が earlier 提起した {2,3} un-injectability の gate-reachability 懸念に**構造的に対応** = DAgger が (ii) を超え得る genuine advantage。§4/§R の case を強化。

## 2. Conservatism(§運用15)
- coverage-vs-representation = genuinely OPEN(doc 明記)= 正しい不確実性表明。
- §9 abort = conservative-definite plateau で (i) へ = bankable。
- capacity pre-test(enhancement)= representation を rollout 前に 0-GPU で反証可能にする conservative front-load。
- cost 見積 = 推測(doc 明記、B1 rollout のみ実測)。

## 3. INVARIANTS
§7 checklist 妥当(独立確認): INV#1 dual-arm({0-3} 両腕 approach)/ INV#2 88mm(CLOSE で set、approach は preserve)/ INV#3 DiffIK(expert=abs target)/ INV#4 コ / INV#5 no-kinematic-trick(rollout=physics)。obs 不変更(DAgger は分布のみ、{11} obs-fix と混同禁止 = §6 明記)。LOCKED は {11} 領域 = scope 外。**全 untouched**。

## 4. OVERALL — **CONCUR: §R(1 instrumented DAgger pass、rollout-free build first、§9 abort、guarded prior、primary=discrimination NOT GO)**

(1) crux framing excellent + **capacity pre-test enhancement**(0-GPU で representation を rollout 前反証)(2) §9 妥当(expert-dependency を正しく operationalize、K_min=3 + conjunction guard、conservatism 正)(3) {0-3} frozen-target 独立確認 + citation 是正 (4) **Pitfall A feasibility-filter 追加 / Pitfall B 解決確認 / {2,3} coverage positive**。

**Rs decision points(§D)への %9 view**: D-1 run DAgger = CONCUR(cheapest、abort が (i) を justify)+ **capacity pre-test を rollout 前 gate に**。D-2 batched Rs-GO + §9 abort cap 妥当。D-3 §9 threshold 妥当(+ robust 外挿 minor)。D-4 β-mixing(safe near-manifold start)推奨 + feasibility-filter。D-5 §9 ABORT 時の (i) 事前授権は Rs 判断(env-build cost = P2 CRITICAL、別 scoping)。

build を要するのは §R step-1(rollout-free、L3-gated); rollout leg は Rs GO(HIGH-COST-GATE 未満だが rollout 禁止解除要)。{11} 別 thread 不変。rollout 禁止・0-commit・band=γ=CP-(ii)-5。

*%9 OPS-SUPERVISOR — 2026-07-03 18:20 JST(書込前 `date`)。INVARIANTS untouched / 0-commit / 編集 = 本 file + log.md。*
