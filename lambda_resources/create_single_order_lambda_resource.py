from aws_cdk import aws_lambda as lambda_
import aws_cdk.aws_appsync as appsync


def create_single_order_lambda_resource(stack, api, schema, db_role, lambda_execution_role):
    with open("lambda_fns/get_single_order/get_single_order.py", 'r') as file:
        get_single_order_function = file.read()

    get_single_order_function_resource = lambda_.CfnFunction(stack, "get",
                                             code=lambda_.CfnFunction.CodeProperty(
                                                 zip_file=get_single_order_function
                                             ),
                                             role=db_role.role_arn,

                                             # the properties below are optional
                                             architectures=["x86_64"],
                                             description="lambda-ds",
                                             environment=lambda_.CfnFunction.EnvironmentProperty(
                                                 variables={
                                                     "ORDER_TABLE": "ORDER"
                                                 }
                                             ),
                                             function_name="get-order-function",
                                             handler="index.handler",
                                             package_type="Zip",
                                             runtime="python3.9",
                                             timeout=123,
                                             tracing_config=lambda_.CfnFunction.TracingConfigProperty(
                                                 mode="Active"
                                             )
                                             )

    lambda_config_property = appsync.CfnDataSource.LambdaConfigProperty(
        lambda_function_arn=get_single_order_function_resource.attr_arn
    )

    get_order_lambda_datasource = appsync.CfnDataSource(scope=stack, id="lambda-get-order-ds", api_id=api.attr_api_id,
                                                 name="lambda_get_order_ds", type="AWS_LAMBDA",
                                                 lambda_config=lambda_config_property,
                                                 service_role_arn=lambda_execution_role.role_arn)

    ## get order resolver
    get_order_resolver = appsync.CfnResolver(stack, "get-order",
                                    api_id=api.attr_api_id,
                                    field_name="order",
                                    type_name="Query",
                                    data_source_name=get_order_lambda_datasource.name)
    get_order_resolver.add_dependency(schema)
    get_order_resolver.add_dependency(get_order_lambda_datasource)
