# テスト用システム要件（テキスト入力テスト）

## システム概要

ECサイトのバックエンドAPI基盤。東京リージョン（ap-northeast-1）に構築。

## 構成要件

### ネットワーク
- VPC: 10.0.0.0/16
- 2 Availability Zone（1a・1c）
- パブリックサブネット × 2（各AZ）
- プライベートサブネット × 2（各AZ）
- DBサブネット × 2（各AZ）
- NAT Gateway × 1（コスト最適化）

### エントリポイント
- Route 53でドメイン管理（api.example.com）
- CloudFrontでグローバル配信・WAFでIPフィルタリング
- ALB（internet-facing）でHTTPS終端（443）

### アプリケーション層
- ECS Fargate × 3サービス（Order Service, User Service, Payment Service）
- 各サービス: desiredCount=2, cpu=256, memory=512MB
- ECRからDockerイメージをプル

### データ層
- RDS PostgreSQL（db.t3.medium, Multi-AZ）: ユーザー・注文データ
- ElastiCache Redis（cache.t3.micro）: セッションキャッシュ
- DynamoDB: カート情報（PAY_PER_REQUEST）
- S3: 商品画像・静的ファイル

### 非同期処理
- SQS FIFO キュー: 注文処理キュー
- Lambda（Node.js 20）: 注文確定後の通知処理
- SNS: メール・プッシュ通知配信

### 監視・運用
- CloudWatch: メトリクス・ログ収集
- X-Ray: 分散トレーシング
- Systems Manager Parameter Store: 設定値管理
