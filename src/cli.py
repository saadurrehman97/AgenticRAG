"""CLI chat interface for the agentic RAG system."""

import sys
from typing import Optional
from pathlib import Path

from src.config import config
from src.document_processor import DocumentProcessor
from src.knowledge_graph import KnowledgeGraph
from src.retriever import GraphAwareRetriever
from src.agent import AgenticRAG


class CLI:
    """Command-line interface for the RAG system."""

    def __init__(self, agent: AgenticRAG):
        self.agent = agent
        self.history = []

    def print_banner(self):
        """Print welcome banner."""
        print("=" * 80)
        print("🤖 Mini Agentic RAG System with LangGraph")
        print("=" * 80)
        print()
        print("Commands:")
        print("  /help    - Show this help message")
        print("  /history - Show conversation history")
        print("  /exit    - Exit the system")
        print()
        print("Type your question and press Enter.")
        print("=" * 80)
        print()

    def print_help(self):
        """Print help message."""
        print()
        print("Available commands:")
        print("  /help    - Show this help message")
        print("  /history - Show conversation history")
        print("  /exit    - Exit the system")
        print()
        print("Example queries:")
        print("  - What is AuthService?")
        print("  - Summarize all documents related to authentication")
        print("  - How many services depend on PaymentRouter?")
        print("  - Which project depends on the service in X.md?")
        print()

    def print_history(self):
        """Print conversation history."""
        if not self.history:
            print("\nNo conversation history yet.\n")
            return

        print("\n" + "=" * 80)
        print("Conversation History")
        print("=" * 80)

        for i, item in enumerate(self.history, 1):
            print(f"\n[{i}] Q: {item['query']}")
            print(f"    A: {item['answer'][:200]}...")
            print(f"    Steps: {len(item['steps_executed'])}")

        print("=" * 80 + "\n")

    def format_output(self, result: dict):
        """Format and print agent output."""
        print("\n" + "─" * 80)
        print("📝 ANSWER:")
        print("─" * 80)
        print(result["answer"])
        print()

        # Debug information
        print("🔍 EXECUTION DETAILS:")
        print("─" * 80)

        print(f"\n• Router Decision: {result['router_decision']}")
        print(f"• Retrieved Chunks: {result['retrieved_chunks']}")

        if result["tools_used"]:
            print(f"• Tools Used: {', '.join(result['tools_used'])}")

            # Show tool results
            for tool_result in result.get("tool_results", []):
                if tool_result.success:
                    print(f"  ✓ {tool_result.tool_name}: Success")
                else:
                    print(f"  ✗ {tool_result.tool_name}: {tool_result.error}")

        print(f"\n• Steps Executed:")
        for i, step in enumerate(result["steps_executed"], 1):
            print(f"  {i}. {step}")

        if result.get("error"):
            print(f"\n⚠️  Error: {result['error']}")

        print("─" * 80 + "\n")

    def run(self):
        """Run the CLI loop."""
        self.print_banner()

        while True:
            try:
                # Get user input
                query = input("💬 You: ").strip()

                if not query:
                    continue

                # Handle commands
                if query.startswith("/"):
                    if query == "/exit":
                        print("\nGoodbye! 👋\n")
                        break
                    elif query == "/help":
                        self.print_help()
                        continue
                    elif query == "/history":
                        self.print_history()
                        continue
                    else:
                        print(f"\nUnknown command: {query}")
                        print("Type /help for available commands.\n")
                        continue

                # Process query
                print("\n🤔 Processing...")

                result = self.agent.run(query)

                # Format and display output
                self.format_output(result)

                # Save to history
                self.history.append({
                    "query": query,
                    "answer": result["answer"],
                    "steps_executed": result["steps_executed"],
                })

            except KeyboardInterrupt:
                print("\n\nGoodbye! 👋\n")
                break
            except Exception as e:
                print(f"\n❌ Error: {str(e)}\n")
                import traceback
                traceback.print_exc()


def initialize_system(
    data_dir: str = "data",
    graph_dir: str = "graph",
    rebuild_graph: bool = False,
) -> AgenticRAG:
    """
    Initialize the RAG system.

    Args:
        data_dir: Directory containing documents
        graph_dir: Directory to save/load knowledge graph
        rebuild_graph: Whether to rebuild the knowledge graph

    Returns:
        Initialized AgenticRAG system
    """
    print("🚀 Initializing Agentic RAG System...")
    print()

    # Check if data directory exists
    if not Path(data_dir).exists():
        raise ValueError(f"Data directory not found: {data_dir}")

    # Step 1: Load and chunk documents
    print("📄 Step 1: Loading and chunking documents...")
    processor = DocumentProcessor(
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
    )
    chunks = processor.process(data_dir)
    print(f"   ✓ Processed {len(chunks)} chunks from documents\n")

    # Step 2: Build or load knowledge graph
    print("🕸️  Step 2: Building knowledge graph...")
    knowledge_graph = KnowledgeGraph(min_entity_freq=config.min_entity_freq)

    graph_path = Path(graph_dir)
    should_rebuild = rebuild_graph or not (graph_path / "entities.json").exists()

    if should_rebuild:
        knowledge_graph.build_from_chunks(chunks)
        knowledge_graph.save(graph_dir)
        print(f"   ✓ Knowledge graph saved to {graph_dir}\n")
    else:
        knowledge_graph.load(graph_dir)
        print(f"   ✓ Knowledge graph loaded from {graph_dir}\n")

    # Step 3: Initialize retriever
    print("🔍 Step 3: Initializing graph-aware retriever...")
    retriever = GraphAwareRetriever(
        chunks=chunks,
        knowledge_graph=knowledge_graph,
        max_hops=config.max_graph_hops,
    )
    print("   ✓ Retriever initialized\n")

    # Step 4: Create agent
    print("🤖 Step 4: Creating LangGraph agent...")
    agent = AgenticRAG(
        retriever=retriever,
        knowledge_graph=knowledge_graph,
        llm_model=config.llm_model,
        openai_api_key=config.openai_api_key,
    )
    print("   ✓ Agent created\n")

    print("✅ System initialized successfully!\n")

    return agent


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Mini Agentic RAG System")
    parser.add_argument(
        "--data-dir",
        default="data",
        help="Directory containing documents (default: data)",
    )
    parser.add_argument(
        "--graph-dir",
        default="graph",
        help="Directory to save/load knowledge graph (default: graph)",
    )
    parser.add_argument(
        "--rebuild-graph",
        action="store_true",
        help="Rebuild knowledge graph from scratch",
    )
    parser.add_argument(
        "--query",
        type=str,
        help="Run a single query and exit (non-interactive mode)",
    )

    args = parser.parse_args()

    try:
        # Initialize system
        agent = initialize_system(
            data_dir=args.data_dir,
            graph_dir=args.graph_dir,
            rebuild_graph=args.rebuild_graph,
        )

        # Run in appropriate mode
        if args.query:
            # Non-interactive mode
            print(f"Query: {args.query}\n")
            result = agent.run(args.query)

            cli = CLI(agent)
            cli.format_output(result)
        else:
            # Interactive mode
            cli = CLI(agent)
            cli.run()

    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
