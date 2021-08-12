import json

from aws_cdk import (
    aws_ec2 as ec2,
    aws_iam as iam,
    aws_secretsmanager as sm,
    aws_rds as rds,
    core
)



class SentryStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sentry_dsn = core.CfnParameter(self, "sentrydsn",
            type="String",
            description="SENTRY DSN"
        )

        vpc = ec2.Vpc(self, "vpc",
            nat_gateways=0,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="public",
                    subnet_type=ec2.SubnetType.PUBLIC
                )
            ]
        )

        db_secret = sm.Secret(self, "db_secret",
            generate_secret_string= sm.SecretStringGenerator(
                secret_string_template=json.dumps({"username": "admin"}),
                generate_string_key="password",
                exclude_punctuation=True,
                password_length=20
            )
        )

        mysql = rds.DatabaseInstance(self, "mysql",
            engine=rds.DatabaseInstanceEngine.mysql(version=rds.MysqlEngineVersion.VER_8_0),
            vpc=vpc,
            port=3306,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE2,
                ec2.InstanceSize.MICRO
            ),
            allocated_storage=20,
            credentials=rds.Credentials.from_secret(db_secret),
            removal_policy=core.RemovalPolicy.DESTROY,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            )
        )

        user_data = ec2.UserData.for_linux()
        user_data.add_commands("yum update -y && yum install -y httpd git mod_wsgi python3-3.7*")
        user_data.add_commands("pip3 install flask==1.1.4 boto3 mysql-connector sentry-sdk[flask]")
        user_data.add_commands("git clone https://github.com/youngwjung/flask-sentry.git /var/www/html/")
        user_data.add_commands(f"sed -i 's/RDS_HOST/{mysql.db_instance_endpoint_address}/g' /var/www/html/app.py")
        user_data.add_commands(f"sed -i 's,SENTRY_DSN,{sentry_dsn.value_as_string},g' /var/www/html/app.py")
        user_data.add_commands("mv /var/www/html/app.conf /etc/httpd/conf.d/")
        user_data.add_commands("systemctl enable httpd")
        user_data.add_commands("systemctl start httpd")

        instance = ec2.Instance(self, "instnace",
            vpc=vpc,
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.MICRO),
            machine_image=ec2.MachineImage.latest_amazon_linux(generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2),
            user_data=user_data,
            user_data_causes_replacement=True
        )

        instance.role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name(
                "AmazonSSMManagedInstanceCore"
            )
        )

        instance.connections.allow_from_any_ipv4(ec2.Port.tcp(80))

        core.CfnOutput(self, "EC2_IP",
            value=instance.instance_public_ip
        )
