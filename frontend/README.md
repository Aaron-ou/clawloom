# ClawLoom Frontend

ClawLoom 前端应用 - Next.js + React + TypeScript + Tailwind CSS

## 功能

- 🌍 **世界管理**: 创建、查看、删除世界
- 🎭 **角色管理**: 添加角色，查看角色状态和记忆
- ⚡ **模拟控制台**: 推进世界模拟，查看结果
- 📜 **时间线**: 浏览世界事件历史

## 开发

```bash
# 安装依赖
npm install

# 开发模式
npm run dev

# 构建
npm run build

# 生产模式
npm start
```

## 配置

API 代理配置在 `next.config.mjs` 中：

```javascript
async rewrites() {
  return [
    {
      source: "/api/:path*",
      destination: "http://localhost:8000/:path*",
    },
  ];
}
```

确保后端服务器运行在 `http://localhost:8000`

## 项目结构

```
src/
├── app/              # Next.js App Router
│   ├── page.tsx      # 首页
│   ├── worlds/       # 世界管理
│   └── ...
├── components/       # 可复用组件
├── lib/              # 工具函数
│   └── api.ts        # API 客户端
├── types/            # TypeScript 类型
└── hooks/            # React Hooks
```
