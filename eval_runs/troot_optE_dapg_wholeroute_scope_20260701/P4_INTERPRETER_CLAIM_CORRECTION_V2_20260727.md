# p4 原因側訂正 v2 — 直呼び撤回の根拠を撤回、および私自身の `rc=0` 根拠を撤回

**訂正者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-27 11:02:50 JST（date-THEN-write）。
**契機:** p18 `MSG-P18-P4-RETURN2-RETRACTION-BASIS-20260727T1102JST-008` 項 3 ＋ p18 advisory `MSG-P18-ADVISORY-WRAPPER-RC-MASKING-20260727T1105JST-009`（出所 = pZ IMPL-VERIFIER）。
**検証:** 両者を**自分で on-disk 実測して確認**した（他 pane の message の数値では裁定していない）。

⛔ **銀行済み記録は amend / rewrite しない。** 本書が追記訂正の正本。先行 = `P4_INTERPRETER_CLAIM_CORRECTION_20260727.md` @ `511e363317a808d79e9a9e3a2e269b67993cffba`。

---

## A. 自分の節を先に撤回 — `rc=0` は合否の根拠にならない

**実測（本ターン・`sys.exit(3)` だけを返す probe）:**

| 実行形 | stdout | rc |
|---|---|---|
| `/home/rlrk/env_isaaclab7/bin/python rc_probe.py` | `probe ran` | **3**（正しい） |
| `VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -p rc_probe.py` | `probe ran` | **0** ⛔ |

両方とも script は走っている（stdout 一致）。**失われるのは終了コードだけ。**
文書側の裏づけ = `AGENTS.md:68` 逐語「**Exit-code exception:** These guard wrappers intentionally call `env_isaaclab/bin/python` directly because `./isaaclab.sh -p` can mask non-zero Python exits.」

⛔ **撤回:** 先行訂正 `P4_INTERPRETER_CLAIM_CORRECTION_20260727.md` §3(c) の表題「— rc=0:」および §5 の「実測で rc=0」。**wrapper の rc を根拠に使わない。**
⭐ **維持:** 「interpreter は解決している」という結論。根拠は `found=True` / `origin=` の観測であり、**rc に依存していない**（mujoco `…/env_isaaclab7/lib/python3.12/site-packages/mujoco/__init__.py`、isaaclab `/home/rlrk/IsaacLab/source/isaaclab/isaaclab/__init__.py`）。

## B. 直呼び撤回の根拠を撤回 — 2 規則は衝突していない

**逐語（本ターン実測）:**

- `CLAUDE.md:82` — 「⚠ **Option-E（mujoco-substrate S-series: S1-S8）の venv は `env_isaaclab7` / Newton 1.2.1（mujoco 3.8.1 / warp 1.13.0）。** … Option-E の smoke/test/build は `/home/rlrk/env_isaaclab7/bin/python` で実行する」
- `AGENTS.md:50` — 「**Use `./isaaclab.sh -p`** to run standalone Python scripts without a `pyproject.toml` (e.g., in CI after switching to a branch with no project files).」
- `CLAUDE.md:23` — `@AGENTS.md`（⇒ AGENTS は CLAUDE.md に取り込まれる規則集であり、対抗する別文書ではない）

**衝突が消える決定的な実測:**

```
VIRTUAL_ENV=/home/rlrk/env_isaaclab7 ./isaaclab.sh -p -c "..."
  sys.executable = /home/rlrk/env_isaaclab7/bin/python
  VIRTUAL_ENV    = /home/rlrk/env_isaaclab7
  PYTHONPATH[0]  = /home/rlrk/IsaacLab/source/isaaclab
```

⇒ **wrapper は `CLAUDE.md:82` が名指しするその binary を実際に起動している。** ⇒ **どちらの形でも `CLAUDE.md:82` は満たされる。** 「どちらの規則が適用されるか」という問い自体が、interpreter に関しては空振りする。

**前置 PYTHONPATH が本 script の import を横取りしないことも実測:**

| module | `source/isaaclab` 配下に存在するか |
|---|---|
| mujoco / numpy / scipy / imageio | **いずれも不在（横取りなし）** |

⇒ 本 script（`isaaclab` の出現 0 件・p18 が銀行 dir の .py 全 7 本で 0 件を実測）に対して、PYTHONPATH の差は**挙動上 inert**。

**⛔ 撤回（2 段）:**
1. 先行訂正 §4 の「撤回の正しい根拠は AGENTS 規則である」— **偽**。`AGENTS.md:50` は条件つき（`pyproject.toml` が無い場合・CI 例）の一般則で、直呼びを禁じていない。`AGENTS.md:68` は逆に、終了コードが要る場面での直呼びを**明示的に是認**している。
2. ⇒ 根拠が残らないので、**v3 §R7(d) の「直呼び実行例の撤回」そのものを撤回する。** 本 script について直呼びは規則違反ではない。

⭐ **維持（同じ検査に通した）:**
- interpreter は解決している（§A のとおり、rc に依らず）
- `v3 §R7` の **asset closure 欠如 ⇒ 銀行 script はこのままでは compile / 実行できない**（interpreter とも実行形とも独立）
- 私は rerun していない（本書の実測は interpreter の import 解決と exit code の確認のみ。probe / 動画生成の再実行を含まない）

## C. 訂正後の正しい記述（3 宛先が読む版）

> **実行形は 2 つとも許容される。両者は同じ binary（`/home/rlrk/env_isaaclab7/bin/python`）を起動する。**
> - **終了コードを合否の信号に使う実行**（負対照・fail-closed guard・「失敗すべき入力で落ちること」の確認）は **直呼び**。⛔ wrapper の rc は非ゼロを飲む（`AGENTS.md:68` ＋ 上記実測）。
> - **repo 内パッケージ（`isaaclab` 等）の import 解決が要る実行**は **wrapper**（`isaaclab.sh:29` が `source/isaaclab` を PYTHONPATH に注入）。
> - **本 script は `isaaclab` を import しない**ので、どちらでも走る。
> ⛔ **判定は artifact の中身（stdout・生成物・log）から読む。実行形の rc から読まない。**
> ⚠ **これは実行の認可ではない。** 可否は依然として gate（class-B fail-closed / RUN CLOSED）の court。

## D. p0 の provenance について（p0 の flag への回答）

p0 の申告 = 測定 run は `CLAUDE.md:82` に従い直呼びで実施、provenance に `python = /home/rlrk/env_isaaclab7/bin/python` / `venv = None` を記録。

⭐ **p4 の見解 = 変更不要。そのまま維持してください。** 理由 = ①直呼びは規則違反ではない（§B）②実行形を変えると `VIRTUAL_ENV` と `PYTHONPATH` の記録値が変わり、「同一入力で同一出力」の比較基準が動く（p0 の指摘どおり）③本 script では wrapper 側の利点（import 解決）が inert。
⛔ **黙って切り替えない。** 統一の裁定が要ると誰かが判断する場合、それは実行標準の変更なので Rs の court。私は決めない。

## E. 非主張

⛔ 設計しない ／ 実装しない ／ 検証しない ／ 値を採用しない ／ GO を出さない ／ gate flip なし ／ rerun なし ／ 銀行済み記録を amend しない ／ 実行認可を要求しない ／ 実行標準を私が決めない ／ 他 pane の record を代理編集しない。

---
**p4 cause-side correction v2 = 2026-07-27 11:02:50 JST / RS-TECH-LEAD (`w2:p4`)**
