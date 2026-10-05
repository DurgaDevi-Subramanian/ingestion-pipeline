from app.storage import s3, BUCKET

response = s3.list_objects_v2(Bucket=BUCKET, MaxKeys=5)
print("Connected to bucket:", BUCKET)
print("Objects so far:", response.get("KeyCount", 0))