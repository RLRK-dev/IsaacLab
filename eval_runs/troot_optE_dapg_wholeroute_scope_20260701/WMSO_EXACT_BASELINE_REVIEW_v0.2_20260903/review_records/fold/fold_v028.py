#!/usr/bin/env python3
"""v0.2.7 -> v0.2.8 fold (round 5: R7/R8 findings gated by verifier V7/V8 verdicts). Records-only; frozen files untouched.
Usage: python3 fold_v028.py <PKG_DIR> <verdicts_v028.json>   verdicts = {id: {"confirmed": bool, "severity": str, "merged_into": str}}"""
import sys, json, re, subprocess, os
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
HC = "| any (EXECUTOR) | **manager 側 head-check**"   # head-check row prefix (v0.2.7)
def hc_edit(old, new):
    row = d.line(HC if d.t.count("\n" + HC) else "| any（SAFEHOLD 中も周期実行"); assert old in row, old[:60]; d.repline(row[:40], row.replace(old, new))

# ======================================================================= 05
d = Doc("05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("RUNTIME SPEC (v0.2.7 REVIEW CANDIDATE)", "RUNTIME SPEC (v0.2.8 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.7（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.6 → v0.2.7 = v0.2.6 本文への再レビュー round 4（R5 / R6 → V5 / V6）の確定 finding の fold（§13）。旧版の系譜:", "- status: **REVIEW CANDIDATE v0.2.8（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.7 → v0.2.8 = v0.2.7 本文への再レビュー round 5（R7 / R8 → V7 / V8）の確定 finding の fold（§13）。旧版の系譜: — v0.2.6 → v0.2.7 = v0.2.6 本文への再レビュー round 4（R5 / R6 → V5 / V6）の確定 finding の fold（§13）。旧版の系譜:")
d.rep("**round 4（R5 / R6 → V5 / V6）の fold = 本版 v0.2.7（§13）**", "round 4（R5 / R6 → V5 / V6）の fold = v0.2.7（2026-09-05 23:32 UTC）→ **round 5（R7 / R8 → V7 / V8）の fold = 本版 v0.2.8（§13）**")

# --- R7-01 / R8-20: head-check は owner を問わず周期実行・(m) は SAFEHOLD からも評価可能
if gate("R7-01", "R8-20"):
    row = d.line(HC); d.repline(HC, row.replace("| any (EXECUTOR) | **manager 側 head-check**（", "| any（SAFEHOLD 中も周期実行: lease を要する副場合 (a)(e)(f) は N/A = True（WAIT の N/A と同じ規約）・(b)(c)(d) のみ評価し、発火は INV-30 の reason 強化 / 記録付き no-op・v0.2.8 R7-01 / R8-20） | **manager 側 head-check**（", 1))
    d.rep("∧ 直近の head-check が周期内に成功。違反 = `R_REGISTRY_UNAVAILABLE`", "∧ 直近の head-check が周期内に成功。**SAFEHOLD 中の評価可能性（v0.2.8 R7-01 / R8-20）**: manager は owner を問わず head-check と非 identity 項目（VALIDITY_MONITOR_LIVENESS / AUDIT_RECORDER_LIVENESS / CLOCK_DRIFT / REGISTRY_HEAD_CHECK）を周期実行し、identity 系 check_id は (a) の BEFORE_PERMIT 実行を当該周期の結果として数える；permit 発行時の同期 head-check で「直近の head-check」を満たしてよい（INITIAL からの初回 permit が deadlock しない）。違反 = `R_REGISTRY_UNAVAILABLE`")
# --- R7-02 / R8-05: head の定義から PROPOSED を除く
if gate("R7-02", "R8-05"):
    d.rep("`permit.profile_hash` の head record（= registry append seq 最大・fork は registry が拒否）", "`permit.profile_hash` の **authority head** record（= state ∈ {ACCEPTED, SUSPENDED, REVOKED} の record のうち registry append seq 最大。PROPOSED は authority を持たず含まない・v0.2.8 R7-02 / R8-05。fork 検出用の seq 最大 head は doc 06 §8.3・fork は registry が拒否）")
    d.rep("registry の線形化読みで `permit.profile_hash` の head record が", "registry の線形化読みで `permit.profile_hash` の authority head record（§3.4 (i) の定義・PROPOSED を除く）が")
    hc_edit("(a) `head(registry, lease.profile_hash)` の", "(a) `head(registry, lease.profile_hash)`（authority head・PROPOSED を除く・§3.4 (i)・R7-02）の")
# --- R7-03 / R8-15: role registry の supersession を monitor 入力 + head-check (f) に
if gate("R7-03", "R8-15"):
    d.rep("layout と baseline registry（定義 = doc 06 §8.3・cell_id ごとに 1 head・v0.2.7 R6-10）の supersession", "layout と baseline registry（定義 = doc 06 §8.3・cell_id ごとに 1 head・v0.2.7 R6-10）・role registry（doc 06 §8.3・1 head・v0.2.8 R7-03 / R8-15）の supersession")
    hc_edit("(e) cell_id の baseline registry head ≠ `record.timing_baseline_hash`（R6-10） |", "(e) cell_id の baseline registry head ≠ `record.timing_baseline_hash`（R6-10）; (f) role registry の head ≠ `record.role_registry_hash`（v0.2.8 R7-03 / R8-15） |")
    hc_edit("; (e) = BASELINE_SUPERSEDED 行（HOLD）。", "; (e) = BASELINE_SUPERSEDED 行（HOLD）; (f) = ROLE_REGISTRY_SUPERSEDED 行（HOLD）。")
    hc_edit("; (e) R_PROFILE_SUSPENDED（BASELINE_SUPERSEDED）, DISPOSITION |", "; (e) R_PROFILE_SUSPENDED（trigger = HEAD_CHECK・sub = BASELINE_SUPERSEDED）; (f) R_PROFILE_SUSPENDED（HEAD_CHECK・sub = ROLE_REGISTRY_SUPERSEDED）, DISPOSITION |")
elif gate("R7-09"):
    hc_edit("; (e) R_PROFILE_SUSPENDED（BASELINE_SUPERSEDED）, DISPOSITION |", "; (e) R_PROFILE_SUSPENDED（trigger = HEAD_CHECK・sub = BASELINE_SUPERSEDED）, DISPOSITION |")
# --- R7-04 / R7-18: gateway 局所 last_disposition・R_MANAGER_UNAVAILABLE 行の実態化
if gate("R7-04"):
    d.rep("線形化読み（cache を持たない）+ 直近 admitted command + `restart_pending` flag |", "線形化読み（cache を持たない）+ 直近 admitted command + `restart_pending` flag + `last_disposition`（直近に成功した線形化読みで観測した `safehold_disposition`・v0.2.8 R7-04） |")
    d.rep("(iii) else SafeHold（`state.safehold_disposition == SAFE_STOP` なら SafeStop — 線形化読み・v0.2.4 R1-03。", "(iii) else SafeHold（`state.safehold_disposition == SAFE_STOP` なら SafeStop — 線形化読み・v0.2.4 R1-03。線形化読みが `manager_liveness_s` 内に完了しない場合は gateway 局所の `last_disposition == SAFE_STOP` なら SafeStop・それ以外 SafeHold（起動直後 = SafeHold・INV-25・v0.2.8 R7-04: manager 不読で SafeStop が SafeHold に緩まない）。")
    d.rep("読みが `manager_liveness_s` 内に完了しないとき (ii) を評価しない（v0.2.2・B-H1） | R_MANAGER_UNAVAILABLE |", "読みが `manager_liveness_s` 内に完了しないとき (ii) を評価しない。その間の (iii) の SafeStop / SafeHold は gateway 局所 `last_disposition` で決める（v0.2.2・B-H1・v0.2.8 R7-04） | R_MANAGER_UNAVAILABLE |")
    d.rep("読みが `manager_liveness_s` 内に完了しない場合、(ii) を評価せず (iii) に落ちる（INV-19）。", "読みが `manager_liveness_s` 内に完了しない場合、(ii) を評価せず (iii) に落ちる（INV-19・SafeStop / SafeHold は `last_disposition`・R7-04）。")
if gate("R7-04", "R7-18"):
    d.repline("| gateway が `manager_liveness_s` 内に AuthorityState を読めない", "| gateway が `manager_liveness_s` 内に AuthorityState を読めない（v0.2.1・B-10） | CommandGateway | `R_MANAGER_UNAVAILABLE` | 出力 = (iii)" + ("（`last_disposition` を保持: SAFE_STOP なら SafeStop・R7-04）" if conf("R7-04") else " SafeHold") + "・lease は形式上継続・gateway は outage を manager へ報告し COMMAND_REJECTED(R_MANAGER_UNAVAILABLE) を記録 | " + ("読みが `command_deadline_s` 内に回復すれば (ii) を再開（CAS なし）；超過は `R_DEADLINE_MISS` 行（`pending_invalidate` 経由）。manager 自身の再起動は R_MANAGER_RESTART 行（v0.2.8 R7-18: 旧「復帰時に MANAGER_RESTART と同じ経路」は link 断では実現されないため撤回）" if conf("R7-18") else "manager 復帰時に TRANSFER_TO_SAFEHOLD(MANAGER_RESTART) と同じ経路で `HOLD`") + " |")
# --- R7-05: arm_targets ⊆ lease.ownership.control
if gate("R7-05"):
    d.rep("∧ `AcceptedEnvelope` 連言 ∧ command 種別 = lease.control_mode ∧ `cmd_seq` 単調。既定出力", "∧ `∀ (r, _) ∈ cmd.arm_targets: lease.ownership.control[r] == True`（未知の r / False = 束縛不一致 → `R_LEASE_UNKNOWN_COMMAND`・executor_id 不一致と同じ class・v0.2.8 R7-05）∧ `AcceptedEnvelope` 連言 ∧ command 種別 = lease.control_mode ∧ `cmd_seq` 単調。既定出力")
    d.rep("`cmd.cmd_seq` は lease 内で厳密単調（v0.2.2） | R_EPOCH_STALE_COMMAND / R_LEASE_UNKNOWN_COMMAND / R_TIMING_VIOLATION |", "`cmd.cmd_seq` は lease 内で厳密単調（v0.2.2）、`∀ (r, _) ∈ cmd.arm_targets: lease.ownership.control[r] == True`（不一致 = `R_LEASE_UNKNOWN_COMMAND`・v0.2.8 R7-05） | R_EPOCH_STALE_COMMAND / R_LEASE_UNKNOWN_COMMAND / R_TIMING_VIOLATION |")
    d.rep("gateway はそれを線形化 snapshot で確認する\n", "gateway はそれを線形化 snapshot で確認する。gripper 資源（gripper_left / gripper_right）への command は本 GatewayCommand の外（OP-22・v0.2.8 R7-05）\n")
    d.rep("| lease_id 不明の command・または `cmd.executor_id ≠ lease.executor_id`（v0.2.1・B-10・v0.2.6 R3-19） | CommandGateway | `R_LEASE_UNKNOWN_COMMAND` |", "| lease_id 不明の command・または `cmd.executor_id ≠ lease.executor_id`・または cmd が `lease.ownership.control` に無い resource を `arm_targets` で提案（v0.2.1・B-10・v0.2.6 R3-19・v0.2.8 R7-05） | CommandGateway | `R_LEASE_UNKNOWN_COMMAND` |")
    d.insert_after_line("| OP-16 |", "| OP-22 | gripper 資源（gripper_left / gripper_right）への command 経路。v0.2 の `GatewayCommand.arm_targets` は ee_* のみを運び、gripper は `lease.ownership.control` の資源としてのみ現れる（v0.2.8・R7-05） | doc 06 §2.1 `ArmSpec.gripper_resource_id` | 別 command 種別 or `arm_targets` の拡張 = 後継版で定義・未 |")
# --- R7-08: 残る境界（INV-35 / INV-07 / (k)）
if gate("R7-08"):
    d.rep("同一 generation であり decision age ≤ decision_max_age_s（条件 6・12）", "同一 generation であり decision age < decision_max_age_s（厳密境界・条件 6・12・v0.2.8 R7-08）")
    d.rep("∧ ack.valid_until ≥ permit.issued_at ∧", "∧ ack.valid_until > permit.issued_at（v0.2.8 R7-08）∧")
    d.rep("(k) `validity_deadline_mono` と `effective_expires_at` を発行時に導出して permit に固定（v0.2.5・OPP-11 / OP-19）", "(k) `validity_deadline_mono` と `effective_expires_at` を発行時に導出して permit に固定（v0.2.5・OPP-11 / OP-19。`effective_expires_at > issued_at` でなければ permit を発行しない — 到達項の code は条件 2 の優先規則・v0.2.8 R7-08）")
# --- R7-09: sub 語彙の SSOT 化
if gate("R7-09"):
    subs = "SUSPENDED | REVOKED | GENERATION_SUPERSEDED | SIBLING_SUSPENDED | SIBLING_REVOKED | BASELINE_SUPERSEDED" + (" | ROLE_REGISTRY_SUPERSEDED" if conf("R7-03") or conf("R8-15") else "")
    d.rep("`R_AUDIT_UNAVAILABLE`: RECORDER_LIVENESS（trigger 語彙の SSOT = 本列挙。", "`R_AUDIT_UNAVAILABLE`: RECORDER_LIVENESS。`R_PROFILE_SUSPENDED` の payload `sub` 語彙 = " + subs + "；`DIAGNOSTIC:<item>` の <item> ∈ REQUIRED_DIAGNOSTIC_ITEMS ∪ baseline.diagnostic_items の項目名（v0.2.8 R7-09）（trigger / sub 語彙の SSOT = 本列挙。")
    hc_edit("sub = SUSPENDED \\| REVOKED \\| GENERATION_SUPERSEDED \\| SIBLING_SUSPENDED", "sub = SUSPENDED \\| REVOKED \\| GENERATION_SUPERSEDED \\| SIBLING_SUSPENDED \\| SIBLING_REVOKED")
# --- R7-10: (i) の再評価から role_registry_hash 節を除く・registry 不読は TRANSFER_TO_SAFEHOLD を止めない
if gate("R7-10"):
    d.rep("P_ACCEPTANCE_RECORD_INVALID == 0 を head で再評価（role 充足・operator 相異）", "P_ACCEPTANCE_RECORD_INVALID == 0 を head で再評価（role 充足・operator 相異。`role_registry_hash` 節は本 (i) の現 head 照合 → `R_PROFILE_SUSPENDED` が担い、再評価から除く・v0.2.8 R7-10）")
    d.rep("起動時 / permit 発行 / CAS では拒否（診断用 SAFEHOLD での起動は可・新規 actuation なし）", "起動時 / permit 発行 / TRANSFER_TO_EXECUTOR の CAS では拒否（TRANSFER_TO_SAFEHOLD は registry 非依存・条件 1 のみ・v0.2.8 R7-10。診断用 SAFEHOLD での起動は可・新規 actuation なし）")
    d.rep("**TRANSFER_TO_SAFEHOLD** の前提条件 = 条件 1 のみ（+ `safehold_reason` 非 null）。", "**TRANSFER_TO_SAFEHOLD** の前提条件 = 条件 1 のみ（+ `safehold_reason` 非 null・registry / role registry / baseline registry の読みを要さない = 不読でも安全側へ遷移できる・v0.2.8 R7-10）。")
    d.rep("| 診断用 SAFEHOLD で起動可・permit / CAS / actuation 全面拒否・R_REGISTRY_UNAVAILABLE |", "| 診断用 SAFEHOLD で起動可・permit / TRANSFER_TO_EXECUTOR / actuation 全面拒否（TRANSFER_TO_SAFEHOLD は可・v0.2.8 R7-10）・R_REGISTRY_UNAVAILABLE |")
# --- R7-11: profile-scoped 再試行の述語を acceptance_record_hash に
if gate("R7-11"):
    d.rep("再試行は `current.active_lease.profile_hash == trigger.profile_hash` の間続ける（別 lease に切り替わっても同じ profile なら無効化する — SUSPENDED profile 上の新 lease が走り続けない）", "再試行は `current.active_lease.acceptance_record_hash == trigger.acceptance_record_hash` の間続ける（別 lease に切り替わっても同じ record なら無効化する — SUSPENDED record 上の新 lease が走り続けない。`trigger.acceptance_record_hash` = supersede された ACCEPTED record の hash（= SUSPENDED record の `supersedes_record_hash`）ゆえ lease の束縛と等値比較できる。v0.2.8 R7-11: profile_hash だけでは新 generation の有効な lease を遅延 / 再送 event が巻き込むため、manager は CAS 前に head-check (a) と同じ線形化読みで head.state を確認する）")
# --- R7-12: 同 tier no-op で記録した clearance 和集合の消費
if gate("R7-12"):
    d.rep("該当する clearance record（§5.4 — 集合は §5.4 と同一定義・v0.2.2・A2-01 / B2-07）が存在する。", "該当する clearance record（§5.4 — 集合は §5.4 と同一定義・v0.2.2・A2-01 / B2-07）が、当該 SAFEHOLD 期間中に記録された要求 clearance の和集合（同 tier / 同 reason の no-op 遷移で CAS_ATTEMPT payload に記録・manager の durable 台帳・CAS tuple 外）の**全 reason について**存在する（和集合は TRANSFER_TO_EXECUTOR で reset・v0.2.8 R7-12: 吸収された tier-2 reason の clearance も消費する）。")
    d.rep("= `record.safehold_reason == current.safehold_reason ∧ record.role", "= `record.safehold_reason ∈ 当該 SAFEHOLD 期間の要求 clearance 和集合（current.safehold_reason を含む・v0.2.8 R7-12）∧ record.role")
# --- R7-13: (l) の基準を durable store に
if gate("R7-13"):
    d.rep("`wall_now` が直前の PERMIT_ISSUED の wall より単調。", "`wall_now` が manager の durable store に保持する `last_permit_wall`（PERMIT_ISSUED と同一 commit で更新・audit 読出しに依存しない・recorder 停止は (l) ではなく (m) の R_REGISTRY_UNAVAILABLE（DIAGNOSTIC:AUDIT_RECORDER_LIVENESS）/ R_AUDIT_UNAVAILABLE が扱う・v0.2.8 R7-13）より単調。")
# --- R7-14: genesis record の資格照合・profile_hash は provenance
if gate("R7-14"):
    d.rep("・role = doc 06 `clearance_roles[GENESIS]`）を書き", "・role = doc 06 `clearance_roles[GENESIS]`・`role_registry_hash` = role registry の現 head ∧ (operator_ref, GENESIS) ∈ registry（§5.4 と同じ資格照合・v0.2.8 R7-14）。genesis の `profile_hash` は provenance（その clearance 手続の下で genesis が書かれた profile の記録）であり permit / CAS の条件ではない — cell は複数 profile を走らせ得る（OPP-8・PT-14）ため genesis に cell を束縛しない（R7-14））を書き")
# --- R7-15 / R8-01: baseline registry head の照合を (i)・条件 12 に
if gate("R7-15", "R8-01"):
    d.rep("`record.role_registry_hash` == doc 06 §8.3 role registry の現 head（不一致 = `R_PROFILE_SUSPENDED`・v0.2.7 R6-05））", "`record.role_registry_hash` == doc 06 §8.3 role registry の現 head（不一致 = `R_PROFILE_SUSPENDED`・v0.2.7 R6-05）；`record.timing_baseline_hash` == doc 06 §8.3 baseline registry の head(cell_id)（不一致 = `R_PROFILE_SUSPENDED`・trigger PERMIT | CAS_COND12・sub BASELINE_SUPERSEDED・v0.2.8 R7-15 / R8-01））")
    d.rep(" ∧ record.role_registry_hash == role registry の現 head（R6-05）`", " ∧ record.role_registry_hash == role registry の現 head（R6-05）∧ record.timing_baseline_hash == baseline registry の head(cell_id)（R7-15 / R8-01）`")
# --- R8-02 (c) / R8-22（05 側）
if gate("R8-02"):
    d.rep("deployment 側の失効 event（incident・tool 交換・firmware 更新", "deployment 側の失効 event（incident・tool 個体（serial）の変更・firmware 更新")
if gate("R8-22"):
    d.rep("（v0.2.7 R6-06: role label の自己申告では解除できない。資格照合不能 = 該当 record 無し）", "（v0.2.7 R6-06: role label だけでは解除できない。記録者の真正性（記録者 = 名指された operator）は OP-5 / U14 の署名方式に依存し本 doc は主張しない・v0.2.8 R8-22。資格照合不能 = 該当 record 無し）")
# --- R8-23（05 側）: DEPLOYMENT_WORKSPACE を arm ごとに評価
if gate("R8-23"):
    d.rep("hold は時間 parameterization のみを変える。tool 形状は評価しない（doc 06 §4・OPP-14・v0.2.3 CD-18）。", "hold は時間 parameterization のみを変える。command の `arm_targets` の各 entry（各 arm）の線分ごとに全 zone に対して評価し、いずれかの arm が FALSE なら term は FALSE（v0.2.8 R8-23）。tool 形状は評価しない（doc 06 §4・OPP-14・v0.2.3 CD-18）。")
# --- tests
newT = []
def addT(txt): newT.append("| T-%d | %s |" % (43 + len(newT), txt))
if any_conf("R7-01", "R8-20"): addT("INITIAL（genesis 直後）から最初の permit 要求（v0.2.8） | (m) は同期 head-check + BEFORE_PERMIT 実行で評価可能・permit 発行（deadlock しない）")
if conf("R7-04"): addT("SAFE_STOP disposition の SAFEHOLD 中に manager との link 断（v0.2.8） | 出力は SafeStop のまま（`last_disposition`）・SafeHold へ緩まない")
if conf("R7-05"): addT("ee_left のみ offered の lease から ee_right を含む arm_targets の command（v0.2.8） | ownership 節不成立・R_LEASE_UNKNOWN_COMMAND・拒否のみ（audit）")
if conf("R7-11"): addT("旧 generation の SUSPENDED event を新 generation の lease 活性中に再送（v0.2.8） | acceptance_record_hash 不一致で無効化しない・head.state を線形化読みで確認")
if conf("R7-12"): addT("CHECKPOINT_DISABLED の SAFEHOLD 中に GATEWAY_RESTART（同 tier no-op）→ GATEWAY_RESTART の clearance だけで CAS（v0.2.8） | 条件 10 不成立（和集合の CHECKPOINT_DISABLED clearance が欠ける）・R_PERMIT_MISBOUND")
if any_conf("R7-15", "R8-01"): addT("baseline registry の head を進めた後、旧 baseline を指す ACCEPTED record で permit 要求（v0.2.8） | (i) の baseline head 照合で R_PROFILE_SUSPENDED（sub BASELINE_SUPERSEDED）・permit 不発行")
if newT: d.insert_after_line("| T-42 |", "\n".join(newT))
rows05 = [("R7-01 / R8-20", "(m) が SAFEHOLD から評価不能（permit deadlock）", "§3.7 head-check 行 from・§3.4 (m)・T"), ("R7-02 / R8-05", "head の定義に PROPOSED が入る", "§3.4 (i)・§3.5 条件 12・head-check (a)"), ("R7-03 / R8-15", "role registry の supersession 検出器が無い", "§2 monitor 行・head-check (f)"), ("R7-04", "manager 不読で SafeStop が SafeHold に緩む", "§2 gateway 状態・§5.2 (iii)・INV-19・失敗表"), ("R7-18", "R_MANAGER_UNAVAILABLE 行が実現されない", "失敗表"), ("R7-05", "arm_targets ⊆ ownership が検査されない", "§2 admission・INV-03・§4.4 arm_targets・OP-22"), ("R7-08", "INV-35 / INV-07 / (k) の境界", "§9・§3.4 (k)"), ("R7-09", "sub 語彙が SSOT に無い", "§8 記録義務・head-check 行"), ("R7-10", "1 条件 2 code・registry 不読と TRANSFER_TO_SAFEHOLD", "§3.4 (i)・失敗表・T-36"), ("R7-11", "profile-scoped 再試行が新 generation を巻き込む", "§3.5 再試行規則"), ("R7-12", "同 tier no-op の clearance 和集合が消費されない", "§3.5 条件 10・§5.4"), ("R7-13", "(l) が audit 読出しに依存", "§3.4 (l)"), ("R7-14", "genesis の role が自己申告・profile_hash が未検査", "§3.2 genesis"), ("R7-15 / R8-01", "baseline registry head が (i) / 条件 12 に無い", "§3.4 (i)・§3.5 条件 12・T"), ("R8-02", "tool 交換の語（05 側）", "§2 monitor 行"), ("R8-22", "clearance の真正性の過大主張（05 側）", "§5.4"), ("R8-23", "DEPLOYMENT_WORKSPACE の arm ごとの評価（05 側）", "§4.3"), ("R7-16", "checker Q2 が除外節の言及を数える", "`check_review_candidate.py` Q2"), ("R7-17", "anchor 23 の C2 WARN 数", "§14 anchor 23")]
tbl = [f"- **v0.2.8 fold（{NOW}）— round 5（reviewer R7 / R8・v0.2.7 対象 → verifier V7 / V8・3 lens）の確定 finding の fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §11:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in rows05: tbl.append(f"| {i} | {c} | {s if any_conf(*i.split(' / ')) else '— 適用せず'} | {'; '.join(f'{x}={vstr(x)}' for x in i.split(' / '))} |")
tbl.append("| （06 側の fold 行は doc 06 §11） | | | |")
d.insert_before_line("## 14. Review anchors", "\n".join(tbl) + "\n")
if gate("R7-17"):
    d.rep("23. 機械検査（`check_review_candidate.py --runtime`）= FAIL 0。残る C2 WARN（6 件）は heuristic で、いずれも「引用行が別の規範（TERMINAL のみ / 型定義）を担い、同じ文に並ぶ識別子はその帰結として本 doc が導入したもの」— slice prereg `:59` を `InterruptOutcome` の処置の根拠として引く行（§6.1・§6.2・OP-11・anchor 17）と、frozen `:151` を `FreshnessPolicy.max_staleness_s = None` の型根拠として引く行（§4.2）。引用先の内容は sed で再確認済み。", "23. 機械検査（`check_review_candidate.py --runtime`）= FAIL 0。残る C2 WARN（{{C2WARN}} 件・v0.2.8 時点の実測 = 11_ §11.1）は heuristic で、(a)「引用行が別の規範（TERMINAL のみ / 型定義）を担い、同じ文に並ぶ識別子はその帰結として本 doc が導入したもの」— slice prereg `:59` を `InterruptOutcome` の処置の根拠として引く行（§6.1・§6.2・OP-11・anchor 17）と、frozen `:151` を `FreshnessPolicy.max_staleness_s = None` の型根拠として引く行（§4.2）、(b) D0 `:318` / `:354`・contracts_v2 `:323` / `:570`・D11B `:255` を散文の根拠として引き、同じ行に本 doc の新語（monitor / permit 前提条件 / decision age / rate 等）を並べた行（§2 表・§3.4 (e)・§3.5 条件 6・§4.2・§4.3）（v0.2.8 R7-17 で件数と分類を再計上）。引用先の内容は sed で再確認済み。")
d.save()

# ======================================================================= 06
d = Doc("06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("DEPLOYMENT PROFILE SPEC (v0.2.7 REVIEW CANDIDATE)", "DEPLOYMENT PROFILE SPEC (v0.2.8 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.7（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.6 → v0.2.7 = round 4（R5 / R6 → V5 / V6）の確定 finding の fold（§11）。旧版の系譜:", "- status: **REVIEW CANDIDATE v0.2.8（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.7 → v0.2.8 = round 5（R7 / R8 → V7 / V8）の確定 finding の fold（§11）。旧版の系譜: — v0.2.6 → v0.2.7 = round 4（R5 / R6 → V5 / V6）の確定 finding の fold（§11）。旧版の系譜:")
newP = []; newPT = []; newOPP = []
def addPT(txt): newPT.append("| PT-%d | %s |" % (49 + len(newPT), txt))
def addOPP(txt): newOPP.append("| OPP-%d | %s |" % (18 + len(newOPP), txt))
second_anchor = "} — 05 §3.4 (b) が `R_PROFILE_MISBOUND`"
def add_second(item): d.rep(second_anchor, ", " + item + second_anchor)
# --- R7-17: header timestamps
if gate("R7-17"):
    d.rep("／ v0.2.6 = 2026-09-05 02:15 UTC（`date -u` 実測）／ v0.2.5", f"／ v0.2.8 = {NOW}（`date -u` 実測）／ v0.2.7 = 2026-09-05 23:32 UTC（`date -u` 実測）／ v0.2.6 = 2026-09-05 02:15 UTC（`date -u` 実測）／ v0.2.5")
# --- R7-01 / R8-20（06 側）
if gate("R7-01", "R8-20"):
    d.rep("identity 系 4 項目 = `health_checks[]` の同 kind の check_id を lease 中に周期再実行（結果は (m) と head-check が参照）", "identity 系 4 項目 = `health_checks[]` の同 kind の check_id を lease 中および SAFEHOLD 中（BEFORE_PERMIT 実行を当該周期の結果として数える・v0.2.8 R7-01 / R8-20）に周期再実行（結果は (m) と head-check が参照）")
    d.rep("は baseline diagnostic item として lease 中も周期再検証する", "は baseline diagnostic item として lease 中も（SAFEHOLD 中は BEFORE_PERMIT 実行で）周期再検証する（v0.2.8 R7-01）")
# --- R7-02 / R8-05: head の定義・PROPOSED の検査
if gate("R7-02", "R8-05"):
    d.rep("head = registry append seq 最大；同一 record を 2 度 supersede する append は registry が拒否（fork なし）。", "head = registry append seq 最大（fork 検出・`supersedes_record_hash` の照合用）；**authority head**（05 §3.4 (i) / 条件 12 / head-check (a) が参照）= state ∈ {ACCEPTED, SUSPENDED, REVOKED} の record のうち seq 最大（PROPOSED は authority を持たず含まない・v0.2.8 R7-02 / R8-05）；同一 record を 2 度 supersede する append は registry が拒否（fork なし）。")
    d.rep("PROPOSED（登録 = 第 1 評価点の文脈・`timing_baseline_hash` を運ぶ・R6-09）→ ACCEPTED（受理）;", "PROPOSED（登録 = 第 1 評価点の文脈・`timing_baseline_hash` を運ぶ・R6-09）→ ACCEPTED（受理・同一 generation）; ACCEPTED → PROPOSED(gen+1)（再登録の第 1 評価点文脈）→ ACCEPTED(gen+1)（PROPOSED(gen+1) は authority head を変えず、活性 lease は ACCEPTED(gen+1) が append されるまで ACCEPTED(gen) に束縛されたまま — append 後は 05 head-check (a) → HOLD GENERATION_SUPERSEDED・v0.2.8 R7-02 / R8-05）;")
    d.rep("**state ∈ {PROPOSED, ACCEPTED} の record について**（v0.2.7 R6-04）: generation が同一 profile_hash の直前 ACCEPTED / PROPOSED record + 1 でない；", "**state ∈ {PROPOSED, ACCEPTED} の record について**（v0.2.7 R6-04・v0.2.8 R8-05 で定義を 1 つに）: generation の規則に反する（PROPOSED = 直前 ACCEPTED の generation + 1・同一登録の ACCEPTED = その PROPOSED と同一 generation・PROPOSED を経ない ACCEPTED(gen+1) = 直前 ACCEPTED + 1 —「+1」は generation 間の規則）；PROPOSED はさらに `timing_baseline_hash` が解決不能・`allowed_lease_modes = ()`・approvals に role_registry で資格ある COMMISSIONING が無い、のいずれかで違反（registry ACL は OPP-13）；")
    d.rep("（PROPOSED record の `P_ACCEPTANCE_RECORD_INVALID` = 必須 field + baseline 解決可能・v0.2.7 R6-09）", "（PROPOSED record の `P_ACCEPTANCE_RECORD_INVALID` = §8.3 の state ∈ {PROPOSED, ACCEPTED} 節 + `timing_baseline_hash` 解決可能 — 定義は §8.3 の 1 箇所・v0.2.7 R6-09・v0.2.8 R8-05）")
    addPT("活性 lease 中に PROPOSED(gen+1) を append（v0.2.8） | authority head 不変（PROPOSED は runtime head にならない）・lease 無影響・permit 判定は非 PROPOSED head")
# --- R7-03 / R8-15（06 側）
if gate("R7-03", "R8-15"):
    d.rep("head の変更 = supersession: 認可された一者または monitor が bound する全 ACCEPTED record に `SUSPENDED(ROLE_REGISTRY_SUPERSEDED)` を append（→ HOLD・再受理は新 generation）。", "head の変更 = supersession: head を変える custodian は**同一 append batch**（原子・R5-12 と同形）で bound する全 ACCEPTED record に `SUSPENDED(ROLE_REGISTRY_SUPERSEDED)` を append する義務を負う（→ HOLD・再受理は新 generation）；monitor は event を出し、manager は 05 head-check (f) で monitor 非依存に検出する（baseline registry の (e) と同形・v0.2.8 R7-03 / R8-15）。")
# --- R7-06 / R8-07: CalibrationRef.measured_at_iso8601・上限の key
if gate("R7-06", "R8-07"):
    row = d.line("| `CalibrationRef.valid_until_iso8601`、および required record のうち kind ∈ {")
    kinds = row[row.find("kind ∈ {"):row.find("} の `valid_until_iso8601`") + 1]
    d.repline("| `CalibrationRef.valid_until_iso8601`、および required record のうち kind ∈ {", "| (a) `CalibrationRef.valid_until_iso8601` が None（第 1 評価点・None 検査のみ — CalibrationRef は measured_at を持たないため上限項は評価しない・v0.2.8 R7-06 / R8-07）；(b) required record のうち " + kinds + " の `valid_until_iso8601` が None（無期限）、または `valid_until − measured_at > baseline.max_validity_s[key]`（key = CALIBRATION_RECORD は参照先 calibration の `CalibrationKind`・他は `DeploymentEvidenceKind`・FI は subject 別。baseline に当該 key の上限が無い = 違反・v0.2.7 R6-11）；(c) 第 2 評価点で `CalibrationRef.valid_until > 対応する CALIBRATION_RECORD.valid_until`（ref が record より長い有効期限を宣言・R8-07）（v0.2.4・R2-18・評価点 = §8.1 (2) の両評価点（R5-04）） | `P_VALIDITY_UNBOUNDED` |")
    d.rep("None 不可・上限 = baseline `max_validity_s[kind]`（v0.2.7）", "None 不可・上限 = baseline `max_validity_s[key]`（key = CALIBRATION_RECORD は参照先 calibration の CalibrationKind・他は DeploymentEvidenceKind・v0.2.7・v0.2.8 R8-07）")
    d.rep("CalibrationKind / DeploymentEvidenceKind（FI は subject 別）→ 有効期間の上限 [s]（P_VALIDITY_UNBOUNDED の上限側）", "CalibrationKind（CALIBRATION_RECORD は参照先 calibration の kind で引く）/ DeploymentEvidenceKind（FI は subject 別）→ 有効期間の上限 [s]（P_VALIDITY_UNBOUNDED の上限側・v0.2.8 R8-07）")
    d.rep("`P_VALIDITY_UNBOUNDED`（`CalibrationRef` 側 + MIN_SHADOW の SAFETY_LAYER_ACCEPTANCE・v0.2.7 R5-04）", "`P_VALIDITY_UNBOUNDED`（`CalibrationRef` 側 = None 検査のみ + MIN_SHADOW の SAFETY_LAYER_ACCEPTANCE・v0.2.7 R5-04・v0.2.8 R8-07）")
    addPT("`CalibrationRef.valid_until` が対応する CALIBRATION_RECORD の `valid_until` より後（v0.2.8） | 第 2 評価点の `P_VALIDITY_UNBOUNDED`（(c) ref ≤ record）→ 05 `R_PROFILE_MISBOUND`")
# --- R7-07 / R8-09: MIN_FAULT_INJECTION を (code, trigger) で
if gate("R7-07", "R8-09"):
    d.rep("                 ∪ {R_DEADLINE_MISS, R_SAFETY_LAYER_LOST, R_TIMING_VIOLATION, R_PERMIT_EXPIRED, R_ACK_TIMEOUT, R_HEALTH_CONFIRM_TIMEOUT, R_BOUNDARY_DWELL_EXCEEDED, R_LEASE_DURATION_EXCEEDED, R_MANAGER_UNAVAILABLE}", "                 ∪ {R_DEADLINE_MISS, R_SAFETY_LAYER_LOST#HEARTBEAT_TIMEOUT, R_TIMING_VIOLATION, R_PERMIT_EXPIRED, R_ACK_TIMEOUT, R_HEALTH_CONFIRM_TIMEOUT, R_BOUNDARY_DWELL_EXCEEDED#DWELL_TIMEOUT, R_LEASE_DURATION_EXCEEDED, R_MANAGER_UNAVAILABLE}   # v0.2.8（R7-07 / R8-09）: timeout 駆動 code は code#trigger で列挙")
    d.rep("R_PROFILE_SUSPENDED#EVENT, R_REGISTRY_UNAVAILABLE, R_INTER_ARM_VIOLATION, R_CLOCK_ANOMALY}   # v0.2.6（R4-13）", "R_PROFILE_SUSPENDED#EVENT, R_REGISTRY_UNAVAILABLE#HEAD_CHECK, R_INTER_ARM_VIOLATION, R_CLOCK_ANOMALY#DRIFT}   # v0.2.6（R4-13）・v0.2.8（R8-09）: HEAD_CHECK / DRIFT の経路を要求")
    d.rep("| `DeploymentEvidencePolicy` が MIN_SHADOW / MIN_CLOSED_LOOP / MIN_FAULT_INJECTION / MIN_NEGATIVE_CONTROLS を含む（v0.2.1・v0.2.6 R4-03） | `P_EVIDENCE_POLICY_TOO_WEAK` |", "| `DeploymentEvidencePolicy` が MIN_SHADOW / MIN_CLOSED_LOOP / MIN_FAULT_INJECTION / MIN_NEGATIVE_CONTROLS を含む。「含む」の MIN_FAULT_INJECTION 側 = (code, trigger) の等値: code#trigger の member は同じ trigger を宣言した `FaultInjectionRequirement` でのみ満たされ、bare member は trigger = None の requirement で満たす（timeout 経路の別経路代替 — HEALTH_FAILED / ATTEMPTS_EXHAUSTED / STARTUP / PERMIT — は不可。member の trigger の選択は 05 §8 語彙内の起草判断・v0.2.8 R7-07 / R8-09）（v0.2.1・v0.2.6 R4-03） | `P_EVIDENCE_POLICY_TOO_WEAK` |")
    d.rep("None = trigger を問わない。語彙に無い = P_FAULT_CODE_UNKNOWN。evidence の subject_ref = code[#trigger]", "None = trigger を問わない（ただし MIN_FAULT_INJECTION の code#trigger member は満たさない・v0.2.8 R7-07）。語彙に無い = P_FAULT_CODE_UNKNOWN。evidence の subject_ref = code[#trigger]")
    addPT("MIN_FAULT_INJECTION の timeout 駆動 code を trigger = None で宣言した policy（v0.2.8） | `P_EVIDENCE_POLICY_TOO_WEAK`（code#trigger の member を満たさない）")
# --- R7-09（06 側）: DIAGNOSTIC:<item> の語彙
if gate("R7-09"):
    d.rep("または `trigger ≠ None ∧ trigger ∉ 05 §8 記録義務が当該 code に定める trigger 語彙`（v0.2.7 R6-03 / R5-10）", "または `trigger ≠ None ∧ trigger ∉ 05 §8 記録義務が当該 code に定める trigger 語彙`（`DIAGNOSTIC:<item>` は <item> ∉ REQUIRED_DIAGNOSTIC_ITEMS ∪ baseline.diagnostic_items なら未知・v0.2.7 R6-03 / R5-10・v0.2.8 R7-09）")
# --- R7-10（06 側）
if gate("R7-10"):
    d.rep("process は診断用 SAFEHOLD で起動してよいが permit 発行・CAS・actuation は全面拒否（05 `R_REGISTRY_UNAVAILABLE`）", "process は診断用 SAFEHOLD で起動してよいが permit 発行・TRANSFER_TO_EXECUTOR・actuation は全面拒否（TRANSFER_TO_SAFEHOLD は registry 非依存・v0.2.8 R7-10・05 `R_REGISTRY_UNAVAILABLE`）")
# --- R7-15 / R8-01（06 側）: 書込時の baseline head 照合
if gate("R7-15", "R8-01"):
    d.rep("`role_registry_hash ≠ role registry の現 head`（書込時・R6-05）；", "`role_registry_hash ≠ role registry の現 head`（書込時・R6-05）；`timing_baseline_hash ≠ baseline registry の head(cell_id)`（書込時・state ∈ {PROPOSED, ACCEPTED}・撤回済 baseline を束縛する record を作らせない・v0.2.8 R8-01 / R7-15）；")
    addPT("baseline registry の head を進めた後に旧 baseline を指す ACCEPTED record を append（v0.2.8） | `P_ACCEPTANCE_RECORD_INVALID`（書込時）；既存 record は 05 §3.4 (i) で permit 拒否")
# --- R8-02: finger 交換の runtime 可視性
if gate("R8-02"):
    d.rep("期限に現れない変更（incident・tool 交換・firmware 更新", "期限に現れない変更（incident・tool 個体（serial）の変更・firmware 更新")
    d.rep("と cell の運用管理の court。本 doc は主張しない。", "と cell の運用管理の court。finger 等の交換部品の物理同一性（RS71 §0 #4）は宣言 ↔ pin の等値（`P_TOOL_GEOMETRY_MISMATCH`）と TPI evidence・保全管理の court であり、serial の TOOL_IDENTITY では検出しない（PT-44・v0.2.8 R8-02）。本 doc は主張しない。")
    d.rep("v0.2.7 open（R6-07 / R6-08 / R6-11）: `base_pose_tolerance_*` / `max_validity_s` の値、", "v0.2.7 open（R6-07 / R6-08 / R6-11）: `base_pose_tolerance_*` / `max_validity_s` の値、TOOL_PAYLOAD_IDENTIFICATION を `P_VALIDITY_UNBOUNDED` の kind 集合に含めるか（finger 再 attest 周期 = `max_validity_s[TOOL_PAYLOAD_IDENTIFICATION]`・v0.2.8 R8-02）、")
# --- R8-03: base pose の frame 規約
if gate("R8-03"):
    d.rep("と `baseline.base_pose_tolerance_m` / `_rad` 内で一致（`layout[arm.base_transform_id]` の Y を arm.resource_id ごとに符号付きで照合: ee_left ↔ ROBOT_LEFT_BASE・ee_right ↔ ROBOT_RIGHT_BASE。鏡像配置は不一致）。", "と `baseline.base_pose_tolerance_m` 内で一致（**並進のみ・SSOT frame で比較**・v0.2.8 R8-03: layout artifact は T_SSOT←cell（または `base_frame_ref == SSOT world frame` の宣言）を運び、それを用いて `layout[arm.base_transform_id]` の並進を SSOT frame へ写して ROBOT_*_BASE と arm.resource_id ごとに符号付きで比較: ee_left ↔ ROBOT_LEFT_BASE・ee_right ↔ ROBOT_RIGHT_BASE（宣言無し / 変換不能 = 評価不能 = 違反）。回転は本検査の対象外 — `_rad` は BASE_POSE_VERIFY（実測 vs layout・参照 = layout 自身）が使う。鏡像配置・frame の取り替えは不一致。固定 base の参照回転と frame 規約の正式値 = OPP-16）。")
    d.rep("`base_pose_tolerance_*` / `max_validity_s` の値、", "`base_pose_tolerance_*` / `max_validity_s` の値、base pose の frame 規約と固定 base の参照回転（T_SSOT←cell の出所・v0.2.8 R8-03）、")
    d.rep("同・回転許容 [rad]", "同・回転許容 [rad]（BASE_POSE_VERIFY のみ・P_BASE_LAYOUT_MISMATCH は並進のみ・R8-03）")
# --- R8-04: evaluator は観測のみ
if gate("R8-04"):
    d.rep("    fail_closed: bool                      # **True 必須**（v0.2.3・CD-14: knob ではなく明示宣言。省略時 default を持たせないための field で、False は登録拒否・欠落は codec 拒否）", "    fail_closed: bool                      # **True 必須**（v0.2.3・CD-14: knob ではなく明示宣言。省略時 default を持たせないための field で、False は登録拒否・欠落は codec 拒否）\n    # v0.2.8（R8-04）: evaluator は**観測のみ**（controller へ運動 command を出さない・ISL でも gateway でもない・P1 / P2 を破らない）。評価に運動を要する check は stage = BEFORE_PERMIT のみで、lease 中の周期再実行（REQUIRED_DIAGNOSTIC_ITEMS の identity 系）から除く。BASE_POSE_VERIFY は commissioning 用（運動を伴う計測・BEFORE_PERMIT）と lease 中用（外部 tracker / mount sensor 等の受動計測）の 2 変種を持ち、受動計測源が無い cell では診断項目は boundary（S_BOUNDARY_WAIT / SAFEHOLD）でのみ実行し周期上限 = lease_max_duration_s + boundary_dwell_s")
# --- R8-06: baseline 変更は PROPOSED を経る
if gate("R8-06"):
    d.rep("のいずれかで違反（registry ACL は OPP-13）；", "のいずれかで違反（registry ACL は OPP-13）；ACCEPTED（gen+1 を含む）の `timing_baseline_hash` が同一登録の PROPOSED record の値と異なる（PROPOSED 無しの gen+1 は superseded record の値と等しいこと・baseline の変更は必ず新 PROPOSED = 第 1 評価点の再実行を経る・v0.2.8 R8-06）；")
    d.rep("**評価点は 2 つ**: 第 1 評価点 = 登録時", "**評価点は 2 つ**（+ record 書込時 = PROPOSED と ACCEPTED の両方の書込み・R8-06 / R8-13）: 第 1 評価点 = 登録時")
# --- R8-08 / R8-16: FI 不等式の scope・struct・load_condition_ref
if gate("R8-08", "R8-16"):
    fi = " §6.1 の FI artifact struct を持つ FI record（subject が失敗表で TRANSFER_TO_SAFEHOLD を伴う timeout 駆動 code: R_DEADLINE_MISS / R_TIMING_VIOLATION / R_HEALTH_CONFIRM_TIMEOUT / R_LEASE_DURATION_EXCEEDED / R_SAFETY_LAYER_LOST#HEARTBEAT_TIMEOUT / R_BOUNDARY_DWELL_EXCEEDED#DWELL_TIMEOUT / R_*_EXPIRED_ACTIVE#DEADLINE。R_PERMIT_EXPIRED / R_ACK_TIMEOUT / R_MANAGER_UNAVAILABLE は SafeHold 遷移を持たず到達時間が定義できないため対象外）は加えて `detection_to_safehold_worst_case_s ≥ max(t_mono(DISPOSITION) − t_mono(FAULT))`（引用範囲内の全 pair・R6-20・struct 欠落 = FALSE）を満たす；他の FI record は subject 文法行のみで照合（v0.2.8 R8-08）。" if conf("R8-08") else " FI record は加えて `detection_to_safehold_worst_case_s ≥ max(t_mono(DISPOSITION) − t_mono(FAULT))`（引用範囲内の全 pair・R6-20）。"
    d.rep(" FI record は加えて `detection_to_safehold_worst_case_s ≥ max(t_mono(DISPOSITION) − t_mono(FAULT))`（引用範囲内の全 pair・R6-20）。", fi)
    if conf("R8-08"):
        d.insert_after_line("#   期待結果 = 拒否 / SafeHold / SafeStop", "#   FI artifact struct（v0.2.8 R8-08・§3 P_FAULT_EVIDENCE_UNVERIFIED / P_SAFETY_BUDGET_EXCEEDED が参照する schema・CEM と同様）= {audit_range, detection_to_safehold_worst_case_s, gateway_switch_worst_case_s, load_condition_ref}。持つ record = subject が失敗表で TRANSFER_TO_SAFEHOLD を伴う timeout 駆動 code の FI（上記「timeout 駆動 code」= この集合）。拒否のみの code（R_PERMIT_EXPIRED / R_ACK_TIMEOUT / R_MANAGER_UNAVAILABLE を含む）の FI record は持たない")
    if conf("R8-16"): d.rep("`load_condition_ref` は両 arm を名指す・検査は ∀ arm で CEM[arm] を用いる・v0.2.7 R6-15。", "`load_condition_ref` が解決し `cell.arms[].resource_id` の全てを名指す（解決不能 / 部分集合 = 評価不能 = 違反・v0.2.8 R8-16）・検査は ∀ arm で CEM[arm] を用いる・v0.2.7 R6-15。")
# --- R8-10: negative control の audit 範囲再利用
if gate("R8-10"):
    d.rep("`NC#<name>` → §6.1 の期待 audit 内容表の record；その他の subject = FALSE。", "`NC#<name>` → §6.1 の期待 audit 内容表の record；その他の subject = FALSE。異なる subject の required HEALTH_CHECK_RUN / FAULT_INJECTION_RESULT record が引く (lease_id, seq 範囲) は互いに素（重なり = FALSE・1 record を複数 subject の証拠に再利用できない・手順内容の照合は OPP-5 / RT0・v0.2.8 R8-10）。")
# --- R8-11: SHADOW 受理の資格照合
if gate("R8-11"):
    d.rep("SHADOW のみ ⇒ ∃ COMMISSIONING ∧ ∃ INDEPENDENT_REVIEWER で相異；", "SHADOW のみ ⇒ ∃ COMMISSIONING ∧ ∃ INDEPENDENT_REVIEWER で相異かつ両者が role_registry で資格あり（v0.2.8 R8-11）；approvals[] の全 entry は `(operator_ref, role) ∈ 現 head の role registry`（§8.3 role registry 節の一般規則の検査位置・R8-11）；")
    addPT("SHADOW のみの ACCEPTED record で INDEPENDENT_REVIEWER が role registry に無い（v0.2.8） | `P_ACCEPTANCE_RECORD_INVALID`")
# --- R8-12: role 語彙の検査を P_* に
if gate("R8-12"):
    d.rep("v0.2.7（R6-06）: role 名は §8.3 role registry が定義する語彙に限る（未知の role 名 = codec 拒否）。", "v0.2.7（R6-06）: role 名は §8.3 role registry が定義する語彙に限る（v0.2.8 R8-12: codec ではなく `P_CLEARANCE_ROLE_MISSING` の拡張節 — 第 1 評価点は現 head・acceptance record 書込時は record.role_registry_hash が指す head の語彙で評価。以後の head 変更は既存の ROLE_REGISTRY_SUPERSEDED が扱う）。")
    d.rep("（= 05 §5.4 条件 10 の集合。SAFETY は ISL clearance record と AND）（v0.2.3・CD-02・v0.2.4 R1-04 / R2-05） | `P_CLEARANCE_ROLE_MISSING` |", "（= 05 §5.4 条件 10 の集合。SAFETY は ISL clearance record と AND）（v0.2.3・CD-02・v0.2.4 R1-04 / R2-05）、かつ ∄ (reason, role) ∈ `clearance_roles`: role ∉ vocabulary(head(role registry))（第 1 評価点 = 現 head・acceptance record 書込時 = record.role_registry_hash が指す head。codec ではなく本 code・v0.2.8 R8-12） | `P_CLEARANCE_ROLE_MISSING` |")
    addPT("role registry に無い role 名を `clearance_roles` に宣言（v0.2.8） | `P_CLEARANCE_ROLE_MISSING`（語彙節・登録拒否）")
# --- R8-14: 期限境界の統一
if gate("R8-14"):
    d.rep("| required record の `valid_until_iso8601` が permit 発行の wall-clock より前（第 2 評価点・`validity_rule` の執行） |", "| required record の `valid_until_iso8601` が permit 発行の wall-clock 以前（等号 = 失効・有効 ⇔ eval_time < valid_until・v0.2.8 R8-14）（第 2 評価点・`validity_rule` の執行） |")
    d.rep("`valid_until` が評価時刻より後 | `P_CALIBRATION_MISSING` / `P_CALIBRATION_EXPIRED` |", "`valid_until` が評価時刻より後（等号 = 失効・R8-14） | `P_CALIBRATION_MISSING` / `P_CALIBRATION_EXPIRED` |")
    d.rep("(4) `P_*` は certificate・EP grade・`SkillDefinitionHash` のいずれにも影響しない。", "(4) `P_*` は certificate・EP grade・`SkillDefinitionHash` のいずれにも影響しない。(5) 期限の境界は全て「有効 ⇔ 評価時刻 < valid_until」（等号 = 失効・05 §3.5 の厳密境界と同じ・v0.2.8 R8-14）。")
# --- R8-17: arm 間の識別子相異
if gate("R8-17"):
    d.rep("単一 robot 限定案は RS71 §0 DUAL-ARM 不変前提と衝突するため不採用・OPP-15） | `P_ARM_COVERAGE` |", "単一 robot 限定案は RS71 §0 DUAL-ARM 不変前提と衝突するため不採用・OPP-15）。arms 間で `robot_serial_ref` / `tool_payload.tool_id` / `tool_payload.tcp_offset_ref` は相異（同一 = identity check が arm を区別できず ARM_SWAP が空文化・v0.2.8 R8-17） | `P_ARM_COVERAGE` |")
    addPT("両 arm に同一 `robot_serial_ref` を宣言（v0.2.8） | `P_ARM_COVERAGE`")
# --- R8-18: authoritative asset の指定
if gate("R8-18"):
    d.rep("が RS71 §0 #4 の pinned gripper geometry asset の hash と一致（`finger_design_ref` 未解決 = 違反。", "が RS71 §0 #4 が**現に authoritative と指定する** gripper geometry asset（SUPERSEDED pointer を追った現行・custody = §0-A・Rs。banked historical LOCK asset との一致は不一致扱い・v0.2.8 R8-18）の hash と一致（`finger_design_ref` 未解決 = 違反。")
    d.rep("RS71 #4 の pinned asset の hash と不一致 = P_TOOL_GEOMETRY_MISMATCH", "RS71 #4 が現に authoritative と指定する asset（SUPERSEDED pointer を追う・R8-18）の hash と不一致 = P_TOOL_GEOMETRY_MISMATCH")
# --- R8-19: BASE_POSE_VERIFY の negative method
if gate("R8-19"):
    d.rep("INTER_ARM_COLLISION = 交差する両腕 setpoint の command\n", "INTER_ARM_COLLISION = 交差する両腕 setpoint の command；`<check_id>#NEGATIVE` の BASE_POSE_VERIFY = evaluator の計測入力へ記録済 offset を注入（HEALTH_CHECK_RUN artifact から参照・物理的に base を動かさない・layout 改変は NC#BASE_TRANSFORM_TAMPER であって本 negative ではない・v0.2.8 R8-19）\n")
# --- R8-22: §9 #11 の拡張
if gate("R8-22"):
    d.rep("と cell の運用管理の court。本 doc は主張しない。", "と cell の運用管理の court。operator_ref の真正性（記録者 = 名指された operator）は OP-5 / U14 の署名方式に依存し、本 doc は主張しない（v0.2.8 R8-22）。本 doc は主張しない。")
# --- R8-23: zone の arm scope
if gate("R8-23"):
    d.rep("→ 新 setpoint の**線分**（FK 後・TCP 点）— ZOH でも腕は連続に動くため点評価では keep-out を跨げる（v0.2.4・R1-06 / R2-19）。", "→ 新 setpoint の**線分**（FK 後・TCP 点）— ZOH でも腕は連続に動くため点評価では keep-out を跨げる（v0.2.4・R1-06 / R2-19）。DEPLOYMENT_WORKSPACE は command の `arm_targets` の各 entry（各 arm）の線分ごとに全 zone に対して評価し、いずれかの arm が FALSE なら term は FALSE（v0.2.8 R8-23。arm 別の reach zone は field を足さない）。")
# --- OPP rows (Rs-exclusive)
if gate("R8-24", "R7-19"): addOPP("registry 意味論（v0.2.8・Rs）: " + ("(a) CLOSED_LOOP 受理の approvals に SHADOW 対（COMMISSIONING + INDEPENDENT_REVIEWER）も要求するか（特権の単調性・R8-24）" if conf("R8-24") else "") + ("；(b) 良性理由の REVOKED が兄弟 profile を止める件は V7 が NOT_A_DEFECT（acceptance 失効が良性の retirement 経路を既に与える）— `AcceptanceState.RETIRED` の要否は任意の検討事項（R7-19）" if conf("R8-24") else "良性理由の REVOKED が兄弟 profile を止める件（R7-19）: `AcceptanceState.RETIRED` の要否") + " | §8.3・05 §3.4 (i) | Rs 裁定待ち")
if newOPP: d.insert_after_line("| OPP-17 |", "\n".join(newOPP))
if newP:
    cl = d.line("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`"); d.repline("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`", cl + " / " + " / ".join(newP) + "（v0.2.8）")
# --- R8-13: 第 1 評価点を閉じた list に（自動生成）+ record 書込時 1b
if gate("R8-13"):
    listed = re.findall(r"`(P_[A-Z_]+)`", d.line("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`"))
    rule = d.line("規則: (1) 全検査は fail-closed")
    a = rule.find("第 2 評価点 = **permit 発行時**"); b = rule.find("} — 05 §3.4 (b)")
    second = set(re.findall(r"`(P_[A-Z_]+)`", rule[a:b]))
    write_time = ["P_TIMEOUT_CEILING", "P_BASELINE_INCOMPLETE", "P_ACCEPTANCE_RECORD_INVALID"]
    both = ["P_EVIDENCE_UNBOUND", "P_PREDICATE_HASH_MISMATCH", "P_VALIDITY_UNBOUNDED", "P_BASE_LAYOUT_MISMATCH", "P_TIMEOUT_ORDER", "P_EXPECTATION_UNCERTIFIED"] + (["P_CLEARANCE_ROLE_MISSING"] if conf("R8-12") else [])
    first = [c for c in listed if (c not in second or c in both) and c not in write_time]
    seen = set(); first = [c for c in first if not (c in seen or seen.add(c))]
    s = rule.find("（構造・単調性・反循環・codec・"); e = rule.find("／ 第 2 評価点")
    assert 0 < s < e
    closed = "（閉じた list・v0.2.8 R8-13・checker Q3 が §8.1 列挙の全 code の配置を検査）= {" + ", ".join(f"`{c}`" for c in first) + "}（このうち " + " / ".join(f"`{c}`" for c in both if c in first) + " は第 2 評価点でも再評価）；評価点 1b = record 書込時（PROPOSED / ACCEPTED）= {" + ", ".join(f"`{c}`" for c in write_time) + "}（`P_BASE_LAYOUT_MISMATCH` / `P_TIMEOUT_ORDER` の baseline 依存項" + ("・`P_CLEARANCE_ROLE_MISSING` の語彙節" if conf("R8-12") else "") + " も）"
    d.repline("規則: (1) 全検査は fail-closed", rule[:s] + closed + rule[e:])
d.insert_before_line("## 12. Review anchors", "PLACEHOLDER_FOLD_TABLE_06\n")
if newPT: d.insert_after_line("| PT-48 |", "\n".join(newPT))
rows06 = [("R7-01 / R8-20", "identity 系 diagnostic の SAFEHOLD 中実行", "§2.1 comment・§8.3 REQUIRED_DIAGNOSTIC_ITEMS"), ("R7-02 / R8-05", "PROPOSED が head になる・PROPOSED の検査が弱い", "§8.3 head 定義・状態遷移・P_ACCEPTANCE_RECORD_INVALID・§8.1 (2)・PT"), ("R7-03 / R8-15", "role registry supersession の検出", "§8.3 role registry"), ("R7-06 / R8-07", "CalibrationRef に measured_at が無く上限項が評価不能", "§3 P_VALIDITY_UNBOUNDED（(a) None のみ / (b) record 側上限 / (c) ref ≤ record）・§6.1 comment・§8.3 `max_validity_s`・§8.1 (2)・PT"), ("R7-07 / R8-09", "MIN_FAULT_INJECTION の bare timeout code", "§6.1 MIN_FAULT_INJECTION・§3 P_EVIDENCE_POLICY_TOO_WEAK・PT"), ("R7-09", "DIAGNOSTIC:<item> の語彙", "§3 P_FAULT_CODE_UNKNOWN"), ("R7-10", "registry 不読と TRANSFER_TO_SAFEHOLD", "§8.3 所在"), ("R7-15 / R8-01", "baseline head の書込時照合", "§8.3 P_ACCEPTANCE_RECORD_INVALID・PT"), ("R8-02", "finger 交換が runtime で不可視（(c) 正直化のみ・(a) は OPP-16）", "§5 (b)・§9 #11・OPP-16"), ("R8-03", "base pose の frame 規約・_rad の参照", "§3 P_BASE_LAYOUT_MISMATCH（並進のみ・SSOT frame）・§8.3 `base_pose_tolerance_rad`・OPP-16"), ("R8-04", "evaluator が運動を伴い得る", "§2.1 HealthCheckSpec"), ("R8-06", "ACCEPTED の baseline が PROPOSED と一致しない", "§8.3 P_ACCEPTANCE_RECORD_INVALID・§8.1 (2)"), ("R8-08 / R8-16", "FI 不等式の scope・struct・load_condition_ref", "§3 P_FAULT_EVIDENCE_UNVERIFIED / P_SAFETY_BUDGET_EXCEEDED・§6.1 FI struct"), ("R8-10", "negative control の audit 範囲再利用", "§3 P_FAULT_EVIDENCE_UNVERIFIED"), ("R8-11", "SHADOW 受理の資格照合", "§8.3・PT"), ("R8-12", "role 語彙検査が codec に置かれている", "§2.1 clearance_roles・§3 `P_CLEARANCE_ROLE_MISSING` 拡張節・PT"), ("R8-13", "第 1 評価点が閉じていない・record 書込時", "§8.1 (2)・checker Q3"), ("R8-14", "期限境界の不一致", "§3・§8.1 (5)"), ("R8-17", "arm 間の識別子相異", "§3 P_ARM_COVERAGE・PT"), ("R8-18", "authoritative asset の単数表現", "§3 P_TOOL_GEOMETRY_MISMATCH・OPP-21"), ("R8-19", "BASE_POSE_VERIFY の negative method", "§6.1"), ("R8-22", "operator_ref の真正性", "§9 #11"), ("R8-23", "DEPLOYMENT_WORKSPACE の arm ごとの評価", "§4（05 §4.3 と同期）"), ("R8-24 / R7-19", "registry 意味論（特権単調性・RETIRED）", "OPP-18"), ("R8-21", "FORCE_SENSOR 失効の class", "—"), ("R8-25", "evidence の束縛単位", "—"), ("R7-17", "header の版時刻", "header")]
tbl = [f"- **v0.2.8 fold（{NOW}）— round 5（R7 / R8 → V7 / V8）の確定 finding の fold**。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §11:", "", "| finding | 内容 | 変更節 | verdict |", "|---|---|---|---|"]
for i, c, s in rows06: tbl.append(f"| {i} | {c} | {s if any_conf(*i.split(' / ')) else '— 適用せず'} | {'; '.join(f'{x}={vstr(x)}' for x in i.split(' / '))} |")
d.rep("PLACEHOLDER_FOLD_TABLE_06\n", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= checker (R7-16 Q2 exclusion clause, R8-13 Q3 placement)
c = Doc("check_review_candidate.py")
if gate("R7-16"):
    c.rep('''                a = jl[0].find("(j) profile が宣言する"); b = jl[0].find("が解決先の内容と一致", a)
                seg = jl[0][a:b] if b > a else jl[0][a:]
                if b <= a: warns.append("Q2 (j) segment end marker not found; matching against the whole (j) tail")
                for h, cls in sorted(decl.items()):''', '''                a = jl[0].find("(j) profile が宣言する"); b = jl[0].find("が解決先の内容と一致", a)
                seg = jl[0][a:b] if b > a else jl[0][a:]
                if b <= a: warns.append("Q2 (j) segment end marker not found; matching against the whole (j) tail")
                # v0.2.8 (R7-16): the exclusion clause '(j) の対象外 = …' is stripped before counting; excluded names pass only via the allowlist
                ex = seg.find("(j) の対象外 =")
                ex_end = seg.find("。", ex) + 1 if ex >= 0 and seg.find("。", ex) >= 0 else len(seg)
                excl_txt = seg[ex:ex_end] if ex >= 0 else ""; seg = (seg[:ex] + seg[ex_end:]) if ex >= 0 else seg
                excluded = set(re.findall(r"(\\w+(?:_sha256|_hash))", excl_txt)); ALLOW_EXCLUDED = {"tensor_binding_hash"}
                for h, cls in sorted(decl.items()):
                    if h in excluded:
                        if h in ALLOW_EXCLUDED: continue
                        fails.append(f"Q2 06 hash field '{h}' is excluded in 05 §3.4 (j) but is not on the checker allowlist"); continue''')
    c.rep("Q2  (profile spec only, v0.2.6 / R3-17 R4-02 / v0.2.7 R6-13) every *_sha256 / *_hash field declared in 06 §2.1-2.2 is named inside the sibling 05 §3.4 (j) segment, at least once per declaring class", "Q2  (profile spec only, v0.2.6 / R3-17 R4-02 / v0.2.7 R6-13 / v0.2.8 R7-16) every *_sha256 / *_hash field declared in 06 §2.1-2.2 is named inside the sibling 05 §3.4 (j) segment (exclusion clause stripped; allowlist = tensor_binding_hash), at least once per declaring class")
if gate("R8-13"):
    c.rep('''        for name, pat in (("PT", r"^\\| (PT-\\d+) \\|"), ("OPP", r"^\\| (OPP-\\d+) \\|")):''', '''        # Q3 (v0.2.8, R8-13): every P_* code in the §8.1 code list is placed in the §8.1 rule (2) evaluation-point text
        if pl:
            rl = [l for l in lines if l.startswith("規則: (1) 全検査は fail-closed")]
            if not rl: fails.append("Q3 §8.1 rule (2) line not found")
            else:
                placed = set(re.findall(r"`(P_[A-Z_]+)`", rl[0]))
                for cde in sorted(set(re.findall(r"`(P_[A-Z_]+)`", pl[0])) - placed): fails.append(f"Q3 code {cde} is listed in §8.1 but has no evaluation point in rule (2)")
        for name, pat in (("PT", r"^\\| (PT-\\d+) \\|"), ("OPP", r"^\\| (OPP-\\d+) \\|")):''')
    c.rep("  Q2  (profile spec only,", "  Q3  (profile spec only, v0.2.8 R8-13) every P_* code in the §8.1 code list appears in the §8.1 rule (2) evaluation-point text (1st point / 1b record write / 2nd point)\n  Q2  (profile spec only,")
c.save()
if any_conf("R7-16", "R8-13"):
    e = Doc("08_INDEPENDENT_REVIEW_PLAN_20260903.md")
    e.rep("を機械検査する — v0.2.6・v0.2.7 R6-13 で強化）", "を機械検査する — v0.2.6・v0.2.7 R6-13 で強化・v0.2.8 R7-16 で除外節を除いて数え / R8-13 で Q3（§8.1 列挙の全 P_* の評価点配置）を追加）"); e.save()

for name in ("07_SUCCESSOR_CONTRACT_DECISION_20260903.md", "04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md", "08_INDEPENDENT_REVIEW_PLAN_20260903.md"):
    d = Doc(name); d.rep("(v0.2.7 REVIEW CANDIDATE)", "(v0.2.8 REVIEW CANDIDATE)"); d.rep("REVIEW CANDIDATE v0.2.7（", "REVIEW CANDIDATE v0.2.8（"); d.save()

# --- R7-17: fill the C2 WARN count of 05 from the actual checker run (date-THEN-write / measured, not remembered)
if conf("R7-17"):
    r = subprocess.run([sys.executable, os.path.abspath(f"{P}/check_review_candidate.py"), os.path.abspath(f"{P}/05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md"), "--runtime"], capture_output=True, text=True, cwd=os.getcwd())
    out = r.stdout + r.stderr; assert "FAIL=0" in out, out[:400]
    n = out.count("WARN C2")
    d = Doc("05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md"); d.rep("{{C2WARN}}", str(n)); d.save(); print("C2 WARN measured:", n)
print("applied:", applied); print("NOW =", NOW)
