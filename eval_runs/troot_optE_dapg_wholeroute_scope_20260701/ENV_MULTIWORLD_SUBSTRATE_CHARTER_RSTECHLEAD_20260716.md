# ENV-MULTIWORLD substrate charter 上程 (RS-TECH-LEAD %12, 2026-07-16)

**Status: PROPOSAL (Rs 裁定待ち)。実装ゼロ。** 経路 = %12 ⇄ OPS-SUP-CODEX(pN) → Rs (design v1.9 §21.10.5 #2)。
親 node 候補 = `T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild` 直下の新 node (起票承認 = Rs、NEST §3.1)。
⛔ pin node の中で env fix は始めない (§21.10.5、scope 混入禁止)。

## 1. 発見 (banked `100997a44a` + design v1.9 `e240418803` §21.10) — ⚠ 新規性 訂正 (OPS-SUP-CODEX correction、%12 on-disk 確認済)

**実 NewtonRouteEnv world_count=4 で worlds 1-3 の cable 物理が積分されない** (settle 不発 + FF 駆動 130 RL step 不動;
minimal harness `6fb00b845c` P-3 と同一シグネチャ = 2 独立 harness 一致)。
⇒ **W1 多世界並列訓練は pin と無関係に不可能** (worlds>0 が物理演算されない)。

**⚠ 訂正 (2026-07-16 17:0x): freeze 現象そのものは【既知 prior art】** — `COMP3_PLAN_ROUTEEXEC_GRASPACT_COORD_20260708.md:79`
(2026-07-08) 逐語「worlds≥1-FROZEN escalation (Rs, SEPARATE campaign item): the as-coded env cannot live-step
worlds≥1 (single_world_template → nworld=1; CC3 empirical world1 dz==0)」+ `:32` に root 構成読み (USE_MUJOCO_CPU=True
task_config:116) まで既記録・`:110` に「worlds≥1 FROZEN would contaminate any batch metric」。当初の「prior-art guard
PASS = 新規」は**誤り** — guard keyword が当該 doc の語彙 (worlds≥1-FROZEN / live-step / dz==0 / single_world_template)
と不一致 (absence-claim の検索空間ミス、`[[feedback-absence-claims-grep-all-build-paths]]` の再演として記録)。
**本 charter の新規差分** = ①根因の**二重確定** (D-1 flag 実測 + D-2 統制対照; COMP3 は構成読みのみ) ②**fork A コスト実測**
(D-2 t≈180 NaN; COMP3 は「GPU-mjwarp+cg plumbing」を無コスト情報で option 記載) ③E-1/pin 文脈での再顕在化 ④**COMP3:79 の
standing Rs-escalation item を 8 日越しに正式 charter 化**するもの (放置されていた escalation の discharge)。

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

| Path | 内容 | 得る | 既知 gap / コスト (p5 分析 + D-2/v1.10 実測) |
|---|---|---|---|
| **A: S8 移行** (`use_mujoco_cpu=False`、warp step) | task_config.py:116 が最初から予定した多世界 mode | 真の in-process 多世界並列 | ① mjw eq re-poke DEFERRED の清算 — **正しい形 = 棚卸し→mirror→NaN で bisect** (v1.10 caveat: D-2 NaN はどの poke が致命か未単離、「NaN=4-bar」と読まない) + **R-a: poke-parity を【機構】に** (単一書込 helper or build 時 parity audit、種= geom_solref GPU-inert assert base:1422-1429 の一般化。44 本手 mirror では 45 本目が同クラス再生 = fork A の DoD 要件) ② 決定論 re-baseline (byte-repro は CPU 前提 pin; memory: route = device-fragile) ③ 忠実度 re-anchor (golden route を warp substrate で再走 → **Rs 動画 GT 再取得**) ④ 真 E-2 (warp 消費/nefc)・E-3 (graph capture) 再検証 |
| **B: CPU 維持 + process 並列** | world_count=1 env × N process (trainer 側 vectorize) | substrate 不変 (proven CPU 忠実度・byte-repro 温存) で並列性 | process overhead / rollout 収集 infra 変更 (trainer 側) / GPU メモリ×N。**acceptance gate = §3.2** |
| **C: world_count=1 訓練** | 現状のまま | 追加作業ゼロ | throughput 最低 (最終手段 / B の minimal smoke) |

⚠ A と B は排他でない (A の gap 清算が長引く場合、B が W1 の実用 bridge)。trade 軸 = **W1 訓練の throughput 要件 × 忠実度 × 工数** = Rs 判断。

### 3.1 OPS-SUP-CODEX 推奨 (verify/co-sponsor = CONCUR-WITH-CORRECTION、2026-07-16 17:0x) + Rs L0 手段制約

**推奨 = B primary / C = minimal smoke / A = 独立 hardening (critical path にしない)。**
根拠 = ⭐**Rs 裁定 (2026-07-16 16:5x、p6 直受 verbatim)「L0目標達成手段に、強化学習、模倣学習。ビジョン、ワールドモデルは必須」**
= RL・IL・vision・world model の**全 4 要素が必須** ⇒ NaN 修復・決定論 re-baseline・GT 再取得を伴う A を主 critical path に
すると vision/WM の計算資源・工数を圧迫する。**proven CPU 忠実度の process 並列 (B) で RL/IL throughput を先に確保**し、
vision/WM 資源を予約する。A は R-a (poke-parity 機構) 込みの独立 hardening として並走可。

### 3.2 fork B acceptance gate (OPS-SUP-CODEX 指定、実測で通す)

1. **throughput 実測**: process 並列 N=1/2/4 で transitions/s (route env 実 rollout、RL step 定義で)。
2. **資源 実測**: CPU/GPU メモリ per process (×N 外挿)。
3. **決定論/忠実度**: N process の world_count=1 env が single-run byte-repro と一致するか (CPU proven 前提の保全確認)。
4. **必要 throughput の定義**: trainer の transition budget (W1 訓練規模) から逆算 ⇒ 実測 N-scaling で充足可否を判定。
⇒ 4 点の実測 artifact が揃って B = accept (未達なら A の優先度再考 = Rs 再裁定)。

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
     ⚠ **v1.10 caveat: NaN は【どの poke が致命か】を単離しない**(「NaN=4-bar」と読まない) ⇒ 正しい形 = 棚卸し→mirror→bisect。

## 4-B. 即時項目 #0 (fork 非依存 hygiene、design v1.10 R-b。⛔実装 = charter node、pin node 不可)

**fail-loud tripwire**: `make_solver` / env init に「`use_mujoco_cpu ∧ world_count>1` ⇒ **raise**」(診断用 opt-out env 変数付き)。
COMP3:110 が警告した「凍結世界が batch metric を汚染する」silent-garbage 訓練を**機構で**塞ぐ (規律でなく)。fork A/B/C の
どれを選んでも有効・低コスト・単一箇所。charter 承認と同時に最初の実装項目とすることを推奨。

## 5. L-triage / gate 見立て (charter 承認後の話。本 doc は提案のみ)

- fork A/B いずれも **L3**: A = `task_config.py` SSOT 変更 (L3 auto-escalation path) + substrate premise / B = trainer infra 変更。
- fork A はさらに: 忠実度 re-anchor = **Rs 動画 GT 再取得** (human-GT leg) + 決定論 re-baseline = banked byte-repro 群の扱い裁定。
- pin 側の carry (env 解決後、design v1.9 §21.10.5 #3): E-1 physical + 真 E-2 を **§21.9.1/§21.8.2 の手続きのまま**再走 (設計変更なし)。

## 6. 上程事項 (Rs へ)

1. **fork A / B / C の選択** — **推奨 = B primary / C smoke / A 独立 hardening** (§3.1: OPS-SUP-CODEX 推奨、
   Rs L0 手段制約 [RL/IL/vision/WM 全 4 必須] に接地。B は §3.2 acceptance gate の実測で通す)。
2. **新 node 起票の承認** (pin node と分離、NEST §3.1) + **即時項目 #0 (R-b tripwire、§4-B) の実装承認**。
3. fork A を(併)走させる場合: 忠実度 re-anchor の Rs 動画 GT 手順は既存 verify-run/video 系 protocol を踏襲予定 — 着手順の指示。
   fork A の DoD には **R-a (poke-parity 機構)** を含む (v1.10)。
