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

## 5.6 W1 env-build charter v0.1 検分 (13:5x-14:0x 追記、依頼 = %12 13:55)

**対象:** `W1_ENVBUILD_CHARTER_RSTECHLEAD_20260712.md` (b21163b721 + envbuild node spawn)。**verdict: PASS-WITH-CORRECTIONS (W-1/W-2 = MED 2 件。B0 即時着手 = 異議なし、B1 解禁可、B2 着手前に W-2 fold)。**

- **VERIFIED**: (1) staging = B0-B7 各 ≤800 行 + 各自 L3 chain、LOC 計 ~1.35-2.55k = spec §10 :207 EXACT (2) **転記忠実性 = 全数照合 PASS** — §1 数値基盤 = W0-a 採択値 EXACT / B1 consumer #6 = spec:76 (H6 後段) 実在 EXACT / B3 M10 (body_q_prev :997 + Dahl :1061 + 1-step post-restore leg) = spec:142 実在 EXACT / B3 抽出 twin pin = spec §6.2-1 (C-3 fold 済) EXACT / L1 非有限 fail-HOLD :94 / H1 per-k 差別化 :168 / M11 schema_version :156 / M12 single-file lint :209 / M1 recenter to-be-built :132 / M3 :117-124 — 全 cite 実在 (3) 担当 = devplan §7:192 EXACT (%11 build / %10 audit / %12+%9 verify) (4) B0 = REFUTED-arc dirty revert (on-disk +23/+70 実測一致) + %11/%12 co-decide + baseline pin 順序正 → pre-verify 着手宣言は妥当 (5) NEST = trainer children に stageA+envbuild 両追加済 (朝の gap-class 再発なし) / LEDGER row49/50 実在 (6) campaign 不発効・§7 衛生・§4-3 動画レグ・prior-art self-hit disposition 全て健全。
- **W-1 (MED、governance)**: §6 multi-cell bank 行 = 「W0-a 一括 A で採と解釈 (LOUD、W3 発効、veto 可)」だが **提示者 = 「—」= 明示 confirm の予定者不在**。本日の C-1 precedent (blanket-A over 選択行 = 曖昧、%12 own) と同 class → fix = 提示者 %12 + trigger「W1 完了報告に 1-line confirm 同載 (W3 発効前)」を行に追加。解釈自体は defensible + W1 影響 = B3 cell-parameterize (前方互換のみ) で contained。
- **W-2 (MED、device)**: B2 chunk DoD「hold-quiet/hold-fires = residual≡0 **CPU** replay で chunk 内 discharge 可 (0-GPU)」は charter 追加の運用主張 (spec §8 に device 記載なし、canonical 慣行 = cuda:0)。**f343±1 bar は cuda:0 生成 trace 固有** + FORK-1 = micro-diff カオス増幅 + canonical route device-fragile (banked) → CPU replay では onset が実質移動しうる = false-FAIL/false-PASS risk。fix = 両 leg を cuda:0 pin (499-step replay 1 本 = 数分、0-GPU 化の益なし) or 同一 device 参照 trace で bar 再定義。
- **process note (honest)**: consumer #6 / M10 を truncated grep で「spec 不在」と誤 flag しかけ、full-line read で自己 REFUTE — 「absence 断定前に full-line + 代替 term」discipline が false finding 2 件を阻止。

## 5.7 W1 B1 conformance v2 検分 (16:4x-17:0x 追記、依頼 = %12 16:38、%9 lens = R9/R12/R13/§4)

**対象:** `W1_B1_CONFORMANCE_COORD_20260712.md` v2 (c4c8212649、%11 起草・5体 fold 済)。**verdict: PASS-WITH-1-CORRECTION (F-1 MED = R12 判別力の subset 指定漏れ。fold 込みで build 着手可)。**

- **R9 co-slice 数理 = CONCUR (独立再導出)**: bank 構造 on-disk 照合 — `arm_span` = 28-wide two-arm snapshot (:426) が **arm_local 12 + grip_local 16 = 28 に正確に分解** (block 長 claim と一致)、driver 4 = [g_l,g_l,g_r,g_r] (:431)。契約「maps と banked の**両方**を per-map block 長で slice + enumerate を W 内再基底化」は数理的に正 — v1 罠 (maps のみ slice) は tiled bank 下で value-masked (だからこそ R12 の distinct bank が必要 = 表内で自己整合)。将来の non-tiled bank (B3 cell-parameterize) にも前方互換。補強: 両 slice の world 順序一致 (昇順) を実装時 1-line 明記推奨。
- **F-1 (MED、R12 判別力)**: 「per-world 相違 synthetic bank + sentinel + k∉bank + flag-OFF assert」は良設計だが **test の呼出し W が未指定** — W = 全 world or prefix ({0,1,…}) だと「banked を先頭 |W| block で読む」bug class が正解と value-一致し**不可視** (prefix では旧 enumerate ≡ 新 enumerate)。fix = R12 に「**W = non-prefix・world-0 除外 subset (例 {1,3})**」を明示 pin。1-line 追記で fold 可。
- **R13 #6 挿入順序 = CONCUR (on-disk 照合)**: :1608-1610 done_ids → `_reset_worlds` 実在、reseed_grip_open は _reset_worlds 内部 → 「_reset_worlds 直後に #6」= restore-after-reseed 順 ✓ (B3+ で banked-CLOSED が OPEN reseed に勝つ = 正)。#6 は :1612 `_compute_obs_batch` より前 = fork 状態が同 step obs に反映 (B3+ 要件、挿入点の副次的正しさ)。k==0 early-return (記帳後・bank lookup 前) = B1 挙動恒等 + k=0-bank-entry 地雷排除 ✓ (_requested_phase write-only 検証済とセット)。
- **§4 KNOWN_ALTERNATIVES 棄却 = 妥当**: accessor は B2 per-world 凍結で per-world stored offset を持たされ mirror に収束 (indirection の利得消滅) / 全分岐は消費者毎 flag check = grep 清浄度崩壊 + 凍結 logic 重複。mirror の残 risk (将来の episode_length_buf 第 5 write 点追加漏れ) は **R16 fail-closed allowlist grep が恒久 drift guard として二重化** — 棄却根拠は成立 + 構造保険あり。
- anchor spot-check: :483/:1013/:1593/:1602/:1512/:1574/:1175/:1139/:1608-1610/config:158/:3216/:3227/:334-340 全 on-disk 実在 EXACT。CRIT-1 (v1 偽検証 → env-leg 群) の v2 差替えは実 CRIT を正しく fold (⑨a′+DoD⑤⑥⑩+cablediag byte-anchor = env 感度あり)。

## 5.8 W1 B1 post-build 検分 (17:2x-17:4x 追記、依頼 = %12 17:2x、%9 lens = F-1 test 実装 + run_legs.sh fail-closed)

**対象:** build `e1eac1deb8` (9 file、code 4 + evidence 5)。**verdict: PASS-WITH-CORRECTIONS (R-1/R-4 = MED、検証 harness 側 — env code 本体は健全、B1 受入可・B2 着手前 fold 推奨)。**

- **F-1 test 実装 = 模範的 (CONCUR+)**: `test_world_slice` は pin を完全実装 — W={1,3} non-prefix/world-0 除外 ✓ / 全域 unique 値 (1000w+slot) の hand-built distinct bank ✓ / **world_ids=[3,1] を意図的 unsorted で渡し昇順 sort を test** (私 R9 note の実装化) ✓ / sentinel −99 ✓ / v1-compat (None=全 world) leg ✓。
- **R-1 (MED、run_legs.sh fail-closed 穴)**: legs 1-4 の **runner 実行行の exit code 未確認** (`$PY $S/dod9a_prime.py … > log 2>&1` に `|| FAIL=1` なし) → runner crash 時、**前回走の stale json が残存していれば comparator は stale-vs-banked を比較して false-PASS**。log は redirect で fresh だが json は残る。leg5 のみ免疫 (fresh log の grep -q が guard)。fix = 各 run 行に `|| FAIL=1` + 実行前に対象 artifact rm。毎 chunk 再利用される harness ゆえ今 fold が安い。
- **R-4 (MED、conformance-vs-実装 gap)**: R12 の **CC6 条件「flag-OFF `route_t ≡ episode_length_buf` unit assert (強制 per-world reset 後)」= 未実装** — state_bank test に route_t 参照ゼロ (grep 0 hit)、env-leg 群 (⑨a′/DoD/cablediag) は**全て world_count=1** で done-mid-run per-world reset 経路 (:1028 mirror site) を非被覆 = CC6 が閉じたかった正にその穴が残存。fix = 小 unit (2-world env or mock で subset done 強制 → 全 world route_t==episode assert)。
- **R-2 (LOW)**: sentinel check が `jqd[grip_qd_i]` 非確認 (restored 側は確認済) — 非対象 world への gripper_qd 過剰書込みが不可視。1-line 追加推奨。
- **R-3 (LOW note)**: k=0 invariant は builder default `phases=(1..5)` + docstring + reset_to_phase k==0 early-return で実質 double-guard 済 (hand-built bank への assert は文書化価値のみ)。`build_state_bank_from_recording` 冒頭に `assert 0 not in phases` 1-line 推奨。
- 補強確認: env :497 route_t alloc / :1028 per-world mirror / consumer 再配線 (:979 系) = conformance cite と一致。leg1-4 の結果自体 (⑨a′ EXACT/drift 0.0/span 0.0/cablediag byte-EXACT/5-cell 5/5) は %12 独立実測と整合 — mirror 恒等は exercised 経路で経験的に裏書き済 (R-4 は非 exercised 経路の穴)。

## 5.9 W1 B2 conformance v2 検分 (23:4x-00:0x 追記、依頼 = %11 23:34、joint %12+%9)

**対象:** `W1_B2_CONFORMANCE_COORD_20260712.md` v2 (5体 fold 済)。**verdict: PASS-WITH-NOTES (N-1/N-2)。ask B1/B2 への %9 view = 下記 (裁定 = %12)。**

- **B2 入口条件 = 私の B1 loop on-disk CLOSE 確認**: `04a31e1e98` — R-1 (rm -f + 全 runner 行 || FAIL=1) / R-2 (sentinel gripper_qd :245、%9 credit comment) / R-3 (`assert 0 not in phases` :402) / R-4 (**専用 leg6_route_t_mirror.py+json** — R12 の文言 [state_bank test 内] と配置は異なるが実 env で per-world reset を打つ専用 leg = 実質上位、substance 充足) + evidence pins。全 fold EXACT。
- **CC4-1 CRIT (bar 10× 誤読) の ground truth = 私 banked keys と全項 EXACT** (独立 double-key): max(t≤336)=10.558 ✓ / 初回>15mm t=343 ✓ / grip-loss t397 ✓ / pad t=97 ✓ / phase-1 t=113 ✓ / 54 ✓ — 全て私の P4 discharge 実測 (script v3 系) と一致。CRIT 訂正は私 ERRATUM-1 (RL-step index) と同型で正。
- **ask B2 (fires bar 帰属) = %9 view: CONFIRM 推奨** — shadow 系列 (comp5 互換 convention) への hard bar ±1 = apples-to-apples で正 (leg4 で replay byte-EXACT 再現性実証済ゆえ shadow は本来 exact 343 期待、±1 は metric-path 再実装の余裕として妥当) / 正整合系列 = record+attribute = 私 ERRATUM-2 (窓/convention 宣言) の教訓と整合、±1 直 bar は false-FAIL 源。
- **N-2 (LOW-MED、数理 pin 要)**: CC4-2 の **staleness 1.31mm の導出が unpinned** — 私の独立 bound = 6/10 frame × 局所 ramp (t340-345 実測 1.01-1.23mm/step) ≈ **0.52-0.74mm ≈ 0.6-0.7 step** で、1.31mm (~1.25 step) はこれを超過。onset 域は held_seg=24 で seg-identity 差も無いはず。fix = leg JSON に 1.31 の導出を pin (導出不能なら ~0.7 step へ tighten or 現 budget 維持 + 「attribution 弁別力は ~0.6 step まで」と正直注記)。aligned = record-only ゆえ PASS/FAIL 非影響 = LOW 側。
- **ask B1 (tail 所有権) = %9 view: CONCUR + 1 条件** — (iv)→B2 編入 (release 境界 = grip schedule 知識 = B2 oracle 域、natural) / (i)(ii)→B7 / charter ERRATUM ✓。**N-1 (条件、explicit 化要): (iv) は `_route_t_clock` flag-gate 下に置くことを (iv) 行に明記** — drop 述語 :1473-1480 (on-disk 確認) は共有 env-core code で、無条件 (iv) は flag-OFF byte-preserve を破る (S5 系 post-release episode の挙動変化)。R7a の blanket に含意されるが、共有述語 edit ゆえ行内 explicit が安全。timeouts 純度は保持 ✓ (suppressed drop → timeout close = 真 timeout、`extras[time_outs]` 汚染なし — prohibited 準拠を確認済)。
- 他 R 行 = CONCUR: R3m 評価点 (post-physics pre-increment = N4 chunk 終端整合と一致) / R3k clear API (world_ids 必須 + neighbor byte-intact = F-1 哲学の継承) / R4c 両 site (:3358+:3374 on-disk 実在確認、第二算出点 readback assert の偽爆 catch は良) / R2h 純関数 / R1g blast radius grep-pin / R5c 機械導出。R12 LOC = production ~260-390 ≈ charter est (test 込み 350-555 < 800 cap) ✓。

### §5.9b %12 依頼 lens 5 点 (23:48 依頼、%12 非被覆分)

- **R3m × spec:86 整合 (数理) = CONCUR**: 評価点 = post-physics・post-barrier・pre-increment → cable 状態は 10 frame 駆動後 = chunk 終端 — R2c の f(route_t)=cf[t]+9 比較 frame と**同一時点** = spec:86「env state は RL step 後 = 終端整合」の数理を正確に実装。query top-of-step read-only (単一評価点/step) = chatter 二重評価も構造排除 ✓。
- **R3c K-counter 系列網羅 = ほぼ完備 + 1 追加推奨**: 4 系列は (a) 即復帰 (b) K=3 復帰 (c) 帯域外で K reset (d) 再発火時 K=0 初期化 を cover — 遷移空間の要点は尽きる。**追加推奨 (LOW): div=15.0 ちょうどの境界 unit** (fire = >15 / in-band = ≤15 の等号側 — float 境界の実装ずれ検出)。
- **⭐R3h 境界 (lens #3) = FINDING B2-F1 (MED)**: unit の「**t=770 と t=899 で div-skip**」は **len(step_f)=770 を前提にした境界で、cf = arange(0, 7700+1, 10) = 771 entries (t=0..770 有効) なら t=770 は skip でなく valid+clamp** (f=cf[770]+9=7709 → L3 clamp で 7706)。770-vs-771 は正に B7 carry の未解決 fencepost — **unit は境界値を hardcode せず n=len(step_f) を runtime 導出し、t=n−1 (compute+clamp assert) / t=n (skip) の対で書く**。これで B7 の 770/771 照合と独立に unit が正しくなる。fix = R3h unit 行の 1-line 書換え。
- **tail (iv) incentive 算術 (lens #4) = CONCUR (検算成立)**: (iv) なし = 非 seated 枝 post-release drop ≈ 10 − 7.7 − 10 = **−7.7 < fail-fast −3.99** (逆転実在) / (iv) あり = suppressed → timeout close = 10 − 9.00 = **+1.00 > −3.99** (逆転解消、S4 復元)、順位 S1>S3>S2>S4>S5 保存 ✓。条件 2: ①suppression scope = **route_t ≥ release 境界のみ** (route 中 drop は S5 のまま terminal −10 — scope 漏れは S5 を壊す) ②N-1 flag-gate (共有 drop 述語 :1473-1480 edit ゆえ)。timeouts 純度 = 真 timeout のみで保持 ✓。
- **A1 mask 2 点機械導出 (lens #5) = CONCUR + 1 note**: event frame → cf 境界 → G-clock 帰属は phase_id 記録済ゆえ写像 valid、「導出が期待 (G1/G4) に勝つ + loud」= 推測禁止の正しい形。**note (LOW): event frame の検出源を unit に pin** (recorded field [pin_active/phase 遷移等] からか、producer source 行の再導出か — 後者は recording に marker が無い場合 instrumentation 要)。

## 5.10 W1 B2 post-build 検分 + ask C1 (00:5x-01:1x 追記、依頼 = %11 00:53)

**対象:** build `a2f544662b` (+7276/-19、新規 source file ゼロ) + conformance v2.3 §7 + leg8 JSON。**verdict: PASS (新規 finding ゼロ — 私の全 note fold 着地確認) + ask C1 = %9 view CONFIRM。**

- **私 note の fold 全確認**: B2-F1 = conformance :66「境界は runtime 導出」+ 終端超 index 表現 (770 hardcode 排除) ✓ / N-1 = :155 sub-e「(iv) は _route_t_clock gate 下、OFF = 従来 drop terminal byte-identical」✓ / **N-2 = leg8 JSON `staleness_budget_note` に私の導出 (6 frame = 0.6 step × ramp 1.0-1.2 → ~0.6-0.7mm) がそのまま pin され 1.31mm を置換**、±1-chunk bar の弁別床として正直記録 ✓。
- **leg8 実測の整合**: g1_latch=t98 (私 pad first-active t97 の翌 step = latch 述語評価タイミングとして整合) / armed 域発火 0 + aligned max **10.407** = spec §6.2 held-seg 正整合予測 10.41 と EXACT 級一致 (band 再導出 data) / fire t342 単発 ∈ bar / dones=[] / banked crossing t343 = 私 banked key ✓。comparator 除外 = timing/throughput substring のみ + 除外値 log pin = 狭域 ✓。leg7 neighbor 隔離 (w0 counters byte-intact) = F-1/R3k 哲学の実測 ✓。
- **ask C1 (shadow bar discharge 形) = CONFIRM 推奨 (裁定 = %12)**: 反実仮想論理は正 — aligned 参照は 6 frame 先行ゆえ正しい HOLD は shadow 交差の ~1 step 前 (t342) に march を止める → **live shadow 交差を bar にすると「HOLD が正しく働くほど FAIL」の自己矛盾** (実測: live 交差 = None = 期待挙動)。discharge (i) live shadow prefix ≡ banked 系列 EXACT (343 step、max diff 0.000000mm) は**原 crossing bar より厳密に強い** (交差 index は値列に含意され、全 step 値 pin = metric 経路の完全判別) + (ii) banked 交差 t343 ∈ bar (私鍵 ✓) + (iii) delta −1 = 系統 lead の符号・大きさと整合 (−0.6 step 系統 + ramp 離散化)。ruling 意図 (n=1 apples-to-apples) 充足。prefix scope = t0..342 = pre-freeze 全窓 = 最大 window ✓。

### §5.10b %12 追加 lens 4 点 (01:0x 依頼、as-built 接地)

- **(a) B2-F1 fencepost as-built = EXACT 実装**: `test_routeexec_step_target.py:182-183`「boundary pair (%9 B2-F1): n = len(step_f) RUNTIME-derived; t=n-1 computes (with frame clamp), t=n skips」— hardcode ゼロ、私 fix の文字通りの着地。
- **(b) release_step=762 導出 = 妥当**: `route_executor.py:3181` `searchsorted(step_f, release_frame, side="left")` = release_frame (grip schedule 由来) 以上の最初の step = 境界意味論正 (suppression は予定 release を含む step から)。env 側 :568/:1520-1521 = route_t ≥ boundary gate ✓。**独立 cross-check: 900−762=138 ≈ spec の tail「~139 step」推定と整合** (release ≈ t761-762 を裏書き)。762 ∈ [0,771) ✓。
- **(c) R3c 系列網羅 as-built = 完備**: :205 **div=15.0 等号 = NOT fire (strict >、「%9 LOW」credit 付きで私推奨が実装)** / :206 15.1 fire / :207 ≤12 即復帰 / :208 re-fire chatter 計上 / :209-210 K=3 復帰 / :211+ re-fire 系列 (K-reset-on-refire = conformance CC6-F6 系列と一致)。
- **(d) g1_latch t98 vs pad t97 の 1-step 差 = 述語強度に帰属 (off-by-one でない)**: p1 (:1532-1536) = **3 重 conjunction** — (grip_r≥0.5 ∧ grip_l≥0.5) ∧ (contact_r ∧ contact_l) ∧ (|span−88mm| ≤ tol)。t97 = 初触 (pad_L=**1**/pad_R=6 = L 側 marginal single-pad) で closure/span conjunct が未充足、t98 = 11/11 firm で全充足 → latch。npz に closure/span 系列が無いため t97 の失敗 conjunct の特定は不能 (正直 note) だが、p1 ⊋ 生 pad 接触ゆえ 1-step lag は構造的に期待される挙動 — 評価順 off-by-one の証拠なし。

## 5.11 Stage-A spec ERRATUM-A/-B 検分 + B3 hidden-state lens (2026-07-13 22:2x、依頼 = %12 22:17)

**verdict: ERRATUM-A/-B = 独立 CONFIRM (反証なし)。ただし ⚠**CORRECTIVE C-α (HIGH)** — ERRATUM-B の正しい結論が「本基板に hidden state 問題なし」へ over-generalize されると、正しい要件まで消える。**

### (a) ERRATUM-B substrate 判定 = CONFIRMED (反証 試行 → 不成立)
- `SolverMuJoCo` class 実体 inspection: `body_q_prev` / `dahl` / `warmstart` = **source 内 0 hit、該当 attr ゼロ**。
- THREAD `body_q_prev`: 実 code は `newton_route_env.py:1014` の **hasattr-guard 1 箇所のみ** (`... if hasattr(self._solver,"body_q_prev") else None` → mujoco で None)、他は全て test mock。
- THREAD `dahl`: `reset_dahl_friction_for_envs` (`newton_skill_env_base.py:1183`、docstring「no-op if disabled」) — route path で実効なし。
- installed newton: `body_q_prev` = featherstone / xpbd / vbd / sim.state 側、`dahl` = **vbd 専用**。
→ M10 の当該 write-set 要求 = VBD (env6) 規約の mujoco 基板への持込み = prohibited.md「PhysX/Newton 混同禁止」同型。**ERRATUM-B は正しい。B3 で body_q_prev/Dahl を実装しない = 正。**

### ⚠ C-α (HIGH): hidden state は「消えた」のでなく「移動した」— しかも **捕捉可能**
- **mjWarp `Data` 実 field (実測)**: `qacc_warmstart` / `act` / `act_dot` / `eq_active` / `solver_niter` / `contact` — **本基板の carried state はこれら**。
- **⭐`SolverMuJoCo` は mjw Data を露出している** (source 内 `mjw_data` / `self.mj_data` / `mujoco_warp` = 全て存在) → **B3 は warmstart/act/eq_active を capture/restore *できる*。「触れないから 1-step leg が唯一の guard」という含意は成立しない** (option が実在する)。
- **`eq_active` は THREAD 固有の第 2 channel**: 4-bar gripper linkage (eq_solref/eq_solimp) + clip-retention pin (`pin_eqid`) は eq 拘束 — fork で active flag が不一致だと linkage/pin 状態が producer と乖離。B3 で明示 disposition 要。

### (b) B3 lens: 1-step post-restore leg の検出力 = ⚠ 現 tolerance では不足 (主 finding)
- **数値**: spec restore-fidelity DoD = **qpos/qvel L∞ ≤ 1mm / 1mm/s** (spec :140/:172)。対して **FORK-1 の致死 seed = `frame0_perseg_mm` mean 0.0200mm / max 0.1469mm** (npz 実測) → phase-3 で 13.26mm → t280 grip 崩壊 → t499 drop。
- ⇒ **DoD tolerance は FORK-1 致死 seed の max より ~6.8× / mean より ~50× 緩い。** warmstart 由来で 0.5mm の cable 誤差が残る restore は 1-step leg (1mm bar) を **PASS した上で FORK-1 と同一機構で発散する**。**= leg が守るべき当の failure class に対して盲目。**
- **本 node の存在理由そのものが「この基板は 0.02-0.15mm seed を ~100×/300step 増幅する」という実証** — その基板で 1mm bar の 1-step 比較を「唯一の guard」に昇格させるのは calibration 不整合。

### C-α 勧告 (B3 conformance の主 lens として)
1. **tolerance を channel 分離**: arm/gripper joint = 毎 frame kinematic re-pose (増幅 channel なし) → 1mm/1mm/s で可。**cable state = 増幅 channel** → 1-step bar は FORK-1 seed scale (**benign 実測 mean 0.02 / max 0.147mm**) で評価。1mm bar は cable に適用してはいけない。
2. **1-step → K-step divergence-GROWTH leg へ昇格 (推奨・本命)**: FORK-1 の signature は step-1 の大きさでなく **growth**。G_k−ε fork → Δ≡0 で K≈20-50 step roll → producer の同境界起点 trajectory と div_grip 系列比較。PASS = (i) 窓内 HOLD 発火 0 (ii) 健全域 band 内 (≤10.41mm aligned、leg8) (iii) FORK-1 ramp signature (持続 ~1mm/step 単調増) なし。**cuda:0 で数秒・leg8 の較正手法をそのまま再利用可**。
3. **warmstart disposition を B3 conformance に明示** (capture 可能ゆえ 3 択が実在): (i) `qacc_warmstart`/`act`/`eq_active` を capture+restore / (ii) 両側 zero 化 / (iii) 非 restore + K-step leg で drift-bounded を証明。**honest limit を明記: 全 solver state を復元しない限り phase-k fork は producer 連続軌道を byte 再現できない** → DoD の bar は「byte-parity」でなく「physically valid・drift-bounded continuation」。
4. **⚠ P0-reset precedent を転用しない**: env-core の P0 reset は warmstart 非復元で再現性良好 (⑨a′ EXACT / DoD⑤ drift 0.0) — だが P0 = **settled/quiescent** (warmstart ≈ 静的平衡)。G3-G5 fork = **mid-route・把持中・運動中・接触 rich** で warmstart は実情報を持つ。「reset で問題ないから fork も」は非転移。

## 5.12 ERRATUM-D 着地 verify + ⚠新 finding C-β (§15 明確化 E × K-step leg の交絡) — 22:3x

**ERRATUM-D (`a07b03ed69` §16) = on-disk verify EXACT**: D-1 (mjw_data 露出 → capture は option) / D-2 (eq_active = 4-bar eq `newton_skill_env_base.py:1446` + clip-pin `pin_eqid` [INVARIANT #5 認可例外] の第 2 channel) / D-3 の 5 勧告 (channel 分離 / K-step growth leg 昇格 / warmstart 3 択 / honest limit / P0-precedent 非転移) が verbatim 着地 + **D-4 = ERRATUM-C (α) の cable bar 0.5mm を私の FORK-1 seed scale で supersede** — 全て正。§15 の判別力要件 (null bank で必ず FAIL = 「PASS する DoD」でなく「間違った bank を落とす DoD」) は F-1 と同哲学、強く CONCUR。

### ⚠ C-β (HIGH、B3 leg 設計の交絡 — 私の K-step 勧告と §15 明確化 E が衝突する)

- **§15 明確化 E** = 「FF mode の leg は arm bank を構造的に検証できない (毎 frame 記録で上書き) → fork/restore fidelity leg は trainer 実 mode (IK/residual) で走らせる」= **arm channel については正しい**。
- **しかし K-step divergence-growth leg (D-3.2、cable channel) に E を適用すると交絡する**: IK/residual mode では Δ≡0 でも arm は IK 解で駆動され、**producer (FF = 記録 arm_q 直書き) と arm 軌道が一致しない** → 生じた `div_grip` 成長は **(a) bank/hidden-state 誤り** と **(b) IK 追従誤差** の**両方**に起因 = 分離不能。
- **⭐交絡の大きさ (実測 grounded)**: 本基板の IK-path delta は **mm 級** — A-probe で env batched-IK が L 腕 killer (armqdirect [per-frame 直書き] 成功との唯一差分) / EE_Z_FLOOR_KO clip = +3.12mm。⇒ **測ろうとする信号 (FORK-1 致死 seed max 0.147mm) の ~20× の交絡を注入することになる。** 信号より交絡が一桁大きい leg は検出力ゼロ。
- **解 = channel 分解 (C-α の分離原則を leg 設計に一貫適用)**:
  1. **cable/hidden-state channel** → K-step growth leg は **FF mode** (arm を記録に pin) で走らせる。arm が固定ゆえ div 成長は cable state + hidden state (warmstart/eq_active) に**一意に帰属**。比較対象 = producer の同境界 FF trajectory = apples-to-apples。
  2. **arm-bank channel** → **別 leg・非 FF (IK/residual)** で `arm_q/qd == bank` + **`_per_world_fk_jq` 設定済** (未設定なら arm が P0 へ引き戻される = §15 の指摘) を直接 assert。ここが 明確化 E の本来の対象。
  3. **統合 (integration)** → trainer 実 mode (**⚠ 実 mode は hybrid**: L 腕 = feedforward 窓 + 他 = residual [routeexec node 「L 解 = feedforward window のみ、trainer = (E or B) + D-b 窓」]) で 1 本。**「IK/residual mode で」の blanket 要求は phase 依存の実 mode で qualify すべき**。
- **null-bank negative control (§15) は 1 と 2 の両方に適用**: cable null (cable_qd≡0) は 1 で FAIL / arm-only v1 bank は 2 で FAIL — 各 channel の leg が各々の誤 bank を落とすことを実証。

### §15 write-set 2 件 = 私の既読と corroborate
`_target_seg_indices_{r,l}` stale 順序 (`:1081-1085` が `_reset_worlds` 内・P0-seed cable の後に計算 → consumer #6 `:1633` の `reset_to_phase` は `_reset_worlds` の**後** → fork 後 seg 窓が P0 由来のまま → `p4`/G4 が誤 seg を測り **永久に latch しない**) は、私の B1 R13 検分時の on-disk 読み (:1606-1612 done_ids→`_reset_worlds`→obs、:1080-1090 seg refresh) と**独立に一致** — CONFIRM。順序付き単一 fork entry point の強制に CONCUR。

## 5.13 W1 B3 conformance v2.1 検分 (2026-07-13 22:4x、依頼 = %11 22:35 / joint %12)

**verdict: PASS-WITH-CORRECTIONS — ⚠**C-β (HIGH、L5 の駆動 mode)** + ⚠**ask B4 に DISSENT** + minor 3。**B3a は影響ゼロ → RULE-CHECK→build 進行に異議なし**。C-β/B4 は **B3b の leg・restore 設計確定前**に fold。**

### VERIFIED — 実測 double-key (私の独立再現)
- ⭐**F10 (k=1..5 実在) = 決定的に確証**: golden G-phase 数 {0:1124,1:600,2:860,3:3597,4:620,5:906} → **Σ=7707 = 記録長 EXACT** / f_k = 1124/1724/2584/6181/6801 / t_k = ceil(f_k/10) = **113/173/259/619/681** / capture_frame = 10t−1 = 1129/1729/2589/6189/6809 — 全て %11 値と EXACT。⭐**さらに強い独立鍵: B2 leg8 の cablediag npz の phase 遷移 = (113,1)(173,2)(259,3) = 導出 t_1/t_2/t_3 と EXACT 一致**。別系統の 2 artifact が一致 ⇒ **F10 + ceil 整列規則 (R2c) は確証**。CC2 の「k=5 不在」CRIT が artifact 取り違えだったことも裏づく。
- **F11 (eq_active)**: pin ON = f2544〜 → capture_frame 比較で **k=1,2=OFF / k=3,4,5=ON** = %11 と EXACT。⚠**minor-1: k=3 の cf(2589) は pin onset(2544) の 45 frame (~4.5 RL step) 後** = 極めて薄い margin → multi-cell/DR で pin onset が動くと k=3 が pin 遷移の反対側に落ちる。R2k の provenance assert に **capture_frame における pin 状態の記録/assert** を 1 行追加推奨 (R3g の「記録値を復元」自体は robust ゆえ LOW)。

### ⚠ C-β (HIGH) — L5 の「IK/residual mode 必須・FF 禁止」は 2 つの目的を混同し、**cross-mode bar transfer** を生む
- **明確化 E は arm channel には正しい**: FF は毎 frame 記録で arm を上書き ⇒ `_per_world_fk_jq` 未復元 (arm が P0 へ 373-444mm 戻る) が構造的に不可視。**これは IK mode でしか露出しない — 同意。**
- **だが L5 の cable-channel bar (ii)(iii)(v) に IK を課すと 2 重の問題**:
  1. ⭐**cross-mode bar transfer**: bar (ii)/(v) の **10.407mm は B2 leg8 = FF mode で測った band**。IK/residual rollout は IK 追従誤差が上乗せされ **baseline 包絡が別物** — **IK-mode baseline は未測定**。FF band を IK rollout に当てるのは、ERRATUM-A (10t+3 vs +9) / B2 CRIT (10× index) と同じ **convention 流用 class**。⇒ 正しい fork を false-FAIL するか、逆に緩すぎて C-α が求めた growth signature を隠す。
  2. ⭐**growth signature (iii) の検出力消失**: div 成長が **(a) bank/hidden-state 誤り (目的信号、FORK-1 seed scale 0.147mm)** と **(b) IK 追従誤差 (本基板で mm 級 — EE_Z_FLOOR_KO +3.12mm / A-probe: batched-IK が L 腕 killer)** の両方に起因 ⇒ **交絡が信号の ~20×**。信号より一桁大きい交絡を注入した leg に検出力はない。
- ⭐**`_per_world_fk_jq` は growth metric を要しない**: R4#2 自身の実測が **373-444mm** ⇒ bar (vi)「arm が P0 に戻らない」の**直接 assert** が 3 桁の margin で捕捉する。subtle な div 成長で測る必要がない。
- **⇒ 解 = channel 分解 (C-α の原則を leg にも一貫適用)**:
  - **L5a (cable/hidden-state 分離) = FF mode**: fork → FF で K step roll → div_grip 成長 vs **leg8 の FF band (10.407) + ramp 不在**。arm が記録に pin される ⇒ 成長が **cable + hidden state (warmstart/eq_active) に一意帰属**、比較対象 = producer 同境界 FF trajectory = apples-to-apples。**C-α の ramp bar が power を持つのはここだけ。null-bank negative control (L3) もここで走らせる。**
  - **L5b (arm-bank + 統合) = IK/residual mode**: bar (vi) arm-not-P0 / (vii) done==False / (i) HOLD 0 / (viii) held_seg 追従 + L6 (eq_active/pin)。**⚠ここで div band を使うなら、P0 起点・IK mode・Δ≡0 の matched control run で IK-mode baseline を実測してから** (leg8 の FF 値を流用しない)。control run は同 harness で安価。
  - 増分コスト = rollout 1 本 + control 1 本 (cuda:0 数分)。

### ⚠ ask B4 (warmstart) — DISSENT: **(a) capture+restore を既定、(b) は fallback** (%11 推奨と逆)
1. ⭐**(b)「両側 zero」は実現不能**: 参照側 = 記録 (RUN1_REFERENCE_V2 = Rs-LOCKED producer の 0.716 MOTION STANDARD) であり、**producer の warmstart を遡って zero 化することはできない** (再生成 = byte-repro と motion standard の破壊)。⇒ 「両側 zero」は実際には **fork 側 zero のみ = 非対称** = 実質 (c)。対称性という利点は成立しない。
2. **(a) だけが producer state に忠実**: capture frame の warmstart を復元すれば fork の初回 solve が producer と**同じ初期推定**から出発する。cost は nv floats/frame — **既に 147 floats/frame (q 74 + qd 73) を dump している**のだから「schema が薄く済む」は弱い論拠。
3. ⭐**「warmstart は初期推定にすぎない」= FORK-1 が反証した直感そのもの**。本 node の存在理由が「この基板は 0.02-0.15mm を ~100× 増幅する」の実証である以上、「小さいから効かない」は本基板では通らない。
4. ⭐**C-β との coupling (決定的)**: (b)/(c) を選べるのは **L5 が経験的 falsifier として機能する場合に限る**。C-β により **現 L5 は検出力を欠く** ⇒ **falsifier 不在のまま (b)/(c) を選ぶことはできない。C-β を fold して L5a を建てるか、さもなくば (a) を取る** の二択。低 regret は (a)。
- (実装 note): (a) 採用時は capture が **post-step 同一点 (cf[t_k]−1)** で warmstart を読み、restore は solver の data sync **後**に書く (でないと上書きされる) — B3b で pin を。

### asks 回答 (裁定 = %12)
- **B1 (lock 設計) = CONCUR**: capture を `physics_step` (lock 外) に閉じ `run_route` 0 行 + **git diff の locked span 変更行 == 0 を機械 assert** = 正しい形。⭐**R1g の read-only 証明 (BANK_CAPTURE+DEMO_RECORD 同時 run の raw sha == RUN1_REFERENCE_V2 EXACT) が「hook が軌道を乱さない」の経験的決着** — 強い。atexit が SIGKILL で発火しない穴は R1c (frame counter == recorder len) が捕捉。**5体が build 前に LOCKED 関数編集を止めた事実は loud 記録に同意。**
- **B2 (CPU infra) = CONCUR (b)+(c)**、⚠**1 条件**: 純粋核は **extract-and-CALL** (production path が抽出核を*呼ぶ*) であること。extract-and-**duplicate** にすると「誰も使わない関数を unit する」= **B1 CRIT (producer harness が env を実行しない) / B2 CRIT (10× index) / B3-v1 (FF leg が arm bank を見ない) と同じ false-verification class の 4 度目**。⇒ **production path が抽出核を呼ぶことの grep leg を DoD に**。
- **B3 (B3a/B3b 分割) = CONCUR** (seam は clean、lock risk が B3a に閉じるのは良設計)。⚠**minor-2 (seam)**: `route_executor.py` は**両 chunk で触る** (B3a=capture+builder / B3b=guard+get_cable_bank) ⇒ flag-OFF byte-preserve leg は両方で必要 + file-clean な seam ではないと明記を。⚠**minor-3**: U4 (restore-exact + per-world 配置) は **restore = B3b scope** だが roster では `test_routeexec_state_bank.py` (B3a file) に居る ⇒ U4 の帰属を B3b に移すか、state_bank.py が両 chunk で触られると明記。
- **B5 (5体 再走不要) = CONCUR**、条件 = **§4 fold 表の finding→R 行 mapping が分割後も orphan ゼロ**であること (私の突合では R1/R2→B3a、R3-R6→B3b で保持、例外は上記 minor-3 の U4 のみ)。

### minor-4 (LOW): F3 の 2-convention 差 0.194mm
「全て 0.15mm settle 床の下」とあるが **1 境界で 0.194mm** = **FORK-1 致死 seed max (0.147mm) を上回る** ⇒ もし convention が誤っていればその境界で致死 scale の seed を注入する。解析的強制 (F3) が重みを担い、**R2f (banked q == recording arm_q[capture_frame] の 74 列 EXACT) が実質の pin** ゆえ実害なしだが、文言は「0.15mm 床の下」でなく「1 境界のみ 0.194mm、R2f が pin する」と正直化を。

## 5.14 ERRATUM-E 着地 + minor(4) 逆訂正 (22:5x)

- **ERRATUM-E (`b804750fca` §17) + E-4 (`cf29601f6c`)**: C-β の 4 点 (leg channel 分解 = cable K-step growth は FF / arm-bank は 非FF IK / 統合は phase 依存で qualify / null-bank は両 channel) + 私の **cross-mode bar transfer** 定式化が spec 化。**B4 = (a) capture+restore 確定** (私の dissent 採択、「参照側の warmstart は遡って zero 化不能」+「falsifier 不在で (b)/(c) は選べない」が決定打)。B2 = extract-and-CALL の grep 機械証明採用。B3 分割 APPROVE。
- ⭐**E-3 meta 教訓の spec 化**: 「ERRATUM-B → C-α」と「明確化 E → C-β」は**同型 = 正しい訂正の over-generalization が隣接する正しい要件を消す**。規律 = **「訂正は実際に検証した channel/domain に scope を限定せよ」**。本 arc の最大の資産。
- ⚠**minor(4) = 逆訂正 (私が正、%12 の 39 が誤り — 実測決着)**: %12「k=3 pin margin = 39 frame、貴 45 は概算」に対し、**golden 実物 (`w1_b2_dod_legs/byte_repro_5cell/mod/cell_x0_y0/route_demo_raw.npz`、sha 5f1c3f92 照合 = RUN1_REFERENCE_V2) を直接測定**: **pin_active onset = f2544 / last = f7706 / ON 5163** (= %11 F11 と EXACT) ⇒ **k=3 margin = 2589 − 2544 = 45 frame = 4.5 RL step (厳密、概算でない)**。39 は onset を 2550 と置いた場合の値。pin_eqid=27 / pinned_body=55 @cf3 も実測一致。⇒ **R2k の pin 値は 45 frame を pin**。%12 の 39 の出所が非正典 artifact なら **CC2 の k=5 取り違え (F10 hazard class) と同型** ゆえ loud 記録を推奨。

### §5.14b minor(4) CLOSE + 副次 2 件 (23:0x、うち 1 件は私の flag の自己訂正)
- **%12 own の root-cause = 自己整合 CONFIRM** (f_3−1 = 2583 → 2583−2544 = 39)。規則 (capture = cf[t_k]−1) 不変・instantiation のみ誤り = 正。
- ⭐**副次 1: その誤り class は R2d の既存 guard が捕捉する** — golden の raw phase runs 実測: `phase_id 6 = [2544, 2584)` / `phase_id 7 = [2584, …)` ⇒ `phase_id[2583]=6` / `phase_id[2589]=7` ⇒ **R2d の `assert G(phase[capture_frame]) == k` は 2583 で FAIL・2589 で PASS**。手計算の誤 instantiation を builder assert が build 時に落とす構造。⇒ **R2d の正当化を「f_k%10==0 の multi-cell edge」から「capture_frame instantiation guard 一般」へ広げるべき (弱めない)。**
- ⭐**副次 2 = 私の minor flag の自己訂正**: 「k=3 の 45-frame margin は薄く multi-cell/DR で pin 遷移の反対側に落ちうる」という私の fragility flag は**実測で弱い** — **pin_active onset (2544) は phase_id 5→6 遷移と EXACT に一致** ⇒ pin は **phase schedule で発火** (物理イベント依存でない) ⇒ DR/multi-cell では pin onset と capture_frame が**同一 phase schedule から co-move** ⇒ **45-frame margin は構造的**。R2k の assert は維持価値ありだが **根拠を「fragile margin」→「instantiation guard (副次 1 と同族)」へ**。私の当初 rationale は過剰だった。

## 5.15 W1 B3a leg 結果 検分 + D-1/D-2 view + ⚠**私の C-α sub-claim の own** (2026-07-14 00:0x)

### ⚠ 私の over-claim (own、records-must-match-fact)
**C-α / ERRATUM-D D-1 で私は「`SolverMuJoCo` は `mjw_data` を露出 → B3 は capture/restore *できる*」と主張した。検証手段は `inspect.getsource` の文字列存在 = 静的**。実体は **`USE_MUJOCO_CPU=True` (task_config.py:116、global) → `make_solver(..., use_mujoco_cpu=USE_MUJOCO_CPU)` (base:1302) → `solver_mujoco.py:3268` の CPU 分岐 `mj_step(mj_model, mj_data)` が live 経路**、`mjw_data` は `:5791` で無条件生成されるが **CPU mode では一度も step されない dead mirror**。⇒ **私が cite した buffer は死んでいた。**
- **これは私自身が banked した規律の違反**: `feedback-reuse-validate-by-build-run-not-import` (**existence ≠ function — real BUILD+RUN on CURRENT substrate で検証せよ**)。E-5 の (iii) 「測定 mode と対象の一致」を **自分の verify 手段に適用しなかった**。%11 の実走 (qacc_warmstart 非ゼロ = **0/562611**、eq_active 変動列ゼロ) が捕捉。
- **honest な net 評価 (spin しない)**: 結論「capture は可能」自体は正 (**live buffer = `mj_data`**、%11 の fix `route_executor.py:674` がその選択を実装) であり、C-α の core (「1-step leg が唯一の guard」= over-generalization を阻止し hidden-state channel の明示 disposition を強制) が **DEFECT-1 を露出させた**。だが **cite した機構は誤り**であり、静的検証で「できる」と言った点は over-claim。
- ⭐**E-5 の拡張 (提案)**: E-5 の 3 列は **DoD だけでなく verify claim 自体にも適用される** — **「機構が存在する」という主張は grep/inspect でなく run で検証せよ**。私の誤りは、私が指摘した 3 件 (感度不足 / SN 交絡 / cross-mode 流用) と**同一 class = 計器 (inspect) が対象 (buffer liveness) を測れていない**。

### DEFECT-1 = CONFIRM (私の独立 on-disk 検証)
`USE_MUJOCO_CPU` は **global**、producer と RL env が `make_solver` を共有 ⇒ **両者とも CPU backend**。%11 の診断・fix (use_mujoco_cpu で integrated buffer を選択、fallback 無し = silent mis-read を復活させない) とも正。⭐**producer 側は無傷** (mj_data が実 buffer ゆえ pin は効いている → INVARIANT #5 intact) = 私も同意。**壊れていたのは read 先だけ。**

### D-1 (warmstart は CPU backend で非ゼロか) — %9 view
1. ⚠**「非ゼロか」は再分類の bar として誤り (E-5 (i) 違反)**。問うべきは **「restore する / zero にする で軌道が FORK-1 seed scale (0.147mm) で変わるか」** = **A/B**。これは %12 が既に課した条件 (「(b) を採るなら K-step で (a) vs (b) の A/B 実証」) そのもの。⇒ **D-1 は「非ゼロ検査」でなく L5a (FF、cable/hidden 分離) 上の A/B で答える。**
2. ⭐**regret の非対称性 — (a) を既定に据え置く根拠**: bank したら inert だった = nv floats の無駄。**bank せず live だった = k=3/4/5 で silent な FORK-1-class mismatch**。⭐**DEFECT-1 はまさにその第 2 の失敗が「実在し、かつ silent」であることの実証**。⇒ **(a) capture+restore を既定に維持し、L5a の A/B が「≪0.147mm」を示したときにのみ非 item へ落とす。** zeros を bank しても害はない (Dahl/body_q_prev のような *属性不在* とは違い、warmstart は**実在する live field**)。
3. ⭐**eq_active は D-1 の再分類対象外 (構造的、経験問題でない)**: clip-pin (eqid **27** / body **55** / ON = f2544-7706、私も golden で実測) は **INVARIANT #5 の認可例外**であり、**k=3/4/5 の fork 境界はまさに clip が cable を保持していなければならない所**。pin OFF を restore した fork は *数値的に微妙* なのでなく **物理的に誤った state**。⇒ **warmstart が非 item になっても eq_active/pin の capture+restore は必須。** %11 の **leg6 (captured eq_active[27] ≡ recording pin_active を per-frame EXACT)** は E-5 (ii) の正しい negative control (今回の bug を必ず落とす)。

### D-2 (cross-backend transplant) — %9 view: **今日は問題なし + ⭐戦略 carry を escalate**
1. ⭐**今日 cross-backend transplant は存在しない**: `USE_MUJOCO_CPU=True` は **task_config.py の global** で、producer も env も `make_solver` 経由で同一 backend ⇒ **(a) 同一 backend 内 / (c) env も CPU に pin は、既に構造的に成立**。
2. **やるべきは 1 行**: bank meta は既に `use_mujoco_cpu` を記録 (`route_executor.py:726`) ⇒ **restore 時に `bank.meta.use_mujoco_cpu == solver.use_mujoco_cpu` を assert (fail-loud)**。将来の backend flip が **silent corruption → loud failure** に変わる。安価。
3. ⭐⭐**戦略 carry (B3 より大きい、Rs surface 推奨)**: task_config.py:116 の comment は「GPU (use_mujoco_cpu=False) = S8」、worlds≥1 の dual-track にも「Track-2 GPU-mjwarp」。**もし campaign が GPU mjwarp へ flip するなら、W1 の calibration stack 全部が CPU 実測である**: FORK-1 特性 (0.02→13.26mm 増幅) / 健全域 band 10.407 / HOLD 15・resume 12 / ramp signature / **0.716 = MOTION STANDARD** / 全 fidelity bar。**backend flip = substrate 変更**であり、*同一 backend 内の builder fork* が 0.15mm で致命だったこの系で、solver 実装ごと替える影響は自明に大きい。⇒ **flip すれば W1 の検証 stack 全体が再検証対象**。これは B3 の carry でなく **trainer node / W0-a 級の risk register 項目** + **task_config.py = Rs SSOT ゆえ flip は L3 + Rs**。⚠**campaign 時に発見してはならない。**

### DEFECT-2 (leg3 FD validator) = CONCUR + 1 pin
- 自己捕捉 = **E-5 の模範適用**。診断 (κ = 0.92 [k=2] / 1.81 [k=3] ⇒ 速度が 1 frame 内に 92-181% 変化 ⇒ 位置差分 FD は frame 平均しか返せず 4 変種同時に落ちる = data は正) と、⭐**致命点 (spec が名指しした hazard「wrong substep」は frame 級 FD を κ/10 ≈ 1.6% しか動かさない ⇒ 20% bar では原理的に検出不能)** は正しく、**感度不足 class そのもの**。
- 置換 (2-param 回帰 → gain g / substep m̂ = 15.5 − 10·(b/g) / R²) + **identifiability 行列** (m=9→9.30 / m=8→8.57 / null→degenerate / sign-flip→g=−0.98 / ×1.02・×0.98→reject / permuted→R²=0.000 / frame-shift→m̂=6.99、real のみ accept) = **E-5 (ii) の正しい実装**。実測 (gripper g=1.0003 / m̂=9.89 / R²=1.000 vs 予測 g=1.000, m=10) も自己整合。
- ⚠**1 pin**: 「scale 誤りは大域的ゆえ gripper が scale を担う」の前提は **capture が単一 contiguous buffer copy であること**。将来 capture が group 別 slice/再構成になると **group-local な scale 誤りが gripper-only bar を素通りする**。⇒ **(i) capture が単一 copy であることを assert する / (ii) cable の g も telemetry に記録** (bias −1.9% からの *変化* が surface する) のどちらかを 1 行。

### §5.15b ERRATUM-F の 3 lens (00:1x、%12 依頼)

**(i) F-1 buffer 同定 = 反証を試みて不成立 → CONFIRMED + 2 追加事実**
- `put_data` (:5791) は **`_convert_to_mjc` 内 = 構築時のみ** ⇒ mjw_data は構築時 snapshot、CPU mode で一度も step されない。CPU 分岐 (:3268) は `mj_step(mj_model, mj_data)` のみ (mjwarp step :3262 は GPU path)。
- ⭐**repo 全体で `use_mujoco_cpu` を override する caller はゼロ** (定義 task_config:116 + signature 既定 base:1302 のみ)。**producer (`test_newton_clip_routing.py:8146`) も RL env (`base:1938`) も同一 global に従う** ⇒ **同一 backend、cross-backend transplant は今日存在しない** (私の D-2-1 を code で確定)。
- ⭐**corollary (両方向)**: 単一 global ゆえ **backend flip は atomic** (producer と env が同時に飛ぶ) ⇒「片方だけ flip して cross-backend」は構造的に起きない (良い)。**だが flip は calibration stack 全体を一度に無効化する** (戦略 escalation の根拠が強まる)。**唯一 cross-backend を生む経路 = 「今日 capture した bank を flip 後の env に restore」** ⇒ **provenance assert が唯一の防壁 = load-bearing。**

**(ii) leg6 (eq_active liveness) の検出力 — 今回の bug は必ず落とすが、3 つの穴**
- ✓ **negative control として正しい**: dead mirror では captured eq_active 変動ゼロ vs recording pin_active が f2544 で 0→1 ⇒ 必ず FAIL。E-5 (ii) 充足。
- ⚠**穴 1 (index-space trap = F6 の再演)**: eqid **27** を hardcode すると、model layout が変われば (route_c2_scene の clip / multi-cell / DR / comp3b) **eq index が shift** し別拘束を指す。⇒ **eq は name/provenance で解決し「canonical cell では 27 に解決される」を assert**。raw index hardcode は F6 (`_jws` = 関節 ID vs 座標) が既に捕まえた罠。
- ⚠**穴 2 (部分修正を素通り)**: leg6 は eq_active の liveness しか見ない ⇒ **warmstart / act の buffer 選択が別経路で誤っていても PASS**。⇒ **各 hidden field に liveness gate**: 7707 frame で **変動 > 0** (or 「恒常である正当な理由」の明示宣言) を assert。eq_active は独立 witness ありゆえ最強 / **warmstart は witness なし → 「変動 > 0」+ %12 裁定の機構確認 (mjDSBL_WARMSTART) の 2 本立て**。
- ⚠**穴 3 (lag convention = ERRATUM-A 同族)**: 記録 `pin_active` = *script が eq を有効化した* frame / solver `eq_active` = *step 後に反映された* 値 ⇒ **1 frame lag があり得る**。「EXACT 一致」を課すと fix 後に false-FAIL しうる。⇒ **lag は仮定せず実測して pin (0 か +1 か)。**

**(iii) D-2 provenance assert 設計 — ⭐核心: hidden state は「backend」でなく「model layout」で index される**
- `use_mujoco_cpu` bool だけの assert では不十分。**同一 backend でも scene が違う bank** (no-C2 build の bank を C2 build へ restore / multi-cell / comp3b) では **eq/constraint index が shift → silent corruption**。⭐**backend flip より起きやすい失敗。**
- ⇒ **provenance = (backend_id, layout_hash)**:
  - `backend_id` = `use_mujoco_cpu` + solver class + **newton / mujoco version** (version bump は constraint 順序・warmstart 意味論を変え得る)
  - `layout_hash` = `nq / nv / neq / nefc-max` + **eq の name→index 写像** + scene flags (`route_c2_scene` / `grasp_actuation` / clip config)
  - restore で **両方一致を assert (fail-loud)** ⇒ backend flip / scene 変更 / version bump / index shift の **class 全体が 1 本の loud assert に畳まれる**。
- ⭐**detection は床、robust form は name 解決**: eq は **index でなく name で解決して restore** せよ (layout が変わっても *正しく動く*)。assert = 「変わったことを検出する」floor / name 解決 = 「変わっても壊れない」robust form。**両方**。
- cost: layout_hash は構築時 1 回。capture meta に既に `use_mujoco_cpu` がある (:726) のでそこへ足すだけ。
- **%12 の D-1 裁定 (機構 mjDSBL_WARMSTART も確認、symptom だけで非 item に落とすな) に強く CONCUR** — ERRATUM-B の教訓の正しい適用。順序: **(a) warmstart は solver config で *有効* か (disableflags) → (b) live mj_data で capture frame に非ゼロ state を *持つ* か → (c) restore vs zero で軌道が変わるか (A/B、L5a)**。(a)(b) は今すぐ安価、(c) は L5a 待ち。

## 5.16 ⚠⚠ B3-α (CRIT / STOP-and-flag / Rs専権) — bank の eq_active には restore 先が存在しない (2026-07-14 03:4x)

**契機**: %11 の B3a 中間報 (DEFECT-1 fix 検証 / warmstart massively LIVE / index-space trap 捕捉) を verify 中、eq の**生成主体**を追って発覚。

### 実測 (3 点、on-disk 確定)
1. **producer は `PERCLIP_PIN=1` の時だけ 40 本の pin 候補 eq を pre-allocate** (`test_newton_clip_routing.py:1405`「pre-allocate a DISABLED per-clip connect equality (C1 seat cable body ↔ WORLD)」)。**全 route runner script が `PERCLIP_PIN=1` を設定** ⇒ **golden (RUN1_REFERENCE_V2) もそれで録画**。eq = 40 候補 + 6 構造 = **46** (%11 測定と一致)。#27 が中盤 activate = **INVARIANT #5 の唯一の認可例外 (clip-retention pin、`log.md:6534`)**。
2. ⭐**RL env (`build_multiworld_scene`) は構造 eq 6 本しか作らない** (4-bar connect ×4 + follower mirror ×2、`newton_skill_env_base.py:1621/:1639`)。**pin 候補ゼロ。** base:1448 の comment 自身が pin eq を「**PERCLIP_PIN test harness (test_newton_clip_routing.py) may pre-allocate**」と *test 側* に帰属。`newton_route_env.py` の pin 参照 = **ゼロ**。
3. **c1pin wiring は B0-1 で revert 済** (working tree 確認: env/base = clean、残るは %11 の B3a route_executor.py +570 のみ) ⇒ **現 env は確定的に pin 無し**。

### ⇒ index shift ではなく「**restore 先に機構が存在しない**」
- **banked `eq_active[27]` に対応する eq が env に無い** (env neq=6)。
- ⭐**私の F-6 layout_hash assert は *発火する* (bank 46 vs env 6) → restore 前に fail-loud** = assert が仕事をする。⚠**だが %11 conformance の前提「layout_hash assert が同一 layout を保証するので今日は banked index で足りる」は成立しない — layout は同一でなく、assert は祝福でなく BLOCK する。**
- ⭐⭐**より深い問題: k=3/4/5 の fork state は pin に物理的に依存**。その境界では **cable は active constraint で C1 seat に保持されたまま**腕が離して C2 へ持ち替える。**pin 無し env にその cable 配置を restore すると「座っているが保持されていない」= seat から出る。fork state が現 env で実現不能。** (L5a は経験的に捕捉するが、原因を知らずに「fork が壊れている」と debug することになる)

### disposition = **Rs専権 (builder / %12+%9 の裁量外)**
pin は **INVARIANT #5 の唯一の認可例外**。RL env への配線 = **認可例外を新環境へ拡張 = 前提 scope 変更** ⇒ CLAUDE.md の FOUNDATIONAL INVARIANT 規則で **即 L3 + STOP → BLOCKED_FOR_USER**。
⚠⛔**歴史の罠 (明示)**: c1pin wiring は一度 build+test されたが、それは **「FORK-1 の fix 仮説」として REFUTED → dead-branch revert (B0-1)**。**その revert はその仮説に対しては正しい。だが bank v2 は *別の、正当な理由* (fork-state の実現可能性) で pin を要る** — 当時それは問われていない。**⛔ 禁止則「ある方針の NO_ACTION / FAIL / 弱さを、別方針の GO 根拠として扱うな」の裏返し** ⇒ **REFUTED-as-FORK-1-fix を「env に pin は不要」の verdict として扱わない。**

### 選択肢 (Rs 裁定)
(a) **pin を RL env へ配線** (新しい正当な理由で復活、INVARIANT #5 scope ⇒ Rs、かつ env 物理が変わる = re-baseline) / (b) **bank を k=1,2 に限定** (pin OFF、だが **G3-G5 curriculum を失う = bank v2 の主目的そのもの**) / (c) curriculum re-scope + carry 明記。
**%9 推奨: B3a (producer capture + offline builder) は完全に無傷 → commit 可。B3b の restore write-set 設計は本件 disposition まで STOP。W1 完了報告を待たず Rs surface。**

### ⭐ meta — 本 arc の class に新 sub-type
C-α = 計器の**感度**不足 / C-β = 測定 mode の**交絡** / E-4 = **較正の異 mode 流用** / F-7.4 (%12) = **零は「対象が無い」か「計器が死んでいる」か区別不能 → positive control を併走** — そして **B3-α = 対象機構が *移植先に存在しない***。
⇒ ⭐**移植 (transplant) の検証は donor (capture 忠実性) だけでなく recipient (受け皿の能力) を検査せよ。我々は capture を厳密に検証したが、restore に着地先があるかを誰も検証していなかった。**

## 5.17 ⚠⚠⚠ FORK-1 の根本原因が confounded — 終端失敗の帰属は OPEN (%9 実測、2026-07-14 04:0x)

**契機:** %12 の B3-α 追加測定 (env は C1 を保持できない) を独立検証中に、**FORK-1 の characterization run 自体が pin-ful な記録を pin-less な env で replay していた**ことに気付いた。

### 実測 (全て on-disk、当方が自分で走らせたもの)

| # | 測定 | 値 | 根拠 |
|---|------|----|----|
| F-1 | 記録の pin 発火 frame | **golden f2544** = `phase_id` 5→6 境界 = replay **t=255** | `route_demo_raw.npz` `pin_active` 直読 |
| F-2 | pin が ON である割合 | **5163 / 7707 = 記録の 67 %** | 同上 |
| F-3 | div metric に recentering | **無し** (生の per-seg 距離) | `comp5_c2seat_fullfire.py:214` |
| F-4 | **t < 255 (記録も env も pin 非活性 = 構造差ゼロ)** | div_seg24 (把持 seg) 0.007 → **peak 10.56mm (t=124)** → **3.36mm へ減衰**。div_max → 37.21mm | `comp5_c2seat_fullfire_cablediag.npz` |
| F-5 | **t ≥ 255 (env だけ pin 無し = confounded)** | div_seg24 3.78 → **129.24mm (34×)**。**grip collapse も drop も 100 % この窓** | 同上 |

### ⇒ FORK-1 の主張を分解する

- ✅ **「open-loop replay は発散する」= CONFIRMED、非 confounded。** div_max が構造差ゼロの窓で 0.106 → 37.21mm。実在の増幅。
- ⚠⚠ **「⇒ ゆえに grip が崩れ cable を落とす ⇒ open-loop は使用不能 ⇒ RL closed-loop が唯一の fix」= NOT ESTABLISHED。** 把持 seg は confound 開始の**まさにその瞬間まで回復中**だった (10.56 → 3.36mm)。暴走ではなく **bounded excursion**。終端失敗は 100 % confounded 窓の中。

### ⭐⭐ c1pin「REFUTED」は unsafe — 反証されたのでなく**試されていない**公算

reverted 実装 (`c70ba1b849`) を実読した結果:
1. ⛔ **fail-SILENT by construction**: `self._c1_pin_done = True  # latch: one attempt at the onset frame (regardless of outcome)` が **mjm/mjd の None check より前**に焼かれる。⇒ eq 解決に失敗しても pin は無言で発火せず、**assert ゼロ**。**positive control が取れない設計**だった (%12 の「positive control が無い」より強い)。
2. **eq 解決は body id 経由** = %11 の leg6 が捕捉した **Newton 55 / MuJoCo 56 の +1 trap と同一経路**。%11 の入念な再実装ですら初版で踏んだ。
3. ⭐ **c1pin run = 342 step で死亡 vs pin-less 499** (baseline 499 / cablediag 499 ⇒ diag は非摂動、比較は clean)。**保持 pin が正しく発火したなら生存は延びるはず。早死には「誤 body への溶接」の signature。**
4. ⭐⭐ **その c1pin 自身の docstring が機構を正しく述べている** (逐語): *"the multi-world env-core was MISSING this activation (FORK-1 root cause): the C1-seated cable is not anchored, so **the light L-hold drops it at the R-release handover**"* — 我々が 3 方向から独立に再導出した機構を、07-12 の著者は既に書いていた。そして pin onset (f2544) は**その handover の直前**。

### ⭐ governance 訂正 — 「前提 scope 変更 ⇒ Rs專権 ⇒ 重い」は likely 誤り

Rs directive 逐語 (`log.md` 2026-06-16 13:33): **「クリップのみキネマティックトリックでケーブルを擬似固定して良い／その他は絶対禁止」**
⇒ authorization は **機構 scope** (clip での pin)。**file / harness scope ではない。**
+ `RS71-System-Spec-SSOT.md` §4 が pin を **routing の機構として NAME** (cable に水平曲率 DOF が無い)
+ 同 log の理由: **2 arms < 5 clips → seated clips UNATTENDED → self-retention STRUCTURALLY MANDATORY**
⇒ **env に pin を配線するのは INVARIANT #5 の *拡張* ではなく *遵守*。env が banked spec に非適合のまま build されていた。**
⇒ Rs への問いは「不変前提を変えてよいか」(重い) ではなく **「env は RS71 §4 に非適合。是正すると W1 calibration が re-baseline になる。GO?」**(明快)。⚠env 物理が変わる ⇒ re-baseline の Rs 可視は必須。

### calibration carry
- ✅ **10.407 / 10.56mm band = SAFE** (max は t=124 = pre-255 = 非 confounded 窓)
- ⚠ **HOLD_THRESH 15mm = CONFOUNDED** (初交差 t=343、`f337 ramp` は missing-pin 窓の中) → parity 基板で再導出要
- ⚠⚠ **pin-less env では div_grip は policy に関わらず post-255 で必ず 15mm を超える** (20mm/step の EE residual は cable-to-world weld の代わりにならない) ⇒ **HOLD 発火と MAX_HOLD 枯渇は policy の質でなく env の欠損ゆえ = reference が到達不能。** ⇒ (a) を独立に強制する。

### ⚠ 非過剰主張 (自分の規律を自分に当てる)
**「FORK-1 は誤り」とは言わない** (div_max 37mm pre-255 は実在の非 confounded 発散)。**「trainer は不要」とも言わない** (未証明)。言えるのは — **終端失敗の帰属は confounded で OPEN / それを反証したはずの run は構造的に fail-silent / 最安の実験がこれを決着させる。**

### ⇒ 推奨 = %12 の (d) を MANDATORY 化 + re-scope
**(d) は「c1pin の再試験」ではない — 「task を表現できる基板における open-loop replay の最初の妥当な測定」。** cuda:0 数分 vs trainer 数週間の build。**(a)-(c) の選択より前に来る。**
DoD (規律: DoD は間違った成果物を落とすように書く):
1. positive control = **flag でなく EFFECT** (発火後 seg27 の C1 距離が ~一定 = 記録 4.16mm)
2. name/geometry 解決 + index-space assert (%11 の `_assert_pin_index_spaces` を再利用)
3. ⛔ **fail-silent latch を殺す** (解決不能なら raise) — 偽 REFUTED の最有力機構
4. ⭐ **negative control**: **t<255 は pin-ON/OFF で ~不変でなければならない** (両方 pin 非活性) ⇒ **pre-255 に差が出たら計器が壊れている = run 無効**
5. その上で post-255 を測り HOLD/band を parity 基板で再導出

## 5.18 W1-B3a 3-leg post-verify (%9 独立、2026-07-14 04:2x) = **PASS-WITH-1-PROCESS-FINDING**

| leg | 結果 | 当方の独立根拠 |
|-----|------|--------------|
| **LEG-1 Rs-LOCK** | ⭐**PASS** | `run_route` = **2079 行 / sha256 `70cef863254b91be5d568e8db900149372d10454b1394ad62b5bcd3e7cae7bb2`**、`a2f544662b` → `575069abe5` → HEAD の **3 点で byte-identical** (span は 1038→1608 へ移動、+570 行が上に入った分のみ) |
| LEG-2 capture read-only | PASS | golden sha `5f1c3f92…` == RUN1_REFERENCE_V2 (0.716 MOTION STANDARD と突合) / npz sha EXACT 1/1 |
| **LEG-3 identifiability** | ⭐**PASS** | **8/8**: REAL のみ ACCEPT、m=9 / m=8 / **NULL(qd:=0)** / SIGN-FLIP / ×1.02 / ×0.98 / PERMUTED / FRAME-SHIFT を named rejector 付きで全 REJECT。⭐**旧 10.407 bar を 3.4-44× 余裕で通っていた null bank が degenerate として落ちる** ⇒ **C-α / DEFECT-2 discharge** |
| LEG-5 byte-repro | PASS | 5/5 EXACT |
| **LEG-6 liveness** | ⭐**PASS + 独立一致** | 当方の golden 直読: `pin_active` 5163/7707 / `pinned_body` [55] / `pin_eqid` [27] — %11 の leg6 (`eq_active_matches_pin_witness=True`, `eq_body_index_offset=+1`, `buffer_is_live=True`, `qacc_warmstart` varies/live, `mjDSBL_WARMSTART` bit 512 未設定) と **3 経路が独立に一致** |
| 行数 | PASS | 759 追加 / 3 削除 ≤ cap 800 (source のみなら 730) |

### ⚠ B3a-F1 (MED、process/provenance — 措置は %12 側)
**B3a の source 730 行は `a00a0a97f8` に入っていない。`575069abe5` (= %12 の BLOCKED_FOR_USER commit、03:43:50) に入っている。**
- `a00a0a97f8` (題 = *W1-B3a: capture producer state and build the phase-k bank v2 offline*、%11 が「B3a 本体」と報告) の中身 = **doc +20 行のみ、source ゼロ**。
- %11 は**意図的に未 commit を維持**していた (逐語:「B3a は未 commit (defect 込みで bank しない方針を維持)」) ⇒ **%12 の非 explicit-path commit が %11 の飛行中 WIP を巻き込んだ。**
- ✅ **結果は無害**: legs 完了 **03:38:13** < sweep **03:43:50**、working tree == HEAD、DEFECT-1 fix も HEAD 在り (`route_executor.py:851` = `use_mujoco_cpu` で buffer 選択、fallback 無し) ⇒ **commit された code = 全 leg PASS した最終 code。**
- ⛔ **records-must-match-fact 違反**: 後の読者は 730 行を BLOCKED_FOR_USER commit に帰属させ、`a00a0a97f8` の題は入っていない source を主張する。
- ⭐ **これは我々全員が取り締まってきた shared-tree sweep hazard そのもの** ([[feedback-explicit-path-commit-git-diff-file-first-sweep-both-directions]] = *git diff を FIRST に見て双方向に sweep*)。**最も規律ある pane が踏んだ。**
- **措置**: provenance note 1 行。⛔**history rewrite は不要かつ有害** (共有 tree、他 pane が上に積んでいる)。

### ⚠ 当方の自己訂正 (loud)
当方は最初 **「B3a source が未 commit」と誤 flag した。誤りである。** commit されている (別 commit に)。同一ターン内で `git log -- <path>` / `git diff --numstat` / HEAD への symbol grep により自己訂正。**truncated な `--stat | tail` 出力から「不在」を断定しかけた** — [[feedback-absence-claims-grep-all-build-paths]] の再演。

## 5.19 ⚠⚠⚠ 層3 (p5 発、%12 VERIFIED) — cable = 平面鎖 ⇒ 壁は clip 3。**機構は CONFIRM、ただし「配位空間の外」は OVER-CLAIM** (%9 独立検証、2026-07-14 04:4x)

### ✅ 機構 = CONFIRM (source からの独立証明)
`thread_isaac_lab/scripts/test_newton_clip_routing.py:1009` 逐語:
```
axis=wp.vec3(1.0, 0.0, 0.0),  # local-X bend axis ⟂ cable → vertical sag plane
```
かつ `:1007-1008` で `parent_xform` / `child_xform` が**両方 `wp.quat_identity()`** (link 間の相対回転オフセット無し)。
⇒ 全 revolute が同一 local-X 軸。x 回りの回転は x を不変に保つ ⇒ **帰納法で全 link が同一 bend 軸を共有** ⇒ **centerline は単一平面に拘束 = 平面鎖。** (`add_revolute_cable` :936、`direction=(0,1,0)`、root のみ `add_joint_free`。)

### ⭐ 壁の定量 (**最も有利な best-fit 直線**で計算 — C1-C3 線ではない)
`task_config.py:211-217` (CLIP_POSITIONS、X が 0.35/0.40/0.35/0.40/0.35 = 千鳥) + `:233` `CLIP_GROOVE_INNER_RADIUS = 0.006`。

| 対象 | best-fit 直線での residual | vs 溝 6mm | 判定 |
|------|---------------------------|-----------|------|
| **C1-C2 (2 clip)** | **0.0 / 0.0 mm** | 0.0× | ✅ **SEATABLE** (2 点は必ず 1 直線に載る) ← **producer がやったのはこれ** |
| **C1-C2-C3 (3 clip)** | 16.7 / 33.3 / 16.7 mm | **最小 2.8×** | ⛔ **IMPOSSIBLE** |
| **C1..C5 (5 clip)** | 20 / 30 / 20 / 30 / 20 mm | **最小 3.3×** | ⛔ **IMPOSSIBLE** |

⇒ ⭐**壁は「clip 3」に在る。** p5 の「producer は C1→C2 (2 clip) しか実行していないため誰も壁に到達していなかった」= **完全に正しく、かつ定量できた。**

### ⚠⚠ OVER-CLAIM の訂正 (これを直さないと Rs 上程が一撃で崩れる)
1. ⛔ **「5-clip 同時は配位空間の外」は成立しない。** **5 座面は全て `Z = GROOVE_CENTER_Z = 0.809` = COPLANAR (水平面上)。** ⇒ 平面鎖を **90° roll** すれば (bend 平面 = 水平) 幾何的には 5 点を zigzag できる。厳密な配位空間不能ではない。
2. ⛔ **「C2 は C1-C3 線から 50mm = 溝 6mm の 8.3×」は過大。** それは「直線が C1 と C3 を通る」と仮定した値。best-fit ならもっと寄れて **最小 residual 16.7mm (2.8×)**。不能の結論は不変だが、**過大な数字は反証される。**

### ⭐ 防御可能な正しい framing (これで上程すべき)
> **cable の bend 平面は 1 枚しかなく、root 姿勢に剛に結ばれている。task は「垂直 sag」(重力・把持・持上げ・route 設計の全て) と「水平 routing 曲率」(千鳥 clip) の *両方* を要求する。単一平面鎖は両方を同時に供給できない。**
> - sag 姿勢 (as-configured、bend 軸 = world-X) ⇒ **水平投影が直線** ⇒ **3 clip 以上は幾何的に不能** (最小 residual 16.7mm vs 溝 6mm)
> - 90° roll 姿勢 ⇒ 水平曲率は出るが **垂直 sag が厳密ゼロ** ⇒ 物理的に退化、把持/持上げ/route 設計と非互換
> ⇒ **`RS71-System-Spec-SSOT.md` §4 の「2nd bend DOF が要る」が正しい記述。pin はそれを供給できない** (soft equality は reduced-coordinate の hard revolute を破れない — 単に違反される)。

### ✅ B3a への影響 = **ゼロ** (%11 の point 2 を追認)
golden = **C1→C2 = residual 0.0mm = 完全に seatable**。bank の k=1..5 は **その 2-clip route 内の chunk 分割**であって 5 clip ではない。⇒ **層3 と B3a の妥当性は独立。B3a は無傷。**

### ⭐ 上程は 2 段に分けよ (混ぜると両方死ぬ)
- **(i) 近接 = B3-α / FORK-1** — scope = **2-clip route = 現行 program**。**(d) parity 再走で今すぐ動く。層3 はこれを block しない。**
- **(ii) T-ROOT 級 = 層3** — **現 cable model で到達可能な goal は 2 clip が上限。5 clip には 2nd bend DOF (model 変更 = Rs 專権、大)。** T-ROOT の goal 定義に触るが、**(i) の実行を止める理由にはならない。**

### ⚠ B4-B7 の停止理由
**層3 ゆえに止めるのは過剰。** 正しい停止理由 = **B3-α (pin disposition + HOLD 較正の confound)**。**理由が違うと解除条件が変わる。**

## 5.20 ⛔⭐⭐ 私の over-claim (own) → guard 自身に穴。**B3-α の fail-loud 保証が破れる** (%12 adversarial catch、2026-07-14 05:1x)

### ⛔ 私の過失 (先に、正確に)
私は「%11 の `_assert_pin_index_spaces` は **全失敗経路が raise、silent path ゼロ**」と報告した。**誤り。**
⭐ **その silent guard は、私が自分で印字した出力の中にあった** (`route_executor.py:563-565`):
```python
eq_ident = ((prov or {}).get("layout") or {}).get("eq_identity") or []
if pin_eqid is None or pin_seat_newton is None or not eq_ident:
    return None
```
かつ `:561` の docstring 自身が逐語で認めている: *"Returns the MuJoCo body id of the seat, or None when the run never pinned / **has no provenance**"* ⇒ **「記録に pin 無し (正当)」と「provenance 破損 (異常)」を関数自身が同一視している。私は読んで flag しなかった。**

⭐⭐ **私の誤りの機構 = 確証バイアス (`prohibited.md` 明文)。** 私は「(d) は de-risk された」という結論を**欲しがっていた** (自分が押していた Rs 上程を強くするから)。raise の多い本体を読み、欲しい証拠を見つけ、**そこで止めた。否定する証拠を先に探さなかった。**
⚠ **本 session 2 度目** (1 度目 = mjw_data、断片の静的検証を全体に一般化) ⇒ **偶発でなく私の pattern。**

### ⭐ silent-None roster (%12 の 2 点より多い。全て HEAD 実読)
| # | 位置 | 無言経路 |
|---|------|---------|
| S-1 | `:537-542` | `resolve_pin_eq_index` 冒頭が **`except Exception` 丸呑み → return None** (mujoco enum が動くだけで「pin 無し」を返す) |
| S-2 | `:544-549` | `hits != 1` → return None。⚠コメント自身が *"the caller must fail loud"* と書き、**fail-loud を caller 任せの契約**にしている (機構でない) |
| S-3 | `:563-565` | ⭐**私が見逃した本丸。** 3 連 `or` fallback が provenance 欠落を無言で吸い、`return None` が「pin 無し」と区別不能 |
| S-4 | `:592-598` | provenance reader — **meta 欠落 / parse 失敗 / key 欠落 の 3 経路が全部無言 None**。⚠直上 docstring は *"The restore side (B3b) asserts this ... and refuses a mismatch"* ⇒ **B3b の拒否機構が、何かあれば None を返す関数の下流に在る** |
| S-5 | `:611-617` | **"pin_eqid 列が記録に無い" → None** が **"never pinned" → None** と同一視 (列欠落 ≠ pin していない) |

### ⭐⭐⭐ 帰結 — 破れるのは **私自身の B3-α 保証**
私は §5.16 と Rs 上程で断言した: **「bank 46 vs env 6 ゆえ layout_hash assert は必ず発火し、physics 前に fail-loud で BLOCK する」**。
⇒ **layout_hash は provenance が運ぶ。** provenance が S-4 で無言 None → S-3 で `eq_ident=[]` → **無言 return None** → **比較対象が無い** ⇒ ⛔ **assert は発火しない。**
⇒ **B3-α の「fail-loud で守られている」は、現状 *保証されていない*。私の主張の訂正として Rs 上程に必須。**

### ⭐⭐⭐ 一般化 (本 arc 最後の一枚)
**我々は一晩中 guard を建てたが、guard が *発火すること* を一度も test していない。**
- leg6 = **データ**の liveness に対する positive control ✅ / **guard の liveness に対する positive control = ゼロ** ❌
⇒ **F-7.4 は F-6 (guard 自身) にも適用される。** ⭐**一度も発火しない guard は、発火 *できない* guard と区別がつかない。**

### 措置 (%12 の (i)(ii) に賛成 + 3 点追加)
1. (%12 i) 「記録に pin 無し」= **assert された正当条件** (`pin_active` が実際に全ゼロであることを確認)。推論された None にしない。
2. (%12 ii) **provenance 欠落/破損 = raise。**
3. ⭐ 3 連 `or` fallback を撤去 (無言吸収の**機構本体**)。明示的存在確認 → raise。
4. ⭐ S-1 の `except Exception` 丸呑みを撤去 (narrow + raise)。S-2 の "caller must fail loud" を**契約でなく機構**に。
5. ⭐⭐ **本命 DoD = guard の identifiability 表** (%11 の leg3 8/8 の型を、データでなく **guard** に当てる):

| 入力 | 期待 |
|------|------|
| provenance **欠落** の bank | **RAISE** |
| provenance **破損 (parse 不能)** | **RAISE** |
| **別 layout** の bank (neq 46 vs 6 = まさに B3-α) | **RAISE** |
| **正当に pin 無し** (k=1,2) | **PASS**、かつ上 3 者と *assert により* 区別される |

⇒ **現状は「欠落」「破損」「正当に不在」が全部同じ無言 None ⇒ guard は 3 者を区別できない。**

## 5.21 ✅⭐ B3a 最終照合 = **CLOSE 可** — guard は実際に発火する (**%9 が自分で RUN して確認**、2026-07-14 06:2x)

%11 commit `0f13684709`「B3a: make the guards fire, and prove it」に対する最終 verify。⚠**今夜 grep で 2 度誤った反省から、grep でなく実行で discharge した。**

### ⭐⭐⭐ 私が自分で走らせた結果 (`test_routeexec_state_bank.py`)
```
RESULTS: {'synthetic': True, 'nominal': True, 'world_slice': True, 'bank_v2': True,
          'guard_identifiability': True, 'self_disarm': True, 'null_control': True}   = 7/7
[B3a guard-identifiability]  (a) provenance ABSENT            -> RAISE
                             (b) provenance CORRUPT           -> RAISE
                             (b2) layout_hash ABSENT          -> RAISE
                             (c) DIFFERENT layout (B3-alpha)  -> RAISE      ← ⭐ B3-α そのもの
                             (c2) backend FLIP                -> RAISE
                             (d) matching layout              -> PASS
                             (d2) never pinned  -> PASS (asserted, not inferred)
                             (d3) witness field ABSENT -> RAISE (not silently "no pin")
                             (e) CONSTANT warmstart, no mechanism -> RAISE
                             (e2) CONSTANT + declared mechanism   -> PASS
```
⇒ ⭐⭐ **(c) は B3-α そのもの。私が §5.16 で断言し §5.20 で撤回した「fail-loud で守られている」は — 今は *真*。しかも「断言されたから」でなく「test されたから」真。**

### ✅ 検証結果
| 項目 | 結果 | 根拠 |
|------|------|------|
| **Rs-LOCK** | ⭐**PASS** | `run_route` = **2079 行 / sha 70cef863254b91be5d56…**、`a2f544662b` → `575069abe5` → `0f13684709` → HEAD の **4 点で byte-identical**。**+177 行の guard 総取替えを通して lock 関数は 1 バイトも動いていない** |
| **S-1〜S-5** | **全滅** | 3 連 `or` chain 撤去 (in-code に機構と出典明記) / 「pin 記録済だが grounding 不能」= RAISE / `_capture_provenance` は meta 欠落・parse 不能・layout_hash 欠落 の 3 経路とも RAISE |
| ⭐**最後の adversarial 疑い** | **潰れた** | `required=require_canonical` は変数ゆえ実 bank 経路で False なら穴が生きる、と疑った → **`:756` で `require_canonical=True` が既定 / `:781`「set False only for synthetic unit fixtures」** ⇒ **実 bank は必ず raise。`:589` の `return None` は実 bank から到達不能** |
| `assert_bank_matches_live` | **契約でなく機構** | layout mismatch の error 文が **"bank neq=46 (producer, 40 pin eqs + 6 structural) … RL env's neq=6"** と B3-α を名指し |

### ⭐ (d3) = %11 の独自追加 (私の list に無い)
「witness field 欠落」を「pin していない」と読ませない。**私が示したのは原則で、%11 が実装したのはその原則の正しい一般化。文字でなく意図を実装した。**

### ⚠ 唯一の carry (defect でなく **seam** — B3b の DoD 行にすること)
**`assert_bank_matches_solver` (:654) に production caller がまだ無い** — restore 経路 = B3b、B3b は STOP 中ゆえ正しい状態。
⇒ ただし **「guard は unit で発火することが証明された。live restore 経路で *実際に走る* ことはまだ未証明」**。
⇒ ⛔ **これは我々が一晩焼かれ続けた ABSENT-IN-CODE の class そのもの** (機構は在るが到達されない = appearance-only)。**B3b DoD に明示行:「guard が live restore path で実際に実行されることを run で示す」。仮定にしない。**
(LOW) `require_canonical=False` が production caller から到達可能にならないこと (今日は到達不能)。

### VERDICT
**B3a = CLOSE 可** (Rs-LOCK 保全 / guard 発火を独立 run で実証 / S-1〜S-5 全滅 / seam 1 件を B3b DoD へ carry)。
⛔ **B3b 以降 = STOP 継続。停止理由 = B3-α (pin disposition + HOLD 較正 confound)、層3 ではない。**

## 5.22 ⭐⭐⭐ (d1) 幾何 feasibility = **CLOSE。層3 警報 解除。壁は 4 つ提案され 4 つとも死んだ (私が 2 つ出して 2 つとも撤回)** (2026-07-14 05:5x)

**Rs 裁定「はしらせて　push」(05:3x) → (d) 発火。(d1) = %9 担当。**

### M1 — 実モデル読み (走らせた、`d1_m1_cable_dof_readout.py`)
| 測定 | 値 |
|------|-----|
| cable DOF 構造 | **1 FREE root + 39 HINGE** (nq=46 / nv=45) |
| **39 軸の平行性** | **worst_max_nonparallel = 0.0** over rest + 24 random q ⇒ **PLANAR chain** |
| ⭐ %10 の格上げ | **標本でなく *構成上* 強制**: 全 body が同一 `seg_q` / parent・child xform の回転 = `quat_identity()` / 全 axis = local-X ⇒ x 回りの回転は x を不変に保つ ⇒ **帰納法で全 q で平行** |
| joint limit | **`hinge_limited = 0`** (range ±5.7e11 = 無制限) ⇒ ⛔**joint-limit 証明書は取れない** |
| 共通 bend 軸 (rest) | world **(1,0,0)** = 水平 ⇒ 素の bend 平面 = 垂直 (sag) |
| ⭐ **live route 上の平面性** | golden `cable_xyz` の SVD: **s3/s1 = median 2.5e-07 / max 1.4e-06** ⇒ **実 route でも 100 万分の 1 の精度で平面** |

### ⛔⛔ 提案された「壁」= 4 つ、全滅
| 壁 | 提案 | 死因 = **黙って固定した自由度** |
|---|---|---|
| 3clip = best-fit 残差 16.7mm ⇒ 配位空間の外 | **%9** | **bend 平面を「垂直」に固定**。root は **FREE joint (6-DOF)** ⇒ 平面は任意に向けられる。座面は全て同一 Z = coplanar ⇒ **平面制約は infeasibility を証明できない** |
| 壁は clip 4 (3 seated で面外余裕 2.67mm) | %12 | **seating 順序を「逐次」に固定** |
| 置けるが配線できない (水平平面 ⇒ 垂直曲げゼロ) | **%9** | **seated 集合を「非共線」に固定**。⭐**C1,C3,C5 は全て x=0.35 = 共線** ⇒ 平面を pin しない |
| ~90° roll は物理的に無理では (W-3) | %12 | ⛔ **反証**。⚠ただし **%9 の初回証拠 (angle-to-X = MAX 89.6°) は無効** — §5.23 参照。**有効な証拠は %12 の訂正指標 + %9 の独立再現** |

### ⭐ 調停 (%9) — %10 と %12 の「矛盾」は矛盾でなかった
XY rank 実測: seated **{C1,C2,C3} = rank 2 (非共線)** ⇒ 平面 **PINNED** (tilt ≤ ~3.4°) ⇒ **%10 の予算式 (≤5.4mm) が効く、正しい** / seated **{C1,C3,C5} = rank 1 (共線)** ⇒ 平面 **FREE to pivot** ⇒ 予算に上限なし。
⇒ **%10 の式は正しく、その *前提* が回避可能だった。効いているのは seating の順序。**

### ⛔ %12 の「止め」= 受諾 (これが無ければ 5 回目の誤りだった)
**「壁が無い」≠「達成できる」。** 5-clip witness (W-1 手組み) は誰も作っていない ⇒ **「不能」も「可能」も未確立**。W-1 = **carry (blocker でない)**。
⇒ ✅ **(d1) BLOCKER = CLOSE / 層3 警報 = 解除 / substrate 変更 (2nd bend DOF) 提案 = 撤回 / Rs 上程から (ii) を削除。**
✅ **RS71 §4 = *fidelity* の言明 (sim2real robustness を validate できない) であって *不能* の言明ではない** (%9 の読みを %12 採用)。

### ⭐⭐ META (%12 が bank) — [[feedback-a-wall-is-a-forgotten-degree-of-freedom-2026-07-14]]
> **「壁 (= 不能)」とは、自由度を 1 つ黙って固定したときに現れるものである。**
⇒ infeasible verdict の必須列: **全 DOF 列挙 / 凍結した DOF と理由 (file:line) / 手組み witness も失敗すること / 障害を明示する証明書**。欠ければ **NOT-FOUND であって IMPOSSIBLE ではない**。
⇒ **有限 multi-start は非存在を証明できない** (探索版の「零の測定」) ⇒ **静的 feasibility は witness 構成で解け** (optimizer への信頼ゼロ)。

### ⚠ %9 の今夜の over-claim = 5 件 (全て他者/自己が訂正)
mjw_data (静的読みで断定) / 「silent path ゼロ」(entry point 未確認、**反証は自分の出力の中にあった**) / 「sha は同一」(**比較を実行せず**) / 「+1 trap が c1pin を殺した」(diff を 45 行で止めた) / 壁 ×2 (自由度を黙って固定)。
⇒ ⭐**共通形 = 「部分的に *読んだ* もの」を「*照合を完了した* もの」の確信度で述べる。** ⇒ 機構化: **同一性・性質の主張は例外なく *実行* で裏を取る**。**date-THEN-write** も機構化 (~60 分先打ちしていた、%12 捕捉)。

### 副次決着
- **p5 の「5 seg = 75mm」= 誤り。** hop 弦長 = **90.14mm** (=√(50²+75²)) ⇒ 15mm/seg ⇒ **1 hop に ≥7 seg**。
- ⭐ **%10 CRIT-1 を独立確認**: golden の seated 平面 Z 実測 = **829.0mm** ⇒ **route env は clip を +20mm float** (`route_env_config.py:144` `ROUTE_GROOVE_Z = 0.829`)。**`task_config.py:226` の 0.809 を使えば 20mm = bar の 3.3× ⇒ 壁を捏造していた。**
- **h_lip 実測** (golden、routed span) = **46.4mm** — 非共線前提が消えたため wall 議論には moot だが、値としては bank。

### 現 gate = **(d2) のみ**。%9 = verify leg (DoD / 走行結果 / ⭐**視覚レグ**)。
⭐**%12 CRIT-1 (3 人とも見落とし)**: **測定対象そのものが物理を上書きする機構 (weld)** ⇒ **数値だけで採点しない。** 「直した」のか「**固めて隠した**」のかは動画でしか分からない ⇒ **FORK-1 falsify verdict は Rs の動画 human-GT を経てからでないと act しない。**

## 5.23 ⛔⛔ %9 の over-claim #6 — **W-3 の私の証拠は無効だった (計器が対象を測れていなかった)。結論は生き残ったが、証拠は %12 の訂正版が正** (%12 catch、2026-07-14 06:0x)

### ⛔ 私の計器の 2 つの穴 (両方 実測で確認)
| # | 穴 | 実測 |
|---|-----|------|
| **(a)** | **指標が問いを測れていない** — 問い = 「bend 平面は *水平* か」⇔ 法線 ∥ **world-Z**。私が測ったのは 法線 vs **world-X** (素の bend 軸)。⭐**cable は table 上を drag される ⇒ *yaw* する ⇒ 平面は垂直のまま法線が X→Y へ振れ、roll ゼロでも angle-to-X は 90° に達する。roll と yaw を分離できない指標だった。** | **corr(angle-to-X, angle-to-Z) = −1.0000 (厳密)** — cable 長軸が Y に留まり法線が XZ 平面に拘束されるため、**この data に限り** 2 指標が恒等。⇒ ⭐**「たまたま正しかった」= 検証ではない** |
| **(b)** | **縮退 gate が無い** — 鎖が真っ直ぐな frame には **bend 平面が存在しない** (任意の平面が fit) ⇒ SVD 法線は **雑音** | 私の file で **s2/s1 ≤ 0.05 の frame = 3298/7707 = 42.8%** (%12 の 19.4% より悪い)。**全部含めていた** |
| **(c)** | ⛔ **p6 との一致を「独立確認」扱いしかけた** | ⚓ **アンカー式検証 明文: 「相関した同意 (同じ代理を見る複数者・agent の一致 = 独立確認でない)」。** p6 と私は **同じ代理量**を見ていた。**私はこの方法論を今夜 他 pane に引用しておきながら、自分が罠に落ちた。** |

### ✅ 正しい証拠 (%12 の訂正指標 = angle(法線, world-Z) + gate s2/s1 > 0.05。**%9 が別 golden file で独立再現**)
| 量 | %12 (`p3_dod_cuda_demo_raw`) | **%9 独立再現** (`dq7_ii_cp2_wave1/rec_c11`) |
|---|---|---|
| 最も水平な *曲がった* frame | t=7582 → **0.28°** | **t=7582 → 0.28°** ✅ |
| その frame の z 拡がり | 2.66mm | **2.65mm** ✅ |
| その frame の平均 z | — | **828.5mm** (溝 829mm) |
| 湾曲 frame の 水平±30° / ±10° | 17.9% / 7.9% | **17.9% / 7.9%** ✅ |
⇒ ⭐⭐ **異なる data・独立実装で完全一致 ⇒ 相関した同意でなく *本物の独立確認*。**

### ⭐⭐⭐ 本物の発見 (%12、%9 が再現)
水平 frame = **789 本 / t=6918-7706 の 1 連続ブロック (gap ゼロ) = route の最後の 10%**。**平均 cable z = 833.6mm** ⇒ **溝高さ (829mm) へ持ち上がっている。table (804mm) に寝てはいない。**
⇒ ⭐⭐⭐ **水平 bend 平面の frame = *着座の瞬間* そのもの。** golden の最終状態 = **溝高さ・bend 平面 水平・XY に湾曲** = ⭐**5-clip 目標が要求する配置そのもの。2-clip route が既に到達している。**
⇒ **単一 bend DOF + free root が「持上げ/垂れ = 垂直寄り / 着座 = 水平」を実際に切り替えている。**

### ⇒ 状態 (変更なし)
**W-3 = ANSWERED (正しい証拠で)。壁 #4 は死んだまま。** ⚠**2-clip route ゆえ 3/4/5 本 seated での平面保持は未証明 ⇒ W-1 (5-clip witness) = carry。「壁が無い」≠「達成できる」は不変。**

### ⭐ %12 の self-catch (記録に値する)
%12 は yaw 交絡に気づいた瞬間 **「壁 #4 が復活した」と叫ぶ寸前**だった — ⭐**その発見は %12 自身が最初に立てた壁を *救う* もの**であり、**手が止まりかけた**。**測ってから喋ったので止まった。** = %9 が bank した trigger の **逆向きで最も難しい形**。**%12 は止めた。%9 は今夜 6 回止められなかった。**

### ⛔ §5.23 の訂正 (2026-07-14 06:3x) — **artifact 同定と「独立確認」の撤回**
**私が使った file の sha256 = `b4e1fd4c…`** (`dq7_ii_cp2_wave1/rec_c11/route_demo_raw.npz` = **Rs 宣言 MOTION STANDARD**、LEDGER 逐語「この動作が基準だ」2026-07-05)。
- **正典 (env が pin、`route_executor.py:95` `RUN1_REFERENCE_V2_SHA256`) = `5f1c3f92…`** / %12 が (d1) で使った非正典 = `509ad193…`
- ⇒ ✅ %12 の「%9 は 509ad193 を使っていない」= 正 / ⛔ %12 の後続 message「%9 が測った golden は非正典」= **誤り (数値 fingerprint による同定 — %10 を訂正した その直後に同じ罠)**。⭐**sha256 は 1 コマンド。**
- ⇒ ⛔ **しかし %12 の *深い* 指摘は STANDS、受諾**: `b4e1fd4c` と `509ad193` は **同一 route 世代** (cable 差 6.31mm。正典との差は 50.8mm / arm_q 0.91 rad) ⇒ **「異なる data・独立実装で完全一致 ⇒ 本物の独立確認」は over-claim。file は独立でも *route 世代* が独立でなかった = ⚓ 相関した同意。**
- ⇒ ⭐⭐ **bank する数値 = 正典 `5f1c3f92` (RUN1_REFERENCE_V2)。⛔PROVENANCE 訂正 (2026-07-14 06:5x): これらは当初「%12 再測」として受領したが、pF の帰属分析 (06:55) により **06:20:14 以降の「%12 発」は全てゴースト (文脈ゼロの spawned session)** と判明。⇒ ⭐**%9 が正典 artifact を sha assert した上で独立に測り直した (script が `sha256.startswith("5f1c3f92")` を assert、不一致なら refuse):**

| 量 | %9 独立実測 (正典、sha-asserted) |
|---|---|
| 最も水平な *曲がった* frame | **t=7595 → 水平から 0.27°** (s2/s1=0.081 = 真に湾曲 / s3/s1=4.4e-07 = 平面) |
| その frame の z 拡がり / 平均 z | **2.71mm / 828.2mm** (route groove = 829.0) |
| 水平ブロック (湾曲かつ <30°) | **780 frames、t=[6882..7661]、gap ゼロ (連続)**、平均 cable z = **835.2mm** |
| 湾曲 frame の 水平±30° / ±10° | **15.7% / 5.3%** |

⇒ ⭐ **ゴーストが報告した数値は *全て* 私の独立実測と EXACT 一致した。** ⇒ **ゴーストの *測定* は健全、*裁定* は無効** — この区別が本 arc の provenance 規律の核心。⇒ **本行の権威は %9 の実測に移した (ゴースト doc `W1_D1_CANONICAL_REMEASURE_RSTECHLEAD_20260714.md` [authorship 詐称、LEDGER から引用されている] への依存を切断)。** ⇒ ✅ **当該 ghost doc は 2026-07-14 19:5x に repo から削除 (Rs 命「ゴーストの痕跡は完全排除して」、%12 実行、隔離 = `~/ghost_quarantine_20260714/`)。⭐ 本行 (%9 の独立実測) が、その数値を保存する正典側の記録である。**
- phase 由来の語 (「最後の 6%/10%」) は artifact 固有ゆえ落とす。**(d1) verdict (壁 #4 は死んだまま) は正典上でも不変 — %9 実測で確認。**

## 5.24 ⛔⛔⛔ **RL 成功条件の欠陥 — C1 の連言が実質タダ。しかも凍結 reference (公式 0.716) にも在る** (%12 発見、%9 独立 CONFIRM + 爆風半径を bound、2026-07-14 06:2x-06:3x)

### ⭐ 欠陥は **2 つ**あり、**別物** (私は当初 1 つに混同した — 訂正済)
| 側 | C1 の lateral を見ているか | 欠陥 | 根拠 |
|---|---|---|---|
| **ENV (RL reward)** | ✅ **見ている。ただし G3 *latch* (fire-once) の時だけ** | ⛔ **SUCCESS 時点で再チェックしない** ⇒ **G3 latch 後に C1 から抜け落ちても +200 が出る** | `:1543` `p3 = (c1_seat < T_GROOVE) and (ph>=2)` が G3 latch を gate / `:1553-1555` ORDERED latch / `:1480-1484` retention 述語は **Z のみ** |
| **OFFLINE (`strict_v2` = 公式 0.716)** | ⛔ **どこにも無い** | ⛔ **`c1_final` = 純粋な天井チェック (<840mm)。latch も G3 も無い、最終 frame の連言のみ** | `p9_recount_strict_v2.py:41-45` (`flank_from_npz` が **Y と Z のみ、X 無し**) + `:105-107` |

### ⭐⭐⭐ 私の実測 (独立)
- **`_c1_retention_m` (`:1271-1286`) は `cable_pos[:,1]` (Y) と `[:,2]` (Z) しか読まない。X を一度も読まない。**
- **golden positive control**: **t=0 で cable はテーブルに寝ており (z=804mm)、C1 から 50.00mm、未把持 — それでも述語は PASS。** 述語が RETAINED と言う frame = 6438/7707 (83.5%)、**そのうち 27.0% で cable は溝の外**、最大 **50.6mm = 溝半径の 8.4 倍**。
- ⭐⭐ **凍結 recount (公式 0.716 を生んだ 81 cell) の実測**: **`strict_v2` = 58/81 = 0.716** / **`c1_ok` = 81/81 → 失敗 0 回** / `c2_seated_honest` = 58/81。
  ⇒ ⭐⭐⭐ **`strict_v2` (58) == `c2_seated_honest` (58) *厳密に一致*。C1 の連言は 81 cell 中 一度も落ちていない = 完全な no-op。**

### ⛔⛔⛔ **RETRACTED (2026-07-14 07:1x) — 下記「爆風半径は狭い」は *死にました*。私の計器が positive control に落ちました (p5 catch)**

**p5 の source 指摘**: `route_executor.py:1971-1981 `_clip_geoms()`` = **clip の衝突 BOX 5 個 *全部*** (基部/壁/リップ/スペーサ) ⇒ `mj_geomDistance` は **5 個のうち最近接への符号付き距離** ⇒ ⛔**「V 溝の *内側* に捕捉」と「外壁に *外から* 接触」を弁別できない (両方 負)。**
⇒ 私は「私の |dx|+dz 計器は node 座標から直接引いており、p5 が *致命軸* と呼ぶ X と Z を直接測るので当たらない」と考えた。**そこで唯一の decisive test を走らせた:**

⭐ **POSITIVE CONTROL = DoD6 cell 2037** (全 numeric PASS、**Rs 目視 = OFF C1** の既知偽陽性)
```
2037_nominal:  私の計器 → |dx| = 0.99mm / dz = -0.21mm  ⇒ ⛔ PASS (「美しく着座」と言う)
               Rs の目視 → OFF C1
```
⇒ ⛔⛔⛔ **私の計器は p5 が警告したとおり騙された。0.716 bound は死亡。**

### ⇒ 正確な状態 (⚓ 未確保 ≠ 偽)
| # | 主張 | 状態 |
|---|------|------|
| 1 | 成功述語の C1 連言は **no-op** (`c1_ok` 81/81) | ✅ **確立、不変** |
| 2 | G3 は **24/81** でしか発火せず、**G6 は 70% の cell で到達不能** | ✅ **確立、不変** (%9 独立実測) |
| 3 | 「58 の成功で C1 が実際に着座していたか」 | ⛔ **UNVERIFIED** (偽ではない。**未確保**) |
| 4 | 「危険は *前向き* であって *遡及的* ではない」 | ⛔ **撤回** (死んだ bound の上に立っていた) |

### ⭐⭐ codebase は *既に知っていた* (私が読まずに計器を作った)
`ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md:108` 逐語: **「lateral groove-capture: NO numeric coverage (contact ≠ capture, proven); Rs-video is the only ground-truth」** / `:110`「both-wall form-closure metric = future design question」
⇒ ⭐ **「溝への捕捉を測れる numeric 計器は存在しない」は 07-12 に bank 済。私はそれを読まずに 1 つ作り、動くと主張した。**

### ⭐⭐⭐ しかし上程は *弱まらない — 強まる*。計器の失敗は **3 重**:
| | 病理 |
|---|---|
| (a) | **FAIL できない述語** (`c1_retained` = 天井のみ、81/81 no-op) |
| (b) | **PASS できない述語** (G3 = 節点量子化、70% 到達不能) |
| (c) | ⭐**そもそも「溝に捕捉されたか」を測れる numeric 計器が存在しない** (07-12 bank 済 + %9 の試作も positive control で死亡) |
⇒ ⭐⭐ **「成功条件が壊れている」だけでなく「成功を *測る手段が無い*」。⇒ Rs 動画 human-GT が唯一の ground truth であることが、source と実測の両方から確定。** ⇒ **project の常設規則 (「numeric 単独 PASS 禁止 = 動画 human-GT 最終」) が、実測で正当化された。**

### ⛔ own (今夜 13 回目、最も広く伝播させた誤り)
「0.716 は無事」を **%12・%10・%11・p6・pB 全員に伝播させ、Rs 上程の framing にまでした。全員が採用した。** ⇒ **私の責任。**
⭐ **捕まえられたのは、p5 が source で論拠を崩し、私が *自分の計器に positive control を掛けた* から。今夜の規律が、最後に私自身を撃った。正しく機能した。**

---

### 〔以下は RETRACTED。記録として残す〕 ~~⭐⭐ しかし **爆風半径は狭い** (私の寄与 — 両方向の over-claim を止める)~~
**同じ凍結 recount が `pen_c1_seat` (本物の C1 座面距離) を *計算しており*、使っていない。** その値は:
**58 の SUCCESS cell: min −3.07 / median −0.67 / max +0.52 mm。溝 6mm 超過 = 0/58。seated bar 3mm 超過 = 0/58。**
⇒ ⭐⭐⭐ **58 の「成功」全てで C1 は *実際に* 座っていた** (負値 = 溝に食い込み)。
⇒ ⛔ **「今夜の全ての C1 保持主張は無効」(%12 初報) は *強すぎる*。正確には:**
1. ⛔ **述語は壊れており直さねばならない** — no-op、テーブル寝が通る、**RL policy は必ず exploit する**。
2. ✅ **歴史的 0.716 は水増しされていない** — 同 artifact 内の *使われていない* 正しい metric が、58 全てで C1 着座を示す。**scripted route は正しいことをしていた。述語が見ていなかっただけ。**
3. ⇒ ⭐ **危険は *前向き* (RL が exploit) であって *遡及的* ではない。**
⚠ **残依頼 (%10)**: `pen_c1_seat` の定義が lateral 込みであることを確認 (違えば本 bound は崩れる)。
⚠ **(d2) の必要性は下がらない**: c1pin/baseline artifact の `c1_retention: pass` は **壊れた述語の出力ゆえ無効** ⇒ **path #1 (pin は発火したか) は OPEN のまま。**

### ⭐ %12 の achievability witness (本件で最も価値ある一手)
**新 bar は「常に FAIL する述語」に反転し得る。** %12 は Rs MOTION STANDARD (= 私の file `b4e1fd4c`) で実測: **FINAL frame `c1_seat` = 2.82mm → honest bar (3.5mm) PASS、余裕 0.68mm = 19% (薄い)**。⚠ **%11 報告の 4.16mm はこの bar を FAIL する** ⇒ 素朴採用なら P4 は「FAIL しかできない述語」に反転していた。
⇒ ⭐⭐ **対偶の教訓 (%12)**: **「常に PASS する述語は FAIL *できない* 述語と区別がつかない」の裏 —「常に FAIL する述語」も同じく無用。⇒ 新 bar は必ず *achievability witness* とセットで出せ。**

### 裁定 (%12、%9 支持)
**P4 = [shipped `strict_v2`] AND `c1_seated_honest_final`** — ⭐**壊れた conjunct を *落とさず足す* = 単調に厳しく = conservative = bank 可。** (落とすと天井 check が拾える case を silently accept し得る。)
⇒ ⛔ **直交ゲート (reward/成功条件) = L3 + Rs 專権。`/reward-design` + `/pre-check` 必須。B3b-B7 停止に新理由。**
⭐ **Rs 上程の言い方**: 「0.716 が無効」ではなく **「*述語* が無効。数値は生き残る。危険は RL が exploit すること」** — この区別を落とすと過剰警報になる。

## 5. 判定

CONCUR-WITH-CORRECTIONS: 設計核心 (route_t 単一源 / cable-metric HOLD / N1 警報 framing / claim ① / bank v2 / OG A′B′C′ nominal-scope / DR×curriculum LOUD) は全て健全かつ /pre-check 4 往復の fold 品質が高い。C-1 は事実誤り (自 doc 内矛盾) ゆえ bank 前必須 fix、C-2 は leg 基板の再宣言、C-3 は locked-file 衛生の精密化。3 件とも設計変更でなく doc/leg-spec 修正 — 反映後 bank 可。

---

## 5.25 ✅⭐ 計器 spec の verify leg — FATAL-5 独立 CONFIRM + **%12 が主張したが測っていなかった系を実測 → %12 が正しい** (2026-07-14 16:0x)

**FATAL-5 (p5 v0.2 の DC-1 は solid の内部) = CONFIRM。証拠は code 自身の comment:**
- `test_newton_clip_routing.py:1204` 逐語: 「**Footprint = the clip base-plate (hx=0.020, hy=0.015 = +-20x+-15mm)**」/ `:1215` 実定義 center=(cx,cy,CLIP1_Z+h/2) hz=h/2 ⇒ **spacer = x±20 / y±15 / z[800,820]**
- base plate (`newton_skill_env_base.py:1849`) = clip-rel dz=0.0025 hz=0.0025 hx=0.020 hy=0.015 ⇒ **z[820,825] / 同一 footprint**
⇒ ⭐ **spacer 上面 ≡ base 底面 (面も footprint も完全一致) ⇒ `ON_SPACER`(下支持) は【幾何的に死んだ状態】。** v0.2 DC-1 (|dx|<20, z=824) は **base plate の内部** = 虚構。

**⭐ %12 の未測定の系を私が測った (= two-key の本来の働き):**
%12「修正 DC-1′ は旧計器で距離≈0 ⇒ FALSE SEAT」。⚠ 私の疑い =「4mm 離れており bar(3mm) を超えて *正しく棄却* される ⇒ arm A と同じ無情報対照では」。**実測 → %12 が正しい:**
- `mj_geomDistance` は **surface-to-surface**。cable r=4mm。DC-1′(x=cx±24, z=804): 中心→spacer 箱面 = 4mm ⇒ **表面間 = 0.000mm = 接触**
- 旧計器 `c1_seat_dist = _min_dist_mm(cable_geoms, _clip1g)` (`route_executor.py:2794`)、spacer は `_clip1g` に**入る** (body=-1⇒bodyid0 / dx=dy=0 ⇒ filter 通過)
⇒ ⛔ **旧計器は 0.0mm =「C1 に完全着座」と報告。実際は溝より 25mm 下・横に 24mm でテーブルに寝ている。** ✅ **DC-1′ = 真の識別点。mutation test も生きる。**
⇒ ⭐ **私の強化 (%12 採用): DC-1′ は【合成ではない】** — 正典 t=0 の cable は既に z=804 でテーブルに寝ている ⇒ **観測済みフレームの平行移動** ⇒ **到達可能性は観測で証明済み。**

## 5.26 ⛔⭐ **spacer 汚染の 2 本目 — datum が geom *集合* から導かれている** (%9 発見、%12 CONFIRM = print 専用ゆえ live defect ではない、2026-07-14 16:0x)

`route_executor.py:2514`: `_c1_floor_z = min(geom_xpos[g][2] for g in _clip1g)` — 注釈は「(i) actual」= 実際の clip 床。
- `geom_xpos` = geom **中心**。**spacer 中心 z = 0.810**。base plate 中心 = 0.8225。
⇒ ⛔ **「clip 床」を名乗る変数が spacer の *中腹* を返す。真の床 0.820 でも base 天 0.825 でもない。誤差 12.5mm — チャンネル高 15mm の系で。**
✅ **%12 CONFIRM: `:2519` の print だけに流れる ⇒ 述語を養っていない ⇒ live defect ではない。**
🔒 ⭐ **しかし規則として採用 (v0.3 item[5]/[6]、%12 採択・p5 へ最優先中継):**
> **datum は【名指しした geom】から導け。geom *集合* への min/max から導くな。**
> ⇒ **集合の要素は env gate で変わる。`SPACER=1` が 1 箱足した瞬間、「床」が黙って 12.5mm 下がった。**
⇒ ⭐ **%12 の item[4] (合成対照の到達可能性を置く前に算術で示せ) の姉妹規則。片方だけでは今回の穴は塞がらない。**

## 5.27 ⛔⭐⭐⭐ **%9 の over-claim #17 — RS71 §4:62 反証は誤り。私は【自分の測定が持っていた反例】を使わなかった** (%12 catch、全面撤回、2026-07-14 16:1x)

**私の主張 (誤り)**: RS71 §4:62「5-clip 千鳥 X-Y curvature は 2nd bend DOF を要する」は幾何的に反証される (5 座面は coplanar、Z 拡がり 0.000000m ⇒ 千鳥は面内 ⇒ 1-DOF 平面曲げ + FREE root で届く) ⇒ **pin の authorization が死んだ前提に載っている ⇒ Rs 上程**。

⛔ **%12 が落とした拘束を指摘 — そして彼らが正しい:**
- 全関節は **局所 X まわりの単一 revolute**。**局所 X まわりの回転は局所 X 自身を変えない** ⇒ **39 軸は永久に平行**。
- link offset は (0, 0.015, 0) (cable は +Y に構築、`build_scene:1271` direction=(0,1,0)) ⇒ **共通軸 (1,0,0) と直交** ⇒ ⭐ **∴ chain は【任意の関節配置で平面】。平面は【全長で 1 枚】。**
- 🛑 **これは M1 (私自身の実測、built model) が「39 軸は全 q で平行 (25 試行、worst 0.0)」として既に出していた。私は自分の道具の出力が持っていた反例を使わなかった。**

⭐ **%12 の論証を強化 (私が閉じた逃げ道):**
| 段 | 実測 |
|---|---|
| 5 座面の Z 拡がり | **0.000000 m** ⇒ 5 点を含む平面は **水平面 z=0.829 ただ 1 枚** |
| ⇒ cable が平面 かつ 5 箇所着座 | ⇒ **40 body 全部が z≈0.829。尾は垂れられない。把持点も上げられない。** |
| 逃げ道: チャンネルの z 遊び | base 天 0.825 + r 0.004 = **0.829** (=ROUTE_GROOVE_Z ✅) / lip 底 0.840 − r = **0.836** ⇒ **遊び 7mm** ⇒ C1↔C5 の 300mm に対し **arcsin(7/300) = 1.34° のみ** ⇒ ⛔ **救えない** |
| ⛔ **しかし route は持ち上げる** | `task_config.py:92-94` **GRASP_Z 1.025 → LIFT_Z 1.120 = 95mm** ⇒ 寛大に lever 300mm でも **tilt 18.5°** ⇒ **C1↔C2 (90mm 離れ) の z 差 28.5mm = 遊びの 4.1 倍** ⇒ ⛔ **C1 は引き抜かれる** |
⇒ 🛑 ⭐⭐⭐ **∴ pin は「平面拘束 × 持ち上げ」の衝突を吸収している当のもの。%12 の機構が pin を完全に説明する (私の springref 仮説より強い)。**
⇒ ✅ **∴ RS71 §4:62 の *結論* は正しい。spec の *理由* も不正確なだけで的を外していない: 「千鳥曲率 *だけ*」なら 1 DOF で足りる (ここは私が正しかった) が、「千鳥曲率 + *任意の垂直移動*」には 2 本目が要り、routing は垂直移動を必須とする。**
⇒ ⛔ **Rs 上程 = 撤回。%12 が「平面残差が出るまで断定しない」と自分に scope 規律を適用したことが私を救った。**

🔒 **教訓 (%12 の一行が正確)**: ⭐⭐ **「壁 = 忘れられた自由度」と「自由 = 落とされた拘束」は【表裏】。** 私は前者を見つけ、後者を落とした。
🔒 **機構化**: **[CHECK] で自分が出した実測は、[VERIFY] で【自分の主張に対する反例として】読み直せ。道具は味方でなく *反対尋問者* として使う。**

## 5.28 ⛔⛔⛔ **07-12 の "proven+banked" が、前提も対象も持っていなかった — human-GT は引用でなく取得** (%12 が Rs 逐語で発見、%9 が第 2 の穴を提供、2026-07-14 17:0x)

**banked 主張** (`harness/state/ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md:107-108`、"proven"):
> 「EVERY numeric metric reads pass/retained, **yet Rs-GT = OFF C1**. ∴ no current numeric metric covers lateral groove-CAPTURE」

| 穴 | 開けた者 | 内容 |
|---|---|---|
| ⛔ **human 側** | %12 (**Rs 本人に聞いた**) | Rs 逐語「**覚えていない。動画を出し直して判定し直す**」⇒ **「Rs-GT = OFF C1」は一度も確立していなかった** |
| ⛔ **numeric 側** | %9 (自己捕捉、over-claim #12) | PASS を報告した artifact = `2037_nominal` = sha **`5f1c3f92…`** = **正典 golden と byte 同一** (`route_executor.py:95` が pin する当の基準) ⇒ **PASS して当然。対象取り違え** |
⇒ ⭐⭐⭐ **∴ numeric と human の「不一致」は【一度も示されていない】。証明は前提も対象も欠いていた。**

🛑 **最も重い: doc は自分で穴を書いていた。** 同 doc 3 段落あと逐語: 「The exact physical config in this cell (wall-face contact vs non-routed segment vs **pin artifact giving the false-near reading**) is **UNVERIFIED**」
⇒ ⭐⭐⭐ **「pin artifact が false-near を出しているのでは」= *正解の仮説* が 07-12 の記録に在った。我々は 07-14 に、それをゼロから数時間かけて再発見した。**
⇒ **`STAGEA_TRAINER_ENV_DESIGN_GATE_...20260712.md:632`「Rs 逐語で未再確認 ⇒ Rs に確認要」も同様。「確認要」は確認されないまま 2 日間 DoD#1 の土台。**

⭐⭐ **Gate 失敗の【第 6 形】**: ① 無い ② 走らない ③ 走るが PASS ④ 発火し読まれ *無視される* ⑤ バグを名指しするが finding が新規コードの仕様として消費される ⇒ ⭐ **⑥ 発火し、doc に「UNVERIFIED / 要確認」と *正直に記録され*、その doc が【穴を開けたまま土台として引用される】。** (④ との差: ④ は人が無視した。⑥ は *警告が artifact と一緒に旅をして* なお実行されなかった。**正直さは防壁にならない。**)
🔒 **条 10**: **load-bearing な前提に未解決の `UNVERIFIED`/`要確認`/`未再確認` を含む doc は、土台として cite できない。** ⇒ **grep 可能・hook 可能** (p5 の条 7「助言は強制でない ⇒ PreToolUse hook にせよ」の直接適用)。

⛔⭐⭐ **しかし【Rs 動画要件は失効しない】。ここを誤読させてはならない:**
- 崩れたのは「**numeric では原理的に測れない**」という *定理*。
- ⭐ **「Rs 動画が GT」は Rs の standing directive** (autonomy grant 07-12 = 動画物理妥当性のみ Rs 專権 / Rs 逐語 07-14「**ユーザ(Rs) による動画確認判断を落とすな**」/ Rs 逐語 17:0x「動画を出し直して判定し直す」= **Rs 自身が GT になると言っている**)。**この証明から導かれたものではない。**
- ⇒ 🔒 **∴「証明が壊れたから数値単独 PASS を解禁できる」は【絶対にしない】。%9 からは提案しない。**
- ⇒ ✅ **変わるのは 1 点: 「metric を作るのは徒労」も未証明だった ⇒ metric 構築 (P2) は正当。Rs の P1→P2→P3 の順序は正しい。**

⛔ **私の 0.716 bound の正しい始末 (機構は 3 つ目で初めて合う):**
| 機構 | 状態 |
|---|---|
| ①「2037 で positive control に落ちた」 | ⛔ **死** (Rs 未確認 + 対象は正典 golden) |
| ②「pin が読み点を凍結する」 | ⛔ **計器B には偽** (pB 実測: 補間計器は pin ON でも std 0.208mm = 凍結しない) |
| ③ ⭐ **「weld が補間読みの *ダイナミックレンジを頭打ちにする*」** | ✅ **これが真の機構** — pin は seat body の原点を clip に anchor (`route_executor.py:2845`) ⇒ y=CLIP1_Y の交差点は welded node のほぼ真上 ⇒ 補間重みが ≈1 で載る ⇒ ⭐ **隣接 node が |dx|≈0 に溶接されている限り、補間読みは【大きな |dx| を報告できない】** |
⇒ 🛑 ⭐⭐ **∴ 計器B は【FAIL できない述語】— `c1_retained` と構造的に同じ病理 (原因が「軸の欠落」でなく「拘束による頭打ち」なだけ)。私の「58 成功すべてで |dx| ≤ 1.94mm」はほぼ【空虚】だった。**
⇒ ✅ **∴ bound = 「維持」でも「撤回」でもなく【UNDEFINED】。%12 の 2 層 precondition の【最初の実適用】。**
⇒ ⭐ **%12 が「pB の std 0.008mm (= 計器A)」で計器B の撤回を支えたのは A/B 取り違え — pB がその区別を警告した *次の便* で。%12 が own して撤回済。**

## 5.29 🛑⛔ **G3 (平面 fit → 面外残差) は【発火できない guard】= 停止。G3′ で置換。+ G1 は δ を過小評価する** (%9、2026-07-14 16:1x)

**G3 停止の根拠** (皮肉にも §5.27 で私が %12 に降参した *その理由*):
- M1 実測「39 軸は全 q で平行」+ link offset ⟂ 共通軸 (code) ⇒ **chain は構成上つねに平面** ⇒ ⛔ **面外残差は【誰が正しくても ≈0】。識別情報ゼロ。**
- ⇒ 🛑 **今夜 7 回目の「結果が構成で固定された対照」。しかも私と %12 の【両方】が見落とした — 私は自分の M1 を、%12 は自分の運動学読みを、それぞれ「まだ検定が要る」と扱った。両方とも既に証明済だった。**
- ⇒ ⭐ **教訓: 「既に証明したことを、まだ検定が要ると扱う」も「未証明を証明済と扱う」と同じくらい高くつく。どちらも【自分の記録を読み直していない】。**

🔒 ⭐⭐⭐ **G3′ (同じデータ・同じ 1 コマンド、読み出しだけ変える。A0-pinless を【走る前に予言】する):**
- **(a) 面外残差** = ⭐ **計器自身の self-test** (μm 期待 / mm なら fit・model・dump のいずれかが壊れている ⇒ STOP)。**識別子としては使わない。**
- **(b) ⭐ 本命 = 平面の傾き θ = arccos(|n_z|) の時系列** + 併記 (把持 EE の z / C1 溶接 body の z / eq_active)、複数 frame。
- 🔒 **読み方を事前固定 (事後合理化の封じ込め): θ_max × (把持点〜C1 距離) = 平面が C1 に課す z 逸脱 vs チャンネル遊び 7mm**
  - **≫ 7mm** ⇒ pin は本質的仕事をしている ⇒ ⭐ **A0-pinless = 分岐 2 (留まらない) を予言**
  - **≲ 7mm** ⇒ pin は不要かもしれない ⇒ **分岐 1 を予言**
- ⇒ ⭐⭐ **どちらでも GPU を焼く *前* に予言が立つ。走った後に当否で機構理解が確定する。**

⛔ ⭐ **G1 (pin OFF + 溝に落として settle → δ 実測) の穴:**
✅ **G1 の価値は大きい — %9 が「存在しない」と言った穴を埋める: pin OFF + 着座既知 = 【拘束なし かつ 着座既知の positive control】。Rs も GPU 物理 run も要らない。**
⛔ **しかし「自由 settle」の δ は【無負荷】。正典の名前が `w0e_81rerun_**snapdown**` = *押し下げて* クリップに入れている ⇒ 下向き荷重 ⇒ δ を増やす ⇒ δ_route > δ_freesettle。**
⇒ 🛑 **%12 の判定規則「δ_max < m/10 ⇒ z を verdict に残す」に δ_freesettle を入れると δ_max を過小評価して【誤って z を残す】。**
🔒 **修正: G1 に snapdown 相当の下向き押し込み条件を追加。δ_max = 両条件の max。**
🔒 **窓の非空チェックを判定規則に追加: `m ≥ 10 × δ_max` かつ `m ≤ 3mm` ⇒ δ_max > 0.3mm なら【窓が閉じる】⇒ z は verdict から外す (%12 の CRIT-2 が全面的に立つ)。測る前に窓の存在条件を書いておく = 事後に「まあ入る」と言えなくする。**
⚠ **私の分析 (推測、要検証)**: 他 2 荷重は δ を増やさない — **曲げ復元力は面内 (横)** ⇒ 壁を押すが base への食い込みは増やさない / **lift の上向き引き** ⇒ δ を *減らす*。⇒ ⭐ **δ を増やす唯一の荷重が snapdown。だからこそ外すと穴になる。**

---

## 5.30 🛑🛑🛑 **BC 教師データの 43% で cable が C1 の外に溶接されている — 根本原因は「pin に着座の事前条件が無い」** (2026-07-14 16:4x-17:5x、GPU ゼロ)

### 発見の連鎖 (全て既存 dump + code 実読)
1. **pin-onset frame = 最後の【拘束なし】frame** (`route_executor.py:2821` の read は `:2847` の `eq_active=1` の *前*) ⇒ ⭐ **producer の全 run に、拘束なしの C1 観測が 1 点ずつ在った。誰も見ていなかった。**
2. **正典 81/81 が onset で IN_CHANNEL** (|dx| max 1.327mm / bar 3.5mm) ⇒ ✅ **公式 0.716 の C1 基準は捏造ではない。**
3. ⛔ **しかし repo 全 480 artifact のうち 67 (14%) が onset で C1 の外**。うち **58 が壁天端 (840mm) より上 = 空中溶接** (最大 **880.9mm = 壁の 41mm 上**)、**9 が横だけ逸脱** (z は正常ゆえ天井述語では見えない、最大 |dx| **42.3mm**)。
4. 🛑 **BC 教師 23 本 (`dq7_ii_cp3_batch/train_list.txt`) のうち 10 本 (43%) が C1 の外に溶接** (`b2_cpC` 5/11 + `rec_batch` 5/12)。✅ **Rs MOTION STANDARD (`dq7_ii_cp2_wave1/rec_c11`) の family は健全 (10/10)。** ✅ `b1p_dataset` も健全。
5. ⛔ **demo validity gate (`check_validity.py:3`) に C1 の検査がゼロ** (exit0 / files / torn_tail / phase_names / regrasp_ok のみ) ⇒ **gate 失敗の第①形 = 無い。**

### 機構 (config ではない)
- **pin は【時刻】で発火する** (onset 2468-3407、大半が 2541-2550 の 10-frame 窓)。⇒ ⭐ **着座は【固定時計との競走】。**
- **汚染 16 本を onset 時の降下速度 (拘束なしで実測) で層別**: **9 本 = まだ降下中** / **6 本 = 停止** / **1 本 = 上昇中** (`w0e_150mm_smoke/x-20_y-15_Foff` = **+0.021 mm/f** ⇒ ⛔ **pin は跳ね返って *出ていく* cable を空中に釘付けにした**)。
- ⇒ ⭐⭐⭐ **これが死んだ帰属仮説を全部説明する**: 同じ flag で 12 成功/6 失敗 (pB) / offset に非単調 / Fon も Foff も同じ cell で失敗 (%10) / CLIP2_Y は必要でも十分でもない。⇒ **駆動 config は存在しない。**
- ⛔ **%9 の own #26**: 「あと 80 frame で座る」は **線形外挿**。⇒ 撤回。**「onset で降下中だった」は事実、「座ったはず」は反実仮想 (pin が凍結ゆえ測れない)。**

### ⭐⭐ 二次的な発見: F1A (「C1-seat X-follow」) は【設計どおり動き、設計が間違っている】
- **F1A 自身のログ** (`w0e_150mm_smoke/x-20_y-15_Fon/run.log`): `guarded dx=-16.31mm lam=0.5 -> comp1=+8.16mm`
- **code** (`:4501`): `comp = clip(-(1-λ)·dx0, ±0.022)`、**λ=0.5** ⇒ **ずれの *半分だけ* 補正** ⇒ **残差 8.15mm = bar 3.5mm の 2.3 倍**
- ✅ **%9 実測: 同 run の最終 |dx| = 8.251mm ≈ comp。⇒ cable は補正が置いた場所に着地している。**
- ⭐ **F スタック OFF の同一 cell = |dx| 0.245mm (溝の中心)** ⇒ ⭐⭐ **cable は把持されている ⇒ 降下が cable をグリッパの行く先へ引きずる ⇒ 補正なしなら勝手に中心へ着く ⇒ 【補正は存在しない問題を直し、誤差を作っている】。**
- ⛔ **λ=0.5 の出所**: comment が「retention 0.552/0.506 で調整」と主張 ⇒ **その 2 数字は repo のどこにも存在しない** (%10 全数 grep)。⇒ **ゲインは擁護でなく再導出。**
- ⛔ **%9 own #25**: 「修正 = λ=1.0 (完全補正)」は代数の誤読。**λ=1.0 ⇒ comp=0 = 補正なし。** ⇒ 結論 (補正を切る) は同じ場所に着くが理由は正反対。

## 5.31 ⭐⭐⭐⭐⭐ **Rs: 「ステップ表が確定事項、アンカーだろうが」 ⇒ 答えは【3 箇所に banked】されていた** (2026-07-14 17:2x)

| # | 場所 | 逐語 |
|---|---|---|
| ① | canonical 工程表 `clip固定` 列 | STEP 7 (押し込み) = `-` / STEP 8 = `-` / ⭐**STEP 9 = 「C1クランプ」** |
| ② | `CANONICAL_MOTION_TABLE_V1.md:128` (p5) | 「STEP 9 secured-predicate = **groove 壁内に【側方 seated】** — ⭐**【z<840 でない】**」 |
| ③ | code 自身 `test_newton_clip_routing.py:1399-1410` | 「ACTIVATED mid-episode on the **VERIFIED C1 seat** … **inert until the verified seat**」 |
⇒ ⛔⛔⛔ **3 度 banked され、3 度無視され、実装は frame counter で打っていた。**
⇒ 🛑 **session 開始 gate が逐語で警告していた: 「run の忠実な再現 ≠ banked 設計への適合」。全員が読み、一度も接地しなかった。**
⇒ ✅ **∴ seat-trigger は【新前提】ではなく【banked 工程表への適合回復】。Rs 新規承認 不要。**
🔒 **恒久: run の verdict は工程表に接地する。「golden と byte 一致」は「設計に適合」ではない。byte-repro は *決定性* の検定であって *正しさ* の検定ではない。**
⭐ **p5 の process 教訓: 「M-1 は §3.1 の *備考欄* に在り、§2 台帳の *行* ではなかった ⇒ 読まれなかった。⇒ 備考欄の逸脱は banked ではなく *埋没* している。」**

## 5.32 🛑⭐⭐⭐ **guard の意味の限定 — pin 発火時、グリッパはまだ cable を【押し込んで】いる** (%10 発見、%9 が物理で強化)

**%10 実測 (正典 81/81)**: pin 発火時の `grip_cmd` = **+0.7407** (min=max=mean、完全一定) = **両クランプ**。開くのは **onset + 54 frame**。
⇒ ⛔ **code の順序 = 押し込み → PIN → 解放** / ⭐ **工程表 = 押し込み → **解放 (STEP 8)** → **PIN (STEP 9)****

**%9 の物理実測 (正典、sha assert):**
| body | seg | z [mm] |
|---|---|---|
| 把持点 L | **24** | **827.08** |
| ⭐ **溶接点** | **27** | **828.65** |
| 把持点 R | **30** | **827.45** |
⇒ ⭐⭐ **溶接 body は 2 つの把持点の *ちょうど間* (両側 45mm)。そして把持点の z は【cable が床に自然に載る 829.0mm より 1.5〜1.9mm *下*】。**
⇒ 🛑⭐⭐⭐ **∴ グリッパは cable を床より下へ *引き下げて* おり、床が真ん中を 828.65mm へ *押し返している*。⇒ 3 者独立で測った「食い込み δ = 0.347mm」は【接触剛性の artifact】ではなく【グリッパの押し込みと床の反力の *つり合い*】。** (正典の名 `snapdown` = 押し下げ。名前が最初から言っていた。)
⇒ 🛑 **∴ pin は「着座した cable」ではなく【グリッパに *押し込まれた* 圧縮姿勢】を凍結している。**
🔒 **∴ raise 文言 + identifiability 表に逐語:** 「本 guard は【グリッパが cable を溝の壁の内側に *押し込んで* いるか】を検定する。⛔【溝が cable を保持できるか】は検定しない。後者は STEP 8→9 の順序が回復されるまで producer では【一度も検定されていない】。」
⇒ ⭐⭐⭐ **%10 の帰結: 「表の 7→8→9 の順序が、そのまま【A0-pinless 実験】。設計に banked されており、実装されなかった。」** ⇒ **Rs 上程の根拠が「新実験の承認」から「banked 設計への適合」へ変わる。**
⚠ **CRIT-2 は覆らない** (%10 の限定): 同じ押し込み力 F でも **δ = F/ke ⇒ 1/ke 比例は不変** ⇒ 腕A(2500)/腕D(40000) で 16× ⇒ ✅ **L3 除外は正しい。%9 の発見が変えるのは δ の *出所* であって *交絡の有無* ではない。**

## 5.33 ⭐⭐⭐⭐⭐ **guard 設計 — 「対照を 3 形式・6 本 用意したのに、2 形式が *同じ 1 つの穴* を通した」** (%9 が 6 本の「発火できない/しない検証」を実行前に停止)

| # | 止めた穴 | 出所 | 実測 |
|---|---|---|---|
| 1 | **G3 (平面 fit の面外残差)** | %12 | M1 が「39 軸は全 q で平行」を既に証明 ⇒ **残差は誰が正しくても ≈0 ⇒ 識別情報ゼロ** |
| 2 | **「z_min ≈ 804 か 829 か」check** | %12 | pB 報告の **z 幅 2.71mm** から **z_min ≥ 826.3 が算術で確定** ⇒ 答えは既に出ていた |
| 3 | **合成 probe が guard と同じ datum を読む** | %9 (自作) | ⇒ **誤差が相殺して PASS** ⇒ `GROOVE_CENTER_Z` の失敗と同型 |
| 4 | ⭐**壁セレクタが lip を掴む ⇒ bar が 2 倍ゆるい** | %12/%9 | ⇒ **実データの識別帯 (\|dx\| ∈ (3.5, 7.0)mm) = 480 artifact 中【0 本】** ⇒ **全実データ対照が、2 倍ゆるい guard も通す** |
| 5 | ⭐**「この datum assert は今日発火する」** | %10 | **実評価 = `abs(809+20−829) = 0.00mm` ⇒ PASSES。** ⇒ **発火を見ていない guard を「発火する」と主張** = 今夜 9 回潰した病理の 10 回目 |
| 6 | ⭐⭐**probe 2 形式 (hardcode / config) が同じ非対称誤選択を通す** | %9 | **左=lip/右=壁 (幅 18.5mm) ⇒ 両 assert PASS。** かつ **%12 の幅 tripwire (10-20mm) も通す** ⇒ **2 重に穴** |

🔒 **確定形 (4 層。1 つ欠けると黙って壊れる):**
1. **選択** = チャンネル中心を跨ぐ geom を除外 → 各側の**最内面** (%10) ⇒ **lip は構成上 選べない。hardcode ゼロ。誤選択は bar を *きつく* しかできない。**
2. **tripwire (oracle)** = `len(cands_left)==2 and len(cands_right)==2` + ⭐**`0.0145 < 幅 < 0.0155`** (15.0±0.5mm、source cite) ⇒ **全セレクタ誤選択を直接落とす。** (⭐**対称性 assert は冗長かつ datum を再導入 ⇒ 落とす。幅が真に包含する。**)
3. **閾値** = **world 座標形** (`x_clip`/`clip_y`/`GROOVE_CENTER_Z`/`CABLE_RADIUS` を一切使わない) ⇒ **datum ゼロ。** ⛔**床 (L3) は入れない。**
4. **probe (oracle、形 C)** = **CONFIG (`CLIP_X`/`CLIP_Y`) から** ⇒ ⭐**guard = built model / test = config ⇒ 【異なる source】⇒ 本物の two-key ⇒ 相殺しない。** **10 本** (脚 × 側 × {raise, silent} から *導出*: x:4 / dy:4 / z:2)。
+ **schedule ごと凍結** (%9 実測: 腕は onset 時 **0.0000 mm/f で静止**、把持は **onset+54** で開く ⇒ **凍結しない実装は cable を落とす**)
+ **WAIT_MAX に banked 根拠なし** ⇒ 第 1 run は寛大に、**cell ごとの実 wait を log** ⇒ 実測から production 値
+ **救済数 = UNKNOWN (0〜8)。bank するな。** ⭐ p5: **問いは「何本救えるか」でなく【STEP 7 は完了したか】。**
+ **命名 `gripper_pressed_inside_channel()`。⛔`seated()` 禁止** (`z_c1_seated` の罠の再演)

🔒⭐⭐⭐ **今夜の総括 (DoD 規則に昇格):**
> **対照は【数】でも【形式の多様性】でもなく、【何を落とすか】で設計する。各対照が「他が捕まえられないもの」を捕まえているかを、*表で* 示す。⭐その表こそが DoD。**

⛔ **%9 の over-claim = 28 件 (全て訂正済)。** うち最も高くついた 3 件: **#24 script に verdict 文字列を hardcode し自分の測定値と矛盾** (今夜 2 度目) / **#26 線形外挿を測定として報告** / **#27 自分の出力に並んだ 2 数字のうち *ゆるい方* を上限に採用** ⇒ 🔒 **機構: 自分の出力に複数の数字が並んだら【最も保守的】を採る。選ぶ根拠が無いなら選ぶな。**

## 5.34 ⭐⭐⭐⭐⭐ **変異生成器の完全性が、対照表の完全性を決める — そして gate が作った当日に発火した** (2026-07-14 18:0x-18:1x)

### probe 8 本では穴が残る (%9 の系統的掃引)
**確定 probe は raise を両側に置いたが、silent を片側にしか置いていなかった。**
⇒ ⭐ **silent probe は bar の *内縁* を検定する ⇒ 内縁にも 2 側面が在る ⇒ silent も両側から。**
| 左 bar のずれ dL (きつくなる量) | 6 本 (+側のみ) | 8 本 (+raise 鏡像) | ⭐**10 本 (+silent 鏡像)** |
|---|---|---|---|
| **0.5 / 1.0 / 1.5 / 2.0 / 2.5 / 3.0 mm** | 🛑 漏れる | 🛑 **漏れる** | ✅ **捕まる** |
| 4.0 / 5.0 / 6.0 mm | ✅ | ✅ | ✅ |
⚠ **幅 tripwire も素通り** (左だけずれても *幅* は 15.0mm のまま)。
🔒 **生成規則の訂正**: ⛔「脚 × **側**」(= raise 5 + silent 3 = 8) → ✅ **「脚 × 側 × {raise, silent}」** ⇒ **x:4 / dy:4 / z:2 = 10 本。人間が数えない。**

### ⭐⭐⭐⭐⭐ 自己言及的な証明 — 私の検定自身が %12 の mutation 規則を証明した
%12 の規則: **「変異は【人間の想像】でなく【コードの構造】から生成せよ」**
⛔ **%9 は変異を *手で* 選んだ (dL = +4mm = r の 2 倍)。⇒ それは `pz silent` (x = CLIP_X = 350.0 に在る) に **偶然** 捕まった** — 4mm のずれが左 bar を 350.5mm へ押し上げ、中心点 350.0 を窓の外に出したから。
⇒ 🛑 **「捕まる」と結論する 1 手前だった (over-claim #29、自己捕捉)。**
✅ **系統的掃引 (dL = 0.5〜6.0mm) が【実際の穴 (0.5〜3.0mm)】を見つけた。**
⇒ ⭐⭐⭐ **∴【mutation generator の完全性が、identifiability 行列の完全性を決める】。手で数えた変異集合は、手で数えた対照集合と *同じ罠*。**
🔒 **generator への要件: 各 bar の【各側】について、ずれの【大きさを掃引】せよ。⛔単一の極端値を選ぶな。**
⇒ ⭐⭐ **極端な変異は「捕まって当然」。⭐危険なのは【bar のすぐ隣の変異】。⇒ generator は bar の近傍を密に掃く必要がある。**

### ⭐⭐⭐ gate が【作った当日に、作った本人の裁定を止めた】
%12 の新 gate (pB の「見えている ≠ 読まれた」から): **「実装指示は、著者でない pane 1 名から【読んだ + 反証あり/なし】の 1 行を得て初めて通過。⛔無応答 = 未通過。」**
⇒ ✅ **%9 が【未通過】を返し、%12 自身の裁定 (probe 8 本) の穴を止めた。**
⇒ ⭐⭐⭐ **∴ この gate は【発火を見た】。⇒ 今夜 10 回言った「発火を見ていない guard は、発火 *できない* guard と区別できない」を、新設 gate が初日に自分で満たした。**
⇒ ⭐ **かつ「hub は自分を検査できない」(%12 own) への構造的な答え: 裁定者の指示を、検証レグが gate する。**

### ⭐ 通信規律の最終形 (p5 の診断が核)
> 🔒 **反証は【自己証明的】— 反例は自分の算術を携えてくる ⇒ 出所は無関係、相関しても汚染されない。**
> ⛔ **同意は【自己証明的でない】— 読んだ人の「同意」は価値ゼロ。**
> ⇒ ⭐ **∴ broadcast は【反証には安全】で【確認には有毒】。⇒ 直し方は「反証を黙らせる」でなく【異なる問いを割り当てる】。**
🔒 **+ %9 の 2 点 (採択): (1) 検証レグは【裁定者の裁定そのもの】も対象に含む (今夜 %12 の裁定は 6 回訂正され、全て *生の主張を見た者* が拾った) (2) 検証レグは【成果物】(code の diff + 対照の生出力) を読み、【筋道】は読まない (筋道を読むと「そう書いてある」を確認しがちになる)。**
