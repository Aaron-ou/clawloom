"use client";

import React, { useRef, useEffect, useState, useCallback, useMemo } from "react";

// ==================== 类型定义 ====================

export type HexLayout = "pointy" | "flat";

export type TerrainType = "grass" | "desert" | "water" | "mountain" | "snow" | "forest" | "none";

export interface HexTile {
  id: string;
  q: number; // 轴向坐标 - 列
  r: number; // 轴向坐标 - 行
  terrain: TerrainType;
  height?: number;
  resource?: string;
  icon?: string;
  label?: string;
  isObstacle?: boolean;
  isStart?: boolean;
  isEnd?: boolean;
  isPath?: boolean;
  isWaypoint?: boolean;
  location_id?: string; // 兼容旧版本
  location_name?: string; // 兼容旧版本
  x?: number; // 兼容旧版本
  y?: number; // 兼容旧版本
  elevation?: number; // 兼容旧版本
  moisture?: number; // 兼容旧版本
  temperature?: number; // 兼容旧版本
  features?: string[]; // 兼容旧版本
  metadata?: Record<string, any>;
}

export interface HexMapData {
  tiles: HexTile[];
  width: number;
  height: number;
  layout: HexLayout;
  metadata?: {
    name?: string;
    description?: string;
    createdAt?: string;
  };
}

export interface CameraState {
  x: number;
  y: number;
  zoom: number;
}

export interface Viewport {
  left: number;
  right: number;
  top: number;
  bottom: number;
}

// ==================== 常量配置 ====================

const TERRAIN_COLORS: Record<TerrainType, string> = {
  grass: "#4ade80",
  desert: "#fbbf24",
  water: "#3b82f6",
  mountain: "#6b7280",
  snow: "#f3f4f6",
  forest: "#166534",
  none: "#e5e7eb",
};

const TERRAIN_NAMES: Record<TerrainType, string> = {
  grass: "草地",
  desert: "沙漠",
  water: "水域",
  mountain: "山地",
  snow: "雪地",
  forest: "森林",
  none: "空地",
};

const DEFAULT_HEX_SIZE = 30;
const MIN_ZOOM = 0.3;
const MAX_ZOOM = 3;
const ZOOM_STEP = 0.1;

// ==================== 六边形数学工具函数 ====================

/**
 * 六边形方向向量
 * Pointy-top: 顶点朝上
 * Flat-top: 边朝上
 */
const HEX_DIRECTIONS = {
  pointy: [
    { q: 1, r: 0 }, { q: 1, r: -1 }, { q: 0, r: -1 },
    { q: -1, r: 0 }, { q: -1, r: 1 }, { q: 0, r: 1 },
  ],
  flat: [
    { q: 1, r: 0 }, { q: 1, r: -1 }, { q: 0, r: -1 },
    { q: -1, r: 0 }, { q: -1, r: 1 }, { q: 0, r: 1 },
  ],
};

/**
 * 将轴向坐标转换为像素坐标 (Pointy-top)
 */
function hexToPixelPointy(q: number, r: number, size: number): { x: number; y: number } {
  const x = size * (Math.sqrt(3) * q + Math.sqrt(3) / 2 * r);
  const y = size * (3 / 2 * r);
  return { x, y };
}

/**
 * 将轴向坐标转换为像素坐标 (Flat-top)
 */
function hexToPixelFlat(q: number, r: number, size: number): { x: number; y: number } {
  const x = size * (3 / 2 * q);
  const y = size * (Math.sqrt(3) / 2 * q + Math.sqrt(3) * r);
  return { x, y };
}

/**
 * 将轴向坐标转换为像素坐标
 */
function hexToPixel(q: number, r: number, size: number, layout: HexLayout): { x: number; y: number } {
  return layout === "pointy" 
    ? hexToPixelPointy(q, r, size) 
    : hexToPixelFlat(q, r, size);
}

/**
 * 将像素坐标转换为轴向坐标
 */
function pixelToHex(x: number, y: number, size: number, layout: HexLayout): { q: number; r: number } {
  if (layout === "pointy") {
    const q = (Math.sqrt(3) / 3 * x - 1 / 3 * y) / size;
    const r = (2 / 3 * y) / size;
    return hexRound(q, r);
  } else {
    const q = (2 / 3 * x) / size;
    const r = (-1 / 3 * x + Math.sqrt(3) / 3 * y) / size;
    return hexRound(q, r);
  }
}

/**
 * 将分数坐标舍入到最近的六边形
 */
function hexRound(q: number, r: number): { q: number; r: number } {
  let s = -q - r;
  let rq = Math.round(q);
  let rr = Math.round(r);
  let rs = Math.round(s);

  const qDiff = Math.abs(rq - q);
  const rDiff = Math.abs(rr - r);
  const sDiff = Math.abs(rs - s);

  if (qDiff > rDiff && qDiff > sDiff) {
    rq = -rr - rs;
  } else if (rDiff > sDiff) {
    rr = -rq - rs;
  }

  return { q: rq, r: rr };
}

/**
 * 计算六边形的顶点
 */
function getHexCorners(centerX: number, centerY: number, size: number, layout: HexLayout): { x: number; y: number }[] {
  const corners: { x: number; y: number }[] = [];
  const startAngle = layout === "pointy" ? 30 : 0;
  
  for (let i = 0; i < 6; i++) {
    const angleDeg = startAngle + 60 * i;
    const angleRad = (Math.PI / 180) * angleDeg;
    corners.push({
      x: centerX + size * Math.cos(angleRad),
      y: centerY + size * Math.sin(angleRad),
    });
  }
  return corners;
}

/**
 * 计算两个六边形之间的距离
 */
function hexDistance(a: { q: number; r: number }, b: { q: number; r: number }): number {
  return (Math.abs(a.q - b.q) + Math.abs(a.q + a.r - b.q - b.r) + Math.abs(a.r - b.r)) / 2;
}

/**
 * 获取相邻的六边形坐标
 */
function getNeighbors(q: number, r: number, layout: HexLayout): { q: number; r: number }[] {
  const directions = HEX_DIRECTIONS[layout];
  return directions.map((d) => ({ q: q + d.q, r: r + d.r }));
}

// ==================== 主组件 ====================

interface HexMapCanvasProps {
  worldId: string;
  initialData?: Partial<HexMapData> | any;
  editable?: boolean;
  onTileClick?: (tile: HexTile | null) => void;
  onTileContextMenu?: (tile: HexTile | null, x: number, y: number) => void;
  className?: string;
}

export const HexMapCanvas: React.FC<HexMapCanvasProps> = ({
  worldId,
  initialData,
  editable = true,
  onTileClick,
  onTileContextMenu,
  className = "",
}) => {
  // ==================== 状态 ====================
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  
  // 地图数据
  const [mapData, setMapData] = useState<HexMapData>({
    tiles: [],
    width: 15,
    height: 15,
    layout: "pointy",
    ...initialData,
  });
  
  // 相机状态
  const [camera, setCamera] = useState<CameraState>({
    x: 0,
    y: 0,
    zoom: 1,
  });
  
  // 交互状态
  const [hoveredTile, setHoveredTile] = useState<HexTile | null>(null);
  const [selectedTiles, setSelectedTiles] = useState<Set<string>>(new Set());
  const [isDragging, setIsDragging] = useState(false);
  const [dragStart, setDragStart] = useState({ x: 0, y: 0 });
  const [isSelecting, setIsSelecting] = useState(false);
  const [selectionStart, setSelectionStart] = useState<{ q: number; r: number } | null>(null);
  const [selectionEnd, setSelectionEnd] = useState<{ q: number; r: number } | null>(null);
  
  // 工具状态
  const [currentTool, setCurrentTool] = useState<TerrainType | "select" | "erase">("select");
  const [showGrid, setShowGrid] = useState(true);
  const [showCoords, setShowCoords] = useState(false);
  const [showHeightShadow, setShowHeightShadow] = useState(false);
  const [hexSize, setHexSize] = useState(DEFAULT_HEX_SIZE);
  
  // 路径查找状态
  const [startTile, setStartTile] = useState<HexTile | null>(null);
  const [endTile, setEndTile] = useState<HexTile | null>(null);
  const [pathTiles, setPathTiles] = useState<Set<string>>(new Set());
  
  // 鼠标位置
  const [mousePos, setMousePos] = useState({ x: 0, y: 0, q: 0, r: 0 });
  
  // ==================== 计算属性 ====================
  
  const tilesMap = useMemo(() => {
    const map = new Map<string, HexTile>();
    mapData.tiles.forEach((tile) => {
      map.set(`${tile.q},${tile.r}`, tile);
    });
    return map;
  }, [mapData.tiles]);
  
  // ==================== 渲染函数 ====================
  
  const render = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    
    // 设置Canvas尺寸
    canvas.width = rect.width * dpr;
    canvas.height = rect.height * dpr;
    ctx.scale(dpr, dpr);
    
    // 清空画布
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(0, 0, rect.width, rect.height);
    
    // 应用相机变换
    ctx.save();
    ctx.translate(rect.width / 2 + camera.x, rect.height / 2 + camera.y);
    ctx.scale(camera.zoom, camera.zoom);
    
    // 计算可视范围
    const viewport: Viewport = {
      left: (-rect.width / 2 - camera.x) / camera.zoom,
      right: (rect.width / 2 - camera.x) / camera.zoom,
      top: (-rect.height / 2 - camera.y) / camera.zoom,
      bottom: (rect.height / 2 - camera.y) / camera.zoom,
    };
    
    // 渲染所有瓦片
    const halfWidth = Math.floor(mapData.width / 2);
    const halfHeight = Math.floor(mapData.height / 2);
    
    for (let q = -halfWidth; q <= halfWidth; q++) {
      for (let r = -halfHeight; r <= halfHeight; r++) {
        const pixel = hexToPixel(q, r, hexSize, mapData.layout);
        
        // 检查是否在可视范围内
        if (pixel.x + hexSize < viewport.left || pixel.x - hexSize > viewport.right ||
            pixel.y + hexSize < viewport.top || pixel.y - hexSize > viewport.bottom) {
          continue;
        }
        
        const tileKey = `${q},${r}`;
        const tile = tilesMap.get(tileKey);
        
        renderHex(ctx, q, r, pixel.x, pixel.y, tile);
      }
    }
    
    // 渲染选区框
    if (isSelecting && selectionStart && selectionEnd) {
      renderSelectionBox(ctx);
    }
    
    ctx.restore();
  }, [mapData, camera, hexSize, tilesMap, hoveredTile, selectedTiles, pathTiles, showGrid, showCoords, showHeightShadow, isSelecting, selectionStart, selectionEnd]);
  
  // 渲染单个六边形
  const renderHex = (
    ctx: CanvasRenderingContext2D,
    q: number,
    r: number,
    x: number,
    y: number,
    tile?: HexTile
  ) => {
    const corners = getHexCorners(x, y, hexSize * 0.95, mapData.layout);
    const isHovered = hoveredTile?.q === q && hoveredTile?.r === r;
    const isSelected = selectedTiles.has(`${q},${r}`);
    const isInPath = pathTiles.has(`${q},${r}`);
    
    // 确定颜色
    let fillColor = TERRAIN_COLORS[tile?.terrain || "none"];
    
    // 高度阴影
    if (showHeightShadow && tile?.height) {
      const shadowIntensity = Math.min(tile.height * 0.1, 0.5);
      fillColor = darkenColor(fillColor, shadowIntensity);
    }
    
    // 路径高亮
    if (isInPath) {
      fillColor = "#facc15"; // 黄色路径
    }
    
    // 绘制六边形
    ctx.beginPath();
    ctx.moveTo(corners[0].x, corners[0].y);
    for (let i = 1; i < 6; i++) {
      ctx.lineTo(corners[i].x, corners[i].y);
    }
    ctx.closePath();
    
    ctx.fillStyle = fillColor;
    ctx.fill();
    
    // 边框
    ctx.strokeStyle = showGrid ? "rgba(255,255,255,0.3)" : "rgba(255,255,255,0.1)";
    ctx.lineWidth = 1;
    ctx.stroke();
    
    // 悬停高亮
    if (isHovered) {
      ctx.strokeStyle = "#f97316";
      ctx.lineWidth = 3;
      ctx.stroke();
      
      // 发光效果
      ctx.shadowColor = "#f97316";
      ctx.shadowBlur = 10;
      ctx.stroke();
      ctx.shadowBlur = 0;
    }
    
    // 选中高亮
    if (isSelected) {
      ctx.strokeStyle = "#3b82f6";
      ctx.lineWidth = 3;
      ctx.stroke();
    }
    
    // 起点/终点标记
    if (tile?.isStart) {
      ctx.fillStyle = "#22c55e";
      ctx.beginPath();
      ctx.arc(x, y, hexSize * 0.3, 0, Math.PI * 2);
      ctx.fill();
    }
    if (tile?.isEnd) {
      ctx.fillStyle = "#ef4444";
      ctx.beginPath();
      ctx.arc(x, y, hexSize * 0.3, 0, Math.PI * 2);
      ctx.fill();
    }
    if (tile?.isWaypoint) {
      ctx.fillStyle = "#f59e0b";
      ctx.beginPath();
      ctx.arc(x, y, hexSize * 0.2, 0, Math.PI * 2);
      ctx.fill();
    }
    
    // 障碍物标记
    if (tile?.isObstacle) {
      ctx.strokeStyle = "#dc2626";
      ctx.lineWidth = 2;
      ctx.beginPath();
      ctx.moveTo(corners[0].x, corners[0].y);
      ctx.lineTo(corners[3].x, corners[3].y);
      ctx.moveTo(corners[1].x, corners[1].y);
      ctx.lineTo(corners[4].x, corners[4].y);
      ctx.stroke();
    }
    
    // 图标
    if (tile?.icon) {
      ctx.font = `${hexSize * 0.6}px Arial`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "white";
      ctx.fillText(tile.icon, x, y);
    }
    
    // 坐标标签
    if (showCoords) {
      ctx.font = `${hexSize * 0.25}px Arial`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "rgba(255,255,255,0.7)";
      ctx.fillText(`${q},${r}`, x, y);
    }
    
    // 高度标签
    if (tile?.height && tile.height > 0) {
      ctx.font = `${hexSize * 0.25}px Arial`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillStyle = "rgba(0,0,0,0.7)";
      ctx.fillText(String(tile.height), x, y + hexSize * 0.5);
    }
  };
  
  // 渲染选区框
  const renderSelectionBox = (ctx: CanvasRenderingContext2D) => {
    if (!selectionStart || !selectionEnd) return;
    
    const startPixel = hexToPixel(selectionStart.q, selectionStart.r, hexSize, mapData.layout);
    const endPixel = hexToPixel(selectionEnd.q, selectionEnd.r, hexSize, mapData.layout);
    
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2;
    ctx.setLineDash([5, 5]);
    ctx.strokeRect(
      Math.min(startPixel.x, endPixel.x) - hexSize,
      Math.min(startPixel.y, endPixel.y) - hexSize,
      Math.abs(endPixel.x - startPixel.x) + hexSize * 2,
      Math.abs(endPixel.y - startPixel.y) + hexSize * 2
    );
    ctx.setLineDash([]);
  };
  
  // 颜色变暗
  const darkenColor = (color: string, amount: number): string => {
    const hex = color.replace("#", "");
    const r = Math.max(0, parseInt(hex.substring(0, 2), 16) * (1 - amount));
    const g = Math.max(0, parseInt(hex.substring(2, 4), 16) * (1 - amount));
    const b = Math.max(0, parseInt(hex.substring(4, 6), 16) * (1 - amount));
    return `rgb(${Math.floor(r)}, ${Math.floor(g)}, ${Math.floor(b)})`;
  };
  
  // ==================== A*路径查找 ====================
  
  const findPath = useCallback((start: HexTile, end: HexTile): HexTile[] => {
    const openSet: HexTile[] = [start];
    const closedSet = new Set<string>();
    const cameFrom = new Map<string, HexTile>();
    const gScore = new Map<string, number>();
    const fScore = new Map<string, number>();
    
    gScore.set(`${start.q},${start.r}`, 0);
    fScore.set(`${start.q},${start.r}`, hexDistance(start, end));
    
    while (openSet.length > 0) {
      // 找到fScore最小的节点
      let current = openSet[0];
      let currentIdx = 0;
      for (let i = 1; i < openSet.length; i++) {
        const fScoreCurrent = fScore.get(`${current.q},${current.r}`) || Infinity;
        const fScoreNext = fScore.get(`${openSet[i].q},${openSet[i].r}`) || Infinity;
        if (fScoreNext < fScoreCurrent) {
          current = openSet[i];
          currentIdx = i;
        }
      }
      
      // 到达终点
      if (current.q === end.q && current.r === end.r) {
        const path: HexTile[] = [];
        let node: HexTile | undefined = current;
        while (node) {
          path.unshift(node);
          node = cameFrom.get(`${node.q},${node.r}`);
        }
        return path;
      }
      
      openSet.splice(currentIdx, 1);
      closedSet.add(`${current.q},${current.r}`);
      
      // 检查邻居
      const neighbors = getNeighbors(current.q, current.r, mapData.layout);
      for (const neighborCoord of neighbors) {
        const neighborKey = `${neighborCoord.q},${neighborCoord.r}`;
        
        if (closedSet.has(neighborKey)) continue;
        
        const neighbor = tilesMap.get(neighborKey);
        if (!neighbor || neighbor.isObstacle) continue;
        
        const tentativeGScore = (gScore.get(`${current.q},${current.r}`) || 0) + 1;
        
        if (!openSet.some((t) => t.q === neighborCoord.q && t.r === neighborCoord.r)) {
          openSet.push(neighbor);
        } else if (tentativeGScore >= (gScore.get(neighborKey) || Infinity)) {
          continue;
        }
        
        cameFrom.set(neighborKey, current);
        gScore.set(neighborKey, tentativeGScore);
        fScore.set(neighborKey, tentativeGScore + hexDistance(neighbor, end));
      }
    }
    
    return []; // 无路径
  }, [mapData.layout, tilesMap]);
  
  // ==================== 事件处理 ====================
  
  const getTileFromPixel = (clientX: number, clientY: number): { q: number; r: number } | null => {
    const canvas = canvasRef.current;
    if (!canvas) return null;
    
    const rect = canvas.getBoundingClientRect();
    const x = (clientX - rect.left - rect.width / 2 - camera.x) / camera.zoom;
    const y = (clientY - rect.top - rect.height / 2 - camera.y) / camera.zoom;
    
    return pixelToHex(x, y, hexSize, mapData.layout);
  };
  
  const handleMouseMove = (e: React.MouseEvent) => {
    const rect = canvasRef.current?.getBoundingClientRect();
    if (!rect) return;
    
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    const hex = getTileFromPixel(e.clientX, e.clientY);
    if (hex) {
      const tile = tilesMap.get(`${hex.q},${hex.r}`);
      setHoveredTile(tile || { id: `empty-${hex.q}-${hex.r}`, q: hex.q, r: hex.r, terrain: "none" });
      setMousePos({ x, y, q: hex.q, r: hex.r });
    }
    
    if (isDragging) {
      const dx = e.clientX - dragStart.x;
      const dy = e.clientY - dragStart.y;
      setCamera((prev) => ({ ...prev, x: prev.x + dx, y: prev.y + dy }));
      setDragStart({ x: e.clientX, y: e.clientY });
    }
    
    if (isSelecting && selectionStart) {
      const endHex = getTileFromPixel(e.clientX, e.clientY);
      if (endHex) {
        setSelectionEnd(endHex);
      }
    }
  };
  
  const handleMouseDown = (e: React.MouseEvent) => {
    if (e.button === 0) {
      // 左键：选择或框选
      const hex = getTileFromPixel(e.clientX, e.clientY);
      if (hex) {
        if (e.shiftKey) {
          // Shift+拖拽 = 框选
          setIsSelecting(true);
          setSelectionStart(hex);
          setSelectionEnd(hex);
        } else if (editable && currentTool !== "select") {
          // 画笔工具
          updateTile(hex.q, hex.r, { terrain: currentTool as TerrainType });
        }
      }
      setDragStart({ x: e.clientX, y: e.clientY });
    } else if (e.button === 1 || (e.button === 0 && e.altKey)) {
      // 中键或Alt+左键 = 拖拽
      setIsDragging(true);
      setDragStart({ x: e.clientX, y: e.clientY });
    }
  };
  
  const handleMouseUp = (e: React.MouseEvent) => {
    if (isSelecting && selectionStart && selectionEnd) {
      // 完成框选
      const minQ = Math.min(selectionStart.q, selectionEnd.q);
      const maxQ = Math.max(selectionStart.q, selectionEnd.q);
      const minR = Math.min(selectionStart.r, selectionEnd.r);
      const maxR = Math.max(selectionStart.r, selectionEnd.r);
      
      const newSelected = new Set(selectedTiles);
      for (let q = minQ; q <= maxQ; q++) {
        for (let r = minR; r <= maxR; r++) {
          newSelected.add(`${q},${r}`);
        }
      }
      setSelectedTiles(newSelected);
    }
    
    setIsDragging(false);
    setIsSelecting(false);
    setSelectionStart(null);
    setSelectionEnd(null);
  };
  
  const handleClick = (e: React.MouseEvent) => {
    const hex = getTileFromPixel(e.clientX, e.clientY);
    if (!hex) return;
    
    const tileKey = `${hex.q},${hex.r}`;
    const tile = tilesMap.get(tileKey);
    
    if (currentTool === "select") {
      // 切换选中状态
      const newSelected = new Set(selectedTiles);
      if (newSelected.has(tileKey)) {
        newSelected.delete(tileKey);
      } else {
        newSelected.add(tileKey);
      }
      setSelectedTiles(newSelected);
      onTileClick?.(tile || null);
    } else if (currentTool === "erase") {
      deleteTile(hex.q, hex.r);
    }
  };
  
  const handleContextMenu = (e: React.MouseEvent) => {
    e.preventDefault();
    const hex = getTileFromPixel(e.clientX, e.clientY);
    if (hex) {
      const tile = tilesMap.get(`${hex.q},${hex.r}`);
      onTileContextMenu?.(tile || null, e.clientX, e.clientY);
    }
  };
  
  const handleWheel = (e: React.WheelEvent) => {
    e.preventDefault();
    const delta = e.deltaY > 0 ? 0.9 : 1.1;
    setCamera((prev) => ({
      ...prev,
      zoom: Math.max(MIN_ZOOM, Math.min(MAX_ZOOM, prev.zoom * delta)),
    }));
  };
  
  // ==================== 数据操作 ====================
  
  const updateTile = (q: number, r: number, updates: Partial<HexTile>) => {
    const tileKey = `${q},${r}`;
    setMapData((prev) => {
      const existingTile = prev.tiles.find((t) => t.q === q && t.r === r);
      if (existingTile) {
        return {
          ...prev,
          tiles: prev.tiles.map((t) =>
            t.q === q && t.r === r ? { ...t, ...updates } : t
          ),
        };
      } else {
        return {
          ...prev,
          tiles: [
            ...prev.tiles,
            {
              id: `tile-${q}-${r}-${Date.now()}`,
              q,
              r,
              terrain: "grass",
              ...updates,
            },
          ],
        };
      }
    });
  };
  
  const deleteTile = (q: number, r: number) => {
    setMapData((prev) => ({
      ...prev,
      tiles: prev.tiles.filter((t) => !(t.q === q && t.r === r)),
    }));
  };
  
  const generateRandomMap = () => {
    const terrains: TerrainType[] = ["grass", "desert", "water", "mountain", "snow", "forest"];
    const newTiles: HexTile[] = [];
    const halfWidth = Math.floor(mapData.width / 2);
    const halfHeight = Math.floor(mapData.height / 2);
    
    for (let q = -halfWidth; q <= halfWidth; q++) {
      for (let r = -halfHeight; r <= halfHeight; r++) {
        if (Math.random() > 0.3) {
          newTiles.push({
            id: `tile-${q}-${r}-${Date.now()}`,
            q,
            r,
            terrain: terrains[Math.floor(Math.random() * terrains.length)],
            height: Math.floor(Math.random() * 5),
          });
        }
      }
    }
    
    setMapData((prev) => ({ ...prev, tiles: newTiles }));
    setSelectedTiles(new Set());
    setPathTiles(new Set());
  };
  
  const clearMap = () => {
    setMapData((prev) => ({ ...prev, tiles: [] }));
    setSelectedTiles(new Set());
    setPathTiles(new Set());
    setStartTile(null);
    setEndTile(null);
  };
  
  const exportToJSON = (): string => {
    return JSON.stringify(mapData, null, 2);
  };
  
  const importFromJSON = (json: string) => {
    try {
      const data = JSON.parse(json) as HexMapData;
      setMapData(data);
      setSelectedTiles(new Set());
      setPathTiles(new Set());
    } catch (e) {
      alert("Invalid JSON format");
    }
  };
  
  // ==================== 路径操作 ====================
  
  const setPathStart = (tile: HexTile) => {
    setStartTile(tile);
    updateTile(tile.q, tile.r, { isStart: true, isEnd: false });
    if (endTile) {
      updateTile(endTile.q, endTile.r, { isStart: false, isEnd: true });
    }
  };
  
  const setPathEnd = (tile: HexTile) => {
    setEndTile(tile);
    updateTile(tile.q, tile.r, { isStart: false, isEnd: true });
    if (startTile) {
      updateTile(startTile.q, startTile.r, { isStart: true, isEnd: false });
    }
  };
  
  const calculatePath = () => {
    if (!startTile || !endTile) return;
    
    const path = findPath(startTile, endTile);
    const pathSet = new Set(path.map((t) => `${t.q},${t.r}`));
    setPathTiles(pathSet);
  };
  
  const toggleObstacle = (tile: HexTile) => {
    updateTile(tile.q, tile.r, { isObstacle: !tile.isObstacle });
  };
  
  const addWaypoint = (tile: HexTile) => {
    updateTile(tile.q, tile.r, { isWaypoint: true });
  };
  
  // ==================== 效果 ====================
  
  useEffect(() => {
    render();
  }, [render]);
  
  useEffect(() => {
    const handleResize = () => {
      render();
    };
    window.addEventListener("resize", handleResize);
    return () => window.removeEventListener("resize", handleResize);
  }, [render]);
  
  // ==================== 渲染UI ====================
  
  return (
    <div ref={containerRef} className={`relative ${className}`}>
      {/* 主画布 */}
      <canvas
        ref={canvasRef}
        className="w-full h-full cursor-crosshair"
        onMouseMove={handleMouseMove}
        onMouseDown={handleMouseDown}
        onMouseUp={handleMouseUp}
        onClick={handleClick}
        onContextMenu={handleContextMenu}
        onWheel={handleWheel}
        style={{ imageRendering: "crisp-edges" }}
      />
      
      {/* 悬浮工具栏 */}
      {editable && (
        <div className="absolute top-4 left-4 bg-white rounded-lg shadow-lg p-3 space-y-3">
          <div className="text-sm font-bold text-gray-700">画笔工具</div>
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => setCurrentTool("select")}
              className={`p-2 rounded ${currentTool === "select" ? "bg-blue-500 text-white" : "bg-gray-100"}`}
              title="选择"
            >
              🖱️
            </button>
            {Object.entries(TERRAIN_COLORS).map(([type, color]) => (
              <button
                key={type}
                onClick={() => setCurrentTool(type as TerrainType)}
                className={`w-8 h-8 rounded border-2 ${currentTool === type ? "border-blue-500" : "border-transparent"}`}
                style={{ backgroundColor: color }}
                title={TERRAIN_NAMES[type as TerrainType]}
              />
            ))}
            <button
              onClick={() => setCurrentTool("erase")}
              className={`p-2 rounded ${currentTool === "erase" ? "bg-red-500 text-white" : "bg-gray-100"}`}
              title="擦除"
            >
              🗑️
            </button>
          </div>
          
          <div className="border-t pt-2">
            <div className="text-sm font-bold text-gray-700 mb-2">操作</div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={generateRandomMap}
                className="px-3 py-1 bg-green-500 text-white rounded text-sm hover:bg-green-600"
              >
                随机生成
              </button>
              <button
                onClick={clearMap}
                className="px-3 py-1 bg-red-500 text-white rounded text-sm hover:bg-red-600"
              >
                清空
              </button>
              <button
                onClick={() => {
                  const data = exportToJSON();
                  const blob = new Blob([data], { type: "application/json" });
                  const url = URL.createObjectURL(blob);
                  const a = document.createElement("a");
                  a.href = url;
                  a.download = `map-${worldId}.json`;
                  a.click();
                }}
                className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
              >
                导出JSON
              </button>
            </div>
          </div>
          
          <div className="border-t pt-2">
            <div className="text-sm font-bold text-gray-700 mb-2">路径查找</div>
            <div className="flex flex-wrap gap-2">
              <button
                onClick={() => startTile && updateTile(startTile.q, startTile.r, { isStart: false }) && setStartTile(null)}
                className="px-3 py-1 bg-gray-200 rounded text-sm"
                disabled={!startTile}
              >
                清除起点
              </button>
              <button
                onClick={() => endTile && updateTile(endTile.q, endTile.r, { isEnd: false }) && setEndTile(null)}
                className="px-3 py-1 bg-gray-200 rounded text-sm"
                disabled={!endTile}
              >
                清除终点
              </button>
              <button
                onClick={calculatePath}
                className="px-3 py-1 bg-yellow-500 text-white rounded text-sm hover:bg-yellow-600"
                disabled={!startTile || !endTile}
              >
                计算路径
              </button>
            </div>
          </div>
          
          <div className="border-t pt-2">
            <div className="text-sm font-bold text-gray-700 mb-2">显示选项</div>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={showGrid}
                onChange={(e) => setShowGrid(e.target.checked)}
              />
              网格线
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={showCoords}
                onChange={(e) => setShowCoords(e.target.checked)}
              />
              坐标标签
            </label>
            <label className="flex items-center gap-2 text-sm">
              <input
                type="checkbox"
                checked={showHeightShadow}
                onChange={(e) => setShowHeightShadow(e.target.checked)}
              />
              高度阴影
            </label>
          </div>
          
          <div className="border-t pt-2">
            <div className="text-sm font-bold text-gray-700 mb-2">布局</div>
            <div className="flex gap-2">
              <button
                onClick={() => setMapData((prev) => ({ ...prev, layout: "pointy" }))}
                className={`px-3 py-1 rounded text-sm ${mapData.layout === "pointy" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
              >
                点顶式
              </button>
              <button
                onClick={() => setMapData((prev) => ({ ...prev, layout: "flat" }))}
                className={`px-3 py-1 rounded text-sm ${mapData.layout === "flat" ? "bg-blue-500 text-white" : "bg-gray-200"}`}
              >
                平顶式
              </button>
            </div>
          </div>
        </div>
      )}
      
      {/* 迷你地图 */}
      <MiniMap
        mapData={mapData}
        camera={camera}
        hexSize={hexSize}
        containerSize={containerRef.current?.getBoundingClientRect()}
      />
      
      {/* 坐标标尺 */}
      <div className="absolute bottom-4 left-4 bg-white rounded px-3 py-2 shadow-lg text-sm font-mono">
        <div>屏幕: ({Math.round(mousePos.x)}, {Math.round(mousePos.y)})</div>
        <div>网格: ({mousePos.q}, {mousePos.r})</div>
        <div>缩放: {(camera.zoom * 100).toFixed(0)}%</div>
      </div>
      
      {/* 悬停提示 */}
      {hoveredTile && (
        <Tooltip tile={hoveredTile} x={mousePos.x} y={mousePos.y} containerRef={containerRef} />
      )}
    </div>
  );
};

// ==================== 迷你地图组件 ====================

interface MiniMapProps {
  mapData: HexMapData;
  camera: CameraState;
  hexSize: number;
  containerSize?: DOMRect;
}

const MiniMap: React.FC<MiniMapProps> = ({ mapData, camera, hexSize, containerSize }) => {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    
    // 设置尺寸
    canvas.width = 200;
    canvas.height = 200;
    
    // 清空
    ctx.fillStyle = "#1e293b";
    ctx.fillRect(0, 0, 200, 200);
    
    // 计算缩放比例
    const miniHexSize = 4;
    const scale = miniHexSize / hexSize;
    
    // 绘制所有瓦片
    const centerX = 100;
    const centerY = 100;
    
    mapData.tiles.forEach((tile) => {
      const pixel = hexToPixel(tile.q, tile.r, miniHexSize * 4, mapData.layout);
      const corners = getHexCorners(centerX + pixel.x, centerY + pixel.y, miniHexSize * 3.5, mapData.layout);
      
      ctx.beginPath();
      ctx.moveTo(corners[0].x, corners[0].y);
      for (let i = 1; i < 6; i++) {
        ctx.lineTo(corners[i].x, corners[i].y);
      }
      ctx.closePath();
      
      ctx.fillStyle = TERRAIN_COLORS[tile.terrain] || "#e5e7eb";
      ctx.fill();
    });
    
    // 绘制视口框
    if (containerSize) {
      const viewWidth = (containerSize.width / camera.zoom) * scale * 4;
      const viewHeight = (containerSize.height / camera.zoom) * scale * 4;
      const viewX = centerX + (-camera.x / camera.zoom) * scale;
      const viewY = centerY + (-camera.y / camera.zoom) * scale;
      
      ctx.strokeStyle = "#f97316";
      ctx.lineWidth = 2;
      ctx.strokeRect(viewX - viewWidth / 2, viewY - viewHeight / 2, viewWidth, viewHeight);
    }
  }, [mapData, camera, hexSize, containerSize]);
  
  return (
    <div className="absolute top-4 right-4 bg-white rounded-lg shadow-lg p-2">
      <div className="text-xs font-bold text-gray-700 mb-1">迷你地图</div>
      <canvas ref={canvasRef} width={200} height={200} className="w-[150px] h-[150px]" />
    </div>
  );
};

// ==================== Tooltip组件 ====================

interface TooltipProps {
  tile: HexTile;
  x: number;
  y: number;
  containerRef: React.RefObject<HTMLDivElement>;
}

const Tooltip: React.FC<TooltipProps> = ({ tile, x, y, containerRef }) => {
  if (!containerRef.current) return null;
  
  const rect = containerRef.current.getBoundingClientRect();
  const tooltipX = Math.min(x + 20, rect.width - 200);
  const tooltipY = Math.min(y + 20, rect.height - 150);
  
  return (
    <div
      className="absolute bg-white rounded-lg shadow-lg p-3 text-sm z-50 pointer-events-none"
      style={{ left: tooltipX, top: tooltipY }}
    >
      <div className="font-bold text-gray-800">
        {tile.label || TERRAIN_NAMES[tile.terrain]}
      </div>
      <div className="text-gray-500 text-xs">坐标: ({tile.q}, {tile.r})</div>
      {tile.height !== undefined && (
        <div className="text-gray-600">高度: {tile.height}</div>
      )}
      {tile.resource && (
        <div className="text-blue-600">资源: {tile.resource}</div>
      )}
      {tile.isObstacle && (
        <div className="text-red-500 text-xs">🚫 障碍物</div>
      )}
      {tile.isStart && (
        <div className="text-green-500 text-xs">🚀 起点</div>
      )}
      {tile.isEnd && (
        <div className="text-red-500 text-xs">🎯 终点</div>
      )}
      {tile.isWaypoint && (
        <div className="text-yellow-500 text-xs">📍 路径点</div>
      )}
    </div>
  );
};

export default HexMapCanvas;
