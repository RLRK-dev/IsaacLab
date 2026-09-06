# WMSO v0.2.8 外部設計レビュー — Rs / Claude Code 向け

## ユーザー向け

対象を次の完全commitに固定した。これはレビュー上の推奨であり、Rs裁定でもhuman two-keyの代替でもない。

```text
repository: RLRK-dev/IsaacLab
commit: 0c6f11c91bf42f3a0c0fa9a89190c8e298bd197d
05 declared SHA-256: 2e508b4e6a689b2dc14fb094d5c875efb1dc660dd301e2b157a733bc433010da
06 declared SHA-256: 45212f203f4b95f0dc6d28e5bd805c077e4ea64faaa356f46c65ac1dba8baa49
```

SHA-256は依頼文と同commitのSHA256SUMS.txtの記載が一致することを確認した値で、ローカル再計算値ではない。GitHubが返すGit blobは05=ce176b4359e1364c0b71abc0da640e3f2fdaf86f、06=b796830db84a43136584820f3c1525626fc6cef2。

### 読了範囲

ファイル名の略記は依頼文§1の順序に対応する。詳細パス・refは02_read_scope.jsonに収録。

| 資料 | 読了範囲 |
|---|---|
| 05 runtime | 1–1082、全文 |
| 06 deployment profile | 1–773、全文 |
| 08 review plan | 1–末尾 |
| 11 review record | 1–38、190–222、264–末尾（§8とround 4/5・起草既定を含む） |
| 凍結 contracts_v2 | 126–164、284–385 |
| D0 architecture | 237–373 |
| 凍結 tensor_binding | 18–186 |
| EP v1.9 | Markdown 127–末尾、JSON 190–末尾 |
| 04 EP impact / checker | それぞれ1–末尾。checkerは静的読解のみ |
| SHA256SUMS.txt | 1–14 |

### 前提の訂正・評価範囲

- round 5のHIGH=0はv0.2.7に対するreviewer/verifierの判定。v0.2.8全文への今回の判定とは分ける（11 §11/§11.1）。
- state別のone-key失効、arm_targetsとownershipの包含照合、解除義務の和集合の全件確認は追加済み。旧版の欠陥をそのまま再掲しない。
- 05:520の「manager不読でSafeStopがSafeHoldに緩まない」は、Gatewayが局所に発火したStopを含めると成立しない（GA-01）。
- 「セル構成が同じ」と「同じ物理セル」は同じ条件ではない。現在のcell単位停止の記述では区別が必要（GA-04）。
- 値・役割の実名、PROPOSEDの採否、診断対象、物理停止方式など、依頼文§4で裁定待ちと指定された事項自体は欠陥件数に含めない。今回の指摘は採用した機構内部の束縛・時刻・状態遷移の整合性に限る。

## 判定

**HOLD — HIGH 4件、MEDIUM 3件。受理阻害IDはGA-01〜GA-04。**

機構上のHOLDと手続上のHOLDは別である。08 §5はpin再測・checker実行・盲検陽性対照の未達もHOLDとしている。今回、それらの正式手続は完了していないため、内容の修正だけでこのレビューを正式PASSへ読み替えてはならない。

B+、外部timing baseline、世代付きregistry、三層の失効検出という採択方針の撤回や、凍結4文書の変更は提案しない。

## Findings

以下は指摘ごとの独立JSON object。各severityは本レビューの判断であり、Claude verifierがconfirmedにしたという意味ではない。
### GA-01 — HIGH

```json
{
  "id": "GA-01",
  "severity": "HIGH",
  "doc": "05",
  "doc_line": "05:82; 05:249; 05:513-525",
  "frozen_ref": "WMSO_D0_ARCHITECTURE_DRAFT_RSTECHLEAD2_20260718.md:318-320",
  "claim": "管理系の読取不能中にGatewayが自ら出したSafeStopを、解除なしにSafeHoldへ戻せる。",
  "evidence": "05:82のlast_dispositionは「直近に成功した線形化読みで観測したsafehold_disposition」。05:518はISL心拍欠落でSafeStop、05:520は管理系が不読ならlast_dispositionで出力を選ぶ。反例: 最後の読取はEXECUTORでdisposition=None → 管理系との通信断 → ISL心拍も欠落して(i′)がSafeStop → 管理系は不読のままISL心拍だけ復帰。未解除SafetyDecisionがなく、解除記録も新しい状態読取もない場合、(i′)は外れ、(iii)は古いNoneからSafeHoldを選ぶ。pending_invalidateも(iii)へ送るだけで停止強度を保存しない。",
  "fix": "Gatewayが実際に発行・要求した未解除の停止を局所ラッチし、現在のISL要求・検証済み管理状態・局所ラッチを合わせて出力制約を維持する。ラッチ解除は対象を束縛した正規の解除確認後のみ。AuthorityManagerの単独書込権は変えない。「不読なら常にSafeStop」を採る裁定とは別で、既に発火したStopを失わない修正。凍結schema delta=0。"
}
```

### GA-02 — HIGH

```json
{
  "id": "GA-02",
  "severity": "HIGH",
  "doc": "05",
  "doc_line": "05:233-236; 05:414-442; 05:565-571",
  "frozen_ref": "WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:157-160,306,372-382",
  "claim": "consumerの証明書をSkillActionIdだけで照合し、実際に使用する契約本文のSkillDefinitionHashへ結び付けていない。",
  "evidence": "05:234が比較するのはcertificate.skill_action_id == proposed_lease.skill_action_id、05:236はcertificateの存在。凍結A:158-159ではActionIdの入力とDefinitionHashの入力が異なる。反例: 同じ実行bundle・同じidentity・同じ挙動で来歴だけが異なるD_AとD_Bを用意する。ActionIdは同じ、DefinitionHashは異なる。D_Aのcertificate/AuthorityDecisionとD_Bのlease・開始検証を組み合わせても、記載されたActionId比較と開始条件の検査はこの取り違えを拒否しない。hash衝突を仮定した反例ではない。",
  "fix": "certificate.skill_definition_hash == lease.skill_definition_hash == invocation.skill_definition_hash == H_WCJ(実際のconsumer definition)を必須化する。開始検証reportの対象・入力も同じruntime検証文脈へ束縛し、別のdefinitionの成功reportを転用させない。凍結certificate/reportへのfield追加ではなく、外側のruntime照合で行う。凍結schema delta=0。"
}
```

### GA-03 — HIGH

```json
{
  "id": "GA-03",
  "severity": "HIGH",
  "doc": "05",
  "doc_line": "05:183-191; 05:230-234; 05:558-577",
  "frozen_ref": "WMSO_D11A_CONTRACTS_V2_DESIGN_RSTECHLEAD2_20260719.md:151,372-380",
  "claim": "開始条件の検証からCASまでの待機中にBeliefRefが失効しても、過去の成功reportで制御移譲できる。",
  "evidence": "05:567-571で開始条件・鮮度を検証した後にACK待ち→permit→CASへ進む。05:233はreport.issuesが空であることを確認するだけ。05:188のeffective_expires_atはpermit・ACK・decision・deployment validityの期限であり、BeliefRefのTTL/開始判断の鮮度期限を含まない。反例の時刻順序: t_validate < t_belief_expiry <= t_CAS < t_effective_expiry。owner/epochと他の検査結果を維持すると、失効した開始判断でも記載条件を通る。",
  "fix": "開始検証に用いたBeliefRef、definition hash、明示now、有効期限をruntime側で束縛する。TTLと適用される鮮度期限をpermitの実効期限へ含め、CAS時に失効していないことと開始条件の有効性を確認する。観測・初期化条件を更新した場合は対応する検証・ACK・permitを再取得する。mid-skill観測方針を決める修正ではない。凍結schema delta=0。"
}
```

### GA-04 — HIGH

```json
{
  "id": "GA-04",
  "severity": "HIGH",
  "doc": "05 (+06)",
  "doc_line": "05:191,240,292; 06:75-100,255-260,507,531",
  "frozen_ref": "",
  "claim": "物理セル単位であるべき停止が構成全体のcell_identity_hashに束縛され、同じ設備の別profileへ伝わらない。",
  "evidence": "06:507はcell_identity_hashをCellIdentity全体のhashとし、06:531と05:240の兄弟停止はその等値で対象を限定する。反例: 同じsite_id/cell_id・同じ左右ロボット対応・同じbaselineを持ち、cell.armsの列順だけが(left,right)と(right,left)で異なる、別途受理済みのprofile A/B。armの一意性・対応検査は両方で同じ結果だが、tuple→arrayで構成hashは異なる。Aにセル全体のINCIDENT停止を記録しても、Bは同一hashの兄弟ではないためセル停止拒否条件を満たさない。独立したlive SafetyDecisionを迂回できるという主張ではなく、セル単位の拒否条件の欠落である。",
  "fix": "構成hashと、認証された安定した物理セルIDを分離する。セル全体の停止・未解消incidentは安定IDに束縛し、permit・CAS・head-checkの全評価点で、当該設備の全profile/世代に適用する。構成hashは構成一致の検査に維持する。IDの別名・改名でも未解消停止を消せないようcustody規則に結線する。凍結schema delta=0。"
}
```

### GA-05 — MEDIUM

```json
{
  "id": "GA-05",
  "severity": "MEDIUM",
  "doc": "05 (+06)",
  "doc_line": "05:249,292; 06:529,538,540",
  "frozen_ref": "",
  "claim": "log headがPROPOSEDの場合、停止イベントの対象hashが活性leaseのACCEPTED recordを指さない。",
  "evidence": "06:529はA_g(ACCEPTED)→P_(g+1)(PROPOSED)を許し、活性leaseはA_gのままとする。06:538,540はSUSPENDED.supersedes_record_hashにlog headを要求するため、SがPを指す経路になる。しかし05:249は「supersedeされたACCEPTEDのhash = SUSPENDED.supersedes_record_hash」と同一視し、活性lease.acceptance_record_hashとの等値で再試行を限定する。Sの直前がPならP != A_gで停止対象を取り違える。A_gを直接supersedeすると既にPがsupersedeしておりfork規則に抵触する。周期head-checkは後で停止し得るため、永続的な失効回避とは判定しない。",
  "fix": "logの直前recordを指すsupersedes_record_hashと、今回停止させる有効ACCEPTED recordのhashを別概念として導出・束縛する。PROPOSEDを挟む場合や停止の再送でも、旧世代を止めつつ新たに受理された世代を誤停止しないよう対象を明示する。PROPOSEDを無条件で停止扱いへ変える必要はない。凍結schema delta=0。"
}
```

### GA-06 — MEDIUM

```json
{
  "id": "GA-06",
  "severity": "MEDIUM",
  "doc": "05",
  "doc_line": "05:251,712; 05 §3.8 証明E / §10 T-16",
  "frozen_ref": "",
  "claim": "合法なMARK_BOUNDARY_WAITの成功が、全CAS成功でepochを増やすINV-02と矛盾する。",
  "evidence": "05:251はMARK_BOUNDARY_WAIT成功時にseqだけを増やし、control_epochは進めないと規定する。05:712 INV-02は「全 CAS SUCCESS: new.control_epoch == expected.control_epoch + 1」。反例: EXECUTOR状態でTerminalOutcomeを受領し、MARK_BOUNDARY_WAITがSUCCESSとなる1遷移。本文の事後条件に従えばINV-02違反、INV-02に従えば本文と不一致。証明Eの全CAS成功に関する主張とT-16の検査対象も同じ矛盾を引き継ぐ。",
  "fix": "epoch/seqの不変量・証明・テスト期待をCasKindと実際の遷移種別ごとに定義する。所有者/lease移譲と、同じlease内でのboundary記録を区別し、MARK_BOUNDARY_WAITのepoch不変を維持する。文言を合わせるためにMARKでepochを増やす修正はしない。凍結schema delta=0。"
}
```

### GA-07 — MEDIUM

```json
{
  "id": "GA-07",
  "severity": "MEDIUM",
  "doc": "05 (+06)",
  "doc_line": "05:191 (l); 06:514-527,539",
  "frozen_ref": "",
  "claim": "CLOCK_DRIFTの許容を参照する判定に対し、baselineのdiagnostic_itemsには周期と検出時間しか定義されていない。",
  "evidence": "05 §3.4(l)はwall/monoのdriftが「baseline diagnostic itemの許容内」であることを要求する。06:527のdiagnostic_itemsは(項目, 周期[s], worst-case detection[s])であり、06:539はCLOCK_DRIFTという項目名を必須化するだけ。周期と最悪検出時間を持つbaselineでも、どの量をどの許容値と比較するかは導出できない。数値をまだRs/RT0が決めていない問題ではなく、その値・判定規則を束縛する入力経路がない問題である。",
  "fix": "非凍結のbaselineまたはそれがhashで参照する時計健全性仕様に、比較量・単位・判定規則・許容値・時計対応の前提を定義し、05(l)をその明示参照へ結線する。周期/最悪検出時間を許容誤差へ読み替えず、値未確定・解決不能は拒否する。数値決定はRs/RT0に残す。凍結schema delta=0。"
}
```

## Rsが決める事項 — 受理への影響順

### 1. 実行可能な承認と、設計の条件付き受理を分ける
baseline / role registryの発行主体、変更権限、安定した物理セルIDの管理主体、停止対象と解除手続を誰が保証するかを確定する。推奨は、profileの受理権限と停止する権限を分け、機械的なhash差替えや新profile作成だけでは未解消停止を消せない形。具体的なpS/pY等への役割割当は本レビューで代行しない。

### 2. 未解決の失効・停止を保守側に残す
PROPOSEDは稼働中のauthorityを与えないという既定を維持しつつ、PROPOSEDが間に入っても一者停止は有効なACCEPTEDを取り消せることを確定する。管理系不読時に常時SafeStopとするかは別の裁定だが、既に発火した未解除Stopの喪失は許容しない。HOLD/SAFE_STOPの物理的適否はロボット・把持・荷重を含むcell safety設計の判断に残す。

### 3. RT0への委任内容と、値が未確定のときのゲートを定める
秒数のceilings、診断周期、許容時計誤差、停止応答予算、base pose許容、有効期間はRT0/cell safety担当の根拠付き出力とする。数値をこのレビューで捏造しない。設計を「値は未確定」として記録することと、その値を使うprofile/leaseを受理することは別。未解決値で実行側へ進めない。

### 4. 監査と物理実行の未裁定範囲を明記する
COMMAND_ADMITTED記録不能時の同期block、TOOL_PAYLOAD_IDENTIFICATIONを期限必須に含めるか、baseの参照回転、追加fault triggerなどは依頼文§4の既知openとして扱う。両腕のevery-motion適合性・末端の指令キュー・補間と物理追従の保証も、単にprofileのhashが一致したことから達成済みとはしない。ここで新規の実機試験やauthorityを許可しない。

## レビュー手法に見える盲点（記録・checkerからの推定）

1. **同じ単語/fieldがあることと、同じ対象を検証したことを混同する。** Q2のhash field言及やcertificate存在だけでは、GA-02の対象hashの取り違えを識別しない。
2. **個々の検査は確認しても、時間と状態をまたぐ結合が弱い。** 検証成功→ACK待ち→CAS、心拍喪失→心拍復帰、ACCEPTED→PROPOSED→停止の反例は単一行のcode列挙からは得られない。
3. **構成identityと操作対象identityを同一視する。** GA-04の列順置換は資源対応を変えないのに構成hashを変える。セル停止の対象は構成の同一性とは別である。

これはClaude reviewerの内部思考への断定ではない。11の処置記録と、checkerが実際に行う文字列・集合検査から推定した検証上の弱点である。次の検証は、上記反例に対する期待結果を修正前に固定し、対象・時刻・遷移・解除義務をまたぐtraceで行うのが妥当。

## 実施した検証と限界

- 03_guard_witnesses.pyはGA-01〜GA-06に関する6組の限定的な条件演算と局所対照を実行し、04_guard_witness_results.jsonに保存した。
- これは本レビューで記述した小モデルであり、WMSO実装、全文から自動抽出した形式モデル、独立した盲検陽性対照ではない。全前提の実機成立や全protocolの正しさを証明しない。GA-07は文書の型/参照の整合性指摘で、実行試験していない。
- 原本のローカルSHA-256再計算、verify_exact_baseline_pins.sh、元のcheck_review_candidate.pyは実行していない。11内の11/11 PASS・FAIL=0は履歴上の報告であり、本レビューの実測に転用しない。
- 凍結文書は表記した抜粋、11は表記した範囲の読解であり全文再監査ではない。02/03行列、07後継判断、個々のClaude reviewer/verifier報告、repository全体は今回未監査。
- repository編集、ロボット/物理シミュレーション、訓練、実装、authority、production、freeze、sliceの解錠は行っていない。7件という件数は問題の網羅を意味しない。

## Claude Codeへの引渡し

本報告をverbatimで保存し、各findingを同じ完全commitの本文でtext/logic/impact別に反証する。特にGA-04はセル停止の拒否条件のみ、GA-05はevent経路の対象不一致で周期head-checkの存在を認めていること、GA-07は数値未決定ではなく入力経路の欠落であることを維持する。confirmed分だけを新版へ反映し、同じ新commit/原本SHAを対象に再検証する。Rs裁定やtwo-key済みとの記録へ昇格させない。

## Internal working output

Reviewed the pinned v0.2.8 candidate in one reviewer context. Proposed four HIGH and three MEDIUM findings; no independent verifier verdict is claimed. Six reduced, reviewer-authored witness/control groups were executed, not the WMSO implementation. Source-byte SHA-256 recomputation, the original checker, and blind positive controls were not completed. No repository mutation or gate opening occurred.
