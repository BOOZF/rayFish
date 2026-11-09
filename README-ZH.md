# RayFish

<em>基于多智能体的模拟引擎，用 AI 人设检验你的想法</em>

[English](./README.md) | [中文文档](./README-ZH.md)

## ⚡ 项目概述

**RayFish** 把种子材料（如产品简介、新闻、政策草案）变成一个模拟的社交世界。它从材料中构建知识图谱，生成拥有独立档案和记忆的 AI 人设，并让它们在模拟的 Twitter 和 Reddit 平台上发帖、回复和互动。运行结束后，报告智能体会分析发生了什么，你还可以与报告智能体或任意人设对话。

> 你只需提供：种子材料和一个用自然语言描述的问题</br>
> RayFish 将返回：一份书面报告，以及一个可以继续提问的模拟世界

RayFish 模拟的是 AI 人设，并不收集真实用户的反馈。请把它的结果当作探索可能反应的工具，而不是真实反应的证据。

## 🔄 工作流程

1. **图谱构建**：从种子材料中提取实体和关系，存入知识图谱
2. **环境搭建**：生成人设和模拟配置
3. **开始模拟**：并行运行 Twitter 和 Reddit 模拟，并把活动写回图谱
4. **报告生成**：报告智能体检索图谱和模拟数据并撰写报告
5. **深度互动**：与报告智能体或任意人设对话

## 🚀 快速开始

### 前置要求

| 工具 | 版本要求 | 说明 | 安装检查 |
|------|---------|------|---------|
| **Node.js** | 18+ | 前端运行环境，包含 npm | `node -v` |
| **Python** | ≥3.11, ≤3.12 | 后端运行环境 | `python --version` |
| **uv** | 最新版 | Python 包管理器 | `uv --version` |

### 1. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env 文件，填入 API 密钥
```

**必需的环境变量：**

```env
# 支持任意兼容 OpenAI SDK 格式的 LLM API
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-5-mini

# Zep Cloud（知识图谱）：https://app.getzep.com/
ZEP_API_KEY=your_zep_api_key
```

模拟会大量调用 LLM，建议先用少量智能体、少量轮次试运行。

### 2. 安装依赖

```bash
npm run setup:all
```

或者分步安装：

```bash
npm run setup          # Node 依赖（根目录 + 前端）
npm run setup:backend  # Python 依赖（自动创建虚拟环境）
```

### 3. 启动服务

```bash
npm run dev
```

- 前端：`http://localhost:3000`
- 后端 API：`http://localhost:5001`

单独启动：

```bash
npm run backend
npm run frontend
```

部署说明见 [DEPLOY.md](./DEPLOY.md)。

## 📄 致谢

模拟引擎由 CAMEL-AI 团队的 **[OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis)** 驱动。

## ⚖️ 许可证

本项目采用 [GNU AGPL-3.0](./LICENSE) 许可证。本项目是 [MiroFish](https://github.com/666ghj/MiroFish) 的修改版本，原项目同样采用 AGPL-3.0 许可证。
