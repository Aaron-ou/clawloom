"""
Authentication & Authorization Module
处理API Key生成、用户认证、权限控制
"""

import hashlib
import secrets
import re
from datetime import datetime, timedelta
from typing import Optional, Tuple
from uuid import uuid4

try:
    from models_sqlite import UserORM, APIKeyORM, AIBindingORM, KeyStatus
except ImportError:
    from models import UserORM, APIKeyORM, AIBindingORM, KeyStatus


# ============ API Key 管理 ============

API_KEY_PREFIX = "claw_"
API_KEY_LENGTH = 32


def generate_api_key() -> Tuple[str, str]:
    """
    生成新的API Key
    
    Returns:
        (plain_key, key_hash) - 明文key用于一次性展示，hash用于存储
    """
    # 生成随机密钥
    random_part = secrets.token_hex(API_KEY_LENGTH)
    plain_key = f"{API_KEY_PREFIX}{random_part}"
    
    # 计算hash
    key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    
    # 生成前缀用于识别
    key_prefix = plain_key[:20]  # claw_ + 前14位
    
    return plain_key, key_hash, key_prefix


def verify_api_key(plain_key: str, key_hash: str) -> bool:
    """验证API Key"""
    if not plain_key or not key_hash:
        return False
    computed_hash = hashlib.sha256(plain_key.encode()).hexdigest()
    return secrets.compare_digest(computed_hash, key_hash)


def hash_password(password: str) -> str:
    """密码哈希（简单实现，生产环境应使用bcrypt等）"""
    # 添加salt
    salt = secrets.token_hex(16)
    hashed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
    return f"{salt}${hashed.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """验证密码"""
    try:
        salt, stored_hash = hashed.split('$')
        computed = hashlib.pbkdf2_hmac('sha256', password.encode(), salt.encode(), 100000)
        return secrets.compare_digest(computed.hex(), stored_hash)
    except:
        return False


# ============ 用户认证 ============

class AuthService:
    """认证服务"""
    
    def __init__(self, db_session):
        self.db = db_session
    
    # ----- 织主（人类用户）管理 -----
    
    def register_weaver(self, username: str, password: str, email: Optional[str] = None) -> Tuple[UserORM, str]:
        """
        注册织主账号
        
        Returns:
            (user, plain_api_key) - 用户对象和API密钥
        """
        from sqlalchemy.exc import IntegrityError
        
        # 检查用户名格式
        if not re.match(r'^[a-zA-Z0-9_-]{3,50}$', username):
            raise ValueError("用户名必须是3-50位字母、数字、下划线或横线")
        
        # 检查密码强度
        if len(password) < 6:
            raise ValueError("密码至少需要6位")
        
        # 创建用户
        user = UserORM(
            id=str(uuid4()),
            username=username,
            email=email,
            hashed_password=hash_password(password),
            role="weaver",
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        try:
            self.db.add(user)
            self.db.flush()  # 获取ID但不提交
            
            # 为用户创建默认API Key
            plain_key, key_hash, key_prefix = generate_api_key()
            api_key = APIKeyORM(
                id=str(uuid4()),
                key_hash=key_hash,
                key_prefix=key_prefix,
                name="默认密钥",
                status=KeyStatus.ACTIVE,
                owner_id=user.id,
                owner_type="weaver",
                created_at=datetime.utcnow(),
                expires_at=None
            )
            
            self.db.add(api_key)
            self.db.commit()
            
            return user, plain_key
            
        except IntegrityError:
            self.db.rollback()
            raise ValueError("用户名已存在")
    
    def authenticate_user(self, username: str, password: str) -> Optional[UserORM]:
        """验证用户登录"""
        user = self.db.query(UserORM).filter(
            UserORM.username == username,
            UserORM.is_active == True
        ).first()
        
        if user and verify_password(password, user.hashed_password):
            return user
        return None
    
    # ----- AI Key 管理 -----
    
    def create_ai_key(self, weaver_id: str, ai_name: str) -> Tuple[APIKeyORM, str]:
        """
        织主为AI创建API Key
        
        Args:
            weaver_id: 织主用户ID
            ai_name: AI的自我命名
            
        Returns:
            (api_key_obj, plain_key) - API Key对象和明文密钥
        """
        # 生成密钥
        plain_key, key_hash, key_prefix = generate_api_key()
        
        # 创建API Key记录
        api_key = APIKeyORM(
            id=str(uuid4()),
            key_hash=key_hash,
            key_prefix=key_prefix,
            name=f"AI: {ai_name}",
            status=KeyStatus.ACTIVE,
            owner_id=weaver_id,  # 归属于织主
            owner_type="ai",      # 但类型是AI
            created_at=datetime.utcnow()
        )
        
        self.db.add(api_key)
        self.db.flush()
        
        # 创建绑定关系
        binding = AIBindingORM(
            id=str(uuid4()),
            weaver_id=weaver_id,
            ai_name=ai_name,
            ai_key_id=api_key.id,
            status="active",
            claimed_at=datetime.utcnow()
        )
        
        self.db.add(binding)
        self.db.commit()
        
        return api_key, plain_key
    
    def verify_api_key(self, plain_key: str) -> Optional[Tuple[APIKeyORM, str]]:
        """
        验证API Key
        
        Returns:
            (api_key_obj, owner_type) 或 None
            owner_type: "weaver" 或 "ai"
        """
        if not plain_key.startswith(API_KEY_PREFIX):
            return None
        
        key_hash = hashlib.sha256(plain_key.encode()).hexdigest()
        
        api_key = self.db.query(APIKeyORM).filter(
            APIKeyORM.key_hash == key_hash,
            APIKeyORM.status == KeyStatus.ACTIVE
        ).first()
        
        if not api_key:
            return None
        
        # 检查是否过期
        if api_key.expires_at and api_key.expires_at < datetime.utcnow():
            api_key.status = KeyStatus.EXPIRED
            self.db.commit()
            return None
        
        # 更新使用统计
        api_key.last_used_at = datetime.utcnow()
        api_key.use_count += 1
        self.db.commit()
        
        return api_key, api_key.owner_type
    
    def get_user_api_keys(self, user_id: str) -> list:
        """获取用户的所有API Key"""
        return self.db.query(APIKeyORM).filter(
            APIKeyORM.owner_id == user_id
        ).order_by(APIKeyORM.created_at.desc()).all()
    
    def revoke_api_key(self, key_id: str, user_id: str) -> bool:
        """撤销API Key"""
        api_key = self.db.query(APIKeyORM).filter(
            APIKeyORM.id == key_id,
            APIKeyORM.owner_id == user_id
        ).first()
        
        if api_key:
            api_key.status = KeyStatus.REVOKED
            self.db.commit()
            return True
        return False
    
    # ----- AI 绑定管理 -----
    
    def get_weaver_ais(self, weaver_id: str) -> list:
        """获取织主认领的所有AI"""
        return self.db.query(AIBindingORM).filter(
            AIBindingORM.weaver_id == weaver_id,
            AIBindingORM.status == "active"
        ).all()
    
    def release_ai(self, binding_id: str, weaver_id: str) -> bool:
        """织主释放AI"""
        binding = self.db.query(AIBindingORM).filter(
            AIBindingORM.id == binding_id,
            AIBindingORM.weaver_id == weaver_id
        ).first()
        
        if binding:
            binding.status = "released"
            binding.released_at = datetime.utcnow()
            
            # 同时撤销AI的key
            if binding.ai_key:
                binding.ai_key.status = KeyStatus.REVOKED
            
            self.db.commit()
            return True
        return False


# ============ 装饰器 ============

def require_auth(service_func):
    """需要认证的装饰器（在FastAPI端点中使用）"""
    async def wrapper(*args, **kwargs):
        # 实际实现在API层的依赖注入中
        return await service_func(*args, **kwargs)
    return wrapper
