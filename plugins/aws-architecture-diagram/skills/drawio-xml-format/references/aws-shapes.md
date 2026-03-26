# AWS Shape Names for DrawIO (AWS4 / 最新版 v29.6.1)

> **重要**: draw.ioのAWSシェイプは "AWS 2026" という独立したプレフィックスは存在せず、
> 現在も **`mxgraph.aws4`** が最新かつ唯一の推奨プレフィックスです（v29.6.1時点、2026年3月更新）。
> ソース: <https://github.com/jgraph/drawio> `src/main/webapp/js/diagramly/sidebar/Sidebar-AWS4.js`

---

## 完全スタイルテンプレート

すべてのリソースアイコンはこのテンプレートをベースにする:

```text
sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;fillColor=<CATEGORY_COLOR>;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<ICON_NAME>;
```

---

## カテゴリ別 fillColor

| カテゴリ | fillColor |
| -------- | --------- |
| Compute / Containers | `#ED7100` |
| Storage | `#7AA116` |
| Database | `#C925D1` |
| Network & Content Delivery | `#8C4FFF` |
| Application Integration | `#E7157B` |
| Analytics | `#8C4FFF` |
| Management & Governance | `#E7157B` |
| Security, Identity, Compliance | `#DD344C` |
| AI / Machine Learning | `#01A88D` |

---

## グループ・コンテナのスタイル

グループコンテナの共通ベース（全コンテナ共通の先頭部分）:

```text
points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;
```

### AWS Account

```xml
<mxCell id="account-1" value="AWS Account"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_account;strokeColor=#CD2264;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#CD2264;dashed=0;"
  vertex="1" parent="layer-0">
  <mxGeometry x="80" y="80" width="2100" height="1400" as="geometry" />
</mxCell>
```

### AWS Cloud (Account alternative)

```xml
style="...shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud_alt;strokeColor=#232F3E;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#232F3E;dashed=0;"
```

### Region

```xml
<mxCell id="region-1" value="ap-northeast-1 (東京)"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;strokeColor=#00A4A6;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;dashed=1;"
  vertex="1" parent="account-1">
  <mxGeometry x="80" y="80" width="1900" height="1200" as="geometry" />
</mxCell>
```

### VPC

```xml
<mxCell id="vpc-main" value="VPC (10.0.0.0/16)"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;strokeColor=#8C4FFF;fillColor=none;verticalAlign=top;align=left;spacingLeft=30;fontColor=#AAB7B8;dashed=0;"
  vertex="1" parent="layer-1">
  <mxGeometry x="300" y="150" width="1600" height="900" as="geometry" />
</mxCell>
```

> **注意**: VPCは `group_vpc2` (アンダースコア+2) を使う。`group_vpc` は旧バージョン。

### Availability Zone

AZはgrIconなしのシンプルな破線ボックス:

```xml
<mxCell id="az-1a" value="ap-northeast-1a"
  style="fillColor=none;strokeColor=#147EBA;dashed=1;verticalAlign=top;fontStyle=0;fontColor=#147EBA;whiteSpace=wrap;html=1;"
  vertex="1" parent="vpc-main">
  <mxGeometry x="20" y="60" width="750" height="820" as="geometry" />
</mxCell>
```

### Public Subnet

```xml
<mxCell id="subnet-pub-1a" value="パブリックサブネット (10.0.1.0/24)"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#7AA116;fillColor=#F2F6E8;verticalAlign=top;align=left;spacingLeft=30;fontColor=#248814;dashed=0;"
  vertex="1" parent="az-1a">
  <mxGeometry x="20" y="60" width="340" height="280" as="geometry" />
</mxCell>
```

### Private Subnet

```xml
<mxCell id="subnet-priv-1a" value="プライベートサブネット (10.0.11.0/24)"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group;grStroke=0;strokeColor=#00A4A6;fillColor=#E6F6F7;verticalAlign=top;align=left;spacingLeft=30;fontColor=#147EBA;dashed=0;"
  vertex="1" parent="az-1a">
  <mxGeometry x="380" y="60" width="340" height="280" as="geometry" />
</mxCell>
```

### Auto Scaling Group

```xml
<mxCell id="asg-web" value="Auto Scaling Group&#xa;Web Tier (min:2 max:10)"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];outlineConnect=0;gradientColor=none;html=1;whiteSpace=wrap;fontSize=12;fontStyle=0;container=1;pointerEvents=0;collapsible=0;recursiveResize=0;shape=mxgraph.aws4.groupCenter;grIcon=mxgraph.aws4.group_auto_scaling_group;grStroke=1;strokeColor=#D86613;fillColor=none;verticalAlign=top;align=center;fontColor=#D86613;dashed=1;spacingTop=25;"
  vertex="1" parent="subnet-priv-1a">
  <mxGeometry x="20" y="40" width="300" height="200" as="geometry" />
</mxCell>
```

### Security Group (オーバーレイ枠)

```xml
<mxCell id="sg-web" value="sg-web"
  style="fillColor=none;strokeColor=#DD3522;verticalAlign=top;fontStyle=0;fontColor=#DD3522;whiteSpace=wrap;html=1;"
  vertex="1" parent="subnet-priv-1a">
  <mxGeometry x="100" y="80" width="140" height="140" as="geometry" />
</mxCell>
```

---

## コンピューティング (`fillColor=#ED7100`)

| サービス | resIcon |
| -------- | ------- |
| EC2 | `mxgraph.aws4.ec2` |
| EC2 Auto Scaling | `mxgraph.aws4.auto_scaling2` |
| Lambda | `mxgraph.aws4.lambda` |
| ECS | `mxgraph.aws4.ecs` |
| EKS | `mxgraph.aws4.eks` |
| Fargate | `mxgraph.aws4.fargate` |
| ECR | `mxgraph.aws4.ecr` |
| Elastic Beanstalk | `mxgraph.aws4.elastic_beanstalk` |
| Batch | `mxgraph.aws4.batch` |
| App Runner | `mxgraph.aws4.app_runner` |

**EC2 アイコンの完全なスタイル例**:

```xml
<mxCell id="ec2-web" value="Web Server&#xa;(t3.medium)"
  style="sketch=0;points=[[0,0,0],[0.25,0,0],[0.5,0,0],[0.75,0,0],[1,0,0],[0,1,0],[0.25,1,0],[0.5,1,0],[0.75,1,0],[1,1,0],[0,0.25,0],[0,0.5,0],[0,0.75,0],[1,0.25,0],[1,0.5,0],[1,0.75,0]];outlineConnect=0;fontColor=#232F3E;fillColor=#ED7100;strokeColor=#ffffff;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;"
  vertex="1" parent="subnet-priv-1a">
  <mxGeometry x="140" y="110" width="60" height="60" as="geometry" />
</mxCell>
```

---

## ネットワーク (`fillColor=#8C4FFF`)

| サービス | shape または resIcon |
| -------- | ------------------- |
| Application Load Balancer | `shape=mxgraph.aws4.application_load_balancer` (専用シェイプ) |
| Network Load Balancer | `shape=mxgraph.aws4.network_load_balancer` (専用シェイプ) |
| Elastic Load Balancing (サービスアイコン) | `resIcon=mxgraph.aws4.elastic_load_balancing` |
| CloudFront | `resIcon=mxgraph.aws4.cloudfront` |
| Route 53 | `resIcon=mxgraph.aws4.route_53` |
| API Gateway | `resIcon=mxgraph.aws4.api_gateway` |
| VPC Endpoint | `resIcon=mxgraph.aws4.vpc_endpoints` |
| Transit Gateway | `resIcon=mxgraph.aws4.transit_gateway` |
| VPN Gateway | `resIcon=mxgraph.aws4.vpn_gateway` |
| Direct Connect | `resIcon=mxgraph.aws4.direct_connect` |
| Global Accelerator | `resIcon=mxgraph.aws4.global_accelerator` |
| Internet Gateway | `resIcon=mxgraph.aws4.internet_gateway` |
| NAT Gateway | `resIcon=mxgraph.aws4.nat_gateway` |

**ALB 専用シェイプの完全なスタイル例**:

```xml
<mxCell id="alb-main" value="Application Load Balancer&#xa;(internet-facing)"
  style="sketch=0;outlineConnect=0;fontColor=#232F3E;gradientColor=none;fillColor=#8C4FFF;strokeColor=none;dashed=0;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;fontSize=12;fontStyle=0;aspect=fixed;pointerEvents=1;shape=mxgraph.aws4.application_load_balancer;"
  vertex="1" parent="subnet-pub-1a">
  <mxGeometry x="140" y="110" width="60" height="60" as="geometry" />
</mxCell>
```

---

## ストレージ (`fillColor=#7AA116`)

| サービス | resIcon |
| -------- | ------- |
| S3 | `mxgraph.aws4.s3` |
| EBS | `mxgraph.aws4.ebs` |
| EFS | `mxgraph.aws4.efs` |
| FSx | `mxgraph.aws4.fsx` |
| S3 Glacier | `mxgraph.aws4.s3_glacier` |
| Storage Gateway | `mxgraph.aws4.storage_gateway` |
| Backup | `mxgraph.aws4.backup` |

---

## データベース (`fillColor=#C925D1`)

| サービス | resIcon |
| -------- | ------- |
| RDS | `mxgraph.aws4.rds` |
| Aurora | `mxgraph.aws4.aurora` |
| DynamoDB | `mxgraph.aws4.dynamodb` |
| ElastiCache | `mxgraph.aws4.elasticache` |
| Neptune | `mxgraph.aws4.neptune` |
| DocumentDB | `mxgraph.aws4.documentdb` |
| MemoryDB | `mxgraph.aws4.memorydb_for_redis` |
| Redshift | `mxgraph.aws4.redshift` |
| QLDB | `mxgraph.aws4.qldb` |
| RDS Proxy | `mxgraph.aws4.rds_proxy` |

---

## アプリケーション統合 (`fillColor=#E7157B`)

| サービス | resIcon |
| -------- | ------- |
| SQS | `mxgraph.aws4.sqs` |
| SNS | `mxgraph.aws4.sns` |
| EventBridge | `mxgraph.aws4.eventbridge` |
| Step Functions | `mxgraph.aws4.step_functions` |
| AppSync | `mxgraph.aws4.appsync` |
| Kinesis Data Streams | `mxgraph.aws4.kinesis_data_streams` |
| Kinesis Data Firehose | `mxgraph.aws4.kinesis_data_firehose` |
| MSK (Kafka) | `mxgraph.aws4.managed_streaming_for_kafka` |

---

## セキュリティ (`fillColor=#DD344C`)

| サービス | resIcon |
| -------- | ------- |
| IAM | `mxgraph.aws4.role` |
| Cognito | `mxgraph.aws4.cognito` |
| WAF | `mxgraph.aws4.waf` |
| Shield | `mxgraph.aws4.shield` |
| KMS | `mxgraph.aws4.kms` |
| Secrets Manager | `mxgraph.aws4.secrets_manager` |
| ACM | `mxgraph.aws4.certificate_manager` |
| Security Hub | `mxgraph.aws4.security_hub` |
| GuardDuty | `mxgraph.aws4.guardduty` |
| Inspector | `mxgraph.aws4.inspector` |

---

## 監視・運用 (`fillColor=#E7157B`)

| サービス | resIcon |
| -------- | ------- |
| CloudWatch | `mxgraph.aws4.cloudwatch` |
| X-Ray | `mxgraph.aws4.xray` |
| Systems Manager | `mxgraph.aws4.systems_manager` |
| CloudTrail | `mxgraph.aws4.cloudtrail` |
| Config | `mxgraph.aws4.config` |
| Trusted Advisor | `mxgraph.aws4.trusted_advisor` |

---

## CI/CD (`fillColor=#E7157B`)

| サービス | resIcon |
| -------- | ------- |
| CodePipeline | `mxgraph.aws4.codepipeline` |
| CodeBuild | `mxgraph.aws4.codebuild` |
| CodeDeploy | `mxgraph.aws4.codedeploy` |
| CodeCommit | `mxgraph.aws4.codecommit` |
| CodeArtifact | `mxgraph.aws4.codeartifact` |

---

## データ分析 (`fillColor=#8C4FFF`)

| サービス | resIcon |
| -------- | ------- |
| Athena | `mxgraph.aws4.athena` |
| Glue | `mxgraph.aws4.glue` |
| EMR | `mxgraph.aws4.emr` |
| QuickSight | `mxgraph.aws4.quicksight` |
| Lake Formation | `mxgraph.aws4.lake_formation` |

---

## 汎用シェイプ

| 用途 | style |
| ---- | ----- |
| インターネット/ユーザー | `shape=mxgraph.aws4.traditional_server;sketch=0;` |
| ユーザー/クライアント | `shape=mxgraph.aws4.user;sketch=0;` |
| モバイルクライアント | `shape=mxgraph.aws4.mobile_client;sketch=0;` |

---

## 接続エッジスタイル早見表

| 種類 | style |
| ---- | ----- |
| 同期（実線） | `edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;` |
| 非同期（破線） | `edgeStyle=orthogonalEdgeStyle;rounded=0;dashed=1;dashPattern=8 4;` |
| IAM権限（細点線） | `edgeStyle=orthogonalEdgeStyle;rounded=0;dashed=1;dashPattern=4 4;endArrow=none;strokeColor=#888888;` |
| レプリケーション（双方向） | `edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;startArrow=block;startFill=1;endFill=1;` |

---

## シェイプ名の確認方法

draw.ioで正確なシェイプ名を確認する手順:

1. draw.io を開き Shape Libraries → AWS を有効化
2. 目的のサービスアイコンをキャンバスにドラッグ
3. アイコンを右クリック → **「スタイルの編集」** を選択
4. 表示された文字列から `resIcon=mxgraph.aws4.XXX` または `shape=mxgraph.aws4.XXX` をコピー

または、公式リポジトリを直接参照:
`https://github.com/jgraph/drawio` → `src/main/webapp/js/diagramly/sidebar/Sidebar-AWS4.js`
