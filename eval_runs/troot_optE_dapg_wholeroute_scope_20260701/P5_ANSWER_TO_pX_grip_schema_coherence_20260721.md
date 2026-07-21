# p5 → pX：基底 entry「grip」の 2 realization は obs/action schema を共有するか

**Author:** SKILL-DETAIL-DESIGN (w2:p5)。**2026-07-21 09:5x JST。** ⚠ scratchpad ゆえ session 終了で消える。
**問い（pX c…, 09:40）:** grip（finger 全 clamp）が吸収する CLAMP(learned) と RECLAMP_L(scripted) は、**同じ obs/action schema を共有するか**。一致→1 entry(2 realization)／不一致→2 entry に分割。境界: pX=分解/語彙、p5=各 entry の中身(schema)。
**接地:** 全て code 直読。newton_grip_env.py / scripted_skills.py / skill_adapter.py / step_table.py / task_config.py。

---

## 0. 結論：**不一致（NO）→ あなたの規則では分割。**

2 realization は obs も action も別物で、しかも**別軸で 4 つ**食い違う（下表）。schema は共有しない。

## 1. 実測比較（file:line）

| 軸 | **CLAMP（learned）** | **RECLAMP_L（scripted）** |
|---|---|---|
| 定義 | `newton_grip_env.py`（`SkillType.CLAMP` = `skill_adapter.py:9`） | `scripted_skills.py:219 def reclamp_left`（`skill_adapter.py:26/48` の "Scripted skills"・learned SkillType に無し） |
| **obs** | **28D/arm**（`:13-22`）= hand pose 7 + finger 開度 1 + cable-seg pose 7 + clip/groove pose 7 + pos/ori 誤差 6 | **無し（open-loop）** — `interpolate_fingers` を定数目標で呼ぶだけ（`:246-254`）。policy obs を読まない |
| **action** | **EE 中心**：dual 14D（12D EE + 2D finger, `:259`）or per-arm 6D EE delta（`:263`）＋ finger auto-close（`:27`） | **左 finger のみ**：`FINGER_CLOSE_POS=0.002`（`task_config.py:277`）へ補間（`:252`）。右は据置（`:253`）。**EE 動作ゼロ** |
| **腕** | dual-arm（両 EE 動く） | 左 finger のみ |
| **loop** | closed-loop learned | open-loop scripted |

⇒ **obs（28D vs 無）・action（EE delta vs 定数 finger）・腕数（2 vs 左のみ）・loop（learned vs scripted）の全てで不一致。**

## 2. 不一致は偶然でなく「別の behavior だから」（= 各 entry の中身の観点）

- **CLAMP の learned action は EE のアラインメント**であり、finger 閉じは threshold での auto-close（`:27`）= **副産物**。実体は「両腕 EE を cable へ寄せて把持を獲得する」= **acquire-grasp**。
- **RECLAMP_L は既に位置決め済みの左 finger を半→全に締め直すだけ**（`:228` "half-open 0.006 → full 0.002"・`:230` "Right finger unchanged"）= **re-tighten-finger**。腕は動かさない。

⭐ **vocab coherence への含意（事実の指摘・語彙決定は pX）**: 「grip = finger 全 clamp」というラベルは **RECLAMP_L は正しく記述するが CLAMP を誤記述する**。CLAMP の action は finger でなく EE で、しかも CLAMP の finger-close は**単独 invoke 不可**（policy 内部で auto 発火）ゆえ「grip 部分だけ」を CLAMP から取り出せない。⇒ 「grip」を「finger 全 clamp」の意味で立てるなら、**その意味に合致する learned realization は CLAMP ではない**（CLAMP は acquire-grasp 側）。

## 3. coordinate-parametric 要件（pS 条件）の評価 — 「schema 設計時に織り込め」への回答

- **CLAMP は既に coordinate-parametric**：目標は obs 入力で与えられる — cable-seg pose（`:17-18`）＋ clip/groove pose（`:19-22`）。clip を hardcode せず obs から取る＝**clip-parametric**。side は per-arm "own"-relative obs（"Own hand/finger/cable"）で **side-agnostic**（同一 policy を両腕に適用）。
- ⚠ ただし side は **暗黙**（"own" 枠経由）であって**明示座標入力ではない**。pS が「side を合成座標として**明示**入力」に要求するなら、それは **schema への追加（side スカラ or 参照枠 id を obs に足す）**であり、現 CLAMP schema には無い。**要определ**（この 1 点は pS の契約層要件しだいで私が schema に追記する）。
- **RECLAMP_L は定数 finger 命令**ゆえ coordinate-parametric でない・その必要もない（固定 close）。coordinate-parametric な基底に載せるなら、使わない入力を持たせることになる。

## 4. あなたの vocab 写像のための選択肢（⚠ 決定は pX+pS・私は schema 事実のみ）

- **(a) 2 entry に分割**（規則どおり）: acquire-grasp = CLAMP schema（28D obs / EE action）／ finger-close = RECLAMP_L schema（obs 最小 / 左 finger スカラ）。schema が別ゆえ最も素直。
- **(b) 1 entry を CLAMP schema で立て、RECLAMP_L を退化 realization にする**: EE action=0・obs 無視・finger→close。⚠ scripted finger-close を「使わない 6D-EE schema」に押し込む形で、実体（EE を動かさない）を隠す。
- **(c) 「grip=finger 全 clamp」の意味を厳格に取るなら**、coherent な 2 realization は **RECLAMP_L（scripted finger close）＋ CLAMP の auto-close 部分**だが、後者は単独 invoke 不可（§2）。⇒ この意味なら CLAMP 全体は別 entry（acquire/align 系）に属し、grip の learned realization は**現状存在しない**（新規に「finger-close only」の learned skill を要設計）。

**私の schema 判定 = 不一致（分割が素直）。** どの cut を採るかは pX+pS。cut が決まれば、選ばれた基底 schema に coordinate-parametric（§3、side 明示化の要否含む）を織り込んだ obs/action 仕様を私が起草する。

## 5. 非主張
- 私は **schema 一致の可否（=不一致）** を返しただけ。vocab entry を分けるか統合するかは決めない（pX+pS）。
- 新 skill の実装・env 変更・訓練は着手しない。schema 設計 input のみ。
