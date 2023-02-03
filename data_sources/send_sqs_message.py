from aws_cdk import aws_lambda as lambda_
import aws_cdk.aws_appsync as appsync


def create_data_source(stack, api, schema, sqs_sendMessage_role, lambda_execution_role, queue):
    with open("lambda_fns/send_sqs_message/send_sqs_message.py", 'r') as file:
        sendSQSMessage_code = file.read()

    sendSQSMessage_function = lambda_.CfnFunction(stack, "send-sqs-event",
                                                  code=lambda_.CfnFunction.CodeProperty(
                                                      zip_file=sendSQSMessage_code
                                                  ),
                                                  role=sqs_sendMessage_role.role_arn,

                                                  # the properties below are optional
                                                  architectures=["x86_64"],
                                                  description="lambda-ds",
                                                  environment=lambda_.CfnFunction.EnvironmentProperty(
                                                      variables={
                                                          "QueueUrl": queue.attr_queue_url
                                                      }
                                                  ),
                                                  function_name="send-sqs-function",
                                                  handler="index.handler",
                                                  package_type="Zip",
                                                  runtime="python3.9",
                                                  timeout=123,
                                                  tracing_config=lambda_.CfnFunction.TracingConfigProperty(
                                                      mode="Active"
                                                  )
                                                  )

    lambda_send_sqs_message_config_property = appsync.CfnDataSource.LambdaConfigProperty(
        lambda_function_arn=sendSQSMessage_function.attr_arn
    )

    lambdaSendSQSMessageDs = appsync.CfnDataSource(scope=stack, id="lambda-post-order-ds", api_id=api.attr_api_id,
                                                   name="lambda_post_order_ds", type="AWS_LAMBDA",
                                                   lambda_config=lambda_send_sqs_message_config_property,
                                                   service_role_arn=lambda_execution_role.role_arn)
    lambdaSendSQSMessageDs.add_dependency(queue)

    #### creating the resolver
    post_order = appsync.CfnResolver(stack, "post-order",
                                     api_id=api.attr_api_id,
                                     field_name="postOrder",
                                     type_name="Mutation",
                                     data_source_name=lambdaSendSQSMessageDs.name)
    post_order.add_dependency(schema)
    post_order.add_dependency(lambdaSendSQSMessageDs)
