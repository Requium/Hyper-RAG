"""
Minimal Model Context Protocol (MCP) server that exposes HyperRAG as a tool.

The server reuses an existing HyperRAG cache (working_dir) and never touches
ElasticSearch. Point it to a cache created beforehand (for example the one
produced by ``examples/hyperrag_elasticsearch_demo.py``) and call the
``query_hyperrag`` tool from any MCP-compatible client.

Example launches:
    # Local stdio transport
    python examples/mcp_hyperrag.py --working-dir caches/esql-esql_docs

    # Remote HTTP transport so clients can reach http://<host>:8000/mcp
    python examples/mcp_hyperrag.py --working-dir caches/esql-esql_docs \
        --transport streamable-http --host 0.0.0.0 --port 8000

See `examples/README_mcp_hyperrag.md` for client configuration examples.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Allow importing hyperrag without installing the package globally
REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

import numpy as np

from hyperrag import HyperRAG, QueryParam
from hyperrag.llm import openai_complete_if_cache, openai_embedding
from hyperrag.utils import EmbeddingFunc
from my_config import EMB_API_KEY, EMB_BASE_URL, EMB_DIM, EMB_MODEL, LLM_API_KEY, LLM_BASE_URL, LLM_MODEL

app = FastMCP("hyperrag-mcp")


async def llm_model_func(prompt: str, system_prompt=None, history_messages=None, **kwargs) -> str:
    return await openai_complete_if_cache(
        LLM_MODEL,
        prompt,
        system_prompt=system_prompt,
        history_messages=history_messages or [],
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        **kwargs,
    )


async def embedding_func(texts: list[str]) -> np.ndarray:
    return await openai_embedding(
        texts,
        model=EMB_MODEL,
        api_key=EMB_API_KEY,
        base_url=EMB_BASE_URL,
    )


_rag_cache: dict[Path, HyperRAG] = {}


def load_rag(working_dir: Path) -> HyperRAG:
    working_dir = working_dir.resolve()
    if not working_dir.exists():
        raise FileNotFoundError(
            f"Working directory '{working_dir}' does not exist. "
            "Run an ingestion script first to populate the cache."
        )

    if working_dir not in _rag_cache:
        _rag_cache[working_dir] = HyperRAG(
            working_dir=working_dir,
            llm_model_func=llm_model_func,
            embedding_func=EmbeddingFunc(
                embedding_dim=EMB_DIM,
                max_token_size=8192,
                func=embedding_func,
            ),
        )

    return _rag_cache[working_dir]


@app.tool()
async def query_hyperrag(
    question: str,
    *,
    working_dir: str,
    mode: str = "hyper",
    top_k: int = 60,
    response_type: str = "Multiple Paragraphs",
) -> str:
    """Ask a question against a cached HyperRAG workspace.

    Parameters
    ----------
    question: str
        Natural language question to answer.
    working_dir: str
        Path to an existing HyperRAG cache directory (e.g. caches/esql-esql_docs).
    mode: str
        Retrieval mode supported by HyperRAG (hyper, hyper-lite, graph, naive, llm).
    top_k: int
        Number of items to retrieve for context.
    response_type: str
        Guidance for the LLM response style.
    """

    rag = load_rag(Path(working_dir))
    param = QueryParam(mode=mode, top_k=top_k, response_type=response_type)
    return await rag.aquery(question, param=param)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a HyperRAG MCP server")
    parser.add_argument(
        "--working-dir",
        type=Path,
        required=True,
        help="Existing HyperRAG cache directory (no ingestion is performed)",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default="stdio",
        help="MCP transport to expose. Use streamable-http for remote clients.",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host/IP to bind (only used with streamable-http)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port to bind (only used with streamable-http)",
    )
    parser.add_argument(
        "--http-path",
        default="/mcp",
        help="Base HTTP path for the MCP endpoint when using streamable-http",
    )
    args = parser.parse_args()

    # Pre-load the cache so the first MCP call is fast and errors early if missing
    load_rag(args.working_dir)

    # Update bind settings when running over HTTP
    if args.transport == "streamable-http":
        app.settings.host = args.host
        app.settings.port = args.port
        app.settings.streamable_http_path = args.http_path

    app.run(transport=args.transport)
