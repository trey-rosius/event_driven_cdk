#!/usr/bin/env python3


import aws_cdk as cdk

from event_driven_cdk_app.event_driven_cdk_app_stack import EventDrivenCdkAppStack

app = cdk.App()
EventDrivenCdkAppStack(app, "EdCdkAppStack",

                       env=cdk.Environment(account='132260253285', region='us-east-2'),

                       )

app.synth()
