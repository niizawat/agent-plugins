import * as cdk from 'aws-cdk-lib';
import * as ec2 from 'aws-cdk-lib/aws-ec2';
import * as ecs from 'aws-cdk-lib/aws-ecs';
import * as ecs_patterns from 'aws-cdk-lib/aws-ecs-patterns';
import * as rds from 'aws-cdk-lib/aws-rds';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import * as wafv2 from 'aws-cdk-lib/aws-wafv2';
import * as cloudwatch from 'aws-cdk-lib/aws-cloudwatch';
import { Construct } from 'constructs';

/**
 * サンプルWebアプリケーションスタック
 * - CloudFront + WAF → ALB → ECS Fargate → RDS Aurora (Multi-AZ)
 * - S3静的コンテンツ配信
 * - CloudWatch監視
 */
export class WebAppStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // ─── ネットワーク ───
    const vpc = new ec2.Vpc(this, 'AppVpc', {
      cidr: '10.0.0.0/16',
      maxAzs: 2,
      natGateways: 1,
      subnetConfiguration: [
        { name: 'Public',   subnetType: ec2.SubnetType.PUBLIC,             cidrMask: 24 },
        { name: 'Private',  subnetType: ec2.SubnetType.PRIVATE_WITH_EGRESS, cidrMask: 24 },
        { name: 'Isolated', subnetType: ec2.SubnetType.PRIVATE_ISOLATED,   cidrMask: 24 },
      ],
    });

    // ─── S3 (静的コンテンツ) ───
    const assetsBucket = new s3.Bucket(this, 'AssetsBucket', {
      versioned: true,
      encryption: s3.BucketEncryption.S3_MANAGED,
      removalPolicy: cdk.RemovalPolicy.RETAIN,
    });

    // ─── ECSクラスター ───
    const cluster = new ecs.Cluster(this, 'AppCluster', { vpc });

    // ─── ALB + ECS Fargate ───
    const fargateService = new ecs_patterns.ApplicationLoadBalancedFargateService(
      this, 'AppService', {
        cluster,
        cpu: 512,
        memoryLimitMiB: 1024,
        desiredCount: 2,
        taskImageOptions: {
          image: ecs.ContainerImage.fromRegistry('nginx:latest'),
          containerPort: 80,
          environment: {
            DB_HOST: '',  // RDS endpoint (filled after DB creation)
          },
        },
        publicLoadBalancer: true,
      }
    );

    // ─── Aurora MySQL (Multi-AZ) ───
    const dbCluster = new rds.DatabaseCluster(this, 'AuroraCluster', {
      engine: rds.DatabaseClusterEngine.auroraMysql({
        version: rds.AuroraMysqlEngineVersion.VER_3_04_0,
      }),
      writer: rds.ClusterInstance.provisioned('writer', {
        instanceType: ec2.InstanceType.of(
          ec2.InstanceClass.T3, ec2.InstanceSize.MEDIUM
        ),
      }),
      readers: [
        rds.ClusterInstance.provisioned('reader1'),
      ],
      vpc,
      vpcSubnets: { subnetType: ec2.SubnetType.PRIVATE_ISOLATED },
      defaultDatabaseName: 'appdb',
      credentials: rds.Credentials.fromGeneratedSecret('admin'),
    });

    // ECS → RDS の接続を許可
    dbCluster.connections.allowFrom(
      fargateService.service,
      ec2.Port.tcp(3306),
      'Allow ECS to connect to Aurora'
    );

    // ─── WAF ───
    const waf = new wafv2.CfnWebACL(this, 'AppWAF', {
      scope: 'CLOUDFRONT',
      defaultAction: { allow: {} },
      rules: [],
      visibilityConfig: {
        cloudWatchMetricsEnabled: true,
        metricName: 'AppWAF',
        sampledRequestsEnabled: true,
      },
    });

    // ─── CloudFront ───
    const distribution = new cloudfront.Distribution(this, 'AppCDN', {
      defaultBehavior: {
        origin: new origins.LoadBalancerV2Origin(fargateService.loadBalancer, {
          protocolPolicy: cloudfront.OriginProtocolPolicy.HTTPS_ONLY,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
      },
      additionalBehaviors: {
        '/assets/*': {
          origin: new origins.S3Origin(assetsBucket),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        },
      },
      webAclId: waf.attrArn,
    });

    // ─── CloudWatch ───
    new cloudwatch.Dashboard(this, 'AppDashboard', {
      dashboardName: 'WebApp-Dashboard',
      widgets: [
        [new cloudwatch.GraphWidget({
          title: 'ECS CPU Utilization',
          left: [fargateService.service.metricCpuUtilization()],
        })],
      ],
    });

    // ─── 出力 ───
    new cdk.CfnOutput(this, 'CloudFrontUrl', {
      value: `https://${distribution.distributionDomainName}`,
    });
    new cdk.CfnOutput(this, 'LoadBalancerDns', {
      value: fargateService.loadBalancer.loadBalancerDnsName,
    });
  }
}
