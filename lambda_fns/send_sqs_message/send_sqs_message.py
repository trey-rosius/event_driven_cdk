import json
import logging
import os

import boto3

logging.Logger("sqs")
queue = boto3.client("sqs")
QueueUrl = os.environ.get("QueueUrl")


def send_message(message_body, message_attributes=None):
    """
    Send a message to an Amazon SQS queue.

    :param queue: The queue that receives the message.
    :param message_body: The body text of the message.
    :param message_attributes: Custom attributes of the message. These are key-value
                               pairs that can be whatever you want.
    :return: The response from SQS that contains the assigned message ID.
    """
    if not message_attributes:
        message_attributes = {}

    try:
        response = queue.send_message(
            MessageBody=json.dumps(message_body),
            MessageAttributes=message_attributes,
            QueueUrl=QueueUrl,
        )
    except Exception as error:
        print("Send message failed: %s", error)
        logging.exception("Send message failed: %s", message_body)
        raise error
    else:
        return response


def handler(event, context):
    message_body = event["arguments"]
    try:
        send_message(message_body)
    except Exception:
        return None
    else:
        return event["arguments"]["input"]
