import aws_cdk.aws_appsync as appsync
from aws_cdk import aws_lambda as lambda_


def delete_order_lambda_resource(stack, api, schema, db_role, lambda_execution_role):
    with open("lambda_fns/delete_order/delete_order.py", "r") as file:
        delete_function = file.read()

    delete_order_function = lambda_.CfnFunction(
        stack,
        "delete",
        code=lambda_.CfnFunction.CodeProperty(zip_file=delete_function),
        role=db_role.role_arn,
        # the properties below are optional
        architectures=["x86_64"],
        description="lambda-ds",
        environment=lambda_.CfnFunction.EnvironmentProperty(
            variables={"ORDER_TABLE": "ORDER"}
        ),
        function_name="delete-order-function",
        handler="index.handler",
        package_type="Zip",
        runtime="python3.9",
        timeout=123,
        tracing_config=lambda_.CfnFunction.TracingConfigProperty(mode="Active"),
    )

    # Data source config property
    lambda_delete_order_config_property = appsync.CfnDataSource.LambdaConfigProperty(
        lambda_function_arn=delete_order_function.attr_arn
    )

    # Data source definition
    delete_order_datasource = appsync.CfnDataSource(
        scope=stack,
        id="lambda-delete-order-ds",
        api_id=api.attr_api_id,
        name="lambda_delete_order_ds",
        type="AWS_LAMBDA",
        lambda_config=lambda_delete_order_config_property,
        service_role_arn=lambda_execution_role.role_arn,
    )

    delete_order_resolver = appsync.CfnResolver(
        stack,
        "delete-order",
        api_id=api.attr_api_id,
        field_name="deleteOrder",
        type_name="Mutation",
        data_source_name=delete_order_datasource.name,
    )
    delete_order_resolver.add_dependency(schema)
    delete_order_resolver.add_dependency(delete_order_datasource)
