# WMSO D1.1-C design v2.5.1 — two-key evidence 軸 verify（OPS-SUP）

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**発行:** 2026-07-21 20:52 JST。
**依頼:** `w2:pQ`（v2.5.1 two-key の evidence 軸）。設計軸 = pS PASS-WITH-CONDITIONS 済（`8a3aaa91a951797b…` @ `7c2df663b0`・逐次順守）。
**pS 名指しの pY leg（C-2）:** golden の byte 実算 / pin exact 照合 / open 群の owner・DDR 対応。＋ pQ の 2 主張の独立再測。
**性質:** evidence/custody。⛔設計判定でない（設計軸 = pS）。⛔freeze/scope 縮小を批准しない。

## ⭐ VERDICT: evidence 軸 = **PASS**（全 pin 一致・golden byte 実算一致・claim 1&2 独立確認・open owner 完全）

## (A) pin exact 照合（on-disk 自算・full-40 一致）

| 対象 | sha256(40) | commit | |
|---|---|---|---|
| design v2.5.1 | `97bfda4355b4fc3d287c1ea47f06f690d2d11fa1` | `878b97bc2f`（==on-disk） | ✅ |
| fixtures build_goldens.py | `bc89e9d7148e15ca4ea67f6adac987651e90a631` | `b994b617b5` | ✅ |
| pS record | `8a3aaa91a951797b8c1210cf2e2ee54d2eb656a1` | `7c2df663b0` | ✅ |
| 凍結 contracts_v2 | `00192d20ca00b654…` | intact | ✅ |
| 凍結 tensor_binding v13 | `5a1874d3be8b98b8…` | intact | ✅ |
| 凍結 EP md | `c474acea7c58acc2…` | intact | ✅ |
| 凍結 EP JSON | `e63176af9bc3a246…` | intact | ✅ |

⇒ 土台の**凍結 4 file 全て無傷**・design/fixtures/pS record も cited と完全一致。

## (B) golden byte 実算（登録コマンドを逐語実行・下記 C と同一 run）

`env_isaaclab/bin/python …/wmso_d11c_fixtures/build_goldens.py --verify <fixtures>` 実行 → **golden A-D が on-disk bytes と一致**（builder の pinned GOLDEN_HASHES と一致）:

| golden | sha256 | bytes | |
|---|---|---|---|
| A | `ce474f3ad393767a…` | 224 | ✅ |
| B | `f49d15698bf379c1…` | 376 | ✅ |
| C | `1b88fdc0c95813de…` | 350 | ✅ |
| D | `4971d3f7a6601ff3…` | 285 | ✅ |

⇒ builder（pinned `bc89e9d7…`）→ その GOLDEN_HASHES → on-disk golden が byte 一致 = **golden byte authenticity 成立**。

## (C) claim 1 独立再測 — **CONFIRMED**（⭐pQ の handoff gap を close）

⚠ pQ 申告「私は本 session で再測していない（handoff 由来）」。⇒ **pY が逐語実行**（上記 B と同 run・実測出力）:
- **`controls: 33/33 fired`** ✅
- **`conformance: 4/4 PASS`** ✅
- **`rc=0`** ✅

⇒ 33/33 fired・4/4 PASS・rc=0 を **on-disk 実行で確認**（handoff 数値でなく実測）。

## (D) claim 2 独立再測 — **CONFIRMED**（semantic v2.5 = `988a005f91`）

`E_MANIFEST_LINEAGE_INCOHERENT` 出現数（pY が各 commit の blob を自算）:
- `45bfdfcaca` = **0**（message「a C-side lineage code」に反し本文 0 = label≠pin の broken byte-state）
- `988a005f91` = **3**（新 code 安定 = semantic v2.5）
- `878b97bc2f`（v2.5.1）= **3**

⇒ **semantic baseline = `988a005f91`**（45bfdfcaca ではない）。pQ 主張・pS 独立 count と一致。

## (E) open 群の owner / DDR 対応 — ✅ 完全列挙・owner 付・過小なし

- §8 = 18 open・全て owner 付（§0:28 完全列挙）。DDR 対応: **U-5→#29**（設計する）/ **U-2→#28**（open-1・owner pQ）/ **U-6→#30**（open-1・owner pQ/Rs）/ carry #26 = substrate 選別 policy（§3 恒久遵守）。
- ⭐**open-11（`:172`）= 「承認済 scope IN 5 項を 2 項へ縮小してよいか」= Rs 判断 (c)**・owner = **Rs**。design 自身が §0:6/:33 で「Rs 未裁定」と明記。⇒ **scope 縮小は Rs 専権として正しく open に置かれている**（本 evidence PASS は批准しない）。
- ⭐design は **私の WCJ finding を正しく fold**（`:183`「v2.4 §6『第 2 の凍結波及』を撤回・凍結 fixture は `:198` ASCII-key assert で適合・凍結 chunk 内の非適合は無い」）。
- ⚠ owner ゼロ items（open-13）は「impl CLOSED ゆえ未割当・Rs venue/後続版」と design が説明（`:174`）= 真の ownerless でない。

## 境界・非主張（pQ の boundary を echo）

- ⛔ **本 evidence PASS は scope 縮小を批准しない**（open-11 = Rs 専権・未裁定）。two-key の **verification** は pS 設計軸 + 本 evidence 軸で満たされるが、**freeze / scope 縮小の採択は Rs**（open-11 + freeze gate）。
- ⛔ **impl / training / authority / push / freeze / slice = CLOSED**。
- ⚠ **§運用10 records-consistency note（pS C-1 と同旨）**: doc §0:33/§8:11/:172（縮小=Rs）と §9:185/routing dispatch（(c) を「部分版 two-key / open-freeze の可否」へ reframe）が表記不整合。**substance（open-11 縮小 freeze = Rs 専権）は open list で正しく述べられている**（:172）。表記整合は pQ に推奨（実体は不変）。
- ⛔ 私は設計の当否を判定しない（pS 設計軸）・凍結/source を編集していない（read-only + builder 逐語実行のみ）。

## 帰結

- **two-key の verification 完了**（pS 設計軸 PASS-WITH-CONDITIONS + 本 evidence 軸 PASS）。
- 次 = **Rs が open-11（scope 縮小可否）+ freeze gate を裁定**。⛔ 本 two-key は freeze でも scope 縮小採択でもない。

---
**evidence 軸 = 2026-07-21 20:52 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
