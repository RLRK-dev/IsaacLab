# P2 sparse-primary reward — /reward-design 4 成果物 (W0-c DRAFT **v1.3** = v1.2 + env-spec 5体 fix [G4 再定義 / latch 明文 / α 探索構造 / spec v1.5 連動]、assumption-labeled)

**Author:** %12. **v1.0** 09:5x → **pre-check = BLOCK (10 issues、`logs/pre-check-log.jsonl` 2026-07-05T10:04)** → **v1.1 10:1x 全 issue 反映**。**Status:** DRAFT — CPU-smoke 実測 + P3 grid で re-discharge するまで最終 PASS を主張しない。決定 = Rs。
**Spec:** `P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md` (v1.4 連動)。**実値 anchor:** `task_config.py:368` T_GROOVE=3mm / `:373` K_INSERT=10 / T_FINGER=12mm / `:264` DR±20mm / **hold-span 実測 = 92.4mm achieved-coupling (`task_config.py:246` 系、banked INV#2 ruling `DQ7_DAGGER_BUILD_SPEC_V2_MINIMAL_COORD2.md:71` + `DQ7_INV2_ASSERT_RULING_PCT12.md`)** / lift rise 実測 +45.7mm (RS71 §0#4 WR recipe) / horizon 771 実測 → 900。

## Assumptions (A1-A5) + counting rule pin
A1 fire step = recorder 15-phase histogram 比例近似 / A2 base DR-SR 代理 = CP-C (**counting rule を P3 前に pin [ISSUE 7]: per-offset unique 計数 + 決定論的 re-run は 1 offset 扱い → 現推定 13/16 = 81.3%** [run-level では 14/18 = 77.8% — 規則選択で evidence-gate 80% 境界が flip するため事前 pin。境界隣接につき P3 実測が decider]) / A3 horizon 900 / A4 sparse の学習信号 = advantage 経由 (成立条件は GATE 節の P4 pre-registration に依存 — 「+206 対比」は N-episode 統計が前提で単発 episode の勾配ではない) / A5 predicate 集合 = 提案。

## Predicate chain (v1.1 改訂)
G1 cage (T_FINGER 12mm 閉 ∧ **grip-contact flag** ∧ **span = 92.4mm achieved-coupling ± P3-grid 導出 window** [88±5 は誤中心 — 実測 92.4 に対し margin 0.6mm しかなく DR 下で G1 恒久不 fire の episode を作る]) → G2 lift (**held_cable_z − z_rest(P0) ≥ +40mm**; 基準 = P0 静置 cable z [demo npz t=0]; P0 値 = 0 <40 = 偽 fire なし / demo 実測 +45.7mm >40 = 到達性 margin 5.7mm ✓) → G3 C1-seat (seated-seg d < 3mm ∧ pin fired) → G4 regrasp_ok (**`test_newton_clip_routing.py:4593-4624`** = `_at_88 AND _R_grips` — v1.0 の :4516 cite は誤り訂正。⚠ v1.3 [CC3-HIGH]: `_at_88` の reach 参照は script command 基準 → **β では「自 command への residual」が trivially satisfiable = tap-hack + 偽 advance** → **in-scene cable-lane 相対 (ACTUAL cable picked-seg ± GHS lane、L-hold 基準) に再定義** [α は base 供給で従来どおり]) → G5 C2-seat (<3mm) → G6 SUCCESS (G5 sustained K_INSERT=10 ∧ ¬dropped ∧ span-guard)。ori 節なし (HIGH4)。
報酬: +5×5 / +200 / −0.01/step / terminate −10。§運用22: 225 vs 19 = 1:11.8 (**v1.3 前提明文: gate = latched-monotonic・fire-once — 無 latch の re-fire farming [seat↔unseat cycle で +5 反復] を封じる。unit-test に no-re-fire leg**)。
**span-guard も 92.4mm 中心に統一** (M-D assert 同様)。commanded-88mm の INVARIANT#2 主張は achieved-span predicate と分離して扱う (banked ruling どおり span-PRESERVATION で判定)。

## Artifact 1 — REACHABILITY (v1.1: 両枝とも CONDITIONAL-PASS)
- **α (residual-on-script) = CONDITIONAL-PASS (v1.0 の無条件 PASS は over-claim だった [pre-check CRIT])**: 全 gate は base が earn (per-offset 81.3% 推定)。**ただし corner の Δ 補正列が PPO batch に自然発生する保証はない** — ①非累積 Δ + zero-mean 探索は経路を random-walk しない ②BC 項は Δ≡0 へ引く (corrective prior ゼロ) ③Δ bound 未導出。**成立条件 (discharge 3 点、v1.2 = %9 CORRECTION 1 反映): (c1) P3 が corner-miss magnitude 分布を実測 (c2) Δ bound ≥ miss + margin を導出 (c3) corrective 機構の正しい役割分担を配線 — (i) oracle-relabel = drift-recovery 教師 (policy が base 近傍から逸脱した時の復帰供給 = Fact A の正しい使途。⚠ oracle は script-faithful ゆえ base 自身が FAIL する corner では「失敗経路への復帰」しか返せない — corner 教師への誤用は mini-test 機構 C [state-blind teacher] と同型の誤り) / (ii) base-failure corner の harvest = c2-sized 局所 RL 発見を PRIMARY 仮説に (seat-miss は terminal-gate 近傍の小補正 = credit path 短; c1/c2 で SIZE された探索 + P4 pre-reg [corner-episodes/update 下限] が条件 — 「純 sparse+探索」の無条件主張ではない) / (iii) c2 bound 超過の miss = draw-class 会計へ編入 (beyond-script teacher = open design-Q として明示)。⚠ v1.3 (env-spec 5体 CC2-CRIT): (ii) は **structured-common-mode 探索 + p_hit(m;σ,W,window) ≥ floor の事前計算を discharge に追加した conditional-PRIMARY** に更新 — per-arm 独立 σ は span-noise 死、生存 σ では miss>3mm の発見 p ≈ 0 (表現可能 ≠ 発見可能)。corner state では Δ≡0 anchor + drift-recovery relabel を **corner-mask** で外す (両者は fix と衝突する持続力)。詳細 = spec §2 v1.5。** → α と β は対称になる (α = oracle-relabel 必須 / β = curriculum 必須) — D-C 判断材料。
- **β (canonical-on-B2) = CONDITIONAL-PASS**: G1-G2 の閉ループ earn 根拠は **b1p5 (nominal、n=1、gate 粒度未計測) のみ** — v1.0 の「on-path 18×」cite は script grid の誤帰属 (訂正)。**P4 前に BC-init per-gate fire-rate @DR を実測 (pre-register)**。G3+ = curriculum 必須 (不変) — **機構 pin は spec v1.3 §2-F2** (推奨 = script-run-to-phase-k; npz-restore は recorder に qvel が無く不忠実 [pre-check 実測 grep 0 hits])。開始集合に G1/G2−ε も追加。
- **共通の到達性上限 (ISSUE 2): 不可勝 draw class が実在** — CP-C 実測 (−8,+8) = 決定論的 R_MISS: bow-chord 112mm > span 窓 (~93-97mm) で「掴む」局所 fix が span-guard 禁止側にある。±20mm 連続 DR はこの近傍を有限率で引く → **SR 上限 < 100% を両枝の表に明記**。draw 方針 = design-gate 項: {truncate-without-penalty / DR-support から除外し limitation 文書化 / Rs-Q: span 規律を RL 下でも hard に保つか}。**予測される挙動: draw では G3 後の bank-and-hover が最適 (+10 > 続行 +1) = selective-hover は訓練 bug でなく期待挙動** — dense HIGH3 とは別種で、sparse 構造の性質として記録。

## Artifact 2 — CAUSAL GATE DAG (v1.1)
driver 注記改訂 (v1.2): α = base + **c2-sized 局所 RL 発見 (primary) + oracle drift-recovery relabel** / β = BC-init + **curriculum (機構 pin 済)** + demo-BC。DEADLOCK: 両枝とも「必須機構なし」構成は DEADLOCK (α: corner 補正列不生成 / β: G3+) — **両枝の必須機構を外した構成を D-C 表で選択肢として出さない**。

## Artifact 3 — GROUND-TRUTH VALUES (実式、v1.1 で性質②を訂正)
表 (hover −9.00 / 即drop −11.00 / G1+G2→drop −4.00 / 成功 T=771 +217.29 / 成功 T=900 +216.00) は不変。
**性質② 訂正 (ISSUE 5 — v1.0 の「2×R_PHASE ≥ TERM_PEN = 試行がペイ」は経済学的に誤り: 獲得済み +10 は sunk で両選択肢に共通、比較から消える)**: 正しくは gate k での限界比較 = p_advance×(R_PHASE + γ^k·E[future]) vs (1−p_advance)×TERM_PEN + Δtime — **試行 incentive は +200 の continuation value が担う** (P3 実測の per-gate p で数値化; p が低い draw 状態では hover が合理 = Artifact 1 の selective-hover と整合)。pre-register する性質 = ①単調順位 (成功≫部分>hover>早期drop、実値表どおり) と ③anti-hover (sparse+time-pen 構造)。

## Artifact 4 — EPISODE TRACE (v1.1)
α-nominal / β-no-curriculum (DEADLOCK trace) / β-with-curriculum = v1.0 のまま有効。**α-corner を訂正**: 「advantage 差 +206 が教える」は N-episode 統計の話 — 単発対比でなく、**P4 pre-registration (GATE 節・spec §9) の {γ≥0.995 or 正当化, GAE λ, envs×steps/update, corner-episodes/update ≥ 下限}** が成立条件 (γ=0.99 では 180-step gate 間隔の中継 +5 が ×0.164 に減衰、末端→序盤 credit は ×0.0024 — value 関数の内挿が実質全部を担うため容量・batch 設計が拘束)。

## §A8 — §運用21 obs ⊇ reward/predicate-inputs 照合表 (ISSUE 8 — 約束していた表、初出)
| predicate/terminate 入力 | obs 対応 | 判定 |
|---|---|---|
| G1 finger 開度 | [7]/[15] | ✅ |
| G1/G4/guard span | clamp pose [0:16] から計算可 | ✅ |
| **G1 grip-contact / G4 _R_grips (法線力)** | **無し** | ⚠ → **obs v2.1 提案: [53:55] per-arm contact flag (2D)** or 却下理由文書化 (pose+finger で代理可能か = design-gate Q) |
| G2 held_cable_z | [48] | ✅ |
| G3/G5 seated-seg d | [49] | ✅ |
| G3 pin state | phase one-hot [42:48] が事後を carry | ✅ (pin = scripted event で policy 制御対象外 → 制御可能性要件なし、状態通知は one-hot で足る — 論拠明記) |
| **reach-fail terminate** | **無し** | ⚠ → **obs v2.1 提案: [55:57] per-arm IK-residual (2D)** (β では policy 起因になり得るため; α では base 起因 → informative)。 |
| within-phase progress | [50] | ✅ (β の semantics [prefix handover 後の基点] = design-gate で pin) |
| drop terminate | held_cable_z [48] + finger [7]/[15] (+提案 [53:55]) | ✅ justified (複合で可観測) |
| explosion terminate | 無し (42D base は velocity 次元ゼロ) | ✅ justified 案: explosion = physics-fault terminate で policy の回避学習対象でない (発生 episode = invalid 扱い) — 本論拠の確認 = design-gate |
| G6 sustain counter (K=10) | 隠れ状態 (obs 化せず) | ⚠ note: +200 の 10-step 先 advantage が担う (γ≥0.995 で ×0.95) — counter obs 化は不要と判断、design-gate で確認 |
→ **obs v2.1 = 57D 案** (42+6+1+1+1+2+2+2)。spec §6-3 の「~53D」を v1.3 で更新。52D/53D 齟齬も本表で解消。

## GATE (v1.2 DRAFT verdict)
Reachability: α CONDITIONAL-PASS (c1-c3) / β CONDITIONAL-PASS (curriculum pin + fire-rate 実測) / 共通 SR 上限明記 ・ DAG: 必須機構込みで PASS ・ Ground-truth: PASS (性質② 訂正済) ・ Trace: PASS (P4 pre-registration 拘束付き)
→ **DRAFT-CONDITIONAL — pre-check 再走 (BLOCK→redesign→re-run 規則) を経てから 5体 [VERIFY] → Rs W0-a′ packet。**
discharge 条件 (統合): CPU-smoke (predicate fire 実測 + unit-test **@cuda:0 pin** + restore/handover fidelity [β]) + P3 grid (per-offset SR [pinned counting] + corner-miss magnitude + span 分布 + draw class 分類) + P4 pre-registration (γ/λ/batch/corner 下限)。

*%12 — 2026-07-05 10:1x。0-commit。*
