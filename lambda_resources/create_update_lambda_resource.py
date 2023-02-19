from aws_cdk import aws_lambda as lambda_
import aws_cdk.aws_appsync as appsync


def create_update_lambda_resource(stack, api, schema, db_role, lambda_execution_role):
    with open("lambda_fns/update_order/update_order.py", 'r') as file:
        update_function = file.read()

    update_lambda_function = lambda_.CfnFunction(stack, "update",
                                                 code=lambda_.CfnFunction.CodeProperty(
                                                     zip_file=update_function
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
                                                 function_name="update-order-function",
                                                 handler="index.handler",
                                                 package_type="Zip",
                                                 runtime="python3.9",
                                                 timeout=123,
                                                 tracing_config=lambda_.CfnFunction.TracingConfigProperty(
                                                     mode="Active"
                                                 )
                                                 )

    lambda_update_order_config_property = appsync.CfnDataSource.LambdaConfigProperty(
        lambda_function_arn=update_lambda_function.attr_arn
    )

    lambda_update_order_ds = appsync.CfnDataSource(scope=stack, id="lambda-update-order-ds", api_id=api.attr_api_id,
                                                   name="lambda_update_order_ds", type="AWS_LAMBDA",
                                                   lambda_config=lambda_update_order_config_property,
                                                   service_role_arn=lambda_execution_role.role_arn)

    update_order = appsync.CfnResolver(stack, "update-order",
                                       api_id=api.attr_api_id,
                                       field_name="updateOrder",
                                       type_name="Mutation",
                                       data_source_name=lambda_update_order_ds.name)
    update_order.add_dependency(schema)
    update_order.add_dependency(lambda_update_order_ds)
