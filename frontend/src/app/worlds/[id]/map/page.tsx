"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { WorldAPI } from "@/lib/api";
import { HexMap } from "@/components/hexmap";

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

// 本地HexTile类型
interface HexTile {
  id: string;
  q: number;
  r: number;
  terrain: string;
  location_id?: string;
  location_name?: string;
  elevation?: number;
  moisture?: number;
  temperature?: number;
  height?: number;
  resource?: string;
  features?: string[];
  properties?: Record<string, any>;
}

interface Region {
  id: string;
  name: string;
  boundary: { x: number; y: number }[];
  color?: string;
  border_color?: string;
}

export default function WorldMapPage() {
  const params = useParams();
  const worldId = params.id as string;

  const [world, setWorld] = useState<any>(null);
  const [locations, setLocations] = useState<Location[]>([]);
  const [paths, setPaths] = useState<Path[]>([]);
  const [regions, setRegions] = useState<Region[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedTile, setSelectedTile] = useState<HexTile | null>(null);
  const [showLocationList, setShowLocationList] = useState(false);

  const loadMapData = useCallback(async () => {
    try {
      setLoading(true);
      const [worldData, mapData] = await Promise.all([
        WorldAPI.get(worldId),
        fetch(`http://localhost:8000/worlds/${worldId}/map`).then((r) =>
          r.json()
        ),
      ]);

      setWorld(worldData);
      setLocations(mapData.locations || []);
      setPaths(mapData.paths || []);
      setRegions(mapData.regions || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载地图失败");
    } finally {
      setLoading(false);
    }
  }, [worldId]);

  useEffect(() => {
    loadMapData();
  }, [loadMapData]);

  const handleTileClick = (tile: HexTile) => {
    setSelectedTile(tile);
  };

  // 将地点与瓦片关联
  const getLocationForTile = (tile: HexTile): Location | undefined => {
    if (!tile.location_id) return undefined;
    return locations.find((l) => l.id === tile.location_id);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载地图中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center text-red-600">
          <p>{error}</p>
          <button
            onClick={loadMapData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <Link
                href={`/worlds/${worldId}`}
                className="text-blue-600 hover:text-blue-800"
              >
                ← 返回世界
              </Link>
              <h1 className="text-2xl font-bold text-gray-900">
                {world?.name} - 六边形地图
              </h1>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                地点: {locations.length} | 路径: {paths.length} | 区域:{" "}
                {regions.length}
              </span>
              <button
                onClick={() => setShowLocationList(!showLocationList)}
                className="text-sm px-3 py-1 bg-gray-100 rounded hover:bg-gray-200"
              >
                {showLocationList ? "隐藏列表" : "地点列表"}
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <div className="flex">
        {/* Map Area */}
        <div className="flex-1 p-4">
          <HexMap
            worldId={worldId}
            onTileClick={handleTileClick}
            className="w-full"
          />
        </div>

        {/* Sidebar - Location List */}
        {showLocationList && (
          <div className="w-80 bg-white border-l shadow-lg p-4 overflow-y-auto max-h-[calc(100vh-80px)]">
            <h3 className="font-bold text-lg mb-4">地点列表</h3>
            <div className="space-y-2">
              {locations.map((location) => (
                <div
                  key={location.id}
                  className="p-3 bg-gray-50 rounded-lg hover:bg-gray-100 cursor-pointer"
                >
                  <div className="flex items-center gap-2">
                    <span className="text-lg">
                      {location.icon ||
                        LOCATION_ICONS[location.location_type] ||
                        "📍"}
                    </span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-sm truncate">
                        {location.name}
                      </div>
                      <div className="text-xs text-gray-500">
                        {location.location_type}
                      </div>
                    </div>
                  </div>
                  {location.description && (
                    <p className="text-xs text-gray-600 mt-1 line-clamp-2">
                      {location.description}
                    </p>
                  )}
                </div>
              ))}
              {locations.length === 0 && (
                <p className="text-gray-500 text-sm text-center py-4">
                  暂无地点
                </p>
              )}
            </div>

            {/* Paths Section */}
            {paths.length > 0 && (
              <>
                <h3 className="font-bold text-lg mb-4 mt-6">路径</h3>
                <div className="space-y-2">
                  {paths.map((path) => (
                    <div
                      key={path.id}
                      className="p-2 bg-gray-50 rounded text-sm"
                    >
                      <div className="flex items-center gap-1">
                        <span>{path.from_location_name || "?"}</span>
                        <span className="text-gray-400">→</span>
                        <span>{path.to_location_name || "?"}</span>
                      </div>
                      <span className="text-xs text-gray-500">
                        {path.path_type}
                      </span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </div>
        )}
      </div>

      {/* Selected Tile Detail Modal */}
      {selectedTile && (
        <div
          className="fixed inset-0 bg-black/50 flex items-center justify-center z-50"
          onClick={() => setSelectedTile(null)}
        >
          <div
            className="bg-white rounded-xl shadow-2xl p-6 max-w-md w-full mx-4"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-start justify-between mb-4">
              <div>
                <h2 className="text-xl font-bold">
                  {selectedTile.location_name ||
                    (() => {
                      const labels: Record<string, string> = {
                        OCEAN: "海洋",
                        DEEP_OCEAN: "深海",
                        COAST: "海岸",
                        PLAINS: "平原",
                        GRASSLAND: "草原",
                        FOREST: "森林",
                        JUNGLE: "丛林",
                        MOUNTAIN: "山脉",
                        HILL: "丘陵",
                        DESERT: "沙漠",
                        TUNDRA: "苔原",
                        SNOW: "雪地",
                        SWAMP: "沼泽",
                        VOLCANO: "火山",
                        CITY: "城市",
                        RUINS: "遗迹",
                        LAKE: "湖泊",
                        RIVER: "河流",
                      };
                      return labels[selectedTile.terrain] || selectedTile.terrain;
                    })()}
                </h2>
                <span className="text-sm text-gray-500">
                  坐标 ({selectedTile.q}, {selectedTile.r})
                </span>
              </div>
              <button
                onClick={() => setSelectedTile(null)}
                className="text-gray-400 hover:text-gray-600 text-2xl"
              >
                ×
              </button>
            </div>

            <div className="space-y-3">
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-blue-50 p-3 rounded text-center">
                  <div className="text-xs text-gray-500">海拔</div>
                  <div className="font-bold text-blue-700">
                    {selectedTile.elevation}m
                  </div>
                </div>
                <div className="bg-green-50 p-3 rounded text-center">
                  <div className="text-xs text-gray-500">湿度</div>
                  <div className="font-bold text-green-700">
                    {selectedTile.moisture}%
                  </div>
                </div>
                <div className="bg-orange-50 p-3 rounded text-center">
                  <div className="text-xs text-gray-500">温度</div>
                  <div className="font-bold text-orange-700">
                    {selectedTile.temperature}°C
                  </div>
                </div>
              </div>

              {selectedTile.resource && (
                <div className="p-3 bg-yellow-50 rounded">
                  <span className="text-sm text-gray-600">资源: </span>
                  <span className="font-medium text-yellow-700">
                    {selectedTile.resource}
                  </span>
                </div>
              )}

              {selectedTile.features && selectedTile.features.length > 0 && (
                <div className="p-3 bg-purple-50 rounded">
                  <span className="text-sm text-gray-600">特征: </span>
                  <span className="font-medium text-purple-700">
                    {selectedTile.features.join(", ")}
                  </span>
                </div>
              )}

              {(() => {
                const location = getLocationForTile(selectedTile);
                if (location) {
                  return (
                    <div className="p-3 bg-orange-50 rounded border border-orange-200">
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-lg">
                          {location.icon ||
                            LOCATION_ICONS[location.location_type] ||
                            "📍"}
                        </span>
                        <span className="font-bold text-orange-800">
                          {location.name}
                        </span>
                      </div>
                      <p className="text-sm text-orange-700">
                        {location.description || "暂无描述"}
                      </p>
                    </div>
                  );
                }
                return null;
              })()}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
