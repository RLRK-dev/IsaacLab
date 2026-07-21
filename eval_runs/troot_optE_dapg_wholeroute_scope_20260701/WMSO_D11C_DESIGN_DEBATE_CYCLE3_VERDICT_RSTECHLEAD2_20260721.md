# WMSO D1.1-C DESIGN v2.2 — 5 体 CC Debate cycle-3 判定記録

- CC1 = `w2:pQ` RS-TECH-LEAD2／実施 = **2026-07-21 16:0x JST**／**cycle-3 の実施承認 = Rs 逐語「推奨で良い」→「susumete」**（custody `WMSO_RS_D11C_REDUCTION_CRITERION_CUSTODY_20260721.md` に追補要・cycle-3 F 群 G-8）
- **対象** = design v2.2 `4f07c26c773bed5c…` @ `1a35dd2c74` ＋ fixtures @ `e1ed170014`
- 体制 = 4 challenger（discharge 監査・executable 攻撃〔40 mutant〕・scope/routing・回帰〔blind〕）+ NHA。全 body read-only

## ⭐ DECIDE = **FAIL（cycle-3）** — ただし収束方向

- **CRITICAL 2 件**（計器）を**本ターンで修正済**（下記 G-1 / G-2）。
- **HIGH 以下（doc 側 G-3〜G-13）は未 fold**。
- ⛔**two-key を開かない**。**次の gate は Rs**（NHA の smallest sufficient alternative と一致）。

## 1. 修正済（cycle-3 で発見 → 同ターンで修正・実測）

- **G-1（CRITICAL・4/5 body）**: **登録済 fail-closed コマンドが pinned dir で rc=1 になっていた**。原因 = `__pycache__`（`.gitignore` 済ゆえ `git status` に出ない）を「予期しない entry」として拒否。`sys.dont_write_bytecode` は **import 経路では無効**（.pyc は module body 実行前に書かれる）。⇒ **DDR #35 と同型の偽 FAIL**。修正 = 許可 entry に追加。**実測: `__pycache__` 有りで rc=0 / 33/33 / 4/4 PASS**。
- **G-2（CRITICAL・3/5 body）**: **builder + golden の協調改竄が rc=0 で通っていた** — oracle が builder 内定数だけで、**外部アンカーが無かった**（cycle-2 F-3 の残余）。修正 = **golden 4 本の pin 済 digest を builder に埋め込み照合**。**実測: 改竄で rc=1（mismatch 2 件）／非 canonical control も引き続き発火**。
  - ⚠**修正が別 control を壊した**（sha 検査が先に走り `E_MANIFEST_NONCANONICAL_BYTES` が届かず `32/33`）。**control が検出**したので順序を入れ替えて解消。
- 反映 = builder `1c4eebff59c520c8…`（22965 bytes）@ `55705bfa56`／design 追補 `eb956c55aaa61802…` @ `1c817ce1df`（§7 の builder pin 更新 + §9 に v2.3）。

## 2. 未 fold（doc 側・次版）

| # | 指摘 | body |
|---|---|---|
| G-3 | **委任集合が依然 不完全**: v13 `:211` `:365` `:392`／contracts_v2 `:437` が D1.1-C を名指しするが §0 にも §8 にも無い。特に **`:392`（宣言↔producer code の責任）は owner ゼロ**で、代替 venue（impl 解錠）は CLOSED | 2/5 |
| G-4 | **open-5 は「未決」ではない可能性**: 凍結 contracts_v2 `:168` が key 順を逐語で決めている ⇒ `identity.py:80-82` は**単に非適合**。さらに **D1.1-B fixture の `wcj_bytes` も同じ非適合**（凍結 chunk 内）＝ §1.1 と同種の凍結波及で未上程。「3 実装」は実は **2 挙動 / 3 site** | 1/5 |
| G-5 | **IN-2 は部分履行**: prereg IN-2 逐語は「silent pooling を**禁止**する（検出・拒否の code を含む）」だが §3 は保証を撤回 ⇒ **scope 不足を open-9 が producer 義務として吸収**。open-11 の「5→2」も過小申告（真値 = 1 + partial）。⚠**承認済 prereg 自身も OUT-1 で DDR #26 を誤同定**しており未 surface | 1/5 |
| G-6 | **凍結 code の適用域拡張**: `E_BINDING_LINEAGE_MISMATCH` を別 operand・別発火点で再利用（凍結は `TrainingProvenance` 比較・certify 時）＝ 凍結に触る決定を未宣言 | 2/5 |
| G-7 | **`--verify` の on-disk leg が byte 比較以外は無 control**（mutant 5 件が 33/33 で生存） | 1/5 |
| G-8 | **cycle-3 自体の custody 不在**（cycle-2 verdict が「Rs 裁量」と定めた。Rs は承認したが記録していない）= cycle-2 F-10 の同型再発 | 1/5 |
| G-9 | **pS の P-1 / W-2、pY の note-2 が v2.2 に 0 hit** — 特に P-1（「code = error-code 設計・package/CI = 仕様であって build でない」を明記せよ）は、**21KB の実行可能 builder を bank した本版でこそ要る** | 1/5 |
| G-10 | **Rs 判断 (c) の枠組みが誤り**: §0 は「scope 縮小」と書くが open-1 は「後続版で設計する」= chunk 内の先送り。**多版 authoring は D1.1-B v1..v13 の先例あり** ⇒ 問うべきは「部分版で two-key してよいか / IN 1・3・4 + U-2/U-6 を open にしたまま freeze してよいか」 | 1/5 |
| G-11 | custody の誠実注記（transcription・Rs 拒否権）が v2.2 に継承されていない | 1/5 |
| G-12 | **12 open のうち 7 件に宛先が無い**（open-2/4/5/7/8/9/10） | 1/5 |
| G-13 | 小: `E_PROOF_ARTIFACT_UNRESOLVED` が宣言のみで実装も control も無い／`check_against_declaration` が全 code を `E_RECORD_SHAPE` に潰す／`:178` の host 落ち（A-9 回帰）／`:471`「kind を含まない」は**逐語で偽**／v2.1 の open 2 件（跨 run pooling・捏造経路）が無処置で消滅／登録コマンドが相対 path／`emit` が非原子/argv guard に control 無し／33 が assert されない／encoder の key 側 reject 欠落／S-2 の charset に凍結根拠が無い／LEDGER に D1.1-C design 行が無い | 各 1-2/5 |

## 3. 生き残った点（再議論しない）

- **encoder vector の判別性は本物**（2 body が UTF-16-BE/UTF-8 のバイト列を独立に再計算し一致）。`sort_keys=True` / 無 sort / `identity.py` の式を**すべて落とす**。
- **counts はすべて正しい**（33 control・8 code・12 open・4 frozen・4 golden・5 pin 行）。
- **3.8 parse 可**は AST 検査で真（実機 3.8 は本 host に無い＝ doc も未実測と明記）。
- **fence 侵犯なし**（凍結 4 file 未編集・push なし・impl/training/authority/freeze/slice CLOSED）。pX / p5 court 越境 0。
- **方向は収束**: v2.2 の変更は**撤回が主**（保証の縮小・自己判定の削除・時刻 field 削除・「正規化」→「拒否」）。147→168 行で open 9→12 = revision fatigue ではない（NHA 評）。
- **NHA = CHANGE_JUSTIFIED / cycle-2 の two-key 前 blocker は DISCHARGED**。

## 4. ⛔ 次の gate（NHA の最小十分案を採用）

**two-key を開かず、Rs へ 1 通で routing する**（新規 design text を足さない）:

- **(a)** 凍結 v13 `:256`/`:471` の併記訂正（凍結編集 = Rs 専権）
- **(b)** 採択 D-1 への影響の正式判断
- **(c)** ⭐**G-10 に従い問いを立て直す** — 「承認済 scope を縮めてよいか」ではなく **「部分版で two-key してよいか」「IN-1/3/4 + U-2/U-6 を open にしたまま freeze してよいか」**
- **(d)** **open-5 の owner 指名**（G-4 により「未決」ではなく「非適合の是正 owner」の可能性）

**理由（NHA）**: pS の設計軸は「IN-OUT 境界が正しいか」であり、**承認済境界が 5 項なのに 2 項の境界を批准させるのは順序が逆**。pY の evidence 軸も、**golden 4 本の byte が open-5 の帰結に依存**するため、先に決まらないと pin が stale になる。

⛔**impl / training / closed-loop authority / push / freeze / slice = CLOSED 継続**。
