# I0-b build record — fork-B collector + supervisor + mechanism legs (RS-TECH-LEAD %12)

**Written**: 2026-07-16 21:53 JST (date-THEN-write).
**Node**: `T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild-substrate-forkB` (IN_PROGRESS, phase = I0-b infra GO, state.md `2cfc58731d`).
**Fence**: I0-a = CLOSE (pN PASS-WITH-CARRY), I0-b = OPEN GO (`00-DESIGN-STATUS-LEDGER.md:58`, commit `3669b370d3`).
**Governing spec**: `FORKB_D1_SPEC_RSTECHLEAD_20260716.md` v0.3 (§1 architecture / §2 layout+manifest / §3 disk / §5 supervisor / §6 lever / §7 移管 legs / §9 chain) + D0 rulings `FORKB_D0_RULINGS_VTDESIGN_20260716.md` (R1-R6) + charter §3.2 + Stage-A `STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md:117` (schema, additive-only).
**L**: L3 (D1 §4; stage1 output in session). **DESIGN-GATE**: N/A — env/reward/success-condition は 0 diff(本 chunk は消費側 infra のみ; (d) policy-drive trigger は対象外・独立 gate 背後 D1 §9)。

## §S exposure declaration (binding carry, I0A_SCOPE_MANIFEST AMENDMENT 1 = `I0A_SCOPE_MANIFEST_RSTECHLEAD_20260716.md:36-45` + `ad0bb76460`)

HEAD の FM3/FM4 tighten コードは live かつ **未批准** (owner chain = /reward-design 再走 → p5 再verify → /pre-check 未完)。よって本 chunk の全 run について:
- 収集 episode の `r_paid` / done / seat・latch 系の意味論は **banked correctness として扱わない** (claims = infra-only: files/sha/restart/pause/spawn/determinism)。
- 全 run artifact (run_manifest / proc_meta / legs result) に `sec_S_exposure` field を機械的に埋め込む。
- 本 chunk は reward-valid / training-ready を **主張しない**。

## Prior-art guard disposition (V7, run 2026-07-16 21:3x)

`check_thread_vault_prior_art.sh --fail-on-blocker forkb collector supervisor process-parallel` → BLOCKER_CONTEXT_FOUND: match = `eval_runs/r2a_track_a_s1b_collector_supervisor_v2_*` (2026-05-28)。**同一 failed path ではない**: S1B (prismatic finger 静的検証 tooling の "supervisor schema" = ラベル検証スキーマ、LEDGER:41 で substrate-walled ABANDONED) と本件 (N-process rollout 収集 infra) は語彙衝突のみ。続行根拠 = node state.md §2 の disposition (Rs 新規裁定「fork Bで進めて」+ concrete delta) + 本日の Rs「A」(I0-b 着手指示)。

## Deliverables (all named by the banked D1 spec — 新規ファイルはタスク指示・spec 由来)

| file | D1 anchor |
|---|---|
| `thread_isaac_lab/scripts/forkb_collector.py` (前セッション起草 → 本セッション finalize) | §1/§2/§3 (R2-1/R2-2/R2-4-b/R3-1/R3-2/R3-3/R6-1) |
| `thread_isaac_lab/scripts/forkb_supervisor.py` (NEW) | §1/§5/§6 (R1-3/R1-4/R6-3, halt, lever) |
| `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/forkb_i0b_legs.py` + `forkb_i0b_legs_result.json` + `forkb_i0b_runs/` | §7 移管 legs (N-1/R2-4-b/N-2/N-3) |
| 本 doc | 記録 |

## [VERIFY] adversarial self-review (CC1; sub-agent debate は 07-15/16 infra 劣化 precedent により fallback — I0-a と同形。独立 verify leg = pN, state.md §4)

**Failure scenarios found in the draft (fixed in the finalized collector):**
1. ⭐ **Restart-path silent overwrite (data destruction)**: draft は ep counter を 0 起点固定 → restart 個体が `ep_000000.npz` を `os.replace` で**既公開 episode に上書き**する。Fix = 起動時に outbox を scan し **max 既存 index + 1 から採番** (resume-safe numbering)。R6-4 隔離 (episode→個体の機械 mapping) も既公開分が保全されて初めて成立する。
2. **proc_meta 上書きで個体 provenance 消失**: restart 個体が `proc_meta.json` を上書き → 旧個体の identity が消える。Fix = current (`proc_meta.json`) + append-only per-individual copy (`proc_meta.rc{NNN}.json`)。episode manifest は各自 derived_seed を持つので episode 帰属は独立に生存 (両建て)。
3. **Stage-A schema 欠落**: draft は `o′` / `time_out` を持たない (Stage-A :117 core は o, a_raw, a_executed, r_paid, **o′**, done, **time_out**, termination_reason, invalid_mask)。Fix = SARS 整列 (o[t]=step 前 obs [reset obs 起点], o′[t]=step 後 obs) + time_out array。
4. **termination_reason の捏造リスク**: env に termination_reason は**存在しない** (grep 空、2026-07-16 実測) — Stage-A の taxonomy は W1 trainer-env build (B3b+) の成果物。draft の「timeout」既定は workload 打切りを env-timeout と**偽る** (かつ timeouts 汚染規律に接触する語彙)。Fix = `termination_reason: ""` (taxonomy 未実装を正直に) + additive field `truncated_by ∈ {workload_step_budget, env_done, supervisor_stop}`。**deviation として宣言** (additive、breaking なし — 既存 field の改名・意味変更ゼロ)。
5. **test hook の os.environ 経路**: D1 §4 carry (R2-3: per-process 設定は config 経由、os.environ 不可) に draft の `THREAD_TEST_CRASH_AFTER` env hook が抵触 → **CLI `--test-crash-after` へ変更** (supervisor は指定 slot のみに転送)。
6. **manifest/npz publish の crash window**: manifest 書込 → npz rename (commit point) の間で crash すると orphan manifest が残る。契約 = 「episode 存在 ⟺ npz 存在。npz 無き manifest は in-flight ゴミ、consumer は無視」を明文化 (rename = 唯一の公開点、R3-1 保存)。
7. **THREAD 固有条件照合**: dual-arm/cable 前提は不変 (env 消費のみ)。PhysX/Newton 混同なし (env7 mujoco CPU path、`/home/rlrk/env_isaaclab7/bin/python` 実行)。N-dependency: collector は world_count=1 固定 (tripwire が誤構成を拒否 — I0-a 検証済 4分岐)。GPU 規則: cuda:0 ≤4 proc (supervisor R1-4 が launch-time 検査; 実測 21:53 k=0)。
8. **K_fail 「超」解釈**: D1 §5 逐語「連続失敗 K_fail 超 → halt」→ halt 条件 = `failures > K_fail` (K_fail=3 なら 4 回目連続失敗で halt、restart 上限 3)。**spec-literal を採用** (p5 CONFORM 済文言に従う; 別解釈は自己導出になるため取らない)。連続 = rc==0 完走でのみ reset。
9. **視覚レグ (mandatory-or-justified)**: 本 chunk の RESULT は infra 述語 (file/sha/restart/pause/spawn) のみで、motion の物理妥当性を一切主張しない (§S が semantic claim を明示的に禁止)。E0 (同 workload) も数値+evidence verify で CLOSE した precedent。→ **視覚レグ省略を宣言 (justified, loud)**。motion 妥当性の claim が入る時点 (policy-drive / W1) で復活。

**層5 3-lens (L3) を本 doc で実施**: (i) 物理忠実 lens = proven CPU path を cfg ごと E0 から不変で消費、env 0 diff / (ii) 決定論・provenance lens = R2/R3 全条項の実装 mapping (下表) / (iii) SSOT 整合 lens = D1 §2 field 対称差 = additive 3 field (`truncated_by`, `drive_mode`, `sec_S_exposure`) のみ、既存 field 欠落ゼロ (OUTCOME で再掲)。

## Mechanism legs — **pre-registered predicates** (I0-a B1 practice: run 前固定。runner = `forkb_i0b_legs.py`, runs = `forkb_i0b_runs/`)

| leg | 操作 | PASS predicate (事前固定) |
|---|---|---|
| **L1a K-pause @ pinned K=200** (N-1) | outbox に人工 backlog 200 npz を事前配置 (人工消費停止の双対; leg artifact に明記) → collector `--episodes 1` | (a) BACKPRESSURE log 出現 (b) backlog≥K の間 新規 publish ゼロ (≥15 s 観測) (c) 1 件 ack (`.consumed`) 後に publish 再開 (d) rc=0。採番 = 既存 max+1 (=`ep_000200`) |
| **L1b K-pause organic** (N-1) | 空 outbox、`--backpressure-k 2 --episodes 3` | 2 本公開後 pause log、≥15 s 3 本目なし → ack 1 → 3 本目公開 → rc=0 |
| **L2 K_fail restart-halt chain** (N-1) | supervisor N=1、`--test-crash-slot 0 --test-crash-after 1 --k-fail 3 --episodes 5` | 個体 rc0..rc3 の 4 個体 (crash×4、restart×3) → **HALT** (`HALT.json` + supervisor exit 2)。4 個体の derived_seed 全て相異 (R6-3 新個体) + `proc_meta.rc000..003.json` 実在 + `ep_000000..000003.npz` 4 本 (上書きゼロ = 採番 fix の positive control) |
| **L3 lever smoke** (§6) | supervisor `--device-map default --n-collect 1 --episodes 1` / `--device-map fallback --n-collect 3 --episodes 1` | default: run_manifest.device_map = {collector cuda:0, trainer cuda:2}、child CVD=0、rc=0 / fallback: trainer=cuda:0・N=3 (cap) で 3 child spawn、rc=0。**設計変更なしに config だけで両形が立つ** |
| **L4 R2-4-b 2×2** (+N-2) | ik_chord・120 step・1 ep: A(seed S) / B(seed S, fresh outbox) / C(seed S′) | **同 seed 象限**: sha(ep_A) == sha(ep_B) (file レベル byte 決定論) / **異 seed 象限**: sha(ep_C) != sha(ep_A) (seed 発現; INIT_XY_NOISE=±5mm が reset で global RNG を消費 `newton_route_env.py:1054-1055`)。FF 異 seed 象限 = banked N-2 (inert) を cite、再走しない。C==A なら **leg FAIL → escalate** (ごまかさない) |
| **L5 N-3 as-run reconcile** | E0v2a n1 個体の closure sha (as-run) ↔ HEAD blob sha 照合 | 各 file: 一致 = landed / 不一致 = 既知 commit (I0-a flip `c60d311f96` 等) で説明 + I0-a byte-identical leg cite / 残差 unexplained >0 = FAIL |

**環境**: `/home/rlrk/env_isaaclab7/bin/python` (Option-E venv)。GPU = cuda:0 (実測 21:53 先客 0)。全 leg 合計見積 ~25 min (init ~80 s/proc 支配)。

## D1 §2 manifest field mapping (層5 lens iii の対称差表)

必要集合 (D1 §2) → 実装: o/a_raw/a_executed/r_paid/o′/done/time_out/invalid_mask = npz arrays ✓ / termination_reason = manifest ("" + 宣言済 deviation) / process_index/derived_seed/pid ✓ / env_fingerprint_sha/code_sha ✓ / episode_idx/invalid_any ✓ / source="online" (R3-4) ✓ / sha256 ✓。追加 (additive): truncated_by, n_steps, drive_mode, sec_S_exposure。**既存 field の改名・削除 = ゼロ。**

## OUTCOME (2026-07-16 22:24 JST 追記、date-THEN-write)

**機械層 (層3)**: targeted ruff check + format = PASS / py_compile = PASS (3 files)。⛔ `./isaaclab.sh -f` (全ファイル) は 740-file 汚染ツリー巻込みのため不使用 (I0-a B3 と同方式)。ik_chord 事前 smoke = rc 0 (env init 69.6 s、published 1 ep)。

**Leg results (v1 full run = `forkb_i0b_legs_result.json` [= `_v1.json` 保全] + L5 v2 = `_only_l5.json`、runs = `forkb_i0b_runs/` 2.8 MB 全量 bank):**

| leg | verdict | 実測 |
|---|---|---|
| L1a K-pause @K=200 | **PASS** (84.6 s) | pause log 発火 / 停止中 publish 0 (count 200 不変) / ack 1 → `ep_000200` 公開 (= resume-safe 採番の positive control) / rc 0 |
| L1b K-pause organic @K=2 | **PASS** (89.8 s) | 2 本公開 → pause → 15 s 保持 (count=2) → ack → 3 本目 → rc 0 |
| L2 K_fail restart-halt | **PASS** (306.1 s) | 個体 rc000..003 = 4 個体・derived_seed 全相異 (1783842106/3294954633/3975626108/519546485) / `ep_000000..03.npz` 上書きゼロ / HALT.json + supervisor exit 2 |
| L3 lever smoke | **PASS** (186.2 s) | default: trainer=cuda:2, child CVD=["0"], 1 ep / fallback: trainer=cuda:0, N=3 (cap), CVD=["0","0","0"], 3 ep — **コード変更なし config のみで両形が立った** |
| L4 R2-4-b 2×2 | **SPLIT** (135.2 s) | **同 seed 象限 = PASS**: sha(A)==sha(B) `c3cc1791f776…` = serializer file-level byte 決定論 実証 / **異 seed 象限 = 測定結果 INERT**: derived_seed は実際に相異 (314674912 vs 1947343058、proc_meta 実測) なのに sha(C)==sha(A) ⇒ **ik_chord でも seed→data channel 無し = banked N-2 (FF inert) の拡張測定**。事前登録どおり FAIL のまま記録 (基準の後付け変更なし) → 設計 carry として escalate (下記) |
| L5 N-3 as-run reconcile | **v1 FAIL → v2 PASS** | v1 bar は D1 §7「land or inert 宣言」の**宣言分岐を欠く実装**だった (要求自体は不変、v1 保全)。v2 = 9/9 分類: landed_at_HEAD ×3 / landed_at_2933fa7bbc (E0v2a harness、後続 format commit で HEAD 相違) / landed_at_92a62f6a96 (skill_env_base、後続 tripwire commit で HEAD 相違) / **DECLARED ×4** (configs/__init__.py・route_env_config.py・route_executor.py = as-run == 現 worktree 未 commit bytes [standing residue] / newton_route_env.py = E0v2⇄E0v2a byte-stable `1fa382f2…` + 現 HEAD clean ⇒ 差分 = c60d311f96 のみ [flip+開示済 sweep、I0A manifest hunk 帰属] + flip 中立性 = I0-a byte-repro leg) / **UNEXPLAINED = 0** |

**D1 §2 対称差 (再掲、実装後)**: 必要集合 − 実装 = ∅ (termination_reason は "" コンテナ + 宣言済 deviation)。実装 − 必要集合 = additive {o_next 命名, truncated_by, n_steps, drive_mode, sec_S_exposure, proc_meta.rc*, cable_traj}。既存 field 改名・削除 = 0。

**視覚レグ**: 省略 (justified, loud) — 本 chunk の全主張は infra 述語。§S が semantic claim を禁止しており、motion 妥当性は一切主張していない。

**v2 landed-bytes 再走 (2026-07-16 23:0x、HEAD `8ae825c954`、fresh dirs `forkb_i0b_runs_v2/`、result `forkb_i0b_legs_result_v2.json`)**: v1 の tested bytes と landed bytes の差 (CHECK-6 注釈 3 行 + docstring 改稿) を閉じるため全レグを新規 dirs で再走 — L1a (103.3 s) / L1b (119.9 s) / L2 (274.1 s、同 derived_seed 連鎖 = 決定論的導出の再現) / L3 (150.2 s) / L5 (0.5 s、9/9 分類・unexplained 0) = **全 PASS 再現**。L4 = 同型 split (same=True / diff=False)。⭐**bonus byte-repro**: L4 same-seed episode sha = **v1 と v2 で同一 `c3cc1791f776…`** ⇒ tested-vs-landed delta が data 経路に不干渉であることの byte 実測。result の `all_pass=False` は L4 quadrant の事前登録 bar をそのまま記録した値 (v1.8 が I0-b scope 外へ解決済 — bar の後付け変更はしない)。

**Open items (escalation、埋めない):**
1. **N-2 seed-differentiation 移管 leg = I0-b では閉じられない (測定確定) → ⭐p5 裁定済 (同日 23:0x 受領、`FORKB_D0_RULINGS_VTDESIGN_20260716.md` v1.8 §N-2-RESOLUTION)**: 両 drive mode とも seed→data channel が env に存在しない (by-construction: INIT_XY_NOISE の書込先 `_ee_target_*` は毎 step route 絶対 target で上書き — draw される ≠ 出力に到達する)。infra 無罪 (L2) = 批准 / L4 の事前登録 FAIL 保持 = 批准 / 同 seed 象限 PASS の主張範囲 = **serializer+pipeline 決定論のみ** (seed-plumbing は L2 が担う)。**裁定 = channel-conditioned standing rule**: per-process seed を消費すべき channel が live になる度、その bring-up acceptance に「異 seed→異 output」判別 leg を含める (primary = trainer/(d) の policy stochasticity; DR CABLE_XY_OFFSET は Rs が ON にした時のみ — ⛔N-2 のために DR を ON にしない; 人工 entropy 却下)。**⛔INIT_XY_NOISE = appearance-only knob と記録** — training-data 多様性主張に数えない。処置 = (d)/trainer bring-up 設計の小項目 carry。
2. **DECLARED still-dirty 3 file** (configs/__init__.py / route_env_config.py / route_executor.py): E0 が走った standing 未 commit residue と byte 一致。land/inert 裁定 = tree-triage owner 案件 (I0-b scope 外、surfaced)。
3. **pN independent verify = pending** — I0-b fence は pN 判定まで CLOSE しない。
4. §S carry 不変: 本 chunk の全 episode data は reward-valid/training-ready 主張から除外 (全 artifact に exposure field 埋込済)。

## CHECK-6 conflict — commit BLOCKED (2026-07-16 22:3x、§運用10 surfaced)

**事実**: pre-commit `validate.sh --staged-only` CHECK 6 (`scripts/validations/check_safety.sh:46-58`) が collector/supervisor の `CUDA_VISIBLE_DEVICES` 4 行 (docstring 2 + 機能 2) を FAIL とし commit を block。**しかし**: (1) CLAUDE.md GPU § は訓練プロセス起動時の CVD を**必須**と定める (check の提案 `--device cuda:N` 単独では PyTorch の cuda:0 余剰 context ~264MiB を防げない) / (2) banked D0 R1-3 + node state.md:103 が per-process 明示 CVD を要求 / (3) tracked の thread_isaac_lab scripts 数十本に同一文字列の docstring 前例 (check より古い) / (4) `.validateignore` は「legacy/archived 専用 + staged は除外しない」と自文書化 = 不適合。check の本来の標的 (script が自分で CVD を掴む anti-pattern) と、launcher (CVD を**子に**付与する、CLAUDE.md 準拠の唯一の機構) の区別が check に無い = miscalibration。
**Options**: **A (推奨)** = CHECK 6 に launcher 許容を最小改修 (行末 annotation `# cvd-launcher` 付き行のみ除外、annotation を機能行 2 箇所に付与、pN verify に含める) / B = .validateignore (意味論不適合) / C = --no-verify (全層素通し、非推奨) / D = commit 保留で別途裁定。
**RESOLVED (2026-07-16 22:4x)**: Rs 裁定 = **A** (verbatim「A」) + pN CONCUR-WITH-CONDITIONS 4 項。⚠初案の blanket `# cvd-launcher` 単一注釈は pN 指摘どおり**過広** (任意の自己 GPU 取得行も注釈だけで通る) → **typed exact-shape exceptions** に置換して実装:
- `# cvd-child-env` = **コピーされた child-env dict への代入のみ** (行内に `os.environ` があれば注釈があっても FAIL) / `# cvd-provenance-read` = **read-only `os.environ.get` のみ** (同一行の environ 代入は FAIL)。shape AND annotation の両方必須 — 注釈単独では何も通らない。
- docstring 2 行はリテラル除去 (supervisor 経由の記述へ変更)。残る literal = 機能 2 行のみ (supervisor:116 / collector:189、各 typed 注釈)。
- **self-test = `scripts/validations/test_check_safety_cvd.sh` 8/8 PASS** — production `cvd_ban_filter` を source (コピー実装でない = 配線の証明、E0v2a B7 と同型)。負対照 4 本: 無注釈代入 / environ 直接変異×両注釈 spoof / get 併記変異 = 全 BANNED。
- validator-level 対照 = commit 前に実測 (staged 違反 fixture → CHECK 6 FAIL / 本 staged set → PASS)。

## pN I0-b HOLD 対応 (B1-B4 + records、2026-07-16 23:2x 起票 — 各対応は typed control 付き)

- **B1 (filter bypass)** → filter v2: child-env 許容 = target が文字どおり `env["CUDA_VISIBLE_DEVICES"]` ∧ 値が `str(<ident>)` か数字リテラル ∧ 行内 `os.environ`/`;` ゼロ。provenance 許容 = `os.environ.get` の dict-entry/単純代入形のみ ∧ `os.environ[`・get 以外の environ メソッド・`;` ゼロ。**self-test 13/13** (pN の 2 制御 `cfg[...]` / `update();get()` = BANNED 実測 + 任意呼出値 BANNED 追加)。既知残差 = 行跨ぎ alias dataflow (check comment に宣言 — grep は tripwire、review が backstop)。
- **B2 (preflight fail-open + 順序)** → fail-closed: count 不能 (missing / nonzero / timeout) = None → **LAUNCH_ABORT.json (stage/detail/§S) + run_manifest preflight=ABORT + exit 2、spawn ゼロ**。D1 §5 順序どおり run_manifest を preflight より先に書く。test hook = `--nvidia-smi-cmd` (CLI、environ 不使用)。
- **B3 (marker OR 検出)** → failure = `rc != 0` **OR** fresh marker (marker.rc == 現個体 restart_count)。stale marker (旧個体) = 不発。unreadable marker = fail-closed (failure 扱い)。hooks: collector `--test-marker-exit-zero` (1 ep publish → marker 書込 → exit 0) + supervisor `--test-crash-rc-max` (個体世代で hook 転送制御)。
- **B4 (schema)** → **p5 v1.9 §B4-DISPOSITION = (a) ADOPT** (bank 本 chunk): termination_reason は taxonomy 着地まで "" 許容 (= 未測定) + truncated_by 3 値 additive 批准。**4 pin 継承**: pin-1 consumer guard (終端意味論は done/time_out+truncated_by のみ、"" 分岐は fail-loud、⛔truncated_by→time_out 写像禁止 — **trainer-ingest spec への binding carry**) / pin-2 backfill 禁止 / pin-3 LEDGER loud 記載 (p6 chain、Rs veto 可) / pin-4 失効 = taxonomy 着地+collector 配線+schema 再 verify。collector は既に (a) 形 → L7 conformance leg で landed 実測。
- **records** → §S field を HALT.json / run_summary.json / LAUNCH_ABORT.json にも追加 (v3 以降 supervisor artifact も被覆。**v1/v2 時点の正確な範囲 = run_manifest / proc_meta / ep manifest / leg result のみ** — 過去の「全 artifact」claim をこの限定に訂正)。handoff memory の stale 「未 bank」記載 = 本 chunk 末に reconcile。

**v3 pre-registered predicates (run 前固定; 未変更軸 L1a/L1b/L4/L5 は pN 指示により再走不要 — v2 が landed 証拠):**
| leg | PASS 条件 (事前固定) |
|---|---|
| L2 再走 | v1/v2 と同型: 4 個体 (rc000-003)・seed 相異・ep 4 本 上書きゼロ・HALT + exit 2 (新検出ロジック下で crash 経路不変の証明) |
| **L2b (新)** | rc0 個体: 1 ep publish + FAILURE.json (rc=0) + exit 0 → supervisor が **rc=0 でも fresh marker で failure 計上 + restart** / rc1 個体 (hook 無): stale marker 残存下で完走 = success。予測: 個体 2・restart 1・HALT 無・supervisor rc 0・ep 3 本 (採番 0-2) |
| L3 再走 | v2 と同型 (default: trainer=cuda:2, CVD=["0"] / fallback: trainer=cuda:0, N=3) |
| **L6 (新)** | `/bin/false` と missing cmd の両方で: exit 2 ∧ LAUNCH_ABORT (stage=preflight_unknown, §S 有) ∧ manifest preflight=ABORT:* ∧ proc dir ゼロ |
| **L7 (新)** | manifest: termination_reason=="" ∧ truncated_by∈{workload_step_budget,env_done,supervisor_stop} ∧ §S 有 ∧ sha 一致 / npz: 必須 9 array の対称差 = ∅ ∧ time_out all-False / rc 0 |

**v3 OUTCOME (2026-07-16 23:4x 実測、HEAD `6cf3dc0015` = landed bytes、result = `forkb_i0b_legs_result_v3_only_l2_l2b_l3_l6_l7.json`、runs = `forkb_i0b_runs_v3/`): 5/5 = 事前登録どおり ALL PASS**
- L2 (332.1 s): 新検出ロジック下で crash 経路同型 — 4 個体・seed 相異・ep 4 本・HALT・exit 2。
- **L2b (154.1 s)**: fresh marker (rc==0 exit + FAILURE.json rc=0) → supervisor が failure 計上 + restart ✓ / rc1 個体が stale marker 残存下で完走 = success ✓ / 個体 2・ep 3 本・HALT 無・rc 0。B3 の両象限 閉鎖。
- L3 (178.3 s): lever 両形 同型 PASS。
- **L6 (0.1 s)**: nonzero (`/bin/false`) と missing の両方で exit 2 + LAUNCH_ABORT (stage=preflight_unknown、§S 有) + spawn ゼロ。B2 閉鎖 (fail-closed 実測)。
- **L7 (84.0 s)**: v1.9 (a) 形 conformance 全項 PASS (termination_reason=""・truncated_by 批准値・§S・sha 一致・9 array 対称差 ∅・time_out all-False)。B4 閉鎖 (landed 実測)。
