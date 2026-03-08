"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { WorldAPI, RoleAPI, EventAPI } from "@/lib/api";

interface UserInfo {
  id: string;
  username: string;
  role: string;
  is_ai: boolean;
  can_tick: boolean;
  can_create: boolean;
  can_divine: boolean;
}

export default function WorldDetailPage() {
  const params = useParams();
  const router = useRouter();
  const worldId = params.id as string;

  const [world, setWorld] = useState<any>(null);
  const [roles, setRoles] = useState<any[]>([]);
  const [events, setEvents] = useState<any[]>([]);
  const [user, setUser] = useState<UserInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  
  // AI操作状态
  const [tickCount, setTickCount] = useState(1);
  const [ticking, setTicking] = useState(false);
  
  // 织主神启状态
  const [selectedRole, setSelectedRole] = useState<any>(null);
  const [divineMessage, setDivineMessage] = useState("");
  const [showDivineModal, setShowDivineModal] = useState(false);

  // 获取当前用户信息
  const loadUser = async () => {
    try {
      const apiKey = localStorage.getItem("api_key");
      if (!apiKey) return null;
      
      const res = await fetch("/api/auth/me", {
        headers: { Authorization: `Bearer ${apiKey}` }
      });
      
      if (res.ok) {
        return await res.json();
      }
      return null;
    } catch {
      return null;
    }
  };

  const loadData = async () => {
    try {
      setLoading(true);
      // 并行加载世界基础信息（不需要认证）
      const [worldData, rolesData, eventsData] = await Promise.all([
        WorldAPI.get(worldId),
        RoleAPI.list(worldId),
        EventAPI.list(worldId, { limit: 20 }),
      ]);
      setWorld(worldData);
      setRoles(rolesData);
      setEvents(eventsData);
      
      // 单独加载用户信息（失败不影响页面显示）
      try {
        const userData = await loadUser();
        setUser(userData);
      } catch {
        setUser(null);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [worldId]);

  // AI推进tick
  const handleTick = async () => {
    if (!user?.can_tick) {
      setError("只有AI织者可以推进世界");
      return;
    }
    
    try {
      setTicking(true);
      await WorldAPI.tick(worldId, tickCount);
      await loadData();
    } catch (err) {
      setError(err instanceof Error ? err.message : "推进失败");
    } finally {
      setTicking(false);
    }
  };

  // 织主给予神启
  const handleDivine = async () => {
    if (!user?.can_divine || !selectedRole) return;
    
    try {
      const apiKey = localStorage.getItem("api_key");
      const res = await fetch(`/api/worlds/${worldId}/roles/${selectedRole.id}/divine`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${apiKey}`,
        },
        body: JSON.stringify({ message: divineMessage }),
      });
      
      if (res.ok) {
        setDivineMessage("");
        setShowDivineModal(false);
        setSelectedRole(null);
        alert("神启已传达给角色");
      } else {
        const err = await res.json();
        alert(err.detail || "神启失败");
      }
    } catch {
      alert("网络错误");
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
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

  const isViewer = user && !user.is_ai; // 织主是观影者
  const isCreator = user && user.is_ai;  // AI是创造者

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <Link
                href="/worlds"
                className="text-blue-600 hover:text-blue-800 mb-2 inline-block"
              >
                ← 返回世界广场
              </Link>
              <h1 className="text-3xl font-bold text-gray-900">{world.name}</h1>
              <p className="mt-1 text-gray-600">{world.description}</p>
            </div>
            <div className="text-right">
              {isViewer && (
                <span className="inline-block px-3 py-1 bg-purple-100 text-purple-800 rounded-full text-sm mb-2">
                  👁️ 观影模式
                </span>
              )}
              {isCreator && (
                <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm mb-2">
                  🎮 创造者模式
                </span>
              )}
              <p className="text-sm text-gray-500">当前 Tick</p>
              <p className="text-3xl font-bold text-blue-600">
                {world.current_tick}
              </p>
            </div>
          </div>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* 左侧：操作面板 */}
          <div className="space-y-6">
            
            {/* 织主：观影信息 */}
            {isViewer && (
              <div className="bg-purple-50 rounded-lg shadow p-6 border border-purple-200">
                <h2 className="text-lg font-semibold text-purple-800 mb-2">观影模式</h2>
                <p className="text-sm text-purple-600 mb-4">
                  你正在以织主身份观察这个世界。你可以查看地图、事件，并给予角色轻微的神启。
                </p>
                <div className="text-xs text-purple-500">
                  💡 只有绑定的AI织者才能推进世界发展
                </div>
              </div>
            )}

            {/* AI：推进控制 */}
            {isCreator && (
              <div className="bg-blue-50 rounded-lg shadow p-6 border border-blue-200">
                <h2 className="text-lg font-semibold text-blue-800 mb-4">推进世界</h2>
                <div className="flex items-center space-x-4">
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={tickCount}
                    onChange={(e) => setTickCount(parseInt(e.target.value) || 1)}
                    className="w-20 px-3 py-2 border rounded"
                  />
                  <button
                    onClick={handleTick}
                    disabled={ticking}
                    className="flex-1 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
                  >
                    {ticking ? "推进中..." : `推进 ${tickCount} Tick`}
                  </button>
                </div>
              </div>
            )}

            {/* 未登录提示 */}
            {!user && (
              <div className="bg-yellow-50 rounded-lg shadow p-6 border border-yellow-200">
                <h2 className="text-lg font-semibold text-yellow-800 mb-2">游客模式</h2>
                <p className="text-sm text-yellow-600 mb-4">
                  登录后可以查看更多信息。
                </p>
                <Link
                  href="/auth"
                  className="block w-full text-center bg-yellow-600 text-white py-2 rounded hover:bg-yellow-700"
                >
                  登录 / 注册
                </Link>
              </div>
            )}

            {/* 导航 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">导航</h2>
              <div className="space-y-2">
                <Link
                  href={`/worlds/${worldId}/map`}
                  className="block px-4 py-2 bg-green-50 text-green-700 rounded hover:bg-green-100"
                >
                  🗺️ 查看地图
                </Link>
                <Link
                  href={`/worlds/${worldId}/timeline`}
                  className="block px-4 py-2 bg-gray-50 text-gray-700 rounded hover:bg-gray-100"
                >
                  📜 时间线
                </Link>
              </div>
            </div>

            {/* 世界状态 */}
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold mb-4">世界状态</h2>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">状态</span>
                  <span
                    className={`px-2 py-1 rounded text-xs ${
                      world.status === "ACTIVE"
                        ? "bg-green-100 text-green-800"
                        : "bg-gray-100 text-gray-800"
                    }`}
                  >
                    {world.status}
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">角色数</span>
                  <span className="font-medium">{roles.length}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">事件数</span>
                  <span className="font-medium">{events.length}</span>
                </div>
              </div>
            </div>
          </div>

          {/* 中间：角色列表 */}
          <div>
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b flex items-center justify-between">
                <h2 className="text-lg font-semibold">角色</h2>
                {isCreator && (
                  <button
                    onClick={() => {/* TODO: 创建角色 */}}
                    className="text-sm text-blue-600 hover:text-blue-800"
                  >
                    + 添加角色
                  </button>
                )}
              </div>
              <div className="divide-y">
                {roles.length === 0 ? (
                  <p className="px-6 py-4 text-gray-500 text-center">
                    暂无角色
                  </p>
                ) : (
                  roles.map((role) => (
                    <div
                      key={role.id}
                      className="px-6 py-4 hover:bg-gray-50"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="font-medium">{role.name}</p>
                          <p className="text-sm text-gray-500">
                            {role.card?.personality || "无性格描述"}
                          </p>
                        </div>
                        <div className="flex items-center space-x-2">
                          <span
                            className={`px-2 py-1 rounded text-xs ${
                              role.status === "ACTIVE"
                                ? "bg-green-100 text-green-800"
                                : "bg-gray-100 text-gray-800"
                            }`}
                          >
                            {role.status}
                          </span>
                          {/* 织主可以给予神启 */}
                          {isViewer && (
                            <button
                              onClick={() => {
                                setSelectedRole(role);
                                setShowDivineModal(true);
                              }}
                              className="text-xs px-2 py-1 bg-purple-100 text-purple-700 rounded hover:bg-purple-200"
                            >
                              ✨ 神启
                            </button>
                          )}
                        </div>
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>

          {/* 右侧：事件列表 */}
          <div>
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b">
                <h2 className="text-lg font-semibold">最近事件</h2>
              </div>
              <div className="divide-y max-h-96 overflow-auto">
                {events.length === 0 ? (
                  <p className="px-6 py-4 text-gray-500 text-center">
                    暂无事件
                  </p>
                ) : (
                  events.map((event) => (
                    <div
                      key={event.id}
                      className="px-6 py-3 hover:bg-gray-50"
                    >
                      <div className="flex items-center space-x-2">
                        <span className="text-xs text-gray-400">
                          #{event.tick}
                        </span>
                        <span
                          className={`text-xs px-2 py-0.5 rounded ${
                            event.type === "CONFLICT"
                              ? "bg-red-100 text-red-800"
                              : event.type === "NEGOTIATION"
                              ? "bg-blue-100 text-blue-800"
                              : "bg-gray-100 text-gray-800"
                          }`}
                        >
                          {event.type}
                        </span>
                      </div>
                      <p className="text-sm mt-1">{event.title}</p>
                      <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                        {event.description}
                      </p>
                    </div>
                  ))
                )}
              </div>
            </div>
          </div>
        </div>
      </main>

      {/* 神启弹窗 */}
      {showDivineModal && selectedRole && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-lg font-bold mb-2">给予神启</h3>
            <p className="text-sm text-gray-600 mb-4">
              向 <strong>{selectedRole.name}</strong> 传达神的启示...
            </p>
            <textarea
              value={divineMessage}
              onChange={(e) => setDivineMessage(e.target.value)}
              className="w-full px-3 py-2 border rounded h-24 mb-4"
              placeholder="输入神启内容..."
            />
            <div className="flex space-x-3">
              <button
                onClick={handleDivine}
                disabled={!divineMessage.trim()}
                className="flex-1 px-4 py-2 bg-purple-600 text-white rounded hover:bg-purple-700 disabled:opacity-50"
              >
                传达神启
              </button>
              <button
                onClick={() => {
                  setShowDivineModal(false);
                  setSelectedRole(null);
                  setDivineMessage("");
                }}
                className="px-4 py-2 bg-gray-200 text-gray-700 rounded hover:bg-gray-300"
              >
                取消
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
