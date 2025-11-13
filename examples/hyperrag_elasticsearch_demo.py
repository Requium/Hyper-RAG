"""Demonstration entry point that ingests ElasticSearch documents into HyperRAG.

The script retrieves ``main_content``, ``breadcrumbs``, and title metadata from a
specified ElasticSearch index before inserting the formatted documents via
``HyperRAG.insert_elasticsearch_documents``.  It mirrors the configuration model
used by ``examples/hyperrag_demo.py`` so existing ``my_config`` settings can be
reused without modification.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import numpy as np

try:  # pragma: no cover - optional dependency for the example entry point
    from elasticsearch import Elasticsearch
except Exception as exc:  # pragma: no cover - defer the import error to runtime
    raise ImportError(
        "The 'elasticsearch' package is required to run the ElasticSearch demo"
    ) from exc

from hyperrag import HyperRAG, QueryParam
from hyperrag.utils import EmbeddingFunc
from hyperrag.llm import openai_embedding, openai_complete_if_cache

from my_config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL
from my_config import EMB_API_KEY, EMB_BASE_URL, EMB_MODEL, EMB_DIM


def build_es_client(args: argparse.Namespace) -> Elasticsearch:
    """Create an ElasticSearch client using CLI arguments or environment data."""

    url = args.elasticsearch_url or os.environ.get("ELASTICSEARCH_URL")
    if not url:
        raise ValueError(
            "ElasticSearch URL must be provided via --elasticsearch-url or ELASTICSEARCH_URL"
        )

    kwargs: dict[str, Any] = {"hosts": [url], "verify_certs": not args.skip_tls_verify}

    api_key = args.api_key or os.environ.get("ELASTICSEARCH_API_KEY")
    api_key_id = args.api_key_id or os.environ.get("ELASTICSEARCH_API_KEY_ID")
    if api_key and api_key_id:
        kwargs["api_key"] = (api_key_id, api_key)
    else:
        username = args.username or os.environ.get("ELASTICSEARCH_USERNAME")
        password = args.password or os.environ.get("ELASTICSEARCH_PASSWORD")
        if username and password:
            kwargs["basic_auth"] = (username, password)

    return Elasticsearch(**kwargs)


def fetch_elasticsearch_documents(
    client: Elasticsearch,
    *,
    index: str,
    limit: int,
    keyword: str | None,
    source_fields: Sequence[str],
) -> list[Mapping[str, Any]]:
    """Search ElasticSearch and return source documents with desired fields."""

    query: Mapping[str, Any]
    if keyword:
        query = {
            "simple_query_string": {
                "query": keyword,
                "fields": [
                    "main_content^3",
                    "title^2",
                    "titles^2",
                    "breadcrumbs",
                ],
                "default_operator": "and",
            }
        }
    else:
        query = {"match_all": {}}

    response = client.search(
        index=index,
        size=limit,
        query=query,
        _source=source_fields,
    )

    hits = response.get("hits", {}).get("hits", [])
    return [hit.get("_source", {}) for hit in hits]


async def llm_model_func(
    prompt: str,
    system_prompt: str | None = None,
    history_messages: Sequence[Mapping[str, str]] | None = None,
    **kwargs: Any,
) -> str:
    history = history_messages or []
    return await openai_complete_if_cache(
        LLM_MODEL,
        prompt,
        system_prompt=system_prompt,
        history_messages=history,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        **kwargs,
    )


async def embedding_func(texts: Iterable[str]) -> np.ndarray:
    return await openai_embedding(
        list(texts),
        model=EMB_MODEL,
        api_key=EMB_API_KEY,
        base_url=EMB_BASE_URL,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Ingest ElasticSearch ES|QL documents and run HyperRAG queries",
    )
    parser.add_argument("index", help="ElasticSearch index name to search")
    parser.add_argument(
        "--keyword",
        help="Optional keyword expression to filter documents (uses simple_query_string)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=20,
        help="Maximum number of documents to retrieve from ElasticSearch",
    )
    parser.add_argument(
        "--elasticsearch-url",
        help="ElasticSearch endpoint URL; defaults to ELASTICSEARCH_URL environment variable",
    )
    parser.add_argument("--username", help="ElasticSearch basic auth username")
    parser.add_argument("--password", help="ElasticSearch basic auth password")
    parser.add_argument("--api-key-id", help="ElasticSearch API key identifier")
    parser.add_argument("--api-key", help="ElasticSearch API key secret")
    parser.add_argument(
        "--skip-tls-verify",
        action="store_true",
        help="Disable certificate verification (useful for self-signed clusters)",
    )
    parser.add_argument(
        "--question",
        default="Summarise the main topics discussed across these ES|QL documents.",
        help="Question to ask once the documents have been ingested",
    )
    parser.add_argument(
        "--mode",
        default="hyper",
        choices=["naive", "hyper", "hyper-lite"],
        help="HyperRAG retrieval mode",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    client = build_es_client(args)
    source_fields = ["main_content", "breadcrumbs", "title", "titles"]

    documents = fetch_elasticsearch_documents(
        client,
        index=args.index,
        limit=args.limit,
        keyword=args.keyword,
        source_fields=source_fields,
    )
    if not documents:
        raise RuntimeError("No ElasticSearch documents found for the provided parameters")

    data_name = f"esql-{args.index}"
    working_dir = Path("caches") / data_name
    working_dir.mkdir(parents=True, exist_ok=True)

    rag = HyperRAG(
        working_dir=working_dir,
        llm_model_func=llm_model_func,
        embedding_func=EmbeddingFunc(
            embedding_dim=EMB_DIM,
            max_token_size=8192,
            func=embedding_func,
        ),
    )

    rag.insert_elasticsearch_documents(documents)

    print(
        f"Inserted {len(documents)} ElasticSearch documents from index '{args.index}' into HyperRAG."
    )

    response = rag.query(
        args.question,
        param=QueryParam(mode=args.mode),
    )
    print("\nHyperRAG response:\n")
    print(response)


if __name__ == "__main__":
    main()
