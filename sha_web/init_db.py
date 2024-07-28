from pymongo import MongoClient
# from werkzeug.security import generate_password_hash
from datetime import datetime

client = MongoClient("mongodb://localhost:27017/")
db = client["sha"]

# 샘플 사용자 데이터 삽입
users = db.users
users.insert_many([
    {
        "username": "sampleuser",
        "password": "password",  # 해시된 비밀번호
        "full_name": "Sample User",
        "email": "sampleuser@example.com"
    }
])

# 샘플 게시글 데이터 삽입
posts = db.posts
post_id = posts.insert_one({
    "title": "First Post",
    "content": "This is the content of the first post.",
    "author": "sampleuser",
    "date_posted": datetime.now()
}).inserted_id

# 샘플 댓글 데이터 삽입
comments = db.comments
comments.insert_many([
    {
        "post_id": post_id,
        "content": "This is a comment.",
        "author": "sampleuser",
        "date_posted": datetime.now()
    }
])

print("Initial data inserted.")
