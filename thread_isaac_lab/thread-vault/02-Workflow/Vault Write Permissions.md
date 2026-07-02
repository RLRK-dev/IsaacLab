---
title: Vault Write Permissions
created: '2026-03-26T19:50:30.371Z'
tags:
  - workflow
  - governance
  - vault
---
# Vault Write Permissions

> Vault内の各ディレクトリに対する書き込み権限を明示的に定義する。
> 事故防止のため、CCは許可されたディレクトリ以外に書き込まない。

---

## 権限マトリクス

| ディレクトリ | Rs (Human) | CC (Agent) | 自動生成 | 備考 |
|-------------|:----------:|:----------:|:--------:|------|
| `index.md` | ✅ Write | ✅ Update | — | 全ページカタログ。CC追記可 |
| `01-Architecture/` | ✅ Write | ❌ Read-only | — | 設計判断はRsの専権 |
| `02-Workflow/` | ✅ Write | ❌ Read-only | — | 運用ルール定義はRsが管理 |
| `03-Issues/` | ✅ Write | ✅ Create/Update | — | CCはIssue作成・ステータス更新可 |
| `04-Specs/` | ✅ Write | ❌ Read-only | — | SOMA, SUBLIMATE等の仕様はRs専権 |
| `05-Thinking/` | ✅ Write | ✅ Append | — | Experiment Log等にCCが結果追記 |
| `06-Knowledge/` | ✅ Write | ✅ Create/Update | — | CCが技術ナレッジを記録（feedback_vault_knowledge準拠） |
| `07-Design/` | ✅ Write | ❌ Read-only | — | 設計はRs専権（例外: `00-DESIGN-STATUS-LEDGER.md` 行更新 = CLAUDE.md §運用4 mandate） |
| `00-Project-Management/` | ✅ Write | ✅ Update | — | NEST 運用 file 群（manifest §2 = GEN 領域につき生成器経由のみ・UPDATE block 追記禁止、LTM-1 v1.2 準拠。2026-07-02 Rs D5 承認で行追加） |
| `docs/` 地図（logical_decomposition*.html、repo 側） | ✅ Write | ✅ Update | — | THE MAP（現在 frame 追記 + atomic commit。同上 D5） |
| node dir（`T-*/state.md` ほか vault 直下 node dirs） | ✅ Write | ✅ Create/Update | — | node DB（層A source of truth。同上 D5） |
| `raw/` | ✅ Write | ❌ Read-only | — | immutable source documents |
| `templates/` | ✅ Write | ❌ Read-only | — | テンプレート定義はRsが管理 |
| `.vault-temp/` | — | ✅ Write | ✅ | レポート・一時ファイル |
| `.vault-backups/` | — | — | ✅ | 自動バックアップ |

## SSOT ファイル権限

| ファイル | Rs | CC | 自動生成 | 備考 |
|---------|:--:|:--:|:--------:|------|
| `CLAUDE.md` | ✅ | ❌ | — | Rs指示時のみCC編集可 |
| `task_config.py` | ✅ | ✅ | — | CCはパラメータ変更可（SOMA.md参照必須） |
| `HARNESS_STATE.md` | ❌ | ❌ | ✅ | 手動編集禁止 |
| `STATE.json` | ✅ | ✅ | ✅ | スクリプト経由のみ（直接jq編集はPIVOT防止対象） |
| `RUN_METRICS.json` | ❌ | ❌ | ✅ | run実行時に自動生成 |

## 原則

1. **Rsが書くもの:** 目標・仕様・設計・ルール・ワークフロー定義（"何をやるか"と"どうやるか"の決定）
2. **CCが書くもの:** 実験結果・技術ナレッジ・Issue・分析（"何が起きたか"と"何を学んだか"の記録）
3. **自動生成:** ランタイム状態・メトリクス・バックアップ（"今どうなっているか"のスナップショット）
4. **例外:** Rsが明示的に指示した場合、CCはどのディレクトリにも書き込み可能

---

## Related
- [[Vault Maintenance]]
- [[Claude Code Integration]]
- [[Operational Rules]]

---

**Created:** 2026-03-27
**Status:** 🟢 Active
