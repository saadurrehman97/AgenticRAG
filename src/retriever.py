"""Graph-aware retriever with multi-hop query resolution."""

from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass
import numpy as np
from sentence_transformers import SentenceTransformer

from src.document_processor import Chunk
from src.knowledge_graph import KnowledgeGraph


@dataclass
class RetrievalResult:
    """Represents a retrieval result."""

    chunk: Chunk
    score: float
    retrieval_method: str
    hop_count: int = 0
    related_entities: List[str] = None

    def __post_init__(self):
        if self.related_entities is None:
            self.related_entities = []


class GraphAwareRetriever:
    """Retriever that uses knowledge graph for multi-hop reasoning."""

    def __init__(
        self,
        chunks: List[Chunk],
        knowledge_graph: KnowledgeGraph,
        embedding_model: str = "all-MiniLM-L6-v2",
        max_hops: int = 2,
        top_k: int = 5,
    ):
        self.chunks = {chunk.chunk_id: chunk for chunk in chunks}
        self.knowledge_graph = knowledge_graph
        self.max_hops = max_hops
        self.top_k = top_k

        # Initialize embedding model
        print(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)

        # Generate embeddings for all chunks
        self._generate_embeddings()

    def _generate_embeddings(self) -> None:
        """Generate embeddings for all chunks."""
        print("Generating embeddings for chunks...")
        chunk_list = list(self.chunks.values())
        texts = [chunk.content for chunk in chunk_list]

        embeddings = self.embedding_model.encode(texts, show_progress_bar=True)

        for chunk, embedding in zip(chunk_list, embeddings):
            chunk.embedding = embedding.tolist()

        print(f"Generated embeddings for {len(chunk_list)} chunks")

    def retrieve(
        self,
        query: str,
        use_graph: bool = True,
        top_k: Optional[int] = None,
    ) -> List[RetrievalResult]:
        """
        Retrieve relevant chunks for a query.

        Args:
            query: The search query
            use_graph: Whether to use graph-based expansion
            top_k: Number of results to return (defaults to self.top_k)

        Returns:
            List of retrieval results sorted by score
        """
        if top_k is None:
            top_k = self.top_k

        # Step 1: Semantic search
        semantic_results = self._semantic_search(query, top_k * 2)

        if not use_graph:
            return semantic_results[:top_k]

        # Step 2: Extract entities from query
        query_entities = self._extract_query_entities(query)

        # Step 3: Graph-based expansion
        graph_results = []
        if query_entities:
            graph_results = self._graph_based_retrieval(query_entities, query)

        # Step 4: Combine and re-rank results
        combined_results = self._combine_and_rerank(
            semantic_results, graph_results, query
        )

        return combined_results[:top_k]

    def _semantic_search(self, query: str, top_k: int) -> List[RetrievalResult]:
        """Perform semantic search using embeddings."""
        query_embedding = self.embedding_model.encode([query])[0]

        # Calculate similarities
        scores = []
        for chunk in self.chunks.values():
            if chunk.embedding:
                similarity = self._cosine_similarity(
                    query_embedding, np.array(chunk.embedding)
                )
                scores.append((chunk, similarity))

        # Sort by score
        scores.sort(key=lambda x: x[1], reverse=True)

        # Create results
        results = []
        for chunk, score in scores[:top_k]:
            results.append(
                RetrievalResult(
                    chunk=chunk,
                    score=score,
                    retrieval_method="semantic",
                )
            )

        return results

    def _extract_query_entities(self, query: str) -> List[str]:
        """Extract entities from query that exist in knowledge graph."""
        query_entities = []

        # Check if any known entities appear in the query
        for entity_name in self.knowledge_graph.entities.keys():
            if entity_name.lower() in query.lower():
                query_entities.append(entity_name)

        return query_entities

    def _graph_based_retrieval(
        self, entities: List[str], query: str
    ) -> List[RetrievalResult]:
        """Retrieve chunks using graph traversal."""
        results = []
        query_embedding = self.embedding_model.encode([query])[0]

        # Collect relevant chunk IDs through graph traversal
        relevant_chunk_ids: Set[str] = set()
        entity_hop_map: Dict[str, int] = {}

        for entity in entities:
            # Direct chunks (hop 0)
            if entity in self.knowledge_graph.entities:
                direct_chunks = self.knowledge_graph.entities[entity].chunks
                relevant_chunk_ids.update(direct_chunks)
                for chunk_id in direct_chunks:
                    entity_hop_map[chunk_id] = 0

            # Multi-hop expansion
            for hop in range(1, self.max_hops + 1):
                related_chunks = self.knowledge_graph.get_related_chunks(
                    entity, max_hops=hop
                )
                for chunk_id in related_chunks:
                    if chunk_id not in entity_hop_map:
                        entity_hop_map[chunk_id] = hop
                relevant_chunk_ids.update(related_chunks)

        # Score and rank the chunks
        for chunk_id in relevant_chunk_ids:
            if chunk_id in self.chunks:
                chunk = self.chunks[chunk_id]

                # Calculate semantic similarity
                if chunk.embedding:
                    semantic_score = self._cosine_similarity(
                        query_embedding, np.array(chunk.embedding)
                    )

                    # Apply hop penalty (closer entities get higher scores)
                    hop_count = entity_hop_map.get(chunk_id, self.max_hops)
                    hop_penalty = 1.0 / (1.0 + hop_count * 0.3)

                    final_score = semantic_score * hop_penalty

                    # Get related entities for this chunk
                    related_entities = self.knowledge_graph.chunk_to_entities.get(
                        chunk_id, []
                    )

                    results.append(
                        RetrievalResult(
                            chunk=chunk,
                            score=final_score,
                            retrieval_method="graph",
                            hop_count=hop_count,
                            related_entities=related_entities,
                        )
                    )

        # Sort by score
        results.sort(key=lambda x: x.score, reverse=True)

        return results

    def _combine_and_rerank(
        self,
        semantic_results: List[RetrievalResult],
        graph_results: List[RetrievalResult],
        query: str,
    ) -> List[RetrievalResult]:
        """Combine and re-rank results from different methods."""
        # Create a map of chunk_id to best result
        result_map: Dict[str, RetrievalResult] = {}

        # Add semantic results
        for result in semantic_results:
            chunk_id = result.chunk.chunk_id
            result_map[chunk_id] = result

        # Add or update with graph results
        for result in graph_results:
            chunk_id = result.chunk.chunk_id
            if chunk_id in result_map:
                # Combine scores (weighted average)
                existing = result_map[chunk_id]
                combined_score = (existing.score * 0.5) + (result.score * 0.5)

                # Keep the higher scored method
                if result.score > existing.score:
                    result.score = combined_score
                    result.retrieval_method = "hybrid"
                    result_map[chunk_id] = result
                else:
                    existing.score = combined_score
                    existing.retrieval_method = "hybrid"
            else:
                result_map[chunk_id] = result

        # Convert to list and sort
        combined_results = list(result_map.values())
        combined_results.sort(key=lambda x: x.score, reverse=True)

        return combined_results

    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        return float(dot_product / (norm1 * norm2))

    def retrieve_by_entity(
        self, entity_name: str, top_k: Optional[int] = None
    ) -> List[RetrievalResult]:
        """Retrieve chunks specifically related to an entity."""
        if top_k is None:
            top_k = self.top_k

        if entity_name not in self.knowledge_graph.entities:
            return []

        # Get all related chunks
        related_chunk_ids = self.knowledge_graph.get_related_chunks(
            entity_name, max_hops=self.max_hops
        )

        results = []
        for chunk_id in related_chunk_ids:
            if chunk_id in self.chunks:
                chunk = self.chunks[chunk_id]

                # Score based on entity mentions
                entity_mentions = self.knowledge_graph.chunk_to_entities.get(
                    chunk_id, []
                )
                score = 1.0 if entity_name in entity_mentions else 0.5

                results.append(
                    RetrievalResult(
                        chunk=chunk,
                        score=score,
                        retrieval_method="entity_lookup",
                        related_entities=entity_mentions,
                    )
                )

        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def multi_hop_query(
        self, start_entity: str, end_entity: str
    ) -> Optional[Dict[str, Any]]:
        """
        Find path between two entities and retrieve relevant context.

        Returns:
            Dictionary with path information and relevant chunks
        """
        path = self.knowledge_graph.get_path_between_entities(
            start_entity, end_entity
        )

        if not path:
            return None

        # Collect chunks for all entities in the path
        all_chunk_ids: Set[str] = set()
        for entity in path:
            if entity in self.knowledge_graph.entities:
                all_chunk_ids.update(self.knowledge_graph.entities[entity].chunks)

        # Get the chunks
        chunks = [self.chunks[cid] for cid in all_chunk_ids if cid in self.chunks]

        return {
            "path": path,
            "path_length": len(path) - 1,
            "chunks": chunks,
            "entities": path,
        }
