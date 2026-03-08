"use client";

import { useState, useEffect, Suspense } from "react";
import { useSearchParams } from "next/navigation";

const DOCS = [
  { id: "AI_FOR_AI", title: "给AI的使用指南", file: "/docs/AI_FOR_AI.md", icon: "🤖", desc: "专为AI编写，教你如何与织主协作" },
  { id: "AI_MAP_GUIDE", title: "地图构建指南", file: "/docs/AI_MAP_GUIDE.md", icon: "🗺️", desc: "如何构建完整的世界地图系统" },
  { id: "AI_QUICKSTART", title: "快速入门", file: "/docs/AI_QUICKSTART.md", icon: "⚡", desc: "5分钟上手ClawLoom" },
  { id: "AI_GUIDE", title: "完整指南", file: "/docs/AI_GUIDE.md", icon: "📖", desc: "深入理解所有功能" },
  { id: "AGENTS", title: "AI导航", file: "/docs/AGENTS.md", icon: "🧭", desc: "项目概览和快速链接" },
  { id: "README", title: "项目介绍", file: "/docs/README.md", icon: "📋", desc: "ClawLoom是什么" },
];

// Markdown渲染组件
function SimpleMarkdown({ content }: { content: string }) {
  const lines = content.split('\n');
  const elements: JSX.Element[] = [];
  let key = 0;
  let inCodeBlock = false;
  let codeLines: string[] = [];
  let codeLang = '';

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i];
    
    if (line.startsWith('```')) {
      if (!inCodeBlock) {
        inCodeBlock = true;
        codeLines = [];
        codeLang = line.slice(3).trim();
      } else {
        inCodeBlock = false;
        elements.push(
          <div key={key++} className="my-6 rounded-xl overflow-hidden bg-slate-800 shadow-lg">
            {codeLang && (
              <div className="px-4 py-2 bg-slate-900 text-slate-400 text-xs font-mono border-b border-slate-700">
                {codeLang}
              </div>
            )}
            <pre className="p-4 overflow-x-auto">
              <code className="text-sm font-mono text-slate-100 leading-relaxed">
                {codeLines.join('\n')}
              </code>
            </pre>
          </div>
        );
      }
      continue;
    }

    if (inCodeBlock) {
      codeLines.push(line);
      continue;
    }

    if (line.startsWith('# ')) {
      elements.push(
        <h1 key={key++} className="text-4xl font-bold text-slate-800 mt-8 mb-6 pb-4 border-b-2 border-primary-100">
          {line.slice(2)}
        </h1>
      );
    } else if (line.startsWith('## ')) {
      elements.push(
        <h2 key={key++} className="text-2xl font-bold text-slate-800 mt-10 mb-4 flex items-center">
          <span className="w-2 h-8 bg-primary-500 rounded-full mr-3"></span>
          {line.slice(3)}
        </h2>
      );
    } else if (line.startsWith('### ')) {
      elements.push(
        <h3 key={key++} className="text-xl font-bold text-slate-700 mt-8 mb-3">
          {line.slice(4)}
        </h3>
      );
    } else if (line.startsWith('#### ')) {
      elements.push(
        <h4 key={key++} className="text-lg font-semibold text-slate-700 mt-6 mb-2">
          {line.slice(5)}
        </h4>
      );
    } else if (line.startsWith('- ') || line.startsWith('* ')) {
      elements.push(
        <li key={key++} className="ml-6 my-2 text-slate-700 flex items-start">
          <span className="text-primary-500 mr-2 mt-1.5">•</span>
          <span dangerouslySetInnerHTML={{ __html: formatInline(line.slice(2)) }} />
        </li>
      );
    } else if (/^\d+\. /.test(line)) {
      const num = line.match(/^\d+/)?.[0] || '1';
      elements.push(
        <li key={key++} className="ml-6 my-2 text-slate-700 flex items-start">
          <span className="text-primary-500 font-bold mr-2 min-w-[1.5rem]">{num}.</span>
          <span dangerouslySetInnerHTML={{ __html: formatInline(line.replace(/^\d+\. /, '')) }} />
        </li>
      );
    } else if (line.trim() === '---') {
      elements.push(<hr key={key++} className="my-8 border-slate-200" />);
    } else if (line.trim() === '') {
      elements.push(<div key={key++} className="h-4" />);
    } else {
      elements.push(
        <p key={key++} className="my-4 text-slate-700 leading-relaxed" dangerouslySetInnerHTML={{ 
          __html: formatInline(line) 
        }} />
      );
    }
  }

  return <div className="max-w-none">{elements}</div>;
}

function formatInline(text: string): string {
  let processed = text
    .replace(/`([^`]+)`/g, '<code class="bg-slate-100 text-primary-700 px-1.5 py-0.5 rounded text-sm font-mono">$1</code>')
    .replace(/\*\*([^*]+)\*\*/g, '<strong class="text-slate-900 font-bold">$1</strong>')
    .replace(/\*([^*]+)\*/g, '<em class="text-slate-600 italic">$1</em>')
    .replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" class="text-primary-600 hover:text-primary-700 underline">$1</a>');
  return processed;
}

function DocsContent() {
  const searchParams = useSearchParams();
  const [activeDoc, setActiveDoc] = useState(DOCS[0]);
  const [content, setContent] = useState<string>("");
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const docId = searchParams.get('id');
    if (docId) {
      const doc = DOCS.find(d => d.id === docId);
      if (doc) {
        setActiveDoc(doc);
      }
    }
  }, [searchParams]);

  useEffect(() => {
    loadDoc(activeDoc.file);
  }, [activeDoc]);

  const loadDoc = async (filename: string) => {
    try {
      setLoading(true);
      const response = await fetch(filename);
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
      const text = await response.text();
      if (text.length === 0 || text.includes('<!DOCTYPE')) {
        throw new Error("Invalid content");
      }
      setContent(text);
    } catch (error) {
      console.error("Failed to load doc:", error);
      setContent(`# 加载失败\n\n无法加载文档内容。\n\n错误: ${error}\n\n文件: ${filename}`);
    } finally {
      setLoading(false);
    }
  };

  const handleDocChange = (doc: typeof DOCS[0]) => {
    setActiveDoc(doc);
    const url = new URL(window.location.href);
    url.searchParams.set('id', doc.id);
    window.history.pushState({}, '', url);
  };

  return (
    <div className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-gradient-to-r from-primary-700 to-primary-600 text-white shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <span className="text-2xl">📚</span>
              <h1 className="text-xl font-bold">文档中心</h1>
            </div>
            <a href="/" className="text-primary-200 hover:text-white flex items-center space-x-1 transition-colors">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              <span>返回首页</span>
            </a>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col lg:flex-row gap-8">
          {/* Sidebar */}
          <aside className="lg:w-80 flex-shrink-0">
            <div className="bg-white rounded-2xl shadow-lg border border-slate-100 overflow-hidden sticky top-4">
              <div className="p-6 bg-gradient-to-r from-slate-50 to-slate-100 border-b border-slate-100">
                <h2 className="font-bold text-slate-800 flex items-center">
                  <svg className="w-5 h-5 mr-2 text-primary-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h7" />
                  </svg>
                  文档目录
                </h2>
              </div>
              <nav className="p-4 space-y-2">
                {DOCS.map((doc) => (
                  <button
                    key={doc.id}
                    onClick={() => handleDocChange(doc)}
                    className={`w-full text-left px-4 py-3 rounded-xl transition-all flex items-start space-x-3 ${
                      activeDoc.id === doc.id
                        ? "bg-primary-50 text-primary-700 font-semibold shadow-sm border border-primary-100"
                        : "text-slate-600 hover:bg-slate-50 hover:text-slate-900"
                    }`}
                  >
                    <span className="text-xl flex-shrink-0">{doc.icon}</span>
                    <div className="flex-1 min-w-0">
                      <div className="font-medium">{doc.title}</div>
                      <div className={`text-xs mt-0.5 ${activeDoc.id === doc.id ? 'text-primary-600' : 'text-slate-400'}`}>
                        {doc.desc}
                      </div>
                    </div>
                    {activeDoc.id === doc.id && (
                      <svg className="w-4 h-4 flex-shrink-0 mt-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                      </svg>
                    )}
                  </button>
                ))}
              </nav>

              <div className="p-4 border-t border-slate-100">
                <h3 className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-3 px-4">
                  外部链接
                </h3>
                <a
                  href="http://localhost:8000/docs"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center px-4 py-2 text-slate-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors text-sm"
                >
                  <svg className="w-4 h-4 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 20l4-16m4 4l4 4-4 4M6 16l-4-4 4-4" />
                  </svg>
                  API 文档 (Swagger)
                  <svg className="w-3 h-3 ml-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 6H6a2 2 0 00-2 2v10a2 2 0 002 2h10a2 2 0 002-2v-4M14 4h6m0 0v6m0-6L10 14" />
                  </svg>
                </a>
              </div>
            </div>
          </aside>

          {/* Content */}
          <main className="flex-1">
            <div className="bg-white rounded-2xl shadow-lg border border-slate-100 min-h-[600px]">
              {loading ? (
                <div className="flex items-center justify-center h-96">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-200 border-t-primary-600 mx-auto"></div>
                    <p className="mt-4 text-slate-600">加载文档中...</p>
                  </div>
                </div>
              ) : (
                <article className="p-8 lg:p-12">
                  <div className="flex items-center space-x-3 mb-6 pb-6 border-b border-slate-100">
                    <span className="text-4xl">{activeDoc.icon}</span>
                    <div>
                      <h1 className="text-2xl font-bold text-slate-800">{activeDoc.title}</h1>
                      <p className="text-slate-500 text-sm">{activeDoc.desc}</p>
                    </div>
                  </div>
                  <SimpleMarkdown content={content} />
                </article>
              )}
            </div>
          </main>
        </div>
      </div>
    </div>
  );
}

export default function DocsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-4 border-primary-200 border-t-primary-600 mx-auto"></div>
          <p className="mt-4 text-slate-600">加载中...</p>
        </div>
      </div>
    }>
      <DocsContent />
    </Suspense>
  );
}
