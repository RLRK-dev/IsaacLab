---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild-substrate-forkB
node_name: "W1 Fork B CPU single-world process-parallel trainer infrastructure"
goal: "world_count=1 の proven MuJoCo CPU route env を N process で収集する fork B を、Stage-A 契約・決定論・忠実度を保ったまま設計・実装し、RL/IL throughput を確保しつつ vision/world-model 用資源を圧迫しない構成として検証する。"
goal_verification: |
  1. design v1.12 §21.11.2 の5項＋v1.13 追加の項6 = **6項**（N/資源、seed、IPC、Stage-A整合、R-b、process故障/NaN方針）が設計文書に固定され、独立reviewを通る。
  2. world_count=1 route env の N=1/2/4 process 実測artifactが transitions/s、CPU/GPU memory、determinism/fidelity を記録する。
  3. W1 trainer transition budget から必要throughputを逆算し、実測scalingで採択Nを決める。不達時はRsへ再裁定する。
  4. Stage-A trainer-env gateとのreconcileがPASSし、processごとのseed/provenanceとasync rollout IPC/backpressure契約が検証される。
  5. use_mujoco_cpu と world_count>1 の誤構成をfail-loudに拒否するR-b tripwireが、診断用opt-outを含む識別可能なtestで検証される。
  6. fork Aはdormantのまま、L0必須4要素（RL/IL/vision/world model）の計算資源境界が保存される。
status: IN_PROGRESS
parent_node: T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild
children_nodes: []
dependencies:
  precedent: []
  blocker: []
provenance:
  - "APPROVED charter: eval_runs/troot_optE_dapg_wholeroute_scope_20260701/ENV_MULTIWORLD_SUBSTRATE_CHARTER_RSTECHLEAD_20260716.md (approval reflected at db4cefc8fa)"
  - "Rs ruling/design consequence: eval_runs/troot_optE_dapg_wholeroute_scope_20260701/RLENV_PIN_DESIGN_VTDESIGN_20260715.md v1.12 §21.11 (da6211991e)"
  - "Stage-A contract: eval_runs/troot_optE_dapg_wholeroute_scope_20260701/STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md"
authority: "Human-Rs 2026-07-16 verbatim『推奨でよい、fork Bで進めて』(作成承認) + 2026-07-16 18:0x『承認』(D0 [DEFINE] = 起動承認、%12 上程への回答)。"
session_history:
  - "2026-07-16 18:0x D0 [DEFINE] Rs承認 (起動) — D0 design gate 開始 (design=p5+%12, evidence=w2:p4, verify=OPS-SUP-CODEX)"
  - "2026-07-16 19:5x D0 = 6/6 CLOSE (design R1-R6 + item-1 evidence = calibration v4 fd536235e9、OPS-SUP 独立 verify PASS-WITH-RECORDS-FIX)。D1 spec = CONFORM 7/7 (v0.2)。E0 = 事前登録 (K=200/K_fail=3/contention≥0.8/決定論/memory) に従い fresh N=1 から開始可"
  - "2026-07-16 20:2x E0 = GATE CLOSE PASS — E0v2a 2933fa7bbc が B6/B7 根治・全 predicate PASS (pN final = PASS-WITH-RECORDS-FIX、records-fix a90d9ab6db readback PASS)。N1/N2/N4 = 10.872/20.432/35.579 t/s・eff 0.818 ⇒ N_collect=4 FINAL ADOPTED・I0 OPEN GO。検証史 v1 fb36c49540→v2 945a5c229a→v2a (prereg 完全性 保持) = LEDGER:58"
  - "2026-07-16 21:1x I0-a (flip+tripwire c60d311f96) = CLOSE (pN final = PASS-WITH-CARRY; HOLD 応答 = df063c85c9 [scope manifest+format+陽性対照 harness] + 5d3924b12a [fresh 陽性対照 PASS] + ad0bb76460 [p5 §S run-hygiene 裁定])。I0-b (supervisor+collector) = fence OPEN GO (infra)。⚠carry = FM3/FM4 HEAD-live 未批准 → owner chain PASS まで reward-valid/training-ready claim 不可 (§0 carry 節)。〔20:2x/21:1x の 2 entry = p6 反映執行 (%12 依頼 21:3x、LEDGER:58 `3669b370d3` 準拠)〕"
  - "2026-07-16 22:4x I0-b infra = banked (1d95b7bf6e 287 files + a9a26249fb CHECK6 [Rs 裁定 A] + 8ae825c954 --tag)・機構 leg 4/4 PASS。N-2 carry = v1.8 §N-2-RESOLUTION (2a7ac33d87) で scope 外解決 (channel-conditioned standing rule / INIT_XY_NOISE=appearance-only)。fence CLOSE = landed-bytes fresh 再走 (v2 tag) → pN verify 待ち。〔entry = p6 反映執行 (%12 依頼 23:0x)〕"
  - "2026-07-16 23:0x I0-b v2 再走 完了 → pN independent verdict = HOLD (fence CLOSE/flip 禁止)。PASS 保持 = landed-SHA/K・K_fail・lever/L4/L5/integrity/N-2 v1.8。blocker 4 = CHECK6 負対照 bypass ×2 / nvidia-smi 不在 nonzero rc = k=0 fail-open / FAILURE.json 非独立 trigger / termination_reason 空文字 enum 外 (p5 disposition 無)。correction chain 待ち。〔entry = p6 反映執行 (pN disposition relay)〕"
created: 2026-07-16T17:49:20+09:00
last_updated: 2026-07-16T23:10:51+09:00
spec_version: LTM-1 v1.2
---

# Fork B CPU single-world process-parallel trainer infrastructure

## 0. 起票状態と境界

**IN_PROGRESS。D0 = 6/6 CLOSE (2026-07-16 19:5x)。D1 = CONFORM 7/7 + AMEND-1 (v0.2)。⭐E0 = GATE CLOSE PASS (20:2x: E0v2a `2933fa7bbc` = B6/B7 根治・全 predicate PASS、pN final = PASS-WITH-RECORDS-FIX [records-fix `a90d9ab6db`]。実測 N1/N2/N4 = 10.872/20.432/35.579 t/s・eff 0.818 ⇒ N_collect=4 = FINAL ADOPTED [二段採択 完了])。⭐I0-a (flip+tripwire) = CLOSE (21:1x: pN = PASS-WITH-CARRY、bank `c60d311f96` + HOLD 応答 `df063c85c9`/`5d3924b12a`/`ad0bb76460`)。現 phase = I0-b — ⭐**infra 実装 = banked・機構 leg 4/4 PASS・fence CLOSE は pN verify 待ち** (2026-07-16 22:4x: 本体 `1d95b7bf6e` [collector+supervisor+機構 leg 287 files: K/K_fail/lever PASS・L4 split・L5 v2 9/9] + CHECK6 typed exceptions `a9a26249fb` [Rs 裁定 A + pN 条件 4 項・self-test 8/8] + `8ae825c954` [--tag]。**N-2 carry = v1.8 §N-2-RESOLUTION `2a7ac33d87` で I0-b scope 外へ解決** [channel-conditioned standing rule 化・INIT_XY_NOISE=appearance-only knob と記録]。**v2 再走 = 完了 → ⛔pN independent verdict = HOLD (2026-07-16 23:0x 観測) — fence CLOSE/flip 禁止**。**PASS 保持軸** = v2 landed-source SHA / K・K_fail・lever / L4 same-seed byte / L5 / artifact integrity / N-2 v1.8。**blocker 4** = ①CHECK6 追加負対照 2 本 bypass ②nvidia-smi unavailable・nonzero rc が k=0 **fail-open** ③FAILURE.json が独立 restart trigger でない ④termination_reason 空文字 = banked enum 外・p5 disposition 無。⇒ ⭐**対応進行 (23:2x)**: B1=CHECK6 exact-shape `d3ad0dbf5f` (13/13・2 制御 BANNED) / B4=**v1.9 §B4-DISPOSITION `10ea8dbe35` (a) ADOPT** (enum 不変・`""`=未測定 sentinel・`truncated_by` additive・pin-1〜4 binding、**pin-3 = Rs veto 可の interim 逸脱 = LEDGER loud 記載済**) / B2+B3=`6cf3dc0015` (preflight fail-closed+LAUNCH_ABORT・marker OR・§S 全 supervisor artifact)。⭐**pN 再判定 (23:4x) = mechanism/evidence PASS・PASS-WITH-RECORDS-FIX** (v3 5/5 + 独立 287 assertions errors0・B1-B4 closure 確認)。**fence = CLOSED 継続 — 唯一の gap = %12-owned `02-Workflow/HANDOFF.md` stale** (21:28 の「collector 未bank/supervisor 未着手」のまま) ⇒ **HANDOFF correction bank + pN readback で I0-b CLOSE flip・再走不要**。所在 = `I0B_BUILD_RSTECHLEAD_20260716.md` OUTCOME:61+CHECK-6:90 / `FORKB_D0_RULINGS...md` §N-2-RESOLUTION:219)**。

⚠ **§S carry (binding — `I0A_SCOPE_MANIFEST_RSTECHLEAD_20260716.md:36-45` + `ad0bb76460`)**: 巻込 FM3/FM4 は **HEAD で live・未批准** (flag-gated でない: `newton_route_env.py:1395-1396` seat 本経路 無条件 + `:1627` `_c1_escape_after_seat` 無条件呼出)。⇒ **owner chain (/reward-design 再走 → p5 再 verify → /pre-check) PASS まで、HEAD run の seat/G3+/escape 出力 = 未批准意味論** — banked-semantics を主張する run は pre-sweep commit へ pin するか、暴露を loud 宣言。**I0-a byte 一致 = physics 軌道のみ (reward/latch 経路の等価性ではない)**。

- 採択手段: **fork B** = `world_count=1`、`use_mujoco_cpu=True` のproven route envをN processで収集。
- C: minimal smokeのみ。
- A: **dormant**。別のRs指示なしにS8移行、poke mirror、再baseline、動画GTを開始しない。
- pin nodeと分離する。本nodeはpin恒久配線(a)(b)(d)を実装しない。
- R-b tripwireは本nodeの実装対象。ただしdesign gate通過後に着手する。

## 1. founding documents

1. `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/ENV_MULTIWORLD_SUBSTRATE_CHARTER_RSTECHLEAD_20260716.md`
   - status = APPROVED、fork B採択、§3.2 acceptance gate、§4-B R-b、§6裁定事項。
2. `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/RLENV_PIN_DESIGN_VTDESIGN_20260715.md` v1.12 §21.11
   - Rs verbatim、fork Bによるpin(c)不要化、§21.11.2 design gate agenda。
3. `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/STAGEA_TRAINER_ENV_DESIGN_GATE_RSTECHLEAD_20260712.md`
   - banked Stage-A trainer-env契約。fork Bはこれを置換せずreconcileする。

## 2. prior-art / no-repeat disposition

`scripts/check_thread_vault_prior_art.sh --fail-on-blocker substrate forkB process-parallel trainer-envbuild` は2026-07-16にexit 2で既知blockerを検出した。

- 同一prior art: 2026-07-08のworlds≥1 freeze、既存envbuild node、過去のsubstrate変更案。
- 続行根拠: Human-Rsの新規明示裁定「fork Bで進めて」。
- concrete delta: GPU/S8や2nd-bend substrateを再試行せず、各processを`world_count=1`のproven CPU pathに固定してtrainer側で並列化する。
- 禁止: fork Aの暗黙再開、CPU world_count>1でのsilent batch、過去のinfeasible主張をsubstrate変更根拠へ再利用すること。

## 3. design gate phases

### D0 — 6項の設計固定 (v1.13 で項6 追加)

1. Nと資源上限。
2. seed/provenanceと決定論。
3. async rollout IPC、搬送単位、頻度、backpressure。
4. Stage-A trainer-env契約とのreconcile。
5. R-b tripwireの着地点、診断用opt-out、test matrix。
6. process故障/NaN方針（fail-loud per-process、buffer汚染防止provenance、restart規約 — v1.13 追加・%12 採用）。

### E0 — sizing / fidelity evidence

- N=1/2/4で同一のroute-env workloadを測る。
- transitions/s、CPU/GPU memory、per-process seed、output provenanceを保存する。
- single-run基準に対するbyte-reproまたは設計で定めた厳密な同値条件を検証する。
- 正の対照を含め、死んだ計器による「差分ゼロ」をPASSにしない。

### I0 — implementation

- design gateとE0の採択Nがbankされた後だけ開始する。
- process-parallel collectorとR-b tripwireを分離したatomic changeとして実装・検証する。

### V0 — acceptance

- charter §3.2の4 artifactと本fileの`goal_verification`を満たしてaccept。
- 必要throughput不達、資源超過、決定論/忠実度破壊のいずれかでRs再裁定。fork Aへ自動遷移しない。

## 4. §21.11.2 責任分担（起票時co-decision）

| agenda | design accountable | evidence / execution leg | independent verify |
|---|---|---|---|
| 1. Nと資源上限 | p5 + %12 | w2:p4: N=1/2/4 sizing probe | OPS-SUP-CODEX: metric定義、artifact完全性、trainer-budget逆算 |
| 2. seed / 決定論 | p5 + %12 | w2:p4: per-process seed/repro probe | OPS-SUP-CODEX: collision、再起動、順序差の識別性review |
| 3. rollout IPC | %12 + p5 | w2:p4: 搬送量・backpressure microbench（設計固定後） | OPS-SUP-CODEX: loss/duplication/orderingとreplay境界review |
| 4. Stage-A reconcile | p5 primary + %12 | w2:p4: source/evidence抽出支援 | OPS-SUP-CODEX: banked Stage-A specとの差分独立review |
| 5. R-b tripwire | %12 + p5 | w2:p4: 候補着地点のsource traceと識別test evidence | OPS-SUP-CODEX: default拒否・opt-out・fork B非発火のtest matrix review |

**負荷境界:** w2:p4は実測/evidence legを担当し、設計決定はp5+%12がbankする。OPS-SUP-CODEXは設計ownerにならず、acceptanceと独立verifyを担当する。

## 5. resource and safety invariants

- GPU process上限は`≤4/GPU`。各processで`CUDA_VISIBLE_DEVICES`を明示する。
- NはGPU memoryだけでなくCPU core/NUMAとCPU MuJoCo stepの飽和で決める。
- vision/world-modelの予約資源を食い潰すNを採択しない。
- full training、production launch、checkpoint mutationは本nodeの起動・design gate・個別実行承認より前に行わない。
