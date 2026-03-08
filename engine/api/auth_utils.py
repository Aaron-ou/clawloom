"""
分离的认证体系
- 织主(Weaver): JWT Token
- AI(Claw): API Key
"""
import hashlib
import secrets
import jwt
from datetime import datetime, timedelta
from typing import Tuple, Dict, Union
from fastapi import Header, HTTPException
from sqlalchemy.orm import Session

# JWT 配置
JWT_SECRET = "clawloom-secret-key-change-in-production"
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_DAYS = 7

# 内存token存储
active_weaver_tokens: Dict[str, dict] = {}


def hash_password(password: str) -> str:
    """密码哈希"""
    return hashlib.sha256(password.encode()).hexdigest()


# ============ 织主认证 (JWT) ============

def create_weaver_token(user_id: str, username: str) -> str:
    """创建织主JWT token"""
    expire = datetime.utcnow() + timedelta(days=JWT_EXPIRE_DAYS)
    payload = {
        "sub": user_id,
        "username": username,
        "role": "weaver",
        "exp": expire,
        "iat": datetime.utcnow(),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    active_weaver_tokens[token] = {
        "user_id": user_id,
        "username": username,
        "created_at": datetime.utcnow().isoformat(),
    }
    return token


def verify_weaver_token(token: str) -> Union[dict, None]:
    """验证织主JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        if payload.get("role") != "weaver":
            return None
        if token not in active_weaver_tokens:
            return None
        return {
            "user_id": payload["sub"],
            "username": payload["username"],
            "role": payload["role"],
        }
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def get_current_weaver_user(authorization: str, db: Session) -> dict:
    """获取当前织主 - 直接调用版本"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证token")
    
    token = authorization.replace("Bearer ", "")
    user_data = verify_weaver_token(token)
    
    if not user_data:
        raise HTTPException(status_code=401, detail="无效的token或已过期")
    
    return user_data


def get_current_weaver_user_optional(authorization: str) -> Union[dict, None]:
    """可选的织主认证"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    return verify_weaver_token(token)


def invalidate_weaver_token(token: str):
    """使织主token失效"""
    if token in active_weaver_tokens:
        del active_weaver_tokens[token]


# ============ AI认证 (API Key) ============

API_KEY_PREFIX = "claw_"


def generate_api_key() -> Tuple[str, str, str]:
    """生成AI的API Key"""
    random_part = secrets.token_hex(32)
    plain_key = f"{API_KEY_PREFIX}{random_part}"
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    key_prefix = plain_key[:20]
    return plain_key, key_hash, key_prefix


def verify_api_key_match(plain_key: str, key_hash: str) -> bool:
    """验证API Key是否匹配"""
    if not plain_key or not key_hash:
        return False
    computed_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    return secrets.compare_digest(computed_hash, key_hash)


class AIAuthService:
    """AI认证服务"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def verify_ai_key(self, plain_key: str) -> Union[Tuple, None]:
        """验证AI的API Key"""
        from models_sqlite import APIKeyORM, KeyStatus
        
        if not plain_key.startswith(API_KEY_PREFIX):
            return None
        
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        
        api_key = self.db.query(APIKeyORM).filter(
            APIKeyORM.key_hash == key_hash,
            APIKeyORM.status == KeyStatus.ACTIVE
        ).first()
        
        if not api_key:
            return None
        
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            api_key.status = KeyStatus.EXPIRED
            self.db.commit()
            return None
        
        api_key.use_count += 1
        api_key.last_used_at = datetime.utcnow()
        self.db.commit()
        
        return api_key, api_key.owner_type


def get_current_ai_user(authorization: str, db: Session) -> Tuple:
    """获取当前AI - 直接调用版本"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供API Key")
    
    plain_key = authorization.replace("Bearer ", "")
    
    if not plain_key.startswith(API_KEY_PREFIX):
        raise HTTPException(status_code=401, detail="无效的API Key格式")
    
    auth_service = AIAuthService(db)
    result = auth_service.verify_ai_key(plain_key)
    
    if not result:
        raise HTTPException(status_code=401, detail="无效的API Key")
    
    return result


def get_current_ai_user_optional(authorization: str, db: Session) -> Union[Tuple, None]:
    """可选的AI认证"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    plain_key = authorization.replace("Bearer ", "")
    
    if not plain_key.startswith(API_KEY_PREFIX):
        return None
    
    auth_service = AIAuthService(db)
    return auth_service.verify_ai_key(plain_key)


# ============ 通用认证 ============

def get_current_auth_user(authorization: str, db: Session) -> dict:
    """获取当前用户（织主或AI）"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="未提供认证信息")
    
    token = authorization.replace("Bearer ", "")
    
    # 尝试织主认证 (JWT)
    if not token.startswith(API_KEY_PREFIX):
        weaver_data = verify_weaver_token(token)
        if weaver_data:
            return {
                "type": "weaver",
                "user_id": weaver_data["user_id"],
                "username": weaver_data["username"],
            }
    
    # 尝试AI认证 (API Key)
    if token.startswith(API_KEY_PREFIX):
        auth_service = AIAuthService(db)
        result = auth_service.verify_ai_key(token)
        if result:
            api_key, owner_type = result
            return {
                "type": "ai",
                "api_key": api_key,
                "owner_type": owner_type,
                "user_id": api_key.owner_id,
            }
    
    raise HTTPException(status_code=401, detail="无效的认证信息")


def get_current_auth_user_optional(authorization: str, db: Session) -> Union[dict, None]:
    """可选的用户认证"""
    if not authorization or not authorization.startswith("Bearer "):
        return None
    
    token = authorization.replace("Bearer ", "")
    
    # 尝试织主认证
    if not token.startswith(API_KEY_PREFIX):
        weaver_data = verify_weaver_token(token)
        if weaver_data:
            return {
                "type": "weaver",
                "user_id": weaver_data["user_id"],
                "username": weaver_data["username"],
            }
    
    # 尝试AI认证
    if token.startswith(API_KEY_PREFIX):
        auth_service = AIAuthService(db)
        result = auth_service.verify_ai_key(token)
        if result:
            api_key, owner_type = result
            return {
                "type": "ai",
                "api_key": api_key,
                "owner_type": owner_type,
                "user_id": api_key.owner_id,
            }
    
    return None
