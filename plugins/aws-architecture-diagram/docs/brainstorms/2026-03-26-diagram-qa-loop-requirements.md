---
date: 2026-03-26
topic: diagram-qa-loop
---

# 構成図 QA ループ（自動生成→レビュー→修正サイクル）

## Problem Frame

`diagram-generator` が生成した `.drawio` ファイルは、アイコン間隔不足（R04）や
エッジラベル重なり（R10）などの違反を含む場合がある。現在は `diagram-reviewer` が
違反を報告するだけで、ユーザーが手動で XML を修正する必要がある。
これを自動化し、品質基準（CRITICAL/ERROR = 0）を満たす構成図を
ユーザーへの手間なく提供できるようにする。

## Requirements

- R1. **QA ループエージェント**: 新しい `diagram-qa` エージェントを作成する。
  ユーザーが構成図の生成を依頼すると、このエージェントが以下のループを自律的に実行する:
  1. `diagram-generator` を呼び出して `.drawio` ファイルを生成（または受け取る）
  2. `diagram-reviewer` を呼び出してルール検証（R01〜R12）を実行
  3. CRITICAL または ERROR が 1 件以上あれば `diagram-fixer` を呼び出して修正
  4. 修正後に再び `diagram-reviewer` でレビュー
  5. CRITICAL/ERROR = 0 または最大反復回数に達したら終了

- R2. **最大反復回数**: ループは最大 3 回（生成 1 回 + 修正最大 3 回）で打ち切る。
  打ち切り時は最後のレビュー結果とともに「N 回試みたが残存 ERROR X 件」と報告する。

- R3. **diagram-fixer エージェント**: 新しい `diagram-fixer` エージェントを作成する。
  reviewer の違反レポートを入力として受け取り、`.drawio` ファイルに対して
  最小限の差分修正のみを行う（レイアウト全体の再設計は行わない）。

- R4. **diagram-fixer の修正スコープ**: 機械的に修正可能な違反のみを対象とする:
  - R04: 同一コンテナ内の全アイコンをグリッド座標（`x = 60 + col_index * 200`,
    `y = 60 + row_index * 180`）に再配置する。コンテナ（subnet/VPC）の
    width/height もアイコン配置後に自動で再計算して必要なら拡張する
  - R10: エッジラベルの `<mxPoint as="offset">` を追加・調整して
    重なるアイコンから 120px 以上遠ざける（ラベル情報は保持する）
  - R02: 欠損レイヤー cell を追加
  - R03: 重複 ID をリネーム
  - R09: エッジスタイルを orthogonalEdgeStyle に修正

- R5. **収束チェック**: 連続 2 回のレビューで違反件数が減少しない場合（修正が効いていない）、
  ループを早期終了して残存違反を報告する。

- R6. **最終レポート**: ループ終了時に以下を報告する:
  - 実施した反復回数
  - 最終レビュー結果（CRITICAL/ERROR/WARNING/INFO の件数）
  - 総合判定（PASS / FAIL）
  - FAIL の場合: 残存 ERROR/CRITICAL の詳細と「手動修正が必要な点」の案内

- R7. **既存ファイルの修正**: 新規生成だけでなく、既存の `.drawio` ファイルを
  指定して「このファイルを QA ループで修正して」という使い方も可能にする。

## Success Criteria

- 単純な R04 違反（アイコン間隔不足）は 1〜2 回のループで自動的に解消される
- エッジラベル重なり（R10）は自動で除去または offset 調整される
- 最大 3 回の試行内で PASS になるか、残存違反を明示して終了する
- 修正によって既存の PASS ルールが新たに違反にならない（回帰なし）

## Scope Boundaries

- `diagram-fixer` は座標・エッジラベルなどの機械的修正のみ。サービス構成の変更・
  コンテナの追加・削除・大幅なレイアウト再設計は行わない
- VISUAL-WARNING（PNG の視覚的問題）は自動修正の対象外（XML では検出不可のため）
- R07（レイヤー配置の妥当性）など判断が必要な WARNING は自動修正しない

## Key Decisions

- **修正担当を専用 diagram-fixer にする**: diagram-generator は「生成」に特化させ、
  XML 差分修正という異なる責任を新エージェントに分離する
- **最大 3 回制限**: 無限ループ防止。3 回で収束しない違反はロジックの問題であり
  手動対応が適切
- **エージェントとして提供**: スキルではなくエージェント（`diagram-qa`）として
  自律的にループを実行する。ユーザーは途中介入不要

## Dependencies / Assumptions

- `diagram-reviewer` が構造化されたレポート（違反 ID・対象 cell・修正案）を出力すること
  を前提とする。現状のレポート形式（[agents/diagram-reviewer.md](../../agents/diagram-reviewer.md)）は
  `diagram-fixer` が解釈できる十分な情報を含んでいる
- `diagram-fixer` は DrawIO XML の座標計算（絶対座標変換を含む）を実行できる必要がある

## Outstanding Questions

### Resolve Before Planning

（なし）

### Deferred to Planning

- Affects R3 `[Technical]` — `diagram-fixer` が diagram-reviewer の出力をどの形式で
  受け取るか（構造化テキスト vs. ファイルパス vs. 直接呼び出し引数）
- Affects R1 `[Technical]` — `diagram-qa` が他のエージェントを呼び出す実装方法
  （Agent ツール経由 vs. Bash でサブプロセス起動 vs. 手順として記述するだけ）
- Affects R4 `[Needs research]` — R04 修正時のコンテナサイズ自動拡張の実装詳細
  （R4 ではコンテナ拡張を行うと決定済み。具体的な計算式を計画フェーズで確定）

## Next Steps

→ `/ce:plan` で実装計画を作成
