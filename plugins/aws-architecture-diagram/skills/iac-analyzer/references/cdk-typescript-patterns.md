# CDK TypeScript Patterns → Diagram Mapping

## Common CDK Construct Mappings

### High-Level Constructs (L3)

These constructs create multiple AWS resources at once. Extract all underlying resources.

#### `ApplicationLoadBalancedFargateService`

```typescript
new ecs_patterns.ApplicationLoadBalancedFargateService(this, 'Service', {
  cluster,
  taskImageOptions: {
    image: ecs.ContainerImage.fromEcrRepository(repo, 'latest'),
    containerPort: 8080,
    environment: { DB_HOST: db.dbInstanceEndpointAddress }
  },
  desiredCount: 2,
  cpu: 256,
  memoryLimitMiB: 512,
  publicLoadBalancer: true,  // → internet-facing ALB
})
```

**Creates**:
- ALB (internet-facing if publicLoadBalancer: true)
- ECS Fargate Service (with desired count)
- ECS Task Definition (cpu/memory)
- Target Group (linked ALB → ECS)
- Security Group for ALB
- Security Group for ECS tasks
- IAM Task Role + Execution Role

**Connections**: ALB → ECS Service → ECR (image pull), ECS → DB (from environment)

---

#### `ApplicationLoadBalancedEc2Service`

Similar to above but uses EC2 launch type instead of Fargate.

**Creates**: ALB + EC2 Auto Scaling Group + ECS Cluster + EC2 Launch Configuration

---

#### `QueueProcessingFargateService`

```typescript
new ecs_patterns.QueueProcessingFargateService(this, 'Worker', {
  cluster,
  image: ecs.ContainerImage.fromEcrRepository(repo),
  queue: myQueue,  // → SQS trigger
  maxScalingCapacity: 10,
})
```

**Creates**: SQS Queue → ECS Fargate Service (auto-scaling based on queue depth)
**Connection**: SQS -(trigger)→ ECS Worker

---

### Network Constructs

#### `ec2.Vpc`

```typescript
const vpc = new ec2.Vpc(this, 'AppVpc', {
  cidr: '10.0.0.0/16',
  maxAzs: 2,
  natGateways: 1,
  subnetConfiguration: [
    { name: 'Public', subnetType: ec2.SubnetType.PUBLIC, cidrMask: 24 },
    { name: 'Private', subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS, cidrMask: 24 },
    { name: 'Isolated', subnetType: ec2.SubnetType.PRIVATE_ISOLATED, cidrMask: 24 },
  ]
})
```

**Creates**:
- VPC with CIDR 10.0.0.0/16
- Public subnets: 2 (one per AZ), with IGW route
- Private subnets: 2 (one per AZ), with NAT GW route
- Isolated subnets: 2 (one per AZ), no internet route
- Internet Gateway (attached to VPC)
- NAT Gateway(s): `natGateways` count (placed in public subnet)
- Route Tables for each subnet type

---

### Lambda Constructs

#### `lambda.Function` with Event Sources

```typescript
const fn = new lambda.Function(this, 'Handler', {
  runtime: lambda.Runtime.NODEJS_20_X,
  handler: 'index.handler',
  code: lambda.Code.fromAsset('src'),
  vpc,  // → Lambda is in VPC (private subnet)
  vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS },
  environment: {
    TABLE_NAME: table.tableName,
    QUEUE_URL: queue.queueUrl,
  }
})

// Event source → SQS trigger Lambda
fn.addEventSource(new lambdaEventSources.SqsEventSource(queue, {
  batchSize: 10,
}))
```

**Creates**: Lambda function in VPC private subnet
**Connections**:
- SQS Queue -(trigger)→ Lambda
- Lambda → DynamoDB Table (from TABLE_NAME env)
- Lambda → SQS Queue (from QUEUE_URL env, for sending messages)

---

#### `NodejsFunction` / `PythonFunction`

Specialized Lambda constructs — same diagram representation as `lambda.Function`.

---

### API Gateway Constructs

#### `apigw.RestApi`

```typescript
const api = new apigw.RestApi(this, 'Api', {
  defaultCorsPreflightOptions: { allowOrigins: apigw.Cors.ALL_ORIGINS }
})
const users = api.root.addResource('users')
users.addMethod('GET', new apigw.LambdaIntegration(getUserFn))
users.addMethod('POST', new apigw.LambdaIntegration(createUserFn))
```

**Creates**: API Gateway REST API
**Connections**: API GW → Lambda functions (one connection per addMethod with LambdaIntegration)

#### `apigw2.HttpApi`

```typescript
const httpApi = new apigw2.HttpApi(this, 'HttpApi')
httpApi.addRoutes({
  path: '/items',
  methods: [HttpMethod.GET],
  integration: new HttpLambdaIntegration('GetItems', getItemsFn),
})
```

**Creates**: API Gateway HTTP API (v2)
**Connections**: API GW HTTP → Lambda

---

### Database Constructs

#### `rds.DatabaseInstance`

```typescript
const db = new rds.DatabaseInstance(this, 'Database', {
  engine: rds.DatabaseInstanceEngine.mysql({
    version: rds.MysqlEngineVersion.VER_8_0
  }),
  instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM),
  vpc,
  vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
  multiAz: true,
  deletionProtection: true,
  credentials: rds.Credentials.fromGeneratedSecret('admin'),
})
```

**Creates**: RDS MySQL (Multi-AZ if multiAz: true)
**Network**: Isolated subnet in VPC

#### `rds.DatabaseCluster` (Aurora)

```typescript
const cluster = new rds.DatabaseCluster(this, 'AuroraCluster', {
  engine: rds.DatabaseClusterEngine.auroraMysql({
    version: rds.AuroraMysqlEngineVersion.VER_3_04_0
  }),
  writer: rds.ClusterInstance.provisioned('writer', {
    instanceType: ec2.InstanceType.of(ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM)
  }),
  readers: [rds.ClusterInstance.provisioned('reader1')],
  vpc,
  vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
})
```

**Creates**: Aurora MySQL Cluster (writer + reader instances)
**Diagram**: Show as Aurora icon with "1 Writer + 1 Reader" label

---

### Storage / Messaging

#### `s3.Bucket` with Notifications

```typescript
const bucket = new s3.Bucket(this, 'DataBucket', {
  versioned: true,
  encryption: s3.BucketEncryption.S3_MANAGED,
})
bucket.addEventNotification(
  s3.EventType.OBJECT_CREATED,
  new s3n.LambdaDestination(processFn)
)
```

**Connection**: S3 -(event notification)→ Lambda (dashed line)

#### `sqs.Queue` with DeadLetterQueue

```typescript
const dlq = new sqs.Queue(this, 'DLQ')
const queue = new sqs.Queue(this, 'MainQueue', {
  deadLetterQueue: { queue: dlq, maxReceiveCount: 3 }
})
```

**Creates**: Two SQS queues — show DLQ connected to main queue with "DLQ" label

---

## Relationship Detection Priority

When extracting relationships from CDK code, check in this order:

1. **Constructor parameters** — resources passed directly imply containment or connection
2. **`.addEventSource()`** — creates trigger relationship
3. **`.grantRead()` / `.grantReadWrite()`** — implies the resource is accessed
4. **`.addToRolePolicy()`** — IAM permission implies access
5. **Environment variables** — variable names containing `TABLE_NAME`, `QUEUE_URL`, `BUCKET_NAME`, etc. imply the Lambda reads/writes that resource
6. **VPC subnets** — `vpcSubnets: { subnetType }` determines which subnet layer the resource is in

---

## CDK Stack Organization

### Single Stack

All resources are in one `Stack` class. Treat as a single diagram.

### Multiple Stacks with Cross-Stack References

```typescript
// Stack A
export class NetworkStack extends Stack {
  public readonly vpc: ec2.Vpc
}

// Stack B
export class AppStack extends Stack {
  constructor(..., { vpc }: { vpc: ec2.Vpc }) {
    // Uses vpc from NetworkStack
  }
}
```

**Diagram approach**: Show all stacks in one diagram. Use stack labels as annotations (not containers). The actual AWS Account/VPC boundaries are more meaningful.

### CDK App with Environments

```typescript
new AppStack(app, 'ProdStack', {
  env: { account: '123456789', region: 'ap-northeast-1' }
})
```

Extract region to label the Region container correctly.
