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

## 項 2 — seed / 決定論 🔶

**DoD**: 裸 np.random 棚卸し + banked byte-repro protocol 群 + 60-key env-fingerprint の per-process 形。

- 既知例 (p5 cite 確認済): `newton_route_env.py:1038-1040` `_reset_worlds` INIT_XY_NOISE = 裸 `np.random.uniform`
  (global RNG、seed 経路なし)。
- **PENDING-COLLECT**: (a) `np.random\.|random\.|torch\..*seed|np.random.seed|default_rng` の env/executor/trainer 全 grep
  棚卸し表 (file:line × 用途 × seed 経路の有無) / (b) byte-repro protocol cite 群 (`test_routeexec_byte_repro.py`、
  golden sha 慣行、`reference-byterepro-monkeypatch-driver-import-selfcheck-2026-07-07`) / (c) 60-key env fingerprint
  (`b7553662a4` recorder) の per-process 記録形 (per-process artifact に fingerprint+seed+pid を格納する案)。

## 項 3 — rollout IPC 🔶

**DoD**: P2 RLPD trainer の data-ingest 界面 + repo 内 multiprocess/vecenv 前例 grep。

- trainer define: `TRAINER_NODE_DEFINE_RSTECHLEAD_*.md` (P2 RLPD residual-on-script) — **PENDING-COLLECT**: data-ingest
  界面の該当 § 逐語 (replay buffer への投入形式・batch 化・off-policy 前提)。
- **PENDING-COLLECT**: repo 内 `multiprocessing|SubprocVecEnv|Pipe|Queue|shared_memory` grep (前例の有無)。
- 設計素材メモ: RLPD = off-policy ⇒ async 収集が自然 (p5 §21.11.2 #3)。搬送単位 (episode 単位 vs chunk)・頻度・
  backpressure が裁定点。

## 項 4 — Stage-A reconcile (line-anchored) ⬜

**DoD**: Stage-A spec 中の world_count / batch / env 数 前提【行】の列挙。

- **PENDING-COLLECT**: `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md` (v0.8.1) を `world_count|batch|env 数|
  並列|worlds` で走査し line-anchored 表に (narrative 禁止、p5 DoD)。

## 項 5 — R-b tripwire 着地点 🔶

**DoD**: make_solver / env `__init__` の呼び出し site trace + env default `world_count=4` の扱い (裁定事項) + opt-out 変数名候補。

- site trace (既確認分): `make_solver` def = `newton_skill_env_base.py:1302` (use_mujoco_cpu 既定=USE_MUJOCO_CPU
  task_config:116) / SolverMuJoCo 呼び出し = `:1322-1331` (contacts) `:1332-1340` (no-contacts) / build 内呼び出し =
  `:1985` / env init: `newton_route_env.py:419` `def __init__(self, world_count=4, ...)` = **default 4** ⇒ fork B 下で
  素の `NewtonRouteEnv()` は CPU×4-world = 凍結構成に落ちる (**R-b が塞ぐ対象そのもの**)。
- **裁定事項 (p5)**: (i) default flip (4→1) するか / (ii) default 温存 + tripwire raise で守るか。素材観点: (i) は挙動
  互換性リスク (既存 caller が world_count 未指定でも 4-world build を期待する箇所の有無 → **PENDING-COLLECT** caller grep)、
  (ii) は非破壊 (推奨候補)。
- opt-out 変数名候補: `THREAD_ALLOW_CPU_MULTIWORLD=1` (診断専用、既定 raise)。
- **PENDING-COLLECT**: `NewtonRouteEnv(` / `build_multiworld_scene(` caller 全列挙 (world_count 引数の実態)。

## 項 6 — process 故障/NaN 方針 (ADOPTED) ⬜

**DoD**: 既存 NaN/crash 検出機構 (env/trainer) 棚卸し + replay buffer provenance 表現の現状。

- 既知素材: env 側 = `_compute_rewards_dones_batch` の explosion/dropped 検出 + `torch.nan_to_num` (obs/rewards)、
  timeouts 純度規則 (prohibited.md)。fail-loud 文化 = pin/authorizer の RAISE-everything 設計。
- **PENDING-COLLECT**: (a) env の NaN→done 経路の file:line 列挙 (b) trainer 側 (RLPD) の受け側検査の有無
  (c) replay buffer の provenance 表現 (transition に process/episode 出自 tag があるか — 現状は無い見込み → 隔離可能な
  tag 設計が裁定点)。

---

## 収集順 (%12 予定)
1. 項 5 caller grep + 項 2 棚卸し grep (机上・速い) → 2. 項 4 line-anchor 走査 + 項 3 trainer define 逐語 + 項 6 棚卸し
→ 3. 項 1 の 1-process profile 実測 (単発診断 run、pN 異議窓の後)。揃った項から p5 へ。
