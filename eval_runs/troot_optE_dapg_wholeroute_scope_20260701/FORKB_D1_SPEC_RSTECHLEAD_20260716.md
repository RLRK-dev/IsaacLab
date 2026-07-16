# fork-B D1 spec (RS-TECH-LEAD %12, 2026-07-16) v0.3

**Node**: `T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild-substrate-forkB`。**Status: p5 verify = CONFORM 7/7 PASS (v1.3) + AMEND-1 (v0.2) + ⭐v0.3 = §7/§9 の POST-E0 DESIGN AMENDMENT 版上げ** (pN E0 HOLD 調停: E0 predicate 再定義 + I0 acceptance leg 移管 [RULINGS v1.5 N-1 / v1.6 R2-4-b `2f6096a6a2`] + E0v2 7 条件 [pN CONCUR-WITH-CONDITIONS]。⛔「元 §7 事前登録の PASS」を主張しない — 移管 leg は amendment として記録)。
**入力**: D0 裁定 = `FORKB_D0_RULINGS_VTDESIGN_20260716.md` v1.3 (`9cea41ac67`; R1 `889ce6b640` / R2-R6 `11fdb0bc11`) +
素材 doc (`92eab23ceb`) + calibration profile **v4 (`fd536235e9`) = 確定 evidence (pN 独立 verify PASS、PASS-WITH-RECORDS-FIX 2026-07-16)**。⚠v4 実測 = peak 350 MiB (v2/v3 一致)/RSS 1310 MB/CPU 1.56% (v2/v3 近似一致: 1317.8→1310/1.58→1.56) だが baseline 308/delta 42/window n=9 は v2/v3 (340/10/12) と異なる — §3 の定常 ~8 steps/s と R1 cap 結論 (N=4) は不変。
**⚠ scope**: 本 doc = 実装可能な spec の固定。**実装 (I0) は E0 の後** — E0 fence (pN 定義) と I0 gate は不変。
数値で「E0 pin」と記す項は E0 実測で確定するまで PROVISIONAL。

---

## §1 architecture (D0 裁定の組立)

```
supervisor (CPU-only, R6)
 ├─ launch-time check: nvidia-smi compute-apps @cuda:0 → 先客 k proc ⇒ N_collect = 4−k + loud log (R1-4)
 ├─ collector proc i = 0..N-1  (cuda:0, world_count=1, use_mujoco_cpu=True = proven CPU path)
 │    ├─ derived_seed = SeedSequence([base_seed, process_index, restart_count]) (AMEND-1 統一形、初回 rc=0)
 │    │    → np.random.seed(derived_seed)
 │    ├─ rollout: episode 完走 → tmp 書込 → sha256 → rename = 公開 (R3-1 atomic)
 │    └─ outbox: rollouts/proc_{i}/  (R3-2)
 ├─ trainer (将来 I0+; cuda:2 primary, R1-3) ← async tail-scan (R3-5)
 └─ FAILURE marker / restart 新個体 / K_fail halt (R6)
```

## §2 dir layout + manifest schema (要件 #2 #3)

```
rollouts/
  run_manifest.json            # run 単位: {base_seed, code_sha, launch_ts, N_collect, device_map, protocol_ref}
  proc_{i}/
    proc_meta.json             # R2-2+AMEND-1: {base_seed, process_index, restart_count, derived_seed, pid,
                               #        CUDA_VISIBLE_DEVICES, env_fingerprint, code_sha, start_ts}
    ep_{k:06d}.npz             # episode data (transition arrays、Stage-A :117 schema)
    ep_{k:06d}.manifest.json   # 下表
    FAILURE.json               # R6-1 (crash 時のみ): {last_episode, reason, ts, rc}
```

**episode manifest field 表 (Stage-A :117 の additive 拡張 — ⛔ breaking 禁止、既存 field 改名なし):**
| field | 型 | 由来 |
|---|---|---|
| (既存) o, a_raw, a_executed, r_paid, o′, done, time_out, termination_reason∈{success,timeout,drop,explosion}, invalid_mask | npz 内 array / manifest echo | Stage-A :117 (不変) |
| + process_index, derived_seed, pid | int | R2-2/R3-2 |
| + env_fingerprint_sha, code_sha | str | R3-2 |
| + episode_idx, invalid_any (any(invalid_mask)) | int/bool | R3-2 |
| + source ∈ {online, demo} | str | R3-4 (collector は常に "online"; demo bank 変換器が "demo" を付す) |
| + sha256 (npz の) | str | R3-1 provenance |

隔離保証 (R6-4): 「process i の episode ≥ X を excise」= manifest の (process_index, episode_idx) で機械可能。

## §3 disk budget + rotation (要件 #1、Stage-A :125 の N-process 再見積)

実測基礎 (resource = calibration v4 `fd536235e9`; **timing = E0 v1 実測で更新 [p5 v1.5 批准・PROVISIONAL 条項]**:
定常 ≈ **10.71 RL steps/s/proc** [199-step off-by-one 補正後、N1]、N4 total ≈ 35.78 t/s。E0v2 で最終): init ≈ 80 s/proc
⇒ 〔以下 HISTORICAL/PROVISIONAL — v2-trace 由来の旧導出。E0v2 最終値で一括更新予定〕900-step episode ≈ 113 s ⇒ ~30 ep/h/proc、N=4 で ~120 ep/h。0.5 MB/ep (Stage-A :125) ⇒ ~60 MB/h、24 h ≈ 1.4 GB。
- **rotation 方針: 削除しない**(容量が問題にならない)。retention = run 単位 dir、disk 残量 < 50 GB で supervisor が
  loud warn (削除は人間判断 — 学習データの silent destruction をしない)。
- E0 で steps/s を再実測後、本節の数値を更新 (PROVISIONAL)。

## §4 R5 実装 spec: default flip + tripwire (要件 #4)

1. **flip**: `newton_route_env.py:419` `world_count=4` → `world_count=1`。
2. **tripwire**: `make_solver` (`newton_skill_env_base.py:1302`、`backend=="mujoco"` 分岐・SolverMuJoCo 構築直前):
   ```python
   if use_mujoco_cpu and model.world_count > 1 and os.environ.get("THREAD_ALLOW_CPU_MULTIWORLD") != "1":
       raise RuntimeError(
           "use_mujoco_cpu=True steps ONLY the single-world CPU template -- worlds>0 would be silently frozen "
           "(COMP3_PLAN_ROUTEEXEC_GRASPACT_COORD_20260708.md:79; ENV_MULTIWORLD_SUBSTRATE_CHARTER 2026-07-16). "
           "Use world_count=1 (fork B), or use_mujoco_cpu=False (S8, unvalidated), or set "
           "THREAD_ALLOW_CPU_MULTIWORLD=1 (diagnostics ONLY -- record the use in your artifact)."
       )
   ```
   (raise message = COMP3:79 + charter cite、R5-2 の「診断者がその場で歴史に接地」要件)
3. **検証 leg (R5-4)**:
   - **byte-repro 無変化証明**: flip 前後で canonical byte-repro harness (`test_routeexec_byte_repro.py` 級) が
     byte-identical (全 live caller wc=1 明示ゆえ理論上無変化 — それ自体を検証)。
   - **tripwire 識別性 (両側)**: (i) CPU×wc=4 素起動 → raise (拒否レグ) (ii) CPU×wc=1 → 通る (iii) opt-out=1 ×wc=4 →
     通る + 使用記録規約 (iv) use_mujoco_cpu=False×wc=4 → tripwire 非発火 (S8 経路を塞がない)。
   - 陽性対照 = 既存 multi-world probe 2 本 (E_probe/E1v2) が opt-out 明示で従来どおり動くこと。
4. **L-triage 見立て**: env default 変更 + solver factory logic = **L3** (newton/solver keyword)。gate chain = fork-B node の
   [VERIFY]→[RULE-CHECK]→実装→§運用15。⛔ pin node と分離 (本 node で実装)。
   **I0 [RULE-CHECK] carry (p5 v1.3 助言)**: R2-3 = 裸 np.random を増やさない / DR・per-process 設定は config 経由
   (os.environ 経路 不可) — checklist 項として明示 carry。

## §5 supervisor spec (要件 #5)

- **launch**: run_manifest 書込 → cuda:0 compute-apps check (R1-4、proc 数判定・MiB でない) → N_collect=4−k →
  collector spawn (per-proc `CUDA_VISIBLE_DEVICES=0` 明示)。
- **監視**: collector 非ゼロ exit or FAILURE.json 検出 → **restart = restart_count+=1 ⇒ 新 derived_seed
  (AMEND-1 統一形 SeedSequence([base_seed, process_index, restart_count])) + proc_meta 再記録 = 別個体** (R6-3)。in-flight episode は atomic 設計により outbox に現れない (R6-1、追加処理不要)。
- **halt**: 同一 slot 連続失敗 **K_fail (提案 3、E0 pin)** 超 → run 全体 halt + loud (systemic 欠陥を restart で隠さない)。
- **backpressure**: outbox 未消費 (trainer 不在の E0 では「ディレクトリ内 episode 数」で代用) 高水位 **K (E0 pin)** で
  collector pause + loud log (R3-3)。
- supervisor 自体は GPU を使わない (R1-3)。python + psutil + nvidia-smi 呼び出しのみ。

## §6 relocate lever (R1-3、要件 #4 系)

- run_manifest / launcher config に `device_map = {collector: "cuda:0", trainer: "cuda:2"}` を **config 値**として持つ。
- fallback 形 = `{collector: "cuda:0" (N=3), trainer: "cuda:0"}` — **設計変更なしに config でこの形に落とせる**ことを
  I0 実装の acceptance に含める (lever の実在テスト: 両 config で supervisor が正しく spawn する smoke)。

## §7 E0 registration — v0.3 POST-E0 AMENDMENT 版 (旧 v0.2 表 = 歴史。移管 leg は「元事前登録の PASS」ではない)

**E0(v2) predicate (実測対象、全て errors/exit2 昇格 = fail-loud 完備):**
| 測定 | 定義 (v0.3) | acceptance |
|---|---|---|
| transitions/s | N∈{1,2,4} fresh (v1/calibration 非流用)、**timer = time.monotonic_ns・window = 199 step 厳密** (step30 実行後 start の off-by-one 修正) | 効率 T(N)/(N·T(1)) 報告 |
| contention | per-proc steps/s N=4 vs **N1 基準 = n1 対の平均 (run 前固定、pN 条件 4)** | **≥0.8、<0.8 は errors/exit2** |
| メモリ | GPU MiB (PID 帰属)・RSS ×N 線形 | **非線形 = errors/exit2** |
| 決定論 (R2-4 npy level) | 同 (as-run sha, fingerprint, derived_seed, workload) 2 回 → **trajectory .npy file sha 一致** (v1.5 D-1 批准形) | **hard、 不一致 = exit2** |
| provenance (pN 条件 3/6) | **per-child**: unified env fingerprint 実値・loaded closure+self hash・recording sha・post-run hash・changed_during_run=[] / harness source as-run hash 前後一致 / 分母 in-artifact / rc 全 0 / trajectory nontrivial+finite | 欠落 = errors/exit2 |
| 正対照 (pN 条件 5) | **注入型**: CPU 0-flat injection → detector が非ゼロ exit する自己テスト + dead-PID GPU=0 対照 + missing GPU/RSS/overlap/closure/fingerprint/race = fail-loud | 自己テスト不発 = exit2 |

### §7.1 E0v2 exact bars (run 前固定、pN CONCUR-WITH-FIXES 2026-07-16 21:0x — 後付け判定防止)

1. **memory 線形 (式を一意固定、v1 の 1.25 係数を carry)**: `max(N4 per-proc GPU peak) ≤ 1.25 × max(n1_a, n1_b GPU peak)`
   **AND** `max(N4 per-proc RSS peak) ≤ 1.25 × max(n1_a, n1_b RSS peak)`。いずれか超過 = errors/exit2。
2. **n4 window overlap > 5.0 s** (共通区間)。以下 = errors/exit2。
3. **trajectory 検査**: finite = **全要素** np.isfinite / nontrivial = `max_t |q(t) − q(0)| > 1e-6 m` (全 child)。違反 = errors/exit2。
4. **注入型 CPU-zero 自己テスト**: **別 subprocess** に人工 0-flat CPU 系列を与え、detector が期待どおり exit2 することを
   親が確認 = self-test PASS。⚠ この注入 subprocess の exit2 は【自己テストの成功】であり、**実 run の overall exit を
   FAIL にしない** (self-test 結果 field として分離記録)。self-test 不発 (注入が exit0) = overall errors/exit2。
5. **unified fingerprint = v4 67-key 機構** (explicit core ∪ actual loaded-closure scrape ∪ static scrape) を **per-child 実値**で
   記録。**n1_a と n1_b の fingerprint 値一致 = hard 条件** (不一致 = exit2)。
6. **artifact 追跡**: 全 result/closure/status/traj を bank 対象に列挙。**v1 path (`forkb_e0_runs/`・`forkb_e0_scaling_result.json`)
   は不変更** — v2 は `forkb_e0v2_runs/`・`forkb_e0v2_scaling_result.json`。

**I0 acceptance へ移管 (POST-E0 DESIGN AMENDMENT — RULINGS v1.5 N-1 / v1.6 R2-4-b。E0v2 の PASS 数に数えない):**
| leg | 内容 | 由来 |
|---|---|---|
| K=200 / K_fail=3 機構テスト | 人工消費停止→pause 発火 / 人工 crash→restart→halt chain (supervisor = I0 成果物) | N-1 (binding) |
| episode-npz serialization 決定論 | serializer を **file レベル byte-決定的**に実装 + ⭐**2×2 判別 leg**: 同 seed 再走→sha 一致 × 異 seed→sha 不一致 (異 seed 象限は seed 発現 workload で — FF は inert [N-2]) | v1.6 R2-4-b |
| seed-differentiation 観測 | 上記 2×2 の異 seed 象限 (N-2) | v1.5 N-2 |
| as-run 差分 reconcile | E0 実行時 dirty tree の as-run sha ↔ committed sha 一致確認 (land or inert 宣言) | v1.5 N-3 |

## §8 trainer bring-up contention 観測 leg (要件 #7)

E0 は collector 側 (cuda:0) のみ被覆。**trainer@cuda:2 の VLM 同居 contention は初回 trainer bring-up (I0+) で観測**:
trainer 単独 vs VLM 同居時の (update/s、GPU MiB、cuda:2 compute-apps slot 数) を 1 回計測し、劣化が大なら
relocate lever (§6) の発動判断材料として Rs/pN へ surface。E0 の acceptance には**含めない** (被覆軸が別)。

## §9 gate chain (v0.3)

D1 (本 doc) → E0 実測 v1 `fb36c49540` (p5 設計軸 PASS v1.5 / **pN evidence HOLD**) → **E0v2** (pN 7 条件の full 再走、
新 run tag・v1 artifact 不変更) → **pN 再判定 (N=4 確定/I0 開始はここ)** → **I0** (flip+tripwire+supervisor+collector、
L3 chain; acceptance = 従来分 + §7 移管 leg 4 本 [K/K_fail 機構・R2-4-b 2×2・N-2・N-3] + §8 trainer contention leg)
→ V0 (charter §3.2)。(d) policy-drive trigger の `/reward-design`+`/pre-check` は本 chain と独立に不変。
