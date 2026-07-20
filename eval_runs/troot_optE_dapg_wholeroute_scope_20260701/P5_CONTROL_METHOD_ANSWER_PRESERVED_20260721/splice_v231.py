"""Splice §14.27 + v2.31 into the charter frozen at c53. Fail-closed: every edit asserts exactly-one match."""
import hashlib
import pathlib

SCRATCH = pathlib.Path("/tmp/claude-1000/-home-rlrk-IsaacLab/b0da55e6-a6b5-4743-88ca-b88a358d3404/scratchpad")
src = (SCRATCH / "charter_c53.md").read_text(encoding="utf-8")
sec = (SCRATCH / "sec_14_27.md").read_text(encoding="utf-8").rstrip("\n")

assert hashlib.sha256(src.encode()).hexdigest() == (
    "b68c598dc5b32524bf52acf57182b0e45520b6ac67d9a45c40d834b69b8b1efb"
), "base is not the c53 blob"


def sub_once(text, old, new, tag):
    n = text.count(old)
    assert n == 1, f"{tag}: expected 1 match, got {n}"
    return text.replace(old, new)


# ---- 1. Status line -------------------------------------------------------
OLD_STATUS = (
    "**Status:** DESIGN **v2.30 = BANKED c51 `031ca0dc95`**"
    "（blob `da1206a69c6364`・sha256 `c98f281b1ea84b47` = p5 独立算出値と exact 一致・%12 は 1 文字も編集せず）。"
    "⚠**records-fix 適用済・再 bank 待ち**（house 先例に従い版は上げない: 版表 v2.28/v2.29/v2.30 の bank 欄を c51 で充填）"
)
NEW_STATUS = (
    "**Status:** DESIGN **v2.31 = 未 bank（本 doc、§14.27 新設）**。"
    "⚠**測定時 worktree は別 branch（`rlrk/optE-s2-substrate-swap` = WMSO 系、HEAD `ddbae19e0f`）にあり "
    "c52/c53 は HEAD の祖先でない** ⇒ **本版の適用・bank は `probe/pd1-arm-pd` 復帰（or `git worktree` 分離）後に行うこと**"
    "（p5 は他 pane が live な共有 tree の branch を切り替えない）。 — "
    "**v2.30 = BANKED c53 `8fda0b6ed1`**（records-fix 込みの最終形・blob `ad88f0fbfa8685`・"
    "sha256 `b68c598dc5b32524` = p5 独立算出値と exact 一致・%12 は 1 文字も編集せず。"
    "直前実体 = c51 `031ca0dc95`/blob `da1206a69c6364`/sha256 `c98f281b1ea84b47`、"
    "差分は Status 同期 + 版表 v2.28-v2.30 bank 欄充填のみで設計実体不変 = %12 diff 確認済）"
)
out = sub_once(src, OLD_STATUS, NEW_STATUS, "status")

# ---- 2. SUPERSEDED-wrap: v2.30 table row (retire 条件節 + 別 class) --------
OLD_ROW_TAIL = "・live consumer 無なら retire）"
NEW_ROW_TAIL = (
    "・live consumer 無なら retire）"
    "⚠**〔v2.31 §14.27 で 2 点 SUPERSEDED: ①「別 triple = 別 class」→ triple 差は "
    "**acceptance evidence の差**であって class の差ではない・class は単一 `DRIVE` ②「live consumer 無なら retire」→ "
    "**反証不能**ゆえ静的条件 **[R-E]** に差替え・現状 4 entry point 該当ゆえ **retire 不可**〕**"
)
out = sub_once(out, OLD_ROW_TAIL, NEW_ROW_TAIL, "v2.30 row wrap")

# ---- 3. SUPERSEDED-wrap: §14.26-d verdict 行 ------------------------------
OLD_VERDICT = "2 枝は別 triple ゆえ別 class**（else 枝に narrowing ① は及ばない）。"
NEW_VERDICT = (
    "2 枝は別 triple ゆえ別 class**（else 枝に narrowing ① は及ばない）"
    "⚠**〔SUPERSEDED v2.31 §14.27(4)(1): 「別 triple」は事実だが **class の差ではなく acceptance evidence の差**。"
    "class は 6 行すべてで単一 `DRIVE`（extent 差 ≠ kind 差）。"
    "「else 枝に narrowing ① は及ばない」の部分は有効。〕**。"
)
out = sub_once(out, OLD_VERDICT, NEW_VERDICT, "14.26-d verdict wrap")

# ---- 4. 版表: v2.31 行を v2.30 行の直前に挿入 ------------------------------
ROW_231 = (
    "| v2.31 | bank = %12 | 2026-07-20 21:0x | §14.27 **`physics_step` 全 consumer 列挙への裁定**"
    "（材料 c52 `46a59e7831`/sha256 `068b51dda8aee047` = p5 独立照合済・材料のみで class 選択なし）: "
    "**class = 単一 `DRIVE`/`MIGRATION_PENDING` 維持・consumer 別分割は却下**"
    "（`gripper_dynamic` は **extent** を変えるが **kind** を変えない。extent 差で割ると remediation 義務が同一な 2 class ができ "
    "**per-consumer 免除の入口**になる ⇒ §14.26 (b) 却下と同形）。"
    "**bind = 全 consumer**（B0/B1 は外部 5 callsite 中 1・同 module 54 は B0/B1 経路外 = 「B0/B1 closure ⊊ symbol closure」3 例目）。"
    "⭐**fence は class の代替でなく加算・2 種別立て**: **F-α rebind sink**"
    "（`T.physics_step = _pp` が AST 静的解決と runtime 実体を乖離 ⇒ guard 契約に module 属性代入 sink を追加。"
    "**guard の健全性欠陥であり class をどう付けても消えない**）/ **F-β untracked closure**"
    "（pin closure 外の実行可能 consumer を track / 隔離 / 実行不能証拠つき登録の 3 択で disposition・**第三状態を残さない**）。"
    "⛔**escalation** = `_pp` の `[ARM_Q:]` 0 埋め + `mj_forward` は cable 側 = **clip-retention pin 系** ⇒ "
    "Rs 07-19「kinematic 完全削除（pin 含む）」射程 ⇒ **Rs surface 項目に登録**（⚠**live とは主張しない**）。"
    "⚠**訂正 #27** = v2.30 の「live consumer 無なら retire」は **反証不能**"
    "（RUN レグを要する条件を RUN CLOSED 下の解除条件に据えた）⇒ 静的条件 **[R-E]**"
    '（`¬set(gripper_dynamic) ∧ backend=="mujoco"` の callsite が静的に 0）に差替え ⇒ '
    "**現状 4 entry point 該当ゆえ retire 不可・exercise 測定は不要**。"
    "⚠**%12 count 訂正** = **`main:8067` は else 枝に入らない**"
    "（`:8206` if の**内**・`:8207-8249` 連鎖の**外**にある `:8250 return` が全 mujoco 枝を返す ⇒ "
    "`:8294` は非 mujoco 限定 ⇒ VBD 枝 `:1836` で FAIL 0）⇒ entry point 5→4・helper 帰属も同じ連言で再 intersect（%12 court）。"
    "⚠**citation 訂正** = `policy_route_runner:506` → 実体 **`:483`**（assert `:484`）。"
    "⭐**新規 [H-1]** = Z-Check gate は `main` 下流 = **VBD 枝**に載る（`CLAUDE.md:271`「Newton VBD」と構造一致）⇒ "
    "移管は substrate 越え port で 6 FAIL を継承しないが、移管先が `gripper_dynamic=False` だと fingertip z が FK 指令の関数になり "
    "**貫通述語が物理由来では偽になり得ない** ⇒ **移管 Z-Check は True path 限定 + gate 入口で fail-closed assert**"
    "（runner 側 assert に依存しない）。instrument の fail-OPEN(`:585-586`)・`found` 短絡(`:591-600`) は逐語移植しない。"
    "⭐一般則 2 件追加: **解除条件は偽を示せる形で書く** / **guard は symbol の束縛も守れ** |"
)
lines = out.split("\n")
idx = [i for i, ln in enumerate(lines) if ln.startswith("| v2.30 |")]
assert len(idx) == 1, f"v2.30 row: expected 1, got {len(idx)}"
lines.insert(idx[0], ROW_231)

# ---- 5. §14.27 を §14.9 の直前に挿入 --------------------------------------
anchor = [i for i, ln in enumerate(lines) if ln == "### §14.9 sequencing"]
assert len(anchor) == 1, f"§14.9 anchor: expected 1, got {len(anchor)}"
lines[anchor[0] : anchor[0]] = sec.split("\n") + [""]

out = "\n".join(lines)
dst = SCRATCH / "charter_v231.md"
dst.write_text(out, encoding="utf-8")

# ---- 6. 検算（印字型: 件数でなく実体を出す） -------------------------------
print("bytes    :", len(out.encode()))
print("lines    :", out.count("\n"))
print("sha256   :", hashlib.sha256(out.encode()).hexdigest())
print("--- literal backslash-n の混入検査（過去 2 回の自己バグ）---")
bad = [i + 1 for i, ln in enumerate(out.split("\n")) if "\\n" in ln]
print("offending lines:", bad if bad else "NONE")
print("--- 版表 行順 ---")
for i, ln in enumerate(out.split("\n"), 1):
    if ln.startswith("| v2.3") or ln.startswith("| v2.2"):
        print(f"  {i}: {ln[:34]}")
print("--- §14.27 見出し ---")
for i, ln in enumerate(out.split("\n"), 1):
    if ln.startswith("### §14.27"):
        print(f"  {i}: {ln[:70]}")
