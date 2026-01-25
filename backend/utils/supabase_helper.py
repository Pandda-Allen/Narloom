import os
import json
from flask import request, jsonify, current_app


def sync_supabase_user_to_local(user_data: dict) -> dict:
    """将Supabase用户数据同步到本地数据库（模拟实现）"""
    # 这里可以添加实际的数据库同步逻辑
    current_app.logger.info(f"Syncing user {user_data['email']} to local database.")
    
    # 模拟本地用户数据
    local_user = {
        "id": user_data["id"],
        "email": user_data["email"],
        "aud": user_data["aud"],
        "role": user_data["role"],
        "phone": user_data["phone"],
        "created_at": user_data["created_at"]
    }
    
    return local_user