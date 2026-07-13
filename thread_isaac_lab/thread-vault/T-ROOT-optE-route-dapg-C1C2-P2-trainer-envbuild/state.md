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
last_updated: 2026-07-13T01:28:00+09:00
spec_version: LTM-1 v1.2
session_history:
  - "2026-07-13 ~01:27 %12+%11 ⭐**B2 CLOSE** (%12 宣言 [msg 自称 01:30 = 先打ち、受信時実測 01:27]、3-leg joint: %12 PASS + C1 CONFIRM [source +649/-19 ≤800 独立実測] / %9 PASS + as-built 4 点 [release_step=762 の 900−762=138 ≈ tail 139 別鍵] / %10 audit PASS-w-FINDINGS [F-1 MED promised-unit ×3 / F-2 LOW 5]) + 追補 eb17e51a7d 全消化 (%12 roster-sweep 実読確認): (a) resume 意味論 unit (fire→chunk-end pin→resume→次 chunk 先頭駆動・再走なし) + div ±1-chunk 判別 (b) stub×flag ValueError unit (c) leg9 tail 抑制 3 述語 (A 抑制+event / B S5 −10 / C flag-OFF −10)。⭐C1 裁定 (banked): shadow bar discharge = prefix≡banked EXACT (0.000000mm/343 step) + banked 交差 t343 ∈ bar + 帰属 −1 step — live 交差 bar 化は『HOLD が正しく働くほど FAIL』の自己反駁。⭐governs: armed quiet max **10.407mm** = B3 restore-fidelity band (spec §6.2 L7 の再計測値)。B3 carries (%12 再掲): 6 点 (latch pre-set / bank_boundary wiring + assert / writesite 反転 / forbid 撤去 / k0 不変量) + capture = 抽出 twin run_route:1028 pin + cell-parameterized + 1-step post-restore 動力学 leg (body_q_prev/Dahl)。B3 から %12+%10 の『約束 unit roster 実在照合』二重 sweep が立つ。"
  - "2026-07-13 00:51 %11 (COORD, w2:p3) ⭐**B2 (HOLD + oracle API) build COMPLETE — commit a2f544662b、%12+%9 post-verify + %10 audit 待ち**。chain: [L-TRIAGE] L3 + DESIGN-GATE cite 充足 → conformance v1 (23:15) → 5体 (CC2 MED2 / CC3 HIGH2 [fixture 誤 file+writesite 漏れ] / CC4 **CRIT1 [較正 bar 10x index 誤読 — spec f343 = RL step、npz 実測で確定]** / CC5 HIGH1 [tail (iv) no-owner] / CC6 HIGH3 [評価点/tail IndexError/reset 漏れ]) → 全 ACCEPT fold v2 → %12 asks 4 点回答 (23:29 A1-A4: mask 機械導出/chunk 終端統一/rc.*/fail-loud) → %12 PASS (23:48) + 裁定 2 (ERRATUM-3 67d01d0c15 = tail (iii)(iv)→B2, (i)(ii)→B7 / fires bar = shadow 系列) → %9 PASS-w-NOTES (23:42、B2-F1 fencepost) → v2.2 → [RULE-CHECK] ALL PASS → build (+7276/-19、source 3 + test 2、新規 source file ゼロ) → legs 全 PASS: 表面適合 5 (⑨a′/DoD⑤⑩ [comparator throughput-key 修正 1 回]/DoD⑥ dict-id/cablediag EXACT vs 311f18cb9b/producer 5-cell vs ca33d1e1a0) + unit 3 suite (release_step=762 pin / mask {0→G1,11→G4} 導出 pin / 状態機械全系列 / neighbor 隔離) + leg7 reset 隔離 + **leg8 較正 cuda:0: g1=98、armed 域発火 0 (max 10.407mm = spec 予測 10.41 一致)、発火 t342 単発 ∈ bar、shadow prefix ≡ banked comp5 EXACT (0.000000mm/343 step)、banked 交差 t343、dones 0**。⭐ask C1 (%12 confirm 待ち): shadow bar の discharge 形 = prefix-EXACT + banked 交差 ∈ bar + 帰属 −1 step (正しい HOLD は shadow 交差を先取りして止めるため live 交差は反実仮想)。carry: B7 に 770/771 fencepost 照合 + claim ① + MAX_HOLD 再導出 (bounded-Δ 注入)。"
  - "2026-07-12 ~17:44 %12+%11 ⭐**B1 CLOSE** (%12 宣言 [msg 自称 17:50 = 先打ち stamp、p6 が実受信 ~17:44 と捕捉 → 訂正済]、3-leg joint: %12 PASS [独立 sha/grep 再実測] / %9 PASS-w-CORR [R-1 harness gating + R-4 CC6-unit + LOW 2] / %10 audit PASS-w-FINDINGS [F-1 = R-4 と独立収束 / F-2 evidence pin]) + 追補 commit 04a31e1e98 全消化: leg6 CC6-unit PASS (world_count=2 flag-OFF、実 step() per-world done branch 発火 dones=[True,False]、route_t≡episode 9 snapshot 恒等、w0 再始動/w1 継続 = :1027 mirror site 実測被覆) / run_legs.sh runner 行 exit-gating + stale-artifact 事前 rm / grep pin (comment 除外 fail-closed 明文化) + unit stdout 3 本 pin / R-2 gripper_qd sentinel + R-3 builder 0∉phases assert。carry to B2+: leg2 comparator = full-dict-diff − 既知変動 key 方式 (substring filter の漏れ 5 key を %10 が捕捉) / stdout は run 時から pin。次 = B2 (HOLD + oracle API) [L-TRIAGE] — hold 較正 両 leg cuda:0 (W-2) / recording contract v2 同梱 (spec §4.2 N9) / conformance = sub-item 列挙方式。"
  - "2026-07-12 17:15 %11 (COORD, w2:p3) ⭐**B1 (route_t 骨格) build COMPLETE — commit e1eac1deb8、%12+%9 post-verify + %10 audit 待ち**。chain: conformance v1 (15:3x) → 5体 [VERIFY] (CC2 PASS / CC3 REVISE / CC4 REVISE-CRIT / CC5 REVISE-HIGH / CC6 cond) → CC1 DECIDE=REVISE 全受容 → v2 c4c8212649 → %12 CONCUR (ERRATUM-2 ce6cdebf29 = B1 セル + §4-2 表面適合規則へ一般化) + %9 PASS-w-1-corr (F-1 W=non-prefix) → v2.1 51d4f31771 joint PASS → [RULE-CHECK] ALL PASS → build (+169/-15 source 4 files、新規 file ゼロ) → DoD 全 PASS: grep leg (5-site exact / consumer 0) + unit 3 本 (state_bank 新 world-slice 判別 test 込み / writesite 不変 / gate-ii) + ⭐env-side flag-OFF legs (⑨a′ 25/81+per-cell EXACT banked 一致 / DoD⑤⑩ diff ゼロ / DoD⑥ dict-identical / cablediag env 軌跡 npz 311f18cb9b と全 array EXACT) + producer 5-cell 5/5 vs ca33d1e1a0 (evidence = w1_b1_dod_legs/)。⭐5体の CRIT catch: v1 の経験 leg (producer byte-repro) は env 非実行で B1 diff に感度ゼロ = 偽検証構造 → env-side legs へ差替え (ERRATUM-2 の源)。B3 carries: fork-time latch pre-set (CC5 無所有者 crack) / bank_boundary wiring + post-fork assert / writesite 反転 / forbid 撤去 / k0-bank 禁止不変量。次 = post-verify PASS で B1 close → B2 (HOLD + oracle API、hold 両 leg cuda:0 pin [W-2])。"
  - "2026-07-12 15:10 %11 (COORD, w2:p3) ⭐**B0 COMPLETE (全 4 項 discharge)** — B0-1 c1pin 3-file dead-branch c70ba1b849 (branch deadbranch/c1pin-refuted-20260712、DO NOT BUILD ON + refutation evidence) → revert a6b7ab6007 (net-zero + tree clean verify、%12 独立検証 PASS) / B0-2 consumer③ = ff-replay のみ縮退 記録 / B0-3 og format revert (完了済 14:0x) / B0-4 flag-OFF baseline pin **ca33d1e1a0** = 29-cell union 全 golden-match (2 層: 毎chunk 5 [x0_y0+DR4隅] / gate-iii 25 [dod9a_prime offline-mirror 導出、count=25 EXACT]; run1 5/5 byte-id + ref self-check PASS / run2 24/24 byte-id + strict mod==golden; %12 条件 a=導出 script+membership sha を manifest 記録 / b=B7 set-equality assert 埋込)。⚠finding: x0_y0 ∉ gate-iii 25-set (env exact-split 述語の不成立側 = 25-vs-58 gap 実体) → union pin で被覆 (%12 ACCEPT)。⭐副次: post-revert route_executor の golden byte 再現 = B0-1 regression 証拠兼務。次 = B1 route_t 骨格 [L-TRIAGE] (charter §4 template)。"
  - "2026-07-12 14:10 %12 (RS-TECH-LEAD, w2:p4) ⭐charter v0.2 BANKED — p1 verify 14:04 = PASS-WITH-CORRECTIONS (転記忠実性 全数照合 PASS / MED 2 fold: W-1 = §6 multi-cell 行に提示者 %12 + W1 完了報告 1-line Rs confirm / W-2 = B2 hold 両 leg を cuda:0 pin に訂正 [f343±1 bar は device 固有、CPU discharge = false-verdict risk]) → blocker 解消、**B1+ 解禁**。ERRATUM-1 (907a526df7) = B0-1 revert scope 3 files (%11 catch: newton_skill_env_base.py +28/-2 omit、%12 on-disk 裏取り: comment の FORK-1 root cause 主張 = REFUTED 済 false + spec 参照ゼロ)。B0-3 完了 (%11、og = revert 択 loud: pre-existing :32 Japanese-text が commit BLOCK → B6 行に carry 註記)。副次: pB tree-wide -f 由来 format dirt 多数 (B0 scope 外、報告のみ、chunk は explicit-path commit ゆえ非干渉)。"
  - "2026-07-12 13:51 %12 (RS-TECH-LEAD, w2:p4) ⭐node 作成 (trainer charter §1 lazy-spawn 授権 + Rs W0-a W1 着手承認 + 本 turn Rs directive「W1 build charter」)。charter v0.1 DRAFT 起草 (W1_ENVBUILD_CHARTER_RSTECHLEAD_20260712.md: B0-B7 chunk 分割 / per-chunk L3 gate template / 担当 %11 build・%10 audit・%12+%9 verify [devplan §7:192] / Rs 後決項 carry 表 / 衛生規則 M12)。prior-art V7 = PASS disposition (hits = 認可設計系譜の自己参照のみ)。on-disk 前提実測: c1pin +23/+70 残 dirty (B0-1 revert 対象) / run_route:1028 実在。1:1 binding = %11 (COORD) builder session (charter 受領時)。次: p1 verify dispatch → PASS 後 %11 B1+ 解禁 (B0 は即時可)。"
---

# T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild — working notes

- 現況 (2026-07-13 01:28): B0 ✓ / B1 CLOSE ✓ / **B2 CLOSE ✓** (a2f544662b + 追補 eb17e51a7d、3-leg joint + C1 CONFIRM) / **現 = B3 (bank v2) [L-TRIAGE] (%11 build)** / B4-B7 残。
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

