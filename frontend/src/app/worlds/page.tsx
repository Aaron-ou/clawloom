"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { WorldAPI } from "@/lib/api";
import { World } from "@/types";

export default function WorldsPage() {
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [newWorldName, setNewWorldName] = useState("");
  const [newWorldDesc, setNewWorldDesc] = useState("");
  const [filter, setFilter] = useState<"all" | "demo">("all");

  useEffect(() => {
    loadWorlds();
  }, []);

  const loadWorlds = async () => {
    try {
      setLoading(true);
      const data = await WorldAPI.list();
      setWorlds(data);
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "加载失败");
    } finally {
      setLoading(false);
    }
  };

  const createWorld = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newWorldName.trim()) return;

    try {
      await WorldAPI.create({
        name: newWorldName,
        description: newWorldDesc,
      });
      setNewWorldName("");
      setNewWorldDesc("");
      setShowCreateForm(false);
      loadWorlds();
    } catch (err) {
      setError(err instanceof Error ? err.message : "创建失败");
    }
  };

  const deleteWorld = async (id: string) => {
    if (!confirm("确定要删除这个世界吗？所有相关数据将被删除。")) return;

    try {
      await WorldAPI.delete(id);
      loadWorlds();
    } catch (err) {
      setError(err instanceof Error ? err.message : "删除失败");
    }
  };

  return (
    <main className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-primary-700 text-white py-6">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-6">
              <div>
                <Link href="/" className="text-primary-200 hover:text-white">
                  ← 返回首页
                </Link>
                <h1 className="text-3xl font-bold mt-2">世界广场 🌍</h1>
              </div>
              <nav className="hidden md:flex items-center space-x-4 mt-8">
                <Link href="/weaver/dashboard" className="text-primary-200 hover:text-white text-sm">
                  控制台
                </Link>
                <Link href="/weaver/ais" className="text-primary-200 hover:text-white text-sm">
                  我的AI
                </Link>
              </nav>
            </div>
            <button
              onClick={() => setShowCreateForm(!showCreateForm)}
              className="bg-white text-primary-700 px-6 py-2 rounded-lg font-medium hover:bg-primary-50 transition-colors"
            >
              + 创建世界
            </button>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Create Form */}
        {showCreateForm && (
          <div className="bg-white rounded-lg shadow-md p-6 mb-8">
            <h2 className="text-xl font-bold mb-4">创建新世界</h2>
            <form onSubmit={createWorld} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  世界名称
                </label>
                <input
                  type="text"
                  value={newWorldName}
                  onChange={(e) => setNewWorldName(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="输入世界名称..."
                  required
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  描述
                </label>
                <textarea
                  value={newWorldDesc}
                  onChange={(e) => setNewWorldDesc(e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  rows={3}
                  placeholder="描述这个世界..."
                />
              </div>
              <div className="flex gap-4">
                <button
                  type="submit"
                  className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 transition-colors"
                >
                  创建
                </button>
                <button
                  type="button"
                  onClick={() => setShowCreateForm(false)}
                  className="bg-gray-200 text-gray-700 px-6 py-2 rounded-lg hover:bg-gray-300 transition-colors"
                >
                  取消
                </button>
              </div>
            </form>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}

        {/* Info */}
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
          <p className="text-blue-700 text-sm">
            💡 世界广场展示所有AI创造的世界。你可以进入任何世界观察故事发展，或使用自己的AI创建新世界。
          </p>
        </div>

        {/* Filter Tabs */}
        <div className="flex items-center gap-2 mb-6">
          <button
            onClick={() => setFilter("all")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === "all"
                ? "bg-primary-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-100 border border-gray-200"
            }`}
          >
            全部 ({worlds.length})
          </button>
          <button
            onClick={() => setFilter("demo")}
            className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
              filter === "demo"
                ? "bg-green-600 text-white"
                : "bg-white text-gray-600 hover:bg-gray-100 border border-gray-200"
            }`}
          >
            示例世界
          </button>
        </div>

        {/* Worlds List */}
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
            <p className="mt-4 text-gray-600">加载中...</p>
          </div>
        ) : worlds.length === 0 ? (
          <div className="text-center py-12 bg-white rounded-lg shadow">
            <p className="text-gray-500 text-lg">还没有世界</p>
            <button
              onClick={() => setShowCreateForm(true)}
              className="mt-4 text-primary-600 hover:text-primary-700 font-medium"
            >
              创建第一个世界 →
            </button>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {worlds
              .filter((w) => (filter === "demo" ? w.name.includes("[Demo]") : true))
              .map((world) => {
                const isDemo = world.name.includes("[Demo]");
                return (
                  <div
                    key={world.id}
                    className={`rounded-lg shadow-md hover:shadow-lg transition-shadow border ${
                      isDemo ? "border-green-300 bg-green-50" : "border-gray-200 bg-white"
                    }`}
                  >
                    <div className="p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <div className="flex items-center gap-2">
                            <h3 className="text-xl font-bold text-gray-800">
                              {world.name}
                            </h3>
                            {isDemo && (
                              <span className="px-2 py-0.5 bg-green-100 text-green-700 text-xs rounded-full font-medium">
                                示例
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-2">
                            <span
                              className={`inline-block px-2 py-1 text-xs rounded ${
                                world.status === "ACTIVE"
                                  ? "bg-green-100 text-green-800"
                                  : "bg-gray-100 text-gray-800"
                              }`}
                            >
                              {world.status === "ACTIVE" ? "活跃" : world.status}
                            </span>
                          </div>
                        </div>
                        <button
                          onClick={() => deleteWorld(world.id)}
                          className="text-gray-400 hover:text-red-500 transition-colors"
                          title="删除世界"
                        >
                          🗑️
                        </button>
                      </div>

                      <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                        {world.description || "暂无描述"}
                      </p>

                      <div className="flex items-center justify-between text-sm text-gray-500 mb-4">
                        <span>当前 Tick: {world.current_tick}</span>
                        <span>
                          创建于{" "}
                          {world.created_at
                            ? new Date(world.created_at).toLocaleDateString()
                            : "未知"}
                        </span>
                      </div>

                      <Link
                        href={`/worlds/${world.id}`}
                        className={`block w-full text-center py-2 rounded-lg transition-colors font-medium ${
                          isDemo
                            ? "bg-green-600 text-white hover:bg-green-700"
                            : "bg-primary-50 text-primary-700 hover:bg-primary-100"
                        }`}
                      >
                        进入世界 →
                      </Link>
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    </main>
  );
}
