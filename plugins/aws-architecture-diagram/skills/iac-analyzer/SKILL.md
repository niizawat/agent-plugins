---
name: IaC Analyzer for AWS Architecture
description: This skill should be used when parsing IaC code to extract AWS resources and their relationships for diagram generation. Triggers on "CDKコードを解析して", "CloudFormationテンプレートからリソースを抽出", "Terraformコードの構造を理解", "IaCからAWSリソースを特定", or when the aws-architecture-diagram agent needs to identify AWS services, configurations, and connections from CDK TypeScript, CloudFormation YAML/JSON, or Terraform HCL code.
version: 0.1.0
---

# IaC Analyzer for AWS Architecture Diagrams

This skill provides procedures for extracting AWS resources, configurations, and relationships from IaC code to drive diagram generation.

## General Extraction Strategy

For any IaC format, extract:

1. **AWS Resources** — service type, logical name, key config (instance type, CIDR, etc.)
2. **Containment** — which resources are inside VPC/subnet/cluster
3. **Connections** — explicit references between resources (security group attachments, IAM roles, event sources)
4. **Network topology** — VPC CIDRs, subnet types, AZ placement

---

## CDK TypeScript Analysis

### File Discovery

Locate CDK files:

```text
Glob: **/*.ts (exclude node_modules, dist, .d.ts files)
Look for: import { ... } from 'aws-cdk-lib'
          import { ... } from '@aws-cdk/...'
          new Stack(...) or extends Stack
```

### Resource Identification Patterns

Match these TypeScript patterns to identify resources:

**VPC**:

```typescript
new ec2.Vpc(this, 'VpcName', {
  cidr: '10.0.0.0/16',           // → VPC CIDR
  maxAzs: 2,                      // → Number of AZs
  natGateways: 1,                 // → NAT Gateway count
  subnetConfiguration: [...]      // → Subnet types
})
```

**ECS Cluster + Service**:

```typescript
new ecs.Cluster(this, 'ClusterName', { vpc })
new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'ServiceName', {
  cluster,
  taskImageOptions: { image: ecs.ContainerImage.fromEcrRepository(repo) },
  desiredCount: 2,
  cpu: 256,
  memoryLimitMiB: 512,
})
```

→ Extract: ECS Cluster, ALB (internet-facing), Fargate Service, ECR repo, desired count

**Lambda**:

```typescript
new lambda.Function(this, 'FunctionName', {
  runtime: lambda.Runtime.NODEJS_20_X,
  handler: 'index.handler',
  code: lambda.Code.fromAsset('lambda'),
  environment: { TABLE_NAME: table.tableName }
})
```

→ Extract: Lambda function, runtime, environment references (DynamoDB table, etc.)

**RDS**:

```typescript
new rds.DatabaseInstance(this, 'DbName', {
  engine: rds.DatabaseInstanceEngine.mysql({ version: ... }),
  instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
  vpc,
  multiAz: true,
  vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED }
})
```

**DynamoDB**:

```typescript
new dynamodb.Table(this, 'TableName', {
  partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
  billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
})
```

**S3**:

```typescript
new s3.Bucket(this, 'BucketName', {
  versioned: true,
  encryption: s3.BucketEncryption.S3_MANAGED,
})
```

**API Gateway**:

```typescript
new apigw.RestApi(this, 'ApiName', { ... })
new apigw.HttpApi(this, 'HttpApiName', { ... })
```

### Relationship Extraction from CDK

**Method calls that imply connections**:

- `.addEventSource(new SqsEventSource(queue))` → Lambda ← SQS trigger
- `.grantRead(lambda)` / `.grantReadWrite(lambda)` → IAM permission (implied connection)
- `.addToRolePolicy(...)` → IAM association
- `taskDefinition.addContainer(...)` → ECS Task → Container relationship
- `.addTarget(new targets.LambdaFunction(fn))` → EventBridge/CloudWatch → Lambda

**Constructor parameter references**:

- If a resource is passed as a parameter to another constructor, they're connected
- Example: `{ vpc }` in RDS constructor → RDS is inside VPC

---

## CloudFormation YAML/JSON Analysis

### Resource Block Parsing

Every resource follows:

```yaml
Resources:
  LogicalResourceId:
    Type: AWS::Service::Resource
    Properties:
      PropertyName: Value
      Ref: OtherResourceId        # → direct reference/connection
      !GetAtt Resource.Attribute  # → attribute reference/connection
```

### Key Resource Types to Extract

| CF Type | Diagram Component |
| ------- | ----------------- |
| `AWS::EC2::VPC` | VPC container |
| `AWS::EC2::Subnet` | Subnet container (check Tags for public/private) |
| `AWS::EC2::InternetGateway` | IGW icon |
| `AWS::EC2::NatGateway` | NAT GW icon |
| `AWS::EC2::SecurityGroup` | SG annotation |
| `AWS::ElasticLoadBalancingV2::LoadBalancer` | ALB/NLB icon |
| `AWS::ECS::Cluster` | ECS Cluster container |
| `AWS::ECS::Service` | ECS Service icon |
| `AWS::Lambda::Function` | Lambda icon |
| `AWS::RDS::DBInstance` | RDS icon |
| `AWS::RDS::DBCluster` | Aurora cluster icon |
| `AWS::DynamoDB::Table` | DynamoDB icon |
| `AWS::S3::Bucket` | S3 icon |
| `AWS::ApiGateway::RestApi` | API GW icon |
| `AWS::ApiGatewayV2::Api` | API GW HTTP icon |
| `AWS::SQS::Queue` | SQS icon |
| `AWS::SNS::Topic` | SNS icon |
| `AWS::CloudFront::Distribution` | CloudFront icon |
| `AWS::Route53::HostedZone` | Route 53 icon |
| `AWS::CloudWatch::Alarm` | CloudWatch icon |
| `AWS::Logs::LogGroup` | CloudWatch Logs icon |

### Relationship Detection in CloudFormation

**Explicit references** (create diagram connections):

- `Ref: SubnetId` in EC2 instance → EC2 is in that subnet
- `Ref: SecurityGroupId` in EC2 instance → SG protects EC2
- `VpcId: !Ref MyVpc` → resource is in VPC
- `SubnetIds: - !Ref SubnetA` → resource spans those subnets
- `FunctionArn: !GetAtt MyFunction.Arn` in event source mapping → trigger connection

**Subnet type detection**:

- Check `MapPublicIpOnLaunch: true` → public subnet
- Check route table association: route to IGW → public; route to NAT GW → private
- Tags with `subnet-type: Public/Private` or `aws-cdk:subnet-type`

---

## Terraform HCL Analysis

### Resource Block Pattern

```hcl
resource "aws_resource_type" "logical_name" {
  argument = value
  argument2 = aws_other_resource.other_name.attribute  # → connection
}
```

### Key Resource Types

| TF Resource | Diagram Component |
| ----------- | ----------------- |
| `aws_vpc` | VPC container |
| `aws_subnet` | Subnet container (check `map_public_ip_on_launch`) |
| `aws_internet_gateway` | IGW |
| `aws_nat_gateway` | NAT GW |
| `aws_lb` | ALB/NLB (check `load_balancer_type`) |
| `aws_ecs_cluster` | ECS Cluster |
| `aws_ecs_service` | ECS Service |
| `aws_lambda_function` | Lambda |
| `aws_db_instance` | RDS |
| `aws_rds_cluster` | Aurora |
| `aws_dynamodb_table` | DynamoDB |
| `aws_s3_bucket` | S3 |
| `aws_api_gateway_rest_api` | API GW (REST) |
| `aws_apigatewayv2_api` | API GW (HTTP) |
| `aws_sqs_queue` | SQS |
| `aws_sns_topic` | SNS |
| `aws_cloudfront_distribution` | CloudFront |
| `aws_route53_zone` | Route 53 |

### Relationship Detection in Terraform

**Reference syntax** `resource_type.name.attribute` creates a connection:

```hcl
resource "aws_instance" "web" {
  subnet_id              = aws_subnet.public.id      # → in public subnet
  vpc_security_group_ids = [aws_security_group.web.id]  # → SG applied
}

resource "aws_lambda_event_source_mapping" "trigger" {
  event_source_arn = aws_sqs_queue.queue.arn  # → SQS triggers Lambda
  function_name    = aws_lambda_function.processor.arn
}
```

### Module Detection

When Terraform uses `module` blocks, look for the module source to identify what AWS resources it creates:

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"  # → Creates VPC, subnets, IGW, NAT GW
  version = "~> 5.0"
  cidr    = "10.0.0.0/16"
  azs     = ["ap-northeast-1a", "ap-northeast-1c"]
  public_subnets  = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets = ["10.0.11.0/24", "10.0.12.0/24"]
}
```

---

## Text Requirements Analysis

When input is plain text or markdown requirements, extract:

1. **Explicit service mentions**: Look for AWS service names (EC2, Lambda, RDS, S3, etc.)
2. **Flow descriptions**: "→", "through", "to", "from", "calls", "triggers" indicate connections
3. **Topology hints**: "public", "private", "VPC", "subnet", "multi-AZ", "region"
4. **Quantity hints**: "2 AZs", "3 instances", "Auto Scaling"

**Example extraction**:

> "ALBからECSのFargateサービスにトラフィックを転送し、ECSはRDS MySQLに接続する。フロントエンドはS3にホストし、CloudFrontで配信する"

→ Resources: ALB, ECS Fargate, RDS MySQL, S3, CloudFront
→ Connections: CloudFront→S3, CloudFront→ALB, ALB→ECS, ECS→RDS

---

## Additional Resources

For detailed parsing examples and edge cases, consult:

- **`references/cdk-typescript-patterns.md`** — Common CDK TypeScript patterns and their diagram mappings
- **`references/cloudformation-patterns.md`** — CloudFormation resource types, intrinsic functions, SAM extensions
- **`references/terraform-patterns.md`** — Terraform HCL resource types, module expansions, count/for_each handling
