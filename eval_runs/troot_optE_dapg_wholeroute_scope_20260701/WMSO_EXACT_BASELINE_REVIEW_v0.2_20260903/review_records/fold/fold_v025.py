#!/usr/bin/env python3
"""v0.2.4 -> v0.2.5 fold: Rs ruling 2026-09-04 (adopts the external recommendation on OPP-15 B+ / OPP-11 / OPP-13 / OP-19).
Usage: python3 fold_v025.py <PKG_DIR>. Records-only; frozen files untouched; every anchor asserts uniqueness."""
import sys, re, subprocess
P = sys.argv[1]
NOW = subprocess.check_output(["date", "-u", "+%Y-%m-%d %H:%M UTC"]).decode().strip()
A = "$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md"; D0 = "$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md"
RS = "Rs 裁定 2026-09-04（GPT5.6sol 推奨を採用・`review_records/rs_consult/`）"

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
    def resub(self, pat, new, count=1):
        self.t, n = re.subn(pat, new, self.t, flags=re.S); assert n == count, (self.name, pat[:60], n)
    def save(self): open(f"{P}/{self.name}", "w", encoding="utf-8").write(self.t); print("wrote", self.name)

# ======================================================================= 05
d = Doc("05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("RUNTIME SPEC (v0.2.4 REVIEW CANDIDATE)", "RUNTIME SPEC (v0.2.5 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.4（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）**", "- status: **REVIEW CANDIDATE v0.2.5（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.4 → v0.2.5 = " + RS + " の反映（OPP-15 B+ / OPP-11 / OPP-13 / OP-19・§13）。旧版の系譜:")
d.rep("→ **v0.2.3 再レビュー round（R1 / R2 → V1 / V2）の fold = 本版 v0.2.4（§13）**", "→ v0.2.3 再レビュー round（R1 / R2 → V1 / V2）の fold = v0.2.4（2026-09-04 23:00 UTC）→ **Rs 裁定（外部推奨採用）の fold = 本版 v0.2.5（§13）**")
# §2: DeploymentValidityMonitor component
d.insert_after_line("| **AuditRecorder** |", "| **DeploymentValidityMonitor**（v0.2.5・OP-19） | deployment 側の失効 event（incident・tool 交換・firmware 更新・layout revision・ISL build 変更・profile の SUSPENDED / REVOKED）を検出し AuthorityManager へ通知する。**自らは AuthorityState を書かない**（manager が唯一 writer として TRANSFER_TO_SAFEHOLD を CAS）。周期診断は timing baseline が定める drift / proof-test 項目のみ | 監視対象の直近観測（durable 不要） | D0 §F fail-closed `%s:318`・doc 06 §8.3 |" % D0)
# §3.2: SafeHoldReason += VALIDITY_EXPIRED
d.rep("| ENVELOPE_VIOLATION | SAFETY | SAFE_STOP | CHECKPOINT_DISABLED   # v0.2.2:", "| ENVELOPE_VIOLATION | SAFETY | SAFE_STOP | CHECKPOINT_DISABLED | VALIDITY_EXPIRED   # v0.2.5（OP-19）: VALIDITY_EXPIRED = lease の validity_deadline_mono 到達 / profile の SUSPENDED・REVOKED / calibration・evidence の失効 event。v0.2.2:")
# §3.4: CommitPermit fields
d.rep("    profile_hash: str                                 # IndustrialDeploymentProfile（doc 06）\n    proposed_lease: ActiveAuthorityLease", "    profile_hash: str                                 # IndustrialDeploymentProfile（doc 06）\n    acceptance_record_hash: str                       # v0.2.5（OPP-13）: doc 06 §8.3 ProfileAcceptanceRecord（state == ACCEPTED・generation を束縛）\n    acceptance_generation: int\n    validity_deadline_mono: float                     # v0.2.5（OP-19）: min(calibration 期限, evidence 期限, acceptance 期限, issued_at + lease_max_duration_s) を manager clock へ変換した値（wall→mono は発行時に確定・doc 06 OPP-3）\n    proposed_lease: ActiveAuthorityLease")
d.rep("    expires_at: float                                 # = issued_at + profile.permit_ttl_s\n```", "    expires_at: float                                 # = issued_at + profile.permit_ttl_s\n    effective_expires_at: float                       # v0.2.5（OPP-11）: = min(expires_at, ack.valid_until, decision.t_mono + decision_max_age_s, validity_deadline_mono)。条件 2 はこちらを使う\n```")
# §3.4 (i) rewrite + (k)
d.rep("(i) `permit.profile_hash ∈ accepted_profiles ∧ permit.profile_hash ∉ revoked_profiles`（登録・受理済かつ未失効の profile。registry の所在・受理権限・失効権限 = doc 06 §8.1 / OPP-13・違反 = `R_PROFILE_MISBOUND`・v0.2.3 CD-17・v0.2.4 R2-08）",
      "(i) doc 06 §8.3 の `ProfileRegistry` で `permit.profile_hash` の最新 `ProfileAcceptanceRecord` が `state == ACCEPTED ∧ proposed_lease.mode ∈ allowed_lease_modes ∧ 有効期限内` であり、permit はその `acceptance_record_hash` / `generation` を束縛する（registry 不読 = `R_REGISTRY_UNAVAILABLE`・permit 不発行；SUSPENDED / REVOKED / 世代不一致 = `R_PROFILE_SUSPENDED`・v0.2.5 OPP-13。旧 v0.2.4 の `accepted_profiles` / `revoked_profiles` 2 集合は本 record に置換）; (k) `validity_deadline_mono` と `effective_expires_at` を発行時に導出して permit に固定（v0.2.5・OPP-11 / OP-19）")
# §3.5 conditions 2 (effective expiry), 6 (age re-check), new 12 (registry re-check)
d.rep("2. `permit.state == UNUSED ∧ now < permit.expires_at ∧", "2. `permit.state == UNUSED ∧ now < permit.effective_expires_at`（v0.2.5・OPP-11: permit_ttl だけでなく ACK・decision age・validity deadline の最小値）` ∧")
d.rep("6. `proposed_lease.mode == CLOSED_LOOP_AUTHORITY ⇒ resolve(authority_decision_ref).granted == True`", "6. `proposed_lease.mode == CLOSED_LOOP_AUTHORITY ⇒ resolve(authority_decision_ref).granted == True ∧ now − decision.t_mono ≤ decision_max_age_s`（age の CAS 時再検査・v0.2.5 OPP-11: permit 発行時に有効でも消費時に失効し得る）")
d.insert_after_line("11. **boundary guard（v0.2.2・B-H2 / B2-02）**", "12. **registry 再検査（v0.2.5・OPP-13）**: doc 06 §8.3 registry の線形化読みで `permit.profile_hash` の最新 record が `state == ACCEPTED ∧ generation == permit.acceptance_generation ∧ proposed_lease.mode ∈ allowed_lease_modes`。違反 = REJECTED・`R_PROFILE_SUSPENDED`（permit 発行後・CAS 前の SUSPENDED / REVOKED 競合を閉じる）。registry 不読 = REJECTED・`R_REGISTRY_UNAVAILABLE`。")
# §3.7 transition rows
d.insert_after_line("| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` | lease 活性時間（LEASE_ACTIVATED からの経過）が `lease_max_duration_s` を超過", "| `S_LEASE_ACTIVE` / `S_HEALTH_PENDING` / `S_BOUNDARY_WAIT`（CLOSED_LOOP_AUTHORITY） | `now ≥ lease.validity_deadline_mono`（calibration / evidence / acceptance の期限到達・manager clock・v0.2.5 OP-19） | TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP if 失効項目が安全機能・TCP・停止性能に関わる) | `S_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP)` | FAULT(R_CALIBRATION_EXPIRED_ACTIVE \\| R_EVIDENCE_EXPIRED_ACTIVE), DISPOSITION(HOLD \\| SAFE_STOP) |\n| any (EXECUTOR・CLOSED_LOOP_AUTHORITY) | DeploymentValidityMonitor の失効 event（incident / tool 交換 / firmware 更新 / layout revision / ISL build 変更 / profile SUSPENDED・REVOKED）（v0.2.5・OP-19 / OPP-13） | TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP if 安全起因) | `S_SAFEHOLD(…)` | FAULT(R_PROFILE_SUSPENDED \\| R_EVIDENCE_EXPIRED_ACTIVE), DISPOSITION(HOLD \\| SAFE_STOP)・全 UNUSED permit VOID |\n| any (EXECUTOR) | INTER_ARM 項の違反（両 arm の提案状態が pairwise keep-out / min separation / swept-volume predicate に反する）（v0.2.5・OPP-15 B+） | TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) | `S_SAFEHOLD(ENVELOPE_VIOLATION)` | FAULT(R_INTER_ARM_VIOLATION), DISPOSITION(HOLD) |")
# failure table rows
d.insert_after_line("| lease 活性時間が `lease_max_duration_s` 超過（v0.2.3・CD-10） |", "| lease の `validity_deadline_mono` 到達（calibration / evidence / acceptance 期限・v0.2.5 OP-19） | AuthorityManager | `R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE` | TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP)・lease 無効・UNUSED permit VOID | `HOLD` / `SAFE_STOP`（安全機能・TCP・停止性能に関わる失効） |\n| profile の SUSPENDED / REVOKED / 世代不一致（permit 発行時・CAS 条件 12・活性 lease 中の event）（v0.2.5・OPP-13） | AuthorityManager / DeploymentValidityMonitor | `R_PROFILE_SUSPENDED` | permit 不発行 / CAS REJECTED / 活性 CLOSED_LOOP lease は TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP if 安全起因) | `HOLD` / `SAFE_STOP` |\n| registry（doc 06 §8.3）が読めない（v0.2.5・OPP-13） | AuthorityManager | `R_REGISTRY_UNAVAILABLE` | permit 不発行・CAS REJECTED・actuation 全面拒否（診断用 SAFEHOLD での起動は可） | `HOLD` |\n| INTER_ARM 項の違反（v0.2.5・OPP-15） | CommandGateway | `R_INTER_ARM_VIOLATION` | command 拒否 + TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) | `HOLD` |")
# §4.1 ActiveAuthorityLease fields
d.rep("    profile_hash: str                                 # IndustrialDeploymentProfile（doc 06）— 変更 = 新 lease（in-place 変更禁止）\n    authority_decision_ref: str | None", "    profile_hash: str                                 # IndustrialDeploymentProfile（doc 06）— 変更 = 新 lease（in-place 変更禁止）\n    acceptance_record_hash: str                       # v0.2.5（OPP-13）: permit から複写（generation を含む record の hash）\n    validity_deadline_mono: float                     # v0.2.5（OP-19）: permit から複写。CLOSED_LOOP では到達 = TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)。SHADOW では記録のみ（次 permit 評価で扱う）\n    authority_decision_ref: str | None")
# §4.3 INTER_ARM term
d.insert_after_line("| SAFETY_RESTRICTION | profile `SafetyRestrictionSet`（静的） |", "| INTER_ARM（v0.2.5・OPP-15 B+） | profile `InterArmRestrictionSet`（min separation / pairwise keep-out / swept-volume predicate・content hash 付き）+ `CellKinematicLayoutRef`（両 arm の base transform） | workspace（両 arm） | CommandGateway | 評価対象 = 提案 command の arm の線分 × 他 arm の**同一線形化 snapshot**での状態（直近 admitted setpoint または実測）。評価不能 = FALSE。動的干渉の独立監視は IndependentSafetyLayer（本 term の代替ではない・AND） |")
d.rep("- 意味論: command `c` は admissible ⇔ 全 term `T` について `T.admit(c) == True`。", "- 意味論: command `c` は admissible ⇔ 全 term `T` について `T.admit(c) == True`（INTER_ARM は両 arm の状態を同一 snapshot で連言評価・v0.2.5）。")
# §4.5 triggers
d.rep("／ profile_hash の更新要求（新 lease 経路へ）／ `NO_CHAIN` 後の SAFEHOLD 転送。", "／ profile_hash の更新要求（新 lease 経路へ）／ `NO_CHAIN` 後の SAFEHOLD 転送 ／ **validity deadline 到達・deployment 失効 event・profile の SUSPENDED / REVOKED（VALIDITY_EXPIRED・v0.2.5 OP-19 / OPP-13）** ／ INTER_ARM 項の違反（v0.2.5）。")
# §5.4 first row: add VALIDITY_EXPIRED
d.rep("| INITIAL / NO_CHAIN / EXECUTOR_LOST / DEADLINE_MISS / TIMING_VIOLATION / ENVELOPE_VIOLATION / HEALTH_FAIL | 完全経路（ACK → permit → CAS）による TRANSFER_TO_EXECUTOR のみ | なし |", "| INITIAL / NO_CHAIN / EXECUTOR_LOST / DEADLINE_MISS / TIMING_VIOLATION / ENVELOPE_VIOLATION / HEALTH_FAIL / VALIDITY_EXPIRED（v0.2.5） | 完全経路（ACK → permit → CAS）による TRANSFER_TO_EXECUTOR のみ（VALIDITY_EXPIRED では新 permit が §3.4 (b)(i) で失効原因の解消を要求する） | なし |")
# §7 enum
d.rep("    R_LEASE_DURATION_EXCEEDED   # v0.2.3（CD-10）", "    R_LEASE_DURATION_EXCEEDED |   # v0.2.3（CD-10）\n    R_PROFILE_SUSPENDED | R_REGISTRY_UNAVAILABLE | R_CALIBRATION_EXPIRED_ACTIVE | R_EVIDENCE_EXPIRED_ACTIVE | R_INTER_ARM_VIOLATION   # v0.2.5（Rs 裁定: OPP-13 / OP-19 / OPP-15）— ProducerOutcome には足さない（§7 規則 1）")
# INV / T / OP
d.insert_after_line("| INV-33 |", "| INV-34 | CLOSED_LOOP_AUTHORITY lease は `validity_deadline_mono` を超えて活性でない（到達 = TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)）。deadline は permit 発行時に wall-clock 期限を manager clock へ変換して固定（v0.2.5・OP-19） | R_CALIBRATION_EXPIRED_ACTIVE / R_EVIDENCE_EXPIRED_ACTIVE |\n| INV-35 | permit の消費（CAS SUCCESS）時点で acceptance record が ACCEPTED・同一 generation であり decision age ≤ decision_max_age_s（条件 6・12）。permit 発行時の検査だけで足りるとしない（v0.2.5・OPP-11 / OPP-13） | R_PROFILE_SUSPENDED / R_AUTHORITY_DECISION_ABSENT |\n| INV-36 | admitted command は INTER_ARM 項を同一線形化 snapshot で満たす（両 arm）（v0.2.5・OPP-15） | R_INTER_ARM_VIOLATION |")
d.insert_after_line("| T-32 |", "| T-33 | 活性 CLOSED_LOOP lease 中に calibration の valid_until を経過（v0.2.5） | deadline 到達で TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)・R_CALIBRATION_EXPIRED_ACTIVE（TCP なら SAFE_STOP） |\n| T-34 | permit 発行後・CAS 前に profile を SUSPENDED（v0.2.5） | CAS 条件 12 で REJECTED・R_PROFILE_SUSPENDED・permit VOID |\n| T-35 | permit 発行後・CAS 前に decision age が decision_max_age_s を超過（v0.2.5） | 条件 6 で REJECTED・再評価要求 |\n| T-36 | registry 不読で起動（v0.2.5） | 診断用 SAFEHOLD で起動可・permit / CAS / actuation 全面拒否・R_REGISTRY_UNAVAILABLE |\n| T-37 | 左右 arm の提案線分が pairwise keep-out を跨ぐ command（v0.2.5） | INTER_ARM 項 FALSE・R_INTER_ARM_VIOLATION・TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION) |")
d.repline("| OP-19 |", "| OP-19 | 活性 lease 中の calibration / evidence 失効の検出。**" + RS + "**: CLOSED_LOOP では「次 permit まで検出しない」を採らず、(1) 既知期限 = `validity_deadline_mono` の決定論的 deadline、(2) 変更 event の即時通知（DeploymentValidityMonitor → manager CAS）、(3) 周期診断は timing baseline（doc 06 §8.3）が定める drift / proof-test 項目のみ、の三層。SHADOW は次 permit 評価で可。**残 open** = 周期診断の対象項目と周期の出所（RT0 safety case） | doc 06 §5 / §8.3 | 三層で確定・周期の値は baseline |")
d.insert_after_line("| OP-19 |", "| OP-20 | `CellSafetyTimingBaseline`（doc 06 §8.3）の発行主体（RT0 / cell safety court）と改訂手続。本 doc は `timing_baseline_hash` を acceptance record 経由で束縛するだけで値を持たない（v0.2.5・OPP-11） | doc 06 OPP-16 | RT0 へ carry |\n| OP-21 | 「every motion で両腕が保持・操作する」（RS71 §0 DUAL-ARM）の実行適合性は本 doc の INTER_ARM 項では検査しない（両 arm の**能力**の存在と相互制約まで）。適合性検査は composition / runtime 検査の court（v0.2.5・OPP-15 B+） | RS71 §0・doc 06 OPP-17 | 本 doc は主張しない |")
# §13 table
tbl = [f"- **v0.2.5 fold（{NOW}）— " + RS + "**: Rs が外部 AI（GPT5.6sol）に問い合わせ、その推奨 4 件を全件採用と裁定（本 session で Rs = 利用者本人が選択）。推奨の前提訂正 5 点は本文で照合済（全て正・`review_records/rs_consult/A_GPT56sol_20260904.md` 末尾）。凍結 schema delta = 0（runtime / deployment 層の型追加のみ）:", "", "| 項目 | 内容 | 変更節 |", "|---|---|---|",
 "| 裁定 OPP-11 | permit の実効失効 `effective_expires_at` = min(ttl, ACK, decision age, validity deadline)・CAS で decision age 再検査・timing baseline は acceptance record 経由 | §3.4 CommitPermit・(k)・§3.5 条件 2 / 6・INV-35・T-35・OP-20 |",
 "| 裁定 OPP-13 | `ProfileAcceptanceRecord`（generation・state・allowed modes）を permit / lease に束縛・CAS 条件 12 で registry 再検査・SUSPENDED / REVOKED で lease 無効化・registry 不読 = actuation 拒否 | §3.4 (i)・§3.5 条件 12・§3.7・§4.1・`R_PROFILE_SUSPENDED` / `R_REGISTRY_UNAVAILABLE`・INV-35・T-34 / T-36 |",
 "| 裁定 OP-19 | CLOSED_LOOP lease の `validity_deadline_mono`（三層: deadline・event・根拠付き周期診断）・`DeploymentValidityMonitor`・`SafeHoldReason.VALIDITY_EXPIRED` | §2・§3.2・§3.4・§3.7・§4.1・§4.5・§5.4・`R_CALIBRATION_EXPIRED_ACTIVE` / `R_EVIDENCE_EXPIRED_ACTIVE`・INV-34・T-33・OP-19 |",
 "| 裁定 OPP-15 B+ | INTER_ARM 項（両 arm の同一 snapshot 連言評価）・`R_INTER_ARM_VIOLATION`・every-motion 適合性は court へ | §4.3・§3.7・INV-36・T-37・OP-21 |"]
d.insert_before_line("## 14. Review anchors", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= 06
d = Doc("06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("DEPLOYMENT PROFILE SPEC (v0.2.4 REVIEW CANDIDATE)", "DEPLOYMENT PROFILE SPEC (v0.2.5 REVIEW CANDIDATE)")
d.rep("／ v0.2.4 = ", "／ v0.2.5 = %s（`date -u` 実測）／ v0.2.4 = " % NOW)
d.rep("- status: **REVIEW CANDIDATE v0.2.4（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）**", "- status: **REVIEW CANDIDATE v0.2.5（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.4 → v0.2.5 = " + RS + " の反映（OPP-15 B+ / OPP-11 / OPP-13 / OP-19・§11）。旧版の系譜:")
# §0 持たないもの: unchanged; §2.1 types
d.rep("    arms: tuple[ArmSpec, ...]              # v0.2.4（R2-04）:", "    kinematic_layout: CellKinematicLayoutRef  # v0.2.5（OPP-15 B+・Rs 裁定）: 両 arm の base transform（base_frame_ref 基準・RS71 §0 の固定 base Y = ∓0.35 を含む）・robot instance 対応・共有 collision model を content-addressed に束縛\n    arms: tuple[ArmSpec, ...]              # v0.2.4（R2-04）:")
d.rep("    controller: ControllerEnvelope         # この arm の運動学上限（関節数 = robot_model_ref）\n", "    controller: ControllerEnvelope         # この arm の運動学上限（関節数 = robot_model_ref）\n    base_transform_id: str                 # v0.2.5（OPP-15 B+）: kinematic_layout artifact 内の当該 arm の base transform entry（未解決 = P_ARM_BASE_UNBOUND）\n    gripper_resource_id: str               # v0.2.5（OPP-15 B+）: \"gripper_left\" | \"gripper_right\"（frozen key）— arm と gripper の対応を一意化（P_ARM_COVERAGE）\n")
d.rep("@dataclass(frozen=True)\nclass ControllerEnvelope:", "@dataclass(frozen=True)\nclass CellKinematicLayoutRef:              # v0.2.5（OPP-15 B+）: 外部 artifact（content-addressed）。中身 = {resource_id → T_cell←base}・robot instance 対応・共有 collision model の ref + sha\n    layout_id: str\n    artifact_sha256: str                   # 05 §3.4 (j) の照合対象（差し替え = R_PROFILE_MISBOUND）\n\n@dataclass(frozen=True)\nclass InterArmRestrictionSet:              # v0.2.5（OPP-15 B+）: arm 間の静的相互制約（単項の WorkspaceRestriction とは分離）\n    min_separation_m: CanonicalDecimal     # > 0（P_INTER_ARM_RESTRICTION_MISSING）\n    pairwise_keepout_refs: tuple[str, ...] # 両 arm の相対状態に対する keep-out（content hash 付き）\n    pairwise_keepout_sha256: tuple[str, ...]\n    swept_volume_predicate_refs: tuple[str, ...]   # 提案線分の swept volume に対する拒否述語\n    swept_volume_predicate_sha256: tuple[str, ...]\n    # 評価 = 05 §4.3 INTER_ARM 項（両 arm の同一線形化 snapshot で連言評価）。動的干渉は IndependentSafetyLayer が独立監視（AND・代替ではない）\n\n@dataclass(frozen=True)\nclass ControllerEnvelope:")
d.rep("    workspace: WorkspaceRestriction\n    safety_restrictions: SafetyRestrictionSet\n", "    workspace: WorkspaceRestriction\n    inter_arm_restrictions: InterArmRestrictionSet   # v0.2.5（OPP-15 B+）\n    safety_restrictions: SafetyRestrictionSet\n")
# §3 rows: arm capability / base / inter-arm; timeout order rewrite; ceiling; acceptance record
d.insert_after_line("| `resource_availability.control` で True の `ee_left` / `ee_right` ごとに", "| schema 1.0 では `resource_availability.control` の `ee_left` / `ee_right` / `gripper_left` / `gripper_right` が全て True（DUAL-ARM cell の**能力**の宣言・RS71 §0 #1。⚠ every motion で両腕が活動する適合性は本検査の外 = OPP-17）（v0.2.5・OPP-15 B+） | `P_ARM_CAPABILITY_MISSING` |\n| 各 `arms[].base_transform_id` が `kinematic_layout` artifact 内の entry に解決し、`arms[].gripper_resource_id` が arms 内で一意（v0.2.5） | `P_ARM_BASE_UNBOUND` / `P_ARM_COVERAGE` |\n| `inter_arm_restrictions.min_separation_m > 0` ∧ pairwise keep-out または swept-volume predicate が ≥ 1（content hash は 05 §3.4 (j) の照合対象）（v0.2.5） | `P_INTER_ARM_RESTRICTION_MISSING` |")
d.repline("| `RuntimeTimeouts` の相対順序（v0.2.3・CD-01）:", "| `RuntimeTimeouts` の相対順序（v0.2.3・CD-01・v0.2.5 " + RS + "）: `safety_heartbeat_timeout_s ≤ command_deadline_s`；`inter_command_jitter_s < 1 / action_rate_hz`（LEARNED expectation ごと）；`decision_max_age_s` は順序ではなく 05 `effective_expires_at` と CAS 条件 6 で扱う（旧 `≤ permit_ttl_s` は撤回 — 発行時有効・消費時失効の穴）；`permit_ttl_s ≤ boundary_dwell_s`；`ack_validity_s ≤ boundary_dwell_s`；`ack_timeout_s ≤ boundary_dwell_s`；`max_reselect_attempts × worst_case_attempt_s + selector_overhead_s ≤ boundary_dwell_s`（worst_case / overhead は timing baseline の値）；`health_confirm_timeout_s < lease_max_duration_s`（同時満了を避ける）；`lease_max_duration_s ≥ boundary_dwell_s`；`manager_liveness_s ≤ command_deadline_s` | `P_TIMEOUT_ORDER` |\n| 各 `RuntimeTimeouts` 値 ≤ `CellSafetyTimingBaseline.approved_ceiling[field]`（baseline = acceptance record の `timing_baseline_hash` が指す content-addressed artifact・§8.3。評価 = 受理時 + 第 2 評価点）（v0.2.5・OPP-11） | `P_TIMEOUT_CEILING` |\n| end-to-end 予算: `safety_heartbeat_timeout_s + detection + gateway 切替 + measured stop time ≤ baseline.safety_response_budget_s`（measured 値は CONTROLLER_ENVELOPE_MEASUREMENT / FAULT_INJECTION_RESULT の実測 artifact）（v0.2.5・OPP-11） | `P_SAFETY_BUDGET_EXCEEDED` |")
d.rep("絶対上限、および `ack_timeout_s ≤ boundary_dwell_s` / `health_confirm_timeout_s ≤ lease_max_duration_s` の追加順序（verifier V2 = Rs 確認事項）は OPP-11 | `P_TIMEOUT_ORDER` |", "| `P_TIMEOUT_ORDER` |") if False else None
# §5 (b): CLOSED_LOOP deadline-bound
d.resub(r"\(b\) calibration 期限切れ・deployment evidence 失効は \*\*活性 lease 中には検出されない\*\*.*?周期再評価を manager に持たせるかは 05 OP-19（未裁定）。",
        "(b) calibration 期限切れ・deployment evidence 失効・acceptance 期限（v0.2.5・" + RS + "・OP-19）: **CLOSED_LOOP_AUTHORITY lease では次 permit まで待たない**。permit 発行時に既知の期限を manager clock へ変換した `validity_deadline_mono` を lease に束縛し、到達 = 05 TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)（安全機能・TCP・停止性能に関わる失効は SAFE_STOP へ強化）。期限に現れない変更（incident・tool 交換・firmware 更新・layout revision・ISL build 変更・profile SUSPENDED / REVOKED）は `DeploymentValidityMonitor` の event で即時無効化。周期診断は timing baseline（§8.3）が定める drift / proof-test 項目のみ。SHADOW_NON_AUTHORITY lease は actuation が無いため次 permit 評価で可。")
d.rep("| PT-13 | 受理済 profile の calibration が失効 | profile 不変。活性 lease は TERMINAL boundary または `lease_max_duration_s` まで継続（lease 中の検出点なし・曝露 ≤ 1 skill かつ ≤ lease_max_duration_s・v0.2.2 B-M7・v0.2.3 CD-10・05 OP-19）。", "| PT-13 | 受理済 profile の calibration が失効 | profile 不変。CLOSED_LOOP lease は `validity_deadline_mono` 到達で TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED)（TCP calibration なら SAFE_STOP・05 R_CALIBRATION_EXPIRED_ACTIVE・v0.2.5 OP-19）。SHADOW lease は次 permit まで継続（曝露 = actuation 無し）。")
# §6.1: negative controls + timeout evidence content
d.rep("deployment_evidence_policy_hash = H_WCJ(DeploymentEvidencePolicy)", "MIN_NEGATIVE_CONTROLS（CLOSED_LOOP_AUTHORITY 前・v0.2.5 OPP-15 B+ / OPP-11）= FAULT_INJECTION_RESULT with subject_ref ∈ {CELL#ARM_SWAP, CELL#ARM_MISSING, CELL#BASE_TRANSFORM_TAMPER, CELL#INTER_ARM_COLLISION, ENV#CLOCK_ANOMALY, ENV#SCHEDULER_STALL, ENV#COMM_LOSS}\n#   期待結果 = 拒否 / SafeHold / SafeStop に baseline の予算内で到達。timeout 駆動 code の FAULT_INJECTION_RESULT artifact は worst-case 負荷下の「検出 → SafeHold / SafeStop 到達」実測上限を含み、P_SAFETY_BUDGET_EXCEEDED の入力になる\ndeployment_evidence_policy_hash = H_WCJ(DeploymentEvidencePolicy)")
# §8.1 rule (2): replace 2-set registry sentence with §8.3 pointer
d.rep("registry の状態 = {ACCEPTED, REVOKED}: 失効（revocation）は `clearance_roles` の role による `RuntimeAuditRecord`（kind = CLEARANCE_RECORDED・payload に revoked profile_hash）で行い、05 §3.4 (i) は `∉ revoked_profiles` を要求する。cell の変更（layout / tooling / incident）後に旧 profile が permit 可能なまま残る経路を閉じる（v0.2.4・R2-08）。", "registry と受理・失効の手続は §8.3（v0.2.5・" + RS + "・旧 v0.2.4 の 2 集合 accepted / revoked は `ProfileAcceptanceRecord` に置換）。")
# §8.3 new section before §9
d.insert_before_line("## 9. 主張しないこと（境界）", """### 8.3 ProfileRegistry と ProfileAcceptanceRecord（v0.2.5・""" + RS + """）

```python
class AcceptanceState(Enum):     PROPOSED | ACCEPTED | SUSPENDED | REVOKED     # REVOKED は終端。再使用 = 新 generation の新 record のみ

@dataclass(frozen=True)
class ProfileAcceptanceRecord:            # 不変・append-only。record_hash = H_WCJ(本 record)
    profile_hash: str
    generation: int                        # 同一 profile_hash の受理世代（再受理ごとに +1）
    state: AcceptanceState
    allowed_lease_modes: tuple[LeaseMode, ...]        # SHADOW_NON_AUTHORITY / CLOSED_LOOP_AUTHORITY（05）
    validator_hash: str                    # 受理時に用いた P_* validator 版の content hash
    evidence_set_hash: str                 # 受理時に照合した DeploymentEvidenceRecord 集合の hash
    timing_baseline_hash: str              # CellSafetyTimingBaseline（下記）の content hash — profile preimage には入れない（反循環）
    cell_identity_hash: str                # CellIdentity（layout_revision_ref・kinematic_layout を含む）の hash
    approvals: tuple[tuple[str, str, str], ...]        # (role, operator_ref, t_iso8601)
    valid_until_iso8601: str               # 受理の有効期限（None 不可）
    supersedes_record_hash: str | None     # 前 generation / 前 state の record

@dataclass(frozen=True)
class CellSafetyTimingBaseline:           # RT0 / cell safety court が発行する content-addressed artifact（OPP-16）。本 doc は値を持たない
    baseline_id: str
    approved_ceiling: dict                 # RuntimeTimeouts の全 field → 上限 [s]（int field は回数）
    safety_response_budget_s: CanonicalDecimal
    worst_case_attempt_s: CanonicalDecimal
    selector_overhead_s: CanonicalDecimal
    diagnostic_items: tuple[tuple[str, CanonicalDecimal, CanonicalDecimal], ...]   # (項目, 周期 [s], worst-case detection [s]) — OP-19 の周期診断はこの項目のみ
```

- **状態遷移**: PROPOSED → ACCEPTED（受理）; ACCEPTED → SUSPENDED（一時停止・one-key fail-safe）; SUSPENDED → ACCEPTED は**新 generation の新 record**（原因除去 evidence + two-key）でのみ; ACCEPTED / SUSPENDED → REVOKED（終端）。旧 record は削除しない（append-only）。
- **受理の権限**: 全 `P_*` = 0 は必要条件。SHADOW_NON_AUTHORITY のみを許す受理 = cell commissioning 担当 + 独立 reviewer。CLOSED_LOOP_AUTHORITY を許す受理 = 「独立 safety approver」と「deployment / operations custody approver」の **two-key**。cell operator 単独では CLOSED_LOOP を許可できない。
- **失効の権限（非対称）**: incident・ISL 異常・layout / tool / controller / safety-layer identity の変更のいずれでも、認可された一者または自動 monitor（05 DeploymentValidityMonitor）が即時 SUSPENDED にできる。解除は上記の再受理のみ。
- **05 との結線**: permit は `acceptance_record_hash` / `generation` を束縛し（05 §3.4 (i)）、CAS 条件 12 で `state == ACCEPTED ∧ 同一 generation ∧ mode ∈ allowed_lease_modes` を再検査する。SUSPENDED / REVOKED は pending permit を VOID にし、活性 CLOSED_LOOP lease を SafeHold（安全起因なら SafeStop）へ移す（05 §3.7）。
- **所在**: registry は AuthorityManager と論理的に分離する（同一 transactional DB を使う場合も namespace・ACL・journal writer を分ける）。AuthorityManager は read-only consumer。registry を復元できない場合、process は診断用 SAFEHOLD で起動してよいが permit 発行・CAS・actuation は全面拒否（05 `R_REGISTRY_UNAVAILABLE`）。
- **反循環**: `timing_baseline_hash` と `acceptance_record_hash` は profile の preimage に入らない（profile_hash → record → baseline の一方向）。
- 検査: record の必須 field 欠落・generation 非単調・CLOSED_LOOP 許可で two-key 不足・`valid_until` None = `P_ACCEPTANCE_RECORD_INVALID`（受理拒否）。
""")
# §8.1 code list
cl = d.line("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`"); d.repline("`P_INTRINSIC_OVERRIDE` / `P_RATE_MISMATCH`", cl + " / `P_ARM_CAPABILITY_MISSING` / `P_ARM_BASE_UNBOUND` / `P_INTER_ARM_RESTRICTION_MISSING` / `P_TIMEOUT_CEILING` / `P_SAFETY_BUDGET_EXCEEDED` / `P_ACCEPTANCE_RECORD_INVALID`（v0.2.5）")
# PT rows
d.insert_after_line("| PT-32 |", "| PT-33 | `ee_right = False` の profile（v0.2.5） | `P_ARM_CAPABILITY_MISSING`（schema 1.0 は DUAL-ARM cell 能力必須） |\n| PT-34 | 両 arm に同じ `gripper_resource_id`（v0.2.5） | `P_ARM_COVERAGE` |\n| PT-35 | `safety_heartbeat_timeout_s` を baseline ceiling の 2 倍で宣言（v0.2.5） | `P_TIMEOUT_CEILING` |\n| PT-36 | 全 timeout を同率で 100 倍（相対順序は維持）（v0.2.5） | `P_TIMEOUT_CEILING`（順序検査だけでは通る — CD-01 / GPT 前提訂正 4） |\n| PT-37 | cell operator 単独の approvals で CLOSED_LOOP を許す record（v0.2.5） | `P_ACCEPTANCE_RECORD_INVALID` |\n| PT-38 | 登録後に kinematic layout artifact の base transform を改変（v0.2.5） | 次 permit で 05 `R_PROFILE_MISBOUND`（(j)）・negative control CELL#BASE_TRANSFORM_TAMPER |")
# OPP rows
d.repline("| OPP-11 |", "| OPP-11 | **" + RS + "**: 絶対上限は本 doc に書かず、RT0 / cell safety court が発行する content-addressed `CellSafetyTimingBaseline`（§8.3）を唯一の ceiling source とし `P_TIMEOUT_CEILING` / `P_SAFETY_BUDGET_EXCEEDED` で検査。追加順序（`ack_timeout_s ≤ boundary_dwell_s` 等）は採用、`decision_max_age_s ≤ permit_ttl_s` は撤回し 05 `effective_expires_at` へ。**残 open** = baseline の発行主体・改訂手続（OPP-16） | §3・§8.3・05 OP-20 | 裁定反映済・値は baseline |")
d.repline("| OPP-13 |", "| OPP-13 | **" + RS + "**: append-only `ProfileRegistry` + 不変 `ProfileAcceptanceRecord`（PROPOSED / ACCEPTED / SUSPENDED / REVOKED・generation）。CLOSED_LOOP 受理 = two-key（独立 safety approver + custody approver）、SUSPENDED = one-key fail-safe、CAS で再検査、registry 不読 = actuation 拒否。**残 open** = 各 role の実名（pS / pY 等）の割当 | §8.3・05 §3.4 (i)・§3.5 条件 12 | 裁定反映済・role の実名は Rs |")
d.repline("| OPP-15 |", "| OPP-15 | **" + RS + "**: 案 B+ を採用 — `ArmSpec` に加え `CellKinematicLayoutRef`（両 arm の base transform・collision model）と `InterArmRestrictionSet`（min separation・pairwise keep-out・swept-volume predicate）を content-addressed に束縛し、schema 1.0 は DUAL-ARM cell 能力（両 EE・両 gripper）を必須化。案 A（単一 robot 限定）は不採用。不変前提への影響なし（DUAL-ARM を単腕化せず、88 mm span / 固定 base を変更しない）。⚠ 案 B/B+ の採用だけで「DUAL-ARM 充足済み」と宣言しない（OPP-17） | RS71 §0・§2.1・§3・05 §4.3 | 裁定反映済 |")
d.insert_after_line("| OPP-15 |", "| OPP-16 | `CellSafetyTimingBaseline` の発行主体（RT0 / cell safety court）・改訂手続・ceiling 値の根拠（cell ごとの risk assessment）。本 doc は hash 束縛と検査だけを持つ（v0.2.5・OPP-11） | §8.3・05 OP-20 | RT0 へ carry |\n| OPP-17 | 「every motion で両腕が保持・操作する」（RS71 §0 #1）の実行適合性検査。本 doc は両腕**能力**の存在と arm 間の静的制約までを検査し、合成・実行適合性は composition / runtime 検査の court に残す（v0.2.5・OPP-15 B+） | §7・05 OP-21 | 主張しない |")
# §11 table
tbl = [f"- **v0.2.5 fold（{NOW}）— " + RS + "**: 推奨 4 件を全件採用（前提訂正 5 点は照合済・全て正）。凍結 schema delta = 0:", "", "| 項目 | 内容 | 変更節 |", "|---|---|---|",
 "| 裁定 OPP-15 B+ | `CellKinematicLayoutRef`・`ArmSpec.base_transform_id` / `gripper_resource_id`・`InterArmRestrictionSet`・DUAL-ARM 能力必須・negative controls | §2.1・§2.2・§3（`P_ARM_CAPABILITY_MISSING` / `P_ARM_BASE_UNBOUND` / `P_INTER_ARM_RESTRICTION_MISSING`）・§6.1 MIN_NEGATIVE_CONTROLS・PT-33 / 34 / 38・OPP-15 / 17 |",
 "| 裁定 OPP-11 | `CellSafetyTimingBaseline`（外部・content-addressed）・`P_TIMEOUT_CEILING` / `P_SAFETY_BUDGET_EXCEEDED`・順序の追加 2 件 + `decision_max_age_s ≤ permit_ttl_s` 撤回 | §3・§8.3・PT-35 / 36・OPP-11 / 16 |",
 "| 裁定 OPP-13 | `ProfileRegistry` + `ProfileAcceptanceRecord`（state / generation / two-key）・`P_ACCEPTANCE_RECORD_INVALID` | §8.1 (2)・§8.3・PT-37・OPP-13 |",
 "| 裁定 OP-19 | CLOSED_LOOP lease の validity deadline + event 無効化 + 根拠付き周期診断（SHADOW は次 permit） | §5 (b)・PT-13・§8.3 diagnostic_items |"]
d.insert_before_line("## 12. Review anchors", "\n".join(tbl) + "\n")
d.save()
for name in ("07_SUCCESSOR_CONTRACT_DECISION_20260903.md", "04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md", "08_INDEPENDENT_REVIEW_PLAN_20260903.md"):
    d = Doc(name); d.rep("(v0.2.4 REVIEW CANDIDATE)", "(v0.2.5 REVIEW CANDIDATE)"); d.rep("REVIEW CANDIDATE v0.2.4（", "REVIEW CANDIDATE v0.2.5（"); d.save()
print("NOW =", NOW)
