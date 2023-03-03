import os

import boto3

ddb_client = boto3.client("dynamodb")
TABLE_NAME = os.environ.get("ORDER_TABLE")


def process_response(data):
    print(data)
    data["id"] = data["id"]["S"]
    data["quantity"] = data["quantity"]["N"]
    data["name"] = data["name"]["S"]
    data["restaurantId"] = data["restaurantId"]["S"]
    data["orderStatus"] = data["orderStatus"]["S"]

    return data


def fetch_all_orders(dynamo_client, table_name):
    results = []
    last_evaluated_key = None
    while True:
        if last_evaluated_key:
            response = ddb_client.scan(
                TableName=table_name, ExclusiveStartKey=last_evaluated_key
            )
        else:
            response = dynamo_client.scan(TableName=table_name)

        last_evaluated_key = response.get("LastEvaluatedKey")
        response = map(process_response, response["Items"])
        response = list(response)
        results.extend(response)

        if not last_evaluated_key:
            break
    print(f"fetch_all_orders returned {results}")
    return results


def handler(event, context):
    items = fetch_all_orders(ddb_client, TABLE_NAME)
    return items
