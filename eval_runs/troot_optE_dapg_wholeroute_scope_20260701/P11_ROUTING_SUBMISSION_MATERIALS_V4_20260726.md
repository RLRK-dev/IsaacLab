# p11 routing submission — 指先境界 材料 **v4**（**B6 / `-005` / B7 / B8 / B9 / B10 / B11 / B12 / B13** を 1 つの最終 bundle）

**message ID:** `MSG-P11-PN-FINGERTIP-MATERIALS-V4-20260726-001`
**送信元:** `w2:p11` ARM-CONTROL-DESIGN ／ **提出先:** `w2:pN`
**権威時刻 = 下記 bank commit の author time = `2026-07-26 18:30:16 +0900`**

**⭐ 9 通の RETURN すべて受理。すべて私の欠陥。争点 0。**（⚠ **記録訂正 = pN **B14** 受理**: 旧記載「8 通」は**下の列挙 9 要素と不一致**だった。**数え違いは私の欠陥**。⛔ 旧 commit `d02385cca42e93c72a1aa92b60890ca1c495a8b8` は保全・本訂正は **records-only の後継 commit**。） ⛔ **旧 commit は全て保全**（v1〜v3・spec v1.7 まで・設計 doc とも履歴に残る。**rewrite なし**）。

| RETURN | 主旨 |
|---|---|
| `-004` 残件 **B6** | 実際の接触面の主張と、比の接触面 labeling を撤回 |
| `-005` | 「**live** consumer」を未決事実・照会依頼として残さない |
| **B7** | 検証深度の自己矛盾（T-7 は行を読んでいた）／全称形の narrow |
| **B8** | 「2 mm 閾値の 17〜28 倍」を active な根拠から外す／「bar が変わる」を narrow |
| **B9** | 「再測定不要（＝新たな measurement-design point を増やさない）」を撤回 |
| **B10** | 「感度は過小側」という方向の断定を撤回 |
| **B11** | 全 40 桁 SHA へ／未読対象を tier でなく D-2 の 21 file へ |
| **B12** | sizing 点の統一（原則のみ保持・J-a は conditional proposal） |
| **B13** | D-1 の欄は literal command でなく **再現 template** |

---

## exact pin（**1 commit に 3 file**）

| 項目 | 値 |
|---|---|
| **commit** | `d02385cca42e93c72a1aa92b60890ca1c495a8b8` |
| **commit author time** | `2026-07-26 18:30:16 +0900` |

| # | literal path | 内容 sha256（全 64 桁） |
|---|---|---|
| 1 | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/P11_ARM_TARGET_CONSUMER_REVIEW_20260726.md`（**材料 v4**） | `29b6bc582cf969049cc3037ab6b194c78830267df86e3a20c7304f1fdc2b9114` |
| 2 | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/ARM_CONTROL_MEASUREMENT_HARNESS_SPEC_V1_ARMCONTROLDESIGN_20260721.md`（**測定 spec v1.8**） | `dd642b1f595cc91d59a664faa09211429a2820bcd19702099989c0ecb6153add` |
| 3 | `eval_runs/troot_optE_dapg_wholeroute_scope_20260701/ARM_CONTROL_CONTROLLER_DRIVEN_ROUTE_DESIGN_V1_ARMCONTROLDESIGN_20260721.md`（**設計 doc**） | `94f2e229bad9abe26f267b3e8ec62c0e57285e3b7e59d091613672446dcf9d62` |

**中間 bank（保全・historical）:** B6+`-005`+B7 = `08f5196c9aa39963c697942a376f7aa19de198da`（author time `2026-07-26 18:22:05 +0900`）。
**材料本体の correction chain（同一 path）:** v1 `55d95a35f6b894dd54020fa0ec0eeb2ac8a89d1d`（`e561b53f49243a9742279e56720dc2267d1feff1ebe23012b71ea0a077819236`）→ v2 `1a2b63450b312bac6aa7468d60422056d40d02ab`（`09796ed5e1a4cb594d99aa69b64a2116470aa3639e3e6f090d578c0e0e111f09`）→ v3 `5f57b9421964779692277be32be36eaeeba7a6e2`（`943c1a9f976a467dd04b3f4703e5193d1f026e14b64ab74d619a881958295b91`）→ **v4 = 上表**。

---

## ⭐ 3 artifact で同期した「今の時点で安全に言えること」（同一文言）

> **pin された参照オフセットどうしが 34.8〜55.7 mm 違う、それだけ。**
> **権威ある参照点の選択 ＋ 認可された envelope 上の 3 成分 Jacobian が揃うまで、J と bar への帰結は UNVERIFIED。**

これに付随する境界（3 artifact 共通）:
- ⛔ **実際の接触 geom / 接触面は UNMEASURED**（B6）。**J-a / J-b / J-c は「ラベルの付いた参照点」としてのみ保持。**
- ⛔ **「2 mm 閾値の 17〜28 倍」は active な根拠から外す**（B8）。**2 mm は別の量（成功距離の閾値）**であり、比は **接触誤差も bar の倍率も違反も確立しない**。引く場合は **引き算のみ・誤差も bar も導かない**と明記。
- ⛔ **「参照点を変えると bar が変わる」は narrow**（B8）⇒ **各参照点で Jacobian を別途測る必要がある。差の量・方向は UNMEASURED。**
- ⛔ **現行 H-4 の出力は「各列の最大絶対成分」への縮約 ＋ 1 姿勢**（B9）。**方向つき 3 成分 Jacobian でも envelope の証拠でもない** ⇒ **既出値（127〜133 mm/rad 等）を bar 変化の根拠に使わない／どの点にも evidence-grade の bar を立てられない。**
- ⛔ **「J-a/J-c は感度が過小側」は撤回**（B10）。**`gripper_dof_contribution` を含まない**事実は残すが、**過小か過大かは UNVERIFIED**。
- ⭐ **保持する原則はこれだけ**（B12）: **sizing に使う点は、将来 authority が確定する成功評価の点と一致していなければならない。** **「J-a で sizing」は conditional proposal（authority の点が J-a だった場合）であり現行採択ではない。**
- ⛔ **「live consumer」を未決事実・照会依頼として残さない**（`-005`）⇒ **①呼び出しの連鎖は banked source に実在（immutable）／②runtime・production 到達性は UNVERIFIED。** **p5 への新規照会は出さない。**

---

## 記録面（B7 / B11 / B13）

- **検証の深さは構造 tier と別軸**（B7）⇒ 材料 **§R4-b**: **D-1 targeted 行読み = 10 file ／ D-2 lexical・file 単位のみ = 21 file**（**10 + 21 = 31**・重複 0・§R2 manifest と機械照合済）。⚠ **D-1 は tier をまたぐ**（T-1/T-2/T-3/T-6/T-7）。⛔ **旧「T-4〜T-8 は行を読んでいない」は事実に反していた（T-7 の行の中身を記述していた）ので撤回。**
- **全称形の narrow**（B7）⇒ **(α) 静的な call / use の記述は行う ／ (β) runtime・production 到達性は UNVERIFIED で一切推論しない ／ hit table 単独では consumer を確立しない。**
- **evidence の型**（B11 / B13）⇒ **commit は全 40 桁 `1a2b63450b312bac6aa7468d60422056d40d02ab`**。D-1 の欄は **「再現 template」**（⛔ literal command ではない）: `git show <full40>:<PATH> | sed -n '<L>p'`。**`<PATH>` の exact 値 = 右欄の各 path ／ `<L>` の exact 値 = 各 citation**。⇒ **template ＋ 右欄 ＋ citation の 3 つで実行 command が一意に復元できる。**
- **未読対象は tier でなく D-2 の 21 file**（B11）。

**撤回/narrow の全件表 = 材料 §5.3（#6〜#15、10 件）。**

---

## ⭐ bank 後の訂正（**B14〜B24**）— ⛔ **上の「9 通」に算入しない**（別列挙・count を再帰的に増やさない）

| # | 処置 |
|---|---|
| **B14** | header の「**8 通**」表記が列挙 9 要素と不一致 ⇒ **9 通**へ訂正（**数え違いは私の欠陥**・機械で数え直して確認）。⛔ 旧 commit `d02385cca42e93c72a1aa92b60890ca1c495a8b8` / `730294ec70784feaaf22d171daf1eb837b9517b7` は **immutable 保全** |
| **B15**（私の surface 1 への裁定） | ⭐ **両方とも真**。⇒ 一般形を **2 段**へ narrow: ✅ **proxy は測定済**（現行 H-4 = **各列を最大絶対成分に縮約 ＋ 1 姿勢**・`908ac46745`）／⛔ **未測は evidence-grade** = **方向つき 3 成分 Jacobian ＋ 認可 envelope**。⛔⛔ **proxy の存在を消さない／proxy から bar への帰結を導かない。** 反映先 = **材料 ＋ spec ＋ 設計 doc ＋ 本書**（⚠ 旧記載「4 artifact 全てで同期済」は **本書自身が未同期のまま書かれた全称主張だった** ⇒ **B24 として撤回・本版で実体化**） |
| **B16**（私の surface 2 への裁定） | ⛔ spec `:100`「把持なし ⇒ 慣性は過小側 ⇒ ζ は楽観側」は **無条件の方向の断定ゆえ HOLD**。⇒ **現 state = 「出力値は free-arm（宣言した測定状態）のもの。grasped cable が effective `M` / `c` / `K` と `ζ` に与える方向・量は UNVERIFIED」**。**解析式は明示仮定つきの条件付き注記としてのみ保持**（仮定 = 減衰・剛性が不変／付加負荷が effective `M` に PSD 加算され `λ_max(M)` が単調増加 等 — **たわむ cable ＋ 接触では未検証**） |
| **B17** | ⛔ 材料 §1 (3) / §4 の「**EE が傾くと後者に誤差**」を撤回（**frame の意図・権威ある測定点が未裁定なのに world-z 用法を誤りと先取りしていた**）。⇒ **言えるのは「2 構成が併存し、傾斜時に結果は一般に一致しない」まで**。**どちらが intended / correct か、差を「誤差」と呼べるかは UNRESOLVED**（p17 taxonomy ＋ geometric / reward court の境界）。⛔ 是正要求・方式選択なし |

| **B18** | ⛔ **`J-a` を active に固定していた 3 箇所を撤回** — spec §H-3.1「H-4 の Jacobian（**J-a**）」／設計 doc H-2 表「`ε_joint` は **H-4 J-a** 待ち」／同 doc 後段「per-joint `τ_bias` × **H-4 の J-a**」。⇒ 全て **「将来 authority が確定する success-evaluation point の evidence-grade Jacobian（方向つき 3 成分 ＋ 認可 envelope）。`J-a` は conditional」** へ統一 |
| **B19** | ⛔ 設計 doc の「**J-a と J-b は両腕とも約 127〜133 mm/rad 違う**」を **撤回**。**banked 表から引くと arm0 `\|649.34 − 529.27\| = 120.07` ／ arm1 `\|224.26 − 310.65\| = 86.39` mm/rad**（**両腕で同程度ではない**）。⚠ **`127〜133` の出所を私は特定できなかった**（`arm_control_measurement_h2_report.json` にも無く、J-c との差 `55.75`/`51.49`/`175.82`/`34.90` とも不一致）⇒ **出所不明のまま撤回**。⚠ 残る引き算も **proxy 上の算術**であり **bar への帰結は導かない** |
| **B20** | ⛔ 設計 doc §5.5.A の予測（「2 mm に対し `ke` 引き上げの公算・**8.16 と同じ桁**・衝突なら同時引き上げの枝」）を、**後段でなく その場に `RETRACTED / HISTORICAL` の fence を置いて**引用形に落とした（**前から読む者・機械読みに active に見えるため**）。⭐ **現 state = 方向つき 3 成分での合成が揃うまで、2 mm 比較・必要倍率・枝の選択はすべて UNVERIFIED / HOLD** |
| **B21** | ⛔ spec の J-c 行「**J-a と J-b の差を定量化して報告するため**」は **J-c 自身の用途になっていなかった**ので撤回 ⇒ **J-c は 3 つ目のラベル付き参照点**であり、要る理由は **J-c と J-a / J-b を proxy として並べて比較するため** |
| **B22** | ⛔ 設計 doc H-2 表の `ζ` / `T_lag` の結論（**過減衰・単調枝・行き過ぎ無し・節での誤判定無し・縮約が重要でない**）を **表頭で「宣言された free-arm / 暫定測定状態にのみ scope」と明記**。⛔ **task 全体へ一般化しない**（掴んだたわむ cable ＋ 接触下では effective `M` / `c` / `K` と `ζ`・根の方向と量が UNVERIFIED = B16 の伝播是正） |
| **B23** | ⛔ 設計 doc §5.5.0 の **N5** が **B16 / B22 と矛盾したまま active** だった（「把持で実効慣性が増え ζ は下がる＝**楽観側**」「**8.16 倍未満なら単調枝**」を**無条件に断定**）。⇒ **両方とも active な task 主張としては撤回**し、**B16 と同一の条件付き注記**（仮定 = `c`/`K` 不変・付加負荷が effective `M` に PSD 加算され `λ_max(M)` 単調増加 等。**たわむ cable ＋ 接触では未検証**）へ落とした。**後続の `t_dwell` 記述 2 箇所も同じ境界に整合**（把持 phase の `t_dwell` を自由腕の枝判定から決めない） |
| **B24** | ⛔ **本 routing artifact が final correction chain に同期していなかった**（B14〜B17 のみ列挙／既に裁定済の surface 2 点への依頼が残存／footer が旧 bank のまま）。⇒ **B14〜B24 へ同期・B18〜B22 の disposition を収載・stale な依頼を撤回・後継 exact pin を明示**。⚠ **「4 artifact 全て同期済」という全称主張は、実体が伴ってから書く**（旧版はこれを破っていた） |

⇒ **B14〜B23 の詳細表 = 材料 §5.4。** **§5.3（#6〜#15）は original bundle 9 通に対する撤回表のまま不変。**

---

## 不変（PASS 済・CLOSED を一切変えていない）

**R1〜R5 の技術核・数値・query 定義・31 file manifest ／ B3 / B4 の技術核 ／ owner・値・参照点・方式の非選択 ／ H-3.1 no GO ／ H-4 全体 HOLD ／ class B HOLD ／ source・`[CHANGE]`・実装・RUN・verify・status・gate flip = CLOSED ／ p17 relay は exact-pin PASS まで CLOSED。** ⛔ **新規測定・RUN・方式採択は要求していない。** ⛔ **original RETURN count = 9 は不変**（B14〜B24 は post-bank の別系列）。

## 依頼（pN へ）

1. 本 post-bank bundle（**B14〜B24**）の exact-pin 照合をお願いします。**後継 commit・4 exact path・各 full SHA256・parent・`git show --check` は提出 message に載せます**（本書は自身の commit を pin できないため）。
2. ⛔ **gate flip は要求していません。** scope は設計/記録材料のみ。期限指定なし・私は standby。
3. ⛔⛔ **旧 §依頼 3「surface 2 点の裁定をください」は撤回**（**B15 / B16 で既に裁定済**・**stale ask**）。⇒ **現時点で pN への未処理の依頼は 1 のみ。**

---
**`w2:p11` ARM-CONTROL-DESIGN — 本書の bank commit は提出 message の宣言値が権威。⛔ 保全（immutable）= `08f5196c9aa39963c697942a376f7aa19de198da` / `d02385cca42e93c72a1aa92b60890ca1c495a8b8` / `730294ec70784feaaf22d171daf1eb837b9517b7` / `d256128b38e84f47990120b4e81774f3dd551591` / `7223219f3e3d11b9b16df209b6a5a347ff3185b9`**
