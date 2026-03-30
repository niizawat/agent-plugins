# agent-plugins

Claude Code 用のマーケットプレイスリポジトリです。
本 README は同梱プラグイン **`aws-architecture-diagram`** の説明です。

## インストール

### 1. マーケットプレイスを追加

Claude Code のチャットで次を実行します（URL は fork 等に合わせて置き換え可）。

```text
/plugin marketplace add https://github.com/niizawat/agent-plugins.git
```

### 2. プラグインをインストール

```text
/plugin install aws-architecture-diagram@agent-plugins
```

`@` 以降はリポジトリ直下 `.claude-plugin/marketplace.json` の `name`（本リポジトリでは
`agent-plugins`）です。
スコープ等のオプションは `/plugin` のヘルプまたは公式ドキュメントを参照してください。

---

## aws-architecture-diagram とは

IaC コード（CDK TypeScript・CloudFormation・Terraform）またはシステム要件から、
AWS アーキテクチャ構成図を DrawIO 形式（`.drawio`）で自動生成する Claude Code プラグインです。

### 機能

- **IaC 解析**: CDK TypeScript・CloudFormation YAML/JSON・Terraform HCL から AWS リソースと接続関係を抽出
- **テキスト要件対応**: 自然言語のシステム要件からも構成図を生成
- **AWS 2026 アイコン**: DrawIO の AWS 公式アイコンを使用
- **6 レイヤー構成**: 役割ごとにレイヤーを分けて描画
- **クリーンなレイアウト**: 要素の重複なし、線が見やすいオルソゴナルルーティング
- **自動 QA ループ**: 生成→レビュー→修正を自動繰り返し、CRITICAL/ERROR ゼロを目指す

### レイヤー構成

| レイヤー | 内容 |
| --- | --- |
| Layer 0 | アカウント/リージョン |
| Layer 1 | ネットワーク（VPC, Subnet, IGW） |
| Layer 2 | セキュリティ（SG, WAF, Shield） |
| Layer 3 | アプリケーション（EC2, ECS, Lambda, ALB） |
| Layer 4 | データ（RDS, DynamoDB, S3） |
| Layer 5 | 監視・運用（CloudWatch, X-Ray） |

### 使い方

#### CDK コードから生成

```text
CDKのコードからAWSアーキテクチャ図を作成して。出力先: ./docs/architecture.drawio
```

#### CloudFormation から生成

```text
このCloudFormationテンプレートをDrawIOの構成図にしてほしい。/path/to/template.yamlを読んで
```

#### Terraform から生成

```text
TerraformコードからAWS構成図を生成してください。出力先は ./architecture.drawio
```

#### テキスト要件から生成

```text
ALB→ECS Fargate→Aurora MySQLの3層Web構成図を作って。
VPCにパブリック/プライベートサブネットを2AZ構成で。出力先: ./arch.drawio
```

### レビュー機能

生成した構成図がルールに従っているか検証できます。

```text
生成した構成図をレビューして
```

```text
output.drawioがルール通りに作成されているか検証して
```

レビューエージェントは次を確認します。

- **XML 構造** (R01): mxGraphModel/root/基底セルの整合性
- **レイヤー定義** (R02): 6 レイヤーすべての存在確認
- **ID 重複なし** (R03): mxCell ID の一意性
- **アイコン間隔** (R04): 同一コンテナ内の最小間隔（水平 200px・垂直 180px）
- **レイヤー配置** (R07): サービスの適切なレイヤーへの配置
- **AWS シェイプ名** (R08): aws4 プレフィックスの使用
- **エッジスタイル** (R09): orthogonalEdgeStyle の使用
- **エッジラベル** (R10): 短距離接続のラベル重なりリスク
- **コンテナの子** (R11): 空コンテナの検出
- **外部リソース** (R12): VPC 左側への配置確認
- **視覚的確認**: PNG 出力でアイコン重なり・ラベル可読性を確認（`drawio` CLI が必要）

### コンポーネント

#### Agents

- **`diagram-generator`**: IaC/要件を解析して DrawIO XML を生成・保存
- **`diagram-reviewer`**: 構成図をルールに従って検証（XML 解析＋視覚的確認）
- **`diagram-qa`**: QA ループのオーケストレーション。生成→レビュー→修正を最大 3 回まで自動実行
- **`diagram-fixer`**: レビューレポートに基づき DrawIO XML を最小限の差分で修正

#### Skills

- **`drawio-xml-format`**: DrawIO XML の構造・シェイプ名・レイヤー定義のリファレンス
- **`aws-architecture-patterns`**: AWS アーキテクチャパターンとレイアウトガイド
- **`iac-analyzer`**: CDK/CloudFormation/Terraform から AWS リソースを抽出する手順
- **`drawio-export`**: `.drawio` を PNG に変換（`drawio` CLI を使用）

### 出力例

生成した DrawIO を draw.io（デスクトップまたは
[diagrams.net](https://app.diagrams.net/)）で開くと、レイヤーパネルに 6 つのレイヤーが表示され、
役割ごとに図形が整理されます。

### 前提条件

- Claude Code（claude-code CLI）
- draw.io で `.drawio` を開ける環境
- 視覚レビューには `drawio` CLI 推奨: `brew install drawio`

### ローカル開発（参考）

プラグイン単体をディレクトリ指定で読み込む場合の例です。

```bash
claude --plugin-dir /path/to/agent-plugins/plugins/aws-architecture-diagram
```

---

## リポジトリ構造（抜粋）

```text
agent-plugins/
├── .claude-plugin/
│   └── marketplace.json          # マーケットプレイス定義
├── README.md                     # 本ファイル（aws-architecture-diagram の説明）
└── plugins/
    └── aws-architecture-diagram/
        ├── .claude-plugin/
        │   └── plugin.json
        ├── agents/
        ├── skills/
        ├── README.md             # プラグイン直下の README（内容は本 README と同一趣旨）
        └── workflow.md           # エージェントワークフロー図
```
