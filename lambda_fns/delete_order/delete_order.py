import boto3
import os
import json
import decimal

TABLE_NAME = os.environ.get("ORDER_TABLE")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def delete_order(event):
    order_id = event['arguments']['id']
    response = table.delete_item(
        Key={
            'id': order_id,
            'user_id': 'demo_user'
        }
    )
    print(f'delete_order {order_id} response: {response}')
    return response


def handler(event, context):
    """Handler function integrated with 
    Parameters
    ----------
    event: dict, required
        API Gateway Lambda Proxy Input Format
        Event doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html#api-gateway-simple-proxy-for-lambda-input-format
    context: object, required
        Lambda Context runtime methods and attributes
        Context doc: https://docs.aws.amazon.com/lambda/latest/dg/python-context-object.html
    Returns
    ------
    API Gateway Lambda Proxy Output Format: dict
        Return doc: https://docs.aws.amazon.com/apigateway/latest/developerguide/set-up-lambda-proxy-integrations.html
    """

    delete_order(event)
    return event['arguments']['id']
