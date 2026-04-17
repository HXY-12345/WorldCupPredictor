# Claude Code 项目配置

## CDP Proxy 修复经验

**问题**：`web-access` skill 的 CDP Proxy 连接失败，提示 `Node.js 版本 < 22 且未安装 ws 模块`

**原因**：
- `ws` 全局安装后，ES 模块的 `import()` 无法直接找到全局模块
- Node.js 20.x 需要回退到 `ws` 模块（Node 22+ 有原生 WebSocket）

**解决方案**：
```bash
cd "C:/Users/Administrator/.claude/skills/web-access"
npm install ws
```

在 skill 目录中本地安装 `ws`，而非全局安装。
