import os
import urllib.request
import boto3

AWS_BUCKET = os.environ.get("AWS_BUCKET_DOG")
AWS_REGION = "us-east-1"

s3 = boto3.client("s3", region_name=AWS_REGION)


def lambda_handler(event, context):
    url = "https://dog.ceo/api/breeds/image/random"
    try:
        with urllib.request.urlopen(url) as response:
            data = response.read()
        import json
        image_url = json.loads(data).get("message")
        if not image_url:
            return {"status": "error", "message": "No image URL found"}

        image_name = os.path.basename(image_url)
        with urllib.request.urlopen(image_url) as response:
            img_data = response.read()
        if not img_data:
            return {"status": "error", "message": "No image data downloaded"}

        s3.put_object(Bucket=AWS_BUCKET, Key=f"html/{image_name}", Body=img_data)
        s3_url = f"https://{AWS_BUCKET}.s3 {AWS_REGION}.amazonaws.com/html/{image_name}"

        return {"status": "success", "uploaded_image": image_name, "image_url": s3_url}

    except Exception as e:
        return {"status": "error", "message": str(e)}