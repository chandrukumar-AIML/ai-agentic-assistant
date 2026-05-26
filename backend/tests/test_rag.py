"""
Tests for the RAG pipeline:
  - embed_texts() returns numpy array of correct shape
  - faiss_store.search() returns [] when index is empty
  - faiss_store.add_vectors() increases the index size
  - HyDE generates a hypothetical document (LLM mocked)
  - Dual retrieval (FAISS + Chroma) merges and deduplicates results
"""
import numpy as np
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch


# ---------------------------------------------------------------------------
# Tests — embedder
# ---------------------------------------------------------------------------

class TestEmbedder:
    """Tests for backend.rag.embedder.embed_texts()
    Uses sentence-transformers all-MiniLM-L6-v2 → EMBEDDING_DIM = 384.
    """

    @pytest.mark.asyncio
    async def test_embed_texts_returns_ndarray(self):
        """embed_texts() must return a numpy ndarray."""
        mock_embeddings = np.random.rand(1, 384).astype(np.float32)
        with patch("backend.rag.embedder._model") as mock_model:
            mock_model.encode = MagicMock(return_value=mock_embeddings)
            from backend.rag.embedder import embed_texts
            result = await embed_texts(["Hello world"])

        assert isinstance(result, np.ndarray)

    @pytest.mark.asyncio
    async def test_embed_texts_correct_shape(self):
        """embed_texts(['a', 'b']) must return shape (2, 384) — sentence-transformers dim."""
        mock_embeddings = np.random.rand(2, 384).astype(np.float32)
        with patch("backend.rag.embedder._model") as mock_model:
            mock_model.encode = MagicMock(return_value=mock_embeddings)
            from backend.rag.embedder import embed_texts
            result = await embed_texts(["text one", "text two"])

        assert result.shape == (2, 384)

    @pytest.mark.asyncio
    async def test_embed_texts_empty_list_returns_empty(self):
        """embed_texts([]) must return an empty array without calling the model."""
        with patch("backend.rag.embedder._model") as mock_model:
            mock_model.encode = MagicMock()
            from backend.rag.embedder import embed_texts
            result = await embed_texts([])

        mock_model.encode.assert_not_called()
        assert result.shape[0] == 0

    @pytest.mark.asyncio
    async def test_embed_texts_dtype_is_float32(self):
        """embed_texts() must return float32 arrays."""
        mock_embeddings = np.array([[0.5] * 384], dtype=np.float32)
        with patch("backend.rag.embedder._model") as mock_model:
            mock_model.encode = MagicMock(return_value=mock_embeddings)
            from backend.rag.embedder import embed_texts
            result = await embed_texts(["test"])

        assert result.dtype == np.float32


# ---------------------------------------------------------------------------
# Tests — FAISS store  (reset_faiss_singleton autouse fixture in conftest resets
#          _index / _metadata before and after every test)
# ---------------------------------------------------------------------------

class TestFAISSStore:
    """Tests for backend.rag.faiss_store."""

    def test_search_returns_empty_when_index_empty(self):
        """search() must return [] when no vectors have been added."""
        from backend.rag.faiss_store import search
        query_vec = np.random.rand(384).astype(np.float32)
        results = search(query_vec, top_k=5)
        assert results == []

    @pytest.mark.asyncio
    async def test_add_vectors_increases_index_size(self):
        """add_vectors() must increase get_index_size() by the number of added vectors."""
        from backend.rag.faiss_store import add_vectors, get_index_size

        initial_size = get_index_size()
        vectors = np.random.rand(3, 384).astype(np.float32)
        metadata_list = [{"text": f"doc {i}", "source": "test"} for i in range(3)]

        with patch("backend.rag.faiss_store.save"):   # avoid touching disk
            await add_vectors(vectors, metadata_list)

        assert get_index_size() == initial_size + 3

    @pytest.mark.asyncio
    async def test_search_returns_results_after_add(self):
        """After adding vectors, search() must return non-empty results."""
        from backend.rag.faiss_store import add_vectors, search

        vectors = np.random.rand(5, 384).astype(np.float32)
        metadata_list = [{"text": f"document {i}", "source": "test"} for i in range(5)]

        with patch("backend.rag.faiss_store.save"):
            await add_vectors(vectors, metadata_list)

        query_vec = np.random.rand(384).astype(np.float32)
        results = search(query_vec, top_k=3)
        assert len(results) > 0
        assert "score" in results[0]

    @pytest.mark.asyncio
    async def test_add_vectors_metadata_stored_correctly(self):
        """Each added vector's metadata must be retrievable from search results."""
        from backend.rag.faiss_store import add_vectors, search

        vectors = np.random.rand(1, 384).astype(np.float32)
        meta = [{"text": "unique-test-content", "source": "unit_test"}]

        with patch("backend.rag.faiss_store.save"):
            await add_vectors(vectors, meta)

        # Use the same vector as query to get a perfect match
        results = search(vectors[0], top_k=1)
        assert len(results) == 1
        assert results[0].get("text") == "unique-test-content"


# ---------------------------------------------------------------------------
# Tests — HyDE
# ---------------------------------------------------------------------------

class TestHyDE:
    """Tests for backend.rag.hyde.generate_hypothetical_document()"""

    @pytest.mark.asyncio
    async def test_hyde_returns_string(self):
        """generate_hypothetical_document() must return a non-empty string."""
        from backend.rag.hyde import generate_hypothetical_document

        with patch(
            "backend.rag.hyde.ollama_chat_completion",
            new=AsyncMock(return_value="Hypothetical answer about quantum computing."),
        ):
            result = await generate_hypothetical_document("What is quantum entanglement?")

        assert isinstance(result, str)
        assert len(result) > 0

    @pytest.mark.asyncio
    async def test_hyde_strips_whitespace(self):
        """generate_hypothetical_document() must strip leading/trailing whitespace."""
        from backend.rag.hyde import generate_hypothetical_document

        with patch(
            "backend.rag.hyde.ollama_chat_completion",
            new=AsyncMock(return_value="  Some answer with surrounding spaces.  "),
        ):
            result = await generate_hypothetical_document("query")

        assert result == result.strip()

    @pytest.mark.asyncio
    async def test_hyde_passes_query_in_prompt(self):
        """The original query must appear inside the prompt sent to the LLM."""
        from backend.rag.hyde import generate_hypothetical_document
        query = "Explain the theory of relativity in detail"
        captured_messages: list = []

        async def capture_invoke(messages, **kwargs):
            captured_messages.extend(messages)
            return "Relativity states that..."

        with patch("backend.rag.hyde.ollama_chat_completion", side_effect=capture_invoke):
            await generate_hypothetical_document(query)

        assert any(query in str(msg.get("content", "")) for msg in captured_messages)


# ---------------------------------------------------------------------------
# Tests — dual retrieval (FAISS + Chroma) deduplication
# ---------------------------------------------------------------------------

class TestDualRetrieval:
    """
    Simulate the dual-retrieval pattern: merge FAISS and Chroma results,
    deduplicate by content, and verify merged output is clean.
    """

    def _deduplicate(self, results: list[dict]) -> list[dict]:
        """Minimal dedup by 'content' key — mirrors typical rag_tool logic."""
        seen = set()
        deduped = []
        for r in results:
            key = r.get("content", "")
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        return deduped

    def test_dedup_removes_exact_duplicates(self):
        """Identical content from FAISS and Chroma must appear only once."""
        faiss_results = [
            {"content": "Python is a programming language.", "source": "faiss", "score": 0.9},
            {"content": "FastAPI is a web framework.",       "source": "faiss", "score": 0.8},
        ]
        chroma_results = [
            {"content": "Python is a programming language.", "source": "chroma", "score": 0.85},
            {"content": "LangGraph is a graph library.",     "source": "chroma", "score": 0.75},
        ]
        merged = faiss_results + chroma_results
        deduped = self._deduplicate(merged)

        contents = [r["content"] for r in deduped]
        assert len(contents) == len(set(contents)), "Duplicates found after dedup"

    def test_dedup_preserves_unique_results(self):
        """All unique documents from both stores must survive deduplication."""
        faiss_results  = [{"content": "Doc A", "score": 0.9}]
        chroma_results = [{"content": "Doc B", "score": 0.8}]
        merged = faiss_results + chroma_results
        deduped = self._deduplicate(merged)
        assert len(deduped) == 2

    def test_merged_results_sorted_by_score(self):
        """After merging and dedup, results should be sortable by score."""
        results = [
            {"content": "Low relevance",  "score": 0.5},
            {"content": "High relevance", "score": 0.95},
            {"content": "Mid relevance",  "score": 0.7},
        ]
        sorted_results = sorted(results, key=lambda r: r["score"], reverse=True)
        assert sorted_results[0]["score"] == 0.95
        assert sorted_results[-1]["score"] == 0.5
