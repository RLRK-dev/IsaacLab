# fork-B D0 素材 doc (RS-TECH-LEAD %12, 2026-07-16)

**Node**: `T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild-substrate-forkB` (IN_PROGRESS、Rs D0 承認 18:0x)。
**役割**: D0 素材集約 (%12) → p5 裁定 (design v1.13 §21.11.2a DoD 準拠、揃った項から) → %12 bank。
**項 6 (process 故障/NaN 方針) = %12 判断で D0 scope に【採用】** (p5 v1.13 提案・推奨どおり。silent restart = 凍結世界
garbage の process 軸再生、の класс分析を批准)。
**⚠ E0 fence との区別 (pN へ loud 申告)**: 項 1 の「1-process 実測 profile」は §21.11.2a が D0【素材】に指定する単発
診断 run (g6_live 級・訓練なし) であり、fence 対象の E0 (N=1/2/4 scaling + acceptance artifact) ではない、と解釈して
実測する。異議あれば実測前に。

status 記法: ✅=素材充足 (裁定可) / 🔶=部分 (収集中) / ⬜=未着手。

---

## 項 1 — N と資源上限 🔶

**DoD**: 1-process 実測 profile (GPU MiB [⚠CPU mode でも warp 配列は cuda:0 — COMP3 §7]・CPU util/thread・RAM) +
両 GPU 現占有 + ≤4 proc 規則 cite ⇒ N は演算で決める。

- 規則 cite: `CLAUDE.md` GPU 節「A6000 48GB / PRO 4000 24GB は最大**4**プロセス」+ `CUDA_VISIBLE_DEVICES` 必須。
- GPU 序列: cuda:2 = RTX PRO 4000 24GB (VLM+訓練優先) / cuda:0 = A6000 48GB (Isaac/Newton)。route env = **cuda:0 系**
  (canonical route は device-fragile cuda:0 ONLY — memory `project-canonical-route-device-fragile-cpu-vs-cuda-2026-07-02`)。
- ⚠ vision/WM 資源予約 (node invariant §5): N 採択は「空きの全部」を取らない。
- **PENDING-MEASURE**: 1-process profile (live route env wc=1 CPU step、rollout 中の nvidia-smi MiB / psutil CPU%/threads
  / RSS)。→ 実測後に N 上限式: `N ≤ min(4/GPU 規則, floor(GPU_free/GPU_per_proc), floor(CPU_cores_eff/threads_per_proc), RAM)`。

### 項 1 run 前 protocol (OPS-SUP CONCUR-WITH-CONDITIONS、run 前固定・全条件 hard)

1. **D0_CALIBRATION_ONLY**: artifact に明記。B accept / N 採択の証拠に**使わない**。
2. **非流用**: E0 開始後は metric bank 済み同一 harness で **N=1 も新規再走** — 本 artifact を E0 へ流用しない。
3. **事前固定**: exact commit sha / 実行 command / env-fingerprint / `CUDA_VISIBLE_DEVICES` / `world_count=1` /
   `use_mujoco_cpu=True` / workload step 範囲。
4. **測定定義の事前固定**: warmup・測定 window・sampling cadence / GPU MiB = baseline・delta・peak の 3 値 /
   process-tree RSS / CPU% 正規化 (コア数基準明記) / thread count。
5. **PID attribution + before/during/after 正対照**。sample 欠損 = fail-loud (artifact に欠損を PASS 扱いで埋めない)。
6. **1 process・cuda:0・訓練/checkpoint/source 変更なし**。

(prior-art guard = OPS-SUP 実行済 blocker 0。E0/I0 fence 不変。)

## 項 2 — seed / 決定論 ✅ (裁定可)

**DoD**: 裸 np.random 棚卸し + banked byte-repro protocol 群 + 60-key env-fingerprint の per-process 形。

- **(a) 裸 RNG 棚卸し (grep 実測 2026-07-16)**: env 4 file (`newton_route_env.py` / `route_executor.py` /
  `newton_skill_env_base.py` / `route_env_config.py`) 中、裸 np.random = **正確に 1 箇所** =
  `newton_route_env.py:1048-1049` `_reset_worlds` INIT_XY_NOISE `np.random.uniform` (global RNG、seed 経路なし。
  ⚠p5 cite :1038-1040 は行 drift、現行 = :1048-1049)。**seed 設定箇所 = env 側ゼロ** (manual_seed/np.random.seed は
  trainer 系 script のみ: `train_segmenter.py:157-159` / `evaluate_rollout.py:96` 等 = args.seed パターン前例あり)。
  ⇒ 裁定素材: per-process seed 化の対象は事実上この 1 箇所 + 将来 DR sampling (Stage-A :131 per-world 配列)。
- **(b) byte-repro 前提**: `test_routeexec_byte_repro.py` (canonical 81-grid、cuda:0 ONLY = device-fragile
  [memory project-canonical-route-device-fragile]) + golden sha 慣行。fork B は substrate 不変 ⇒ per-process
  byte-repro は「同 seed 同 workload なら process に依らず同一」が主張可能 (E0 で検証)。
- **(c) 60-key env-fingerprint** (`b7553662a4` recorder): per-process artifact に fingerprint + seed + pid +
  `CUDA_VISIBLE_DEVICES` を格納する形を提案 (E0 acceptance の provenance 要件と同族)。

## 項 3 — rollout IPC ✅ (裁定可 — 「界面は共同設計」が主所見)

**DoD**: P2 RLPD trainer の data-ingest 界面 + repo 内 multiprocess/vecenv 前例 grep。

- **主所見: trainer 本体は未建造** — `TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md:30` 逐語「new off-policy trainer
  build ~500-800 LOC (**SAC/TD3/replay = ZERO in repo**; 2nd cost cliff)」⇒ **適合すべき既存 ingest code は無い**。
  collector と trainer は共同設計 (拘束 = define:7 の RLPD 条項 [SAC + 50/50 demo/online replay + high UTD +
  no-pretrain online] + Stage-A :117 transition schema [o, a_raw, a_executed, r_paid, o′, done, time_out,
  termination_reason∈{success,timeout,drop,explosion} + invalid_mask])。
- **multiprocess 前例 (grep)**: RL vecenv = ゼロ。process-pool 前例 = optimizer 系 3 script
  (`comprehensive_optimization.py` 等、multiprocessing 使用) のみ。
- 設計素材メモ: RLPD off-policy ⇒ async 収集自然。裁定点 = 搬送単位 (episode vs chunk)・頻度・backpressure・
  demo/online 50/50 の process 出自別管理。

## 項 4 — Stage-A reconcile (line-anchored) ✅ (裁定可)

**DoD**: Stage-A spec 中の world_count / batch / env 数 前提【行】の列挙。

grep 実測 (`STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md`、multi-world 前提行):
| 行 | 前提 | fork B (N-process × wc=1) への含意 |
|---|---|---|
| :76 | interface v2 `reset_to_phase(k, world_ids=None)` + consumer #6 per-world done-reset | wc=1 では world_ids 恒等 — 契約は保持 (退化形で成立)、per-process には process 管理層が対応 |
| :117 | transition core schema (termination_reason + invalid_mask) | **項 6 の provenance 基盤が既在** — process 出自 tag を additive 拡張 |
| :125 | export disk budget「~0.5MB/episode × **81 worlds 級**」 | 81-world → N-process 換算で再見積 (rotation/retention 再 pin) |
| :131 | DR per-world 配列「**os.environ 経路は multi-world 不可**」 | per-process では env config 経由が同様に必須 (os.environ は process 毎に可だが規約は config 経由を維持) |
| :142/:144 | cable restore = env-level per-world / DR×curriculum 相互排他 | wc=1 で per-world→単世界に退化、矛盾なし。curriculum fork の bank v2 は process 間共有物 (read-only 配布) |
| :324 | consumer #6 順序付き fork entry (restore→seg 窓→fk_jq→route_t→latch) | wc=1 退化形で保持 |
⇒ 主所見: **矛盾は無く「退化 + 換算」で reconcile 可能**。要 re-pin = :125 disk budget と :117 schema の process 出自 tag 拡張のみ。

## 項 5 — R-b tripwire 着地点 ✅ (裁定可)

**DoD**: make_solver / env `__init__` の呼び出し site trace + env default `world_count=4` の扱い (裁定事項) + opt-out 変数名候補。

- site trace (既確認分): `make_solver` def = `newton_skill_env_base.py:1302` (use_mujoco_cpu 既定=USE_MUJOCO_CPU
  task_config:116) / SolverMuJoCo 呼び出し = `:1322-1331` (contacts) `:1332-1340` (no-contacts) / build 内呼び出し =
  `:1985` / env init: `newton_route_env.py:419` `def __init__(self, world_count=4, ...)` = **default 4** ⇒ fork B 下で
  素の `NewtonRouteEnv()` は CPU×4-world = 凍結構成に落ちる (**R-b が塞ぐ対象そのもの**)。
- **裁定事項 (p5)**: (i) default flip (4→1) するか / (ii) default 温存 + tripwire raise で守るか — caller 実態は下記
  (両案とも成立、互換リスクは実測でほぼゼロ)。
- opt-out 変数名候補: `THREAD_ALLOW_CPU_MULTIWORLD=1` (診断専用、既定 raise)。
- **caller 全列挙 (grep 実測 2026-07-16)**: live route-env caller = **全て `world_count=1` 明示**
  (`test_c1_seat_gate{,_mutations}.py` / `p1a_c1_camera_design.py` / `comp3_perarm_cell_grasplift.py` /
  `comp3_g1aprobe_grasplift.py` / `comp5_c2seat_fullfire.py` / `g6_live_rollout_pin.py` / `test_routeexec_writesite.py`
  ×8)。**default=4 に依存する caller = ゼロ** (4 を渡すのは私の multi-world probe 2 本のみ = 意図的)。
  ⇒ 裁定素材: (i) default flip 4→1 の互換リスクは実測上ほぼゼロ / (ii) 温存+tripwire も非破壊。どちらも成立、
  選好判断は p5 (R-b の「機構で塞ぐ」精神は (ii)+flip 併用も可)。

## 項 6 — process 故障/NaN 方針 (ADOPTED) ✅ (裁定可)

**DoD**: 既存 NaN/crash 検出機構 (env/trainer) 棚卸し + replay buffer provenance 表現の現状。

- **(a) env 側 NaN/crash 検出 (grep 実測)**: IK target NaN 検査 `newton_route_env.py:885` / `:1223` (nan_mask) /
  obs sanitize `:1557` `np.nan_to_num` / drop 検出 `:410-411` (DROP_LIFT_MARGIN_M + contact-loss debounce 8) /
  explosion→PPO-mask + timeouts 純度 (`:44-46` docstring、prohibited.md 規則)。
- **(b) trainer 受け側**: 未建造 (項 3) ⇒ 受け側検査は新設計 — 既存拘束は Stage-A :117 の **invalid_mask**
  (explosion = batch mask) のみ。
- **(c) buffer provenance の現状**: **Stage-A :117 が termination_reason + invalid_mask を transition schema に
  既定** ⇒ 隔離基盤あり。無いのは【process 出自 tag】(pid/process_seed/env-fingerprint ref) — additive 拡張が裁定点。
- 裁定素材 (%12 案): fail-loud per-process (crash=その process の in-flight episode を DISCARD + loud log、silent
  restart 禁止) / NaN transition は invalid_mask 既定機構で mask + episode 単位で隔離 / restart は新 seed +
  fingerprint 再記録で「別 process 個体」として履歴分離。

---

## 収集順 (%12 予定) — 進捗 2026-07-16 18:3x
1. ✅ 項 5 caller grep + 項 2 棚卸し grep → 2. ✅ 項 4 line-anchor + 項 3 trainer define + 項 6 棚卸し
→ 3. 🔶 項 1 の 1-process profile 実測 (protocol = pN 6 条件で固定済、run 待ちのみ)。
**status: 項 2/3/4/5/6 = 裁定可 (✅)、項 1 = protocol 固定・実測待ち (🔶)。**
