# AI 学习规划师

基于大模型和多智能体系统的个性化学习规划平台。

## 项目简介

通过 AI 智能体与用户对话，理解学习目标，生成个性化学习计划，配合游戏化激励机制，帮助用户高效学习。

## 核心功能

- 🤖 **AI 对话规划** — 多智能体系统，深度理解学习需求
- 📋 **个性化计划** — 基于生活习惯、知识储备定制学习路径
- ✅ **任务打卡** — 每日任务追踪，培养学习习惯
- 🏆 **成就系统** — 积分、徽章、等级，激发学习动力

## 技术栈

### 后端
- Python 3.11+ / FastAPI
- PostgreSQL + Redis
- 阿里云 DashScope (通义千问)
- LangGraph (多智能体调度)

### 前端
- UniApp + Vue3 (跨平台)

### 部署
- Docker / 阿里云 ECS
- 阿里云 OSS / VOD

## 项目结构

```
ai-study-planner/
├── backend/              # Python FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── models/      # 数据模型
│   │   ├── services/    # 业务逻辑
│   │   ├── agents/      # AI 智能体
│   │   ├── schemas/     # Pydantic 模型
│   │   └── db/          # 数据库
│   ├── tests/           # 测试
│   └── requirements.txt
├── frontend/             # UniApp 前端
├── docs/                # 项目文档
├── logs/                # 日志目录
└── README.md
```

## 快速开始

### 环境要求

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+
- Redis 7+

### 后端启动

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env  # 配置环境变量
uvicorn app.main:app --reload
```

### 前端启动

```bash
cd frontend
npm install
npm run dev:h5
```

## 文档

- [需求文档 (PRD)](docs/PRD.md)
- [技术架构](docs/ARCHITECTURE.md)
- [实现计划](docs/IMPLEMENTATION.md)
- [变更日志](docs/CHANGELOG.md)

## 许可证

MIT License
