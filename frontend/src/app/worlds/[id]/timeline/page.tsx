"use client";

import { useEffect, useState, useCallback } from "react";
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

interface EventDetail {
  id: string;
  type: string;
  title: string;
  description?: string;
  participants?: string[];
  location_id?: string;
  outcome?: any;
  world_changes?: any;
  created_at?: string;
}

interface RoleDetail {
  id: string;
  name: string;
  status: string;
  health: number;
  influence: number;
  location_id?: string;
  card?: any;
  recent_memories?: {
    tick: number;
    type: string;
    content: string;
  }[];
}

interface WorldChange {
  type: string;
  description: string;
  role_id?: string;
  role_name?: string;
  from?: string;
  to?: string;
  diff?: number;
}

interface TickDetails {
  world_id: string;
  tick: number;
  world: {
    tick: number;
    timestamp?: string;
    summary?: string;
    role_count: number;
    event_count: number;
    changes_from_previous: WorldChange[];
  };
  events: EventDetail[];
  roles: RoleDetail[];
  previous_tick?: number;
}

// 事件类型颜色映射
const EVENT_TYPE_COLORS: Record<string, { bg: string; text: string; border: string; icon: string }> = {
  conflict: { bg: "bg-red-100", text: "text-red-700", border: "border-red-300", icon: "⚔️" },
  decision: { bg: "bg-blue-100", text: "text-blue-700", border: "border-blue-300", icon: "🤔" },
  interaction: { bg: "bg-green-100", text: "text-green-700", border: "border-green-300", icon: "🤝" },
  movement: { bg: "bg-amber-100", text: "text-amber-700", border: "border-amber-300", icon: "🚶" },
  birth: { bg: "bg-pink-100", text: "text-pink-700", border: "border-pink-300", icon: "👶" },
  death: { bg: "bg-gray-100", text: "text-gray-700", border: "border-gray-300", icon: "💀" },
  discovery: { bg: "bg-purple-100", text: "text-purple-700", border: "border-purple-300", icon: "🔍" },
  default: { bg: "bg-slate-100", text: "text-slate-700", border: "border-slate-300", icon: "📌" },
};

const ROLE_STATUS_COLORS: Record<string, string> = {
  ACTIVE: "text-green-400",
  INACTIVE: "text-gray-400",
  DECEASED: "text-red-400",
  MISSING: "text-yellow-400",
};

export default function WorldTimelinePage() {
  const params = useParams();
  const worldId = params.id as string;

  const [world, setWorld] = useState<any>(null);
  const [timelineData, setTimelineData] = useState<TimelineData | null>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedTick, setSelectedTick] = useState<number | null>(null);
  const [hoveredTick, setHoveredTick] = useState<number | null>(null);
  const [filter, setFilter] = useState<string>("all");
  
  // Tick 详情
  const [tickDetails, setTickDetails] = useState<TickDetails | null>(null);
  const [loadingDetails, setLoadingDetails] = useState(false);
  const [activeTab, setActiveTab] = useState<"events" | "roles" | "changes">("events");

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
      
      const sortedSnapshots = (data.timeline || []).sort((a: Snapshot, b: Snapshot) => b.tick - a.tick);
      setSnapshots(sortedSnapshots);
      
      if (sortedSnapshots.length > 0 && !selectedTick) {
        setSelectedTick(sortedSnapshots[0].tick);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载时间线失败");
    } finally {
      setLoading(false);
    }
  }, [worldId, selectedTick]);

  // 加载 tick 详情
  const loadTickDetails = useCallback(async (tick: number) => {
    if (!tick) return;
    try {
      setLoadingDetails(true);
      const response = await fetch(`http://localhost:8000/worlds/${worldId}/timeline/${tick}`);
      if (response.ok) {
        const data = await response.json();
        setTickDetails(data);
      }
    } catch (err) {
      console.error("Failed to load tick details:", err);
    } finally {
      setLoadingDetails(false);
    }
  }, [worldId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  useEffect(() => {
    if (selectedTick) {
      loadTickDetails(selectedTick);
    }
  }, [selectedTick, loadTickDetails]);

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

  const getEventTypeStyle = (eventType: string) => {
    return EVENT_TYPE_COLORS[eventType] || EVENT_TYPE_COLORS.default;
  };

  const getDominantEventType = (eventTypes?: Record<string, number>) => {
    if (!eventTypes || Object.keys(eventTypes).length === 0) return null;
    return Object.entries(eventTypes).sort((a, b) => b[1] - a[1])[0][0];
  };

  const filteredSnapshots = snapshots.filter((snapshot) => {
    if (filter === "all") return true;
    const dominantType = getDominantEventType(snapshot.event_types);
    return dominantType === filter;
  });

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
              <p className="mt-1 text-slate-400">世界时间线 - 探索每个时刻的故事</p>
            </div>
            
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
          {/* 左侧：时间线列表 */}
          <div className="lg:col-span-5">
            {filteredSnapshots.length === 0 ? (
              <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700/50 p-12 text-center">
                <div className="text-6xl mb-4">📜</div>
                <p className="text-slate-300 text-lg">暂无时间线记录</p>
                <p className="text-slate-500 mt-2">
                  世界还没有开始演化，推进 tick 后将生成记录
                </p>
              </div>
            ) : (
              <div className="relative bg-slate-800/30 backdrop-blur rounded-2xl border border-slate-700/50 p-6 max-h-[calc(100vh-250px)] overflow-auto">
                {/* 时间线主轴 */}
                <div className="absolute left-12 top-6 bottom-6 w-0.5 bg-gradient-to-b from-blue-500/50 via-purple-500/50 to-blue-500/50"></div>
                
                {/* 时间线节点 */}
                <div className="space-y-4">
                  {filteredSnapshots.map((snapshot, index) => {
                    const isSelected = selectedTick === snapshot.tick;
                    const isHovered = hoveredTick === snapshot.tick;
                    const dominantEventType = getDominantEventType(snapshot.event_types);
                    const style = getEventTypeStyle(dominantEventType || "default");
                    const isLatest = index === 0;
                    
                    return (
                      <div
                        key={snapshot.tick}
                        className={`relative flex items-start gap-4 cursor-pointer transition-all duration-300 ${
                          isSelected ? "scale-[1.02]" : "hover:scale-[1.01]"
                        }`}
                        onClick={() => setSelectedTick(snapshot.tick)}
                        onMouseEnter={() => setHoveredTick(snapshot.tick)}
                        onMouseLeave={() => setHoveredTick(null)}
                      >
                        {/* 节点圆圈 */}
                        <div className="relative flex-shrink-0 w-8 flex flex-col items-center">
                          <div 
                            className={`w-8 h-8 rounded-full flex items-center justify-center text-xs transition-all duration-300 z-10 ${
                              isSelected
                                ? "bg-blue-500 text-white shadow-lg shadow-blue-500/50 scale-110"
                                : isLatest
                                ? "bg-gradient-to-br from-green-400 to-emerald-500 text-white"
                                : `${style.bg} ${style.text} border ${style.border}`
                            }`}
                          >
                            {isLatest ? "★" : style.icon}
                          </div>
                        </div>

                        {/* 内容卡片 */}
                        <div 
                          className={`flex-1 rounded-xl p-4 transition-all duration-300 border ${
                            isSelected
                              ? "bg-slate-700/80 border-blue-500/50 shadow-lg"
                              : isHovered
                              ? "bg-slate-700/50 border-slate-600/50"
                              : "bg-slate-800/50 border-slate-700/30"
                          }`}
                        >
                          <div className="flex items-center justify-between mb-2">
                            <span className="text-lg font-bold text-blue-400">#{snapshot.tick}</span>
                            {isLatest && (
                              <span className="px-2 py-0.5 bg-green-500/20 text-green-400 text-xs rounded-full">
                                最新
                              </span>
                            )}
                          </div>
                          
                          <p className="text-slate-300 text-sm line-clamp-2 mb-2">
                            {snapshot.summary || "该时刻没有重要事件记录"}
                          </p>
                          
                          <div className="flex items-center gap-2 text-xs text-slate-500">
                            <span>{formatDate(snapshot.timestamp)}</span>
                            {snapshot.event_count ? (
                              <span className={`px-2 py-0.5 rounded ${style.bg} ${style.text}`}>
                                {snapshot.event_count} 事件
                              </span>
                            ) : null}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}
          </div>

          {/* 右侧：详情面板 */}
          <div className="lg:col-span-7">
            {loadingDetails ? (
              <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700/50 p-12 text-center">
                <div className="animate-spin w-12 h-12 border-4 border-blue-500 border-t-transparent rounded-full mx-auto mb-4"></div>
                <p className="text-slate-400">加载 Tick #{selectedTick} 详情...</p>
              </div>
            ) : tickDetails ? (
              <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700/50 overflow-hidden">
                {/* 头部 */}
                <div className="px-6 py-4 border-b border-slate-700/50 bg-gradient-to-r from-slate-800 to-slate-700/50">
                  <div className="flex items-center justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-white">
                        Tick #{tickDetails.tick} 详情
                      </h2>
                      <p className="text-slate-400 text-sm mt-1">
                        {tickDetails.world.timestamp ? formatDate(tickDetails.world.timestamp) : "未知时间"}
                        {tickDetails.previous_tick !== undefined && (
                          <span className="ml-2 text-slate-500">(上一 Tick: #{tickDetails.previous_tick})</span>
                        )}
                      </p>
                    </div>
                    <div className="flex gap-3">
                      <div className="text-center px-4 py-2 bg-slate-700/50 rounded-xl">
                        <div className="text-2xl font-bold text-blue-400">{tickDetails.world.event_count}</div>
                        <div className="text-xs text-slate-400">事件</div>
                      </div>
                      <div className="text-center px-4 py-2 bg-slate-700/50 rounded-xl">
                        <div className="text-2xl font-bold text-green-400">{tickDetails.world.role_count}</div>
                        <div className="text-xs text-slate-400">角色</div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Tab 切换 */}
                <div className="flex border-b border-slate-700/50">
                  {[
                    { key: "events", label: "📋 事件详情", count: tickDetails.events.length },
                    { key: "roles", label: "👤 角色状态", count: tickDetails.roles.length },
                    { key: "changes", label: "📊 世界变化", count: tickDetails.world.changes_from_previous?.length || 0 },
                  ].map(({ key, label, count }) => (
                    <button
                      key={key}
                      onClick={() => setActiveTab(key as any)}
                      className={`flex-1 px-4 py-3 text-sm font-medium transition-all ${
                        activeTab === key
                          ? "bg-blue-600/20 text-blue-400 border-b-2 border-blue-500"
                          : "text-slate-400 hover:text-white hover:bg-slate-700/30"
                      }`}
                    >
                      {label}
                      <span className="ml-2 px-2 py-0.5 bg-slate-700 rounded-full text-xs">{count}</span>
                    </button>
                  ))}
                </div>

                {/* 内容区域 */}
                <div className="p-6 max-h-[calc(100vh-400px)] overflow-auto">
                  {/* 事件详情 Tab */}
                  {activeTab === "events" && (
                    <div className="space-y-4">
                      {tickDetails.events.length === 0 ? (
                        <p className="text-slate-500 text-center py-8">该 Tick 没有事件发生</p>
                      ) : (
                        tickDetails.events.map((event, idx) => {
                          const style = getEventTypeStyle(event.type);
                          return (
                            <div key={event.id} className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/30">
                              <div className="flex items-start gap-3">
                                <span className={`w-10 h-10 rounded-lg ${style.bg} ${style.text} flex items-center justify-center text-xl flex-shrink-0`}>
                                  {style.icon}
                                </span>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2 mb-1">
                                    <h3 className="font-semibold text-white">{event.title}</h3>
                                    <span className={`text-xs px-2 py-0.5 rounded ${style.bg} ${style.text}`}>
                                      {event.type}
                                    </span>
                                  </div>
                                  <p className="text-slate-300 text-sm mb-2">{event.description}</p>
                                  
                                  {event.participants && event.participants.length > 0 && (
                                    <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
                                      <span>参与者:</span>
                                      {event.participants.map((p, i) => (
                                        <span key={i} className="px-2 py-0.5 bg-slate-600/50 rounded">{p}</span>
                                      ))}
                                    </div>
                                  )}
                                  
                                  {event.outcome && (
                                    <div className="mt-2 p-2 bg-slate-800/50 rounded text-sm">
                                      <span className="text-slate-400">结果: </span>
                                      <span className="text-slate-300">{JSON.stringify(event.outcome)}</span>
                                    </div>
                                  )}
                                </div>
                              </div>
                            </div>
                          );
                        })
                      )}
                    </div>
                  )}

                  {/* 角色状态 Tab */}
                  {activeTab === "roles" && (
                    <div className="space-y-3">
                      {tickDetails.roles.length === 0 ? (
                        <p className="text-slate-500 text-center py-8">暂无角色数据</p>
                      ) : (
                        tickDetails.roles.map((role) => (
                          <div key={role.id} className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/30">
                            <div className="flex items-center justify-between mb-3">
                              <div className="flex items-center gap-3">
                                <span className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 to-pink-500 flex items-center justify-center text-lg">
                                  {role.card?.avatar || "👤"}
                                </span>
                                <div>
                                  <h3 className="font-semibold text-white">{role.name}</h3>
                                  <span className={`text-xs ${ROLE_STATUS_COLORS[role.status] || "text-slate-400"}`}>
                                    {role.status}
                                  </span>
                                </div>
                              </div>
                              <div className="flex gap-4 text-sm">
                                <div className="text-center">
                                  <div className="text-red-400 font-bold">{role.health}%</div>
                                  <div className="text-xs text-slate-500">生命</div>
                                </div>
                                <div className="text-center">
                                  <div className="text-yellow-400 font-bold">{role.influence}</div>
                                  <div className="text-xs text-slate-500">影响力</div>
                                </div>
                              </div>
                            </div>
                            
                            {role.recent_memories && role.recent_memories.length > 0 && (
                              <div className="mt-3 pt-3 border-t border-slate-600/30">
                                <h4 className="text-xs text-slate-400 mb-2">近期记忆</h4>
                                <div className="space-y-1">
                                  {role.recent_memories.map((memory, idx) => (
                                    <div key={idx} className="text-sm text-slate-300 flex items-center gap-2">
                                      <span className="text-xs text-slate-500">#{memory.tick}</span>
                                      <span className="px-1.5 py-0.5 bg-slate-600/50 rounded text-xs">{memory.type}</span>
                                      <span className="line-clamp-1">{memory.content}</span>
                                    </div>
                                  ))}
                                </div>
                              </div>
                            )}
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {/* 世界变化 Tab */}
                  {activeTab === "changes" && (
                    <div className="space-y-3">
                      {(!tickDetails.world.changes_from_previous || tickDetails.world.changes_from_previous.length === 0) ? (
                        <p className="text-slate-500 text-center py-8">与上一 Tick 相比没有显著变化</p>
                      ) : (
                        tickDetails.world.changes_from_previous.map((change, idx) => (
                          <div key={idx} className="bg-slate-700/30 rounded-xl p-4 border border-slate-600/30">
                            <div className="flex items-center gap-3">
                              <span className="w-8 h-8 rounded-lg bg-blue-500/20 text-blue-400 flex items-center justify-center">
                                {change.type === "role_status_change" ? "🔄" :
                                 change.type === "role_health_change" ? "❤️" :
                                 change.type === "role_count_change" ? "👥" : "📊"}
                              </span>
                              <div className="flex-1">
                                <p className="text-slate-200">
                                  {change.description || (
                                    change.type === "role_status_change" ? (
                                      <>
                                        <span className="font-semibold text-white">{change.role_name}</span>
                                        {" 状态从 "}
                                        <span className="text-slate-400">{change.from}</span>
                                        {" 变为 "}
                                        <span className="text-green-400">{change.to}</span>
                                      </>
                                    ) : change.type === "role_health_change" ? (
                                      <>
                                        <span className="font-semibold text-white">{change.role_name}</span>
                                        {" 生命值变化 "}
                                        <span className={change.diff && change.diff > 0 ? "text-green-400" : "text-red-400"}>
                                          {change.diff && change.diff > 0 ? "+" : ""}{change.diff}
                                        </span>
                                      </>
                                    ) : null
                                  )}
                                </p>
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>

                {/* 底部操作 */}
                <div className="px-6 py-4 border-t border-slate-700/50 bg-slate-800/30 flex gap-3">
                  <Link
                    href={`/worlds/${worldId}?tick=${selectedTick}`}
                    className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl transition-all font-medium"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
                    </svg>
                    查看世界状态
                  </Link>
                  {tickDetails.previous_tick !== undefined && (
                    <button
                      onClick={() => setSelectedTick(tickDetails.previous_tick!)}
                      className="px-4 py-2 bg-slate-700 hover:bg-slate-600 text-slate-300 rounded-xl transition-all"
                    >
                      ← 上一 Tick
                    </button>
                  )}
                </div>
              </div>
            ) : (
              <div className="bg-slate-800/50 backdrop-blur rounded-2xl border border-slate-700/50 p-12 text-center">
                <div className="w-20 h-20 mx-auto mb-4 rounded-full bg-slate-700/50 flex items-center justify-center text-3xl">
                  👆
                </div>
                <p className="text-slate-400">点击左侧时间线节点<br/>查看该时刻的详细信息</p>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  );
}
