#!/usr/bin/env python3
"""v0.2.6 -> v0.2.7 fold (round 4: R5/R6 findings gated by verifier V5/V6 verdicts). Records-only; frozen files untouched.
Usage: python3 fold_v027.py <PKG_DIR> <verdicts_v027.json>   verdicts = {id: {"confirmed": bool, "severity": str, "merged_into": str}}"""
import sys, json, re, subprocess
P = sys.argv[1]; VERD = json.load(open(sys.argv[2]))
NOW = subprocess.check_output(["date", "-u", "+%Y-%m-%d %H:%M UTC"]).decode().strip()
RS71 = "thread_isaac_lab/thread-vault/04-Specs/RS71-System-Spec-SSOT.md"
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
d.rep("RUNTIME SPEC (v0.2.6 REVIEW CANDIDATE)", "RUNTIME SPEC (v0.2.7 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.6（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.5 → v0.2.6 = v0.2.5 本文への再レビュー round 3（R3 / R4 → V3 / V4）の確定 finding の fold（§13）。旧版の系譜:", "- status: **REVIEW CANDIDATE v0.2.7（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.6 → v0.2.7 = v0.2.6 本文への再レビュー round 4（R5 / R6 → V5 / V6）の確定 finding の fold（§13）。旧版の系譜: — v0.2.5 → v0.2.6 = v0.2.5 本文への再レビュー round 3（R3 / R4 → V3 / V4）の確定 finding の fold（§13）。旧版の系譜:")
d.rep("**round 3（R3 / R4 → V3 / V4）の fold = 本版 v0.2.6（§13）**", "round 3（R3 / R4 → V3 / V4）の fold = v0.2.6（2026-09-05 02:15 UTC）→ **round 4（R5 / R6 → V5 / V6）の fold = 本版 v0.2.7（§13）**")

# --- R5-01 / R6-16: SHADOW も deadline で無効化（mode を問わず）に統一
if gate("R5-01", "R6-16"):
    d.rep("SHADOW は次 permit 評価で可。**残 open**", "SHADOW も mode を問わず deadline / event / head-check で無効化（記録上の SafeHold・§3.7・INV-34。裁定の「SHADOW は次 permit で許容できる」は採らず保守側に統一・v0.2.7 R5-01 / R6-16）。**残 open**")
    d.rep("活性 CLOSED_LOOP lease は TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP if 安全起因)", "活性 lease（mode を問わず・v0.2.7 R5-01）は TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP if 安全起因)")
# --- R5-08 / R6-21: ACCEPTANCE 到達の fault code + sub-kind の解決元 ; R5-11: deadline の検出者と遅延上限
row290_pre = "| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` / `S_BOUNDARY_WAIT`（mode を問わず・v0.2.6） |"
if gate("R5-08", "R6-21"):
    old = d.line(row290_pre)
    new = old.replace("FAULT(R_CALIBRATION_EXPIRED_ACTIVE \\| R_EVIDENCE_EXPIRED_ACTIVE), DISPOSITION(HOLD \\| SAFE_STOP) |", "FAULT(R_CALIBRATION_EXPIRED_ACTIVE \\| R_EVIDENCE_EXPIRED_ACTIVE \\| R_PROFILE_SUSPENDED — 到達項目の kind = CALIBRATION / EVIDENCE / ACCEPTANCE に対応・v0.2.7 R5-08 / R6-21), DISPOSITION(HOLD \\| SAFE_STOP) |")
    new = new.replace("lease 時間上限は別行 R_LEASE_DURATION_EXCEEDED） |", "lease 時間上限は別行 R_LEASE_DURATION_EXCEEDED。到達項目の sub-kind（TCP / camera / SAFETY_LAYER_ACCEPTANCE 等）は `lease.profile_hash` の profile（calibration_id → kind）と evidence store（record_id → kind）から遷移時に解決し、解決不能 = 表に無い = SAFE_STOP・v0.2.7 R5-08） |")
    assert new != old; d.repline(row290_pre, new)
    d.rep("到達時の fault と disposition は kind / id から doc 06 §5 (b) の表で決まる（表に無い = SAFE_STOP）", "到達時の fault と disposition は kind / id から doc 06 §5 (b) の表で決まる（表に無い = SAFE_STOP）。v0.2.7（R5-08）: 副 kind は id を `lease.profile_hash` の profile `calibration_refs`（CALIBRATION）/ evidence store（EVIDENCE の record kind）で解決する（profile は content-addressed で不変・wall-clock 再読なし）；解決不能 = 表に無い = SAFE_STOP")
    d.rep("| lease の `validity_deadline_mono` 到達（calibration / evidence / acceptance 期限・v0.2.5 OP-19） | AuthorityManager | `R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE` |", "| lease の `validity_deadline_mono` 到達（calibration / evidence / acceptance 期限・v0.2.5 OP-19） | AuthorityManager | `R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE` / `R_PROFILE_SUSPENDED`（ACCEPTANCE 到達・v0.2.7 R5-08） |")
if gate("R5-11"):
    old = d.line(row290_pre)
    new = old.replace("`now ≥ lease.validity_deadline_mono`（calibration / evidence / acceptance の期限到達・manager clock・v0.2.5 OP-19。", "`now ≥ lease.validity_deadline_mono`（calibration / evidence / acceptance の期限到達・manager clock・v0.2.5 OP-19。検出者 = AuthorityManager が `validity_deadline_mono` に設定する timer。検出遅延の上限 = baseline diagnostic item `VALIDITY_DEADLINE_DETECTION`（worst-case detection・doc 06 §8.3 MIN_DIAGNOSTIC_ITEMS）。gateway へは検出後に通知する（v0.2.7 R5-11）。")
    assert new != old; d.repline(row290_pre, new)
    d.rep("`pending_invalidate`（VALIDITY_EXPIRED の deadline / event を含む・v0.2.6 R3-06）= gateway が TRANSFER_TO_SAFEHOLD の trigger を検出してから", "`pending_invalidate`（VALIDITY_EXPIRED の event、および manager の deadline timer からの通知を含む・v0.2.6 R3-06・v0.2.7 R5-11: deadline は gateway 状態に無いため manager が検出して通知する）= gateway が TRANSFER_TO_SAFEHOLD の trigger を検出（または manager から通知）してから")
# --- R5-02: event 行の到達不能 code を除去 + head-check 行を副場合ごとに total 化（R5-12 兄弟 / R5-13 新 generation / R6-10 baseline head / R5-06 audit）
if gate("R5-02"):
    d.rep("FAULT(R_PROFILE_SUSPENDED \\| R_EVIDENCE_EXPIRED_ACTIVE), DISPOSITION(HOLD \\| SAFE_STOP)・全 UNUSED permit VOID |", "FAULT(R_PROFILE_SUSPENDED — payload EVENT・reason。R_EVIDENCE_EXPIRED_ACTIVE は対応する SuspensionReason が無いため本行から除去・v0.2.7 R5-02), DISPOSITION(HOLD \\| SAFE_STOP)・全 UNUSED permit VOID |")
    sub_a = "(a) `head(registry, lease.profile_hash)` の `record_hash ≠ lease.acceptance_record_hash ∨ state ≠ ACCEPTED`" + ("、または同一 `cell_identity_hash` を持つ他 profile の head record が state ∈ {SUSPENDED, REVOKED}（新 generation の ACCEPTED で置換されていない）（R5-12）" if conf("R5-12") else "")
    trig = ("| any (EXECUTOR) | **manager 側 head-check**（baseline `diagnostic_items` の周期・monitor 非依存・registry の読みは条件 12 と同じ線形化読み・v0.2.6 R3-08・v0.2.7 R5-02 で副場合ごとに fault と disposition を固定）: " + sub_a +
            "; (b) registry が head-check 周期を超えて読めない; (c) DeploymentValidityMonitor の heartbeat が baseline 項目 `VALIDITY_MONITOR_LIVENESS` の上限を超えて欠落; (d) baseline diagnostic item の失敗（drift 項目 / identity 再検証 / proof-test" + ("・`AUDIT_RECORDER_LIVENESS`（R5-06）" if conf("R5-06") else "") + "・R3-20）" +
            ("; (e) cell_id の baseline registry head ≠ `record.timing_baseline_hash`（R6-10）" if conf("R6-10") else "") + " |")
    disp = ("| TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP) — disposition は副場合ごと: (a) head.state ∈ {SUSPENDED, REVOKED} = head.suspension_reason を doc 06 §5 (b) 表で（REVOKED / 不読 = 表に無い = SAFE_STOP）" +
            ("、head が新 generation の ACCEPTED（record_hash ≠ ∧ state == ACCEPTED）= HOLD（payload GENERATION_SUPERSEDED・R5-13）" if conf("R5-13") else "") + ("、兄弟 SUSPENDED / REVOKED = その reason の行" if conf("R5-12") else "") +
            "; (b)(c) = HOLD; (d) drift 項目 = CLOCK_ANOMALY 行（SAFE_STOP）・他の項目 = DIAGNOSTIC_FAILURE 行（HOLD・`on_validity_expired` で強化可）" + ("; (e) = BASELINE_SUPERSEDED 行（HOLD）" if conf("R6-10") else "") + "。(c)(d) の disposition は起草既定（OP-19 残 open・Rs が強化可） |")
    rec = ("| `S_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP)` | FAULT: (a) R_PROFILE_SUSPENDED（payload trigger = HEAD_CHECK・sub = SUSPENDED \\| REVOKED" + (" \\| GENERATION_SUPERSEDED" if conf("R5-13") else "") + (" \\| SIBLING_SUSPENDED" if conf("R5-12") else "") +
           "）; (b) R_REGISTRY_UNAVAILABLE（HEAD_CHECK）; (c) R_REGISTRY_UNAVAILABLE（MONITOR_LOST）; (d) drift = R_CLOCK_ANOMALY（DRIFT）・他 = R_EVIDENCE_EXPIRED_ACTIVE（DIAGNOSTIC:<item>）" + ("・recorder = R_AUDIT_UNAVAILABLE（RECORDER_LIVENESS）" if conf("R5-06") else "") +
           ("; (e) R_PROFILE_SUSPENDED（BASELINE_SUPERSEDED）" if conf("R6-10") else "") + ", DISPOSITION |")
    d.repline("| any (EXECUTOR) | **manager 側 head-check**", trig + disp + rec)
    d.rep("**残 open** = 周期診断の対象項目と周期の出所（RT0 safety case）", "**残 open** = 周期診断の対象項目と周期の出所（RT0 safety case）、および head-check 副場合 (c) monitor 喪失 / (d) 診断失敗の disposition 既定（v0.2.7 R5-02: HOLD を起草既定とした・Rs が強化可）")
# --- R5-03: permit 前提条件 (m) 監視系の生存 + §5.4 の解消条件
if gate("R5-03"):
    d.rep("周期 drift 検査（baseline 項目）の失敗 = TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP); (j) profile が宣言する", "周期 drift 検査（baseline 項目）の失敗 = TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP); (m) **監視系の生存（v0.2.7・R5-03）**: DeploymentValidityMonitor の直近 heartbeat が baseline 項目 `VALIDITY_MONITOR_LIVENESS` 内 ∧ baseline `diagnostic_items` の全項目が直近周期内に pass（評価不能 / 欠落 = FALSE）∧ 直近の head-check が周期内に成功。違反 = `R_REGISTRY_UNAVAILABLE`（FAULT payload trigger = MONITOR_LOST \\| DIAGNOSTIC:<item> \\| HEAD_CHECK）・permit 不発行（monitor 喪失で SafeHold に落ちた系が monitor 不在のまま再 lease する flap を閉じる。manager は registry を書かない = 06 §8.3 read-only のまま）; (j) profile が宣言する")
    d.rep("head-check 周期（baseline diagnostic item）を超えて読めない場合は TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)（R3-08） | `HOLD` |", "head-check 周期（baseline diagnostic item）を超えて読めない場合は TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)（R3-08）。permit 発行時の (m) 違反（monitor 喪失 / 診断失敗）も本 code（v0.2.7 R5-03） | `HOLD` |")
    d.rep("（VALIDITY_EXPIRED では新 permit が §3.4 (b)(i) で失効原因の解消を要求する。", "（VALIDITY_EXPIRED では新 permit が §3.4 (b)(i)(l)(m) で失効原因の解消を要求する — deadline = (b)、event / head 不一致 = (i)、clock = (l)、monitor 喪失 / 診断失敗 = (m) が拒否（v0.2.7 R5-03）。")
# --- R5-05: TRANSFER_TO_EXECUTOR で safehold_disposition を None に戻す + INV-01
if gate("R5-05"):
    d.rep("- `AuthorityState := (EXECUTOR(executor_id), expected.control_epoch + 1, new_lease_id, expected.consumed_offer_ids ∪ {consume_offer_id}, None, False, expected.seq + 1)`。", "- `AuthorityState := (EXECUTOR(executor_id), expected.control_epoch + 1, new_lease_id, expected.consumed_offer_ids ∪ {consume_offer_id}, None, False, expected.seq + 1)` + `safehold_disposition := None`（同一線形化点・v0.2.7 R5-05: 前 SAFEHOLD 期間の SAFE_STOP が新 lease の (iii) 窓へ漏れない）。")
    d.rep("`state.owner.kind == SAFEHOLD ⇔ state.safehold_reason != None` |", "`state.owner.kind == SAFEHOLD ⇔ state.safehold_reason != None`; `state.owner.kind == SAFEHOLD ⇔ state.safehold_disposition != None`（v0.2.7 R5-05） |")
# --- R5-06: AuditRecorder 不能の fault code・失敗表行・記録が先
if gate("R5-06"):
    d.rep("    R_CLOCK_ANOMALY   # v0.2.6（round 3）", "    R_CLOCK_ANOMALY | R_AUDIT_UNAVAILABLE   # v0.2.7（R5-06）: R_AUDIT_UNAVAILABLE = AuditRecorder の append 不能 / 停止。v0.2.6（round 3）")
    d.insert_after_line("| wall-clock の異常（過去へ戻る", "| AuditRecorder が record を append できない / 応答しない（v0.2.7・R5-06） | AuthorityManager / CommandGateway | `R_AUDIT_UNAVAILABLE` | CAS SUCCESS の executor への通知・permit VOID 通知・HealthConfirmation の受理は当該 record の durable append 後（`permit.state := CONSUMED` 自体は線形化点のまま・INV-04）。recorder 不能が baseline diagnostic item `AUDIT_RECORDER_LIVENESS` の周期を超えれば head-check 行 (d) と同じ経路で TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)・全 UNUSED permit VOID。書けなかった record は復旧後に元の `t_mono` で遡って append する。gateway が `COMMAND_ADMITTED` の append 不能で admission を同期 block するかは OP-5 の open note | `HOLD` |")
    d.rep("**CLOSED_LOOP lease の全 admitted command（`COMMAND_ADMITTED`・`GatewayCommand` payload・v0.2.3 B-L3 残差）**。欠落 = INV-17 違反。", "**CLOSED_LOOP lease の全 admitted command（`COMMAND_ADMITTED`・`GatewayCommand` payload・v0.2.3 B-L3 残差）**。欠落 = INV-17 違反。**記録が先（v0.2.7・R5-06）**: CAS SUCCESS の通知・permit VOID 通知・HealthConfirmation の受理は当該 record の durable append 後。recorder 不能が baseline diagnostic item `AUDIT_RECORDER_LIVENESS` を超える = `R_AUDIT_UNAVAILABLE`（§3.7 失敗表・head-check 行 (d) の経路）。")
    old = d.line("| OP-5 |"); d.repline("| OP-5 |", old.replace("| 定めない |", "| 定めない。v0.2.7（R5-06）open note: gateway が `COMMAND_ADMITTED` の append 不能時に admission を同期 block するか（(iii) へ落とすか）は設計選択・未決 |"))
    old = d.line("| INV-17 |"); d.repline("| INV-17 |", old.replace("| 記録欠落 = fault |", "| R_AUDIT_UNAVAILABLE（記録欠落 = fault・v0.2.7 R5-06） |"))
# --- R5-07: 境界の厳密化 + CAS 条件 2 到達の失敗表行
if gate("R5-07"):
    d.rep("∧ now ≤ ack.valid_until ∧", "∧ now < ack.valid_until（条件 2 と同じ厳密境界・v0.2.7 R5-07）∧")
    d.rep("∧ now − decision.t_mono ≤ decision_max_age_s`（age の CAS 時再検査", "∧ now − decision.t_mono < decision_max_age_s`（厳密境界・v0.2.7 R5-07。age の CAS 時再検査")
    d.rep("`granted == True ∧ age ≤ decision_max_age_s`（違反 = `R_AUTHORITY_DECISION_ABSENT`", "`granted == True ∧ age < decision_max_age_s`（厳密境界・v0.2.7 R5-07。違反 = `R_AUTHORITY_DECISION_ABSENT`")
    d.rep("CAS 時点で ACK 失効（`now > ack.valid_until`・条件 3）", "CAS 時点で ACK 失効（`now ≥ ack.valid_until`・条件 3・v0.2.7 R5-07）")
    old = d.line("| permit 失効 | AuthorityManager | `R_PERMIT_EXPIRED` |"); d.repline("| permit 失効 | AuthorityManager | `R_PERMIT_EXPIRED` |", old.replace("| permit 失効 | AuthorityManager |", "| permit 失効 = `effective_expires_at` 到達（CAS 未試行・どの項の到達でも本 code・v0.2.7 R5-07） | AuthorityManager |"))
    d.insert_after_line("| permit 失効 = `effective_expires_at` 到達", "| CAS 条件 2 で validity 項（`validity_deadline_mono`）または decision age 項が到達（v0.2.7・R5-07） | AuthorityManager | `R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE` / `R_PROFILE_SUSPENDED` / `R_AUTHORITY_DECISION_ABSENT`（条件 2 の優先規則） | CAS REJECTED・permit VOID・状態不変（活性 lease は無い — 同 code の活性 lease 行と区別） | `RESELECT`（新 permit は §3.4 (b)(e)(i) で原因解消を要求） |")
# --- R5-10 / R6-03: FAULT payload の trigger 語彙を SSOT 化
if gate("R5-10", "R6-03"):
    d.rep("`R_BOUNDARY_DWELL_EXCEEDED`: DWELL_TIMEOUT | ATTEMPTS_EXHAUSTED — doc 06 §6.1", "`R_BOUNDARY_DWELL_EXCEEDED`: DWELL_TIMEOUT | ATTEMPTS_EXHAUSTED、`R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE`: DEADLINE | HEAD_CHECK | DIAGNOSTIC:<item> | CAS_COND2、`R_PROFILE_SUSPENDED`: EVENT | HEAD_CHECK | CAS_COND12 | PERMIT | DEADLINE、`R_REGISTRY_UNAVAILABLE`: HEAD_CHECK | MONITOR_LOST | DIAGNOSTIC:<item> | PERMIT | CAS_COND12 | STARTUP、`R_CLOCK_ANOMALY`: PERMIT | DRIFT" + ("、`R_AUDIT_UNAVAILABLE`: RECORDER_LIVENESS" if conf("R5-06") else "") + "（trigger 語彙の SSOT = 本列挙。doc 06 `FaultInjectionRequirement.trigger` はここに無い語を P_FAULT_CODE_UNKNOWN で拒否・v0.2.7 R5-10 / R6-03） — doc 06 §6.1")
# --- R5-12: 兄弟 profile の SUSPENDED を head 状態の述語に固定（(i)・条件 12）
if gate("R5-12"):
    d.rep("同一 `cell_identity_hash` を持つ他 record が原因未解消の SUSPENDED なら本 profile も `R_PROFILE_SUSPENDED`（兄弟 profile による迂回を閉じる）", "同一 `cell_identity_hash` を持つ他 profile の head record が `state ∈ {SUSPENDED, REVOKED}`（新 generation の ACCEPTED で置換されていない）なら本 profile も `R_PROFILE_SUSPENDED`（兄弟 profile による迂回を閉じる。v0.2.7 R5-12: 述語を head 状態に固定し、条件 12 と head-check にも同じ節を置く）")
    d.rep("∧ proposed_lease.mode ∈ allowed_lease_modes`（v0.2.6 R4-16: hash 等値を含む）", "∧ proposed_lease.mode ∈ allowed_lease_modes ∧ 同一 cell_identity_hash の他 profile の head record に state ∈ {SUSPENDED, REVOKED} が無い`（v0.2.6 R4-16: hash 等値を含む・v0.2.7 R5-12: 兄弟節）")
# --- R6-05（05 側）: acceptance record の role_registry_hash を現 head と照合（(i)・条件 12）
if gate("R6-05"):
    d.rep("validator の content hash == `record.validator_hash`；`timing_baseline_hash` の artifact を解決して再検証；不一致 = `R_PROFILE_MISBOUND`）", "validator の content hash == `record.validator_hash`；`timing_baseline_hash` の artifact を解決して再検証；不一致 = `R_PROFILE_MISBOUND`；`record.role_registry_hash` == doc 06 §8.3 role registry の現 head（不一致 = `R_PROFILE_SUSPENDED`・v0.2.7 R6-05））")
    if conf("R5-12"): d.rep("`（v0.2.6 R4-16: hash 等値を含む・v0.2.7 R5-12: 兄弟節）", " ∧ record.role_registry_hash == role registry の現 head（R6-05）`（v0.2.6 R4-16: hash 等値を含む・v0.2.7 R5-12: 兄弟節）")
    else: d.rep("∧ proposed_lease.mode ∈ allowed_lease_modes`（v0.2.6 R4-16: hash 等値を含む）", "∧ proposed_lease.mode ∈ allowed_lease_modes ∧ record.role_registry_hash == role registry の現 head（R6-05）`（v0.2.6 R4-16: hash 等値を含む）")
# --- R6-10（05 側）: baseline registry の定義先
if gate("R6-10"):
    d.rep("layout と baseline registry の supersession・registry の state 変化（R4-14）", "layout と baseline registry（定義 = doc 06 §8.3・cell_id ごとに 1 head・v0.2.7 R6-10）の supersession・registry の state 変化（R4-14）")
# --- R6-17（05 側）: 失効 disposition の根拠を 06 表へ
if gate("R6-17"):
    d.rep("| `HOLD` / `SAFE_STOP`（安全機能・TCP・停止性能に関わる失効） |", "| `HOLD` / `SAFE_STOP`（doc 06 §5 (b) 表で決まる — 安全機能・TCP・停止性能（FI 含む）の失効は SAFE_STOP・v0.2.7 R6-17） |")
# --- R6-06: clearance record の資格照合
if gate("R6-06"):
    d.rep("clearance record = `RuntimeAuditRecord`（kind = CLEARANCE_RECORDED・payload = `{safehold_reason, role, operator_ref, profile_hash, evidence_ref}`）。CAS 条件 10 の「該当する clearance record」= `record.safehold_reason == current.safehold_reason ∧ record.role ∈ profile.escalation.clearance_roles[reason] ∧ record.profile_hash == permit.profile_hash ∧ record.seq > 当該 SAFEHOLD 遷移の record.seq`。", "clearance record = `RuntimeAuditRecord`（kind = CLEARANCE_RECORDED・payload = `{safehold_reason, role, operator_ref, role_registry_hash, profile_hash, evidence_ref}`）。CAS 条件 10 の「該当する clearance record」= `record.safehold_reason == current.safehold_reason ∧ record.role ∈ profile.escalation.clearance_roles[reason] ∧ record.profile_hash == permit.profile_hash ∧ record.seq > 当該 SAFEHOLD 遷移の record.seq ∧ record.role_registry_hash == doc 06 §8.3 role registry の現 head ∧ (record.operator_ref, record.role) ∈ その registry`（v0.2.7 R6-06: role label の自己申告では解除できない。資格照合不能 = 該当 record 無し）。")
# --- R6-13: (j) 区間内の除外宣言（frozen hash は (g) で束縛）— checker Q2 強化と対
if gate("R6-13"):
    d.rep("checker Q2 が 06 §2.1 の hash field 名 ⊆ 本列挙を機械検査・v0.2.6 R3-17 / R4-02）が解決先の内容と一致", "(j) の対象外 = `binding_expectations[].tensor_binding_hash`（frozen D1.1-B の hash・(g) が等値束縛する）。checker Q2 が 06 §2.1–2.2 の hash field 名が本区間に宣言 class ごとに 1 回以上現れることを機械検査・v0.2.6 R3-17 / R4-02・v0.2.7 R6-13）が解決先の内容と一致")
# --- 05 §3.4 (j) 列挙（R6-01 finger geometry hash）
if gate("R6-01"):
    d.rep("`initiation_strengthening.conjuncts[].schema_hash`（frozen InitiationSpec と同型の payload schema hash） / required `DeploymentEvidenceRecord.artifact_sha256`。", "`initiation_strengthening.conjuncts[].schema_hash`（frozen InitiationSpec と同型の payload schema hash） / `cell.arms[].tool_payload.finger_geometry_sha256`（RS71 §0 #4 の pinned gripper geometry・v0.2.7 R6-01） / required `DeploymentEvidenceRecord.artifact_sha256`。")
# --- tests
newT = []
if conf("R5-06"): newT.append("| T-38 | CAS SUCCESS 直後に AuditRecorder を停止（v0.2.7） | executor へ LEASE_ACTIVATED が通知されない・`AUDIT_RECORDER_LIVENESS` 超過で TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)・R_AUDIT_UNAVAILABLE・復旧後に record を遡って append |")
if conf("R5-05"): newT.append("| T-%d | SAFE_STOP disposition の SAFEHOLD から clearance → CAS SUCCESS → 最初の command 前（v0.2.7） | (iii) 窓の出力 = SafeHold（SafeStop ではない）・`safehold_disposition == None` |" % (38 + len(newT)))
if conf("R5-03"): newT.append("| T-%d | DeploymentValidityMonitor 停止中に permit 要求（v0.2.7） | 前提条件 (m) 不成立・R_REGISTRY_UNAVAILABLE（MONITOR_LOST）・permit 不発行 |" % (38 + len(newT)))
if conf("R5-07"): newT.append("| T-%d | `now == ack.valid_until` で CAS（v0.2.7） | 条件 2 / 3 とも不成立（厳密境界）・R_ACK_MISBOUND・REJECTED |" % (38 + len(newT)))
if conf("R5-12"): newT.append("| T-%d | 兄弟 profile（同一 cell_identity_hash）を SUSPENDED にして CAS（v0.2.7） | 条件 12 の兄弟節で REJECTED・R_PROFILE_SUSPENDED（SIBLING_SUSPENDED） |" % (38 + len(newT)))
if newT: d.insert_after_line("| T-37 |", "\n".join(newT))
rows05 = [("R5-01 / R6-16", "SHADOW の deadline 扱いが 3 通り", "OP-19・失敗表 R_PROFILE_SUSPENDED 行"), ("R5-02", "head-check 行が total でない・event 行の到達不能 code", "§3.7 head-check 行・event 行"), ("R5-03", "monitor 喪失後の再 permit を止める前提が無い", "§3.4 (m)・§5.4"), ("R5-05", "TRANSFER_TO_EXECUTOR が safehold_disposition を戻さない", "§3.5 事後条件・INV-01"), ("R5-06", "AuditRecorder 不能の code / 行が無い", "`R_AUDIT_UNAVAILABLE`・§3.7・§8・INV-17"), ("R5-07", "条件 2 / 3 / 6 の境界不一致・CAS 時失効の行", "§3.5 条件 3 / 6・§3.4 (e)・失敗表"), ("R5-08 / R6-21", "ACCEPTANCE 到達の fault code・sub-kind の解決元", "§3.7 deadline 行・失敗表"), ("R5-10 / R6-03", "trigger 副因の語彙が 2 code 分しか無い", "§8 記録義務"), ("R5-11", "gateway は deadline を検出できない", "§3.7 deadline 行・§5.2 (ii)"), ("R5-12", "兄弟 SUSPENDED が permit 発行時にしか効かない", "§3.4 (i)・§3.5 条件 12・head-check 行"), ("R6-05 / R6-06", "acceptance / clearance record の role registry 照合", "§3.4 (i)・§3.5 条件 12・§5.4 clearance record 定義"), ("R6-10", "baseline registry の定義先", "§2 monitor 行"), ("R6-17", "失効 disposition の根拠", "失敗表 validity 行"), ("R6-01", "finger geometry hash の (j) 列挙", "§3.4 (j)"), ("R6-13", "(j) 区間の除外宣言（checker Q2 強化と対）", "§3.4 (j)")]
tbl = [f"- **v0.2.7 fold（{NOW}）— round 4（reviewer R5 / R6・v0.2.6 対象 → verifier V5 / V6・3 lens）の確定 finding の fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §10:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in rows05: tbl.append(f"| {i} | {c} | {s if any_conf(*i.split(' / ')) else '— 適用せず'} | {'; '.join(f'{x}={vstr(x)}' for x in i.split(' / '))} |")
tbl.append("| （06 側の fold 行は doc 06 §11） | | | |")
d.insert_before_line("## 14. Review anchors", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= 06
d = Doc("06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("DEPLOYMENT PROFILE SPEC (v0.2.6 REVIEW CANDIDATE)", "DEPLOYMENT PROFILE SPEC (v0.2.7 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.6（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.5 → v0.2.6 = round 3（R3 / R4 → V3 / V4）の確定 finding の fold（§11）。旧版の系譜:", "- status: **REVIEW CANDIDATE v0.2.7（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.6 → v0.2.7 = round 4（R5 / R6 → V5 / V6）の確定 finding の fold（§11）。旧版の系譜: — v0.2.5 → v0.2.6 = round 3（R3 / R4 → V3 / V4）の確定 finding の fold（§11）。旧版の系譜:")
newP = []; newPT = []
second_anchor = "} — 05 §3.4 (b) が `R_PROFILE_MISBOUND`"
def add_second(item): d.rep(second_anchor, ", " + item + second_anchor)
# --- R5-01 / R6-16
if gate("R5-01", "R6-16"):
    d.rep("SHADOW_NON_AUTHORITY lease は actuation が無いため次 permit 評価で可。いずれの場合も", "SHADOW_NON_AUTHORITY lease も同じ deadline / event / 診断で無効化する（mode を問わず・05 §3.7 / INV-34 と同期・v0.2.7 R5-01 / R6-16。actuation が無いため効果は記録上の SafeHold のみ）。いずれの場合も")
    d.rep("SHADOW lease は次 permit まで継続（曝露 = actuation 無し）。次の permit 発行は", "SHADOW lease も deadline 到達で TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)（記録上・v0.2.7 R5-01 / R6-16 — `R_CALIBRATION_EXPIRED_ACTIVE#DEADLINE` の commissioning evidence はここで作る）。次の permit 発行は")
    d.rep("SUSPENDED / REVOKED は pending permit を VOID にし、活性 CLOSED_LOOP lease を SafeHold", "SUSPENDED / REVOKED は pending permit を VOID にし、活性 lease（mode を問わず・v0.2.7 R5-01）を SafeHold")
    d.rep("| 裁定 OP-19 | CLOSED_LOOP lease の validity deadline + event 無効化 + 根拠付き周期診断（SHADOW は次 permit） |", "| 裁定 OP-19 | CLOSED_LOOP lease の validity deadline + event 無効化 + 根拠付き周期診断（SHADOW は次 permit → v0.2.7 R5-01 / R6-16 で mode を問わずに統一） |")
# --- R5-04 / R6-11 / R5-14 / R6-17: P_VALIDITY_UNBOUNDED の評価点・kind 集合・上限
if gate("R5-04"):
    d.rep("`P_ARM_*` / `P_TIMEOUT_ORDER`）／ 第 2 評価点", "`P_ARM_*` / `P_TIMEOUT_ORDER` / `P_VALIDITY_UNBOUNDED`（`CalibrationRef` 側 + MIN_SHADOW の SAFETY_LAYER_ACCEPTANCE・v0.2.7 R5-04）／ 第 2 評価点")
    add_second("`P_VALIDITY_UNBOUNDED`（当該 lease mode の required set の record 側・v0.2.7 R5-04）")
    newPT.append("| PT-%d | CALIBRATION_RECORD を `valid_until = None` で登録して CLOSED_LOOP permit 要求（v0.2.7） | 第 2 評価点の `P_VALIDITY_UNBOUNDED` → 05 `R_PROFILE_MISBOUND`・permit 不発行 |" % (43 + len(newPT)))
if gate("R5-04", "R5-14", "R6-11", "R6-17"):
    kinds = "CALIBRATION_RECORD, SAFETY_LAYER_ACCEPTANCE" + (", CONTROLLER_ENVELOPE_MEASUREMENT（停止性能の入力・R5-14）" if conf("R5-14") else "") + (", FAULT_INJECTION_RESULT with subject R_SAFETY_LAYER_LOST#HEARTBEAT_TIMEOUT（同・R6-17）" if conf("R6-17") else "")
    upper = "、または `valid_until − measured_at > baseline.max_validity_s[kind]`（上限・baseline に当該 kind の上限が無い = 違反・v0.2.7 R6-11）" if conf("R6-11") else ""
    pts = "・評価点 = §8.1 (2) の両評価点（R5-04）" if conf("R5-04") else ""
    d.rep("| `CalibrationRef.valid_until_iso8601`、および required record のうち kind ∈ {CALIBRATION_RECORD, SAFETY_LAYER_ACCEPTANCE} の `valid_until_iso8601` が None（無期限）（v0.2.4・R2-18） | `P_VALIDITY_UNBOUNDED` |", "| `CalibrationRef.valid_until_iso8601`、および required record のうち kind ∈ {" + kinds + "} の `valid_until_iso8601` が None（無期限）" + upper + "（v0.2.4・R2-18" + pts + "） | `P_VALIDITY_UNBOUNDED` |")
    d.rep("ただし kind ∈ {CALIBRATION_RECORD, SAFETY_LAYER_ACCEPTANCE} の required record と CalibrationRef は None 不可（P_VALIDITY_UNBOUNDED）", "ただし §3 `P_VALIDITY_UNBOUNDED` が挙げる kind の required record と CalibrationRef は None 不可" + ("・上限 = baseline `max_validity_s[kind]`" if conf("R6-11") else "") + "（v0.2.7）")
if gate("R6-11"):
    d.rep("    max_acceptance_validity_s: CanonicalDecimal   # v0.2.6（R4-16）: acceptance record の valid_until 上限\n", "    max_acceptance_validity_s: CanonicalDecimal   # v0.2.6（R4-16）: acceptance record の valid_until 上限\n    max_validity_s: dict                   # v0.2.7（R6-11）: CalibrationKind / DeploymentEvidenceKind（FI は subject 別）→ 有効期間の上限 [s]（P_VALIDITY_UNBOUNDED の上限側）\n")
if gate("R6-17"):
    d.rep("EVIDENCE(SAFETY_LAYER_ACCEPTANCE | CONTROLLER_ENVELOPE_MEASUREMENT) → SAFE_STOP", "EVIDENCE(SAFETY_LAYER_ACCEPTANCE | CONTROLLER_ENVELOPE_MEASUREMENT | FAULT_INJECTION_RESULT with subject R_SAFETY_LAYER_LOST#HEARTBEAT_TIMEOUT — 停止性能の根拠・v0.2.7 R6-17) → SAFE_STOP")
# --- R5-09 / R6-12
if gate("R5-09", "R6-12"):
    d.rep("`AcceptedEnvelope.terms` の 3 項 ← §4", "`AcceptedEnvelope.terms` の 4 項（DEPLOYMENT_WORKSPACE / CONTROLLER / SAFETY_RESTRICTION / INTER_ARM・v0.2.7 R5-09 / R6-12）← §4")
# --- R5-10 / R6-03: FaultInjectionRequirement.trigger
if gate("R5-10", "R6-03"):
    d.rep("    must_be_exercised_before: LeaseMode    # 05 LeaseMode（SHADOW_NON_AUTHORITY / CLOSED_LOOP_AUTHORITY）", "    must_be_exercised_before: LeaseMode    # 05 LeaseMode（SHADOW_NON_AUTHORITY / CLOSED_LOOP_AUTHORITY）\n    trigger: str | None                    # v0.2.7（R6-03 / R5-10）: 05 §8 記録義務の trigger 語彙（DEADLINE / EVENT / HEARTBEAT_TIMEOUT / DWELL_TIMEOUT 等）。None = trigger を問わない。語彙に無い = P_FAULT_CODE_UNKNOWN。evidence の subject_ref = code[#trigger]")
    d.rep("| `fault_injection[].runtime_fault_code` ∉ 05 `RuntimeFaultCode` | `P_FAULT_CODE_UNKNOWN` |", "| `fault_injection[].runtime_fault_code` ∉ 05 `RuntimeFaultCode`、または `trigger ≠ None ∧ trigger ∉ 05 §8 記録義務が当該 code に定める trigger 語彙`（v0.2.7 R6-03 / R5-10） | `P_FAULT_CODE_UNKNOWN` |")
    d.rep("with must_be_exercised_before ⊑ mode: `subject_ref == runtime_fault_code`）", "with must_be_exercised_before ⊑ mode: `subject_ref == runtime_fault_code[#trigger]`（v0.2.7 R6-03））")
    d.rep("で timeout 経路そのものを要求する（health==failed", "で timeout 経路そのものを要求する（`FaultInjectionRequirement.trigger` で宣言・subject = trigger が None なら code・あれば code#trigger・v0.2.7 R6-03。health==failed")
# --- R5-13: ACCEPTED → ACCEPTED(gen+1) + head-check の GENERATION_SUPERSEDED
if gate("R5-13"):
    d.rep("- **状態遷移**: PROPOSED → ACCEPTED（受理）; ACCEPTED → SUSPENDED", "- **状態遷移**: PROPOSED → ACCEPTED（受理）; ACCEPTED → ACCEPTED(generation +1)（evidence 追加 / 再受理・受理条件は同じ・`supersedes_record_hash` = 旧 ACCEPTED。活性 lease は旧 generation に束縛されているため 05 head-check で HOLD（GENERATION_SUPERSEDED）に落ち、新 generation で再 lease・v0.2.7 R5-13）; ACCEPTED → SUSPENDED")
    d.rep("表に無い項目 = SAFE_STOP。`EscalationPolicy.on_validity_expired`", "GENERATION_SUPERSEDED（head ACCEPTED の新 generation・05 head-check 副 case・SuspensionReason の member ではない・R5-13）→ HOLD。表に無い項目 = SAFE_STOP。`EscalationPolicy.on_validity_expired`")
# --- R5-12（06 側）: cell 単位停止の原子性
if gate("R5-12"):
    d.rep("cell 単位の trigger は同一 `cell_identity_hash` の全 record を停止する（R3-09）。", "cell 単位の trigger は同一 `cell_identity_hash` の全 record を停止する（R3-09）— 同一 append batch（原子・連続 seq）で全兄弟 record に適用する（v0.2.7 R5-12）。")
# --- R5-06: MIN_FAULT_INJECTION に R_AUDIT_UNAVAILABLE
if gate("R5-06"):
    d.rep("R_INTER_ARM_VIOLATION, R_CLOCK_ANOMALY}   # v0.2.6（R4-13）", "R_INTER_ARM_VIOLATION, R_CLOCK_ANOMALY}   # v0.2.6（R4-13）\n                 ∪ {R_AUDIT_UNAVAILABLE}   # v0.2.7（R5-06）")
# --- R6-01: gripper finger geometry の束縛
if gate("R6-01"):
    d.rep("    tool_id: str                           # v0.2.6（R4-14）: tool の個体 serial（機種 id ではない）— TOOL_IDENTITY の照合先\n", "    tool_id: str                           # v0.2.6（R4-14）: tool の個体 serial（機種 id ではない）— TOOL_IDENTITY の照合先\n    finger_design_ref: str                 # v0.2.7（R6-01）: RS71 §0 #4 が human-LOCK する gripper finger 設計の識別子（`%s:26`）\n    finger_geometry_sha256: str            # v0.2.7（R6-01）: 上記設計の pinned geometry asset の content hash。RS71 #4 の pinned asset の hash と不一致 = P_TOOL_GEOMETRY_MISMATCH（第 1 評価点）・05 §3.4 (j) の再照合対象。値は本 doc に書かない\n" % RS71)
    d.insert_after_line("| kinematic_layout の各 arm base", "| `arms[].tool_payload.finger_geometry_sha256` が RS71 §0 #4 の pinned gripper geometry asset の hash と一致（`finger_design_ref` 未解決 = 違反。asset の同一性と pin の custody = RS71 §0-A・Rs・値は本 doc に書かない）（第 1 評価点・v0.2.7・R6-01） | `P_TOOL_GEOMETRY_MISMATCH` |")
    d.rep("`conjuncts[].schema_hash` / required record の `artifact_sha256`・v0.2.6 R3-17 / R4-02）", "`conjuncts[].schema_hash` / `arms[].tool_payload.finger_geometry_sha256`（v0.2.7 R6-01） / required record の `artifact_sha256`・v0.2.6 R3-17 / R4-02）")
    d.rep("TOOL_PAYLOAD_IDENTIFICATION = arms[].resource_id#tool_payload.tool_id（arm ごと）", "TOOL_PAYLOAD_IDENTIFICATION = arms[].resource_id#tool_payload.tool_id（arm ごと。artifact は `finger_design_ref` を attest する — 束縛のみ・開口実測等の内容は commissioning = OPP-5 / RT0・v0.2.7 R6-01）")
    d.rep("`P_ARM_*` / `P_TIMEOUT_ORDER`", "`P_ARM_*` / `P_TOOL_GEOMETRY_MISMATCH`（R6-01） / `P_TIMEOUT_ORDER`")
    newP.append("`P_TOOL_GEOMETRY_MISMATCH`"); newPT.append("| PT-%d | 同一 tool serial のまま別 finger 設計（別 `finger_geometry_sha256`）を宣言した profile（v0.2.7） | `P_TOOL_GEOMETRY_MISMATCH`（serial の TOOL_IDENTITY では検出できない経路） |" % (43 + len(newPT)))
# --- R6-02 / R6-20: P_FAULT_EVIDENCE_UNVERIFIED の subject 文法
if gate("R6-02"):
    fi_extra = " FI record は加えて `detection_to_safehold_worst_case_s ≥ max(t_mono(DISPOSITION) − t_mono(FAULT))`（引用範囲内の全 pair・R6-20）。" if conf("R6-20") else ""
    d.rep("| FAULT_INJECTION_RESULT / HEALTH_CHECK_RUN の `artifact_ref` が解決する audit 範囲に、`kind = FAULT ∧ fault == subject_ref の code ∧ profile_hash 一致`（fault）／ `kind ∈ {HEALTH_CONFIRMED, HEALTH_FAILED} ∧ payload に check_id`（health）の `RuntimeAuditRecord` が ≥ 1 件（第 2 評価点・v0.2.4 R2-02） | `P_FAULT_EVIDENCE_UNVERIFIED` |", "| FAULT_INJECTION_RESULT / HEALTH_CHECK_RUN の `artifact_ref` が解決する audit 範囲（全 record が profile_hash 一致）に、subject 文法ごとの期待 record が ≥ 1 件（第 2 評価点・v0.2.4 R2-02・v0.2.7 R6-02 で期待結果を subject ごとに固定）: `<check_id>` → HEALTH_CONFIRMED(check_id)；`<check_id>#NEGATIVE` → HEALTH_FAILED(check_id) ∧ FAULT(R_HEALTHCHECK_FAILED)；`<code>` → FAULT(fault == code)；`<code>#<trigger>` → FAULT(fault == code ∧ payload.trigger == trigger)；`NC#<name>` → §6.1 の期待 audit 内容表の record；その他の subject = FALSE。" + fi_extra + " | `P_FAULT_EVIDENCE_UNVERIFIED` |")
    d.rep("HEALTH_CHECK_RUN = check_id / FAULT_INJECTION_RESULT = fault code（timeout 駆動は '<code>#<trigger>'）", "HEALTH_CHECK_RUN = check_id | check_id#NEGATIVE（negative control） / FAULT_INJECTION_RESULT = code | code#trigger（timeout 駆動）| NC#<name>（negative control・§6.1）（v0.2.7 R6-02 で文法を閉じる）")
    d.rep("（fault code ではないので P_FAULT_CODE_UNKNOWN の対象外。P_FAULT_EVIDENCE_UNVERIFIED は下の期待 audit 内容で照合）", "（fault code ではないので P_FAULT_CODE_UNKNOWN の対象外。P_FAULT_EVIDENCE_UNVERIFIED の `NC#<name>` 枝が下の期待 audit 内容表で照合・v0.2.7 R6-02）")
    d.rep("| mandatory kind の各 `check_id` について、誘発した不一致で `R_HEALTHCHECK_FAILED` / HEALTH_FAILED を出した negative-control の HEALTH_CHECK_RUN record（artifact_ref → 当該 record を含む audit 範囲）が CLOSED_LOOP lease 前に存在（constant-True evaluator の排除・v0.2.4 R2-06） | `P_EVIDENCE_UNBOUND`（subject = check_id#NEGATIVE） |", "| mandatory kind の各 `check_id` について subject = `check_id#NEGATIVE` の HEALTH_CHECK_RUN record が CLOSED_LOOP lease 前に存在（存在のみ。内容 = `P_FAULT_EVIDENCE_UNVERIFIED` の `<check_id>#NEGATIVE` 枝で HEALTH_FAILED ∧ FAULT(R_HEALTHCHECK_FAILED) を要求・constant-True evaluator の排除・v0.2.4 R2-06・v0.2.7 R6-02） | `P_EVIDENCE_UNBOUND`（subject = check_id#NEGATIVE） |")
    d.rep("#   期待 audit 内容: ARM_SWAP / ARM_MISSING", "#   期待 audit 内容（規範・§3 `P_FAULT_EVIDENCE_UNVERIFIED` の `NC#<name>` 枝が参照する本文・v0.2.7 R6-02）: ARM_SWAP / ARM_MISSING")
elif gate("R6-20"):
    d.rep("の `RuntimeAuditRecord` が ≥ 1 件（第 2 評価点・v0.2.4 R2-02） | `P_FAULT_EVIDENCE_UNVERIFIED` |", "の `RuntimeAuditRecord` が ≥ 1 件（第 2 評価点・v0.2.4 R2-02）。FI record は加えて `detection_to_safehold_worst_case_s ≥ max(t_mono(DISPOSITION) − t_mono(FAULT))`（引用範囲内・v0.2.7 R6-20） | `P_FAULT_EVIDENCE_UNVERIFIED` |")
# --- R6-04: one-key record の検査を state で限定
if gate("R6-04"):
    d.rep("必須 field 欠落；generation が同一 profile_hash の直前 record + 1 でない；CLOSED_LOOP ∈ allowed_lease_modes ⇒", "必須 field 欠落；**state ∈ {PROPOSED, ACCEPTED} の record について**（v0.2.7 R6-04）: generation が同一 profile_hash の直前 ACCEPTED / PROPOSED record + 1 でない；CLOSED_LOOP ∈ allowed_lease_modes ⇒")
    d.rep("SUSPENDED で `suspension_reason` None。", "SUSPENDED で `suspension_reason` None。**state ∈ {SUSPENDED, REVOKED} の record について**（one-key fail-safe・v0.2.7 R6-04）: `supersedes_record_hash` 必須（head を指す）；generation = superseded record と同一；`allowed_lease_modes = ()`；approvals ≥ 1（role registry に登録された operator_ref、または MONITOR。two-key・相異は要求しない）；hash field と `valid_until` は superseded record から複写；**SUSPENDED / REVOKED の append を approval 不足で拒否することは無い** — 拒否理由は fork・supersedes 欠落 / 未知・未知の profile_hash・`suspension_reason` None のみ（失効は常に通る）。")
    newPT.append("| PT-%d | MONITOR 単独の approvals で SUSPENDED record を append（v0.2.7） | 受理される（one-key）・05 event 行 / head-check（PT-40）で活性 lease は SAFEHOLD |" % (43 + len(newPT)))
# --- R6-05 / R6-06: 権威ある role registry
if gate("R6-05", "R6-06"):
    d.rep("    role_registry_hash: str                # v0.2.6（R4-04）: operator_ref → 資格 role 集合の content-addressed registry（受理時に照合・profile preimage 外）", "    role_registry_hash: str                # v0.2.6（R4-04）: operator_ref → 資格 role 集合の content-addressed registry（受理時に照合・profile preimage 外）。v0.2.7（R6-05）: 自己申告ではなく **role registry の現 head** との等値を record 書込時と 05 §3.4 (i) / 条件 12 で要求（不一致 = 05 `R_PROFILE_SUSPENDED`）。record 側の値は監査用に保持")
    d.rep("class SuspensionReason(Enum):    INCIDENT | ISL_ANOMALY | IDENTITY_CHANGE | LAYOUT_CHANGE | BASELINE_SUPERSEDED | DIAGNOSTIC_FAILURE | CLOCK_ANOMALY | OPERATOR   # v0.2.6（R4-11）", "class SuspensionReason(Enum):    INCIDENT | ISL_ANOMALY | IDENTITY_CHANGE | LAYOUT_CHANGE | BASELINE_SUPERSEDED | DIAGNOSTIC_FAILURE | CLOCK_ANOMALY | OPERATOR | ROLE_REGISTRY_SUPERSEDED   # v0.2.6（R4-11）・v0.2.7（R6-05）: ROLE_REGISTRY_SUPERSEDED = role registry の head 変更（bound する全 ACCEPTED record を停止）")
    d.rep("IDENTITY_CHANGE / LAYOUT_CHANGE / BASELINE_SUPERSEDED / DIAGNOSTIC_FAILURE / OPERATOR → HOLD。", "IDENTITY_CHANGE / LAYOUT_CHANGE / BASELINE_SUPERSEDED / DIAGNOSTIC_FAILURE / OPERATOR / ROLE_REGISTRY_SUPERSEDED（R6-05）→ HOLD。")
    d.rep("`cell_identity_hash ≠ H_WCJ(profile.cell)`（R4-09）；", "`cell_identity_hash ≠ H_WCJ(profile.cell)`（R4-09）；`role_registry_hash ≠ role registry の現 head`（書込時・R6-05）；")
    d.insert_after_line("- **反循環**: `timing_baseline_hash`", "- **role registry（v0.2.7・R6-05 / R6-06）**: operator_ref → 資格 role 名の集合を持つ content-addressed artifact で、ProfileRegistry と同じ custody の下に**ただ 1 つの head** を持つ（head の発行者 / ACL = OPP-13 open・Rs）。acceptance record（`role_registry_hash`）と 05 clearance record は書込時に現 head との等値と `(operator_ref, role) ∈ registry` を要する。head の変更 = supersession: 認可された一者または monitor が bound する全 ACCEPTED record に `SUSPENDED(ROLE_REGISTRY_SUPERSEDED)` を append（→ HOLD・再受理は新 generation）。role 名の語彙は registry が定義する（AcceptanceRole を含み、clearance 用 role（例: safety officer）も同じ語彙）。")
    if conf("R6-06"):
        d.rep("v0.2.1（C-13）: IndependentSafetyLayer の clearance record・durable 整合検査の**代替ではない**（常に AND）", "v0.2.1（C-13）: IndependentSafetyLayer の clearance record・durable 整合検査の**代替ではない**（常に AND）。v0.2.7（R6-06）: role 名は §8.3 role registry が定義する語彙に限る（未知の role 名 = codec 拒否）。clearance record は `role_registry_hash` を運び、現 head との等値と operator_ref の資格を照合される（05 §5.4）")
        newPT.append("| PT-%d | role registry に無い operator_ref が SAFE_STOP の role を自己申告した clearance record（v0.2.7） | 05 CAS 条件 10 不成立（該当 record 無し）・R_PERMIT_MISBOUND |" % (43 + len(newPT)))
# --- R6-07: base pose tolerance・符号付き・評価点
if gate("R6-07"):
    d.rep("    approved_ceiling: dict                 # RuntimeTimeouts の全 field → 上限 [s]（int field は回数）", "    base_pose_tolerance_m: CanonicalDecimal      # v0.2.7（R6-07）: BASE_POSE_VERIFY / P_BASE_LAYOUT_MISMATCH の並進許容 [m]（値 = RT0）\n    base_pose_tolerance_rad: CanonicalDecimal    # v0.2.7（R6-07）: 同・回転許容 [rad]\n    approved_ceiling: dict                 # RuntimeTimeouts の全 field → 上限 [s]（int field は回数）")
    d.rep("| kinematic_layout の各 arm base の Y が RS71 §0 #2 の固定 base（`%s:24`・値は本 doc に書かない）と baseline 許容内で一致（v0.2.6・R4-17） | `P_BASE_LAYOUT_MISMATCH` |" % RS71, "| kinematic_layout の各 arm base が resource_id ごとに**符号付き**で RS71 §0 #2 の固定 base（`%s:24`・機械可読 SSOT = `thread_isaac_lab/configs/task_config.py:21-22` の ROBOT_LEFT_BASE / ROBOT_RIGHT_BASE・値は本 doc に書かない）と `baseline.base_pose_tolerance_m` / `_rad` 内で一致（`layout[arm.base_transform_id]` の Y を arm.resource_id ごとに符号付きで照合: ee_left ↔ ROBOT_LEFT_BASE・ee_right ↔ ROBOT_RIGHT_BASE。鏡像配置は不一致）。評価 = 第 1 評価点（PROPOSED record の baseline を解決・R6-09）+ 第 2 評価点（v0.2.6・R4-17・v0.2.7 R6-07） | `P_BASE_LAYOUT_MISMATCH` |" % RS71)
    d.rep("BASE_POSE_VERIFY = 実測 base pose と kinematic_layout の T_cell←base の差が baseline 許容内（arm ごと）", "BASE_POSE_VERIFY = 実測 base pose と kinematic_layout の T_cell←base の差が `baseline.base_pose_tolerance_m` / `_rad` 内（arm ごと・符号付き・v0.2.7 R6-07）")
    add_second("`P_BASE_LAYOUT_MISMATCH`（baseline 許容を要する・R6-07）")
    newPT.append("| PT-%d | 両 arm の base を入替えた鏡像 layout（各 base は許容内に存在）（v0.2.7） | `P_BASE_LAYOUT_MISMATCH`（resource_id ごとの符号付き照合） |" % (43 + len(newPT)))
# --- R6-08: MIN_DIAGNOSTIC_ITEMS
if gate("R6-08"):
    items = ["VALIDITY_MONITOR_LIVENESS"] + (["VALIDITY_DEADLINE_DETECTION"] if conf("R5-11") else []) + (["AUDIT_RECORDER_LIVENESS"] if conf("R5-06") else []) + ["CLOCK_DRIFT", "REGISTRY_HEAD_CHECK", "CONTROLLER_IDENTITY", "TOOL_IDENTITY", "SAFETY_LAYER_IDENTITY", "BASE_POSE_VERIFY"]
    d.insert_after_line("- 検査 `P_ACCEPTANCE_RECORD_INVALID`", "- **REQUIRED_DIAGNOSTIC_ITEMS（v0.2.7・R6-08・閉じた語彙・規範）**: `baseline.diagnostic_items` の項目名 ⊇ {" + ", ".join(items) + "}。実行者: VALIDITY_MONITOR_LIVENESS / REGISTRY_HEAD_CHECK" + (" / AUDIT_RECORDER_LIVENESS" if conf("R5-06") else "") + " = AuthorityManager（05 §3.7 head-check）、CLOCK_DRIFT = AuthorityManager（05 §3.4 (l)）、identity 系 4 項目 = `health_checks[]` の同 kind の check_id を lease 中に周期再実行（結果は (m) と head-check が参照）。周期・worst-case の値は baseline = OPP-16。不足 = `P_BASELINE_INCOMPLETE`（record 書込時 + 第 2 評価点）。空の `diagnostic_items` で周期層が消える経路を閉じる。")
    d.insert_after_line("| kinematic_layout の各 arm base", "| acceptance record が指す `CellSafetyTimingBaseline.diagnostic_items` ⊇ REQUIRED_DIAGNOSTIC_ITEMS（§8.3・record 書込時 + 第 2 評価点）（v0.2.7・R6-08） | `P_BASELINE_INCOMPLETE` |")
    d.rep("本 doc は hash 束縛と検査だけを持つ（v0.2.5・OPP-11） | §8.3・05 OP-20 | RT0 へ carry |", "本 doc は hash 束縛と検査だけを持つ（v0.2.5・OPP-11）。v0.2.7 open（R6-07 / R6-08 / R6-11）: `base_pose_tolerance_*` / `max_validity_s` の値、identity 系 diagnostic item を必須（§2.1 comment の現行）とするか「baseline が定める場合」に緩めるか | §8.3・05 OP-20 | RT0 へ carry |")
    add_second("`P_BASELINE_INCOMPLETE`（R6-08）")
    newP.append("`P_BASELINE_INCOMPLETE`"); newPT.append("| PT-%d | `diagnostic_items = ()` の baseline を指す acceptance record（v0.2.7） | `P_BASELINE_INCOMPLETE`（record 拒否） |" % (43 + len(newPT)))
# --- R6-09: baseline 値を要する順序項の評価点
if gate("R6-09"):
    d.rep("`max_reselect_attempts × worst_case_attempt_s + selector_overhead_s ≤ boundary_dwell_s`（worst_case / overhead は timing baseline の値）", "`max_reselect_attempts × worst_case_attempt_s + selector_overhead_s ≤ boundary_dwell_s`（worst_case / overhead は登録時の PROPOSED record が指す timing baseline の値・§8.1 (2)・v0.2.7 R6-09）")
    d.rep("**評価点は 2 つ**: 第 1 評価点 = 登録時（構造・単調性・反循環・codec・", "**評価点は 2 つ**: 第 1 評価点 = 登録時 = `ProfileAcceptanceRecord(state = PROPOSED, timing_baseline_hash, …)` の書込みの下で評価し、baseline 依存項（`P_TIMEOUT_ORDER` の worst_case / overhead 項・`P_BASE_LAYOUT_MISMATCH`）はその `timing_baseline_hash` を解決する（PROPOSED record の `P_ACCEPTANCE_RECORD_INVALID` = 必須 field + baseline 解決可能・v0.2.7 R6-09）（構造・単調性・反循環・codec・")
    d.rep("- **状態遷移**: PROPOSED → ACCEPTED（受理）;", "- **状態遷移**: PROPOSED（登録 = 第 1 評価点の文脈・`timing_baseline_hash` を運ぶ・R6-09）→ ACCEPTED（受理）;")
# --- R6-10: baseline registry
if gate("R6-10"):
    d.insert_after_line("- **反循環**: `timing_baseline_hash`", "- **baseline registry（v0.2.7・R6-10）**: `CellSafetyTimingBaseline` は cell_id ごとに head を持つ content-addressed store に置く（発行主体・改訂手続 = OPP-16）。head の変更 = supersession: monitor は event（BASELINE_SUPERSEDED）を出し、manager は head-check で `head(baseline_registry, cell_id) ≠ record.timing_baseline_hash` を monitor 非依存に検出する（05 §3.7）。")
# --- R6-14: arm 単位 kind の ∀
if gate("R6-14"):
    d.rep("CALIBRATION_RECORD ∀ `calibration_refs[].calibration_id`・HEALTH_CHECK_RUN ∀ `health_checks[].check_id`・", "CALIBRATION_RECORD ∀ `calibration_refs[].calibration_id`・CONTROLLER_ENVELOPE_MEASUREMENT / TOOL_PAYLOAD_IDENTIFICATION ∀ `cell.arms[]`（subject = §6.1・v0.2.7 R6-14）・HEALTH_CHECK_RUN ∀ `health_checks[].check_id`・")
# --- R6-15: FI は cell 全体・検査は ∀ arm
if gate("R6-15"):
    d.rep("FI = 当該 arm の R_SAFETY_LAYER_LOST#HEARTBEAT_TIMEOUT の FAULT_INJECTION_RESULT artifact（struct:", "FI = cell 全体の R_SAFETY_LAYER_LOST#HEARTBEAT_TIMEOUT の FAULT_INJECTION_RESULT artifact（両 arm を worst-case 負荷で同時に動かした 1 record・`load_condition_ref` は両 arm を名指す・検査は ∀ arm で CEM[arm] を用いる・v0.2.7 R6-15。struct:")
# --- R6-18: operator 相異の文と基準時刻
if gate("R6-18"):
    d.rep("v0.2.6（R4-04）: operator_ref は role ごとに相異・role_registry で資格照合", "v0.2.6（R4-04）: operator_ref の相異の範囲 = 本 §8.3 `P_ACCEPTANCE_RECORD_INVALID` の定義（SAFETY_APPROVER / CUSTODY_APPROVER / OPERATOR 間・v0.2.7 R6-18）・role_registry で資格照合")
    d.rep("`valid_until` None または baseline `max_acceptance_validity_s` 超過；", "`valid_until` None または `valid_until − registry append の wall time > baseline.max_acceptance_validity_s`（基準時刻 = append 時・v0.2.7 R6-18）；")
# --- R6-19: 自己申告依存の明示
if gate("R6-19"):
    d.insert_after_line("10. **D1.1-C artifact manifest**", "11. **identity 系 check の限界（v0.2.7・R6-19）**: identity 系 check（CONTROLLER / TOOL / SAFETY_LAYER）は機器の**自己申告値**と宣言の等値であり、個体の物理同一性・報告の真正性は evidence（CELL_COMMISSIONING / TOOL_PAYLOAD_IDENTIFICATION）と cell の運用管理の court。本 doc は主張しない。")
if newP:
    cl = d.line("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`"); d.repline("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`", cl + " / " + " / ".join(newP) + "（v0.2.7）")
if newPT: d.insert_after_line("| PT-42 |", "\n".join(newPT))
rows06 = [("R5-01 / R6-16", "SHADOW の deadline 扱い（§5 (b)・PT-13・§8.3）", "§5 (b)・PT-13・§8.3・§11 裁定 OP-19 行"), ("R5-04 / R5-14 / R6-11 / R6-17", "P_VALIDITY_UNBOUNDED の評価点・kind 集合・上限", "§3・§6.1 comment・§8.1 (2)・§8.3 `max_validity_s`・§5 (b) 表"), ("R5-09 / R6-12", "§5 の「3 項」", "§5"), ("R5-10 / R6-03", "'#DEADLINE' 等の subject が FaultInjectionRequirement で表現不能", "§6.1 `trigger`・§3 P_FAULT_CODE_UNKNOWN / P_EVIDENCE_UNBOUND"), ("R5-13", "ACCEPTED → ACCEPTED(gen+1) が無い", "§8.3 状態遷移・§5 (b) 表"), ("R5-06", "MIN_FAULT_INJECTION に R_AUDIT_UNAVAILABLE", "§6.1"), ("R6-01", "gripper finger geometry（RS71 #4）が profile に束縛されない", "§2.1 `finger_design_ref` / `finger_geometry_sha256`・§3 `P_TOOL_GEOMETRY_MISMATCH`・§6.1・PT"), ("R6-02 / R6-20", "P_FAULT_EVIDENCE_UNVERIFIED が期待結果を区別しない・FI 値の照合", "§3・§6.1 subject 文法"), ("R6-04", "one-key SUSPENDED record が P_ACCEPTANCE_RECORD_INVALID に落ちる", "§8.3 検査・PT"), ("R6-05 / R6-06", "role registry が自己申告・clearance が role label", "§8.3 role registry（1 head）・`SuspensionReason.ROLE_REGISTRY_SUPERSEDED`・§5 (b) 表・§2.1 clearance_roles・PT"), ("R6-07", "base pose の許容が無い・評価点・鏡像", "§8.3 `base_pose_tolerance_m` / `_rad`・§3・§2.1・PT・OPP-16"), ("R6-08", "diagnostic_items の最小集合", "§8.3 REQUIRED_DIAGNOSTIC_ITEMS・§3 `P_BASELINE_INCOMPLETE`・PT・OPP-16"), ("R6-09", "P_TIMEOUT_ORDER の baseline 項の評価点", "§8.1 (2) PROPOSED record 文脈・§3・§8.3 状態遷移"), ("R6-10", "baseline registry・head-check", "§8.3"), ("R6-14", "P_EVIDENCE_UNBOUND の arm 単位 kind", "§3"), ("R6-15", "FI の arm 解決", "§3 `P_SAFETY_BUDGET_EXCEEDED`"), ("R6-18", "operator 相異の文・基準時刻", "§8.3"), ("R6-19", "identity の自己申告依存", "§9 #11"), ("R6-13", "checker Q2 の弱さ（(j) 行全体への部分一致・§2.2 未走査・artifact_sha256 の多重）", "`check_review_candidate.py` Q2（08 §1）")]
tbl = [f"- **v0.2.7 fold（{NOW}）— round 4（R5 / R6 → V5 / V6）の確定 finding の fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §10:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in rows06: tbl.append(f"| {i} | {c} | {s if any_conf(*i.split(' / ')) else '— 適用せず'} | {'; '.join(f'{x}={vstr(x)}' for x in i.split(' / '))} |")
d.insert_before_line("## 12. Review anchors", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= checker Q2 (R6-13)
if gate("R6-13"):
    c = Doc("check_review_candidate.py")
    c.rep('''        s21 = text[text.find("### 2.1"):text.find("### 2.2")]
        hf = sorted({m for m in re.findall(r"^\\s{4}(\\w+(?:_sha256|_hash)):", s21, re.M)})
        sib05 = os.path.join(os.path.dirname(os.path.abspath(path)), "05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md")
        if os.path.isfile(sib05):
            t05 = open(sib05, encoding="utf-8").read(); jl = [l for l in t05.splitlines() if "(j) profile が宣言する" in l]
            if not jl: fails.append("Q2 05 §3.4 (j) enumeration line not found")
            else:
                for h in hf:
                    if h not in jl[0]: fails.append(f"Q2 06 §2.1 hash field '{h}' is not named in 05 §3.4 (j)")''',
          '''        # v0.2.7 (R6-13): scan §2.1 AND §2.2, match only inside the (j) segment, and require one mention per declaring class
        s2 = text[text.find("### 2.1"):text.find("### 2.3")]
        decl = {}
        for cls, body in re.findall(r"^class (\\w+)[^\\n]*\\n((?:^    [^\\n]*\\n?)+)", s2, re.M):
            for h in re.findall(r"^\\s{4}(\\w+(?:_sha256|_hash)):", body, re.M): decl.setdefault(h, set()).add(cls)
        sib05 = os.path.join(os.path.dirname(os.path.abspath(path)), "05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md")
        if os.path.isfile(sib05):
            t05 = open(sib05, encoding="utf-8").read(); jl = [l for l in t05.splitlines() if "(j) profile が宣言する" in l]
            if not jl: fails.append("Q2 05 §3.4 (j) enumeration line not found")
            else:
                a = jl[0].find("(j) profile が宣言する"); b = jl[0].find("が解決先の内容と一致", a)
                seg = jl[0][a:b] if b > a else jl[0][a:]
                if b <= a: warns.append("Q2 (j) segment end marker not found; matching against the whole (j) tail")
                for h, cls in sorted(decl.items()):
                    n = len(re.findall(r"(?<![\\w.])" + re.escape(h) + r"(?!\\w)", seg.replace("`", " "))) + len(re.findall(r"\\." + re.escape(h) + r"(?!\\w)", seg))
                    if n == 0: fails.append(f"Q2 06 §2.1/2.2 hash field '{h}' ({'/'.join(sorted(cls))}) is not named in 05 §3.4 (j)")
                    elif n < len(cls): fails.append(f"Q2 06 hash field '{h}' is declared by {len(cls)} classes ({'/'.join(sorted(cls))}) but named {n} time(s) in 05 §3.4 (j)")''')
    c.rep("Q2  (profile spec only, v0.2.6 / R3-17 R4-02) every *_sha256 / *_hash field declared in 06 §2.1 is named in the sibling 05 §3.4 (j) content-hash enumeration", "Q2  (profile spec only, v0.2.6 / R3-17 R4-02 / v0.2.7 R6-13) every *_sha256 / *_hash field declared in 06 §2.1-2.2 is named inside the sibling 05 §3.4 (j) segment, at least once per declaring class")
    e = Doc("08_INDEPENDENT_REVIEW_PLAN_20260903.md"); e.rep("Q2 06 §2.1 の hash field ⊆ 05 §3.4 (j) 列挙を機械検査する — v0.2.6）", "Q2 06 §2.1–2.2 の hash field が 05 §3.4 (j) 区間内に宣言 class ごとに 1 回以上名指しされることを機械検査する — v0.2.6・v0.2.7 R6-13 で強化）"); e.save()
    c.save()

for name in ("07_SUCCESSOR_CONTRACT_DECISION_20260903.md", "04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md", "08_INDEPENDENT_REVIEW_PLAN_20260903.md"):
    d = Doc(name); d.rep("(v0.2.6 REVIEW CANDIDATE)", "(v0.2.7 REVIEW CANDIDATE)"); d.rep("REVIEW CANDIDATE v0.2.6（", "REVIEW CANDIDATE v0.2.7（"); d.save()
print("applied:", applied); print("NOW =", NOW)
