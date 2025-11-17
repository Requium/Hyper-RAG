import asyncio
import html
import io
import csv
import json
import logging
import os
import re
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from functools import wraps
from hashlib import md5
from typing import Any, Protocol, Union, List
import xml.etree.ElementTree as ET

import numpy as np

logger = logging.getLogger("hyper_rag")


class Tokenizer(Protocol):
    """Protocol describing the minimal tokenizer surface used by HyperRAG."""

    def encode(self, text: str) -> list[str]:
        """Split *text* into tokens."""

    def decode(self, tokens: list[str]) -> str:
        """Reconstruct a string from the provided tokens."""


class RegexTokenizer:
    """A lightweight regex-based tokenizer compatible with generic LLMs.

    The tokenizer preserves whitespace tokens to keep round-trip encode/decode
    behaviour stable without depending on vendor-specific libraries such as
    tiktoken.
    """

    _pattern = re.compile(r"\s+|\S+")

    def encode(self, text: str) -> list[str]:
        if not text:
            return []
        return self._pattern.findall(text)

    def decode(self, tokens: list[str]) -> str:
        if not tokens:
            return ""
        return "".join(tokens)


_TOKENIZER: Tokenizer = RegexTokenizer()


def set_tokenizer(tokenizer: Tokenizer):
    """Register a tokenizer implementation for downstream helpers to use."""

    global _TOKENIZER
    _TOKENIZER = tokenizer


def get_tokenizer() -> Tokenizer:
    return _TOKENIZER


def set_logger(log_file: str):
    logger.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(file_handler)


@dataclass
class EmbeddingFunc:
    embedding_dim: int
    max_token_size: int
    func: callable

    async def __call__(self, *args, **kwargs) -> np.ndarray:
        return await self.func(*args, **kwargs)


def locate_json_string_body_from_string(content: str) -> Union[str, None]:
    """Locate the JSON string body from a string"""
    maybe_json_str = re.search(r"{.*}", content, re.DOTALL)
    if maybe_json_str is not None:
        return maybe_json_str.group(0)
    else:
        return None


def convert_response_to_json(response: str) -> dict:
    json_str = locate_json_string_body_from_string(response)
    assert json_str is not None, f"Unable to parse JSON from response: {response}"
    try:
        data = json.loads(json_str)
        return data
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {json_str}")
        raise e from None


def compute_args_hash(*args):
    return md5(str(args).encode()).hexdigest()


def compute_mdhash_id(content, prefix: str = ""):
    return prefix + md5(content.encode()).hexdigest()


def limit_async_func_call(max_size: int, waitting_time: float = 0.0001):
    """Add restriction of maximum async calling times for a async func"""

    def final_decro(func):
        """Not using async.Semaphore to aovid use nest-asyncio"""
        __current_size = 0

        @wraps(func)
        async def wait_func(*args, **kwargs):
            nonlocal __current_size
            while __current_size >= max_size:
                await asyncio.sleep(waitting_time)
            __current_size += 1
            result = await func(*args, **kwargs)
            __current_size -= 1
            return result

        return wait_func

    return final_decro


def wrap_embedding_func_with_attrs(**kwargs):
    """Wrap a function with attributes"""

    def final_decro(func) -> EmbeddingFunc:
        new_func = EmbeddingFunc(**kwargs, func=func)
        return new_func

    return final_decro


def load_json(file_name):
    if not os.path.exists(file_name):
        return None
    with open(file_name, encoding="utf-8") as f:
        return json.load(f)


def write_json(json_obj, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(json_obj, f, indent=2, ensure_ascii=False)


def encode_string_by_tiktoken(content: str, model_name: str = ""):
    """Tokenize *content* using the globally configured tokenizer.

    The argument ``model_name`` is preserved for backwards compatibility with
    previous tiktoken-based signatures; it is ignored by the default
    implementation.
    """

    return get_tokenizer().encode(content)


def decode_tokens_by_tiktoken(tokens: list[str], model_name: str = ""):
    """Reconstruct text from the provided tokens using the global tokenizer."""

    return get_tokenizer().decode(tokens)


def pack_user_ass_to_openai_messages(*args: str):
    roles = ["user", "assistant"]
    return [
        {"role": roles[i % 2], "content": content} for i, content in enumerate(args) #if content is not None
    ]


def split_string_by_multi_markers(content: str, markers: list[str]) -> list[str]:
    """Split a string by multiple markers"""
    if not markers:
        return [content]
    results = re.split("|".join(re.escape(marker) for marker in markers), content)
    return [r.strip() for r in results if r.strip()]


# Refer the utils functions of the official GraphRAG implementation:
# https://github.com/microsoft/graphrag
def clean_str(input: Any) -> str:
    """Clean an input string by removing HTML escapes, control characters, and other unwanted characters."""
    # If we get non-string input, just give it back
    if not isinstance(input, str):
        return input

    result = html.unescape(input.strip())
    # https://stackoverflow.com/questions/4324790/removing-control-characters-from-a-string-in-python
    return re.sub(r"[\x00-\x1f\x7f-\x9f]", "", result)


def is_float_regex(value):
    return bool(re.match(r"^[-+]?[0-9]*\.?[0-9]+$", value))


def truncate_list_by_token_size(list_data: list, key: callable, max_token_size: int):
    """Truncate a list of data by token size"""
    if max_token_size <= 0:
        return []
    tokens = 0
    for i, data in enumerate(list_data):
        tokens += len(encode_string_by_tiktoken(key(data)))
        if tokens > max_token_size:
            return list_data[:i]
    return list_data


def list_of_list_to_csv(data: List[List[str]]) -> str:
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerows(data)
    return output.getvalue()


def csv_string_to_list(csv_string: str) -> List[List[str]]:
    output = io.StringIO(csv_string)
    reader = csv.reader(output)
    return [row for row in reader]


def save_data_to_file(data, file_name):
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


def xml_to_json(xml_file):
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()

        # Print the root element's tag and attributes to confirm the file has been correctly loaded
        print(f"Root element: {root.tag}")
        print(f"Root attributes: {root.attrib}")

        data = {"nodes": [], "edges": []}

        # Use namespace
        namespace = {"": "http://graphml.graphdrawing.org/xmlns"}

        for node in root.findall(".//node", namespace):
            node_data = {
                "id": node.get("id").strip('"'),
                "entity_type": node.find("./data[@key='d0']", namespace).text.strip('"')
                if node.find("./data[@key='d0']", namespace) is not None
                else "",
                "description": node.find("./data[@key='d1']", namespace).text
                if node.find("./data[@key='d1']", namespace) is not None
                else "",
                "source_id": node.find("./data[@key='d2']", namespace).text
                if node.find("./data[@key='d2']", namespace) is not None
                else "",
            }
            data["nodes"].append(node_data)

        for edge in root.findall(".//edge", namespace):
            edge_data = {
                "source": edge.get("source").strip('"'),
                "target": edge.get("target").strip('"'),
                "weight": float(edge.find("./data[@key='d3']", namespace).text)
                if edge.find("./data[@key='d3']", namespace) is not None
                else 0.0,
                "description": edge.find("./data[@key='d4']", namespace).text
                if edge.find("./data[@key='d4']", namespace) is not None
                else "",
                "keywords": edge.find("./data[@key='d5']", namespace).text
                if edge.find("./data[@key='d5']", namespace) is not None
                else "",
                "source_id": edge.find("./data[@key='d6']", namespace).text
                if edge.find("./data[@key='d6']", namespace) is not None
                else "",
            }
            data["edges"].append(edge_data)

        # Print the number of nodes and edges found
        print(f"Found {len(data['nodes'])} nodes and {len(data['edges'])} edges")

        return data
    except ET.ParseError as e:
        print(f"Error parsing XML file: {e}")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None


def process_combine_contexts(hl, ll):
    header = None
    list_hl = csv_string_to_list(hl.strip())
    list_ll = csv_string_to_list(ll.strip())

    if list_hl:
        header = list_hl[0]
        list_hl = list_hl[1:]
    if list_ll:
        header = list_ll[0]
        list_ll = list_ll[1:]
    if header is None:
        return ""

    if list_hl:
        list_hl = [",".join(item[1:]) for item in list_hl if item]
    if list_ll:
        list_ll = [",".join(item[1:]) for item in list_ll if item]

    combined_sources_set = set(filter(None, list_hl + list_ll))

    combined_sources = [",\t".join(header)]

    for i, item in enumerate(combined_sources_set, start=1):
        combined_sources.append(f"{i},\t{item}")

    combined_sources = "\n".join(combined_sources)

    return combined_sources


def always_get_an_event_loop() -> asyncio.AbstractEventLoop:
    """
    Ensure that there is always an event loop available.

    This function tries to get the current event loop. If the current event loop is closed or does not exist,
    it creates a new event loop and sets it as the current event loop.

    Returns:
        asyncio.AbstractEventLoop: The current or newly created event loop.
    """
    try:
        # Try to get the current event loop
        current_loop = asyncio.get_event_loop()
        if current_loop.is_closed():
            raise RuntimeError("Event loop is closed.")
        return current_loop

    except RuntimeError:
        # If no event loop exists or it is closed, create a new one
        logger.info("Creating a new event loop in main thread.")
        new_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(new_loop)
        return new_loop

def deduplicate_by_key(data_list, key_string):
    unique_data = []
    seen_keys = set()

    def make_hashable(value):
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, list):
            try:
                return tuple(sorted(make_hashable(v) for v in value))
            except TypeError:
                return json.dumps(value, ensure_ascii=False, sort_keys=True)
        if isinstance(value, dict):
            return tuple(sorted((k, make_hashable(v)) for k, v in value.items()))
        return str(value)

    for item in data_list:
        raw_key = item.get(key_string)
        if raw_key is None:
            continue
        key = make_hashable(raw_key)
        if key not in seen_keys:
            seen_keys.add(key)
            unique_data.append(item)
    return unique_data


def _normalize_string_sequence(value: Any, delimiter: str = " > ") -> str:
    """Normalize values that may be strings, lists, or tuples into a string."""

    if value is None:
        return ""
    if isinstance(value, str):
        return value.strip()
    if isinstance(value, (list, tuple)):
        cleaned_parts = [str(v).strip() for v in value if str(v).strip()]
        return delimiter.join(cleaned_parts)
    return str(value).strip()


def format_elasticsearch_document(
    document: Mapping[str, Any],
    *,
    metadata_fields: Sequence[str] | None = None,
    main_content_key: str = "main_content",
    title_keys: Sequence[str] = ("title", "titles"),
    breadcrumbs_key: str = "breadcrumbs",
) -> str:
    """Create a structured text payload from an ElasticSearch ES|QL document.

    Parameters
    ----------
    document:
        Source payload retrieved from ElasticSearch.
    metadata_fields:
        Optional subset of keys to surface as additional metadata rows. When not
        provided, all non-empty scalar fields (excluding title/breadcrumb/main
        content keys) are appended automatically.
    main_content_key:
        Key name containing the full article text such as tutorials or guides.
    title_keys:
        Ordered collection of candidate keys that may represent the document
        title.
    breadcrumbs_key:
        Key holding hierarchical navigation data.

    Returns
    -------
    str
        Human-readable text that emits a JSON metadata header (title,
        breadcrumbs, url_path, and any requested fields) followed by the raw
        main content so HyperRAG can ingest the document with minimal
        preprocessing.
    """

    if main_content_key not in document or not str(document[main_content_key]).strip():
        raise ValueError(
            f"ElasticSearch document must include non-empty '{main_content_key}' content."
        )

    main_content = str(document[main_content_key]).strip()
    title_value = next(
        (
            _normalize_string_sequence(document[key])
            for key in title_keys
            if key in document and _normalize_string_sequence(document[key])
        ),
        "",
    )
    breadcrumbs_value = _normalize_string_sequence(document.get(breadcrumbs_key))
    url_path_value = _normalize_string_sequence(document.get("url_path"))

    metadata_obj: dict[str, Any] = {}
    if title_value:
        metadata_obj["title"] = title_value
    if breadcrumbs_value:
        metadata_obj["breadcrumbs"] = breadcrumbs_value
    if url_path_value:
        metadata_obj["url_path"] = url_path_value

    candidate_metadata = metadata_fields
    if candidate_metadata is None:
        excluded_keys = set(title_keys) | {main_content_key, breadcrumbs_key, "url_path"}
        candidate_metadata = [
            key
            for key in document.keys()
            if key not in excluded_keys
        ]

    for key in candidate_metadata:
        if key not in document:
            continue
        value = _normalize_string_sequence(document[key], delimiter=", ")
        if not value:
            continue
        metadata_obj.setdefault("metadata", {})[key] = value

    sections: list[str] = []
    if metadata_obj:
        compact_metadata = json.dumps(metadata_obj, ensure_ascii=False, indent=2)
        sections.append(f"Document Metadata (JSON):\n{compact_metadata}")

    sections.append(f"main_content:\n{main_content}")

    return "\n\n".join(sections)
