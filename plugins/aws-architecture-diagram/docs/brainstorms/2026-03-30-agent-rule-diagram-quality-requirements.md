---
date: 2026-03-30
topic: agent-rule-diagram-quality
---

# エージェントルール改善：DrawIO構成図品質ルール追加

## Problem Frame

`diagram-generator` が生成した `architecture.drawio` をレビュー・手動修正する中で、以下の4つの根本原因が判明した。これらは `diagram-generator` の生成ロジックの不備と `diagram-drawio-reviewer` の検証ルール欠落によって引き起こされる再現性のある問題であり、同様の構成図を生成するたびに同じ問題が発生するリスクがある。

両エージェントにルールを反映することで、問題の発生（生成フェーズ）と検出（レビューフェーズ）の両面をカバーする。

## 根本原因と対応ルール

### 根本原因 1: テキストセルへの `autosize=1` 適用

**発生事象**: "ECS Cluster" テキストラベルが Internet Gateway アイコンの位置に表示される（座標設定が `autosize=1` により上書きされる）

**原因**: DrawIO の `autosize=1` スタイル属性は、レンダリング時に x/y 座標を自動的に再計算・上書きする。テキストセルに `autosize=1` を付与すると、XML に記述した座標値が無効化され、意図しない位置にテキストが配置される。

**新ルール R13**:
- generator: テキストセル（`shape=` なし、`vertex="1"` かつ `value` を持つセル）のスタイルに `autosize=1` を含めてはならない
- reviewer: `autosize=1` を含むテキストセルを ERROR として検出する

---

### 根本原因 2: 複数AZに跨るリソースのラベル不統一

**発生事象**: AZ-1a の ALB は `"Application Load Balancer (internet-facing)"` と表示され、AZ-1c の ALB は `"ALB (Multi-AZ)"` と表示された（同一リソースの別表現が混在）

**原因**: 同一の論理リソース（Multi-AZ 配置の ALB）が複数の Availability Zone にアイコンとして配置される場合、各セルの `value` 属性に異なる文字列が設定された。

**新ルール R14**:
- generator: 同一の論理リソースを複数の AZ コンテナ内に配置する場合、すべてのセルの `value` を同一文字列にする
- reviewer: 同一 AWS サービス（`shape=mxgraph.aws4.*` が共通）を複数 AZ に配置している場合、`value` が不一致なら WARNING として検出する

---

### 根本原因 3: VPC コンテナとリージョンコンテナの上端が同一 y 座標

**発生事象**: リージョン枠とVPC枠が上端で重なって見える（枠線が一本線に見える）

**原因**: `region-1`（リージョンコンテナ）と `vpc-main`（VPC コンテナ）の絶対 y 座標が両方とも `y=100` で同一であった。DrawIO はコンテナの上端ボーダーをコンテナの y 座標位置に描画するため、差分が 0px の場合は2本の枠線が重なる。

**新ルール R15**:
- generator: VPC コンテナの絶対 y 座標は、リージョンコンテナの絶対 y 座標より 60px 以上下に配置する
- reviewer: VPC コンテナの絶対 y 座標とリージョンコンテナの絶対 y 座標の差が 60px 未満なら ERROR として検出する

---

### 根本原因 4: エッジの exit 方向がソース・ターゲットの相対位置と不一致

**発生事象**: NAT Gateway への outbound エッジが ALB→Fargate のエッジと交差する

**原因**: `edge-ecs-to-nat` の `exitX=0` は「ソースの左側から出る」を意味するが、ECS Fargate（ソース）の右上方向に NAT Gateway（ターゲット）が位置するため、左出口では経路が交差する。正しくは `exitX=1`（右出口）かつ `entryY=1`（ターゲット下入口）とすべきであった。

**新ルール R16**:
- generator: `exitX/exitY/entryX/entryY` はソース・ターゲットの相対位置に基づいて選択する。ターゲットがソースの右側にある場合は `exitX=1`、左側は `exitX=0`、上方は `exitY=0`、下方は `exitY=1`
- reviewer: ターゲットがソースより右側（絶対 x 座標が大きい）にもかかわらず `exitX=0` が設定されている場合、またはその逆の場合を WARNING として検出する

## Requirements

- R1. `diagram-generator` に生成禁止ルール R13（autosize=1 禁止）を追加する
- R2. `diagram-generator` に生成ルール R14（複数AZ同一ラベル）を追加する
- R3. `diagram-generator` に生成ルール R15（VPC y座標オフセット ≥ 60px）を追加する
- R4. `diagram-generator` に生成ルール R16（exit/entry 方向の相対位置選択）を追加する
- R5. `diagram-drawio-reviewer` に検証ルール R13（ERROR: autosize=1 on text cell）を追加する
- R6. `diagram-drawio-reviewer` に検証ルール R14（WARNING: 複数AZ ラベル不一致）を追加する
- R7. `diagram-drawio-reviewer` に検証ルール R15（ERROR: VPC/リージョン y 差 < 60px）を追加する
- R8. `diagram-drawio-reviewer` に検証ルール R16（WARNING: exit 方向とターゲット相対位置の不一致）を追加する

## Success Criteria

- 同一構成の構成図を再生成したとき、上記4つの問題が発生しない
- `diagram-drawio-reviewer` が既存の `architecture.drawio` を検証した際、修正済みのファイルで R13–R16 に関する違反が0件になる
- `diagram-drawio-reviewer` が修正前のファイル（または意図的に問題を含む drawio）を検証した際、対応するルール違反が検出される

## Scope Boundaries

- 既存のルール R01–R12 は変更しない
- `diagram-image-reviewer` および `diagram-fixer` への変更は対象外（視覚検査・自動修正で対応済みの範囲のため）
- ルール R13–R16 の自動修正ロジックを `diagram-fixer` に追加することは対象外（今回は generator + reviewer のみ）

## Key Decisions

- **両エージェントに追加（reviewer のみではなく）**: 問題の根本原因は generator の生成ロジックにあるため、reviewer での検出だけでなく generator で最初から正しい XML を生成させることが最も効果的
- **R14 は WARNING（ERROR ではない）**: ラベルの表記揺れは品質上の問題だが、構造的には有効な XML であるため WARNING 扱いとする
- **R16 は WARNING（ERROR ではない）**: exit 方向の誤りは視覚的な問題（エッジ交差）を引き起こすが、DrawIO としては有効な XML であるため WARNING 扱いとする

## Dependencies / Assumptions

- `diagram-generator.md` の現行ルールセクションが存在し、ルール番号体系が確立されていること
- `diagram-drawio-reviewer.md` の現行ルールが R01–R12 として定義されており、R13 以降の番号が未使用であること

## Next Steps

→ `/ce:plan` で実装計画を作成する
