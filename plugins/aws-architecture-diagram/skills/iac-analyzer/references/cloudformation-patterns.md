# CloudFormation Patterns → Diagram Mapping

## Template Structure Overview

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Description: "Stack description"
Parameters: { ... }   # Input parameters
Mappings: { ... }     # Static key-value mappings
Conditions: { ... }   # Conditional creation flags
Resources: { ... }    # AWS resources (required)
Outputs: { ... }      # Exported values
```

図の生成には主に `Resources` セクションを使用する。`Parameters` は設定値の補完に活用する。

---

## Resource Extraction Rules

### 1. VPC / ネットワーク系

#### `AWS::EC2::VPC`

```yaml
MyVpc:
  Type: AWS::EC2::VPC
  Properties:
    CidrBlock: 10.0.0.0/16
    EnableDnsSupport: true
    EnableDnsHostnames: true
    Tags:
      - Key: Name
        Value: MyVpc
```

→ VPC コンテナ（Layer 1）。`CidrBlock` をラベルに含める。

---

#### `AWS::EC2::Subnet`

```yaml
PublicSubnet1:
  Type: AWS::EC2::Subnet
  Properties:
    VpcId: !Ref MyVpc           # → このVPCに属する
    CidrBlock: 10.0.1.0/24
    AvailabilityZone: ap-northeast-1a
    MapPublicIpOnLaunch: true   # true → パブリックサブネット
    Tags:
      - Key: Name
        Value: Public Subnet 1a
```

**サブネット種別の判定**:
1. `MapPublicIpOnLaunch: true` → Public Subnet
2. `AWS::EC2::RouteTable` + `AWS::EC2::Route` でデフォルトルートが IGW → Public
3. デフォルトルートが NAT Gateway → Private
4. デフォルトルートなし → Isolated (DBサブネット)
5. Tag `subnet-type: public/private/isolated` があればそれに従う

---

#### `AWS::EC2::InternetGateway` + `AWS::EC2::VPCGatewayAttachment`

```yaml
IGW:
  Type: AWS::EC2::InternetGateway

IGWAttachment:
  Type: AWS::EC2::VPCGatewayAttachment
  Properties:
    VpcId: !Ref MyVpc
    InternetGatewayId: !Ref IGW
```

→ IGW アイコン（Layer 1）。`VPCGatewayAttachment` から VPC との接続を確認する。

---

#### `AWS::EC2::NatGateway`

```yaml
NatGateway1:
  Type: AWS::EC2::NatGateway
  Properties:
    AllocationId: !GetAtt EIP1.AllocationId
    SubnetId: !Ref PublicSubnet1   # → パブリックサブネットに配置
```

→ NAT Gateway アイコン（Layer 1）。`SubnetId` で配置サブネットを特定する。

---

### 2. コンピューティング系

#### `AWS::EC2::Instance`

```yaml
WebServer:
  Type: AWS::EC2::Instance
  Properties:
    InstanceType: t3.medium
    ImageId: !Ref LatestAmiId
    SubnetId: !Ref PrivateSubnet1
    SecurityGroupIds:
      - !Ref WebSG
    IamInstanceProfile: !Ref EC2Profile
    Tags:
      - Key: Name
        Value: WebServer
```

→ EC2 アイコン（Layer 3）。`SubnetId` で配置先サブネットを特定する。

---

#### `AWS::AutoScaling::AutoScalingGroup`

```yaml
WebASG:
  Type: AWS::AutoScaling::AutoScalingGroup
  Properties:
    VPCZoneIdentifier:
      - !Ref PrivateSubnet1
      - !Ref PrivateSubnet2
    LaunchTemplate:
      LaunchTemplateId: !Ref WebLT
      Version: !GetAtt WebLT.LatestVersionNumber
    MinSize: '2'
    MaxSize: '10'
    DesiredCapacity: '2'
    TargetGroupARNs:
      - !Ref WebTG         # → ALB と接続
```

→ Auto Scaling アイコン（Layer 3）。`VPCZoneIdentifier` で複数サブネットに跨る。
  ラベル: `Auto Scaling Group\nWeb Tier (min:2, max:10)`

---

#### `AWS::ECS::Cluster`

```yaml
ECSCluster:
  Type: AWS::ECS::Cluster
  Properties:
    ClusterName: MyCluster
    CapacityProviders:
      - FARGATE
      - FARGATE_SPOT
```

→ ECS Cluster コンテナグループ（Layer 3）。

---

#### `AWS::ECS::TaskDefinition`

```yaml
WebTaskDef:
  Type: AWS::ECS::TaskDefinition
  Properties:
    Family: web-task
    Cpu: '256'
    Memory: '512'
    NetworkMode: awsvpc
    RequiresCompatibilities:
      - FARGATE
    ContainerDefinitions:
      - Name: web
        Image: !Sub '${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/myapp:latest'
        PortMappings:
          - ContainerPort: 8080
        Environment:
          - Name: DB_HOST
            Value: !GetAtt DB.Endpoint.Address   # → RDS への接続を示唆
```

→ 単独アイコンとして描画せず、ECS Service のラベルに CPU/メモリを記載する。
  `Image` から ECR リポジトリへの接続を抽出する。
  `Environment` の `!GetAtt` / `!Ref` は接続関係として抽出する。

---

#### `AWS::ECS::Service`

```yaml
WebService:
  Type: AWS::ECS::Service
  Properties:
    Cluster: !Ref ECSCluster
    TaskDefinition: !Ref WebTaskDef
    DesiredCount: 2
    LaunchType: FARGATE
    NetworkConfiguration:
      AwsvpcConfiguration:
        Subnets:
          - !Ref PrivateSubnet1
          - !Ref PrivateSubnet2
        SecurityGroups:
          - !Ref EcsSG
    LoadBalancers:
      - ContainerName: web
        ContainerPort: 8080
        TargetGroupArn: !Ref WebTG   # → ALB と接続
```

→ ECS Service アイコン（Layer 3）。`DesiredCount` をラベルに含める。
  `Subnets` で配置サブネットを特定する。

---

#### `AWS::Lambda::Function`

```yaml
ProcessorFn:
  Type: AWS::Lambda::Function
  Properties:
    FunctionName: order-processor
    Runtime: nodejs20.x
    Handler: index.handler
    Code:
      S3Bucket: !Ref DeployBucket
      S3Key: lambda.zip
    Role: !GetAtt LambdaRole.Arn
    VpcConfig:                          # VPC内Lambda
      SubnetIds:
        - !Ref PrivateSubnet1
      SecurityGroupIds:
        - !Ref LambdaSG
    Environment:
      Variables:
        TABLE_NAME: !Ref OrdersTable    # → DynamoDB接続
        QUEUE_URL: !Ref OrderQueue      # → SQS接続
```

→ Lambda アイコン（Layer 3）。`VpcConfig` があればVPC内サブネットに配置する。
  `Environment.Variables` の `!Ref` / `!GetAtt` から接続先リソースを抽出する。

---

#### `AWS::Lambda::EventSourceMapping`

```yaml
SQSTrigger:
  Type: AWS::Lambda::EventSourceMapping
  Properties:
    EventSourceArn: !GetAtt OrderQueue.Arn   # SQS → Lambda のトリガー
    FunctionName: !GetAtt ProcessorFn.Arn
    BatchSize: 10
```

→ SQS -(破線矢印)→ Lambda のトリガー接続として描画する。

---

### 3. ロードバランサー系

#### `AWS::ElasticLoadBalancingV2::LoadBalancer`

```yaml
ALB:
  Type: AWS::ElasticLoadBalancingV2::LoadBalancer
  Properties:
    Name: my-alb
    Scheme: internet-facing        # internet-facing or internal
    Type: application              # application / network / gateway
    Subnets:
      - !Ref PublicSubnet1
      - !Ref PublicSubnet2
    SecurityGroups:
      - !Ref ALBSG
```

→ `Type: application` → ALB アイコン（Layer 3）
  `Type: network` → NLB アイコン（Layer 3）
  `Scheme: internet-facing` → ラベルに「(internet-facing)」を追加する。

---

#### `AWS::ElasticLoadBalancingV2::Listener` + `TargetGroup`

```yaml
HTTPSListener:
  Type: AWS::ElasticLoadBalancingV2::Listener
  Properties:
    LoadBalancerArn: !Ref ALB
    Port: 443
    Protocol: HTTPS
    DefaultActions:
      - Type: forward
        TargetGroupArn: !Ref WebTG

WebTG:
  Type: AWS::ElasticLoadBalancingV2::TargetGroup
  Properties:
    Port: 8080
    Protocol: HTTP
    VpcId: !Ref MyVpc
    TargetType: ip                   # ip → Fargate
```

→ Listener/TargetGroup は個別アイコンにせず、ALB → ECS の接続線ラベルに「HTTPS:443」として表示する。

---

### 4. API Gateway

#### `AWS::ApiGateway::RestApi` (v1)

```yaml
RestApi:
  Type: AWS::ApiGateway::RestApi
  Properties:
    Name: MyApi
    EndpointConfiguration:
      Types:
        - REGIONAL
```

→ API Gateway (REST) アイコン（Layer 3）。

`AWS::ApiGateway::Method` + `AWS::ApiGateway::Integration` から Lambda/HTTP の接続先を抽出する。

---

#### `AWS::ApiGatewayV2::Api` (v2 HTTP/WebSocket)

```yaml
HttpApi:
  Type: AWS::ApiGatewayV2::Api
  Properties:
    Name: MyHttpApi
    ProtocolType: HTTP             # HTTP or WEBSOCKET
```

→ API Gateway (HTTP) アイコン（Layer 3）。

---

### 5. データベース系

#### `AWS::RDS::DBInstance`

```yaml
Database:
  Type: AWS::RDS::DBInstance
  Properties:
    DBInstanceClass: db.t3.medium
    Engine: mysql
    EngineVersion: '8.0'
    MultiAZ: true                  # true → Multi-AZ 表示
    DBSubnetGroupName: !Ref DBSubnetGroup
    VPCSecurityGroups:
      - !Ref DBSG
    MasterUsername: admin
    ManageMasterUserPassword: true
```

→ RDS アイコン（Layer 4）。`MultiAZ: true` はラベルに「Multi-AZ」を追加する。

---

#### `AWS::RDS::DBCluster` (Aurora)

```yaml
AuroraCluster:
  Type: AWS::RDS::DBCluster
  Properties:
    Engine: aurora-mysql
    EngineVersion: '8.0.mysql_aurora.3.04.0'
    DBSubnetGroupName: !Ref DBSubnetGroup
    VpcSecurityGroupIds:
      - !Ref DBSG

AuroraInstance1:
  Type: AWS::RDS::DBInstance
  Properties:
    DBClusterIdentifier: !Ref AuroraCluster
    DBInstanceClass: db.t3.medium
    Engine: aurora-mysql
    PromotionTier: 0               # 0 → Writer, 1+ → Reader
```

→ `PromotionTier: 0` の DBInstance が Writer、それ以外が Reader。
  Aurora アイコン（Layer 4）にラベル「Aurora MySQL (1W+1R)」などと記載する。

---

#### `AWS::DynamoDB::Table`

```yaml
OrdersTable:
  Type: AWS::DynamoDB::Table
  Properties:
    TableName: Orders
    BillingMode: PAY_PER_REQUEST
    AttributeDefinitions:
      - AttributeName: orderId
        AttributeType: S
    KeySchema:
      - AttributeName: orderId
        KeyType: HASH
    StreamSpecification:
      StreamViewType: NEW_AND_OLD_IMAGES   # DynamoDB Streams有効
```

→ DynamoDB アイコン（Layer 4）。`StreamSpecification` があればストリーム出力を示す矢印を追加する。

---

#### `AWS::ElastiCache::ReplicationGroup`

```yaml
Cache:
  Type: AWS::ElastiCache::ReplicationGroup
  Properties:
    ReplicationGroupDescription: Redis cache
    CacheNodeType: cache.t3.medium
    Engine: redis
    NumCacheClusters: 2            # 2 → Multi-AZ
    CacheSubnetGroupName: !Ref CacheSubnetGroup
```

→ ElastiCache (Redis) アイコン（Layer 4）。

---

### 6. ストレージ / メッセージング

#### `AWS::S3::Bucket`

```yaml
AssetsBucket:
  Type: AWS::S3::Bucket
  Properties:
    BucketName: !Sub 'my-assets-${AWS::AccountId}'
    VersioningConfiguration:
      Status: Enabled
    NotificationConfiguration:
      LambdaConfigurations:
        - Event: s3:ObjectCreated:*
          Function: !GetAtt ProcessFn.Arn   # → S3 → Lambda イベント
```

→ S3 アイコン（Layer 4）。`NotificationConfiguration` から接続先を抽出する。

---

#### `AWS::SQS::Queue`

```yaml
OrderQueue:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: order-queue.fifo
    FifoQueue: true
    RedrivePolicy:
      deadLetterTargetArn: !GetAtt DLQ.Arn   # → DLQ接続
      maxReceiveCount: 3

DLQ:
  Type: AWS::SQS::Queue
  Properties:
    QueueName: order-dlq.fifo
    FifoQueue: true
```

→ SQS アイコン（Layer 4）。DLQ は別アイコンとして描画し「DLQ」ラベルで接続する。

---

#### `AWS::SNS::Topic`

```yaml
NotificationTopic:
  Type: AWS::SNS::Topic
  Properties:
    TopicName: notifications
    Subscription:
      - Protocol: sqs
        Endpoint: !GetAtt OrderQueue.Arn     # → SNS → SQS
      - Protocol: lambda
        Endpoint: !GetAtt NotifyFn.Arn       # → SNS → Lambda
```

→ SNS アイコン（Layer 4）。`Subscription` から接続先を破線矢印で描画する。

---

### 7. CDN / DNS

#### `AWS::CloudFront::Distribution`

```yaml
CDN:
  Type: AWS::CloudFront::Distribution
  Properties:
    DistributionConfig:
      Origins:
        - Id: S3Origin
          DomainName: !GetAtt AssetsBucket.RegionalDomainName
          S3OriginConfig: {}
        - Id: ALBOrigin
          DomainName: !GetAtt ALB.DNSName
          CustomOriginConfig:
            HTTPSPort: 443
            OriginProtocolPolicy: https-only
      DefaultCacheBehavior:
        TargetOriginId: ALBOrigin
        ViewerProtocolPolicy: redirect-to-https
      WebACLId: !GetAtt WAF.Arn        # → WAF接続
```

→ CloudFront アイコン（Layer 3、VPC外）。
  `Origins` から接続先（S3, ALB）を抽出する。`WebACLId` から WAF との接続を抽出する。

---

#### `AWS::Route53::HostedZone` / `AWS::Route53::RecordSet`

```yaml
HostedZone:
  Type: AWS::Route53::HostedZone
  Properties:
    Name: example.com

DnsRecord:
  Type: AWS::Route53::RecordSet
  Properties:
    HostedZoneId: !Ref HostedZone
    Name: app.example.com
    Type: A
    AliasTarget:
      DNSName: !GetAtt ALB.DNSName    # → Route 53 → ALB
      HostedZoneId: !GetAtt ALB.CanonicalHostedZoneID
```

→ Route 53 アイコン（Layer 3、VPC外）。`AliasTarget` から接続先を抽出する。

---

### 8. セキュリティ系

#### `AWS::WAFv2::WebACL`

```yaml
WAF:
  Type: AWS::WAFv2::WebACL
  Properties:
    Name: MyWAF
    Scope: REGIONAL                # REGIONAL or CLOUDFRONT
    DefaultAction:
      Allow: {}
```

→ WAF アイコン（Layer 2）。`Scope: CLOUDFRONT` の場合は CloudFront に接続する。

---

### 9. 監視系

#### `AWS::CloudWatch::Alarm`

```yaml
HighCPUAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: HighCPU
    MetricName: CPUUtilization
    Namespace: AWS/EC2
    Dimensions:
      - Name: AutoScalingGroupName
        Value: !Ref WebASG
    AlarmActions:
      - !Ref ScalingPolicy         # → Auto Scaling Policy と接続
```

→ CloudWatch アイコン（Layer 5）。複数の Alarm は1つの CloudWatch アイコンにまとめてよい。

---

## Intrinsic Functions の処理

CloudFormation の組み込み関数から接続関係を抽出する:

| 関数 | 接続関係の解釈 |
|------|---------------|
| `!Ref ResourceName` | `ResourceName` への参照（多くの場合ID/ARN） |
| `!GetAtt Resource.Attribute` | `Resource` の属性値を参照 → 接続関係あり |
| `!Sub '${Resource.Attribute}'` | 文字列内の `${Resource}` / `${Resource.Attr}` を抽出 |
| `!Select [0, !GetAZs '']` | AZ指定（接続ではなく配置先情報） |
| `!If [Condition, A, B]` | 条件付きリソース → 両方を図に含め「(条件付き)」と注記 |

---

## Parameters からの情報補完

`!Ref ParameterName` で参照されるパラメータは、`Default` 値を使って値を補完する:

```yaml
Parameters:
  InstanceType:
    Type: String
    Default: t3.medium    # ← ラベルに使用
  Environment:
    Type: String
    Default: production
```

---

## Nested Stacks

```yaml
NetworkStack:
  Type: AWS::CloudFormation::Stack
  Properties:
    TemplateURL: https://s3.amazonaws.com/bucket/network.yaml
    Parameters:
      VpcCidr: 10.0.0.0/16
```

→ ネストされたスタックは、参照先テンプレートも読み込んで同一図に含める。
  ファイルパスが指定されている場合は `Read` ツールで読み込む。

---

## SAM (Serverless Application Model) 拡張

SAM テンプレートは `Transform: AWS::Serverless-2016-10-31` を持つ CloudFormation テンプレート。
追加のリソースタイプ:

| SAM Type | 展開されるリソース |
|----------|------------------|
| `AWS::Serverless::Function` | Lambda + IAM Role + Event Source Mappings |
| `AWS::Serverless::Api` | API Gateway REST API + Deployment + Stage |
| `AWS::Serverless::HttpApi` | API Gateway HTTP API |
| `AWS::Serverless::SimpleTable` | DynamoDB Table (シンプル構成) |
| `AWS::Serverless::StateMachine` | Step Functions State Machine |

```yaml
Transform: AWS::Serverless-2016-10-31
Resources:
  OrderFunction:
    Type: AWS::Serverless::Function
    Properties:
      Handler: index.handler
      Runtime: nodejs20.x
      Events:
        ApiEvent:
          Type: Api                      # → API Gateway → Lambda
          Properties:
            Path: /orders
            Method: POST
        SQSEvent:
          Type: SQS                      # → SQS → Lambda (トリガー)
          Properties:
            Queue: !GetAtt OrderQueue.Arn
```
