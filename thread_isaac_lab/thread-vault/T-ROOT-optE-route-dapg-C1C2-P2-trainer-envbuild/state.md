---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild
node_name: "W1 P2 env build (Stage-A spec v0.8.1 実装、staged ≤800 行/diff L3 chain)"
goal: "banked Stage-A 設計 (STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md v0.8.1、全 gate PASS + Rs W0-a 承認) を env-core 上に実装する。対象 = route_t/HOLD/oracle-API/bank v2/DR+recenter+curriculum/export+会計/OG port/recording contract v2/smoke 一式 (est ~1.35-2.55k LOC)。charter = eval_runs/troot_optE_dapg_wholeroute_scope_20260701/W1_ENVBUILD_CHARTER_RSTECHLEAD_20260712.md (B0-B7 chunk 列)。設計判断は本 node で行わない — 疑義 = STOP → spec ERRATUM 手続き (charter §7-4)。campaign は不発効 (HIGH-COST + production-launch + fresh Rs GO 背後、不変)。"
goal_verification: |
  charter §3 B0-B7 全 chunk close = node COMPLETE:
  - B0: c1pin revert + og format diff disposition + baseline sha pin
  - B1-B6: 各 chunk = L3 chain (pre 5体 [implementation-vs-spec fidelity scope] + [RULE-CHECK]) + chunk DoD legs + flag-OFF byte-preserve subset (毎 chunk、pinned baseline) + %10 audit + %12+%9 verify + explicit-path commit + p6 relay
  - B7: spec §8 smoke legs 全数 (bar = spec §8 表が正)。motion-bearing leg = 視覚レグ必須、物理妥当性正式 verdict = Rs video human-GT
  - 完了報告に §6 Rs 後決項 (OG band / mix 比率 / MAX_HOLD 再導出 / M-AB 時期) を単独項で同梱
status: IN_PROGRESS
parent_node: T-ROOT-optE-route-dapg-C1C2-P2-trainer
children_nodes: []
dependencies:
  precedent:
    - "Stage-A design-gate COMPLETE (spec v0.8.1 banked d17f8f9cd6/e8d53aae10、design chain 全 PASS)"
    - "Rs W0-a =「A」一括承認 2026-07-12 13:29 (W0A_PACKET_RSTECHLEAD_20260712.md:89 —「W1 (env build) 着手可」+ D-B trigger 充足)"
    - "P2-envcore COMPLETE (基底 build f6ee1443f5→HEAD 1640L) / P2-routeexec COMPLETE-with-carry-forward (抽出 twin run_route:1028 byte-repro 81/81)"
  blocker: []
created: 2026-07-12T13:51:00+09:00
last_updated: 2026-07-14T04:05:00+09:00
spec_version: LTM-1 v1.2
session_history:
  - "2026-07-14 ~04:05 %11 (COORD, w2:p3) ⭐**B3a (producer capture + offline bank v2 builder) build COMPLETE — build 本体 commit = `575069abe5` (⚠`a00a0a97f8` ではない、B3a-F1 参照)、legs 全 PASS (W1_B3A_LEGS_FAIL=0)。3-leg post-verify PASS (%12+%9) + %10 audit PASS-WITH-FINDINGS。** ⛔**同時に B3b = STOP (BLOCKED_FOR_USER、上記参照)**。chain: conformance v2.2 → 5体 [VERIFY] (CRIT 5 class を build 前に捕捉: Rs-LOCK 抵触 / bar が空虚 / fork write-set 欠落 / qd の ground truth ゼロ / seg window 陳腐) → %12+%9 joint PASS-WITH-CORRECTIONS → [RULE-CHECK] → B3a build → ⭐**leg 走行で自己捕捉 DEFECT 2 件 (bar 緩和でなく fix-first)**: **DEFECT-1 = capture が dead mirror (mjw_data) を読んでいた** (task_config.py:116 USE_MUJOCO_CPU=True ⇒ live は mj_data、mjw_data は put_data で無条件生成されるが CPU path で一度も step されない) ⇒ hidden-state channel が no-op (qacc_warmstart 0/562611・eq_active 変動ゼロ) ⇒ k=3/4/5 の fork が **pin OFF を restore** = FORK-1 同 class の silent mismatch。fix 後の live 実測 = **warmstart 非ゼロ 559764/562611 / absmax 1.08e6** (mjDSBL_WARMSTART=OFF、%12 独立確認) ⇒ ⭐**『0/562611』は死んだ計器の artifact であって substrate の事実でなかった — 当方は これを根拠に「非 item 化」を提起しており、%12 の F-5 (1) 裁定 (symptom で再分類するな + regret 非対称) が absmax 1e6 の live hidden state を bank から落とす事故を防いだ**。**DEFECT-2 = leg3 の bar が構造的に不適** (SIM_SUBSTEPS=10 ゆえ位置差分は frame 平均のみ ⇒ κ=0.92/1.81 の k=2/3 で 4 変種同時 FAIL = 計器の帯域不足 / 「wrong substep」は κ/10≈1.6% しか動かず 20% bar で原理的に不可視 / scale に盲目) ⇒ **2-param 回帰 (gain / substep index m̂ = 15.5−10·(b/g) / R²) + identifiability 表 8 摂動へ置換** (real のみ ACCEPT、m=9→9.30 / null→degenerate / ×0.98 逆符号 / permuted / frame-shift 全 REJECT)。⭐**副次 catch: leg6 が index-space trap を捕捉 — 記録 pinned_body=Newton body id (55) vs eq_obj1id=MuJoCo body id (56、worldbody が index 0) ⇒ 初版 resolve_pin_eq_index は eq 26 に着地 (正解 27) = 別 constraint を silent に pin。F6 (_jws) の第 2 目撃例、しかも『その罠を防ぐために書いた関数』自身が踏んだ。** fix = offset を producer 自身の eq 表から導出 + round-trip assert。%12/%9 ERRATUM 群 fold: **§18 ERRATUM-F** (source inspection では liveness を discharge できない — 設定 backend 上の runtime 測定のみ) / **F-5** (D-1 の bar 差替え = 存在でなく L5a の restore-vs-zero A/B が決める; eq_active は構造的必須) / **F-6** (provenance = backend_id + layout_hash、eq は identity 解決) / **F-7.4** (⭐**零・不在・変動なしの測定は「対象が無い」のか「計器が死んでいる」のか区別できない ⇒ 必ず positive control を併走させよ**)。legs: leg1 run_route byte-identical (2080 行) / leg2 capture read-only (npz sha EXACT 1/1) / leg3 substep readout (m̂ 9.81・9.89 vs 予測 10、identifiability 8/8) / leg4 units (境界 EXACT + fail-loud 5 種 + null-bank 棄却) / leg5 producer 5-cell byte-repro 5/5 / leg6 hidden-state liveness (eq_active[27] ≡ 記録 pin_active、**lag=0 を実測して pin**、identity round-trip、per-field liveness gate)。source = route_executor.py +570 / test_routeexec_state_bank.py +160−3 = **730 行 (cap 800 内、%10 F-6 実測で訂正)**、増分は全て検証機構。npz は commit せず sha256 で pin (capture = 312dc63898…)。⛔**B3-α (%9 発見、%11+%12 が on-disk 独立確認) で B3b STOP**: RL env は pin 候補 eq をゼロ本しか作らない ⇒ banked eq_active に restore 先が無い + **env は C1 を保持できない** (%12 実測: C1 距離 4.16mm 一定 [記録] vs 単調離脱 52.87mm [env])。**移植の検証は donor だけでなく recipient (受け皿の能力) を検査せよ** = 本 arc の新 sub-type。"
  - "2026-07-13 ~01:27 %12+%11 ⭐**B2 CLOSE** (%12 宣言 [msg 自称 01:30 = 先打ち、受信時実測 01:27]、3-leg joint: %12 PASS + C1 CONFIRM [source +649/-19 ≤800 独立実測] / %9 PASS + as-built 4 点 [release_step=762 の 900−762=138 ≈ tail 139 別鍵] / %10 audit PASS-w-FINDINGS [F-1 MED promised-unit ×3 / F-2 LOW 5]) + 追補 eb17e51a7d 全消化 (%12 roster-sweep 実読確認): (a) resume 意味論 unit (fire→chunk-end pin→resume→次 chunk 先頭駆動・再走なし) + div ±1-chunk 判別 (b) stub×flag ValueError unit (c) leg9 tail 抑制 3 述語 (A 抑制+event / B S5 −10 / C flag-OFF −10)。⭐C1 裁定 (banked): shadow bar discharge = prefix≡banked EXACT (0.000000mm/343 step) + banked 交差 t343 ∈ bar + 帰属 −1 step — live 交差 bar 化は『HOLD が正しく働くほど FAIL』の自己反駁。⭐governs: armed quiet max **10.407mm** = B3 restore-fidelity band (spec §6.2 L7 の再計測値)。B3 carries (%12 再掲): 6 点 (latch pre-set / bank_boundary wiring + assert / writesite 反転 / forbid 撤去 / k0 不変量) + capture = 抽出 twin run_route:1028 pin + cell-parameterized + 1-step post-restore 動力学 leg (body_q_prev/Dahl)。B3 から %12+%10 の『約束 unit roster 実在照合』二重 sweep が立つ。"
  - "2026-07-13 00:51 %11 (COORD, w2:p3) ⭐**B2 (HOLD + oracle API) build COMPLETE — commit a2f544662b、%12+%9 post-verify + %10 audit 待ち**。chain: [L-TRIAGE] L3 + DESIGN-GATE cite 充足 → conformance v1 (23:15) → 5体 (CC2 MED2 / CC3 HIGH2 [fixture 誤 file+writesite 漏れ] / CC4 **CRIT1 [較正 bar 10x index 誤読 — spec f343 = RL step、npz 実測で確定]** / CC5 HIGH1 [tail (iv) no-owner] / CC6 HIGH3 [評価点/tail IndexError/reset 漏れ]) → 全 ACCEPT fold v2 → %12 asks 4 点回答 (23:29 A1-A4: mask 機械導出/chunk 終端統一/rc.*/fail-loud) → %12 PASS (23:48) + 裁定 2 (ERRATUM-3 67d01d0c15 = tail (iii)(iv)→B2, (i)(ii)→B7 / fires bar = shadow 系列) → %9 PASS-w-NOTES (23:42、B2-F1 fencepost) → v2.2 → [RULE-CHECK] ALL PASS → build (+7276/-19、source 3 + test 2、新規 source file ゼロ) → legs 全 PASS: 表面適合 5 (⑨a′/DoD⑤⑩ [comparator throughput-key 修正 1 回]/DoD⑥ dict-id/cablediag EXACT vs 311f18cb9b/producer 5-cell vs ca33d1e1a0) + unit 3 suite (release_step=762 pin / mask {0→G1,11→G4} 導出 pin / 状態機械全系列 / neighbor 隔離) + leg7 reset 隔離 + **leg8 較正 cuda:0: g1=98、armed 域発火 0 (max 10.407mm = spec 予測 10.41 一致)、発火 t342 単発 ∈ bar、shadow prefix ≡ banked comp5 EXACT (0.000000mm/343 step)、banked 交差 t343、dones 0**。⭐ask C1 (%12 confirm 待ち): shadow bar の discharge 形 = prefix-EXACT + banked 交差 ∈ bar + 帰属 −1 step (正しい HOLD は shadow 交差を先取りして止めるため live 交差は反実仮想)。carry: B7 に 770/771 fencepost 照合 + claim ① + MAX_HOLD 再導出 (bounded-Δ 注入)。"
  - "2026-07-12 ~17:44 %12+%11 ⭐**B1 CLOSE** (%12 宣言 [msg 自称 17:50 = 先打ち stamp、p6 が実受信 ~17:44 と捕捉 → 訂正済]、3-leg joint: %12 PASS [独立 sha/grep 再実測] / %9 PASS-w-CORR [R-1 harness gating + R-4 CC6-unit + LOW 2] / %10 audit PASS-w-FINDINGS [F-1 = R-4 と独立収束 / F-2 evidence pin]) + 追補 commit 04a31e1e98 全消化: leg6 CC6-unit PASS (world_count=2 flag-OFF、実 step() per-world done branch 発火 dones=[True,False]、route_t≡episode 9 snapshot 恒等、w0 再始動/w1 継続 = :1027 mirror site 実測被覆) / run_legs.sh runner 行 exit-gating + stale-artifact 事前 rm / grep pin (comment 除外 fail-closed 明文化) + unit stdout 3 本 pin / R-2 gripper_qd sentinel + R-3 builder 0∉phases assert。carry to B2+: leg2 comparator = full-dict-diff − 既知変動 key 方式 (substring filter の漏れ 5 key を %10 が捕捉) / stdout は run 時から pin。次 = B2 (HOLD + oracle API) [L-TRIAGE] — hold 較正 両 leg cuda:0 (W-2) / recording contract v2 同梱 (spec §4.2 N9) / conformance = sub-item 列挙方式。"
  - "2026-07-12 17:15 %11 (COORD, w2:p3) ⭐**B1 (route_t 骨格) build COMPLETE — commit e1eac1deb8、%12+%9 post-verify + %10 audit 待ち**。chain: conformance v1 (15:3x) → 5体 [VERIFY] (CC2 PASS / CC3 REVISE / CC4 REVISE-CRIT / CC5 REVISE-HIGH / CC6 cond) → CC1 DECIDE=REVISE 全受容 → v2 c4c8212649 → %12 CONCUR (ERRATUM-2 ce6cdebf29 = B1 セル + §4-2 表面適合規則へ一般化) + %9 PASS-w-1-corr (F-1 W=non-prefix) → v2.1 51d4f31771 joint PASS → [RULE-CHECK] ALL PASS → build (+169/-15 source 4 files、新規 file ゼロ) → DoD 全 PASS: grep leg (5-site exact / consumer 0) + unit 3 本 (state_bank 新 world-slice 判別 test 込み / writesite 不変 / gate-ii) + ⭐env-side flag-OFF legs (⑨a′ 25/81+per-cell EXACT banked 一致 / DoD⑤⑩ diff ゼロ / DoD⑥ dict-identical / cablediag env 軌跡 npz 311f18cb9b と全 array EXACT) + producer 5-cell 5/5 vs ca33d1e1a0 (evidence = w1_b1_dod_legs/)。⭐5体の CRIT catch: v1 の経験 leg (producer byte-repro) は env 非実行で B1 diff に感度ゼロ = 偽検証構造 → env-side legs へ差替え (ERRATUM-2 の源)。B3 carries: fork-time latch pre-set (CC5 無所有者 crack) / bank_boundary wiring + post-fork assert / writesite 反転 / forbid 撤去 / k0-bank 禁止不変量。次 = post-verify PASS で B1 close → B2 (HOLD + oracle API、hold 両 leg cuda:0 pin [W-2])。"
  - "2026-07-12 15:10 %11 (COORD, w2:p3) ⭐**B0 COMPLETE (全 4 項 discharge)** — B0-1 c1pin 3-file dead-branch c70ba1b849 (branch deadbranch/c1pin-refuted-20260712、DO NOT BUILD ON + refutation evidence) → revert a6b7ab6007 (net-zero + tree clean verify、%12 独立検証 PASS) / B0-2 consumer③ = ff-replay のみ縮退 記録 / B0-3 og format revert (完了済 14:0x) / B0-4 flag-OFF baseline pin **ca33d1e1a0** = 29-cell union 全 golden-match (2 層: 毎chunk 5 [x0_y0+DR4隅] / gate-iii 25 [dod9a_prime offline-mirror 導出、count=25 EXACT]; run1 5/5 byte-id + ref self-check PASS / run2 24/24 byte-id + strict mod==golden; %12 条件 a=導出 script+membership sha を manifest 記録 / b=B7 set-equality assert 埋込)。⚠finding: x0_y0 ∉ gate-iii 25-set (env exact-split 述語の不成立側 = 25-vs-58 gap 実体) → union pin で被覆 (%12 ACCEPT)。⭐副次: post-revert route_executor の golden byte 再現 = B0-1 regression 証拠兼務。次 = B1 route_t 骨格 [L-TRIAGE] (charter §4 template)。"
  - "2026-07-12 14:10 %12 (RS-TECH-LEAD, w2:p4) ⭐charter v0.2 BANKED — p1 verify 14:04 = PASS-WITH-CORRECTIONS (転記忠実性 全数照合 PASS / MED 2 fold: W-1 = §6 multi-cell 行に提示者 %12 + W1 完了報告 1-line Rs confirm / W-2 = B2 hold 両 leg を cuda:0 pin に訂正 [f343±1 bar は device 固有、CPU discharge = false-verdict risk]) → blocker 解消、**B1+ 解禁**。ERRATUM-1 (907a526df7) = B0-1 revert scope 3 files (%11 catch: newton_skill_env_base.py +28/-2 omit、%12 on-disk 裏取り: comment の FORK-1 root cause 主張 = REFUTED 済 false + spec 参照ゼロ)。B0-3 完了 (%11、og = revert 択 loud: pre-existing :32 Japanese-text が commit BLOCK → B6 行に carry 註記)。副次: pB tree-wide -f 由来 format dirt 多数 (B0 scope 外、報告のみ、chunk は explicit-path commit ゆえ非干渉)。"
  - "2026-07-12 13:51 %12 (RS-TECH-LEAD, w2:p4) ⭐node 作成 (trainer charter §1 lazy-spawn 授権 + Rs W0-a W1 着手承認 + 本 turn Rs directive「W1 build charter」)。charter v0.1 DRAFT 起草 (W1_ENVBUILD_CHARTER_RSTECHLEAD_20260712.md: B0-B7 chunk 分割 / per-chunk L3 gate template / 担当 %11 build・%10 audit・%12+%9 verify [devplan §7:192] / Rs 後決項 carry 表 / 衛生規則 M12)。prior-art V7 = PASS disposition (hits = 認可設計系譜の自己参照のみ)。on-disk 前提実測: c1pin +23/+70 残 dirty (B0-1 revert 対象) / run_route:1028 実在。1:1 binding = %11 (COORD) builder session (charter 受領時)。次: p1 verify dispatch → PASS 後 %11 B1+ 解禁 (B0 は即時可)。"
---

# T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild — working notes

- 現況 (2026-07-14 05:3x): B0 ✓ / B1 CLOSE ✓ / B2 CLOSE ✓ / ✅**B3a = CLOSE 確定 (2026-07-14 05:15-05:22、時刻は git author date と %10 stamp が anchor — 下記 §RESOLUTION の時刻訂正参照)** — 記録訂正 + guard-fire commit `0f13684709`、**3-leg 全 CONFIRM** (%12 on-disk 2 点照合 / %9 独立 run で unit 7/7 + guard identifiability 10 分岐 + Rs-LOCK run_route sha 4 点 byte-identical / %10 audit 残指摘ゼロ + positive control の非循環性を保全コピーで独立照合)。**push 済 (fork/rlrk/optE-s2-substrate-swap = `0f13684709`、remote==local 実測)**。⚠**build 本体の commit = `575069abe5`** (`a00a0a97f8` は conformance 追補のみ、source ゼロ — B3a-F1) / ⏳**B3b-B7 = STOP 継続 ((d) 結果待ち、下記 §RESOLUTION)**。 ⛔⛔⛔**06:20 追記 — B3b-B7 STOP に *2 本目の独立した理由*: RL 成功条件の半分がタダで通る (%12 発見・p6 独立確認)**。`c1_retained_final` (**G6 SUCCESS = c1_retained_final AND c2_seated_honest**) は **X を一度も見ない天井チェック** (`newton_route_env.py:1491-1495` + `_c1_retention_m:1272-1286`) ⇒ **p6 正典 positive control (`5f1c3f92`、自前実装): t=0 で cable が table に寝ていて (804.0mm) 掴まれてもいないのに 述語 = PASS、真の横ズレ 50.00mm = 溝半径の 8.3 倍**; PASS frame の 22.1% で cable は溝の外 (MAX 50.61mm)。⚠⚠**ただし「policy は何もしないで半分を獲得」は *env については誤り* (p1 実読で訂正、p6 own = 私も同文を書いた)**: env は `:1543` `p3 = (c1_seat < T_GROOVE) and (ph >= 2)` で **lateral 込み `c1_seat` を G3 latch gate に使用** + `:1553-1555` **ORDERED latch** ⇒ t=0 の table 寝 cable は env success を通らない。⇒ ⭐⭐**欠陥は 2 つ・別物**: 【**ENV**】lateral を見るのは **G3 latch 時だけ** ⇒ ⛔**SUCCESS 時点で再チェックせず、latch 後に C1 から抜けても +200 が出る**。【**OFFLINE** (`strict_v2` / 公式 0.716)】⛔**lateral がどこにも無い** (`p9_recount_strict_v2.py:39-44` = Y/Z のみ / `:107` = 天井、**p6 source 直読**) ⇒ **c1_ok = 81/81 = 完全な no-op** (p1 実測) ⇒ ⭐**load-bearing は OFFLINE 側 (C-5/P4 経路)**。**修正も 2 つ (同一 fix ではない)**。⭐⭐**穴は移植由来でなく *凍結 reference 自体* ⇒ %10 への「producer か移植か」の問いは CLOSED** (p6 source 直読)。 ✅⭐⭐**爆風半径は狭い — 歴史的 0.716 は無効化されない** (⭐**p6 が source 直読で決着 = %10 依頼 DISCHARGED**): `pen_c1_seat` = producer metric の passthrough (`recount_strict_v2.py:81`) → 実体 = **`route_executor.py:2794` `_min_dist_mm` = MuJoCo `mj_geomDistance` = 符号付き geom 間距離 (負 = 貫入)** ⇒ **lateral 感応** ⇒ ✅**58 SUCCESS cell 全てで C1 は実際に座っていた** (min −3.07 / median −0.67 / max +0.52mm、3mm bar 超過 0/58) ⇒ ⭐**危険は *前向き* (RL の exploit) であって *遡及的* ではない**。⚠**残る限界**: `mj_geomDistance` は「clip geom への接触/貫入」を示すが「溝内側への capture」ではない (`_clip1g` 未確定) ⇒ p5 の capture-blind 指摘は完全には反証されず (⇒ %12/%10)。⇒ ⛔**reward/成功条件 欠陥 = 直交ゲート = L3 + Rs 専権** (`/reward-design` + `/pre-check` 必須; ⭐**p5 の r5 §1.4 STEP 9 に *既に annotate 済* の gap ⇒ 新バグでなく「測れていないと設計面が書いた指標が成功条件に採用されていた」構造** ⇒ 修正は metric の新設計)。⇒ ⛔**offline artifact の `c1_retention: pass` は無効、path #1 (pin 発火) は依然 OPEN**、**(d2) の必要性は上昇・P1 bar は *横ズレ (lateral)* で測ること**。⛔⭐**bar 決定前に metric identity を固定せよ** — p6 の 4.16mm (正典・中心↔中心 XY) と p1 の 2.82mm (b4e1fd4c・geom min-dist) は **別の量** (= E-4 cross-mode bar 流用禁止 `cf29601f6c`)。⚠**Rs 上程は「*述語* が無効・*数値* は生存・危険は RL の exploit」の形に** (「全て無効」は強すぎ = 過剰警報)。〔下記 §RESOLUTION の W-1/W-3 節 = **06:1x SUPERSEDED**: W-3 (物理) = 正典再測で ANSWERED (壁 #4 は死んだまま)、W-1 = **p5 の L-geom witness FOUND** (`shared/GEOM_WITNESS_5CLIP_p5_20260714.py` sha `6fdaafcf`、6/6 PASS、p6 独立検算一致 + source 直読で free-root/limit-なし revolute を確認) ⇒ **「どちら向きにも witness が無い」は もはや偽**。ただし **立ったのは L-geom のみ / L-phys・L-exec は未確立** ⇒ 「達成可能」とは書かない。詳細 = 地図 now-box + LEDGER W1 行〕
- ⚠⭐ **B3a-F1 (MED、commit provenance) — 正本は本 file 下部の %12 記載 (`e458bf9b9e`)。当方 (%11) も on-disk で独立確認済。** 事実 = **`a00a0a97f8` = conformance doc +20 行のみ (source ゼロ) / `575069abe5` = BLOCKED_FOR_USER + B3a source 730 行**。✅**成果物は無害** (legs 完了 03:38:13 < sweep 03:43:50、working tree == HEAD、DEFECT-1 fix は `route_executor.py:851` に在る ⇒ commit 済 code = 全 leg PASS した最終 code)。⛔**history rewrite はしない** (%9/%12 一致: 不要かつ有害)。
  **過失の切り分け (正確に)**: (a) **sweep 自体 = %12** (path 制限なし commit が当方の stage 済 index を巻き込んだ — %12 自認)。(b) ⚠**当方 (%11) の過失 = 別項**: commit 後に**その commit の中身を検証せずに「B3a 本体」と報告した** (`git show --stat` を打っていれば source ゼロに即気付けた)。⇒ **記録が事実と一致しない主張を、当方が発信した**。**教訓 = 自分の commit も「narrative でなく on-disk で検証してから主張する」** (`feedback-narrative-signal-not-established-fact-verify-on-disk` は他者の主張だけでなく**自分の commit にも適用される**)。

✅ **BLOCKED_FOR_USER = 部分解除 (Rs 裁定 2026-07-14 05:2x 逐語「はしらせて　push」)** — 下記 §RESOLUTION 参照。**(d1)+(d2) の実行 = 承認 / push = 承認 / B3b-B7 = (d) 結果まで STOP 継続 (pin の恒久 disposition は Rs 未裁定)**。以下は上程時点の記録 (歴史、⚠層 3 は §RESOLUTION で訂正済)。
**Context (B3-α、%9 発見 → %11 + %12 が on-disk 独立確認):**
- producer は `PERCLIP_PIN=1` で **40 本の pin 候補 eq** を事前確保 (test_newton_clip_routing.py:1405)。golden もこれで録画。総 eq = 46 (40 + 構造 6)。
- ⭐**RL env (`build_multiworld_scene`) は構造 eq 6 本のみ、pin 候補ゼロ** (newton_skill_env_base.py:1451 の comment 自身が pin を *test harness* に帰属)。`newton_route_env.py` の pin 参照 = 0。
- ⇒ **bank の `eq_active[27]` に restore 先が存在しない** (bank neq=46 vs env neq=6)。B3a の layout_hash assert は**正しく発火して BLOCK する**。
- ⭐⭐**より深い (%12 実測)**: **env は C1 を保持できない** — C1 着座 seg 27 の C1 距離 = 記録 (pin あり) **4.16mm 一定** vs env (pin なし) **1.08 → 5.76 → 14.14 → 25.80 → 41.20 → 52.87mm と単調離脱** (t=255→396)。⇒ env は reference trajectory が依存する機構を欠く。RL success 述語は `c1_final` を conjunct に持つ ⇒ **pin 無しで task 達成可能かも open**。
- ⚠**FORK-1 根本原因も open に戻る (断定はしない)**: C1 離脱 runaway (t≈300-320) が grip divergence runaway (t≈337) に**先行**。かつ c1pin「REFUTED」の evidence に **pin が発火した positive control が無い** ⇒ spec F-7.4 の規律により再検証を要する。⛔ 同時に「REFUTED を『pin 不要』の根拠に流用しない」も守る (prohibited.md)。
**Options:** A) pin を RL env へ配線 (新しい正当理由 = fork-state 実現可能性; 過去の REFUTED は *FORK-1 fix 仮説* に対するもので本件とは別問題) / B) bank を k=1,2 に限定 (**G3-G5 curriculum を失う = bank v2 の主目的そのもの**) / C) curriculum を re-scope して carry
**Recommendation:** 当方は推奨を付さない (前提 scope = Rs 専権)。%12 が Rs へ上程済 (`575069abe5`)。

⛔⭐ **B3b 再開時の DoD 必須行 (%9 carry、B3a CLOSE 時に確定)**: **`assert_bank_matches_live` は unit (guard identifiability 10 分岐) で発火が実証済だが、production caller がまだ無い** (restore = B3b、STOP 中ゆえ正しい状態)。⚠**「unit で発火する」≠「live restore path で実際に実行される」** = **機構は在るが到達されない = appearance-only = CLAUDE.md §15 の ABSENT-IN-CODE class** (本 arc で一晩焼かれた当のもの)。⇒ **B3b の DoD に明示行**: 「**B3-α の状況そのもの (producer bank neq=46 → RL env neq=6) を live restore path に食わせ、`assert_bank_matches_live` が実際に raise して restore を止めることを run 出力で示す**」。unit の PASS で代替しない。(LOW) `require_canonical=False` は synthetic fixture 専用 — production caller から到達可能にしない (今日は到達不能、%9 確認済)。
- Anchors (§運用4): LEDGER row49/50 → charter (本 node) → spec v0.8.1 (設計 SSOT) → W0A_PACKET (数値 decision-of-record) → devplan §7:192 (担当)。
- 数値基盤 = Rs W0-a 採択値 (HOLD 15/12/24placeholder、Δ-bound 0.020、DR±20 OFF 既定、mix 集合のみ)。smoke 再導出条項付きの値はその条項が governs。

---

## ⛔ BLOCKED_FOR_USER (2026-07-14 03:4x、%12 — B3-α / %9 escalate / FOUNDATIONAL INVARIANT #5 抵触)

**BLOCKED_FOR_USER: RL env に clip-retention pin (INVARIANT #5 の唯一の認可例外) を配線してよいか。配線しない場合、bank v2 の k≥3 fork は実現不能であり、かつ RL task 自体の達成可能性が open になる。**

### Context (全て on-disk 実測、%12 独立検証済)

1. **producer は pin を持つ**: `test_newton_clip_routing.py:1405` = `PERCLIP_PIN=1` gate で 40 本の pin 候補 eq を pre-allocate。golden もこれで録画 (eq = 40 候補 + 6 構造 = 46、#27 が activate、`pin_active` = frame 2544-7706 ON)。
2. **RL env は pin を持たない**: `build_multiworld_scene` の eq は構造 6 本のみ (`newton_skill_env_base.py:1621` 4-bar / `:1639` mirror)。pin 候補ゼロ。`:1448` の comment 自身が pin eq を *test harness* に帰属。`newton_route_env.py` の pin 参照 4 件は全て無関係 (phase-active clip XY の "pin" 用語)。c1pin 配線は B0-1 で revert 済 (tree clean)。
3. ⭐**帰結 A (bank)**: bank の `eq_active[27]` に **restore 先が存在しない**。F-6 の layout_hash assert が発火し (bank 46 eq vs env 6 eq) restore 前に fail-loud で BLOCK する = guard は正しく仕事をする。**k=3/4/5 の fork state は現 env で実現不能** (その境界で cable は active constraint で C1 seat に保持されたまま腕が持ち替える。pin 無し env へ restore = 「座っているが保持されていない」)。
4. ⭐⭐**帰結 B (task 自体、%12 新規測定)**: **env は C1 を保持できない**。C1 着座 seg 27 の C1 中心からの距離を実測:
   - **記録 (pin あり)**: t=255→396 で **4.16mm 一定** (pin_active=1 で保持)。
   - **env (pin なし)**: 同 window で **1.08 → 5.76 → 14.14 → 25.80 → 41.20 → 52.87mm** と単調に離脱。
   ⇒ **env は reference trajectory が依存している機構を欠いている。** RL の success 述語は `c1_final` (C1 保持) を conjunct に持つため、**pin なしで task が達成可能かどうか自体が open**。
5. ⚠**FORK-1 根本原因の再検討 (open question、断定しない)**: C1 離脱の runaway (t≈300-320) は grip divergence の runaway (t≈337) に **先行する**。かつ **c1pin の「REFUTED」判定の evidence (`comp5_c2seat_fullfire_c1pin_result.json`、banked 311f18cb9b) には pin が実際に発火したことを示す positive control が無い** (記録内容 = steps_run 342 / max_phase 3 / NUMERIC_NOGO のみ)。**spec F-7.4 の規律 (「効果なし」の測定は「機構が無関係」と「機構が発火しなかった」を区別できない) により、当該 REFUTED は再検証を要する。**
   ⛔ **prohibited.md 遵守**: 「c1pin は FORK-1 fix として REFUTED」を「env に pin 不要」の verdict に流用しない (ある方針の FAIL を別方針の根拠にしない)。bank v2 は **別の正当な理由 (fork-state 実現可能性 + C1 保持)** で pin を要求しており、当時その問いは立てられていない。

### なぜ Rs 専権か

pin = **RS71 §0 INVARIANT #5 (NO KINEMATIC TRICK) の唯一の認可例外**。**RL 訓練環境への配線は、認可例外の scope を「scripted producer」から「policy が学習する環境」へ拡張する = 前提 (premise) の変更**であり、design tradeoff ではない (CLAUDE.md §0: 即 L3 + STOP → BLOCKED_FOR_USER → build/probe 前に 5体検証)。policy が非物理的機構に依存して成功する可能性 = sim2real fidelity の一次問題。

### Options

- **(a) pin を RL env へ配線** (新理由 = fork-state 実現可能性 + C1 保持。Rs 承認 → 5体検証 → build)。帰結: bank v2 の k≥3 curriculum が可能に。⚠ policy が pin 依存で学習する sim2real caveat を明示 carry。
- **(b) bank を k=1,2 に限定** (pin OFF 域のみ)。帰結: **G3-G5 curriculum を失う = bank v2 の主目的が消える**。かつ **帰結 B (task 達成可能性) は未解決のまま残る**。
- **(c) curriculum re-scope + carry** (B3b を再設計)。同上。
- **(d) ⭐先に FORK-1 の再検証** (c1pin REFUTED の positive-control 付き再走: pin が実際に発火し C1 を保持することを実証した上で divergence を測る)。**低コスト (cuda:0 数分)、かつ (a)-(c) の選択根拠そのものを与える。**

### Recommendation (%12)

**(d) → 結果に応じて (a) か (b)/(c)。** 理由: 帰結 B (task 達成可能性) と FORK-1 の根本原因は同じ実験で答えられ、W1 全体の前提に関わる。**現状の全 build (B3b 以降) は「env は pin 無しで route を完遂できる」という未検証の前提の上に立っている。**

### 停止範囲

- **B3a = 影響なし → commit 可** (producer 側 capture の忠実性は本件と独立)。
- **B3b (env restore) = STOP** (裁定まで着手しない)。
- B4-B7 = 本件裁定に依存 (curriculum / DR / smoke の前提)。


### ⭐ B3-α 追補 (2026-07-14 03:5x — VT-DESIGN (p5) corroboration。%12 が両引用を on-disk VERIFIED)

**問題は「bank の restore 先が無い」より遥かに大きい。banked spec 自身が pin を routing の機構として名指ししている。**

**FACT 1 (%12 verified — `RS71-System-Spec-SSOT.md` §4 CABLE、FIDELITY BOUNDARY、Rs DECISION B2 2026-06-25、Rs-accepted)**:
> cable は **1-DOF/joint の PLANAR bender**、bend plane = **VERTICAL (sag)** → 動的に表現するのは **vertical SAG + position + free-root pose** のみで、**horizontal routing curvature は表現しない** (5-clip 千鳥の X-Y 曲率には第 2 の bend DOF が要る)。**「Horizontal routing through the staggered clips is therefore KINEMATIC (grasp-drag + the AUTHORIZED clip-retention pin)、NOT a dynamically-curved cable」**。これは **banked sim2real fidelity limitation (Rs-accepted、defect ではない)**。**Cable-SHAPE robustness は in-sim では vertical sag についてのみ trainable/validatable、horizontal routing curvature については不可。**

⇒ **pin は「あれば便利」ではなく、banked spec が routed-hold の機構として指名している。** pin を持たない env は **routing task を表現できない** (cable model に水平曲率の DOF が無い)。

**FACT 2 (p5 canonical 表 r5)**: STEP 9 (A_C1) = 「腕が離れても C1 が cable を独立保持」。**STEP 10 / 16 / 24 / 32 / 40 / 43 の全てが prereq に「9-STILL」を持つ** ⇒ **STEP 9 以降の全段が「clip が保持し続ける」機構に依存**。fork 境界だけの問題ではない。

**FACT 3 (%12 verified — `newton_route_env.py:55-58` の env-core 自身の記述)**:
> 「Producer-grade seat metrics (…**frozen seat-body pin**) are route-executor refinements; **the env-core uses geometric cable-vs-clip proxies** from cable body positions」

⇒ **env-core は pin を持たないことを承知の上で、seat を「幾何 proxy」で *測る* 設計になっている。だが proxy は *測る* 手段であって *保持する* 機構ではない。** env は「cable が clip の近くにあるか」を測れるが、**そこに留める force を持たない**。

### ⇒ Options の再評価 (p5 の主寄与、%12 CONCUR)

- **(b) bank を k=1,2 に限定 / (c) curriculum re-scope は機構問題を回避しない — 先送りするだけ。** bank restore を諦めても、**policy 自身が STEP 9 以降を達成し、env がそれを保持できねばならない** (STEP 10-43 の全 prereq = 9-STILL)。pin-less env では RS71:62 の banked 判断により **routed-hold 自体が動的表現の外**。
- ⇒ **(b)/(c) が真に機構問題を回避するのは「trainer scope を STEP 8 (C1 での解放) より手前で cap する場合のみ」。** そうでなければ壁は **訓練時に再来する**。

### 未確立 (正直に、p5)

「**C1 単独 (STEP 9) なら pin なしで動的保持できるか**」は未証明。RS71:62 の議論は千鳥 = 複数 clip の水平曲率についてであり、直線 cable が単一 V 溝に座るだけなら動的に成立し得る。**だが** (i) 2 clip 同時保持 = STEP 16 では確実に水平曲率が要る → そこでは確実に機構が要る (ii) DoD6 の Rs human-GT が既に「**cable OFF C1**」を出しており、**C1 単独保持も established でない**。⇒ **「pin 不要」を仮定しないこと。**

### 帰結 (%12)

**現 trainer node の全 build (B3b 以降) と、FORK-1 の根本原因診断 (「chaotic amplification ⇒ closed-loop RL のみが fix」) は、いずれも「pin 無しの env が route を保持できる」という *banked spec 自身が否定している* 前提の上に立っている。** これは B3 の問題ではなく **trainer node / W0-a 級の前提問題**。

*%12 — 2026-07-14。p5 の 2 引用は %12 が on-disk VERIFIED。p5 からも Rs へ同内容を報告予定。*

## ⛔⛔ BLOCKED_FOR_USER 更新 (2026-07-14 04:2x) — **3 層に深化。上程 ceiling が上がった**

### 層 2 (%9、%12 on-disk VERIFIED): FORK-1 の終端失敗の帰属は **confounded**、その反証 run は **構造的に fail-silent**

- **pin 発火 = golden f2544 = phase 5→6 = replay t=255** (記録の 67% が pin-ON)。div metric に recentering 無し (`comp5:214`) ⇒ 以下は artifact でなく物理。
- ⭐**t<255 (記録も env も pin 非活性 = 構造差ゼロ = UNCONFOUNDED)**: div_seg24 (把持 seg) 0.007 → **peak 10.56mm (t=124)** → **3.36mm へ減衰 (t=254)** = **暴走していない。excursion して回復している** (%12 再現)。div_max (最悪 seg) は 37.21mm = 実在の unconfounded 形状発散。
- **t≥255 (記録=pin あり / env=pin 無し = CONFOUNDED)**: 3.78 → **129.24mm (34×)**。⭐**grip collapse も drop も 100% この窓の中。**
⇒ **「open-loop は発散する」= CONFIRMED (unconfounded、div_max 37mm)。しかし「⇒ grip collapse ⇒ drop ⇒ RL closed-loop が唯一の fix」= NOT ESTABLISHED。**
- ⭐**c1pin「REFUTED」は unsafe** (%9 が reverted 実装 `c70ba1b849` を実読、%12 確認): latch `_c1_pin_done = True` が **mjm/mjd の None check より前**に「**regardless of outcome**」で焼かれる ⇒ **eq 解決に失敗しても latch が閉じ pin は無言で発火しない。assert ゼロ = positive control が構造的に取れない設計**。かつ eq 解決は **body id 経由 = leg6 が今日捕捉した Newton 55 / MuJoCo 56 の +1 trap と同一経路**。かつ **c1pin run は 342 step で死亡 vs pin-less 499** = 保持 pin が正しく発火したなら生存は延びるはず → **早死には「誤 body への溶接」signature**。⇒ **仮説は「反証された」のでなく「試されていない」公算が高い。**
- ⭐**c1pin 自身の docstring が機構を正しく述べていた** (逐語): *"the multi-world env-core was MISSING this activation (FORK-1 root cause): the C1-seated cable is not anchored, so the light L-hold drops it at the R-release handover"* — pin onset (f2544) は **まさにその handover の直前**。
- ⭐**GOVERNANCE 訂正 (%9、%12 受諾)**: Rs 授権の逐語 (log.md 2026-06-16) = 「**クリップのみ**キネマティックトリックでケーブルを擬似固定して良い／その他は絶対禁止」= **機構 scope (clip での pin) であって file/harness scope ではない**。+ RS71 §4 が pin を routing 機構として NAME。⇒ **env へ pin を配線するのは INVARIANT #5 の *拡張* ではなく *遵守*。env が banked spec に非適合のまま build されていた。** Rs への問いは「不変前提を変えてよいか」(重い) ではなく **「env は RS71 §4 に非適合。是正すると W1 calibration が re-baseline になる。GO?」**。
- **calibration carry**: ✅ B2 の armed-quiet band **10.407mm = SAFE** (max = t=124 = 非 confounded) / ⚠ **HOLD_THRESH 15mm = CONFOUNDED** (初交差 t=343 = missing-pin 窓の中) ⇒ **parity 基板で再導出要**。⚠⚠ **pin-less env では div_grip は policy に関わらず post-255 で必ず 15mm を超える** ⇒ **HOLD 発火は policy の質でなく env の欠損 = reference が到達不能。**

### 層 3 (p5、%12 on-disk VERIFIED): ⛔ **5-clip 目標状態は cable の配位空間の外** — pin では救えない

- **cable = 平面鎖** (RS71 §4: 39 joint 各 1 revolute、bend plane VERTICAL) + **Stage-B 実測「horiz out-of-plane tangent ≤0.173° across 30 held configs」** ⇒ **水平投影は直線**。
- **clip は千鳥** (`task_config.py:202-204`、%12 実測): C1(0.35, +0.150) / **C2(0.40, +0.075)** / C3(0.35, 0.000) / C4(0.40, −0.075) / C5(0.35, −0.150)。
- ⭐**C1 と C3 は共に x=0.35 → その直線から C2 は 50.0mm 外れる。溝捕捉半径 = 6.0mm。比 = 8.3×。**
⇒ **平面 cable は C1+C2 に入れば C3 を外し、C1+C3 に入れば C2 を外す。3 本同時 = 配位空間の外。**
- ⭐⭐**pin はこれを救わない**: eq constraint は segment を *保持* できるが、joint が持たない **bend DOF を供給できない**。RS71 自身が「the 5-clip 千鳥 X-Y curvature would need a **2nd bend DOF/joint**」と書いている。⇒ **pin を配線して買えるのは C2 まで。whole-route (C3-C5) は買えない。**
- **なぜ今まで壊れなかったか**: producer は **C1→C2 (2 clip) しか実行していない** (C3-C5 未実装)。**任意 2 点は必ず 1 つの鉛直面に乗る** ⇒ 2-clip は表現可能。**壁に誰も到達していないだけ。**
- **p5 の反証 2 本は失敗** (R1 「非平面鎖では」→ Stage-B 実測が平面性 CONFIRM / R2 「溝半径が 50mm 級では」→ 実値 6mm)。**未実施の決定的反証 = CPU のみ**: scene を build し C1+C2+C3 へ同時配置を試み、3 溝すべてに 6mm 以内で入るか測る (**入れば p5 が誤り**)。GPU 不要・即実行可。
- **副次 defect (p5 自己申告)**: banked §2.1 の clip↔groove body 対応 (5 seg = 75mm) は千鳥ピッチ **90.1mm** (=√(50²+75²)) と矛盾 — 非伸長 cable は arc ≥ chord ゆえ **最低 7 seg (105mm)** 必要。p5 の r5 §1.4:109 も同誤対応を restate。p5 は独断修正せず Rs 上程。

### Rs option (層 3 が支配的 — 全て Rs 専権)

- **(A) 2nd bend DOF を追加** (= substrate upgrade、RS71 で DECLINED 済) — 全 cable 結果の再検証コスト。
- **(B) 千鳥を外す** (clip を同一 X へ) — ⭐**C1, C3, C5 は既に collinear (全て x=0.35)** ゆえ平面 cable で 5 本貫通可能になる。**task 定義の変更**。
- **(C) 目標を 2 clip (C1→C2) に cap** — 現 producer の実装範囲と一致。
- **(D) pin で拘束違反のまま押し込む** — **物理的に bogus** (「数値 PASS / 動画 wrong」の温床、DoD6 型)。
- **+ (d) 先に低コスト実験 2 本** (Rs 判断の材料、GPU 不要 or 数分): **(d1)** C1+C2+C3 同時配置の幾何テスト (p5 の反証) / **(d2)** positive-control 付き c1pin 再走 (%9 の DoD: 発火 = flag でなく **効果** [seg27 の C1 距離が記録の 4.16mm 近傍で一定] / fail-silent latch を殺す / negative control = pre-255 は pin ON/OFF で不変であること)。

### %12 の git 事故 (own、records-must-match-fact)

**B3a の source (route_executor.py +570 / test_routeexec_state_bank.py +160−3) は `575069abe5` (私の BLOCKED_FOR_USER commit) に混入している。** 原因 = %12 が `git add <state.md> && git commit -m` を実行した際、**path 制限を付けなかったため index に stage 済みだった %11 の B3a source を巻き込んだ** (memory `feedback-explicit-path-commit-git-diff-file-first-sweep-both-directions` 違反 — `git diff --cached --name-only` を commit 前に見ていない)。**コードは無傷で失われていない**が、commit message が実体と一致しない。⇒ **`a00a0a97f8` = conformance doc のみ / `575069abe5` = BLOCKED_FOR_USER + B3a source** が事実。history 改変は共有 tree で危険ゆえ行わず、**本記録を正とする**。

---

## ✅ RESOLUTION (2026-07-14 05:2x、%12) — Rs 裁定「はしらせて　push」

⚠ **時刻訂正 (p6 捕捉、%12 が `date` 実測で確認 = 2026-07-14 05:30 JST)**: 本節の初版は **06:0x/06:1x/06:2x と ~63 分 先打ち**されていた (%12 の date-THEN-write 違反 — 記憶で stamp した)。**検証可能な anchor に差替え**: commit `0f13684709` = **05:09** / `aa15596710` = **05:18** / `e52ab93b9b` = **05:22** (git author date)。⇒ **Rs 裁定 ≤ 05:22** (push と同一 turn)、**B3a CLOSE = 05:15-05:22** (%10 CONFIRM stamp 05:15)。**未来時刻を durable record に書かない** (§運用15 records-must-match-fact: date-THEN-write)。

**Rs 逐語 (2026-07-14 05:2x): 「はしらせて　push」** ⇒ 解釈 (%12): **(d1)+(d2) の実行を承認、かつ push を承認**。**pin の恒久 disposition (option A/B/C) は未裁定** — (d) はその判断材料を作るための測定である。

### 解除の scope (厳密に)

| 項目 | 状態 |
|---|---|
| **(d1) 幾何 feasibility テスト** (CPU、実モデル運動学) | ✅ **実行承認** — 担当 %9 |
| **(d2) positive-control 付き c1pin 再走** (cuda:0、env-core へ測定用最小配線) | ✅ **実行承認** — 担当 %11 |
| **push** | ✅ **実行済** (`73de09eed7..0f13684709` → fork、16 commit、remote==local 実測) |
| **B3b / B4-B7 の build** | ⛔ **STOP 継続** — (d) の結果と Rs の pin 裁定を待つ |
| **pin の恒久 env 配線 (option A)** | ⛔ **Rs 未裁定** — (d2) は「測定のための最小配線」であって恒久採択ではない |

### ⚠ 層 3 の記録訂正 (%9 → %12 受諾、上記 §層3 は歴史記述として残置)

- ❌ **撤回**: 「C2 は C1-C3 線から **50.0mm** 外れる = **8.3×**」「5-clip 目標は **配位空間の外**」 (%12 の over-claim)。
- ✅ **正**: cable の bend plane は自由に向けられる ⇒ 効く量は **best-fit residual**。実測 (SVD best-fit、%9 → %12 が独立再計算し EXACT 一致): **2 clip = 0.0mm (SEATABLE) / 3 clip = 16.7mm (2.8×) / 5 clip = 20mm (3.3×)**。**壁は clip 3 にある** (2 点は必ず 1 平面に乗るので 2-clip は常に可能)。
- ✅ **かつ 5 seat は coplanar (Z=0.809)** ⇒ **90° roll した鎖なら幾何的には zigzag し得る** ⇒ 「配位空間の外」は**厳密には偽**。⇒ **(d1) は root pose の roll を解に許さねばならない** (許さなければ結論を仕込むことになる)。
- ⇒ **層 3 は「B3b の停止理由」ではない (%9 訂正)。停止理由は 層 1+2 = pin disposition + HOLD 較正の交絡。** 層 3 は T-ROOT 級の別 open question であり (d1) が決着させる。

### %9 carry → B3b DoD 明示行 (必須)

⛔ **`assert_bank_matches_solver` (route_executor.py:654) には production caller がまだ無い。** guard は unit で発火が実証されたが、**live restore 経路で実際に実行されることは未証明** = 本 arc が一晩焼かれ続けた **ABSENT-IN-CODE class そのもの** (機構は在るが到達されない = appearance-only)。⇒ **B3b の DoD に明示行として入れる:「guard が live restore path で実際に実行されることを run で示す」。仮定にしない。**
(LOW carry) `require_canonical=False` が production caller から到達可能にならないこと (現在は到達不能、:756 既定 True / :781 synthetic fixture 限定)。

### (d) DoD 裁定 (2026-07-14 05:3x、%12) — 両 DoD とも走行前に訂正が入った

**(d2) [%11] = 3 腕へ設計変更、APPROVED。** ⛔**%12 の over-claim を撤回**: 「07-12 の c1pin run は Newton/MuJoCo の +1 index-space trap で別 body に weld した」は **code と一致しない** (%11 実読: c1pin は `norm(mjd.xpos[eq_obj1id[i]] - _seat_world)` = **world 位置一致**で解決、両者とも MuJoCo body id 空間 ⇒ index-space cross なし)。⭐**%12 は「342 step 死亡」という salient な症状に、直前に見た trap (B3a leg6) を当てはめた = 症状から機構を逆算した** — 本 arc で焼かれ続けた誤りの型そのもの (%9 の 2 度の over-claim を注意した直後に %12 が犯した)。
⭐⭐**%11 の論理が本 leg 最大の発見**: pin が一度も発火しなかったなら run は pin-less と同挙動 (~499 step) のはず。**しかし 342 step で死んだ ⇒ 何かが確実に変わっている。fail-silent latch *だけ* では説明できない。** ⇒ **3 腕**: A=baseline / B=**事前確保のみ (発火ゼロ)** / C=事前確保+発火。**合格条件 = A ≡ B (厳密一致)。** ⇒ **A ≠ B なら「07-12 の 342 step は pin が発火しなくても説明できる ⇒ あの run は pin の反証ですらなく *交絡の実証*」= それ自体が上程項目** (機構候補: `_wire_s6_grasp_solref` が disabled eq も stiffen / nefc・njmax・constraint 順序)。

**(d1) [%9] = APPROVE-WITH-3-CORRECTIONS。** %12 実測 (task_config 実値、env_isaaclab7):
- ⭐⭐**5 groove center の min-width SLAB = 0.000mm (n=ẑ、座面は厳密 coplanar Z=0.809)** ⇒ 平面鎖の必要条件は **k=2,3,4,5 すべてで充足** ⇒ ⛔ **平面論では infeasibility を証明できない。** (%9 の 16.7mm は best-fit **LINE** 残差 = 「bend 平面が垂直」前提の量で、free root の下では前提が成立しない ⇒ **moot**。なお %12 の SVD 再計算では k=3 の垂直残差は max 33.33 / rms 23.57 / mean 22.22mm で 16.7 と一致せず — 定義照会中。)
- ⭐**CORRECTION-1 (instrument-cannot-measure-its-target)**: %9 の P0 (FK 較正) が **hinge 39 本のみ**をランダム化 ⇒ **root 姿勢 (quaternion) 経路を一度も走らせない。しかし M2 の発見は丸ごと root roll に乗っている** ⇒ **quat 規約バグ (Newton wxyz vs MuJoCo xyzw) が P0 を素通りし infeasible を *計器の故障で* 出す** ⇒ **P0 は root pose (位置+quat) もランダム化必須。**
- ⭐**CORRECTION-2 (governance)**: **「optimizer が infeasible」≠「IMPOSSIBLE」**。46 次元で multi-start 200 の失敗は証明でない。⇒ **infeasible 単独では T-ROOT 上程 (substrate 変更!) の根拠にしない。** 必要 = (1) 手組み witness も失敗 + (2) 障害を明示する厳密証明書 (joint-limit 算術 / slab / lift budget)。無ければ verdict は **NOT FOUND** であって IMPOSSIBLE でない。
- **CORRECTION-3 (bar)**: seated bar は **6mm ではない** — code の `T_GROOVE = 0.003` (task_config.py:368) + `cable_in_groove` + `GROOVE_BODIES_MIN=2` (:384) が SSOT。6mm は溝の内半径。**%12 の 6mm 指定は緩すぎた。**
- **拘束している真の量 (%12 実測、検定対象として %9 へ)**: hop 弦長 **90.14mm** ⇒ **1 hop に ≥7 seg** (⭐**p5 の副次 defect 決着: banked §2.1 の 5 seg = 誤り、7 seg が正**) / 各中間 clip の turn = **67.38°** ⇒ ~10°/joint ⇒ ⭐**`jnt_range` が決定的** / **2 seated 時の平面 pivot = 無制限** (2 点は共線、C3 端は C1-C2 線から **83.21mm** ⇒ 持上げ = 83.2·sinψ、ψ 無拘束) ⇒ ⭐**C3 を上から落とす運動は利用可能 — 壁は clip 3 に無い** / **3 seated 時の平面 tilt = 13.89° に pin** ⇒ **C4 位置の持上げ余地は 8.00mm のみ** (bar 3mm なら **4.0mm**) ⇒ ⭐⭐**壁があるとすれば clip 4。機構 = 「seated 集合が非共線になった瞬間に平面が pin され、面外の持上げ余地が崩壊する」。** ⚠ これは %12 の *導出* であって verdict でない — **ground truth = producer の C1→C2 記録から cable の Z=0.809 面からの最大逸脱 (= 実際の必要持上げ量) を実測して比較。**

### ⛔⛔ 2026-07-14 05:4x — **壁は 3 説とも壊れた / 「c1pin REFUTED」が空虚である経路は 4 本**

#### (A) 幾何の「壁」= **全説 撤回。差し替えの結論も置かない。**

| 提案された壁 | 提案者 | 結末 |
|---|---|---|
| 「3 clip = best-fit 16.7mm ⇒ 配位空間の外」 | %12 → %9 | ⛔ **破棄** — best-fit **LINE** は「bend 平面が垂直」前提。root は **FREE joint** ゆえ強制されない |
| 「壁は clip 4 (3 seated で平面が pin → 面外持上げ余地 8mm[bar6] / 4mm[bar3] / **2.67mm[bar2]** へ崩壊)」 | %12 | ⛔ **破棄** — **逐次順序 C1→C2→C3→C4→C5 を暗黙前提**にしていた |
| 「置ける が 配線できない (水平平面 ⇒ 垂直曲げ厳密ゼロ)」 | %9 | ⛔ **破棄** — **共線 3 点は平面を pin しない** |

⭐**破壊した反例 = 奇数 clip 先行 (%12、env_isaaclab7 実測、Z0=0.829 / bar=2mm)**: **C1・C3・C5 は全て x=0.35 = 共線** ⇒ 3 本座らせても **平面は x=0.35 の直線まわりに自由 pivot** ⇒ τ=**21.80°** 傾ければ **x=0.40 の材料が 20mm 持ち上がる**、その間 **奇数 3 本は pivot 軸上ゆえ溝を出ない** (軸から 2mm ずれた seat の z 変位 = **0.74mm** < bar 2mm) ⇒ **τ→0 で C2 と C4 に *同時* 着座、奇数 3 本は一度も動かない**。予算充足: zigzag **360.6mm** / cable 600mm (25 seg / 40)、turn **67.38°** ≈ 11.2°/joint に対し **%9 の M1 実測 `hinge_limited = 0` (range ±5.7e11 = 無制限)**。
⭐**%9 の M1 (built model 実走)**: cable = **1 FREE + 39 HINGE**、**39 軸すべてが任意 q で平行** (25 試行、worst_nonparallel = 0.0)、共通軸 = world (1,0,0) ⇒ **鎖は PLANAR で確定**。⇒ ⛔**joint-limit による厳密証明書は取れない。**
⇒ ⭐⭐ **「幾何的に不能」も「幾何的に可能」も現時点で言えない。どちら向きにも witness が無い。** ⛔ **壁を別の壁で置き換えない** (今夜 3 回やった誤りの 4 回目になる)。**p5 の HARD STOP (「5-clip は配位空間の外」) も撤回対象。**
⇒ **(d1) の task を書き換え**: 「不能を証明する」→ ⭐**「witness を作る」** (W-1 静的手組み + FK 検算 [bar 2/3/6mm、groove center は **built model** から: `route_env_config.py:144` **ROUTE_GROOVE_Z=0.829**、task_config の 0.809 ではない] / W-2 運動の各 step で既着座が bar 内 / ⭐**W-3 = 本当の open question**)。
⭐⭐**W-3 (物理、誰も 30 分前には聞いていなかった問い)**: 鎖に **twist DOF が無い** ⇒ **bend 平面の向き = root 姿勢 = 鎖全体で 1 個の剛体 DOF**。build 時 hinge 軸 = world (1,0,0) / cable は Y 方向 ⇒ **素の bend 平面は垂直 (YZ)**。奇数先行 plan は **鎖を ~68° roll する**ことを要求 ⇒ **重力・テーブル接触・gripper の下でその roll は実現するか?** (roll が位置的に無コストなのは **鎖が真っ直ぐな時だけ** / policy は root 姿勢を直接制御しない / 水平 bend 平面の鎖は **Z 方向に剛体 = 垂れない**)。⇒ **運動学ではなく物理。これが (d1) の本命。**

#### (B) ⭐⭐ 「c1pin REFUTED」が空虚である **独立な経路 = 4 本**

| # | 経路 | 発見者 | 状態 |
|---|---|---|---|
| 1 | **pin が一度も発火しなかった** — fail-silent は **2 本** (latch が None check の前で焼かれる + **5mm 位置一致 gate が print のみ・raise 無し** ⇒ index が正しくても `mjd.xpos` が stale なら silent skip) | %9 + **%10** | **code 上で確定** |
| 2 | **事前確保だけで挙動が変わった** — pin が発火せずとも 342 step を説明可 (`_wire_s6_grasp_solref` が disabled eq も stiffen / nefc・njmax・constraint 順序) | **p3** | (d2) 腕 B が決める |
| 3 | ⭐**342 vs 499 が baseline 自身の run-to-run ばらつきの中** = **信号が最初から存在しなかった** | **%12** | (d2) 腕 A/A′ が決める (**A ≢ A′ なら A を N≥5 回走らせ分布を取る**) |
| 4 | ⭐⭐**artifact が「どれなのか」に *原理的に* 答えられない** — result.json に PERCLIP_PIN / eq_active / seat body / position-match が **1 field も無く**、**termination_reason すら無く、stdout も未保存** (⇔ producer 側 log には witness `[PERCLIP_PIN] ACTIVATED eq#27 ... position-match 0.000mm ... eq_active=1` が在る) | **%10** | ⭐**GPU 不要で *既に確定*** |

⇒ ⭐⭐⭐ **#4 が確定している以上、1/2/3 のどれであれ「REFUTED」は成立していない。正確な現状は「反証された」ではなく「試されたか *不明*」。** (d2) は **「どれだったか」を決める**のであって「REFUTED が正しかったか」を決めるのではない。
⇒ ⚠ **この連鎖の下流 = FORK-1 の終端帰属 → 「閉ループ RL だけが直せる」→ trainer を数週間 build する、の *起点* が witness 無き artifact。**

#### (C) (d2) DoD v2 (p3、`D2_PIN_REMEASURE_DOD_COORD_20260714.md`、commit cf025fd872) — %12 verify = PASS-WITH-2-CRIT

- ⛔⛔**CRIT-1 (Rs 専権 gate の欠落、3 名とも見落とし)**: **視覚レグが 1 行も無い (grep 0 件)**。⭐**測定対象そのものが kinematic trick (weld = 物理を上書きする機構)** ⇒ **「数値 PASS / 動画 wrong」に最も転びやすい配置** (「seg27 が 4.16mm に留まる」は cable が clip に *めり込んだまま* weld が押さえていても成立する / 「route 完走」は weld が物理的にありえない配置を保持していても成立する)。かつ **route 完走 ⇒ trainer を止める**決定 ⇒ **数値だけで下してはならない**。⇒ **追加必須**: P4 で動画 (route 全域 + **C1 接触点 zoom**) / **pC の blind 独立判定** / ⭐**FORK-1 を falsify する verdict は Rs の動画 human-GT を経てからでないと act しない** (autonomy grant の唯一の例外) / `~/Downloads` へ納品 / 見る 3 点 = **めり込み / 指間 slip / 不自然な硬直 (weld が divergence を「直した」のか「隠した」のか)**。
- ⛔**CRIT-2**: **A ≢ A′ の分岐が無い** ⇒ 上記 (B)#3 を追加。
- **MED-1**: 「seated で完走」は code 自身の述語 (`cable_in_groove` / `GROOVE_BODIES_MIN=2` :384 / `T_GROOVE=0.003` :368) を使う。発明しない。
- **MED-2**: P1 の bar「4.16mm 近傍」は曖昧かつ **危険** — **4.16mm は *記録* (producer build) の値で、env は別 build (それが FORK-1 の前提)** ⇒ **一致する必然性は無い** ⇒ bar を **「有界かつ非発散」** に (52.87mm への単調離脱との差は十分大きく判別力は保たれる)。「4.16 と一致しないから INSTRUMENT DEAD」と誤読される bar にしない。
- ✅ 承認: 3 腕 (A/B/C) / 走行順序 A′→A→B→[A≡B]→C→P1→P4→P5 / witness 永続化 + stdout 保存 / seat 非移植 (P0′) / termination_reason / flag-OFF byte-preserve / 新規 dir / **測定 ≠ 採択** (pin 常設は Rs 専権)。

### ✅ 2026-07-14 05:5x — **(d1) = CLOSE。壁は 4 説とも死んだ。層 3 の警報 = 解除。**

⭐⭐ **%9 が golden 記録 (Rs 宣言の MOTION STANDARD = 現に動いている route) を実測 → 私の W-3 (物理) が反証された。**
- `route_demo_raw.npz` の `cable_xyz` (7707,40,3) を毎フレーム SVD 平面 fit: **cable の平面性 s3/s1 = median 2.5e-07 / max 1.4e-06** ⇒ **live route 上でも鎖は 100 万分の 1 の精度で平面** (M1 の構造的事実が実データで確認)。
- ⭐⭐ **bend 平面の法線 vs 素の bend 軸 (world X): median 17.6° / p95 78.4° / MAX 89.6°** ⇒ ⭐⭐⭐ **現に動いている route は bend 平面を最大 89.6° roll させている。**
- ⚠ **%12 の数値訂正 (%10 捕捉)**: 必要な roll は **68° ではなく 90°** (私は **67.38° = zigzag の *turn* 角** と roll を取り違えた)。⇒ **にもかかわらず答えは変わらない — golden 実測 MAX 89.6° ≈ 90°。**

| # | 提案された壁 | 提案者 | 死因 (⭐ 4 つとも同型) |
|---|---|---|---|
| 1 | 3 clip = best-fit 16.7mm ⇒ 配位空間の外 | %12→%9 | **bend 平面を「垂直」と黙って固定** (root は FREE joint) |
| 2 | 壁は clip 4 (持上げ余地 2.67mm) | **%12** | **seating 順序を「逐次」と黙って固定** (奇数先行は許される) |
| 3 | 置ける が 配線できない | %9 | **seated 集合を「非共線」と黙って固定** (C1,C3,C5 は共線) |
| 4 | ~90° roll は物理的に無理では | **%12 (W-3)** | **roll を「未検証」と黙って仮定** (**golden が既に 89.6° roll している**) |

⭐⭐ **%9 の META (bank 済 `feedback-a-wall-is-a-forgotten-degree-of-freedom-2026-07-14`)**: **「壁とは、自由度を 1 つ忘れたときに現れるもの」。**
⭐ **p5 も HARD STOP を撤回・自己診断**: 「**私自身の tool 出力に反証が印字されていた** — 『C1,C3,C5: cross=+0.00000 -> COLLINEAR』。出力しておきながら『route は偶数 clip も要る』で読み飛ばした = **自分で生成した反証の握り潰し**」(prohibited.md 確証バイアス、p5 自認)。
- ✅ **%9 の調停 (XY rank)**: seated {C1,C2,C3} = rank 2 (非共線) ⇒ 平面 **PINNED** ⇒ **%10 の予算式 (≤5.4mm) は正しい** / seated {C1,C3,C5} = rank 1 (共線) ⇒ 平面 **FREE** ⇒ 上限なし。⇒ **%10 と %12 は矛盾していなかった — 効いているのは seating の *順序*。**
- ✅ **RS71 §4 の読み方 (%9 が正、%12 受諾)**: 「horizontal routing curvature を動的に表現しない」は **fidelity の言明** (sim2real robustness を validate できない) であって **不能の言明ではない**。⇒ **substrate 変更 (2nd bend DOF 追加) の提案は撤回。新規上程 不要** (境界は RS71 が既に bank・Rs 受諾済)。
- ✅ **副次決着**: hop 弦長 **90.14mm** ⇒ **1 hop に ≥7 seg** (p5 の banked step-table §2.1「5 seg」は誤り。訂正は p5 領域 ⇒ p5 が Rs へ上程)。**h_lip 実測 = 46.4mm** / **seated 平面の実測 Z = 829.0mm** (%10 の CRIT-1 を %9 が独立確認)。

⛔ **ただし「壁が無い」≠「達成できる」(%12 の止め、%9 全面受諾)**: ⭐**5-clip 着座の witness (実際に構成して FK で検算した配置) は *まだ誰も作っていない*。** 4 つの壁は全て「証拠なしに断定した」から死んだ ⇒ **逆向きの断定も同じ規律に服する。**
⇒ ⚓ **正確な状態 = 「提案された壁は 4 つとも壊れた。達成可能性の witness も存在しない。⇒『不能』も『可能』も未確立。」**
⇒ **W-1 (手組み witness) = blocker から *carry* へ降格** (「5-clip route は達成可能」と誰かが主張する *前に* 必ず作る。whole-route DoD 行)。**現 gate は (d2) ただ 1 つ。**

### ⭐⭐ 2026-07-14 05:5x — (d2): **07-12 の動画が現存。GPU ゼロで核心に答え得る (%10 発見)**

`~/Downloads` fresh ls (%12 実測): **`comp5_c2seat_fullfire_c1pin_ctx.mp4`** (全景、07-12 02:20) / `comp5_c2seat_fullfire_c1pin_c2zoom.mp4` / `comp5_c1pin_GRIPDROP_bright.mp4` (02:25) + frames dir に c2zoom PNG **228 枚**。⚠ 07-12 の pC 判定 PNG も 3 枚残存 (`pC_c1pin_PHASE3_DROP_grippers-tilt_one-lifts-away_cable-FREE-END_t9.5.png` 等)。
⇒ ⭐ **「07-12 の run で pin は cable を C1 に保持していたか」は *見れば分かる* 可能性がある** ⇒ **pC に blind 判定を dispatch 済** (設問 1 つ = 「C1 に保持され続けているか / 離れていくか」、数値・仮説・期待・過去判定は渡さない。判定不能なら「不能」と返せと明示)。⚠ **「保持されている」と「*物理的に妥当に* 保持されている」は別** — weld は物理を上書きする ⇒ めり込み / 不自然な硬直も報告させる。
⇒ ⭐⭐⭐ **verdict は Rs の動画 human-GT が最終** (autonomy grant の唯一の例外)。動画は既に `~/Downloads` に在る。

### (d2) bar の訂正 (%10 C-1、%12 の bar が誤り)

⛔ **%12 が置いた「A ≡ B (厳密一致)」は誤り** — **A と B は model が違う (neq 6 vs 46)** ⇒ solver 内部配列・reduction 順序が変わる ⇒ **物理が同一でも bitwise は割れ得る** ⇒ **「効果ゼロ」でも FAIL する bar = 偽の escalation。**
⇒ ⭐ **正しい構成 (%10 C-1 + %12 CRIT-2 の合成、%9 も支持)**: **A vs A′ (同一 arm 2 回) が *ノイズ床* を定義し、A vs B をその床に対する *相対* で判定する** — |A−B| ≈ |A−A′| ⇒ pre-alloc 効果なし / |A−B| ≫ |A−A′| ⇒ **07-12 は交絡の実証**。**boolean を捨てて「ノイズ床に対する相対」へ。**
⚠ ⭐ **%10 の prior**: env 経路の決定性には強い証拠 (B1/B2/B3a の leg4 が `comp5_c2seat_fullfire.py` 再走で banked npz と全 array EXACT、日と code 変更を跨いで) ⇒ **A ≡ A′ が期待値** ⇒ ⛔ **A ≢ A′ が出たら (d2) を超える発見** (B1/B2/B3a の byte-anchor leg 群の前提が崩れる) ⇒ **A′ verdict 表に「A ≢ A′ ⇒ (d2) を止めて byte-anchor 系 leg の再審へ escalate」を入れる。**
- **%10 C-2**: P1 の bar に **識別力の対** (同 leg で腕 A の同 metric が 52.87mm へ離脱することを示す = 追加コストゼロ)。
- **%10 C-3 ⊥ %12 MED-2 (両方必要)**: **値の一致は不要** (4.16mm は producer build の値、env は別 build = FORK-1 の前提) ⇒ bar = **「有界かつ非発散 (≤10mm・単調増加でない)」** / **定義の一致は必須** (どの seg / どの clip 中心 / 3D か水平か / groove Z の読み元 = route 0.829)。

---

## ✅ RESOLUTION of BLOCKED_FOR_USER #2 (2026-07-14 19:27、%12) — **Rs 動画 GT により前提が偽と判明。警報を解除する。**

**Rs 逐語 (2026-07-14、C1 断面動画 `BLIND_DO_NOT_JUDGE__p1b_c1_xsec_3a717010.mp4` = cell `2037_x-20_y-15_Fon` を直接見て):**
> 「これは**ケーブルが C1 の溝に入っているし C1 の底にもついているから見た目上は ok**。**C2 へのケーブル誘導、押し込みもできている**。ここにもどてくれ」

⇒ ⛔ **下記 BLOCKED_FOR_USER #2 の中核前提「Rs が cell 2037 を目視で却下した ⇒ 全数値 pass なのに人間 FAIL ⇒ 成功条件は *測れない*」は【偽】。** Rs の判定は **同一 cell で OK**。**numeric と human は一致していた。**
⇒ ✅ **成功条件は「測れない」のではなく「式が緩い」**。残る欠陥は **source だけで立つ 3 件**: (1) `c1_retained` が X 不参照 (`newton_route_env.py:1491-1495`) (2) offline `strict_v2` に lateral 無し (`p9_recount_strict_v2.py:39-44`) (3) G3 bar 3mm < 量子化床 7.32mm。⇒ **危険は前向き (RL exploit) であり、台本 route の遡及的無効化は起きない。**
⇒ 🔒 **裁定 = `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` §20-Z (supersedes §20.1)** / LEDGER 行 = `C1 着座 + C2 誘導/押込 = Rs 動画 GT`。
⇒ ⭐ **次作業 = Rs 指定 (2026-07-14 17:18 逐語)**:「**ピンが打たれる前に『本当に溝に居るか』を確かめる」これはあたりまえだ**」= **seat-trigger** (canonical 工程表 `CANONICAL_MOTION_TABLE_V1.md:128` STEP 9 = 側方 seated 確認後に C1 クランプ / 現行実装 = frame counter 発火)。
⚠ **BLOCKED_FOR_USER #1 (pin の恒久 env 配線 = INVARIANT #5 の scope 拡張) は【依然 OPEN】** — Rs 未裁定。本 RESOLUTION は #2 のみを解除する。
⚠ **数値単独 PASS 禁止 (動画 human-GT が最終) は不変** — Rs standing directive であり、本件から導かれた規則ではない。

---

## ⛔⛔⛔ BLOCKED_FOR_USER #2 (2026-07-14 07:2x、実 %12 起票) — ⛔**上記 RESOLUTION により SUPERSEDED (前提が偽)。以下は歴史。** — **成功条件が測れない。campaign を回せば壊れた計器の上で GPU を焼く**

⚠ **本件は ghost が「Rs へ上程します」と書いたまま *誰も実行していなかった* もの。実 %12 が起票する。** (ghost 事故 = memory `reference-claude-pane-backgrounded-session-spawns-strays-2026-07-14`)

**BLOCKED_FOR_USER: RL trainer の成功条件 (`G6 SUCCESS = strict_v2 = c1_retained_final AND c2_seated_honest`) は、3 重に壊れている。設計変更 = 直交 DESIGN-GATE (L3) + spec = Rs 専権ゆえ、%12 は fix を打てない。B3b-B7 は STOP 継続。**

### Context (全て on-disk 実測、%12 独立検証済 — 詳細 = spec §20、commit `216e8c2985`)

| # | 病理 | 根拠 |
|---|---|---|
| **(a)** | ⛔ **FAIL できない述語** — `c1_retained` (`newton_route_env.py:1491-1495`) = `z_c1 < 0.840 and flank < 0.840` = **天井チェックのみ、X 不参照** (`_c1_retention_m:1270-1286`)。凍結 recount 81 cell で **`c1_ok` = 81/81 = no-op**、**`strict_v2`(58) == `c2_seated_honest`(58) 厳密一致** ⇒ **C1 の連言は *タダ*。** | %12 code 実読 + p1 実測 |
| **(b)** | ⛔ **PASS できない述語** — 溝は **Y 押し出し** (`create_clip.py:68`) ⇒ **Y = 自由軸**。だが G3 (`:1550`) は `_seat_metrics` の **XY ノルム**で採点 ⇒ **自由軸 dy を着座誤差として課金**。**node 間隔 14.64mm ⇒ \|dy\| 床 7.32mm > bar 3.0mm** ⇒ ⭐ **bar は分解能の 2.4 倍細かい = 抽選** ⇒ **G3 は 24/81 でしか発火せず、ORDERED latch が切れ G6(+200) が 70% の cell で到達不能。物理は 81/81 で着座している。** | %12 が正典 golden (`5f1c3f92…`) から再導出 + p1/p6 独立 CONFIRM |
| **(c)** | ⛔⭐ **そもそも「溝に *捕捉* されたか」を測れる numeric 計器が *存在しない*** — **07-12 に proven + banked**: `ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md:108`「lateral groove-capture: **NO numeric coverage** (contact ≠ capture, **proven**); **Rs-video is the only ground-truth**」。**誰も読まず、3 名が計器を作り直しては positive control で殺した** (p1 の \|dx\| 計器は **Rs が目視で却下した cell 2037 を PASS させた**)。 | p1 発見 + p5 source + p6 negative control |

⭐⭐ **(a) と (b) は互いを隠していた**: **FAIL できない述語は警報を鳴らさず、PASS できない述語は「課題が難しい」に見える。どちらも沈黙する。**
⭐⭐⭐ **動画による直接反証 (pC blind、ghost 非依存)** — ⚠ **pC 自己撤回により訂正済 (07:49)**:
- ❌ **撤回**: 「no-pin run の全 frame で C1 溝は空 = cable は一度も入っていない」 — **pC が npz を自ら実読して反証。cable は step 253-259 / 273 に C1 溝域を *通過している* (seg#27、lat 1.08-1.85mm、z 827.5-827.9mm)。** ⭐ **pC の誤りの機構: 分母 (全 167 frame) は直したが *解像度* を壊した** (contact sheet の 1 コマが 152×120px で、8px の線を見落とした) ⇒ ⭐ **掃引は「分母」と「解像度」の *両方* が十分でなければ不在主張は成立しない。**
- ✅ **核心は無傷 (むしろ情報量が増える)**: **cable は溝を *訪れた* が *留まらなかった*。** 述語の**評価点 (step 498) で cable は C1 から横 56.5mm / z=824.0mm** (= 台座 820 + cable 半径 4 = **台座に寝ている**。着座なら 827)。⇔ **`c1_retention: pass = TRUE`。** ⇒ ⭐ **述語は *自分の評価点で* 証明可能に誤っている。**
- ⚠ **「捕捉されたか」は video でも numeric でも判定不能** (近接 ≠ 捕捉、gripper が同時に在る) ⇒ **Rs 動画 GT が唯一の GT、は不変 (= L1-(c))。**

⭐⭐⭐ **そして %10 が banked npz から実測して像を閉じた (`comp5_c2seat_fullfire_cablediag.npz` = no-pin baseline、env_cxyz [499,40,3])** — ⭐**軌道の主張に依存せず、評価点そのもので述語が偽:**

| t | Y 最近傍 node | lateral | \|dx\| | z |
|---|---|---|---|---|
| 0 | #30 | **50.00mm** (= 設計定数 GRASP_X↔CLIP1_X) | 50.00 | 803.8mm (= table) |
| **255** | **#27** | ⭐ **1.08mm** | 0.89 | ⭐ **827.6mm** (溝 829 の近傍 = **通過している**) |
| **273** | #27 | ⭐ **1.63mm** | 1.52 | ⭐ **827.9mm** |
| ⛔ **498 (述語の評価点)** | #35 | ⛔ **56.51mm** | 56.06 | ⛔ **824.0mm** |

⇒ ⭐⭐ **評価点で cable は横 56.5mm 離れ、z=824.0mm。それでも `c1_retention = pass: TRUE`。** ⇒ **述語は *自分の評価点で* 証明可能に誤っている。1 コマンドで再現できる。**

⭐⭐⭐ **新規 (%10、L1-(c) の *機構* が経験的に実証された)**: **824.0mm ≈ spacer 上面 (820) + cable 半径 (4)** ⇒ ⭐ **cable は *spacer riser の上に寝ている* (溝 829 ではない)。**
⇒ ⛔ **producer の `cable_c1_final_dist_mm` は `_clip_geoms` (= C1 XY±30mm の worldbody BOX **全部**、**spacer riser を含む**。C2 のみ `:5559-5566` で分離済、**C1 は未分離**) への最小距離** ⇒ ⭐⭐⭐ **spacer の上に寝た cable は、その計器で「接触/貫入 = 着座」と読まれる。横に 56mm 離れているのに。**
⇒ ⭐⭐ **∴ 「contact ≠ capture (proven)」(07-12 banked) の *機構* が、この run で経験的に実証された。像が 1 つに収束する:**
> ⭐ **cable は溝を訪れ、捕捉されず、56mm 離れて *spacer の上* に寝た。そして全ての numeric が PASS と言う。**
⇒ **上程の核はこれ。**「溝が空だった」(軌道の主張、pC 撤回済) ではなく **「評価点で 56.5mm 離れ spacer の上に寝ているのに全 numeric が PASS」**。

### ⛔ Stake (これが上程の理由)

**campaign を回していれば、agent は demo 分布の 70% で成功信号を一度も受け取れず、「RL が効かない / 課題が難しすぎる」と *誤診* されるところだった。数週間の GPU が、壊れた計器の上で焼かれる。**

### Options (全て Rs 専権 — %12 は推奨を付すが決定しない)

- **(A)** ⭐ **計器を直してから B3b-B7 を再開** — fix = 折れ線を y=CLIP_Y で補間し **3 連言** (\|dx\| ≤ 3mm ∧ \|z − ROUTE_GROOVE_Z\| ≤ 3mm ∧ **wall-only 接触 ≤ 0.5mm**) で採点 / **`obs[49]` も同じ差替え** (policy の *観測* も ±7.5mm 汚染、%10 catch) / **bar は緩めない (3mm 据置)** = conservatism 方向 OK。⚠ **env 単独では打てない** — env docstring (`:1271-1280`) が「the EXACT frozen def」と自認、**DoD-9a が offline recount との parity を検証** ⇒ **env + offline(strict_v2) + PREREG の 3 点同時改訂 = spec 層。**
- **(B)** **p5 に両壁 form-closure metric の設計を授権** — ⭐**受入条件が確定した: 「Rs 却下 cell `2037` を FAIL し、真の着座 cell を PASS する」(両方向 control)。** ⚠ **`c1_wall_dist_spacer_excluded_mm` は未 emit ⇒ producer 再走が要る。**
- **(C)** **現状のまま campaign** — ⛔ **%12 は反対**。70% で成功信号ゼロ ⇒ 情報を生まず、誤診を生む。

**%12 の推奨: (A) + (B) を並行。(C) は取らない。** ただし **決定は Rs。**

### ⛔⛔⛔ 併せて未決 — **そして今夜の最初の発見と最後の発見は *同一* だった (p1、07:2x)**

**pin (INVARIANT #5 の唯一の認可例外) を RL env へ *恒久* 配線してよいか** — 依然 Rs 未裁定。**(d2) の最小配線は *測定* の授権であって *採択* ではない。**

⛔⛔ **RETRACTED (2026-07-14 08:5x、実 %12 = session `25eca88d`、on-disk 再検証)。以下の「論拠が確定した」は *両前提とも立っていない*。歴史記述として残置し、訂正を直下に置く。**

~~⭐⭐⭐ 論拠が確定した (p1 が source で verify):~~
~~1. clip は衝突ジオメトリを持たない — `CLIP_COLLISION` は既定 OFF ⇒ clip は物理的に何も保持できない。~~
~~2. cable の rest 形状は直線 (`dof_springref: 0.0`) ⇒ 湾曲は外部拘束によってのみ維持される。~~
~~⇒ ∴ routed cable を clip に留められる機構は、認可された pin だけ。∴ 5-clip routing は全 clip に pin を要求する。~~

### ✅ 訂正 (実 %12、両前提を自分で grep して確認)

**前提 1「clip は衝突ジオメトリを持たない」= ⛔ VERIFIED FALSE。**
- **RL env は `CLIP_COLLISION` を読んでいない。** clip の衝突は **ハードコード**: C1 の 5 parts (`newton_skill_env_base.py:1898`) / C2 の 5 parts (`:1915`) / C2 spacer (`:1927`) が全て `scene.shape_flags[idx] = 0x6  # COLLIDE | BROADPHASE` ⇒ **RL env の clip は常に衝突する。**
- **producer** (`test_newton_clip_routing.py:1168`) は env-gate で既定 `"0"` = OFF。**だが実行系は全て `CLIP_COLLISION=1` を立てている** (`w0e_81rerun_runner.sh:21` / `w0e_probe_band.sh:15` / `b2_cpC_m8pair.sh:10` / `w0e_liftraise_smoke.sh:14` / `test_routeexec_byte_repro.py:77`) ⇒ **実行時は衝突する。**
- ⇒ ⭐ **コードの *既定値* を *実行時の値* と取り違えていた。** 上程文 §5 (`RS_ESCALATION_GATE_REVISION_RSTECHLEAD_20260714.md:131`) が既に撤回済。**本節だけが未更新で残っていた。**

**前提 2「cable の rest 形状は直線」= ⚠ producer では確認、RL env では未確立。**
- **producer** = code で確認 (`test_newton_clip_routing.py:1014` `"mujoco:dof_springref": 0.0`)。
- **RL env** = ⛔ **`springref` の代入が存在しない。唯一の出現は `newton_skill_env_base.py:1865` = *comment*。** cable は `add_rod` (`:1727`) 経由ゆえ rest 形状は Newton 既定に依存し、**env については誰も追っていない。**
- ⇒ ⭐ ⚓ **comment は narrative、制約は code に在る。** 本節はその comment を論拠として使っていた。

⇒ ⛔ **∴ 結論「湾曲を保持できる機構は pin だけ」「5-clip routing は全 clip に pin を要求する」は成立していない。撤回する。**

### ⛔ ただし逆向きの断定もしない (本 arc で 4 つの壁が「証拠なき断定」で死んだ)

- **実測は残る**: pin 無し env で C1 距離が **1.08 → 52.87mm** へ単調離脱 (本 file :67)。
- ⇒ ⭐ **正確な現状: clip は衝突する。それでも cable は C1 から離れる。⇒ 言えるのは「衝突だけでは保持に足りない」まで。「何が保持するのか」は未確立。**

### ⭐⭐ かつ — *より安い説明* が既に code に在り、一度も走っていない

- `newton_skill_env_base.py:1873-1876` = **`ROUTE_C1_STIFF_MATCH` (flag、既定 OFF)**。既定の env C1 clip = **ke 2500 / kd 100 / gap 0.001**、`=1` で producer 一致の **40000 / 400 / 0.002** になる。
- **%12 独立確認**: producer C1 (`test_newton_clip_routing.py:1179-1181`) = `MUJOCO_CONTACT_KE` / `MUJOCO_CONTACT_KD` / gap 0.002、実値 = **40000 / 400** (`task_config.py:168-169`)。env C2 も同値。⇒ ⭐ **env の C1 *だけ* が producer の 1/16 の接触剛性。**
- ⇒ **(d2) 腕 D は既に配線・commit 済** (`92a62f6a96`、flag-gated・既定 OFF・byte-preserve)。**走っていないだけ。**
- ⇒ ⛔⭐ **∴ pin 上程 (Rs 裁定 #2) は腕 D の結果に *条件付き* である。** 腕 D で横滑りが消えるなら、pin を要求する論拠は残らない。**⇒ 本上程は現状 Rs に出せる形になっていない。** (⚠ 腕 D の実行 = Rs の停止解除待ち。%12 は self-start しない。)

---

## ⭐⭐⭐ CAPSTONE — **これは metric bug ではなく governance gap。fix は metric でなく *ゲート* に打つ**

### (i) ⛔ 私 (%12) 自身の failure — **証明は 2 日前に、私が書いていた**

`harness/state/ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md` = **RS-TECH-LEAD p4 ⇄ VT-DESIGN p5 の joint decision doc (私が共著)**。`:104-110` 逐語:
> **「EVERY numeric metric (z-proxy + honest-3D-contact + temporal-continuous + C2-seat + regrasp) reads pass/retained, yet Rs-GT = OFF C1. ∴ no current numeric metric covers lateral groove-CAPTURE; the honest-looking ones false-positive on wall/adjacent contact. This is the systematic root of the DoD⑥ false verdict + the "correlated agreement" trap (pB reads these numbers / pC scoped / **p4 glance** all shared the capture-blind basis.)」**

⇒ ⭐⭐⭐ **私は 07-12 に、今夜の失敗を——「correlated agreement の罠」という名前まで付けて、自分を名指しして——書いていた。そして 07-14、その文書を読まずに、書いてあるとおりの穴に全員で落ちた。** (%10 も同じ own: 「anchor-set 接地で `harness/state/` を読んでいなかった」。)
⇒ ⚠ **接地範囲の拡張提案 (%10)**: anchor-set gate に **`harness/state/`** を追加。

### (ii) ⛔⛔ **唯一 *発火した* ゲートが、欠陥を *強制* していた (p5、source verified)**

`newton_route_env.py:1283-1289` 逐語: 「**DoD-9a validates this live-geometry verdict against the frozen two-key reference and any divergence is fixed here to the frozen def, *never by loosening tol***」「**the EXACT frozen def**」
⇒ ⭐ **C1-retention 述語は、frozen reference を厳密に鏡写しする *契約 (DoD-9a) に拘束されていた*。**
⇒ ⛔ **契約は「frozen def から逸脱するな」と *命じて* いた** ⇒ **書いた者は「設計している」と思っていない。「忠実に移植している」と思っており、契約がそれを *要求* していた。** ⇒ ⭐ **`/reward-design` は *発火しようがなかった*。**
⇒ ⭐⭐ **パリティ / 忠実性の契約は「正しく写したか」を検証するが、「写した *もの* が正しいか」は検証できない。しかも写しを *権威化* する。** ⇒ **ここでは契約は欠陥に *沈黙* していたのではない。欠陥を *命じて* いた。**

### (iii) ⇒ **ゲート改訂案 = 4 条 (Rs 上程項。⚠ skill workflow 変更 = L3、%12 は self-start しない)**

| # | 条 | 出自 |
|---|---|---|
| **1** | `/reward-design` に **Artifact 0 = banked-gap 照合** — 述語を作ろうとしている *量* について vault に「NO numeric coverage」「cannot measure」「X is the only ground truth」の banked annotation が無いか grep。**在れば numeric 述語は作れない ⇒ escalate。** | p1 |
| **2** | **Reachability Table は *demo 分布全体* で取る** (単一 nominal cell 禁止)。⭐**24/81 はそこでしか出ない。** ⚠ **ゲートには reachability レグが *既に在る* — 走らなかったか、1 cell で走った。** | p1 |
| **3** | ⭐ **強制ゲートは *コードの新規性* でなく *述語の役割* で発火する** — 「reward/成功条件の述語を **定義する / 採用する / 鏡写しする** のか?」→ YES なら発火。**reference を mirror することは免除にならない。** | p5 |
| **4** | ⭐⭐ **パリティ / 忠実性の契約は、妥当性ゲートを *discharge できない***。**忠実性ゲートは妥当性ゲートに *従属* する。** 順序を逆にすると **忠実に壊れたものを増やす。** | p5 |
| **5** | ⭐⭐⭐ **prior-art gate の *探索 root* に `harness/state/` (+ 他の banked 面) を入れる** — **実証済 (p3 が今、実際に走らせた)**: `scripts/check_thread_vault_prior_art.sh "groove capture" "lateral" "seat metric"` → **`findings=0 blockers=0` → PASS**。⛔ **しかし当該 banked finding は実在する** (`harness/state/ANCHOR_STEPTABLE_ALIGNMENT_p4p5_20260712.md:107-108`、plain grep で 30 秒)。**gate の探索 root = `thread-vault` / finding の在処 = `harness/state/`。** | **p3 (実測)** |
⇒ ⛔ **(3)(4) が無ければ、(1)(2) を足したゲートは *今回と同じく発火しない*。** (移植者はゲートを呼ばない — 自分が設計しているとは思っていないから。)

⭐⭐⭐ **そして p3 の実証が capstone を完成させた**: 我々は「**bank しただけでは実装は止まらない — 強制経路が無い**」と診断した。
⇒ ⛔⛔ **さらに悪い。強制経路は *存在し*、p3 はそれを *持って* おり、走らせたら **PASS を返した**。**
⇒ ⭐⭐⭐ **「gate が無い」のではなく「gate が、*見えない場所* を分母から外していた」。** ⇒ **pF の「分母を 06:34 で凍結」「書込で停止を主張」と *完全に同型* — 今度は *gate 自身* が踏んだ。**
⇒ ⭐ **本 arc の中心命題は、最後に gate に着地した**: **「不在主張の分母は、主張する述語と同じ空間から取れ」— これは人にも、guard にも、そして *ゲートにも* 適用される。**

### (iii-b) ⭐⭐⭐ **条 (4) の *機構* が特定された — two-key の「独立」は *実装* の独立でしかなかった (p1、自分の script を通っていた)**

`newton_route_env.py:1283-1289` は「the EXACT frozen def (recount `p9_recount_strict_v2.py:39-44`)」を名指す。⇒ **`p9_recount_strict_v2.py` = p1 (OPS-SUP) の script** (header 逐語「%9 OPS-SUP **independent** strict_v2 recount」/「Does **NOT** import/execute %12's `recount_strict_v2.py`」)。

| # | 段 |
|---|---|
| 1 | **PREREG spec v0.9 (`1f074169a1`)** が `c1_retained_final` を **天井チェック** (`z<840 ∧ flank<840`) として定義 — ⭐**欠陥の起源はここ** |
| 2 | **%12 が実装** (`recount_strict_v2.py`) |
| 3 | ⭐ **p1 が *独立に* 実装** (`p9_recount_strict_v2.py`) — **two-key check として** |
| 4 | **一致** ⇒ ⛔ **その一致が *妥当性の検証* として読まれた** |
| 5 | **env の成功述語が「the EXACT frozen def」として p1 の script を名指し、忠実に鏡写し** |
| 6 | **DoD-9a が parity を *契約で強制*** — 逐語「**never by loosening tol**」= ⛔ **直すための逸脱すら禁止** |
| 7 | ⇒ ⛔⛔ **欠陥は忠実性契約で *ロックイン* され、p1 の「独立検証」がそれを *authorise した 2 本の鍵の 1 本* になった** |

⭐⭐⭐ **∴ 教訓 (今夜最深)**: **two-key 独立検証が検査するのは *実装の忠実性* だけ。両方の鍵が *同じ定義* を encode していれば、一致は *必然* であり、何も証明しない。**
⇒ ⭐ **独立性は *実装* の水準ではなく *定義* の水準で要る。**
⇒ ⛔ **そしてその一致の上に建てた parity 契約は、欠陥を見逃すのではなく — *命じる*。**
⇒ ⭐⭐ **これは ⚓「相関した同意 (同じ代理を見る複数者の一致 ≠ 独立確認)」の *定義* 水準版。** 我々が今夜 (d1) で踏み、bank した、まさにその罠が、**数ヶ月前に stack の頂上で起き、いま RL の成功条件に契約でロックされている。**
⇒ ⚠ **∴ 「0.716 は two-key で検証済」は *妥当性の* 検証ではない。** 上程でそう扱わないこと。

### (iv) ⭐⭐⭐ **そして最後に、これは我々自身に返る (p1)**

**今夜 ~13 の教訓を bank した。「guard には positive control を」「DoD は間違った成果物を落とすように」「comment は narrative、制約は code に在る」…**
⇒ ⭐ **次にこの codebase を触る者に、それらを *実行させる* 強制経路は無い。**
⇒ ⛔⛔ **我々の memory も、07-12 の annotation と *全く同じ穴* を持っている。** ⇒ ⭐ **annotate された gap に強制経路が無いのと、bank された教訓に強制経路が無いのは、同じ failure class。**
⇒ ⭐⭐⭐ **∴ 今夜の教訓は memory ではなく *gate (skill)* に着地させねばならない。** (p5: 「だから私は今、教訓を memory に bank する手を *止めた*。memory は *記録* であって *強制* ではない。」)

### ⚠ 本 §RESOLUTION の commit provenance (records-must-match-fact)

**本節 (§RESOLUTION、%12 執筆) は `aa15596710`「B3a CLOSE: carry the "prove the guard RUNS on the live path" DoD to B3b」(%11 の commit) に含まれている** — 共有 tree 上で %12 の未 commit 編集を %11 の commit が巻き込んだため (commit message は本節に言及していない)。**内容は無傷** (%12 が `git show aa15596710` で実体照合)。⇒ **git log で「Rs 裁定 (d) 承認はいつ記録されたか」を追う者のために本行を置く。** ⭐**これは %12 が `575069abe5` で犯した sweep の鏡像** — 共有 tree での `git add` は explicit path + `git diff --cached --name-only` の事前確認が要る、を双方向で再確認 (memory `feedback-explicit-path-commit-git-diff-file-first-sweep-both-directions`)。history 改変はしない (共有 tree、%9/%12/%10 一致方針)。
