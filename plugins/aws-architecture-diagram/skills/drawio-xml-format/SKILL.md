---
name: DrawIO XML Format for AWS Diagrams
description: This skill should be used when generating or editing DrawIO XML for AWS architecture diagrams, when asked about "DrawIOのXML形式", "drawioのシェイプ名", "AWSアイコンの使い方", "レイヤーの定義方法", or when the aws-architecture-diagram agent needs technical reference for DrawIO XML structure, AWS shape names, layer syntax, or connection styles.
version: 0.1.0
---

# DrawIO XML Format for AWS Architecture Diagrams

DrawIO uses an XML-based format to represent diagrams. Understanding the structure is essential for programmatically generating valid `.drawio` files.

## Document Root Structure

Every `.drawio` file has this skeleton:

```xml
<mxGraphModel dx="1422" dy="762" grid="1" gridSize="10" guides="1"
              tooltips="1" connect="1" arrows="1" fold="1" page="1"
              pageScale="1" pageWidth="2339" pageHeight="1654"
              math="0" shadow="0">
  <root>
    <mxCell id="0" />
    <mxCell id="1" parent="0" />
    <!-- All layers, shapes, and edges go here -->
  </root>
</mxGraphModel>
```

**Page sizes** (use A3 landscape for complex diagrams):
- A4 landscape: `pageWidth="1654" pageHeight="1169"`
- A3 landscape: `pageWidth="2339" pageHeight="1654"` (recommended for AWS diagrams)

---

## Layer System

Layers are `mxCell` nodes that are direct children of `<mxCell id="1">`. Shapes placed on a layer use the layer's `id` as their `parent` attribute.

### Defining Layers

```xml
<!-- Layer 0: Account/Region -->
<mxCell id="layer-0" value="Layer 0: アカウント/リージョン" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Layer 1: Network -->
<mxCell id="layer-1" value="Layer 1: ネットワーク" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Layer 2: Security -->
<mxCell id="layer-2" value="Layer 2: セキュリティ" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Layer 3: Application -->
<mxCell id="layer-3" value="Layer 3: アプリケーション" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Layer 4: Data -->
<mxCell id="layer-4" value="Layer 4: データ" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>

<!-- Layer 5: Monitoring/Operations -->
<mxCell id="layer-5" value="Layer 5: 監視・運用" style="" vertex="1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### Placing Shapes on Layers

Set `parent` to the layer ID:

```xml
<!-- This EC2 shape is on Layer 3 (Application) -->
<mxCell id="ec2-web" value="Web Server\n(EC2 t3.medium)"
        style="shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ec2;..."
        vertex="1" parent="layer-3">
  <mxGeometry x="400" y="300" width="60" height="60" as="geometry" />
</mxCell>
```

> **Note**: Shapes inside a container (e.g., a subnet group) should use the container's ID as `parent`, not the layer ID directly. The container itself uses the layer ID as its `parent`.

---

## Shape Types

### Resource Icons (Standard AWS Service Icons)

```xml
<mxCell id="UNIQUE_ID" value="LABEL"
  style="shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.ICON_NAME;
         labelBackgroundColor=none;sketch=0;fontStyle=1;fontSize=11;"
  vertex="1" parent="PARENT_ID">
  <mxGeometry x="X" y="Y" width="60" height="60" as="geometry" />
</mxCell>
```

### Container Groups (VPC, Subnet, AZ)

```xml
<!-- VPC Group -->
<mxCell id="vpc-main" value="VPC\n10.0.0.0/16"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];
         shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc2;grStroke=1;
         verticalLabelPosition=top;verticalAlign=bottom;
         labelBackgroundColor=none;sketch=0;fontStyle=1;fontSize=12;"
  vertex="1" parent="layer-1">
  <mxGeometry x="200" y="200" width="1600" height="900" as="geometry" />
</mxCell>

<!-- Public Subnet -->
<mxCell id="subnet-pub-1a" value="パブリックサブネット\n10.0.1.0/24 (ap-northeast-1a)"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];
         shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_public_subnet;grStroke=0;
         fillColor=#E8F5E9;strokeColor=#66BB6A;
         verticalLabelPosition=top;verticalAlign=bottom;
         labelBackgroundColor=none;sketch=0;fontSize=11;"
  vertex="1" parent="vpc-main">
  <mxGeometry x="40" y="60" width="360" height="300" as="geometry" />
</mxCell>

<!-- Private Subnet -->
<mxCell id="subnet-priv-1a" value="プライベートサブネット\n10.0.11.0/24 (ap-northeast-1a)"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];
         shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_private_subnet;grStroke=0;
         fillColor=#E3F2FD;strokeColor=#42A5F5;
         verticalLabelPosition=top;verticalAlign=bottom;
         labelBackgroundColor=none;sketch=0;fontSize=11;"
  vertex="1" parent="vpc-main">
  <mxGeometry x="440" y="60" width="360" height="300" as="geometry" />
</mxCell>
```

### Availability Zone Group

```xml
<mxCell id="az-1a" value="ap-northeast-1a"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];
         shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_availability_zone;grStroke=1;
         fillColor=none;strokeColor=#147EBA;strokeWidth=2;
         verticalLabelPosition=top;verticalAlign=bottom;
         labelBackgroundColor=none;sketch=0;fontStyle=2;fontSize=11;"
  vertex="1" parent="vpc-main">
  <mxGeometry x="20" y="40" width="820" height="380" as="geometry" />
</mxCell>
```

### AWS Account / Region Containers

```xml
<!-- AWS Account -->
<mxCell id="account-1" value="AWS Account"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];
         shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_account;grStroke=1;
         fillColor=none;strokeColor=#CD853F;strokeWidth=3;
         verticalLabelPosition=top;verticalAlign=bottom;
         labelBackgroundColor=none;sketch=0;fontStyle=1;fontSize=14;"
  vertex="1" parent="layer-0">
  <mxGeometry x="80" y="80" width="2000" height="1400" as="geometry" />
</mxCell>

<!-- AWS Region -->
<mxCell id="region-1" value="ap-northeast-1 (東京)"
  style="points=[[0,0],[0.25,0],[0.5,0],[0.75,0],[1,0],[1,0.25],[1,0.5],[1,0.75],[1,1],[0.75,1],[0.5,1],[0.25,1],[0,1],[0,0.75],[0,0.5],[0,0.25]];
         shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_region;grStroke=1;
         fillColor=none;strokeColor=#147EBA;strokeWidth=2;
         verticalLabelPosition=top;verticalAlign=bottom;
         labelBackgroundColor=none;sketch=0;fontStyle=1;fontSize=12;"
  vertex="1" parent="account-1">
  <mxGeometry x="80" y="80" width="1800" height="1200" as="geometry" />
</mxCell>
```

---

## Connection Edges

### エッジラベルの重なり防止ルール

アイコンラベル（`verticalLabelPosition=bottom`）は下方向に **約40px** を占有する。
エッジラベルをデフォルト中央（`relative=0.5`）に置くと、この領域と重なりやすい。

**判定基準**:

- アイコン間の距離が **200px 未満** → ラベルを省略するか `<mxPoint>` でオフセット
- アイコン間の距離が **200px 以上** → ラベル背景色を白にして可読性を確保

**垂直方向エッジのラベルオフセット（推奨）**:

```xml
<mxCell id="edge-cf-s3" value="S3 Origin"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
         jettySize=auto;align=left;labelBackgroundColor=#ffffff;labelBorderColor=none;"
  edge="1" source="cloudfront-1" target="s3-assets" parent="1">
  <mxGeometry relative="1" as="geometry">
    <!-- ラベルを中央から右に20pxずらして重なりを回避 -->
    <mxPoint x="20" y="0" as="offset" />
  </mxGeometry>
</mxCell>
```

**水平方向エッジのラベル（標準）**:

```xml
<mxCell id="edge-alb-ecs" value="HTTP:8080"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
         jettySize=auto;labelBackgroundColor=#ffffff;labelBorderColor=none;"
  edge="1" source="alb-1" target="ecs-service" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

**ラベルを省略する場合（間隔が狭い時）**:

```xml
<!-- value="" でラベルなし、矢印のみ -->
<mxCell id="edge-waf-cf" value=""
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;"
  edge="1" source="waf-1" target="cloudfront-1" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

---

### Synchronous (Solid Line)

```xml
<mxCell id="edge-alb-ecs" value="HTTP:8080"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
         jettySize=auto;exitX=1;exitY=0.5;exitDx=0;exitDy=0;
         entryX=0;entryY=0.5;entryDx=0;entryDy=0;
         labelBackgroundColor=#ffffff;labelBorderColor=none;"
  edge="1" source="alb-1" target="ecs-service" parent="1">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### Asynchronous / Event-Driven (Dashed Line)

```xml
<mxCell id="edge-lambda-sqs" value="publish"
  style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;
         jettySize=auto;dashed=1;dashPattern=8 4;"
  edge="1" source="lambda-processor" target="sqs-queue" parent="layer-3">
  <mxGeometry relative="1" as="geometry" />
</mxCell>
```

### Cross-Layer Edge

For connections that span layers (e.g., application to data), use `parent="layer-3"` of the source's layer. Alternatively, use `parent="1"` to make it a root-level edge visible across all layers.

---

## Coordinate System & Layout Guidelines

- **Origin**: Top-left corner is (0, 0)
- **Standard icon size**: 60×60px
- **Effective icon footprint**: 120px wide × 100px tall（ラベル込み。`verticalLabelPosition=bottom` のラベルが下方向に約40px占有）
- **Minimum spacing between icon centers**: 200px horizontal, 180px vertical
- **Group internal padding**: 60px on all sides（ラベルが枠外にはみ出さないよう余裕を持たせる）
- **Inter-group spacing**: 80px

> **重要**: アイコン中心間距離が200px未満だとエッジラベルとアイコンラベルが重なる。
> 必ず200px以上の間隔を確保すること。

**Recommended starting positions**:

- External resources (Internet, User): x=80, y=400
- AWS Account container: x=80, y=80
- VPC: offset 160px from region container edges

---

## Common Style Attributes

| Attribute | Purpose | Example |
|-----------|---------|---------|
| `sketch=0` | Disable hand-drawn look | `sketch=0` |
| `fontStyle=1` | Bold label | `fontStyle=1` |
| `fontSize=11` | Label size | `fontSize=11` |
| `fillColor` | Background color | `fillColor=#E8F5E9` |
| `strokeColor` | Border color | `strokeColor=#66BB6A` |
| `verticalLabelPosition=top` | Label above shape | `verticalLabelPosition=top` |
| `labelBackgroundColor=none` | No label background | `labelBackgroundColor=none` |

---

## Additional Resources

For the complete AWS shape name reference, consult:

- **`references/aws-shapes.md`** — Full list of AWS 2026 shape names for all services
- **`references/layer-structure.md`** — Detailed layer organization patterns and examples
