# Deep Agents: Feature Guide

A tour of everything the open-source [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) package (`deepagents`) can do. For step-by-step setup, see [the project README](../README.md).

**Legend:** ✅ used in this project · ➕ available, not used here

---

## How Deep Agents works

`create_deep_agent()` gives you a ready-made agent loop, built on LangChain's agent building blocks and run by LangGraph. LangGraph provides durable execution, streaming, and human-in-the-loop. Out of the box the agent can work with files, delegate to subagents, and keep long conversations under control. You add your model, tools, and instructions.

```bash
uv add deepagents        # or: pip install deepagents
```

You need a model that supports tool calling, plus that provider's API key.

| Feature | How you turn it on | Here? |
|---|---|---|
| [Create an agent](#1-create-an-agent) | `create_deep_agent(...)` | ✅ |
| [Models](#2-models) | `model=` | ✅ |
| [System prompt](#3-system-prompt) | `system_prompt=` | ✅ (from `AGENTS.md`) |
| [Custom tools](#4-custom-tools) | `tools=[...]` | ✅ |
| [MCP tools](#5-mcp-tools) | `MCPAdapter` → `tools=` | ➕ |
| [Built-in file tools](#6-built-in-file-tools) | always on | ✅ |
| [Backends](#7-backends-where-files-live) | `backend=` | ✅ |
| [Memory](#8-memory) | `memory=` + `StoreBackend` | ✅ (`/memories/`) |
| [Skills](#9-skills) | `skills=[...]` | ✅ |
| [Planning (to-dos)](#10-planning-to-dos) | `TodoListMiddleware()` | ✅ |
| [Subagents](#11-subagents) | `subagents=[...]` | ➕ (built-in general-purpose only) |
| [Human-in-the-loop](#12-human-in-the-loop) | `interrupt_on=` | ➕ |
| [Permissions](#13-permissions) | `permissions=[...]` | ✅ |
| [Sandboxes](#14-sandboxes) | sandbox `backend=` | ➕ |
| [Code interpreter](#15-code-interpreter) | `CodeInterpreterMiddleware()` | ➕ |
| [Middleware](#16-middleware) | `middleware=[...]` | ✅ (tool-call logging) |
| [Context management](#17-context-management-automatic) | automatic | ✅ |
| [Structured output](#18-structured-output) | `response_format=` | ➕ |
| [Streaming](#19-streaming) | `stream()` / `stream_events()` | ✅ (via Studio) |
| [Fault tolerance](#20-fault-tolerance) | retry/fallback middleware | ➕ |
| [Multimodal](#21-multimodal) | content blocks | ➕ |
| [Profiles](#22-harness-and-provider-profiles) | `register_harness_profile` | ➕ |
| [Deploying](#23-deploying) | `langgraph.json` | ✅ |
| [Frontends and protocols](#24-frontends-and-protocols) | `useStream`, ACP, AG-UI, A2A | ➕ |

---

## 1. Create an agent

```python
from deepagents import create_deep_agent

agent = create_deep_agent(
    model="openai:gpt-6-luna",
    tools=[tavily_search],
    system_prompt="You are an expert research assistant.",
)
result = agent.invoke({"messages": [{"role": "user", "content": "Research SASE trends"}]})
print(result["messages"][-1].content)
```

`create_deep_agent` returns a compiled LangGraph graph, so `invoke`, `stream`, and the rest of LangGraph work on it. Every parameter:

| Parameter | What it does |
|---|---|
| `model` | `"provider:model"` string or a chat model object |
| `tools` | Your tools: functions, `@tool`, tool dicts, MCP tools |
| `system_prompt` | Your instructions (placed before the built-in prompt) |
| `middleware` | Extra hooks around model and tool calls |
| `subagents` | Specialists the agent can delegate to |
| `skills` | Folders of on-demand `SKILL.md` playbooks |
| `memory` | `AGENTS.md` files loaded at startup |
| `permissions` | Read/write rules for the file tools |
| `backend` | Where files live (defaults to `StateBackend`) |
| `interrupt_on` | Pause before tools for human approval |
| `response_format` | Structured output schema |
| `state_schema` | Custom graph state (subclass `DeepAgentState`) |
| `context_schema` | Per-run context, e.g. a user ID, passed with `invoke(..., context=...)` |
| `checkpointer` | Saves conversation state. Required for human-in-the-loop. LangSmith provides it when deployed. |
| `store` | Long-term store used by `StoreBackend`. LangSmith provides it when deployed. |
| `debug`, `name`, `cache` | Debug mode, graph name, model cache |

[Docs](https://docs.langchain.com/oss/python/deepagents/customization)

## 2. Models

Use a `"provider:model"` string, or build the model yourself for full control:

```python
from langchain_openai import ChatOpenAI
model = ChatOpenAI(model="gpt-6-luna")     # this project
# or: model="anthropic:claude-sonnet-4-6", "google_genai:gemini-3.6-flash", ...
```

- Any LangChain chat model works. Install its package (e.g. `langchain-anthropic`) and set its API key.
- `openai:` strings use OpenAI's Responses API by default.
- Chat models retry transient failures automatically.
- **Switch models per request:** a `@wrap_model_call` middleware can read the model name from `context` and swap it with `request.override(model=...)`.

[Docs](https://docs.langchain.com/oss/python/deepagents/models)

## 3. System prompt

`system_prompt=` takes a string or a `SystemMessage`. This project reads it from `AGENTS.md`:

```python
system_prompt=(BASE_DIR / "AGENTS.md").read_text()
```

Your prompt always comes first, ahead of the built-in prompt, memory, skills, and tool instructions. For a prompt that changes per request, use `@dynamic_prompt` middleware. [Docs](https://docs.langchain.com/oss/python/deepagents/customization#system-prompt)

## 4. Custom tools

Plain functions and `@tool` functions both work. The tool's schema comes from the signature and docstring:

```python
from langchain_core.tools import tool

@tool(parse_docstring=True)
def tavily_search(query: str) -> str:
    """Search the web for information on a given query.

    Args:
        query: Search query to execute
    """
```

- **Provider-native web search:** pass `{"type": "web_search"}` (OpenAI), `{"google_search": {}}` (Gemini), or `{"type": "web_search_20260209", "name": "web_search"}` (Anthropic). No search API key needed.
- **Multimodal results:** a tool can return a list of content blocks (text, image, audio, video, file).

[Docs](https://docs.langchain.com/oss/python/deepagents/tools)

## 5. MCP tools

Load every tool from an MCP server and pass them in:

```python
from langchain.mcp import MCPAdapter      # pip install "langchain[mcp]"

config = {"mcpServers": {"docs": {"url": "https://docs.langchain.com/mcp"}}}
async with MCPAdapter(config) as adapter:
    tools = await adapter.list_tools()
    agent = create_deep_agent(model=model, tools=tools)
```

stdio servers, OAuth, and tool filtering are covered in the [LangChain MCP guide](https://docs.langchain.com/oss/python/langchain/mcp). [Docs](https://docs.langchain.com/oss/python/deepagents/tools#mcp-tools)

## 6. Built-in file tools

Every agent gets these automatically:

| Tool | What it does |
|---|---|
| `ls` | List a directory |
| `read_file` | Read a file, with paging. Images, audio, video, and PDFs come back as content the model can see. |
| `write_file` | Create or overwrite a file |
| `edit_file` | Replace exact text in a file |
| `delete` | Delete a file or folder |
| `glob` | Find files by pattern, e.g. `**/*.md` |
| `grep` | Search file contents |
| `execute` | Run shell commands (only with a backend that supports it) |
| `task` | Hand a job to a subagent |
| `write_todos` | Keep a to-do list. **Opt-in**, see [Planning](#10-planning-to-dos). |

Tools a backend can't support are hidden from the model. To expose only some tools, use `FilesystemMiddleware(backend=..., tools=["read_file", "ls", "glob", "grep"])`. [Docs](https://docs.langchain.com/oss/python/deepagents/tools#built-in-harness-tools)

## 7. Backends: where files live

The file tools read and write through a **backend**. Pick one, or route paths to several:

| Backend | Stores files in | Use for |
|---|---|---|
| `StateBackend` (default) | The conversation's state | Scratch files for one conversation |
| `StoreBackend(namespace=...)` | The LangGraph store | Files that persist across conversations (memory) |
| `FilesystemBackend(root_dir=..., virtual_mode=True)` | Your real disk | Local development. Can expose secrets on a server, so mount only what's safe. |
| `LocalShellBackend` | Real disk, plus an unrestricted shell | Local development only |
| `ContextHubBackend("my-agent")` | A LangSmith Context Hub repo | Shared, versioned files |
| Sandbox backends | An isolated machine | Running code (see [Sandboxes](#14-sandboxes)) |
| `CompositeBackend(default=..., routes={...})` | Routes by path prefix | Mixing the above |

This project routes three ways:

```python
backend = CompositeBackend(
    default=StateBackend(),                                                # /final_report.md: this conversation only
    routes={
        "/memories/": StoreBackend(namespace=lambda _rt: ("memories",)),   # shared across conversations
        "/skills/": FilesystemBackend(root_dir=BASE_DIR / "skills", virtual_mode=True),  # read-only skills
    },
)
```

- Always use `virtual_mode=True` with `FilesystemBackend`: it blocks paths that escape `root_dir`.
- Give `StoreBackend` an explicit `namespace`. Use the user's identity (`rt.server_info.user.identity`) for per-user files.
- Keep `StateBackend` as the default, because the agent stores internal data (like offloaded results) there.
- You can write your own backend by implementing `BackendProtocol`.

[Docs](https://docs.langchain.com/oss/python/deepagents/backends)

## 8. Memory

`memory=[...]` lists `AGENTS.md`-style files that are loaded into every conversation, and that the agent can update with `edit_file`. Route `/memories/` to a `StoreBackend` so they persist:

```python
agent = create_deep_agent(
    memory=["/memories/AGENTS.md"],
    backend=CompositeBackend(default=StateBackend(), routes={
        "/memories/": StoreBackend(namespace=lambda rt: (rt.server_info.user.identity,)),  # per user
    }),
)
```

- **Scope by namespace:** per user (`user.identity`, the recommended default), per agent (`assistant_id`), or per org (`rt.context.org_id`).
- Memory is always loaded. Skills load only when relevant.
- **Security:** shared, writable memory is a prompt-injection risk, so keep shared memory read-only where you can.
- This project saves notes to `/memories/research_notes.md`, shared by all users.
- **Advanced patterns:** episodic memory (searching past threads) and background consolidation (a cron job that tidies memory).

[Docs](https://docs.langchain.com/oss/python/deepagents/memory)

## 9. Skills

Skills are folders with a `SKILL.md`. The agent sees only each skill's name and description, and reads the full file when a task needs it:

```markdown
---
name: linkedin-post
description: Write a LinkedIn post. Use when asked for LinkedIn content.
---
# LinkedIn Post Skill
...
```

```python
agent = create_deep_agent(skills=["/skills/"], backend=backend)  # the PARENT folder of the skill folders
```

- Point `skills=` at the folder that *contains* the skill folders. Pointing at a single skill folder loads nothing.
- `name` must be lowercase-with-hyphens and match the folder name.
- **Extras:** pinned skills (force-load one, e.g. for a `/command`), skill-specific tools (`metadata.include_tools`), and per-subagent skills.
- Make skills read-only with a [permission](#13-permissions) rule, as this project does.

[Docs](https://docs.langchain.com/oss/python/deepagents/skills)

## 10. Planning (to-dos)

`write_todos` gives the agent a visible to-do list (`pending` → `in_progress` → `completed`). **Since v0.7 it's opt-in:**

```python
from langchain.agents.middleware import TodoListMiddleware
agent = create_deep_agent(..., middleware=[TodoListMiddleware()])
```

This project adds it, so the "Plan" step in `AGENTS.md` works. [Docs](https://docs.langchain.com/oss/python/deepagents/overview#task-planning)

## 11. Subagents

The agent hands focused jobs to subagents with the `task` tool. Each subagent works in its own context and returns one final answer, which keeps the main conversation clean.

```python
fact_checker = {
    "name": "fact-checker",
    "description": "Checks a draft report's claims against the web.",
    "system_prompt": "You are a meticulous fact-checker...",
    "tools": [tavily_search],
    "model": "openai:gpt-6-luna",          # optional, defaults to the main model
}
agent = create_deep_agent(..., subagents=[fact_checker])
```

- A **`general-purpose`** subagent with the same tools is always added. This project uses only that one.
- Optional keys: `model`, `middleware`, `interrupt_on`, `skills`, `response_format`, `permissions`, `mode`.
- **Fork mode** (`"mode": "fork"`): the subagent starts with the parent's conversation history.
- **`CompiledSubAgent`:** use any LangGraph graph as a subagent.
- **Async subagents:** background jobs on another deployment that the agent can start, check, update, and cancel while it keeps talking to you.
- **Dynamic subagents:** with the code interpreter, the agent can fan out many subagents from code.

[Docs](https://docs.langchain.com/oss/python/deepagents/subagents)

## 12. Human-in-the-loop

Pause before chosen tools so a person can approve, edit, or reject the call:

```python
agent = create_deep_agent(
    tools=[send_email],
    interrupt_on={"send_email": {"allowed_decisions": ["approve", "reject"]}},
    checkpointer=MemorySaver(),    # required locally; LangSmith provides one when deployed
)
```

Resume with `agent.invoke(Command(resume={"decisions": [{"type": "approve"}]}), config=config)`, using the same `thread_id`. You can also interrupt only matching calls with a `"when"` predicate. [Docs](https://docs.langchain.com/oss/python/deepagents/human-in-the-loop)

## 13. Permissions

Allow, deny, or require approval for file paths:

```python
from deepagents import FilesystemPermission

permissions=[FilesystemPermission(operations=["write"], paths=["/skills/**"], mode="deny")]  # this project
```

- `operations`: `"read"` and/or `"write"`. `mode`: `"allow"`, `"deny"`, or `"interrupt"` (ask a human).
- **The first matching rule wins.** If no rule matches, the action is allowed, so put specific rules first.
- Permissions cover only the built-in file tools: not your own tools, MCP tools, or sandbox shell commands.

[Docs](https://docs.langchain.com/oss/python/deepagents/permissions)

## 14. Sandboxes

Give the agent an isolated machine with a shell (`execute`) for running code:

```python
from deepagents.backends import LangSmithSandbox
from langsmith.sandbox import SandboxClient

client = SandboxClient()
sandbox = client.create_sandbox()
agent = create_deep_agent(model=model, backend=LangSmithSandbox(sandbox=sandbox))
# ... later: client.delete_sandbox(sandbox.name)
```

- **Providers:** LangSmith, AWS AgentCore, Daytona, E2B, Modal, NVIDIA OpenShell, Runloop, and Vercel.
- You create, reuse, and clean up sandboxes yourself, usually one per conversation.
- Never put secrets inside a sandbox: use an auth proxy, or keep secret-using tools outside it.

[Docs](https://docs.langchain.com/oss/python/deepagents/sandboxes)

## 15. Code interpreter

`CodeInterpreterMiddleware` adds an `eval` tool that runs JavaScript in a locked-down in-memory runtime. It's good for loops, data transforms, and calling tools from code. It has no filesystem, network, or shell.

```python
from langchain_quickjs import CodeInterpreterMiddleware    # pip install "deepagents[quickjs]"
agent = create_deep_agent(..., middleware=[CodeInterpreterMiddleware()])
```

[Docs](https://docs.langchain.com/oss/python/deepagents/interpreters)

## 16. Middleware

Middleware hooks run around model and tool calls. This project logs every tool call:

```python
class LogToolCalls(AgentMiddleware):
    def wrap_tool_call(self, request, handler): ...          # sync
    async def awrap_tool_call(self, request, handler): ...   # async (used by langgraph dev / LangSmith)
```

- LangChain's prebuilt middleware works too: `PIIMiddleware`, `ModelCallLimitMiddleware`, `ModelRetryMiddleware`, `ModelFallbackMiddleware`, and more.
- Replace a built-in by passing one with the same name, e.g. your own `SummarizationMiddleware(...)` with different thresholds.

[Docs](https://docs.langchain.com/oss/python/deepagents/customization#middleware)

## 17. Context management (automatic)

These keep long runs from overflowing the model's context, with no setup:

- **Offloading:** tool results over ~20,000 tokens are saved to a file and replaced with a path and a short preview.
- **Summarization:** at about 85% of the context window, older messages are summarized. The full history is saved to `/conversation_history/`.
- **Prompt caching:** automatic for Anthropic and Bedrock models.
- **Subagents** isolate heavy work from the main conversation.
- **On demand:** `create_summarization_tool_middleware(...)` lets the agent compact its own conversation.

[Docs](https://docs.langchain.com/oss/python/deepagents/context-engineering)

## 18. Structured output

```python
class Report(BaseModel):
    title: str
    sources: list[str]

agent = create_deep_agent(..., response_format=Report)
agent.invoke(...)["structured_response"]
```

[Docs](https://docs.langchain.com/oss/python/deepagents/customization#structured-output)

## 19. Streaming

- **Classic:** `agent.stream(..., stream_mode="updates" | "messages" | "custom", subgraphs=True)` streams progress, tokens, and your own events (sent with `get_stream_writer()`).
- **Event streaming (recommended):** `agent.stream_events(input, version="v3")` gives typed streams, including `stream.subagents` with one handle per delegated task (name, status, messages, tool calls, output).

LangGraph Studio uses streaming to show the agent working step by step. [Docs](https://docs.langchain.com/oss/python/deepagents/streaming) · [Event streaming](https://docs.langchain.com/oss/python/deepagents/event-streaming)

## 20. Fault tolerance

Add LangChain middleware for production resilience:

```python
from langchain.agents.middleware import ModelRetryMiddleware, ModelFallbackMiddleware, ToolRetryMiddleware

middleware=[
    ModelRetryMiddleware(max_retries=3),
    ModelFallbackMiddleware("anthropic:claude-sonnet-4-6"),
    ToolRetryMiddleware(max_retries=2, tools=["tavily_search"]),
]
```

Also available: `ToolErrorMiddleware` (send tool errors back to the model instead of crashing), `ModelCallLimitMiddleware` / `ToolCallLimitMiddleware` (cost caps), and rate limiters. [Docs](https://docs.langchain.com/oss/python/deepagents/fault-tolerance)

## 21. Multimodal

Send images (and audio, video, PDFs) as content blocks, and tools can return them too:

```python
{"role": "user", "content": [{"type": "text", "text": "What's in this chart?"},
                             {"type": "image", "url": "https://example.com/chart.png"}]}
```

`read_file` returns media files as content the model can see. The model has to support the media type. [Docs](https://docs.langchain.com/oss/python/deepagents/multimodal)

## 22. Harness and provider profiles

Tune the harness for a specific model or provider, applied automatically whenever that model is used:

```python
from deepagents import HarnessProfile, register_harness_profile

register_harness_profile("openai:gpt-6-luna", HarnessProfile(system_prompt_suffix="Be concise."))
```

`HarnessProfile` can also hide tools or middleware and disable the general-purpose subagent. `ProviderProfile` sets default model settings, such as temperature. Register profiles before creating the agent. [Docs](https://docs.langchain.com/oss/python/deepagents/profiles)

## 23. Deploying

This project ships with a `langgraph.json`, so it runs on LangGraph's server:

```json
{ "dependencies": ["."], "graphs": { "research_agent": "./agent.py:agent" }, "env": ".env" }
```

| Option | How |
|---|---|
| Local dev + Studio | `uv run langgraph dev` |
| LangSmith Deployment | Deploy from GitHub (see the README). You get threads, persistence, auth, cron, an API, MCP, and A2A. |
| Managed Deep Agents | The hosted runtime from [Part 2](../../2-managed-deep-agent/) |
| Self-host | `langgraph build` produces a Docker image |

**Production checklist from the docs:**
- Pass a `thread_id` on every call.
- Scope memory per user.
- Write async tools.
- Don't deploy `FilesystemBackend` or `LocalShellBackend` with broad access.
- Add fault-tolerance middleware and guardrails (permissions, PII redaction).

[Docs](https://docs.langchain.com/oss/python/deepagents/going-to-production)

## 24. Frontends and protocols

- **React/Vue/Svelte/Angular:** `useStream` from `@langchain/react` (and siblings) shows messages, subagent cards, to-do lists, and interrupts. [Docs](https://docs.langchain.com/oss/python/deepagents/frontend/overview)
- **ACP:** run the agent inside editors like Zed, JetBrains, VS Code, and Neovim (`deepagents-acp`). [Docs](https://docs.langchain.com/oss/python/deepagents/acp)
- **AG-UI:** connect to AG-UI frontends such as CopilotKit. [Docs](https://docs.langchain.com/oss/python/deepagents/ag-ui)
- **A2A:** deployed agents expose an Agent2Agent endpoint at `/a2a/{assistant_id}`. [Docs](https://docs.langchain.com/langsmith/server-a2a)

---

## Learn more

- [Deep Agents overview](https://docs.langchain.com/oss/python/deepagents/overview) · [Quickstart](https://docs.langchain.com/oss/python/deepagents/quickstart)
- [Deep research example](https://docs.langchain.com/oss/python/deepagents/deep-research)
- [Deep Agents vs. Claude Agent SDK](https://docs.langchain.com/oss/python/deepagents/comparison)
- Want hosting, a sandbox, Slack, and cron without running them? See [Part 2: Managed Deep Agents](../../2-managed-deep-agent/) and its [comparison doc](../../2-managed-deep-agent/docs/MDA_VS_DEEP_AGENTS.md).
