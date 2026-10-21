from langchain.tools import tool
from tavily import TavilyClient

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
