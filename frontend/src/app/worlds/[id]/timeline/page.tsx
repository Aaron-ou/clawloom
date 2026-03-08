"use client";

import { useEffect, useState, useCallback, useRef } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { WorldAPI, TimelineAPI } from "@/lib/api";

interface Snapshot {
  tick: number;
  timestamp: string;
  summary?: string;
  event_count?: number;
  event_types?: Record<string, number>;
}

interface TimelineData {
  world_id: string;
  current_tick: number;
  start_tick: number;
  end_tick: number;
  timeline: Snapshot[];
}

// 事件类型颜色映射
const EVENT_TYPE_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  conflict: { bg: "bg-red-100", text: "text-red-700", border: "border-red-300" },
  decision: { bg: "bg-blue-100", text: "text-blue-700", border: "border-blue-300" },
  interaction: { bg: "bg-green-100", text: "text-green-700", border: "border-green-300" },
  movement: { bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-300" },
  birth: { bg: "bg-pink-100", text: "text-pink-700", border: "border-pink-300" },
  death: { bg: "bg-gray-100", text: "text-gray-700", border: "border-gray-300" },
  discovery: { bg: "bg-purple-100", text: "text-purple-700", border: "border-purple-300" },
  default: { bg: "bg-slate-100", text: "text-slate-700", border: "border-slate-300" },
};

// 事件类型图标
const EVENT_TYPE_ICONS: Record<string, string> = {
  conflict: "⚔️",
  decision: "🤔",
  interaction: "🤝",
  movement: "🚶",
  birth: "👶",
  death: "💀",
  discovery: "🔍",
  default: "📌",
};

export default function WorldTimelinePage() {
  const params = useParams();
  const router = useRouter();
  const worldId = params.id as string;

  const [world, setWorld] = useState<any>(null);
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedTick, setSelectedTick] = useState<number | null>(null);
  const [hoveredTick, setHoveredTick] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>("all");
  const timelineRef = useRef<HTMLDivElement>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [worldData, timelineRes] = await Promise.all([
        WorldAPI.get(worldId),
        TimelineAPI.get(worldId),
      ]);
      
      setWorld(worldData);
      
      const data = timelineRes as TimelineData;
      setTimelineData(data);
      
      // 按 tick 降序排列
      const sortedSnapshots = (data.timeline || []).sort((a: Snapshot, b: Snapshot) => b.tick - a.tick);
      setSnapshots(sortedSnapshots);
      
      // 默认选中最新的
      if (sortedSnapshots.length > 0 && !selectedTick) {
        setSelectedTick(sortedSnapshots[0].tick);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载时间线失败");
    } finally {
      setLoading(false);
    }
  }, [worldId, selectedTick]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const formatDate = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return date.toLocaleString("zh-CN", {
        month: "short",
        day: "numeric",
        hour: "2-digit",
        minute: "2-digit",
      });
    } catch {
      return "未知时间";
    }
  };

  const formatRelativeTime = (tick: number, currentTick: number) => {
    const diff = currentTick - tick;
    if (diff === 0) return "当前";
    if (diff === 1) return "1 tick前";
    return `${diff} ticks前`;
  };

  const getEventTypeColor = (eventType: string) => {
    return EVENT_TYPE_COLORS[eventType] || EVENT_TYPE_COLORS.default;
  };

  const getEventTypeIcon = (eventType: string) => {
    return EVENT_TYPE_ICONS[eventType] || EVENT_TYPE_ICONS.default;
  };

  const getDominantEventType = (eventTypes?: Record<string, number>) => {
    if (!eventTypes || Object.keys(eventTypes).length === 0) return null;
    return Object.entries(eventTypes).sort((a, b) => b[1] - a[1])[0][0];
  };

  // 过滤快照
  const filteredSnapshots = snapshots.filter((snapshot) => {
    if (filter === "all") return true;
    const dominantType = getDominantEventType(snapshot.event_types);
    return dominantType === filter;
  });

  // 计算进度百分比
  const getProgressPercent = (tick: number) => {
    if (!timelineData || timelineData.end_tick === timelineData.start_tick) return 0;
    return ((tick - timelineData.start_tick) / (timelineData.end_tick - timelineData.start_tick)) * 100;
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center">
          <div className="relative w-20 h-20 mx-auto mb-6">
            <div className="absolute inset-0 border-4 border-blue-500/20 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-blue-500 border-t-transparent rounded-full animate-spin"></div>
            <div className="absolute inset-0 flex items-center justify-center text-2xl">⏳</div>
          </div>
          <p className="text-blue-400 text-lg">加载时间线...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-6xl mb-4">⚠️</div>
          <p className="text-red-400 text-lg mb-6">{error}</p>
          <button
            onClick={loadData}
            className="px-6 py-3 bg-blue-600 text-white rounded-xl hover:bg-blue-700 transition-all"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  const selectedSnapshot = snapshots.find(s => s.tick === selectedTick);

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900 text-white">
      {/* 背景装饰 */}
      <div className="fixed inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-500/10 rounded-full blur-3xl"></div>
        <div className="absolute bottom-0 right-1/4 w-96 h-96 bg-purple-500/10 rounded-full blur-3xl"></div>
      </div>

      {/* Header */}
      <header className="relative z-10 bg-slate-800/50 backdrop-blur-lg border-b border-slate-700/50">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <Link
                href={`/worlds/${worldId}`}
                className="text-blue-400 hover:text-blue-300 mb-2 inline-flex items-center gap-2 transition-colors"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
                返回世界
              </Link>
              <h1 className="text-3xl font-bold bg-gradient-to-r from-blue-400 to-purple-400 bg-clip-text text-transparent">
                {world?.name}
              </h1>
              <p className="mt-1 text-slate-400">世界时间线</p>
            </div>
            
            {/* 当前Tick大数字显示 */}
            <div className="text-right">
              <p className="text-sm text-slate-400 mb-1">当前 Tick</p>
              <div className="relative">
                <span className="text-5xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
                  {world?.current_tick || 0}
                </span>
                <div className="absolute -bottom-2 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>
      </header>

      <main className="relative z-10 max-w-7xl mx-auto px-4 py-8">
        {/* 过滤器 */}
        <div className="mb-8 flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2 bg-slate-800/50 backdrop-blur rounded-xl p-2 border border-slate-700/50">
            <span className="text-sm text-slate-400 px-3">筛选事件:</span>
            {[
              { key: "all", label: "全部", icon: "🌟" },
              { key: "conflict", label: "冲突", icon: "⚔️" },
              { key: "decision", label: "决策", icon: "🤔" },
              { key: "interaction", label: "互动", icon: "🤝" },
              { key: "discovery", label: "发现", icon: "🔍" },
            ].map(({ key, label, icon }) => (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all ${
                  filter === key
                    ? "bg-blue-600 text-white shadow-lg shadow-blue-500/25"
                    : "text-slate-300 hover:bg-slate-700/50"
                }`}
              >
                <span className="mr-1">{icon}</span>
                {label}
              </button>
            ))}
          </div>
          
          <div className="text-slate-400 text-sm">
            共 <span className="text-white font-bold">{filteredSnapshots.length}</span> 个记录
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* 左侧：时间线可视化 */}
          <div className="lg:col-span-8">
            {filteredSnapshots.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700/50 p-12 text-center">
                <div className="text-6xl mb-4">📜</div>
                <p className="text-slate-300 text-lg">暂无时间线记录</p>
                <p className="text-slate-500 mt-2">
                  世界还没有开始演化，推进 tick 后将生成记录
                </p>
              </div>
            ) : (
              <div 
                ref={timelineRef}
                className="relative bg-slate-800/30 backdrop-blur rounded-2xl border border-slate-700/50 p-8"
              >
                {/* 时间线主轴 */}
                <div className="absolute left-16 top-8 bottom-8 w-1 bg-gradient-to-b from-blue-500/50 via-purple-500/50 to-blue-500/50 rounded-full"></div>
                
                {/* 时间线节点 */}
                <div className="space-y-6">
                  {filteredSnapshots.map((snapshot, index) => {
                    const isSelected = selectedTick === snapshot.tick;
                    const isHovered = hoveredTick === snapshot.tick;
                    const dominantEventType = getDominantEventType(snapshot.event_types);
                    const eventColors = getEventTypeColor(dominantEventType || "default");
                    const isLatest = index === 0;
                    
                    return (
                      <div
                        key={snapshot.tick}
                        className={`relative flex items-start gap-6 cursor-pointer transition-all duration-300 ${
                          isSelected ? "scale-[1.02]" : "hover:scale-[1.01]"
                        }`}
                        onClick={() => setSelectedTick(snapshot.tick)}
                        onMouseEnter={() => setHoveredTick(snapshot.tick)}
                        onMouseLeave={() => setHoveredTick(null)}
                      >
                        {/* 左侧：Tick标记 */}
                        <div className="relative flex-shrink-0 w-16 flex flex-col items-center">
                          {/* 节点圆圈 */}
                          <div 
                            className={`w-10 h-10 rounded-full flex items-center justify-center text-sm font-bold transition-all duration-300 z-10 ${
                              isSelected
                                ? "bg-blue-500 text-white shadow-lg shadow-blue-500/50 scale-110"
                                : isLatest
                                ? "bg-gradient-to-br from-green-400 to-emerald-500 text-white shadow-lg shadow-green-500/30"
                                : `${eventColors.bg} ${eventColors.text} border-2 ${eventColors.border}`
                            }`}
                          >
                            {isLatest ? "★" : getEventTypeIcon(dominantEventType || "default")}
                          </div>
                          
                          {/* Tick数字 */}
                          <span className={`mt-2 text-sm font-mono ${
                            isSelected ? "text-blue-400" : "text-slate-500"
                          }`}>
                            #{snapshot.tick}
                          </span>
                        </div>

                        {/* 右侧：内容卡片 */}
                        <div 
                          className={`flex-1 rounded-xl p-5 transition-all duration-300 border ${
                            isSelected
                              ? "bg-slate-700/80 border-blue-500/50 shadow-xl shadow-blue-500/10"
                              : isHovered
                              ? "bg-slate-700/50 border-slate-600/50"
                              : "bg-slate-800/50 border-slate-700/30"
                          }`}
                        >
                          {/* 头部信息 */}
                          <div className="flex items-center justify-between mb-3">
                            <div className="flex items-center gap-3">
                              {isLatest && (
                                <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full font-medium">
                                  最新
                                </span>
                              )}
                              <span className="text-slate-400 text-sm flex items-center gap-1">
                                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                                </svg>
                                {formatDate(snapshot.timestamp)}
                              </span>
                            </div>
                            
                            {snapshot.event_count !== undefined && snapshot.event_count > 0 && (
                              <span className={`px-3 py-1 rounded-full text-xs font-medium ${eventColors.bg} ${eventColors.text}`}>
                                {snapshot.event_count} 个事件
                              </span>
                            )}
                          </div>

                          {/* 摘要 */}
                          <p className={`text-base leading-relaxed ${
                            isSelected ? "text-white" : "text-slate-300"
                          }`}>
                            {snapshot.summary || "该时刻没有重要事件记录"}
                          </p>

                          {/* 事件类型分布 */}
                          {snapshot.event_types && Object.keys(snapshot.event_types).length > 0 && (
                            <div className="mt-4 flex flex-wrap gap-2">
                              {Object.entries(snapshot.event_types).map(([type, count]) => (
                                <span 
                                  key={type}
                                  className={`px-2 py-1 rounded text-xs ${getEventTypeColor(type).bg} ${getEventTypeColor(type).text}`}
                                >
                                  {getEventTypeIcon(type)} {type}: {count}
                                </span>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* 右侧：详情面板 */}
          <div className="lg:col-span-4">
            <div className="sticky top-8 space-y-6">
              {/* 详情卡片 */}
              <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700/50 overflow-hidden">
                <div className="px-6 py-4 border-b border-slate-700/50 bg-gradient-to-r from-slate-800 to-slate-700/50">
                  <h2 className="text-lg font-semibold flex items-center gap-2">
                    <span className="text-blue-400">📋</span>
                    {selectedSnapshot ? `Tick #${selectedTick} 详情` : "选择时刻"}
                  </h2>
                </div>
                
                {selectedSnapshot ? (
                  <div className="p-6 space-y-5">
                    {/* Tick大数字 */}
                    <div className="text-center p-4 bg-slate-700/30 rounded-xl">
                      <span className="text-4xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-blue-400 to-cyan-400">
                        #{selectedSnapshot.tick}
                      </span>
                      <p className="text-slate-400 text-sm mt-1">
                        {formatRelativeTime(selectedSnapshot.tick, world?.current_tick || 0)}
                      </p>
                    </div>

                    {/* 时间 */}
                    <div>
                      <span className="text-sm text-slate-400">记录时间</span>
                      <p className="text-white flex items-center gap-2 mt-1">
                        <svg className="w-4 h-4 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
                        </svg>
                        {formatDate(selectedSnapshot.timestamp)}
                      </p>
                    </div>

                    {/* 事件统计 */}
                    {selectedSnapshot.event_count !== undefined && (
                      <div>
                        <span className="text-sm text-slate-400">事件统计</span>
                        <div className="mt-2 flex items-center gap-3">
                          <div className="flex-1 h-2 bg-slate-700 rounded-full overflow-hidden">
                            <div 
                              className="h-full bg-gradient-to-r from-blue-500 to-cyan-500 rounded-full"
                              style={{ width: `${Math.min((selectedSnapshot.event_count / 10) * 100, 100)}%` }}
                            ></div>
                          </div>
                          <span className="text-white font-bold">{selectedSnapshot.event_count}</span>
                        </div>
                      </div>
                    )}

                    {/* 事件类型饼图效果 */}
                    {selectedSnapshot.event_types && Object.keys(selectedSnapshot.event_types).length > 0 && (
                      <div>
                        <span className="text-sm text-slate-400">事件分布</span>
                        <div className="mt-3 space-y-2">
                          {Object.entries(selectedSnapshot.event_types).map(([type, count]) => {
                            const colors = getEventTypeColor(type);
                            const total = Object.values(selectedSnapshot.event_types!).reduce((a, b) => a + b, 0);
                            const percent = (count / total) * 100;
                            return (
                              <div key={type} className="flex items-center gap-3">
                                <span className="text-lg">{getEventTypeIcon(type)}</span>
                                <div className="flex-1">
                                  <div className="flex items-center justify-between text-sm mb-1">
                                    <span className="text-slate-300 capitalize">{type}</span>
                                    <span className="text-slate-400">{count} ({Math.round(percent)}%)</span>
                                  </div>
                                  <div className="h-1.5 bg-slate-700 rounded-full overflow-hidden">
                                    <div 
                                      className={`h-full rounded-full ${colors.bg.replace('bg-', 'bg-').replace('100', '500')}`}
                                      style={{ width: `${percent}%` }}
                                    ></div>
                                  </div>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    )}

                    {/* 摘要 */}
                    <div>
                      <span className="text-sm text-slate-400">摘要</span>
                      <p className="text-slate-300 mt-1 text-sm leading-relaxed">
                        {selectedSnapshot.summary || "该 tick 无详细描述"}
                      </p>
                    </div>

                    {/* 操作按钮 */}
                    <div className="pt-4 border-t border-slate-700/50 space-y-2">
                      <Link
                        href={`/worlds/${worldId}?tick=${selectedTick}`}
                        className="flex items-center justify-center gap-2 w-full px-4 py-3 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-all font-medium"
                      >
                        <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                        </svg>
                        查看该时刻世界状态
                      </Link>
                      
                      {selectedSnapshot.tick > 0 && (
                        <button
                          onClick={() => setSelectedTick(selectedSnapshot.tick - 1)}
                          className="flex items-center justify-center gap-2 w-full px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-xl transition-all text-sm"
                        >
                          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                          </svg>
                          查看上一时刻
                        </button>
                      )}
                    </div>
                  </div>
                ) : (
                  <div className="px-6 py-12 text-center">
                    <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-slate-700/50 flex items-center justify-center text-3xl">
                      👆
                    </div>
                    <p className="text-slate-400">点击左侧时间线节点<br/>查看详细信息</p>
                  </div>
                )}
              </div>

              {/* 快捷导航 */}
              <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700/50 p-6">
                <h3 className="text-sm font-semibold text-slate-300 mb-4">快捷导航</h3>
                <div className="space-y-3">
                  <Link
                    href={`/worlds/${worldId}`}
                    className="flex items-center gap-3 px-4 py-3 bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 rounded-xl transition-all group"
                  >
                    <span className="w-10 h-10 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                      🏠
                    </span>
                    <span>世界详情</span>
                  </Link>
                  <Link
                    href={`/worlds/${worldId}/map`}
                    className="flex items-center gap-3 px-4 py-3 bg-slate-700/50 hover:bg-slate-600/50 text-slate-300 rounded-xl transition-all group"
                  >
                    <span className="w-10 h-10 rounded-lg bg-green-500/20 text-green-400 flex items-center justify-center group-hover:scale-110 transition-transform">
                      🗺️
                    </span>
                    <span>查看地图</span>
                  </Link>
                </div>
              </div>

              {/* 统计信息 */}
              {timelineData && (
                <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700/50 p-6">
                  <h3 className="text-sm font-semibold text-slate-300 mb-4">时间线统计</h3>
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center p-3 bg-slate-700/30 rounded-xl">
                      <div className="text-2xl font-bold text-blue-400">{timelineData.start_tick}</div>
                      <div className="text-xs text-slate-400">起始 Tick</div>
                    </div>
                    <div className="text-center p-3 bg-slate-700/30 rounded-xl">
                      <div className="text-2xl font-bold text-purple-400">{timelineData.end_tick}</div>
                      <div className="text-xs text-slate-400">结束 Tick</div>
                    </div>
                    <div className="text-center p-3 bg-slate-700/30 rounded-xl col-span-2">
                      <div className="text-2xl font-bold text-green-400">{snapshots.length}</div>
                      <div className="text-xs text-slate-400">记录总数</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
