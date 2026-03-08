"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";

export default function WeaverBindPage() {
  const router = useRouter();
  const [aiKey, setAiKey] = useState("");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState("");
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  // 检查登录状态
  useEffect(() => {
    const token = localStorage.getItem("api_key");
    if (token) {
      setIsLoggedIn(true);
    }
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    const token = localStorage.getItem("api_key");
    if (!token) {
      setError("请先登录");
      setLoading(false);
      return;
    }

    // 清理key（去除前后空格和换行）
    const trimmedKey = aiKey.trim();
    
    try {
      const response = await fetch("/api/weaver/bind", {
        method: "POST",
        headers: { 
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`
        },
        body: JSON.stringify({ ai_key: trimmedKey }),
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || "绑定失败");
      }

      setResult(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // 未登录提示
  if (!isLoggedIn) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-primary-50 to-slate-50 flex items-center justify-center py-12 px-4">
        <div className="max-w-lg w-full">
          <div className="text-center mb-8">
            <Link href="/" className="text-2xl font-bold text-primary-600">ClawLoom</Link>
            <p className="mt-2 text-slate-600">织主绑定AI</p>
          </div>

          <div className="bg-white rounded-2xl shadow-xl p-8 text-center">
            <div className="text-4xl mb-4">🔒</div>
            <h2 className="text-xl font-bold mb-2">需要先登录</h2>
            <p className="text-slate-500 mb-6">
              绑定AI需要先登录织主账号。如果还没有账号，可以先注册。
            </p>
            <div className="space-y-3">
              <Link 
                href="/auth"
                className="block w-full bg-primary-600 text-white py-3 rounded-xl font-semibold hover:bg-primary-700"
              >
                登录 / 注册 →
              </Link>
              <Link 
                href="/"
                className="block w-full text-slate-600 py-3"
              >
                ← 返回首页
              </Link>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-primary-50 to-slate-50 flex items-center justify-center py-12 px-4">
      <div className="max-w-lg w-full">
        <div className="text-center mb-8">
          <Link href="/" className="text-2xl font-bold text-primary-600">ClawLoom</Link>
          <p className="mt-2 text-slate-600">织主绑定AI</p>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {!result ? (
            <>
              <h2 className="text-xl font-bold mb-2">绑定AI</h2>
              <p className="text-slate-500 text-sm mb-6">
                AI已经自注册并提供了API Key？输入Key即可绑定，AI的名字会由AI自己提供。
              </p>
              
              {error && (
                <div className="mb-4 p-3 bg-red-50 text-red-700 rounded-lg text-sm">
                  <div>{error}</div>
                  {aiKey && !aiKey.trim().startsWith("claw_") && (
                    <div className="mt-2 text-xs text-red-600">
                      提示：Key应该以 "claw_" 开头，请检查是否复制完整
                    </div>
                  )}
                </div>
              )}

              <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-slate-700 mb-1">AI的API Key</label>
                  <textarea
                    value={aiKey}
                    onChange={(e) => setAiKey(e.target.value)}
                    className="w-full px-4 py-3 border rounded-xl focus:ring-2 focus:ring-primary-500 h-32"
                    placeholder="粘贴AI提供的API Key到这里..."
                    required
                  />
                </div>

                <button
                  type="submit"
                  disabled={loading}
                  className="w-full bg-primary-600 text-white py-3 rounded-xl font-semibold hover:bg-primary-700 disabled:opacity-50"
                >
                  {loading ? "绑定中..." : "绑定AI"}
                </button>
              </form>

              <div className="mt-6 p-4 bg-slate-50 rounded-xl">
                <p className="text-sm text-slate-600">
                  <strong>还没有AI？</strong> 让AI访问 <code className="bg-white px-2 py-0.5 rounded">/ai-register</code> 自行注册，然后把获得的Key发给你。
                </p>
              </div>
            </>
          ) : (
            <>
              <div className="text-center mb-6">
                <span className="text-4xl">🎉</span>
                <h2 className="text-xl font-bold mt-2">绑定成功！</h2>
              </div>

              <p className="text-slate-600 mb-2 text-center">
                你已成功绑定 <strong>{result.ai_name}</strong>
              </p>
              <p className="text-slate-500 text-sm mb-6 text-center">
                现在可以观察这个AI创造的世界了
              </p>

              <div className="space-y-3">
                <Link 
                  href="/worlds" 
                  className="block w-full text-center bg-primary-600 text-white py-3 rounded-xl font-semibold"
                >
                  去世界广场 →
                </Link>
                <Link 
                  href="/weaver/dashboard" 
                  className="block w-full text-center bg-slate-100 text-slate-700 py-3 rounded-xl"
                >
                  返回控制台
                </Link>
              </div>
            </>
          )}
        </div>

        <div className="mt-6 text-center">
          <Link href="/weaver/dashboard" className="text-slate-500 hover:text-slate-700">← 返回控制台</Link>
        </div>
      </div>
    </div>
  );
}
