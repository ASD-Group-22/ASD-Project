"""Shared Release 1 RAG server.

Provides the local HTTP interface for shared RAG operations.

The final server is expected to coordinate operations such as:
- health/status checking
- corpus refresh/indexing
- retrieval
- grounded answer generation

Feature-specific trusted data is provided through the modules under sources/.
"""

from mcp.server.fastmcp import FastMCP

from rag_pipeline import (
    answer_question as answer_question_impl,
    refresh_corpus as refresh_corpus_impl,
    retrieve_context as retrieve_context_impl
)


mcp = FastMCP(
    "Shared Enterprise RAG MCP"
)


AVAILABLE_TOOLS = [
    "refresh_corpus",
    "retrieve_context",
    "answer_question"
]


@mcp.tool()
def refresh_corpus(
    caller: str = "student"
):

    return refresh_corpus_impl(
        caller=caller
    )


@mcp.tool()
def retrieve_context(
    query: str,
    k: int = 5,
    caller: str = "student"
):

    return retrieve_context_impl(
        query=query,
        k=k,
        caller=caller
    )


@mcp.tool()
def answer_question(
    query: str,
    k: int = 5,
    caller: str = "student"
):

    return answer_question_impl(
        query=query,
        k=k,
        caller=caller
    )


if __name__ == "__main__":

    print(
        "Starting Shared Enterprise RAG MCP Server..."
    )

    print(
        "Server status: RUNNING"
    )

    print(
        "Available tools:"
    )

    for tool in AVAILABLE_TOOLS:

        print(
            f"- {tool}"
        )

    mcp.run()