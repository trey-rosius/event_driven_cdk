import os
import json
from os import path
from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,

    aws_sqs as sqs, CfnParameter,
    aws_appsync as appsync,
    aws_iam as iam,
    aws_sns as sns,
    aws_dynamodb as dynamodb,
    aws_stepfunctions as stepfunctions

)

from data_sources.post import create_data_source as create_post_ds
from data_sources.delete import create_data_source as create_delete_ds
from data_sources.update import create_data_source as create_update_ds
from data_sources.get_by_id import create_data_source as create_get_by_id_ds
from data_sources.get_all import create_data_source as create_get_all_ds
from data_sources.send_sqs_message import create_data_source as create_sqs_send_message_ds
from step_function_workflow.step_function import create_step_function

dirname = path.dirname(__file__)

with open(os.path.join(dirname, "../schema.graphql"), 'r') as file:
    data_schema = file.read().replace('\n', '')


class EventDrivenCdkAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        email_address = CfnParameter(self, "subscriptionEmail")
        # SNS
        cfn_topic = sns.CfnTopic(self, "MyCfnTopic",
                                 display_name="sns-topic",
                                 fifo_topic=False,
                                 topic_name="sns-topic"
                                 )

        sns_publish_policy = sns.CfnTopicPolicy(self, "MyCfnTopicPolicy",
                                                policy_document=iam.PolicyDocument(
                                                    statements=[iam.PolicyStatement(
                                                        actions=["sns:Publish", "sns:Subscribe"
                                                                 ],
                                                        principals=[iam.AnyPrincipal()],
                                                        resources=["*"]
                                                    )]
                                                ),
                                                topics=[cfn_topic.attr_topic_arn]
                                                )
        cloud_watch_role_full_access = iam.ManagedPolicy.from_managed_policy_arn(self, "cloudWatchLogRole",
                                                                                 'arn:aws:iam::aws:policy/CloudWatchLogsFullAccess')
        db_full_access_role = iam.ManagedPolicy.from_aws_managed_policy_name('AmazonDynamoDBFullAccess')
        sns_full_access_role = iam.ManagedPolicy.from_aws_managed_policy_name(
            'AmazonSNSFullAccess')
        sqs_full_access_role = iam.ManagedPolicy.from_managed_policy_arn(self, "sqsSendMessage",
                                                                         'arn:aws:iam::aws:policy/AmazonSQSFullAccess')
        sf_full_access_role = iam.ManagedPolicy.from_aws_managed_policy_name(
            'AWSStepFunctionsFullAccess')
        appsync_cloud_watch_role = iam.Role(self, "AppSyncCloudWatchRole",
                                            assumed_by=iam.ServicePrincipal("appsync.amazonaws.com"),
                                            managed_policies=[
                                                cloud_watch_role_full_access
                                            ])

        lambda_dynamodb_cloud_watch_role = iam.Role(self, "LambdaDynamoDBCloudWatchRole",
                                                    assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                                    managed_policies=[db_full_access_role,
                                                                      cloud_watch_role_full_access])

        lambda_step_function_role = iam.Role(self, "LambdaStepFunctionRole",
                                             assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                             managed_policies=[db_full_access_role,
                                                               sns_full_access_role,
                                                               cloud_watch_role_full_access,
                                                               sns_publish_policy])

        lambda_execution_role = iam.Role(self, "LambdaExecutionRole",
                                         assumed_by=iam.AnyPrincipal(),
                                         managed_policies=[
                                             iam.ManagedPolicy.from_managed_policy_arn(self, "lambdaexecution",
                                                                                       'arn:aws:iam::aws:policy/service-role/AWSLambdaRole')])

        sqs_sendMessage_role = iam.Role(self, "SQSSendMessageRole",
                                        assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                        managed_policies=[
                                            sqs_full_access_role,
                                            cloud_watch_role_full_access])

        sqs_receiveMessage_role = iam.Role(self, "SQSReceiveMessageRole",
                                           assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
                                           managed_policies=[
                                               sqs_full_access_role,
                                               cloud_watch_role_full_access,
                                               sf_full_access_role])

        sns.CfnSubscription(self, "EmailSubscription",
                            topic_arn=cfn_topic.attr_topic_arn,
                            protocol="email",
                            endpoint=email_address.value_as_string

                            )

        # DynamoDB
        dynamodb.CfnTable(self, "Table",
                          key_schema=[dynamodb.CfnTable.KeySchemaProperty(
                              attribute_name="user_id",
                              key_type="HASH"
                          ),
                              dynamodb.CfnTable.KeySchemaProperty(
                                  attribute_name="id",
                                  key_type="RANGE"
                              )],
                          billing_mode="PAY_PER_REQUEST",
                          table_name="ORDER",
                          attribute_definitions=[dynamodb.CfnTable.AttributeDefinitionProperty(
                              attribute_name="user_id",
                              attribute_type="S"
                          ),
                              dynamodb.CfnTable.AttributeDefinitionProperty(
                                  attribute_name="id",
                                  attribute_type="S"
                              )]
                          )

        # SQS
        queue = sqs.CfnQueue(
            self, "CdkAccelerateQueue",
            visibility_timeout=300,
            queue_name="sqs-queue"
        )

        deadLetterQueue = sqs.Queue(
            self, "CdkAccelerateDLQueue",
            visibility_timeout=Duration.minutes(10),
            queue_name="dead-letter-queue"
        )

        sqs.DeadLetterQueue(max_receive_count=4, queue=deadLetterQueue)

        # APPSYNC

        log_config = appsync.CfnGraphQLApi.LogConfigProperty(
            cloud_watch_logs_role_arn=appsync_cloud_watch_role.role_arn,
            exclude_verbose_content=False,
            field_log_level="ALL")

        api = appsync.CfnGraphQLApi(self, "Api",
                                    name="event_driven_cdk",
                                    authentication_type="API_KEY",
                                    xray_enabled=True,
                                    log_config=log_config
                                    )

        api.add_dependency(queue)

        # Setting GraphQl schema

        schema = appsync.CfnGraphQLSchema(scope=self, id="schema", api_id=api.attr_api_id, definition=data_schema)

        workflow = create_step_function(self, lambda_step_function_role, cfn_topic)

        simple_state_machine = stepfunctions.CfnStateMachine(self, "SimpleStateMachine",
                                                             definition=json.loads(workflow),
                                                             role_arn=lambda_execution_role.role_arn
                                                             )

        create_delete_ds(self, api, schema, lambda_dynamodb_cloud_watch_role, lambda_execution_role)
        create_update_ds(self, api, schema, lambda_dynamodb_cloud_watch_role, lambda_execution_role)
        create_get_by_id_ds(self, api, schema, lambda_dynamodb_cloud_watch_role, lambda_execution_role)
        create_get_all_ds(self, api, schema, lambda_dynamodb_cloud_watch_role, lambda_execution_role)
        create_sqs_send_message_ds(self, api, schema, sqs_sendMessage_role, lambda_execution_role, queue)
        create_post_ds(self, simple_state_machine, sqs_receiveMessage_role, queue)
