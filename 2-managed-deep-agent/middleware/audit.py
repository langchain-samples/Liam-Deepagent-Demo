import logging
from collections.abc import Awaitable, Callable

from langchain.agents.middleware import wrap_tool_call
from langchain.messages import ToolMessage
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command

logger = logging.getLogger(__name__)


@wrap_tool_call
async def log_tool_calls(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command]],
) -> ToolMessage | Command:
    tool_name = request.tool_call["name"]
    # Omit arguments from logs; they can contain user data.
    logger.info("[Tool Call] %s", tool_name)
    result = await handler(request)
    logger.info("[Tool Done] %s", tool_name)
    return result
