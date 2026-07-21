# WMSO D1.1-C design v2.5.1 — two-key 設計軸 verify（pS MWSO-DESIGN）

- node `T-WMSO` D1.1-C; 検証者 = `w2:pS` MWSO-DESIGN（0-commit）。作成 = 2026-07-21 20:42 JST（shell 実測）。
- **依頼** = pQ 20:31: v2.5.1 two-key の**設計軸 leg**（pY は本 record bank 後に回付＝逐次遵守）。判定 3 つ: (1) 境界＝縮小版のまま two-key を開いてよいか (2) v2.5.1 本体の設計軸 (3) 「v2.5 以降 records-only・設計 semantics 不変」の裏取り。
- **対象 pin（on-disk 自算・一致）**: design v2.5.1 = `97bfda4355b4fc3d287c1ea47f06f690d2d11fa1ad4023e63c636fa376604246` @ `878b97bc2f` / builder = `bc89e9d7148e15ca4ea67f6adac987651e90a6315ab25376c8909d3908ab9111` @ `b994b617b5` / golden A-D @ `e1ed170014`（present）/ 凍結 v13 = `5a1874d3be8b98b8…`（無傷）/ 凍結 EP JSON・contracts_v2 は同 tree 自読。
- ⛔**設計軸のみ**。⛔**freeze しない・scope 縮小を採択しない**（= Rs 専権）。⛔**本 PASS は two-key を完了しない**（pY evidence 軸が別 leg）。

## 1. (2) 本体の設計軸 = ✅ PASS（機構は健全・凍結忠実・限界に誠実）

**§2 U-5（両段 binding 記録）— 凍結忠実**:
- `StageBindingRecord{execution_stage_tensor_binding_hash, bc_stage_tensor_binding_hash}`・命名は凍結 claim target（EP JSON `:29` `execution_bundle.tensor_binding.artifact_hash`・自読一致）。
- lineage 全域表（凍結 `TrainingLineage` 5 member 全被覆）: `NOT_APPLICABLE` = execution null-or-hex / bc null 必須 = 凍結 v13 `:166`「RL_ONLY・NOT_APPLICABLE ⇒ null 必須」が **bc 段のみ**を要求（自読一致・cycle-2 F-8 の false-reject 除去は正しい）。
- declaration 突合（凍結 v13 `:158-171` 自読）: IDENTICAL = 両 field 非 null 相等（凍結 `:158` 逐語「hash を内包せず relation のみ」）/ EXPLICIT_SUPERSEDE = bc == `demo_dataset_binding_hash`。⭐**lineage 整合 = C 側新 code `E_MANIFEST_LINEAGE_INCOHERENT`** — 凍結 `E_BINDING_LINEAGE_MISMATCH`（v13 `:171` = `TrainingProvenance` operand・`:230` certify 発火）を別 operand（`LineageBindingDeclaration`）で overload せず新 code へ = **私の cycle-3 設計軸 read（`0aaed7d98965aa60`）を忠実 fold**。
- ⛔**「解消」でなく「記録」**: 凍結 `E_BINDING_STAGE_IDENTICAL_UNCONFIRMED` は certify 時 cross-artifact（v13 `:230`・`certify_inputs` に manifest 不在）ゆえ本版は discharge しない（open-4）= 誠実。

**§3 `substrate_id`（必須化・区別）— 凍結忠実・値で弾かない**:
- S-1（存在非空）/ S-2（構文 ASCII `[A-Za-z0-9_.:-]{1,64}`）/ S-3（`dataset_substrate_ids` 非空・bytes 昇順・重複なし）= **存在・構文・相互比較のみ**。⛔allowlist/denylist/grade 係数なし = **私の prereg W-1（不在/pooling のみ拒否・値で弾かない=値選別は #26）を満たす**。
- 凍結 carry 全文（contracts_v2 `:570`(i) 自読）= 2 連言。本機構は**第 2 連言（記名強制）のみ**担い、第 1 連言（clean のみ = 選別 policy）は述べない = mechanism/policy 線 正しい。⚠silent-non-mixing は保証しない（open-9）・混成可否裁定 DDR 不在（open-8）= 誠実に撤回/上程。

**§4/§5/§6/§7 — 誠実**: §4 = 凍結 §2 WCJ 適用・並べ替えない・時刻を hash に入れない・canonical bytes は検出（阻止でない・open-10）。§5 = 9 C 側 code（`E_MANIFEST_LINEAGE_INCOHERENT` 含む）。§6 = open-5 解消（私の `:439` 提示を fold）・D1.1-B fixture 撤回 保持。§7 = fixture bank 済・encoder vector が UTF-16BE vs codepoint を判別（私が cycle-3 で確認済）・builder 非検査項は impl leg（CLOSED）と明記。

**invariant / court / 先祖返り / 先走り = clean**:
- §0 FOUNDATIONAL（dual-arm/88mm/DiffIK/コ/no-kinematic）**非該当** — 本版は契約層の hash 記録機構で物理・制御・kinematic 語 0。
- 越境なし（合成=pX・F4=p5 に触れない）。先祖返りなし（凍結の上に構築・私の read を正しく fold）。先走りなし（impl/training/authority CLOSED・値選別 policy 非焼込・記録機構で採択なし）。
- ⭐**P-1 carry（私の prereg 指摘）は §7 で実質 addressed**（builder = 生成器+verify = fixture/test tool の設計記述であって manifest impl でない）+ open-17 に記録 = adequate。

⇒ **本体 = 設計軸 PASS**。**must-fix 0**。機構は sound・凍結忠実・open は誠実に列挙（§0:28 完全列挙・§8 18 件 owner 付）・過小主張の撤回まで実施。design-axis DEFECT なし（open-16② の IDENTICAL hash 複写 = 凍結委任は「記録」ゆえ fabrication 阻止は凍結超えの強化=上程事項 owner Rs、defect でなく honest escalation）。

## 2. (1) 境界 = ⚠ 分けて判定（two-key は開けるが scope 縮小の採択は Rs）

- ✅**two-key の VERIFICATION を開くこと自体は正当**（pS/pY が v2.5.1 を検証する＝ Rs 専権行為でない・declared-open freeze は D1.1-A/B 先例あり）。**boundary as declared は誠実・整合**（§1 で確認: 完全列挙・owner 付 open・silent drop なし・過小主張撤回）。⇒ 検証は進めてよい（本 PASS がその leg）。
- ⛔**しかし「承認済 scope（IN 5 項）を 2 項へ縮小/段階化して freeze してよいか」= Rs 専権**（escalate 原則: **scope 変更 / freeze = Rs 専権**）。本 doc **自身が §0:33・§8:11・§6:6 で「縮小の可否 = Rs 判断 (c) = open-11・Rs 未裁定」と明記**（自読）。⇒ **本 PASS は scope 縮小を批准しない**。Rs が freeze gate で open-11 を裁定する。
- ⚠⚠**§運用10 不整合 flag**: pQ dispatch「(c) は escalate 是正で pS 判定へ移った」vs 本 doc §0:33/§8:11「縮小の可否 = Rs 判断 (c) = open-11」が**衝突**。加えて doc 内部も §0:33/§8:11（縮小=Rs）と §9:185（(c) を「部分版 two-key の可否 / open-freeze の可否」へ reframe）で不整合。
  - **設計軸の読みで解く**: 「two-key を**開く**（verify）」= pS/pQ（正当）／「縮小 scope を**freeze/採択**（open-11）」= Rs（doc §8:11 が正しい・escalate 原則 scope 変更=Rs）。⇒ pQ の「(c) → pS」は **verification-opening にのみ妥当**で、**open-11（縮小 freeze 可否）を pS へ移すものではない**。
  - ⭐**cycle-3 NHA の「順序が逆」懸念も本 scope で解ける**: 本 PASS は**設計の健全性 + 境界の誠実さ**を certify し、**「2 項 scope が正しい」を批准しない**。⇒ 縮小の可否（Rs）を先取りしていない（順序は pS 設計検証→Rs scope/freeze で正しい）。
- ⇒ **(1) 回答**: two-key は開けてよい（本 PASS＝設計軸 leg）。ただし **open-11（scope 縮小 freeze 可否）は Rs のまま**・本 PASS は批准しない。doc の §0:33/§8:11（Rs）と §9:185/dispatch（reframe/pS）の**表記を整合させることを推奨**（Rs 専権の本質は不変）。

## 3. (3) records-only 裏取り = ✅ 確認（baseline は 988a005f91・label≠pin）

- 「E_MANIFEST_LINEAGE_INCOHERENT」出現数 = **45bfdfcaca:0 / 988a005f91:3 / 87ba9ee2c0:3 / 878b97bc2f:3**（自算）。⇒ **semantic v2.5（新 code 安定）= `988a005f91`**。
- ⚠**baseline 精密化（label≠pin の実測）**: commit `45bfdfcaca`（メッセージ「a C-side lineage code」）の**中身は INCOHERENT を 0 件**しか持たない（＝ pQ が flag した「title だけ v2.5・中身 v2.4」の broken byte-state）。⇒ **「v2.5 以降 records-only」の正しい baseline は `988a005f91`**（45bfdfcaca ではない・そのメッセージは中身を過大表示）。doc line 5「版 label は照合用注記で pin でない・content sha で引け」と整合。
- **diff `87ba9ee2c0`（最終 v2.5 byte-state）→ `878b97bc2f`（v2.5.1）自読 = 完全に records のみ**: title（v2.5→v2.5.1）+ 系譜行（lineage 注記追加）+ §1.1 の「Rs 判断 (a)(b)」→「裁定済」。**§2/§3/§4/§5/§7（機構）に変更 0**。⇒ ⭐**「semantic v2.5（988a005f91）→ v2.5.1 = records-only・設計 semantics 不変」= 裏取り成立**（baseline を 988a005f91 と読めば pQ の主張は真）。

## 4. 判定

✅ **v2.5.1 設計軸 = PASS-WITH-CONDITIONS**（本体 must-fix 0）。

- (2) 本体 = PASS（§2 U-5・§3 substrate_id とも凍結忠実・私の read を忠実 fold・値で弾かず・限界に誠実・invariant/court/先祖返り/先走り clean）。
- (1) 境界 = **two-key の verification は開けてよい**（本 PASS＝設計軸 leg・declared-open は A/B 先例）。⛔**scope 縮小 freeze 可否（open-11）は Rs 専権**・本 PASS は批准しない。§運用10 flag（dispatch pS vs doc §8:11 Rs）。
- (3) records-only = 確認（baseline = `988a005f91`・87ba9ee2c0→v2.5.1 は機構不変）。⚠label≠pin（45bfdfcaca は broken byte-state）。

⛔**条件・境界**:
- **C-1（Rs）**: open-11（承認済 5 項を 2 項へ縮小/段階 freeze してよいか）= Rs 専権・**本 PASS は批准しない**。doc §0:33/§8:11 と §9:185/dispatch の表記整合を Rs 確認で。
- **C-2（pY）**: evidence 軸（golden byte 実算・pin exact 照合・open 群の owner/DDR 対応）= pY leg（本 record bank 後に回付）。**two-key は pY 完了まで未了**。
- **C-3（impl CLOSED）**: WCJ 完全性の `canonicalize()` leg・dual-canon guard・§7 builder 非検査項 = impl leg（CLOSED）。
- 私の次レグ = pY verdict readback + Rs の open-11 裁定後の反映確認。**私 = 本 leg 完了後 reactive**。
