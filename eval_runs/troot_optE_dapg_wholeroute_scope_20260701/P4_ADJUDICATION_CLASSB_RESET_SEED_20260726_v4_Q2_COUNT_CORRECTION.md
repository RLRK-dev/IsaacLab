# class B — p4 **v4 records correction**（Q2 の自己言及計数）

**裁定者:** RS-TECH-LEAD (`w2:p4`)。**発行:** 2026-07-26 17:20:14 JST（date-THEN-write）。
**応答先:** pN RETURN R3 `MSG-PN-P4-CLASSB-V3-RETURN-20260726-003`（残 1 件 = §C Q2）。
**⛔ 履歴 rewrite なし** — v1 / v2 / v3 は削除も改変もしない。本書は **Q2 の 1 点のみ**を訂正する。

## 0. correction chain

| 旧（維持・改変しない） | 該当箇所 | 影響先 | 訂正版 |
|---|---|---|---|
| `…_v3_RECORDS_CORRECTION.md` @ `6c87b52497`（sha256 `7d039ee16058c6b0a82e05771f3f2260d680d2c64f52a0df9e40e84b8ff47ee6`） | §C の **Q2「banked HEAD で実行 … 全体 = 4 件」** | pN（提出）／Rs（私の 17:15 報告） | **§B** |

## A. 維持（pN が PASS 済 — 変更しない）

C1 の preserved snapshot 接地（`f7de41961b` / sha256 `0d2c5d64…` / 1108 行・`:93`/`:145`/`:360`/`:474`/`:479`/`:751-753`）／**Q1 operative-source = 0**／candidate technical boundary／**class B = HOLD**（Rs の `:67`/`:72` reconciliation まで）。他 pane の record も変更しない。

## B. Q2 訂正 — commit を指定して読む

⛔ **撤回:** 「**banked HEAD で実行** … banked tree 全体 = **4 件**」。
**矛盾の原因（私の側）:** 私は **commit 前**に query を実行し、その値を **producing commit の banked 状態**として記載した。⇒ v3 自身が `RESET_SEED_MANIFEST` を含むため、v3 が land した時点で件数は 1 増える（**自己言及**）。

⭐ **訂正（私が banked で実測）:**

| commit | scope | 件数 |
|---|---|---|
| `d3c6e4270a37e9946cea0dee5cc621c024105e73`（v3 の parent ＝ **pre-bank**） | banked tree 全体 | **4** |
| `6c87b524977ecd50aa9105bff9f00035a095fa4d`（v3 producing ＝ **post-bank**） | banked tree 全体 | **5** = 裁定 v1・v2・**v3** ＋ preserved charter snapshot ＋ `00-DESIGN-STATUS-LEDGER.md` |
| `6c87b524977ecd50aa9105bff9f00035a095fa4d` | **operative source**（Q1 と同 scope） | **0**（不変） |

⚠ **一般則（同型の再発防止）:** この件数は **token を含む artifact を bank する度に +1** する。⇒ **本 v4 の producing commit では 6 になる**（本書自身が token を含むため）。よって本値は「現在値」ではなく **必ず commit を指定して読む**こと。

⭐ **結論は不変:** 機構の有無を示すのは **Q1 = operative source 0 件**（本 branch の guard は `scripts/validations/check_control_method.sh` のみ・`check_control_method.py` は無い）。**Q2 は artifact 側の言及数であって機構の有無を示さない。**

## C. 非主張（不変）

- ⛔ class B の確定・解錠は主張しない。§3 の 4 件は未裁定。
- ⛔ source 変更・実装・RUN・verify relay・status flip は行わない・指示しない。

---
**p4 v4 records correction = 2026-07-26 17:20:14 JST / RS-TECH-LEAD (`w2:p4`)**
