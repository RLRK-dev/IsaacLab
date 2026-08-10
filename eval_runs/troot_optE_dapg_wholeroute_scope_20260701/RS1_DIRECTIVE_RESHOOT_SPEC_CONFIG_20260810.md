# Rs1 (the human) 指示 — 仕様書どおりの構成で DoD 動画を撮り直す（先祖返り禁止つき）

bank: **`w2:p5`**（Rs1 発話は本 session に直接届いた = 私が custody 保持者）/ 起票 2026-08-10 09:0x JST
⛔ 本 file は指示の bank と実行仕様。**私は run しない**（wired = p0 の court・run 認可 = Rs1、下記 §3）。

---

## 1. Rs1 逐語（本 session・3 turn 連続・文脈 = 前夜の DoD 動画 `ur15_dod_c2_stall_20260810.mp4` を見た後）

1. 「**それだ。今回の動画はそれを前提にしているのか**」（「それ」= 直前 turn で私が名指した **07-28 供給仕様書一式** `~/Downloads/ur15-dual-arm-cell/`。Rs1 自身が「それだ」で確定 ⇒ 指示対象の解決は Rs1 本人）
2. 「**仕様書どおりの構成で撮り直せ**」
3. 「**先祖返りはするな**」

## 2. 私の解決（resolver = p5・labelled 対話ゆえ一意）

- **撮り直す物** = DoD 動画（前夜の run と同じ経路 = wired driver + 動画出力）。
- **構成** = 仕様書の値。⭐ **仕様書の機械可読モデル（URDF）を本 turn 実測した結果、直すべき逸脱は取付 3 値だけ**（§4）。
- **「先祖返りはするな」の適用**（§運用16 の語彙・= 古い状態の復元禁止）:
  - ⛔ **code の巻き戻し禁止** — 昨夜着地の 6 commit（サーボ開始修正・guard・recorder、wired content sha256 `8fae5334e85e6af5…`）は**そのまま**。取付だけを仕様値にする。
  - ⭐ **手段は既存の override 機構**（着地 commit `0f6b4a733e` 自身が「`YOKE_SPREAD_OVERRIDE=0.22 TILT_DEG_OVERRIDE=45` で built が新しい解釈器で再現される」ことを検証済みと記す）⇒ **編集 0 行・復元 0 行**で仕様構成になる。
  - ⛔ **既定値（C-2 で着地済み）はこの指示では動かさない** — 本指示は**撮影の構成**であって既定の差し戻しではない。既定を仕様値へ戻すかは別決定（dep-1 系・p4 court・要るなら Rs1 の一言）。

## 3. 権限

- **run 認可 = Rs1 逐語「撮り直せ」**（= 本撮り直し 1 回に scoped。一般解錠ではない。dep-3 閉鎖後の通常規則どおり）。
- 実行 = **p0**（wired の owner）。検証レグ = 動画→ログ→照合の三者一致（pB/pC + Rs1 動画 GT・numeric 単独 PASS 禁止）。私は起動しない。

## 4. 仕様書の機械可読モデル（URDF）— 本 turn 実測（全て一次読み）

| 項 | URDF の実測 | 帰結 |
|---|---|---|
| joints | **stereo_head_mount / left・right_yoke_mount = fixed**・腕 6×2 = revolute・gripper 系 revolute/fixed のみ | ⭐ **柱の回転 joint は無い** ⇒ 回転柱は URDF モデル上 DOF を持たない（建てる物なし） |
| cell_base の形状 | **円柱 1 本のみ** r 0.1020 / 長 1.160 / z 0.95 | ⭐ **建った cell の stem と同一値** ⇒ ヨーク部材の形状は URDF に無い（#54 は URDF 自身とは矛盾しない） |
| stereo_head | **`<link name="stereo_head"/>` = 自閉 tag ＝ 形状ゼロの frame**（origin: xyz 0 −0.175 1.485 / rpy 2.356194 0 0） | ⭐ 物理・衝突には存在しない ⇒ **撮影の必須要件ではない**。見た目に欲しい場合は別件（p11 設計・glb/json が source。⚠ 頭は両腕の間 = 88 mm interleave の場所ゆえ、足せば clearance は必ず狭くなる） |
| 取付 origin | **±0.220 / rpy 0.785398（= 45°）** | ⛔ **これだけが現行 run との実逸脱** ⇒ override 2 本で解消 |
| meshes | 腕（UR15 dae 一式）＋ 2F-85 一式のみ | cell/頭/ヨークの mesh は無い |

⇒ **「仕様書どおりの構成」= 現行 code ＋ `YOKE_SPREAD_OVERRIDE=0.22 TILT_DEG_OVERRIDE=45`**（crown は literal 0.110 が built 値と一致 — 0.22/2 の偶然を着地 commit が明記）。

## 5. ⚠ 正直な射程（撮る前に書いておく — 結果がどうであれ報告はこのまま）

1. **built 構成（0.22/45/crown 0.110）の 240-draw witness は「左腕の無干渉開始解 0/240・両腕 +0.0 mm（指令 88 mm span）」**。⇒ **撮り直しは開始付近で接触・stall を映す可能性が高い**。⛔ この測定は 2 度 Rs1 に提示済みで、その上で「撮り直せ」— **そのまま撮り、そのまま報告する**（閾値緩和・回避・kinematic trick は禁止のまま）。
2. 動画名は構成を運ぶ: `ur15_dod_speccell_022_45_20260810.mp4`（→ `~/Downloads`）。**構成 echo（spread/tilt/crown/WORK_ROW_DY・wired content sha）を log と報告に併記**。
3. #48 cap は不変（cable 由来の主張に無印 PASS なし・Rs1 の文言着地待ち）。

## 6. 回付

p18 経由: **p0 = 実行**（§4 の override・§5 の名前と echo）／cc p4（dep 整合・既定値の別決定）／p11（stereo head を見た目に建てるかは Rs1 が求めた場合のみ・standing）／pB・pC（結果の三者照合）。
