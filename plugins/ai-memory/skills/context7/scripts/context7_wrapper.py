#!/usr/bin/env python3
"""
Context7 Wrapper with Tokenization and Reranking

Wraps context7 MCP calls with:
- Token counting (tiktoken)
- TF-IDF reranking for relevance
- Returns top 5 most relevant chunks

Usage:
    python context7_wrapper.py resolve <library_name>
    python context7_wrapper.py docs <library_id> [--topic <topic>] [--tokens <max_tokens>]
"""

import argparse
import json
import re
import subprocess
import sys
from collections import Counter
from dataclasses import dataclass
from math import log
from typing import Optional


@dataclass
class DocChunk:
    """A chunk of documentation with metadata."""

    content: str
    source: str
    tokens: int
    score: float = 0.0


def count_tokens(text: str) -> int:
    """Count tokens using a simple approximation (words + punctuation)."""
    # Simple approximation: ~4 chars per token on average
    return len(text) // 4


def try_tiktoken(text: str) -> Optional[int]:
    """Try to count tokens using tiktoken if available."""
    try:
        import tiktoken

        enc = tiktoken.get_encoding("cl100k_base")
        return len(enc.encode(text))
    except ImportError:
        return None


def tokenize(text: str) -> int:
    """Count tokens, preferring tiktoken if available."""
    result = try_tiktoken(text)
    return result if result is not None else count_tokens(text)


def extract_terms(text: str) -> list[str]:
    """Extract terms from text for TF-IDF."""
    # Lowercase and extract words
    words = re.findall(r"\b[a-zA-Z_][a-zA-Z0-9_]*\b", text.lower())
    # Filter stopwords
    stopwords = {
        "the",
        "a",
        "an",
        "is",
        "are",
        "was",
        "were",
        "be",
        "been",
        "being",
        "have",
        "has",
        "had",
        "do",
        "does",
        "did",
        "will",
        "would",
        "could",
        "should",
        "may",
        "might",
        "can",
        "this",
        "that",
        "these",
        "those",
        "it",
        "its",
        "of",
        "in",
        "to",
        "for",
        "with",
        "on",
        "at",
        "by",
        "from",
        "as",
        "or",
        "and",
        "if",
        "then",
        "else",
        "when",
        "where",
        "which",
        "who",
        "what",
        "how",
        "all",
        "each",
        "every",
        "both",
        "few",
        "more",
        "most",
        "other",
        "some",
        "such",
        "no",
        "not",
        "only",
        "own",
        "same",
        "so",
        "than",
        "too",
        "very",
        "just",
        "also",
        "now",
        "here",
        "there",
        "but",
        "about",
        "into",
        "through",
        "during",
        "before",
        "after",
        "above",
        "below",
        "between",
        "under",
        "again",
        "further",
        "once",
    }
    return [w for w in words if w not in stopwords and len(w) > 2]


def compute_tfidf_score(
    query_terms: list[str], doc_terms: list[str], idf: dict
) -> float:
    """Compute TF-IDF similarity score."""
    if not doc_terms or not query_terms:
        return 0.0

    # Term frequency in document
    tf = Counter(doc_terms)
    doc_len = len(doc_terms)

    # Score based on query term matches
    score = 0.0
    for term in query_terms:
        if term in tf:
            term_freq = tf[term] / doc_len
            term_idf = idf.get(term, 1.0)
            score += term_freq * term_idf

    return score


def rerank_chunks(chunks: list[DocChunk], query: str, top_k: int = 5) -> list[DocChunk]:
    """Rerank chunks by relevance to query using TF-IDF."""
    if not chunks:
        return []

    query_terms = extract_terms(query)
    if not query_terms:
        return chunks[:top_k]

    # Build IDF from all chunks
    doc_count = len(chunks)
    term_doc_freq: Counter = Counter()
    chunk_terms = []

    for chunk in chunks:
        terms = extract_terms(chunk.content)
        chunk_terms.append(terms)
        unique_terms = set(terms)
        for term in unique_terms:
            term_doc_freq[term] += 1

    # Compute IDF
    idf = {
        term: log(doc_count / (freq + 1)) + 1 for term, freq in term_doc_freq.items()
    }

    # Score each chunk
    for i, chunk in enumerate(chunks):
        chunk.score = compute_tfidf_score(query_terms, chunk_terms[i], idf)

    # Sort by score descending
    ranked = sorted(chunks, key=lambda c: c.score, reverse=True)
    return ranked[:top_k]


def split_into_chunks(
    content: str, source: str = "", max_chunk_tokens: int = 1000
) -> list[DocChunk]:
    """Split content into chunks based on headers or paragraphs."""
    chunks = []

    # Split by markdown headers or double newlines
    sections = re.split(r"\n(?=#{1,3}\s)|(?:\n\n)+", content)

    current_chunk = ""
    current_tokens = 0

    for section in sections:
        section = section.strip()
        if not section:
            continue

        section_tokens = tokenize(section)

        # If section fits in current chunk
        if current_tokens + section_tokens <= max_chunk_tokens:
            current_chunk += "\n\n" + section if current_chunk else section
            current_tokens += section_tokens
        else:
            # Save current chunk if exists
            if current_chunk:
                chunks.append(
                    DocChunk(
                        content=current_chunk, source=source, tokens=current_tokens
                    )
                )

            # Start new chunk
            if section_tokens <= max_chunk_tokens:
                current_chunk = section
                current_tokens = section_tokens
            else:
                # Section too large, split by sentences
                sentences = re.split(r"(?<=[.!?])\s+", section)
                current_chunk = ""
                current_tokens = 0
                for sentence in sentences:
                    sent_tokens = tokenize(sentence)
                    if current_tokens + sent_tokens <= max_chunk_tokens:
                        current_chunk += " " + sentence if current_chunk else sentence
                        current_tokens += sent_tokens
                    else:
                        if current_chunk:
                            chunks.append(
                                DocChunk(
                                    content=current_chunk,
                                    source=source,
                                    tokens=current_tokens,
                                )
                            )
                        current_chunk = sentence
                        current_tokens = sent_tokens

    # Don't forget last chunk
    if current_chunk:
        chunks.append(
            DocChunk(content=current_chunk, source=source, tokens=current_tokens)
        )

    return chunks


def call_context7_resolve(library_name: str) -> dict:
    """Call context7 resolve-library-id via MCP."""
    # Build MCP tool call request
    request = {"libraryName": library_name}

    # For now, just return the request format - actual MCP call handled by Claude
    return {
        "tool": "mcp__context7__resolve-library-id",
        "input": request,
        "instruction": f"Call resolve-library-id with libraryName='{library_name}' to get the Context7-compatible library ID",
    }


def call_context7_docs(
    library_id: str, topic: Optional[str] = None, tokens: int = 10000
) -> dict:
    """Call context7 get-library-docs via MCP."""
    request = {"context7CompatibleLibraryID": library_id, "tokens": tokens}
    if topic:
        request["topic"] = topic

    return {
        "tool": "mcp__context7__get-library-docs",
        "input": request,
        "instruction": f"Call get-library-docs for '{library_id}'"
        + (f" with topic='{topic}'" if topic else ""),
    }


def format_output(chunks: list[DocChunk], query: str) -> str:
    """Format reranked chunks for output."""
    output = []
    output.append(f"# Top {len(chunks)} Results for: {query}\n")

    total_tokens = sum(c.tokens for c in chunks)
    output.append(f"_Total tokens: {total_tokens}_\n")

    for i, chunk in enumerate(chunks, 1):
        output.append(
            f"\n## Result {i} (score: {chunk.score:.3f}, tokens: {chunk.tokens})"
        )
        if chunk.source:
            output.append(f"_Source: {chunk.source}_")
        output.append("")
        output.append(chunk.content)

    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Context7 wrapper with tokenization and reranking"
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # Resolve command
    resolve_parser = subparsers.add_parser("resolve", help="Resolve library name to ID")
    resolve_parser.add_argument("library_name", help="Library name to resolve")

    # Docs command
    docs_parser = subparsers.add_parser("docs", help="Get and rerank library docs")
    docs_parser.add_argument("library_id", help="Context7-compatible library ID")
    docs_parser.add_argument("--topic", "-t", help="Topic to focus on")
    docs_parser.add_argument(
        "--tokens", "-n", type=int, default=10000, help="Max tokens to retrieve"
    )
    docs_parser.add_argument(
        "--top", "-k", type=int, default=5, help="Top K results to return"
    )
    docs_parser.add_argument(
        "--query", "-q", help="Query for reranking (defaults to topic)"
    )

    # Process command (for processing raw content)
    process_parser = subparsers.add_parser(
        "process", help="Process and rerank raw content"
    )
    process_parser.add_argument(
        "--query", "-q", required=True, help="Query for reranking"
    )
    process_parser.add_argument(
        "--top", "-k", type=int, default=5, help="Top K results"
    )
    process_parser.add_argument("--input", "-i", help="Input file (or stdin)")

    args = parser.parse_args()

    if args.command == "resolve":
        result = call_context7_resolve(args.library_name)
        print(json.dumps(result, indent=2))

    elif args.command == "docs":
        result = call_context7_docs(args.library_id, args.topic, args.tokens)
        print(json.dumps(result, indent=2))

    elif args.command == "process":
        # Read content from file or stdin
        if args.input:
            with open(args.input) as f:
                content = f.read()
        else:
            content = sys.stdin.read()

        # Split into chunks
        chunks = split_into_chunks(content, source="context7")

        # Rerank by query
        query = args.query
        ranked = rerank_chunks(chunks, query, top_k=args.top)

        # Output
        print(format_output(ranked, query))

    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
