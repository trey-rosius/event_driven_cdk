from aws_cdk import aws_lambda as lambda_
import aws_cdk.aws_appsync as appsync


def send_sqs_lambda_resource(stack, api, schema, sqs_send_message_role, lambda_execution_role, queue):
    with open("lambda_fns/send_sqs_message/send_sqs_lambda_resource.py", 'r') as file:
        sqs_lambda = file.read()

    sqs_lambda_function = lambda_.CfnFunction(stack, "send-sqs-event",
                                                  code=lambda_.CfnFunction.CodeProperty(
                                                      zip_file=sqs_lambda
                                                  ),
                                                  role=sqs_send_message_role.role_arn,

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
        lambda_function_arn=sqs_lambda_function.attr_arn
    )

    lambda_send_sqs_message_ds = appsync.CfnDataSource(scope=stack, id="lambda-post-order-ds", api_id=api.attr_api_id,
                                                       name="lambda_post_order_ds", type="AWS_LAMBDA",
                                                       lambda_config=lambda_send_sqs_message_config_property,
                                                       service_role_arn=lambda_execution_role.role_arn)
    lambda_send_sqs_message_ds.add_dependency(queue)

    #### creating the resolver
    post_order_resolver = appsync.CfnResolver(stack, "post-order",
                                     api_id=api.attr_api_id,
                                     field_name="postOrder",
                                     type_name="Mutation",
                                     data_source_name=lambda_send_sqs_message_ds.name)
    post_order_resolver.add_dependency(schema)
    post_order_resolver.add_dependency(lambda_send_sqs_message_ds)
