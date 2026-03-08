"use client";

import { useState, useCallback, useEffect } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { HexMapCanvas, HexTile, HexMapData, HexLayout } from "@/components/hexmap";

// 地图尺寸选项
const MAP_SIZES = [
  { label: "15×15", width: 15, height: 15 },
  { label: "21×21", width: 21, height: 21 },
  { label: "31×31", width: 31, height: 31 },
  { label: "51×51", width: 51, height: 51 },
];

export default function MapEditorPage() {
  const params = useParams();
  const worldId = params.id as string;
  
  // 地图数据
  const [mapData, setMapData] = useState<Partial<HexMapData>>({
    width: 15,
    height: 15,
    layout: "pointy" as HexLayout,
    tiles: [],
  });
  
  // 选中的地块
  const [selectedTile, setSelectedTile] = useState<HexTile | null>(null);
  
  // 右键菜单状态
  const [contextMenu, setContextMenu] = useState<{
    visible: boolean;
    x: number;
    y: number;
    tile: HexTile | null;
  }>({ visible: false, x: 0, y: 0, tile: null });
  
  // 路径状态
  const [startTile, setStartTile] = useState<HexTile | null>(null);
  const [endTile, setEndTile] = useState<HexTile | null>(null);
  
  // 地图尺寸
  const [selectedSize, setSelectedSize] = useState(MAP_SIZES[0]);
  
  // 从服务器加载地图数据
  const loadMapFromServer = useCallback(async () => {
    try {
      const response = await fetch(`http://localhost:8000/worlds/${worldId}/hexmap`);
      if (!response.ok) {
        console.log("No existing map data, using default");
        return;
      }
      
      const data = await response.json();
      if (data.tiles && data.tiles.length > 0) {
        // 转换服务器数据格式
        const tiles: HexTile[] = data.tiles.map((t: any) => ({
          id: t.id,
          q: t.q,
          r: t.r,
          terrain: mapTerrainFromServer(t.terrain),
          height: t.elevation,
          resource: t.resource,
        }));
        
        setMapData((prev) => ({
          ...prev,
          tiles,
          width: data.bounds?.max_q ? data.bounds.max_q - data.bounds.min_q + 1 : 15,
          height: data.bounds?.max_r ? data.bounds.max_r - data.bounds.min_r + 1 : 15,
        }));
      }
    } catch (error) {
      console.error("Failed to load map:", error);
    }
  }, [worldId]);
  
  // 将服务器地形映射到编辑器地形
  const mapTerrainFromServer = (serverTerrain: string): HexTile["terrain"] => {
    const mapping: Record<string, HexTile["terrain"]> = {
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
  
  // 初始加载
  useEffect(() => {
    loadMapFromServer();
  }, [loadMapFromServer]);
  
  // 处理地块点击
  const handleTileClick = useCallback((tile: HexTile | null) => {
    setSelectedTile(tile);
  }, []);
  
  // 处理右键菜单
  const handleTileContextMenu = useCallback((tile: HexTile | null, x: number, y: number) => {
    if (tile) {
      setContextMenu({
        visible: true,
        x,
        y,
        tile,
      });
    }
  }, []);
  
  // 关闭右键菜单
  const closeContextMenu = () => {
    setContextMenu((prev) => ({ ...prev, visible: false }));
  };
  
  // 设置起点
  const handleSetStart = () => {
    if (contextMenu.tile) {
      // 清除之前的起点
      if (startTile) {
        updateTileState(startTile.q, startTile.r, { isStart: false });
      }
      setStartTile(contextMenu.tile);
      updateTileState(contextMenu.tile.q, contextMenu.tile.r, { isStart: true, isEnd: false });
    }
    closeContextMenu();
  };
  
  // 设置终点
  const handleSetEnd = () => {
    if (contextMenu.tile) {
      // 清除之前的终点
      if (endTile) {
        updateTileState(endTile.q, endTile.r, { isEnd: false });
      }
      setEndTile(contextMenu.tile);
      updateTileState(contextMenu.tile.q, contextMenu.tile.r, { isEnd: true, isStart: false });
    }
    closeContextMenu();
  };
  
  // 切换障碍物
  const handleToggleObstacle = () => {
    if (contextMenu.tile) {
      updateTileState(
        contextMenu.tile.q,
        contextMenu.tile.r,
        { isObstacle: !contextMenu.tile.isObstacle }
      );
    }
    closeContextMenu();
  };
  
  // 添加路径点
  const handleAddWaypoint = () => {
    if (contextMenu.tile) {
      updateTileState(contextMenu.tile.q, contextMenu.tile.r, { isWaypoint: true });
    }
    closeContextMenu();
  };
  
  // 更新地块状态（辅助函数）
  const updateTileState = (q: number, r: number, updates: Partial<HexTile>) => {
    setMapData((prev) => ({
      ...prev,
      tiles: prev.tiles?.map((t) =>
        t.q === q && t.r === r ? { ...t, ...updates } : t
      ) || [],
    }));
  };
  
  // 生成随机地图
  const generateRandomMap = () => {
    const terrains: HexTile["terrain"][] = ["grass", "desert", "water", "mountain", "snow", "forest"];
    const newTiles: HexTile[] = [];
    const halfWidth = Math.floor(selectedSize.width / 2);
    const halfHeight = Math.floor(selectedSize.height / 2);
    
    for (let q = -halfWidth; q <= halfWidth; q++) {
      for (let r = -halfHeight; r <= halfHeight; r++) {
        // 创建圆形地图
        const distance = Math.max(Math.abs(q), Math.abs(r), Math.abs(-q - r));
        if (distance > halfWidth) continue;
        
        newTiles.push({
          id: `tile-${q}-${r}-${Date.now()}`,
          q,
          r,
          terrain: terrains[Math.floor(Math.random() * terrains.length)],
          height: Math.floor(Math.random() * 5),
        });
      }
    }
    
    setMapData((prev) => ({ ...prev, tiles: newTiles }));
    setSelectedTile(null);
    setStartTile(null);
    setEndTile(null);
  };
  
  // 导出JSON
  const exportJSON = () => {
    const data = {
      ...mapData,
      metadata: {
        name: `Map-${worldId}`,
        description: "Generated by ClawLoom Map Editor",
        createdAt: new Date().toISOString(),
      },
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `clawloom-map-${worldId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };
  
  // 导入JSON
  const importJSON = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string) as HexMapData;
        setMapData(data);
        setSelectedTile(null);
        setStartTile(null);
        setEndTile(null);
      } catch (error) {
        alert("Invalid JSON file");
      }
    };
    reader.readAsText(file);
  };
  
  // 保存到服务器
  const saveToServer = async () => {
    try {
      const apiKey = localStorage.getItem("api_key");
      if (!apiKey) {
        alert("请先登录");
        return;
      }
      
      // 首先生成新的地图
      const response = await fetch(
        `http://localhost:8000/worlds/${worldId}/hexmap/generate`,
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${apiKey}`,
          },
          body: JSON.stringify({
            radius: Math.floor(selectedSize.width / 2),
            seed: Date.now(),
            land_ratio: 0.6,
            ocean_ring: 2,
          }),
        }
      );
      
      if (!response.ok) {
        throw new Error("Failed to generate map");
      }
      
      alert("地图已保存到服务器！");
    } catch (error) {
      console.error("Failed to save map:", error);
      alert("保存失败，请检查网络连接");
    }
  };
  
  // 点击其他地方关闭右键菜单
  useEffect(() => {
    const handleClickOutside = () => {
      closeContextMenu();
    };
    
    document.addEventListener("click", handleClickOutside);
    return () => document.removeEventListener("click", handleClickOutside);
  }, []);
  
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
              <h1 className="text-xl font-bold text-white">地图编辑器</h1>
              <span className="text-gray-500">|</span>
              <span className="text-gray-400 text-sm">世界ID: {worldId}</span>
            </div>
            
            <div className="flex items-center gap-3">
              {/* 地图尺寸选择 */}
              <select
                value={selectedSize.label}
                onChange={(e) => {
                  const size = MAP_SIZES.find((s) => s.label === e.target.value);
                  if (size) {
                    setSelectedSize(size);
                    setMapData((prev) => ({
                      ...prev,
                      width: size.width,
                      height: size.height,
                    }));
                  }
                }}
                className="bg-gray-700 text-white px-3 py-1.5 rounded text-sm border border-gray-600"
              >
                {MAP_SIZES.map((size) => (
                  <option key={size.label} value={size.label}>
                    {size.label}
                  </option>
                ))}
              </select>
              
              {/* 布局切换 */}
              <div className="flex bg-gray-700 rounded overflow-hidden">
                <button
                  onClick={() => setMapData((prev) => ({ ...prev, layout: "pointy" }))}
                  className={`px-3 py-1.5 text-sm ${
                    mapData.layout === "pointy"
                      ? "bg-blue-600 text-white"
                      : "text-gray-300 hover:bg-gray-600"
                  }`}
                >
                  点顶式
                </button>
                <button
                  onClick={() => setMapData((prev) => ({ ...prev, layout: "flat" }))}
                  className={`px-3 py-1.5 text-sm ${
                    mapData.layout === "flat"
                      ? "bg-blue-600 text-white"
                      : "text-gray-300 hover:bg-gray-600"
                  }`}
                >
                  平顶式
                </button>
              </div>
              
              <div className="h-6 w-px bg-gray-600" />
              
              {/* 导入导出 */}
              <label className="px-3 py-1.5 bg-gray-700 text-gray-300 rounded text-sm hover:bg-gray-600 cursor-pointer">
                导入JSON
                <input
                  type="file"
                  accept=".json"
                  onChange={importJSON}
                  className="hidden"
                />
              </label>
              <button
                onClick={exportJSON}
                className="px-3 py-1.5 bg-gray-700 text-gray-300 rounded text-sm hover:bg-gray-600"
              >
                导出JSON
              </button>
              <button
                onClick={saveToServer}
                className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
              >
                保存到服务器
              </button>
            </div>
          </div>
        </div>
      </header>
      
      {/* 主编辑区 */}
      <div className="relative h-[calc(100vh-60px)]">
        <HexMapCanvas
          worldId={worldId}
          initialData={mapData}
          editable={true}
          onTileClick={handleTileClick}
          onTileContextMenu={handleTileContextMenu}
          className="w-full h-full"
        />
        
        {/* 右键菜单 */}
        {contextMenu.visible && contextMenu.tile && (
          <div
            className="absolute bg-white rounded-lg shadow-xl py-1 z-50 min-w-[150px]"
            style={{ left: contextMenu.x, top: contextMenu.y }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="px-3 py-2 text-xs text-gray-500 border-b">
              坐标 ({contextMenu.tile.q}, {contextMenu.tile.r})
            </div>
            <button
              onClick={handleSetStart}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
            >
              <span className="text-green-500">●</span> 设为起点
            </button>
            <button
              onClick={handleSetEnd}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
            >
              <span className="text-red-500">●</span> 设为终点
            </button>
            <button
              onClick={handleToggleObstacle}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
            >
              <span className="text-gray-500">🚫</span> {contextMenu.tile.isObstacle ? "移除障碍" : "设为障碍"}
            </button>
            <button
              onClick={handleAddWaypoint}
              className="w-full px-3 py-2 text-left text-sm hover:bg-gray-100 flex items-center gap-2"
            >
              <span className="text-yellow-500">📍</span> 添加路径点
            </button>
          </div>
        )}
        
        {/* 选中地块信息面板 */}
        {selectedTile && (
          <div className="absolute bottom-4 right-4 bg-white rounded-lg shadow-xl p-4 w-64">
            <h3 className="font-bold text-gray-800 mb-2">地块详情</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-gray-500">坐标:</span>
                <span>({selectedTile.q}, {selectedTile.r})</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">地形:</span>
                <span className="capitalize">{selectedTile.terrain}</span>
              </div>
              {selectedTile.height !== undefined && (
                <div className="flex justify-between">
                  <span className="text-gray-500">高度:</span>
                  <span>{selectedTile.height}</span>
                </div>
              )}
              {selectedTile.resource && (
                <div className="flex justify-between">
                  <span className="text-gray-500">资源:</span>
                  <span>{selectedTile.resource}</span>
                </div>
              )}
              <div className="flex gap-2 mt-3">
                {selectedTile.isStart && (
                  <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded">起点</span>
                )}
                {selectedTile.isEnd && (
                  <span className="px-2 py-0.5 bg-red-100 text-red-700 text-xs rounded">终点</span>
                )}
                {selectedTile.isObstacle && (
                  <span className="px-2 py-0.5 bg-gray-100 text-gray-700 text-xs rounded">障碍</span>
                )}
                {selectedTile.isWaypoint && (
                  <span className="px-2 py-0.5 bg-yellow-100 text-yellow-700 text-xs rounded">路径点</span>
                )}
              </div>
            </div>
          </div>
        )}
        
        {/* 快捷键提示 */}
        <div className="absolute bottom-4 left-1/2 -translate-x-1/2 bg-gray-800 text-white text-xs px-4 py-2 rounded-full opacity-70 hover:opacity-100 transition-opacity">
          左键点击: 选择/画笔 | 右键: 菜单 | Alt+拖拽: 平移 | 滚轮: 缩放 | Shift+拖拽: 框选
        </div>
      </div>
    </div>
  );
}
