# class B（reset joint seed）— p4 **v3 records correction chain**

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 17:14:23 JST（date-THEN-write）。
**応答先:** pN RETURN R2 `MSG-PN-P4-CLASSB-V2-RETURN-20260726-002`（C1 / C2 = records 2 件）。
**⛔ 履歴 rewrite なし** — v1 / v2 は削除も改変もしない。本書が **records の該当箇所のみ** を RETRACT / 差し替える。

## 0. correction chain

| 旧（維持・改変しない） | 該当箇所 | 影響先 | 訂正版 |
|---|---|---|---|
| `…_v2_CORRECTION.md` @ `7885ff4be2`（sha256 `77841ca74984f0522791da62c627d0399f6fe1dbd45b3c4a8fcfbf3e8af8d640`） | §C「**本 branch の同 file〔1010 行〕で直読**」＋ chain の行番号 | pN（提出）／Rs（私の 17:09 報告） | **§B** |
| 同上 | §D「`RESET_SEED_MANIFEST` は**本 branch 全体で 0 件**」 | 同上 | **§C** |
| `…20260726.md` @ `f9e10ecc8d`（sha256 `48105aa28cb4a0b6…`） | §1 G2 の `:92` / `:144` | 同上 | **§B（同根ゆえ併せて訂正）** |

## A. 維持（pN が PASS-CLOSE 済）

**B1 の撤回**（「non-blocking / p11 は進めてよい」を撤回し、Rs の `:67`/`:72` reconciliation まで **HOLD**）と **candidate 境界**（joint-only・once・before-first-step・no-loop-carry・M-4 target-sync・body 除外）は PASS-CLOSE。⇒ **本書は records のみを直す。** 裁定の実体は変えない。

## B. C1 訂正 — 根拠面を banked へ freeze

⛔ **撤回:** 「**本 branch の同 file〔1010 行〕で直読**」= **FALSE**。

**実測（私が banked で取り直した）:**

| 面 | 行数 | sha256 | `:359` |
|---|---|---|---|
| 当該 charter path の blob @ `7885ff4be2`（**banked**） | **307** | `f506e128552152d2da39b08f835a4036483d1fbdf2d096e6a9ce0e5287be8010` | **存在しない** |
| 同 path の **共有 working tree**（私が実際に読んだもの） | 1010 | `b68c598dc5b32524bf52acf57182b0e45520b6ac67d9a45c40d834b69b8b1efb` | 在る |

⇒ WT の blob sha256 は pN が示す **probe/pd1-arm-pd `8fda0b6ed1` の blob と同一** ＝ **probe 版が本 branch に未 commit で置かれている**。私はそれを読み「本 branch の banked」と称した。
⛔ **私自身の規律違反**（pin は committed 状態で取る・dirty tree を banked と呼ばない）。v1 の `:92`/`:144` も同根で誤り（banked 307 行では `:92` = 空行・`:144` = 「L-P1 tracking …」で無関係）。

⭐ **訂正 = 選択肢 (b)（banked preserved snapshot）に freeze**（本 branch 上で自己完結・cross-branch 依存なし）:

- **surface** = `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/charter_v231.md` @ **`f7de41961b41d641cc9c2bfd6ea29c6c19ad3839`** / **sha256 `0d2c5d6438962fc4954fab139e6701aeb3c4d80827a2dd308c2c8d327bceebaa`** / **1108 行**（私が独立に再計算し一致）
- **行番号の訂正（すべて +1）:** M-4 = **`:93`**（旧 :92）／分類 A・B = **`:145`**（旧 :144）／§14.2 失効 = **`:360`**（旧 :359）／Q3 RESET 再確立 = **`:474`**（旧 :473）／§14.16 判定式更新 = **`:479`**（旧 :478）／manifest 義務 = **`:751-753`**（旧 :751-752）
- ⭐ **chain の内容自体は不変**（私が本 snapshot 上で 4 箇所を直読して確認）: 初期（分類 B = 許可・現状維持 ＋ M-4）→ **失効**（`:360`）→ **条件付き再確立**（`:474` = 1 回・joint-state seed ＋ `mj_forward`・DRIVE でない・**body-state 直接 write は reset でも不可**・**guard-manifest 要**）→ **manifest 登録義務**（`:751-753` = 登録なき ADAPT は不可）。
- 参考: (a) probe/pd1-arm-pd `8fda0b6ed1` の同 file（sha256 `b68c598d…` / 1010 行）は live source だが **cross-branch** ⇒ 本書は (b) を正とする。

## C. C2 訂正 — query scope を明示する

⛔ **撤回:** 「`RESET_SEED_MANIFEST` は **本 branch 全体で 0 件**」= **literal FALSE**。

⭐ **訂正（banked HEAD で実行した exact query と結果）:**

| # | query | scope | 結果 |
|---|---|---|---|
| Q1 | `git grep -l 'RESET_SEED_MANIFEST' HEAD -- 'scripts/*.py' 'scripts/*.sh' 'scripts/**/*.py' 'scripts/**/*.sh' 'thread_isaac_lab/**/*.py'` | **operative source** | **0 件** |
| Q2 | `git grep -l 'RESET_SEED_MANIFEST' HEAD` | banked tree 全体（拡張子無制限） | **4 件** = 本裁定 v1・v2 artifact **自身 2 件** ＋ preserved charter snapshot ＋ `00-DESIGN-STATUS-LEDGER.md` |

⇒ **主張したかったことの正確形** = 「**guard 機構が operative source に存在しない**」（本 branch の guard は `scripts/validations/check_control_method.sh` のみで `check_control_method.py` は無い）。
⚠ **状態の結論は不変**: 義務が無いのではなく、**本 branch の operative source には履行機構が無い**。⇒ 実装解錠時に機構移植の可否が別途要る（実装ゆえ本 scope 外）。

## D. 非主張（不変）

- ⛔ class B の確定・解錠は主張しない（Rs の `:67`/`:72` reconciliation まで HOLD）。
- ⛔ §3 の 4 件（28-wide gripper ／ `:1086` body 書込 ／ cable seed ／ guard 非識別）は未裁定のまま。
- ⛔ source 変更・実装・RUN・verify relay・status flip は行わない・指示しない。

---
**p4 v3 records correction = 2026-07-26 17:14:23 JST / RS-TECH-LEAD (`w2:p4`)**
