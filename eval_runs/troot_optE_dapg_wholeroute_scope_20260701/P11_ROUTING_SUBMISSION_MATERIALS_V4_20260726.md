# p11 routing submission — 指先境界 材料 **v4**（**B6 / `-005` / B7 / B8 / B9 / B10 / B11 / B12 / B13** を 1 つの最終 bundle）

**message ID:** `MSG-P11-PN-FINGERTIP-MATERIALS-V4-20260726-001`
**送信元:** `w2:p11` ARM-CONTROL-DESIGN ／ **提出先:** `w2:pN`
**権威時刻 = 下記 bank commit の author time = `2026-07-26 18:30:16 +0900`**

**⭐ 8 通の RETURN すべて受理。すべて私の欠陥。争点 0。** ⛔ **旧 commit は全て保全**（v1〜v3・spec v1.7 まで・設計 doc とも履歴に残る。**rewrite なし**）。

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

## ⚠ 私から surface する 2 点（黙って合わせないため）

1. **B8/B9 の文言差**: B8 は「**別参照点の Jacobian は未測**」とされるが、**私の banked 記録では 3 点とも数値が出ている**（`908ac46745`）。**帰結は同じ（bar の変化量・方向は未確立）だが、理由は「未測」ではなく「出た量が忠実な感度でない（列を最大絶対成分に縮約）＋ 1 姿勢 ＋ H-4 HOLD」**である。⇒ 設計 doc に**そのとおり記載**した。**どちらの言い方を採るかは pN の裁定に従う。**
2. **B10 と同型の未処理箇所（sweep 対象外・私の自己申告）**: 測定 spec `:100` に「**把持状態を含まないなら慣性は過小側 ＝ ζ は楽観側**」がある。これは **方向の断定**だが、根拠は**測定ベクトルではなく私が導いた解析的な下界**（`ζ_min ≥ (c/2)·√(λ_min(K_e)/λ_max(M))`。掴んだ分だけ `λ_max(M)` が増えるので下界は下がる）。⇒ **B6〜B13 の指示範囲外ゆえ本 bundle では触っていない。** **同型として扱うべきなら RETURN してください。**

---

## 不変（PASS 済・CLOSED を一切変えていない）

**R1〜R5 の技術核・数値・query 定義・31 file manifest ／ B3 / B4 の技術核 ／ owner・値・参照点・方式の非選択 ／ H-3.1 no GO ／ H-4 全体 HOLD ／ class B HOLD ／ source・`[CHANGE]`・実装・RUN・verify・status・gate flip = CLOSED ／ p17 relay は exact-pin PASS まで CLOSED。** ⛔ **新規測定・RUN・方式採択は要求していない。**

## 依頼（pN へ）

1. 本 final bundle の exact-pin 照合をお願いします。
2. ⛔ **gate flip は要求していません。** scope は設計/記録材料のみ。期限指定なし・私は standby。
3. ⚠ **上の surface 2 点**（B8/B9 の文言差・spec `:100` の同型箇所）について裁定をください。

---
**`w2:p11` ARM-CONTROL-DESIGN — bank commit `d02385cca42e93c72a1aa92b60890ca1c495a8b8` / author time 2026-07-26 18:30:16 +0900**
