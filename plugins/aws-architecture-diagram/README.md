# aws-architecture-diagram

IaCコード（CDK TypeScript・CloudFormation・Terraform）またはシステム要件から、AWSアーキテクチャ構成図をDrawIO形式（`.drawio`）で自動生成するClaude Codeプラグイン。

## 機能

- **IaC解析**: CDK TypeScript・CloudFormation YAML/JSON・Terraform HCLを解析してAWSリソースと接続関係を抽出
- **テキスト要件対応**: 自然言語のシステム要件からも構成図を生成
- **AWS 2026アイコン**: DrawIOのAWS公式アイコンを使用
- **6レイヤー構成**: 役割ごとにレイヤーを分けて描画
- **クリーンなレイアウト**: 要素の重複なし、線が見やすいオルソゴナルルーティング
- **自動QAループ**: 生成→レビュー→修正を自動繰り返し、CRITICAL/ERROR ゼロを目指す

## レイヤー構成

| レイヤー | 内容 |
|---------|------|
| Layer 0 | アカウント/リージョン |
| Layer 1 | ネットワーク（VPC, Subnet, IGW） |
| Layer 2 | セキュリティ（SG, WAF, Shield） |
| Layer 3 | アプリケーション（EC2, ECS, Lambda, ALB） |
| Layer 4 | データ（RDS, DynamoDB, S3） |
| Layer 5 | 監視・運用（CloudWatch, X-Ray） |

## 使い方

### CDKコードから生成

```text
CDKのコードからAWSアーキテクチャ図を作成して。出力先: ./docs/architecture.drawio
```

### CloudFormationから生成

```text
このCloudFormationテンプレートをDrawIOの構成図にしてほしい。/path/to/template.yamlを読んで
```

### Terraformから生成

```text
TerraformコードからAWS構成図を生成してください。出力先は ./architecture.drawio
```

### テキスト要件から生成

```text
ALB→ECS Fargate→Aurora MySQLの3層Web構成図を作って。
VPCにパブリック/プライベートサブネットを2AZ構成で。出力先: ./arch.drawio
```

## レビュー機能

生成した構成図がルールに従っているか検証できます。

```text
生成した構成図をレビューして
```

```text
output.drawioがルール通りに作成されているか検証して
```

レビューエージェントは以下を確認します:

- **XML構造** (R01): mxGraphModel/root/基底セルの整合性
- **レイヤー定義** (R02): 6レイヤーすべての存在確認
- **ID重複なし** (R03): mxCell IDの一意性
- **アイコン間隔** (R04): 同一コンテナ内の最小間隔（水平200px・垂直180px）
- **レイヤー配置** (R07): サービスの適切なレイヤーへの配置
- **AWSシェイプ名** (R08): aws4プレフィックスの使用
- **エッジスタイル** (R09): orthogonalEdgeStyle の使用
- **エッジラベル** (R10): 短距離接続のラベル重なりリスク
- **コンテナの子** (R11): 空コンテナの検出
- **外部リソース** (R12): VPC左側への配置確認
- **視覚的確認**: PNG出力してアイコン重なり・ラベル可読性を画像で確認（`drawio` CLI必要）

## コンポーネント

### Agents

- **`diagram-generator`**: メインエージェント。IaC/要件を解析してDrawIO XMLを生成・保存
- **`diagram-reviewer`**: 生成した構成図をルールに従って検証。XML解析＋視覚的確認
- **`diagram-qa`**: QAループオーケストレーター。生成→レビュー→修正を最大3回繰り返し自動実行
- **`diagram-fixer`**: レビューレポートを受け取り、DrawIO XMLに最小限の差分修正を適用

### Skills

- **`drawio-xml-format`**: DrawIO XMLの構造・シェイプ名・レイヤー定義の技術リファレンス
- **`aws-architecture-patterns`**: 一般的なAWSアーキテクチャパターンとレイアウトガイド
- **`iac-analyzer`**: CDK/CloudFormation/TerraformコードからAWSリソース抽出の手順
- **`drawio-export`**: `.drawio` ファイルをPNG画像に変換（`drawio` CLI を使用）

## 出力例

生成されたDrawIOファイルをdraw.io（デスクトップアプリまたはapp.diagrams.net）で開くと、レイヤーパネルに6つのレイヤーが表示され、それぞれの役割ごとに図形が整理されています。

## 前提条件

- Claude Code（claude-code CLI）
- draw.io（デスクトップアプリまたはブラウザ版）でファイルを開く環境
- 視覚的レビューには `drawio` CLI が必要: `brew install drawio`

## インストール

### Claude Code（マーケットプレイス経由）

マーケットプレイスを登録したうえで、本プラグインをインストールします。コマンドは Claude Code のチャットで入力するスラッシュコマンドです。

1. **マーケットプレイスを追加**  
   プラグイン一覧が定義された Git リポジトリを登録します。URL は利用するマーケットプレイスに合わせて置き換えてください。

   ```text
   /plugin marketplace add https://github.com/niizawat/agent-plugins.git
   ```

2. **本プラグインをインストール**  
   マーケットプレイス名（リポジトリ直下の `.claude-plugin/marketplace.json` の `name`）と、プラグイン名を `@` でつなげます。

   ```text
   /plugin install aws-architecture-diagram@agent-plugins
   ```

インストール先やスコープなどのオプションは、利用中の Claude Code のバージョンに合わせて `/plugin` のヘルプまたは公式ドキュメントを参照してください。
