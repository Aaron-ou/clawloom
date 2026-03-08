"use client";

import { useEffect, useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { WorldAPI, TimelineAPI } from "@/lib/api";

interface Snapshot {
  tick: number;
  timestamp: string;
  summary?: string;
  event_count?: number;
}

export default function WorldTimelinePage() {
  const params = useParams();
  const worldId = params.id as string;

  const [world, setWorld] = useState<any>(null);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [selectedTick, setSelectedTick] = useState<number | null>(null);

  const loadData = useCallback(async () => {
    try {
      setLoading(true);
      const [worldData, timelineData] = await Promise.all([
        WorldAPI.get(worldId),
        TimelineAPI.get(worldId),
      ]);
      
      setWorld(worldData);
      // 处理时间线数据，按 tick 排序
      const timelineSnapshots = timelineData.snapshots || timelineData || [];
      setSnapshots(timelineSnapshots.sort((a: Snapshot, b: Snapshot) => b.tick - a.tick));
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载时间线失败");
    } finally {
      setLoading(false);
    }
  }, [worldId]);

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

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载时间线...</p>
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
            onClick={loadData}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            重试
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <Link
                href={`/worlds/${worldId}`}
                className="text-blue-600 hover:text-blue-800 mb-2 inline-block"
              >
                ← 返回世界
              </Link>
              <h1 className="text-3xl font-bold text-gray-900">
                {world?.name} - 时间线
              </h1>
              <p className="mt-1 text-gray-600">回顾世界的演变历程</p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">当前 Tick</p>
              <p className="text-3xl font-bold text-blue-600">
                {world?.current_tick || 0}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：时间线列表 */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold">历史快照</h2>
                <p className="text-sm text-gray-500 mt-1">
                  共 {snapshots.length} 个记录点
                </p>
              </div>
              
              {snapshots.length === 0 ? (
                <div className="px-6 py-12 text-center">
                  <div className="text-4xl mb-4">📜</div>
                  <p className="text-gray-500">暂无时间线记录</p>
                  <p className="text-sm text-gray-400 mt-2">
                    世界还没有开始演化，推进 tick 后将生成记录
                  </p>
                </div>
              ) : (
                <div className="divide-y max-h-[calc(100vh-300px)] overflow-auto">
                  {snapshots.map((snapshot, index) => (
                    <div
                      key={snapshot.tick}
                      className={`px-6 py-4 hover:bg-gray-50 cursor-pointer transition-colors ${
                        selectedTick === snapshot.tick ? "bg-blue-50 border-l-4 border-blue-500" : ""
                      }`}
                      onClick={() => setSelectedTick(snapshot.tick)}
                    >
                      <div className="flex items-start space-x-4">
                        {/* 时间标记 */}
                        <div className="flex-shrink-0 w-16 text-center">
                          <div className="text-2xl font-bold text-blue-600">
                            #{snapshot.tick}
                          </div>
                          {index === 0 && (
                            <span className="text-xs text-green-600 font-medium">
                              最新
                            </span>
                          )}
                        </div>

                        {/* 内容 */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center space-x-2 text-sm text-gray-500 mb-1">
                            <span>🕐 {formatDate(snapshot.timestamp)}</span>
                            {snapshot.event_count !== undefined && (
                              <span className="px-2 py-0.5 bg-gray-100 rounded text-xs">
                                {snapshot.event_count} 事件
                              </span>
                            )}
                          </div>
                          <p className="text-gray-700">
                            {snapshot.summary || "该 tick 无详细描述"}
                          </p>
                        </div>

                        {/* 箭头 */}
                        <div className="flex-shrink-0 text-gray-400">
                          <svg
                            className="w-5 h-5"
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M9 5l7 7-7 7"
                            />
                          </svg>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* 右侧：详情面板 */}
          <div>
            <div className="bg-white rounded-lg shadow sticky top-8">
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold">
                  {selectedTick ? `Tick #${selectedTick} 详情` : "快照详情"}
                </h2>
              </div>
              
              {selectedTick ? (
                <div className="p-6">
                  {(() => {
                    const snapshot = snapshots.find(s => s.tick === selectedTick);
                    if (!snapshot) return null;
                    return (
                      <>
                        <div className="mb-4">
                          <span className="text-sm text-gray-500">时间标记</span>
                          <p className="text-xl font-bold text-blue-600">
                            Tick #{snapshot.tick}
                          </p>
                        </div>
                        
                        <div className="mb-4">
                          <span className="text-sm text-gray-500">记录时间</span>
                          <p className="text-gray-700">{formatDate(snapshot.timestamp)}</p>
                        </div>

                        {snapshot.event_count !== undefined && (
                          <div className="mb-4">
                            <span className="text-sm text-gray-500">事件数量</span>
                            <p className="text-gray-700">{snapshot.event_count} 个事件</p>
                          </div>
                        )}

                        <div className="mb-4">
                          <span className="text-sm text-gray-500">快照摘要</span>
                          <p className="text-gray-700 mt-1">
                            {snapshot.summary || "该 tick 无详细描述"}
                          </p>
                        </div>

                        <div className="mt-6 pt-4 border-t">
                          <Link
                            href={`/worlds/${worldId}?tick=${selectedTick}`}
                            className="block w-full text-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
                          >
                            查看该时刻世界状态
                          </Link>
                        </div>
                      </>
                    );
                  })()}
                </div>
              ) : (
                <div className="px-6 py-12 text-center">
                  <div className="text-4xl mb-4">📋</div>
                  <p className="text-gray-500">点击左侧快照查看详情</p>
                </div>
              )}
            </div>

            {/* 快捷导航 */}
            <div className="bg-white rounded-lg shadow mt-6 p-6">
              <h3 className="text-sm font-semibold text-gray-900 mb-4">快捷导航</h3>
              <div className="space-y-2">
                <Link
                  href={`/worlds/${worldId}`}
                  className="block px-4 py-2 bg-gray-50 text-gray-700 rounded hover:bg-gray-100"
                >
                  🏠 世界详情
                </Link>
                <Link
                  href={`/worlds/${worldId}/map`}
                  className="block px-4 py-2 bg-green-50 text-green-700 rounded hover:bg-green-100"
                >
                  🗺️ 查看地图
                </Link>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
