
<p align=center>
  <img width="100%" src="https://github.com/mizhare/dog-api-pipeline/blob/main/images/header3-alinhado.png" />
</p>

## Overview

This project was developed as the deliverable for the “Intermediate and Advanced AWS Services” challenge (Module 7) in the Santander Code Girls 2025 Bootcamp.

The objective was to design a realistic workflow that demonstrates how multiple AWS services can be orchestrated to build an end-to-end serverless data pipeline, applying concepts such as Lambda Functions, Step Functions, S3 storage, SNS notifications, and DynamoDB logging.

For this challenge, I decided to create a pipeline that interacts with a public Dog API to fetch random dog images. The workflow performs the following steps:

1. **Fetch Dog Image**: A Lambda function requests a random dog image from the API.
2. **Upload to S3**: The image is ingested and stored in an S3 bucket.
3. **File Type Check**: The Step Functions workflow checks whether the uploaded image is a .png, which is not expected in this pipeline.
4. **Alerting**: If a .png file is detected, a dedicated Lambda function triggers an SNS notification to alert the user.
5. **Logging**: Finally, all image metadata (image name, URL, file type, timestamp, and alert status) is stored in a DynamoDB table for audit and monitoring purposes.
    
The main focus of this project was to show how to orchestrate multiple AWS services in a controlled workflow. It demonstrates the integration of:

- **Lambda Functions**: for serverless execution of API requests, image ingestion, alerting, and logging.
- **Step Functions**: for coordinating tasks, handling branching logic, and sequencing operations.
- **S3**: for scalable and durable storage of ingested images.
- **SNS**: for real-time notifications when unexpected events (like a .png upload) occur.
- **DynamoDB**: for structured storage of metadata, enabling traceability and potential analytics on uploaded files.

Additionally, the project includes a Python ingestion script (ingest_dog.py), which automates the fetch-and-upload logic for local testing or direct execution outside of the Step Functions workflow.
Overall, this project highlights a complete serverless architecture from fetching raw data, processing and storing it, to monitoring and logging demonstrating practical applications of intermediate and advanced AWS services for data orchestration, reliability, and observability.

## Components

### 1. S3 Bucket
- **Purpose:** Stores all downloaded dog images.
- **Structure:** Images are uploaded into a designated folder (**html/**) for organization.
- **Security:** Access is controlled via IAM roles and policies to allow Lambda functions to write files securely without exposing credentials.

---

### 2. Lambda Functions

#### FetchAndUploadDogImage (UploadToS3) 
- **Purpose:** Fetches an image from the Dog CEO API and uploads it to S3.
- **Language:** Python
- **Environment Variables:**
    - DOG_BUCKET: Name of the S3 bucket to store images.
- **Steps:**
    1. Request a random dog image from the Dog CEO API https://dog.ceo/api/breeds/image/random.
    2. Parse the JSON response to extract the **image_url**.
    3. Download the image from the URL.
    4. Upload the image to the S3 bucket in **html/** folder.
    5. Return a JSON object containing the **status** and uploaded image name.
        
- **Key Features:**
    - Handles error cases such as missing URL or failed download.
    - Can be adapted to fetch test images (e.g., PNG or JPEG) for testing purposes.
    - Avoids use of external libraries like **requests** to ensure compatibility with Lambda default runtime.
        
- **Python Implementation:**
```python
import os
import urllib.request
import boto3
  

AWS_BUCKET = os.environ.get("DOG_BUCKET")
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


        return {"status": "success", "uploaded_image": image_name,"image_url": s3_url}
  
    except Exception as e:
        return {"status": "error", "message": str(e)}

```

---

#### AlertPNG

- **Purpose:** Triggered when a .png extension is detected in the workflow (upload of PNG images).
- **Behavior:** Can send a message to an SNS topic or log the detection.
- **Notes:** Used mainly for demonstration and testing SNS notifications.

- **Python Implementation:**
```python
def lambda_handler(event, context):
    print("⚠️ PNG detected:", event.get("uploaded_image"))
    return {"status": "alert", "message": "PNG detected", "image": event.get("uploaded_image")}

```

---

#### LogToDynamoDB

- **Purpose:**  
    Store metadata about each uploaded image in a DynamoDB table for traceability and auditing purposes.  
    This function serves as the final logging step of the workflow, ensuring every image processed through the pipeline is recorded with its key attributes.
    
- **Behavior:**  
    Receives the event data from Step Functions (including uploaded_image, image_url, timestamp, and alert status), and inserts a new item into the DynamoDB table.  
    Each entry includes:
    
    - **image_name**: The name of the file uploaded to S3.
    - **image_url**: Full S3 URL for easy access.
    - **upload_timestamp**: Time when the Step Function reached this state.
    - **file_type**: Image extension (e.g., jpg or png).
    - **alert_triggered**: Boolean flag indicating if an alert (such as a PNG detection) was triggered.
        
- **Notes:**
    - The Lambda execution role must include the dynamodb:PutItem permission for the table DogImageUploads.
    - Logs are sent to **CloudWatch** automatically.
    - This Lambda helps maintain a lightweight audit trail without needing an external database or analytics engine.
    - The workflow can later be extended to analyze these records for insights (e.g., image type distribution, frequency of alerts).
        
- **Python Implementation:**
```python
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

```


---

### 3. Step Functions Workflow

<p align=center>
  <img src="https://github.com/mizhare/dog-api-pipeline/blob/main/images/stepfunctions_graph.png" />
</p>

#### Workflow States

1. **FetchAndUploadDogImage (Task)**
- Invokes the Lambda function to fetch a random dog image and upload it to S3.
- Returns the image name and bucket path as output.
- Transitions to **LogToDynamoDB**.

2. **LogToDynamoDB (Task)**
- Invokes the Lambda function **LogToDynamoDB**, which writes metadata (such as image name, timestamp, and bucket location) to the **DogImageUploads** DynamoDB table.
- Ensures every upload is registered in a persistent NoSQL database for tracking and analytics.
- On success, transitions to **CheckIfPNG**.
        
3. **CheckIfPNG (Choice)**
    - Evaluates the uploaded image filename.
    - If the filename ends with .png: transition to AlertPNG.
    - Otherwise: transition to SuccessState.

![](https://github.com/mizhare/dog-api-pipeline/blob/main/images/check_ifpng.png)
        
4. **AlertPNG (Task)**
    - Calls Lambda AlertPNG to prepare notification data.
    - Passes output to PublishPNGAlert.
        
5. **PublishPNGAlert (Task)**
    - Uses **SNS integration** (arn:aws:states:::sns:publish) to publish an alert message.
    - The message dynamically includes the uploaded file name using States.Format.
    - Example Parameters:
```json
"TopicArn": "arn:aws:sns:region:account-id:png-alert-topic",   "Message.$": "States.Format('A PNG file was detected and processed: {}', $.image)" }
```

6. **SuccessState (Succeed)**
    - Marks the successful completion of the workflow.
        

---

### 4. Testing & Validation SNS messages

**Scenario:** Verify SNS notifications for image type detection.
- **Method:**
    1. *Temporarily modified the Choice State* to fetch a test using JPG (since it is not easy to get PNG images through this API).
    2. Ran the Step Function and observed state transitions:
        - CheckIfPNG: correctly detected the file extension.
        - AlertPNG: invoked as expected.
        - PublishPNGAlert: published a message to SNS.
    3. Confirmed that SNS subscribers received the message successfully.
- **Outcome:** Successfully confirmed alert mechanism works for extensions detection.
<p align=center>
  <img src="https://github.com/mizhare/dog-api-pipeline/blob/main/images/email_sns.png" />
</p>

---

### 5. IAM Permissions - Roles and User Functions 

A key part of the implementation involved carefully setting up **IAM roles and policies** to ensure each service had the necessary permissions while following security best practices.

Step Functions Role
The Step Functions workflow (DogUploaderPipeline) runs under a dedicated IAM role:
**StepFunctions-DogUploaderPipeline-role

This role is assumed by Step Functions to execute all tasks in the workflow. To function properly, it required:
- **Lambda invocation permissions**: The role must have _lambda:InvokeFunction_ on all Lambda functions used in the pipeline, such as FetchDogImage**, **UploadToS3**, **LogToDynamoDB**, and **AlertPNG**.
- **SNS publish permissions**: To send alerts when a .png file is detected, the role needs _sns:Publish_ access to the SNS topic (png-alert-topic).
- **S3 read/write permissions**: While the Lambda functions interact with S3 directly, Step Functions relies on the Lambda role, so the Lambda role also needed _s3:PutObject_ access for uploading images.
- **DynamoDB write permissions**: To allow the **LogToDynamoDB** function to insert image metadata into the table, the role required dynamodb:PutItem permission on that table’s ARN.
![](https://github.com/mizhare/dog-api-pipeline/blob/main/images/uploader_role_permissions.png)

- **Lambda Functions**
    - Need permissions to interact with S3 (s3:PutObject) and optionally read the bucket.
    - Does not require administrative privileges.

**UploadToS3, LogToDynamoDB: Permissions policies for the Execution Role** - PutObject and GetObject. Invoke Functions for the StepFunction Role.

> All credentials and sensitive information are stored in environment variables and IAM roles, avoiding exposure in the workflow code.

---
### Ingestion Script

- A separate _ingestion script_ exists in the repository to handle bulk API ingestion for additional datasets.
- This script is designed to:
    - Pull data from external APIs.
    - Transform and normalize data as needed.
    - Store output in S3 for further processing.
- Can be integrated into Step Functions for orchestrated ingestion pipelines.
    

---
### Notes and Best Practices

- Step Functions allow modular extension of the workflow:
    - Additional Choice states for different file types.
    - Retry policies on failures.
    - Logging using CloudWatch and DynamoDB for audit trails.
        
- Testing with known image types (PNG/JPG) helps validate SNS alerts without waiting for random API results.
- All Python code avoids external dependencies to simplify Lambda deployment.
- Environment variables and IAM roles keep sensitive information secure.

