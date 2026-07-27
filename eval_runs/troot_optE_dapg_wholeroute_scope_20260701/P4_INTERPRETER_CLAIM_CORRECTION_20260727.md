# p4 原因側訂正 — 「実行 interpreter は未解決」を撤回（追記訂正・amend しない）

**訂正者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-27 10:52:33 JST（date-THEN-write）。
**契機:** p18 RETURN `MSG-P18-P4-DISPOSITION-AND-RETURN-20260727T1050JST-004` 項 3。
**検証:** p18 の指摘を**自分で on-disk 実測して確認**した（他 pane の message の数値では裁定していない）。

⛔ **銀行済み記録は amend / rewrite しない。** 本書が追記訂正の正本。

---

## 1. 撤回する節（所在 4 箇所・すべて私が書いた）

| 所在 | 撤回する文言 |
|---|---|
| `P4_UR15_HANDOVER_TO_IMPL_CHAIN_20260727.md:88` @ `8162d3b2bbced968de3a352c1cb7a3c855e1049a` | 「実行 interpreter が未解決（AGENTS の `./isaaclab.sh -p` 既定解決先に mujoco 無し／`env_isaaclab7` に isaaclab 無し）」 |
| dispatch `MSG-P4-P18-RESUBMIT-P11-P0-PZ-HANDOVER-20260727-012` 本文 (5) | 同旨「interpreter 未解決」 |
| `P4_UR15_RECORDS_CORRECTION_V3_20260727.md` §R7 closure 未凍結項目 4 @ `c0aca0ef498f4bc9f113ddddf2b91e72960f43b8` | 「実行に使う interpreter — **UNRESOLVED**」 |
| 同 v3 §R2 の p11 向け置換本文（実行 interpreter の行） | 「実行 interpreter は **UNRESOLVED**（…）私は決めません」 |

⛔ **上記の「未解決」という結論を撤回する。**

## 2. 私の誤りの型

**測った面と、結論が要求する面が違った。**

- 私が測ったもの = **dist-info の有無**（venv にパッケージが *インストール* されているか）
- 結論が要求していたもの = **import が解決するか**

`env_isaaclab7` に `isaaclab` の dist-info が 0 件であることは真だが、そこから「どちらでそのまま走るかは未解決」は**導けない**。⇒ 自分の memory 教訓「測った量に、それが測っていない結論をぶら下げない」に該当する。

## 3. 実測（本ターン・私自身が実行）

**(a) wrapper の仕組み — `isaaclab.sh:29` 逐語:**
```
export PYTHONPATH="$ISAACLAB_PATH/source/isaaclab:$PYTHONPATH"
```
⇒ `isaaclab` は venv ではなく **repo の `source/isaaclab` から解決する**。venv 未インストールでも import できる。

**(b) 直呼び `/home/rlrk/env_isaaclab7/bin/python`:**

| module | found | origin |
|---|---|---|
| mujoco | ✅ | `/home/rlrk/env_isaaclab7/lib/python3.12/site-packages/mujoco/__init__.py` |
| isaaclab | ⛔ **False** | — |
| warp | ✅ | `…/site-packages/warp/__init__.py` |

**(c) `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -p` — rc=0:**

| 項目 | 実測 |
|---|---|
| interpreter | `/home/rlrk/env_isaaclab7/bin/python` |
| mujoco | ✅ `…/env_isaaclab7/lib/python3.12/site-packages/mujoco/__init__.py` |
| isaaclab | ✅ **`/home/rlrk/IsaacLab/source/isaaclab/isaaclab/__init__.py`** |
| warp | ✅ |

⇒ **AGENTS の wrapper に `VIRTUAL_ENV` を与えれば、mujoco と isaaclab の両方が解決し rc=0 で走る。interpreter は解決している。**

## 4. 撤回の範囲（残す節も同じ検査に通した）

- ⛔ **撤回:** 「interpreter UNRESOLVED」「どちらでそのまま走るかは未解決」「私は決めません」。
- ⭐ **維持:** v2 で書いた **直呼び実行例の撤回**。⚠ ただし**理由を訂正する** — 私は当初「env が足りない」ことを含意していたが、実測では本 script は `isaaclab` を import しない（`ur15_steps.py` の import は mujoco / numpy / scipy / imageio のみ・`isaaclab` の出現 0 件）ため、直呼びでも script 自体は走る。**撤回の正しい根拠は AGENTS 規則である** — `AGENTS.md:50` 逐語「**Use `./isaaclab.sh -p`** to run standalone Python scripts without a `pyproject.toml`」。⇒ 直呼びは *動かないから* ではなく *規則に反するから* 使わない。
- ⭐ **維持:** v3 §R7 本体の **asset closure 欠如 ⇒ model は compile できない**。これは interpreter とは独立の事実で、影響を受けない（銀行ディレクトリに `.stl` 0 件・両 XML の mesh が dir 配下に不在）。
- ⭐ **維持:** 私は rerun していない。本書の実測は import 解決の確認のみで、probe / 動画生成の再実行を含まない。

## 5. 訂正後の正しい記述（3 宛先が読む版）

> **実行 interpreter:** AGENTS `:50` に従い repo root から `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -p <script>` を使う。実測で rc=0・mujoco と isaaclab の双方が解決する（isaaclab は `isaaclab.sh:29` が `source/isaaclab` を PYTHONPATH に注入するため、venv 未インストールでも解決する）。⛔ 直呼び `/home/rlrk/env_isaaclab7/bin/python` は AGENTS 規則に反するので使わない。
> ⚠ **これは実行の認可ではない。** 実行可否は依然として gate（class-B fail-closed / RUN CLOSED）の court。

## 6. 非主張

⛔ 設計しない ／ 実装しない ／ 検証しない ／ 値を採用しない ／ GO を出さない ／ gate flip なし ／ rerun なし ／ 銀行済み記録を amend しない ／ 実行認可を要求しない ／ 他 pane の record を代理編集しない。

---
**p4 cause-side correction = 2026-07-27 10:52:33 JST / RS-TECH-LEAD (`w2:p4`)**
