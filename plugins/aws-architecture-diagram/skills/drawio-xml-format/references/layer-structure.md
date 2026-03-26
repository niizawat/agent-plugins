# DrawIO Layer Structure for AWS Architecture Diagrams

## Standard 6-Layer Configuration

このプラグインでは、以下の6レイヤー構成を標準として使用します。

| Layer ID | 表示名 | 対象リソース |
|----------|--------|-------------|
| layer-0 | Layer 0: アカウント/リージョン | AWS Account boundary, Region |
| layer-1 | Layer 1: ネットワーク | VPC, Subnet, IGW, NAT GW, Route Tables, VPC Endpoints, TGW |
| layer-2 | Layer 2: セキュリティ | Security Groups, NACLs, WAF, Shield, Cognito, ACM, KMS |
| layer-3 | Layer 3: アプリケーション | EC2, ECS, EKS, Lambda, ALB, NLB, API GW, CloudFront, Step Functions |
| layer-4 | Layer 4: データ | RDS, Aurora, DynamoDB, ElastiCache, S3, Kinesis, SQS, SNS |
| layer-5 | Layer 5: 監視・運用 | CloudWatch, X-Ray, CloudTrail, Config, Systems Manager |

---

## Layer XML Definitions (Complete)

```xml
<!-- Always include all 6 layers in every diagram -->
<mxCell id="layer-0" value="Layer 0: アカウント/リージョン" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<mxCell id="layer-1" value="Layer 1: ネットワーク" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<mxCell id="layer-2" value="Layer 2: セキュリティ" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<mxCell id="layer-3" value="Layer 3: アプリケーション" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<mxCell id="layer-4" value="Layer 4: データ" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
<mxCell id="layer-5" value="Layer 5: 監視・運用" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

---

## Parent Chain for Nested Resources

DrawIOではネストされたリソースの`parent`チェーンに注意が必要です。

### 例: EC2インスタンスをサブネット内に配置する場合

```
EC2 (vertex) → parent: subnet-priv-1a
  └─ subnet-priv-1a (vertex) → parent: az-1a  OR  vpc-main
       └─ az-1a (vertex) → parent: vpc-main  OR  layer-1
            └─ vpc-main (vertex) → parent: layer-1
                 └─ layer-1 (vertex) → parent: 1
```

**重要**: `parent`チェーンは必ずルート（`id="1"`）まで繋がっていなければなりません。

### 例: レイヤー直下にVPCを置く場合

```xml
<!-- VPC is a direct child of layer-1 -->
<mxCell id="vpc-main" value="VPC" ... vertex="1" parent="layer-1">
  <mxGeometry x="80" y="80" width="1600" height="900" as="geometry" />
</mxCell>

<!-- AZ is inside VPC -->
<mxCell id="az-1a" value="ap-northeast-1a" ... vertex="1" parent="vpc-main">
  <mxGeometry x="20" y="60" width="760" height="760" as="geometry" />
</mxCell>

<!-- Public Subnet is inside AZ (or directly in VPC) -->
<mxCell id="subnet-pub-1a" value="Public Subnet" ... vertex="1" parent="az-1a">
  <mxGeometry x="20" y="60" width="340" height="280" as="geometry" />
</mxCell>

<!-- EC2 is inside the Subnet (on layer-3 visually, but parent is subnet) -->
<!-- NOTE: parent must be the container for positioning, not the layer -->
<mxCell id="ec2-bastion" value="Bastion Host" ... vertex="1" parent="subnet-pub-1a">
  <mxGeometry x="140" y="110" width="60" height="60" as="geometry" />
</mxCell>
```

> **Draw.IOのレイヤーとparentの関係**:
> DrawIOでは、図形のparentは「論理的な所属先（コンテナ）」を指します。
> レイヤーはユーザーが切り替えできる「可視性グループ」です。
> **図形がコンテナの中に入る場合、parentはそのコンテナのIDにします**。
> レイヤーは最上位のコンテナ（VPC, Account等）のparentにのみ指定します。

---

## Cross-Layer Edges

異なるレイヤー間の接続（例: アプリケーション → データ）の場合:

```xml
<!-- Edge between ECS (layer-3 resource) and RDS (layer-4 resource) -->
<!-- Use parent="1" to make the edge visible regardless of layer visibility -->
<mxCell id="edge-ecs-rds" value="MySQL:3306"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;"
  edge="1" source="ecs-service" target="rds-primary" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

または同じレイヤーのparentを使っても構いませんが、`parent="1"`が最も安全です。

---

## Layer Visibility Best Practices

DrawIOでレイヤーを開いたとき、ユーザーが迷わないようにするための推奨事項:

1. **Layer 0（アカウント/リージョン）**: 常に表示。アーキテクチャ全体の外枠。
2. **Layer 1（ネットワーク）**: デフォルト表示。VPC/Subnetは他リソースのコンテキストに必要。
3. **Layer 2（セキュリティ）**: 必要に応じて表示/非表示。複雑な図でセキュリティを別途確認する際に有用。
4. **Layer 3（アプリケーション）**: 常に表示。主要な処理フローを示す。
5. **Layer 4（データ）**: 常に表示。データストアを示す。
6. **Layer 5（監視・運用）**: 必要に応じて表示/非表示。監視の詳細を別途確認する際に有用。

---

## Complete Minimal Diagram Template

```xml
<?xml version="1.0" encoding="UTF-8"?>
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1" tooltips="1"
              connect="1" arrows="1" fold="1" page="1" pageScale="1"
              pageWidth="2339" pageHeight="1654" math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />

    <!-- ====== Layer Definitions ====== -->
    <mxCell id="layer-0" value="Layer 0: アカウント/リージョン" style="" vertex="1" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="layer-1" value="Layer 1: ネットワーク" style="" vertex="1" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="layer-2" value="Layer 2: セキュリティ" style="" vertex="1" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="layer-3" value="Layer 3: アプリケーション" style="" vertex="1" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="layer-4" value="Layer 4: データ" style="" vertex="1" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>
    <mxCell id="layer-5" value="Layer 5: 監視・運用" style="" vertex="1" parent="1">
      <mxGeometry relative="1" as="geometry" />
    </mxCell>

    <!-- ====== Layer 0: Account/Region ====== -->
    <mxCell id="account-1" value="AWS Account"
      style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_account;grStroke=1;fillColor=none;strokeColor=#CD853F;strokeWidth=3;verticalLabelPosition=top;verticalAlign=bottom;labelBackgroundColor=none;sketch=0;fontStyle=1;fontSize=14;"
      vertex="1" parent="layer-0">
      <mxGeometry x="80" y="80" width="2100" height="1400" as="geometry" />
    </mxCell>

    <mxCell id="region-1" value="ap-northeast-1 (東京)"
      style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;grStroke=1;fillColor=none;strokeColor=#147EBA;strokeWidth=2;verticalLabelPosition=top;verticalAlign=bottom;labelBackgroundColor=none;sketch=0;fontStyle=1;fontSize=12;"
      vertex="1" parent="account-1">
      <mxGeometry x="80" y="80" width="1900" height="1200" as="geometry" />
    </mxCell>

    <!-- ====== Layer 1: Network ====== -->
    <!-- Add VPC, Subnets, IGW, NAT GW here -->

    <!-- ====== Layer 2: Security ====== -->
    <!-- Add WAF, Shield, Security Groups here -->

    <!-- ====== Layer 3: Application ====== -->
    <!-- Add ALB, ECS, Lambda, API GW here -->

    <!-- ====== Layer 4: Data ====== -->
    <!-- Add RDS, DynamoDB, S3 here -->

    <!-- ====== Layer 5: Monitoring ====== -->
    <!-- Add CloudWatch, X-Ray here -->

    <!-- ====== Connections ====== -->
    <!-- Add edges here with parent="1" for cross-layer edges -->

  </root>
</mxGraphModel>
```
