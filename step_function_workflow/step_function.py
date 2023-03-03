from string import Template

from aws_cdk import aws_lambda as lambda_
from aws_cdk.aws_sns import CfnTopicPolicy

with open("lambda_fns/initialize_order/initialize_order.py", "r") as file:
    initialize_order = file.read()
with open("lambda_fns/cancel_failed_order/cancel_failed_order.py", "r") as file:
    cancel_failed_order = file.read()
with open("lambda_fns/complete_order/complete_order.py", "r") as file:
    complete_order = file.read()
with open("lambda_fns/process_payment/process_payment.py", "r") as file:
    process_payment = file.read()
with open("step_function_workflow/workflow.json", "r") as file:
    workflow = file.read()


def create_step_function(stack, lambda_step_function_role, cfn_topic):
    cancel_failed_order_function = lambda_.CfnFunction(
        stack,
        "cancel-failed-order-function",
        code=lambda_.CfnFunction.CodeProperty(zip_file=cancel_failed_order),
        role=lambda_step_function_role.role_arn,
        # the properties below are optional
        architectures=["x86_64"],
        description="lambda-ds",
        environment=lambda_.CfnFunction.EnvironmentProperty(
            variables={"ORDER_TABLE": "ORDER", "TOPIC_ARN": cfn_topic.attr_topic_arn}
        ),
        function_name="cancel-failed-order-function",
        handler="index.handler",
        package_type="Zip",
        runtime="python3.9",
        timeout=123,
        tracing_config=lambda_.CfnFunction.TracingConfigProperty(mode="Active"),
    )

    complete_order_function = lambda_.CfnFunction(
        stack,
        "complete-order-function",
        code=lambda_.CfnFunction.CodeProperty(zip_file=complete_order),
        role=lambda_step_function_role.role_arn,
        # the properties below are optional
        architectures=["x86_64"],
        description="lambda-ds",
        environment=lambda_.CfnFunction.EnvironmentProperty(
            variables={"ORDER_TABLE": "ORDER", "TOPIC_ARN": cfn_topic.attr_topic_arn}
        ),
        function_name="complete-order-function",
        handler="index.handler",
        package_type="Zip",
        runtime="python3.9",
        timeout=123,
        tracing_config=lambda_.CfnFunction.TracingConfigProperty(mode="Active"),
    )

    initialize_order_function = lambda_.CfnFunction(
        stack,
        "initialize-order-function",
        code=lambda_.CfnFunction.CodeProperty(zip_file=initialize_order),
        role=lambda_step_function_role.role_arn,
        # the properties below are optional
        architectures=["x86_64"],
        description="lambda-ds",
        environment=lambda_.CfnFunction.EnvironmentProperty(
            variables={"ORDER_TABLE": "ORDER", "TOPIC_ARN": cfn_topic.attr_topic_arn}
        ),
        function_name="initialize-order-function",
        handler="index.handler",
        package_type="Zip",
        runtime="python3.9",
        timeout=123,
        tracing_config=lambda_.CfnFunction.TracingConfigProperty(mode="Active"),
    )

    process_payment_function = lambda_.CfnFunction(
        stack,
        "process-payment-function",
        code=lambda_.CfnFunction.CodeProperty(zip_file=process_payment),
        role=lambda_step_function_role.role_arn,
        # the properties below are optional
        architectures=["x86_64"],
        description="lambda-ds",
        environment=lambda_.CfnFunction.EnvironmentProperty(
            variables={"ORDER_TABLE": "ORDER", "TOPIC_ARN": cfn_topic.attr_topic_arn}
        ),
        function_name="process-payment-function",
        handler="index.handler",
        package_type="Zip",
        runtime="python3.9",
        timeout=123,
        tracing_config=lambda_.CfnFunction.TracingConfigProperty(mode="Active"),
    )

    sf_workflow = Template(workflow).substitute(
        InitializeOrderArn=initialize_order_function.attr_arn,
        ProcessPaymentArn=process_payment_function.attr_arn,
        CompleteOrderArn=complete_order_function.attr_arn,
        CancelFailedOrderArn=cancel_failed_order_function.attr_arn,
        dollar="$",
    )

    return sf_workflow
