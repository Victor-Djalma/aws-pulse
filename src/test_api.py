import json
import os


def lambda_handler(event, context):
    api_status = os.environ.get("API_STATUS", "UP").upper()

    if api_status == "DOWN":
        return {
            "statusCode": 503,
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({
                "service": "AWS Pulse Test API",
                "status": "DOWN",
                "message": "Service temporarily unavailable"
            })
        }

    return {
        "statusCode": 200,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps({
            "service": "AWS Pulse Test API",
            "status": "UP",
            "message": "API funcionando normalmente"
        })
    }
