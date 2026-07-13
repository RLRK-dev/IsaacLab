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

- 現況 (2026-07-14 06:2x): B0 ✓ / B1 CLOSE ✓ / B2 CLOSE ✓ / ✅**B3a = CLOSE 確定 (2026-07-14 06:1x)** — 記録訂正 + guard-fire commit `0f13684709`、**3-leg 全 CONFIRM** (%12 on-disk 2 点照合 / %9 独立 run で unit 7/7 + guard identifiability 10 分岐 + Rs-LOCK run_route sha 4 点 byte-identical / %10 audit 残指摘ゼロ + positive control の非循環性を保全コピーで独立照合)。**push 済 (fork/rlrk/optE-s2-substrate-swap = `0f13684709`、remote==local 実測)**。⚠**build 本体の commit = `575069abe5`** (`a00a0a97f8` は conformance 追補のみ、source ゼロ — B3a-F1) / ⏳**B3b-B7 = STOP 継続 ((d) 結果待ち、下記 §RESOLUTION)**。
- ⚠⭐ **B3a-F1 (MED、commit provenance) — 正本は本 file 下部の %12 記載 (`e458bf9b9e`)。当方 (%11) も on-disk で独立確認済。** 事実 = **`a00a0a97f8` = conformance doc +20 行のみ (source ゼロ) / `575069abe5` = BLOCKED_FOR_USER + B3a source 730 行**。✅**成果物は無害** (legs 完了 03:38:13 < sweep 03:43:50、working tree == HEAD、DEFECT-1 fix は `route_executor.py:851` に在る ⇒ commit 済 code = 全 leg PASS した最終 code)。⛔**history rewrite はしない** (%9/%12 一致: 不要かつ有害)。
  **過失の切り分け (正確に)**: (a) **sweep 自体 = %12** (path 制限なし commit が当方の stage 済 index を巻き込んだ — %12 自認)。(b) ⚠**当方 (%11) の過失 = 別項**: commit 後に**その commit の中身を検証せずに「B3a 本体」と報告した** (`git show --stat` を打っていれば source ゼロに即気付けた)。⇒ **記録が事実と一致しない主張を、当方が発信した**。**教訓 = 自分の commit も「narrative でなく on-disk で検証してから主張する」** (`feedback-narrative-signal-not-established-fact-verify-on-disk` は他者の主張だけでなく**自分の commit にも適用される**)。

✅ **BLOCKED_FOR_USER = 部分解除 (Rs 裁定 2026-07-14 06:0x 逐語「はしらせて　push」)** — 下記 §RESOLUTION 参照。**(d1)+(d2) の実行 = 承認 / push = 承認 / B3b-B7 = (d) 結果まで STOP 継続 (pin の恒久 disposition は Rs 未裁定)**。以下は上程時点の記録 (歴史、⚠層 3 は §RESOLUTION で訂正済)。
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

## ✅ RESOLUTION (2026-07-14 06:2x、%12) — Rs 裁定「はしらせて　push」

**Rs 逐語 (2026-07-14 06:0x): 「はしらせて　push」** ⇒ 解釈 (%12): **(d1)+(d2) の実行を承認、かつ push を承認**。**pin の恒久 disposition (option A/B/C) は未裁定** — (d) はその判断材料を作るための測定である。

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
