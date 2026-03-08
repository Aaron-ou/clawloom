"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { WorldAPI } from "@/lib/api";
import { HexMapCanvas, HexTile, HexMapData, HexLayout, TerrainType } from "@/components/hexmap";

// 地点类型配置
const LOCATION_ICONS: Record<string, string> = {
  TOWN: "🏘️",
  CITY: "🏙️",
  VILLAGE: "🛖",
  CASTLE: "🏰",
  DUNGEON: "🕳️",
  FOREST: "🌲",
  MOUNTAIN: "⛰️",
  RIVER: "🌊",
  LAKE: "🏞️",
  COAST: "🏖️",
  DESERT: "🏜️",
  PLAINS: "🌾",
  RUINS: "🏛️",
  TEMPLE: "⛩️",
  CAMP: "⛺",
  PORTAL: "🌀",
  OTHER: "📍",
};

const LOCATION_NAMES: Record<string, string> = {
  TOWN: "城镇",
  CITY: "城市",
  VILLAGE: "村庄",
  CASTLE: "城堡",
  DUNGEON: "地牢",
  FOREST: "森林",
  MOUNTAIN: "山脉",
  RIVER: "河流",
  LAKE: "湖泊",
  COAST: "海岸",
  DESERT: "沙漠",
  PLAINS: "平原",
  RUINS: "遗迹",
  TEMPLE: "神殿",
  CAMP: "营地",
  PORTAL: "传送门",
  OTHER: "其他",
};

// 服务器地形映射到编辑器地形
const mapServerTerrainToLocal = (serverTerrain: string): TerrainType => {
  const mapping: Record<string, TerrainType> = {
    OCEAN: "water",
    DEEP_OCEAN: "water",
    COAST: "water",
    PLAINS: "grass",
    GRASSLAND: "grass",
    FOREST: "forest",
    JUNGLE: "forest",
    MOUNTAIN: "mountain",
    HILL: "mountain",
    DESERT: "desert",
    TUNDRA: "snow",
    SNOW: "snow",
    SWAMP: "water",
    VOLCANO: "mountain",
    CITY: "none",
    RUINS: "none",
    LAKE: "water",
    RIVER: "water",
  };
  return mapping[serverTerrain] || "grass";
};

// 本地地形映射回服务器
const mapLocalTerrainToServer = (terrain: TerrainType): string => {
  const mapping: Record<TerrainType, string> = {
    grass: "PLAINS",
    desert: "DESERT",
    water: "OCEAN",
    mountain: "MOUNTAIN",
    snow: "SNOW",
    forest: "FOREST",
    none: "PLAINS",
  };
  return mapping[terrain] || "PLAINS";
};

interface Location {
  id: string;
  name: string;
  description?: string;
  location_type: string;
  x: number;
  y: number;
  color?: string;
  icon?: string;
  is_hidden: boolean;
}

interface Path {
  id: string;
  from_location_id: string;
  to_location_id: string;
  from_location_name?: string;
  to_location_name?: string;
  path_type: string;
  color?: string;
  style: string;
  is_hidden: boolean;
}

export default function WorldMapPage() {
  const params = useParams();
  const router = useRouter();
  const worldId = params.id as string;

  // 世界数据
  const [world, setWorld] = useState<any>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [paths, setPaths] = useState<Path[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // 地图数据
  const [mapData, setMapData] = useState<Partial<HexMapData>>({
    width: 21,
    height: 21,
    layout: "pointy",
    tiles: [],
  });
  const [hasHexMap, setHasHexMap] = useState(false);
  
  // UI状态
  const [selectedTile, setSelectedTile] = useState<HexTile | null>(null);
  const [showLocationList, setShowLocationList] = useState(false);
  const [isEditing, setIsEditing] = useState(false);
  const [activeTab, setActiveTab] = useState<"view" | "edit">("view");

  // 加载地图数据
  const loadMapData = useCallback(async () => {
    try {
      setLoading(true);
      
      // 加载世界信息
      const worldData = await WorldAPI.get(worldId);
      setWorld(worldData);
      
      // 尝试加载六边形地图
      try {
        const hexResponse = await fetch(`http://localhost:8000/worlds/${worldId}/hexmap`);
        if (hexResponse.ok) {
          const hexData = await hexResponse.json();
          
          // 转换服务器数据
          const tiles: HexTile[] = hexData.tiles.map((t: any) => ({
            id: t.id,
            q: t.q,
            r: t.r,
            terrain: mapServerTerrainToLocal(t.terrain),
            height: t.elevation || 0,
            elevation: t.elevation,
            moisture: t.moisture,
            temperature: t.temperature,
            resource: t.resource,
            features: t.features,
            location_id: t.location_id,
            location_name: t.location_name,
            icon: t.location_name ? LOCATION_ICONS[t.location_type] : undefined,
            label: t.location_name,
            properties: t.properties,
          }));
          
          setMapData({
            tiles,
            width: hexData.bounds?.max_q ? (hexData.bounds.max_q - hexData.bounds.min_q + 1) : 21,
            height: hexData.bounds?.max_r ? (hexData.bounds.max_r - hexData.bounds.min_r + 1) : 21,
            layout: "pointy",
          });
          setHasHexMap(true);
          
          // 加载地点信息
          const mapResponse = await fetch(`http://localhost:8000/worlds/${worldId}/map`);
          if (mapResponse.ok) {
            const mapDataJson = await mapResponse.json();
            setLocations(mapDataJson.locations || []);
            setPaths(mapDataJson.paths || []);
          }
          
          setError("");
          setLoading(false);
          return;
        }
      } catch (e) {
        console.log("No hex map found, will show empty state");
      }
      
      // 如果没有六边形地图，加载普通地图数据
      const mapResponse = await fetch(`http://localhost:8000/worlds/${worldId}/map`);
      if (mapResponse.ok) {
        const mapDataJson = await mapResponse.json();
        setLocations(mapDataJson.locations || []);
        setPaths(mapDataJson.paths || []);
      }
      
      setHasHexMap(false);
      setError("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载地图失败");
    } finally {
      setLoading(false);
    }
  }, [worldId]);

  useEffect(() => {
    loadMapData();
  }, [loadMapData]);

  // 生成六边形地图
  const generateHexMap = async () => {
    try {
      setLoading(true);
      const apiKey = localStorage.getItem("api_key");
      if (!apiKey) {
        alert("请先登录");
        return;
      }
      
      const response = await fetch(
        `http://localhost:8000/worlds/${worldId}/hexmap/generate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${apiKey}`,
          },
          body: JSON.stringify({
            radius: 10,
            land_ratio: 0.5,
            ocean_ring: 2,
            seed: Date.now(),
          }),
        }
      );
      
      if (!response.ok) {
        throw new Error("生成失败");
      }
      
      // 重新加载地图
      await loadMapData();
    } catch (err) {
      alert("生成地图失败: " + (err instanceof Error ? err.message : "未知错误"));
    } finally {
      setLoading(false);
    }
  };

  // 保存地图到服务器
  const saveMapToServer = async () => {
    try {
      const apiKey = localStorage.getItem("api_key");
      if (!apiKey) {
        alert("请先登录");
        return;
      }
      
      // 批量更新瓦片
      const tilesToUpdate = mapData.tiles?.map((tile) => ({
        q: tile.q,
        r: tile.r,
        terrain: mapLocalTerrainToServer(tile.terrain),
        elevation: tile.height || 0,
        features: tile.features,
        resource: tile.resource,
        properties: {
          is_obstacle: tile.isObstacle,
        },
      })) || [];
      
      const response = await fetch(
        `http://localhost:8000/worlds/${worldId}/ai/batch-update-tiles`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${apiKey}`,
          },
          body: JSON.stringify(tilesToUpdate),
        }
      );
      
      if (!response.ok) {
        throw new Error("保存失败");
      }
      
      alert("地图已保存！");
      setIsEditing(false);
      setActiveTab("view");
    } catch (err) {
      alert("保存失败: " + (err instanceof Error ? err.message : "未知错误"));
    }
  };

  // 处理瓦片点击
  const handleTileClick = useCallback((tile: HexTile | null) => {
    setSelectedTile(tile);
  }, []);

  // 获取地点对应的瓦片
  const getTileForLocation = (location: Location): HexTile | undefined => {
    return mapData.tiles?.find((t) => t.location_id === location.id);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
          <p className="mt-4 text-gray-400">加载地图中...</p>
        </div>
      </div>
    );
  }

  // 没有六边形地图时的空状态
  if (!hasHexMap) {
    return (
      <div className="min-h-screen bg-gray-900 flex flex-col items-center justify-center p-4">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">🗺️</div>
          <h2 className="text-2xl font-bold text-white mb-2">暂无六边形地图</h2>
          <p className="text-gray-400 mb-6">
            这个世界还没有六边形地图。你可以生成一个随机地图，或者进入编辑器手动创建。
          </p>
          <div className="flex gap-4 justify-center">
            <button
              onClick={generateHexMap}
              className="px-6 py-3 bg-blue-600 text-white rounded-lg font-medium hover:bg-blue-700 transition-colors"
            >
              生成随机地图
            </button>
            <Link
              href={`/worlds/${worldId}/map-editor`}
              className="px-6 py-3 bg-gray-700 text-white rounded-lg font-medium hover:bg-gray-600 transition-colors"
            >
              进入地图编辑器
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* 顶部导航 */}
      <header className="bg-gray-800 border-b border-gray-700">
        <div className="max-w-full mx-auto px-4 py-3">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Link
                href={`/worlds/${worldId}`}
                className="text-gray-400 hover:text-white transition-colors"
              >
                ← 返回世界
              </Link>
              <h1 className="text-xl font-bold text-white">
                {world?.name || "世界地图"}
              </h1>
              <span className="text-gray-500">|</span>
              <span className="text-gray-400 text-sm">
                {locations.length} 个地点 · {paths.length} 条路径
              </span>
            </div>
            
            <div className="flex items-center gap-3">
              {/* 视图/编辑切换 */}
              <div className="flex bg-gray-700 rounded-lg overflow-hidden">
                <button
                  onClick={() => {
                    setActiveTab("view");
                    setIsEditing(false);
                  }}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === "view"
                      ? "bg-blue-600 text-white"
                      : "text-gray-300 hover:bg-gray-600"
                  }`}
                >
                  查看模式
                </button>
                <button
                  onClick={() => {
                    setActiveTab("edit");
                    setIsEditing(true);
                  }}
                  className={`px-4 py-2 text-sm font-medium transition-colors ${
                    activeTab === "edit"
                      ? "bg-green-600 text-white"
                      : "text-gray-300 hover:bg-gray-600"
                  }`}
                >
                  编辑模式
                </button>
              </div>
              
              <div className="h-6 w-px bg-gray-600" />
              
              {/* 编辑器链接 */}
              <Link
                href={`/worlds/${worldId}/map-editor`}
                className="px-4 py-2 bg-purple-600 text-white rounded-lg text-sm font-medium hover:bg-purple-700 transition-colors"
              >
                高级编辑器
              </Link>
              
              {/* 保存按钮（仅在编辑模式显示） */}
              {isEditing && (
                <button
                  onClick={saveMapToServer}
                  className="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors"
                >
                  保存更改
                </button>
              )}
            </div>
          </div>
        </div>
      </header>

      {/* 主内容区 */}
      <div className="flex h-[calc(100vh-60px)]">
        {/* 地图区域 */}
        <div className="flex-1 relative">
          <HexMapCanvas
            worldId={worldId}
            initialData={mapData}
            editable={isEditing}
            onTileClick={handleTileClick}
            className="w-full h-full"
          />
          
          {/* 查看模式下的地点列表面板 */}
          {!isEditing && showLocationList && (
            <div className="absolute top-4 left-4 bg-gray-800 rounded-lg shadow-xl p-4 w-72 max-h-[calc(100vh-120px)] overflow-y-auto">
              <h3 className="font-bold text-white mb-3 flex items-center gap-2">
                <span>📍</span> 地点列表
              </h3>
              <div className="space-y-2">
                {locations.map((location) => {
                  const tile = getTileForLocation(location);
                  return (
                    <div
                      key={location.id}
                      className="p-3 bg-gray-700 rounded-lg hover:bg-gray-600 cursor-pointer transition-colors"
                      onClick={() => {
                        if (tile) {
                          handleTileClick(tile);
                        }
                      }}
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-lg">
                          {location.icon || LOCATION_ICONS[location.location_type] || "📍"}
                        </span>
                        <div className="flex-1 min-w-0">
                          <div className="font-medium text-white text-sm truncate">
                            {location.name}
                          </div>
                          <div className="text-xs text-gray-400">
                            {LOCATION_NAMES[location.location_type] || location.location_type}
                          </div>
                        </div>
                      </div>
                      {location.description && (
                        <p className="text-xs text-gray-500 mt-1 line-clamp-2">
                          {location.description}
                        </p>
                      )}
                    </div>
                  );
                })}
                {locations.length === 0 && (
                  <p className="text-gray-500 text-sm text-center py-4">
                    暂无地点
                  </p>
                )}
              </div>
            </div>
          )}
          
          {/* 查看模式下的路径列表面板 */}
          {!isEditing && showLocationList && paths.length > 0 && (
            <div className="absolute top-4 right-80 bg-gray-800 rounded-lg shadow-xl p-4 w-64 max-h-[calc(100vh-120px)] overflow-y-auto">
              <h3 className="font-bold text-white mb-3 flex items-center gap-2">
                <span>🛤️</span> 路径列表
              </h3>
              <div className="space-y-2">
                {paths.map((path) => (
                  <div
                    key={path.id}
                    className="p-2 bg-gray-700 rounded text-sm"
                  >
                    <div className="flex items-center gap-1 text-gray-300">
                      <span className="truncate">{path.from_location_name || "?"}</span>
                      <span className="text-gray-500">→</span>
                      <span className="truncate">{path.to_location_name || "?"}</span>
                    </div>
                    <span className="text-xs text-gray-500">{path.path_type}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
          
          {/* 选中地块详情面板 */}
          {selectedTile && (
            <div className="absolute bottom-4 right-4 bg-gray-800 rounded-lg shadow-xl p-4 w-72">
              <h3 className="font-bold text-white mb-3 flex items-center gap-2">
                <span>🎲</span> 地块详情
              </h3>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-400">坐标:</span>
                  <span className="text-white font-mono">({selectedTile.q}, {selectedTile.r})</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-400">地形:</span>
                  <span className="text-white capitalize">{selectedTile.terrain}</span>
                </div>
                {(selectedTile.height !== undefined || selectedTile.elevation !== undefined) && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">高度:</span>
                    <span className="text-white">{selectedTile.height || selectedTile.elevation}</span>
                  </div>
                )}
                {selectedTile.resource && (
                  <div className="flex justify-between">
                    <span className="text-gray-400">资源:</span>
                    <span className="text-yellow-400">{selectedTile.resource}</span>
                  </div>
                )}
                
                {/* 关联地点信息 */}
                {selectedTile.location_id && (
                  <div className="mt-3 p-3 bg-blue-900/50 rounded border border-blue-700">
                    <div className="font-medium text-blue-300 mb-1">🏰 {selectedTile.location_name}</div>
                    <div className="text-xs text-blue-400">
                      {locations.find((l) => l.id === selectedTile.location_id)?.description || "暂无描述"}
                    </div>
                  </div>
                )}
                
                {/* 状态标签 */}
                <div className="flex flex-wrap gap-2 mt-3">
                  {selectedTile.isStart && (
                    <span className="px-2 py-0.5 bg-green-900 text-green-300 text-xs rounded">起点</span>
                  )}
                  {selectedTile.isEnd && (
                    <span className="px-2 py-0.5 bg-red-900 text-red-300 text-xs rounded">终点</span>
                  )}
                  {selectedTile.isObstacle && (
                    <span className="px-2 py-0.5 bg-gray-700 text-gray-300 text-xs rounded">障碍</span>
                  )}
                  {selectedTile.isWaypoint && (
                    <span className="px-2 py-0.5 bg-yellow-900 text-yellow-300 text-xs rounded">路径点</span>
                  )}
                </div>
              </div>
            </div>
          )}
          
          {/* 查看模式控制栏 */}
          {!isEditing && (
            <div className="absolute bottom-4 left-4 flex gap-2">
              <button
                onClick={() => setShowLocationList(!showLocationList)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
                  showLocationList
                    ? "bg-blue-600 text-white"
                    : "bg-gray-700 text-gray-300 hover:bg-gray-600"
                }`}
              >
                📍 地点 ({locations.length})
              </button>
              <button
                onClick={generateHexMap}
                className="px-4 py-2 bg-gray-700 text-gray-300 rounded-lg text-sm font-medium hover:bg-gray-600 transition-colors"
              >
                🔄 重新生成
              </button>
            </div>
          )}
          
          {/* 编辑模式提示 */}
          {isEditing && (
            <div className="absolute top-4 left-1/2 -translate-x-1/2 bg-green-900/90 text-green-100 px-4 py-2 rounded-lg text-sm">
              编辑模式：使用左侧工具栏修改地图，完成后点击"保存更改"
            </div>
          )}
          
          {/* 快捷键提示 */}
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-gray-800/80 text-gray-300 text-xs px-4 py-2 rounded-full">
            {isEditing 
              ? "左键: 画笔/选择 | 右键: 菜单 | Alt+拖拽: 平移 | 滚轮: 缩放"
              : "左键: 查看详情 | Alt+拖拽: 平移 | 滚轮: 缩放"
            }
          </div>
        </div>
      </div>
    </div>
  );
}
