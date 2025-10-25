def lambda_handler(event, context):
    print("⚠️ Non-image file detected:", event.get("uploaded_image"))
    return {"status": "alert", "message": "Non-image file detected", "image": event.get("uploaded_image")}