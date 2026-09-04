#!/usr/bin/env python3
"""v0.2.1 -> v0.2.2 fold for 06 / 07 / 04 / 08 / 10 / 02.csv / 03.csv (records-only; frozen files untouched).
Usage: python3 fold_v022_others.py <PKG_DIR> [verdicts.json]
Every replacement asserts its anchor exists exactly once (fail-closed)."""
import sys, json, csv, io, re, subprocess

P = sys.argv[1]
VERD = json.load(open(sys.argv[2])) if len(sys.argv) > 2 else {}
NOW = subprocess.check_output(["date", "-u", "+%Y-%m-%d %H:%M UTC"]).decode().strip()  # date-THEN-write
A = "$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md"
B = "$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md"
D0 = "$D/WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md"
EPM = "$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md"
EPJ = "$D/WMSO_EvidencePolicy_v1.9.json"

def verdicts(ids):
    out = []
    for i in ids.split(" / "):
        i = i.strip()
        v = VERD.get(i)
        out.append(f"{i}={v}" if v else f"{i}=（verifier 未了）")
    return "; ".join(out)

class Doc:
    def __init__(self, name):
        self.name = name; self.t = open(f"{P}/{name}", encoding="utf-8").read()
    def rep(self, old, new, count=1):
        n = self.t.count(old); assert n == count, (self.name, old[:70], n)
        self.t = self.t.replace(old, new)
    def repline(self, prefix, new):
        lines = self.t.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
        assert len(idx) == 1, (self.name, prefix[:70], idx)
        lines[idx[0]] = new; self.t = "\n".join(lines)
    def insert_before_line(self, prefix, block):
        lines = self.t.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
        assert len(idx) == 1, (self.name, prefix[:70], idx)
        lines[idx[0]:idx[0]] = block.split("\n"); self.t = "\n".join(lines)
    def insert_after_line(self, prefix, block):
        lines = self.t.split("\n"); idx = [i for i, l in enumerate(lines) if l.startswith(prefix)]
        assert len(idx) == 1, (self.name, prefix[:70], idx)
        lines[idx[0]+1:idx[0]+1] = block.split("\n"); self.t = "\n".join(lines)
    def save(self):
        open(f"{P}/{self.name}", "w", encoding="utf-8").write(self.t); print("wrote", self.name)

# ---------------------------------------------------------------- 06
d = Doc("06_WMSO_INDUSTRIAL_PROFILE_v0.2_REVIEW_CANDIDATE_20260903.md")
d.rep("DEPLOYMENT PROFILE SPEC (v0.2.1 REVIEW CANDIDATE)", "DEPLOYMENT PROFILE SPEC (v0.2.2 REVIEW CANDIDATE)")
d.rep("／ v0.2.1 = 2026-09-04 01:5x UTC", f"／ v0.2.1 = 2026-09-04 01:51 UTC（file mtime 実測 01:51:18）／ v0.2.2 = {NOW}（`date -u` 実測）")
d.rep("- status: **REVIEW CANDIDATE v0.2.1（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.1 = 陽性対照レビューの注入外 finding の fold（§11）",
      "- status: **REVIEW CANDIDATE v0.2.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.1 = 陽性対照レビューの注入外 finding の fold ／ v0.2.1 → v0.2.2 = 3 軸独立レビューの確定 finding の fold（§11・verdict と処置の全体 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`）")
d.rep("    manager_liveness_s: CanonicalDecimal\n",
      "    manager_liveness_s: CanonicalDecimal\n"
      "    safety_heartbeat_timeout_s: CanonicalDecimal   # v0.2.2（B2-01 / B-H3）: IndependentSafetyLayer heartbeat 欠落の上限（05 TimingBinding 同名 field・超過 = 05 §5.2 (i′) SafeStop + R_SAFETY_LAYER_LOST）\n"
      "    decision_max_age_s: CanonicalDecimal           # v0.2.2（A-01 / B2-14）: permit 発行時に AuthorityDecision に許す最大 age（05 §3.4 (e)）\n"
      "    boundary_dwell_s: CanonicalDecimal             # v0.2.2（B-M9）: S_BOUNDARY_WAIT 滞留の上限（超過 = 05 R_BOUNDARY_DWELL_EXCEEDED → NO_CHAIN 経路）\n"
      "    max_reselect_attempts: int                     # v0.2.2（B-M9）: 1 boundary あたりの候補試行上限（≥ 1）\n"
      "    command_kind_mismatch_max: int                 # v0.2.2（B2-15）: 連続 R_COMMAND_KIND_MISMATCH の許容回数（≥ 1・超過 = TRANSFER_TO_SAFEHOLD(ENVELOPE_VIOLATION)）\n"
      "    inter_command_jitter_s: CanonicalDecimal       # v0.2.2（B-L2 / B2-13）: 連続 command 間隔の許容偏差（超過 = 05 R_TIMING_VIOLATION）\n")
d.repline("- **反循環**: profile は自身の",
      f"- **反循環（v0.2.2・A-06 / A2-09 で構造 pattern に揃えた）**: profile は **自身から導かれる hash**（`profile_hash`・その部分 hash）と、「自身と同一である」ことを主張する任意の hash、および `profile_hash` を preimage に持つ runtime 値（lease id・`control_epoch`・permit id）を preimage に置かない（`{B}:23` の構造 pattern「自己参照 hash を preimage に置かない」と同型）。`profile_hash` は `SkillActionId` / `ExecutionBundleHash` / `tensor_binding_hash` の preimage に入らない（03 matrix C03）ため、`binding_expectations[].skill_action_id` / `tensor_binding_hash` のような**他 artifact の静的 id の参照**は自己参照ではなく許される。検出 = `P_SELF_HASH`（前者の列挙に対する検査）。")
d.rep("| `attested_by` 空 ⇒ `P_RESOURCE_UNATTESTED`（CELL_COMMISSIONING evidence 必須） |",
      "| evidence store に `kind = CELL_COMMISSIONING` ∧ `record.profile_hash == H_WCJ(profile)` の `DeploymentEvidenceRecord` が無い ⇒ `P_RESOURCE_UNATTESTED`（登録時・第 1 評価点・§2.1 注記と同一規則。v0.2.2 A2-03: 旧 cell は削除済 field `attested_by` を参照していた） |")
d.rep("| 全 `RuntimeTimeouts` > 0・有限 | `P_TIMEOUT_NONPOSITIVE` |",
      "| 全 `RuntimeTimeouts` field > 0・有限（`int` field は ≥ 1・v0.2.2） | `P_TIMEOUT_NONPOSITIVE` |")
d.rep("`TimingBinding.{ack_timeout_s, permit_ttl_s, health_confirm_timeout_s, command_deadline_s, manager_liveness_s}` ← `RuntimeTimeouts`",
      "`TimingBinding.{ack_validity_s, ack_timeout_s, permit_ttl_s, health_confirm_timeout_s, command_deadline_s, manager_liveness_s, safety_heartbeat_timeout_s, decision_max_age_s, boundary_dwell_s, max_reselect_attempts, command_kind_mismatch_max, inter_command_jitter_s}` ← `RuntimeTimeouts`（同名 field の等値写像・v0.2.2 で 6 field 追加）")
d.repline("- lease 活性中に profile の前提が崩れた場合",
      "- lease 活性中に profile の前提が崩れた場合（v0.2.2・B-M7 で 05 と同期）: (a) health check 失敗（stage AT_HEALTH_CONFIRMATION / BOTH）は 05 §4.5 `R_HEALTH_CONFIRM_FAILED` → SAFEHOLD。(b) calibration 期限切れ・deployment evidence 失効は **活性 lease 中には検出されない**（05 は lease 中の周期再評価を持たない — 05 OP-19・保守既定）。検出点 = **次の permit 発行時**（05 §3.4 (b) の第 2 評価点 → `R_PROFILE_MISBOUND`・permit 不発行）。曝露 = 最大 1 skill（TERMINAL boundary まで）。周期再評価を manager に持たせるかは 05 OP-19（未裁定）。いずれの場合も profile 側の「更新」ではなく新 profile（新 hash）での新 lease。")
d.repline("| PT-13 |",
      "| PT-13 | 受理済 profile の calibration が失効 | profile 不変。活性 lease は TERMINAL boundary まで継続（lease 中の検出点なし・曝露 ≤ 1 skill・v0.2.2 B-M7・05 OP-19）。次の permit 発行は `P_CALIBRATION_EXPIRED` → 05 `R_PROFILE_MISBOUND` で不成立 |")
d.repline("- EP md / JSON に `controller`",
      f"- **不在主張の範囲と再現（v0.2.2・A-03 / A2-10）**: 対象は **EP md / JSON の 2 file のみ**。再現 command（本 package 内で解決可能）: `for p in controller calibrat deploy inject epoch lease; do grep -ic \"$p\" {EPM} {EPJ}; done` = 全 pattern で 0 / 0（2026-09-04 実測）。`cell` は EP が usage matrix の表 cell の語として使う（md 10 行 / json 3 行）ため対象外（v0.2.1 C-14）。⚠ DESIGN 2 file には散文語の hit がある（`{A}:570`・`{B}:337`「calibrated uncertainty」／ `{B}:255`・`{B}:313`「全 deployment の resolver」）— いずれも型・field・enum ではない。ゆえに deployment evidence は EP の claim_target / ProofKind の**外**にある（型レベルの根拠 = 07 §1 根拠 4）。")
d.rep("- **v0.2.1 fold（2026-09-04 01:5x UTC）", "- **v0.2.1 fold（2026-09-04 01:51 UTC・file mtime 実測）")
d.repline("16. 機械検査（`check_review_candidate.py`）= FAIL 0。",
      "16. 機械検査（`check_review_candidate.py`）= FAIL 0（v0.2.2 の実測出力は `11_THREE_AXIS_REVIEW_RECORD_20260903.md`）。C2 WARN は heuristic で、いずれも「1 行に複数 locus を並べた表の行」か「frozen 行を型根拠として引き、同じ行で本 doc の新語（`P_*` / `profile_hash` 等）を導入した行」— 引用先の内容は起草時に sed で確認済み（§1 表・§3 表・§12）。")
d.insert_before_line("## 12. Review anchors",
f"""- **v0.2.2 fold（{NOW}）— 3 軸独立レビュー（reviewer A / A2〔Opus〕/ B / B2〔Opus〕・別 context・v0.2.1 対象）の finding のうち本 doc に帰属するものを fold**。verdict 列 = 独立 verifier の判定（未了なら明記）と起草者の再検証（各 finding の前提文が本 doc に実在することは本 fold script の anchor assert で機械確認）。全 finding の一覧・処置 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`。⚠ 軸 C（deployment・reviewer C）は session 上限で未了 — 完了後に追補する:

| finding | 内容 | 変更節 | verdict |
|---|---|---|---|
| A-06 / A2-09 (LOW) | §2.3 反循環文が字義的に自己矛盾（`SkillActionId` を内包しない ↔ `binding_expectations[].skill_action_id`） | §2.3 を構造 pattern（自身から導かれる hash を preimage に置かない）で言い換え | {verdicts("A-06 / A2-09")} |
| A2-03 (MEDIUM) | §3 表の `P_RESOURCE_UNATTESTED` trigger が削除済 field `attested_by` を参照 | §3 表 cell を §2.1 注記（evidence store 照会）へ同期 | {verdicts("A2-03")} |
| B-M7 (MEDIUM) | §5 / PT-13「活性 lease 中の失効 ⇒ lease 無効化」に 05 側の検出点・遷移が無い | §5・PT-13 を保守既定（検出 = 次 permit 発行時・曝露 ≤ 1 skill・05 OP-19）へ同期 | {verdicts("B-M7")} |
| B2-01 / B-H3 / A-01 / B2-14 / B-M9 / B2-15 / B-L2 / B2-13 (05 由来) | 05 v0.2.2 が `TimingBinding` に足した 6 field の出所 | §2.1 `RuntimeTimeouts` += `safety_heartbeat_timeout_s` / `decision_max_age_s` / `boundary_dwell_s` / `max_reselect_attempts` / `command_kind_mismatch_max` / `inter_command_jitter_s`・§3 `P_TIMEOUT_NONPOSITIVE`・§5 写像文 | {verdicts("B2-01 / B-H3 / A-01 / B2-14 / B-M9 / B2-15 / B-L2 / B2-13")} |
| A-03 / A2-10 (MEDIUM / LOW) | 不在主張の範囲が広すぎ・package 外 scratch（critic 報告）を根拠に引用 | §6.2 を再現 command + 範囲限定（EP md / JSON）へ | {verdicts("A-03 / A2-10")} |
| A-09 / A2-11 (LOW) | x-mask 時刻（01:5x） | header・§11 を file mtime 実測へ | {verdicts("A-09 / A2-11")} |
| A2-12 / B-L5（05 側で fold） | `validate_outcome` 失敗経路 | 本 doc 変更なし（05 §3.7） | {verdicts("A2-12 / B-L5")} |
""")
d.save()

# ---------------------------------------------------------------- 07
d = Doc("07_SUCCESSOR_CONTRACT_DECISION_20260903.md")
d.rep("# WMSO 後継静的契約の判断（successor contract decision）(v0.2 REVIEW CANDIDATE)", "# WMSO 後継静的契約の判断（successor contract decision）(v0.2.2 REVIEW CANDIDATE)")
d.rep("作成 = 2026-09-03（UTC・`date -u` 実測）", f"作成 = 2026-09-03 16:40 UTC（file mtime 実測 16:40:49）／ v0.2.2 = {NOW}（`date -u` 実測）")
d.rep("- status: **REVIEW CANDIDATE v0.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）**",
      "- status: **REVIEW CANDIDATE v0.2.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.2 = 3 軸独立レビュー finding の fold（§7）")
d.rep("05 runtime spec v0.2 ／ 06 industrial profile v0.2", "05 runtime spec v0.2.2 ／ 06 industrial profile v0.2.2")
d.repline("- 凍結 4 file に cell / controller / calibration / deploy の語彙は無い",
      f"- frozen 型に cell / controller / calibration / deployment を表す **field は無い**（`SkillDefinition` の field 列挙 `{A}:127-149`・`TensorBindingSpec` `{B}:176-181`。v0.2.2 A-03 / A2-10: 型レベルの事実であり語彙の不在主張ではない — 散文語の hit は `{A}:570`・`{B}:337`「calibrated uncertainty」・`{B}:255`・`{B}:313`「全 deployment の resolver」で、いずれも型・field・enum ではない。EP md / JSON の 0 hit は 06 §6.2 の再現 command）⇒ deployment profile は外部で定義でき、strict codec（`{A}:385`）がその field を frozen 型へ静かに足す経路を閉じる。")
d.repline("2. 新 field は既定で `BehaviorSignature` に入り",
      f"2. 新 field は既定で `BehaviorSignature` に入り（補集合定義・`:218`）、`SkillDefinitionHash`（`:159`）も動く。`SkillActionId` は `{{ns, skill, bundle, variant, brev}}` の関数ゆえ**自動では動かない**（`:158`）が、同 key での再登録は `E_BEHAVIOR_REVISION_STALE` で拒否される（`:219`「ActionId は不変のまま、忘却は登録境界で機械捕捉」）⇒ `behavior_revision` の bump（= ActionId 変更）と certificate の再発行が事実上必須になる（v0.2.2・A2-06: 旧文「全 certified skill の identity が変わり」は frozen `:219` と 03 matrix C08–C12 に反していた）。")
d.rep("- v0.1（前 package・参照不能）→ v0.2（本 doc）。handoff 決定 E を根拠に再構成。旧 v0.1 の識別子は本 doc に無い（05/06 で 削除）。",
      "- v0.1（前 package・参照不能）→ v0.2（本 doc）。handoff 決定 E を根拠に再構成。旧 v0.1 の識別子は本 doc に無い（05/06 で 削除）。\n"
      f"- v0.2 → **v0.2.2**（{NOW}）: 3 軸独立レビューの finding A-03 / A2-10（§1 根拠 4 を型レベルの事実へ・package 外 scratch 参照の除去）・A2-06（§3 理由 2 の identity 文言を frozen `:158` / `:219` に整合）を fold。v0.2.1 は本 doc には無い（05 / 06 のみ）。verdict = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`（{verdicts('A-03 / A2-10 / A2-06')}）。")
d.rep("1. 委譲の根拠 4 点 — §1 ↔ `$D/WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:382`・`:354`・`:537`・`$D/WMSO_D11B_TENSOR_BINDING_DESIGN_RSTECHLEAD2_20260720.md:374`。",
      f"1. 委譲の根拠 4 点 — §1 ↔ `{A}:382`・`:354`・`:537`・`{B}:374`・型レベルの不在 = `{A}:127-149`・`{B}:176-181`（v0.2.2）。")
d.rep("3. v3 名称の 4 理由 — §3 ↔ `:385`・`:218`・`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`。",
      "3. v3 名称の 4 理由 — §3 ↔ `:385`・`:218`・`:158`・`:219`（v0.2.2）・`$D/WMSO_D11A_EVIDENCE_POLICY_V1_RSTECHLEAD2_20260719.md:163`。")
d.save()

# ---------------------------------------------------------------- 04
d = Doc("04_EVIDENCE_POLICY_IMPACT_ASSESSMENT_20260903.md")
d.rep("(v0.2 REVIEW CANDIDATE)", "(v0.2.2 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）**",
      "- status: **REVIEW CANDIDATE v0.2.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.2 = 3 軸独立レビュー finding A2-10 の fold（§8）")
d.rep("（EP md / JSON で `epoch` / `lease` = 0 hit — critic 報告 §3.7）", "（EP md / JSON で `epoch` / `lease` = 0 hit — 再現 command は 06 §6.2・v0.2.2 A2-10 で package 外の scratch 参照を除去）")
d.insert_after_line("- v0.1（前 package・参照不能）→ v0.2（本 doc）。handoff 決定 F",
      f"- v0.2 → **v0.2.2**（{NOW}）: A2-10（package 外 scratch 参照）を fold。判断内容は不変。verdict = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`（{verdicts('A2-10')}）。")
d.save()

# ---------------------------------------------------------------- 08
d = Doc("08_INDEPENDENT_REVIEW_PLAN_20260903.md")
d.rep("(v0.2 REVIEW CANDIDATE)", "(v0.2.2 REVIEW CANDIDATE)")
d.rep("- status: **REVIEW CANDIDATE v0.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）**",
      "- status: **REVIEW CANDIDATE v0.2.2（未 bank・two-key 未・Rs 未裁定・gate PASS を主張しない）** — v0.2 → v0.2.2 = 3 軸独立レビュー finding A-08 の fold（§10）")
d.rep("で FAIL = 0 を確認してから読む（FAIL があれば読む前に HOLD）。",
      "で FAIL = 0 を確認してから読む（FAIL があれば読む前に HOLD）。CSV（02 / 03）は同 script が拡張子 `.csv` で CSV mode に入る（H1 / S1 非適用・header と行数 40 / 14 の assert・`disposition_v0_2` / `verdict` が removed / not_adopted の行は F1 免除・C1 は同じ）— v0.2.2（A-08）。")
d.insert_after_line("- v0.1（前 package・参照不能）→ v0.2（本 doc）。handoff 決定 H",
      f"- v0.2 → **v0.2.2**（{NOW}）: A-08（CSV の機械検査手順）を §1 項 3 に反映。checklist は不変。実施記録 = `11_THREE_AXIS_REVIEW_RECORD_20260903.md`（{verdicts('A-08')}）。")
d.save()

# ---------------------------------------------------------------- 10
d = Doc("10_POSITIVE_CONTROL_RECORD_20260903.md")
d.rep("記録 = 2026-09-04 01:5x UTC", "記録 = 2026-09-04 01:49 UTC（file mtime 実測 01:49:59・v0.2.2 A-09 / A2-11 で x-mask を除去）")
d.save()

# ---------------------------------------------------------------- 02 csv
name = "02_FIELD_OVERLAP_AND_HOME_MATRIX_20260903.csv"
lines = open(f"{P}/{name}", encoding="utf-8").read().rstrip("\n").split("\n")
assert len(lines) == 41, len(lines)
def setrow(rid, new):
    idx = [i for i, l in enumerate(lines) if l.startswith(rid + ",")]
    assert len(idx) == 1, (rid, idx); lines[idx[0]] = new
setrow("F16", f"F16,ReadinessAck,v0.2_runtime,partial,{D0}:267-272,authority_manager/command_gateway,new_runtime_type,D0 offer→accept→ack の ack を転送前の前提条件に具体化（handoff 訂正 2・v0.2.2 A-07 で locus を step 2 の accept+ack まで広げた）,{D0}:267-272")
setrow("F18", f"F18,\"AuthorityCas / AuthorityState (owner, control_epoch, active_lease_id, consumed_offer_ids, safehold_reason, boundary_wait, seq)\",v0.2_runtime,partial,{A}:382,authority_manager/command_gateway,new_runtime_type,D0 の one atomic token flip を 7 要素 tuple の CAS として具体化（handoff 訂正 3・4。v0.2.1 で safehold_reason / boundary_wait / seq を追加・v0.2.2 A-07 で本行を同期）,{D0}:270-272")
setrow("F21", f"F21,SafeHold / SafeStop (null output),v0.2_runtime,partial,{D0}:270-272,runtime_process,new_runtime_type,D0『producer retains ownership and safe-stops』の runtime 実現（逐語 = fail-closed 項・v0.2.2 A-07 で citation を訂正）,{D0}:273-274")
setrow("F36", f"F36,IndustrialDeploymentProfile (cell / controller / tool / payload / workspace),v0.2_profile,no,-,IndustrialDeploymentProfile,new_profile_type,frozen 型（SkillDefinition / TensorBindingSpec）に cell・controller・calibration・deployment の field なし（型レベルの事実。散文語の hit は A:570・B:255/313/337 のみ — v0.2.2 A-03）⇒ 外部 profile,{A}:127-149; {B}:176-181")
open(f"{P}/{name}", "w", encoding="utf-8").write("\n".join(lines) + "\n"); print("wrote", name)
rows = list(csv.reader(io.StringIO("\n".join(lines)))); assert all(len(r) == 9 for r in rows), [len(r) for r in rows]

# ---------------------------------------------------------------- 03 csv
name = "03_IDENTITY_HASH_EVIDENCE_IMPACT_MATRIX_20260903.csv"
lines = open(f"{P}/{name}", encoding="utf-8").read().rstrip("\n").split("\n")
assert len(lines) == 15, len(lines)
for rid in ("C08", "C09", "C10", "C11", "C12"):
    idx = [i for i, l in enumerate(lines) if l.startswith(rid + ",")]
    assert len(idx) == 1, (rid, idx)
    lines[idx[0]] += f"; {A}:158（SkillActionId の preimage = ns / skill / bundle / variant / brev のみ — v0.2.2 A2-07）; {A}:219（ActionId は不変・同 key の再登録は E_BEHAVIOR_REVISION_STALE）"
open(f"{P}/{name}", "w", encoding="utf-8").write("\n".join(lines) + "\n"); print("wrote", name)
rows = list(csv.reader(io.StringIO("\n".join(lines)))); assert all(len(r) == 12 for r in rows), [len(r) for r in rows]
print("NOW =", NOW)
