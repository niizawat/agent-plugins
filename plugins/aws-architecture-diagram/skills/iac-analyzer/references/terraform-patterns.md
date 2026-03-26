# Terraform HCL Patterns → Diagram Mapping

## HCL 基本構文

```hcl
# リソース定義
resource "aws_resource_type" "logical_name" {
  argument = value
  nested_block {
    argument = value
  }
}

# 他リソースへの参照（接続関係として抽出）
resource "aws_instance" "web" {
  subnet_id = aws_subnet.public.id              # → public subnet に配置
  vpc_security_group_ids = [aws_security_group.web.id]  # → SG適用
}

# 変数
variable "instance_type" {
  default = "t3.medium"
}

# ローカル値
locals {
  common_tags = { Environment = "production" }
}

# データソース（既存リソースの参照、新規リソースではない）
data "aws_ami" "amazon_linux" { ... }
```

---

## ネットワーク系

### `aws_vpc`

```hcl
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true

  tags = {
    Name = "main-vpc"
  }
}
```

→ VPC コンテナ（Layer 1）。`cidr_block` をラベルに含める。

---

### `aws_subnet`

```hcl
resource "aws_subnet" "public_1a" {
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "ap-northeast-1a"
  map_public_ip_on_launch = true              # true → パブリックサブネット

  tags = { Name = "public-1a" }
}

resource "aws_subnet" "private_1a" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = "ap-northeast-1a"
  # map_public_ip_on_launch デフォルト false → プライベート

  tags = { Name = "private-1a" }
}
```

**サブネット種別判定**:
1. `map_public_ip_on_launch = true` → Public Subnet
2. `aws_route_table` の `route` ブロックで `gateway_id = aws_internet_gateway.xxx.id` → Public
3. `route` で `nat_gateway_id` → Private
4. ルートなし → Isolated

---

### `aws_internet_gateway`

```hcl
resource "aws_internet_gateway" "igw" {
  vpc_id = aws_vpc.main.id
  tags = { Name = "main-igw" }
}
```

→ IGW アイコン（Layer 1）。`vpc_id` の参照で VPC との接続を確認する。

---

### `aws_nat_gateway`

```hcl
resource "aws_eip" "nat_1a" {
  domain = "vpc"
}

resource "aws_nat_gateway" "nat_1a" {
  allocation_id = aws_eip.nat_1a.id
  subnet_id     = aws_subnet.public_1a.id    # → パブリックサブネットに配置

  tags = { Name = "nat-1a" }
}
```

→ NAT Gateway アイコン（Layer 1）。`subnet_id` で配置サブネットを特定する。

---

### `aws_route_table` + `aws_route_table_association`

```hcl
resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.nat_1a.id   # → このRTはプライベート用
  }
}

resource "aws_route_table_association" "private_1a" {
  subnet_id      = aws_subnet.private_1a.id
  route_table_id = aws_route_table.private.id
}
```

→ ルートテーブル自体はアイコンにしない。`route` の `nat_gateway_id` / `gateway_id` からサブネット種別を判定するために使用する。

---

## コンピューティング系

### `aws_instance`

```hcl
resource "aws_instance" "web" {
  ami           = data.aws_ami.amazon_linux.id
  instance_type = "t3.medium"
  subnet_id     = aws_subnet.private_1a.id       # → プライベートサブネットに配置
  vpc_security_group_ids = [aws_security_group.web_sg.id]
  iam_instance_profile   = aws_iam_instance_profile.web.name

  tags = { Name = "web-server" }
}
```

→ EC2 アイコン（Layer 3）。`subnet_id` で配置サブネットを特定する。

---

### `aws_autoscaling_group`

```hcl
resource "aws_autoscaling_group" "web" {
  vpc_zone_identifier = [
    aws_subnet.private_1a.id,
    aws_subnet.private_1c.id
  ]
  min_size         = 2
  max_size         = 10
  desired_capacity = 2

  launch_template {
    id      = aws_launch_template.web.id
    version = "$Latest"
  }

  target_group_arns = [aws_lb_target_group.web.arn]   # → ALB 接続
}
```

→ Auto Scaling アイコン（Layer 3）。`min_size`/`max_size` をラベルに含める。
  `target_group_arns` から ALB との接続を抽出する。

---

### `aws_ecs_cluster`

```hcl
resource "aws_ecs_cluster" "main" {
  name = "main-cluster"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}
```

→ ECS Cluster コンテナグループ（Layer 3）。

---

### `aws_ecs_task_definition`

```hcl
resource "aws_ecs_task_definition" "web" {
  family                   = "web"
  cpu                      = "256"
  memory                   = "512"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  task_role_arn            = aws_iam_role.ecs_task.arn

  container_definitions = jsonencode([{
    name  = "web"
    image = "${aws_ecr_repository.app.repository_url}:latest"  # → ECR 参照
    portMappings = [{ containerPort = 8080 }]
    environment = [
      { name = "DB_HOST", value = aws_db_instance.main.endpoint }   # → RDS 参照
      { name = "REDIS_URL", value = aws_elasticache_replication_group.main.primary_endpoint_address }
    ]
  }])
}
```

→ 単独アイコンにせず、ECS Service ラベルに `cpu`/`memory` を含める。
  `container_definitions` の `environment` から `aws_*` 参照を接続として抽出する。

---

### `aws_ecs_service`

```hcl
resource "aws_ecs_service" "web" {
  name            = "web-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.web.arn
  desired_count   = 2
  launch_type     = "FARGATE"

  network_configuration {
    subnets         = [aws_subnet.private_1a.id, aws_subnet.private_1c.id]
    security_groups = [aws_security_group.ecs_sg.id]
  }

  load_balancer {
    target_group_arn = aws_lb_target_group.web.arn   # → ALB 接続
    container_name   = "web"
    container_port   = 8080
  }
}
```

→ ECS Service アイコン（Layer 3）。`network_configuration.subnets` で配置サブネットを特定する。

---

### `aws_lambda_function`

```hcl
resource "aws_lambda_function" "processor" {
  function_name = "order-processor"
  runtime       = "nodejs20.x"
  handler       = "index.handler"
  role          = aws_iam_role.lambda_role.arn
  filename      = "lambda.zip"

  vpc_config {                                    # VPC 内 Lambda
    subnet_ids         = [aws_subnet.private_1a.id]
    security_group_ids = [aws_security_group.lambda_sg.id]
  }

  environment {
    variables = {
      TABLE_NAME = aws_dynamodb_table.orders.name   # → DynamoDB 接続
      QUEUE_URL  = aws_sqs_queue.orders.id          # → SQS 接続
    }
  }
}
```

→ Lambda アイコン（Layer 3）。`vpc_config` があればVPC内サブネットに配置する。
  `environment.variables` の `aws_*` 参照から接続先を抽出する。

---

### `aws_lambda_event_source_mapping`

```hcl
resource "aws_lambda_event_source_mapping" "sqs_trigger" {
  event_source_arn = aws_sqs_queue.orders.arn     # SQS → Lambda
  function_name    = aws_lambda_function.processor.arn
  batch_size       = 10
}
```

→ SQS -(破線矢印)→ Lambda のトリガー接続として描画する。

---

## ロードバランサー系

### `aws_lb` (ALB/NLB)

```hcl
resource "aws_lb" "main" {
  name               = "main-alb"
  internal           = false           # false → internet-facing
  load_balancer_type = "application"   # application / network / gateway

  subnets = [
    aws_subnet.public_1a.id,
    aws_subnet.public_1c.id
  ]

  security_groups = [aws_security_group.alb_sg.id]
}
```

→ `load_balancer_type = "application"` → ALB アイコン（Layer 3）。
  `internal = false` → ラベルに「(internet-facing)」を追加する。

---

### `aws_lb_listener` + `aws_lb_target_group`

```hcl
resource "aws_lb_listener" "https" {
  load_balancer_arn = aws_lb.main.arn
  port              = 443
  protocol          = "HTTPS"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.web.arn   # → TG → ECS/EC2
  }
}

resource "aws_lb_target_group" "web" {
  port        = 8080
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"                  # ip → Fargate, instance → EC2
}
```

→ Listener/TG は個別アイコンにしない。ALB → ECS の接続線ラベルに「HTTPS:443」と記載する。

---

## API Gateway

### `aws_api_gateway_rest_api`

```hcl
resource "aws_api_gateway_rest_api" "main" {
  name = "MyApi"
  endpoint_configuration {
    types = ["REGIONAL"]
  }
}
```

→ API Gateway (REST) アイコン（Layer 3）。

`aws_api_gateway_integration` の `uri` から Lambda/HTTP エンドポイントへの接続を抽出する:
```hcl
resource "aws_api_gateway_integration" "lambda" {
  uri = aws_lambda_function.handler.invoke_arn   # → Lambda 接続
  integration_http_method = "POST"
  type = "AWS_PROXY"
}
```

---

### `aws_apigatewayv2_api`

```hcl
resource "aws_apigatewayv2_api" "http" {
  name          = "MyHttpApi"
  protocol_type = "HTTP"              # HTTP or WEBSOCKET
}

resource "aws_apigatewayv2_integration" "lambda" {
  api_id             = aws_apigatewayv2_api.http.id
  integration_type   = "AWS_PROXY"
  integration_uri    = aws_lambda_function.handler.invoke_arn   # → Lambda
}
```

→ API Gateway (HTTP) アイコン（Layer 3）。

---

## データベース系

### `aws_db_instance` (RDS)

```hcl
resource "aws_db_instance" "main" {
  identifier        = "main-db"
  engine            = "mysql"
  engine_version    = "8.0"
  instance_class    = "db.t3.medium"
  multi_az          = true                # true → Multi-AZ 表示
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
  username          = "admin"
  manage_master_user_password = true
}
```

→ RDS アイコン（Layer 4）。`multi_az = true` はラベルに「(Multi-AZ)」を追加する。

---

### `aws_rds_cluster` (Aurora)

```hcl
resource "aws_rds_cluster" "aurora" {
  cluster_identifier  = "aurora-cluster"
  engine              = "aurora-mysql"
  engine_version      = "8.0.mysql_aurora.3.04.0"
  db_subnet_group_name = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db_sg.id]
}

resource "aws_rds_cluster_instance" "writer" {
  identifier         = "aurora-writer"
  cluster_identifier = aws_rds_cluster.aurora.id
  instance_class     = "db.t3.medium"
  engine             = aws_rds_cluster.aurora.engine
  # promotion_tier デフォルト 0 → Writer
}

resource "aws_rds_cluster_instance" "reader" {
  identifier         = "aurora-reader-1"
  cluster_identifier = aws_rds_cluster.aurora.id
  instance_class     = "db.t3.medium"
  engine             = aws_rds_cluster.aurora.engine
  promotion_tier     = 1              # 1+ → Reader
}
```

→ Aurora アイコン（Layer 4）。`aws_rds_cluster_instance` の `promotion_tier` で Writer/Reader を判定する。
  ラベル例: `Aurora MySQL\n(1 Writer + 1 Reader)`

---

### `aws_dynamodb_table`

```hcl
resource "aws_dynamodb_table" "orders" {
  name         = "Orders"
  billing_mode = "PAY_PER_REQUEST"
  hash_key     = "orderId"

  attribute {
    name = "orderId"
    type = "S"
  }

  stream_enabled   = true                          # DynamoDB Streams 有効
  stream_view_type = "NEW_AND_OLD_IMAGES"
}
```

→ DynamoDB アイコン（Layer 4）。`stream_enabled = true` があればストリーム出力の矢印を追加する。

---

### `aws_elasticache_replication_group`

```hcl
resource "aws_elasticache_replication_group" "redis" {
  replication_group_id = "redis-cluster"
  description          = "Redis cache"
  node_type            = "cache.t3.medium"
  num_cache_clusters   = 2                # 2 → Multi-AZ
  subnet_group_name    = aws_elasticache_subnet_group.main.name
  security_group_ids   = [aws_security_group.cache_sg.id]
}
```

→ ElastiCache (Redis) アイコン（Layer 4）。

---

## ストレージ / メッセージング

### `aws_s3_bucket` + `aws_s3_bucket_notification`

```hcl
resource "aws_s3_bucket" "data" {
  bucket = "my-data-bucket"
}

resource "aws_s3_bucket_notification" "trigger" {
  bucket = aws_s3_bucket.data.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.processor.arn   # → S3 → Lambda
    events              = ["s3:ObjectCreated:*"]
  }
}
```

→ S3 アイコン（Layer 4）。`aws_s3_bucket_notification` から Lambda への接続を抽出する。

---

### `aws_sqs_queue`

```hcl
resource "aws_sqs_queue" "main" {
  name                        = "main-queue.fifo"
  fifo_queue                  = true
  content_based_deduplication = true
  redrive_policy = jsonencode({
    deadLetterTargetArn = aws_sqs_queue.dlq.arn   # → DLQ 接続
    maxReceiveCount     = 3
  })
}

resource "aws_sqs_queue" "dlq" {
  name = "main-dlq.fifo"
  fifo_queue = true
}
```

→ SQS アイコン（Layer 4）。DLQ は別アイコンとして「DLQ」ラベルで接続する。

---

### `aws_sns_topic` + `aws_sns_topic_subscription`

```hcl
resource "aws_sns_topic" "notifications" {
  name = "notifications"
}

resource "aws_sns_topic_subscription" "to_sqs" {
  topic_arn = aws_sns_topic.notifications.arn
  protocol  = "sqs"
  endpoint  = aws_sqs_queue.main.arn          # → SNS → SQS
}

resource "aws_sns_topic_subscription" "to_lambda" {
  topic_arn = aws_sns_topic.notifications.arn
  protocol  = "lambda"
  endpoint  = aws_lambda_function.notify.arn  # → SNS → Lambda
}
```

→ SNS アイコン（Layer 4）。`aws_sns_topic_subscription` から接続先を破線矢印で描画する。

---

## CDN / セキュリティ

### `aws_cloudfront_distribution`

```hcl
resource "aws_cloudfront_distribution" "cdn" {
  origin {
    domain_name = aws_s3_bucket.assets.bucket_regional_domain_name
    origin_id   = "S3-assets"
    s3_origin_config { origin_access_identity = "..." }
  }

  origin {
    domain_name = aws_lb.main.dns_name
    origin_id   = "ALB-main"
    custom_origin_config {
      http_port  = 80
      https_port = 443
      origin_protocol_policy = "https-only"
    }
  }

  web_acl_id = aws_wafv2_web_acl.main.arn   # → WAF 接続

  default_cache_behavior {
    target_origin_id = "ALB-main"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["DELETE","GET","HEAD","OPTIONS","PATCH","POST","PUT"]
  }
}
```

→ CloudFront アイコン（Layer 3、VPC外）。`origin` から S3/ALB への接続を抽出する。

---

### `aws_wafv2_web_acl`

```hcl
resource "aws_wafv2_web_acl" "main" {
  name  = "main-waf"
  scope = "REGIONAL"    # REGIONAL or CLOUDFRONT
  ...
}

resource "aws_wafv2_web_acl_association" "alb" {
  resource_arn = aws_lb.main.arn               # → WAF → ALB に適用
  web_acl_arn  = aws_wafv2_web_acl.main.arn
}
```

→ WAF アイコン（Layer 2）。`aws_wafv2_web_acl_association` から保護対象との接続を抽出する。

---

## Module の扱い

### サードパーティモジュール

```hcl
module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 5.0"

  cidr = "10.0.0.0/16"
  azs  = ["ap-northeast-1a", "ap-northeast-1c"]

  public_subnets   = ["10.0.1.0/24", "10.0.2.0/24"]
  private_subnets  = ["10.0.11.0/24", "10.0.12.0/24"]
  database_subnets = ["10.0.21.0/24", "10.0.22.0/24"]

  enable_nat_gateway     = true
  single_nat_gateway     = false   # false → AZごとに NAT GW
  enable_dns_hostnames   = true

  public_subnet_tags = { "subnet-type" = "public" }
}
```

**`terraform-aws-modules/vpc`** が作成するリソース:
- VPC (cidr から)
- パブリックサブネット × AZ数
- プライベートサブネット × AZ数
- DBサブネット × AZ数（あれば）
- IGW
- NAT Gateway（`enable_nat_gateway = true`、`single_nat_gateway = false` なら AZ×1個）
- ルートテーブル各種

---

### よく使うモジュールのリソース展開早見表

| モジュール | 展開されるリソース |
|-----------|------------------|
| `terraform-aws-modules/vpc/aws` | VPC, Subnets, IGW, NAT GW, Route Tables |
| `terraform-aws-modules/alb/aws` | ALB/NLB, Listeners, Target Groups |
| `terraform-aws-modules/ecs/aws` | ECS Cluster, Service, Task Definition, IAM Roles |
| `terraform-aws-modules/lambda/aws` | Lambda, IAM Role, CloudWatch Log Group |
| `terraform-aws-modules/rds/aws` | RDS Instance, Subnet Group, Parameter Group |
| `terraform-aws-modules/rds-aurora/aws` | Aurora Cluster, Instances, Subnet Group |

---

## Variables / Locals の活用

```hcl
variable "env" {
  default = "prod"
}

locals {
  name_prefix = "${var.env}-myapp"
  azs         = ["ap-northeast-1a", "ap-northeast-1c"]
}

resource "aws_subnet" "public" {
  count             = length(local.azs)
  availability_zone = local.azs[count.index]
  cidr_block        = "10.0.${count.index}.0/24"
}
```

`count` や `for_each` が使われている場合:
- `count = 2` → 同種のリソースが2つ生成 → AZ×1個ずつとして図に展開する
- ラベルに「(×2)」や「(per AZ)」と注記する

---

## `data` ソースの扱い

`data` ブロックは **既存のリソース** を参照するもので、新規リソースを作成しない。

```hcl
data "aws_vpc" "existing" {
  id = var.vpc_id
}
```

→ 参照した既存VPCをコンテナとして図に含める（「既存VPC」と注記する）。
