import json
import os
import uuid
from datetime import datetime
from typing import Optional, Dict, Any

USERS_DB_FILE = "users_database.json"

class UserService:
    """Simple JSON-based user database service"""
    
    @staticmethod
    def _load_users() -> Dict[str, Any]:
        """Load users from JSON file"""
        if not os.path.exists(USERS_DB_FILE):
            return {}
        try:
            with open(USERS_DB_FILE, "r") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading users: {e}")
            return {}
    
    @staticmethod
    def _save_users(users: Dict[str, Any]) -> None:
        """Save users to JSON file"""
        try:
            with open(USERS_DB_FILE, "w") as f:
                json.dump(users, f, indent=2)
        except Exception as e:
            print(f"Error saving users: {e}")
    
    @staticmethod
    def register_user(name: str, phone: Optional[str], shop_id: Optional[str], password: str, age: Optional[int], role: str) -> Dict[str, Any]:
        """Register a new user (phone for regular users, shop_id for admins)"""
        users = UserService._load_users()
        
        # Check if user already exists
        identifier = phone if role == "user" else shop_id
        for user_id, user_data in users.items():
            if role == "user" and user_data.get("phone") == phone:
                return {"success": False, "message": "Phone number already registered"}
            if role == "admin" and user_data.get("shop_id") == shop_id:
                return {"success": False, "message": "Shop ID already registered"}
        
        # Create new user
        user_id = str(uuid.uuid4())
        new_user = {
            "id": user_id,
            "name": name,
            "phone": phone if role == "user" else None,
            "shop_id": shop_id if role == "admin" else None,
            "password": password,  # In production, hash this with bcrypt!
            "age": age,
            "role": role,
            "created_at": datetime.now().isoformat()
        }
        
        users[user_id] = new_user
        UserService._save_users(users)
        
        return {
            "success": True,
            "message": "User registered successfully",
            "user": {
                "id": user_id,
                "name": name,
                "phone": new_user.get("phone"),
                "shop_id": new_user.get("shop_id"),
                "role": role
            }
        }
    
    @staticmethod
    def login_user(phone: Optional[str], shop_id: Optional[str], password: str, role: str) -> Dict[str, Any]:
        """Login a user by phone/shop_id and password"""
        users = UserService._load_users()
        
        identifier = phone if role == "user" else shop_id
        
        for user_id, user_data in users.items():
            # Match by phone for regular users, shop_id for admins
            if role == "user" and user_data.get("phone") == phone and user_data.get("password") == password and user_data.get("role") == "user":
                return {
                    "success": True,
                    "message": "Login successful",
                    "user": {
                        "id": user_id,
                        "name": user_data["name"],
                        "phone": user_data.get("phone"),
                        "role": user_data["role"]
                    }
                }
            elif role == "admin" and user_data.get("shop_id") == shop_id and user_data.get("password") == password and user_data.get("role") == "admin":
                return {
                    "success": True,
                    "message": "Login successful",
                    "user": {
                        "id": user_id,
                        "name": user_data["name"],
                        "shop_id": user_data.get("shop_id"),
                        "role": user_data["role"]
                    }
                }
        
        return {"success": False, "message": "Invalid credentials"}
    
    @staticmethod
    def get_user(user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        users = UserService._load_users()
        return users.get(user_id)
