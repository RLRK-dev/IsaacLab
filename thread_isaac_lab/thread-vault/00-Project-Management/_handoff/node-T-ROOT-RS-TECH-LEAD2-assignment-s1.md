---
node_id: T-ROOT-RS-TECH-LEAD2
session_to: T-ROOT-RS-TECH-LEAD2#s1
assignee: "new Claude Code pane w2:pQ"
assignment: "WMSO development owner"
created: 2026-07-18T12:44:00+09:00
---

# T-ROOT-RS-TECH-LEAD2 initial assignment

Rs directにより、あなたを `T-ROOT-RS-TECH-LEAD2` とし、`T-WMSO` のdevelopment/design ownerへ割り当てる。

## Startup read order

1. session-start規則に従いrepo rootの `CLAUDE.md` とproject memory `MEMORY.md` を読む。
2. `thread_isaac_lab/thread-vault/02-Workflow/VaultProtocol.md` のV7/V9/V10/V11/V12を適用する。
3. `thread_isaac_lab/thread-vault/T-ROOT-RS-TECH-LEAD2/state.md` を読む。
4. `thread_isaac_lab/thread-vault/T-WMSO/state.md` を読む。
5. `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/WMSO_ADOPTION_CHARTER_OPSSUP_20260718.md` を読む。
6. `00-Project-Management/_handoff/node-T-ROOT-RS-TECH-LEAD2-pins-s1.sha256` をrepo rootから検証する。

## First action

WMSO D0 read-only inventoryを開始する。current learned skills、policy lineage、obs/action schema、vision belief、termination/checkpoint、handoff/recovery、`routing_orchestrator.py`、safety path、deadline候補をsource/hash付きでinventory化し、architecture draftと分離してbank前reviewをpNへ依頼する。

## Boundaries

- production control変更、training launch、WMSO inference、closed-loop authorityは未承認。
- WMSOはPPO限定でない。BC / BC+RL / PPO / DAPG等を共通contractで扱う。
- pNはindependent verifier、p6はcustody。自分で自分のevidence/design gateを閉じない。
- p4のgrip gate chainを停止・混入しない。
- 実験・rerun・source promotion前はprior-art gateを実施する。

最初に `[RS-TECH-LEAD2→OPS-SUP-CODEX] assignment readback` として、readback、境界理解、D0 inventoryのpreregistered scopeを `w2:pN`へ返信すること。
