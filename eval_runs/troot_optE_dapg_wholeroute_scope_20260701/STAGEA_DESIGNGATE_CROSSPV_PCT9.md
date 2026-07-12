# Stage-A design-gate v0.6 + reward artifacts v3.x — %9 OPS-SUP cross-PV 台帳 (2026-07-12 12:2x)

**対象:** `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` v0.6 + `STAGEA_REWARD_ARTIFACTS_20260712.md` (v3.1 on-disk、依頼文 v3.2 表記)。
**verdict: CONCUR-WITH-CORRECTIONS (C-1 HIGH = §0/§8 の no-C2-quiet 主張が banked evidence に矛盾 — bank 前 fix 要。設計本体 [HOLD/route_t/bank v2/OG legs] は健全)。**
数値は cablediag.npz 独立再計算 + code cite on-disk 照合 + dd7c97d480 JSON 直読。

## 0. ERRATUM (charter §7 P4 単位) — CONFIRMED + script v2 発行

- 実証: npz `diff(t)==1` (sample 連番) + `diff(recf)==10` (記録 frame 10 刻み、offset+3) → 1 sample = 1 env.step = 10 physics frames。私 v1 の mm/frame label = 誤、正 = **mm/RL-step**。×d regime check = 二重計上。
- **script v2 = `p9_p4_deltabound_discharge.py` sha `a2ad75955d` (supersedes `fdcacf98`)**: units 訂正 + regime check を per-RL-step 直接比較化 (vs env pin DELTA_BOUND_M=0.020 `newton_route_env.py:405`)。rate 不変 (mean 0.269 / p95 1.081 / max 1.855 mm/RL-step、pre-collapse [0..397])、**margin vs pin20 = 10.78×**、FEASIBLE 不変。per-physics-frame rate = UNMEASURED (上界 = per-RL-step 値) 明記。
- v1 誤りの方向 = 保守側 (margin 過小視) — records-must-match-fact で supersession 本 file 記録。

### 0b. ERRATUM-2/-3 (5体 debate 由来、charter d17f8f9cd6) — CONFIRMED + script v3 発行

- **ERRATUM-2 (窓宣言)**: 私 v2 統計 (0.269/1.081/1.855) = [0..397] truncated 窓。全系列 = **0.358/1.047/1.940** (独立再計算 EXACT)。重要確認: 58mm 交差 frame == pad-drop frame == **f397 で経験的一致** → 私の窓は正に「gripped pre-58mm 補正 regime」= 値は正・宣言が欠落。v3 で primary 窓を明示宣言 + 全系列を reference 併記 (post-grip-loss drift は policy 補正対象外)。
- **ERRATUM-3 (F-1a 降格)**: ±22mm = W0-e seat-guide C2-X 補償 clamp (累積・単軸) の precedent 転用 = **scale 参照であって授権 envelope でない**。conjunct (i) は env pin DELTA_BOUND_M=0.020 (env:405) に対する実測 headroom 10.78× で自立。正式授権 = Rs W0-a。
- **script v3 = sha `b55bc43d07` (supersedes a2ad75955d → fdcacf98)**。結論 FEASIBLE 不変 (3 版通貫)。

## 1. VERIFIED EXACT (独立再計算・on-disk 照合)

- **npz 数値 (spec §0/§2/§4.2)**: 健全域 f0-336 max **10.56** / 15mm 初交差 **f343** / pre-onset 実 max **14.84** (f342、N5) / phase-3 |inc| mean **0.579** p95 **1.230** max **1.940** (spec 0.577/1.229/1.940 — mean/p95 の ±0.002 は窓境界差 trivial) / f343 起点 155 step 単調率 **98.7%**、減少 **2 回 ≤0.44mm** / onset→58mm = **54 RL steps** (f343→f397) — 全 EXACT。
- **code cites**: `newton_route_env.py:405-407` = DELTA_BOUND_M 0.020 / GRIPPING_ARM_SIGMA_CAP_M 0.002 / PHYSICS_STEPS_PER_RL 10 EXACT / `route_executor.py` (envs/) `_REC_CADENCE=10` (:88 帯) + bank :427-433 = arm/gripper q + qd=zeros のみ (cable なし) + `:3235-3240` reset_to_phase(k≥1) raise (cable re-seed unwired を code 自身が disclaim) — §0 grounding 行の実能力訂正は正確。
- **recorder keys** (`route_demo_recorder.py:52-61`): `held_seg_l` 実在・**`held_seg_r` 不在** (nearest_seg_r のみ) — N2 の L-only scope 宣言の前提 CONFIRMED。cable_xyz/cable_quat = _STACK_KEYS 実在 (contract v2 昇格対象の実体あり)。
- **reward artifacts 算術**: S1 +217.29 / S2 +207.00 / S3 +216.09 (T=891≤900 ✓) / S4 +1.00 / S5 −3.99 / 比率 225:19=11.8:1 / 未訓練 stall return +6 (15−9) — 全再計算一致。順位 S1>S3>S2>S4>S5 健全。

## 2. 注目 3 点の verdict

- **§4.2 N1 警報再解釈 = CONCUR (core)**: comp5 = residual≡0 canonical 構成 (control JSON `drive: feedforward (D rho=0)` 直読 + node 04:18) → nominal-quiet band は本基板 (C2 scene env replay) に不存在、HOLD@f343 = FORK-1 実体の正しい警報、stall→timeout = 期待初期挙動、HOLD-resume rate = 学習 telemetry — 論理・接地とも健全。**但し C-1 (下記) の contrast 主張のみ REFUTED。**
- **§2 D-2 claim ① bar = CONCUR**: 「drift-under-HOLD (Δ≡0) < drift-with-march mean 0.58 mm/RL-step」は march-driver 機構を直接弁別 (v0.4 の <2mm bar は march 込みで満たされ弁別力ゼロ = 撤回正当)。mean 実測 0.577-0.579 verified。2 段 contingency (機構 bar 0.58 / 容量 bar 2.0=σ-cap) 明確。σ-cap marginality (max 1.94 vs cap 2.0) の honest 併記も適切。
- **§6.2 producer-path bank capture = CONCUR-in-principle + C-3 精密化**: env feedforward replay は t≈498 死 (実測) で k≥4 境界不到達 → producer 系 capture 必然。cross-builder transplant は (a1) 同等性 (contact param 同一 + frame-0 0.02mm) + restore-fidelity DoD (L∞ ≤1mm/1mm/s ∧ div_grip ≤10.56) + 正制御 leg で 3 重 guard = sound。→ C-3: capture host の pin を推奨。

## 3. CORRECTIONS

- **C-1 (HIGH、bank 前 fix 要): 「quiet は no-C2 scene で成立」は banked evidence に REFUTED。** spec §0 N1c 行「quiet が成立するのは no-C2 scene (byte-id 実証) と producer 経路のみ」+ §8 hold-quiet 行「全 route quiet leg は no-C2 scene でのみ実施」に対し、**dd7c97d480 の control JSON 直読 = no-C2 も同一 failure** (`grip_loss_first_zero_pad_t: 397` / `early_done: 499` / `max_phase_reached: 3`) — trace 同一性こそが C2 exoneration の根拠であり、no-C2 に full-route quiet は無い。同 spec §0 FORK-1 行の byte-id cite と**同一 doc 内で矛盾** (v0.6 stale-line 掃きの残り 2 箇所と推定)。**fix: quiet 主張の scope = 健全域 f0-336 のみ (scene 不問)。full-route quiet の env-replay 基板は存在しない (producer 経路のみ、そこに HOLD 機構は無い)。§8 hold-quiet leg = 健全域-only に縮退 or 削除。**
- **C-2 (MED): §8 HOLD 込み horizon leg (p99≤810「不変」) の基板が N1 下で未定義。** residual≡0 + HOLD ON → f343 で凍結・Δ≡0 は回復不能 → 全 episode timeout@900 = p99≤810 を満たす run が存在しない。関連: Artifact 3 S3 (HOLD 120 step、T=891) も 810 bar と非整合。fix = leg の基板・意味論を再宣言 (例: 健全域/bank-fork 局所窓での overhead 検証、or「完走 episode の route 長 ≤810」へ意味変更、or 訓練後 policy 対象へ defer)。
- **C-3 (MED、精密化): bank v2 capture host を route_executor.run_route に pin 推奨** (§6.2-1 は「producer 経路 (locked runner)」表記)。抽出は byte-repro 81/81 npz sha EXACT 実証済 = 同一 state 系列を再生し、**Rs-LOCKED file への新規計測 edit (rule-10 escalation 再演) を回避**できる。専用 dump (ISSUE-B: cable body_q/qd + arm/gripper q/qd + chunk 整列 index + provenance sha) は非 locked の production engine 側が自然な帰属。locked runner 内部にしか無い hook が必要な場合のみ locked edit + Rs surface。

## 4. minor / notes

- phase-3 mean 0.577 vs 私 0.579、p95 1.229 vs 1.230 = 窓境界 (f259 包含差) — 表記側で「窓 = phase==3 全域 f259-498」を一行 pin すれば消える。
- 私 P4 v2 の max 1.855 (pre-collapse 窓) vs spec §2 の 1.940 (phase-3 全域、post-collapse 含む) = 窓定義差で両立。§2 が 1.94 (保守側の広い方) を採るのは妥当。
- reward artifacts の header 版数 (on-disk v3.1 vs 依頼文 v3.2) = 表記ずれ、内容は v3 amendment 込みで一致 — bank 時に版数統一推奨。
- 9-lens 残り: 単位系 (ISSUE-A 後) 一貫 ✓ / predicate-completeness = Artifact 1 stall-class honest 登録 ✓ / conservatism 方向 = §11 明示 (実機 EE-guard 非保守含む) ✓ / authority 境界 = Rs W0-a 項全列挙 ✓ / cost 再見積 ~1.3-2.4k = staged ≤800 分割宣言 ✓ / INVARIANTS/task_config 不触 ✓。

## 5.5 W0-a packet assembly 検分 (13:3x 追記、依頼 = %12 13:27 の two-key 観点 ①-④)

**対象:** `W0A_PACKET_RSTECHLEAD_20260712.md` (30e4707ace)。**verdict: CONCUR-WITH-CORRECTIONS (C-1/C-2 = Rs 決定前 fold 要)。**

- **VERIFIED (①転記/③台帳cite/④D-rows)**: §2a 全値 = spec v0.8 EXACT — resume ≤12mm/3step/鋸歯2.84 = spec:92 (v0.8 M5 fold、新規判断でない ✓) / G1 arming = spec:91 (H7 fold ✓) / 15mm・≤6step・MAX_HOLD 24 placeholder・Δ-bound 20 vs 1.94 (~10×)・DR±20 OFF・緩和 option 全一致。§2b 全 cite 実在: abort 規則 = devplan:124 EXACT / Q_rank_error <0.10 = devplan 実在 / γ0.997・λ0.95・corner≥8 = v1.5h 実在 / ≥70% illustrative 明記 ✓。③ 私台帳 cite 記述正確 ✓。④ D-B/D-C/D-D = devplan §8 忠実 (D-C veto 代替 = canonical DAPG 差戻し ✓)。C-1 quiet fix = spec:165 着地 ✓。§5 NHA 条件 (COMPLETE 同時宣言) + campaign decouple ✓。
- **C-1 (HIGH、②/④)**: §1-1 D-A が **07-05 Rs 既決を open 質問として再提示** — LEDGER row47 ⟦07-05 10:17 W0-b 終局⟧ = Rs D-A′「(B)」= R1 CLOSE + A-vs-B は P2 state-feedback oracle 稼働後の named probe へ pre-register 済。「再開 か skip か」の再決定は既決と矛盾/二重決定 risk。fix = 1-1 を「既決 (B) の確認 + pre-registered probe の発火時期 (oracle は Stage-A 成果物 → 発火 = Stage-A build 後が自然) のみ」へ reframe + prior-decision cite。
- **C-2 (MED、③/provenance)**: packet §4「全て commit 済み pointer」に対し **%9 台帳 (本 file) + script v3 = 両方 untracked (git status ?? 実測)** → %12 bank (banking = %12、07-06 recount txt precedent) で claim 真化、or §4 注記修正。
- **M-1 (minor、①)**: §2a 開始 mix「比率は smoke 後に再提示」 = spec:145「比率 = Rs W0-a」からの silent 逸脱 → 逸脱を loud 化 (n=1 で根拠不在ゆえの deferral 提案と明記) or 比率案を今提示。
- **M-2 (minor、②)**: §3-2 falsifiable claim ③ (HOLD 非観測でも脱出学習) = **spec v0.8 に不在の新規登録** + 「全て §8 に反証 leg あり」が ③ に不成立 (③ の実測 = Stage-C 訓練時 HOLD-resume rate、§8 smoke でない) → spec 1-line 追記 + 反証帰属の正直化、or packet から ③ 削除。

## 5. 判定

CONCUR-WITH-CORRECTIONS: 設計核心 (route_t 単一源 / cable-metric HOLD / N1 警報 framing / claim ① / bank v2 / OG A′B′C′ nominal-scope / DR×curriculum LOUD) は全て健全かつ /pre-check 4 往復の fold 品質が高い。C-1 は事実誤り (自 doc 内矛盾) ゆえ bank 前必須 fix、C-2 は leg 基板の再宣言、C-3 は locked-file 衛生の精密化。3 件とも設計変更でなく doc/leg-spec 修正 — 反映後 bank 可。
