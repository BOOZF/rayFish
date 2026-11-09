# RayFish

<em>A multi-agent simulation engine for testing ideas on AI personas</em>

[English](./README.md) | [中文文档](./README-ZH.md)

## ⚡ Overview

**RayFish** turns seed material, such as a product brief, news story, or policy draft, into a simulated social world. It builds a knowledge graph from the material, generates AI personas with their own profiles and memory, and lets them post, reply, and react to each other on simulated Twitter and Reddit platforms. When the run finishes, a report agent analyses what happened, and you can chat with the report agent or with any persona.

> You provide: seed material and a question in plain language</br>
> RayFish returns: a written report and a simulated world you can question

RayFish simulates AI personas. It doesn't collect feedback from real users, so treat its output as a way to explore reactions, not as evidence of them.

## 🔄 Workflow

1. **Graph building**: extract entities and relationships from the seed material and store them in a knowledge graph
2. **Environment setup**: generate personas and the simulation configuration
3. **Simulation**: run Twitter and Reddit simulations in parallel, writing activity back to the graph
4. **Report generation**: a report agent searches the graph and simulation data and writes the report
5. **Interaction**: chat with the report agent or with any persona

## 🚀 Quick Start

### Prerequisites

| Tool | Version | Description | Check Installation |
|------|---------|-------------|-------------------|
| **Node.js** | 18+ | Frontend runtime, includes npm | `node -v` |
| **Python** | ≥3.11, ≤3.12 | Backend runtime | `python --version` |
| **uv** | Latest | Python package manager | `uv --version` |

### 1. Configure environment variables

```bash
cp .env.example .env
# Edit .env and fill in the API keys
```

**Required variables:**

```env
# Any LLM API that follows the OpenAI SDK format
LLM_API_KEY=your_api_key
LLM_BASE_URL=https://api.openai.com/v1
LLM_MODEL_NAME=gpt-5-mini

# Zep Cloud (knowledge graph): https://app.getzep.com/
ZEP_API_KEY=your_zep_api_key
```

Simulations make many LLM calls. Try a small run (few agents, few rounds) before a large one.

### 2. Install dependencies

```bash
npm run setup:all
```

Or step by step:

```bash
npm run setup          # Node dependencies (root + frontend)
npm run setup:backend  # Python dependencies (creates a virtual environment)
```

### 3. Start the services

```bash
npm run dev
```

- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:5001`

To start them separately:

```bash
npm run backend
npm run frontend
```

For hosting, see [DEPLOY.md](./DEPLOY.md).

## 📄 Acknowledgments

The simulation engine is powered by **[OASIS (Open Agent Social Interaction Simulations)](https://github.com/camel-ai/oasis)** from the CAMEL-AI team.

## ⚖️ License

Licensed under the [GNU AGPL-3.0](./LICENSE). This project is a modified version of [MiroFish](https://github.com/666ghj/MiroFish), also licensed under AGPL-3.0.
