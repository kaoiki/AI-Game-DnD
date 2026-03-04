# 🚀 事件驱动 LLM MVP 框架

一个基于 FastAPI 构建的轻量级事件驱动后端框架，用于实现结构化的大模型（LLM）事件流程系统。

本项目提供一个最小可运行（MVP）的后端基座，支持以“事件”为核心的系统架构设计，例如：

```
INIT → ACTION → RESOLUTION
```

适用于 AI 叙事系统、游戏流程引擎、Agent 调度系统等场景。

---

## ✨ 当前能力（MVP 基座）

* 基于 FastAPI 构建的后端服务
* 统一事件入口（/invoke）
* 事件路由分发骨架
* 统一返回结构（success / error）
* 全局异常处理
* 基础结构化日志
* `.env` 环境配置管理（pydantic-settings）
* 健康检查接口
* pytest 测试基座
* 使用 `uv` 管理依赖
* 开发使用 `uvicorn`
* 内部测试/稳定运行使用 `gunicorn`

---

## 🏗 架构概览

```
客户端
  ↓
/invoke（事件入口）
  ↓
事件路由分发
  ↓
具体事件处理（如 INIT）
  ↓
LLM 适配层（DeepSeek）
  ↓
统一响应结构返回
```

系统分层说明：

* **传输层**：FastAPI 接口
* **路由层**：事件分发
* **业务层**：具体事件逻辑
* **模型层**：LLM 调用适配
* **基础设施层**：配置、日志、响应封装

---

## 📦 技术栈

* Python 3.10+
* FastAPI
* Pydantic v2
* pydantic-settings
* uv（依赖管理）
* Uvicorn（开发运行）
* Gunicorn（内部测试 / 生产形态运行）
* DeepSeek SDK

---

## ⚙️ 安装依赖

使用 uv：

```bash
uv sync
```

如需手动添加：

```bash
uv add fastapi uvicorn gunicorn pydantic-settings python-dotenv
```

---

## 🔧 环境配置

在项目根目录创建 `.env` 文件：

```
DEEPSEEK_API_BASE=https://api.deepseek.com
DEEPSEEK_API_KEY=your_key_here
```

配置读取采用 `pydantic-settings` 管理。

---

## ▶️ 启动方式

### 本地开发

```bash
uv run uvicorn app.main:app --reload
```

### 内部测试 / 稳定运行

```bash
uv run gunicorn app.main:app \
  -k uvicorn.workers.UvicornWorker \
  -w 4 \
  -b 0.0.0.0:8000
```

---

## ❤️ 健康检查

```
GET /health
```

返回：

```json
{
  "status": "ok"
}
```

---

## 🧠 事件入口

```
POST /invoke
```

所有事件通过统一入口分发。

示例请求：

```json
{
  "event": {
    "type": "INIT"
  },
  "context": {}
}
```

---

## 🧪 测试

运行测试：

```bash
uv run pytest
```

---

## 📁 项目结构（MVP 阶段）

```
app/
├── main.py                  # FastAPI 入口（app = FastAPI()）
├── api/                     # HTTP 路由层（只放接口）
│   ├── __init__.py
│   ├── health.py            # /health
│   └── invoke.py            # /invoke（事件总入口，仅分发骨架）
├── core/                    # 基础设施层（项目“地基”）
│   ├── __init__.py
│   ├── config.py            # pydantic-settings：统一读取 .env
│   ├── logging.py           # logging 基座（格式/请求id等）
│   ├── response.py          # success()/error() 统一返回
│   └── exceptions.py        # 全局异常处理（注册到 FastAPI）
├── schemas/                 # 入参/出参模型（你说的 schema 控制）
│   ├── __init__.py
│   ├── base.py              # 公共模型（BaseResponse 等）
│   └── invoke.py            # InvokeRequest / InvokeResponse（事件入口模型）
├── events/                  # 事件体系（先骨架，不实现具体事件）
│   ├── __init__.py
│   ├── dispatcher.py        # 根据 event.type 分发
│   └── types.py             # 事件类型常量/枚举（INIT 等）
├── db/                      # DuckDB 相关（轻量持久化）
│   ├── __init__.py
│   ├── client.py            # duckdb 连接/初始化（最小封装）
│   └── repo.py              # 简单读写封装（MVP 可非常薄）
├── utils/                   # 工具函数（通用，不依赖业务）
│   ├── __init__.py
│   └── time.py              # 例如时间格式化/now等
├── scripts/                 # 你现在这些“验证脚本/实验脚本”归档到这里
│   ├── __init__.py
│   ├── check_deepseek_sdk.py
│   └── test_deepseek.py
└── playground/              # 可选：保留你当前 DnD 相关实验，不污染主代码
    ├── __init__.py
    ├── dnd_agent.py
    └── dnd_game.py
```

## 🎯 设计理念

本项目遵循以下原则：

* 先构建稳定的最小基座
* 统一入口，清晰分层
* 可扩展，但不过度设计
* 支持后续平滑演进至完整事件体系

---

## 📜 License

MIT License

---
