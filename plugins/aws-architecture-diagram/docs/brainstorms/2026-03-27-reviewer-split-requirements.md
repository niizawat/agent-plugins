---
date: 2026-03-27
topic: reviewer-split
---

# diagram-reviewer を XML レビューと画像レビューに分離

## Problem Frame

現在の `diagram-reviewer` は XML ルールチェック（R01〜R12）と PNG 視覚検査の両方を
1 つのエージェントが担っている。責任が混在しているため、各レビューの精度向上・
独立改善が難しく、並列実行もできない。
分離することで、それぞれの専門性を高め、QA ループの処理速度も改善する。

## Requirements

- R1. **diagram-drawio-reviewer 新設**: 現 `diagram-reviewer` の XML ルールチェック部分
  （R01〜R12）を専任エージェントとして分離する。入力は `.drawio` ファイルパスのみ。
  出力は現行と同じ構造化違反レポート（CRITICAL/ERROR/WARNING/INFO）。
  PNG エクスポート・視覚検査のロジックは持たない。

- R2. **diagram-image-reviewer 新設**: `.drawio` を PNG にエクスポートし、
  画像を視覚的にレビューする専任エージェントを新設する。
  チェック項目: アイコン重なり、ラベル可読性、エッジラベル重なり、空コンテナ（R11）、
  全体バランス。出力は `VISUAL-ERROR` / `VISUAL-WARNING` を含む視覚レポート。
  XML ルールチェックのロジックは持たない。
  **視覚レポートは修正可能な形式で出力する**: 視覚問題は cell ID・座標・推奨修正を含む
  構造化された形式で報告し、`diagram-fixer` が XML を修正できるようにする。
  このため `diagram-image-reviewer` は PNG 検査の前に `.drawio` XML も読み込み、
  視覚上の位置と cell ID を対応づける。

- R3. **diagram-qa の更新**: 各 QA ループイテレーションで
  `diagram-drawio-reviewer` と `diagram-image-reviewer` を **並列実行** する。
  両エージェントの完了を待ってから結果を統合し、`diagram-fixer` に渡す。

- R4. **統合レポートの定義**: `diagram-qa` が 2 つのレビュー結果を統合して
  1 つの違反リストを作成し、それを `diagram-fixer` へのプロンプトに含める。
  fixer は統合レポートを単一入力として受け取る（現行のインターフェースを維持）。

- R5. **PASS 判定の維持**: PASS 条件は現行どおり
  `CRITICAL = 0 AND ERROR = 0 AND VISUAL-ERROR = 0`。
  XML レビューと画像レビューのいずれかで ERROR/VISUAL-ERROR が残れば FAIL。

- R6. **既存 diagram-reviewer の廃止**: 分離完了後、元の `diagram-reviewer` エージェントは
  削除する（または description を「非推奨」に更新して残す）。

## Success Criteria

- QA ループの各イテレーションで、XML チェックと画像チェックが並列で完了する
- `diagram-fixer` は統合レポートを受け取り、XML 違反と修正可能な VISUAL-ERROR/WARNING の両方を修正する
- VISUAL-ERROR（画像のみで検出可能な問題）と XML ルール違反が独立してトラッキングされる
- 既存の QA ループ（最大 3 回、収束チェック）の動作が変わらない

## Scope Boundaries

- `diagram-fixer` が修正する VISUAL-ERROR は以下に限定する:
  - **修正可能**: アイコン重なり（グリッド再配置）、エッジラベル重なり（mxPoint オフセット）、コンテナサイズ不足（コンテナ拡張）、ラベル可読性（アイコン間隔拡大）、R11 空コンテナ（コンテナの parent に属するアイコンの相対座標を調整してコンテナ内に収める）
  - **修正不可（VISUAL-WARNING でスキップ）**: 全体バランス（主観的で定量化困難）
  - R11 修正の制約: parent 関係にあるアイコンの座標調整のみ。別レイヤーに属するアイコンは対象外（R07 で対処）
- `diagram-fixer` のインターフェース（入力: ファイルパス＋レポート全文）は変更しない
- `diagram-generator` は変更しない

## Key Decisions

- **並列実行**: 2 つのレビュアーを並列で呼び出す。これにより各イテレーションの
  待ち時間がレビュー2本分から1本分相当に短縮される
- **統合レポートは diagram-qa が作成**: fixer のインターフェースを変えないために、
  qa が2レポートを結合してから fixer を呼ぶ。fixer 側の変更を最小化する
- **VISUAL-ERROR/WARNING も diagram-fixer の修正対象とする**: image-reviewer が
  cell ID・座標を含む構造化レポートを出力し、fixer がそれを元に XML を修正する。
  ただし R11（空コンテナ）・全体バランスは自動修正不可としてスキップする
- **既存 diagram-reviewer は廃止**: 分離後に残すと混乱の元になるため削除する

## Dependencies / Assumptions

- `diagram-qa` が Agent ツールで複数エージェントを並列呼び出しできることを前提とする
  （現状の diagram-qa の tools に "Agent" が含まれており実現可能）
- `diagram-image-reviewer` は `diagram-reviewer` と同じ PNG エクスポートスクリプト
  （`skills/drawio-export/scripts/export-to-png.sh`）を使用する

## Outstanding Questions

### Resolve Before Planning

（なし）

### Deferred to Planning

- `[Affects R3]` `[Technical]` `diagram-qa` が Agent ツールで2エージェントを並列呼び出す
  具体的な記述方法（同一プロンプト内で複数 Agent ツール呼び出しを並列指示する方法）
- `[Affects R4]` `[Technical]` 統合レポートのフォーマット詳細
  （2つのレポートをどう結合するか: セクション追記方式 vs. 違反リストのマージ方式）
- `[Affects R6]` `[User decision]` 既存 `diagram-reviewer` を削除するか、description を
  「非推奨」として残して後方互換を保つか（廃止スケジュール）

## Next Steps

→ `/ce:plan` で実装計画を作成
