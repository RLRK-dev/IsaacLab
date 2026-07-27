# ⚠ この dir の file は「走った記録」であって、run が読む実体ではありません

**作成:** RS-TECH-LEAD (`w2:p4`) 2026-07-27 17:02 JST（date-THEN-write）。
**契機:** p18 `-190` §2（p0 発）逐語「⛔ **同名 copy が `p4_ur15_sim_20260727/` に在り そちらは 0.0382/0.0258 = 10.00 のまま**です」。

## run が実際に読む実体（唯一）

| 役割 | path |
|---|---|
| ⭐ **live model** | `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/_ur15_2f85_koshape_actuated.xml` |
| 参照元 | driver の `GRIP_XML`（**絶対 path**） |

⭐ **現在の live model の口:** `f1ext pos z = 0.0402` / `f2ext pos z = 0.0238` ⇒ **開口 14.00 mm**
（Rs 指示「コの上下幅を4mm増やして」・commit `f11273d5be6b41884bc83cc066aad54b6b27ed8f` 16:25:29）。

## ⚠ この dir の同名 copy

`p4_ur15_sim_20260727/_ur15_2f85_koshape_actuated.xml`（mtime 2026-07-27 04:18）は
**`f1ext 0.0382` / `f2ext 0.0258` = 開口 10.00 mm**。

⇒ ⭐ **これは陳腐化ではなく、04:18 時点で走った内容の記録です。** ⛔ しかし **file 名が live と同じ**ため、
dir を開いた読み手が live と読み違えます。**それが本注記の理由です。**
⛔ **上書きしません**（記録を書き換えることになるため）。⛔ **この copy から幾何を読まないでください。**

## 同様の注意（同 dir 内）

- `ur15_steps.py`（11:43）・`ur15_steps_reaim.py`（14:39）は **その時刻に走った driver の記録**。
  ⚠ 現在の作業 driver は別 path に在り、**行番号は一致しません**。
  ⇒ 他 pane が `ur15_steps_reaim.py:NNN` で引いた行は **当該 copy の中で**読んでください。
- `.log` は各 run の出力。⭐ **`ur15_wide14.log` / `ur15_wide14_control.log` は同一内容**（Rs が「両方成功」と判定した run）。

## ⛔ 本注記が主張しないこと

⛔ どの copy が正しいかを判定しない ／ ⛔ 記録を編集・削除しない ／ ⛔ banked LOCK 資産 `2f85_koshape.xml` に触れない。

---
**p4 note = 2026-07-27 17:02 JST / RS-TECH-LEAD (`w2:p4`)**
