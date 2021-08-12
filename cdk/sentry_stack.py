from aws_cdk import (
    aws_ec2 as ec2,
    core
)


class SentryStack(core.Stack):

    def __init__(self, scope: core.Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
