---
title: "feat: DrawIO構成図品質ルール R13–R16 をエージェントスキルに追加"
type: feat
status: completed
date: 2026-03-30
origin: docs/brainstorms/2026-03-30-agent-rule-diagram-quality-requirements.md
---

# DrawIO構成図品質ルール R13–R16 をエージェントスキルに追加

## Overview

`architecture.drawio` の手動修正で判明した4つの根本原因を、`diagram-generator` と `diagram-drawio-reviewer` の両エージェントに反映する。生成フェーズでの禁止・指示ルール追加と、レビューフェーズでの検証ルール追加を両輪で実施する。

(see origin: docs/brainstorms/2026-03-30-agent-rule-diagram-quality-requirements.md)

## Problem Statement

現状の `diagram-generator` は以下の問題のある XML を生成してしまう:

1. **autosize=1 の誤用**: テキストセルに `autosize=1` を付与 → DrawIO が x/y を上書きして意図しない位置にラベルが表示される
2. **AZ 跨ぎラベル不統一**: 同一論理リソースが複数 AZ に配置されるとき `value` が AZ ごとに異なる文字列になる
3. **VPC/リージョン y 座標の衝突**: VPC コンテナとリージョンコンテナの上端が同一 y=100 → 枠線が重なって見える
4. **エッジ exit 方向の誤り**: ターゲットがソースの右側にあるのに `exitX=0`（左出口）が設定され、エッジが他のエッジと交差する

`diagram-drawio-reviewer` にはこれらを検出するルールが存在しないため、QA ループでも問題が検出されない。

## Proposed Solution

### diagram-generator.md への追加

Phase 3 (DrawIO XML Generation) の末尾に **「Generation Prohibition Rules」** セクションを新設し、以下の制約を明文化する:

| ルール | 内容 | 挿入箇所 |
|--------|------|----------|
| G-R13 | テキストセルに `autosize=1` を使わない | 新セクション末尾 |
| G-R14 | 同一論理リソースは AZ 間で同一 `value` を使う | 新セクション末尾 |
| G-R15 | VPC の絶対 y 座標 ≥ リージョン絶対 y + 60px | 新セクション末尾 |
| G-R16 | exit/entry 方向をソース・ターゲットの相対位置で決める | 新セクション末尾 |

### diagram-drawio-reviewer.md への追加

R12 の直後に **R13–R16** を追加し、Frontmatter の description も更新する:

| ルール | 重大度 | 内容 |
|--------|--------|------|
| R13 | ERROR | テキストセルに `autosize=1` が存在する |
| R14 | WARNING | 同一サービスが複数 AZ に配置され `value` が不一致 |
| R15 | ERROR | VPC とリージョンコンテナの y 座標差 < 60px |
| R16 | WARNING | ターゲット相対位置と exitX/exitY が不一致 |

## Technical Considerations

### diagram-generator.md の記述スタイル

既存は Phase 制の段階的手順書。新ルールは Quality Standards（行399-407）の**直前**に独立セクションとして挿入する。XML 悪例・良例を添える。

### diagram-drawio-reviewer.md の記述スタイル

既存の R01–R12 フォーマット（見出し `### RXX — [名前] ([重大度])`、箇条書き説明、出力テンプレートへの記述方法）に厳密に従う。

- R06, R11 は欠番のため R13 が次の適切な番号
- Frontmatter description の `R01–R12` 表現を `R01–R16（R06, R11 除く）` に更新
- Output Format セクションに R13–R16 用の出力行テンプレートを追加
- Pass / Fail Criteria は変更不要（CRITICAL/ERROR 件数の閾値は既存のまま）

## Implementation Phases

### Phase 1: diagram-generator.md にルール追加

- [x] ファイルを読み込んで Quality Standards セクション（行399-407）の直前の挿入位置を確認
- [x] 「Generation Prohibition Rules」セクションを追加:
  - G-R13: `autosize=1` 禁止（XMLの悪例・良例を添える）
  - G-R14: Multi-AZ 同一ラベル（`value` 統一の例を添える）
  - G-R15: VPC/リージョン y 座標オフセット（計算式と例を添える）
  - G-R16: exitX/Y 相対位置選択（方向表を添える）

### Phase 2: diagram-drawio-reviewer.md にルール追加

- [x] ファイルを読み込んで R12 の末尾（行238 付近）の挿入位置を確認
- [x] R13 を追加（ERROR: autosize=1 on text cell）
  - 検出条件: `style` に `autosize=1` を含む かつ `shape=mxgraph.` を含まない `vertex="1"` セル
  - 出力形式: 既存ルールのフォーマットに従う
- [x] R14 を追加（WARNING: Multi-AZ label inconsistency）
  - 検出条件: 同一 `shape=mxgraph.aws4.*` パターンを持つセルが複数 AZ に存在し、`value` が異なる
  - グルーピング方法: shape の末尾部分（例: `mxgraph.aws4.alb`）で同一サービスと判定
- [x] R15 を追加（ERROR: VPC/Region y-coordinate gap < 60px）
  - 検出条件: VPC コンテナの絶対 y − リージョンコンテナの絶対 y < 60
  - 絶対座標計算: 親チェーンを辿って計算（既存の R04 で行っている方法と同様）
- [x] R16 を追加（WARNING: Edge exit direction mismatch）
  - 検出条件: `exitX=0` かつ target の絶対 cx > source の絶対 cx、または `exitX=1` かつ target の絶対 cx < source の絶対 cx
- [x] Frontmatter の description を更新（`R01–R12` → `R01–R16（R06, R11 除く）`）
- [x] Output Format セクションの report テンプレートに R13–R16 用の行を追加

## Acceptance Criteria

- [x] R1（要件）: `diagram-generator.md` に G-R13（autosize=1 禁止）が記述されている
- [x] R2（要件）: `diagram-generator.md` に G-R14（Multi-AZ 同一ラベル）が記述されている
- [x] R3（要件）: `diagram-generator.md` に G-R15（VPC y オフセット ≥ 60px）が記述されている
- [x] R4（要件）: `diagram-generator.md` に G-R16（exit/entry 相対位置選択）が記述されている
- [x] R5（要件）: `diagram-drawio-reviewer.md` に R13（ERROR: autosize=1）が記述されている
- [x] R6（要件）: `diagram-drawio-reviewer.md` に R14（WARNING: AZ label inconsistency）が記述されている
- [x] R7（要件）: `diagram-drawio-reviewer.md` に R15（ERROR: VPC/region y gap < 60px）が記述されている
- [x] R8（要件）: `diagram-drawio-reviewer.md` に R16（WARNING: exit direction mismatch）が記述されている
- [x] Frontmatter と Output Format が更新されている
- [x] 既存の R01–R12 が変更されていない

## Dependencies & Risks

- **依存**: `diagram-generator.md` と `diagram-drawio-reviewer.md` の現行内容の把握（研究フェーズで確認済み）
- **リスク**: R15 の絶対座標計算は `parent` 属性が layer セルでない場合に注意が必要。レビュアーが親チェーンを正しく辿る手順を記述する必要がある（R04 の既存記述を参照する）
- **リスク**: R16 の判定はエッジ両端の中心座標を使うため、コンテナネストが深い場合に絶対座標の計算精度が求められる

## Sources & References

**Origin document:** [docs/brainstorms/2026-03-30-agent-rule-diagram-quality-requirements.md](docs/brainstorms/2026-03-30-agent-rule-diagram-quality-requirements.md)

Key decisions carried forward:
- 両エージェントに追加（generator + reviewer の両輪）
- R14, R16 は WARNING（構造的に有効なため ERROR にはしない）
- `diagram-fixer`, `diagram-image-reviewer` は対象外

Internal references:
- [agents/diagram-generator.md](agents/diagram-generator.md) — Phase 2/3, Quality Standards（行399-407）
- [agents/diagram-drawio-reviewer.md](agents/diagram-drawio-reviewer.md) — R12 末尾（行234-238），Output Format（行246-284）
