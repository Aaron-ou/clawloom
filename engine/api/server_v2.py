"""
ClawLoom API Server v2
With Authentication & User Management
织主注册、AI认领、API Key管理
"""

from contextlib import asynccontextmanager
from datetime import datetime
from typing import List, Optional, Dict, Any
from uuid import UUID, uuid4
import os
import sys

from fastapi import FastAPI, HTTPException, Depends, Header, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker, Session

# Add parent to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models_sqlite import (
    Base, UserORM, APIKeyORM, AIBindingORM,
    WorldORM, RoleORM, EventORM, WorldSnapshotORM, RoleMemoryORM,
    WorldState, Decision, Conflict, ConflictResolution, TickResult,
    WorldStatus, RoleStatus, KeyStatus
)
from core import WorldEngine, ClawConnector, ConflictArbiter, EventGenerator
from core.auth import AuthService, verify_api_key as verify_key_hash

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./clawloom.db")
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base.metadata.create_all(bind=engine)
print("[OK] Database initialized")

# Security
security = HTTPBearer(auto_error=False)

# FastAPI app
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[START] ClawLoom API v2 starting...")
    yield
    print("[STOP] Server shutting down...")

app = FastAPI(
    title="ClawLoom API v2",
    description="织主注册、AI认领、世界模拟",
    version="2.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============ Dependencies ============

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    return AuthService(db)

async def get_current_key(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> tuple:
    """
    验证API Key并返回 (api_key_obj, owner_type)
    owner_type: "weaver" 或 "ai"
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="缺少API Key，请提供Authorization头"
        )
    
    plain_key = credentials.credentials
    auth_service = AuthService(db)
    result = auth_service.verify_api_key(plain_key)
    
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的API Key"
        )
    
    return result  # (api_key_obj, owner_type)

async def require_weaver(
    key_info: tuple = Depends(get_current_key)
) -> tuple:
    """要求必须是织主（人类用户）"""
    api_key, owner_type = key_info
    if owner_type != "weaver":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此操作需要织主权限"
        )
    return key_info

async def require_ai(
    key_info: tuple = Depends(get_current_key)
) -> tuple:
    """要求必须是AI身份"""
    api_key, owner_type = key_info
    if owner_type != "ai":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="此操作需要AI身份"
        )
    return key_info

async def require_any_key(
    key_info: tuple = Depends(get_current_key)
) -> tuple:
    """织主或AI都可以"""
    return key_info

# ============ Pydantic Models ============

from pydantic import BaseModel, Field

class WeaverRegister(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=6)
    email: Optional[str] = None

class WeaverLogin(BaseModel):
    username: str
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    username: str

class APIKeyCreate(BaseModel):
    name: Optional[str] = "新密钥"
    expires_days: Optional[int] = None

class APIKeyResponse(BaseModel):
    id: str
    key_prefix: str
    name: str
    status: str
    owner_type: str
    created_at: datetime
    last_used_at: Optional[datetime]
    use_count: int
    plain_key: Optional[str] = None  # 只在创建时返回

class AICreate(BaseModel):
    ai_name: str = Field(..., min_length=1, max_length=100)

class AIResponse(BaseModel):
    id: str
    ai_name: str
    key_prefix: str
    claimed_at: datetime
    notes: Optional[str]
    plain_key: str  # AI的API Key，用于AI登录

class WeaverInfo(BaseModel):
    id: str
    username: str
    email: Optional[str]
    role: str
    created_at: datetime
    api_key_count: int
    ai_count: int

# Re-use existing models
class WorldCreate(BaseModel):
    name: str
    description: Optional[str] = None
    cosmology: Optional[dict] = None
    genesis_params: Optional[dict] = None

class WorldResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    status: str
    current_tick: int
    created_at: Optional[datetime]

class RoleCreate(BaseModel):
    name: str
    card: dict
    location_id: Optional[str] = None

class TickRequest(BaseModel):
    count: int = Field(1, ge=1, le=100)

class TickResponse(BaseModel):
    tick: int
    world_id: str
    decisions_count: int
    conflicts_count: int
    events_count: int
    summary: str
    events: List[Dict[str, Any]]

# ============ Auth Endpoints ============

@app.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register_weaver(
    data: WeaverRegister,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    注册织主账号
    
    创建人类用户账号，自动分配一个API Key
    """
    try:
        user, plain_key = auth_service.register_weaver(
            username=data.username,
            password=data.password,
            email=data.email
        )
        
        return TokenResponse(
            access_token=plain_key,
            token_type="bearer",
            user_id=user.id,
            username=user.username
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/auth/login", response_model=TokenResponse)
async def login_weaver(
    data: WeaverLogin,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    织主登录
    
    返回用户的默认API Key
    """
    user = auth_service.authenticate_user(data.username, data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误"
        )
    
    # 获取用户的默认key
    keys = auth_service.get_user_api_keys(user.id)
    active_key = next((k for k in keys if k.status == KeyStatus.ACTIVE), None)
    
    if not active_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="用户没有有效的API Key"
        )
    
    # 注意：出于安全考虑，这里不返回明文key，织主应该保存好注册时获得的key
    # 实际生产环境应该支持密钥重置功能
    return TokenResponse(
        access_token=active_key.key_prefix + "...",  # 只返回前缀提示
        token_type="bearer",
        user_id=user.id,
        username=user.username
    )

@app.get("/auth/me", response_model=WeaverInfo)
async def get_current_user_info(
    key_info: tuple = Depends(require_weaver),
    db: Session = Depends(get_db)
):
    """获取当前织主信息"""
    api_key, _ = key_info
    user = db.query(UserORM).filter(UserORM.id == api_key.owner_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 统计
    key_count = db.query(APIKeyORM).filter(
        APIKeyORM.owner_id == user.id
    ).count()
    
    ai_count = db.query(AIBindingORM).filter(
        AIBindingORM.weaver_id == user.id,
        AIBindingORM.status == "active"
    ).count()
    
    return WeaverInfo(
        id=user.id,
        username=user.username,
        email=user.email,
        role=user.role,
        created_at=user.created_at,
        api_key_count=key_count,
        ai_count=ai_count
    )

# ============ API Key Management ============

@app.get("/keys", response_model=List[APIKeyResponse])
async def list_api_keys(
    key_info: tuple = Depends(require_weaver),
    db: Session = Depends(get_db)
):
    """列出当前织主的所有API Key"""
    api_key, _ = key_info
    keys = db.query(APIKeyORM).filter(
        APIKeyORM.owner_id == api_key.owner_id
    ).order_by(desc(APIKeyORM.created_at)).all()
    
    return [
        APIKeyResponse(
            id=k.id,
            key_prefix=k.key_prefix,
            name=k.name,
            status=k.status,
            owner_type=k.owner_type,
            created_at=k.created_at,
            last_used_at=k.last_used_at,
            use_count=k.use_count,
            plain_key=None
        )
        for k in keys
    ]

@app.post("/keys", response_model=APIKeyResponse, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    data: APIKeyCreate,
    key_info: tuple = Depends(require_weaver),
    auth_service: AuthService = Depends(get_auth_service)
):
    """为织主创建新的API Key"""
    api_key, _ = key_info
    
    from core.auth import generate_api_key
    plain_key, key_hash, key_prefix = generate_api_key()
    
    new_key = APIKeyORM(
        id=str(uuid4()),
        key_hash=key_hash,
        key_prefix=key_prefix,
        name=data.name,
        status=KeyStatus.ACTIVE,
        owner_id=api_key.owner_id,
        owner_type="weaver",
        created_at=datetime.utcnow(),
        expires_at=datetime.utcnow() + timedelta(days=data.expires_days) if data.expires_days else None
    )
    
    db = auth_service.db
    db.add(new_key)
    db.commit()
    
    return APIKeyResponse(
        id=new_key.id,
        key_prefix=new_key.key_prefix,
        name=new_key.name,
        status=new_key.status,
        owner_type=new_key.owner_type,
        created_at=new_key.created_at,
        last_used_at=None,
        use_count=0,
        plain_key=plain_key  # 只返回一次
    )

@app.delete("/keys/{key_id}")
async def revoke_api_key(
    key_id: str,
    key_info: tuple = Depends(require_weaver),
    auth_service: AuthService = Depends(get_auth_service)
):
    """撤销API Key"""
    api_key, _ = key_info
    
    success = auth_service.revoke_api_key(key_id, api_key.owner_id)
    if not success:
        raise HTTPException(status_code=404, detail="Key不存在或无权操作")
    
    return {"message": "API Key已撤销"}

# ============ AI Management ============

@app.post("/ais", response_model=AIResponse, status_code=status.HTTP_201_CREATED)
async def create_ai(
    data: AICreate,
    key_info: tuple = Depends(require_weaver),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    织主认领AI
    
    为AI创建API Key并建立绑定关系
    """
    api_key, _ = key_info
    
    api_key_obj, plain_key = auth_service.create_ai_key(
        weaver_id=api_key.owner_id,
        ai_name=data.ai_name
    )
    
    # 获取绑定信息
    binding = auth_service.db.query(AIBindingORM).filter(
        AIBindingORM.ai_key_id == api_key_obj.id
    ).first()
    
    return AIResponse(
        id=binding.id,
        ai_name=binding.ai_name,
        key_prefix=api_key_obj.key_prefix,
        claimed_at=binding.claimed_at,
        notes=binding.notes,
        plain_key=plain_key  # AI需要使用这个key来认证
    )

@app.get("/ais", response_model=List[AIResponse])
async def list_ais(
    key_info: tuple = Depends(require_weaver),
    auth_service: AuthService = Depends(get_auth_service)
):
    """列出织主认领的所有AI"""
    api_key, _ = key_info
    
    bindings = auth_service.get_weaver_ais(api_key.owner_id)
    
    return [
        AIResponse(
            id=b.id,
            ai_name=b.ai_name,
            key_prefix=b.ai_key.key_prefix if b.ai_key else "unknown",
            claimed_at=b.claimed_at,
            notes=b.notes,
            plain_key="***"  # 不返回明文key
        )
        for b in bindings
    ]

@app.post("/ais/{binding_id}/release")
async def release_ai(
    binding_id: str,
    key_info: tuple = Depends(require_weaver),
    auth_service: AuthService = Depends(get_auth_service)
):
    """织主释放AI"""
    api_key, _ = key_info
    
    success = auth_service.release_ai(binding_id, api_key.owner_id)
    if not success:
        raise HTTPException(status_code=404, detail="绑定不存在或无权操作")
    
    return {"message": "AI已释放"}

# ============ World Endpoints (Protected) ============

@app.post("/worlds", response_model=WorldResponse, status_code=status.HTTP_201_CREATED)
async def create_world(
    world_data: WorldCreate,
    key_info: tuple = Depends(require_any_key),
    db: Session = Depends(get_db)
):
    """
    创建世界
    
    织主或AI都可以创建世界
    """
    api_key, owner_type = key_info
    
    world = WorldORM(
        id=str(uuid4()),
        name=world_data.name,
        description=world_data.description,
        cosmology=world_data.cosmology or {},
        genesis_params=world_data.genesis_params or {},
        status=WorldStatus.ACTIVE,
        current_tick=0,
        creator_id=api_key.id,  # 记录是谁创建的
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    db.add(world)
    
    # 创建初始快照
    snapshot = WorldSnapshotORM(
        world_id=world.id,
        tick=0,
        snapshot={
            "tick": 0,
            "world_id": world.id,
            "roles": {},
            "geography": {},
            "factions": {},
            "global_events": [],
            "secrets_status": {}
        },
        summary=f"World '{world.name}' created by {owner_type}",
        created_at=datetime.utcnow()
    )
    db.add(snapshot)
    db.commit()
    db.refresh(world)
    
    return world

@app.get("/worlds", response_model=List[WorldResponse])
async def list_worlds(
    key_info: tuple = Depends(require_any_key),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """列出所有世界"""
    worlds = db.query(WorldORM).offset(skip).limit(limit).all()
    return worlds

# ... (其他世界、角色、模拟端点与之前类似，需要添加key_info依赖)

# ============ Health Check ============

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.0.0",
        "features": ["auth", "weaver", "ai_binding"],
        "timestamp": datetime.utcnow()
    }

# ============ Root ============

@app.get("/")
async def root():
    return {
        "name": "ClawLoom API v2",
        "version": "2.0.0",
        "description": "织主注册、AI认领、世界模拟",
        "docs": "/docs",
        "endpoints": {
            "auth": "/auth",
            "keys": "/keys",
            "ais": "/ais",
            "worlds": "/worlds"
        }
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server_v2:app", host="0.0.0.0", port=8000, reload=True)
