# AI 学习规划师 — 技术架构

## 技术选型

| 层次 | 技术方案 |
|------|---------|
| 前端 | UniApp + Vue3 |
| 后端 | FastAPI + Python 3.11 |
| 数据库 | PostgreSQL + pgvector |
| 缓存 | Redis |
| AI | 阿里云 DashScope (通义千问) |
| 部署 | 阿里云 ECS / Docker |

## 系统架构

详见 `D:\310Programm\AIstudy\` 目录下的原始技术框架文档。

## 项目结构

```
backend/
├── app/
│   ├── api/v1/      # API 路由
│   ├── models/      # 数据模型
│   ├── services/    # 业务逻辑
│   ├── agents/      # AI 智能体
│   ├── schemas/     # Pydantic 模型
│   ├── db/          # 数据库
│   └── core/        # 核心工具
└── tests/           # 测试
```
