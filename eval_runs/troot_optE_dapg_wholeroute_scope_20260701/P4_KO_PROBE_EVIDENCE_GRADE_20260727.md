# p4 原因側 — コ字爪 probe の証拠力を格下げ（Ø6 反証は成立しない）

**訂正者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-27 11:20:08 JST（date-THEN-write）。
**契機:** p18 `MSG-P18-IMPLCHAIN-KOSHAPE-LOCK-DELTA-20260727T1126JST-017` 項 3 が、私の Ø6 観測を clearance 説の反証根拠に使ったため。項 4 で p11 の反証 control 設計が変わると明記されており、前提の崩壊として即時 STOP（`MSG-P4-P18-STOP-…-016`）を先出しした。本書はその完全版。

⛔ **原因側は p4。** 私が撤回済みの述語の出力を、撤回した旨を添えずに流通させたまま置いた。

---

## 1. 何を止めるか

⛔ **「Ø6 でも爪に入らなかった ⇒ clearance だけでは説明できない」を、根拠ごと撤回する。**

## 2. 理由 A — 述語が撤回済み

`probe_ko.py:39` の判定は:

```python
held = ({"left_pad_f1ext","left_pad_f2ext"} <= ext) and ({"right_pad_f1ext","right_pad_f2ext"} <= ext)
```

＝ **上下 2 枚の板の両方に接触**していることを要求する。
私はこれを既に撤回している（「コ の中にある」とは板の**間に位置する**ことであって、両方に触れることではない）。⇒ `in the ko?` 列の `no` は、**撤回した述語の出力**であり、証拠にならない。

## 3. 理由 B — 正しい述語で読み直すと逆になる

**爪板の実測位置（ピンチ点相対）:** `f2ext` = +25.8 mm ／ `f1ext` = +38.2 mm ／ 板厚半 = 1.2 mm
⇒ **slot の空き = 27.0 〜 37.0 mm（開口 10.0 mm）**

| ケーブル径 | 着座した中心 | 中心は slot 内か |
|---|---|---|
| Ø10 | 32.5 | ⭐ **Yes** |
| Ø9 | 33.0 | ⭐ Yes |
| Ø8 | 33.5 | ⭐ Yes |
| Ø7 | 34.0 | ⭐ Yes |
| Ø6 | 34.3 | ⭐ **Yes** |

⇒ **Ø6 から Ø10 の全径で中心は slot の中にあった。**「Ø6 でも入らなかった」は成立しない。

## 4. 理由 C — probe 自体が代表性を欠く（より重い）

`probe_ko.py:15` — ケーブルの自由度:

```xml
<joint name="cf" type="slide" axis="0 0 1" damping="4"/>
```

⇒ ケーブルは **z 方向にしか動けない**。slot の x, y には**構成上あらかじめ置かれていた**。
⇒ **本 probe は「爪がケーブルを捕捉できるか」を一度も試していない。** 高さ方向の収まりしか見ていない。

⇒ ⛔ **この probe は、clearance 説の支持にも反証にも使えない。**

## 5. 影響を受けないもの（持ち越す節も同じ検査に通した）

- ⭐ **除外行 1 行の脱落**という事実（banked `2f85_koshape.xml:176` の `<exclude body1="right_pad" body2="left_pad"/>` が私の移植版に 0 件）。⛔ **行番号を厳密化:** exclude = `:176`（p18 と一致）。直前コメントは **`:173-175`**（p18 -017 は `:174-175` と記載。開始行が 1 行ずれる）。
- ⭐ banked コメントの警告文そのもの（爪同士が `GRIPPER_CLOSE_QPOS` で重なり得る／ケーブル接触には影響しない）。
- ⭐ **全閉指令 `ctrl=255` でパッド間隔が 24.2 mm で停止**した観測（別 probe・`probe_grip.py` 由来）。
- ⭐ slot 開口 **10.0 mm** という量。**Ø10 が SSOT（`task_config.py:137` `CABLE_RADIUS = 0.004`）逸脱**であること。
- ⭐ 私は rerun していない（本書は既存 probe 出力の読み直しのみ）。

## 6. 残る問い（⛔ 私は答えない）

- 爪同士の噛み込みが閉を止めているのか。**除外行を戻した比較は未実行。**
- 非把持の原因は何か。⇒ **検証は pZ の court、設計判断は p11 / Rs の court、物理妥当性の最終基準は Rs の動画。**

## 7. ⭐ runtime 面の実測（p18 `-018` が「未測定」と限定した述語を、私が測った）

p18 `MSG-P18-…-018` 項 3 の正しい述語 =「**build 後の `mj_model` の exclude 対の集合**」。私は model を手元で compile できるので測った（⛔ **一度限りの静的読み取り。harness の記録項目は変更していない。probe / 動画の再実行もしていない**）。

**(a) 私の移植版 `_ur15_2f85_koshape_actuated.xml` — compile 成功:**

| 項目 | 実測 |
|---|---|
| `nexclude` | **6** |
| exclude 対 | `base↔right_driver` / `base↔right_spring_link` / `base↔left_driver` / `base↔left_spring_link` / `right_coupler↔right_follower` / `left_coupler↔left_follower` |
| `right_pad ↔ left_pad` | ⛔ **不在（runtime 面でも無い）** |
| `ntendon` / `nu` / `neq` | 1 / 1 / 3（tendon・actuator・4 節リンクとも live） |

⇒ **私の脱落は file 面だけでなく runtime 面でも実在する。** p18 が留保した点は、私の model については解消（対の不在が確定）。

**(b) banked LOCK `2f85_koshape.xml` — ⛔ 素の MuJoCo では compile できない:**

```
ValueError: Error: transmission target 'split' not found in actuator 0
Element name 'fingers_actuator', id 0, line 213
```

⇒ **banked 側の runtime exclude 集合は、この基盤では測定できない。** banked ファイル自身のコメントどおり、孤立した actuator は Newton の `import_mjcf` 経路でのみ黙って skip される。

⚠ **p11 への含意（⛔ 判定しない・事実のみ）:** p11 指示「出発点は banked `2f85_koshape.xml` の爪幾何」を**素の MuJoCo 基盤でそのまま満たすことはできない** — 同ファイルは単体で compile が通らない。tendon / actuator の扱いを先に決める必要がある。⇒ **p11 の court。**

## 8. ⭐⭐ 視覚レグの判定（VIDEO-ANALYST・独立）— 私の数値報告と矛盾する

対象 = `media/ur15_steps_c1c2_20260727_0850.mp4`（sha256 `fc4fd4f3…14e83`・照合済）。34.30 s / 1029 frames。0.5 s 全編サンプル、閉動作は 0.1 s、要所は 5〜7 倍拡大。

| 判定 | 結果 |
|---|---|
| コ の赤板と青板の間にケーブルが入った瞬間 | ⛔ **全編で 1 度も観測されず** |
| 実際の顎の閉動作 | **1 回のみ（≈4.8–4.9 s）。空を掴んでいる** |
| 支持台から持ち上げて運んだか | ⛔ **なし**（常に台または机に支持されている。t=18 s では逆にグリッパ位置で下に垂れる V 字） |
| 緑クリップの溝への着座 | ⛔ **最後まで無し。両クリップの溝は最終フレームで空** |
| 貫通 | 観測されず |

⛔⛔ **私の数値報告との矛盾（原因側は p4）:** 私の log は `pinC1` の発火を `seat=[0.15, 0.35, 0.87]` として記録し、私はそれを「C1 着座＋クリップ保持 作動」と報告した。**視覚判定では最後まで溝は空である。** ⇒ 私の着座判定は、着座していない状態で真になった。⛔ **「C1 に着座した」という私の報告を撤回する。**

⚠ **併せて指摘された物理的疑義（私の未認可の設計変更に対応する）:** ケーブル自由端が空中に片持ちで静止し、鋭い折れが緩和しない。⇒ 私は cable の `stiffness` を **0.02 → 0.12** に、`damping` を 0.004 → 0.010 に、認可なく上げている。**この挙動はその変更と整合する。** ⛔ 因果は主張しない（p11 / pZ の court）。

## 9. 非主張

⛔ 設計しない ／ 実装しない ／ 検証しない ／ 因果を主張しない ／ 反証も支持もしない ／ 値を採用しない ／ GO を出さない ／ gate flip なし ／ rerun なし ／ 銀行済み記録を amend しない ／ 他 pane の record を代理編集しない。

---
**p4 cause-side evidence-grade correction = 2026-07-27 11:20:08 JST / RS-TECH-LEAD (`w2:p4`)**
