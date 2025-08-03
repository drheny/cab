#!/usr/bin/env python3
"""
Emergency standalone server that works without environment variables
Creates default users automatically and works with in-memory data if needed
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from datetime import datetime, timedelta
from typing import Optional, List
import bcrypt
import json
import os
from jose import JWTError, jwt
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# FastAPI app
app = FastAPI(title="Medical Cabinet - Emergency Mode")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT Configuration
SECRET_KEY = "emergency-secret-key-for-deployment"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440

# Security
security = HTTPBearer()

# In-memory data store (fallback if MongoDB fails)
emergency_data = {
    "users": [],
    "patients": [],
    "appointments": [],
    "consultations": [],
    "payments": []
}

# MongoDB fallback
try:
    from pymongo import MongoClient
    MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/cabinet_medical')
    client = MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
    # Test connection
    client.server_info()
    db = client.get_database("cabinet_medical")
    USE_MONGODB = True
    print("✅ MongoDB connected successfully")
except Exception as e:
    USE_MONGODB = False
    db = None
    client = None
    print(f"⚠️  MongoDB unavailable, using in-memory storage: {e}")

# Models
class LoginRequest(BaseModel):
    username: str
    password: str

class User(BaseModel):
    username: str
    full_name: str
    role: str
    is_active: bool = True

# Helper functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

def get_user(username: str):
    """Get user from MongoDB or in-memory store"""
    if USE_MONGODB and db:
        try:
            users_collection = db["users"]
            return users_collection.find_one({"username": username})
        except:
            pass
    
    # Fallback to in-memory
    for user in emergency_data["users"]:
        if user["username"] == username:
            return user
    return None

def create_default_users():
    """Create default users if they don't exist"""
    if get_user("medecin"):
        return  # Users already exist
    
    # Create default users
    medecin_user = {
        "username": "medecin",
        "full_name": "Dr Heni Dridi",
        "role": "medecin",
        "hashed_password": hash_password("medecin123"),
        "is_active": True,
        "permissions": {
            "administration": True,
            "delete_appointment": True,
            "delete_payments": True,
            "export_data": True,
            "reset_data": True,
            "manage_users": True,
            "consultation_read_only": False
        },
        "created_at": datetime.now(),
        "last_login": None
    }
    
    secretaire_user = {
        "username": "secretaire",
        "full_name": "Secrétaire Médicale",
        "role": "secretaire",
        "hashed_password": hash_password("secretaire123"),
        "is_active": True,
        "permissions": {
            "administration": False,
            "delete_appointment": False,
            "delete_payments": False,
            "export_data": False,
            "reset_data": False,
            "manage_users": False,
            "consultation_read_only": True
        },
        "created_at": datetime.now(),
        "last_login": None
    }
    
    # Try to save to MongoDB first
    if USE_MONGODB and db:
        try:
            users_collection = db["users"]
            users_collection.insert_many([medecin_user, secretaire_user])
            print("✅ Default users created in MongoDB")
            return
        except Exception as e:
            print(f"⚠️  MongoDB insert failed: {e}")
    
    # Fallback to in-memory
    emergency_data["users"].extend([medecin_user, secretaire_user])
    print("✅ Default users created in memory")

# Initialize default users on startup
@app.on_event("startup")
async def startup_event():
    create_default_users()
    print("🚀 Emergency server started successfully")

# Routes
@app.get("/")
async def root():
    return {
        "message": "Medical Cabinet - Emergency Mode",
        "status": "online",
        "mode": "MongoDB" if USE_MONGODB else "In-Memory",
        "timestamp": datetime.now().isoformat(),
        "login_info": {
            "username": "medecin",
            "password": "medecin123"
        }
    }

@app.get("/api/status")
async def api_status():
    user_count = 0
    if USE_MONGODB and db:
        try:
            user_count = db["users"].count_documents({})
        except:
            pass
    else:
        user_count = len(emergency_data["users"])
    
    return {
        "api_status": "running",
        "database_mode": "MongoDB" if USE_MONGODB else "In-Memory",
        "users_count": user_count,
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/auth/login")
async def login(login_request: LoginRequest):
    user = get_user(login_request.username)
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    if not verify_password(login_request.password, user["hashed_password"]):
        raise HTTPException(status_code=401, detail="Incorrect password")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=401, detail="User account is disabled")
    
    # Create access token
    access_token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "username": user["username"],
            "full_name": user["full_name"],
            "role": user["role"]
        }
    }

@app.get("/debug/users")
async def debug_users():
    """Debug endpoint to see all users"""
    users = []
    
    if USE_MONGODB and db:
        try:
            users_collection = db["users"]
            users = list(users_collection.find({}, {"hashed_password": 0}))
            for user in users:
                if "_id" in user:
                    user["_id"] = str(user["_id"])
        except Exception as e:
            return {"error": f"MongoDB error: {e}", "fallback": emergency_data["users"]}
    else:
        users = [
            {k: v for k, v in user.items() if k != "hashed_password"}
            for user in emergency_data["users"]
        ]
    
    return {
        "users": users,
        "count": len(users),
        "mode": "MongoDB" if USE_MONGODB else "In-Memory"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "mode": "emergency",
        "database": "connected" if USE_MONGODB else "in-memory",
        "timestamp": datetime.now().isoformat()
    }

if __name__ == "__main__":
    import uvicorn
    print("🚀 Starting Emergency Medical Cabinet Server...")
    uvicorn.run(app, host="0.0.0.0", port=8001)