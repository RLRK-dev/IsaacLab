# Rs W0-a′ 決定 packet — P2 whole-route env + BC+RL LADDER v2 (1 回決定型)

**Status: v1.0 (14:37 — %9 content PV = PASS [PASS-w-4-fixes → 全反映を spot-diff 5/5 確認]、c-j7-1 re-CONCUR SATISFIED → Rs 提示可)。**bank commit = Rs 14:2x 授権済 (「判定確定したらpacket v1とbank commitまで進めて」)。構造 = v0.1 凍結のまま (11:38 %9 構造 PV PASS-w-3-additions、cite 9/9 ✓)。
**Author:** %12 RS-TECH-LEAD。**定義元:** spec §9-3 v1.5 (`P2_ROUTE_ENV_SPEC_INPUT_W0C_RSTECHLEAD_20260705.md:115`、W0-a を supersede)。
**Grounding:** LEDGER `BC+RL LADDER v2` 行 / devplan v1.1 (`BCRL_DEVPLAN_LADDER_V2_RSTECHLEAD_20260705.md`) / spec v1.5 + artifacts v1.3 / PREREG+A1 (`P3_GRID_PREREG_20260705.md`) / 5体 DECIDE (`P2_ENVSPEC_5TAI_DECIDE_20260705.md`) / %9 台帳 (`P2_W0C_CROSSPV_PCT9.md`)。
**使い方 (Rs):** §1→§8 を上から順に。各決定 = 選択肢 + 推奨 + 根拠 cite。**全て Rs 専権事項 (env/reward/DR/UNIT) — 承認まで build なし。**

---

## §0. 決定リスト一覧 (この packet で Rs が決める全項目)

**承認の総体 (s1):** 本 packet の承認 = **spec v1.5 + artifacts v1.3 を P2 設計基底として採択し、§8 の staged build charter 発行を授権する** こと。個別決定は下表。

| # | 決定 | 種別 | 節 |
|---|---|---|---|
| P | premise 再確認 (経路全体 1-unit) | 前提 | §1 |
| DC-1 | branch α vs β (± 併用順序) = D-C 本体 (+α 採択時 sub: 6D vs 12D) | UNIT/algo | §3 |
| DC-2 | R3 既定 algo (RLPD 案) | algo | §3 |
| DC-3 | AR-extend 却下 → NEW env 建設 | env | §3 |
| Q1-Q11 | named-design-Q 10 項 + confirm-only 3 件 (Q11) | env/reward | §4 |
| T1-T3 | §4.3 数値閾値 3 pin | gate | §5 |
| P4 | credit/訓練 pre-registration 5 項 | 訓練 | §6 |
| L | L-TRIAGE L2 降格 confirm | 手続 | §7 |

---

## §1. premise 再確認 (1 行)

**「route 全体を 1 unit として学習する」方針を、新証拠 (R0/R1 = pure-BC/模倣系 4 path plateau + β-mix instrument 不成立 [R1 CLOSE c1-c4] + 文献では stage 分解 + 局所 RL + 高位 recovery が勝ち筋 [devplan:81、公開事例ゼロ]) の下で再確認いただく。** 変更する場合 = premise change → 本 packet の §3 以降は再構成 (stage 分解案は devplan:159 (d)、STOP-and-flag 手続き)。**推奨 = 維持** (LADDER v2 は 1-unit のまま R2 で局所 RL 相当 [c2-sized 発見 + curriculum] を branch 内に内蔵済み)。

## §2. P3-grid 実測 (evidence base) — 完走 81/81 (07-05 13:18、infra 0、三者一致 + %9 countersign 済)

- **SR@DR ±20mm strict (A1 PRIMARY) = 59/81 = 0.728、Wilson95 [0.623, 0.813]** / any-seat (diagnostic) = 80/81 = 0.988 [0.933, 0.998]。内訳: seat-miss (delivery-ok) 21 cell (per-cell 表 = `p3_grid/P3_GRID_REPORT_draft.md` + CSV) + FAIL 1 (x-20_y5、R_MISS grip-whiff r_grip=0.0N)。計器注記 (annex、J-8b→**解消済 14:2x**): 22 non-strict 中 1 cell (x-20_y-15) は計器 false-negative と確定 (Y-argmin が自由端 node0 [clip から x 266mm] に hijack; 実 routed 節 18-21 は mouth footprint 内 z 829.9-831.2 = seat 高 — 数値 3 leg + node 表 + video 無矛盾、frame check two-key 済)。**公式値は A1 凍結 producer flag の 59/81 = 0.728 を維持** (遡及再分類なし)。**方向 tag (GROVE §2.2): 公式値の誤差は under-state 側のみ** (over-state 経路は strict 59 の測定 node が全て routed 帯 18-25 で不観測)、flip 上限 1 cell ≪ 0.80 跨ぎに必要な ~5.8 cell → **≤80% 枝判断に対し conservative-definite** (JOINTREAD J-8e r4)。
- **evidence-gate 判定 (PREREG §2 pin、J1 確定 14:2x): 点推定 = ≤80% 枝 → α-DR は (d) position-DR で開始可**。CI 上端 0.813 が 0.80 を僅か跨ぐ事実を併記。**robust 結論 = ≥95% 枝の決定的棄却 — M-C bites せず、(a)/(b) は「必須」でなく robustness OPTION として retained** (frame check two-key 完了、JOINTREAD 確定 section)。
- **device 条件付き注記 (annex、GPU1 資格 probe 14:1x)**: 本 SR map / 決定論 6/6 は **cuda:0 (A6000) 条件付き**。異機種 cuda:1 (PRO 4000) 再走 = 3 class 代表 3/3 MISMATCH・両方向 outcome 反転 (同 device 再走は 7/7 完全一致) — marginal 帯 knife-edge の独立実証 (J-8 連続体像と整合; x-20_y5 は final cable 位置 1.9mm 差で verdict flip = 把持 microevent)。帰結: GPU1 = 独立 workload 専用 / cross-device 集計比較は device-confound caveat 必須 (`gpu1_qual_probe/PROBE_PREREG.md` two-key 済)。訓練含意: DR 学習は bit 決定論に依存しない設計 (realization noise 頑健性 = まさに DR の対象) — 比較実験の same-device 規約 (§3 comparator) はこれで裏付け。
- sha-epoch 注記 (annex): grid meta の working-tree sha は 3 epoch (走行中の md 前倒し編集)。**物理系 code 非接触 = %9 検証済** (governing 4 file の mtime [task_config 06-26 / grip_env 06-15 / test_newton 07-03 / policy_route_runner 07-04 14:15] 全て grid 開始前) + **behavioral 閉包** = render 7-cell MATCH (後 2 epoch) + x0_y0 cuda:0 再走 = **EXACT-MATCH (14:30 完了、Δz/Δwall 0.000・discrete 同一、%9 tuple 照合 EXACT 14:3x — 最初期 epoch 閉包、`p3_grid/sha_epoch_close/`)**。将来項: per-file sha stamp (P2 build spec 提案)。
- **⭐ 失敗機構 (J-8、独立 2 経路 two-key):** 22 non-strict 全てが **in_groove(z) leg** で fail — **実分離軸 = z (drop-in 完了度)、lateral wall は非分離軸** (strict z_gap [−0.2, +3.0] vs non-strict [+3.1, +56.2] median +7.1mm [seat-miss 21 基準; 22 全体では +7.0]; 帯 3-5mm ×9 / 5-16mm ×10 / 25-56mm ×3)。→ **c2 Δ bound は z-gap 分布で size する** (lateral 2.4mm 基準だと ~3× 過小)。p_hit stage-2 の成功域 = 2D offset grid-map そのもの (Δ_EE common-mode ~1:1 補償、REPORT 図) + 本 z 分布 — floor 判定は P4 pre-reg 時に discharge。
- dual-grip span: **92.42mm 定数 (分布退化、[p1,p99] 幅ゼロ)** → G1/span-guard window は設計値で pin。**positive finding: settle span が ±20mm IC に対して不変 = common-mode recenter が全域で機能 = INV#2 の運用的裏付け。**
- episode 長 (n=81): **max 771 < 810 → horizon 900 確定** (bump 規則 非発動; max-of-n 保守注記)。
- **draw-class = EMPTY (provisional)、n_winnable = 81 ≥ 59** — 全 22 non-strict が直交 5mm 以内に strict 隣接 + reach residual max 1.2mm でバリア無し。fallback: z-tail cell を Δ/z bound が cover できなければ draw 会計へ復帰し SR を機械更新。補強 (GPU1 probe 副産物、保守方向のみ): FAIL cell x-20_y5 が別 realization で **delivery-level 成功の witness** (SUCCESS_DUAL_LOADED、ただし honest=False = strict-level は unwitnessed) → 幾何的 unwinnable でない (denominator 81 会計不変)。
- **%9 独立再計数 countersign (r3): 済 13:2x 全一致** (凍結 parser sha=03ff671f、CP-C 較正 EXACT)。決定論: CP-C 共通 6 cell 日跨ぎ同 class 6/6 + m8_p8 rerun 同一 outcome。
- **decision-of-record = `P3_GRID_JOINTREAD_20260705.md`** (J1-J8c、%12+%9 two-key)。
- 参考 prior (CP-C 17 offsets、07-03; %9 凍結 parser 較正 11:48 で確定): **strict 14/17=82.4% Wilson95[0.590,0.938] / any-seat 16/17=94.1% [0.730,0.990]** — 境界隣接ゆえ grid が decider (spec:32、旧 13/16 記載は 11:52 訂正済)。

## §3. D-C: branch 決定 + R3 + AR-extend + supersession 義務

**DC-1 (本体): α = R2b residual-on-frozen-script vs β = R2a′ canonical-DAPG-on-B2-contract (± 併用順序)。**
- 対称必須機構 (どちらも「必須機構なし」構成は選択肢にしない、spec:32/29):
  - **α = 3 点**: (i) oracle drift-recovery relabel (script-faithful 限界明記) + (ii) structured-common-mode 局所 RL 発見 (原則 0 準拠 σ 構造化 + p_hit 事前 discharge + corner-mask) + (iii) 発見不能域 = draw 会計。trainer 統合 = 交互 aux imitation update。
  - **β = curriculum 必須**: script-run-to-phase-k (推奨 = precomputed phase-k **state-bank**、fork 3 択 spec:29) + prefix 3 pin (①prefix transitions PPO 除外 ②time/horizon = handover 起点 ③phase-k 未達 = resample)。
- 判断材料: 4-fork 比較表 = spec §2 (F1 contract / F2 phase-clock / 学習対象の実質 / OG 接続)。α の売り (copycat 構造回避) は M-C 制約と対 — **α 採択の実質条件 = α-DR (a)/(b)、その decider = §2 grid 実測** (spec:36)。devplan:208 の旧推奨 (R2b primary) は 5体 CC2-CRIT (発見可能性) を経て「整理」に降格済。**joint 推奨 (%12+%9 連名、JOINTREAD J7) = α (residual-on-frozen-script) lean。決定 = Rs。** 根拠 (z 改訂 mapping): 配達 0.988 / honest-seat 0.728 (計器 annex = §2) / 失敗 22/22 = terminal 近傍の**垂直 drop-in 不足** (典型 +3〜+15mm、median +7.1 [seat-miss 21; 22 全体 7.0]) = 小 Δ・短 credit path = residual regime。β の勝ち筋 (base 崩壊時の自前 following/restoring) は実測失敗像と逆。fallback trigger 名指し: **α discharge FAIL at P4 → β 再浮上 or α-DR (a) 追加 (D-C 再訪)**、β 行は menu 残置。D-C loop 含意: drop-in 不足の base-choreography 系統成分 (seat push 深さ) が script-param 側で回収される scenario では strict SR 上振れ → 枝が ≥95% 側へ動き M-C/α-DR が復活し得る — §2 の retained-OPTION 語がこれを受ける (観察のみ、workstream 化 = Rs)。SR 文言は frame check two-key 済の確定値 (0.728 公式、annex 注記付き)。
- **α 採択時の sub-decision (s3、HIGH5 の hinge): residual contract = α-6D (position-only) vs α-12D (rot 込み)。推奨 = α-6D** — HIGH5 (rot 6D near-inert + demo rot-delta ≡0) を moot 化、G7 は base-ori 依存として明示 (spec:28 F1 sub-option)。**α-12D を選ぶ場合 = HIGH5 再輸入 + Q4 (seat-ori 節) の再検討が連動して live 化。**
- **共通 comparator pre-register (併用/比較時の判定規約、いま pin)**: from-P0 SR / identical winnable-support (P3 draw 除外を両枝同一適用) / matched GPU budget / same env sha + cuda:0 + same seed/DR stream / per-class 内訳 (nominal SR + corner uplift) / 併用時の order-confound 明記 — N≥30 + nomA/nomB band + %12+%9 joint verdict (既存規律と同一文)。
- **DC-1 採択が α (PARKED-A un-park) の場合: DQ1=B→A′ supersession を同 turn で LEDGER + node state に banking (義務、devplan:236)。**

**DC-2: R3 既定 = RLPD (+ IBRL 型 proposal は BC-proposal fallback 併設で caveat 運用) + horizon 対策 arm ≥1。Cal-QL/WSRL = 条件付き (devplan:208、§5-R3-1)。** grid 非依存 — 本 packet で確定可。

**DC-3: AR-extend 却下 → NEW route env 建設 (NHA-3 disposition)**: AR は frozen-L contract / mid-air reset 前提 / dense reward / MAX200 / row56 regression surface が結合し、whole-route 要件と非互換 → NEW。実 reuse = base 2109 行は両案共通 (spec:115)。cost = spec §7 (~3.4-6.4k touched、staged per-component L3 chain ≤800 行/diff)。

## §4. named-design-Q 10 項 (各 = 問い / 選択肢 / 推奨+根拠)

| # | Q | 選択肢 | 推奨 (根拠) |
|---|---|---|---|
| Q1 α-PC | base clock と policy 逸脱の re-sync 規約 | (a) 無条件 march / (b) 逸脱>閾値で base pause + oracle 再照会 / (c) predicate 到達で advance | **(b) 系** (B1 型 desync 回避、spec:29)。α 採択時のみ live |
| Q2 α-DR | α の学習信号源 **(α 採択時のみ live)** | (a) 摂動注入 / (b) obs-noise・est-pose / (c) retention margin / (d) position-DR-only | **(d) position-DR で開始 = evidence-gate 実測結果** (§2 ≤80% 枝、{59,60} 不変)。(a)/(b) は robustness OPTION として retained (≥95% 棄却により必須性消滅; D-C loop scenario で復活し得る、§3) |
| Q3 Q7 承継 | inter-arm collision の扱い | re-enable + penalty / reach-terminate のみ | **推奨 = reach-terminate + 実 wrist proxy 監視** (AC で sphere 落とし OVERLAP 確定済 spec:59; sim-geom は REAL-wrist proxy でない [memory: dualarm-collision]) — Rs 確定要 |
| Q4 HIGH4 | success の seat-ori 節 | 含める / **外す (G7 解決まで)** | **外す** (base-route が ori 供給; 復活条件 = G7 解決後; **α-12D 選択時のみ再検討の節が live — DC-1 sub [s3] と連動**、spec:45) |
| Q5 horizon | RL horizon | 900 (実測 771 + margin) | **900 確定** — n=81 実測 max 771 < 810、bump 規則 非発動 (§2) |
| Q6 OG band | band α/β/γ | 現行 draft のまま provisional / 再較正 | **provisional 明記のまま採用 → §6-11 OG port+再検証後に再 pin = 1 決定に統合** (devplan:117-121; seg-follow ceiling 0.667<0.8 問題) |
| Q7 draw 方針 | 不可勝 cell の扱い | truncate-無-penalty / **DR-support 除外 + 文書化** | **DR-support 除外** (truncate は quit-button hack 3 注意 [trigger 可影響 / V(s) alias / time_outs 純度] を全て踏む、spec:75)。cell list = **EMPTY (provisional、§2)** — ±20mm 全域 winnable、fallback 規則のみ残置 |
| Q8 obs v2.1 | 53D か 57D か | 53D / **57D** ([53:55] contact + [55:57] IK-resid) | **57D** (§A8 照合: G1/G4 の reward 入力 grip-contact と reach-fail に obs 対応が無いと §運用21 違反、artifacts §A8) |
| Q9 counting | SR 計数規則 | — | **確定済み扱いの confirm のみ**: per-offset unique + A1 (strict PRIMARY / any-seat diagnostic / seat-miss per-cell) — PREREG two-key 済 (11:21) |
| Q10 span tier | span-guard window の tier | informative 既定 / hard terminate | **informative 既定を維持** — P3 実測 window = 92.42mm 定数 (分布退化、§2) → window は設計値で pin、hard 化は design-gate 項 (f2) のまま。banked ruling 忠実 (spec:75) |
| Q11 confirm 群 (s2) | **confirm-only 3 件** (規約は既決、Rs 確認のみ): ①explosion terminate の obs 非対応 rationale (artifacts §A8 explosion 行 = justified-absent) ②sustain-counter の obs 化不要 (artifacts §A8 G6 行、0.995^10=0.951 論拠) ③oracle mid-servo label = ACHIEVED-vs-COMMANDED 規約 (spec §5 D-1 行、converter 慣例 route_demo_to_bc.py:287 準拠) | confirm / 差戻し | **3 件とも confirm を推奨** — spec/artifacts 内の design-gate flag を宙に浮かせない (確認日時が本 packet に記録される) |

## §5. §4.3 数値閾値 3 pin (draft 値 — 本 packet で Rs 確定、確定まで HIGH-COST-GATE は GO を出さない)

1. **abort**: post_base_drop >0.20 が 2 連続 eval OR OG restoring legs 3 checkpoint 連続 monotone 悪化 (de-risk window=3 実績準拠)。
2. **actor-gate (R3)**: Q_rank_error <0.10。
3. **R2b PASS bar**: DR±20mm in-sim category-SUCCESS **≥70%** (N≥30、band 分離) かつ script-under-DR baseline (= §2 grid 実測 **strict 0.728 [0.623,0.813]**、計器 1 cell 確定で {0.728|0.741}) を band 超えで上回る。
(devplan:124。fail-set = 契約統一後に再変換した B1+budget-test rollouts、devplan:122)

## §6. P4 credit/訓練 pre-registration (提案値入り — 空欄 provision 禁止)

| 項 | 提案値 | 根拠 |
|---|---|---|
| γ | **0.997** | 1/(1−γ)=333 vs horizon 900; smoke で再検証 (spec:115) |
| GAE λ | **0.95** | RSL-RL 標準; whole-route 長 horizon での bias-variance 折衷 |
| envs×steps | **smoke 実測で確定** (仮 pin は smoke DoD throughput ≥9.7fps から逆算) | spec §4 DoD |
| corner-episodes | **≥8 /update** | (ii) 発見の E[discoveries/update] ≥1 と整合。p_hit stage-2 discharge は P4 pre-reg 時 (§2 grid-map + z_gap 分布が入力) — 実測により Δ bound は z 軸で size (§2 J-8) |
| λ_relabel / anchor decay (α のみ) | **λ_relabel = 別 buffer 交互 update、比率 1:4 案 / anchor decay = corner-mask + 線形 decay 案** | CC2-CH2/CH3 fix (DECIDE 表); 選択肢の比較は P4 pre-reg 内で ablation 予約 |

## §7. L-TRIAGE 降格 confirm

本 design-gate chain は以下を**全て完走済み** (r2、実 gate 列挙): 5体 debate ×2 (mini-test [VERIFY] + env-spec、DECIDE 記録 banked) + pre-check 3-entry chain (BLOCK 10:04 → WARN 10:36 → PASS 10:45、`logs/pre-check-log.jsonl`) + %9 PV 台帳 (9-lens / DECIDE cross-PV / spot-diff、`P2_W0C_CROSSPV_PCT9.md`)。build 段は **staged per-component charter (各 ≤800 行 diff、個別 L3 chain)** で進める前提のため、**packet 承認自体の追加 gate は不要 = L2 扱いを confirm** (devplan:7 carry)。未 confirm の場合 = L3 追加 gate (層5 多視点並行検証を packet に対して再実施)。

## §8. 承認後の即時 banking + 次工程 (Rs 承認と同 turn で %12 実施)

1. LEDGER `BC+RL LADDER v2` 行更新 (Rs-PENDING → DECIDED 分離解消) + DC-1=α の場合 DQ1 supersession 行。
2. node state.md + 地図 (今ここ frame) + manifest §2 再生成 (確定事項の即反映 gate)。
3. staged build charter 発行順: **env-core → route-executor 抽出 → oracle → OG port → trainer** (spec §7、各個別 L3 chain)。
4. P4 pre-reg の smoke-確定項 (envs×steps) は env-core smoke 完了時に再提示。

---
*%9 cross-PV: 構造 PV = **PASS-w-3-additions (11:36、cite 9/9 ✓)**。content PV = **PASS (14:37、PASS-w-4-fixes C1-C4+n1 反映を spot-diff 5/5 確認、c-j7-1 re-CONCUR SATISFIED、countersign 済)**。*
*v0 skeleton 11:30 → v0.1 11:38 → v0.9 pre-fold 13:5x → **v1.0-rc 14:2x JST %12** (frame check + probe two-key 確定を反映、全 slot 最終値。decision-of-record = `P3_GRID_JOINTREAD_20260705.md` + `gpu1_qual_probe/PROBE_PREREG.md`)。*
