# KN-BCRL-Frontier-2026-07 — BC+RL (imitation + reinforcement) frontier survey

- 調査日: 2026-07-05
- 調査主体: web-research skill (Claude subagent, T-ROOT BC+RL ladder support)
- 目的: RS-TECH-LEAD の段階的ラダー skeleton (R0 pure-BC → R1 imit+offpath → R2 DAPG → R3 IBRL+Cal-QL/RLPD → R4 exceed) の per-rung 設計に先立ち、名指しされた手法 (IN-RIL / Cal-QL / OLLIE / IBRL / RLPD / DAPG / residual RL / RECAP / RL Token) の claim を一次ソースで検証し、2025-2026 SOTA (demo-augmented RL × long-horizon contact-rich × dual-arm × cable) を洗い出す
- 調査量: 17 検索/fetch、~60+ 独立ソース (arXiv 一次 + project page + GitHub 実装 + survey repo)
- 注: 本ファイルは調査記録。設計判断は Rs 専権 (07-Design への昇格は別 gate)

---

## 1. 手法別 検証結果 (canonical citation + mechanism + THREAD 適合)

### 1.1 DAPG — VERIFIED (ただし THREAD ladder の用語と乖離あり)
- **出典:** Rajeswaran, Kumar, Gupta, Vezzani, Schulman, Todorov, Levine, "Learning Complex Dexterous Manipulation with Deep Reinforcement Learning and Demonstrations", **RSS 2018**, arXiv:1709.10087
- **機構:** BC で policy を初期化 → **natural policy gradient (on-policy)** に demo データ上の BC 項を加えた augmented gradient で fine-tune。BC 項の重みは訓練とともに **decay**。residual 構造ではない
- **結果:** ADROIT 24-DoF hand の 4 task (relocate/door/hammer/pen)、少数 human demos で数時間相当の sample 数まで効率化、pure RL より頑健で自然な動作
- **⚠ 用語乖離:** ladder R2 の「DAPG=Residual-PPO+BC」は canonical DAPG と別物。canonical DAPG = BC-regularized on-policy PG (decay 付き)。residual-on-frozen-base は §1.7 の系譜 (ResiP 等)。rung 名は「BC-anchored on-policy RL」の方が正確で、実装候補は {canonical DAPG 項, ResiP 型 residual, IN-RIL 型 interleave} の 3 択になる

### 1.2 Cal-QL — VERIFIED (handoff の「monotone-DIVERGENCE 既知解」claim は正当)
- **出典:** Nakamoto, Zhai, Singh, Mark, Ma, Finn, Kumar, Levine, "Cal-QL: Calibrated Offline RL Pre-Training for Efficient Online Fine-Tuning", **NeurIPS 2023**, arXiv:2303.05479、公式実装 github.com/nakamotoo/Cal-QL
- **機構:** CQL の conservative 項を **calibrate**: 学習 Q が「自 policy 値の下界 かつ 参照 (behavior) policy 値の上界」になるよう制約 → offline pretrain 後の online fine-tune 開始時の **性能 dip (unlearning) を防止**。CQL からの変更は one-line
- **結果:** fine-tuning benchmark 9/11 で SOTA (当時)
- **前提条件 (THREAD 照合):** ①offline データに reward ラベル必須 (THREAD: sim 内 script rollout なら付与可能) ②offline RL (TD) pretraining を行う path でのみ意味を持つ。R0-R2 が BC 系なら Cal-QL の出番は「offline RL pretrain を採る場合の保険」に限定
- **2025 更新 (重要):** **WSRL** (Zhou et al., ICLR 2025, arXiv:2412.07762) — warmup 数 rollout で Q を online 分布に再較正すれば **offline データ保持なし + 標準 SAC** で dip なく fine-tune 可能 (Cal-QL 系より速い事例)。**Three Regimes** (arXiv:2510.01460, 2025-10) — 「π0 と D のどちらが優位か」で stability 対象を選ぶ taxonomy (Superior/Inferior/Comparable、63 例中 45 で予測一致)。THREAD の script-oracle demos は高品質 → 多くの rung で "policy-superior regime" → π0 (BC/script) 保持側の手法が整合、という選択指針が得られる

### 1.3 OLLIE — VERIFIED (ただし THREAD 適合度は低め)
- **出典:** Yue, Hua, Ren, Lin, Zhang, Zhang, "OLLIE: Imitation Learning from Offline Pretraining to Online Finetuning", **ICML 2024**, arXiv:2405.17477
- **機構:** offline→online の **adversarial imitation (討論者=discriminator, 報酬なし)** 版 unlearning 対策。policy init と **aligned discriminator init** を同時学習し、online IL 開始時の discriminator 乱調→policy 破壊を防ぐ。20 task で baseline 超え
- **THREAD 照合:** THREAD は sim 内で reward/成功条件を自前定義できるため、報酬なし adversarial IL の必然性が薄い。位置づけは「reward-free 制約が出た場合の既知解」であり、ladder 主経路には不要 (推測ではなく consistency 判断: OLLIE の対象問題は discriminator init 起因の unlearning で、Cal-QL/WSRL の対象 (Q 再較正) と別物)

### 1.4 IBRL — VERIFIED (handoff の「frozen script-oracle = action提案 hard-guide」構想と整合)
- **出典:** Hu, Mirchandani, Sadigh, "Imitation Bootstrapped Reinforcement Learning", arXiv:2311.02198 (v6)、実装 github.com/hengyuan-hu/ibrl
- **機構 (一次ソース確認済):** ①IL policy を先に訓練し **RL 中は凍結** ②**actor proposal**: env 相互作用時、IL 案と RL 案の 2 候補を target Q で比較し高い方を実行 ③**bootstrap proposal**: TD target で両 policy の次行動の高い方から bootstrap。backbone は **TD3** (任意の actor-critic off-policy に一般化可)。BC 正則化 loss 不要 (凍結分離ゆえ hyperparameter 探索が消える)
- **結果:** Robomimic PickPlaceCan で **RLPD 比 6.4x** (10 demos + 100K steps)。demos: can=10 / square=50 / Meta-World=**3 (scripted)**。実機: Lift 100% (8K steps) / Drawer 95% / **布 Hang 85%** (30K steps、deformable、他手法は BC 未満)。ViT Q-net + actor dropout が寄与
- **THREAD 照合 (肯定材料):** ①Meta-World 実験は **scripted demos** で成立 → script-oracle 由来 IL policy という THREAD 構図に前例 ②さらに強い形として、IL policy の代わりに **script oracle T*(o,t) 自体を凍結 proposal policy に据える**変形が自然 (paper の要求は「任意状態で action を返す凍結 policy」のみ。DAgger 用 per-step relabel expert はこれを満たす) ③布 Hang の成功は deformable への適用可能性の直接証拠
- **制約:** 単一 task・10-100K steps 級の検証。whole-route 長 horizon への直接適用は未検証 (→ §3 の chunking/stage 分解と組み合わせ)

### 1.5 RLPD — VERIFIED
- **出典:** Ball, Smith, Kostrikov, Levine, "Efficient Online Reinforcement Learning with Offline Data", **ICML 2023**, arXiv:2302.02948、実装 github.com/ikostrikov/rlpd
- **機構:** **SAC** + ①**symmetric sampling** (各 batch の 50% を offline データ、50% を online replay から) ②critic **LayerNorm** (OOD action の catastrophic 過大評価防止) ③critic ensemble ④**高 UTD (実装既定 20)** ⑤offline pretraining なし (最初から online)。GitHub で utd_ratio=20、Adroit sparse binary 対応を確認
- **結果:** 既存比 ~2.5x、demo 少数でも大量 suboptimal でも可
- **THREAD 照合:** HIL-SERL の基盤 (§2.1)。sparse reward + 少 demo での off-policy 効率の実績が R3 rung の根拠として妥当。IBRL は RLPD を難 task で上回る報告 (IBRL 論文) だが、RLPD は実機実績の厚み (SERL/HIL-SERL 系) で優る

### 1.6 IN-RIL — VERIFIED (新しめ、preprint)
- **出典:** arXiv:2505.10442 (2025-05, UC Davis + Toyota InfoTech Labs)。**査読状況未確認 (preprint)**
- **機構:** fine-tuning 全期間で「RL 更新 k 回ごとに IL 更新を注入」する **interleave** + IL/RL 勾配を **直交部分空間に分離** (destructive interference 防止)。各種 RL algo への plug-in を主張
- **結果:** FurnitureBench / Gym / Robomimic 14 task。**Robomimic Transport 12%→88% (6.3x)**。sim 中心 (実機報告は abstract からは未確認)
- **THREAD 照合:** R2 rung の「BC anchor を decay させる DAPG」に対する 2025 型代替 (anchor を decay でなく interleave+gradient-surgery で維持)。採用時は preprint リスクと再現実装コストを明示すべき

### 1.7 Residual RL — VERIFIED (2024-2025 に系譜が SOTA 化)
- **古典:** Johannink et al. / Silver et al. (2018-19、residual = base controller + 学習補正)
- **ResiP** — Ankile et al., "From Imitation to Refinement — Residual RL for Precise Assembly", arXiv:2407.16677: **凍結 chunked-BC (diffusion) を trajectory planner とみなし、その上に per-step closed-loop residual policy を on-policy RL (PPO) で学習**。精密 assembly で BC 単体・直接 RL fine-tune 双方を上回る。「chunked BC = open-loop 計画器、residual = 反応性の補完」という分解が核
- **Residual Off-Policy RL** — arXiv:2509.19301 (2025-09): 凍結 BC を black-box base とし **off-policy RL で軽量 per-step 補正**、**sparse binary reward のみ**、**実機 humanoid + dexterous hands で初の real-world RL** を主張。高 DoF 系での実績
- **THREAD 照合:** R2 rung の実体はこの系譜 (residual-PPO+BC ≈ ResiP 型)。2025 の教訓は「residual は off-policy 化でさらに sample 効率が上がる」→ R2 (on-policy residual) と R3 (off-policy) の間の橋として "residual + RLPD/TD3" 変形が文献上自然

### 1.8 RECAP / π*0.6 — VERIFIED
- **出典:** Physical Intelligence, "π*0.6: a VLA That Learns From Experience", arXiv:2511.14759 (2025-11)
- **機構 (一次ソース確認済):** ①**分布型 value fn** (steps-to-completion を 201 bin 離散化し cross-entropy、reward = -1/step, 0 成功, 大負 failure; Gemma3 670M backbone) ②**advantage conditioning**: advantage>閾値 を「Advantage: positive/negative」の **binary indicator テキストトークン**として policy 入力に付け、推論時は classifier-free guidance (β) で positive 側を生成 ③**専門家 teleop corrections は無条件で positive 扱い** ④データ 3 源 (demos / autonomous / corrections) を反復再訓練。**AWR 系 weighted regression (off-policy 勾配なし、on-policy PG なし)**
- **結果:** laundry / **box assembly (episode 600s)** / espresso で **throughput >2x・failure ~1/2**、難 task 90%+、13h 連続運転
- **THREAD 照合:** 「whole-route 級 long-horizon を advantage-conditioned supervised learning で改善できる」ことの最大規模の実証。機構 (advantage 条件付け + corrections 優遇) は小規模 policy にも移植可能な原理だが、結果の絶対値は 5B VLA + 大 infra 前提 → R4 の発想源であり R2-R3 の drop-in ではない

### 1.9 RL Token (RLT) — VERIFIED (THREAD に最も近い実タスク証拠)
- **出典:** Physical Intelligence, "RL Token: Bootstrapping Online RL with Vision-Language-Action Models", arXiv:2604.23073 (2026-04)、解説 pi.website/research/rlt
- **機構 (一次ソース確認済):** ①**凍結 VLA (π0.6)** に情報ボトルネック encoder-decoder を付け、内部埋め込みを圧縮した **RL token** を露出 ②その上に **小型 actor-critic head を off-policy RL** で訓練 ③**actor は VLA の予測 action を入力に取り「置換でなく編集 (edit)」を学習** (residual 思想) ④正則化で探索を base 出力近傍に **anchor**、**reference-action dropout** で盲目コピー防止 ⑤human interventions を RL 更新に取り込み可
- **結果:** 実機 4 task = **M3 screw / zip-tie 締結 / Ethernet 挿入 / charger 挿入** (ケーブル系精密 task 3/4)。難所 phase 最大 **3x 高速化**、**15 分の実機データ**から改善・~2h サイクル。Ethernet: 中央値 66 steps vs 人間 teleop 146 vs base 228。throughput 例: Ethernet ~350 vs ~100 /10min
- **THREAD 照合:** 「凍結 base + 小 head + off-policy + reference-action anchor」が **実ケーブル精密操作で時間単位で効く**という、R3 設計 (IBRL 的 hard-guide + off-policy) の最直接な 2026 証拠。RECAP=長 horizon 広域 / RLT=難 stage 局所、という **役割分担**も THREAD の「whole-route + 難所 stage 補強」二層構想への良い前例

### 1.10 HIL-SERL — VERIFIED (補足: Rs「言葉で教示」との長期整合枠)
- **出典:** Luo, Xu, Wu, Levine, "Precise and Dexterous Robotic Manipulation via Human-in-the-Loop Reinforcement Learning", arXiv:2410.21845、**Science Robotics 2025** (scirobotics.ads5033)、実装 rail-berkeley/hil-serl (LeRobot 移植あり)
- **機構:** RLPD 系 off-policy + **binary reward classifier** (teleop 正負例から学習) + demo buffer + **human corrections (漸減)**
- **結果 (paper claim):** **1-2.5h** で near-perfect SR、IL 比 **~2x SR・1.8x 速度**、task は dynamic / precision assembly (timing belt 含む) / **dual-arm 協調**
- **THREAD 照合:** sim-only の現 phase では corrections=script/rs-directive に置換する形で思想だけ借りられる。実機 phase での本命候補

---

## 2. 2025-2026 SOTA — demo-augmented RL × long-horizon contact-rich × dual-arm × cable

### 2.1 ケーブル/DLO 直接系 (成立性確認: Step 0 相当)
| 系 | 出典 | 内容 | RL? | dual-arm? |
|---|---|---|---|---|
| **クリップ通しケーブル routing (最近傍先行)** | Luo et al., arXiv:2307.08927, **IEEE T-RO 2024** | 実機で複数クリップへ連続 routing。**階層 IL** (高位=primitive 選択+リカバリ、低位=vision policy)。RL ではない | ✗ | ✗ (単腕) |
| whole-body global DLO 操作 (3D 拘束環境) | Yu et al., IJRR 2025 (journals.sagepub 02783649241276886) | dual-arm DLO の大域操作 (計画+制御系) | ✗ | ✓ |
| DLO shape control | arXiv:2602.21816 (2026-02) | self-curriculum **model-based RL** で DLO 形状制御 | ✓ | 記載未確認 |
| 産業 harnessing (捻り) | arXiv:2410.10729 | 単腕 DLO harnessing | 部分 | ✗ |
| connector mating / BC 実証 | arXiv:2503.09409 / arXiv:2602.22100 (2026) | コネクタ嵌合の model-based+visuotactile / BC 実証研究 | ✗/✗ | ✗ |
| **RLT (再掲)** | arXiv:2604.23073 | zip-tie/Ethernet/charger = ケーブル系精密 stage を off-policy RL で改善 | ✓ | ✗ |
| MuJoCo DLO 忠実度 | arXiv:2310.00911 (DER in generalized coords, IROS 2025 投稿) + mujoco cable plugin | env7 substrate の忠実度検証・改善の参照点 | - | - |

**Gap 判定 (成立性):** 「demo-augmented **RL** で **dual-arm** の **クリップ routing whole-route** を端到端」は **公開事例ゼロ** (2026-07 時点、上記探索範囲)。最近傍 = 階層 IL の Berkeley cable routing (単腕・RL なし) + stage 局所 RL の RLT。→ ladder R4「THREAD 固有 exceed」の frontier 位置づけは実態と一致。同時に「全部を一発 RL」ではなく **stage 分解 + 局所 RL 補強 + 高位リカバリ**が文献の勝ち筋

### 2.2 汎用 demo-augmented RL の 2025-2026 上位互換
- **Q-chunking** — Li, Zhou, Levine, **NeurIPS 2025**, arXiv:2507.07969: **chunked action 空間で TD 学習** (unbiased n-step backup)、offline-to-online、**long-horizon sparse-reward manipulation で prior best 超え**。BC が action-chunk 出力なら R3 の TD 系はこれで接続するのが 2025 標準
- **DPPO** — arXiv:2409.00588, **ICLR 2025**: diffusion policy の PG fine-tune (二層 MDP)。Robomimic Transport を RL で初めて >50% (sparse reward, pixel 可)。BC=diffusion の場合の R2 有力候補
- **WSRL / Three Regimes** — §1.2 参照 (offline→online の設計指針の現行 SSOT)
- **assembly sim2real 系 (Isaac 圏):** IndustReal / **AutoMate** (RL+IL、実機 ~80%) / **SRSA** (skill 検索→PPO+self-imitation fine-tune) / FORGE (force 条件付け) / MatchMaker (ICRA 2025) / Refinery (arXiv:2510.11019, contact-rich policy の active fine-tune)。NVIDIA R²D² blog に集約。→ 「specialist RL → 蒸留 → 新 task へ retrieval+fine-tune」という **skill 資産化 pattern** は THREAD の per-clip skill 構想と同型
- **実機 online RL の設計選択:** "What Matters for Simulation to Online RL on Real Robots", arXiv:2602.20220 (2026-02): 3 platform・**100 real-world runs** の ablation。実機 phase 前の必読 checklist

### 2.3 VLA×RL 全景 (survey)
- survey repo: github.com/Denghaoyuan123/Awesome-RL-VLA — taxonomy = offline RL-VLA (ConRFT, SRPO, **RECAP**...) / online RL-VLA (**SimpleVLA-RL** arXiv:2509.09674 — LIBERO 99%, RoboTwin 1.0/2.0 +80% 相対, 実機 +120% 相対 / VLA-RL / RIPT-VLA / iRe-VLA / GRAPE...) / test-time (V-GPS, DSRL...) / emerging (**RL Token**, dVLA-RL arXiv:2606.23623...)
- dual-arm benchmark: **RoboTwin 2.0** (arXiv:2506.18088, 50 dual-arm task + 強 DR; SimpleVLA-RL 平均 68.8% 等)。ただし cable routing 級の DLO task は含まれない

---

## 3. ladder (R0-R4) との照合 — 検証済み事実に基づく整合性判定

| rung | handoff 記載 | 文献照合結果 |
|---|---|---|
| R0 pure-BC | — | 標準。BC の器 (per-step MLP / chunked / diffusion) の選択が R2-R3 の接続先を決める (chunked→Q-chunking/ResiP、diffusion→DPPO、per-step→IBRL/RLPD 直結) という **依存関係が文献から確定** |
| R1 imit+offpath (DQ7 iv/ii) | DAgger 正当化済 | 整合。IBRL 論文の教訓「IL policy の質が RL 上限を規定」により、R1 の off-path 被覆は R3 の前提投資としても効く |
| R2 「DAPG=Residual-PPO+BC」 | 基準点 | **命名乖離あり** (§1.1)。canonical DAPG=BC-regularized NPG。residual-PPO+BC の実体は **ResiP** (arXiv:2407.16677) が 2024-25 の代表。代替: IN-RIL (interleave, preprint) / DPPO (diffusion 時)。rung の意図 (BC anchor + on-policy RL) 自体は文献と整合 |
| R3 IBRL + Cal-QL/RLPD | 最新に並ぶ | 概ね妥当。**優先順位の文献的根拠**: script-oracle が凍結 proposal として使える THREAD では **IBRL が構造一致で第一候補** (scripted-demo 前例 + 布 deformable 実績)。RLPD は HIL-SERL 系実績で第二。Cal-QL は「offline RL pretrain を採る場合のみ」の条件付き (WSRL が 2025 の軽量代替)。**2025-26 補強: Q-chunking (chunk 化 TD) / residual off-policy (2509.19301) / RLT (凍結 base+edit head の実ケーブル実証)** を R3 変形として検討価値 |
| R4 THREAD 固有 exceed | — | **frontier 確認** (§2.1 gap)。公開最近傍 = 階層 IL routing (単腕) + stage 局所 RL (RLT)。RECAP は long-horizon 側の原理証拠 |

**横断 caveat (conservatism):**
1. 本 survey の実機系結果 (IBRL/RLPD/HIL-SERL/RLT/RECAP) は THREAD sim (env7 mujoco, dual-arm Franka→UR5e 予定, 88mm span) への **直接転移を保証しない** — algorithm class の成立性証拠として **non-conservative** (現実→sim 方向の壁: contact model 差、whole-route horizon 長)
2. IBRL/RLPD の検証 horizon は 10-100K steps・単一 stage。whole-route への適用は {stage 分解 or chunking or curriculum} の追加設計が必要というのが文献の一致点
3. IN-RIL は preprint (査読未確認)、RLT/RECAP は 5B VLA 前提 — 機構は借りられるが数値は借りられない
4. 律速は handoff どおり **whole-route RL env (P2) の不在**。本 survey は algo 側の選択肢を確定させるのみで、env 律速は変わらない

---

## 4. 出典一覧 (一次)
- DAPG: arxiv.org/abs/1709.10087 (RSS 2018)
- Cal-QL: arxiv.org/abs/2303.05479 (NeurIPS 2023) / github.com/nakamotoo/Cal-QL
- OLLIE: arxiv.org/abs/2405.17477 (ICML 2024)
- IBRL: arxiv.org/abs/2311.02198 / github.com/hengyuan-hu/ibrl / ibrl.hengyuanhu.com
- RLPD: arxiv.org/abs/2302.02948 (ICML 2023) / github.com/ikostrikov/rlpd
- IN-RIL: arxiv.org/abs/2505.10442 (preprint 2025-05)
- ResiP: arxiv.org/abs/2407.16677 / residual-assembly.github.io
- Residual off-policy: arxiv.org/abs/2509.19301
- RECAP/π*0.6: arxiv.org/abs/2511.14759 / pi.website/blog/pistar06
- RL Token: arxiv.org/abs/2604.23073 / pi.website/research/rlt
- HIL-SERL: arxiv.org/abs/2410.21845 / Science Robotics 2025 (ads5033) / hil-serl.github.io
- WSRL: arxiv.org/abs/2412.07762 (ICLR 2025) / zhouzypaul.github.io/wsrl
- Three Regimes: arxiv.org/abs/2510.01460
- Q-chunking: arxiv.org/abs/2507.07969 (NeurIPS 2025)
- DPPO: arxiv.org/abs/2409.00588 (ICLR 2025)
- Berkeley cable routing: arxiv.org/abs/2307.08927 (IEEE T-RO 2024)
- DLO/dual-arm: IJRR 2025 (02783649241276886) / arxiv.org/abs/2602.21816 / arxiv.org/abs/2410.10729 / arxiv.org/abs/2310.00911
- Assembly/sim2real: AutoMate, SRSA, FORGE (arxiv.org/abs/2408.04587), IndustReal, MatchMaker, Refinery (arxiv.org/abs/2510.11019), arxiv.org/abs/2602.20220
- VLA×RL: SimpleVLA-RL arxiv.org/abs/2509.09674 / RoboTwin 2.0 arxiv.org/abs/2506.18088 / survey github.com/Denghaoyuan123/Awesome-RL-VLA
