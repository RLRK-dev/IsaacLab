#!/usr/bin/env python3
"""v0.2.3 -> v0.2.4 fold (records-only; frozen files untouched).
Usage: python3 fold_v024.py <PKG_DIR> <verdicts_v024.json>   verdicts = {id: {"confirmed": bool, "severity": str, "merged_into": str}}
Each finding block is applied only when verdicts[id].confirmed is True (merged duplicates follow their survivor)."""
import sys, json, re, subprocess
P = sys.argv[1]; VERD = json.load(open(sys.argv[2]))
NOW = subprocess.check_output(["date", "-u", "+%Y-%m-%d %H:%M UTC"]).decode().strip()
A = "$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md"; B = "$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md"; D0 = "$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md"

def conf(i):
    v = VERD.get(i, {})
    if v.get("merged_into"): return conf(v["merged_into"])
    return bool(v.get("confirmed"))
def any_conf(*ids): return any(conf(i) for i in ids)
def vstr(i):
    v = VERD.get(i)
    if not v: return "（verifier 未了）"
    if v.get("merged_into"): return f"重複 → {v['merged_into']}"
    return f"CONFIRMED（{v['severity']}）" if v["confirmed"] else f"refuted（{v['severity']}）"

class Doc:
    def __init__(self, name): self.name = name; self.t = open(f"{P}/{name}", encoding="utf-8").read()
    def rep(self, old, new, count=1):
        n = self.t.count(old); assert n == count, (self.name, old[:80], n); self.t = self.t.replace(old, new)
    def repline(self, prefix, new):
        L = self.t.split("\n"); idx = [i for i, l in enumerate(L) if l.startswith(prefix)]
        assert len(idx) == 1, (self.name, prefix[:80], idx); L[idx[0]] = new; self.t = "\n".join(L)
    def line(self, prefix):
        L = [l for l in self.t.split("\n") if l.startswith(prefix)]; assert len(L) == 1, (self.name, prefix[:80], len(L)); return L[0]
    def insert_after_line(self, prefix, block):
        L = self.t.split("\n"); idx = [i for i, l in enumerate(L) if l.startswith(prefix)]
        assert len(idx) == 1, (self.name, prefix[:80], idx); L[idx[0]+1:idx[0]+1] = block.split("\n"); self.t = "\n".join(L)
    def insert_before_line(self, prefix, block):
        L = self.t.split("\n"); idx = [i for i, l in enumerate(L) if l.startswith(prefix)]
        assert len(idx) == 1, (self.name, prefix[:80], idx); L[idx[0]:idx[0]] = block.split("\n"); self.t = "\n".join(L)
    def save(self): open(f"{P}/{self.name}", "w", encoding="utf-8").write(self.t); print("wrote", self.name)

applied = []
def gate(*ids):
    ok = any_conf(*ids)
    if ok: applied.append(" / ".join(ids))
    return ok

# ======================================================================= 05
d = Doc("05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("RUNTIME SPEC (v0.2.3 REVIEW CANDIDATE)", "RUNTIME SPEC (v0.2.4 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.3（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）**", "- status: **REVIEW CANDIDATE v0.2.4（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2.3 → v0.2.4 = v0.2.3 本文への再レビュー round（reviewer R1 / R2 + verifier V1 / V2・別 context）の確定 finding の fold（§13）。旧版の系譜:")
d.rep("→ **verifier verdict + 残差 + 軸 C の fold = 本版 v0.2.3（§13）**", "→ verifier verdict + 残差 + 軸 C の fold = v0.2.3（2026-09-04 20:47 UTC）→ **v0.2.3 再レビュー round（R1 / R2 → V1 / V2）の fold = 本版 v0.2.4（§13）**")

if gate("R1-01"):
    d.rep("    command_deadline_s: CanonicalDecimal              # ≥ 1/action_rate_hz（LEARNED）。超過 = R_DEADLINE_MISS", "    command_deadline_s: CanonicalDecimal              # ≥ 1/action_rate_hz（LEARNED）。超過 = R_DEADLINE_MISS（計時範囲 = §4.2・v0.2.4 R1-01）")
    d.insert_after_line("- 実測 inter-command 間隔が profile 許容", "- **`command_deadline_s` / `inter_command_jitter_s` の計時範囲（v0.2.4・R1-01）**: 計時は `owner == EXECUTOR ∧ ¬boundary_wait ∧ mode == CLOSED_LOOP_AUTHORITY ∧ 当該 lease で admitted command ≥ 1` のときのみ。S_BOUNDARY_WAIT では停止（滞留上限 = `boundary_dwell_s`）、初回 command 前の上限は `health_confirm_timeout_s`（`first_command_admitted`）。よって TERMINAL boundary が DEADLINE_MISS に化けて再選択が SAFEHOLD 起動（B1 の offer 検証を迂回）へ逸れることは無い。executor heartbeat 義務（`R_EXECUTOR_LOST`）は LEASE_INVALIDATED まで継続。")
if gate("R1-02"):
    old = d.line("- **permit 発行の前提条件（v0.2.1・C-07 / C-10）**")
    a = old.find("**age の基準（v0.2.3・B2-14 残差）**"); b = old.find("(f) `permit.profile_hash")
    assert a > 0 and b > a
    new = old[:a] + "**age の基準（v0.2.3・B2-14 残差 → v0.2.4・R1-02 で起点を評価時刻へ）**: `age = now(manager) − t_mono`、`t_mono` = `evaluate_authority_grant` が呼ばれた時（O0 層が decision を評価時刻の audit record と共に引き渡す）に記録した `RuntimeAuditRecord`（kind = ASSESSMENT・payload = decision ref + 4 入力 record の ref `%s:346-352`）の `t_mono`。manager の「最初の解決」時刻ではない（それでは初回 age = 0 で常に通る）。その record が無い decision は不在として扱う（`R_AUTHORITY_DECISION_ABSENT`）。age 超過 = 再評価（新 ref）を要求し permit 不発行; " % A + old[b:]
    d.repline("- **permit 発行の前提条件（v0.2.1・C-07 / C-10）**", new)
if gate("R1-03"):
    d.rep("    seq: int                                          # CAS 成功ごとに +1（durable 化の単調 key）", "    seq: int                                          # CAS 成功ごとに +1（durable 化の単調 key）\n    safehold_disposition: RuntimeDisposition | None   # v0.2.4（R1-03）: 当該 SAFEHOLD 期間の実効 disposition の max（SAFE_STOP > HOLD）。条件 1 の等値比較の対象外だが同一線形化点で durable 更新され、§5.2 (iii) はこれを線形化読みで読む（audit 読出しに依存しない）。owner.kind == EXECUTOR では None")
    d.rep("current が既に SAFEHOLD のとき TRANSFER_TO_SAFEHOLD は理由を**強める方向にしか**書き換えない（弱い理由への上書きは記録付き no-op = FAULT + audit・状態不変・epoch 不変 — INV-30）。",
          "current が既に SAFEHOLD のとき TRANSFER_TO_SAFEHOLD は理由を**強める方向にしか**書き換えない（弱い理由への上書きは記録付き no-op = FAULT + audit・状態不変・epoch 不変 — INV-30）。**同 tier / 同 reason（v0.2.4・R1-03）**: reason は保持・epoch 不変の記録付き no-op とし、要求される clearance の**和集合**を CAS_ATTEMPT payload に記録する。いずれの no-op でも `safehold_disposition := max(現値, 実効 disposition)`（SAFE_STOP > HOLD）は同一線形化点で durable 更新する（B2-05 の例外が no-op で失われない）。")
    d.rep("| any | AuthorityManager 再起動 | TRANSFER_TO_SAFEHOLD(MANAGER_RESTART)（durable state からの復帰 CAS） | `S_SAFEHOLD(MANAGER_RESTART)` |", "| any | AuthorityManager 再起動 | TRANSFER_TO_SAFEHOLD(MANAGER_RESTART)（durable state からの復帰 CAS） | `S_SAFEHOLD(max(persisted reason, MANAGER_RESTART))`（persisted が同 tier 以上なら reason・epoch 保持 — 失敗表 R_MANAGER_RESTART 行と同一・v0.2.4 R1-03） |")
    d.rep("  (iii) else SafeHold（safehold_reason == SAFE_STOP なら SafeStop；safehold_reason == SAFETY かつ当該遷移の記録 disposition が SAFE_STOP なら clearance record まで SafeStop・v0.2.3 B2-05）", "  (iii) else SafeHold（`state.safehold_disposition == SAFE_STOP` なら SafeStop — 線形化読み・v0.2.4 R1-03。SAFETY 理由でも当該期間の実効 disposition が SAFE_STOP なら clearance record まで SafeStop・v0.2.3 B2-05）")
    d.repline("| INV-31 |", "| INV-31 | 再起動した gateway は `safehold_reason == GATEWAY_RESTART` を観測するか、自分の再起動報告以後に `seq` が進んだ（= manager が復帰 CAS を線形化した）ことを観測するまで (ii) を評価しない（v0.2.2・B-M10・v0.2.4 R1-03） | R_GATEWAY_RESTART |")
    d.repline("| T-28 |", d.line("| T-28 |").rstrip(" |") + "；同 tier / 同 reason の再遷移で reason・epoch 不変かつ `safehold_disposition` が max へ更新される（v0.2.4） |")
if gate("R1-05", "R2-03"):
    d.rep("(j) profile が参照する外部内容（`predicate_refs` / `evaluator_ref` / `tcp_offset_ref` の解決先）の content sha256 が profile の宣言と一致（doc 06 §2.1・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-04）",
          "(j) profile が宣言する**全ての** content hash（`predicate_sha256` / `evaluator_sha256` / `zones[].geometry_sha256` / `calibration_refs[].artifact_sha256` / `gateway_config.artifact_sha256` / `deployment_evidence_policy_hash` = H_WCJ(解決した policy) / required `DeploymentEvidenceRecord.artifact_sha256`）が解決先の内容と一致（doc 06 §3・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-04・v0.2.4 R1-05 / R2-03 で全 hash へ一般化）")
    d.rep("tool 形状は評価しない（doc 06 §4・OPP-14・v0.2.3 CD-18） |", "tool 形状は評価しない（doc 06 §4・OPP-14・v0.2.3 CD-18）。gateway は評価前に zone geometry の解決内容 sha256 を `geometry_sha256` と再検証し、不一致 = 評価不能 = FALSE（v0.2.4・R1-05） |")
if gate("R1-06", "R2-19"):
    d.rep("評価対象 = hold が LINEAR_INTERPOLATE のとき直前 admitted setpoint → 新 setpoint の線分（TCP 点・FK 後）、ZERO_ORDER_HOLD のとき点。", "評価対象 = `DIFF_IK_EE_TARGET` では hold 種別にかかわらず**線分**（直前 admitted setpoint → 新 setpoint；初回は実測 TCP → setpoint・FK 後の TCP 点）— 物理的な腕は setpoint 間を連続に動くため ZOH でも点評価では keep-out を跨げる（v0.2.4・R1-06 / R2-19）。hold は時間 parameterization のみを変える。")
if gate("R1-07"):
    d.rep("| ACK の束縛不一致（epoch/offer/invocation） | AuthorityManager | `R_ACK_MISBOUND` | 変化なし | `RESELECT` |", "| ACK の束縛不一致（epoch/offer/invocation）または CAS 時点で ACK 失効（`now > ack.valid_until`・条件 3）（v0.2.4・R1-07） | AuthorityManager | `R_ACK_MISBOUND` | 変化なし（CAS REJECTED） | `RESELECT` |\n| CAS 条件 9 不成立（IndependentSafetyLayer の health 不良 / 未処理 STOP・HOLD 決定）（v0.2.4・R1-07） | AuthorityManager | `R_SAFETY_OVERRIDE`（未処理決定）/ `R_SAFETY_LAYER_LOST`（health failed・heartbeat 欠落） | CAS REJECTED・状態不変（safety 側の遷移は該当行） | 該当行の disposition（`HOLD` / `SAFE_STOP`） |\n| CAS 条件 10 不成立（clearance record 不在）（v0.2.4・R1-07） | AuthorityManager | `R_PERMIT_MISBOUND`（CAS_ATTEMPT payload に欠落した clearance を記録） | CAS REJECTED・状態不変 | 変化なし（clearance 待ち・permit は VOID） |")
if gate("R1-08"):
    d.rep("| Terminal INVALID_STATE | 解消せず | SAFE_STOP（TRANSFER_TO_SAFEHOLD(SAFE_STOP)・原因 fault は別途記録・v0.2.2） |", "| Terminal INVALID_STATE | 解消せず | NO_CHAIN 経路 = §3.7 の S_BOUNDARY_WAIT 退出行（TRANSFER_TO_SAFEHOLD(NO_CHAIN \\| SAFE_STOP per on_no_chain)・fault = `R_NO_CANDIDATE` / `R_BOUNDARY_DWELL_EXCEEDED`）— v0.2.4 R1-08 で §3.7 / B5 と同一定義に |")
if gate("R1-09"):
    d.rep("| any | IndependentSafetyLayer STOP / HOLD | TRANSFER_TO_SAFEHOLD(SAFETY) | `S_SAFEHOLD(SAFETY)` | SAFETY_OVERRIDE, PERMIT_VOIDED(全), FAULT(R_SAFETY_OVERRIDE) |", "| any | IndependentSafetyLayer STOP / HOLD | TRANSFER_TO_SAFEHOLD(SAFETY) | `S_SAFEHOLD(SAFETY)` | SAFETY_OVERRIDE, PERMIT_VOIDED(全), FAULT(R_SAFETY_OVERRIDE), DISPOSITION(HOLD \\| SAFE_STOP by decision.action)（v0.2.4・R1-09） |")
if gate("R1-10"):
    d.rep("| `S_SAFEHOLD` / `S_BOUNDARY_WAIT` | ack → permit → CAS 成功 | TRANSFER_TO_EXECUTOR | `S_HEALTH_PENDING` | EPOCH_TRANSITION, LEASE_ACTIVATED, LEASE_INVALIDATED(旧) |", "| `S_SAFEHOLD` / `S_BOUNDARY_WAIT` | ack → permit → CAS 成功 | TRANSFER_TO_EXECUTOR | `S_HEALTH_PENDING` | EPOCH_TRANSITION, LEASE_ACTIVATED, LEASE_INVALIDATED(旧 lease がある場合のみ), PERMIT_CONSUMED, CAS_ATTEMPT（v0.2.4・R1-10） |")
    d.repline("| INV-17 |", "| INV-17 | §3.7 の各事象について、その行が要求する record kind ごとにちょうど 1 件の `RuntimeAuditRecord`；加えて §8 記録義務の各項目（admitted command 等・§3.7 事象でないもの）について 1 件（v0.2.2・B2-17・v0.2.4 R1-10） | 記録欠落 = fault |")
if gate("R1-11"):
    d.rep("| `S_TRANSFER_PENDING` | 上記いずれか + UNUSED permit ≥ 1 |", "| `S_TRANSFER_PENDING` | (`S_SAFEHOLD` ∨ `S_BOUNDARY_WAIT`) + UNUSED permit ≥ 1（§3.4 (d) / INV-28 により LEASE_ACTIVE / HEALTH_PENDING では permit は存在し得ない・v0.2.4 R1-11） |")
    d.rep("+ 直近 admitted command + `restart_pending` flag |", "+ 直近 admitted command + `restart_pending` flag + `pending_invalidate` flag（v0.2.3・§5.2） |")
if gate("R1-12"):
    d.rep("`(lease_id, control_epoch)` 等値 ∧ `¬boundary_wait` ∧ `AcceptedEnvelope` 連言", "`(lease_id, control_epoch)` 等値 ∧ `cmd.executor_id == lease.executor_id`（v0.2.4・R1-12） ∧ `¬boundary_wait` ∧ `AcceptedEnvelope` 連言")
    d.repline("| INV-03 |", "| INV-03 | admitted command: `(cmd.lease_id, cmd.control_epoch) == (state.active_lease_id, state.control_epoch)` を線形化点で満たし、`cmd.executor_id == lease.executor_id`（v0.2.4・R1-12）、`cmd.cmd_seq` は lease 内で厳密単調（v0.2.2） | R_EPOCH_STALE_COMMAND / R_LEASE_UNKNOWN_COMMAND / R_TIMING_VIOLATION |")
if gate("R1-13"):
    d.rep("B0  AuditRecorder: ASSESSMENT 開始。snapshot := AuthorityManager.read_snapshot()", "B0  AuditRecorder: ASSESSMENT 開始。snapshot := AuthorityManager.read_snapshot()。producer / offer がある場合は `snapshot.boundary_wait == True` を要求し、偽なら `boundary_dwell_s` 内に再読（MARK_BOUNDARY_WAIT の線形化を待つ）— permit 要求は boundary_wait 観測後のみ（v0.2.4・R1-13）")
    d.rep("| boundary 外からの転送要求（v0.2.2・B-H2 / B2-02） | AuthorityManager | `R_MIDSKILL_TRANSFER_BLOCKED` | permit 不発行 / CAS REJECTED・状態不変 | 変化なし（audit・lease 継続） |", "| boundary 外からの転送要求（v0.2.2・B-H2 / B2-02） | AuthorityManager | `R_MIDSKILL_TRANSFER_BLOCKED` | permit 不発行 / CAS REJECTED・状態不変 | 変化なし（audit・lease 継続）。Orchestrator は `boundary_dwell_s` 内に snapshot を再読して再要求（v0.2.4・R1-13） |")
if gate("R1-14"):
    d.rep("| SAFETY | 同上 | IndependentSafetyLayer の clearance record（`stabilized_post_action_state` `%s:320` の参照を含む）。runtime は自ら解除しない |" % D0, "| SAFETY | 同上 | IndependentSafetyLayer の clearance record（`stabilized_post_action_state` `%s:320` の参照を含む）。executor 発の SAFETY_STABILIZED（ISL 決定が先行しない場合）では、ISL の clearance record が executor の報告した stabilized state を確認したものであること（確認不能なら CHECKPOINT_DISABLED 行と同じ operator clearance + 再観測）（v0.2.4・R1-14）。runtime は自ら解除しない |" % D0)
if gate("R1-15", "R2-12"):
    d.repline("| INV-33 |", "| INV-33 | `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` における lease の活性時間（LEASE_ACTIVATED からの経過）は `lease_max_duration_s` 以下（超過 = TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION) + `R_LEASE_DURATION_EXCEEDED`）— WAIT を含む。`S_BOUNDARY_WAIT` の滞留は `boundary_dwell_s` が上限（NO_CHAIN 経路・§3.7）ゆえ lease の総活性時間 ≤ `lease_max_duration_s + boundary_dwell_s`（v0.2.3・CD-10・v0.2.4 R1-15 / R2-12: boundary 滞留を TIMING_VIOLATION に写さない — R1-01 と同根） | R_LEASE_DURATION_EXCEEDED |")
if gate("R1-16"):
    d.rep("`pending_invalidate` = gateway が TRANSFER_TO_SAFEHOLD の trigger を検出してから再試行 CAS の SUCCESS を観測するまで True・v0.2.3 B-M1 / B2-04）", "`pending_invalidate` = gateway が TRANSFER_TO_SAFEHOLD の trigger を検出してから、再試行 CAS の SUCCESS **または** 線形化読みで trigger の lease が既に非活性（`state.active_lease_id ≠ trigger.lease_id ∨ owner.kind == SAFEHOLD`）と分かるまで True・v0.2.3 B-M1 / B2-04・v0.2.4 R1-16: lease-scoped CAS が捨てられても flag が残らない）")
if gate("R2-01"):
    d.rep("全 safety override、SHADOW の全 command 判定、", "全 safety override（FAULT record の payload は trigger 副因を持つ — `R_SAFETY_LAYER_LOST`: HEARTBEAT_TIMEOUT | HEALTH_FAILED、`R_BOUNDARY_DWELL_EXCEEDED`: DWELL_TIMEOUT | ATTEMPTS_EXHAUSTED — doc 06 §6.1 の fault-injection evidence が timeout 経路を要求するため・v0.2.4 R2-01）、SHADOW の全 command 判定、")
if gate("R2-08"):
    d.rep("(i) `permit.profile_hash ∈ accepted_profiles`（登録・受理済 profile の集合。registry の所在と受理権限 = doc 06 OPP-13・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-17）", "(i) `permit.profile_hash ∈ accepted_profiles ∧ permit.profile_hash ∉ revoked_profiles`（登録・受理済かつ未失効の profile。registry の所在・受理権限・失効権限 = doc 06 §8.1 / OPP-13・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-17・v0.2.4 R2-08）")
if gate("R2-15"):
    d.rep("で **genesis record**（`epoch 起点・consumed_offer_ids = ∅・invalidated_lease_ids = ∅`）を書き", "で **genesis record**（`epoch 起点・consumed_offer_ids = ∅・invalidated_lease_ids = ∅・profile_hash`（この genesis が権限づける profile・v0.2.4 R2-15）・role = doc 06 `clearance_roles[GENESIS]`）を書き")
if gate("R2-07"):
    d.rep("の join key（lease 無しでも profile と結線）", "の join key（lease 無しでも profile と結線）。permit 発行時の health-check-run record も lease_id = None・profile_hash 必須（doc 06 §6.1 の audit 範囲解決・v0.2.4 R2-07）")
if gate("R2-17"):
    d.rep("(a) `profile.health_checks` のうち stage ∈ {BEFORE_PERMIT, BOTH} の全 check が pass（失敗 = `R_HEALTHCHECK_FAILED`・permit 不発行）", "(a) `profile.health_checks` のうち stage ∈ {BEFORE_PERMIT, BOTH} の全 check が pass（失敗 = `R_HEALTHCHECK_FAILED`・permit 不発行）。全 stage の check は**各実行の直前**に evaluator の content sha256 を `evaluator_sha256` と再検証し、不一致 = check FAILED（fail_closed・v0.2.4 R2-17）")

rows05 = [("R1-01","command_deadline_s の計時範囲が無い","§4.1 comment・§4.2"),("R1-02","age の起点が初回解決で無意味","§3.4 (e)"),("R1-03","同 tier / 同 reason の SAFEHOLD 遷移が未定義・(iii) が audit 読出しに依存","§3.2 `safehold_disposition`・§3.5・§3.7・§5.2 (iii)・INV-31・T-28"),("R1-05 / R2-03","content hash の照合が 3 参照のみ","§3.4 (j)・§4.3 DEPLOYMENT_WORKSPACE"),("R1-06 / R2-19","ZOH で点評価","§4.3 DEPLOYMENT_WORKSPACE（線分・hold 非依存）"),("R1-07","条件 9 / 10 / ACK 失効に fault・行が無い","§3.7 失敗表 3 行"),("R1-08","§7 INVALID_STATE 行が §3.7 / B5 と不一致","§7"),("R1-09","ISL 行に DISPOSITION record が無い","§3.7"),("R1-10","TRANSFER_TO_EXECUTOR 行の record 集合","§3.7・INV-17"),("R1-11","S_TRANSFER_PENDING の定義・gateway state 列","§3.6・§2"),("R1-12","executor_id が admission に無い","§2・INV-03"),("R1-13","B0 snapshot が MARK_BOUNDARY_WAIT に先行し得る","§6.2 B0・§3.7 失敗表"),("R1-14","executor 発 SAFETY_STABILIZED の解除経路","§5.4 SAFETY 行"),("R1-15 / R2-12","INV-33 の範囲と CD-10 行の from 集合が不一致","INV-33（範囲を明示・boundary 滞留は boundary_dwell_s 側）"),("R1-16","pending_invalidate が残留","§5.2 (ii)"),("R2-01","timeout 束縛の迂回（05 側 = FAULT 副因）","§8 記録義務"),("R2-08","profile の失効経路","§3.4 (i)"),("R2-15","genesis の role / profile_hash","§3.2"),("R2-17","evaluator の実行直前再検証","§3.4 (a)")]
tbl = [f"- **v0.2.4 fold（{NOW}）— v0.2.3 本文への再レビュー round**: reviewer R1（05・contract + runtime lens）/ R2（06・deployment lens）が v0.2.3 を対象に fold 回帰 + 新規反証を実施し、verifier V1 / V2（3 lens・別 context）が全 finding を判定。確定分を fold（refuted は適用せず）。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §7:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in rows05: tbl.append(f"| {i} | {c} | {s if any_conf(*i.split(' / ')) else '— 適用せず'} | {'; '.join(f'{x}={vstr(x)}' for x in i.split(' / '))} |")
tbl.append("| （06 側の fold 行は doc 06 §11） | | | |")
d.insert_before_line("## 14. Review anchors", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= 06
d = Doc("06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("DEPLOYMENT PROFILE SPEC (v0.2.3 REVIEW CANDIDATE)", "DEPLOYMENT PROFILE SPEC (v0.2.4 REVIEW CANDIDATE)")
d.rep("／ v0.2.3 = ", "／ v0.2.4 = %s（`date -u` 実測）／ v0.2.3 = " % NOW)
d.rep("- status: **REVIEW CANDIDATE v0.2.3（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）**", "- status: **REVIEW CANDIDATE v0.2.4（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2.3 → v0.2.4 = v0.2.3 本文への再レビュー round（R1 / R2 → V1 / V2）の確定 finding の fold（§11）。旧版の系譜:")
newP, newPT, newOPP = [], [], []
if gate("R1-04", "R2-05"):
    d.rep("v0.2.3（CD-02）: {SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART} の各 reason に ≥ 1 role が必須（P_CLEARANCE_ROLE_MISSING）", "v0.2.3（CD-02）→ v0.2.4（R1-04 / R2-05）: {SAFETY, SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART}%s の各 reason に ≥ 1 role が必須（P_CLEARANCE_ROLE_MISSING — 05 §5.4 条件 10 の集合と同一。SAFETY の role は ISL clearance record と AND）" % ("（+ GENESIS・R2-15）" if conf("R2-15") else ""))
    d.rep("| `clearance_roles` が {SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART} の各 reason に ≥ 1 role を持つ（SAFETY は ISL clearance record が主・role は AND）（v0.2.3・CD-02） | `P_CLEARANCE_ROLE_MISSING` |", "| `clearance_roles` が {SAFETY, SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART}%s の各 reason に ≥ 1 role を持つ（= 05 §5.4 条件 10 の集合。SAFETY は ISL clearance record と AND）（v0.2.3・CD-02・v0.2.4 R1-04 / R2-05） | `P_CLEARANCE_ROLE_MISSING` |" % ("・GENESIS（R2-15）" if conf("R2-15") else ""))
    d.repline("| PT-22 |", "| PT-22 | `clearance_roles` に SAFETY の role が無い profile（v0.2.3・v0.2.4 で SAFETY を必須集合へ） | `P_CLEARANCE_ROLE_MISSING` |")
if gate("R1-05", "R2-03"):
    d.rep("| `predicate_refs` / `evaluator_ref` の解決内容の sha256 が `predicate_sha256` / `evaluator_sha256` と一致（登録時；第 2 評価点の再照合は 05 `R_PROFILE_MISBOUND`）（v0.2.3・CD-04） | `P_PREDICATE_HASH_MISMATCH` |", "| profile が宣言する**全ての** content hash（`predicate_sha256` / `evaluator_sha256` / `zones[].geometry_sha256` / `calibration_refs[].artifact_sha256` / `gateway_config.artifact_sha256` / `deployment_evidence_policy_hash` / required record の `artifact_sha256`）が解決先の内容と一致（登録時；第 2 評価点の再照合は 05 §3.4 (j) `R_PROFILE_MISBOUND`；gateway は predicate と zone geometry を評価前に再検証）（v0.2.3・CD-04・v0.2.4 R1-05 / R2-03 で全 hash へ一般化） | `P_PREDICATE_HASH_MISMATCH`（名称は据え置き・対象は全宣言 hash） |")
    newPT.append("| PT-27 | 登録後に keep-out zone の geometry artifact を差し替え（v0.2.4） | 次 permit で `R_PROFILE_MISBOUND`・gateway 評価前の再検証で FALSE |")
if gate("R1-06", "R2-19"):
    d.rep("hold = LINEAR_INTERPOLATE のとき直前 admitted setpoint → 新 setpoint の線分（FK 後・TCP 点）、ZERO_ORDER_HOLD のとき点。", "`DIFF_IK_EE_TARGET` では hold 種別にかかわらず直前 admitted setpoint（初回は実測 TCP）→ 新 setpoint の**線分**（FK 後・TCP 点）— ZOH でも腕は連続に動くため点評価では keep-out を跨げる（v0.2.4・R1-06 / R2-19）。")
if gate("R1-15", "R2-12"):
    d.rep("lease を無効化するのは health check 失敗（§5 (a)）", "**profile 起因で** lease を無効化するのは health check 失敗（§5 (a)）")
if gate("R2-01"):
    d.rep("`ack_validity_s ≤ boundary_dwell_s`；`lease_max_duration_s ≥ boundary_dwell_s`（CD-10）。絶対上限は OPP-11", "`ack_validity_s ≤ boundary_dwell_s`；`lease_max_duration_s ≥ boundary_dwell_s`（CD-10）；`manager_liveness_s ≤ command_deadline_s`（LEARNED / SCRIPTED・v0.2.4 R2-01）。絶対上限、および `ack_timeout_s ≤ boundary_dwell_s` / `health_confirm_timeout_s ≤ lease_max_duration_s` の追加順序（verifier V2 = Rs 確認事項）は OPP-11")
    d.rep("| OPP-11 | `RuntimeTimeouts` の**絶対上限**（秒の ceiling）は cell / 規格依存で本 doc は相対順序（`P_TIMEOUT_ORDER`）しか検査しない（v0.2.3・CD-01） |", "| OPP-11 | `RuntimeTimeouts` の**絶対上限**（秒の ceiling）は cell / 規格依存で本 doc は相対順序（`P_TIMEOUT_ORDER`）しか検査しない（v0.2.3・CD-01）。追加候補の順序 `ack_timeout_s ≤ boundary_dwell_s` / `health_confirm_timeout_s ≤ lease_max_duration_s` は Rs 確認後に足す（v0.2.4・R2-01 / V2） |")
    d.rep("R_HEALTH_CONFIRM_TIMEOUT, R_BOUNDARY_DWELL_EXCEEDED}   # v0.2.3（CD-01）: timeout 駆動の fault は同一 profile_hash の下で commissioning 時に必ず発火させる", "R_HEALTH_CONFIRM_TIMEOUT, R_BOUNDARY_DWELL_EXCEEDED, R_LEASE_DURATION_EXCEEDED, R_MANAGER_UNAVAILABLE}   # v0.2.3（CD-01）+ v0.2.4（R2-01）: timeout 駆動の fault は同一 profile_hash の下で commissioning 時に必ず発火させる。\n#   timeout 駆動 code の FAULT_INJECTION_RESULT は subject_ref = '<code>#<timeout_trigger>'（例 R_SAFETY_LAYER_LOST#HEARTBEAT_TIMEOUT・R_BOUNDARY_DWELL_EXCEEDED#DWELL_TIMEOUT）で timeout 経路そのものを要求する（health==failed / attempts 尽きの別経路で代替できない — 05 §8 FAULT payload の trigger 副因と照合・v0.2.4 R2-01）")
if gate("R2-02"):
    d.insert_after_line("| required record の `valid_until_iso8601`", "| FAULT_INJECTION_RESULT / HEALTH_CHECK_RUN の `artifact_ref` が解決する audit 範囲に、`kind = FAULT ∧ fault == subject_ref の code ∧ profile_hash 一致`（fault）／ `kind ∈ {HEALTH_CONFIRMED, HEALTH_FAILED} ∧ payload に check_id`（health）の `RuntimeAuditRecord` が ≥ 1 件（第 2 評価点・v0.2.4 R2-02） | `P_FAULT_EVIDENCE_UNVERIFIED` |")
    newP.append("`P_FAULT_EVIDENCE_UNVERIFIED`"); newPT.append("| PT-28 | FAULT_INJECTION_RESULT の artifact_ref が当該 fault を含まない audit 範囲を指す（v0.2.4） | `P_FAULT_EVIDENCE_UNVERIFIED` |")
if gate("R2-04"):
    d.rep("class CellIdentity:\n    cell_id: str\n    site_id: str\n    robot_model_ref: str                   # RS71 §0 の型式（UR15）と一致必須（不一致 = P_ROBOT_MODEL_MISMATCH・v0.2.1）— DDR#41 の曝露点（§10 OPP-7）\n    base_frame_ref: str                    # v0.2.1（C-11）: 空間項（workspace / tool CoM / envelope）の基準 frame。全 spatial field はこの frame か tool_flange で表す\n    robot_serial_ref: str\n    controller_firmware_ref: str\n",
          "class CellIdentity:\n    cell_id: str\n    site_id: str\n    robot_model_ref: str                   # RS71 §0 の型式（UR15）と一致必須（不一致 = P_ROBOT_MODEL_MISMATCH・v0.2.1）— DDR#41 の曝露点（§10 OPP-7）。全 arm 共通\n    base_frame_ref: str                    # v0.2.1（C-11）: 空間項（workspace / tool CoM / envelope）の基準 frame。全 spatial field はこの frame か tool_flange で表す\n    arms: tuple[ArmSpec, ...]              # v0.2.4（R2-04）: DUAL-ARM cell（RS71 §0 不変前提）を表現できるよう arm 単位に識別・envelope・tool・TCP を持つ（旧 robot_serial_ref / controller_firmware_ref / controller / tool_payload は ArmSpec へ移設）\n" + ("    safety_layer_ref: str                  # v0.2.4（R2-09）: IndependentSafetyLayer の identity（version / build）— SAFETY_LAYER_ACCEPTANCE.subject_ref と SAFETY_LAYER_IDENTITY health check の照合先\n" if conf("R2-09") else ""))
    d.rep("@dataclass(frozen=True)\nclass ControllerEnvelope:", "@dataclass(frozen=True)\nclass ArmSpec:                             # v0.2.4（R2-04）: 1 arm = frozen ControlResourceSpec の key 1 つ\n    resource_id: str                       # \"ee_left\" | \"ee_right\"（frozen ControlResourceSpec の key・%s:142）。arms 内で一意\n    robot_serial_ref: str\n    controller_firmware_ref: str\n    controller: ControllerEnvelope         # この arm の運動学上限（関節数 = robot_model_ref）\n    tool_payload: ToolPayloadSpec          # この arm の tool（gripper_* 資源に対応）。TCP は tool_payload.tcp_offset_ref（arm ごとに kind = TCP の calibration_refs entry・P_TCP_REF_UNRESOLVED）\n\n@dataclass(frozen=True)\nclass ControllerEnvelope:" % A)
    d.rep("    cell: CellIdentity\n    controller: ControllerEnvelope\n    tool_payload: ToolPayloadSpec\n    workspace: WorkspaceRestriction\n", "    cell: CellIdentity                     # v0.2.4（R2-04）: controller / tool_payload は cell.arms[] へ移設\n    workspace: WorkspaceRestriction\n")
    d.rep("| `ControllerEnvelope` の tuple 長 = `robot_model_ref` の関節数 | `P_ENVELOPE_SHAPE` |", "| 各 `arms[].controller` の tuple 長 = `robot_model_ref` の関節数（arm ごと・v0.2.4） | `P_ENVELOPE_SHAPE` |\n| `resource_availability.control` で True の `ee_left` / `ee_right` ごとに `cell.arms` に `resource_id` が一致する entry がちょうど 1 つ（gripper_* は当該 arm の tool_payload）。arm 単位の identity / envelope / TCP を持たない資源を offered にできない（v0.2.4・R2-04 — 単一 robot 限定案は RS71 §0 DUAL-ARM 不変前提と衝突するため不採用・OPP-15） | `P_ARM_COVERAGE` |")
    d.rep("CONTROLLER_IDENTITY = controller が報告する serial / firmware と CellIdentity.{robot_serial_ref, controller_firmware_ref} の等値（LIVENESS ≠ identity）。ENVELOPE_READBACK = controller 側に設定された運動学上限の readback と ControllerEnvelope の等値", "CONTROLLER_IDENTITY = 各 arm の controller が報告する serial / firmware と `arms[].{robot_serial_ref, controller_firmware_ref}` の等値（LIVENESS ≠ identity・arm ごとに評価・v0.2.4 R2-04）。ENVELOPE_READBACK = 各 arm の controller 側に設定された運動学上限の readback と `arms[].controller` の等値")
    d.rep("                            , CONTROLLER(profile.controller)          … joint space", "                            , CONTROLLER(profile.cell.arms[cmd.resource].controller)  … joint space（command が指す arm の envelope・v0.2.4 R2-04）")
    newP.append("`P_ARM_COVERAGE`"); newPT.append("| PT-29 | `resource_availability.control = {ee_left: True, ee_right: True, …}` で `cell.arms` が 1 entry（v0.2.4） | `P_ARM_COVERAGE` |")
    newOPP.append("| OPP-15 | DUAL-ARM cell の profile 表現（v0.2.4・R2-04）: 本 doc は arm 単位の `ArmSpec` を採用（案 B）。単一 robot 限定（案 A）は RS71 §0 DUAL-ARM 不変前提と衝突するため不採用。arm 間の共有 workspace / 相互干渉 zone の扱いは未裁定 | RS71 §0・§2.1 | Rs 確認事項（不変前提に触れないことの確認） |")
if gate("R2-06"):
    d.insert_after_line("| `clearance_roles` が ", "| mandatory kind の各 `check_id` について、誘発した不一致で `R_HEALTHCHECK_FAILED` / HEALTH_FAILED を出した negative-control の HEALTH_CHECK_RUN record（artifact_ref → 当該 record を含む audit 範囲）が CLOSED_LOOP lease 前に存在（constant-True evaluator の排除・v0.2.4 R2-06） | `P_EVIDENCE_UNBOUND`（subject = check_id#NEGATIVE） |")
    d.rep("| OPP-9 | `HealthCheckSpec.evaluator_ref` の登録・版管理（EP の evaluator registry を流用しない） | EP `evaluator_registry_rule` は certification 用 | 別 registry（名前空間を分ける）— 内容は impl 解錠後 |", "| OPP-9 | `HealthCheckSpec.evaluator_ref` の登録・版管理（EP の evaluator registry を流用しない）。kind 認証済 evaluator registry が無い間、`P_HEALTHCHECK_MISSING` は kind label の存在検査に過ぎず、evaluator の意味は negative-control evidence（§3・v0.2.4 R2-06）で担保する | EP `evaluator_registry_rule` は certification 用 | 別 registry（名前空間を分ける）— 内容は impl 解錠後 |")
if gate("R2-07"):
    d.rep("kind ∈ {HEALTH_CHECK_RUN, FAULT_INJECTION_RESULT} では 05 RuntimeAuditRecord の (lease_id, seq 範囲) に解決する（audit trail への束縛）", "kind ∈ {HEALTH_CHECK_RUN, FAULT_INJECTION_RESULT} では 05 RuntimeAuditRecord の (lease_id | None, seq 範囲) に解決し、範囲内の全 record が `profile_hash == 本 record の profile_hash` を持つ（INITIAL SAFEHOLD から走る BEFORE_PERMIT check や lease 無しで誘発する fault は lease_id = None = 05 §8 `profile_hash` join・v0.2.4 R2-07）")
if gate("R2-08"):
    d.rep("(2) profile の受理（`profile_hash` の登録 = `accepted_profiles` への追加・registry と受理権限は OPP-13）は全 `P_*` = 0 が前提。", "(2) profile の受理（`profile_hash` の登録 = `accepted_profiles` への追加・registry と受理権限は OPP-13）は全 `P_*` = 0 が前提。registry の状態 = {ACCEPTED, REVOKED}: 失効（revocation）は `clearance_roles` の role による `RuntimeAuditRecord`（kind = CLEARANCE_RECORDED・payload に revoked profile_hash）で行い、05 §3.4 (i) は `∉ revoked_profiles` を要求する。cell の変更（layout / tooling / incident）後に旧 profile が permit 可能なまま残る経路を閉じる（v0.2.4・R2-08）。")
    d.rep("| OPP-13 | profile の **registry**", "| OPP-13 | profile の **registry**（失効の権限 = 誰が REVOKED にできるか・v0.2.4 R2-08 を含む）")
if gate("R2-09"):
    d.rep("| GATEWAY_CONFIG_MATCH | ENVELOPE_READBACK | CONTROLLER_IDENTITY\n", "| GATEWAY_CONFIG_MATCH | ENVELOPE_READBACK | CONTROLLER_IDENTITY | SAFETY_LAYER_IDENTITY\n#   v0.2.4（R2-09）: SAFETY_LAYER_IDENTITY = IndependentSafetyLayer が報告する version / build と CellIdentity.safety_layer_ref の等値（heartbeat ≠ identity）\n")
    if not conf("R2-04"):
        d.rep("    layout_revision_ref: str               # cell layout の版（keep-out の前提）", "    layout_revision_ref: str               # cell layout の版（keep-out の前提）\n    safety_layer_ref: str                  # v0.2.4（R2-09）: IndependentSafetyLayer の identity（version / build）— SAFETY_LAYER_ACCEPTANCE.subject_ref と SAFETY_LAYER_IDENTITY health check の照合先")
    d.rep("{SAFETY_LAYER_HEARTBEAT, CONTROLLER_LIVENESS, ENVELOPE_READBACK, GATEWAY_CONFIG_MATCH, CONTROLLER_IDENTITY, TOOL_IDENTITY} の各 kind が ≥ 1", "{SAFETY_LAYER_HEARTBEAT, SAFETY_LAYER_IDENTITY, CONTROLLER_LIVENESS, ENVELOPE_READBACK, GATEWAY_CONFIG_MATCH, CONTROLLER_IDENTITY, TOOL_IDENTITY} の各 kind が ≥ 1（v0.2.4 R2-09 で SAFETY_LAYER_IDENTITY 追加）")
    newPT.append("| PT-30 | SAFETY_LAYER_ACCEPTANCE 後に IndependentSafetyLayer を更新して permit 要求（v0.2.4） | SAFETY_LAYER_IDENTITY fail → 05 `R_HEALTHCHECK_FAILED` |")
if gate("R2-10"):
    d.rep("(xi) envelope / zone / predicate を空虚にする — `P_ENVELOPE_NONPOSITIVE` / `P_WORKSPACE_EMPTY` / `P_ENVELOPE_EXCEEDS_MEASURED` / `P_PREDICATE_HASH_MISMATCH`。", "(xi) envelope / zone を空虚にする — `P_ENVELOPE_NONPOSITIVE` / `P_WORKSPACE_EMPTY` / `P_ENVELOPE_EXCEEDS_MEASURED`（`predicate_refs = ()` は許す = 静的 restriction 無し・live 決定は ISL のみ。空虚化の検査対象は zone / envelope であり predicate の内容差し替えは `P_PREDICATE_HASH_MISMATCH`・v0.2.4 R2-10）。")
if gate("R2-11"):
    d.rep("| `ControllerEnvelope` の各上限 ≤ `CONTROLLER_ENVELOPE_MEASUREMENT` record の測定値（artifact schema = ControllerEnvelope と同一 field・登録時に照合） | `P_ENVELOPE_EXCEEDS_MEASURED` |", "| `ControllerEnvelope` の各上限 ≤ `CONTROLLER_ENVELOPE_MEASUREMENT` record の測定値（artifact schema = ControllerEnvelope と同一 field）。評価点 = **第 2 評価点・`proposed_lease.mode == CLOSED_LOOP_AUTHORITY` のとき**（登録時 = MIN_SHADOW には測定 record が無い・v0.2.4 R2-11） | `P_ENVELOPE_EXCEEDS_MEASURED` |")
if gate("R2-13"):
    d.rep('    frame_ref: str = ""                    # v0.2.1（C-11）: == CellIdentity.base_frame_ref（gateway の FK 変換の目標 frame）', "    frame_ref: str                         # v0.2.1（C-11）: == CellIdentity.base_frame_ref（gateway の FK 変換の目標 frame）。v0.2.4（R2-13）: default 無し（欠落 = codec 拒否）")
if gate("R2-14"):
    d.insert_after_line("| `fault_injection[].runtime_fault_code` ∉ 05", "| `required_before_shadow_lease` に HEALTH_CHECK_RUN / FAULT_INJECTION_RESULT を含む、または `fault_injection[].must_be_exercised_before == SHADOW_NON_AUTHORITY`（lease でしか作れない evidence を最初の lease の前提にする循環・schema 1.0）（v0.2.4・R2-14。非単調（CLOSED_LOOP 集合 ⊉ SHADOW 集合）は MIN_CLOSED_LOOP が全 8 kind を含むため 1.0 では表現不能 — code を足さない） | `P_EVIDENCE_POLICY_CIRCULAR` |")
    newP += ["`P_EVIDENCE_POLICY_CIRCULAR`"]
    newPT.append("| PT-31 | `must_be_exercised_before = SHADOW_NON_AUTHORITY` の fault_injection 要件（v0.2.4） | `P_EVIDENCE_POLICY_CIRCULAR` |")
if gate("R2-15"):
    d.rep("# (safehold_reason, role) — SAFETY / SAFE_STOP / CHECKPOINT_DISABLED / MANAGER_RESTART / GATEWAY_RESTART の解除に要する **追加の** role（05 §5.4）。", "# (safehold_reason, role) — SAFETY / SAFE_STOP / CHECKPOINT_DISABLED / MANAGER_RESTART / GATEWAY_RESTART の解除、および GENESIS（05 §3.2 genesis record の権限・v0.2.4 R2-15）に要する **追加の** role（05 §5.4）。")
if gate("R2-16"):
    subj = (("arms[].controller_firmware_ref（arm ごと）", "arms[].tool_payload.tool_id（arm ごと）") if conf("R2-04") else ("cell.controller_firmware_ref", "tool_payload.tool_id")) + (("cell.safety_layer_ref",) if conf("R2-09") else ("cell.cell_id（ISL identity 未宣言）",))
    d.rep("    subject_ref: str                       # cell_id / controller_firmware_ref / tool_id / calibration_id / config_id / check_id / fault code", "    subject_ref: str                       # kind ごとに定義（v0.2.4・R2-16）: CELL_COMMISSIONING = cell.cell_id / CONTROLLER_ENVELOPE_MEASUREMENT = %s / TOOL_PAYLOAD_IDENTIFICATION = %s / GATEWAY_CONFIG_ATTESTATION = gateway_config.config_id / SAFETY_LAYER_ACCEPTANCE = %s / CALIBRATION_RECORD = calibration_id / HEALTH_CHECK_RUN = check_id / FAULT_INJECTION_RESULT = fault code（timeout 駆動は '<code>#<trigger>'）" % subj)
if gate("R2-17"):
    d.rep("    evaluator_sha256: str                  # v0.2.3（CD-04）: evaluator 内容の content hash（第 2 評価点で照合・不一致 = R_PROFILE_MISBOUND）", "    evaluator_sha256: str                  # v0.2.3（CD-04）: evaluator 内容の content hash（第 2 評価点で照合・不一致 = R_PROFILE_MISBOUND）。v0.2.4（R2-17）: 各実行の直前にも再検証し、不一致 = check FAILED（fail_closed）")
if gate("R2-18"):
    d.insert_after_line("| required record の `valid_until_iso8601`", "| `CalibrationRef.valid_until_iso8601`、および required record のうち kind ∈ {CALIBRATION_RECORD, SAFETY_LAYER_ACCEPTANCE} の `valid_until_iso8601` が None（無期限）（v0.2.4・R2-18） | `P_VALIDITY_UNBOUNDED` |")
    d.rep("    valid_until_iso8601: str | None\n\n@dataclass(frozen=True)\nclass FaultInjectionRequirement:", "    valid_until_iso8601: str | None        # v0.2.4（R2-18）: None の意味 = 失効なし（期限検査の対象外）。ただし kind ∈ {CALIBRATION_RECORD, SAFETY_LAYER_ACCEPTANCE} の required record と CalibrationRef は None 不可（P_VALIDITY_UNBOUNDED）\n\n@dataclass(frozen=True)\nclass FaultInjectionRequirement:")
    newP.append("`P_VALIDITY_UNBOUNDED`"); newPT.append("| PT-32 | TCP calibration を `valid_until = None` で宣言（v0.2.4） | `P_VALIDITY_UNBOUNDED` |")
if newP:
    cl = d.line("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`"); d.repline("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`", cl + " / " + " / ".join(newP) + "（v0.2.4）")
if newPT: d.insert_after_line("| PT-26 |", "\n".join(newPT))
if newOPP: d.insert_after_line("| OPP-14 |", "\n".join(newOPP))
rows06 = [("R1-04 / R2-05","SAFETY の clearance role が 05 で必須・06 で任意","§2.1・§3・PT-22"),("R1-05 / R2-03","content hash の照合が 3 参照のみ","§3（全宣言 hash）・PT-27"),("R1-06 / R2-19","ZOH で点評価","§4"),("R1-15 / R2-12","§8.1 規則 (3) の「のみ」","§8.1"),("R2-01","timeout 束縛の迂回（別経路・欠落 code・順序漏れ）","§3 `P_TIMEOUT_ORDER`・§6.1"),("R2-02","fault / health evidence の内容未検証","§3 `P_FAULT_EVIDENCE_UNVERIFIED`・PT-28"),("R2-04","単一 robot しか表現できない（DUAL-ARM 不変前提）","§2.1 `ArmSpec`・§3 `P_ARM_COVERAGE`・§4・PT-29・OPP-15"),("R2-06","constant-True evaluator が通る","§3 negative-control・OPP-9"),("R2-07","BEFORE_PERMIT の evidence が lease_id 必須で不成立","§6.1"),("R2-08","profile の失効経路が無い","§8.1・OPP-13"),("R2-09","ISL の identity が無い","§2.1 `safety_layer_ref`・SAFETY_LAYER_IDENTITY・PT-30"),("R2-10","(xi) の predicate 空虚化検査が空振り","§3 (xi)"),("R2-11","P_ENVELOPE_EXCEEDS_MEASURED の評価点","§3"),("R2-13","frame_ref の default","§2.1"),("R2-14","evidence policy の循環（非単調は 1.0 で表現不能）","§3 `P_EVIDENCE_POLICY_CIRCULAR`・PT-31"),("R2-15","genesis の role","§2.1"),("R2-16","singleton kind の subject","§6.1"),("R2-17","evaluator の実行直前再検証","§2.1"),("R2-18","無期限 calibration / acceptance","§3 `P_VALIDITY_UNBOUNDED`・PT-32")]
tbl = [f"- **v0.2.4 fold（{NOW}）— v0.2.3 本文への再レビュー round（R1 / R2 → V1 / V2）の確定 finding を fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §7:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in rows06: tbl.append(f"| {i} | {c} | {s if any_conf(*i.split(' / ')) else '— 適用せず'} | {'; '.join(f'{x}={vstr(x)}' for x in i.split(' / '))} |")
d.insert_before_line("## 12. Review anchors", "\n".join(tbl) + "\n")
d.save()
for name in ("07_SUCCESSOR_CONTRACT_DECISION_20260903.md", "04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md", "08_INDEPENDENT_REVIEW_PLAN_20260903.md"):
    d = Doc(name); d.rep("(v0.2.3 REVIEW CANDIDATE)", "(v0.2.4 REVIEW CANDIDATE)"); d.rep("REVIEW CANDIDATE v0.2.3（", "REVIEW CANDIDATE v0.2.4（"); d.save()
print("applied:", applied); print("NOW =", NOW)
