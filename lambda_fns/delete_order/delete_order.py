import decimal
import json
import os

import boto3

TABLE_NAME = os.environ.get("ORDER_TABLE")
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE_NAME)


def delete_order(event):
    order_id = event["arguments"]["id"]
    response = table.delete_item(Key={"id": order_id, "user_id": "demo_user"})
    print(f"delete_order {order_id} response: {response}")
    return response


def handler(event, context):
    delete_order(event)
    return event["arguments"]["id"]
