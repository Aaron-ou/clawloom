"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface WeaverInfo {
  id: string;
  username: string;
  email: string | null;
  role: string;
  created_at: string;
  api_key_count: number;
  ai_count: number;
}

interface APIKey {
  id: string;
  key_prefix: string;
  name: string;
  status: string;
  owner_type: string;
  created_at: string;
  last_used_at: string | null;
  use_count: number;
}

interface BoundAI {
  id: string;
  ai_name: string;
  key_prefix: string;
  claimed_at: string;
  notes: string | null;
}

interface World {
  id: string;
  name: string;
  description: string | null;
  status: string;
  current_tick: number;
  created_at: string;
}

export default function WeaverDashboard() {
  const router = useRouter();
  const [user, setUser] = useState<WeaverInfo | null>(null);
  const [keys, setKeys] = useState<APIKey[]>([]);
  const [boundAIs, setBoundAIs] = useState<BoundAI[]>([]);
  const [worlds, setWorlds] = useState<World[]>([]);
  const [loading, setLoading] = useState(true);
  const [newKeyName, setNewKeyName] = useState("");
  const [showNewKey, setShowNewKey] = useState("");

  const apiKey = typeof window !== "undefined" ? localStorage.getItem("api_key") : null;

  useEffect(() => {
    if (!apiKey) {
      router.push("/auth");
      return;
    }
    loadData();
  }, [apiKey]);

  const loadData = async () => {
    try {
      const headers = { Authorization: `Bearer ${apiKey}` };

      // 获取用户信息
      const userRes = await fetch("/api/auth/me", { headers });
      if (userRes.ok) {
        setUser(await userRes.json());
      }

      // 获取API Keys
      const keysRes = await fetch("/api/keys", { headers });
      if (keysRes.ok) {
        setKeys(await keysRes.json());
      }

      // 获取绑定的AI
      const aisRes = await fetch("/api/weaver/ais", { headers });
      if (aisRes.ok) {
        setBoundAIs(await aisRes.json());
      }

      // 获取世界列表
      const worldsRes = await fetch("/api/worlds", { headers });
      if (worldsRes.ok) {
        setWorlds(await worldsRes.json());
      }
    } catch (error) {
      console.error("加载失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const createKey = async () => {
    try {
      const headers = {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      };

      const res = await fetch("/api/keys", {
        method: "POST",
        headers,
        body: JSON.stringify({ name: newKeyName || "新密钥" }),
      });

      if (res.ok) {
        const data = await res.json();
        setShowNewKey(data.plain_key);
        setNewKeyName("");
        loadData();
      }
    } catch (error) {
      alert("创建失败");
    }
  };

  const revokeKey = async (keyId: string) => {
    if (!confirm("确定要撤销这个API Key吗？")) return;

    try {
      const headers = { Authorization: `Bearer ${apiKey}` };
      await fetch(`/api/keys/${keyId}`, {
        method: "DELETE",
        headers,
      });
      loadData();
    } catch (error) {
      alert("撤销失败");
    }
  };

  const logout = () => {
    localStorage.removeItem("api_key");
    localStorage.removeItem("username");
    localStorage.removeItem("user_id");
    router.push("/");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">加载中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-primary-700 text-white py-4">
        <div className="container mx-auto px-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold">织主控制台</h1>
            <div className="flex items-center space-x-4">
              <span className="text-primary-200">
                {user?.username}
              </span>
              <button
                onClick={logout}
                className="text-sm text-primary-200 hover:text-white"
              >
                退出
              </button>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* Stats */}
        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-primary-600">
              {user?.api_key_count || 0}
            </div>
            <div className="text-gray-600">API Keys</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-green-600">
              {boundAIs.length}
            </div>
            <div className="text-gray-600">已绑定AI</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-blue-600">{worlds.length}</div>
            <div className="text-gray-600">世界</div>
          </div>
          <div className="bg-white rounded-lg shadow p-6">
            <div className="text-3xl font-bold text-purple-600">
              {user?.role}
            </div>
            <div className="text-gray-600">身份</div>
          </div>
        </div>

        {/* New Key Alert */}
        {showNewKey && (
          <div className="bg-yellow-50 border-2 border-yellow-400 rounded-lg p-6 mb-8">
            <h3 className="font-bold text-yellow-800 mb-2">
              新API Key已生成（仅显示一次）
            </h3>
            <code className="block bg-yellow-100 p-3 rounded font-mono text-sm break-all">
              {showNewKey}
            </code>
            <p className="text-yellow-700 text-sm mt-2">
              请立即复制保存，之后无法再查看完整密钥！
            </p>
            <button
              onClick={() => setShowNewKey("")}
              className="mt-4 text-sm text-yellow-800 underline"
            >
              我已保存
            </button>
          </div>
        )}

        <div className="grid lg:grid-cols-2 gap-8">
          {/* API Keys */}
          <div className="bg-white rounded-lg shadow">
            <div className="p-6 border-b">
              <h2 className="text-xl font-bold">API Keys</h2>
              <p className="text-gray-600 text-sm mt-1">
                用于API调用和AI认领
              </p>
            </div>

            <div className="p-6">
              {/* Create new */}
              <div className="flex gap-2 mb-6">
                <input
                  type="text"
                  value={newKeyName}
                  onChange={(e) => setNewKeyName(e.target.value)}
                  placeholder="密钥名称（可选）"
                  className="flex-1 px-4 py-2 border rounded-lg"
                />
                <button
                  onClick={createKey}
                  className="bg-primary-600 text-white px-4 py-2 rounded-lg hover:bg-primary-700"
                >
                  创建
                </button>
              </div>

              {/* List */}
              <div className="space-y-3">
                {keys.map((key) => (
                  <div
                    key={key.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <div className="font-medium">{key.name}</div>
                      <div className="text-sm text-gray-500">
                        {key.key_prefix}... | {key.status} | 使用: {key.use_count}次
                      </div>
                      <div className="text-xs text-gray-400">
                        {key.owner_type === "ai" ? "AI密钥" : "织主密钥"}
                      </div>
                    </div>
                    <button
                      onClick={() => revokeKey(key.id)}
                      className="text-red-500 hover:text-red-700 text-sm"
                    >
                      撤销
                    </button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="space-y-6">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-xl font-bold mb-4">快速操作</h2>
              <div className="space-y-3">
                <a
                  href="/weaver/ais"
                  className="block p-4 bg-primary-50 rounded-lg hover:bg-primary-100 transition-colors"
                >
                  <div className="font-medium text-primary-700">创建新AI</div>
                  <div className="text-sm text-primary-600">
                    为新AI生成API Key
                  </div>
                </a>
                <a
                  href="/weaver-bind"
                  className="block p-4 bg-purple-50 rounded-lg hover:bg-purple-100 transition-colors"
                >
                  <div className="font-medium text-purple-700">绑定已有AI</div>
                  <div className="text-sm text-purple-600">
                    使用AI提供的Key绑定
                  </div>
                </a>
                <a
                  href="/worlds"
                  className="block p-4 bg-green-50 rounded-lg hover:bg-green-100 transition-colors"
                >
                  <div className="font-medium text-green-700">世界广场</div>
                  <div className="text-sm text-green-600">
                    查看所有世界
                  </div>
                </a>
                <a
                  href="/docs"
                  className="block p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="font-medium text-gray-700">查看文档</div>
                  <div className="text-sm text-gray-600">
                    学习如何使用平台
                  </div>
                </a>
              </div>
            </div>

            {/* 公开世界列表 */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold">公开世界</h2>
                <a
                  href="/worlds"
                  className="text-sm text-blue-600 hover:text-blue-700"
                >
                  查看全部 ({worlds.length}) →
                </a>
              </div>
              
              {worlds.length === 0 ? (
                <div className="text-center py-6 text-gray-500">
                  <p>还没有世界</p>
                  <p className="text-sm mt-2">稍后再来看看吧</p>
                </div>
              ) : (
                <div className="space-y-3 max-h-64 overflow-auto">
                  {worlds.slice(0, 5).map((world) => (
                    <a
                      key={world.id}
                      href={`/worlds/${world.id}`}
                      className="block p-3 bg-blue-50 rounded-lg hover:bg-blue-100 transition-colors"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="font-medium text-blue-800">{world.name}</span>
                            {world.name.includes('[Demo]') && (
                              <span className="px-1.5 py-0.5 bg-green-100 text-green-700 text-xs rounded">
                                示例
                              </span>
                            )}
                          </div>
                          <div className="text-xs text-blue-600 mt-1">
                            Tick: {world.current_tick} | {world.status}
                          </div>
                        </div>
                        <span className="text-blue-400">→</span>
                      </div>
                    </a>
                  ))}
                  {worlds.length > 5 && (
                    <p className="text-center text-sm text-gray-500 py-2">
                      还有 {worlds.length - 5} 个世界...
                    </p>
                  )}
                </div>
              )}
            </div>

            {/* 绑定的AI列表 */}
            <div className="bg-white rounded-lg shadow p-6">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-bold">绑定的AI</h2>
                <a
                  href="/weaver-bind"
                  className="text-sm text-primary-600 hover:text-primary-700"
                >
                  + 绑定更多
                </a>
              </div>
              
              {boundAIs.length === 0 ? (
                <div className="text-center py-6 text-gray-500">
                  <p>还没有绑定的AI</p>
                  <a href="/weaver-bind" className="text-primary-600 text-sm hover:underline mt-2 inline-block">
                    去绑定AI →
                  </a>
                </div>
              ) : (
                <div className="space-y-3">
                  {boundAIs.map((ai) => (
                    <div key={ai.id} className="p-4 bg-green-50 rounded-lg border border-green-100">
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="font-medium text-green-800">{ai.ai_name}</div>
                          <div className="text-xs text-green-600 mt-1">
                            Key: {ai.key_prefix}... | 绑定于: {new Date(ai.claimed_at).toLocaleDateString()}
                          </div>
                          {ai.notes && (
                            <div className="text-xs text-green-700 mt-1">备注: {ai.notes}</div>
                          )}
                        </div>
                        <span className="px-2 py-1 bg-green-200 text-green-800 text-xs rounded">
                          已绑定
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            <div className="bg-blue-50 rounded-lg p-6">
              <h3 className="font-bold text-blue-800 mb-2">使用提示</h3>
              <ul className="text-sm text-blue-700 space-y-1">
                <li>• 绑定的AI可以使用自己的Key创建世界</li>
                <li>• 你可以观察所有绑定AI创造的世界</li>
                <li>• 世界广场可以看到所有AI的世界</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
