# Rs 裁定 — 記録訂正の bank 可否（records/docs commit gate）

**記録者:** RS-TECH-LEAD (`w2:p4`)。**私は直接の witness**（relay ではない — Rs から p4 への直接 turn）。
**発行:** 2026-07-26 21:23:26 JST（date-THEN-write）。

---

## 1. Rs 逐語

> 推奨で良い

## 2. 受領文脈（この逐語が何に答えたか）

私が Rs へ上げた選択肢は **4 つ**、私の推奨は **A** だった。逐語で再掲する:

> **ご判断いただきたいこと（新規・2 件目）:** 記録の訂正をどう扱うか。
> - **A) 文書・記録のみの commit に限りチェックを省く**（従来の運用。DDR#35 の実態）
> - **B) baseline を直す**（約 1000 ファイル・確定記録の書き換えを含むため不変性と衝突）
> - **C) `eval_runs/` 等を対象外にする**（リポジトリ設定変更＝ L3）
> - **D) 現状維持**（訂正は残せない。誤りが記録上 live のまま）
>
> 私の見立てでは **A が唯一、記録の不変性を壊さずに訂正を残せる**選択肢です（推奨）。

⇒ **「推奨」= A。** ⇒ **A を採用。**

## 3. 判断の根拠となった実測（私自身の測定・pN の所見の再現）

**方法:** 隔離した detached worktree（⛔ 共有ツリーではない）を clean parent **`81779f2a3ec58c0f472ce6e0e9abf1065d6d03e9`** に作成し、`./isaaclab.sh -f` の実体である `python -m pre_commit run --all-files` を実行。

| 項目 | 実測値 |
|---|---|
| 終了コード | **1**（＝ FAIL・pN の所見と一致） |
| 失敗 hook | **8** — `ruff (legacy alias)` / `ruff format` / `trim trailing whitespace` / `fix end of files` / `check that scripts with shebangs are executable` / `debug statements (python)` / `codespell` / `Insert license in comments` |
| **file を書き換えた hook** | **5** |
| worktree 内で modified になった file | **1019** |
| 指摘された file の所在（distinct 1026 件） | `eval_runs` **647** ／ `thread_isaac_lab` **372** ／ `source` **3** ／ `scripts` **3** ／ `docs` **1** |

⚠ **log は私の session ローカルで durable pin を付けられないため artifact として提出しない。** 上記 commit と command で**再現可能**であることをもって接地とする。

**構造上の帰結（A を選んだ理由）:** `codespell` の指摘は **banked immutable artifact の中にも在る**（例 `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P5_CONTROL_METHOD_ANSWER_PRESERVED_20260721/charter_v231.md:455`/`:465`、`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/TRAINER_NODE_DEFINE_RSTECHLEAD_20260712.md:69`、`eval_runs/troot_optE_dapg_wholeroute_scope_20260701/WMSO_D11_SCOPE_DESIGN_RATIFY_WMSODESIGN_20260719.md:90`）。⇒ **all-files を緑にする行為が、記録の不変性を壊す。** B は不変性と衝突し、D は誤った記録を live のまま残す。

## 4. 採用した運用（A の内容）

- **対象 = 文書・記録のみの commit**（`.md` / `.json` 等の records）。**pathspec 限定**で行い、**その path 以外を混ぜない**。
- **リポジトリ全体の pre-commit を通す要件を、この対象に限って課さない。**
- ⛔ **code の commit は対象外**（本裁定は code に適用しない）。
- ⚠ **共有作業ツリーで `--all-files` を走らせない**（§3 実測のとおり 1019 file を書き換えるため）。

## 5. pN の PROCESS HOLD との関係

`MSG-PN-P4-FINGERTIP-H4-DRAFT-PASS-HOLD-20260726-004` は解除条件を **「all-files gate または人間/Rs 別裁定まで HOLD」**と明示していた。⇒ **本裁定が後者に当たり、HOLD は自らの条件により解除される。** 私は pN へ本裁定を full pin つきで通知する。

## 6. 非主張（本書が**しない**こと）

- ⛔ **`CLAUDE.md` / `prohibited.md` を編集しない。** 本裁定を恒久規則の本文にするか否かは**別の Rs 判断**であり、まだ取られていない。⚠ 私は Rs の一言を規則文へ昇格させない。
- ⛔ **gate flip なし** — H-3.1 GO なし ／ H-4 全体 HOLD ／ **class B は `CLAUDE.md:67`/`:72` の文言整合まで HOLD** ／ source・`[CHANGE]`・実装・RUN・verify・status は CLOSED のまま。
- ⛔ 他 pane の record を代理編集しない。
- ⛔ 物理妥当性は判定しない（Rs 動画が最終基準）。

---
**p4 custody = 2026-07-26 21:23:26 JST / RS-TECH-LEAD (`w2:p4`)**
