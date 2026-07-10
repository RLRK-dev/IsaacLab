# Vault 設計内容 scatter/重複 監査 — disposition map + 最適化提案

**Author:** COORD2 (%10 / w2:p2)。**Charter:** %12 2026-07-11 04:24（Rs verbatim「設計内容がvaultで散在、重複などないか？あれば最適化して」）。**[DEFINE] GO:** %12 04:27（two-tier / policy-first / prior-art CONCUR）。
**Status:** AUDIT v1.0 — **paper only（0-commit、提案のみ）。** 移動/統合/編集の執行は **per-item Rs 承認後**。07-Design=Rs 専権 + Vault Write Permissions 遵守。
**L-TRIAGE:** L1（read-only survey + eval_runs 分析 doc）。**baseline:** HEAD `909b065b3f`、実測日時 2026-07-11 04:2x-04:3x（全数値は本 session の python 実測パス、下記 §2/§3 に法）。

---

## §0. Scope + method + prior-art disposition

- **Scope（%12 two-tier 確定）:** ①04-Specs（22 .md + DEPRECATED）②06-Knowledge 設計 subset（GD×2 + LL-*-Design×13 = 15、残 88 は Tier-2 screen）③eval_runs 設計 doc（troot_verbal_teaching 13 + troot_optE_dapg 97）④02-Workflow（19）。**Tier-1 = full disposition / Tier-2 = header screen + 設計内容判明時は昇格。**
- **中心論点（P3、policy 先行）:** eval_runs↔07-Design 境界 = live 設計 surface の住処規則（§1）。
- **OUT:** 07-Design 内部（renewal charter `T-ROOT-DesignDoc-Renewal-20260711` owns、二重 scope 禁止）/ SOMA stale（node `04e05a8066` owns）/ RS71（INDEX=正）。**ただし 07-Design を参照する eval_runs doc の重複/drift は IN。**
- **method:** (a) inventory × LEDGER-status join（§2）(b) 重複検出 = reference-over-copy grep + supersession-banner gap（§3）(c) disposition map = renewal §6-2 の 3列 ledger を vault 全体へ一般化（§4）(d) 私 prior AUDIT 残件 fold（§5）。
- **prior-art guard:** 実行済、BLOCKER context = **FALSE-POSITIVE**（hit 元 `eval_runs/r2a_track_a_d0_c4_g1_g3_refinement_0gpu_20260524/D0_C4_G1_G3_REFINEMENT.md:35/42` = RL-Routing の PRODUCT_GO=false / execution・source-mutation・training・product-claim 非授権 の注記、keyword 'vault'/'design' の偶発 match）。本 task = read-only doc-org 監査で実行/訓練/source変更/product主張ゼロ = **別 path** + 新 Rs directive 04:24。→ %12 CONCUR 04:27。continue 授権。

---

## §1. 境界 POLICY 勧告（中心論点、Rs 決定 — dispositions を駆動）

### §1.1 scatter の root cause（実測診断）
**path-rule が「live 設計 surface」と「run evidence」を区別しない** → eval_runs に両者が混在し、**Tier-1 設計 doc 67本中 51本が LEDGER 未追跡（§2）= どれが current / superseded / historical か doc を開かないと不明**。renewal CC3-C4 も同所見（工程表 CANONICAL_MOTION_TABLE 自体が eval_runs 在住の live 設計 surface）。

### §1.2 policy options（Rs 決定項）

| # | option | 効果 | cost / risk |
|---|---|---|---|
| A | 全 live 設計を 07-Design へ移設 | canonical 集約 | Rs-専権ゆえ高速反復が Rs bottleneck / mass-move が 48-file cite web を破壊 |
| B | 専用 live-design dir 新設（05-LiveDesign 等、07-Design より軽い governance + LEDGER 追跡） | evolving 設計 vs run evidence を物理分離 | 新 dir + 移設 churn / cite 更新 |
| **C** | **tracking-by-LEDGER + frontmatter tag**（位置不変、全 design-content doc に LEDGER 行 + `doc_class` tag 必須化） | **51 untracked→tracked を移設なしで解決**（cite 破壊ゼロ）、境界を機械判定可能に | tag 付与作業（軽）/ enforcement hook |
| D | status quo | — | scatter 継続 |

### §1.3 勧告（labeled — 方式決定 = Rs）
**推奨 = C を base に、B-lite + supersession-banner を組合せ（lowest-regret、mass-move 回避）:**
- **PR-1（最優先・最安）:** **live 設計内容を持つ全 doc に LEDGER 行を必須化**（位置に依らず）→ 51 untracked を tracked 化、「どれが current か」を移設なしで解決。判別のため frontmatter `doc_class: design-surface | run-evidence | reference` を付す（境界を machine-determinable に）。
- **PR-2:** **canonical 化した（反復停止した）設計のみ 07-Design へ Rs授権 flow で昇格**。eval_runs は WORKING 設計 + run evidence を保持（renewal §5.6「設計基盤 pane が canonical surface を保持」と complement）。
- **PR-3（reference-over-copy）:** task_config 等 SSOT 値は **pointer-cite（file:line）必須、bare-restate 禁止**。§3.2 の copy-violation 候補を per-lineage disposition で flag（mass-edit しない）。
- **PR-4（supersession banner）:** superseded 設計 doc に banner + LEDGER SUPERSEDED 行（renewal ARCHIVE-banner pattern の一般化）。
- **⛔ 非推奨 = A の mass-move**（48-file cite web 破壊 + Rs bottleneck）。tracking-by-LEDGER が真の lever。

---

## §2. Inventory × LEDGER-status（core finding）

**GRAND = 254 .md / 4 bucket**（charter '~32'・私初見 '~49' いずれも過小 — 06-K 103 が件数支配、うち 88 は非設計）。

| bucket | total | Tier-1（設計、full disp） | Tier-2（screen） | 備考 |
|---|---|---|---|---|
| ①04-Specs | 22 | ~10（design-content） | ~12（registry/index/roadmap） | name 判定不可（location=spec）→ content 分別。RS71/SOMA=OUT |
| ②06-Knowledge | 103 | 15（GD×2+LL-Design×13） | 88（lessons=knowledge、screen） | LL-* の多くは lessons ≠ 設計 |
| ③eval verbal | 13 | 7 | 6（debate/verdict/approval=evidence） | 工程表 = 設計 surface（境界事例） |
| ③eval optE | 97 | 45 | 52（result/report/crosspv=evidence） | **1 node の設計進化 scratchpad（§3.1）** |
| ④02-Workflow | 19 | ~1 | ~18（protocol/handoff） | name-hit 3 は false（handoff/plan） |

**⭐ core finding — LEDGER coverage（実測）:** Tier-1 設計 doc **67本中 tracked=16 / UNTRACKED=51**。→ **51本は supersession-status 不可視**（scatter/重複の中核）。untracked 51 の主群:
- **06-K vision/L1 設計 family 14本**（LL-Vision-* 9 + LL-BaseAdapter/Cascade-C×2/L1-B-Routing/Orchestration 5）= vision pipeline 設計群が丸ごと untracked。
- **optE 設計 lineage 群**（DQ7×6 / B-BC×4 / COMP3×6 / P2×4 / P3×2 / BUILD_PLAN×3 / W0-a'-W0-e packet 系 / ST2×2 / SLOT/SRG…）。
- RENEWAL_PLAN_07DESIGN.md（sibling renewal charter の doc 自体 — renewal owns、参照のみ）。

---

## §3. Scatter/重複 findings（4 class）

### §3.1 supersession-lineage scatter（最大 cluster）
**eval optE の 45 design-named = 1 node（route-dapg-C1C2）の設計進化が 45 file に分散。** filename-version family は 2 のみ（`B_EVALUATOR_PRECHECK{,_R2}` / `dq7_ii_mini_spec{,_v2}`）= 重複は **content-level lineage**（別名で supersede）。実 distinct 設計 lineage ≈ **8-10**:

| lineage | files（代表） | 現状 |
|---|---|---|
| DQ7 off-path 教師 | DQ7_OFFPATH_SCOPING / III_DAGGER_SCOPING / DAGGER_BUILD_SPEC{,_V2_MINIMAL} / dq7_{capacity,ii,ii_v2,iv}_mini_spec / minitest_verify_packet | R1 CLOSE（LEDGER row47）→ 全 historical、banner 要 |
| B-BC imitation | B_BC_IMITATION_SCOPING / B_BC_BUILD_SPEC{,_DEBATE_R1} / B_EVALUATOR_PRECHECK{,_R2} / B0_BUILD_REPORT / B2_KICKOFF_SPEC / b2_{fix5_geometric,runner_v2} | superseded by ladder v2 / envcore、banner 要 |
| COMP3 route-exec | COMP3_{DRIVEPATH,FORCE,GEOMETRIC×2,PLAN,REWARD,RULECHECK}_* | route-exec node ACTIVE（一部 live）|
| P2 env-spec/reward | P2_{ENVSPEC_5TAI_DECIDE,REWARD_DESIGN,REWARD_ARTIFACTS,ROUTE_ENV_SPEC_INPUT} | env-core COMPLETE（LEDGER row47）→ 一部 historical |
| P3 recorder | P3_{DEMO_RECORDER_SPEC,RECORDER_BUILD_REPORT} | LEDGER row44 tracked ✓ |
| route-exec build plan | BUILD_PLAN_ROUTEEXEC{,_LAYERB} / BUILD_PLAN_ENVCORE / ROUTE_EXECUTOR_CHARTER_SCOPING | 一部 ACTIVE |
| W0-a'/W0-e packet | RS_W0APRIME_PACKET / RS_W0E_PACKET_V1_1 / W0APRIME_..._CROSSPV / W0E_{GEOMETRIC_DESIGN,SEAT_GUIDE_OFFSETFOLLOW_SPEC} | W0-e CLOSED（LEDGER row47）→ historical |
| ladder/devplan | BCRL_DEVPLAN_LADDER_V2 | LEDGER row47 tracked ✓ |
| VT canonical | CANONICAL_MOTION_TABLE_V1（verbal dir）| ACTIVE 設計 surface（境界事例）|
| SLOT/SRG | SLOT_REDESIGN_STUDY / SRG_PROBE_DESIGN_DRAFT | live probe 設計 |

→ **consolidation:** lineage 内の superseded 版に PR-4 banner + LEDGER 行、current 版のみ live 明示。移設ではなく **status 可視化**が主対処。

### §3.2 reference-over-copy（SSOT 値の散在）
scope 254 file 中、task_config SSOT 値の出現数（実測）:

| 値 | 出現 file 数 | sample 判定 |
|---|---|---|
| 88mm / 0.044（span, INV#2） | 48 | 広範（多くは legit pointer 見込み） |
| SR 0.716 / 58/81 | 18 | — |
| 0.7407（DRIVER_CLOSE） | 12 | **sample: on-line pointered 5 / bare-on-line 6**（bare = copy-violation 候補の保守上限、doc 内他所 pointer の可能性残）|
| 1.0668（z_grasp） | 10 | — |
| 0.809（GROOVE_CENTER_Z） | 9 | — |
| RUN1_REF sha 5f1c3f92 | 8 | — |

→ **finding:** SSOT 値が広く restate されている。0.7407 sample で ~半数が on-line pointer 無し = **reference-over-copy 違反候補**（PR-3 対象）。full copy-vs-pointer 分類は L1 over-scope → **per-lineage disposition 時に flag + spot-audit follow-on** を推奨（silent に「違反ゼロ」と断じない）。

### §3.3 untracked-design（supersession-banner gap）
§2 の 51 untracked = PR-1/PR-4 の直接対象。特に **06-K vision 設計 14本**は LEDGER に 1 行も無く、current/superseded 判別が doc-open 依存。

### §3.4 04-Specs の design vs reference 混在
22本中 design-content ~10（Cable Physics Parameters / IK Solver Configuration / Dual-Arm Reaching / Unified Policy Architecture / Vision Pipeline / Phase E-G Design Stock / Camera Backend / Deterministic Core-Stochastic Shell / NFRCP-THREAD / Robot Parameters）/ reference ~12（SSOT Registry / RUN Metrics / Testing Progression / *Roadmap / Crystal9-Mapping / Validate Script Spec / Gate System / SUBLIMATE 等）。design-content の LEDGER 追跡状況は個別確認要（多くが 04-Specs = 旧 spec stock、stale 可能性）。

---

## §4. Disposition ledger（renewal §6-2 3列 一般化、lineage/bucket 単位）

> 254 個別行は L1 over-scope ゆえ **lineage/bucket 単位**。列 = {disposition ∈ correct-location / relocate候補 / duplicate-of-X / stale-flag / by-design-evidence} × decided-by。**全て提案 — 執行 = per-item Rs 承認。**

| item（lineage/bucket） | 件数 | disposition（提案） | decided-by |
|---|---|---|---|
| optE DQ7 lineage | ~9 | **stale-flag + PR-4 banner + LEDGER SUPERSEDED 行**（R1 CLOSE 済、historical） | Rs（07-Design/LEDGER 編集 = Rs授権） |
| optE B-BC lineage | ~8 | **stale-flag + banner**（ladder v2/envcore で superseded） | Rs |
| optE W0-a'/W0-e packet | ~6 | **stale-flag**（W0-e CLOSED、historical run 設計） | Rs |
| optE COMP3 / route-exec / build-plan | ~12 | **by-design-evidence（一部 ACTIVE）**→ current 版に PR-1 LEDGER 行、旧に banner | %12/Rs |
| optE P2/P3 env-core | ~6 | P3=correct（LEDGER tracked）/ P2=stale-flag（env-core COMPLETE） | Rs |
| VT CANONICAL_MOTION_TABLE | 1 | **relocate候補**（live 設計 surface → PR-2 で 07-Design or live-dir 昇格の第一候補、renewal §5.6 governance） | Rs |
| VT verbal その他設計 | ~6 | correct（active VT node）+ PR-1 LEDGER 行 | %12/Rs |
| 06-K vision/L1 設計 14 | 14 | **PR-1 LEDGER 行必須（untracked）** + current/superseded 判定 | Rs（設計 status = Rs-confirmable）|
| 06-K GD-* 2 | 2 | correct（LEDGER tracked、active building-block） | — |
| 04-Specs design-content ~10 | 10 | **stale-flag 精査**（旧 spec stock、多くが superseded 疑い） | Rs |
| 04-Specs reference ~12 | 12 | correct（index/registry、by-design）| — |
| 02-Workflow ~18 | 18 | correct（protocol/handoff = 非設計）| — |
| Tier-2 evidence（optE/verbal result・crosspv・verdict ~58） | ~58 | **correct（by-design-evidence = run evidence、eval_runs が正住処）** | — |

---

## §5. Prior AUDIT 残件 fold（%10、charter method-d）

| 残件 | 現状 | 本監査での disposition |
|---|---|---|
| RS71 §0#4:26 spec-drift（Rs-PENDING） | 私 prior AUDIT で検出、Rs 未裁定 | **§4 の 04-Specs/RS71 系と統合**。RS71=INDEX は正だが §0#4 の該当 line drift は Rs 裁定待ち（本監査は再掲 + PR-1/PR-4 枠内で追跡化を提案、独自解決せず）|
| GD-Ko:95-96（Rs-PENDING） | 同上 | GD-KoShape = LEDGER tracked（correct-location）だが :95-96 の記述 drift は Rs-PENDING のまま carry。PR-4 banner 対象候補として登録 |

→ いずれも **Rs 裁定待ちを維持**（黙って解決しない、§運用10）。本監査は disposition ledger に行として可視化するのみ。

---

## §6. 最適化提案サマリ（proposal-only、per-item Rs 承認 gated）

1. **PR-1（最優先）:** 51 untracked 設計 doc に LEDGER 行 + `doc_class` frontmatter tag → 移設なしで supersession-status 可視化。**執行 = LEDGER 編集ゆえ Rs授権**。
2. **PR-4:** superseded lineage（DQ7/B-BC/W0-e packet ~23本）に banner + LEDGER SUPERSEDED 行。
3. **PR-2:** CANONICAL_MOTION_TABLE を live-design 昇格の第一候補として Rs 提示（renewal §5.6 と調整）。
4. **PR-3:** reference-over-copy spot-audit（0.7407 bare 6件等）を follow-on task 化。
5. **⛔ mass file-move は非推奨**（cite web 破壊）。
6. **Tier-2 ~176本 = 大半 correct（run evidence / protocol / lessons）** — eval_runs/02-W/06-K が正住処、no-action。

**boundary policy（§1.3）の Rs 決定が 1-6 を駆動。** policy 承認前は個別執行に進まない。

---

## §7. 接地台帳（§運用4）

| ソース | 用途 | cite |
|---|---|---|
| 00-DESIGN-STATUS-LEDGER.md | LEDGER coverage join（tracked 16 / untracked 51） | 本 session python 実測（filename ∈ LEDGER 判定） |
| task_config.py | SSOT 値（reference-over-copy 基準） | :291 DRIVER_CLOSE 0.7407 / :235 GRIP_HALF_SPAN 0.044 / :226 GROOVE_CENTER_Z 0.809 |
| renewal `RENEWAL_PLAN_07DESIGN.md` | §6-2 3列 ledger format（method-c 基盤）+ 境界 CC3-C4 finding | :142 §6-2 / :168 CANONICAL D-1 stale |
| RS71-System-Spec-SSOT.md | INDEX=正（OUT 根拠） | INDEX markers 2 |
| prior-art blocker | false-positive 判定根拠 | `D0_C4_G1_G3_REFINEMENT.md:35/42` |
| 実測パス | inventory/tier/dup 全数値 | 本 session python（254 files、Tier1 67、untracked 51、値出現数、0.7407 sample 5/6）|

**Conservatism（§運用15）:** 件数・LEDGER coverage・値出現数 = measured。「bare-on-line = 違反」は copy-violation の**保守上限**（doc 内他所 pointer で減じ得る）→ spot-audit follow-on（PR-3）。全 disposition = 提案、執行 = per-item Rs 承認。paper-only / 0-commit / 07-Design・07-Design 内部・SOMA・RS71 未編集。

*COORD2 %10 — 2026-07-11（完了時刻 = sha ping 参照）*
