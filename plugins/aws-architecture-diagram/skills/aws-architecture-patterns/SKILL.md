---
name: AWS Architecture Patterns for DrawIO
description: This skill should be used when designing AWS architecture diagrams, determining component grouping and arrangement, identifying "一般的なAWSアーキテクチャパターン", "Webアプリの構成図", "サーバーレス構成", "マイクロサービス構成", "3層アーキテクチャ", or when the aws-architecture-diagram agent needs guidance on how to structure and arrange AWS components in a diagram.
version: 0.1.0
---

# AWS Architecture Patterns for DrawIO Diagrams

This skill provides guidance on structuring common AWS architecture patterns into well-organized DrawIO diagrams. Use these patterns as starting templates and adapt them based on the actual IaC code or requirements.

## Core Diagramming Principles

### Spatial Organization Rules

**Horizontal axis**: Represents traffic/data flow direction (left = external/ingress, right = internal/backend)
**Vertical axis**: Represents layers (top = presentation, bottom = data/infrastructure)
**Containment**: Physical/logical boundaries use enclosing containers (VPC > AZ > Subnet)

### Visual Hierarchy

1. **Account/Region** (outermost container) → Layer 0
2. **VPC** (network boundary) → Layer 1
3. **Availability Zones** (physical separation) → Layer 1, inside VPC
4. **Subnets** (routing boundary) → Layer 1, inside AZ
5. **Resources** (services) → Layers 2-5, inside subnets

---

## Pattern 1: Standard 3-Tier Web Application

**Use when**: Web applications with frontend, application, and database tiers.

**Component layout** (left to right, top to bottom):
```
[Internet/Users] → [Route 53] → [CloudFront] → [WAF] → [ALB]
                                                          ↓
[Public Subnet]:  NAT GW    ALB
[Private Subnet]: ECS/EC2 App Tier    RDS (Primary)
[Private Subnet]: RDS (Standby/Multi-AZ)
```

**Layer assignments**:
- Route 53, CloudFront, WAF → Layer 2 (セキュリティ) or Layer 3 (アプリケーション)
- ALB → Layer 3
- ECS/EC2 → Layer 3
- RDS, ElastiCache → Layer 4
- NAT Gateway, IGW → Layer 1
- CloudWatch → Layer 5

**Key groups**:
- Wrap RDS primary + standby in an "RDS Multi-AZ" label group
- Place ALB outside (or spanning) AZs to show it's regional

---

## Pattern 2: Serverless (Lambda + API Gateway)

**Use when**: Event-driven or API-backed serverless architectures.

**Component layout**:
```
[Users] → [CloudFront] → [API Gateway] → [Lambda Functions]
                                                ↓
                                    [DynamoDB] [S3] [SQS]
                                         ↓
                                    [Lambda (async)]
```

**Layer assignments**:
- API Gateway → Layer 3
- Lambda → Layer 3
- DynamoDB, S3 → Layer 4
- SQS, SNS, EventBridge → Layer 3 (messaging) or Layer 4 (data)
- CloudWatch, X-Ray → Layer 5

**Key patterns**:
- Lambda functions grouped by domain (e.g., "Order Service Lambdas")
- Show SQS/SNS connections with dashed lines (async)
- EventBridge rules as a central event router if present

---

## Pattern 3: Container-Based Microservices (ECS/EKS)

**Use when**: Containerized microservices architecture.

**Component layout**:
```
[ALB] → [ECS Service A] → [RDS-A]
      ↘ [ECS Service B] → [DynamoDB-B]
      ↘ [ECS Service C] → [ElastiCache]
```

**ECS representation**:
- ECS Cluster as a container group
- Each ECS Service as a resource icon inside the cluster
- ECS Task Definition shown as annotation (not a separate box)
- ECR as a separate icon connected to ECS with a "pulls from" arrow

**EKS representation**:
- EKS Cluster as container
- Node Groups inside (labeled with instance type)
- Services/Pods represented at service level (not individual pods)

---

## Pattern 4: Data Pipeline / Analytics

**Use when**: Data ingestion, processing, and analytics workloads.

**Component layout** (left to right = data flow):
```
[Data Sources] → [Kinesis/SQS] → [Lambda/Glue] → [S3 Data Lake]
                                                        ↓
                                              [Athena/Redshift]
                                                        ↓
                                              [QuickSight/BI Tool]
```

**Layer assignments**:
- Kinesis, SQS → Layer 3 (streaming) or Layer 4
- Lambda (ETL), Glue → Layer 3
- S3, Redshift → Layer 4
- Athena → Layer 3 (query) or Layer 4 (data)

---

## Pattern 5: Multi-Account / Multi-Region

**Use when**: Enterprise architectures spanning multiple AWS accounts.

**Layout approach**:
- Draw each account as a separate Account container
- Use a central "Transit Gateway" or "VPC Peering" arrow between VPCs
- Place shared services account (SSO, Security Hub) on the side
- Use dashed lines for cross-account connections

---

## Standard Component Groups

### VPC with Public/Private Subnets (Standard Pattern)

Always organize subnets by:
1. **Public Subnets** (left or top): Contain ALB, NAT Gateway, Bastion Host
2. **Private Subnets** (middle): Contain application tier (ECS, EC2, Lambda in VPC)
3. **Isolated/DB Subnets** (right or bottom): Contain RDS, ElastiCache

Replicate per Availability Zone (minimum 2 AZs for production):
```
AZ: ap-northeast-1a          AZ: ap-northeast-1c
  [Public Subnet 10.0.1.0/24]  [Public Subnet 10.0.2.0/24]
  [Private Subnet 10.0.11.0/24] [Private Subnet 10.0.12.0/24]
  [DB Subnet 10.0.21.0/24]     [DB Subnet 10.0.22.0/24]
```

### Security Group Representation

Do NOT draw Security Groups as containers (too cluttered). Instead:
- Show Security Groups as labels/annotations on the resource they protect
- Example: EC2 label: `Web Server\n(EC2 t3.medium)\nSG: sg-web`
- For WAF/Shield: draw as a separate icon in Layer 2 with arrows showing protection scope

### IAM Roles/Policies

Represent IAM as:
- A small IAM icon near the resource it's attached to
- Connected with a thin dashed line labeled "assumes" or "uses"
- Group multiple IAM roles in a corner "IAM" section if there are many

---

## Layout Anti-Patterns to Avoid

❌ **Do not** place resources from different layers in the same subnet container
❌ **Do not** draw individual EC2 instances for Auto Scaling Groups — use a single ASG icon with a note "2-10 instances"
❌ **Do not** show every Security Group rule as an arrow (show only primary traffic flows)
❌ **Do not** make VPC containers too small — always leave 40px padding around child elements
❌ **Do not** use diagonal lines — always use orthogonal routing

---

## Additional Resources

For detailed pattern examples and component arrangements, consult:

- **`references/patterns.md`** — Complete pattern diagrams with exact coordinates and XML snippets
