"""Deep research agent built with Deep Agents, packaged for LangGraph.

Run locally with `langgraph dev`, or deploy from GitHub with LangSmith Deployments.
The platform supplies the checkpointer and store, so none are configured here.
"""

import logging
from pathlib import Path

from deepagents import FilesystemPermission, create_deep_agent
from deepagents.backends import CompositeBackend, FilesystemBackend, StateBackend, StoreBackend
from langchain.agents.middleware import AgentMiddleware
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from tavily import TavilyClient

logger = logging.getLogger(__name__)

# AGENTS.md and skills live on disk next to this file and are mounted at /config/.
CONFIG_DIR = Path(__file__).parent / "agent_config"

model = ChatOpenAI(model="gpt-5")

tavily_client = TavilyClient()


@tool(parse_docstring=True)
def tavily_search(query: str) -> str:
    """Search the web for information on a given query.

    Args:
        query: Search query to execute
    """
    search_results = tavily_client.search(query, max_results=3, topic="general")

    result_texts = []
    for result in search_results.get("results", []):
        url = result["url"]
        title = result["title"]
        content = result.get("content", "No content available")
        result_text = f"## {title}\n**URL:** {url}\n\n{content}\n\n---\n"
        result_texts.append(result_text)

    return f"Found {len(result_texts)} result(s) for '{query}':\n\n{''.join(result_texts)}"


class LogToolCalls(AgentMiddleware):
    """Log every tool call the agent makes.

    Implements both sync and async hooks: the LangGraph server runs agents async,
    and a sync-only `@wrap_tool_call` raises NotImplementedError there.
    """

    def wrap_tool_call(self, request, handler):
        tool_name = request.tool_call["name"]
        # Omit arguments from logs; they can contain user data.
        logger.info("[Tool Call] %s", tool_name)
        result = handler(request)
        logger.info("[Tool Done] %s", tool_name)
        return result

    async def awrap_tool_call(self, request, handler):
        tool_name = request.tool_call["name"]
        logger.info("[Tool Call] %s", tool_name)
        result = await handler(request)
        logger.info("[Tool Done] %s", tool_name)
        return result


backend = CompositeBackend(
    default=StateBackend(),  # Scratch files like /final_report.md are per-thread
    routes={
        # Persists across threads via the platform-provided store
        "/memories/": StoreBackend(namespace=lambda _rt: ("memories",)),
        # Read-only agent identity + skills, loaded from the repo
        "/config/": FilesystemBackend(root_dir=CONFIG_DIR, virtual_mode=True),
    },
)

agent = create_deep_agent(
    model=model,
    tools=[tavily_search],
    system_prompt="You are an expert research assistant.",
    middleware=[LogToolCalls()],
    skills=["/config/skills/"],  # LinkedIn + Twitter skills loaded on demand
    memory=["/config/AGENTS.md"],  # Identity + workflow from AGENTS.md
    backend=backend,
    # In production the agent must not rewrite its own instructions or the repo files.
    permissions=[FilesystemPermission(operations=["write"], paths=["/config/**"], mode="deny")],
)
