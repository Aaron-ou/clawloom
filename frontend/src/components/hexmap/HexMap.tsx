"use client";

import { useState, useEffect, useRef, useCallback } from "react";

// 地形类型
export type TerrainType =
  | "OCEAN"
  | "DEEP_OCEAN"
  | "COAST"
  | "PLAINS"
  | "GRASSLAND"
  | "FOREST"
  | "JUNGLE"
  | "MOUNTAIN"
  | "HILL"
  | "DESERT"
  | "TUNDRA"
  | "SNOW"
  | "SWAMP"
  | "VOLCANO"
  | "CITY"
  | "RUINS"
  | "LAKE"
  | "RIVER";

// 六边形瓦片数据
export interface HexTile {
  id: string;
  q: number;
  r: number;
  x: number;
  y: number;
  terrain: TerrainType;
  elevation: number;
  moisture: number;
  temperature: number;
  features: string[];
  resource?: string;
  location_id?: string;
  location_name?: string;
  properties: Record<string, any>;
}

// 地图数据
export interface HexMapData {
  world_id: string;
  tiles: HexTile[];
  bounds: {
    min_q: number;
    max_q: number;
    min_r: number;
    max_r: number;
  };
  center: { q: number; r: number };
  radius: number;
}

// 地形配置
const TERRAIN_CONFIG: Record<
  TerrainType,
  { color: string; borderColor: string; icon: string; label: string }
> = {
  OCEAN: { color: "#3b82f6", borderColor: "#2563eb", icon: "", label: "海洋" },
  DEEP_OCEAN: { color: "#1e40af", borderColor: "#1e3a8a", icon: "", label: "深海" },
  COAST: { color: "#93c5fd", borderColor: "#60a5fa", icon: "", label: "海岸" },
  PLAINS: { color: "#86efac", borderColor: "#4ade80", icon: "", label: "平原" },
  GRASSLAND: { color: "#22c55e", borderColor: "#16a34a", icon: "", label: "草原" },
  FOREST: { color: "#15803d", borderColor: "#166534", icon: "🌲", label: "森林" },
  JUNGLE: { color: "#166534", borderColor: "#14532d", icon: "🌴", label: "丛林" },
  MOUNTAIN: { color: "#78716c", borderColor: "#57534e", icon: "⛰️", label: "山脉" },
  HILL: { color: "#a8a29e", borderColor: "#78716c", icon: "🌄", label: "丘陵" },
  DESERT: { color: "#fcd34d", borderColor: "#fbbf24", icon: "🏜️", label: "沙漠" },
  TUNDRA: { color: "#e5e7eb", borderColor: "#d1d5db", icon: "❄️", label: "苔原" },
  SNOW: { color: "#f9fafb", borderColor: "#e5e7eb", icon: "🏔️", label: "雪地" },
  SWAMP: { color: "#3f6212", borderColor: "#365314", icon: "🌿", label: "沼泽" },
  VOLCANO: { color: "#dc2626", borderColor: "#b91c1c", icon: "🌋", label: "火山" },
  CITY: { color: "#f97316", borderColor: "#ea580c", icon: "🏰", label: "城市" },
  RUINS: { color: "#7c2d12", borderColor: "#9a3412", icon: "🏛️", label: "遗迹" },
  LAKE: { color: "#60a5fa", borderColor: "#3b82f6", icon: "💧", label: "湖泊" },
  RIVER: { color: "#93c5fd", borderColor: "#60a5fa", icon: "🌊", label: "河流" },
};

// 六边形工具函数
const HEX_SIZE = 30;
const HEX_WIDTH = HEX_SIZE * 2;
const HEX_HEIGHT = HEX_SIZE * Math.sqrt(3);

function hexToPixel(q: number, r: number): { x: number; y: number } {
  const x = HEX_SIZE * (1.5 * q);
  const y = HEX_SIZE * ((Math.sqrt(3) / 2) * q + Math.sqrt(3) * r);
  return { x, y };
}

function generateHexPoints(cx: number, cy: number, size: number): string {
  const points: string[] = [];
  for (let i = 0; i < 6; i++) {
    const angleDeg = 60 * i - 30;
    const angleRad = (Math.PI / 180) * angleDeg;
    const px = cx + size * Math.cos(angleRad);
    const py = cy + size * Math.sin(angleRad);
    points.push(`${px.toFixed(1)},${py.toFixed(1)}`);
  }
  return points.join(" ");
}

interface HexMapProps {
  worldId: string;
  onTileClick?: (tile: HexTile) => void;
  className?: string;
}

export function HexMap({ worldId, onTileClick, className = "" }: HexMapProps) {
  const [mapData, setMapData] = useState<HexMapData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTile, setSelectedTile] = useState<HexTile | null>(null);
  
  // 视图状态
  const [scale, setScale] = useState(1);
  const [offset, setOffset] = useState({ x: 0, y: 0 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // 加载地图数据
  useEffect(() => {
    loadMapData();
  }, [worldId]);

  const loadMapData = async () => {
    try {
      setLoading(true);
      const res = await fetch(`http://localhost:8000/worlds/${worldId}/hexmap`);
      if (!res.ok) {
        throw new Error("Failed to load hex map");
      }
      const data = await res.json();
      setMapData(data);
      
      // 计算初始偏移使地图居中
      if (data.tiles.length > 0) {
        const xs = data.tiles.map((t: HexTile) => t.x);
        const ys = data.tiles.map((t: HexTile) => t.y);
        const centerX = (Math.max(...xs) + Math.min(...xs)) / 2;
        const centerY = (Math.max(...ys) + Math.min(...ys)) / 2;
        setOffset({ x: -centerX, y: -centerY });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  };

  // 生成地图
  const generateMap = async () => {
    try {
      setLoading(true);
      const apiKey = localStorage.getItem("api_key");
      const res = await fetch(
        `http://localhost:8000/worlds/${worldId}/hexmap/generate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${apiKey}`,
          },
          body: JSON.stringify({
            radius: 8,
            land_ratio: 0.4,
            ocean_ring: 2,
          }),
        }
      );
      if (!res.ok) throw new Error("生成失败");
      await loadMapData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "生成失败");
    } finally {
      setLoading(false);
    }
  };

  // 处理瓦片点击
  const handleTileClick = (tile: HexTile) => {
    setSelectedTile(tile);
    onTileClick?.(tile);
  };

  // 拖拽处理
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      setIsDragging(true);
      setDragStart({ x: e.clientX - offset.x, y: e.clientY - offset.y });
    }
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (isDragging) {
      setOffset({
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      });
    }
  };

  const handleMouseUp = () => {
    setIsDragging(false);
  };

  // 缩放处理
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setScale((s) => Math.max(0.3, Math.min(3, s * delta)));
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96 bg-blue-900 rounded-lg">
        <div className="text-white text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-white mx-auto mb-4" />
          <p>加载地图中...</p>
        </div>
      </div>
    );
  }

  if (error || !mapData) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-blue-900 rounded-lg text-white">
        <p className="mb-4">{error || "地图尚未生成"}</p>
        <button
          onClick={generateMap}
          className="px-4 py-2 bg-orange-500 hover:bg-orange-600 rounded-lg transition-colors"
        >
          生成六边形地图
        </button>
      </div>
    );
  }

  // 计算视图框
  const padding = HEX_SIZE * 2;
  const tileXs = mapData.tiles.map((t) => t.x);
  const tileYs = mapData.tiles.map((t) => t.y);
  const minX = Math.min(...tileXs) - padding;
  const maxX = Math.max(...tileXs) + padding;
  const minY = Math.min(...tileYs) - padding;
  const maxY = Math.max(...tileYs) + padding;

  return (
    <div className={`relative ${className}`}>
      {/* 工具栏 */}
      <div className="absolute top-4 left-4 z-10 flex gap-2">
        <button
          onClick={() => setScale((s) => Math.min(3, s * 1.2))}
          className="px-3 py-1 bg-white rounded shadow hover:bg-gray-100 text-sm"
        >
          放大
        </button>
        <button
          onClick={() => setScale((s) => Math.max(0.3, s * 0.8))}
          className="px-3 py-1 bg-white rounded shadow hover:bg-gray-100 text-sm"
        >
          缩小
        </button>
        <button
          onClick={() => {
            setScale(1);
            setOffset({ x: 0, y: 0 });
          }}
          className="px-3 py-1 bg-white rounded shadow hover:bg-gray-100 text-sm"
        >
          重置
        </button>
        <button
          onClick={generateMap}
          className="px-3 py-1 bg-orange-500 text-white rounded shadow hover:bg-orange-600 text-sm"
        >
          重新生成
        </button>
      </div>

      {/* 图例 */}
      <div className="absolute top-4 right-4 z-10 bg-white/90 backdrop-blur rounded-lg shadow p-3 max-w-xs">
        <h4 className="font-bold text-sm mb-2">地形图例</h4>
        <div className="grid grid-cols-2 gap-1 text-xs">
          {Object.entries(TERRAIN_CONFIG)
            .filter(([key]) => !["OCEAN", "DEEP_OCEAN", "COAST"].includes(key))
            .map(([key, config]) => (
              <div key={key} className="flex items-center gap-1">
                <div
                  className="w-4 h-4 rounded"
                  style={{ backgroundColor: config.color }}
                />
                <span>
                  {config.icon} {config.label}
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* 选中瓦片信息 */}
      {selectedTile && (
        <div className="absolute bottom-4 left-4 z-10 bg-white/95 backdrop-blur rounded-lg shadow p-4 max-w-sm">
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-bold">
              {TERRAIN_CONFIG[selectedTile.terrain].icon} {" "}
              {selectedTile.location_name || TERRAIN_CONFIG[selectedTile.terrain].label}
            </h4>
            <button
              onClick={() => setSelectedTile(null)}
              className="text-gray-400 hover:text-gray-600"
            >
              ×
            </button>
          </div>
          <div className="text-sm space-y-1 text-gray-600">
            <p>坐标: ({selectedTile.q}, {selectedTile.r})</p>
            <p>海拔: {selectedTile.elevation}m</p>
            <p>湿度: {selectedTile.moisture}%</p>
            <p>温度: {selectedTile.temperature}°C</p>
            {selectedTile.resource && <p>资源: {selectedTile.resource}</p>}
            {selectedTile.features.length > 0 && (
              <p>特征: {selectedTile.features.join(", ")}</p>
            )}
          </div>
        </div>
      )}

      {/* 地图容器 */}
      <div
        ref={containerRef}
        className="w-full h-[600px] bg-blue-900 rounded-lg overflow-hidden cursor-grab active:cursor-grabbing"
        onMouseDown={handleMouseDown}
        onMouseMove={handleMouseMove}
        onMouseUp={handleMouseUp}
        onMouseLeave={handleMouseUp}
        onWheel={handleWheel}
      >
        <svg
          ref={svgRef}
          className="w-full h-full"
          viewBox={`${minX} ${minY} ${maxX - minX} ${maxY - minY}`}
          style={{
            transform: `translate(${offset.x}px, ${offset.y}px) scale(${scale})`,
            transformOrigin: "center",
          }}
        >
          {/* 深海背景 */}
          <rect
            x={minX - 1000}
            y={minY - 1000}
            width={maxX - minX + 2000}
            height={maxY - minY + 2000}
            fill="#1e40af"
          />

          {/* 渲染瓦片 */}
          {mapData.tiles.map((tile) => {
            const config = TERRAIN_CONFIG[tile.terrain];
            const points = generateHexPoints(tile.x, tile.y, HEX_SIZE * 0.95);
            const isSelected = selectedTile?.id === tile.id;

            return (
              <g key={tile.id}>
                {/* 六边形 */}
                <polygon
                  points={points}
                  fill={config.color}
                  stroke={isSelected ? "#f97316" : config.borderColor}
                  strokeWidth={isSelected ? 3 : 1}
                  className="transition-all duration-200 hover:brightness-110 cursor-pointer"
                  onClick={() => handleTileClick(tile)}
                />

                {/* 图标（非海洋） */}
                {config.icon && tile.terrain !== "OCEAN" && tile.terrain !== "DEEP_OCEAN" && (
                  <text
                    x={tile.x}
                    y={tile.y + 5}
                    textAnchor="middle"
                    fontSize={HEX_SIZE * 0.7}
                    style={{
                      textShadow: "1px 1px 2px rgba(0,0,0,0.5)",
                      pointerEvents: "none",
                    }}
                  >
                    {config.icon}
                  </text>
                )}

                {/* 地点标记 */}
                {tile.location_name && (
                  <g>
                    <circle
                      cx={tile.x}
                      cy={tile.y - HEX_SIZE * 0.5}
                      r={6}
                      fill="#f97316"
                      stroke="white"
                      strokeWidth={2}
                    />
                    <text
                      x={tile.x}
                      y={tile.y - HEX_SIZE * 0.8}
                      textAnchor="middle"
                      fill="white"
                      fontSize={10}
                      fontWeight="bold"
                      style={{
                        textShadow: "1px 1px 2px rgba(0,0,0,0.8)",
                        pointerEvents: "none",
                      }}
                    >
                      {tile.location_name}
                    </text>
                  </g>
                )}
              </g>
            );
          })}
        </svg>
      </div>
    </div>
  );
}

export default HexMap;
