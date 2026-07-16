# I0-a commit scope manifest (c60d311f96 の交差開示、pN I0A-B2 対応) — RS-TECH-LEAD %12, 2026-07-16

**事実**: commit `c60d311f96` の `newton_route_env.py` は私の I0-a flip (1 hunk) に加え、**shared working tree に
存在した他実装 (121+/23-) を無開示で同時収録**した。原因 = `git add` 前の per-file diff 検査を怠った (file 変更
警告が edit 時に出ていた)。shared-tree sweep class の再演 — 私の過失。履歴 rewrite はしない (pN 裁定)。

## hunk 帰属 (git show 実測)

| hunk | 内容 | track / 帰属 |
|---|---|---|
| @@ -416 (+13) | **flip (wc default 4→1 + 裁定コメント)** | ⭐**I0-a (%12 本 commit の意図 scope)** — I0-a leg で検証済 |
| @@ -573/-640 | `_wire_c1_pin_from_recording` 常時 C1 identity 化 + **pin witness triple の all-or-none 検査/復元** (prepared recording の pin field 欠落 = 私が g6_live で発見した (d2) recording-plumbing bug への fix) | **pin node track** (LEDGER:57 gate ② 系) |
| @@ -1279〜-1417 | `_seat_crossing(segment_indices=)` 署名拡張 + `_seat_identity_segments` (C1 = pinned seat node を端点とする hard identity / C2 = C1 node 連結) = **FM4 tighten** | **pin node gate ② track** (reward-design 領域) |
| @@ -1460〜-1787 | `_c1_escape_after_seat` post-G3 fail-closed escape guard = **FM3 tighten** + 関連配線 | **pin node gate ② track** |

## 帰属と disposition

1. **著者**: %12 名義の shared tree 上の未 commit WIP (どの session/pane かは本 manifest 時点で未特定 —
   LEDGER:57 は FM3/FM4 tighten を「実装=%12・再verify=p5」と assign 済ゆえ、pin-node 側 %12 作業の見込み)。
   **著者 pane は claim を** — 本 manifest が呼び水。
2. **disposition = intentional-keep + 非批准**: revert は peer の実装を tree/HEAD 双方から消す (working tree は
   本 commit が消費済) ため不可。**ただし c60d311f96 への収録は当該実装の検証・批准を一切構成しない**。
3. **接地すべき検証 chain (owner 側)**: FM3/FM4 = reward-design gate ② の tighten leg (LEDGER:57: 実装後
   **/reward-design 再走 + p5 再 verify + /pre-check**)。pin-witness triple/(d2) fix = pin node の verify leg。
   **本 I0-a はこれらを検証していない** — I0-a leg が証したのは「この複合 source で FF-replay 物理 traj が
   pre-flip banked と byte 一致」のみ (pN 指摘どおり flip 単独の原子 bank ではない)。
4. **I0-a への影響評価**: flip hunk は独立 (default 値のみ)。複合 source 上でも 4 分岐識別性 + byte 一致が
   PASS しており、**I0-a の主張 (tripwire 有効・flip 無変化) は本交差で無効化されない** — が、その最終判定は pN。

## 再発防止 (私の手順修正、即時適用)

- **commit 前 hard step**: `git diff --cached --stat` + per-file hunk 数を意図 scope と照合し、**意図外 hunk が
  1 つでもあれば add をやり直す** (path 単位でなく hunk 単位の検査。`git add -p` 相当の規律)。
- shared file の edit 警告 (「file has been modified on disk」) を見たら、**bank 前に必ず `git diff`全読**。
