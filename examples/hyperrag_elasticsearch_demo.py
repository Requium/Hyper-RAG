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

from tenacity import (
    RetryError,
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

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

try:  # pragma: no cover - import is optional depending on the provider used
    from openai import RateLimitError
except Exception:  # pragma: no cover - fall back to a generic sentinel exception
    class RateLimitError(Exception):
        """Placeholder when the OpenAI client is unavailable."""


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
    if api_key:
        if api_key_id:
            kwargs["api_key"] = (api_key_id, api_key)
        else:
            # ElasticSearch also accepts a single base64 API key string.
            kwargs["api_key"] = api_key
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
    parser.add_argument(
        "--api-key",
        help="ElasticSearch API key secret (or full base64 value if no ID is provided)",
    )
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
    parser.add_argument(
        "--llm-max-async",
        type=int,
        default=4,
        help=(
            "Maximum number of concurrent LLM calls. Lower this if you encounter "
            "provider rate limits."
        ),
    )
    parser.add_argument(
        "--embedding-max-async",
        type=int,
        default=4,
        help=(
            "Maximum number of concurrent embedding calls. Lower this if you encounter "
            "provider rate limits."
        ),
    )
    parser.add_argument(
        "--ingest-retries",
        type=int,
        default=5,
        help=(
            "Number of exponential-backoff retries to perform when the provider "
            "returns rate-limit errors during ingestion."
        ),
    )
    parser.add_argument(
        "--preview-only",
        action="store_true",
        help=(
            "Skip LLM extraction and hypergraph writes; instead dump the entity "
            "extraction prompts to caches/<data_name>/entity_extraction_prompts.jsonl "
            "for inspection."
        ),
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.llm_max_async < 1:
        parser.error("--llm-max-async must be a positive integer")
    if args.embedding_max_async < 1:
        parser.error("--embedding-max-async must be a positive integer")
    if args.ingest_retries < 1:
        parser.error("--ingest-retries must be a positive integer")

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
        llm_model_max_async=args.llm_max_async,
        embedding_func=EmbeddingFunc(
            embedding_dim=EMB_DIM,
            max_token_size=8192,
            func=embedding_func,
        ),
        embedding_func_max_async=args.embedding_max_async,
    )

    def _is_rate_limit_retryable(exc: BaseException) -> bool:
        if isinstance(exc, RateLimitError):
            return True
        if isinstance(exc, RetryError):
            last_exc = exc.last_attempt.exception() if exc.last_attempt else None
            return isinstance(last_exc, RateLimitError)
        return False

    @retry(
        reraise=True,
        retry=retry_if_exception(_is_rate_limit_retryable),
        stop=stop_after_attempt(args.ingest_retries),
        wait=wait_exponential(multiplier=1, min=2, max=60),
    )
    def _insert_with_backoff():
        return rag.insert_elasticsearch_documents(
            documents,
            combine_documents=True,
            preview_only=args.preview_only,
        )

    try:
        insert_result = _insert_with_backoff()
    except RateLimitError as exc:
        raise RuntimeError(
            "The language model provider reported a rate limit while processing the "
            "documents. Try lowering --llm-max-async/--embedding-max-async or wait "
            "before retrying."
        ) from exc
    except RetryError as exc:
        last_exc = exc.last_attempt.exception() if exc.last_attempt else exc
        if isinstance(last_exc, RateLimitError):
            raise RuntimeError(
                "The language model provider reported a rate limit while processing the "
                "documents. Try lowering --llm-max-async/--embedding-max-async or "
                "wait before retrying."
            ) from last_exc
        raise

    print(
        f"Inserted {len(documents)} ElasticSearch documents from index '{args.index}' into HyperRAG."
    )

    if args.preview_only:
        preview_path = working_dir / "entity_extraction_prompts.jsonl"
        num_prompts = len(insert_result or []) if insert_result else 0
        print(
            "\nPreview-only mode: wrote entity extraction prompts to"
            f" {preview_path.resolve()}"
        )
        print(f"Prompt records generated: {num_prompts}")
        print("Skipping hypergraph ingestion and querying to avoid LLM costs.")
        return

    response = rag.query(
        args.question,
        param=QueryParam(mode=args.mode),
    )
    print("\nHyperRAG response:\n")
    print(response)


if __name__ == "__main__":
    main()
