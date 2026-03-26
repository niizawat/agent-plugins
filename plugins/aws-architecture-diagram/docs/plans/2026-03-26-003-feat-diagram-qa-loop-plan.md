---
title: "feat: Add Diagram QA Loop with Auto-Fix (diagram-qa + diagram-fixer)"
type: feat
status: completed
date: 2026-03-26
origin: docs/brainstorms/2026-03-26-diagram-qa-loop-requirements.md
---

自動生成→レビュー→修正のループを自律的に実行する `diagram-qa` エージェントと、DrawIO XML を機械的に修正する `diagram-fixer` エージェントを新設する。これにより、ユーザーが手動で XML を修正せずとも CRITICAL/ERROR = 0 の品質基準を満たす構成図を受け取れるようにする。

（origin: [docs/brainstorms/2026-03-26-diagram-qa-loop-requirements.md](../brainstorms/2026-03-26-diagram-qa-loop-requirements.md) — 以下の決定事項を引き継ぐ: 専用 diagram-fixer エージェント分離・最大3回反復制限・エージェントとして提供）

## Problem Statement / Motivation

`diagram-generator` が生成した `.drawio` ファイルは R04（アイコン間隔不足）・R10（エッジラベル重なり）などの違反を含む場合がある。現在は `diagram-reviewer` が違反を報告するだけで、ユーザーが手動で XML を修正する必要がある。この手動作業を自動化し、品質基準を満たす構成図を提供する。(see origin: 2026-03-26-diagram-qa-loop-requirements.md § Problem Frame)

## Proposed Solution

3 つのエージェントで役割を分担する:

| エージェント | 役割 | 状態 |
| --- | --- | --- |
| `diagram-generator` | IaC→DrawIO XML 生成 | 既存 |
| `diagram-reviewer` | R01〜R12 ルール検証 | 既存 |
| `diagram-qa` | ループ制御オーケストレーター | **新規** |
| `diagram-fixer` | XML 差分修正のみ | **新規** |

`diagram-qa` が `Agent` ツールを使用して他のエージェントを呼び出し、CRITICAL/ERROR = 0 になるまで最大 3 回の修正ループを実行する。

## Technical Considerations

### アーキテクチャ決定

#### 1. エージェント間呼び出し方式

`diagram-qa` の `tools` に `"Agent"` を含め、Agent ツール経由で他のエージェントを呼び出す:

```yaml
tools: ["Read", "Write", "Grep", "Glob", "Bash", "Agent"]
```

`diagram-qa` のシステムプロンプトに以下を指示する:

- `diagram-generator` を Agent ツールで呼び出して .drawio ファイルを生成
- `diagram-reviewer` を Agent ツールで呼び出してレビュー結果を取得
- `diagram-fixer` を Agent ツールで呼び出して修正実行

`diagram-fixer` のツールセット: `["Read", "Write", "Bash"]`（XML 読み書きに特化）

(see origin: § Deferred to Planning — R1 Technical)

#### 2. reviewer → fixer の情報受け渡し

`diagram-reviewer` は既に構造化 Markdown レポートを出力する（違反詳細・修正案含む）。`diagram-qa` が reviewer の出力テキストを変数として保持し、fixer 呼び出し時のプロンプトに埋め込む方式を採用する:

```text
diagram-fixer エージェントへの入力:
- ファイルパス: /path/to/output.drawio
- レビューレポート: [reviewer の出力全文]
```

スキーマ定義は不要（自然言語レポートをそのまま渡す）。(see origin: § Deferred to Planning — R3 Technical)

#### 3. ファイル変更戦略

- **修正はインプレース**（`.drawio` ファイルを直接上書き）
- **バックアップ**: 最初の修正前に `.drawio.bak` を作成
- バックアップは最終報告後も残す（ユーザーが元ファイルを確認できるよう）
- versioned ファイル（`output_v2.drawio` 等）は生成しない（see origin: § Deferred to Planning — R4 Needs research）

#### 4. PASS/FAIL 判定基準

- **PASS**: CRITICAL = 0 かつ ERROR = 0
- VISUAL-WARNING（PNG 視覚検査由来）は PASS/FAIL 判定に含めない
- WARNING・INFO は自動修正対象外・PASS を妨げない

（see origin: § Success Criteria）

#### 5. 収束チェック（R5）の実装

`diagram-qa` が反復ごとに `(critical_count, error_count)` タプルを記録し、連続 2 回で改善なし（前回以下）の場合は早期終了する。最大 3 回制限（R2）と組み合わせ: R5 は反復 2→3 で効果が出る独立したセーフガード。

#### 6. R04 修正のコンテナサイズ自動拡張

`diagram-fixer` が R04 を修正する際の計算式（グリッド再配置）:

```python
# アイコン配置
x_icon = 60 + col_index * 200
y_icon = 60 + row_index * 180

# コンテナサイズ（アイコン配置後に再計算）
n_cols = ceil(sqrt(n_icons))
n_rows = ceil(n_icons / n_cols)
container_width  = 180 + (n_cols - 1) * 200
container_height = 220 + (n_rows - 1) * 180
```

（see origin: § R4 — R04 fix, § Deferred to Planning — R4 Needs research）

#### 7. R03 修正時の edge 参照更新

`diagram-fixer` が R03（重複 ID）を修正する際は、リネームした ID を参照している edge の `source`/`target` 属性も合わせて更新する。リネーム方式: `id` + `_2`（例: `ec2-1` → `ec2-1_2`）。（see origin: § R4）

#### 8. R10 エッジラベル offset 方向

offset 調整の優先順位:

1. `offset_x = +120`（右方向）を試みる
2. 右方向でも別アイコンに重なる場合は `offset_y = +120`（下方向）
3. 両方向で重なりが解消できない場合は違反として報告して終了

（see origin: § Deferred to Planning — R4 Needs research → R10 fix direction）

### SpecFlow 分析で特定された追加考慮事項

- **R02 と scope 境界**: `diagram-fixer` が追加するのは「欠損レイヤー cell」のみ（VPC/Subnet コンテナの追加ではない）。レイヤー cell は構造的メタデータであり「サービスコンテナの追加」に該当しない → scope 内で実施可。
- **VISUAL-WARNING の扱い**: PNG 視覚検査は `diagram-fixer` では実施しない（XML では視覚的問題は検出不可のため）。最終報告で VISUAL-WARNING が残る場合はユーザーに手動確認を案内。
- **ループ終了後の PNG**: `diagram-reviewer` が出力した PNG ファイルは削除しない（既存の reviewer 仕様通り）。

## System-Wide Impact

- **interaction graph**: `diagram-qa` → `diagram-generator`（Agent ツール） → `diagram-reviewer`（Agent ツール） → `diagram-fixer`（Agent ツール） → `diagram-reviewer`（Agent ツール、繰り返し）
- **state lifecycle**: `.drawio` ファイルはインプレース修正。`.drawio.bak` が残存状態として存在。PNG ファイルは最後の reviewer 呼び出し後に残る。
- **error propagation**: Agent ツール呼び出しが失敗した場合（エージェントが見つからない、実行エラー）、`diagram-qa` はエラーを最終報告に含めてループを中断。
- **既存エージェントへの影響**: `diagram-reviewer` と `diagram-generator` には変更なし。

## Acceptance Criteria

- [x] `diagram-qa` エージェントが作成され、新規生成依頼を受け取れる（R1）
- [x] `diagram-qa` が既存 `.drawio` ファイルを指定して修正ループを実行できる（R7）
- [x] 最大 3 回の修正ループで打ち切り、「N 回試みたが残存 ERROR X 件」を報告する（R2）
- [x] `diagram-fixer` エージェントが reviewer レポートを解釈して以下を修正できる:
  - R04: グリッド座標への再配置 + コンテナサイズ自動拡張（R4）
  - R10: offset 調整（+120px 右 or 下）（R4）
  - R02: 欠損レイヤー cell の追加（R4）
  - R03: 重複 ID のリネーム + edge 参照更新（R4）
  - R09: エッジスタイルを orthogonalEdgeStyle に修正（R4）
- [x] 連続 2 回のレビューで違反件数が減少しない場合、早期終了する（R5）
- [x] 最終レポートに反復回数・CRITICAL/ERROR/WARNING/INFO 件数・PASS/FAIL を含む（R6）
- [x] PASS 時に残存 VISUAL-WARNING はユーザーに案内するが、FAIL 扱いにしない
- [x] 修正によって既存の PASS ルールが新たに違反にならない（回帰なし）
- [x] `.drawio.bak` バックアップが修正前に作成される

## Implementation Plan

### Phase 1: `diagram-fixer` エージェント作成

**ファイル**: `agents/diagram-fixer.md`

**作成内容**:

- YAML frontmatter: name, description（triggering examples）, model: inherit, color: green, tools: ["Read", "Write", "Bash"]
- システムプロンプト:
  1. 入力: `.drawio` ファイルパス + reviewer レポートテキスト
  2. `.drawio.bak` バックアップ作成
  3. Read ツールで `.drawio` XML を読み込み
  4. レポートの各違反を解析し、対象ルール別に修正を適用:
     - R04: グリッド座標計算 + mxGeometry x/y 書き換え + コンテナサイズ再計算
     - R10: `<mxPoint as="offset">` 追加/調整（右+120 → 下+120 のフォールバック）
     - R02: 欠損レイヤー cell を `<root>` に追加
     - R03: 重複 ID をリネーム（`_2` suffix）+ edge source/target 更新
     - R09: edge の style 属性に `edgeStyle=orthogonalEdgeStyle` を追加
  5. Write ツールで修正済み XML を書き込み
  6. 修正サマリーを出力（修正した違反 ID・件数）

### Phase 2: `diagram-qa` エージェント作成

**ファイル**: `agents/diagram-qa.md`

**作成内容**:

- YAML frontmatter: name, description（examples: 新規生成依頼・既存ファイル修正），model: inherit, color: blue, tools: ["Read", "Write", "Grep", "Glob", "Bash", "Agent"]
- システムプロンプト（ループロジック）:

```text
入力受付:
  A. 新規生成の場合: ユーザー要件 + 出力ファイルパス
  B. 既存ファイルの場合: .drawio ファイルパス

初期化:
  max_iterations = 3
  iteration = 0
  prev_violation_count = None

ループ:
  if A の場合 (iteration == 0):
    Agent: diagram-generator で .drawio を生成

  iteration += 1

  Agent: diagram-reviewer で .drawio をレビュー → レビューレポートを取得
  (critical, error) = レポートから件数を抽出
  violation_count = critical + error

  if violation_count == 0:
    → PASS で終了

  if iteration >= max_iterations:
    → 「{iteration} 回試みたが残存 CRITICAL={critical} ERROR={error}」で終了

  if prev_violation_count is not None and violation_count >= prev_violation_count:
    → 「連続 2 回改善なし。残存違反 {violation_count} 件」で早期終了

  prev_violation_count = violation_count

  Agent: diagram-fixer でレポートを渡して修正

  ループ継続

最終レポート出力:
  - 実施した反復回数
  - 最終 CRITICAL/ERROR/WARNING/INFO 件数
  - PASS / FAIL 総合判定
  - FAIL の場合: 残存 ERROR/CRITICAL 詳細 + 手動修正案内
  - VISUAL-WARNING がある場合: PNG を確認するよう案内
```

### Phase 3: README 更新

`README.md` の「コンポーネント」セクションに以下を追加:

- `diagram-qa`: QA ループオーケストレーター（新規エージェント）
- `diagram-fixer`: XML 差分修正エージェント（新規エージェント）

「使い方」セクションに QA ループの使用例を追加:

```text
### QA ループで自動修正
生成した構成図を自動的にレビュー→修正するには:
  QA ループで構成図を自動修正して。出力先: ./architecture.drawio

既存ファイルを修正するには:
  ./existing.drawio を QA ループで修正して
```

## Dependencies & Risks

### 依存関係

- `diagram-reviewer` が構造化レポート（違反 ID・対象 cell・修正案）を出力すること（既存）
- `Agent` ツールが `diagram-qa` から利用可能であること（tools リストに "Agent" を含める必要あり）
- DrawIO XML の `mxGeometry` 座標が絶対値（コンテナ相対）で記述されていること（既存仕様）

### リスク

- **R04 グリッド再配置の副作用**: 座標を強制再配置すると、接続エッジのルーティングが大きく変わる可能性がある。orthogonalEdgeStyle を使用していれば DrawIO が自動再ルーティングするため、最終的な見た目への影響は限定的。
- **R10 offset の衝突**: offset 調整後に別のラベルや別のアイコンと新たに重なる可能性がある。次の reviewer 呼び出しで検出されるため、ループで解消できる見込み。最大 3 回ループを超えた場合は手動対応として報告。
- **Agent ツールの可用性**: `diagram-qa` が diagram-reviewer/diagram-fixer を Agent ツールで呼び出す機能はプラグインシステムに依存。動作確認が必要。

## Sources & References

### Origin

- **Origin document**: [docs/brainstorms/2026-03-26-diagram-qa-loop-requirements.md](../brainstorms/2026-03-26-diagram-qa-loop-requirements.md)
  - 引き継いだ主要決定事項: 専用 diagram-fixer 新設・最大 3 回反復制限・エージェントとして提供・R04 グリッド再配置+コンテナ拡張・R10 offset 調整

### Internal References

- [agents/diagram-reviewer.md](../../agents/diagram-reviewer.md) — レビュールール定義（R01〜R12）・出力フォーマット
- [agents/diagram-generator.md](../../agents/diagram-generator.md) — グリッド座標式・VPC スタイル定義
- [skills/drawio-xml-format/SKILL.md](../../skills/drawio-xml-format/SKILL.md) — DrawIO XML 構造リファレンス
