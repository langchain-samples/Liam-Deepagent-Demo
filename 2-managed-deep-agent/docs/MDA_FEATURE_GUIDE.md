# Managed Deep Agents: Feature Guide

A tour of everything Managed Deep Agents (MDA) can do, and where each feature lives in a project. For step-by-step setup, see [the project README](../README.md).

MDA is in public beta on LangSmith Cloud. Docs: [docs.langchain.com/langsmith/python/managed-deep-agents-overview](https://docs.langchain.com/langsmith/python/managed-deep-agents-overview)

**Legend:** ✅ used in this project · ➕ available, not used here

---

## How MDA works

You write the agent's *business logic*: instructions, tools, skills, and the model. MDA provides the rest:

- **The Deep Agents harness**: the same open-source agent loop as Part 1 (filesystem tools, subagents, skills, and planning with `write_todos` once you add `TodoListMiddleware`).
- **A managed runtime**: every deployment runs on LangSmith Agent Server, so you get threads, runs, streaming, an API, and an MCP endpoint without running a server.

The key difference from Part 1: `create_deep_agent()` returns a compiled agent that *you* host. `define_deep_agent()` returns a *definition*. The `mda` CLI hands it to LangSmith, which supplies the backend, store, checkpointer, memory, skills, and system prompt.

**Every feature is a file.** Add the file to turn the feature on, delete it to turn it off.

| Feature | File | Here? |
|---|---|---|
| [Agent definition](#1-agent-definition) | `agent.py` (required) | ✅ |
| [Instructions](#2-instructions) | `instructions.md` | ✅ |
| [Skills](#3-skills) | `skills/<name>/SKILL.md` | ✅ |
| [Custom tools](#4-custom-tools) | `tools/*.py` | ✅ |
| [MCP connectors](#5-mcp-connectors) | `tools/mcp.py` | ✅ |
| [Middleware](#6-middleware) | `middleware/*.py` | ✅ |
| [Subagents](#7-subagents) | `subagents=` in `agent.py` | ✅ |
| [Human-in-the-loop](#8-human-in-the-loop) | `interrupt_on=` in `agent.py` | ➕ |
| [Memory](#9-memory) | `memory.py` | ✅ |
| [Sandbox](#10-sandbox) | `sandbox/__init__.py` (+ `setup.sh`) | ✅ |
| [Identity](#11-identity) | `identity.py` | ✅ |
| [Connections](#12-connections) | `mda connections create` | ➕ |
| [Slack](#13-slack-channel) | `channels/slack.py` | ✅ |
| [HTTP webhook channel](#14-http-channel) | `channels/<name>.py` | ➕ |
| [Schedules](#15-schedules) | `schedules/<name>.py` | ✅ |
| [MCP endpoint](#16-mcp-endpoint-use-your-agent-as-a-tool) | built into every deployment | ✅ |
| [Context Hub](#17-context-hub) | built in | ✅ |
| [Evals](#18-evals) | `evals/` | ➕ |

---

## 1. Agent definition

**File:** `agent.py` (required). It must export a variable named `agent`.

```python
from managed_deepagents import define_deep_agent

agent = define_deep_agent(
    name="research-agent",          # graph ID, deployment name, and the assistant_id clients use
    model="openai:gpt-6-luna",      # "provider:model", or a LangChain chat model instance
    tools=[tavily_search],
    middleware=[log_tool_calls, TodoListMiddleware()],  # TodoListMiddleware adds write_todos
    subagents=[fact_checker],
)
```

| Parameter | What it does |
|---|---|
| `name` | Required. Letters, numbers, `-`, `_`, starting with a letter. Clients call the agent by this name. |
| `model` | Any LangChain provider, e.g. `"anthropic:claude-sonnet-4-6"`. Put the provider's API key in `.env`. |
| `tools` | Your tools, or a provider's built-in tools such as `{"type": "web_search"}` for OpenAI. |
| `middleware` | Runs around model and tool calls, in list order. |
| `subagents` | Specialist agents the main agent can delegate to. |
| `interrupt_on` | Pause for human approval before chosen tools run. |
| `permissions` | Filesystem path rules. Cleared when the project has a sandbox. |
| `response_format` | Force structured output that matches a schema. |

**LLM Gateway:** use `model="langsmith:provider/model"` (note the slash) to route calls through LangSmith's gateway for rate limits, fallbacks, and spend controls.

**Per-run configuration:** export a *function* named `agent` instead, and it can pick instructions, skills, MCP servers, or the sandbox for each run based on the caller's `context`. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-agent-definition#select-configuration-per-run)

## 2. Instructions

**File:** `instructions.md`. The always-on system prompt, loaded on every run. The agent can't change it.

On deploy it syncs to [Context Hub](#17-context-hub), where you can edit it in the LangSmith UI without redeploying. Keep the file in the repo as the source of truth. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-instructions)

## 3. Skills

**Files:** `skills/<name>/SKILL.md`, plus any supporting files (templates, scripts).

```markdown
---
name: twitter-post
description: Write a Twitter/X post or thread. Use when asked for tweets or threads.
---
# Twitter/X Post Skill
...
```

The agent sees only each skill's name and description at first, and reads the full skill when a task matches. Skills sync to Context Hub on deploy and are read-only to the agent. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-skills)

| | Instructions | Skills | Memory |
|---|---|---|---|
| Loaded | Every run | When relevant | When enabled |
| Agent can edit | No | No | Yes |

## 4. Custom tools

**Files:** any module in `tools/`. Import the tool in `agent.py` and add it to `tools=[...]`.

```python
from langchain.tools import tool

@tool(parse_docstring=True)
def tavily_search(query: str) -> str:
    """Search the web for information on a given query.

    Args:
        query: Search query to execute
    """
```

Tools read secrets from environment variables (`.env` locally; `mda deploy` sends them to the deployment). A tool can also take a `runtime: ManagedToolRuntime` parameter to see the verified caller, the Slack conversation, and the sandbox. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-tools)

## 5. MCP connectors

**File:** `tools/mcp.py`. Pull in tools from remote MCP servers without writing them yourself.

```python
from managed_deepagents import define_mcp

mcp = define_mcp(
    servers={
        "langchainDocs": {
            "transport": "http",
            "url": "https://docs.langchain.com/mcp",
            "include_tools": ["search_docs_by_lang_chain"],
        },
    },
)
```

- Supports HTTP and SSE servers (not stdio). One `mcp` per project: put every server in it.
- Tools are prefixed with the server name, e.g. `langchainDocs__search_docs_by_lang_chain`.
- `include_tools` / `exclude_tools` pick which tools to expose.
- For servers that need login, add a `connection` (see [Connections](#12-connections)).
- **Built-in web search (Parallel):** add `"Parallel": {"transport": "http", "url": "https://api.smith.langchain.com/v1/managed-tools/servers/parallel/mcp"}` for search with no extra API key (Plus/Startup plans, US region). [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-search)

[Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-mcp-connectors)

## 6. Middleware

**Files:** any module in `middleware/`. Import it in `agent.py` and add it to `middleware=[...]`.

Middleware wraps model and tool calls, for logging, PII redaction, call limits, retries, or model fallbacks. LangChain's prebuilt middleware works as-is:

```python
from langchain.agents.middleware import ModelCallLimitMiddleware, PIIMiddleware

middleware=[PIIMiddleware("email", strategy="redact", apply_to_input=True), ModelCallLimitMiddleware(run_limit=50)]
```

Custom middleware must use **async** hooks, because MDA always runs the agent asynchronously. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-middleware)

## 7. Subagents

**Where:** `subagents=[...]` in `agent.py`. Specialists with their own prompt, tools, and optionally model. The main agent delegates to them with the built-in `task` tool, which keeps their work out of its own context.

```python
fact_checker = {
    "name": "fact-checker",
    "description": "Checks a draft report's claims against the web before it is finalized.",
    "system_prompt": "You are a meticulous fact-checker...",
    "tools": [tavily_search],
}
```

[Docs](https://docs.langchain.com/oss/python/deepagents/subagents)

## 8. Human-in-the-loop

**Where:** `interrupt_on=` in `agent.py`. The run pauses before the chosen tools, so a person can approve, edit, or reject the call.

```python
agent = define_deep_agent(..., interrupt_on={"send_email": True})
```

Studio shows the pending call locally. In Slack, approvals render as Approve / Reject buttons. Via the API, resume with `Command(resume=...)`. MDA stores the paused state for you. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-tools#human-in-the-loop)

## 9. Memory

**File:** `memory.py`. Without it, the agent remembers nothing between conversations.

```python
from managed_deepagents import MemoryLayer, define_memory

memory = define_memory(
    agent=MemoryLayer(),  # /memories/agent/ - shared by everyone who uses the deployment
    user=MemoryLayer(),   # /memories/user/  - private to each signed-in person
)
```

- **Hot vs. cold memory:** `AGENTS.md` at the root of each folder is loaded into every model call, so keep it short. Other files are read only when needed.
- **What gets remembered** is up to the agent, guided by your instructions. See the Memory section of `instructions.md`.
- **User memory** needs a real signed-in person. By default it turns on in Studio and Slack DMs, not for plain API-key callers or Slack channels.
- **Agent memory is shared:** anything one caller gets the agent to save, every later caller sees. Never store secrets or personal data there.
- Memory lives in Context Hub, and deploys never overwrite it.

[Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-memory)

## 10. Sandbox

**Files:** `sandbox/__init__.py`, plus optional `sandbox/setup.sh`. Each conversation gets its own isolated Linux machine with a filesystem and a shell.

```python
from managed_deepagents import define_sandbox

sandbox = define_sandbox(
    idle_ttl_seconds=600,   # delete the sandbox after 10 idle minutes
    default_timeout=600,    # max seconds per shell command
)
```

- The agent works in it with `ls`, `read_file`, `write_file`, `edit_file`, `glob`, `grep`, and `execute` (shell).
- **`setup.sh`** runs once per deploy and is saved as a snapshot that every new conversation starts from. This project uses it to install `pandoc`, `pandas`, and `matplotlib`. The image is Debian, so install packages with `apt-get`, not `pip`.
- **Custom base image:** set `docker_image="python:3.12-slim"` (or `snapshot_name` / `snapshot_id`).
- **Auth proxy:** inject API keys into the sandbox's outbound requests without the code ever seeing them.
- Your own tools can read and write sandbox files through `runtime.backend`.

[Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-sandboxes)

## 11. Identity

**File:** `identity.py`. Decides who can call your deployment.

| Option | Code | Best for |
|---|---|---|
| LangSmith API key (this project) | `auth.langsmith_api_key()` | Scripts, notebooks, MCP clients. Everyone with the key shares one identity. |
| Supabase | `auth.supabase(project_ref="...")` | Signed-in end users, each with private threads and memory |
| Your own backend | `"backend"` + `MDA_INGRESS_SECRET` | Your API logs users in and calls the agent for them |

Members of your LangSmith workspace can always see every thread in Studio. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-identity)

## 12. Connections

**Command:** `uv run mda connections create <name> ...`. Store API keys and OAuth logins in your LangSmith workspace instead of in `.env`. Tools fetch them at runtime:

```python
from managed_deepagents import connections

api_key = await connections.get("company-tavily", {"type": "agent"})   # one shared credential
token = await connections.get("my-github", {"type": "user"})           # each caller's own login
```

- **Agent-owned:** one credential for the whole deployment, e.g. `mda connections create company-tavily --secret-from-env TAVILY_API_KEY`.
- **User-owned (OAuth):** each person signs in to their own account. MDA runs the whole OAuth flow, including the login prompt in Slack and Studio.
- Built-in OAuth settings for GitHub, Google, Slack, Linear, Notion, Atlassian, and more: `mda connections catalog`.
- Rotate a key without redeploying.

[Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-connections)

## 13. Slack channel

**File:** `channels/slack.py`.

```python
from managed_deepagents import channels

channel = channels.slack(
    name="Research Agent",
    description="Researches topics on the web and writes cited reports and social posts",
)
```

- `mda deploy` creates the Slack app for you. The first time, you approve it in your browser.
- People DM the agent, @mention it, or reply in its threads. Each Slack thread is its own conversation.
- Slack users count as signed-in people, so they get user memory (in DMs) and their own OAuth connections.
- With a sandbox, users can upload files to the agent, and the agent can send files back.
- Options: `icon`, `background_color`, `reactions` (the emoji it reacts with), `trigger_on_all_messages`, `allow_bot_triggers`.
- **Advanced:** tools can post interactive Block Kit forms and pause until someone clicks ([agent-owned interrupts](https://docs.langchain.com/langsmith/python/managed-deep-agents-agent-owned-interrupts)).

[Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-channels-slack)

## 14. HTTP channel

**File:** `channels/<name>.py` with `channels.http(...)`. Turns the agent into a webhook endpoint (`POST /channels/<name>/events`) that any service can call. You write `verify` (check the signature), `parse` (turn the request into a message), and optionally `post` (send the reply back). [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-channels-http)

## 15. Schedules

**Files:** `schedules/<name>.py`. Run the agent on a cron schedule.

```python
from managed_deepagents import define_schedule

schedule = define_schedule(
    cron="0 9 * * 1",                    # every Monday at 09:00
    timezone="America/Los_Angeles",
    prompt="Write a short weekly digest of the most useful research takeaways.",
)
```

- Each run gets a fresh conversation by default.
- `deliver_to=` posts the result to a Slack channel.
- Values must be plain literals (no environment variables or function calls).
- Created when `mda deploy` finishes. Don't use `--no-wait`.
- Tools can also create schedules at runtime ("remind me every Friday…") through `runtime.schedules`.

[Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-schedules)

## 16. MCP endpoint: use your agent as a tool

Every deployment exposes `<API_URL>/mcp`, so other agents can call yours as a tool:

```bash
claude mcp add --transport http research-agent <API_URL>/mcp --header "x-api-key: $LANGSMITH_API_KEY"
```

Find the **API URL** on the deployment page in LangSmith. Each MCP call is a fresh conversation. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-mcp-endpoint)

## 17. Context Hub

LangSmith's home for your agent's `instructions.md`, `skills/`, and memory. Open it from the deployment page to:

- edit instructions or skills live, without a redeploy, and
- browse what the agent has saved to memory.

If someone edits in the UI, the next `mda deploy` asks which version to keep. In CI, pass `--context-strategy overwrite` or `--context-strategy keep-hub`. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-context-hub)

## 18. Evals

`uv run mda evals init -i` sets up a [Harbor](https://www.harborframework.com/docs/tasks) eval workspace in `evals/` and hands off to your coding agent (Claude Code, Cursor, Codex…) with the `eval-engineering` skill, which writes test tasks for your agent. Results can be recorded in LangSmith. Requires Docker. [Docs](https://docs.langchain.com/langsmith/python/managed-deep-agents-evals)

---

## The `mda` CLI

| Command | What it does |
|---|---|
| `mda init <name>` | Create a new project (`--channel slack`, `--memory agent`, `--model ...`) |
| `mda dev` | Run locally in LangSmith Studio (`--port`, `--no-browser`, `--no-schedules`) |
| `mda build` | Compile without deploying, to check for errors |
| `mda deploy` | Deploy to LangSmith (`--name`, `--deployment-type prod`) |
| `mda logs` | Stream the deployment's logs (`--level error`) |
| `mda delete` | Delete the deployment and what it created |
| `mda connections ...` | Manage stored API keys and OAuth logins |
| `mda channels init slack` | Add a Slack channel to an existing project |
| `mda evals init -i` | Set up Harbor evals |

**What `mda deploy` does with each file:**

```text
instructions.md + skills/   ->  Context Hub (editable in the UI)
.env                        ->  deployment secrets (the file itself is never uploaded)
everything else             ->  built and deployed to LangSmith
schedules/                  ->  cron jobs, created once the deployment is live
channels/slack.py           ->  a Slack app for your agent
```

## Coming from Deep Agents?

| Deep Agents (`create_deep_agent`) | Managed Deep Agents |
|---|---|
| `system_prompt=` | `instructions.md` |
| `skills=` | `skills/` |
| `memory=` / `StoreBackend` | `memory.py` |
| `backend=` (sandbox) | `sandbox/` |
| `store=`, `checkpointer=` | Handled for you; remove them |
| `model`, `tools`, `middleware`, `subagents`, `interrupt_on`, `response_format` | Same in `define_deep_agent` |
| `state_schema` | Not supported (Python) |
| Custom server routes | Not supported; use a regular LangSmith deployment |

[Full migration guide](https://docs.langchain.com/langsmith/python/managed-deep-agents-migrate)
