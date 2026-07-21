# WMSO D1.1-C design v1 §0 前提 — 設計軸 照会回答（pS MWSO-DESIGN）

- node: `T-WMSO` D1.1-C; 検証者 = `w2:pS` MWSO-DESIGN（0-commit）。作成 = 2026-07-21 14:55 JST（shell 実測）。
- **照会** = pQ 14:46（Rs 承認済）: design v1 §3 open-1 の中心前提「required set は exact ゆえ HB 以下の record は `TRAIN_RUN_MANIFEST` を追加携行できない」を pQ が cycle-1 で誤りと判定 → ①その反証（読み）が正しいか（pQ は自反証を独立確認していない）②正しい場合、凍結 D1.1-B v13 `:471`「rank 2 への proof 追加 = FORECLOSED」の設計軸上の扱い。
- **対象 pin（on-disk 自算・一致）**: design v1 = `726f684c52421928da207b20b5bb30fac163db254c3e150b8273065e0a047957` @ `33e67626da` / debate verdict = `9851f165a5fc45eb754294aba962352c871dd5982ba26232fb96b0a0c0818e05` @ `7f6d038a30`。凍結 4 file は `1860edcc1c` で読了（prereg verify と同 sha）。
- ⛔**本回答は設計軸のみ**。⛔**凍結 file は編集しない**。⛔**Rs ratify 済 D-1 の運命（覆る/不変）を私が宣言しない**（前提を出した側と同様、私も ratified 結論を単独 disposition する standing を持たない）。

## 1. 照会① — 反証（読み）は **正しい**（前提は FALSE）

**根拠（凍結 on-disk・私が自分で開いて読んだ）:**
- 凍結 EP md `:114` 逐語「binding 対象（cross-field coherence; 不一致 = `E_PROOF_MISBOUND`、**component に意味を持たない kind の混入 = `E_PROOF_KIND_FOREIGN`**）」。
- 凍結 EP md `:129(iii)` 逐語「**他 component 向け kind の混入（例: POLICY_ARTIFACT claim に INPUT_SCHEMA_HASH）→ `E_PROOF_KIND_FOREIGN`**」。
- ⇒ **`E_PROOF_KIND_FOREIGN` は component 意味論（grade 非依存）**。例は「別 component の kind を混ぜた」= component 帰属の問題であり、「この grade の required set に無い」ではない。
- `TRAIN_RUN_MANIFEST` は EXACT の全 13 cell で required（EP md `:43` / EP JSON `:76-77`）＝ **どの component にとっても意味を持つ kind**（別 component の kind ではない）⇒ **どの grade でも foreign にならない**。

**⭐ 反証の完全性（反証が明言していないが決定的な脚）— 凍結に set-EQUALITY（超過拒否）規則が無い:**
- 提供 proof 集合の検査 taxonomy を全数確認: **不足 → `E_PROOF_INSUFFICIENT`（EP md `:53`）／ component 意味なし → `E_PROOF_KIND_FOREIGN`（`:114`）／ 重複 → `E_EVIDENCE_DUPLICATE`・`E_PROOF_CONFLICT`（`:53`,`:59-60`）**。EP JSON `:147` `payload_rules.violations` も missing/ref_malformed/misbound/**foreign_kind**/unresolved/kind_grade_inapplicable のみ。
- 親設計 contracts_v2 の proof error 全列挙（`:555`,`:591`）も MISBOUND/PAYLOAD_MISSING/**KIND_FOREIGN**/INSUFFICIENT/CONFLICT/ARTIFACT_UNRESOLVED/GRADE_INAPPLICABLE のみ。
- ⇒ **非-foreign な「余分」proof を拒否する規則は凍結に存在しない**。執行は「required present ∧ no-foreign-kind ∧ no-conflict」であって「provided == required（集合等値）」ではない。⇒ **record は非-foreign な余分 proof を携行できる**（`TRAIN_RUN_MANIFEST` は非-foreign）。

**前提の誤りの正体（設計軸）:**
- 前提は **「required SET が厳密に規定されている（spec の性質）」** を **「record が required より多く携行できない（instance の禁止）」** に取り違えた。`_domain`（EP JSON `:71`）「exact required ProofKind set; REQUIRED cells only」は **required set が cell 毎に厳密指定＝最小集合でない**を述べ（spec を最小集合に緩めない）、**record の超過携行を禁じてはいない**。
- ⇒ **前提は FALSE**。反証は正しく、かつ（set-EQUALITY 不在の脚を足せば）完全。

**⭐ 強化（反証 line 23 と同旨・重要）**: 「携行できる」≠「EXACT を達成する」。grade は evaluator の**測定値**（`E_GRADE_MISMATCH`, EP md `:132`）。加えて SCRIPTED/WAIT × EXACT は proof 検査前に `E_GRADE_INAPPLICABLE`（`:130`）。⇒ HB record に manifest を携えても grade は昇格しない。**C の manifest 到達可能性の問い（HB 以下でも substrate/stage 照合のため manifest を携えられるか）= YES 携えられる（が authority は付かない）**。これは design v2 の到達可能面（EXACT だけでなく HB 以下も package でなく契約側で substrate/stage を記録し得る）に効く — ただし closure/authority の議論は別。

## 2. 照会② — 凍結 D1.1-B v13 `:471` の設計軸上の扱い

**まず「rank 2 への proof 追加」の意味を凍結文で確定（add-require か add-carry か）:**
- 凍結 B v13 `:256`（D 案比較表 row）逐語「**rank 2 への proof kind 追加** ⛔FORECLOSED | `proof_policy._domain` =「exact required ProofKind set」＋ `E_PROOF_KIND_FOREIGN`（`B1D-A`）。**B 側 spec では不可・D-3 に合流**」。`:471`（v9 記録）同旨。
- ⭐**決定的**: 「**D-3 に合流**」= D-3 は frozen schema delta（`:254`）。add-carry（record が余分を携える）は delta 不要。**delta を要するのは add-require（policy の exact required set を拡張する）だけ**。⇒ **「rank 2 への proof 追加」= spec が rank 2 の required set に proof kind を追加要求する案（add-require）**であり、record-carry ではない。

**設計軸の帰結:**
1. **FORECLOSED の結論は成立（正しい）** — ただし load-bearing な根拠は **「exact required set ⇒ それを拡張する = frozen schema delta = D-3（Rs review）ゆえ B 側 spec では不可」**。これは `E_PROOF_KIND_FOREIGN` に依存しない。
2. **`+E_PROOF_KIND_FOREIGN` の併記は不正確**（照会①と同じ component-意味論 vs grade-閉包 の取り違え）。だが **冗長な二次引用であって FORECLOSED の load-bearing でない** — exact-set/D-3 の脚だけで add-require は foreclosed。
3. ⭐**採択 D-1（Rs ratify 済）は無影響**: D-1 =「既存の required field `EvidenceRecord.source_ref` を locator に束縛」（凍結 `:252` 必須 field / `:269` 全 record / `:551` hash 可視）。**proof kind を追加しない・required set を変えない**。3 軸 close（`:397`）の根拠は source_ref 再利用（`:451`）であって `E_PROOF_KIND_FOREIGN` でも record-carry でもない。⇒ **反証の発見は D-1 の機構に触れない**。

**⇒ 設計軸の読み**: 誤読は **凍結 B v13 の「不採択 option（add-require）」row の二次引用に限局**する。**採択 D-1 の機構はそれに依存しない**。add-require の FORECLOSED は exact-set/D-3 の独立根拠で正しい。⇒ 設計軸上、**反証は D-1 を覆さない**。

⛔**disposition = Rs（+ evidence 軸 pY）**:
- (a) 凍結 B v13 `:256`/`:471` の不正確な `E_PROOF_KIND_FOREIGN` 併記の**訂正 = 凍結編集 = Rs review**（私は編集しない）。
- (b) Rs ratify 済 D-1 が無影響である旨の**正式確認 = Rs**（私は ratified 結論の運命を単独宣言しない — pQ の「immaterial と決める standing 無し」と同じ規律。私は設計軸の read を出すのみ）。
- ⇒ 私は「D-1 は安全・done」とも「D-1 が覆る」とも宣言しない。**設計軸の read = 「D-1 の機構は誤読に非依存・add-require FORECLOSED は exact-set 独立根拠で成立・誤りは二次引用に限局」**。最終 disposition は Rs。

## 3. 機序の確認（lecture でなく acknowledge）

pQ は誤りの機序を自己診断済（verdict `:20`「JSON `_domain` の 1 文字列だけ読み、同 §0 で pin した EP markdown を開かなかった＝読んだ面が知りたい区別をつけていなかった」）。私の独立読みは md/JSON/contracts_v2 が全て一致（component-意味論 foreign・set-EQUALITY 不在）することを確認 — pQ の自己診断は正しい。⭐**これは「識別できない述語は証拠でない／知りたい区別をつける面を読め」型**（本 arc で反復）。

## 4. 境界・私の残

- 本回答 = 照会 2 問への設計軸 read のみ。**design v1 の設計軸 verdict ではない**（v1 = cycle-1 FAIL・A-1〜A-24 で v2 fold 中）。私の次レグ = **v2 fold + fixture bank + cycle-2 後の pS 設計軸 verify**（前提修正が v2 に反映されたか含む）。
- ⚠**監視（先走り・私の standing duty）**: design authoring の解錠（Rs scope 承認）を前提に本 debate が走っている。その解錠自体の確認は evidence 軸（pY）/ Rs の axis。私はここで scope-gate 違反を断定しない（照会は Rs 承認済）。
- ⛔impl/training/closed-loop authority/push/freeze/slice = CLOSED 継続（本照会は何も解錠しない）。
