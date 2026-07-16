# fork-B D0 設計裁定 (VT-DESIGN p5, 2026-07-16) v1.9

**Node**: `T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild-substrate-forkB`。**Status: D0 = 6/6 CLOSE（design + evidence）** — 裁定 v1.0 R2-R6 `11fdb0bc11` / v1.1 R1 `889ce6b640`［cuda:2 配置 = %12 CONCUR 決着］/ v1.2 要件 #7 `8304500dbd` / v1.3 D1-VERIFY（CONFORM 7/7 + AMEND-1）`9cea41ac67`。**item-1 evidence = v4 `fd536235e9` PASS**（pN 独立 verify、末尾 EVIDENCE-RECORD UPDATE `55086b197b` [record-only、%12 custodial — p5 検証・受理済: 設計文 append-only、peak 一致・RSS/CPU 近似一致 (1317.8→1310/1.58→1.56) ゆえ **R1 の N=4 結論 不変**、v4a narrative=UNVERIFIED 隔離は正]）。**v1.4 = 本 header の evidence-status 同期のみ（owner 実施、設計内容 無変更）**。**E0 status〔record-fix %12、pN 条件〕: 実測完了 `fb36c49540` → p5 E0-VERIFY = PASS（v1.5、⚠設計軸のみ・N=4 確定は この軸限定）／ pN independent verify = **HOLD**（evidence 完全性 B1-B5）→ B1/B2 = v1.6 R2-4-b + N-1 で I0 acceptance へ移管（**post-E0 design amendment**、元 §7 pre-reg PASS ではない）／ B3/B4/B5 = **E0v2 full 再走**（pN scope CONCUR-WITH-CONDITIONS 7 条件）。N=4 確定/I0 開始 = E0v2 全 PASS 後の pN 再判定。** 0-commit（bank = %12）。
**入力**: 素材 = `FORKB_D0_MATERIALS_RSTECHLEAD_20260716.md`（DoD = `RLENV_PIN_DESIGN_VTDESIGN_20260715.md` §21.11.2a、v1.13 `7b4c918251`）。
**範囲**: 全 6 項の裁定 — 項 2/3/4/5/6 = v1.0、項 1 = v1.1 追裁定（当初「実測待ちで保留」〔歴史〕→ **v4 `fd536235e9` PASS で解消済**〔record-fix %12〕）。
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
| 7 | **初回 trainer bring-up 時の contention 観測 leg**（cuda:2、VLM 同居時）— E0 は collector 側/cuda:0 のみで**この軸を覆わない**（%12 提案 2026-07-16、p5 批准） | R1-3/R1-5 被覆 gap |

**保留**: 項 1（N と資源上限）= 1-process 実測 profile 待ち（protocol = pN 6 条件固定済）。実測到着後に N 上限式へ代入して裁定。→ **v1.1 R1 で解消（下記）**。

---

## R1 🔒 項 1 — N と資源上限（v1.1 追裁定、2026-07-16。**evidence of record = v4 `fd536235e9`〔record-fix %12〕**; 裁定時実測 = v2 `e1298c4bf6`〔歴史〕）

**R1-0 実測批准（p5 artifact 自読、⚠v2 時点〔歴史〕。current evidence = v4: peak 350 同値 / baseline 308 / delta 42 / RSS 1310 / CPU 1.56% / n_window=9〔record-fix %12〕）**: 全数値を v2 artifact で確認 — GPU **350 MiB/proc**（PID 帰属 peak、delta 10、baseline 340）/ RSS **1317.8 MB/proc** / CPU **1.58% 正規化 ≈ 1.0 core/proc**（64 core、146 threads は idle pool = 単一 core 支配）/ n_window=12 / `use_mujoco_cpu_observed=true` / workload_exit=0 / after 正対照 dead-pid GPU=0。protocol 準拠（sha `11fdb0bc11` / CVD=0 / wc=1 / window [30,230) / cadence 2s / D0_CALIBRATION_ONLY MARK 明記）。⭐ **v1→v2 の経緯（CPU 計器死を self-check で捕捉 → fail-loud 正対照へ昇格、`_v1_deadcpu.json` 保全）= 「計器が自分の死を検出する」positive-control 教訓の正しい適用と評価。**

**R1-1 上限式の各項（p5 再計算、v2 artifact 分母〔歴史〕— v4 分母で cap 再確認済: 拘束 = ≤4 規則 不変〔record-fix %12〕）**:
| 項 | 計算 | 上限 |
|---|---|---|
| GPU | (49,140 − 2,666 ambient) / 350 | ≈ **132** |
| RSS | 455 GB / 1.32 GB | ≈ **344** |
| CPU | 64 core / ~1.0 core | ≈ **63** |
| **規則** | CLAUDE.md「最大 4 プロセス/GPU」 | **4** ← **唯一の拘束** |

**R1-2 裁定: N_collect = 4 @ cuda:0**（collector = route env、device-fragile cuda:0 ONLY [memory: canonical-route-device-fragile]）。資源 margin = GPU 4×350=1.4 GB ≪ 46.5 GB free / CPU 4×1 ≪ 64 / RSS 4×1.32=5.3 GB ≪ 455 GB — 全次元で規則が先に効く。

**R1-3 配置裁定（trainer/supervisor）**:
- **trainer = cuda:2（primary）** — CLAUDE.md GPU 役割表（cuda:2 = 「VLM + **訓練**」優先 1）に整合。SAC（低次元 obs・6 act）の footprint は小さい見込み（実測は E0/I0）⇒ cuda:2 は **slot 3/4 + 大半の VRAM が vision/WM に残る** = node invariant §5（vision/WM 予約）は「全量温存」でなく「明示予約」で満たす読み。
- ⭐ **relocate lever を config 化（D1 要件に追加）**: trainer device は config 値とし、vision/WM が cuda:2 全量を要する事態では **trainer→cuda:0 + N_collect 4→3** に落とせる形（設計変更でなく config 変更で済むことを D1 が保証）。
- ⚠ **%12 の「cuda:2 温存」見立てとの差分を明示**: 温存 =「全量 untouched」なら Option-2（trainer@cuda:0、N_collect=3）。本裁定は CLAUDE.md 役割表を優先して primary を上記とするが、**ここは %12/pN の co-decide 対象 — 異見あれば返せ**（どちらも成立、lever があるため後から可逆）。
- supervisor（restart/halt/marker、R6）= **CPU-only**（GPU slot 消費ゼロ）。

**R1-4 launch-time 前提 check（機構化）**: N=4 は「cuda:0 に先客 compute proc ゼロ」前提。launcher は起動前に `nvidia-smi --query-compute-apps` を確認し（CLAUDE.md 既存規則の機構化）、**先客 k proc なら N_collect = 4−k に自動減 + loud log**。ambient 2,666 MiB は「メモリ」であって proc slot でない — 判定は compute-apps の proc 数で行う。

**R1-5 E0 への条件付け**: 本 calibration は 1-proc・非流用（MARK どおり、E0 は N=1 も新規再走）。**N=4 は「calibration 上限確定・E0-confirmed で採択確定」の二段** — E0 が (i) N=4 契約: contention による per-proc 劣化（CPU cache/mem BW/GPU）≤ しきい値（E0 事前登録で pin）(ii) R2-4 per-process byte-repro leg (iii) backpressure K / K_fail を pin。

⇒ **D0 = 6/6 項 裁定完了**（R2-R6 banked `11fdb0bc11` + 本 R1）。次 = D1（fork-B spec、%12 起草・p5 verify、引き継ぎ要件 6 項 + R1-3 lever 追加）。

**⚠ scope 注記**: 本裁定は設計固定であり実装認可ではない。実装は fork-B node の gate chain（L3、素材 doc §項 1 protocol・E0/I0 fence 不変）に従う。(d) policy-drive trigger の `/reward-design`+`/pre-check` gate は本 D0 と独立に不変（pin 側 §21.4）。

---

## D1-VERIFY 🔒 spec v0.1 照合 verdict（v1.3、2026-07-16、対象 = `FORKB_D1_SPEC_RSTECHLEAD_20260716.md` `d70fea96ed`）

**方法**: 要件 1-7 を sub-item 単位で spec § と 1:1 照合（行単位 PASS 禁止規律）。input cites（v1.2 `8304500dbd` / calibration `e1298c4bf6`〔verify 時点の artifact = v2 世代〔歴史〕; evidence of record は現在 v4 `fd536235e9`〔record-fix %12〕〕）on-disk 検証済。

### verdict = **CONFORM 7/7** — 修正裁定 1（R2-1 AMEND）+ 批准根拠 1 + 助言 1 を添えて PASS

| 要件 | spec § | 照合結果（sub-item） |
|---|---|---|
| 1 disk budget | §3 | ✅ 再見積の算術一致（8 steps/s→113 s/ep→~30 ep/h/proc→N=4 で 60 MB/h→24h 1.4 GB、p5 再計算一致）。rotation=**削除しない**+<50 GB loud warn+削除は人間判断 = silent-destruction 禁止と整合。PROVISIONAL 明記 ✓（⚠ 8 steps/s は profile summary でなく artifact timestamp からの導出 — E0 再実測明記済ゆえ可） |
| 2 schema | §2 表 | ✅ :117 既存 field 不変+additive 9 field（R3-2 完全一致+source∈{online,demo}=R3-4）+ ⛔breaking 禁止明記 + R6-4 隔離 = (process_index, episode_idx) 機械可能 |
| 3 layout | §2 | ✅ run_manifest/proc_meta（R2-2 全 field）/ep npz+manifest/FAILURE.json。atomic = tmp→sha256→rename（§1、R3-1）|
| 4 flip+tripwire | §4 | ✅ flip :419 / tripwire@make_solver（guard 形・COMP3:79+charter cite・opt-out+使用記録文言）/ 検証 leg = byte-repro 無変化 + **識別性 4 象限**（(iv) S8 経路を塞がない、を含む — 良）+ 陽性対照 = 既存 probe 2 本 / L3 見立て+pin node 分離 ✓ |
| 5 supervisor | §5 | ✅ launch（compute-apps **proc 数**判定=R1-4）/restart=新個体/halt=K_fail/backpressure（E0 代用形明示）/CPU-only。⚠ restart seed 形は下記 AMEND |
| 6 lever+E0 事前登録 | §6/§7 | ✅ lever=config 値+fallback 形+**実在テストを I0 acceptance に**（R1-3 の「config で落とせる保証」そのもの）。E0 表 = N=1 新規再走（非流用）/contention ≥0.8/メモリ線形/決定論 byte-identical **hard**/K 機構テスト+初期 200 ep（≈1.7 h、算術一致）/K_fail=3 注入テスト/**死計器 正対照 standing 化**（v1 教訓の制度化 — 良）|
| 7 trainer contention | §8 | ✅ I0+ bring-up で単独 vs VLM 同居を 1 回計測・lever 発動判断材料として Rs/pN へ surface・**E0 acceptance に含めない**（被覆軸分離が正確）|

### 🔒 修正裁定 AMEND-1: R2-1 の seed key を【3 要素に統一】する

§5 の restart seed = `SeedSequence([base, i, restart_count])` は R6-3「新個体」の自然な決定的導出だが、**R2-1 の字義（2 要素 `[base_seed, i]`）と初回 spawn で食い違う**（`SS([b,i])` ≠ `SS([b,i,0])`）。曖昧なまま実装させない:
⇒ **R2-1 を AMEND: derived_seed = `SeedSequence([base_seed, process_index, restart_count]).generate_state(1)[0]`、初回 = restart_count=0 で統一**（一様な 1 形 > 字義保存。proc_meta に restart_count を記録 field として追加 — additive）。spec §1/§5 はこの統一形で実装。

### 🔒 批准根拠の追記: contention bar ≥0.8 は恣意でない —「N=4 が理想 N=3 を支配する」導出

効率 0.8 × 4 proc = **実効 3.2 > 3.0 =（完全 scaling の）N=3** ⇒ **bar ≥0.8 は「N=4 が N=3 fallback を必ず上回る」break-even+margin の線**。0.75 では理想 N=3 と同点。⇒ ≥0.8 提案を**この導出付きで批准**（E0 で下回れば §7 どおり N=3 再測 = R1-5 二段の設計どおり）。

### 助言（FAIL でない）: I0 rule-check に R2-3 を carry

「env 内に裸 `np.random` を増やさない / DR 供給は config 経由（os.environ 不可、Stage-A :131）」は D1 要件外の standing 規約 — **I0 の [RULE-CHECK] checklist に明示 carry** を推奨（collector/supervisor 新 code が対象になる最初の機会）。

### PROVISIONAL の扱い = 適正

§0/§3/§7 の PROVISIONAL 明記 + pN HOLD → v3/v4 差替え → E0 最終、の三段は records-match-fact に適合。〔**RESOLVED 2026-07-16 19:5x〔record-fix %12〕**: v4 `fd536235e9` = pN 独立 verify PASS。数値 = peak 350 (v2 一致)/RSS 1310/CPU 1.56%（v2 近似一致: 1317.8→1310/1.58→1.56; baseline 308/delta 42/n9 は相違）⇒ **R1 の拘束構造（唯一の拘束=4-proc 規則、margin 30-80×）は不変・再裁定不要**。E0 で最終確認。〕

---

## E0-VERIFY 🔒 事前登録照合 verdict（v1.5、2026-07-16、対象 = `forkb_e0_scaling_result.json` bank `fb36c49540`）

**方法**: artifact 自読（message 数値で裁定しない）+ 全 predicate の p5 再計算。

### verdict = **PASS（全 5 predicate）→ R1-5 二段採択の E0-confirm 成立 = N_collect=4 採択【確定】**
> ⚠〔scope-fix p5 2026-07-16、two-key 整合〕本 PASS/「確定」= **p5 設計軸のみ**。pN independent verify（evidence 完全性）= HOLD B1-B5 → B1/B2 = v1.6 R2-4-b+N-1 で I0 移管（**post-E0 amendment — 元 §7 pre-reg の PASS ではない**、pN `84665ddccc` の規律どおり）/ B3-B5 = **E0v2 full 再走**。⇒ **N=4 最終確定・I0 開始 = E0v2 全 PASS 後の pN 再判定**（header の record-fix と同旨、verdict 行にも刻む）。

| 事前登録（D1 §7） | artifact 実測 | p5 再計算 | 判定 |
|---|---|---|---|
| 決定論 byte-identical（hard） | n1_a vs n1_b（同 seed 2 回）traj sha `f5a32604…` 一致 | sha 同一を目視 | ✅ **PASS**（deviation 下記 D-1）|
| contention ≥0.8 | 0.835 | 8.99/10.764=0.835 ✓。⭐**参照非依存**: n1_b 基準でも 0.815、平均基準 0.825 — 全変種 ≥0.8 | ✅ PASS |
| メモリ線形 | GPU 350 flat ×4 / RSS 1303-1309 flat | per-proc 一定 = 線形 ✓ 超線形なし | ✅ PASS |
| throughput | N1/N2/N4 = 10.764/20.574/35.96 t/s | 和の再計算一致（N2 効率 0.954 / N4 0.835）| ✅ 報告どおり |
| K / K_fail | K=200ep→**1.39h**（実測 rate）/ K_fail=3 数値 pin | 35.96 t/s→143.8 ep/h→200/143.8=1.39 ✓ | ✅ 数値 pin（機構 = 下記 N-1）|

**D-1 逸脱の批准: npz→npy 比較** — zip container の timestamp 非決定は実物の性質。⇒ **R2-4 の byte-repro predicate を【npy payload レベル】と正式化**。系論: R3-2 manifest の `sha256`（npz file）は **identity（同定）であって repro 証明ではない** — 両者を混同しない（記録）。

### 注記 3 件（PASS を変えないが binding/観察）

- **N-1（binding、I0 acceptance へ carry）**: K 機構テスト（人工消費停止→pause 発火）+ K_fail 機構テスト（人工 crash→restart[新個体]→halt chain）は **supervisor が I0 成果物ゆえ E0 では構造的に実行不能** — 繰延は正当。ただし**I0 acceptance の必須 leg として binding**（数値 pin だけで機構未検証のまま運用に入らない）。
- **N-2（事前登録外の観察 = wire-then-validate 級）**: **全 traj sha が process/seed に依らず同一**（n1_a/n1_b/n2×2/n4×4 = 全て `f5a32604…`）。本 workload（FF-replay）は **seed 差を軌道に発現させない** ⇒ E0 は「同 seed → 同 bytes」を実証したが「**異 seed → 異 episode**」（per-process seed 機構が inert でないこと）は**未実証**。⇒ **I0/初回 policy-drive で seed-differentiation を 1 回観測**（INIT_XY_NOISE が live な経路で、異 seed 2 proc の episode が異なることを確認）— appearance-only ≠ working の防止。
- **N-3（evidence→production 連続性）**: E0 は **dirty tree で走った**（git_head `8d64d8d2d1` + as-run 3 env file の未 commit 差分 137/29 行、**as_run sha256 で pin 済 = 開示適正**）。⇒ E0 数値を「production env の数値」として cite する前に、**I0 で as-run 差分を land するか inert 宣言する**（as-run sha と committed sha の一致確認を I0 verify に含める）。

**付帯批准**: D1 §3 timing（v2 trace 由来 ~8 t/s）→ **実測 10.764 t/s へ更新** = PROVISIONAL 条項どおり（disk budget 再計算: 143.8 ep/h ×0.5MB ≈ 72 MB/h、rotation 方針に影響なし）。

### 🔒 R2-4-b（v1.6 追加裁定、%12 要請 = pN HOLD B1 への回答）: **episode-npz serialization determinism = I0 acceptance 必須 leg（ADOPT）+ serializer は【byte-決定的】に作る**

**要請の妥当性**: 私の D-1 npy 正式化は **E0 の計器レベル**（probe の traj 比較）を覆ったが、**production episode file（`ep_*.npz`、R3-1 の serializer が書く）は I0 成果物** — その byte 安定性は R2-4/D-1 の**外に残っていた**。B1 は真の gap。N-1 と対称（機構が I0 にしか存在しない ⇒ acceptance leg も I0）。

**裁定**:
1. **serializer 要件（design）**: I0 の episode serializer は **file レベルで byte-決定的**に作る — 同 (code sha, fingerprint, derived_seed, workload) ⇒ `ep_*.npz` が **container 込みで byte-identical**（実装手段 [zip date_time 固定 / `np.lib.format` 直書き等] は %12 自由）。⇒ **系論: R3-2 manifest の `sha256` が「identity のみ」から【identity + repro 比較可能】へ昇格**（D-1 の caveat は「非硬化 writer の generic npz」にのみ残る）。運用利得 = repro 検証が sha 比較 1 発（payload 抽出不要）。
2. **I0 acceptance 必須 leg（binding、N-1 と同格）**: ⭐ **N-2 と統合した 2×2 判別テスト**で張る —
   | | 同 derived_seed 再走 | 異 derived_seed |
   |---|---|---|
   | **期待** | file sha **一致**（serialization determinism = B1）| file sha **不一致**（seed-differentiation = N-2、episode 内容が実際に異なることの実証）|
   両象限が期待どおりで初めて PASS — 「同」だけなら inert-seed でも通り、「異」だけなら非決定 serializer でも通る。**2×2 が両故障 mode を同時に判別する**（判別できないテストはテストでない、の適用）。⚠ 異 seed 象限は **seed が軌道に発現する workload**（policy-drive / noise-live 経路）で実施（N-2 の FF-inert 所見どおり FF では不成立）。
3. ⇒ **B1 = 本裁定で closed**（pN 同意見の確認は %12 経由でそのまま進めてよい）。B3/B4/B5 の E0v2 補完 run 搭載 = 了解（裁定要請なし、到着時に verify）。

---

## E0v2-VERIFY 🔒 照合 verdict（v1.7、2026-07-16、対象 = `forkb_e0v2_scaling_result.json` bank `945a5c229a`、bar = D1 v0.3 §7/§7.1〔run 前固定 `3a14e38c17`〕）

**方法**: bar を先に自読（v0.3 §7/§7.1）→ artifact 自読 → 全 predicate + 全 exact bar を p5 再計算。

### verdict = **PASS〔p5 設計軸〕— 全 pinned predicate + §7.1 exact bars 6 本、再計算一致。最終確定 = pN 再判定（並行中）を待つ。**

| bar（§7/§7.1、run 前固定） | artifact | p5 再計算 | 判定 |
|---|---|---|---|
| 決定論 traj npy sha（hard） | TRUE | n1_a `f5a32604…` == n1_b ✓ | ✅ |
| fingerprint n1 対一致（hard、67-key per-child 実値） | TRUE | 67-key dict 完全一致 ✓ | ✅ |
| contention ≥0.8（**基準 = n1 対平均、run 前固定** — v1 の参照依存懸念を制度で解消） | 0.815 | 8.872/10.886=0.815 ✓ | ✅ |
| §7.1-1 memory 式 bar（1.25 係数 carry） | PASS | GPU 350≤437.5 ✓ / RSS 1306.4≤1632.1 ✓ | ✅ |
| §7.1-2 overlap > 5.0s | 22.3 | ✓ | ✅ |
| §7.1-3 traj finite（全要素）+ nontrivial（>1e-6m）全 child | TRUE | 8/8 child ✓ | ✅ |
| §7.1-4 注入型 CPU-zero 自己テスト（別 subprocess、実 run exit と分離） | PASS | field 分離記録 ✓ | ✅ |
| §7.1-5/provenance | — | per-child {derived_seed, CVD, pid, closure at-load, recording sha, fingerprint} + `changed_during_run=[]`（at-load==post-run の実体）+ harness self-sha pre==post + rcs 全 0 | ✅ |
| throughput | N1 対平均 10.886 / T2 20.503 / T4 35.488 | 全て和・比の再計算一致（eff2=0.942 / eff4=0.815）/ K=200ep→1.41h ✓ | ✅ 報告どおり |

**所見**: (i) 全 traj sha 単一 = v1 と同じ FF-inert（既知、N-2 は I0 移管済 — 新事実でない）。(ii) v0.3 §7.1 の「後付け判定防止」（bar の run 前固定 + 移管 leg を PASS 数に数えない）は `84665ddccc` 規律の正しい制度化。(iii) timer monotonic_ns + window 199 厳密化（off-by-one 修正）で v1 数値との微差（10.764→10.886 等）は計器改善由来と読める — 拘束・結論に影響なし。

⇒ **p5 設計軸 = E0v2 PASS。N=4 最終確定・I0 開始 gate = pN 再判定の完了**（two-key、私の軸はこれで閉、over-close しない）。I0 acceptance 積み残し（binding）= N-1 機構 2 本 / R2-4-b 2×2 / N-2 異 seed 象限 / N-3 as-run reconcile — v0.3 移管表に fold 済を確認。

**追記（E0v2a spot-check、2026-07-16、bank `2933fa7bbc`、任意 verify）**: pN B6/B7 対応の full fresh 再走を **整合 spot-check**（全再照合は pN 軸と重複ゆえ実施せず）— 数値再計算一致（対平均 10.872 / T4 35.579 / contention 0.818、v2 と noise 内整合）/ **B6 = `dead_pid_control {gpu_mib_attributed: 0, PASS}`** / **B7 = per-child post bracket（4 child）+ `changed_during_run_union=[]`** — ⚠ top-level `changed_during_run=None` は**旧 field の空置でなく per-child 形への移設**（union が「走って空」を証す — 死計器でないことを確認済）/ rcs 全 0。**v1.7 verdict は不変で有効。**

---

## EVIDENCE-RECORD UPDATE (record-only、%12 custodial per OPS-SUP PASS-WITH-RECORDS-FIX 2026-07-16 19:5x。設計内容 無変更・p5 通知済)

- **item-1 evidence = 独立 verify PASS** (OPS-SUP-CODEX、v4 再々 verify): evidence artifact = **calibration v4 `fd536235e9`**
  (blob sha256 `8d07643b…294dad`、closure 9/9・at-load==post-run・changed_during_run=[]・fingerprint 67 key・
  recording sha=banked golden lineage 一致)。R1-0 の evidence 指示は v2/v3 系譜から **v4 へ supersede**。
- ⚠ **精度記録 (pN 指示)**: v4 は v2/v3 と「完全同値」ではない — **baseline 308 MiB / delta 42 / window n=9**
  (v2/v3: baseline 340/delta 10/n=12)。peak 350 MiB は一致、RSS 1310 MB / CPU mean 1.56% は近似一致 (v2/v3: 1317.8 MB / 1.58%) で **R1 の cap 結論 (N=4) 不変**。
- ⚠ v4a crash 捕捉の主張 (「fail-loud が phantom __file__ を実捕捉」) = **narrative-only UNVERIFIED** (crash artifact 未保全、
  非 blocker)。
- ⇒ **D0 = 6/6 CLOSE (design + evidence)**。E0 = D1 事前登録 (K=200/K_fail=3/contention≥0.8/決定論/memory gate) に従い
  fresh N=1 から開始可 (v4 非流用)。

---

## N-2-RESOLUTION 🔒 seed-differentiation 移管 leg の解決先 裁定（v1.8、2026-07-16、%12 I0-b L4 照会への回答。入力 = `I0B_BUILD_RSTECHLEAD_20260716.md` OUTCOME L4 + `forkb_i0b_legs_result.json` + `forkb_i0b_runs/l4_*`）

### 0. L4 の扱い = 批准
- **事前登録どおり FAIL を record して escalate（bar 後付け変更なし）= 正**。infra 無罪（L2 = 4 restart 個体の derived_seed 全相異を provenance で実証 — seed の導出・搬送・記録は働いている）も批准。
- **同 seed 象限 PASS の主張範囲を確定**: 実証されたのは **serializer の file-level byte 決定論（B1、`c3cc1791f776…`）+ pipeline/physics 決定論**。⚠ live channel 不在下では 2×2 が 1 軸に退化しており、「同 seed 一致」は seed-plumbing の正しさを**追加証明しない**（それは L2 が担う）。**B1 = PROVEN のまま。**

### 1. 測定の by-construction 説明（設計事実、なぜ ik_chord でも inert か）
zero-residual scripted 収集 + DR OFF の env には **設計上 seed→data channel が存在しない**。唯一の RNG 消費 = INIT_XY_NOISE（`_reset_worlds` reset 時 draw）だが、その書込先 `_ee_target_*` は **毎 step route の絶対 base target で上書きされる**（`_apply_actions_batch`: `target = route_targets + residual` → `_ee_target_*[w] = target.copy()`）⇒ **draw されるが記録系に到達しない**（%12 診断と一致）。⇒ 🔒 **教訓形: 「RNG が draw される」≠「RNG が出力に到達する」— 消費は因果でない**（L4 事前登録の期待「INIT_XY_NOISE で seed 発現」はこの前提誤りで、正直な FAIL 記録がそれを捕まえた = 事前登録の存在価値の実演）。

### 2. 🔒 裁定 = **N-2 を【channel-conditioned standing acceptance rule】に転換**（(a)単独でも (b) 単独でもない）
一回性の leg（どの日に閉じるか）ではなく、**規則**として置く:
> **「per-process seed を消費すべき channel が live になる度、その channel の bring-up acceptance に『異 seed → 異 output』判別 leg を含める」**

| instance | 時期 | gate |
|---|---|---|
| **(i) policy stochasticity（第一解決点）** | trainer/(d) bring-up（SAC sampling が本来の exploration 熵源） | trainer chain 内（追加 Rs gate 不要）— **これが N-2 の primary 解決点** |
| **(ii) DR `CABLE_XY_OFFSET` wiring** | Stage-A §6.1 config が **Rs により ON** になった時 | ⛔ **N-2 を閉じるために DR を ON にしない**（ON は訓練設計上の Rs 専権判断 — テスト都合で系を変えるのは instrument-for-the-test） |
| (iii) 将来の任意 noise channel | 各 bring-up | 同規則 |

**却下**: 人工 entropy channel の追加（テストを通すための fake diversity）。**I0-b fence = infra 述語のみで進行 = 正**（本 carry は fence を block しない）。

### 3. ⛔ 派生 flag: INIT_XY_NOISE = 【appearance-only knob】と記録
実測（FF + ik_chord 両 mode）で episode content に不達 ⇒ **どの training-data 多様性主張にも INIT_XY_NOISE を数えない**（appearance-only ≠ working）。処置（実効化 wire / inert 文書化 / 削除）は **(d)/trainer bring-up 設計の小項目**として carry（今は触らない — 触るのも env 変更 = gate 対象）。

---

## B4-DISPOSITION 🔒 termination_reason schema 裁定（v1.9、2026-07-16、%12 照会 = pN I0-b HOLD B4。p5 spot: env grep = taxonomy ゼロ実在確認 + manifest 実物 `""`+`truncated_by` 視認）

### 一行 disposition: **(a) ADOPT** — `termination_reason` は env taxonomy（W1 B3b+ 成果物）着地まで `""` 許容〔意味 =「**未測定**」、「無終端」ではない〕+ `truncated_by ∈ {workload_step_budget, env_done, supervisor_stop}` を additive 批准。**(b) 却下・(c) 却下。**

### 根拠と 4 pin（binding）
- **(b) 却下 = 軸混同**: Stage-A `:117` の enum {success,timeout,drop,explosion} は **task-semantic 軸**（何が起きたか）。`infra_truncation` は**記録停止事由の軸**（なぜ記録が止まったか）— 別軸を同じ enum に足すのは category error（境界/同一性 lesson 族）。両軸は **2 field で分離**が正: `termination_reason`（semantic、未測定なら `""`）× `truncated_by`（infra、常に truthful）。**(c) 却下** = Stage-A core への breaking。**timeout 偽記 = 不可**（prohibited.md timeouts 汚染禁止 — %12 の前提どおり）。
- **pin-1（consumer guard、trainer-ingest spec に binding）**: 学習側の終端意味論（bootstrap 判断等）は **done/time_out arrays + truncated_by のみに乗せる** — `termination_reason` が `""` であり得る間、これに分岐する consumer は **fail-loud**（`""` を黙って解釈しない）。⛔ `truncated_by` の値を time_out/termination_reason へ写像しない（step-budget 打切りの bootstrap 扱いは **trainer-ingest 設計時の明示裁定項目**とする — 今決めない、偽らない）。
- **pin-2（無遡及）**: taxonomy 着地後も既存 `""` episode は `""` のまま（**backfill 禁止** — 「未測定だった」が歴史の真実。records-must-match-fact）。着地後の collector は前方のみ実測値を記録。
- **pin-3（enum 不変）**: Stage-A `:117` enum は**測定値の contract として不変** — 本裁定は enum の変更でなく「未測定 sentinel の interim 許容」。⚠ **Rs-approved spec（Stage-A W0-a）に対する interim 逸脱ゆえ、LEDGER 行に loud 記載（p6 chain）— Rs はいつでも veto 可**（黙って運用しない）。
- **pin-4（着地条件）**: 本許容の失効 = W1 B3b+ の env termination taxonomy 着地 + collector 配線 +（その時の）schema 再 verify。それまで manifest の `sec_S_exposure` 型の宣言 field 方式（今回実物で視認 — §S 規則の per-manifest 実装 = 良）を維持。

⇒ %12: minimal collector schema rerun は本 disposition どおりで進めてよい。
