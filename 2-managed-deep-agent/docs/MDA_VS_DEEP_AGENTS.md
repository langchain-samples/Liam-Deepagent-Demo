# What Managed Deep Agents Adds on Top of Deep Agents

Both parts of this workshop run the **same agent harness**: the open-source [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) loop with planning, filesystem tools, subagents, and skills. Your tools, middleware, and subagents work the same way in both.

The difference is everything *around* the agent. With Deep Agents (Part 1), you build and run that layer yourself. With Managed Deep Agents (Part 2), each piece is a small file, and LangSmith runs it.

> In one line: **Deep Agents gives you the agent. Managed Deep Agents gives you the agent plus the production infrastructure around it.**

---

## At a glance

| You need… | Deep Agents (Part 1) | Managed Deep Agents (Part 2) |
|---|---|---|
| **Hosting** | Run it yourself, or write `langgraph.json` and deploy from GitHub | `uv run mda deploy` |
| **A filesystem + shell for the agent** | Pick a sandbox provider, provision it, and wire it in as a backend | `sandbox/__init__.py`, plus `setup.sh` to customize the image |
| **Memory across conversations** | Set up a store and route `/memories/` to a `StoreBackend` | `memory.py`: shared agent memory **and** private per-user memory |
| **Editing the prompt without redeploying** | Change code, redeploy | Edit `instructions.md` or skills live in Context Hub |
| **Per-user private conversations** | Write custom auth and resource-ownership rules | `identity.py`: API key, Supabase, or your own backend |
| **Third-party logins (OAuth) for each user** | Build the OAuth flow, token storage, and refresh yourself | `mda connections create`: MDA runs the whole flow |
| **Slack** | Build a Slack app, webhook handler, and reply logic | `channels/slack.py`: `mda deploy` creates the Slack app |
| **Other webhooks** | Write a server route | `channels/<name>.py` with `channels.http(...)` |
| **Cron jobs** | Run your own scheduler | `schedules/<name>.py`, plus runtime schedules the agent can create |
| **Remote MCP tools with auth** | Wire up an MCP client and manage credentials | `tools/mcp.py` + connections |
| **Web search without a search API key** | Bring your own (e.g. Tavily) | Built-in Parallel search MCP server (Plus/Startup plans) |
| **Evals** | Set up your own harness | `mda evals init -i` scaffolds Harbor evals for your coding agent |

---

## Baked in with MDA

### 1. One-command deploys
`mda deploy` compiles the project, uploads it, builds it, and runs it on LangSmith Agent Server. There's no `langgraph.json`, GitHub connection, or environment-variable form to fill in: your `.env` keys become deployment secrets automatically. `mda logs` streams logs, and `mda delete` tears everything down.

### 2. A managed sandbox
Each conversation gets its own isolated Linux machine, which LangSmith creates, snapshots, reuses, and deletes when idle.
- `setup.sh` runs once per deploy and is snapshotted, so every conversation starts with your tools preinstalled.
- An auth proxy injects API keys into outbound requests, so code running in the sandbox never sees the secrets.
- Your own tools can read and write the sandbox's files through `runtime.backend`.

In Deep Agents, sandboxes are a backend you choose, provision, and manage.

### 3. Two kinds of durable memory
- **Agent memory** (`/memories/agent/`): shared by everyone who uses the deployment.
- **User memory** (`/memories/user/`): private to each signed-in person. It turns on by default only in private conversations (Studio, Slack DMs), and you can set your own access policy.

Memory lives in Context Hub, survives every redeploy, and can be browsed in the LangSmith UI. In Deep Agents you wire up the store and namespaces yourself, and per-user separation is your code.

### 4. Live-editable instructions and skills (Context Hub)
`instructions.md` and `skills/` sync to Context Hub on deploy. Anyone with access can edit them in the LangSmith UI, and the next run picks up the change without a redeploy. If the UI copy and your repo copy diverge, `mda deploy` asks which version to keep.

### 5. Identity and private threads
`identity.py` decides who can call the deployment:
- a LangSmith API key (the default),
- Supabase sign-in, or
- your own backend.

With Supabase or backend identity, each end user gets private threads automatically. Tools and middleware receive the *verified* caller (`runtime.server_info.principal`), kept separate from untrusted request data.

### 6. Connections: credentials and OAuth handled for you
Store API keys and OAuth logins in your LangSmith workspace, then fetch them in code with `connections.get(...)`.
- **User-owned connections:** each person signs in to their *own* GitHub, Notion, Google, and so on. When someone hasn't connected yet, MDA pauses the run and shows a connect prompt (built into Slack and Studio), then resumes.
- No callback routes, token storage, or refresh logic to write.
- Rotate a key without redeploying.

### 7. Slack out of the box
Add `channels/slack.py` and deploy. MDA creates the Slack app, verifies incoming events, maps each Slack thread to its own conversation and sandbox, and posts replies. Out of the box you also get:
- approval buttons for human-in-the-loop,
- file uploads and downloads (with a sandbox),
- emoji reactions,
- Slack users resolved to real people, so user memory and per-user logins just work.

### 8. Generic webhooks
`channels.http(verify=..., parse=..., post=...)` turns any service that can send a signed webhook into a way to start runs, without writing a web server.

### 9. Schedules
- **Declared:** a file in `schedules/` becomes a LangSmith cron job when you deploy, and removing the file removes the job. Results can be delivered to Slack.
- **Runtime:** tools can let the agent create, list, pause, and cancel schedules from a conversation ("remind me every Friday…").

### 10. Extras on the runtime
Tools and middleware get three things a plain Deep Agent doesn't:
- **`server_info`**: the verified caller,
- **`channel`**: which Slack (or webhook) conversation started the run, and a way to post back,
- **`backend`**: the conversation's sandbox.

---

## Shared by both when you deploy on LangSmith

Some infrastructure comes from **LangSmith Agent Server** itself, so Part 1 gets it too when you deploy it with LangSmith Deployments:

- Threads, runs, streaming, and the Agent Server API
- Persistence (checkpointer and store) backed by managed Postgres
- Human-in-the-loop pause and resume
- Tracing in LangSmith
- An MCP endpoint at `/mcp`, so other agents can call yours as a tool
- LangSmith Studio

The difference: MDA sets all of this up for you with no `langgraph.json` or deployment form, and adds sections 1–10 above.

---

## What you give up with MDA

MDA hosts *the agent*, not an arbitrary application. Stay on Deep Agents (Part 1) when you need:

| Need | Why MDA doesn't fit |
|---|---|
| A custom backend (your own `BackendProtocol`) | The runtime owns the backend. The managed sandbox is the only filesystem option. |
| Your own store or checkpointer | Persistence comes from Agent Server |
| A custom state schema (`state_schema`) | Not supported in Python (`defineDeepAgent` in TypeScript does accept `stateSchema`) |
| Custom API routes or app code around the agent | Use a regular LangSmith deployment instead |
| Self-hosting, or running outside LangSmith Cloud | MDA is LangSmith Cloud only (public beta) |
| Synchronous middleware | MDA always runs the agent async, so middleware must use async hooks |
| Filesystem permission rules alongside a sandbox | Declaring a sandbox clears `permissions=` |

A common path: build on Deep Agents first, then move to MDA when you want the production layer without running it. The [migration guide](https://docs.langchain.com/langsmith/python/managed-deep-agents-migrate) covers the steps, and the [Part 1 → Part 2 mapping table](../README.md#how-part-1-maps-to-part-2) shows them on this agent.

## Learn more

- [Relationship to Deep Agents](https://docs.langchain.com/langsmith/python/managed-deep-agents-overview#relationship-to-deep-agents)
- [Move from Deep Agents](https://docs.langchain.com/langsmith/python/managed-deep-agents-migrate)
- [MDA feature guide](MDA_FEATURE_GUIDE.md)
