# Deep Research Agent: from Deep Agents to Managed Deep Agents

A research agent that plans its work, searches the web, writes cited reports, and turns its findings into LinkedIn posts or Twitter/X threads. It's built twice, so you can see what changes when LangSmith runs the infrastructure for you.

| Folder | What it is | You run |
|---|---|---|
| [`1-deep-agent/`](1-deep-agent/) | The agent built with open-source [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) on LangGraph. You wire up the backend, memory store, and deployment config yourself. | `uv run langgraph dev` |
| [`2-managed-deep-agent/`](2-managed-deep-agent/) | **The same agent** as a [LangSmith Managed Deep Agent](https://docs.langchain.com/langsmith/python/managed-deep-agents-overview). It's a folder of small files, and LangSmith adds hosting, a sandbox, durable memory, Slack, and cron jobs. | `uv run mda deploy` |

Each folder is a separate project with its own `README.md`, `pyproject.toml`, and `.env`.

## Workshop path

1. **Read the code**: open [`1-deep-agent/agent.py`](1-deep-agent/agent.py) to see how a Deep Agent is assembled.
2. **Compare**: open [`2-managed-deep-agent/agent.py`](2-managed-deep-agent/agent.py). The same agent is about 20 lines, and each extra feature is its own file. The [mapping table](2-managed-deep-agent/README.md#how-part-1-maps-to-part-2) shows where each piece went.
3. **Deploy it yourself**: follow [`2-managed-deep-agent/README.md`](2-managed-deep-agent/README.md) to run it locally, deploy it to LangSmith, and chat with it in Slack.

**Quick start (Part 2):**

```bash
git clone https://github.com/langchain-samples/Liam-Deepagent-Demo.git
cd Liam-Deepagent-Demo/2-managed-deep-agent
uv sync
cp .env.example .env      # add your LangSmith, OpenAI, and Tavily keys
uv run mda dev            # try it locally in LangSmith Studio
uv run mda deploy         # deploy to LangSmith + connect Slack
```

You need [uv](https://docs.astral.sh/uv/getting-started/installation/) and API keys for [LangSmith](https://smith.langchain.com) (Settings → API Keys), [OpenAI](https://platform.openai.com/api-keys), and [Tavily](https://app.tavily.com).

## Set up your coding agent for LangSmith

If you build with Claude Code, Cursor, Codex, or another coding agent, these give it direct access to LangSmith and the docs:

- **[LangSmith CLI](https://docs.langchain.com/langsmith/langsmith-cli)**: lets your agent query and manage tracing projects, traces, datasets, evaluators, and experiments from the terminal.
  ```bash
  curl -fsSL https://cli.langsmith.com/install.sh | sh
  ```
- **[LangSmith Skills](https://docs.langchain.com/langsmith/skills)**: guidance and best practices for tracing, building datasets, and writing evaluators.
  ```bash
  npx skills add langchain-ai/langsmith-skills --skill '*' --yes
  ```
- **Managed Deep Agents skill**: walks your agent through building, testing, and deploying with the `mda` CLI.
  ```bash
  npx skills add langchain-ai/langchain-skills --skill managed-deep-agents --yes
  ```
- **LangChain docs MCP**: lets your agent read the LangChain and LangSmith docs directly.
  ```bash
  claude mcp add --transport http langchain-docs https://docs.langchain.com/mcp
  ```
- **[Tracing docs](https://docs.langchain.com/langsmith/observability-quickstart)**: how to send traces from your own code to LangSmith.

## Learn more

- [Deep Agents documentation](https://docs.langchain.com/oss/python/deepagents/overview)
- [Managed Deep Agents documentation](https://docs.langchain.com/langsmith/python/managed-deep-agents-overview)
- [LangSmith](https://docs.langchain.com/langsmith/home)
- [LangChain Academy](https://academy.langchain.com/)
