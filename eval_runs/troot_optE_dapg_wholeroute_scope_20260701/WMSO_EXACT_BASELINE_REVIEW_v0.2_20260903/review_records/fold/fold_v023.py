#!/usr/bin/env python3
"""v0.2.2 -> v0.2.3 fold (records-only; frozen files untouched).
Inputs: <PKG_DIR> <verdicts_v023.json>  where verdicts = {finding_id: {"confirmed": bool, "severity": str, "fold_status": str}}
Applies: (1) verifier verdict stamping into the v0.2.2 fold tables (05/06/07/04/08),
         (2) the 12 PARTIAL residuals named by the verifiers (all verified CONFIRMED),
         (3) reviewer C findings CD-01..CD-18 — each block applied only if verdicts[id].confirmed is True.
Every anchor replacement asserts uniqueness (fail-closed)."""
import sys, json, re, subprocess

P = sys.argv[1]; VERD = json.load(open(sys.argv[2]))
NOW = subprocess.check_output(["date", "-u", "+%Y-%m-%d %H:%M UTC"]).decode().strip()
A = "$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md"
B = "$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md"
D0 = "$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md"

def conf(i): return bool(VERD.get(i, {}).get("confirmed"))
def vstr(i):
    v = VERD.get(i)
    if not v: return "（verifier 未了）"
    if not v["confirmed"]: return f"refuted（{v['severity']}）"
    fs = v.get("fold_status", "")
    if fs in ("", "NOT_APPLICABLE"): return f"CONFIRMED（{v['severity']}）"
    return f"CONFIRMED（{v['severity']}）/ v0.2.2 fold = {fs}" + ("→ v0.2.3 で残差処置" if fs == "PARTIAL" else "")

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
    def stamp(self):
        pat = re.compile(r"((?:A2|A|B2|B)-[HML]?\d+)=起草者再検証=CONFIRMED（独立 verifier 未了・11_ §4）")
        self.t, n = pat.subn(lambda m: f"{m.group(1)}={vstr(m.group(1))}", self.t); return n
    def save(self): open(f"{P}/{self.name}", "w", encoding="utf-8").write(self.t); print("wrote", self.name)

applied, skipped = [], []
def gate(i):
    (applied if conf(i) else skipped).append(i); return conf(i)

# ======================================================================= 05
d = Doc("05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md")
n = d.stamp(); print("05 stamped", n)
d.rep("RUNTIME SPEC (v0.2.2 REVIEW CANDIDATE)", "RUNTIME SPEC (v0.2.3 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.1 = 陽性対照レビューの注入外 finding の fold／ v0.2.1 → v0.2.2 = 3 軸独立レビュー（A / A2 / B / B2 / C）の確定 finding の fold（§13）",
      "- status: **REVIEW CANDIDATE v0.2.3（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.1 = 陽性対照レビューの注入外 finding の fold／ v0.2.1 → v0.2.2 = 3 軸独立レビュー（A / A2 / B / B2）の finding の fold／ v0.2.2 → v0.2.3 = 独立 verifier（3 lens）の verdict 反映 + PARTIAL 残差の処置 + 軸 C（v0.2.2 対象）finding の fold（§13・全体記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`）")
d.rep("→ **3 軸独立レビューの確定 finding の fold = 本版 v0.2.2（§13）**", "→ 3 軸独立レビュー（A / A2 / B / B2）finding の fold = v0.2.2（2026-09-04 15:41 UTC）→ **verifier verdict + 残差 + 軸 C の fold = 本版 v0.2.3（§13）**")

# ---- PARTIAL residuals (all verifier-confirmed)
# A-10: §6.1 CHECKPOINT row
d.rep("**v0.2 では受理のみ・再選択を開始しない（fail-closed）**: TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED)・fault `R_CHECKPOINT_SWITCH_DISABLED`・disposition `HOLD`。",
      "**v0.2 では受理のみ・再選択を開始しない（fail-closed）**: reason ∈ {PLANNED_SWITCH, EVENT} ⇒ TRANSFER_TO_SAFEHOLD(CHECKPOINT_DISABLED)・fault `R_CHECKPOINT_SWITCH_DISABLED`・disposition `HOLD`；reason == SAFETY_STABILIZED ⇒ TRANSFER_TO_SAFEHOLD(SAFETY)・fault なし（§3.7・§5.4 SAFETY 行と同一・v0.2.3 A-10 残差）。")
# A2-12: rule 3
d.rep("runtime は `R_OFFER_INVALID` / `R_INVOCATION_INVALID` で包んで disposition に写す", "runtime は `R_OFFER_INVALID` / `R_INVOCATION_INVALID` / `R_OUTCOME_INVALID`（validate_outcome・v0.2.3 A2-12 残差）で包んで disposition に写す")
# B-M1 / B2-04: retry paragraph sentence + INV-24 + §5.2 (ii)
d.rep("再試行中も gateway 出力は §5.2 (i)（safety 決定）または (iii) に既に落ちているため、CONFLICT の間に executor lease が actuation を再開することは無い（INV-24）。",
      "**再試行中の gateway 出力（v0.2.3・B-M1 / B2-04 残差）**: safety 起因（SAFETY / SAFE_STOP）の CONFLICT では §5.2 (i) / (i′) / (iii) に既に落ちている。非 safety 起因（EXECUTOR_LOST / HEALTH_FAIL / DEADLINE_MISS / TIMING_VIOLATION / ENVELOPE_VIOLATION / CHECKPOINT_DISABLED / NO_CHAIN）では、CommandGateway は trigger を検出した時点で局所 flag `pending_invalidate` を立てて (iii) に落ち、再試行 CAS が SUCCESS するまで (ii) を評価しない（executor command の再 admit は無い）。manager 単独検出（EXECUTOR_LOST 等）で gateway への通知が CAS 完了より遅れる窓に限り、既 admit の setpoint 保持が最大 `command_deadline_s` 続き得る（新 command の admit は無い — INV-24）。")
d.repline("| INV-24 |", "| INV-24 | TRANSFER_TO_SAFEHOLD の CONFLICT は必ず再試行される。CONFLICT 中の出力: safety 起因 = (i) / (i′) / (iii)；非 safety 起因 = gateway が検出時点で `pending_invalidate` により (iii)（(ii) を評価しない）。manager 単独検出で gateway 未通知の窓に限り既 admit setpoint の保持が最大 `command_deadline_s` 続き得る（新 command の admit は無い）（v0.2.1・B-04・v0.2.3 B-M1 / B2-04） | 設計違反（test） |")
d.rep("  (ii)  else if owner == EXECUTOR ∧ ¬state.boundary_wait ∧ ¬restart_pending ∧ mode == CLOSED_LOOP_AUTHORITY ∧ 直近 admitted command あり → その setpoint（hold は admitted 間のみ・§4.2）",
      "  (ii)  else if owner == EXECUTOR ∧ ¬state.boundary_wait ∧ ¬restart_pending ∧ ¬pending_invalidate ∧ mode == CLOSED_LOOP_AUTHORITY ∧ 直近 admitted command あり → その setpoint（hold は admitted 間のみ・§4.2。`pending_invalidate` = gateway が TRANSFER_TO_SAFEHOLD の trigger を検出してから再試行 CAS の SUCCESS を観測するまで True・v0.2.3 B-M1 / B2-04）")
# B-M2: R_MANAGER_RESTART row + T-09
d.rep("| AuthorityManager crash/restart | manager（起動時） | `R_MANAGER_RESTART` | durable state を読み `epoch := persisted + 1`・owner := SAFEHOLD・全 lease 無効・全 permit VOID。durable state 不読 ⇒ 起動拒否 |",
      "| AuthorityManager crash/restart | manager（起動時） | `R_MANAGER_RESTART` | durable state を読む。persisted owner が EXECUTOR、または persisted が SAFEHOLD で reason が MANAGER_RESTART より弱いときのみ `epoch := persisted + 1`・owner := SAFEHOLD(MANAGER_RESTART)；persisted が SAFEHOLD(SAFETY / SAFE_STOP) なら reason と epoch を保持（INV-30 / T-28・v0.2.3 B-M2 残差）。いずれも全 lease 無効・全 permit VOID。durable state 不読 ⇒ 起動拒否 |")
d.repline("| T-09 |", "| T-09 | AuthorityManager kill → restart | persisted = EXECUTOR or 弱い reason: epoch = persisted + 1・owner = SAFEHOLD(MANAGER_RESTART)・旧 lease 無効；persisted = SAFEHOLD(SAFETY / SAFE_STOP): reason・epoch 保持（INV-30）。durable 不読 ⇒ 起動拒否（v0.2.3 B-M2 残差） |")
# B-L3: record obligation + AuditKind comment
d.rep("全 safety override、SHADOW の全 command 判定。欠落 = INV-17 違反。", "全 safety override、SHADOW の全 command 判定、**CLOSED_LOOP lease の全 admitted command（`COMMAND_ADMITTED`・`GatewayCommand` payload・v0.2.3 B-L3 残差）**。欠落 = INV-17 違反。")
d.rep("    COMMAND_ADMITTED   # v0.2.2（B-L3）: CLOSED_LOOP lease の admitted command（GatewayCommand 参照）（B-13）: CAS の CONFLICT/REJECTED も CAS_ATTEMPT で記録・clearance / genesis は独立 kind",
      "    COMMAND_ADMITTED   # v0.2.2（B-L3）: CLOSED_LOOP lease の admitted command（GatewayCommand 参照・記録義務 = §8 本文）\n    # v0.2.1（B-13）: CAS の CONFLICT/REJECTED も CAS_ATTEMPT で記録・clearance / genesis は独立 kind")
# B2-05: ISL reason SAFETY + (iii)
d.rep("（(iii) は `safehold_reason == SAFE_STOP` で SafeStop を出す）。", "（(iii) は `safehold_reason == SAFE_STOP` で SafeStop を出す）。**例外（v0.2.3・B2-05 残差）**: IndependentSafetyLayer 起因の遷移（STOP 決定・heartbeat 欠落）は reason SAFETY を保つ（SafeStop 出力は (i) / (i′) から出る）。(iii) は `safehold_reason == SAFETY` でも、当該 SAFEHOLD 遷移の記録 disposition が SAFE_STOP なら §5.4 SAFETY 行の clearance record が記録されるまで SafeStop を出す（heartbeat が戻り (i′) が外れても SafeHold に緩まない）。")
d.rep("  (iii) else SafeHold（safehold_reason == SAFE_STOP なら SafeStop）", "  (iii) else SafeHold（safehold_reason == SAFE_STOP なら SafeStop；safehold_reason == SAFETY かつ当該遷移の記録 disposition が SAFE_STOP なら clearance record まで SafeStop・v0.2.3 B2-05）")
# B2-14: age referent
d.rep("`granted == True ∧ age ≤ decision_max_age_s`（違反 = `R_AUTHORITY_DECISION_ABSENT`・v0.2.2・B2-14）",
      "`granted == True ∧ age ≤ decision_max_age_s`（違反 = `R_AUTHORITY_DECISION_ABSENT`・v0.2.2・B2-14）。**age の基準（v0.2.3・B2-14 残差）**: `age = now(manager) − t_mono`、`t_mono` = manager が当該 `authority_decision_ref` を最初に解決した時に記録した `RuntimeAuditRecord`（kind = ASSESSMENT・payload = decision ref）の `t_mono`（frozen `AuthorityDecision` は timestamp を持たない `%s:351`）。その record が無い decision は不在として扱う（`R_AUTHORITY_DECISION_ABSENT`）" % A)
# B2-17: T-17
d.repline("| T-17 |", "| T-17 | audit 完全性: (事象, その §3.7 行が要求する record kind) ↔ record の全単射（欠落なし・重複なし）（v0.2.3・B2-17 残差） | INV-17 |")

# ---- C findings (05 side)
if gate("CD-12"):
    d.rep("profile は有限値への強化のみ可（有限 → None は `P_FRESHNESS_RELAXED`・doc 06）", "profile は有限値への強化のみ可（profile None = 強化なし = frozen 値が執行値；`P_FRESHNESS_RELAXED` ⇔ `p > f` — doc 06 §3 が SSOT・v0.2.3 CD-12）")
if gate("CD-13"):
    d.repline("| INV-22 |", "| INV-22 | `TimingBinding` の profile 由来 field（`RuntimeTimeouts` の全 field — v0.2.3 CD-13 で列挙から「全 field」へ）は `profile_hash` 由来で lease に写され、本 doc に数値定数は無い | R_PROFILE_MISBOUND |")
    d.rep("ReadinessAck.valid_until = t_ack + ack_validity_s（profile 由来）", "ReadinessAck.valid_until = t_receive + ack_validity_s（manager clock・§3.2 clock domain・profile 由来・v0.2.3 CD-13）")
if gate("CD-10"):
    d.rep("    inter_command_jitter_s: CanonicalDecimal          # v0.2.2（B-L2）: inter-command 間隔の許容偏差（超過 = R_TIMING_VIOLATION）",
          "    inter_command_jitter_s: CanonicalDecimal          # v0.2.2（B-L2）: inter-command 間隔の許容偏差（超過 = R_TIMING_VIOLATION）\n    lease_max_duration_s: CanonicalDecimal            # v0.2.3（CD-10）: lease 活性時間の上限（超過 = R_LEASE_DURATION_EXCEEDED → TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION)）")
    d.insert_after_line("| any (EXECUTOR) | `R_COMMAND_KIND_MISMATCH` が連続", "| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` | lease 活性時間（LEASE_ACTIVATED からの経過）が `lease_max_duration_s` を超過（v0.2.3・CD-10 — WAIT / TIMEOUT 非宣言 skill でも lease は有限） | TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION) | `S_SAFEHOLD(TIMING_VIOLATION)` | FAULT(R_LEASE_DURATION_EXCEEDED), DISPOSITION(HOLD) |")
    d.insert_after_line("| IndependentSafetyLayer の heartbeat 欠落 / health failed（v0.2.2・B2-01） |", "| lease 活性時間が `lease_max_duration_s` 超過（v0.2.3・CD-10） | AuthorityManager | `R_LEASE_DURATION_EXCEEDED` | TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION)・lease 無効 | `HOLD`（解除 = §5.4 TIMING_VIOLATION 行 = 完全経路） |")
    d.rep("    R_MIDSKILL_TRANSFER_BLOCKED | R_SAFETY_LAYER_LOST | R_OUTCOME_INVALID | R_BOUNDARY_DWELL_EXCEEDED   # v0.2.2",
          "    R_MIDSKILL_TRANSFER_BLOCKED | R_SAFETY_LAYER_LOST | R_OUTCOME_INVALID | R_BOUNDARY_DWELL_EXCEEDED |   # v0.2.2\n    R_LEASE_DURATION_EXCEEDED   # v0.2.3（CD-10）")
    d.rep("| OP-19 | 活性 lease 中の calibration / evidence 失効の検出（既定 = 次の permit 発行時・曝露 ≤ 1 skill）。", "| OP-19 | 活性 lease 中の calibration / evidence 失効の検出（既定 = 次の permit 発行時・曝露 ≤ 1 skill かつ ≤ `lease_max_duration_s`・v0.2.3 CD-10）。")
    d.insert_after_line("| INV-32 |", "| INV-33 | 全 lease の活性時間は `lease_max_duration_s` 以下（超過 = TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION) + `R_LEASE_DURATION_EXCEEDED`）— WAIT を含む（v0.2.3・CD-10） | R_LEASE_DURATION_EXCEEDED |")
    d.insert_after_line("| T-31 |", "| T-32 | WAIT lease を `lease_max_duration_s` 超過まで放置（v0.2.3） | TRANSFER_TO_SAFEHOLD(TIMING_VIOLATION)・R_LEASE_DURATION_EXCEEDED・lease 無効（INV-33） |")
pre_g = []
if gate("CD-05"): pre_g.append("(g) `∃ e ∈ profile.binding_expectations: e.skill_action_id == proposed_lease.skill_action_id ∧ e.tensor_binding_hash == proposed_lease.timing.tensor_binding_hash ∧ e.control_mode == proposed_lease.control_mode`（未 commissioning の skill は lease 不可・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-05）")
if gate("CD-06"): pre_g.append("(h) `proposed_lease.ownership.control ⊆ profile.resource_availability.control ∧ (ownership.contact ⇒ resource_availability.contact)`（chained handoff の offer が cell に無い資源を主張する経路を閉じる・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-06）")
if gate("CD-17"): pre_g.append("(i) `permit.profile_hash ∈ accepted_profiles`（登録・受理済 profile の集合。registry の所在と受理権限 = doc 06 OPP-13・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-17）")
if gate("CD-04"): pre_g.append("(j) profile が参照する外部内容（`predicate_refs` / `evaluator_ref` / `tcp_offset_ref` の解決先）の content sha256 が profile の宣言と一致（doc 06 §2.1・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-04）")
extra_b = " `P_EVIDENCE_EXPIRED`（required record の valid_until 超過・v0.2.3 CD-03）/" if gate("CD-03") else ""
d.rep("（doc 06 §8.1 の第 2 評価点 = `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND` / `P_EXPECTATION_UNCERTIFIED`）", "（doc 06 §8.1 の第 2 評価点 = `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND` /%s `P_EXPECTATION_UNCERTIFIED`）" % extra_b)
if pre_g:
    d.rep("(f) `permit.profile_hash == proposed_lease.profile_hash`。permit は発行時にこれらの結果 ref を束縛する。", "(f) `permit.profile_hash == proposed_lease.profile_hash`; " + "; ".join(pre_g) + "。permit は発行時にこれらの結果 ref を束縛する。")
if gate("CD-02"):
    d.rep("Orchestrator・Executor・RecoveryRoutingPolicy は HOLD を解除できない（AuthorityState を書けない）。",
          "**clearance record の形と「該当」の定義（v0.2.3・CD-02）**: clearance record = `RuntimeAuditRecord`（kind = CLEARANCE_RECORDED・payload = `{safehold_reason, role, operator_ref, profile_hash, evidence_ref}`）。CAS 条件 10 の「該当する clearance record」= `record.safehold_reason == current.safehold_reason ∧ record.role ∈ profile.escalation.clearance_roles[reason] ∧ record.profile_hash == permit.profile_hash ∧ record.seq > 当該 SAFEHOLD 遷移の record.seq`。SAFETY 行は加えて IndependentSafetyLayer の clearance record（AND）。profile が当該 reason の role を 1 つも宣言しない場合は登録時に doc 06 `P_CLEARANCE_ROLE_MISSING`（定義なし = 解除不能 HOLD にも「任意の record で解除」にもしない）。\n\nOrchestrator・Executor・RecoveryRoutingPolicy は HOLD を解除できない（AuthorityState を書けない）。")
if gate("CD-04"):
    d.rep("| SAFETY_RESTRICTION | profile `SafetyRestrictionSet`（静的） | gateway predicate | CommandGateway | IndependentSafetyLayer の live 決定は本 term ではなく §5.2 (i) の優先出力 |",
          "| SAFETY_RESTRICTION | profile `SafetyRestrictionSet`（静的） | gateway predicate | CommandGateway | IndependentSafetyLayer の live 決定は本 term ではなく §5.2 (i) の優先出力。gateway は評価前に predicate の解決内容 sha256 を `predicate_sha256` と再検証し、不一致 = 評価不能 = FALSE（v0.2.3・CD-04） |")
if gate("CD-07"):
    d.rep("| CONTROLLER | profile `ControllerEnvelope`（velocity / acceleration / jerk / force / torque） | joint space | CommandGateway | 制御周波数は含まない（R5） |",
          "| CONTROLLER | profile `ControllerEnvelope`（velocity / acceleration / jerk / ee_speed — admission 可能な運動学項のみ） | joint space | CommandGateway | 制御周波数は含まない（R5）。`ee_force_max` / `joint_torque_max` は command から評価不能なため admission 項ではなく**監視上限**（IndependentSafetyLayer / controller が測定値で監視・v0.2.3 CD-07） |")
if gate("CD-18"):
    d.rep("| DEPLOYMENT_WORKSPACE | profile `WorkspaceRestriction`（keep-out / reach / height） | workspace | CommandGateway（FK 後） | doc 06 |",
          "| DEPLOYMENT_WORKSPACE | profile `WorkspaceRestriction`（keep-out / reach / height） | workspace | CommandGateway（FK 後） | doc 06。評価対象 = hold が LINEAR_INTERPOLATE のとき直前 admitted setpoint → 新 setpoint の線分（TCP 点・FK 後）、ZERO_ORDER_HOLD のとき点。tool 形状は評価しない（doc 06 §4・OPP-14・v0.2.3 CD-18） |")

# §13 v0.2.3 table
rows = [
 ("A-01 / B-M5", "06 §5 の stale 参照（条件 6）", "doc 06 §5"),
 ("A-10", "§6.1 CHECKPOINT 行が SAFETY_STABILIZED を除外していない", "§6.1"),
 ("A2-12", "規則 3 が R_OUTCOME_INVALID を列挙しない", "§7 規則 3"),
 ("B-M1 / B2-04", "INV-24 と再試行文が非 safety 起因で過大主張", "§3.5・§5.2 (ii) `pending_invalidate`・INV-24"),
 ("B-M2", "R_MANAGER_RESTART 行 / T-09 が無条件 epoch+1", "§3.7 失敗表・T-09"),
 ("B-M7", "06 §8.1 規則 (3) が旧文", "doc 06 §8.1"),
 ("B-L3", "記録義務が admitted CLOSED_LOOP command を含まない", "§8 記録義務・AuditKind comment"),
 ("B2-05", "ISL 起因行で reason SAFETY / disposition SAFE_STOP の食い違い", "§3.5 例外・§5.2 (iii)"),
 ("B2-14", "age の基準が無い", "§3.4 (e)"),
 ("B2-17", "T-17 が旧 INV-17 の文", "T-17"),
]
crow = [
 ("CD-12", "None 鮮度の規則が 05/06 で二重定義", "§4.2"),
 ("CD-13", "INV-22 の列挙漏れ・ack_validity の clock", "INV-22・§4.1 comment"),
 ("CD-10", "lease に時間上限が無く曝露が無限", "`lease_max_duration_s`・§3.7・`R_LEASE_DURATION_EXCEEDED`・INV-33・T-32・OP-19"),
 ("CD-05", "commissioning 済 expectation の照合が無い", "§3.4 (g)"),
 ("CD-06", "offer の ownership が cell 資源と照合されない", "§3.4 (h)"),
 ("CD-17", "accepted profile 集合の前提が無い", "§3.4 (i)"),
 ("CD-04", "参照内容の content hash が無い", "§3.4 (j)・§4.3 SAFETY_RESTRICTION"),
 ("CD-02", "clearance record の形と「該当」が未定義", "§5.4"),
 ("CD-07", "force / torque を admission 項にしている", "§4.3 CONTROLLER"),
 ("CD-18", "workspace 項が点評価のみ", "§4.3 DEPLOYMENT_WORKSPACE"),
 ("CD-03", "evidence 失効・subject 単位が未執行", "§3.4 (b)"),
]
tbl = [f"- **v0.2.3 fold（{NOW}）— 独立 verifier（3 lens・別 context・v0.2.1 finding を v0.2.1 本文で検証し v0.2.2 での fold 状態を判定）の verdict を上表に反映し、PARTIAL とされた残差と、軸 C（reviewer C・v0.2.2 対象・verifier C）の確定 finding を fold**。全 verdict と処置 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in rows: tbl.append(f"| {i}（残差） | {c} | {s} | {'; '.join(f'{x}={vstr(x)}' for x in i.split(' / '))} |")
for i, c, s in crow:
    tbl.append(f"| {i} | {c} | {s if conf(i) else '— 適用せず'} | {vstr(i)} |")
d.insert_before_line("## 14. Review anchors", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= 06
d = Doc("06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md")
n = d.stamp(); print("06 stamped", n)
d.rep("DEPLOYMENT PROFILE SPEC (v0.2.2 REVIEW CANDIDATE)", "DEPLOYMENT PROFILE SPEC (v0.2.3 REVIEW CANDIDATE)")
d.rep("／ v0.2.2 = ", "／ v0.2.3 = %s（`date -u` 実測）／ v0.2.2 = " % NOW)
d.rep("- status: **REVIEW CANDIDATE v0.2.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.1 = 陽性対照レビューの注入外 finding の fold ／ v0.2.1 → v0.2.2 = 3 軸独立レビューの確定 finding の fold（§11・verdict と処置の全体 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`）",
      "- status: **REVIEW CANDIDATE v0.2.3（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.1 = 陽性対照レビュー fold ／ v0.2.1 → v0.2.2 = 3 軸レビュー（A / A2 / B / B2）fold（起草者再検証のみ）／ v0.2.2 → v0.2.3 = 独立 verifier verdict 反映 + 残差 + 軸 C（reviewer C は v0.2.2 を対象・verifier C）fold（§11・全体 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`）。verdict は AI verifier のもので human two-key ではない")
# B-M7 residual: §8.1 rule (3)
exp = " / `P_EVIDENCE_EXPIRED`" if conf("CD-03") else ""
d.rep("(3) 受理後の事実変化（期限切れ・evidence 失効）は profile を変えず lease を無効化する（§5）。",
      "(3) 受理後の事実変化（期限切れ・evidence 失効）は profile を変えない。活性 lease は継続し、次の permit 発行が `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND`%s → 05 `R_PROFILE_MISBOUND` で不成立になる（§5 (b)）。lease を無効化するのは health check 失敗（§5 (a)）%sのみ（v0.2.3・B-M7 残差）。" % (exp, "と `lease_max_duration_s` 超過（CD-10）" if conf("CD-10") else ""))
# A-01 / B-M5 residual: §5 stale reference
d.rep("`CommitPermit.profile_hash` と等値（05 §3.5 前提 6 の inputs 束縛）。", "`CommitPermit.profile_hash` と等値（05 §3.5 条件 2・§3.4 (f) の等値束縛 — v0.2.3 A-01 / B-M5 残差。条件 6 は certificate の skill_action_id のみを束縛する）。")

newP = []; newPT = []; newOPP = []
# --- CD-08 enums (needed by several)
if gate("CD-08"):
    d.rep("class EscalationTarget(Enum):     HOLD | SAFE_STOP                              # 05 §7 の disposition 名を再利用（SAFE_STOP 側へのみ強化）",
          "class EscalationTarget(Enum):     HOLD | SAFE_STOP                              # 05 §7 の disposition 名を再利用（SAFE_STOP 側へのみ強化）\nclass CalibrationKind(Enum):      TCP | CAMERA_EXTRINSIC | CAMERA_INTRINSIC | FORCE_SENSOR   # v0.2.3（CD-08）: 閉じた enum（自由文字列を廃止・未知 = codec 拒否）\nclass ZoneKind(Enum):             KEEP_OUT | REACH_LIMIT | HEIGHT_BAND                       # v0.2.3（CD-08）\n# 評価空間は型で固定（v0.2.3・CD-08）: ControllerEnvelope = joint space、WorkspaceRestriction = workspace（05 §4.3）。自由文字列 field `representation` は削除")
    d.rep('    representation: str = "joint_space"                     # AcceptedEnvelope 項の評価空間（05 §4.3）\n', "")
    d.rep('    representation: str = "workspace"\n', "")
    d.rep('    kind: str                              # "keep_out" | "reach_limit" | "height_band"', "    kind: ZoneKind                         # v0.2.3（CD-08）: 閉じた enum")
    d.rep('    kind: str                              # "tcp" | "camera_extrinsic" | "camera_intrinsic" | "force_sensor" | ...', "    kind: CalibrationKind                  # v0.2.3（CD-08）: 閉じた enum")
    d.rep("| `calibration_refs` の必須 kind（`tcp` + belief を担う camera 系）が存在し、`valid_until` が評価時刻より後 | `P_CALIBRATION_MISSING` / `P_CALIBRATION_EXPIRED` |",
          "| `calibration_refs` が `REQUIRED_CALIBRATION_KINDS(control_mode)` を含む（LEARNED = {TCP, CAMERA_EXTRINSIC, CAMERA_INTRINSIC}・SCRIPTED / WAIT = {TCP}・binding_expectations の各 control_mode について評価・v0.2.3 CD-08）、`valid_until` が評価時刻より後 | `P_CALIBRATION_MISSING` / `P_CALIBRATION_EXPIRED` |")
    newPT.append("| PT-18 | `CalibrationRef.kind` に未知文字列（typo）を与える（v0.2.3） | codec 拒否（enum strict） |")
# --- CD-14 always-True bools / P_INTRINSIC_OVERRIDE
if gate("CD-14"):
    d.rep("    fail_closed: bool                      # **True 必須**", "    fail_closed: bool                      # **True 必須**（v0.2.3・CD-14: knob ではなく明示宣言。省略時 default を持たせないための field で、False は登録拒否・欠落は codec 拒否）")
    d.rep("    requires_safety_layer_health: bool     # **True 必須**（P_SAFETY_LAYER_NOT_REQUIRED）", "    requires_safety_layer_health: bool     # **True 必須**（P_SAFETY_LAYER_NOT_REQUIRED）。v0.2.3（CD-14）: 明示宣言（省略時 default を持たせない）— False = 登録拒否・欠落 = codec 拒否")
intr = "profile に action-space bounds を表す field が現れたら strict codec が `P_UNKNOWN_FIELD`（PT-05）。`P_INTRINSIC_OVERRIDE` = null-binding expectation（SCRIPTED / WAIT）に非 null の timing 値がある場合（v0.2.3・CD-05 / CD-14 で再定義）" if (conf("CD-14") or conf("CD-05")) else "profile に action-space bounds を表す field が現れたら `P_INTRINSIC_OVERRIDE`（codec = unknown field）"
d.rep("| 触れない | profile に action-space bounds を表す field が現れたら `P_INTRINSIC_OVERRIDE`（codec = unknown field） |", "| 触れない | %s |" % intr)
# --- CD-05 expectations
if conf("CD-05"):
    d.rep("| `BindingExpectation.{…}` | **等値**（`==` TensorBindingSpec の値） | `P_RATE_MISMATCH` / `P_HOLD_MISMATCH` |",
          "| `BindingExpectation.{…}` | **等値**（`==` TensorBindingSpec の値）。評価は `tensor_binding_hash ≠ null` のときのみ；null（SCRIPTED / WAIT・TensorBindingSpec が存在しない `%s:289`）では timing 4 field は None 必須（非 null = `P_INTRINSIC_OVERRIDE`）・SCRIPTED の timing 執行は 05 `command_deadline_s` のみ（v0.2.3・CD-05） | `P_RATE_MISMATCH` / `P_HOLD_MISMATCH` |" % B)
    d.rep("・SCRIPTED / WAIT では唯一の source", "・SCRIPTED / WAIT では timing 値を持たない（None・v0.2.3 CD-05）。lease 成立には当該 skill の expectation が存在すること（05 §3.4 (g)）")
    newPT.append("| PT-19 | SCRIPTED skill の expectation に `action_rate_hz` を非 null で宣言（v0.2.3） | `P_INTRINSIC_OVERRIDE` |")
# --- CD-06
if conf("CD-06"):
    d.rep("| offered 集合の**宣言**（frozen 検査は不変）。cell が持たない資源を offered と宣言する = 事実誤り |", "| offered 集合の**宣言**（frozen 検査は不変）。cell が持たない資源を offered と宣言する = 事実誤り。全 lease の `ownership.control` ⊆ 本宣言（chained handoff の offer も・05 §3.4 (h)・v0.2.3 CD-06） |")
# --- CD-01 timeouts order
if gate("CD-01"):
    lmd = "；`lease_max_duration_s ≥ boundary_dwell_s`（CD-10）" if conf("CD-10") else ""
    d.rep("| 全 `RuntimeTimeouts` field > 0・有限（`int` field は ≥ 1・v0.2.2） | `P_TIMEOUT_NONPOSITIVE` |",
          "| 全 `RuntimeTimeouts` field > 0・有限（`int` field は ≥ 1・v0.2.2） | `P_TIMEOUT_NONPOSITIVE` |\n| `RuntimeTimeouts` の相対順序（v0.2.3・CD-01）: `safety_heartbeat_timeout_s ≤ command_deadline_s`；`inter_command_jitter_s < 1 / action_rate_hz`（LEARNED expectation ごと）；`decision_max_age_s ≤ permit_ttl_s ≤ boundary_dwell_s`；`ack_validity_s ≤ boundary_dwell_s`%s。絶対上限は OPP-11 | `P_TIMEOUT_ORDER` |" % lmd)
    d.rep("MIN_FAULT_INJECTION（CLOSED_LOOP_AUTHORITY 前）= {R_EPOCH_STALE_COMMAND, R_OFFER_REUSED, R_PERMIT_REUSED, R_SAFETY_OVERRIDE, R_HEALTH_CONFIRM_FAILED, R_EXECUTOR_LOST, R_POST_OUTCOME_COMMAND, R_GATEWAY_RESTART}",
          "MIN_FAULT_INJECTION（CLOSED_LOOP_AUTHORITY 前）= {R_EPOCH_STALE_COMMAND, R_OFFER_REUSED, R_PERMIT_REUSED, R_SAFETY_OVERRIDE, R_HEALTH_CONFIRM_FAILED, R_EXECUTOR_LOST, R_POST_OUTCOME_COMMAND, R_GATEWAY_RESTART}\n                 ∪ {R_DEADLINE_MISS, R_SAFETY_LAYER_LOST, R_TIMING_VIOLATION, R_PERMIT_EXPIRED, R_ACK_TIMEOUT, R_HEALTH_CONFIRM_TIMEOUT, R_BOUNDARY_DWELL_EXCEEDED}   # v0.2.3（CD-01）: timeout 駆動の fault は同一 profile_hash の下で commissioning 時に必ず発火させる")
    newPT.append("| PT-20 | `safety_heartbeat_timeout_s = 1e9`（他は妥当）の profile（v0.2.3） | `P_TIMEOUT_ORDER` |")
    newOPP.append("| OPP-11 | `RuntimeTimeouts` の**絶対上限**（秒の ceiling）は cell / 規格依存で本 doc は相対順序（`P_TIMEOUT_ORDER`）しか検査しない（v0.2.3・CD-01） | §3・05 OP-10 | RT0 / Rs へ carry（値は書かない） |")
# --- CD-02 clearance roles + CD-09 health kinds
hk_set = "{SAFETY_LAYER_HEARTBEAT, CONTROLLER_LIVENESS, ENVELOPE_READBACK}"
adds = []
if conf("CD-02"): adds.append("GATEWAY_CONFIG_MATCH")
if gate("CD-09"): adds += ["CONTROLLER_IDENTITY", "TOOL_IDENTITY"]
if adds:
    hk_set = "{SAFETY_LAYER_HEARTBEAT, CONTROLLER_LIVENESS, ENVELOPE_READBACK, " + ", ".join(adds) + "}"
    d.rep("| `health_checks` に `SAFETY_LAYER_HEARTBEAT`・`CONTROLLER_LIVENESS`・`ENVELOPE_READBACK` の 3 kind が各 ≥ 1（stage は BOTH 推奨・BEFORE_PERMIT 必須） | `P_HEALTHCHECK_MISSING` |",
          "| `health_checks` に %s の各 kind が ≥ 1・stage ∈ {BEFORE_PERMIT, BOTH}（v0.2.3・%s） | `P_HEALTHCHECK_MISSING` |" % (hk_set, " / ".join([x for x in ("CD-02" if conf("CD-02") else "", "CD-09" if conf("CD-09") else "") if x])))
if conf("CD-09"):
    d.rep("class HealthCheckKind(Enum):      CONTROLLER_LIVENESS | SAFETY_LAYER_HEARTBEAT | CALIBRATION_VALID | TOOL_IDENTITY | GATEWAY_CONFIG_MATCH | ENVELOPE_READBACK",
          "class HealthCheckKind(Enum):      CONTROLLER_LIVENESS | SAFETY_LAYER_HEARTBEAT | CALIBRATION_VALID | TOOL_IDENTITY | GATEWAY_CONFIG_MATCH | ENVELOPE_READBACK | CONTROLLER_IDENTITY\n#   v0.2.3（CD-09）: CONTROLLER_IDENTITY = controller が報告する serial / firmware と CellIdentity.{robot_serial_ref, controller_firmware_ref} の等値（LIVENESS ≠ identity）。ENVELOPE_READBACK = controller 側に設定された運動学上限の readback と ControllerEnvelope の等値（executor 側 envelope readback = 05 §3.3 とは別）")
    newPT.append("| PT-21 | commissioning 後に firmware 更新・tool 交換（profile 不変）で permit 要求（v0.2.3） | CONTROLLER_IDENTITY / TOOL_IDENTITY が fail → 05 `R_HEALTHCHECK_FAILED`・permit 不発行 |")
if conf("CD-02"):
    d.rep("clearance_roles: tuple[tuple[str, str], ...]   # (safehold_reason, role) — SAFETY / SAFE_STOP / CHECKPOINT_DISABLED / MANAGER_RESTART / GATEWAY_RESTART の解除に要する **追加の** role（05 §5.4）。",
          "clearance_roles: tuple[tuple[str, str], ...]   # (safehold_reason, role) — SAFETY / SAFE_STOP / CHECKPOINT_DISABLED / MANAGER_RESTART / GATEWAY_RESTART の解除に要する **追加の** role（05 §5.4）。v0.2.3（CD-02）: {SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART} の各 reason に ≥ 1 role が必須（P_CLEARANCE_ROLE_MISSING）— 未定義 = 解除不能でも任意解除でもない。")
    d.insert_after_line("| `health_checks` に ", "| `clearance_roles` が {SAFE_STOP, CHECKPOINT_DISABLED, MANAGER_RESTART, GATEWAY_RESTART} の各 reason に ≥ 1 role を持つ（SAFETY は ISL clearance record が主・role は AND）（v0.2.3・CD-02） | `P_CLEARANCE_ROLE_MISSING` |")
    newPT.append("| PT-22 | `clearance_roles = ()` の profile（v0.2.3） | `P_CLEARANCE_ROLE_MISSING` |")
# --- CD-03 evidence per subject / expiry / unknown fault code
if gate("CD-03"):
    d.rep("| `deployment_evidence_policy_hash` が解決でき、§6 の required kinds が profile_hash に対し存在 | `P_EVIDENCE_UNBOUND` |",
          "| `deployment_evidence_policy_hash` が解決でき、required kinds が **(kind × subject) 単位**で profile_hash に対し存在（登録時 = MIN_SHADOW・permit 発行時 = 当該 lease mode の集合。CALIBRATION_RECORD ∀ `calibration_refs[].calibration_id`・HEALTH_CHECK_RUN ∀ `health_checks[].check_id`・FAULT_INJECTION_RESULT ∀ `fault_injection[]` with must_be_exercised_before ⊑ mode: `subject_ref == runtime_fault_code`）（v0.2.3・CD-03） | `P_EVIDENCE_UNBOUND` |\n| required record の `valid_until_iso8601` が permit 発行の wall-clock より前（第 2 評価点・`validity_rule` の執行） | `P_EVIDENCE_EXPIRED` |\n| `fault_injection[].runtime_fault_code` ∉ 05 `RuntimeFaultCode` | `P_FAULT_CODE_UNKNOWN` |")
    d.rep("第 2 評価点 = **permit 発行時**（時刻・lease 文脈依存の `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND` / `P_EXPECTATION_UNCERTIFIED` を再評価", "第 2 評価点 = **permit 発行時**（時刻・lease 文脈依存の `P_CALIBRATION_EXPIRED` / `P_EVIDENCE_UNBOUND`（当該 lease mode の集合・subject 単位） / `P_EVIDENCE_EXPIRED` / `P_EXPECTATION_UNCERTIFIED` を再評価")
    d.rep("    runtime_fault_code: str                # 05 RuntimeFaultCode の名（例: R_EPOCH_STALE_COMMAND）", "    runtime_fault_code: str                # 05 RuntimeFaultCode の名（例: R_EPOCH_STALE_COMMAND）。v0.2.3（CD-03）: 05 enum に無い名 = P_FAULT_CODE_UNKNOWN")
    newPT.append("| PT-23 | `SAFETY_LAYER_ACCEPTANCE` record の `valid_until` を過去にして permit 要求（v0.2.3） | `P_EVIDENCE_EXPIRED` → 05 `R_PROFILE_MISBOUND` |")
    newPT.append("| PT-24 | FAULT_INJECTION_RESULT が MIN_FAULT_INJECTION の 1 code 分しか無い profile で CLOSED_LOOP permit（v0.2.3） | `P_EVIDENCE_UNBOUND`（subject 単位） |")
# --- CD-04 content hashes
if conf("CD-04"):
    d.rep("    predicate_refs: tuple[str, ...]        # 各 predicate は「拒否条件」のみを表現する（許可条件は表現不能）",
          "    predicate_refs: tuple[str, ...]        # 各 predicate は「拒否条件」のみを表現する（許可条件は表現不能）\n    predicate_sha256: tuple[str, ...]      # v0.2.3（CD-04）: predicate_refs と同長・解決内容の content hash（登録時 + 第 2 評価点で照合、gateway は評価前に再検証・不一致 = FALSE）")
    d.rep("    evaluator_ref: str\n    stage: HealthCheckStage", "    evaluator_ref: str\n    evaluator_sha256: str                  # v0.2.3（CD-04）: evaluator 内容の content hash（第 2 評価点で照合・不一致 = R_PROFILE_MISBOUND）\n    stage: HealthCheckStage")
    d.rep("    tcp_offset_ref: str                    # calibration 側で attest される TCP offset の参照", "    tcp_offset_ref: str                    # == calibration_refs 内の kind = TCP の calibration_id（未解決 = P_TCP_REF_UNRESOLVED・v0.2.3 CD-04）— 内容は artifact_sha256 で束縛")
    d.insert_after_line("| `ControllerEnvelope` の tuple 長", "| `predicate_refs` / `evaluator_ref` の解決内容の sha256 が `predicate_sha256` / `evaluator_sha256` と一致（登録時；第 2 評価点の再照合は 05 `R_PROFILE_MISBOUND`）（v0.2.3・CD-04） | `P_PREDICATE_HASH_MISMATCH` |\n| `tcp_offset_ref` が `calibration_refs` の kind = TCP entry に解決する | `P_TCP_REF_UNRESOLVED` |")
    newPT.append("| PT-25 | 登録後に `keepout_pred_v1` の内容を常時許可に差し替え（v0.2.3） | 次 permit で `R_PROFILE_MISBOUND`・gateway 評価前の再検証で FALSE（拒否） |")
# --- CD-07 envelope honesty
if gate("CD-07"):
    d.rep("    ee_force_max: CanonicalDecimal | None                   # [N]\n    joint_torque_max: tuple[CanonicalDecimal, ...] | None   # [N·m]",
          "    ee_force_max: CanonicalDecimal | None                   # [N]   — v0.2.3（CD-07）: **監視上限**（command から評価不能。IndependentSafetyLayer / controller が測定値で監視・admission 項 CONTROLLER には含めない）\n    joint_torque_max: tuple[CanonicalDecimal, ...] | None   # [N·m] — 同上（監視上限）")
    d.rep("                            , CONTROLLER(profile.controller)          … joint space（velocity / acceleration / jerk / force / torque）",
          "                            , CONTROLLER(profile.controller)          … joint space（velocity / acceleration / jerk / ee_speed — admission 可能な運動学項のみ。force / torque は監視上限・v0.2.3 CD-07）")
    d.insert_after_line("| `ControllerEnvelope` の tuple 長", "| `ControllerEnvelope` の全上限 > 0・有限（v0.2.3・CD-07） | `P_ENVELOPE_NONPOSITIVE` |\n| `workspace.zones` に kind = REACH_LIMIT が ≥ 1（到達域の宣言なし = 空間制約なし、を許さない） | `P_WORKSPACE_EMPTY` |\n| `ControllerEnvelope` の各上限 ≤ `CONTROLLER_ENVELOPE_MEASUREMENT` record の測定値（artifact schema = ControllerEnvelope と同一 field・登録時に照合） | `P_ENVELOPE_EXCEEDS_MEASURED` |")
    d.repline("**「広げる」試みの網羅（反証の型）**",
      "**「広げる」試みの網羅（反証の型・v0.2.3 CD-07 で正直化）**: profile が frozen より緩い挙動を引き起こす経路は (i) action-space bounds を緩める — field が無い、(ii) 周波数・hold・control_mode を変える — 等値検査、(iii) initiation を緩める — AND のみ、(iv) 鮮度を緩める — `p ≤ f`、(v) 資源を偽って offered にする — CELL_COMMISSIONING evidence、(vi) 安全層を不要にする — True 必須、(vii) disposition を緩める — enum に緩和値が無い、(viii) boundary を checkpoint 化する — field が無い、(ix) 合成語彙を持ち込む — `P_COMPOSITION_CONTENT`、(x) timeout を伸ばして安全機構を無効化する — `P_TIMEOUT_ORDER`（相対順序。絶対上限 = OPP-11）、(xi) envelope / zone / predicate を空虚にする — `P_ENVELOPE_NONPOSITIVE` / `P_WORKSPACE_EMPTY` / `P_ENVELOPE_EXCEEDS_MEASURED` / `P_PREDICATE_HASH_MISMATCH`。**契約層で検証できるのは形・単調性・宣言と evidence の束縛まで**であり、物理事実（資源の実在・上限値の真偽・zone 幾何の正しさ・predicate 内容の妥当性・tool 質量）は全て evidence（§6）に委ねる（OPP-5 を拡張）。")
    d.rep("| OPP-5 | `ResourceAvailability` の真偽は契約層で判定不能（cell の物理事実） | §3 (v) | CELL_COMMISSIONING evidence に委ねる |",
          "| OPP-5 | 物理事実（`ResourceAvailability`・`ControllerEnvelope` 値・zone 幾何・predicate 内容・tool 質量）の真偽は契約層で判定不能（v0.2.3・CD-07 で範囲を拡張） | §3 (v)(xi) | 対応する evidence kind（CELL_COMMISSIONING / CONTROLLER_ENVELOPE_MEASUREMENT / …）に委ねる。P_* は形・単調性・束縛のみ |")
    newPT.append("| PT-26 | `joint_velocity_max = (1e6, …)`・`zones = ()`・`predicate_refs = ()` の profile（v0.2.3） | `P_WORKSPACE_EMPTY`・`P_ENVELOPE_EXCEEDS_MEASURED`（測定値超過） |")
# --- CD-10 06 side
if conf("CD-10"):
    d.rep("    inter_command_jitter_s: CanonicalDecimal       # v0.2.2（B-L2 / B2-13）: 連続 command 間隔の許容偏差（超過 = 05 R_TIMING_VIOLATION）\n",
          "    inter_command_jitter_s: CanonicalDecimal       # v0.2.2（B-L2 / B2-13）: 連続 command 間隔の許容偏差（超過 = 05 R_TIMING_VIOLATION）\n    lease_max_duration_s: CanonicalDecimal         # v0.2.3（CD-10）: lease 活性時間の上限（WAIT / TIMEOUT 非宣言 skill でも lease を有限にする・超過 = 05 R_LEASE_DURATION_EXCEEDED）\n")
    d.rep("command_kind_mismatch_max, inter_command_jitter_s}` ← `RuntimeTimeouts`（同名 field の等値写像・v0.2.2 で 6 field 追加）", "command_kind_mismatch_max, inter_command_jitter_s, lease_max_duration_s}` ← `RuntimeTimeouts`（同名 field の等値写像・v0.2.2 で 6 field・v0.2.3 で 1 field 追加）")
    d.rep("曝露 = 最大 1 skill（TERMINAL boundary まで）。", "曝露 = 最大 1 skill かつ最大 `lease_max_duration_s`（TERMINAL boundary または 05 INV-33 の上限まで・v0.2.3 CD-10）。")
    d.rep("活性 lease は TERMINAL boundary まで継続（lease 中の検出点なし・曝露 ≤ 1 skill・v0.2.2 B-M7・05 OP-19）", "活性 lease は TERMINAL boundary または `lease_max_duration_s` まで継続（lease 中の検出点なし・曝露 ≤ 1 skill かつ ≤ lease_max_duration_s・v0.2.2 B-M7・v0.2.3 CD-10・05 OP-19）")
# --- CD-15 label
if gate("CD-15"):
    d.rep("    profile_label: str                     # 人間向け label（pin ではない — content sha で引く）", "    profile_label: str                     # 人間向け label。hash preimage に**入る**（label 変更 = 新 profile_hash = identity event・evidence 再取得が要る）。preimage からの射影は §2.3「新 canonicalization 規則を足さない」と衝突するため OPP-12（v0.2.3・CD-15）")
    newOPP.append("| OPP-12 | `profile_label` を hash preimage から射影するか（§2.3 の「新規則を足さない」と衝突） | §2.2 | 現状 = preimage に含む（label 変更 = identity event） |")
# --- CD-16 audit join
if gate("CD-16"):
    d.rep("    artifact_ref: str\n    artifact_sha256: str\n    measured_at_iso8601: str", "    artifact_ref: str                      # v0.2.3（CD-16）: kind ∈ {HEALTH_CHECK_RUN, FAULT_INJECTION_RESULT} では 05 RuntimeAuditRecord の (lease_id, seq 範囲) に解決する（audit trail への束縛）\n    artifact_sha256: str\n    measured_at_iso8601: str")
    d.rep("両者は `profile_hash` と `lease_id` で join する（05 §8）。", "両者は `profile_hash` で join し、HEALTH_CHECK_RUN / FAULT_INJECTION_RESULT は `artifact_ref` が指す (lease_id, seq 範囲) で 05 §8 の record に束縛される（v0.2.3・CD-16）。")
# --- CD-17 registry
if conf("CD-17"):
    newOPP.append("| OPP-13 | profile の **registry**（所在・受理権限 = two-key か operator か・受理済集合 `accepted_profiles` の永続化）。05 §3.4 (i) は `profile_hash ∈ accepted_profiles` を前提にする（v0.2.3・CD-17） | §8.1 第 1 評価点 | 受理の権限は Rs 専権側（本 doc は集合の存在だけを要求） |")
    d.rep("(2) profile の受理（`profile_hash` の登録）は全 `P_*` = 0 が前提。", "(2) profile の受理（`profile_hash` の登録 = `accepted_profiles` への追加・registry と受理権限は OPP-13）は全 `P_*` = 0 が前提。")
# --- CD-18 workspace evaluation
if gate("CD-18"):
    d.rep("- SCRIPTED / WAIT skill（`tensor_binding_hash = null`）では INTRINSIC 項が欠け、profile 3 項のみ（05 OP-2）。profile はこれを埋めない（intrinsic 宣言は future static candidate）。",
          "- SCRIPTED / WAIT skill（`tensor_binding_hash = null`）では INTRINSIC 項が欠け、profile 3 項のみ（05 OP-2）。profile はこれを埋めない（intrinsic 宣言は future static candidate）。\n- **DEPLOYMENT_WORKSPACE の評価対象（v0.2.3・CD-18）**: hold = LINEAR_INTERPOLATE のとき直前 admitted setpoint → 新 setpoint の線分（FK 後・TCP 点）、ZERO_ORDER_HOLD のとき点。tool 形状（collision hull）は評価しない — 物体形状に対する keep-out は IndependentSafetyLayer の監視（OPP-14）。")
    newOPP.append("| OPP-14 | tool / payload の形状（collision hull）を profile に宣言して workspace 項で評価するか（現状 = TCP 点 / 線分のみ・形状は ISL 監視） | §4 | 宣言 field は無し（追加は新 evidence kind を伴う） |")
# --- CD-11 (records) — handled by header + 11_ existence; note in fold table only
gate("CD-11")

# §8.1 code list append
codes = []
if conf("CD-01"): codes.append("`P_TIMEOUT_ORDER`")
if conf("CD-02"): codes.append("`P_CLEARANCE_ROLE_MISSING`")
if conf("CD-03"): codes += ["`P_EVIDENCE_EXPIRED`", "`P_FAULT_CODE_UNKNOWN`"]
if conf("CD-04"): codes += ["`P_PREDICATE_HASH_MISMATCH`", "`P_TCP_REF_UNRESOLVED`"]
if conf("CD-07"): codes += ["`P_ENVELOPE_NONPOSITIVE`", "`P_WORKSPACE_EMPTY`", "`P_ENVELOPE_EXCEEDS_MEASURED`"]
if codes:
    cl = d.line("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`"); d.repline("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`", cl + " / " + " / ".join(codes) + "（v0.2.3）")
if newPT: d.insert_after_line("| PT-15 |", "\n".join(newPT))
if newOPP: d.insert_after_line("| OPP-10 |", "\n".join(newOPP))
# §11 table
d.rep("⚠ 軸 C（deployment・reviewer C）は session 上限で未了 — 完了後に追補する:", "軸 C（deployment・reviewer C）は v0.2.2 を対象に実施し v0.2.3 で fold（下表の次）:")
c06 = [("CD-01","timeout に上限が無く安全機構を無効化できる","§3 `P_TIMEOUT_ORDER`・§6.1 MIN_FAULT_INJECTION・(x)・OPP-11"),("CD-02","clearance_roles の被覆・GATEWAY_CONFIG_MATCH 必須が無い","§2.1・§3 `P_CLEARANCE_ROLE_MISSING`・05 §5.4"),("CD-03","evidence の失効・subject 単位が未執行","§3 `P_EVIDENCE_UNBOUND` 再定義・`P_EVIDENCE_EXPIRED`・`P_FAULT_CODE_UNKNOWN`・§8.1"),("CD-04","predicate / evaluator / tcp_offset が名前参照のみ","§2.1 `predicate_sha256` / `evaluator_sha256`・§3・05 §3.4 (j)"),("CD-05","SCRIPTED / WAIT の expectation 評価が未定義・lease 前提に無い","§2.1・§3・05 §3.4 (g)"),("CD-06","offer の ownership が cell 宣言と照合されない","§3・05 §3.4 (h)"),("CD-07","空虚な envelope が通る・force / torque が admission 項","§2.1・§3・§4・(xi)・OPP-5"),("CD-08","自由文字列 kind / representation","§2.1 enum・§3 REQUIRED_CALIBRATION_KINDS"),("CD-09","identity を確認する health check が無い","§2.1 CONTROLLER_IDENTITY・§3 必須集合"),("CD-10","lease の時間上限が無い","§2.1 `lease_max_duration_s`・§5・PT-13・05 INV-33"),("CD-11","11_ 不在・SHA256SUMS 陳腐・verifier 未了の明示","header・`11_` 追加・SHA256SUMS 再生成"),("CD-12","None 鮮度の二重定義","05 §4.2（06 が SSOT）"),("CD-13","INV-22 列挙漏れ","05 INV-22・§4.1"),("CD-14","P_INTRINSIC_OVERRIDE が到達不能・常時 True bool","§3 再定義・§2.1 注記"),("CD-15","profile_label が hash-visible","§2.2 注記・OPP-12"),("CD-16","evidence record が audit に束縛されない","§6.1・§6.3"),("CD-17","registry / 受理権限が未定義","§8.1・OPP-13・05 §3.4 (i)"),("CD-18","workspace 項が点評価のみ","§4・OPP-14・05 §4.3")]
tbl = [f"- **v0.2.3 fold（{NOW}）— verifier verdict の反映（上表 verdict 列）・PARTIAL 残差（A-01 / B-M5 → §5、B-M7 → §8.1 規則 (3)）・軸 C finding の fold**。verifier C（3 lens）の verdict 列 = `11_` §3 と同一:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in c06: tbl.append(f"| {i} | {c} | {s if conf(i) else '— 適用せず'} | {vstr(i)} |")
d.insert_before_line("## 12. Review anchors", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= 07 / 04 / 08 stamps
for name in ("07_SUCCESSOR_CONTRACT_DECISION_20260903.md", "04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md", "08_INDEPENDENT_REVIEW_PLAN_20260903.md"):
    d = Doc(name); n = d.stamp(); d.rep("(v0.2.2 REVIEW CANDIDATE)", "(v0.2.3 REVIEW CANDIDATE)"); d.rep("REVIEW CANDIDATE v0.2.2（", "REVIEW CANDIDATE v0.2.3（"); print(name, "stamped", n); d.save()
print("applied:", sorted(set(applied))); print("skipped:", sorted(set(skipped))); print("NOW =", NOW)
