# AWS Architecture Pattern Examples

## Pattern 1: Web 3-Tier Application (Standard)

### Typical Component Layout

```
[Internet]
    |
[Route 53] ──────→ [CloudFront] ──→ [S3 Static Assets]
                         |
                      [WAF]
                         |
              [Application Load Balancer]
               (internet-facing, dual-AZ)
                    /          \
         [AZ: 1a]               [AZ: 1c]
    [Public Subnet]           [Public Subnet]
       [NAT GW]                  [NAT GW]
    [Private Subnet]          [Private Subnet]
    [ECS Fargate Task]        [ECS Fargate Task]
         |                          |
    [DB Subnet]               [DB Subnet]
    [RDS Primary]             [RDS Standby]
         |____Multi-AZ Sync________|
```

### Coordinate Map (A3 landscape, 2339x1654)

| Component | x | y | w | h |
|-----------|---|---|---|---|
| AWS Account | 80 | 80 | 2100 | 1400 |
| Region | 80 | 80 | 1900 | 1200 (inside Account) |
| VPC | 300 | 120 | 1500 | 900 (inside Region) |
| AZ-1a group | 20 | 60 | 700 | 800 (inside VPC) |
| AZ-1c group | 760 | 60 | 700 | 800 (inside VPC) |
| Public Subnet 1a | 20 | 60 | 660 | 200 (inside AZ-1a) |
| Private Subnet 1a | 20 | 300 | 660 | 200 (inside AZ-1a) |
| DB Subnet 1a | 20 | 540 | 660 | 180 (inside AZ-1a) |
| Internet user | 80 | 500 | 60 | 60 (outside VPC) |
| Route 53 | 80 | 400 | 60 | 60 (outside VPC, Layer 3) |
| CloudFront | 80 | 300 | 60 | 60 (outside VPC) |
| WAF | 80 | 200 | 60 | 60 (outside VPC, Layer 2) |
| ALB | 300 | 130 | 60 | 60 (inside Public Subnet 1a) |
| NAT GW 1a | 500 | 130 | 60 | 60 (inside Public Subnet 1a) |
| ECS Service 1a | 300 | 370 | 60 | 60 (inside Private Subnet 1a) |
| RDS Primary | 300 | 600 | 60 | 60 (inside DB Subnet 1a) |
| CloudWatch | 1700 | 500 | 60 | 60 (Layer 5) |

---

## Pattern 2: Serverless API

### Component Layout

```
[Client/Browser]
       |
  [CloudFront]
       |
  [API Gateway HTTP]
       |
  [Lambda Functions (VPCなし)]
       |          |          |
  [DynamoDB]  [S3 Bucket]  [SQS Queue]
                                |
                        [Lambda Worker (async)]
                                |
                      [DynamoDB (write result)]
```

### Key Characteristics

- Lambda functions placed outside VPC unless accessing VPC resources
- DynamoDB placed at Layer 4 even though it's serverless
- SQS→Lambda represented with dashed arrow (async)
- API Gateway sits at boundary between Layer 3 and external

---

## Pattern 3: ECS Microservices

### Component Layout

```
[ALB]
  |
  ├── /api/orders → [ECS: Order Service]  → [RDS PostgreSQL]
  |                        |
  |                   [SQS: order-events]
  |                        |
  ├── /api/users  → [ECS: User Service]   → [DynamoDB: users]
  |
  └── /api/notify → [ECS: Notification]   → [SES]
                          |
                        [SNS]
```

### Drawing Tips

- Use ECS Cluster as a container group around all ECS services
- Each microservice as a separate ECS Service icon
- Show service-to-database connections clearly
- Inter-service communication via SQS/SNS shown with dashed lines

---

## Pattern 4: Data Lake / Analytics

### Component Layout

```
[Data Sources]                     [Analytics]
  [RDS]  [App Logs]  [IoT]               |
     \        |        /          [Athena] [QuickSight]
      \       |       /                |
    [Kinesis Data Firehose]    [S3: Processed]
              |                        |
      [S3: Raw Data Lake]      [Glue ETL Jobs]
```

### Drawing Tips

- Left side = data sources, Right side = consumers
- S3 buckets with lifecycle labels (raw, processed, curated)
- Glue crawlers/jobs as Lambda-sized icons between S3 buckets
- Athena connected to S3 with dotted line (query, not move data)

---

## Pattern 5: Multi-AZ High Availability

### Key Principles

1. **Always show 2+ AZs** for production systems
2. **ALB and NLB span multiple AZs** — draw them spanning the AZ boundary or above the VPC
3. **RDS Multi-AZ** — primary in one AZ, standby in another, connected with "sync replication" arrow
4. **Auto Scaling Group** — show a single ASG icon with notation "min:2 max:10" rather than individual instances
5. **NAT Gateway** — one per AZ for HA (show two if multi-AZ NAT is required)

### ASG Representation

```xml
<!-- Use a single EC2 icon with ASG overlay and label -->
<mxCell id="asg-web" value="Auto Scaling Group&#xa;Web Tier&#xa;(min:2, max:10, t3.medium)"
  style="shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.auto_scaling2;
         labelBackgroundColor=none;sketch=0;fontStyle=0;fontSize=11;"
  vertex="1" parent="subnet-priv-1a">
  <mxGeometry x="130" y="110" width="60" height="60" as="geometry" />
</mxCell>
```

---

## Common Connection Patterns

### Synchronous request/response

```xml
style="edgeStyle=orthogonalEdgeStyle;rounded=0;exitX=1;exitY=0.5;entryX=0;entryY=0.5;"
```

### Event/async trigger (dashed)

```xml
style="edgeStyle=orthogonalEdgeStyle;rounded=0;dashed=1;dashPattern=8 4;"
```

### IAM permission (thin dotted, no arrow)

```xml
style="edgeStyle=orthogonalEdgeStyle;rounded=0;dashed=1;dashPattern=4 4;endArrow=none;strokeColor=#888888;"
```

### Replication (bidirectional)

```xml
style="edgeStyle=orthogonalEdgeStyle;rounded=0;endArrow=block;startArrow=block;startFill=1;endFill=1;"
```

### Data flow to S3/storage

```xml
style="edgeStyle=orthogonalEdgeStyle;rounded=0;exitX=0.5;exitY=1;entryX=0.5;entryY=0;"
```
