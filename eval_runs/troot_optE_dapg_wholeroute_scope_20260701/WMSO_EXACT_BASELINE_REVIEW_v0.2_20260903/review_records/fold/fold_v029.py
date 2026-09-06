#!/usr/bin/env python3
"""v0.2.8 -> v0.2.9 fold (external review round: GPT-astra GA-01..07 gated by Claude verifier V9 verdicts). Records-only; frozen files untouched.
Usage: python3 fold_v029.py <PKG_DIR> <verdicts_v029.json>   verdicts = {id: {"confirmed": bool, "severity": str, "merged_into": str}}"""
import sys, json, subprocess, os
P = sys.argv[1]; VERD = json.load(open(sys.argv[2]))
NOW = subprocess.check_output(["date", "-u", "+%Y-%m-%d %H:%M UTC"]).decode().strip()
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
d.rep("RUNTIME SPEC (v0.2.8 REVIEW CANDIDATE)", "RUNTIME SPEC (v0.2.9 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.8（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.7 → v0.2.8 = v0.2.7 本文への再レビュー round 5（R7 / R8 → V7 / V8）の確定 finding の fold（§13）。旧版の系譜:", "- status: **REVIEW CANDIDATE v0.2.9（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.8 → v0.2.9 = v0.2.8 本文への外部レビュー（GPT-astra GA-01..07 → Claude verifier V9）の確定 finding の fold（§13）。旧版の系譜: — v0.2.7 → v0.2.8 = v0.2.7 本文への再レビュー round 5（R7 / R8 → V7 / V8）の確定 finding の fold（§13）。旧版の系譜:")
d.rep("**round 5（R7 / R8 → V7 / V8）の fold = 本版 v0.2.8（§13）**", "round 5（R7 / R8 → V7 / V8）の fold = v0.2.8（2026-09-06 00:30 UTC）→ **外部レビュー（GPT-astra GA → V9）の fold = 本版 v0.2.9（§13）**")
newT = []
def addT(txt): newT.append("| T-%d | %s |" % (49 + len(newT), txt))
# --- GA-01: gateway 局所 stop_latch（自ら出した (i′) SafeStop を manager 不読中に失わない）
if gate("GA-01"):
    d.rep("+ `last_disposition`（直近に成功した線形化読みで観測した `safehold_disposition`・v0.2.8 R7-04） |", "+ `last_disposition`（直近に成功した線形化読みで観測した `safehold_disposition`・v0.2.8 R7-04）+ `stop_latch`（gateway 自身が (i′) で SafeStop を出した時点で True・durable 不要・v0.2.9 GA-01） |")
    d.rep("  (i′)  else if IndependentSafetyLayer の heartbeat が safety_heartbeat_timeout_s を超えて欠落 → SafeStop（(ii) を評価しない・v0.2.2・B2-01）", "  (i′)  else if IndependentSafetyLayer の heartbeat が safety_heartbeat_timeout_s を超えて欠落 ∨ stop_latch → SafeStop（(ii) を評価しない・v0.2.2・B2-01。v0.2.9 GA-01: gateway は (i′) で SafeStop を出した時点で局所 `stop_latch := True` とし、解除は線形化読みで seq > latch 時観測 seq の SAFEHOLD state を観測したとき（= manager の TRANSFER_TO_SAFEHOLD(SAFETY) が線形化済）のみ — 以後は (iii) の `safehold_disposition == SAFE_STOP` 規則が §5.4 clearance まで SafeStop を担う。heartbeat が戻っても manager 不読 / SAFETY CAS 未線形化なら SafeStop を維持し (ii) を再開しない。gateway は (i′) の観測を R_MANAGER_UNAVAILABLE 行と同形で manager へ報告する = manager が欠落を独立観測していない場合の SAFETY CAS の起点）")
    d.rep("gateway 局所の `last_disposition == SAFE_STOP` なら SafeStop・それ以外 SafeHold（起動直後 = SafeHold・INV-25・v0.2.8 R7-04: manager 不読で SafeStop が SafeHold に緩まない）", "gateway 局所の `last_disposition == SAFE_STOP ∨ stop_latch` なら SafeStop・それ以外 SafeHold（起動直後 = SafeHold・INV-25・v0.2.8 R7-04・v0.2.9 GA-01: manager 不読で SafeStop が SafeHold に緩まない — gateway 自身が出した (i′) の停止も含む）")
    d.rep("その間の (iii) の SafeStop / SafeHold は gateway 局所 `last_disposition` で決める（v0.2.2・B-H1・v0.2.8 R7-04） | R_MANAGER_UNAVAILABLE |", "その間の (iii) の SafeStop / SafeHold は gateway 局所 `max(last_disposition, stop_latch)`（stop_latch = SAFE_STOP 相当）で決める（v0.2.2・B-H1・v0.2.8 R7-04・v0.2.9 GA-01） | R_MANAGER_UNAVAILABLE |")
    d.rep("出力 = (iii)（`last_disposition` を保持: SAFE_STOP なら SafeStop・R7-04）", "出力 = (iii)（`max(last_disposition, stop_latch)` を保持: SAFE_STOP / latch なら SafeStop・R7-04 / GA-01）")
    old = d.line("| INV-29 |"); d.repline("| INV-29 |", old.replace("かつ TRANSFER_TO_SAFEHOLD(SAFETY) が発行される（v0.2.2・B2-01） |", "かつ TRANSFER_TO_SAFEHOLD(SAFETY) が発行される（v0.2.2・B2-01）。(ii) は gateway 局所 `stop_latch` の解除（SAFETY CAS の線形化を観測）まで評価されない（v0.2.9 GA-01） |"))
    d.rep("safety 起因（SAFETY / SAFE_STOP）の CONFLICT では §5.2 (i) / (i′) / (iii) に既に落ちている。", "safety 起因（SAFETY / SAFE_STOP）の CONFLICT では §5.2 (i) / (i′) / (iii) に既に落ちている（(i′) は `stop_latch` で SAFETY CAS の線形化まで保持・v0.2.9 GA-01）。")
    addT("manager link 断中に ISL heartbeat 欠落 → 復帰（link 依然断）（v0.2.9） | (i′) の `stop_latch` により SafeStop 維持・SafeHold へ緩まない")
    addT("ISL heartbeat 欠落 → `command_deadline_s` 内に復帰・manager state = EXECUTOR のまま（v0.2.9） | `stop_latch` 解除 = SAFETY CAS の線形化観測まで (ii) 不再開")
# --- GA-02: certificate / lease / invocation を SkillDefinitionHash で束縛
if gate("GA-02"):
    d.rep("8. `proposed_lease.skill_action_id` が certified（certificate 存在）。", "8. `cert = certificate(proposed_lease.skill_action_id)` が存在（Draft 不可）∧ `cert.skill_definition_hash == proposed_lease.skill_definition_hash == invocation.skill_definition_hash == H_WCJ(definition_c)`（definition_c = §6.2 B4 で `validate_invocation_start` に渡し executor が実行する definition 物。不一致 = REJECTED・`R_INVOCATION_INVALID`・v0.2.9 GA-02: SkillActionId の preimage は provenance を含まない（frozen `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:158`）ため ActionId の一致は本文一致の代用にならない）。")
    d.rep("の `skill_action_id == proposed_lease.skill_action_id`。⚠ frozen `AuthorityDecision` は profile を知らない", "の `skill_action_id == proposed_lease.skill_action_id` ∧ その certificate が条件 8 の `cert` と同一（`skill_definition_hash` 等値・不一致 = `R_AUTHORITY_DECISION_MISBOUND`・v0.2.9 GA-02）。⚠ frozen `AuthorityDecision` は profile を知らない")
    d.rep("      c.skill_action_id が certified か（§7-2）", "      c.skill_action_id が certified か（§7-2）。definition_c := certificate.skill_definition_hash と H_WCJ が一致する登録 definition（同 ActionId の複数 entry は certificate の hash で解決・解決不能 = R_INVOCATION_INVALID）；new_invocation は skill_definition_hash := H_WCJ(definition_c)（v0.2.9 GA-02）")
    d.rep("= 06 §8.3 read-only のまま）; (j) profile が宣言する", "= 06 §8.3 read-only のまま）; (n) **definition の束縛（v0.2.9・GA-02）**: 条件 8 と同じ等値（`cert.skill_definition_hash == proposed_lease.skill_definition_hash == invocation.skill_definition_hash == H_WCJ(definition_c)`）を発行時にも検査。違反 = `R_INVOCATION_INVALID`・permit 不発行; (j) profile が宣言する")
    d.rep("    now_used: float                                   # validate_invocation_start に渡した now", "    now_used: float                                   # validate_invocation_start に渡した now" + ("（start_belief_ref / now_used は permit から複写・同一物・v0.2.9 GA-03）" if conf("GA-03") else "") + "\n    definition_hash_used: str                         # v0.2.9（GA-02）: = H_WCJ(definition_c)。invocation_validation_report_ref は (invocation_id, definition_hash_used, now_used) に束縛され、別 definition の成功 report を転用できない")
    d.rep("    skill_definition_hash: str\n", "    skill_definition_hash: str                        # v0.2.9（GA-02）: == certificate.skill_definition_hash == invocation.skill_definition_hash == H_WCJ(definition_c)（条件 8・permit 前提 (n)）\n")
    d.rep("| INV-15 | `lease.skill_action_id` に対する `ContractCertificate` が存在（Draft 不可） | 候補除外 |", "| INV-15 | `lease.skill_action_id` に対する `ContractCertificate` が存在（Draft 不可）∧ `cert.skill_definition_hash == lease.skill_definition_hash`（v0.2.9 GA-02） | 候補除外 / R_INVOCATION_INVALID |")
    d.rep("| INV-14 | `definition.required_control_resources ⊆ lease.ownership.control`（frozen `:380` の包含） | R_INVOCATION_INVALID |", "| INV-14 | `definition.required_control_resources ⊆ lease.ownership.control`（frozen `:380` の包含・definition = H_WCJ が `lease.skill_definition_hash` に一致する物・v0.2.9 GA-02） | R_INVOCATION_INVALID |")
    addT("同 SkillActionId・異 SkillDefinitionHash（provenance のみ相違）の definition で lease 提案（v0.2.9） | 条件 8 / permit 前提 (n) 不成立・R_INVOCATION_INVALID・REJECTED")
# --- GA-03: 開始判断の belief 鮮度を permit / CAS に束縛
if gate("GA-03"):
    d.rep("    acceptance_generation: int\n    validity_deadline_mono: float                     # v0.2.5（OP-19）: min(calibration 期限", "    acceptance_generation: int\n    start_belief_ref: BeliefRef                       # v0.2.9（GA-03）: §6.2 B4 で validate_invocation_start に渡した belief（frozen 型そのまま）\n    belief_valid_until_mono: float                    # v0.2.9（GA-03）: = t_obs + min(ttl, runtime_max_staleness_s〔None なら ttl のみ〕) を validate 時に manager clock で確定。effective_expires_at の min に含める\n    validity_deadline_mono: float                     # v0.2.5（OP-19）: min(calibration 期限")
    d.rep("= min(expires_at, ack.valid_until, validity_deadline_mono, [decision.t_mono + decision_max_age_s — authority_decision_ref ≠ None のときのみ])", "= min(expires_at, ack.valid_until, validity_deadline_mono, belief_valid_until_mono（v0.2.9 GA-03）, [decision.t_mono + decision_max_age_s — authority_decision_ref ≠ None のときのみ])")
    d.rep("validity なら該当 `R_*_EXPIRED_ACTIVE` / `R_PROFILE_SUSPENDED`、ttl のみなら `R_PERMIT_EXPIRED`", "validity なら該当 `R_*_EXPIRED_ACTIVE` / `R_PROFILE_SUSPENDED`、belief 項（`belief_valid_until_mono`）なら `R_INVOCATION_INVALID`・disposition RE_OBSERVE（B2 から再観測・再検証・再 ACK・再 permit・v0.2.9 GA-03）、ttl のみなら `R_PERMIT_EXPIRED`")
    d.rep("前者の評価に用いた `authority_epoch_snapshot == expected.control_epoch`。", "前者の評価に用いた `authority_epoch_snapshot == expected.control_epoch`。後者は `(permit.start_belief_ref, InitializationRecord.now_used, H_WCJ(definition_c))` に束縛され `now < permit.belief_valid_until_mono`（v0.2.9 GA-03: 開始判断に用いた観測が CAS 時にも有効・観測 / 初期化条件を更新した場合は検証・ACK・permit を再取得）。")
    d.rep("decision age < decision_max_age_s（厳密境界・条件 6・12・v0.2.8 R7-08）", "decision age < decision_max_age_s ∧ now < permit.belief_valid_until_mono（厳密境界・条件 2・5・6・12・v0.2.8 R7-08・v0.2.9 GA-03）")
    addT("t_validate < t_belief_expiry ≤ t_CAS < t_effective_expiry の順で ACK 待ち（v0.2.9） | 条件 2 の belief 項到達・R_INVOCATION_INVALID・RE_OBSERVE（B2 から再観測）")
if gate("GA-02", "GA-03"):
    d.rep("| validate_invocation_start 失敗 | Orchestrator | `R_INVOCATION_INVALID` | 変化なし | `RESELECT` / `RE_OBSERVE`（freshness 起因） |", "| validate_invocation_start 失敗、または CAS 条件 2 の belief 項到達 / 条件 5 の束縛不一致 / 条件 8 の definition hash 不一致（v0.2.9 GA-02 / GA-03） | Orchestrator / AuthorityManager | `R_INVOCATION_INVALID` | 変化なし（CAS では REJECTED・permit VOID） | `RESELECT` / `RE_OBSERVE`（freshness / belief 起因 = B2 から再観測） |")
# --- GA-04: 兄弟停止の key を構成 hash から物理 cell の安定 id へ
if gate("GA-04"):
    d.rep("同一 `cell_identity_hash` を持つ他 profile の head record が `state ∈ {SUSPENDED, REVOKED}`（新 generation の ACCEPTED で置換されていない）なら本 profile も `R_PROFILE_SUSPENDED`", "同一 `(site_id, cell_id)`（= 物理 cell の安定 id・doc 06 §8.3。構成 hash `cell_identity_hash` ではない・v0.2.9 GA-04）を持つ他 profile の head record が `state ∈ {SUSPENDED, REVOKED}`（新 generation の ACCEPTED で置換されていない）なら本 profile も `R_PROFILE_SUSPENDED`")
    d.rep("∧ 同一 cell_identity_hash の他 profile の head record に state ∈ {SUSPENDED, REVOKED} が無い", "∧ 同一 (site_id, cell_id) の他 profile の head record に state ∈ {SUSPENDED, REVOKED} が無い（GA-04）")
    d.rep("または同一 `cell_identity_hash` を持つ他 profile の head record が state ∈ {SUSPENDED, REVOKED}（新 generation の ACCEPTED で置換されていない）（R5-12）", "または同一 `(site_id, cell_id)` を持つ他 profile の head record が state ∈ {SUSPENDED, REVOKED}（新 generation の ACCEPTED で置換されていない）（R5-12・v0.2.9 GA-04）")
    addT("同一 (site_id, cell_id)・異 cell_identity_hash（arms の列順のみ相違）の兄弟 profile を INCIDENT で SUSPENDED → 本 profile で CAS（v0.2.9） | 条件 12 の兄弟節（安定 id）で REJECTED・R_PROFILE_SUSPENDED（SIBLING_SUSPENDED）")
# --- GA-05: event の停止対象 = PROPOSED を透過した authority record
if gate("GA-05"):
    d.rep("再試行は `current.active_lease.acceptance_record_hash == trigger.acceptance_record_hash` の間続ける", "再試行は `current.active_lease.profile_hash == trigger.profile_hash ∧ current.active_lease.acceptance_record_hash == trigger.acceptance_record_hash` の間続ける")
    d.rep("`trigger.acceptance_record_hash` = supersede された ACCEPTED record の hash（= SUSPENDED record の `supersedes_record_hash`）ゆえ lease の束縛と等値比較できる。", "`trigger.acceptance_record_hash` = SUSPENDED record から `supersedes_record_hash` を辿って最初に到達する state == ACCEPTED の record の hash（PROPOSED を透過 = 停止対象の authority record・v0.2.9 GA-05: log の直前 record と現に効いている承認は別概念）ゆえ lease の束縛と等値比較できる。event はこの hash と SUSPENDED record 自身の hash の両方を運ぶ。")
    d.rep("manager は CAS 前に head-check (a) と同じ線形化読みで head.state を確認する）", "manager は CAS 前に head-check (a) と同じ線形化読みで head.state を確認する — head.state ∈ {SUSPENDED, REVOKED} なら本照合で無効化・head が新 generation の ACCEPTED なら event を捨てる・v0.2.9 GA-05）")
    d.rep("event は profile_hash + acceptance_record_hash を運ぶ）", "event は profile_hash + 停止対象 ACCEPTED record の hash（PROPOSED を透過・§3.5・v0.2.9 GA-05）+ SUSPENDED record 自身の hash を運ぶ）")
    d.rep("| T-46 | 旧 generation の SUSPENDED event を新 generation の lease 活性中に再送（v0.2.8） | acceptance_record_hash 不一致で無効化しない・head.state を線形化読みで確認 |", "| T-46 | 旧 generation の SUSPENDED event を新 generation の lease 活性中に再送（v0.2.8） | acceptance_record_hash 不一致で無効化しない・head.state を線形化読みで確認（head が新 generation の ACCEPTED = event を捨てる・v0.2.9 GA-05） |")
    addT("ACCEPTED(g) の lease 活性中に PROPOSED(g+1) を append した後 INCIDENT で SUSPENDED（v0.2.9） | event の停止対象 = 透過先の ACCEPTED(g)・即時 TRANSFER_TO_SAFEHOLD(SAFE_STOP)")
# --- GA-06: INV-02 / P5 / 証明 E を CasKind 別に
if gate("GA-06"):
    d.rep("| INV-02 | 全 CAS SUCCESS: `new.control_epoch == expected.control_epoch + 1 ∧ new.seq == expected.seq + 1` | 設計違反（test） |", "| INV-02 | CasKind 別（v0.2.9 GA-06）: TRANSFER_TO_EXECUTOR / TRANSFER_TO_SAFEHOLD の SUCCESS: `new.control_epoch == expected.control_epoch + 1 ∧ new.seq == expected.seq + 1`；MARK_BOUNDARY_WAIT の SUCCESS: `new.control_epoch == expected.control_epoch ∧ new.seq == expected.seq + 1 ∧ new.boundary_wait == True`；INV-30 の記録付き no-op は SUCCESS ではなく状態不変（CAS_ATTEMPT 記録のみ） | 設計違反（test） |")
    d.rep("`control_epoch` は CAS 成功ごとにちょうど +1。", "`control_epoch` は owner 遷移 CAS（TRANSFER の 2 kind）の成功ごとにちょうど +1（MARK_BOUNDARY_WAIT は epoch 不変・seq のみ +1・v0.2.9 GA-06）。")
    d.rep("と同じ int 領域。CAS 成功ごとに +1", "と同じ int 領域。TRANSFER 系 CAS 成功ごとに +1（MARK_BOUNDARY_WAIT は不変・GA-06）")
    d.rep("全ての CAS 成功は `control_epoch := expected.control_epoch + 1`（両 kind 共通）ゆえ epoch は成功列に沿って厳密増加。", "TRANSFER の 2 kind の CAS 成功は `control_epoch := expected.control_epoch + 1` ゆえ epoch は owner 遷移列に沿って厳密増加し、MARK_BOUNDARY_WAIT は epoch 不変・seq のみ +1 で単調性（epoch 非減少・seq 厳密増加）を壊さない（v0.2.9 GA-06）。")
    d.rep("| T-16 | ランダム interleaving（model check）: 全 trace で INV-01/02/03/10/11 |", "| T-16 | ランダム interleaving（model check）: 全 trace で INV-01/02（CasKind 別・v0.2.9）/03/10/11 |")
# --- GA-07: (l) の drift 判定を baseline の許容値 slot へ結線
if gate("GA-07"):
    d.rep("∧ wall / mono の drift が baseline diagnostic item の許容内 ∧", "∧ clock drift = `|(wall_now − wall_ref) − (mono_now − mono_ref)| ≤ baseline.clock_drift_tolerance_s`（基準対 (wall_ref, mono_ref) = 直前の PERMIT_ISSUED payload / 直前の CLOCK_DRIFT 診断で durable に記録した対・評価周期 = diagnostic_items の CLOCK_DRIFT 周期・許容値未解決 / 基準対欠落 = 偽・周期 / worst-case detection を許容値に読み替えない・v0.2.9 GA-07）∧")
if newT: d.insert_after_line("| T-48 |", "\n".join(newT))
rows05 = [("GA-01", "gateway 自身が出した (i′) SafeStop が manager 不読中に失われる", "§2 gateway 状態 `stop_latch`・§5.2 (i′)(iii)・INV-19 / INV-29・失敗表・§3.5・T"), ("GA-02", "certificate を SkillActionId だけで照合し SkillDefinitionHash に束縛していない", "§3.5 条件 6 / 8・§3.4 (n)・§4.1 lease・InitializationRecord・§6.2 B4・INV-14 / 15・失敗表・T"), ("GA-03", "開始検証後の待機で belief が失効しても CAS が通る", "§3.4 CommitPermit `start_belief_ref` / `belief_valid_until_mono`・条件 2 / 5・INV-35・失敗表・T"), ("GA-04", "兄弟停止の key が構成 hash で物理 cell を切れない", "§3.4 (i)・§3.5 条件 12・head-check (a)・T"), ("GA-05", "PROPOSED を挟むと event の停止対象を取り違える", "§3.5 再試行規則・§3.7 event 行・T-46・T"), ("GA-06", "MARK_BOUNDARY_WAIT が INV-02 / P5 / 証明 E と矛盾", "INV-02・§3.1 P5・§3.2 comment・§3.8 証明 E・T-16"), ("GA-07", "(l) の drift 許容値に入力経路が無い", "§3.4 (l)")]
tbl = [f"- **v0.2.9 fold（{NOW}）— 外部レビュー（GPT-astra GA-01..07・v0.2.8 対象 → Claude verifier V9・3 lens）の確定 finding の fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §12:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in rows05: tbl.append(f"| {i} | {c} | {s if conf(i) else '— 適用せず'} | {i}={vstr(i)} |")
tbl.append("| （06 側の fold 行は doc 06 §11） | | | |")
d.insert_before_line("## 14. Review anchors", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= 06
d = Doc("06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("DEPLOYMENT PROFILE SPEC (v0.2.8 REVIEW CANDIDATE)", "DEPLOYMENT PROFILE SPEC (v0.2.9 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.8（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.7 → v0.2.8 = round 5（R7 / R8 → V7 / V8）の確定 finding の fold（§11）。旧版の系譜:", "- status: **REVIEW CANDIDATE v0.2.9（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.8 → v0.2.9 = 外部レビュー（GPT-astra GA-01..07 → Claude verifier V9）の確定 finding の fold（§11）。旧版の系譜: — v0.2.7 → v0.2.8 = round 5（R7 / R8 → V7 / V8）の確定 finding の fold（§11）。旧版の系譜:")
d.rep("／ v0.2.8 = ", f"／ v0.2.9 = {NOW}（`date -u` 実測）／ v0.2.8 = ")
newPT = []; newOPP = []
def addPT(txt): newPT.append("| PT-%d | %s |" % (56 + len(newPT), txt))
def addOPP(txt): newOPP.append("| OPP-%d | %s |" % (18 + len(newOPP), txt))
# --- GA-04（06 側）: record に site_id / cell_id・batch 規則・custody
if gate("GA-04"):
    d.rep("    cell_identity_hash: str                # CellIdentity（layout_revision_ref・kinematic_layout を含む）の hash", "    cell_identity_hash: str                # CellIdentity（layout_revision_ref・kinematic_layout を含む）の hash（構成の等値検査用・R4-09）\n    site_id: str                           # v0.2.9（GA-04）: == profile.cell.site_id — 物理 cell の安定 id（兄弟停止の key。構成 hash ではない）\n    cell_id: str                           # v0.2.9（GA-04）: == profile.cell.cell_id（不一致 = P_ACCEPTANCE_RECORD_INVALID。manager は profile を解決せずに兄弟を列挙できる）")
    d.rep("`cell_identity_hash ≠ H_WCJ(profile.cell)`（R4-09）；", "`cell_identity_hash ≠ H_WCJ(profile.cell)`（R4-09）；`record.site_id ≠ profile.cell.site_id ∨ record.cell_id ≠ profile.cell.cell_id`（書込時・head 再評価・v0.2.9 GA-04）；")
    d.rep("cell 単位の trigger は同一 `cell_identity_hash` の全 record を停止する（R3-09）— 同一 append batch", "cell 単位の trigger は同一 `(site_id, cell_id)` の全 record を停止する（R3-09・v0.2.9 GA-04: 停止対象は物理 cell の安定 id で切り、構成 hash `cell_identity_hash` は構成等値検査（R4-09）に残す — 同 cell の別構成 profile（arms の列順・保守的 / 高速 envelope 等）にも伝わる）— 同一 append batch")
    d.rep("AuthorityManager は read-only consumer。", "AuthorityManager は read-only consumer。`(site_id, cell_id)` は baseline registry の head(cell_id) と同じ custody（OPP-16）の下で一意（改名 / 別名で未解消停止が消えないための規則 = OPP-18・v0.2.9 GA-04）。")
    addOPP("安定な物理 cell id `(site_id, cell_id)` の発行主体・一意性・改名 / 別名の custody 規則（改名で未解消の停止・incident が消えない保証）・cell 全体の停止と解除の管理主体（v0.2.9・GA-04・外部レビュー「Rs が決める事項 1」） | §8.3・05 §3.4 (i) / 条件 12 / head-check (a) | Rs 裁定待ち（暫定 = baseline registry と同じ custody で一意）")
    addPT("`record.cell_id ≠ profile.cell.cell_id` の ACCEPTED record を append（v0.2.9） | `P_ACCEPTANCE_RECORD_INVALID`（書込時）")
# --- GA-05（06 側）: PROPOSED を supersede する SUSPENDED の複写元と停止対象
if gate("GA-05"):
    d.rep("hash field と `valid_until` は superseded record から複写；", "hash field と `valid_until`・generation は superseded record から複写（PROPOSED を supersede する場合は透過先の ACCEPTED = authority head の値・v0.2.9 GA-05）；")
    d.rep("append 後は 05 head-check (a) → HOLD GENERATION_SUPERSEDED・v0.2.8 R7-02 / R8-05）;", "append 後は 05 head-check (a) → HOLD GENERATION_SUPERSEDED・v0.2.8 R7-02 / R8-05）; ACCEPTED(g) と PROPOSED(g+1) の並存中の SUSPENDED は log head = PROPOSED(g+1) を supersede しつつ、停止対象（05 event の acceptance_record_hash）= `supersedes_record_hash` を辿って最初に到達する ACCEPTED = authority head = ACCEPTED(g)（v0.2.9 GA-05）;")
# --- GA-07（06 側）: baseline に許容値 slot
if gate("GA-07"):
    d.rep("    base_pose_tolerance_rad: CanonicalDecimal    # v0.2.7（R6-07）: 同・回転許容 [rad]（BASE_POSE_VERIFY のみ・P_BASE_LAYOUT_MISMATCH は並進のみ・R8-03）", "    base_pose_tolerance_rad: CanonicalDecimal    # v0.2.7（R6-07）: 同・回転許容 [rad]（BASE_POSE_VERIFY のみ・P_BASE_LAYOUT_MISMATCH は並進のみ・R8-03）\n    clock_drift_tolerance_s: CanonicalDecimal    # v0.2.9（GA-07）: 05 §3.4 (l) の drift 判定 `|(wall_now − wall_ref) − (mono_now − mono_ref)|` の許容値 [s]（値 = RT0・本 doc に書かない）。周期 / worst-case detection とは別の量。解決不能 = P_BASELINE_INCOMPLETE")
    d.rep("| acceptance record が指す `CellSafetyTimingBaseline.diagnostic_items` ⊇ REQUIRED_DIAGNOSTIC_ITEMS（§8.3・record 書込時 + 第 2 評価点）（v0.2.7・R6-08） | `P_BASELINE_INCOMPLETE` |", "| acceptance record が指す `CellSafetyTimingBaseline.diagnostic_items` ⊇ REQUIRED_DIAGNOSTIC_ITEMS（§8.3・record 書込時 + 第 2 評価点）（v0.2.7・R6-08）、かつ `clock_drift_tolerance_s` が解決できる（CLOCK_DRIFT 項目の許容値・v0.2.9 GA-07） | `P_BASELINE_INCOMPLETE` |")
    old = d.line("| OPP-16 |"); d.repline("| OPP-16 |", old.replace(" | §8.3・05 OP-20 | RT0 へ carry |", "、`clock_drift_tolerance_s` の値と時計対応の前提（wall 源の同期方式・v0.2.9 GA-07） | §8.3・05 OP-20 | RT0 へ carry |"))
    addPT("`clock_drift_tolerance_s` を持たない baseline を指す acceptance record（v0.2.9） | `P_BASELINE_INCOMPLETE`（record 拒否）；05 (l) は許容値未解決 = 偽 = R_CLOCK_ANOMALY")
if newOPP: d.insert_after_line("| OPP-17 |", "\n".join(newOPP))
if newPT: d.insert_after_line("| PT-55 |", "\n".join(newPT))
rows06 = [("GA-04", "兄弟停止の key（record の site_id / cell_id・batch 規則・custody）", "§8.3 ProfileAcceptanceRecord・P_ACCEPTANCE_RECORD_INVALID・失効の権限・所在・OPP-18・PT"), ("GA-05", "PROPOSED を supersede する SUSPENDED の複写元と停止対象", "§8.3 SUSPENDED 規則・状態遷移"), ("GA-07", "baseline に drift 許容値の slot が無い", "§8.3 `clock_drift_tolerance_s`・§3 P_BASELINE_INCOMPLETE・OPP-16・PT")]
tbl = [f"- **v0.2.9 fold（{NOW}）— 外部レビュー（GPT-astra GA-01..07 → V9）の確定 finding の fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §12:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in rows06: tbl.append(f"| {i} | {c} | {s if conf(i) else '— 適用せず'} | {i}={vstr(i)} |")
tbl.append("| GA-01 / GA-02 / GA-03 / GA-06 | 05 側のみ | doc 05 §13 | " + "; ".join(f"{x}={vstr(x)}" for x in ("GA-01", "GA-02", "GA-03", "GA-06")) + " |")
d.insert_before_line("## 12. Review anchors", "\n".join(tbl) + "\n")
d.save()

for name in ("07_SUCCESSOR_CONTRACT_DECISION_20260903.md", "04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md", "08_INDEPENDENT_REVIEW_PLAN_20260903.md"):
    d = Doc(name); d.rep("(v0.2.8 REVIEW CANDIDATE)", "(v0.2.9 REVIEW CANDIDATE)"); d.rep("REVIEW CANDIDATE v0.2.8（", "REVIEW CANDIDATE v0.2.9（"); d.save()
print("applied:", applied); print("NOW =", NOW)
