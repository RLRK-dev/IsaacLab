---
node_id: T-ROOT-optE-route-dapg-C1C2-P2-trainer-envbuild-substrate-forkB
node_name: "W1 Fork B CPU single-world process-parallel trainer infrastructure"
goal: "world_count=1 の proven MuJoCo CPU route env を N process で収集する fork B を、Stage-A 契約・決定論・忠実度を保ったまま設計・実装し、RL/IL throughput を確保しつつ vision/world-model 用資源を圧迫しない構成として検証する。"
goal_verification: |
  1. design v1.12 §21.11.2 の5項（N/資源、seed、IPC、Stage-A整合、R-b）が設計文書に固定され、独立reviewを通る。
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
created: 2026-07-16T17:49:20+09:00
last_updated: 2026-07-16T18:05:00+09:00
spec_version: LTM-1 v1.2
---

# Fork B CPU single-world process-parallel trainer infrastructure

## 0. 起票状態と境界

**IN_PROGRESS (起動承認済 2026-07-16 18:0x、Rs『承認』= D0 [DEFINE])。** D0 design gate から開始。probe (E0) は D0 の metric 定義固定後、source 実装 (I0) は D0/E0 bank 後。

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

### D0 — 5項の設計固定

1. Nと資源上限。
2. seed/provenanceと決定論。
3. async rollout IPC、搬送単位、頻度、backpressure。
4. Stage-A trainer-env契約とのreconcile。
5. R-b tripwireの着地点、診断用opt-out、test matrix。

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
