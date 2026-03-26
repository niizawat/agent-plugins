---
title: "feat: Add diagram-reviewer agent for DrawIO layout validation"
type: feat
status: active
date: 2026-03-26
---

# feat: Add diagram-reviewer agent for DrawIO layout validation

## Overview

`aws-architecture-diagram` プラグインに `diagram-reviewer` サブエージェントを追加する。
このエージェントは `diagram-generator` が生成した DrawIO XML ファイルを受け取り、
プラグインのルール（レイヤー割り当て・アイコン間隔・重なり禁止・エッジラベル等）に
従って作成されているかを静的に検証し、違反箇所と改善案を報告する。

## Problem Statement / Motivation

`diagram-generator` はルールを文章で与えられているが、LLM の出力には以下の問題が起きやすい:

1. **アイコンの重なり** — 同一/近接座標への複数アイコン配置（WAF と CloudFront が重なるなど）
2. **不正なレイヤー割り当て** — WAF を layer-3 に置くなど、ルールと異なる層への配置
3. **間隔不足** — アイコン中心間距離が水平 200px / 垂直 180px を下回る
4. **エッジラベルのアイコンラベルへの重なり** — 狭い間隔でエッジラベルを表示している
5. **XML 構造の問題** — 必須レイヤー不足・重複 ID など

レビュアーエージェントを設けることで、生成後すぐにルール違反を発見・修正できる。

## Proposed Solution

### エージェント: `diagram-reviewer`

- **入力**: レビュー対象の `.drawio` ファイルパス
- **処理**: DrawIO XML を解析してルールチェックを実行
- **出力**: 違反リスト・重大度・修正提案を含む構造化レポート

### ルールチェック一覧

| チェック ID | 内容 | 重大度 |
|------------|------|--------|
| R01 | 有効な XML・mxGraphModel 構造 | CRITICAL |
| R02 | layer-0〜layer-5 が全て定義されている | CRITICAL |
| R03 | 全セル ID が一意 | CRITICAL |
| R04 | 同一/重複座標（バウンディングボックス overlap）の禁止 | ERROR |
| R05 | 水平アイコン中心間距離 ≥ 200px | ERROR |
| R06 | 垂直アイコン中心間距離 ≥ 180px | ERROR |
| R07 | レイヤー割り当て検証（WAF→layer-2、EC2→layer-3 等） | WARNING |
| R08 | AWS シェイプ名が `mxgraph.aws4.*` 形式 | WARNING |
| R09 | エッジに `edgeStyle=orthogonalEdgeStyle` | WARNING |
| R10 | エッジラベルと隣接アイコンラベルの重なり検出 | WARNING |
| R11 | コンテナ（VPC/Subnet）が子アイコンを含む | INFO |
| R12 | 外部リソース（WAF/CF/R53）がVPC外・左列に配置 | INFO |

## Technical Approach

### Architecture

```
agents/
  diagram-generator.md   （既存）
  diagram-reviewer.md    （新規追加）
```

レビュアーは **Read** ツールで `.drawio` ファイルを読み込み、
XML をテキスト解析してルールチェックを実行する。
外部スクリプトは使わず、エージェント自身が XML を読んで検証する。

### Implementation

**エージェントのフロー**:

1. 引数またはユーザー入力からレビュー対象ファイルパスを取得
2. Read ツールで `.drawio` ファイルを読み込む
3. XML をパースして全 `mxCell` を抽出
4. 各ルール（R01〜R12）を順番にチェック
5. 違反を重大度別（CRITICAL / ERROR / WARNING / INFO）に分類
6. 構造化レポートを出力
7. CRITICAL/ERROR が存在する場合は修正アクションを提案

**レポート形式（出力例）**:

```markdown
## DrawIO Diagram Review Report

📄 ファイル: /path/to/output.drawio
🕐 レビュー日時: 2026-03-26

### サマリー
| 重大度 | 件数 |
|--------|------|
| CRITICAL | 0 |
| ERROR | 2 |
| WARNING | 3 |
| INFO | 1 |

### 違反詳細

#### ERROR: アイコン重なり検出 (R04)
- **対象**: `waf-1` (x=200, y=480) と `cloudfront-1` (x=200, y=480)
- **問題**: 同一座標に配置されています
- **修正案**: `cloudfront-1` を y=660 に移動してください

#### ERROR: 水平間隔不足 (R05)
- **対象**: `alb-1` と `ecs-service-1` の中心間距離 = 120px（最小 200px 必要）
- **修正案**: `ecs-service-1` の x 座標を +80px ずらしてください
```

### エージェント定義ファイル: `agents/diagram-reviewer.md`

```markdown
---
name: diagram-reviewer
description: |
  Use this agent when the user wants to review or validate a DrawIO AWS
  architecture diagram file. Examples:
  ...
model: inherit
color: yellow
tools: ["Read", "Glob"]
---

You are a DrawIO AWS Architecture Diagram Quality Reviewer...
```

### ツール制限

Read + Glob のみ（書き込み不要。レビューのみ）。

## Acceptance Criteria

- [ ] `agents/diagram-reviewer.md` ファイルが作成されている
- [ ] エージェントが `.drawio` ファイルパスを引数またはプロンプトから受け付ける
- [ ] R01〜R06（CRITICAL/ERROR ルール）を全てチェックできる
- [ ] R07〜R12（WARNING/INFO ルール）をチェックできる
- [ ] 重大度別の違反レポートを出力する
- [ ] CRITICAL/ERROR が 0 件の場合「問題なし」として合格を宣言する
- [ ] `diagram-generator` が生成したサンプル（test/sample-cdk-stack.ts から生成）でレビューが動作する
- [ ] エージェント名が `aws-architecture-diagram:diagram-reviewer` で呼び出せる

## Dependencies & Risks

**依存**:
- `agents/diagram-generator.md` — レビュー対象のファイルを生成するエージェント
- `skills/drawio-xml-format/SKILL.md` — DrawIO XML 形式のリファレンス（ルール定義の根拠）

**リスク**:
- DrawIO XML の `mxCell` 属性をテキストベースで解析するため、属性値のパースが複雑になる可能性
  → 対策: XML の各属性をシンプルな正規表現でキャプチャし、過剰に厳密な解析は避ける
- LLM がすべての座標計算を正確に行えない場合がある
  → 対策: 違反の有無のみ報告し、座標の計算自体は報告に含める形で人間が確認できるようにする

## Implementation Notes

### レイヤーとリソースの対応表（R07 用）

エージェントのシステムプロンプトに埋め込む:

```
layer-2 (セキュリティ): WAF, Shield, Cognito, ACM, SecurityGroup, NACL
layer-3 (アプリケーション): EC2, ECS, EKS, Lambda, ALB, NLB, API Gateway, CloudFront, AppSync
layer-4 (データ): RDS, Aurora, DynamoDB, ElastiCache, S3, Kinesis, OpenSearch
layer-5 (監視): CloudWatch, X-Ray, Systems Manager, Config, CloudTrail
```

### バウンディングボックス計算（R04〜R06 用）

アイコンの実効サイズ: 幅 120px × 高さ 100px（本体 60×60 + ラベル下 40px）

```
overlap = (|x1 - x2| < 120) AND (|y1 - y2| < 100)
```

## Sources & References

- [agents/diagram-generator.md](../agents/diagram-generator.md) — 生成ルールの定義
- [skills/drawio-xml-format/SKILL.md](../skills/drawio-xml-format/SKILL.md) — DrawIO XML 形式
- [skills/drawio-xml-format/references/aws-shapes.md](../skills/drawio-xml-format/references/aws-shapes.md) — AWSシェイプ名一覧
