#!/usr/bin/env python3
"""v0.2.9 -> v0.2.10 fold: reflect the Rs decision of 2026-09-06 (RS-1 OPP-18 cell-id custody / RS-2 R7-04 stop retention / RS-3 OPP-16 clock / RS-4 08 §5 trace verification).
Records-only; frozen files untouched; zero frozen-schema delta. Gated by decision items (all applied) — verification is post-hoc (trace_eval + verifier V10).
Usage: python3 fold_v0210.py <PKG_DIR>"""
import sys, subprocess
P = sys.argv[1]
NOW = subprocess.check_output(["date", "-u", "+%Y-%m-%d %H:%M UTC"]).decode().strip()
RSD = "`review_records/rs_consult/RS_DECISION_20260906.md`"
class Doc:
    def __init__(self, name): self.name = name; self.t = open(f"{P}/{name}", encoding="utf-8").read()
    def rep(self, old, new, count=1):
        n = self.t.count(old); assert n == count, (self.name, old[:90], n); self.t = self.t.replace(old, new)
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
def gate(i): applied.append(i); return True

# ======================================================================= 05
d = Doc("05_WMSO_RUNTIME_SPEC_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("RUNTIME SPEC (v0.2.9 REVIEW CANDIDATE)", "RUNTIME SPEC (v0.2.10 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.9（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.8 → v0.2.9 = ", f"- status: **REVIEW CANDIDATE v0.2.10（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.9 → v0.2.10 = Rs 裁定 2026-09-06（RS-1 OPP-18 cell id custody / RS-2 R7-04 停止保持 / RS-3 OPP-16 時計・{RSD}）の反映（§13・レビュー finding の fold ではなく human 裁定の反映。v0.2.10 本文への再レビューは未実施）。旧版の系譜: — v0.2.8 → v0.2.9 = ")
d.rep("**外部レビュー（GPT-astra GA → V9）の fold = 本版 v0.2.9（§13）**", "外部レビュー（GPT-astra GA → V9）の fold = v0.2.9（2026-09-06 08:41 UTC）→ **Rs 裁定 2026-09-06 の反映 = 本版 v0.2.10（§13）**")
newT = []; newINV = []; newOP = []
def addT(txt): newT.append("| T-%d | %s |" % (55 + len(newT), txt))
def addINV(txt): newINV.append("| INV-%d | %s |" % (37 + len(newINV), txt))
def addOP(txt): newOP.append("| OP-%d | %s |" % (23 + len(newOP), txt))

# ---------------- RS-1（OPP-18）: 正規 (site_id, cell_id)・CellLedger・cell 停止と解除
if gate("RS-1"):
    d.rep("baseline registry の head(cell_id)（不一致 = `R_PROFILE_SUSPENDED`・trigger PERMIT | CAS_COND12・sub BASELINE_SUPERSEDED・v0.2.8 R7-15 / R8-01））",
          "baseline registry の head((site_id, cell_id))（key = 正規 `(site_id, cell_id)`・cell_id 単独では引かない・v0.2.10 RS-1。不一致 = `R_PROFILE_SUSPENDED`・trigger PERMIT | CAS_COND12・sub BASELINE_SUPERSEDED・v0.2.8 R7-15 / R8-01））")
    d.rep("（兄弟 profile による迂回を閉じる。v0.2.7 R5-12: 述語を head 状態に固定し、条件 12 と head-check にも同じ節を置く）",
          "（兄弟 profile による迂回を閉じる。v0.2.7 R5-12: 述語を head 状態に固定し、条件 12 と head-check にも同じ節を置く）。**cell 停止（v0.2.10・RS-1・Rs 裁定 2026-09-06 §1）**: doc 06 §8.3 `CellLedger` で profile の宣言（正規 id または alias）を正規 `(site_id, cell_id)` に解決し（解決不能 = doc 06 `P_CELL_ID_UNRESOLVED` = `R_PROFILE_MISBOUND`）、その正規 id に**未解消**の `CellStopRecord`（= 有効な `CellClearanceRecord` の無い stop・`predecessors` から継承した stop を含む）があれば `R_PROFILE_SUSPENDED`（sub CELL_STOP_UNRESOLVED・trigger PERMIT | CAS_COND12 | HEAD_CHECK | EVENT）。新 profile / 新 generation の ACCEPTED / alias の追加は cell 停止を解除しない（解除 = ledger の独立二者 clearance のみ・profile 受理とは別操作）。ledger 不読 = `R_REGISTRY_UNAVAILABLE`・permit 不発行（TRANSFER_TO_SAFEHOLD は ledger 非依存）")
    d.rep("∧ 同一 (site_id, cell_id) の他 profile の head record に state ∈ {SUSPENDED, REVOKED} が無い（GA-04） ∧ record.role_registry_hash == role registry の現 head（R6-05）∧ record.timing_baseline_hash == baseline registry の head(cell_id)（R7-15 / R8-01）`",
          "∧ 同一 (site_id, cell_id) の他 profile の head record に state ∈ {SUSPENDED, REVOKED} が無い（GA-04） ∧ doc 06 §8.3 CellLedger に正規 (site_id, cell_id) の未解消 CellStopRecord が無い（v0.2.10 RS-1・sub CELL_STOP_UNRESOLVED・ledger 不読 = R_REGISTRY_UNAVAILABLE） ∧ record.role_registry_hash == role registry の現 head（R6-05）∧ record.timing_baseline_hash == baseline registry の head((site_id, cell_id))（R7-15 / R8-01・key = 正規 id・RS-1）`")
    d.rep("| any（SAFEHOLD 中も周期実行: lease を要する副場合 (a)(e)(f) は N/A = True", "| any（SAFEHOLD 中も周期実行: lease を要する副場合 (a)(e)(f)(g) は N/A = True")
    d.rep("(e) cell_id の baseline registry head ≠ `record.timing_baseline_hash`（R6-10）; (f) role registry の head ≠ `record.role_registry_hash`（v0.2.8 R7-03 / R8-15） ||",
          "(e) 正規 (site_id, cell_id) の baseline registry head ≠ `record.timing_baseline_hash`（R6-10・key = (site_id, cell_id)・v0.2.10 RS-1）; (f) role registry の head ≠ `record.role_registry_hash`（v0.2.8 R7-03 / R8-15）; (g) doc 06 §8.3 CellLedger に lease の正規 (site_id, cell_id) の未解消 CellStopRecord がある（monitor 非依存・ledger の読みは (b) と同じ線形化読み・不読 = (b) と同形・v0.2.10 RS-1） ||")
    d.rep("(f) = ROLE_REGISTRY_SUPERSEDED 行（HOLD）。(c)(d) の disposition は起草既定", "(f) = ROLE_REGISTRY_SUPERSEDED 行（HOLD）; (g) = `CellStopRecord.disposition`（doc 06 §5 (b) CELL_STOP 行・欠落 = SAFE_STOP）。(c)(d) の disposition は起草既定")
    d.rep("(f) R_PROFILE_SUSPENDED（HEAD_CHECK・sub = ROLE_REGISTRY_SUPERSEDED）, DISPOSITION |", "(f) R_PROFILE_SUSPENDED（HEAD_CHECK・sub = ROLE_REGISTRY_SUPERSEDED）; (g) R_PROFILE_SUSPENDED（HEAD_CHECK・sub = CELL_STOP_UNRESOLVED）, DISPOSITION |")
    d.rep("| any (EXECUTOR) | DeploymentValidityMonitor の失効 event = registry に `SUSPENDED(reason)` record を append した**後**の通知（reason ∈ doc 06 §8.3 `SuspensionReason`・v0.2.6 R4-11: 記録なしの event は無い。event は profile_hash + 停止対象 ACCEPTED record の hash（PROPOSED を透過・§3.5・v0.2.9 GA-05）+ SUSPENDED record 自身の hash を運ぶ） |",
          "| any (EXECUTOR) | DeploymentValidityMonitor の失効 event = registry に `SUSPENDED(reason)` record を append した**後**の通知（reason ∈ doc 06 §8.3 `SuspensionReason`・v0.2.6 R4-11: 記録なしの event は無い。event は profile_hash + 停止対象 ACCEPTED record の hash（PROPOSED を透過・§3.5・v0.2.9 GA-05）+ SUSPENDED record 自身の hash を運ぶ）／ doc 06 §8.3 CellLedger に `CellStopRecord` を append した**後**の通知（reason = CELL_STOP・event は正規 (site_id, cell_id) + stop_id + disposition を運ぶ・対象 = その cell の全活性 lease・v0.2.10 RS-1） |")
    d.rep("| SAFE_STOP | 同上 | profile が定義する operator / health-check clearance（doc 06）。runtime は自ら解除しない |",
          "| SAFE_STOP | 同上 | profile が定義する operator / health-check clearance（doc 06）。runtime は自ら解除しない。cell 停止（doc 06 §8.3 CellLedger の未解消 `CellStopRecord`）起因なら、加えて ledger の `CellClearanceRecord`（独立した二者・profile 受理とは別操作・v0.2.10 RS-1）が無い限り §3.4 (i) / 条件 12 が拒否する = runtime も profile 再受理も解除できない |")
    d.rep("`R_PROFILE_SUSPENDED` の payload `sub` 語彙 = SUSPENDED | REVOKED | GENERATION_SUPERSEDED | SIBLING_SUSPENDED | SIBLING_REVOKED | BASELINE_SUPERSEDED | ROLE_REGISTRY_SUPERSEDED；",
          "`R_PROFILE_SUSPENDED` の payload `sub` 語彙 = SUSPENDED | REVOKED | GENERATION_SUPERSEDED | SIBLING_SUSPENDED | SIBLING_REVOKED | BASELINE_SUPERSEDED | ROLE_REGISTRY_SUPERSEDED | CELL_STOP_UNRESOLVED（v0.2.10 RS-1）；")
    addOP("SAFEHOLD 中（lease 無し）の cell 停止の評価経路: head-check (g) は lease の cell を要するため SAFEHOLD 中は N/A。cell 停止中の disposition 強化は §3.7 の CELL_STOP event 行（INV-30 強化・記録付き no-op）が担い、次の permit は §3.4 (i) が拒否する。manager 自身の cell 帰属（lease 無しで自 cell の停止を読む経路）は未定義（v0.2.10・RS-1） | doc 06 §8.3 CellLedger | 後継版で定義・未")
    addT("正規 (site_id, cell_id) に未解消 CellStopRecord（disposition SAFE_STOP）が append され monitor event 到達（v0.2.10） | CELL_STOP event 行 → TRANSFER_TO_SAFEHOLD(VALIDITY_EXPIRED \\| SAFE_STOP)・R_PROFILE_SUSPENDED（EVENT・sub CELL_STOP_UNRESOLVED）")
    addT("cell 停止中に profile を two-key で ACCEPTED(gen+1) へ再受理し permit → CAS（v0.2.10） | clearance 無し = (i) / 条件 12 の cell 停止節で R_PROFILE_SUSPENDED（CELL_STOP_UNRESOLVED）・permit 不発行 / REJECTED（再受理は解除ではない）")
    addT("profile が alias で cell を宣言し、alias の正規 id に未解消 stop（v0.2.10） | ledger で正規 id に解決してから照合 = 同上で拒否；alias 未登録 / 曖昧 = doc 06 P_CELL_ID_UNRESOLVED = R_PROFILE_MISBOUND")
    addT("CellLedger 不読で permit 要求 / TRANSFER_TO_SAFEHOLD（v0.2.10） | permit = R_REGISTRY_UNAVAILABLE・不発行；TRANSFER_TO_SAFEHOLD は ledger 非依存で成立")

# ---------------- RS-2（R7-04）: manager 不読 = 停止状態の保持（常時 SafeStop ではない）・latch の解除条件
if gate("RS-2"):
    d.rep("+ `stop_latch`（gateway 自身が (i′) で SafeStop を出した時点で True・durable 不要・v0.2.9 GA-01） |",
          "+ `stop_latch`（gateway 自身が (i′) で SafeStop を出した時点で `(True, stop_report_id, latch 時観測 seq)`・**gateway 局所 durable**（起動時に復元・復元不能 = latched 扱い・v0.2.10 RS-2。v0.2.9 の「durable 不要」は撤回）・v0.2.9 GA-01）+ `safehold_path_verified`（§5.1 の controller 側 hold 経路の直近 `manager_liveness_s` 内の readback・v0.2.10 RS-2） |")
    d.rep("解除は線形化読みで seq > latch 時観測 seq の SAFEHOLD state を観測したとき（= manager の TRANSFER_TO_SAFEHOLD(SAFETY) が線形化済）のみ — 以後は (iii) の `safehold_disposition == SAFE_STOP` 規則が §5.4 clearance まで SafeStop を担う。heartbeat が戻っても manager 不読 / SAFETY CAS 未線形化なら SafeStop を維持し (ii) を再開しない。gateway は (i′) の観測を R_MANAGER_UNAVAILABLE 行と同形で manager へ報告する = manager が欠落を独立観測していない場合の SAFETY CAS の起点）",
          "解除は線形化読みで `owner.kind == SAFEHOLD ∧ safehold_disposition == SAFE_STOP ∧ stop_report_id ∈ state.stop_report_acks` を観測したとき（= manager が**この**停止事象を引き受け、停止要求が途切れず SAFE_STOP として保持されている・v0.2.10 RS-2・Rs 裁定 2026-09-06 §2）のみ — 以後は (iii) の `safehold_disposition == SAFE_STOP` 規則が §5.4 clearance まで SafeStop を担う。heartbeat 復帰・link 復旧・無関係な seq 増加（ack を伴わない SAFEHOLD 遷移・HOLD disposition の SAFEHOLD を含む）・gateway 再起動（durable latch を復元）では解除しない（v0.2.9 の「seq > latch 時観測 seq の SAFEHOLD」条件は撤回・RS-2）。heartbeat が戻っても manager 不読 / ack 未観測なら SafeStop を維持し (ii) を再開しない。gateway は (i′) の観測を `stop_report_id` 付きで manager へ報告する（R_MANAGER_UNAVAILABLE 行と同形）。manager は受領時に TRANSFER_TO_SAFEHOLD(SAFETY | SAFE_STOP)（既に SAFEHOLD なら INV-30 の強化）を線形化し、同一線形化点で `stop_report_acks ∋ stop_report_id` を durable 更新する（= 引継ぎ。ack を伴わない受領は無い・manager が欠落を独立観測していない場合の SAFETY CAS の起点）")
    d.repline("  (iii) else SafeHold（", "  (iii) else（manager 側 disposition・線形化読み）: `state.safehold_disposition == SAFE_STOP` なら SafeStop・それ以外 SafeHold（v0.2.4 R1-03）。線形化読みが `manager_liveness_s` 内に完了しない場合（manager 不読・v0.2.8 R7-04・v0.2.9 GA-01・v0.2.10 RS-2 = Rs 裁定 2026-09-06 §2「常時 SafeStop ではなく停止状態の保持」）は 3 段: (1) `last_disposition == SAFE_STOP ∨ stop_latch` → SafeStop（未解除の停止要求 / 停止状態を保持する。保持するのは停止であって executor の直近 setpoint ではない = (ii) は評価しない）; (2) else if `safehold_path_verified`（§5.1 の controller 側 hold 経路が直近 `manager_liveness_s` 内に確認済） → SafeHold; (3) else → ISL / controller の検証済み停止経路（SafeStop 相当）に委ね、通常指令を通さない。起動直後 = (2) / (3)、durable latch を復元した場合 = (1)（INV-25）。SAFETY 理由でも当該期間の実効 disposition が SAFE_STOP なら clearance record まで SafeStop・v0.2.3 B2-05）")
    d.rep("読みが `manager_liveness_s` 内に完了しない場合、(ii) を評価せず (iii) に落ちる（INV-19・SafeStop / SafeHold は `last_disposition`・R7-04）。",
          "読みが `manager_liveness_s` 内に完了しない場合、(ii) を評価せず (iii) に落ちる（INV-19・SafeStop / SafeHold は (iii) の 3 段規則 `max(last_disposition, stop_latch)` → `safehold_path_verified` → 検証済み停止経路・R7-04・v0.2.10 RS-2）。")
    d.rep("で決める（v0.2.2・B-H1・v0.2.8 R7-04・v0.2.9 GA-01） | R_MANAGER_UNAVAILABLE |",
          "で決め、Stop が無く SafeHold の成立（`safehold_path_verified`）を確認できないときは検証済み停止経路に委ね通常指令を通さない（v0.2.2・B-H1・v0.2.8 R7-04・v0.2.9 GA-01・v0.2.10 RS-2） | R_MANAGER_UNAVAILABLE |")
    d.repline("| INV-25 |", "| INV-25 | CommandGateway の起動直後の出力 = SafeHold（`safehold_path_verified` が取れるまでは検証済み停止経路・§5.2 (iii) (3)）。ただし gateway 局所 durable の `stop_latch` を復元した場合（復元不能を含む）= SafeStop（停止は gateway 再起動でも失われない・v0.2.10 RS-2）。再起動前の lease は新 CAS 無しに再 admit されない（v0.2.1・B-09） | R_GATEWAY_RESTART |")
    d.rep("(ii) は gateway 局所 `stop_latch` の解除（SAFETY CAS の線形化を観測）まで評価されない（v0.2.9 GA-01） |",
          "(ii) は gateway 局所 `stop_latch` の解除（manager の `stop_report_acks ∋ stop_report_id ∧ safehold_disposition == SAFE_STOP` を線形化読みで観測 = 引継ぎ）まで評価されない（v0.2.9 GA-01・v0.2.10 RS-2） |")
    d.rep("出力 = (iii)（`max(last_disposition, stop_latch)` を保持: SAFE_STOP / latch なら SafeStop・R7-04 / GA-01）",
          "出力 = (iii) の 3 段規則（`max(last_disposition, stop_latch)` = SafeStop → `safehold_path_verified` = SafeHold → 検証済み停止経路・R7-04 / GA-01 / v0.2.10 RS-2 = Rs 裁定「停止状態の保持・常時 SafeStop にしない」）")
    d.insert_after_line("    safehold_disposition: RuntimeDisposition | None", "    stop_report_acks: frozenset[str]                  # v0.2.10（RS-2）: manager が引き受けた gateway 発 (i′) 停止報告の stop_report_id 集合。TRANSFER_TO_SAFEHOLD(SAFETY | SAFE_STOP)（既に SAFEHOLD なら INV-30 強化）と同一線形化点で durable 追加・TRANSFER_TO_EXECUTOR で空に戻す。条件 1 の等値比較の対象外（safehold_disposition と同じ扱い）。gateway の latch 解除条件（§5.2 (i′)）が読む")
    d.rep("`SafeStop` = `SafeHold` + profile `ControllerEnvelope` が定義する stop-class 要求。",
          "`SafeStop` = `SafeHold` + profile `ControllerEnvelope` が定義する stop-class 要求。SafeStop は controller / ISL の**検証済み停止経路**への要求であって無条件の電源遮断ではない（把持保持・荷重支持を含む物理的適否 = cell safety 設計の court・doc 06 §9 #7・Rs 裁定 2026-09-06 §2・v0.2.10 RS-2）。**SafeHold の成立確認（`safehold_path_verified`・v0.2.10 RS-2）** = controller 側 hold 経路（上表の凍結 / 保持）の直近 `manager_liveness_s` 内の readback（`GATEWAY_CONFIG_MATCH` と同じ health 経路）。確認不能 = §5.2 (iii) (3)（検証済み停止経路に委ね通常指令を通さない）。")
    d.rep("    EPOCH_TRANSITION | ACK_RECEIVED | PERMIT_ISSUED | PERMIT_CONSUMED | PERMIT_VOIDED |",
          "    EPOCH_TRANSITION | ACK_RECEIVED | PERMIT_ISSUED | PERMIT_CONSUMED | PERMIT_VOIDED | STOP_REPORT_ACKED | CLOCK_REF_UPDATED |   # v0.2.10（RS-2 / RS-3）: STOP_REPORT_ACKED = gateway 発 (i′) 停止報告の引継ぎ（stop_report_id・同一線形化点の AuthorityState.stop_report_acks 更新）; CLOCK_REF_UPDATED = (l) 参照組の明示更新（理由・新旧の対・host_id / boot_id）")
    addINV("gateway の `stop_latch` は manager の引継ぎ（`stop_report_acks ∋ stop_report_id ∧ safehold_disposition == SAFE_STOP` の線形化観測）以外で解除されない（heartbeat 復帰 / link 復旧 / 無関係な seq 増加 / gateway 再起動では解除されない。latch は gateway 局所 durable）（v0.2.10 RS-2） | 設計違反（test）")
    addT("latch 中に manager が ack 無しで SAFEHOLD(DEADLINE_MISS・HOLD) へ遷移（seq > latch 時観測 seq）→ link 復旧（v0.2.10） | 解除条件不成立（ack 無し・HOLD）・SafeStop 維持（v0.2.9 の seq 条件では緩んでいた）")
    addT("latch 中に gateway 再起動 → durable latch 復元（v0.2.10） | INV-25: 起動直後から SafeStop・復元不能でも latched 扱い")
    addT("manager 不読・Stop 無し・`safehold_path_verified` 未取得（v0.2.10） | (iii) (3): 検証済み停止経路に委ね通常指令を通さない（SafeHold を出さない）")
    addT("manager が STOP_REPORT_ACKED を線形化（SAFEHOLD・SAFE_STOP・acks ∋ id）→ gateway が線形化読み（v0.2.10） | latch 解除・出力は manager 側 disposition の SafeStop が §5.4 clearance まで途切れず続く（正常系対照）")

# ---------------- RS-3（OPP-16）: 時計対応の前提・期限変換の余裕・TIME_SYNC・試験用仮値の分離
if gate("RS-3"):
    d.rep("(k) `validity_deadline_mono` と `effective_expires_at` を発行時に導出して permit に固定（v0.2.5・OPP-11 / OP-19。",
          "(k) `validity_deadline_mono` と `effective_expires_at` を発行時に導出して permit に固定（v0.2.5・OPP-11 / OP-19。**暦時刻期限の変換（v0.2.10・RS-3・Rs 裁定 2026-09-06 §3）**: `validity_deadline_mono = mono_ref + (wall_deadline − wall_ref) − baseline.clock_correspondence_margin_s`（基準対 = (l) の有効な参照組・余裕 = 基準時刻の誤差 + 参照組の読取誤差 + 対応を使う期間中のずれの上限・値 = RT0・doc 06 §8.3）。余裕が解決できない / 参照組が無効 = `R_CLOCK_ANOMALY`・permit 不発行。発行後の参照組更新（CLOCK_REF_UPDATED）は本 permit / lease の期限を変えない。")
    d.rep("（基準対 (wall_ref, mono_ref) = 直前の PERMIT_ISSUED payload / 直前の CLOCK_DRIFT 診断で durable に記録した対・評価周期 = diagnostic_items の CLOCK_DRIFT 周期・許容値未解決 / 基準対欠落 = 偽・周期 / worst-case detection を許容値に読み替えない・v0.2.9 GA-07）∧",
          "（基準対 = 参照組 `(wall_ref, mono_ref, host_id, boot_id)` = 直前の PERMIT_ISSUED payload / 直前の CLOCK_DRIFT 診断 / `CLOCK_REF_UPDATED` 記録で durable に記録した対・**有効 ⇔ host_id == manager host ∧ boot_id == 現 boot**（再起動 / サスペンド復帰 / 暦時刻の不連続変更 = 参照組無効 → 再検証 = TIME_SYNC pass の下で理由付き `CLOCK_REF_UPDATED` を記録してから。異常を隠す目的の取り直し禁止 = 直前の drift 判定が偽のままの更新は不可・v0.2.10 RS-3）・評価周期 = diagnostic_items の CLOCK_DRIFT 周期・許容値未解決 / 基準対欠落 = 偽・周期 / worst-case detection を許容値に読み替えない・v0.2.9 GA-07）∧ **TIME_SYNC**（baseline 項目・v0.2.10 RS-3: wall 源の同期状態 == synchronized ∧ 基準時刻の古さ ≤ `baseline.clock_sync_max_ref_age_s` ∧ 推定誤差 ≤ `baseline.clock_sync_error_bound_s`。wall/mono 差の小ささは UTC 正しさの証明ではない・同期 daemon の表示値を保証済み上限とは扱わず RT0 承認上限と比較する・上限未解決 = 偽）∧ 実行時の経過時間（期限 / timeout / age）は AuthorityManager の単調時計のみで測り、暦時刻は evidence / calibration / acceptance の期限照合にのみ使う（INV-38）∧")
    d.rep("(d) drift 項目 = CLOCK_ANOMALY 行（SAFE_STOP）・他の項目 = DIAGNOSTIC_FAILURE 行", "(d) drift / TIME_SYNC 項目 = CLOCK_ANOMALY 行（SAFE_STOP・TIME_SYNC 分は起草既定・Rs が緩和可・v0.2.10 RS-3）・他の項目 = DIAGNOSTIC_FAILURE 行")
    d.rep("(d) drift = R_CLOCK_ANOMALY（DRIFT）・他 = R_EVIDENCE_EXPIRED_ACTIVE", "(d) drift / TIME_SYNC = R_CLOCK_ANOMALY（DRIFT | TIME_SYNC）・他 = R_EVIDENCE_EXPIRED_ACTIVE")
    d.rep("`R_CLOCK_ANOMALY`: PERMIT | DRIFT、", "`R_CLOCK_ANOMALY`: PERMIT | DRIFT | TIME_SYNC（v0.2.10 RS-3）、")
    old = d.line("| OP-20 |"); d.repline("| OP-20 |", old.replace(" | doc 06 OPP-16 | RT0 へ carry |", "。**Rs 裁定 2026-09-06 §3（v0.2.10 RS-3）**: 設計試験用の仮値（drift 許容・値は本 doc に書かない）は `review_records/trace/test_baseline_TEST_ONLY_20260906.json` のみに置き本 doc / 実運用 baseline へ昇格禁止・実運用値は RT0 検証（測定誤差・時計対応の維持可能時間・期限判定に許される誤差）後に承認 = 未承認のまま | doc 06 OPP-16 | RT0 へ carry（未解決値のまま = 解決済と記録しない） |"))
    addINV("実行時の経過時間は AuthorityManager の単調時計のみ。暦時刻 ↔ 単調時刻の変換は (l) の有効な参照組（同 host・同 boot・TIME_SYNC pass）でのみ行い、別 host / 別 boot の単調時刻を変換根拠なしに比較しない。参照組の更新は `CLOCK_REF_UPDATED` として記録し、既存 permit / lease の期限を変えない（(k) は発行時に固定）（v0.2.10 RS-3） | R_CLOCK_ANOMALY")
    addT("baseline に `clock_correspondence_margin_s` が無い / 解決不能で permit 要求（v0.2.10） | (k) 変換不能 = R_CLOCK_ANOMALY・permit 不発行（doc 06 側は P_BASELINE_INCOMPLETE）")
    addT("再起動後（boot_id 変化）に旧参照組で drift 判定が偶然 ≤ 許容（v0.2.10） | 参照組無効（boot_id 不一致）= (l) 偽 = R_CLOCK_ANOMALY・CLOCK_REF_UPDATED（TIME_SYNC pass 下）まで permit 不発行")
    addT("drift ≤ 許容だが wall 源が unsynchronized / 基準時刻が古い / 推定誤差 > 上限（v0.2.10） | TIME_SYNC 偽 = (l) 偽 = R_CLOCK_ANOMALY（TIME_SYNC）・permit 不発行；lease 中は head-check (d) → CLOCK_ANOMALY 行")
    addT("permit 発行後に CLOCK_REF_UPDATED（参照組を先へ）（v0.2.10） | 発行済 permit / lease の validity_deadline_mono は不変（延長も短縮もしない・正常系対照）")

if newINV: d.insert_after_line("| INV-36 |", "\n".join(newINV))
if newT: d.insert_after_line("| T-54 |", "\n".join(newT))
if newOP: d.insert_after_line("| OP-22 |", "\n".join(newOP))
rows05 = [("RS-1", "OPP-18 裁定: 正規 (site_id, cell_id) を全 cell 単位参照の key に統一・CellLedger の未解消 cell 停止を (i) / 条件 12 / head-check (g) / event 行 / §5.4 で照合（profile 再受理では解除されない）", "§3.4 (i)・§3.5 条件 12・§3.7 head-check (g) / CELL_STOP event・§5.4 SAFE_STOP 行・§7 sub 語彙・OP-23・T-55..58"),
          ("RS-2", "R7-04 裁定: manager 不読 = 停止状態の保持（3 段: latch / last_disposition → safehold_path_verified → 検証済み停止経路）・latch の解除 = manager の引継ぎ（STOP_REPORT_ACKED・SAFE_STOP）のみ・latch は gateway 局所 durable・SafeStop ≠ 電源遮断", "§2 gateway 状態・§3.2 AuthorityState.stop_report_acks・§5.1・§5.2 (i′)(iii)・INV-19 / INV-25 / INV-29 / INV-37・§8 AuditKind・失敗表 R_MANAGER_UNAVAILABLE・T-59..62"),
          ("RS-3", "OPP-16 裁定: 期限変換 = mono_ref + (wall_deadline − wall_ref) − 余裕（余裕未解決 = 不発行）・参照組に host_id / boot_id・CLOCK_REF_UPDATED・TIME_SYNC を drift と分離・試験用仮値は test baseline のみ（本文に数値を書かない）", "§3.4 (k)(l)・head-check (d)・§7 trigger 語彙・INV-38・§8 AuditKind・OP-20・T-63..66")]
tbl = [f"- **v0.2.10 fold（{NOW}）— Rs 裁定 2026-09-06（{RSD}）の反映**。レビュー finding の fold ではなく human 裁定の反映。verifier（V10）と trace 検証（`review_records/trace/`・PRE_PINNED D1–D11）は事後。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §13:", "", "| 裁定項目 | 内容 | 変更節 |", "|---|---|---|"]
for i, c, s in rows05: tbl.append(f"| {i} | {c} | {s} |")
tbl.append("| RS-4 | 08 §5 trace 検証の必須化 | doc 08 §5（05 本文の変更なし） |")
tbl.append("| （06 側の fold 行は doc 06 §11） | | |")
d.insert_before_line("## 14. Review anchors", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= 06
d = Doc("06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("DEPLOYMENT PROFILE SPEC (v0.2.9 REVIEW CANDIDATE)", "DEPLOYMENT PROFILE SPEC (v0.2.10 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2.9（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.8 → v0.2.9 = ", f"- status: **REVIEW CANDIDATE v0.2.10（未 bank・two-key 未・gate PASS を主張しない）** — v0.2.9 → v0.2.10 = Rs 裁定 2026-09-06（RS-1 OPP-18 / RS-3 OPP-16 / RS-2 SafeStop の意味・{RSD}）の反映（§11・human 裁定の反映。v0.2.10 本文への再レビューは未実施）。旧版の系譜: — v0.2.8 → v0.2.9 = ")
d.rep("／ v0.2.9 = ", f"／ v0.2.10 = {NOW}（`date -u` 実測）／ v0.2.9 = ")
newPT = []
def addPT(txt): newPT.append("| PT-%d | %s |" % (58 + len(newPT), txt))
if gate("RS-1（06）"):
    old = d.line("class SuspensionReason(Enum):"); assert " | ROLE_REGISTRY_SUPERSEDED   #" in old
    d.repline("class SuspensionReason(Enum):", old.replace(" | ROLE_REGISTRY_SUPERSEDED   #", " | ROLE_REGISTRY_SUPERSEDED | CELL_STOP   #") + "・v0.2.10（RS-1）: CELL_STOP = CellLedger の `CellStopRecord`（cell 全体の停止・disposition は record が運ぶ・§5 (b)）")
    d.rep("class CellIdentity:\n    cell_id: str\n    site_id: str\n", "class CellIdentity:\n    cell_id: str                           # v0.2.10（RS-1）: 正規 id または alias（§8.3 CellLedger で正規 (site_id, cell_id) にちょうど 1 つ解決・不能 = P_CELL_ID_UNRESOLVED）\n    site_id: str                           # v0.2.10（RS-1）: 同上（正規 key = (site_id, cell_id)・cell_id 単独では引かない）\n")
    d.rep("    cell_id: str                           # v0.2.6（R4-10）: == profile.cell.cell_id（不一致 = P_TIMEOUT_CEILING）",
          "    site_id: str                           # v0.2.10（RS-1）: == 正規 site_id（baseline の key = 正規 (site_id, cell_id)・不一致 = P_TIMEOUT_CEILING）\n    cell_id: str                           # v0.2.6（R4-10）: == profile.cell.cell_id の正規 id（不一致 = P_TIMEOUT_CEILING）")
    d.rep("`(site_id, cell_id)` は baseline registry の head(cell_id) と同じ custody（OPP-16）の下で一意（改名 / 別名で未解消停止が消えないための規則 = OPP-18・v0.2.9 GA-04）。",
          "正規 `(site_id, cell_id)` は CellLedger（custody = 設備台帳管理者・OPP-18 裁定・v0.2.10 RS-1）が発行し、baseline registry / ProfileRegistry / 05 の cell 単位参照は全て正規 (site_id, cell_id) を key とする（cell_id 単独では引かない。改名 / 別名で未解消停止が消えない = CellLedger の alias / predecessors 規則・v0.2.9 GA-04）。")
    d.rep("`CellSafetyTimingBaseline` は cell_id ごとに head を持つ content-addressed store に置く（発行主体・改訂手続 = OPP-16）。head の変更 = supersession: monitor は event（BASELINE_SUPERSEDED）を出し、manager は head-check で `head(baseline_registry, cell_id) ≠ record.timing_baseline_hash`",
          "`CellSafetyTimingBaseline` は正規 `(site_id, cell_id)` ごとに head を持つ content-addressed store に置く（発行主体・改訂手続 = OPP-16・key は cell_id 単独ではない・v0.2.10 RS-1。`issuer_ref` が role registry の RT0 issuer でない artifact（試験専用 baseline を含む）は append 不可・RS-3）。head の変更 = supersession: monitor は event（BASELINE_SUPERSEDED）を出し、manager は head-check で `head(baseline_registry, (site_id, cell_id)) ≠ record.timing_baseline_hash`")
    d.insert_after_line("- **role registry（v0.2.7・R6-05 / R6-06）**", "- **CellLedger（設備台帳・v0.2.10・RS-1・Rs 裁定 2026-09-06 §1）**: 物理 cell の正規 id `(site_id, cell_id)` と cell 全体の停止 / 解除を保持する content-addressed・append-only store。custody = Rs が指名する**設備台帳管理者**（role registry の `CELL_LEDGER_CUSTODIAN`・実名 = OPP-18）のみが `CellRecord` を発行 / 付け替える（profile 作成者・AuthorityManager・RT0・本 doc の起草者は発行できない。RT0 は測定 / 検証のみ）。record: `CellRecord{site_id, cell_id, issued_by, t_iso8601, predecessors: tuple[(site_id, cell_id), ...], aliases: tuple[str, ...]}`（正規 id は不変・再利用禁止。表示名の変更 = alias の追加。alias は**ちょうど 1 つ**の正規 id に解決し、未登録 / 曖昧 / 循環 = 拒否 = `P_CELL_ID_UNRESOLVED`。設備の移設 / 統合 = 改名ではなく `predecessors` を持つ新 CellRecord = 旧 id の未解消 stop を継承する移行手続）; `CellStopRecord{stop_id, site_id, cell_id, requested_by_role ∈ {OPERATOR, MAINTAINER, SAFETY_OFFICER, MONITOR}, operator_ref, reason: SuspensionReason, disposition ∈ {HOLD, SAFE_STOP}, t_iso8601, evidence_ref}`（**一者で可能**・二者承認を待たない・`(operator_ref, role) ∈ 現 head の role registry`・disposition は cell safety 設計（OPP-16 の court）が定める規則で要求者が選ぶ・欠落 = SAFE_STOP）; `CellClearanceRecord{stop_id, approvals = ((INDEPENDENT_SAFETY_APPROVER, operator_ref, t), (FACILITY_OPERATIONS_OWNER, operator_ref, t)), cause_removal_evidence_ref, role_registry_hash}`（**独立した二者**: 両 role の operator_ref が相異 ∧ 各 `(operator_ref, role) ∈ 現 head の role registry` ∧ `role_registry_hash == 現 head` ∧ 原因除去の evidence が解決できる。一人が二役を承認した record・未登録の人選 = 無効 = stop は未解消のまま・権限を自動補完しない）。**未解消 stop** := 有効な CellClearanceRecord の無い CellStopRecord（`predecessors` を辿って継承した stop を含む）。**profile の受理と cell 停止の解除は別操作**: 新 profile / 新 generation の ACCEPTED / alias の追加は stop を解除しない。未解消 stop は当該 cell の現在および将来の全 profile に効く（05 §3.4 (i) / 条件 12 / head-check (g)・sub CELL_STOP_UNRESOLVED）。stop の append 後、monitor は event（reason CELL_STOP・05 §3.7）を出し、manager は head-check (g) で monitor 非依存に検出する。ledger は ProfileRegistry と同じ分離規則（namespace / ACL / journal writer）に従い、AuthorityManager は read-only consumer。role 名（CELL_LEDGER_CUSTODIAN / MAINTAINER / SAFETY_OFFICER / INDEPENDENT_SAFETY_APPROVER / FACILITY_OPERATIONS_OWNER）は role registry の語彙（AcceptanceRole enum には足さない）。")
    d.rep("`record.site_id ≠ profile.cell.site_id ∨ record.cell_id ≠ profile.cell.cell_id`（書込時・head 再評価・v0.2.9 GA-04）；",
          "`(record.site_id, record.cell_id) ≠ CellLedger で解決した profile.cell の正規 (site_id, cell_id)`（record は正規 id を持つ・alias 不可・書込時・head 再評価・v0.2.9 GA-04・v0.2.10 RS-1）；")
    d.rep("`timing_baseline_hash ≠ baseline registry の head(cell_id)`（書込時", "`timing_baseline_hash ≠ baseline registry の head((site_id, cell_id))`（key = 正規 id・RS-1・書込時")
    d.rep("解除は上記の再受理のみ。", "解除は上記の再受理のみ（= profile の停止の解除）。cell 全体の停止 = CellLedger の `CellStopRecord`（一者）・解除 = `CellClearanceRecord`（独立二者）であり、profile の再受理では解除されない（v0.2.10 RS-1）。")
    d.rep("OPERATOR / ROLE_REGISTRY_SUPERSEDED（R6-05）→ HOLD。", "OPERATOR / ROLE_REGISTRY_SUPERSEDED（R6-05）→ HOLD；CELL_STOP → `CellStopRecord.disposition`（cell safety 設計が定める・欠落 = SAFE_STOP・v0.2.10 RS-1）。")
    d.rep("`P_TOOL_GEOMETRY_MISMATCH` / `P_BASELINE_INCOMPLETE`（v0.2.7）", "`P_TOOL_GEOMETRY_MISMATCH` / `P_BASELINE_INCOMPLETE`（v0.2.7） / `P_CELL_ID_UNRESOLVED`（v0.2.10）")
    d.rep("= {`P_INTRINSIC_OVERRIDE`, `P_RATE_MISMATCH`,", "= {`P_CELL_ID_UNRESOLVED`（v0.2.10 RS-1・第 1 評価点 + 1b + 第 2 評価点）, `P_INTRINSIC_OVERRIDE`, `P_RATE_MISMATCH`,")
    d.rep("= {`P_TIMEOUT_CEILING`, `P_BASELINE_INCOMPLETE`, `P_ACCEPTANCE_RECORD_INVALID`}", "= {`P_TIMEOUT_CEILING`, `P_BASELINE_INCOMPLETE`, `P_ACCEPTANCE_RECORD_INVALID`, `P_CELL_ID_UNRESOLVED`}")
    d.rep("`P_BASELINE_INCOMPLETE`（R6-08）} — 05 §3.4 (b)", "`P_BASELINE_INCOMPLETE`（R6-08）, `P_CELL_ID_UNRESOLVED`（ledger の alias / 移行は受理後に変わり得る・v0.2.10 RS-1）} — 05 §3.4 (b)")
    d.insert_after_line("| acceptance record が指す `CellSafetyTimingBaseline.diagnostic_items`", "| `cell.site_id` / `cell.cell_id`（正規 id または alias）が §8.3 CellLedger の正規 `(site_id, cell_id)` に**ちょうど 1 つ**解決する（未登録 / 曖昧 / 循環 / ledger 不読 = 違反・第 1 評価点 + record 書込時 + 第 2 評価点）（v0.2.10・RS-1） | `P_CELL_ID_UNRESOLVED` |")
    d.repline("| OPP-18 |", f"| OPP-18 | **Rs 裁定 2026-09-06 §1（v0.2.10 RS-1・{RSD}）**: 正規 id `(site_id, cell_id)` の発行 = Rs が指名する設備台帳管理者のみ（不変・再利用禁止・alias は 1 正規 id に解決・移設 / 統合は predecessors を持つ移行手続で停止義務を継承）；停止 = 認可された一者（運用 / 保守 / 安全 / 自動監視）・解除 = 独立した二者（独立安全承認者 + 設備運用責任者・同一人物の二役不可・未登録 = 拒否）；profile 受理と cell 停止の解除は別操作（新 profile / 新 generation / alias 追加で停止は消えない）；cell 単位参照（baseline 等）の key = 正規 (site_id, cell_id)。**残 open** = 設備台帳管理者 / INDEPENDENT_SAFETY_APPROVER / FACILITY_OPERATIONS_OWNER / MAINTAINER / SAFETY_OFFICER の実名割当（role registry・OPP-13 と同根）・移行手続の evidence 様式・SAFEHOLD 中の cell 帰属（05 OP-23） | §8.3 CellLedger・05 §3.4 (i) / 条件 12 / head-check (g) / §5.4 | 裁定反映済・実名は Rs |")
    d.rep("7. **機能安全の内容**: `SafetyRestrictionSet` / `SAFETY_LAYER_ACCEPTANCE` / `StopClass` の**物理的・規格的内容**は本 doc の外（IndependentSafetyLayer と cell の安全設計の court）。本 doc は「存在・束縛・fail-closed」を要求するのみ。",
          "7. **機能安全の内容**: `SafetyRestrictionSet` / `SAFETY_LAYER_ACCEPTANCE` / `StopClass` の**物理的・規格的内容**は本 doc の外（IndependentSafetyLayer と cell の安全設計の court）。本 doc は「存在・束縛・fail-closed」を要求するのみ。SafeStop / SAFE_STOP を無条件の電源遮断と読み替えない（HOLD / SafeStop の物理的適否 = 把持保持・荷重支持を含む cell safety 設計の court・Rs 裁定 2026-09-06 §2・v0.2.10）。")
    addPT("alias が 2 つの正規 id に解決する / 未登録 / 循環する cell 宣言（v0.2.10） | `P_CELL_ID_UNRESOLVED`（第 1 評価点・record 書込時・第 2 評価点）")
    addPT("未解消 CellStopRecord のある正規 id に対し two-key で ACCEPTED(gen+1) を append（v0.2.10） | record は書ける（受理は評価点）が 05 §3.4 (i) / 条件 12 が CELL_STOP_UNRESOLVED で拒否・clearance 無しに permit 不発行")
    addPT("CellClearanceRecord の両 role を同一 operator_ref が承認（v0.2.10） | clearance 無効（独立二者不成立）・stop は未解消のまま")
    addPT("alias で宣言した profile の正規 id に未解消 stop（v0.2.10） | 正規 id へ解決してから照合 = 05 (i) で CELL_STOP_UNRESOLVED")
    addPT("baseline の `site_id` が正規 site_id と不一致（v0.2.10） | `P_TIMEOUT_CEILING`（baseline は正規 (site_id, cell_id) に束縛）")
if gate("RS-3（06）"):
    old = d.line("    clock_drift_tolerance_s: CanonicalDecimal"); assert "（値 = RT0・本 doc に書かない）" in old
    d.repline("    clock_drift_tolerance_s: CanonicalDecimal", old.replace("（値 = RT0・本 doc に書かない）", "（値 = RT0 承認値のみ・本 doc に書かない。設計試験用の仮値は `review_records/trace/test_baseline_TEST_ONLY_20260906.json` に置き実運用 baseline へ昇格禁止・Rs 裁定 2026-09-06 §3・v0.2.10 RS-3）"))
    d.insert_after_line("    clock_drift_tolerance_s: CanonicalDecimal", "    clock_correspondence_margin_s: CanonicalDecimal   # v0.2.10（RS-3）: 05 §3.4 (k) の期限変換の誤差余裕 [s] = 基準時刻の誤差 + 参照組の読取誤差 + 対応を使う期間中のずれの上限（値 = RT0・本 doc に書かない）。解決不能 = P_BASELINE_INCOMPLETE / 05 R_CLOCK_ANOMALY（permit 不発行）\n    clock_sync_error_bound_s: CanonicalDecimal        # v0.2.10（RS-3）: TIME_SYNC 項目の推定誤差の承認上限 [s]（wall 源の UTC 同期精度・drift 許容とは別の量・値 = RT0）\n    clock_sync_max_ref_age_s: CanonicalDecimal        # v0.2.10（RS-3）: TIME_SYNC 項目の基準時刻の古さの上限 [s]（値 = RT0）\n    issuer_ref: str                              # v0.2.10（RS-3）: 発行主体（RT0 / cell safety court・role registry で資格照合・OPP-16）。試験専用 baseline（issuer_ref = TEST_ONLY_NON_ACTUATING）は registry へ append 不可 = P_BASELINE_INCOMPLETE")
    d.rep("（CLOCK_DRIFT 項目の許容値・v0.2.9 GA-07） | `P_BASELINE_INCOMPLETE` |", "（CLOCK_DRIFT 項目の許容値・v0.2.9 GA-07）、かつ `clock_correspondence_margin_s` / `clock_sync_error_bound_s` / `clock_sync_max_ref_age_s` / `site_id`（正規 id）/ `issuer_ref`（role registry の RT0 issuer・試験専用 artifact は不可）が解決できる（v0.2.10 RS-3 / RS-1） | `P_BASELINE_INCOMPLETE` |")
    d.rep("CONTROLLER_IDENTITY, TOOL_IDENTITY, SAFETY_LAYER_IDENTITY, BASE_POSE_VERIFY}。実行者: VALIDITY_MONITOR_LIVENESS / REGISTRY_HEAD_CHECK / AUDIT_RECORDER_LIVENESS = AuthorityManager（05 §3.7 head-check）、CLOCK_DRIFT = AuthorityManager（05 §3.4 (l)）、",
          "CONTROLLER_IDENTITY, TOOL_IDENTITY, SAFETY_LAYER_IDENTITY, BASE_POSE_VERIFY, TIME_SYNC}（TIME_SYNC・v0.2.10 RS-3）。実行者: VALIDITY_MONITOR_LIVENESS / REGISTRY_HEAD_CHECK / AUDIT_RECORDER_LIVENESS = AuthorityManager（05 §3.7 head-check）、CLOCK_DRIFT / TIME_SYNC = AuthorityManager（05 §3.4 (l)・TIME_SYNC = wall 源の同期状態・基準時刻の古さ・推定誤差を `clock_sync_*` の RT0 上限と比較する。wall/mono 差の検査とは別の量・daemon の表示値を保証済み上限とは扱わない・v0.2.10 RS-3）、")
    d.rep("、`clock_drift_tolerance_s` の値と時計対応の前提（wall 源の同期方式・v0.2.9 GA-07） | §8.3・05 OP-20 | RT0 へ carry |",
          f"、`clock_drift_tolerance_s` の値と時計対応の前提（wall 源の同期方式・v0.2.9 GA-07）。**Rs 裁定 2026-09-06 §3（v0.2.10 RS-3・{RSD}）**: 設計試験用の仮値（drift 許容・非実機・出力なし・値は本 doc に書かない）は `review_records/trace/test_baseline_TEST_ONLY_20260906.json` のみに置き本 doc / 実運用 baseline へ昇格禁止；実運用値（drift 許容・対応余裕・同期誤差上限・基準時刻の古さ・base pose 許容・有効期間・停止応答予算）は RT0 が測定誤差・時計対応の維持可能時間・期限判定に許される誤差を確認するまで**未承認**（未解決値の baseline を指す profile / lease は P_BASELINE_INCOMPLETE / 05 R_CLOCK_ANOMALY で通過しない）；時計対応（wall↔mono・同 host 同 boot・参照組の明示更新・既存期限の不延長）と UTC 同期精度（TIME_SYNC）は別に検証 | §8.3・05 OP-20・05 §3.4 (k)(l) | 裁定反映済・実運用値は RT0（未解決のまま = 解決済と記録しない） |")
    addPT("`clock_correspondence_margin_s` / `clock_sync_*` / `issuer_ref` のいずれかを欠く baseline を指す acceptance record（v0.2.10） | `P_BASELINE_INCOMPLETE`（record 拒否）；05 (k) は余裕未解決 = R_CLOCK_ANOMALY")
    addPT("試験専用 baseline（issuer_ref = TEST_ONLY_NON_ACTUATING）を baseline registry へ append / acceptance record が指す（v0.2.10） | append 拒否・`P_BASELINE_INCOMPLETE`（昇格禁止）")
if newPT: d.insert_after_line("| PT-57 |", "\n".join(newPT))
rows06 = [("RS-1", "OPP-18 裁定: CellLedger（正規 id・alias・predecessors・一者停止・独立二者解除）・cell 単位参照の key = 正規 (site_id, cell_id)・SuspensionReason.CELL_STOP・P_CELL_ID_UNRESOLVED", "§2.1 CellIdentity comment・§3 P_ 表・§5 (b)・§8.1 list / rule (2)・§8.3 SuspensionReason / CellSafetyTimingBaseline.site_id / 所在 / baseline registry / CellLedger / P_ACCEPTANCE_RECORD_INVALID / 失効の権限・§9 #7・OPP-18・PT-58..62"),
          ("RS-3", "OPP-16 裁定: baseline に対応余裕・同期誤差上限・基準時刻の古さ・issuer_ref を追加・TIME_SYNC を必須項目に・試験用仮値は test baseline のみ・実運用値は未承認", "§8.3 CellSafetyTimingBaseline・REQUIRED_DIAGNOSTIC_ITEMS・§3 P_BASELINE_INCOMPLETE・OPP-16・PT-63..64")]
tbl = [f"- **v0.2.10 fold（{NOW}）— Rs 裁定 2026-09-06（{RSD}）の反映**。human 裁定の反映（レビュー finding の fold ではない）。verifier（V10）と trace 検証は事後。記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md` §13:", "", "| 裁定項目 | 内容 | 変更節 |", "|---|---|---|"]
for i, c, s in rows06: tbl.append(f"| {i} | {c} | {s} |")
tbl.append("| RS-2 | 05 側（§5.2 (iii) 3 段・latch 解除条件）。本 doc は §9 #7 の SafeStop の意味のみ | doc 05 §13 |")
d.insert_before_line("## 12. Review anchors", "\n".join(tbl) + "\n")
d.save()

# ======================================================================= 08（RS-4）+ 04 / 07 label bumps
d = Doc("08_INDEPENDENT_REVIEW_PLAN_20260903.md")
d.rep("(v0.2.9 REVIEW CANDIDATE)", "(v0.2.10 REVIEW CANDIDATE)"); d.rep("REVIEW CANDIDATE v0.2.9（", "REVIEW CANDIDATE v0.2.10（")
if gate("RS-4（08）"):
    d.insert_before_line("- 同じ finding が再発した場合は根本原因（型・順序・語彙）を直す。回数上限で止めない。", f"- **trace 検証（必須・v0.2.10・Rs 裁定 2026-09-06 §4・{RSD}）**: trace = 入力・障害・状態遷移の時系列。各 finding / 裁定について (1) 初期状態・入力・事象の順序・満たすべき規範・期待結果を trace spec に記録し sha256 で固定する（期待結果の根拠 = 設計上の要求。修正後の本文 / 評価器の挙動から逆算しない。固定は本文編集より**前**に commit し順序を git 履歴で証明する）; (2) 同じ期待結果で修正前後を評価し、修正前で指摘した違反が現れ修正後で消えることを確認する（修正前でも満たす trace = 指摘の誤り / 前提不足 / モデル不足を再検討し regression control と記す）; (3) 正常系を対照として確認する（全操作を拒否するだけの修正は合格にしない。期待結果を変えるときは元の spec を上書きせず理由と新版を残す）。artifact = `review_records/trace/`（手続 = 同 dir `README.md`・spec = `TRACES_*.json`・pin = `PIN_*.sha256`・評価器 = `trace_eval.py`・結果 = `RESULTS_*.json`）。\n- **事後整備の明示**: 既に修正済みの版（v0.2.9）に対する trace は `POST_HOC` と label し「修正前に固定した」と主張しない。厳密な先行固定（`PRE_PINNED`）は v0.2.10 以降の修正に適用する。\n- **記録区分の分離**: 限定モデル検証・文書 checker・実装試験・実機試験の結果は別々に記録し、限定モデルの成功を実機の安全性へ読み替えない。checker の FAIL = 0 は時系列反例 / 対象取り違えの不在証明ではない。")
    d.insert_after_line("- v0.2 → **v0.2.2**", f"- v0.2.9 → **v0.2.10**（{NOW}）: §5 に trace 検証（期待結果先行固定・修正前後比較・正常系対照・記録区分の分離）を必須追加（Rs 裁定 2026-09-06 §4）。checklist の他の項は不変。")
d.save()
for name in ("07_SUCCESSOR_CONTRACT_DECISION_20260903.md", "04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md"):
    d = Doc(name); d.rep("(v0.2.9 REVIEW CANDIDATE)", "(v0.2.10 REVIEW CANDIDATE)"); d.rep("REVIEW CANDIDATE v0.2.9（", "REVIEW CANDIDATE v0.2.10（"); d.save()
print("applied:", applied); print("NOW =", NOW)
