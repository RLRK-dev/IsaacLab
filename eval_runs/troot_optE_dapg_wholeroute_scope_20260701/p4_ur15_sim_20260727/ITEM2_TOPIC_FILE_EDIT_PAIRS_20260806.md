# ITEM 2 — EVIDENCE ONLY: the two topic-file edit pairs

⛔ **This file states NO disposition.** It contains no recommendation about A, B or C, and it
discharges nothing. It is an INPUT to Rs's item 2 and not a part of it. Banked under p18's
RULING B (2026-08-06), whose conditions were: evidence only, no disposition language, do not
touch the memory files, label as input rather than discharge.

## Why this exists

Of the four memory-directory files p4 wrote on 2026-08-04, two have a pre-write backup on disk
(`MEMORY.md` newest 07-21 17:24, `handoff.md` newest 08-02 23:58) and **two have zero backups**.
For those two the pre-write state existed nowhere but in p4's own record, so any claim about
byte-exact reversibility was self-verified. This file records the transformation itself, so the
claim can be recomputed by anyone instead of taken on one desk's word.

## Slots, all emitted (empty ones say so)

```
inputs   : the two memory files as they stand, plus the edit pairs below
operation: replace new_string by old_string, once, in each file
output   : the pre-write state, sha256 recorded per file below
env      : (not an input — no program is run by this file)
settings : (none)
written  : 2026-08-06 09:18:54 JST by p4
```

## Independent attestation

The pairs below are transcribed from the session transcript, not retyped: session
`9e3d21d6-f86b-478f-b9ad-3e1ebf2862c0`, which records **exactly one** `Edit` call per file.
Anyone with the transcript can compare these strings to the tool-call arguments.


## `reference-busy-wait-loop-stole-a-core-from-the-sim-2026-07-28.md`

- Edit at `2026-08-04T05:51:20.717Z` (UTC) — one call, the only one on this file in the session
- current file : 2398 chars, sha256 `13f4f77c6a299bac7151dc656163a9767d485b47cd8b2fe6a8146085e3224e8b`
- occurrences of new_string in the current file: **1** (must be 1 for the pair to be unique)
- recomputed pre-write state: 1220 chars, sha256 `61e2be9304828b089c03d7de7ef0e8a78065a29dece00329a84dcbee7382de54`
- old_string: 188 chars, sha256 `488d0167a671d7c573b2e8568a7b11e6f6c32efc867a5e02ccb6d59e4947257c`
- new_string: 1366 chars, sha256 `d770ad0b1df1a5dfffae7c48dffa726a28a56ac0169143e2aec4438735807e74`

### old_string, verbatim

```text
関連 → [[feedback-do-not-hang-a-conclusion-on-a-quantity-that-did-not-measure-it-2026-07-26]] [[feedback-confirming-measurement-is-not-root-cause-isolation-reconcile-the-control-2026-07-18]]
```

### new_string, verbatim

```text
---

## ⭐⭐ 待つ**対象の同定**（2026-08-04 追記 — 同じ turn で 3 形すべて踏んだ）

待ち方が正しくても、**待っている相手が違えば検査は何も識別しない**。実測で外れた 3 形:

1. ⛔ **`$!` は起動した python でなく常駐 shell を返した** — `… nohup python x.py >> f 2>&1 &` の直後の `$!` が **951726**、実体は **951727**。951726 の `comm` は `bash`、`stat` の starttime は **5.8 日前** = Claude Code の持続 shell。⇒ **pid を信じず `cmdline` で引く**:
   `for d in /proc/[0-9]*; do case "$(tr '\0' ' ' < $d/cmdline)" in *x.py*) case "$(cat $d/comm)" in python*) echo ${d#/proc/};; esac;; esac; done`
2. ⛔ **`pgrep -f 'x.py'` / `ps -eo … -p PID`** — 前者は**起動した shell 自身**（cmdline に文字列を含む）も拾い、bracket 回避 `x[.]py` でも harness の wrapper は残る。後者は **`-eo` が `-p` を上書き**して全プロセスを出す。
3. ⛔ **「ファイルが伸びなくなった」を「走り終わった」と読まない** — 出力が block-buffer され、計算 phase では 30 秒以上無音になる。実測: 216 行で 3 回連続同数 → 「settled」と出たが**プロセスは生存**。
   ⇒ 終了述語は**プロセス消滅**（cmdline 照合つき）か、**出力自身の終端印**（例: 走行末尾にしか出ない行が期待個数あるか）で置く。

⭐ 共通形は [[feedback-a-predicate-that-cannot-discriminate-is-not-evidence-2026-07-21]] と同じ — **「生きている/終わった」を答えられない検査で生死を判定していた**。

⚠ 付随: `cd` は harness の shell に**残る**。前の call の `cd` のせいで同じファイル名が「無い」と返る。⇒ **長い待ち/走行を跨ぐ command は絶対パス**。

関連 → [[feedback-do-not-hang-a-conclusion-on-a-quantity-that-did-not-measure-it-2026-07-26]] [[feedback-confirming-measurement-is-not-root-cause-isolation-reconcile-the-control-2026-07-18]] [[feedback-a-predicate-that-cannot-discriminate-is-not-evidence-2026-07-21]]
```

## `feedback-a-pass-must-carry-the-scope-of-its-query-2026-07-27.md`

- Edit at `2026-08-04T06:42:40.080Z` (UTC) — one call, the only one on this file in the session
- current file : 2991 chars, sha256 `b97ce024ffe5099952a72c5874586e0aa96a4335bc605e30912ae09a776cc778`
- occurrences of new_string in the current file: **1** (must be 1 for the pair to be unique)
- recomputed pre-write state: 2060 chars, sha256 `4e7fe4622f8d94ed519346b8bfbbf8cffb93fff049fe6e4cf877058bd898c4d8`
- old_string: 149 chars, sha256 `47aa4976443f7247534e2c46aa02bb41e7d7dec945910415dac325def7cef964`
- new_string: 1080 chars, sha256 `21d170da1ebfcbc27ce3a249adb41f706764fc6b47598f4154fb636d15244d98`

### old_string, verbatim

```text
[[feedback-a-predicate-that-cannot-discriminate-is-not-evidence-2026-07-21]]
[[feedback-calibrate-retraction-scope-downgrade-not-nullify-2026-07-26]]
```

### new_string, verbatim

```text
⭐⭐⭐ **2026-08-04 の形: 比較を成立させるために正規化したなら、判定の語も正規化された語でなければならない。**
差分を取るために `sed` で行番号を潰し、そのうえで「**300 行がバイト一致**」と書いた。⛔ 生で数えると **295 一致・
9 相違**。潰した 5 行がそのまま差（295+5=300、9−5=4）として出ていた。⇒ ⭐ **「バイト一致」は媒体についての主張**
であって、私が実際に回したのは**正規化後の一致**だった。⚠ 危険なのは、この誤りが**厳しく聞こえる語で報告される**
こと — 甘い判定は疑われるが、**実際より厳しく聞こえる判定は疑われない**。

⭐⭐ **裏面（相手側が同日に自認した形）: control の単位は、主張が語る量であって、印字される媒体ではない。**
「既存行が**バイト再現**すること」という control は、**行が自分の行番号を印字する file では、正しい変更でも誤った
変更でも落ちる** — 識別しない述語が、測定でなく control の位置に入っていた。⇒ 正しい単位は「**全ての数値が再現し、
引用された行番号は上に挿入した行数だけ動く**」。⭐ 後者は前者より**弱く見えて強い**（動くべきでないものが動かな
かったことも検証する）。

**How to apply（追加）:**
5. 比較の前処理（正規化・除外・丸め）を 1 つでも入れたら、**判定文にその前処理を書く**。書かないなら前処理を外す。
6. control を設計するとき「**これは正しい変更と誤った変更を別々に落とすか**」を先に問う。落とさないなら control ではない。
7. 数え上げを報告するときは**母集団を書く**（同日、私の 19 と相手の 29 は**どちらも正しく**、母集団が違っただけだった —
   19=動いた token、29=差分行の行番号 token 全部、30=file 全体）。

[[feedback-a-predicate-that-cannot-discriminate-is-not-evidence-2026-07-21]]
[[feedback-calibrate-retraction-scope-downgrade-not-nullify-2026-07-26]]
[[feedback-refutation-is-self-certifying-agreement-is-not-2026-07-14]]
```

## What this does NOT establish

⚠ This derives the pre-write state from a recorded transformation. It is **not** a pre-write
copy. The derivation is checkable — apply the replacement, compare the sha — but the claim that
these pairs are what actually ran rests on the transcript, not on an independent snapshot of
the files as they stood before 2026-08-04. No such snapshot exists for these two files.
