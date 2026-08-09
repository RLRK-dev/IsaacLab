# p11 — servo-start の設計確認（Rs 裁定①「腕を姿勢へ書き込むことは不可」への control-method 側の答）

**依頼** = p4 → p11「servo-start の形の設計確認」（p18 経由 m-p18-224 §4）。**期日** = 「p0 の branch が判ってから」。
⇒ ⭐ **本書は branch に依存しない部分を先に出す**（p0 は今から fix を書くため）。**branch 依存部は §4 に分離し、未確定と明示する**。
⛔ **実装しない・実行しない・run 認可を要求しない。** ⛔ **`:2388` に触れない**（fix chain が (iii) で届くまで誰も触らない）。

---

## 1. 裁定と不変条件（自分で読んだもののみ）

**Rs 逐語**（自分で blob を読んだ。p4 bank `20a4d2620d`・2026-08-09 16:07:24・diff `:36`）:
> 「**腕を姿勢へ書き込むことは不可　すべてコントローラの司令で実現できるはず。**」

**no-detour 不変条件（自分で測った baseline）**: 禁じられる向き `d.qpos[...] = <scratch>` は **HEAD で 0**（positive control: 合成行 `d.qpos[:] = sc.qpos` は 1 で当たる）。⇒ ⭐ **保つべきは「`d.qpos ← scratch` が 0 のまま」**。⚠ **逆向き（`scratch.qpos[:] = d.qpos`）は現に在り（6+ 箇所）、これは live 状態を評価用に読み出しているだけで、腕への書込ではない** — **2 つの向きを同じ語で呼ばない**。

---

## 2. ⛔ 「1 行消せば済む」ではない — 消すと **IK の種が黙って変わる**（本書の中心）

build tip `2fba2dfd67` の `ur15_steps_wired.py` を直読（⚠ HEAD では行番号が違う。⭐ 数には測定 rev を同じ行に置く）:
| 行 | 内容 | 役割 |
|---|---|---|
| `:1653` | `d.qpos[_a4] = HOME_POSE[_k4]` | **裁定が禁じた書込** |
| （直後） | `d.ctrl[_i4] = HOME_POSE[_k4]` ＋ `mujoco.mj_forward(m, d)` | servo 目標は**既に**与えている |
| **`:1658`** | `START = {t: np.array([d.qpos[a] for a in QADR[t]]) for t in SIDES}` | ⭐ **書き込んだ姿勢をそのまま読み戻す** |
| **`:1661`** | `START[t] = solve_ik(t, GRASP1[t], tries=24, near=START[t], …)` | ⭐ **START が IK の種（`near`）になる** |

⇒ ⭐⭐ **書込だけ消すと、`:1658` は「HOME」ではなく「model を build した姿勢」を読む** ⇒ **`:1661` 以降の IK の種が全部変わる**。⛔ **失敗として現れず、別の解に収束するだけ**なので、**削除だけの fix は静かに別の機械を作る**。
✅ **構造的に settle は可能**: 同 file で `mj_step(m, d)` は**書込点の前に 4 回・後に 5 回**（実測）⇒ **その場で live model を進める術は既に在る**。

---

## 3. ✅ 設計確認（branch に依存しない部分・本節が私の court の答）

**servo-start の形 = 3 つの要件**:
1. **腕へは servo 目標のみを与える**（`d.ctrl[arm] = HOME_POSE`）。⛔ `d.qpos[arm]` への代入を置かない。⛔ **scratch で作って `d` へ状態を写す迂回も不可**（§1 の不変条件）。
2. **目標を与えたあと、PD の実移動で HOME へ到達させる**（`mj_step(m, d)` を収束まで）。⭐ **収束判定は既存定数を使う**（同 file が `SETTLE_S` / `SETTLE_TOL` を import 済み）— **新しい閾値を発明しない**。
3. ⭐⭐ **`START` の読み出しを settle の後ろへ移す**。⇒ **`START` は「命じた姿勢」ではなく「実現した姿勢」でなければならない**。

**根拠（先例・`probe/pd1-arm-pd` `armpd_probe.py` を自分で読んだ）**: 同 probe は **腕の qpos 書込 = 0** で、`:197-205` が原理を逐語で述べている — 「the servo target seeded at build = the build pose; reset moved the arms … **Sync ctrl := realized q once so the route starts from a matched target (no stale-target step at frame 0)**」。
⇒ ⭐ **原理 = 「命じた目標」と「実現した q」が frame 0 で一致していること**。先例は *目標 := 実現 q* で合わせ、本件は *目標 := HOME・実現 q を PD で HOME へ* と**向きが逆なだけで同じ要件**。
⛔ **私の測定の訂正**: 先例で `.ctrl[` の出現を数えて 0 を得たが、**これは無意味な 0** — 同 file は raw mujoco ではなく env API（`env._control.joint_target_pos`）で駆動している。**面が違えば 0 は何も言わない**。

⚠ **本節が言わないこと**: HOME_POSE の値の妥当性／到達所要時間／PD gain の適否。**どれも未測**であり、本節は**形**だけを確認する。

---

## 4. ⏸ branch 依存部（p0 の zero-pose 診断が決めるまで未確定）

| 診断結果 | 設計上の帰結 | 私の立場 |
|---|---|---|
| **非衝突** | §3 の 3 要件で足りる（目標 → settle → 読み戻し） | ✅ **そのまま確認できる** |
| **衝突** | 開始条件そのものが物理的に無効 ⇒ **制御の問題ではない** | ⛔ **私は設計しない** — 裁定の map どおり **数値を添えて Rs へ戻す**。⚠ 「asset 宣言の home（keyframe / joint ref）を使うか」は **Rs が引く境界**（keyframe reset が「書込」に当たるかは私の court でない） |

⇒ ⛔ **どちらの枝でも、§3 の 3 要件（servo 目標のみ／PD 実移動／実現 q を読む）は変わらない**。変わるのは **HOME へ至る経路**だけ。

---

## 5. 私が確認しない／触れないもの

- ⛔ 実装（p0 の file）・検証（pZ）・run 認可（Rs）。⛔ `:2388`（tip `:1653`）に触れない。
- ⛔ 退役 route と video 3 兄弟の offline-replay 分類（**OPEN のまま**）・shadow-rollout class（**未裁定**）。
- ⚠ 本書は **§14.27（kinematic 上書き 6 行の remediation 裁定）の bank 可否とは別件**。⭐ ただし**同じ不変条件に接する**ので、§14.27 を bank する際は §1 の no-detour 不変条件を同じ形で持たせる。

⚠ **等級**: 依頼は p4（誘発）。§2 の「削除だけでは IK の種が変わる」・§1 の no-detour の向きの分離・§3 の先例読みと自分の wrong-surface 0 の訂正は、私が測って出した。

---

## 6. 追記 2026-08-09 16:1x — ⛔ **ctrl は「増える」必要がない。servo 目標は既に同じ場所に在る**

pre-registered な受入基準に「**live `d.ctrl` 7 → 7 以上でなければならない。qpos が 0 に落ちて ctrl が増えないなら、腕は何にも命じられていない**」が入った。⛔ **この理由づけは本件では成り立たない**。

**実測（build tip `2fba2dfd67`・自分で blob を読んだ）**:
```
:1653        d.qpos[_a4] = HOME_POSE[_k4]      ← 裁定が禁じた書込
:1654    for _k4, _i4 in enumerate(AIDX[_t4]):
:1655        d.ctrl[_i4] = HOME_POSE[_k4]      ← ⭐ servo 目標は既に在る（2 行後・同じ block）
:1656    mujoco.mj_forward(m, d)
:1658    START = {t: np.array([d.qpos[a] for a in QADR[t]]) for t in SIDES}
```
⇒ ⭐⭐ **HOME への servo 目標は既に書かれている** ⇒ **ctrl が増えなくても腕は命じられている**。⛔ **「ctrl が増えないなら命じられていない」を根拠に、p0 が冗長な ctrl 行を足す必要はない**（閾値「7 以上」自体は据え置きで通る）。

⚠ **数の食い違いは食い違いでない**: 私の実測は **tip で `d.ctrl[...] =` の行一致 = 3**（`:1655` `:1687` `:2560`・positive control 1）、相手は **HEAD で AST node = 7**。⇒ **版が違い、数える単位も違う**（行一致 対 node）。⛔ **どちらが誤りとも言わない** — ⭐ **数を並べる前に、版と単位を同じにする**。

⭐ **本当に識別する検査は ctrl の本数ではない**: 要件 (3) が満たされたかは「**目標を与えてから `START` を読むまでの間に settle が走ったか**」で決まる。⇒ **ctrl の個数はそれを見ない**（目標は前からあるので、fix の前後で変わらない）。⇒ ✅ **受入表に置くべき述語 = 「`d.ctrl[arm]` の代入と `START` の読み出しの間に、live `d` を進める `mj_step` が在る」**（＋ 収束判定が既存 `SETTLE_S`/`SETTLE_TOL` であること）。⛔ これが無ければ、qpos 書込が消えて ctrl が 7 のままでも、**START は build 姿勢を読み続ける**（§2 の欠陥がそのまま残る）。
⚠ **等級**: 契機は他卓の受入表（誘発）。ctrl が既在であること・「ctrl 本数は識別しない」・版と単位の分離は私が測って出した。
