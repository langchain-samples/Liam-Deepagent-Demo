# 2. Deep Research Agent as a Managed Deep Agent

> Part 2 of the workshop. This is the same agent as [Part 1](../1-deep-agent/), packaged for [LangSmith Managed Deep Agents](https://docs.langchain.com/langsmith/python/managed-deep-agents-overview) (MDA). Managed Deep Agents is in public beta on LangSmith Cloud.

In Part 1 you wrote the agent **and** the plumbing around it: backend, store, permissions, server config. With MDA you keep only the agent: instructions, tools, skills, and the model. Each extra capability is one small file, and LangSmith runs everything else: the Deep Agents harness, hosting, sandboxes, memory, Slack, and cron.

## What's in this folder

Every file maps to one MDA feature. Open any of them: most are under 10 lines.

> **New to MDA?** [docs/MDA_FEATURE_GUIDE.md](docs/MDA_FEATURE_GUIDE.md) tours every feature, including the ones this project doesn't use yet. [docs/MDA_VS_DEEP_AGENTS.md](docs/MDA_VS_DEEP_AGENTS.md) explains what MDA gives you that plain Deep Agents doesn't.

```
2-managed-deep-agent/
├── agent.py              # the agent: model, tools, middleware, subagent      (required)
├── instructions.md       # system prompt (was AGENTS.md)
├── skills/               # LinkedIn + Twitter skills, loaded only when needed
├── tools/
│   ├── search.py         # Tavily web search (same code as Part 1)
│   └── mcp.py            # remote MCP tools: LangChain docs search
├── middleware/audit.py   # logs every tool call (same idea as Part 1)
├── memory.py             # durable memory: shared agent memory + per-user memory
├── sandbox/
│   ├── __init__.py       # an isolated filesystem + shell for each conversation
│   └── setup.sh          # customizes the sandbox image (installs pandoc, pandas, …)
├── identity.py           # who can call the deployment (LangSmith API key)
├── channels/             # talk to the agent in Slack (slack.py + bot icon)
├── schedules/            # cron job: a weekly research digest every Monday
├── pyproject.toml        # dependencies
├── .env.example          # API keys template
└── docs/
    ├── MDA_FEATURE_GUIDE.md   # every MDA feature, explained
    └── MDA_VS_DEEP_AGENTS.md  # what MDA adds on top of Deep Agents
```

### How Part 1 maps to Part 2

| Part 1 (`1-deep-agent/agent.py`) | Part 2 (this folder) |
|---|---|
| `create_deep_agent(...)` builds and compiles the agent | `define_deep_agent(...)` only *declares* it; LangSmith compiles and runs it |
| `system_prompt=` loaded from `AGENTS.md` | `instructions.md` |
| `skills=["/skills/"]` + a `FilesystemBackend` mount | `skills/` (no backend needed) |
| `StoreBackend` at `/memories/` | `memory.py` (`/memories/agent/` and `/memories/user/`) |
| `StateBackend` scratch files | `sandbox/`: a real filesystem with a shell |
| `FilesystemPermission` deny on `/skills/**` | Not needed: instructions and skills are read-only to the agent |
| `langgraph.json` + deploy from GitHub | `uv run mda deploy` |
| Not available | Slack (`channels/`), cron jobs (`schedules/`), MCP tools (`tools/mcp.py`), caller auth (`identity.py`) |

## Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/)
- API keys:
  - **LangSmith**: [smith.langchain.com](https://smith.langchain.com) → Settings → API Keys (use a *personal* key)
  - **OpenAI**: [platform.openai.com/api-keys](https://platform.openai.com/api-keys)
  - **Tavily**: [app.tavily.com](https://app.tavily.com) (free tier available)
- A Slack workspace where you can install apps (for the Slack step)

## Step 1: Install and add your keys

```bash
git clone https://github.com/langchain-samples/Liam-Deepagent-Demo.git
cd Liam-Deepagent-Demo/2-managed-deep-agent
uv sync
cp .env.example .env      # then open .env and paste your three keys
```

`.env` is git-ignored. `mda deploy` sends your OpenAI and Tavily keys to the deployment as secrets, so you don't have to configure them in the UI.

## Step 2: Run it locally in Studio

```bash
uv run mda dev
```

This compiles the project, builds the sandbox from `sandbox/setup.sh` (the first run takes a minute or two), starts a local server, and opens LangSmith Studio. Try:

> Research what LangChain Deep Agents are, write a brief report, and then write a LinkedIn post about your findings.

Watch the agent plan, search, hand the draft to the `fact-checker` subagent, and write `/workspace/final_report.md` in its sandbox. Stop the server with `Ctrl+C`, and rerun `uv run mda dev` after you change files.

> Locally, Slack doesn't connect and memory is stored on disk under `.mda/`. Both work for real after you deploy.

## Step 3: Deploy to LangSmith and connect Slack

```bash
uv run mda deploy
```

This one command:

1. Uploads `instructions.md` and `skills/` to LangSmith Context Hub, where you can edit them in the UI without redeploying.
2. Builds and deploys the agent on LangSmith (a few minutes).
3. Creates the Monday cron job from `schedules/`.
4. Creates a Slack app for your agent from `channels/slack.py`.

**The first time**, the CLI prints a Slack authorization link:

1. Open the link, pick your Slack workspace, and click **Allow**. If your workspace needs admin approval, get that first.
2. Go back to the terminal and press **Enter**. The deploy continues.
3. When it finishes, **the agent sends you a DM in Slack.** Reply to start a conversation.

In Slack you can DM the agent, `@mention` it in a channel (invite it first), and reply in its threads. Each Slack thread is its own conversation with its own sandbox.

When the deploy finishes, the CLI prints your deployment's URL in LangSmith. Open it to see traces of every run, the cron job, and the **Context Hub** link for live-editing instructions and skills.

> Don't use `--no-wait` with this project. Slack setup needs the finished deployment.

## Step 4: Try each feature

| Feature | Try this | Where to look |
|---|---|---|
| **Skills** | "Write a Twitter thread about vector databases" | The agent reads `skills/twitter-post/SKILL.md` |
| **Subagent** | "Write a fact-checked report on SASE" | A `task` tool call to `fact-checker` in the trace |
| **Sandbox** | "Turn your report into HTML with pandoc" | `execute` calls; tools installed by `sandbox/setup.sh` |
| **Agent memory** | In one thread: "Remember: always check official docs first." Then ask in a *new* thread how it researches | `/memories/agent/` in Context Hub, shared by everyone |
| **User memory** | DM the agent in Slack: "I prefer short, punchy posts" | `/memories/user/`, private to you (Slack DMs and Studio) |
| **MCP tools** | "How do I add memory to a LangGraph agent?" | `langchainDocs__search_docs_by_lang_chain` calls |
| **Schedules** | Wait until Monday 09:00 PT, or edit the cron in `schedules/weekly_digest.py` and redeploy | Crons tab on the deployment |
| **Live instructions** | Edit `instructions.md` in Context Hub from the deployment page | Next run uses it without a redeploy |

### Call it from code or another agent

Every deployment is an Agent Server with an API and an MCP endpoint. Copy the **API URL** from the deployment page, then:

```bash
# Use the agent as a tool inside Claude Code
claude mcp add --transport http research-agent <API_URL>/mcp --header "x-api-key: $LANGSMITH_API_KEY"
```

```python
from langgraph_sdk import get_sync_client

client = get_sync_client(url="<API_URL>", api_key="<LANGSMITH_API_KEY>")
result = client.runs.wait(None, "research-agent", input={"messages": [{"role": "user", "content": "Research SASE trends"}]})
print(result["messages"][-1]["content"])
```

## Customize it

| To change… | Edit |
|---|---|
| Persona, workflow, rules | `instructions.md` |
| Add a skill | `skills/<name>/SKILL.md` with `name` and `description` frontmatter |
| Add a tool | Write it in `tools/`, import it in `agent.py`, add it to `tools=[...]` |
| Add an MCP server | Add an entry to `servers` in `tools/mcp.py` |
| The model | `model=` in `agent.py`, e.g. `"anthropic:claude-sonnet-4-6"` (add `ANTHROPIC_API_KEY` to `.env`) |
| Sandbox packages | `sandbox/setup.sh` (it reruns only when the file changes) |
| Schedule | `cron=` / `prompt=` in `schedules/weekly_digest.py` |
| Slack name or description | `channels/slack.py`, then redeploy |

## Clean up

```bash
uv run mda delete
```

Deletes the deployment and the LangSmith resources it created, including its sandboxes and sandbox snapshots.

## Troubleshooting

**`LangSmith could not identify the API key owner` or 403 errors.** The key is wrong or revoked, or it isn't a personal key. `mda` reads `.env` first, so check the key there. If you also exported an old `LANGSMITH_API_KEY` in your shell, other tools may still pick that one up.

**`Deploy fails with 401/403`.** Your LangSmith workspace needs access to deployments and the Managed Deep Agents beta. See [pricing plans](https://www.langchain.com/pricing).

**Context Hub conflict on deploy.** Someone edited `instructions.md` or `skills/` in the LangSmith UI. Answer the prompt, or in CI pass `--context-strategy overwrite` (use your local files) or `--context-strategy keep-hub` (keep the UI edits).

**`sandbox setup.sh exited with code 1`.** The sandbox image is Debian, so install Python packages with `apt-get install python3-<name>`, not `pip install`.

**Want a different region?** Set `LANGSMITH_ENDPOINT` in `.env` before your first deploy, e.g. `https://eu.api.smith.langchain.com`.

## Learn more

- [Managed Deep Agents overview](https://docs.langchain.com/langsmith/python/managed-deep-agents-overview)
- [Quickstart](https://docs.langchain.com/langsmith/python/managed-deep-agents-quickstart) · [Project structure](https://docs.langchain.com/langsmith/python/managed-deep-agents-project-structure) · [CLI reference](https://docs.langchain.com/langsmith/python/managed-deep-agents-cli)
- [Slack](https://docs.langchain.com/langsmith/python/managed-deep-agents-channels-slack) · [Memory](https://docs.langchain.com/langsmith/python/managed-deep-agents-memory) · [Sandboxes](https://docs.langchain.com/langsmith/python/managed-deep-agents-sandboxes) · [Schedules](https://docs.langchain.com/langsmith/python/managed-deep-agents-schedules)
- [Move from Deep Agents](https://docs.langchain.com/langsmith/python/managed-deep-agents-migrate)
