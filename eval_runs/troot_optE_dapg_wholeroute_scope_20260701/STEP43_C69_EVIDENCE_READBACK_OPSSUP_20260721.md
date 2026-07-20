# c69 evidence readback — Rs 裁定 A/B + servo over-claim 撤回

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**Verdict 発行:** 2026-07-21 01:34 JST。
**対象:** c69 `183c1bb5dc` = `STEP43_CONTROLLER_REALIZATION_BASELINE_RSTECHLEAD_20260721.md`
sha256 `f1ea5e5a0109fee6c07806a1ab1cda9fad119e4ef97634c34871ce32ae11817e`。
**⚠ 本件は FOUNDATIONAL INVARIANT (RS71 §0#5) に触れる PREMISE 変更を含む。**

## ⭐ VERDICT: **PASS** — ただし custody 1 点を注記（下記 §C）

## A. 完成物 integrity — ✅PASS

| レグ | 結果 |
|---|---|
| sha256 @ `183c1bb5dc` | **完全一致** |
| records-only | 1 file・`.md`（52 insert / 6 delete）・**code 0** ⇒ census 35 不変は構造的に従う |

## B. 裁定 B（pin 例外の復活）の検証

### B-1. provenance の分離 — ✅**正しく行われている**

doc §9 は 2 層を**明示的に分離**している:

- **Rs 逐語（2 段）** =「kinematicは使用するなよ」→「ただし、クリップのケーブル固定だけは kinematic を使用する」
- **適用範囲表** = 見出しに「**私の理解 → Rs「ok」で確定**」と明記

⇒ **p4 の列挙を Rs の言葉として提示していない**。2026-07-20 の SKILL 所管裁定で確立した規律
（「scope 分割は私の解釈であり Rs の言葉ではない」）が守られている。p6 の LEDGER 記録も
「**p4 の適用範囲確認に Rs「ok」**」と同じ分離を保持（`00-DESIGN-STATUS-LEDGER.md:35`）。

### B-2. ⭐⭐ 独立 corroboration — **裁定 B は 07-15 の banked Rs 決定と一致する**

**本 readback の最重要所見。** `RS71-System-Spec-SSOT.md:28` に **2026-07-15 の human-Rs 逐語**が既に banked:

> **SCOPE EXTENDED TO THE RL ENV — human-Rs DECISION 2026-07-15
> (verbatim:「クリップ**のみ** pin を RL env に恒久配線しろ」)**
> The clip-retention pin is **permanently wired into the learning env** … **CLIP-RETENTION ONLY** —
> this authorizes no other kinematic exception, and the pin may fire **only at a clip seat**.
> (Recorded by %12 on Rs's instruction 2026-07-15 01:0x「かいて」)

⇒ **裁定 B（01:3x）と 07-15 決定は、内容・範囲とも同一方向**（pin のみ許可・他の kinematic 例外は認めない）。
**6 日隔てた 2 つの Rs 発話が一致し、07-19 directive の側が outlier** という構図。
⇒ 本 PREMISE 変更は **新規の逸脱ではなく、banked spec への復帰**。**逆転の risk は実質的に低い。**

さらに `RS71:27` は元から「the ONLY authorized exception is the clip-retention pin」と記載
（p6 実測・私も確認）⇒ **spec 本文の編集は不要**で、07-19 directive が *実務上* これを上書きしていた状態が解消された。

### B-3. ⚠ **C. custody 注記（唯一の OPEN・blocking ではない）**

**裁定 B の逐語は、受領経路が 1 本しかない**（Rs → p4 → doc → p6/pY）。
p6 は検証可能な周辺（sha full-64・producing commit・`RS71:27` 実測）をすべて独立確認しているが、
**「Rs が何と言ったか」自体は p4 の relay に依存**する（p6 の記録は 01:33＝p4 relay の 2 分後）。

⚠ **同一 configuration が 1 度失敗している**: 2026-07-20 の SKILL 所管裁定で、**p4 の受領分は
Rs 逐語の後半「整合性を持つように」が欠落**しており、**pQ の独立 custody record を p4 が実読して初めて**補完された
（c61 の経緯）。**今回は独立 custody record が存在しない。**

⇒ ⭐**提案 = Rs の 1 行確認で恒久 CLOSE**（コストほぼ 0）。
⛔ ただし **B-2 の corroboration があるため blocking にはしない**。作業停止の理由にはならない。

## D. servo over-claim の撤回 — ✅**撤回は正しい**（独立確認）

p4 撤回:「指の servo 駆動は実証済み」= over-claim。**独立検証で裏づけ**:

| 主張 | 実測 |
|---|---|
| SSOT が「faithful actuated close は deferred」と述べる | ✅ `task_config.py:337` 逐語「actuated close is **deferred** — **production stripped build has no actuator/equality**, R-S6.6」 |
| 43 step 経路で `gripper_dynamic` が未設定（⇒ `else` 枝 ⇒ 指も kinematic） | ✅ **閉クエリ 0 hit**（`thread_isaac_lab/scripts/wet_run_full_sequence.py`） |

⇒ **Rs 観察②「いままで kinematic によりフィンガ動作は実現できていた」は 43 step 経路について実測で TRUE。**

⭐ **失敗の型 = CLAUDE.md §15 の第 3 bucket「ABSENT-IN-CODE」の教科書例**:
comment の "servo close, NOT kinematic" を読み、**mechanism が runtime で ACTIVE か検証せずに「実証済み」と bank** した。
CLAUDE.md 逐語「**未 wired =「wire-then-validate」= premise FALSE、appearance-only ≠ working**」に正確に該当。
p4 が自ら 5 箇所を訂正し §8 に型として記録した点は適切。
⇒ **今後「指が閉じる」を根拠に使う主張は、この撤回の下で再評価が要る。**

## E. 波及（記録のみ・裁定しない）

| 面 | 状態 |
|---|---|
| LEDGER §35 + DDR#25 carry ④ | ✅p6 反映済（`cadc20c8d2`） |
| node `T-ROOT-Kinematic-Pin-Complete-Removal-20260719` | ✅p6 が goal を narrow 済。⚠**node 名自体は superseded な directive を保持**（改名要否 = 所有者判断） |
| `02-Workflow/HANDOFF.md` / `HANDOFF_p5_vtdesign.md` | ⛔**旧前提を保持**（所有 = p4/p5・p6 が訂正要請済） |
| memory `project-sim-is-reality-no-kinematic-20260719` 他 | ⛔**旧前提を保持**（standing directive ⭐⭐⭐ 扱い ⇒ 次 session の接地を誤らせる risk）。pY が更新 |
| Layer 8 census 35 の class | ⚠**再判定が必要**（pin 系サイトの class が変わり得る）。**class 裁定 = 設計軸**ゆえ本 readback では選ばない |

## 非主張

- ⛔ 裁定 A（p4 任務 = 43 step をアームとコントローラで実現・DoD = 動画）は**記録の確認のみ**。実施計画は p4 の lane。
- ⛔ Layer 8 class の disposition・pin 系サイトの扱いは**設計軸**であり本書では選ばない。
- ⛔ freeze / impl / training / closed-loop authority = CLOSED 継続。

---
**readback 実施 = 2026-07-21 01:34 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
