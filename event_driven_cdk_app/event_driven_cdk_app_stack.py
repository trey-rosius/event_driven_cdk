import json
import os
from os import path

from aws_cdk import CfnParameter, Duration, Stack
from aws_cdk import aws_appsync as appsync
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_iam as iam
from aws_cdk import aws_sns as sns
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_stepfunctions as stepfunctions
from constructs import Construct

from event_driven_cdk_app.post_order_resource import create_post_order_lambda_resource
from lambda_resources.delete_order_lambda_resource import delete_order_lambda_resource
from lambda_resources.get_all_orders_lambda_resource import (
    get_all_orders_lambda_resource,
)
from lambda_resources.get_single_order_lambda_resource import (
    get_single_order_lambda_resource,
)
from lambda_resources.send_sqs_lambda_resource import send_sqs_lambda_resource
from lambda_resources.update_order_lambda_resource import update_order_lambda_resource
from step_function_workflow.step_function import create_step_function

dir_name = path.dirname(__file__)

with open(os.path.join(dir_name, "../schema.graphql"), "r") as file:
    data_schema = file.read().replace("\n", "")


class EventDrivenCdkAppStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        email_address = CfnParameter(self, "subscriptionEmail")
        # SNS
        cfn_topic = sns.CfnTopic(
            self,
            "MyCfnTopic",
            display_name="sns-topic",
            fifo_topic=False,
            topic_name="sns-topic",
        )

        sns_policy = sns.CfnTopicPolicy(
            self,
            "MyCfnTopicPolicy",
            policy_document=iam.PolicyDocument(
                statements=[
                    iam.PolicyStatement(
                        actions=["sns:Publish", "sns:Subscribe"],
                        principals=[iam.AnyPrincipal()],
                        resources=["*"],
                    )
                ]
            ),
            topics=[cfn_topic.attr_topic_arn],
        )
        cloud_watch_role_full_access = iam.ManagedPolicy.from_managed_policy_arn(
            self,
            "cloudWatchLogRole",
            "arn:aws:iam::aws:policy" "/CloudWatchLogsFullAccess",
        )
        db_full_access_role = iam.ManagedPolicy.from_aws_managed_policy_name(
            "AmazonDynamoDBFullAccess"
        )

        sqs_full_access_role = iam.ManagedPolicy.from_managed_policy_arn(
            self, "sqsSendMessage", "arn:aws:iam::aws:policy/AmazonSQSFullAccess"
        )
        sf_full_access_role = iam.ManagedPolicy.from_aws_managed_policy_name(
            "AWSStepFunctionsFullAccess"
        )
        appsync_cloud_watch_role = iam.Role(
            self,
            "AppSyncCloudWatchRole",
            assumed_by=iam.ServicePrincipal("appsync.amazonaws.com"),
            managed_policies=[cloud_watch_role_full_access],
        )

        lambda_dynamodb_cloud_watch_role = iam.Role(
            self,
            "LambdaDynamoDBCloudWatchRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[db_full_access_role, cloud_watch_role_full_access],
        )

        lambda_step_function_role = iam.Role(
            self,
            "LambdaStepFunctionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                db_full_access_role,
                cloud_watch_role_full_access,
                sns_policy,
            ],
        )

        lambda_execution_role = iam.Role(
            self,
            "LambdaExecutionRole",
            assumed_by=iam.AnyPrincipal(),
            managed_policies=[
                iam.ManagedPolicy.from_managed_policy_arn(
                    self,
                    "lambdaexecution",
                    "arn:aws:iam::aws:policy/service-role/AWSLambdaRole",
                )
            ],
        )

        sqs_send_message_role = iam.Role(
            self,
            "SQSSendMessageRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[sqs_full_access_role, cloud_watch_role_full_access],
        )

        sqs_receive_message_role = iam.Role(
            self,
            "SQSReceiveMessageRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                sqs_full_access_role,
                cloud_watch_role_full_access,
                sf_full_access_role,
            ],
        )

        sns.CfnSubscription(
            self,
            "EmailSubscription",
            topic_arn=cfn_topic.attr_topic_arn,
            protocol="email",
            endpoint=email_address.value_as_string,
        )

        # DynamoDB
        dynamodb.CfnTable(
            self,
            "Table",
            key_schema=[
                dynamodb.CfnTable.KeySchemaProperty(
                    attribute_name="user_id", key_type="HASH"
                ),
                dynamodb.CfnTable.KeySchemaProperty(
                    attribute_name="id", key_type="RANGE"
                ),
            ],
            billing_mode="PAY_PER_REQUEST",
            table_name="ORDER",
            attribute_definitions=[
                dynamodb.CfnTable.AttributeDefinitionProperty(
                    attribute_name="user_id", attribute_type="S"
                ),
                dynamodb.CfnTable.AttributeDefinitionProperty(
                    attribute_name="id", attribute_type="S"
                ),
            ],
        )

        # SQS
        queue = sqs.CfnQueue(
            self, "CdkAccelerateQueue", visibility_timeout=300, queue_name="sqs-queue"
        )

        dead_letter_queue = sqs.Queue(
            self,
            "CdkAccelerateDLQueue",
            visibility_timeout=Duration.minutes(10),
            queue_name="dead-letter-queue",
        )

        sqs.DeadLetterQueue(max_receive_count=4, queue=dead_letter_queue)

        # APPSYNC

        log_config = appsync.CfnGraphQLApi.LogConfigProperty(
            cloud_watch_logs_role_arn=appsync_cloud_watch_role.role_arn,
            exclude_verbose_content=False,
            field_log_level="ALL",
        )

        api = appsync.CfnGraphQLApi(
            self,
            "Api",
            name="event_driven_cdk",
            authentication_type="API_KEY",
            xray_enabled=True,
            log_config=log_config,
        )

        api.add_dependency(queue)

        # Setting GraphQl schema

        schema = appsync.CfnGraphQLSchema(
            scope=self, id="schema", api_id=api.attr_api_id, definition=data_schema
        )

        workflow = create_step_function(self, lambda_step_function_role, cfn_topic)

        simple_state_machine = stepfunctions.CfnStateMachine(
            self,
            "SimpleStateMachine",
            definition=json.loads(workflow),
            role_arn=lambda_execution_role.role_arn,
        )

        delete_order_lambda_resource(
            self, api, schema, lambda_dynamodb_cloud_watch_role, lambda_execution_role
        )
        update_order_lambda_resource(
            self, api, schema, lambda_dynamodb_cloud_watch_role, lambda_execution_role
        )
        get_single_order_lambda_resource(
            self, api, schema, lambda_dynamodb_cloud_watch_role, lambda_execution_role
        )
        get_all_orders_lambda_resource(
            self, api, schema, lambda_dynamodb_cloud_watch_role, lambda_execution_role
        )
        send_sqs_lambda_resource(
            self, api, schema, sqs_send_message_role, lambda_execution_role, queue
        )
        create_post_order_lambda_resource(
            self, simple_state_machine, sqs_receive_message_role, queue
        )
