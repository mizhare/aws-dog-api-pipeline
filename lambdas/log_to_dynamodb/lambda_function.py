import boto3
from datetime import datetime
import os

dynamodb = boto3.resource("dynamodb")
TABLE_NAME = os.environ.get("DDB_TABLE")

def lambda_handler(event, context):
    uploaded_image = event.get("uploaded_image")
    image_url = event.get("image_url")
    status = event.get("status", "unknown")
    if not uploaded_image:
        return {"status": "error", "message": "uploaded_image not found in input"}


    try:
        file_type = uploaded_image.split(".")[-1].lower()
    except Exception:
        file_type = "unknown"

    alert_triggered = status.lower() != "success"

    item = {
        "image_name": uploaded_image,
        "image_url": image_url,
        "upload_timestamp": datetime.utcnow().isoformat(),
        "file_type": file_type,
        "alert_triggered": alert_triggered
    }

    table = dynamodb.Table(TABLE_NAME)
    table.put_item(Item=item)

    return {"status": "success", "logged_item": item}