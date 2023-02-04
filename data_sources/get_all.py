from aws_cdk import aws_lambda as lambda_
import aws_cdk.aws_appsync as appsync


def create_data_source(stack, api, schema, db_role, lambda_execution_role):
    with open("lambda_fns/get_orders/get_orders.py", 'r') as file:

        getAll_function = file.read()

    getAllDs_function = lambda_.CfnFunction(stack, "gets",
                                            code=lambda_.CfnFunction.CodeProperty(
                                                zip_file=getAll_function
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
                                            function_name="get-orders-function",
                                            handler="index.handler",
                                            package_type="Zip",
                                            runtime="python3.9",
                                            timeout=123,
                                            tracing_config=lambda_.CfnFunction.TracingConfigProperty(
                                                mode="Active"
                                            )
                                            )

    lambda_getAll_order_config_property = appsync.CfnDataSource.LambdaConfigProperty(
        lambda_function_arn=getAllDs_function.attr_arn
    )

    lambdaGetAllOrderDs = appsync.CfnDataSource(scope=stack, id="lambda-getAll-order-ds", api_id=api.attr_api_id,
                                                name="lambda_getAll_order_ds", type="AWS_LAMBDA",
                                                lambda_config=lambda_getAll_order_config_property,
                                                service_role_arn=lambda_execution_role.role_arn)

    # Resolvers
    ## list orders resolver
    list_orders = appsync.CfnResolver(stack, "list-orders",
                                      api_id=api.attr_api_id,
                                      field_name="orders",
                                      type_name="Query",
                                      data_source_name=lambdaGetAllOrderDs.name)
    list_orders.add_dependency(schema)
    list_orders.add_dependency(lambdaGetAllOrderDs)
