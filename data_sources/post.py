from aws_cdk import aws_lambda as lambda_


def create_data_source(stack, simple_state_machine, sqs_receiveMessage_role, queue):
    with open("lambda_fns/post_order/post_order.py", 'r') as file:
        post_function = file.read()

    post_function = lambda_.CfnFunction(stack, "post",
                                        code=lambda_.CfnFunction.CodeProperty(
                                            zip_file=post_function
                                        ),
                                        role=sqs_receiveMessage_role.role_arn,

                                        # the properties below are optional
                                        architectures=["x86_64"],
                                        description="lambda-ds",
                                        environment=lambda_.CfnFunction.EnvironmentProperty(
                                            variables={
                                                "ORDER_TABLE": "ORDER",
                                                "STATE_MACHINE_ARN": simple_state_machine.attr_arn
                                            }
                                        ),
                                        function_name="post-order-function",
                                        handler="index.handler",
                                        package_type="Zip",
                                        runtime="python3.9",
                                        timeout=123,
                                        tracing_config=lambda_.CfnFunction.TracingConfigProperty(
                                            mode="Active"
                                        )
                                        )

    event_source_mapping = lambda_.EventSourceMapping(scope=stack, id="MyEventSourceMapping",
                                                      target=post_function,
                                                      batch_size=5,
                                                      enabled=True,
                                                      event_source_arn=queue.attr_arn)
