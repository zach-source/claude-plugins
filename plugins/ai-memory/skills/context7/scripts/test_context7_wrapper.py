#!/usr/bin/env python3
"""Tests for context7_wrapper.py"""

import pytest
from context7_wrapper import (
    count_tokens,
    extract_terms,
    compute_tfidf_score,
    rerank_chunks,
    split_into_chunks,
    DocChunk,
    call_context7_resolve,
    call_context7_docs,
    format_output,
)


class TestTokenization:
    """Tests for token counting functions."""

    def test_count_tokens_empty(self):
        assert count_tokens("") == 0

    def test_count_tokens_short(self):
        # ~4 chars per token
        result = count_tokens("hello world")
        assert result == 2  # 11 chars / 4 = 2

    def test_count_tokens_longer(self):
        text = "This is a longer piece of text for testing token counting"
        result = count_tokens(text)
        assert result > 10  # Should be reasonable estimate


class TestTermExtraction:
    """Tests for term extraction."""

    def test_extract_terms_basic(self):
        terms = extract_terms("Hello World Python Programming")
        assert "hello" in terms
        assert "world" in terms
        assert "python" in terms
        assert "programming" in terms

    def test_extract_terms_filters_stopwords(self):
        terms = extract_terms("the quick brown fox jumps over the lazy dog")
        assert "the" not in terms
        # "over" is kept as it can be meaningful in code contexts
        assert "quick" in terms
        assert "brown" in terms
        assert "fox" in terms
        assert "jumps" in terms

    def test_extract_terms_filters_short_words(self):
        terms = extract_terms("a is an it")
        assert len(terms) == 0

    def test_extract_terms_handles_code(self):
        terms = extract_terms("function_name variableName camelCase")
        assert "function_name" in terms
        assert "variablename" in terms
        assert "camelcase" in terms


class TestTFIDF:
    """Tests for TF-IDF scoring."""

    def test_compute_tfidf_empty_query(self):
        score = compute_tfidf_score([], ["hello", "world"], {"hello": 1.0})
        assert score == 0.0

    def test_compute_tfidf_empty_doc(self):
        score = compute_tfidf_score(["hello"], [], {"hello": 1.0})
        assert score == 0.0

    def test_compute_tfidf_matching_terms(self):
        query_terms = ["python", "programming"]
        doc_terms = ["python", "is", "great", "for", "programming"]
        idf = {"python": 2.0, "programming": 1.5, "great": 1.0}
        score = compute_tfidf_score(query_terms, doc_terms, idf)
        assert score > 0

    def test_compute_tfidf_no_matching_terms(self):
        query_terms = ["javascript", "nodejs"]
        doc_terms = ["python", "django", "flask"]
        idf = {"javascript": 1.0, "nodejs": 1.0, "python": 1.0}
        score = compute_tfidf_score(query_terms, doc_terms, idf)
        assert score == 0.0


class TestReranking:
    """Tests for chunk reranking."""

    def test_rerank_empty_chunks(self):
        result = rerank_chunks([], "python")
        assert result == []

    def test_rerank_single_chunk(self):
        chunks = [
            DocChunk(content="Python programming guide", source="test", tokens=10)
        ]
        result = rerank_chunks(chunks, "python", top_k=5)
        assert len(result) == 1
        assert result[0].score > 0

    def test_rerank_orders_by_relevance(self):
        chunks = [
            DocChunk(content="JavaScript is a language", source="js", tokens=10),
            DocChunk(
                content="Python programming Python code Python examples",
                source="py",
                tokens=10,
            ),
            DocChunk(content="Ruby on Rails framework", source="ruby", tokens=10),
        ]
        result = rerank_chunks(chunks, "python programming", top_k=5)
        # Python chunk should be first due to more matches
        assert result[0].source == "py"

    def test_rerank_respects_top_k(self):
        chunks = [
            DocChunk(content=f"Document {i} about Python", source=f"doc{i}", tokens=10)
            for i in range(10)
        ]
        result = rerank_chunks(chunks, "python", top_k=3)
        assert len(result) == 3


class TestChunking:
    """Tests for content chunking."""

    def test_split_empty_content(self):
        result = split_into_chunks("")
        assert result == []

    def test_split_small_content(self):
        content = "This is a small piece of content."
        result = split_into_chunks(content)
        assert len(result) == 1
        assert result[0].content == content

    def test_split_by_headers(self):
        content = """# Header 1
Content under header 1.

## Header 2
Content under header 2.

### Header 3
Content under header 3."""
        result = split_into_chunks(content, max_chunk_tokens=50)
        assert len(result) >= 1

    def test_split_preserves_content(self):
        content = "First paragraph.\n\nSecond paragraph.\n\nThird paragraph."
        result = split_into_chunks(content)
        combined = "\n\n".join(c.content for c in result)
        # All content should be preserved
        assert "First paragraph" in combined
        assert "Second paragraph" in combined
        assert "Third paragraph" in combined


class TestMCPCalls:
    """Tests for MCP call formatting."""

    def test_call_context7_resolve(self):
        result = call_context7_resolve("react")
        assert result["tool"] == "mcp__context7__resolve-library-id"
        assert result["input"]["libraryName"] == "react"

    def test_call_context7_docs_basic(self):
        result = call_context7_docs("/facebook/react")
        assert result["tool"] == "mcp__context7__get-library-docs"
        assert result["input"]["context7CompatibleLibraryID"] == "/facebook/react"
        assert result["input"]["tokens"] == 10000

    def test_call_context7_docs_with_topic(self):
        result = call_context7_docs("/facebook/react", topic="hooks", tokens=5000)
        assert result["input"]["topic"] == "hooks"
        assert result["input"]["tokens"] == 5000


class TestFormatOutput:
    """Tests for output formatting."""

    def test_format_output_empty(self):
        result = format_output([], "test query")
        assert "Top 0 Results" in result

    def test_format_output_with_chunks(self):
        chunks = [
            DocChunk(
                content="First result content", source="src1", tokens=10, score=0.9
            ),
            DocChunk(
                content="Second result content", source="src2", tokens=20, score=0.5
            ),
        ]
        result = format_output(chunks, "test query")
        assert "Top 2 Results" in result
        assert "First result content" in result
        assert "Second result content" in result
        assert "score: 0.900" in result
        assert "tokens: 30" in result  # Total tokens


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
