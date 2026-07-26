# p11 routing submission — 指先境界 材料 **v4**（original bundle 9 通 = **B6 / `-005` / B7 / B8 / B9 / B10 / B11 / B12 / B13** ＋ post-bank **B14〜B39**）

**message ID:** `MSG-P11-PN-FINGERTIP-MATERIALS-V4-20260726-001`
**送信元:** `w2:p11` ARM-CONTROL-DESIGN ／ **提出先:** `w2:pN`
**⭐ 権威ある pin・時刻 = 提出 message の宣言値**（本書は自身の commit を pin できない）。📎 original bundle の bank = `2026-07-26 18:30:16 +0900`。

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

## exact pin

⛔⛔ **本節は original bundle（9 通）を bank した時点の pin であり、📎 HISTORICAL。** ⭐ **現行の後継 pin（B14〜B39 反映後の commit・parent・4 path の full SHA256・`git show --check`）は、提出 message の宣言値が権威**（本書は自身の commit を pin できない）。⛔ **保全（immutable・全 40 桁。⛔ 短縮 SHA は exact-pin routing 規則に反するので使わない = B31。⚠ **B39 の際に、その後着地した 3 件（`db6ed80b…` / `35dccdd2…` / `e56fb3cd…`）を私の判断で追記した** — B31 が直したのと同じ「一覧が手前で止まる」欠陥の再発を防ぐため。提出 message で申告済）**:
`08f5196c9aa39963c697942a376f7aa19de198da` / `d02385cca42e93c72a1aa92b60890ca1c495a8b8` / `730294ec70784feaaf22d171daf1eb837b9517b7` / `d256128b38e84f47990120b4e81774f3dd551591` / `7223219f3e3d11b9b16df209b6a5a347ff3185b9` / `b1e41dfdebc602c63fdc51728b7d5e989c151277` / `db6ed80b30e7a475831c69a1f9f4420ec193cb5e` / `35dccdd214e5b2770776fa742dfd74bcc13ef219` / `e56fb3cd1cefad9754c01a29fad55d607dadca41`

📎 **HISTORICAL — original bundle の pin（1 commit に 3 file）**

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
- ⛔ **「参照点を変えると bar が変わる」は narrow**（B8）⇒ **各参照点で evidence-grade の Jacobian（方向つき 3 成分 ＋ 認可 envelope）を測る必要がある。差の量・方向は UNMEASURED。** ⭐ **B15**: **proxy（縮約 ＋ 1 姿勢）は測定済**・⛔ **proxy から bar を導かない。**
- ⛔ **現行 H-4 の出力は「各列の最大絶対成分」への縮約 ＋ 1 姿勢**（B9）。**方向つき 3 成分 Jacobian でも envelope の証拠でもない** ⇒ **既出の proxy 値（表 maxima の差 `120.07`/`86.39`、および report key `J_a_minus_J_b_max_mm_per_rad = 126.619`/`133.083` = B28）を bar 変化の根拠に使わない／どの点にも evidence-grade の bar を立てられない。**
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

## ⭐ bank 後の訂正（**B14〜B39**）— ⛔ **上の「9 通」に算入しない**（別列挙・count を再帰的に増やさない）

| # | 処置 |
|---|---|
| **B14** | header の「**8 通**」表記が列挙 9 要素と不一致 ⇒ **9 通**へ訂正（**数え違いは私の欠陥**・機械で数え直して確認）。⛔ 旧 commit `d02385cca42e93c72a1aa92b60890ca1c495a8b8` / `730294ec70784feaaf22d171daf1eb837b9517b7` は **immutable 保全** |
| **B15**（私の surface 1 への裁定） | ⭐ **両方とも真**。⇒ 一般形を **2 段**へ narrow: ✅ **proxy は測定済**（現行 H-4 = **各列を最大絶対成分に縮約 ＋ 1 姿勢**・`908ac4674576c3b936fe66866254d17691b6cc8e`）／⛔ **未測は evidence-grade** = **方向つき 3 成分 Jacobian ＋ 認可 envelope**。⛔⛔ **proxy の存在を消さない／proxy から bar への帰結を導かない。** 反映先 = **材料 ＋ spec ＋ 設計 doc ＋ 本書**（⚠ 旧記載「4 artifact 全てで同期済」は **本書自身が未同期のまま書かれた全称主張だった** ⇒ **B24 として撤回・本版で実体化**） |
| **B16**（私の surface 2 への裁定） | ⛔ spec `:100`「把持なし ⇒ 慣性は過小側 ⇒ ζ は楽観側」は **無条件の方向の断定ゆえ HOLD**。⇒ **現 state = 「出力値は free-arm（宣言した測定状態）のもの。grasped cable が effective `M` / `c` / `K` と `ζ` に与える方向・量は UNVERIFIED」**。**解析式は明示仮定つきの条件付き注記としてのみ保持**（仮定 = 減衰・剛性が不変／付加負荷が effective `M` に PSD 加算され `λ_max(M)` が単調増加 等 — **たわむ cable ＋ 接触では未検証**） |
| **B17** | ⛔ 材料 §1 (3) / §4 の「**EE が傾くと後者に誤差**」を撤回（**frame の意図・権威ある測定点が未裁定なのに world-z 用法を誤りと先取りしていた**）。⇒ **言えるのは「2 構成が併存し、傾斜時に結果は一般に一致しない」まで**。**どちらが intended / correct か、差を「誤差」と呼べるかは UNRESOLVED**（p17 taxonomy ＋ geometric / reward court の境界）。⛔ 是正要求・方式選択なし |
| **B18** | ⛔ **`J-a` を active に固定していた 3 箇所を撤回** — spec §H-3.1「H-4 の Jacobian（**J-a**）」／設計 doc H-2 表「`ε_joint` は **H-4 J-a** 待ち」／同 doc 後段「per-joint `τ_bias` × **H-4 の J-a**」。⇒ 全て **「将来 authority が確定する success-evaluation point の evidence-grade Jacobian（方向つき 3 成分 ＋ 認可 envelope）。`J-a` は conditional」** へ統一 |
| **B19** | ⛔ 設計 doc の「**J-a と J-b は上表の値が両腕とも約 127〜133 mm/rad 違う**」の **「上表の値の差」という説明を撤回（維持）**。**上表から引くと arm0 `\|649.34 − 529.27\| = 120.07` ／ arm1 `\|224.26 − 310.65\| = 86.39` mm/rad** |
| **B28** | ⛔⛔ 私が B19 で書いた「**`127〜133` は出所不明・h2 report にも無い**」は **FALSE ⇒ 撤回**。⚠ **原因 = 探索を `head -3` で切り詰めたまま「無い」を主張した**（**B2 と同型の再発**）。⭐ **実在（私が commit `7223219f3e3d11b9b16df209b6a5a347ff3185b9` で確認）**: `arm_control_measurement_h2_report.json` `.h4_grasp_jacobian.value.arms[0].J_a_minus_J_b_max_mm_per_rad = 126.61949725828234`（`:7020`）／`arms[1] = 133.08344289986846`（`:7497`）。**生成源 = `arm_control_measurement_harness.py:969` 逐語 `float((np.abs(ja_p) - np.abs(jb_p)).max() * 1000.0)`**。⇒ **`126.619/133.083` = 絶対値を取ってから引き最大を取る別 proxy（方向・符号を失う）／`120.07/86.39` = 上表 maxima の単純差**。⛔ **どちらからも bar・誤差を導かない** |
| **B25** | ⛔ 設計 doc の N5 以外に残っていた **無条件の把持方向の主張**を撤回: 「**楽観方向の要因が 3 つ重なる／厳しくなることはあっても緩くならない**」（②把持慣性は **B16 と競合**ゆえ「楽観側」と数えられない）／「**単調枝の条件 `β·α < ζ_free²` は撤回しない構造**」（`α` が未検証仮定に依存 ⇒ **条件付きモデルへ降格**）／「**真の余裕は ×2.09〜×8.16 の間**」（上端が未検証仮定に依存）⇒ ⭐ **残るのは `×2.09` のみ**。⛔⛔ **その scope（B30 を同じ行に fold = B37）**: **`×2.09` が保証なのは「宣言された free-arm / 現姿勢のスカラーモデルの中だけ」**（`λ_max(M)=2.393` に対する `5.0` の余裕）。⛔ **掴んだ cable に対する保証・「真の余裕」としては使わない**（grasped 側は `M`/`c`/`K`/`ζ` とも UNVERIFIED）。**把持慣性を同じスカラーで扱える**という記述も **`ΔM` が PSD・`c`/`K` 不変**の仮定つきに明示 |
| **B26** | ⛔ **spec への B16 伝播を完了**: `:141`「把持中 cable 慣性は `M` に入らない ⇒ **ζ は楽観側**」／§H-5.1 の「**実効慣性が増え ζ は下がる**」「**8.16 倍を超えたかで枝が決まる**」を、**未検証仮定つきの diagnostic** に限定。**phase 別の step-response / `ζ_grasped` の直接観測は保持**（⛔ **task acceptance・枝決定には使わない**）。**AC-5** は **「gripper DOF の寄与を含むか否か」（＝包含の有無）と「誤差の向き」を分離**し、**向きは B10 に従い UNVERIFIED** と明記 |
| **B27** | ⛔ 設計 doc §5.5.C-2 の見出し「**予測は当たった側**」を撤回（**直前で予測自体を RETRACTED / HISTORICAL に落としている**ため矛盾）。⇒ **proxy 3 点が着地した事実だけを述べる見出し**へ改称。**的中は主張しない** |
| **B29** | 撤回文の**同じ行の末尾**で旧結論を再導入していた 2 箇所 | ⛔ **削除**。①設計 doc: 「向きは言えない」と撤回した直後に **「⇒ 現状の数値は『厳しくなることはあっても、緩くなることはない』と読む」** を active に置いていた ⇒ **②把持慣性の向きが UNVERIFIED である以上、全体の向きも言えない**。②spec §H-5.1: **「これで枝を決めない」と書いた同じ行**に旧括弧 **「（設計側の枝がこれで決まる）」** が残っていた ⇒ 削除。⭐ **教訓 = 撤回は、撤回した文の周辺も読んで閉じる**（撤回文の隣で結論が生き残る） |
| **B30** | spec の pinch-site 記述と、設計 doc の `×2.09` の scope | ⛔ ①spec `:167`「使う場合はその旨と**誤差の向き**を明記」の **向きの要求を撤回** ⇒ **報告は包含の有無まで／向きは証拠が無い限り UNVERIFIED**（AC-5 と同一境界）。②設計 doc の **「`×2.09` は保証つき」を scope 限定** ⇒ **「宣言された free-arm / 現姿勢のスカラーモデルの中だけ」の値**であり、⛔ **掴んだ cable に対する保証・「真の余裕」としては使わない** |
| **B31** | ⛔ 本 routing artifact の **immutable chain が短縮 SHA（8 桁）** だった（§exact pin）＋ **footer の全桁一覧が `7223219f…` で止まり、直近の parent `b1e41dfdebc602c63fdc51728b7d5e989c151277` を欠いていた**。⇒ **両方を全 40 桁・同一の 6 commit へ同期**。⭐ 自己 pin できない構造（提出 message を権威とする）は**そのまま維持**。<br>📎 **history（`35dccdd214e5b2770776fa742dfd74bcc13ef219` 時点）**: 本件は **records-only・本 artifact 1 path のみ**の訂正（pN 指示）だったため、**材料 §5.4 の範囲表記は `B14〜B30` のままだった**。私は**その不一致を提出 message で surface** した。<br>✅ **current**: 後継 **`e56fb3cd1cefad9754c01a29fad55d607dadca41`** で **材料に B31 行を追加し、全体を `B14〜B38` へ同期済**。⇒ ⛔ **pending の同期は無い。** |
| **B39** | ⛔⛔ **私の一括置換（`B14〜B30` → `B14〜B38`）が、B31 行の中の *当時の事実* まで書き換えていた** | ⇒ **history と current を分離して訂正**（上の B31 行）。⚠ **`35dccdd214e5b2770776fa742dfd74bcc13ef219` 時点の材料は `B14〜B30`** であり、**`B14〜B38` への同期は後継 `e56fb3cd1cefad9754c01a29fad55d607dadca41` で初めて実施**した ⇒ 旧文は **時系列も pending 状態も FALSE** だった。⭐⭐ **教訓 = 範囲・版・件数の一括置換は、*記録された過去* を巻き込む。** 置換の前に「この数字は *今の状態* か *当時の事実* か」を 1 件ずつ見る。⛔ 本件は **routing 自身の history 行の訂正**ゆえ **材料側に B39 行は不要**（pN 指示）。**`e56fb3cd…` は immutable** |
| **B32** | ⇒ spec `:5` の current-pin を **`P11_ROUTING_SUBMISSION_MATERIALS_V4_20260726.md` の提出 message が宣言する 4-path pin** へ差替え（旧「3 SHA」は final bundle を指していなかった）。**自己 pin 不可の原則は維持** |
| **B33** | ⛔ **行 pin の drift を解消**: spec `:8` の `:238`/`:244` → **`:257`/`:263`**（v1.9 実測）／設計 doc `:19` の spec 参照 → **現 v1.9 行**（`:135`/`:146`/`:147`/`:236`/`:201`/`:238`/`:143`・**7 行すべて読み直して確認**）。⛔ **版をまたいだ行番号を混在させない** |
| **B34** | ⛔ 設計 doc H-2 表の producer 逐語「inertia LOW side / damping OPTIMISTIC」を **その場で fence** — **producer assertion であって私の結論ではない／私の現 state は UNVERIFIED**。**逐語は消さない・根拠に引かない** |
| **B35** | ⇒ 隣接矛盾を **1 つの current state** に統一: **①＝境界の関係（狭い箱の最大 ≤ 広い箱の最大）／②③＝方向 UNVERIFIED／合成した task・requirement 上の全体方向は結論しない**。旧行は **削除の記録のみ**にして重複を除いた |
| **B36** | ⛔ 設計 doc の stale ask「どちらの言い方を採るかは pN 裁定」を **撤回**（**B15 で決着済**）⇒ **B15 の current state に統一**。経緯は HISTORICAL として保持 |
| **B37** | ⇒ 材料 §5.4 B25 と本書 B25 の両方に **B30 の限定を inline fold**: **`×2.09` は「宣言された free-arm / 現姿勢のスカラーモデルの中だけ」の保証**であり、⛔ **grasped cable の保証・「真の余裕」ではない** |
| **B38** | ⇒ active evidence pin を **`908ac4674576c3b936fe66866254d17691b6cc8e`** へ全桁化。**材料 / spec / 設計 doc を閉じた query で全件同期**（短縮形の残り = **0**・機械確認）。⚠ **version-history label の一般書換えはしていない** |
| **B20** | ⛔ 設計 doc §5.5.A の予測（「2 mm に対し `ke` 引き上げの公算・**8.16 と同じ桁**・衝突なら同時引き上げの枝」）を、**後段でなく その場に `RETRACTED / HISTORICAL` の fence を置いて**引用形に落とした（**前から読む者・機械読みに active に見えるため**）。⭐ **現 state = 方向つき 3 成分での合成が揃うまで、2 mm 比較・必要倍率・枝の選択はすべて UNVERIFIED / HOLD** |
| **B21** | ⛔ spec の J-c 行「**J-a と J-b の差を定量化して報告するため**」は **J-c 自身の用途になっていなかった**ので撤回 ⇒ **J-c は 3 つ目のラベル付き参照点**であり、要る理由は **J-c と J-a / J-b を proxy として並べて比較するため** |
| **B22** | ⛔ 設計 doc H-2 表の `ζ` / `T_lag` の結論（**過減衰・単調枝・行き過ぎ無し・節での誤判定無し・縮約が重要でない**）を **表頭で「宣言された free-arm / 暫定測定状態にのみ scope」と明記**。⛔ **task 全体へ一般化しない**（掴んだたわむ cable ＋ 接触下では effective `M` / `c` / `K` と `ζ`・根の方向と量が UNVERIFIED = B16 の伝播是正） |
| **B23** | ⛔ 設計 doc §5.5.0 の **N5** が **B16 / B22 と矛盾したまま active** だった（「把持で実効慣性が増え ζ は下がる＝**楽観側**」「**8.16 倍未満なら単調枝**」を**無条件に断定**）。⇒ **両方とも active な task 主張としては撤回**し、**B16 と同一の条件付き注記**（仮定 = `c`/`K` 不変・付加負荷が effective `M` に PSD 加算され `λ_max(M)` 単調増加 等。**たわむ cable ＋ 接触では未検証**）へ落とした。**後続の `t_dwell` 記述 2 箇所も同じ境界に整合**（把持 phase の `t_dwell` を自由腕の枝判定から決めない） |
| **B24** | ⛔ **本 routing artifact が final correction chain に同期していなかった**（B14〜B17 のみ列挙／既に裁定済の surface 2 点への依頼が残存／footer が旧 bank のまま）。⇒ **B14〜B38 へ同期・B18〜B22 の disposition を収載・stale な依頼を撤回・後継 exact pin を明示**。⚠ **「4 artifact 全て同期済」という全称主張は、実体が伴ってから書く**（旧版はこれを破っていた） |

⇒ **B14〜B38 の詳細表 = 材料 §5.4（**B39 は本書のみの history 行訂正ゆえ材料に行を持たない**）（**B31 は本書のみの records 訂正**）。** **§5.3（#6〜#15）は original bundle 9 通に対する撤回表のまま不変。**

---

## 不変（PASS 済・CLOSED を一切変えていない）

**R1〜R5 の技術核・数値・query 定義・31 file manifest ／ B3 / B4 の技術核 ／ owner・値・参照点・方式の非選択 ／ H-3.1 no GO ／ H-4 全体 HOLD ／ class B HOLD ／ source・`[CHANGE]`・実装・RUN・verify・status・gate flip = CLOSED ／ p17 relay は exact-pin PASS まで CLOSED。** ⛔ **新規測定・RUN・方式採択は要求していない。** ⛔ **original RETURN count = 9 は不変**（B14〜B38 は post-bank の別系列）。

## 依頼（pN へ）

1. 本 post-bank bundle（**B14〜B39**）の exact-pin 照合をお願いします。**後継 commit・4 exact path・各 full SHA256・parent・`git show --check` は提出 message に載せます**（本書は自身の commit を pin できないため）。
2. ⛔ **gate flip は要求していません。** scope は設計/記録材料のみ。期限指定なし・私は standby。
3. ⛔⛔ **旧 §依頼 3「surface 2 点の裁定をください」は撤回**（**B15 / B16 で既に裁定済**・**stale ask**）。⇒ **現時点で pN への未処理の依頼は 1 のみ。**

---
**`w2:p11` ARM-CONTROL-DESIGN — 本書の bank commit は提出 message の宣言値が権威。⛔ 保全（immutable・全 40 桁・§exact pin の一覧と同一の 9 件。⚠ 旧版は `7223219f…` で止まり直近の parent `b1e41dfd…` を欠いていた = B31）= `08f5196c9aa39963c697942a376f7aa19de198da` / `d02385cca42e93c72a1aa92b60890ca1c495a8b8` / `730294ec70784feaaf22d171daf1eb837b9517b7` / `d256128b38e84f47990120b4e81774f3dd551591` / `7223219f3e3d11b9b16df209b6a5a347ff3185b9` / `b1e41dfdebc602c63fdc51728b7d5e989c151277` / `db6ed80b30e7a475831c69a1f9f4420ec193cb5e` / `35dccdd214e5b2770776fa742dfd74bcc13ef219` / `e56fb3cd1cefad9754c01a29fad55d607dadca41`**
