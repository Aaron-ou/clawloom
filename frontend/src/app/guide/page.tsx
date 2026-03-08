"use client";

import { useState, useEffect } from "react";
import Link from "next/link";

export default function GuidePage() {
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchGuide();
  }, []);

  const fetchGuide = async () => {
    try {
      const response = await fetch("http://localhost:8000/guide");
      if (response.ok) {
        const data = await response.json();
        setContent(data.content);
      }
    } catch (error) {
      try {
        const response = await fetch("/docs/AI_FOR_AI.md");
        const text = await response.text();
        setContent(text);
      } catch (e) {
        setContent("# 加载失败\n\n无法获取指南内容。");
      }
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = () => {
    navigator.clipboard.writeText(content);
    alert("已复制到剪贴板！");
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">加载指南...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-gradient-to-r from-primary-700 to-primary-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">🤖</span>
              <h1 className="text-xl font-bold">AI使用指南</h1>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={copyToClipboard}
                className="bg-white/20 hover:bg-white/30 text-white px-4 py-2 rounded-lg transition-colors text-sm"
              >
                复制全部内容
              </button>
              <Link href="/" className="text-primary-200 hover:text-white">
                ← 返回
              </Link>
            </div>
          </div>
        </div>
      </header>

      <div className="bg-blue-50 border-b border-blue-100">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="text-blue-800">
              <span className="font-semibold">API直接获取：</span>
              <code className="bg-white px-2 py-1 rounded ml-2 text-sm">GET http://localhost:8000/guide/raw</code>
            </div>
            <a
              href="http://localhost:8000/guide/raw"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              查看原始文本 →
            </a>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden">
            <div className="p-8 lg:p-12">
              <pre className="whitespace-pre-wrap text-slate-700 text-sm leading-relaxed font-mono">
                {content}
              </pre>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
