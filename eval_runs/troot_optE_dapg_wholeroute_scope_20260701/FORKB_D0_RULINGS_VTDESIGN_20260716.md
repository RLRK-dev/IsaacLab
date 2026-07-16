# fork-B D0 設計裁定 (VT-DESIGN p5, 2026-07-16) v1.0

**Node**: `T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild-substrate-forkB`。**Status: DRAFT — %12 verify 待ち。0-commit（bank = %12）。**
**入力**: 素材 = `FORKB_D0_MATERIALS_RSTECHLEAD_20260716.md`（DoD = `RLENV_PIN_DESIGN_VTDESIGN_20260715.md` §21.11.2a、v1.13 `7b4c918251`）。
**範囲**: 項 2/3/4/5/6 の裁定（素材 ✅ 分）。項 1（N sizing）= 実測待ちで**保留**。
**接地検証（p5 自読、2026-07-16）**: 項2 `newton_route_env.py:1047-1049`（裸 `np.random.uniform`、行 drift 訂正を確認）/ 項3 `TRAINER_NODE_DEFINE...0712.md:7`（RLPD 条項逐語）+ `:30`（SAC/TD3/replay=ZERO 逐語）/ 項4 `STAGEA_...0712.md:117/:125/:131`（schema・disk budget・os.environ 規約 逐語）/ 項5 `newton_route_env.py:419`（default=4）+ caller grep（wc=1 明示を裏書き、wc=NW は E_probe のみ=意図的）。

---

## R2 🔒 項 2 — seed / 決定論

1. **R2-1 per-process seed 規約**: process i の derived seed = `np.random.SeedSequence([base_seed, process_index]).generate_state(1)[0]` → process 起動時に `np.random.seed(derived_seed_i)`（**global legacy RNG を per-process に明示 seed する** — 現状 env 側 seed ゼロ = 非再現、seed 化は純改善）。⚠ **base_seed + i の素朴加算は不採用**（stream 相関回避、SeedSequence が標準解）。RNG 機構の Generator 移行は **D0 外**（消費者が 1 箇所の今やる理由がない、E0 re-baseline を汚さない）。
2. **R2-2 記録**: per-process artifact に `{base_seed, process_index, derived_seed, pid, CUDA_VISIBLE_DEVICES, 60-key env-fingerprint, code sha}` を必ず格納（素材 (c) 案を批准。E0 acceptance の provenance と同族）。
3. **R2-3 裸 RNG 禁止規約（前方）**: env 4 file 内の裸 `np.random` は現 1 箇所（`:1047-1049`）から**増やさない**。将来 DR sampling は Stage-A `:131` どおり **config 経由 per-world 配列 → fork B では per-process config**（os.environ 経路は per-process でも規約として不可 — R4-3 と同一）。
4. **R2-4 byte-repro leg**: 「同 (code sha, env-fingerprint, derived_seed_i, workload) ⇒ per-process byte-identical」を **E0 acceptance に含める**（D0 は規約固定のみ、検証は E0。fork B の主要な得 = CPU substrate byte-repro 温存、の実証形）。

## R3 🔒 項 3 — rollout IPC（trainer 未建造 ⇒ 界面 = 本裁定が contract を固定、実装形は共同設計）

1. **R3-1 搬送単位 = episode 単位 npz、atomic write（tmp → rename）**。根拠: env は CPU-step で episode 生成が遅い（IPC は bottleneck でない）/ crash 時に部分 episode が構造的に生まれない（rename 前 = 存在しない）/ sha per file = provenance native / 項 6 の隔離単位と一致。chunk/stream/共有メモリは premature（E0 実測で必要になったら D1 で再裁定）。
2. **R3-2 配置と schema**: per-process outbox `rollouts/proc_{i}/` + manifest 行 = **Stage-A `:117` transition schema（termination_reason∈{success,timeout,drop,explosion} + invalid_mask）を additive 拡張**した `{process_index, derived_seed, pid, env_fingerprint_sha, code_sha, episode_idx, termination_reason, invalid_any, sha256}`。⛔ **breaking 変更禁止 — 拡張は additive のみ**（R4-2 と同一）。
3. **R3-3 backpressure**: outbox 未消費高水位 K episodes で env pause + loud log（黙って書き続けない/黙って捨てない）。**K の数値は E0/I0 実測後に pin**（D0 は機構のみ）。
4. **R3-4 demo/online 50/50（RLPD 条項 define:7）**: collector は **online のみ**書く。50/50 は trainer 側 sampling で実現。demo は既存 demo bank から — schema の出自 tag で demo/online が**構造的に区別可能**であること（tag に source∈{demo, online} 相当を含める）。
5. **R3-5 trainer ingest**: async tail-scan（watch/poll）。**contract = file format + manifest + dir layout のみ本裁定で固定** — trainer 内部（buffer 実装・UTD・sampling）は trainer node の設計自由度として残す（共同設計の分界線）。

## R4 🔒 項 4 — Stage-A reconcile

1. **R4-1**: 素材の line-anchored 表（`:76/:117/:125/:131/:142/:144/:324`）に基づき「**矛盾なし・退化+換算で reconcile 可**」を**批准**。wc=1 退化形で契約保持（world_ids 恒等 / per-world→単世界）、process 軸は新設の process 管理層が担う。
2. **R4-2 re-pin 2 件 = D1（fork-B spec）の必須項目**: (i) `:125` disk budget を N-process 形で再見積（rotation/retention 込み、N は項 1 確定後）(ii) `:117` schema の process 出自 tag **additive** 拡張（R3-2 の形）。
3. **R4-3**: `:131` 規約（os.environ 経路不可 → config 経由）を per-process にそのまま適用（R2-3 と同一の規約、二重掲示）。

## R5 🔒 項 5 — R-b tripwire 着地 + env default

1. **R5-1 裁定 = 【併用】: default flip（4→1）AND tripwire raise**。
   - flip の根拠: 全 live caller が wc=1 明示（互換リスク実測ほぼゼロ、素材 grep + p5 裏書き）+ **default は「動く構成」であるべき** — tripwire 単独だと素の `NewtonRouteEnv()` が即 raise = default が地雷のまま（「正しい既定」と「誤要求の拒否」は別の防御層）。
   - tripwire の根拠: flip 単独では「明示的に wc>1 を CPU で要求する誤構成」を塞げない（R-b の本来対象、charter §4-B）。
2. **R5-2 tripwire 着地点 = `make_solver`**（`newton_skill_env_base.py:1302`、`backend=="mujoco"` 分岐内・SolverMuJoCo 構築直前）。env init でなく solver factory に置く理由: **use_mujoco_cpu と world_count の両方が見える最後の共通点**であり、env 以外の caller（probe/test/将来 harness）も必ず通る。raise message に COMP3:79 + charter を cite（診断者がその場で歴史に接地できる形）。
3. **R5-3 opt-out**: `THREAD_ALLOW_CPU_MULTIWORLD=1` を批准（診断専用・既定 raise・**使用時は artifact に使用の旨を明記する規約**）。%12 の multi-world probe 2 本（意図的 wc=4）は opt-out 明示で正当に通る。
4. **R5-4 実装 scope**: flip + tripwire とも **fork-B node で実装**（pin node 不可、§21.11.3 のまま）。flip は挙動変更ゆえ通常の検証 chain（byte-repro: 全 live caller wc=1 明示ゆえ理論上無変化 — それ自体を検証 leg に）。

## R6 🔒 項 6 — process 故障 / NaN 方針

1. **R6-1 fail-loud per-process**: crash/NaN で episode を完走できない場合、**outbox には何も現れない**（R3-1 の atomic 設計が in-flight discard を構造で与える — 検査後 rename のみが公開）+ process は FAILURE marker（最終 episode 情報 + 理由）を書いて非ゼロ exit + loud log。⛔ silent restart 禁止（素材 %12 案を批准）。
2. **R6-2 NaN の 2 層を区別**: (i) **episode 内 explosion 等** = Stage-A `:117` invalid_mask の既定機構（episode は完走・mask 付きで出す — 既存規約、変更なし。⚠ prohibited.md: timeouts 汚染禁止は不変）/ (ii) **episode を完走できない process 死** = R6-1（no file + marker）。
3. **R6-3 restart 規約**: supervisor が**新 derived_seed + fingerprint 再記録**で「別 process 個体」として起動（素材案批准 = 履歴分離）。**同一 process slot の連続失敗カウンタ K_fail 超で run 全体 halt**（提案 K_fail=3、E0 で pin）— 「3 回失敗したら方針を疑え」の process 版。restart で systemic 欠陥を隠さない。
4. **R6-4 事後隔離の粒度保証**: 出自 tag（R3-2）により「process i の episode ≥ X を excise」が後日可能であること（buffer 汚染の遡及対処が構造的に可能 = provenance の存在理由）。

---

## D1（fork-B spec、%12 起草・p5 verify）への引き継ぎ要件

| # | 要件 | 由来 |
|---|---|---|
| 1 | disk budget 再見積（rotation/retention、N 確定後） | R4-2(i) |
| 2 | schema additive 拡張の具体 field 表 | R3-2/R4-2(ii) |
| 3 | outbox/manifest/dir layout の正確な形 | R3-1/R3-2 |
| 4 | flip+tripwire の実装と検証 leg（byte-repro 無変化証明） | R5 |
| 5 | supervisor（restart/halt/marker）の仕様 | R6 |
| 6 | E0 で pin する数値: **N**（項 1 実測後）/ **backpressure K**（R3-3）/ **K_fail**（R6-3）/ per-process byte-repro leg（R2-4） | 各項 |

**保留**: 項 1（N と資源上限）= 1-process 実測 profile 待ち（protocol = pN 6 条件固定済）。実測到着後に N 上限式へ代入して裁定。

**⚠ scope 注記**: 本裁定は設計固定であり実装認可ではない。実装は fork-B node の gate chain（L3、素材 doc §項 1 protocol・E0/I0 fence 不変）に従う。(d) policy-drive trigger の `/reward-design`+`/pre-check` gate は本 D0 と独立に不変（pin 側 §21.4）。
