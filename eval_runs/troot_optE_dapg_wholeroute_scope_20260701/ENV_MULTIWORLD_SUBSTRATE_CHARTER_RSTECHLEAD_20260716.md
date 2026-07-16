# ENV-MULTIWORLD substrate charter 上程 (RS-TECH-LEAD %12, 2026-07-16)

**Status: PROPOSAL (Rs 裁定待ち)。実装ゼロ。** 経路 = %12 ⇄ OPS-SUP-CODEX(pN) → Rs (design v1.9 §21.10.5 #2)。
親 node 候補 = `T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild` 直下の新 node (起票承認 = Rs、NEST §3.1)。
⛔ pin node の中で env fix は始めない (§21.10.5、scope 混入禁止)。

## 1. 発見 (banked `100997a44a` + design v1.9 `e240418803` §21.10)

**実 NewtonRouteEnv world_count=4 で worlds 1-3 の cable 物理が積分されない** (settle 不発 + FF 駆動 130 RL step 不動;
minimal harness `6fb00b845c` P-3 と同一シグネチャ = 2 独立 harness 一致; prior-art guard PASS = 新規)。
⇒ **W1 多世界並列訓練は pin と無関係に不可能** (worlds>0 が物理演算されない)。

## 2. 根因 = by-construction (バグではなく CPU-smoke 構成の既知限界の初顕在化)

| 事実 | cite |
|---|---|
| `USE_MUJOCO_CPU = True`。コメント逐語「Opt-1/S4-S7 = CPU smoke; **GPU (use_mujoco_cpu=False) = S8**」 | `task_config.py:116` |
| env solver build 既定 = `make_solver(model, enable_cable_contacts=...)` → `use_mujoco_cpu=USE_MUJOCO_CPU` | `newton_skill_env_base.py:1302/:1322-1340/:1985` |
| solver step: `use_mujoco_cpu=True` ⇒ `mj_step(mj_model, mj_data)` = **single-world host template のみ積分** (mjw は step されない) | `solver_mujoco.py:3266-3289` |
| **D-1 (1-bit 判別) = True 実測**: production build path (wc=4, cuda:0) で `solver.use_mujoco_cpu=True`。`separate_worlds` 属性は post-init 不在 (CPU path で未消費) | D-1 run 2026-07-16 (本 doc §4) |

全観測 (worlds>0 完全不動・mjw 配列 (4,40) per-world 実在なのに不動・2 harness 一致) がこの構成で余さず説明される。
route env の物理検証はこれまで**全て world_count=1** (g6_live 含む) = CPU 単一世界 path のみ proven。

## 3. 設計 fork (p5 事前分析 = design v1.9 §21.10.4。**選択 = Rs**)

| Path | 内容 | 得る | 既知 gap / コスト (p5 分析) |
|---|---|---|---|
| **A: S8 移行** (`use_mujoco_cpu=False`、warp step) | task_config.py:116 が最初から予定した多世界 mode | 真の in-process 多世界並列 | ① mjw eq re-poke DEFERRED の清算 (4-bar 剛性ほか CPU/mj_model 限定 poke の全数棚卸し→mjw mirror) ② 決定論 re-baseline (byte-repro は CPU 前提 pin; memory: route = device-fragile) ③ 忠実度 re-anchor (golden route を warp substrate で再走 → **Rs 動画 GT 再取得**) ④ 真 E-2 (warp 消費/nefc)・E-3 (graph capture) 再検証 |
| **B: CPU 維持 + process 並列** | world_count=1 env × N process (trainer 側 vectorize) | substrate 不変 (proven CPU 忠実度・byte-repro 温存) で並列性 | process overhead / rollout 収集 infra 変更 (trainer 側) / GPU メモリ×N |
| **C: world_count=1 訓練** | 現状のまま | 追加作業ゼロ | throughput 最低 (最終手段) |

⚠ A と B は排他でない (A の gap 清算が長引く場合、B が W1 の実用 bridge)。trade 軸 = **W1 訓練の throughput 要件 × 忠実度 × 工数** = Rs 判断。

## 4. 判別テスト結果 (D-1 / D-2、§21.10.1 指定)

- **D-1 (1-bit) = True**: production build path で `solver.use_mujoco_cpu=True` 実測 ⇒ step 分岐 cite により仮説確定。
- **D-2 (対照、事前登録予測付き)**: `use_mujoco_cpu=False` 強制 (probe-local monkeypatch、source 不変) + settle 試験。
  事前登録予測 = 「全 world settle 開始 / 4-bar は flop し得る (mjw eq re-poke DEFERRED = S8-gap の実証)」。
  **結果 = 予測 2 本とも確認 (より強い形)** — `env_multiworld_d2_control_result.json`:
  1. ✅ **全 4 world が同期 settle** (t=60: 808.22 / t=120: 805.91、全 world 同値) ⇒ warp path は worlds>0 を積分する。
     CPU 分岐で凍結・warp で可動 = **根因二重確定** (D-1 flag + D-2 対照)。
  2. ⚠ **t≈180 で全 world NaN 爆発** (world1 のみ t=180 に 802.53 で一瞬生存後 NaN)。予測の「4-bar flop し得る」は
     現実には**物理爆発**として顕在化 = S8-gap (CPU/mj_model 限定 poke 未 mirror — 4-bar eq_solref [0.001,1]
     剛性化 44 本等) の実証。⇒ **fork A 作業項目① (mjw poke 全数棚卸し→mirror) は必須・非自明** — warp 移行は
     flag flip では済まない (D-2 がその最小反例)。D-2 は失敗ではなく fork A のコスト実測。

## 5. L-triage / gate 見立て (charter 承認後の話。本 doc は提案のみ)

- fork A/B いずれも **L3**: A = `task_config.py` SSOT 変更 (L3 auto-escalation path) + substrate premise / B = trainer infra 変更。
- fork A はさらに: 忠実度 re-anchor = **Rs 動画 GT 再取得** (human-GT leg) + 決定論 re-baseline = banked byte-repro 群の扱い裁定。
- pin 側の carry (env 解決後、design v1.9 §21.10.5 #3): E-1 physical + 真 E-2 を **§21.9.1/§21.8.2 の手続きのまま**再走 (設計変更なし)。

## 6. 上程事項 (Rs へ)

1. **fork A / B / C の選択** (または A+B 並走の指示)。
2. **新 node 起票の承認** (pin node と分離、NEST §3.1)。
3. fork A の場合: 忠実度 re-anchor の Rs 動画 GT 手順は既存 verify-run/video 系 protocol を踏襲予定 — 着手順の指示。
