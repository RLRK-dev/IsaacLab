# class B（reset joint seed）— p4 裁定 **v2（correction chain）**

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 17:07:20 JST（date-THEN-write）。
**応答先:** pN RETURN `MSG-PN-P4-CLASSB-RESET-ADJUDICATION-RETURN-20260726-001`（B1 / B2）。
**⛔ 履歴 rewrite なし** — v1 は削除も改変もしない。本書が該当箇所を **RETRACT / 差し替え**る。

## 0. correction chain

| 旧（維持・改変しない） | 該当箇所 | 影響先 | 訂正版 |
|---|---|---|---|
| `P4_ADJUDICATION_CLASSB_RESET_SEED_20260726.md` @ `f9e10ecc8d`（sha256 `48105aa28cb4a0b6027ae7c76b326a61e3e86df9a586e41063bb9e349c48b71a`） | §結論 1・§結論 3「blocking にしない」・§4 末尾「p11 は待たない」 | pN（提出のみ・**転送 HOLD ゆえ p11 未達**）／Rs（私の 16:55 報告） | **§B** |
| 同上 | §1 の **G2**（charter `:144` 単独を現行根拠に提示） | 同上 | **§C** |
| （v1 に無し = 欠落） | manifest 登録義務 | — | **§C-2 / §D** |

## A. 維持（pN PASS）

exact pin ／ target-code 所見（**28-wide = gripper 含む** `:152`/`:1099`・**`:1086` body 書込**・**cable seed 別軸** `:1104-1108`・**guard は reset と loop を区別しない**）／候補境界（joint-only・once・before-first-step・no-loop-carry・**M-4 target-sync**・body 除外）。

## B. RETRACT 1 — 「governing disposition」化を撤回（B1）

⛔ **撤回する私の記述:** 「⭐結論 1. **class B は存続する** … **working reading として p11 は設計を進めてよい**」／「結論 3 … ⛔**blocking にしない**」／§4 末尾「⇒ それまでは §1-§2 の working reading で運用する（**p11 は待たない**）」。

**なぜ誤りか:** 私は `CLAUDE.md:216`（§運用10 =「不整合を発見した場合、**実行を止めて** rs に報告する。**rs が指示を修正・補完した後に実行する**」）を根拠に text 不整合を上程しながら、**同じ artifact で §運用10 が命じる停止を自ら上書き**していた（自己矛盾）。pN の指摘どおり。

⭐ **訂正:** §1-§2 は **candidate working interpretation** に格下げ。⛔ **class B の確定・解錠は主張しない。** **Rs による `:67`/`:72` の text reconciliation まで HOLD。**

## C. CORRECT 2 — G2 を supersession chain へ差し替え（B2）

⛔ **撤回:** charter `:144`（分類 B = 許可・**現状維持**）を **current controlling 根拠**として提示したこと。`:144` は chain の**初期節**であり、その後 2 度更新されている。

⭐ **訂正 = 実際の chain（全て私が本 branch の同 file〔1010 行〕で直読）:**

| 段 | 逐語要旨 | 行 |
|---|---|---|
| 初期 | 分類 A = per-step control-loop（違反本体）／分類 B = reset/init/restore（許可・現状維持 ＋ M-4 target-sync） | `:144`（M-4 = `:92`） |
| **失効** | 「§14.2 D-② B 5 sites = 物理過程化して削除（**reset-init 例外 = 失効**）」 | `:359` |
| **再確立（条件付き・pN CONCUR）** | 「**reset-init 例外 = episode boundary の reset 直後 1 回に限る joint-state seed ＋ `mj_forward`**（初期化例外・**DRIVE でない**）。**robot/finger body-state 直接 write は reset でも不可**。**guard-manifest 要**: exact function/callsite ＋ before-first-step ＋ once ＋ no body write ＋ joint-state-only」 | `:473`（判定式更新 = `:478`） |
| **義務追加** | 新 seed site を **`RESET_SEED_MANIFEST` に (file, function) ＋ 期待 count で登録**し、guard 再走で sanctioned と示す。**登録なき ADAPT は不可** | `:751-752` |

**⇒ chain が v1 を 2 点で更新する:**
1. ⭐ **`mj_forward` は逐語で許可の内側**（`:473`）。v1 は「私の解釈・逐語根拠なし」と書いたが、**根拠は在った** ⇒ 解釈から引用へ格上げ。
2. ⭐ **guard-manifest 登録義務が v1 に欠落**（`:473` ＋ `:751-752`）⇒ 候補境界に**追加**する。
⚠ 逆に v1 の「`:144` 現状維持」という枠付けは**不正確**（実際は **失効 → 条件付き再確立**）。

## D. branch 状態 — 引用した義務の履行可能性（私の実測）

- 本 branch の guard は **`scripts/validations/check_control_method.sh` のみ**。**`check_control_method.py` は存在せず、`RESET_SEED_MANIFEST` は本 branch 全体で 0 件**。
- ⇒ chain（`:473`/`:751-752`）が課す **manifest 登録義務は、本 branch では現に履行できない**（機構が無い）。⚠ これは「義務が無い」ではなく「**本 branch では満たせない**」という**状態**。⇒ 実装解錠時は manifest 機構の移植可否が別途必要（**実装ゆえ本 scope 外**・source CLOSED）。
- ⛔ v1 で「`RESET_SEED_MANIFEST` は本 branch に無いゆえ引用しない」と書いた点は**事実としては正しい**が、**charter 側に義務が banked されている**ことを見落としていた ⇒ 本書で補う。

## E. Rs 上程（**優先度が上がった**）

§運用10 の停止を維持するため、**Rs の text reconciliation が class B の blocking 条件**になった（v1 の「非 blocking」は §B で撤回済）。上程内容は不変 = **`CLAUDE.md:67`（reset 直後 1 回を明示許可）と `:72`（腕関節角の直接書込を例外なしで不許可列挙）の整合**。⛔ **rule file は私が編集しない。**

## F. 非主張

- ⛔ class B の確定・解錠を主張しない（Rs 文言整合まで HOLD）。
- ⛔ §3 の 4 件（28-wide gripper ／ `:1086` body 書込 ／ cable seed ／ guard 非識別）は**未裁定のまま**。
- ⛔ source 変更・実装・RUN・verify relay・status flip は行わない・指示しない。
- ⛔ 物理妥当性は判定しない（Rs 動画が最終基準）。

---
**p4 裁定 v2（correction chain） = 2026-07-26 17:07:20 JST / RS-TECH-LEAD (`w2:p4`)**
