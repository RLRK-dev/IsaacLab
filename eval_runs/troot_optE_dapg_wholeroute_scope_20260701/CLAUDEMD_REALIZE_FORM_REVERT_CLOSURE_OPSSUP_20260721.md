# CLAUDE.md:72 realize-form 追記の revert — OPS-SUP closure + custody gap flag

**Verifier:** T-ROOT-OPS-SUPERVISOR (`w2:pY`)。**発行:** 2026-07-21 19:00 JST。
**契機:** p4 relay — Rs が「すてるなよ」rule を disavow（p4 relay 逐語「そんなルール知らない」）・意図 = 既存 invariant「許可されていない箇所に kinematic を使うな」。p4 が realize-form 追記を revert（`3ef4814f30`）。
**性質:** revert の独立検証 + 私の moot verdict の status 反映 + 残る custody gap の flag。

## ⭐ VERDICT: revert = **独立確認 PASS**・私の 2 verdict = **MOOT（evidence 保持）**・custody gap 2 件を flag

## 1. revert 独立検証（producing commit で実測）

| gate | 実測 | |
|---|---|---|
| revert commit | `3ef4814f30`「Revert clip-pin realize-form clause (unconfirmed premise)」・CLAUDE.md 1 行 | ✅ |
| CLAUDE.md:72 @ `3ef4814f30` == 追記前 `f45670929e` | 両 line72 sha256(16) = `8ccfe388d1496d58` = **byte-identical** | ✅ |
| realize-form 追記 | 現 on-disk line 72 に「認可例外の realize 形」= **0 件**（除去確認） | ✅ |
| ⭐ pin 例外 | 「kinematic の認可例外は clip-retention pin の 1 件のみ」= **1 件（intact）** | ✅ 不変前提 preserved |

⇒ p4 relay どおり。CLAUDE.md:72 は追記前の confirmed baseline に復帰・pin 例外 intact。

## 2. 私の verdict の status 反映（確定事項の即反映）

- **`bff430fd6d2c54fb`（L3 custody-verify）** + **`1cc6da8384f7fb9d`（landed re-confirm）** = 検証対象の realize-form clause が revert された ⇒ **MOOT（governing custody として無効）**。⛔削除しない（evidence 保持）。両 doc 内の逐語記録・§0.5 分析・authorization note は evidence として残る。
- ⭐**authorization note（`1cc6da` §3）は的中していた**: 私は「L3 edit の根拠『それを実行』の係り先が未確認」と flag した。Rs 逐語「そんなルール知らない」で**前提（『すてるなよ』= rule）自体が disavow** ⇒ **未確認前提の上の L3 edit だった**ことが確定。**A′ VOID（`WMSO_D11B_TENSOR_BINDING_DESIGN…:462-465`）と同型** = human 発話への解釈が確認なしに設計/governance 面へ載る型。custody の「brief human 発話に依拠する面は confirm してから stands」規律が機能した。

## 3. ⚠ 残る custody gap 2 件（flag・私の lane 外の記録は owner court）

1. **disavowal 逐語が未 bank**: 「そんなルール知らない」の on-disk custody 記録が無い（grep 0・実測）。revert + §0.5 supersession の authority がこの発話ゆえ、**未記録だと元の問題の鏡像**（未記録の Rs 発話に依拠）。⇒ **p4/p11 court で逐語を bank 推奨**（受領文脈 = 何への応答か・date-THEN-write）。⚠ 私は当該発話を直接 witness していない（p4 relay）ゆえ私は記録者になれない。
2. **§0.5 が stale**: `ARM_CONTROL_FORWARD_DESIGN_SCOPE…:27` は今も「Rs 逐語=すてるなよ」を directive として提示・disavowal flag 無し。⇒ p11 court で supersession flag 反映推奨（P-1 原則の扱いも要再判定 — 「すてるなよ」由来ゆえ）。

## 4. 関連 thread の確認（私の WCJ verdict は confirmed）

- pQ が「第 2 の凍結波及」主張を **retract**（`988a005f91`「the frozen fixture is guarded and compliant」= 私の `641229b6d6f18b3f` finding）+ **open-5 dissolve**（`4f6a9848fc`/`87ba9ee2c0`「frozen spec が identity.canonical_json を adjudicate 済」= 私の Site-2 conditional の解決）。⇒ **私の WCJ verdict は confirmed・Site-2 conditional は pS/pQ が解決**。

## 非主張

- ⛔ P-1 原則（腕・指制御の「物理を捨てない」）の扱い = p4/p11 + Rs（「すてるなよ」由来ゆえ disavowal の射程に入るか要判定）。本 leg は CLAUDE.md:72 の revert に限る。
- ⛔ 私は CLAUDE.md / §0.5 を編集していない（read-only 実測のみ）。p6 が LEDGER/MEMORY 反映中（p6 court）。

---
**closure = 2026-07-21 19:00 JST / T-ROOT-OPS-SUPERVISOR (`w2:pY`)**
