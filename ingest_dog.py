import requests
import boto3
import os

# AWS Configurations
AWS_BUCKET = os.environ.get("AWS_BUCKET_DOG")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.environ.get("AWS_ACCESS_KEY_ID_DOG")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY_DOG")

# S3 Client
s3 = boto3.client(
    "s3",
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_KEY
)

def fetch_dog_image():
    url = "https://dog.ceo/api/breeds/image/random"
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch dog image: {response.status_code}")
    return response.json()["message"]

def upload_to_s3(image_url):
    image_name = os.path.basename(image_url)
    img_data = requests.get(image_url).content
    s3.put_object(Bucket=AWS_BUCKET, Key=f"dog/{image_name}", Body=img_data)
    print(f"Uploaded {image_name} to s3://{AWS_BUCKET}/")

if __name__ == "__main__":
    img_url = fetch_dog_image()
    upload_to_s3(img_url)