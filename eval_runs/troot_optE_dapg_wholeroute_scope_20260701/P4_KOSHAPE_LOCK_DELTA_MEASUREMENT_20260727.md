# p4 実測 — 移植グリッパ vs banked LOCK 設計の差分（RS71 §0 #4 escalation への材料）

**測定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-27 11:10:13 JST（date-THEN-write）。
**契機:** p18 `MSG-P18-IMPLCHAIN-INTERPRETER-CORRECTION-V2-20260727T1115JST-013` 項 7（p11 発）— 「移植 model の RS71 §0 #4 LOCK 保存が未検証・Rs へ escalate 済」。

⛔ **本書は測定と報告のみ。** LOCK 保存の可否は私（p4）の court ではない。設計判断 = p11 / Rs。

---

## 0. 対象（exact pin）

| file | 状態 |
|---|---|
| **banked LOCK 設計** `thread_isaac_lab/assets/ur5e_robotiq/robotiq_2f85/2f85_koshape.xml` | commit `85315bbec6787a9cfcb3cb147c87fb78beb3b5ca` ／ blob `b4a6158c9d79ea3b67708c6a6bf2ab61ff3ae750` ／ sha256 `a3bef79ee9b4f4161dd6da20967e65e0da78f5706724fbf61e35fb43ba230ba3` |
| **私が認可なく作った移植版** `…/robotiq_2f85/_ur15_2f85_koshape_actuated.xml` | ⛔ **untracked（`??`）** ／ sha256 `c2d65167d32b413bcbf2985a153025e5455a3d5e8051cd89733cb67e11751ffe` |

## 1. ⭐ 保存されているもの（実測・byte 比較）

| 項目 | 結果 |
|---|---|
| コ字爪 geom 4 本（`left/right_pad_f1ext` / `_f2ext`） | ⭐ **byte 一致**（`size` `pos` `quat` `friction` `solimp` `solref` `priority` `rgba` すべて） |
| 爪が載る `right_pad` / `left_pad` body の `pos` | ⭐ 一致（`0 -0.0189 0.01352`） |
| 爪を運ぶ機構 body の `pos`（driver / coupler / spring_link / follower、左右） | ⭐ **10 body すべて一致** |
| `pad_box1` / `pad_box2` class の存在 | ⭐ 双方に存在 |
| `<equality>` 4 節リンク 3 行 | ⭐ 一致 |
| `<actuator> fingers_actuator` | ⭐ 一致（`tendon="split"` / `forcerange` / `ctrlrange` / `gainprm` / `biasprm`） |

## 2. ⛔ 差分 2 件（私が加えた／落とした）

### 差分 A — `<tendon>` を私が**復活させた**

**banked LOCK 設計:** `<tendon>` ノードは**削除済み**で、代わりに理由コメントが入っている（逐語・要点）:

> `<tendon>` node REMOVED. WHY: the combined UR5e+Robotiq add_mjcf build crashes SolverMuJoCo construction at `_init_tendons` … Removing `<tendon>` is the disk-viable Path-A strip … The orphaned `<actuator general tendon="split">` below is SILENTLY skipped at parse … **NOT a faithful gripper — the Robotiq 4-bar grasp is rebuilt at S5 (tendon-OOB fix).**

**私の移植版:** 以下を**追加**した。

```xml
<tendon>
  <fixed name="split">
    <joint joint="right_driver_joint" coef="0.5"/>
    <joint joint="left_driver_joint" coef="0.5"/>
  </fixed>
</tendon>
```

⇒ これにより `fingers_actuator` が実際に効く（banked 版では parse 時に silently skip される）。

⚠ **注記（事実のみ）:** banked の削除理由は **Newton solver（`add_mjcf` → `_init_tendons`）のクラッシュ回避**であり、グリッパ設計上の判断とは書かれていない。私の model は **素の MuJoCo で動かしており Newton を経由しない**。⛔ **それが復活を正当化するかは私が決めない — p11 / Rs の court。**

### 差分 B — 爪同士の接触除外を私が**落とした**

**banked LOCK 設計の `<contact>` に在り、私の版に無い 1 行:**

```xml
<exclude body1="right_pad" body2="left_pad"/>
```

banked 側の直前コメント（逐語・要点）:

> **Prevent claw-claw self-collision jam at the scripted close** (the protruding コ claws `f1ext`/`f2ext` can overlap at `GRIPPER_CLOSE_QPOS`). Cable contact is UNAFFECTED (the cable is a separate body).

⇒ **これは私の単純な脱落。** 他の 6 行の `<exclude>` は双方に存在し一致する。

⚠ **観測との関係（因果は主張しない）:** 私の実測で、全閉指令（`ctrl=255`）に対しパッド間隔が **24.2 mm で停止**し、Ø8/Ø10 いずれのケーブルも爪に入らなかった。banked コメントが記す「爪同士が `GRIPPER_CLOSE_QPOS` で重なって閉が詰まる」現象と**現象面が一致する**。⛔ **私は因果を確かめていない**（除外行を戻した比較を実行していない）。**検証は pZ の court、設計判断は p11 / Rs の court。**

## 3. まとめ（p11 / Rs 向けの単一の答え）

- **コ字爪の幾何そのものは保存されている**（爪 geom・pad body・機構 body すべて一致）。
- **保存されていないのは幾何ではなく、周辺 2 点** = ①`<tendon>` の復活（banked は Newton 都合で削除）②爪同士の接触除外の脱落（私の脱落）。
- ⇒ **「LOCK された形状は保たれているが、LOCK 済みファイルと同一の model ではない」** が実測の結論。

⛔ **私は判定しない。** 上記が §0 #4 の LOCK 抵触に当たるか、当たる場合どちらを直すかは p11 / Rs。

## 4. 非主張

⛔ 設計しない ／ 実装しない ／ 検証しない ／ 因果を主張しない ／ 値を採用しない ／ GO を出さない ／ gate flip なし ／ rerun なし ／ LOCK 面（`2f85_koshape.xml`）を編集していない ／ 他 pane の record を代理編集しない。

---
**p4 measurement = 2026-07-27 11:10:13 JST / RS-TECH-LEAD (`w2:p4`)**
