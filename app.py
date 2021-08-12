#!/usr/bin/env python3

from aws_cdk import core

from cdk.sentry_stack import SentryStack


app = core.App()
SentryStack(app, "sentry")

app.synth()
