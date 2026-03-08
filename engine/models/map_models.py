"""
地图相关的Pydantic模型
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class LocationType(str, Enum):
    TOWN = "TOWN"
    CITY = "CITY"
    VILLAGE = "VILLAGE"
    CASTLE = "CASTLE"
    DUNGEON = "DUNGEON"
    FOREST = "FOREST"
    MOUNTAIN = "MOUNTAIN"
    RIVER = "RIVER"
    LAKE = "LAKE"
    COAST = "COAST"
    DESERT = "DESERT"
    PLAINS = "PLAINS"
    RUINS = "RUINS"
    TEMPLE = "TEMPLE"
    CAMP = "CAMP"
    PORTAL = "PORTAL"
    OTHER = "OTHER"


class PathType(str, Enum):
    ROAD = "ROAD"
    TRAIL = "TRAIL"
    RIVER_PATH = "RIVER"
    SEA_ROUTE = "SEA"
    SECRET = "SECRET"
    PORTAL = "PORTAL"


# ============ Location Models ============

class LocationCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    location_type: LocationType = LocationType.OTHER
    x: int = 0
    y: int = 0
    zoom_level: int = Field(1, ge=1, le=3)
    properties: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    icon: Optional[str] = None
    color: Optional[str] = None
    is_hidden: bool = False


class LocationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    location_type: Optional[LocationType] = None
    x: Optional[int] = None
    y: Optional[int] = None
    zoom_level: Optional[int] = Field(None, ge=1, le=3)
    properties: Optional[Dict[str, Any]] = None
    tags: Optional[List[str]] = None
    icon: Optional[str] = None
    color: Optional[str] = None
    is_hidden: Optional[bool] = None
    is_discovered: Optional[bool] = None


class LocationResponse(BaseModel):
    id: str
    world_id: str
    name: str
    description: Optional[str]
    location_type: str
    x: int
    y: int
    zoom_level: int
    properties: Dict[str, Any]
    tags: List[str]
    icon: Optional[str]
    color: Optional[str]
    is_discovered: bool
    is_hidden: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Path Models ============

class PathCreate(BaseModel):
    from_location_id: str
    to_location_id: str
    path_type: PathType = PathType.TRAIL
    name: Optional[str] = None
    description: Optional[str] = None
    distance: Optional[int] = None
    travel_difficulty: int = Field(1, ge=1, le=10)
    travel_time: Optional[int] = None
    is_hidden: bool = False
    color: Optional[str] = None
    style: str = "solid"
    properties: Dict[str, Any] = Field(default_factory=dict)


class PathUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    path_type: Optional[PathType] = None
    distance: Optional[int] = None
    travel_difficulty: Optional[int] = Field(None, ge=1, le=10)
    travel_time: Optional[int] = None
    is_hidden: Optional[bool] = None
    is_blocked: Optional[bool] = None
    block_reason: Optional[str] = None
    color: Optional[str] = None
    style: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class PathResponse(BaseModel):
    id: str
    world_id: str
    from_location_id: str
    to_location_id: str
    from_location_name: Optional[str] = None
    to_location_name: Optional[str] = None
    path_type: str
    name: Optional[str]
    description: Optional[str]
    distance: Optional[int]
    travel_difficulty: int
    travel_time: Optional[int]
    is_hidden: bool
    is_blocked: bool
    block_reason: Optional[str]
    color: Optional[str]
    style: str
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Region Models ============

class Point(BaseModel):
    x: int
    y: int


class RegionCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    boundary: List[Point] = Field(default_factory=list)
    region_type: str = "area"
    properties: Dict[str, Any] = Field(default_factory=dict)
    color: Optional[str] = None
    border_color: Optional[str] = None


class RegionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    boundary: Optional[List[Point]] = None
    region_type: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None
    color: Optional[str] = None
    border_color: Optional[str] = None


class RegionResponse(BaseModel):
    id: str
    world_id: str
    name: str
    description: Optional[str]
    boundary: List[Point]
    region_type: str
    properties: Dict[str, Any]
    color: Optional[str]
    border_color: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ============ Map Data Models ============

class MapDataResponse(BaseModel):
    """完整地图数据（用于前端一次性加载）"""
    world_id: str
    locations: List[LocationResponse]
    paths: List[PathResponse]
    regions: List[RegionResponse]
    bounds: Dict[str, int]  # {min_x, max_x, min_y, max_y}


class LocationBrief(BaseModel):
    """简化版地点信息（用于列表）"""
    id: str
    name: str
    location_type: str
    x: int
    y: int


class MapSearchResult(BaseModel):
    locations: List[LocationBrief]
    total: int


# ============ Hex Tile Map Models ============

class TerrainType(str, Enum):
    """地形类型 - 用于六边形瓦片地图"""
    OCEAN = "OCEAN"           # 海洋 - 蓝色
    DEEP_OCEAN = "DEEP_OCEAN" # 深海 - 深蓝色
    COAST = "COAST"           # 海岸 - 浅蓝色
    PLAINS = "PLAINS"         # 平原 - 浅绿色
    GRASSLAND = "GRASSLAND"   # 草原 - 绿色
    FOREST = "FOREST"         # 森林 - 深绿色
    JUNGLE = "JUNGLE"         # 丛林 - 热带绿
    MOUNTAIN = "MOUNTAIN"     # 山脉 - 灰色/棕色
    HILL = "HILL"             # 丘陵 - 浅棕
    DESERT = "DESERT"         # 沙漠 - 黄色
    TUNDRA = "TUNDRA"         # 苔原 - 灰白色
    SNOW = "SNOW"             # 雪地 - 白色
    SWAMP = "SWAMP"           # 沼泽 - 暗绿色
    VOLCANO = "VOLCANO"       # 火山 - 红色/黑色
    CITY = "CITY"             # 城市 - 特殊标记
    RUINS = "RUINS"           # 遗迹 - 特殊标记
    LAKE = "LAKE"             # 湖泊 - 蓝色
    RIVER = "RIVER"           # 河流 - 浅蓝色


class HexTileCreate(BaseModel):
    """创建六边形瓦片"""
    q: int = Field(..., description="轴向坐标q（列）")
    r: int = Field(..., description="轴向坐标r（行）")
    terrain: TerrainType = TerrainType.OCEAN
    elevation: int = Field(0, ge=-5, le=10, description="海拔高度")
    moisture: int = Field(50, ge=0, le=100, description="湿度")
    temperature: int = Field(20, ge=-30, le=50, description="温度")
    features: List[str] = Field(default_factory=list, description="特殊特征，如['forest', 'mountain']")
    resource: Optional[str] = Field(None, description="资源类型")
    location_id: Optional[str] = Field(None, description="关联的地点ID")
    properties: Dict[str, Any] = Field(default_factory=dict)


class HexTileUpdate(BaseModel):
    """更新六边形瓦片"""
    terrain: Optional[TerrainType] = None
    elevation: Optional[int] = Field(None, ge=-5, le=10)
    moisture: Optional[int] = Field(None, ge=0, le=100)
    temperature: Optional[int] = Field(None, ge=-30, le=50)
    features: Optional[List[str]] = None
    resource: Optional[str] = None
    location_id: Optional[str] = None
    properties: Optional[Dict[str, Any]] = None


class HexTileResponse(BaseModel):
    """六边形瓦片响应"""
    id: str
    world_id: str
    q: int
    r: int
    # 计算坐标（用于渲染）
    x: float
    y: float
    terrain: str
    elevation: int
    moisture: int
    temperature: int
    features: List[str]
    resource: Optional[str]
    location_id: Optional[str]
    location_name: Optional[str] = None
    properties: Dict[str, Any]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class HexMapDataResponse(BaseModel):
    """六边形地图完整数据"""
    world_id: str
    tiles: List[HexTileResponse]
    bounds: Dict[str, int]  # {min_q, max_q, min_r, max_r}
    center: Dict[str, float]  # {q, r}
    radius: int  # 地图半径（格数）


class HexMapGenerateRequest(BaseModel):
    """生成六边形地图请求"""
    radius: int = Field(10, ge=5, le=50, description="地图半径（格数）")
    seed: Optional[int] = Field(None, description="随机种子")
    land_ratio: float = Field(0.4, ge=0.1, le=0.8, description="陆地比例")
    ocean_ring: int = Field(2, ge=0, le=5, description="海洋环宽度（确保地图边缘是海洋）")
