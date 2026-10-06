# Deep Research Agent

A production-ready research agent built with [Deep Agents](https://docs.langchain.com/oss/python/deepagents/) on top of [LangGraph](https://docs.langchain.com/oss/python/langgraph/). Give it a topic and it plans the work, searches the web, writes a cited report, and can turn its findings into LinkedIn posts or Twitter/X threads.

You can run it locally in LangGraph Studio with one command, and deploy it from GitHub with LangSmith Deployments.

## What the agent does

| Capability | How it works |
|---|---|
| **Planning** | Breaks each request into a to-do list (`write_todos`) and works through it |
| **Web research** | Searches the web with [Tavily](https://tavily.com) and cites every source |
| **Reports** | Writes a structured report with inline citations to `/final_report.md` |
| **Long-term memory** | Saves key takeaways to `/memories/`, which persist across conversations |
| **Skills** | Loads LinkedIn and Twitter/X writing guides only when a task needs them |
| **Guardrails** | Its own instructions and skills are read-only, so it can't rewrite its behavior |
| **Observability** | Every run is traced in [LangSmith](https://smith.langchain.com) |

## Project structure

```
.
├── agent.py                  # Agent definition (model, tools, memory, skills)
├── agent_config/
│   ├── AGENTS.md             # Agent identity, workflow, and rules (always loaded)
│   └── skills/
│       ├── linkedin-post/SKILL.md
│       └── twitter-post/SKILL.md
├── langgraph.json            # LangGraph server / deployment config
├── pyproject.toml            # Dependencies (pinned)
└── .env.example              # Template for required API keys
```

## Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/getting-started/installation/) (recommended) or pip
- API keys:
  - **OpenAI** – [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
  - **Tavily** – [app.tavily.com](https://app.tavily.com) (free tier available)
  - **LangSmith** – [smith.langchain.com](https://smith.langchain.com) → Settings → API Keys

## Run locally

**1. Clone and install**

```bash
git clone <this-repo-url>
cd <repo-name>
uv sync
```

<details>
<summary>Using pip instead of uv</summary>

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e . "langgraph-cli[inmem]"
```

Then drop the `uv run` prefix from the commands below.
</details>

**2. Add your API keys**

```bash
cp .env.example .env
```

Open `.env` and fill in `OPENAI_API_KEY`, `TAVILY_API_KEY`, and `LANGSMITH_API_KEY`. The `.env` file is git-ignored, so it is never committed.

**3. Start the agent**

```bash
uv run langgraph dev
```

> Use `uv run` so the server runs with this project's pinned dependencies rather than a global `langgraph` install.

LangGraph Studio opens in your browser. Select **research_agent** and try a prompt such as:

> Research what LangChain Deep Agents are, write a brief report, and then write a LinkedIn post about your findings.

In Studio you can watch the agent plan, call tools, and write files step by step. Each run also appears as a trace in your LangSmith project.

The local API is served at `http://127.0.0.1:2024`, so you can also call the agent from code with the [LangGraph SDK](https://docs.langchain.com/langsmith/sdk):

```python
from langgraph_sdk import get_sync_client

client = get_sync_client(url="http://127.0.0.1:2024")
for chunk in client.runs.stream(
    None,  # threadless run
    "research_agent",
    input={"messages": [{"role": "user", "content": "Research the latest trends in SASE."}]},
    stream_mode="updates",
):
    print(chunk.event, chunk.data)
```

## Deploy to LangSmith

1. **Push this repo to GitHub.** Your own `.env` stays local.
2. In [LangSmith](https://smith.langchain.com), go to **Deployments → + New Deployment**.
3. Connect your GitHub account and select this repository and branch.
4. Set the config file path to `langgraph.json`.
5. Under **Environment Variables**, add:

   | Name | Value |
   |---|---|
   | `OPENAI_API_KEY` | your OpenAI key |
   | `TAVILY_API_KEY` | your Tavily key |
   | `LANGSMITH_TRACING` | `true` |
   | `LANGSMITH_PROJECT` | e.g. `deepagents-research-agent` |

   The deployment reads these settings instead of a `.env` file. You don't need to add `LANGSMITH_API_KEY`, because the platform provides it.
6. Click **Submit**. When the build finishes, open the deployment in Studio or call its API URL with the SDK snippet above. Add your LangSmith API key as the `api_key`.

If you enable automatic updates, each push to the selected branch triggers a new revision.

## Customize the agent

| To change… | Edit |
|---|---|
| The agent's workflow, rules, or persona | `agent_config/AGENTS.md` |
| Add a new skill | Create `agent_config/skills/<skill-name>/SKILL.md` with `name` and `description` frontmatter (see the existing skills) |
| The model | `model = ChatOpenAI(model="gpt-5")` in `agent.py`; any LangChain chat model works, e.g. `ChatAnthropic` or `ChatBedrockConverse` |
| Tools | Add a `@tool` function in `agent.py` and include it in `tools=[...]` |
| Search depth | `max_results` in `tavily_search`, and the "Use 2-3 searches maximum" rule in `AGENTS.md` |

`langgraph dev` reloads automatically as you edit files.

## Troubleshooting

**`ImportError: cannot import name 'FilesystemPermission' from 'deepagents'`** (or a warning that `langgraph-api` is End of Life)

You started a `langgraph` that is installed globally or in another environment, and it has an older version of `deepagents`. Start the server from the project environment instead:

```bash
uv run langgraph dev
```

If you use pip, activate the project's `.venv` first, then check with `which langgraph`. It should point inside `.venv/`.

**Authentication errors from OpenAI or Tavily during a run**

`.env` is missing, or a key in it is empty or wrong. Copy `.env.example` to `.env`, fill it in, and restart `langgraph dev`.

### How storage works

The agent's virtual filesystem routes paths to different backends:

| Path | Backend | Lifetime |
|---|---|---|
| `/memories/` | LangGraph store | Persists across all conversations |
| `/config/` | Files in `agent_config/` | Read-only; versioned in git |
| Everything else (e.g. `/final_report.md`) | Thread state | Scoped to a single conversation |

Locally, `langgraph dev` keeps the store and conversation history in memory and saves them to `.langgraph_api/`. In a LangSmith deployment they are backed by managed Postgres.

## Learn more

- [Deep Agents documentation](https://docs.langchain.com/oss/python/deepagents/)
- [LangGraph documentation](https://docs.langchain.com/oss/python/langgraph/)
- [Deploying to LangSmith](https://docs.langchain.com/langsmith/deployments)
- [LangChain Academy](https://academy.langchain.com/)
