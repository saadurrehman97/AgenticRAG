"""Knowledge graph construction and management."""

import re
import json
from typing import List, Dict, Set, Tuple, Any, Optional
from collections import defaultdict, Counter
from dataclasses import dataclass, field
import networkx as nx
from pathlib import Path

try:
    import spacy
    SPACY_AVAILABLE = True
except ImportError:
    SPACY_AVAILABLE = False


@dataclass
class Entity:
    """Represents an entity in the knowledge graph."""

    name: str
    entity_type: str
    mentions: int = 0
    chunks: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Relation:
    """Represents a relation between entities."""

    source: str
    target: str
    relation_type: str
    weight: float = 1.0
    context: List[str] = field(default_factory=list)


class KnowledgeGraph:
    """Builds and manages a knowledge graph from document chunks."""

    def __init__(self, min_entity_freq: int = 2):
        self.min_entity_freq = min_entity_freq
        self.graph = nx.DiGraph()
        self.entities: Dict[str, Entity] = {}
        self.relations: List[Relation] = []
        self.chunk_to_entities: Dict[str, List[str]] = defaultdict(list)

        # Try to load spaCy model
        self.nlp = None
        if SPACY_AVAILABLE:
            try:
                self.nlp = spacy.load("en_core_web_sm")
            except OSError:
                print("Warning: spaCy model 'en_core_web_sm' not found. Using pattern-based extraction.")

    def build_from_chunks(self, chunks: List[Any]) -> None:
        """Build knowledge graph from document chunks."""
        print("Extracting entities from chunks...")

        # First pass: extract entities
        entity_counter = Counter()
        entity_chunks = defaultdict(set)

        for chunk in chunks:
            entities = self._extract_entities(chunk.content)

            for entity_name, entity_type in entities:
                entity_counter[entity_name] += 1
                entity_chunks[entity_name].add(chunk.chunk_id)

        # Filter entities by frequency
        print(f"Found {len(entity_counter)} unique entities")
        filtered_entities = {
            name: count
            for name, count in entity_counter.items()
            if count >= self.min_entity_freq
        }
        print(f"Keeping {len(filtered_entities)} entities with freq >= {self.min_entity_freq}")

        # Create entity objects
        for entity_name in filtered_entities:
            entity_type = self._get_entity_type(entity_name)
            self.entities[entity_name] = Entity(
                name=entity_name,
                entity_type=entity_type,
                mentions=entity_counter[entity_name],
                chunks=entity_chunks[entity_name],
            )

        # Second pass: extract relations
        print("Extracting relations...")
        for chunk in chunks:
            chunk_entities = [
                e for e, _ in self._extract_entities(chunk.content)
                if e in self.entities
            ]

            self.chunk_to_entities[chunk.chunk_id] = chunk_entities

            # Extract relations from this chunk
            relations = self._extract_relations(chunk.content, chunk_entities)
            for relation in relations:
                self.relations.append(relation)

        # Build NetworkX graph
        self._build_networkx_graph()

        print(f"Knowledge graph built: {len(self.entities)} entities, {len(self.relations)} relations")

    def _extract_entities(self, text: str) -> List[Tuple[str, str]]:
        """Extract entities from text using spaCy or patterns."""
        entities = []

        if self.nlp:
            # Use spaCy NER
            doc = self.nlp(text)
            for ent in doc.ents:
                if ent.label_ in ["PERSON", "ORG", "PRODUCT", "GPE", "WORK_OF_ART", "EVENT"]:
                    entities.append((ent.text, ent.label_))
        else:
            # Fallback: pattern-based extraction
            entities.extend(self._pattern_based_extraction(text))

        return entities

    def _pattern_based_extraction(self, text: str) -> List[Tuple[str, str]]:
        """Extract entities using regex patterns."""
        entities = []

        # Capitalized words (likely proper nouns)
        proper_nouns = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", text)
        for noun in proper_nouns:
            if len(noun) > 2:  # Filter out short words
                entities.append((noun, "ENTITY"))

        # Common technical patterns
        # CamelCase identifiers
        camel_case = re.findall(r"\b[A-Z][a-z]+(?:[A-Z][a-z]+)+\b", text)
        for identifier in camel_case:
            entities.append((identifier, "IDENTIFIER"))

        # Module/Service names (e.g., AuthService, PaymentRouter)
        services = re.findall(r"\b([A-Z][a-zA-Z]*(?:Service|Router|Module|Manager|Controller|Handler))\b", text)
        for service in services:
            entities.append((service, "SERVICE"))

        return entities

    def _get_entity_type(self, entity_name: str) -> str:
        """Determine entity type from name."""
        if any(suffix in entity_name for suffix in ["Service", "Router", "Module", "Manager", "Controller", "Handler"]):
            return "SERVICE"
        elif entity_name[0].isupper():
            return "ENTITY"
        return "UNKNOWN"

    def _extract_relations(self, text: str, entities: List[str]) -> List[Relation]:
        """Extract relations between entities in text."""
        relations = []

        # Co-occurrence based relations (entities in same chunk)
        for i, entity1 in enumerate(entities):
            for entity2 in entities[i + 1 :]:
                relations.append(
                    Relation(
                        source=entity1,
                        target=entity2,
                        relation_type="CO_OCCURS",
                        weight=1.0,
                        context=[text[:200]],  # Store snippet
                    )
                )

        # Pattern-based relations (case-insensitive, handle various formats)
        relation_patterns = [
            (r"\b(\w+(?:Service|Router|Module|Manager))\s+depends?\s+on\s+(\w+(?:Service|Router|Module|Manager))\b", "DEPENDS_ON"),
            (r"\b(\w+(?:Service|Router|Module))\s+uses?\s+(\w+(?:Service|Router|Module))\b", "USES"),
            (r"\b(\w+(?:Service|Router))\s+calls?\s+(\w+(?:Service|Router))\b", "CALLS"),
            (r"\b(\w+)\s+extends?\s+(\w+)\b", "EXTENDS"),
            (r"\b(\w+)\s+implements?\s+(\w+)\b", "IMPLEMENTS"),
            (r"depends?\s+on[:]\s*([^.]+)", "DEPENDS_ON_LIST"),  # Catches "depends on: X, Y, Z"
            (r"(?:used by|depend on it|using)[:]\s*([^.]+)", "USED_BY_LIST"),  # Catches lists
        ]

        for pattern, rel_type in relation_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for source, target in matches:
                if source in entities and target in entities:
                    relations.append(
                        Relation(
                            source=source,
                            target=target,
                            relation_type=rel_type,
                            weight=2.0,  # Explicit relations have higher weight
                            context=[text[:200]],
                        )
                    )

        return relations

    def _build_networkx_graph(self) -> None:
        """Build NetworkX graph from entities and relations."""
        # Add entity nodes
        for entity_name, entity in self.entities.items():
            self.graph.add_node(
                entity_name,
                entity_type=entity.entity_type,
                mentions=entity.mentions,
                chunks=",".join(list(entity.chunks)),  # Convert list to string for GraphML
            )

        # Add relation edges
        relation_weights = defaultdict(float)
        for relation in self.relations:
            key = (relation.source, relation.target, relation.relation_type)
            relation_weights[key] += relation.weight

        for (source, target, rel_type), weight in relation_weights.items():
            if source in self.graph and target in self.graph:
                self.graph.add_edge(source, target, relation_type=rel_type, weight=weight)

    def get_neighbors(self, entity: str, max_hops: int = 1) -> Set[str]:
        """Get neighboring entities within max_hops."""
        if entity not in self.graph:
            return set()

        neighbors = set()
        for hop in range(1, max_hops + 1):
            if hop == 1:
                neighbors.update(self.graph.neighbors(entity))
            else:
                new_neighbors = set()
                for neighbor in list(neighbors):
                    new_neighbors.update(self.graph.neighbors(neighbor))
                neighbors.update(new_neighbors)

        return neighbors

    def get_related_chunks(self, entity: str, max_hops: int = 2) -> Set[str]:
        """Get all chunks related to an entity within max_hops."""
        if entity not in self.entities:
            return set()

        # Start with direct chunks
        related_chunks = set(self.entities[entity].chunks)

        # Add chunks from neighboring entities
        neighbors = self.get_neighbors(entity, max_hops)
        for neighbor in neighbors:
            if neighbor in self.entities:
                related_chunks.update(self.entities[neighbor].chunks)

        return related_chunks

    def get_path_between_entities(self, entity1: str, entity2: str) -> Optional[List[str]]:
        """Find shortest path between two entities."""
        if entity1 not in self.graph or entity2 not in self.graph:
            return None

        try:
            path = nx.shortest_path(self.graph.to_undirected(), entity1, entity2)
            return path
        except nx.NetworkXNoPath:
            return None

    def save(self, output_dir: str) -> None:
        """Save knowledge graph to disk."""
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # Save entities
        entities_data = {
            name: {
                "name": entity.name,
                "entity_type": entity.entity_type,
                "mentions": entity.mentions,
                "chunks": list(entity.chunks),
            }
            for name, entity in self.entities.items()
        }

        with open(output_path / "entities.json", "w") as f:
            json.dump(entities_data, f, indent=2)

        # Save relations
        relations_data = [
            {
                "source": rel.source,
                "target": rel.target,
                "relation_type": rel.relation_type,
                "weight": rel.weight,
            }
            for rel in self.relations
        ]

        with open(output_path / "relations.json", "w") as f:
            json.dump(relations_data, f, indent=2)

        # Save graph in GraphML format
        nx.write_graphml(self.graph, str(output_path / "knowledge_graph.graphml"))

        print(f"Knowledge graph saved to {output_dir}")

    def load(self, input_dir: str) -> None:
        """Load knowledge graph from disk."""
        input_path = Path(input_dir)

        # Load entities
        with open(input_path / "entities.json", "r") as f:
            entities_data = json.load(f)

        for name, data in entities_data.items():
            self.entities[name] = Entity(
                name=data["name"],
                entity_type=data["entity_type"],
                mentions=data["mentions"],
                chunks=set(data["chunks"]),
            )

        # Load relations
        with open(input_path / "relations.json", "r") as f:
            relations_data = json.load(f)

        for rel_data in relations_data:
            self.relations.append(
                Relation(
                    source=rel_data["source"],
                    target=rel_data["target"],
                    relation_type=rel_data["relation_type"],
                    weight=rel_data["weight"],
                )
            )

        # Rebuild NetworkX graph
        self._build_networkx_graph()

        print(f"Knowledge graph loaded from {input_dir}")
