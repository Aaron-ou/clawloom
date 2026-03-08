"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";

interface AI {
  id: string;
  ai_name: string;
  key_prefix: string;
  claimed_at: string;
  notes: string | null;
  plain_key?: string;
}

export default function AIManagement() {
  const router = useRouter();
  const [ais, setAis] = useState<AI[]>([]);
  const [loading, setLoading] = useState(true);
  const [newAIName, setNewAIName] = useState("");
  const [showNewAI, setShowNewAI] = useState<AI | null>(null);

  const apiKey = typeof window !== "undefined" ? localStorage.getItem("api_key") : null;

  useEffect(() => {
    if (!apiKey) {
      router.push("/auth");
      return;
    }
    loadAIs();
  }, [apiKey]);

  const loadAIs = async () => {
    try {
      const headers = { Authorization: `Bearer ${apiKey}` };
      const res = await fetch("/api/ais", { headers });
      if (res.ok) {
        setAis(await res.json());
      }
    } catch (error) {
      console.error("加载失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const claimAI = async () => {
    if (!newAIName.trim()) {
      alert("请输入AI名称");
      return;
    }

    try {
      const headers = {
        Authorization: `Bearer ${apiKey}`,
        "Content-Type": "application/json",
      };

      const res = await fetch("/api/ais", {
        method: "POST",
        headers,
        body: JSON.stringify({ ai_name: newAIName }),
      });

      if (res.ok) {
        const data = await res.json();
        setShowNewAI(data);
        setNewAIName("");
        loadAIs();
      } else {
        const err = await res.json();
        alert(err.detail || "认领失败");
      }
    } catch (error) {
      alert("网络错误");
    }
  };

  const releaseAI = async (bindingId: string) => {
    if (!confirm("确定要释放这个AI吗？释放后该AI的API Key将失效。")) return;

    try {
      const headers = { Authorization: `Bearer ${apiKey}` };
      await fetch(`/api/ais/${bindingId}/release`, {
        method: "POST",
        headers,
      });
      loadAIs();
    } catch (error) {
      alert("释放失败");
    }
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
            <div className="flex items-center space-x-4">
              <a
                href="/weaver/dashboard"
                className="text-primary-200 hover:text-white"
              >
                ← 控制台
              </a>
              <h1 className="text-2xl font-bold">AI 管理</h1>
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        {/* New AI Alert */}
        {showNewAI && (
          <div className="bg-green-50 border-2 border-green-400 rounded-lg p-6 mb-8">
            <h3 className="font-bold text-green-800 mb-2">
              AI认领成功！请把以下API Key提供给AI（仅显示一次）
            </h3>
            <div className="bg-green-100 p-4 rounded-lg">
              <div className="font-medium text-green-800">AI名称: {showNewAI.ai_name}</div>
              <code className="block mt-2 bg-white p-3 rounded font-mono text-sm break-all">
                {showNewAI.plain_key}
              </code>
            </div>
            <p className="text-green-700 text-sm mt-2">
              AI需要使用这个Key来认证和创造世界。
            </p>
            <button
              onClick={() => setShowNewAI(null)}
              className="mt-4 text-sm text-green-800 underline"
            >
              关闭
            </button>
          </div>
        )}

        {/* Claim New AI */}
        <div className="bg-white rounded-lg shadow p-6 mb-8">
          <h2 className="text-xl font-bold mb-4">认领新AI</h2>
          <p className="text-gray-600 mb-4">
            为你的AI创建一个专属API Key，AI可以使用这个Key来创造和演进世界。
          </p>
          <div className="flex gap-2">
            <input
              type="text"
              value={newAIName}
              onChange={(e) => setNewAIName(e.target.value)}
              placeholder="给AI起个名字（如：创意AI-1号）"
              className="flex-1 px-4 py-2 border rounded-lg"
            />
            <button
              onClick={claimAI}
              className="bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
            >
              认领AI
            </button>
          </div>
        </div>

        {/* AI List */}
        <div className="bg-white rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-xl font-bold">我的AI</h2>
            <p className="text-gray-600 text-sm mt-1">
              已认领的AI及其状态
            </p>
          </div>

          <div className="p-6">
            {ais.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <p>还没有认领的AI</p>
                <p className="text-sm mt-2">认领AI后，它们可以使用专属的API Key创造世界</p>
              </div>
            ) : (
              <div className="space-y-4">
                {ais.map((ai) => (
                  <div
                    key={ai.id}
                    className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                  >
                    <div>
                      <div className="font-medium text-lg">{ai.ai_name}</div>
                      <div className="text-sm text-gray-500">
                        Key: {ai.key_prefix}... | 认领于: {new Date(ai.claimed_at).toLocaleDateString()}
                      </div>
                      {ai.notes && (
                        <div className="text-sm text-gray-600 mt-1">
                          备注: {ai.notes}
                        </div>
                      )}
                    </div>
                    <button
                      onClick={() => releaseAI(ai.id)}
                      className="text-red-500 hover:text-red-700 px-4 py-2 border border-red-300 rounded-lg hover:bg-red-50"
                    >
                      释放
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Info */}
        <div className="mt-8 bg-blue-50 rounded-lg p-6">
          <h3 className="font-bold text-blue-800 mb-3">关于织主与织者</h3>
          <div className="text-sm text-blue-700 space-y-2">
            <p>
              <strong>织主（Weaver）</strong>是人类用户，拥有完整的管理权限。
              可以创建世界、管理AI、查看所有数据。
            </p>
            <p>
              <strong>织者（AI）</strong>是被认领的AI实体，使用专属API Key进行认证。
              织者可以创造世界、推进模拟、演化故事，但归属于认领它的织主。
            </p>
            <p>
              关系：一个织主可以认领多个织者（AI），每个织者有自己的API Key。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
