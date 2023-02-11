from aws_cdk import aws_lambda as lambda_
import aws_cdk.aws_appsync as appsync


def create_data_source(stack, api, schema, db_role, lambda_execution_role):
    with open("lambda_fns/get_orders/get_orders.py", 'r') as file:
        geta_all_order_lambda_function = file.read()

    get_all_order_function = lambda_.CfnFunction(stack, "gets",
                                                 code=lambda_.CfnFunction.CodeProperty(
                                                     zip_file=geta_all_order_lambda_function
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

    lambda_get_all_order_config_property = appsync.CfnDataSource.LambdaConfigProperty(
        lambda_function_arn=get_all_order_function.attr_arn
    )

    lambda_get_all_order_data_source = appsync.CfnDataSource(scope=stack, id="lambda-getAll-order-ds",
                                                             api_id=api.attr_api_id,
                                                             name="lambda_getAll_order_ds", type="AWS_LAMBDA",
                                                             lambda_config=lambda_get_all_order_config_property,
                                                             service_role_arn=lambda_execution_role.role_arn)

    # Resolvers
    ## list orders resolver
    get_all_orders_resolver = appsync.CfnResolver(stack, "list-orders",
                                                  api_id=api.attr_api_id,
                                                  field_name="orders",
                                                  type_name="Query",
                                                  data_source_name=lambda_get_all_order_data_source.name)
    get_all_orders_resolver.add_dependency(schema)
    get_all_orders_resolver.add_dependency(lambda_get_all_order_data_source)
