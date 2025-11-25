"""Custom tools for the agentic RAG system."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass
import re


@dataclass
class ToolResult:
    """Result from a tool execution."""

    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None


class LookupTool:
    """Tool for looking up facts about specific entities."""

    def __init__(self, knowledge_graph, retriever):
        self.knowledge_graph = knowledge_graph
        self.retriever = retriever

    def lookup_facts(self, entity_name: str) -> ToolResult:
        """
        Look up facts about a specific entity.

        Args:
            entity_name: Name of the entity to look up

        Returns:
            ToolResult with entity information
        """
        try:
            if entity_name not in self.knowledge_graph.entities:
                # Try case-insensitive search
                entity_lower = entity_name.lower()
                matching_entities = [
                    e for e in self.knowledge_graph.entities.keys()
                    if e.lower() == entity_lower
                ]

                if not matching_entities:
                    return ToolResult(
                        tool_name="lookup_facts",
                        success=False,
                        result=None,
                        error=f"Entity '{entity_name}' not found in knowledge graph",
                    )

                entity_name = matching_entities[0]

            entity = self.knowledge_graph.entities[entity_name]

            # Get related chunks
            results = self.retriever.retrieve_by_entity(entity_name, top_k=3)

            # Get neighboring entities
            neighbors = self.knowledge_graph.get_neighbors(entity_name, max_hops=1)

            # Get relations
            relations = [
                rel for rel in self.knowledge_graph.relations
                if rel.source == entity_name or rel.target == entity_name
            ]

            facts = {
                "entity_name": entity.name,
                "entity_type": entity.entity_type,
                "mentions": entity.mentions,
                "related_entities": list(neighbors),
                "relations": [
                    {
                        "source": rel.source,
                        "target": rel.target,
                        "type": rel.relation_type,
                    }
                    for rel in relations[:5]  # Limit to top 5
                ],
                "relevant_chunks": [
                    {
                        "content": result.chunk.content[:200] + "...",
                        "source": result.chunk.metadata.get("source", "unknown"),
                    }
                    for result in results
                ],
            }

            return ToolResult(
                tool_name="lookup_facts",
                success=True,
                result=facts,
            )

        except Exception as e:
            return ToolResult(
                tool_name="lookup_facts",
                success=False,
                result=None,
                error=str(e),
            )


class SummarizeTool:
    """Tool for summarizing documents on a specific topic."""

    def __init__(self, retriever, llm):
        self.retriever = retriever
        self.llm = llm

    def summarize_document(self, topic: str) -> ToolResult:
        """
        Summarize all documents related to a specific topic.

        Args:
            topic: The topic to summarize

        Returns:
            ToolResult with summary
        """
        try:
            # Retrieve relevant chunks
            results = self.retriever.retrieve(
                query=f"information about {topic}",
                use_graph=True,
                top_k=5,
            )

            if not results:
                return ToolResult(
                    tool_name="summarize_document",
                    success=False,
                    result=None,
                    error=f"No documents found related to '{topic}'",
                )

            # Combine context
            context = "\n\n".join([
                f"[Source: {result.chunk.metadata.get('source', 'unknown')}]\n{result.chunk.content}"
                for result in results
            ])

            # Generate summary using LLM
            prompt = f"""Based on the following excerpts, provide a comprehensive summary about {topic}.

Context:
{context}

Summary:"""

            summary = self.llm.invoke(prompt)

            return ToolResult(
                tool_name="summarize_document",
                success=True,
                result={
                    "topic": topic,
                    "summary": summary.content if hasattr(summary, 'content') else str(summary),
                    "sources": [
                        result.chunk.metadata.get("source", "unknown")
                        for result in results
                    ],
                    "num_chunks": len(results),
                },
            )

        except Exception as e:
            return ToolResult(
                tool_name="summarize_document",
                success=False,
                result=None,
                error=str(e),
            )


class CalculationTool:
    """Tool for performing calculations on extracted data."""

    def __init__(self, knowledge_graph):
        self.knowledge_graph = knowledge_graph

    def run_calculation(self, calculation_input: str) -> ToolResult:
        """
        Perform calculations based on knowledge graph data.

        Supports:
        - count entities: Count total entities
        - count entities of type X: Count entities of specific type
        - count relations: Count total relations
        - count dependencies of X: Count dependencies of an entity
        - calculate avg mentions: Average mentions per entity

        Args:
            calculation_input: Description of calculation to perform

        Returns:
            ToolResult with calculation result
        """
        try:
            calc_lower = calculation_input.lower()

            # Count total entities
            if "count entities" in calc_lower and "type" not in calc_lower:
                count = len(self.knowledge_graph.entities)
                return ToolResult(
                    tool_name="run_calculation",
                    success=True,
                    result={
                        "calculation": "count_entities",
                        "value": count,
                        "description": f"Total number of entities: {count}",
                    },
                )

            # Count entities by type
            if "count entities of type" in calc_lower or "count" in calc_lower and "type" in calc_lower:
                # Extract type
                type_match = re.search(r"type\s+(\w+)", calc_lower)
                if type_match:
                    entity_type = type_match.group(1).upper()
                    count = sum(
                        1 for e in self.knowledge_graph.entities.values()
                        if e.entity_type == entity_type
                    )

                    return ToolResult(
                        tool_name="run_calculation",
                        success=True,
                        result={
                            "calculation": "count_entities_by_type",
                            "type": entity_type,
                            "value": count,
                            "description": f"Number of {entity_type} entities: {count}",
                        },
                    )

            # Count relations
            if "count relations" in calc_lower or "count dependencies" in calc_lower:
                # Check if for specific entity
                entity_match = re.search(r"(?:of|for)\s+(\w+)", calculation_input)
                if entity_match:
                    entity_name = entity_match.group(1)

                    # Find matching entity (case-insensitive)
                    matching = [
                        e for e in self.knowledge_graph.entities.keys()
                        if e.lower() == entity_name.lower()
                    ]

                    if matching:
                        entity_name = matching[0]
                        count = sum(
                            1 for rel in self.knowledge_graph.relations
                            if rel.source == entity_name or rel.target == entity_name
                        )

                        return ToolResult(
                            tool_name="run_calculation",
                            success=True,
                            result={
                                "calculation": "count_entity_relations",
                                "entity": entity_name,
                                "value": count,
                                "description": f"Number of relations for {entity_name}: {count}",
                            },
                        )
                else:
                    # Count all relations
                    count = len(self.knowledge_graph.relations)
                    return ToolResult(
                        tool_name="run_calculation",
                        success=True,
                        result={
                            "calculation": "count_relations",
                            "value": count,
                            "description": f"Total number of relations: {count}",
                        },
                    )

            # Average mentions
            if "avg" in calc_lower or "average" in calc_lower:
                if self.knowledge_graph.entities:
                    avg = sum(
                        e.mentions for e in self.knowledge_graph.entities.values()
                    ) / len(self.knowledge_graph.entities)

                    return ToolResult(
                        tool_name="run_calculation",
                        success=True,
                        result={
                            "calculation": "average_mentions",
                            "value": round(avg, 2),
                            "description": f"Average mentions per entity: {round(avg, 2)}",
                        },
                    )

            # If no pattern matched
            return ToolResult(
                tool_name="run_calculation",
                success=False,
                result=None,
                error=f"Unknown calculation type: '{calculation_input}'",
            )

        except Exception as e:
            return ToolResult(
                tool_name="run_calculation",
                success=False,
                result=None,
                error=str(e),
            )


class DependencyAnalysisTool:
    """Tool for analyzing dependencies between services/modules."""

    def __init__(self, knowledge_graph, retriever=None):
        self.knowledge_graph = knowledge_graph
        self.retriever = retriever

    def analyze_dependencies(self, entity_name: str) -> ToolResult:
        """
        Analyze dependencies for a specific entity.

        Args:
            entity_name: Name of the entity to analyze

        Returns:
            ToolResult with dependency analysis
        """
        try:
            # Find entity (case-insensitive)
            matching = [
                e for e in self.knowledge_graph.entities.keys()
                if e.lower() == entity_name.lower()
            ]

            if not matching:
                return ToolResult(
                    tool_name="analyze_dependencies",
                    success=False,
                    result=None,
                    error=f"Entity '{entity_name}' not found",
                )

            entity_name = matching[0]

            # First, try to get dependencies from graph relations
            depends_on_graph = [
                rel.target for rel in self.knowledge_graph.relations
                if rel.source == entity_name and rel.relation_type in ["DEPENDS_ON", "USES", "CALLS"]
            ]
            depended_by_graph = [
                rel.source for rel in self.knowledge_graph.relations
                if rel.target == entity_name and rel.relation_type in ["DEPENDS_ON", "USES", "CALLS"]
            ]

            # Also extract from document text using retriever
            depends_on_text = []
            depended_by_text = []

            if self.retriever:
                # Retrieve documents about this entity
                results = self.retriever.retrieve_by_entity(entity_name, top_k=5)

                # Parse dependency information from text
                import re
                for result in results:
                    content = result.chunk.content

                    # Look for "X depends on:" followed by bullet list
                    depends_section = re.search(
                        rf'{entity_name}\s+depends?\s+on[:\s]+(.+?)(?=\n\n|\n[A-Z]|$)',
                        content,
                        re.IGNORECASE | re.DOTALL
                    )
                    if depends_section:
                        deps_text = depends_section.group(1)
                        # Extract all service/module names from this section
                        found_deps = re.findall(r'\b([A-Z][a-z]+(?:Service|Router|Module|Manager))\b', deps_text)
                        depends_on_text.extend([d for d in found_deps if d != entity_name])

                    # Look for "Dependencies" section
                    deps_header = re.search(r'##?\s*Dependencies\s*\n(.+?)(?=\n##|$)', content, re.DOTALL | re.IGNORECASE)
                    if deps_header:
                        deps_section = deps_header.group(1)
                        found_deps = re.findall(r'-\s+([A-Z][a-z]+(?:Service|Router|Module|Manager))', deps_section)
                        depends_on_text.extend([d for d in found_deps if d != entity_name])

                    # Look for "Projects Using X" or "Services that depend"
                    depended_section = re.search(
                        rf'(?:Projects? Using {entity_name}|Services? that depend on {entity_name}|Dependent Services)[:\s]+(.+?)(?=\n\n|\n##|$)',
                        content,
                        re.IGNORECASE | re.DOTALL
                    )
                    if depended_section:
                        deps_text = depended_section.group(1)
                        # Extract projects and services
                        found_deps = re.findall(r'\b(Project[A-Z][a-z]+|[A-Z][a-z]+(?:Service|Router|Module|Manager))\b', deps_text)
                        depended_by_text.extend([d for d in found_deps if d != entity_name])

                    # Look for "Used By" or "Depended By" sections
                    used_by_header = re.search(r'##?\s*(?:Used By|Dependent Services)\s*\n(.+?)(?=\n##|$)', content, re.DOTALL | re.IGNORECASE)
                    if used_by_header:
                        deps_section = used_by_header.group(1)
                        found_deps = re.findall(r'(?:-\s+|\d+\.\s+)([A-Z][a-z]+(?:Service|Router|Module|Manager|Project[A-Z][a-z]+))', deps_section)
                        depended_by_text.extend([d for d in found_deps if d != entity_name])

            # Combine graph and text-based dependencies
            depends_on = list(set(depends_on_graph + depends_on_text))
            depended_by = list(set(depended_by_graph + depended_by_text))

            analysis = {
                "entity": entity_name,
                "depends_on": depends_on,
                "depended_by": depended_by,
                "depends_on_count": len(depends_on),
                "depended_by_count": len(depended_by),
                "is_critical": len(depended_by) > 2,  # Critical if many depend on it
            }

            return ToolResult(
                tool_name="analyze_dependencies",
                success=True,
                result=analysis,
            )

        except Exception as e:
            return ToolResult(
                tool_name="analyze_dependencies",
                success=False,
                result=None,
                error=str(e),
            )
