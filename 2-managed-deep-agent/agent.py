from managed_deepagents import define_deep_agent

from middleware.audit import log_tool_calls
from tools.search import tavily_search

fact_checker = {
    "name": "fact-checker",
    "description": "Checks a draft report's claims against the web before it is finalized.",
    "system_prompt": (
        "You are a meticulous fact-checker. Verify each factual claim in the draft with "
        "tavily_search. Reply with a short list of claims that are unsupported or wrong, "
        "with the correction and a source URL. If every claim checks out, say so."
    ),
    "tools": [tavily_search],
}

agent = define_deep_agent(
    name="research-agent",
    model="openai:gpt-6-luna",
    tools=[tavily_search],
    middleware=[log_tool_calls],
    subagents=[fact_checker],
)
