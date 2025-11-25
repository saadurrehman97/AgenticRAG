# Mini Agentic RAG System with LangGraph

A production-quality agentic Retrieval-Augmented Generation (RAG) system built with Python and LangGraph, featuring graph-based knowledge retrieval, multi-step reasoning, and custom tool integration.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Features](#features)
- [Installation](#installation)
- [Usage](#usage)
- [System Components](#system-components)
- [Design Decisions](#design-decisions)
- [Limitations](#limitations)
- [Production Improvements](#production-improvements)
- [Testing](#testing)

## 🎯 Overview

This system demonstrates a sophisticated agentic RAG implementation that:

- **Ingests and processes** documents with intelligent chunking
- **Builds a knowledge graph** with entity and relation extraction
- **Implements graph-aware retrieval** with multi-hop query resolution
- **Uses LangGraph** for agent orchestration with conditional workflows
- **Provides custom tools** for lookup, summarization, calculation, and dependency analysis
- **Handles errors gracefully** with fallback strategies
- **Exposes a CLI interface** with transparent execution traces

## 🏗️ Architecture

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLI Interface                            │
│                     (User Interaction)                           │
└─────────────────────────┬───────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────────┐
│                     LangGraph Agent                              │
│  ┌──────────┐   ┌────────────┐   ┌──────────┐   ┌──────────┐  │
│  │  Router  │──▶│  Retriever │──▶│ Reasoning│──▶│   End    │  │
│  │   Node   │   │    Node    │   │   Node   │   │          │  │
│  └────┬─────┘   └──────┬─────┘   └────▲─────┘   └──────────┘  │
│       │                │               │                         │
│       │         ┌──────▼──────┐        │                         │
│       └────────▶│    Tool     │────────┘                         │
│                 │  Executor   │                                  │
│                 │    Node     │                                  │
│                 └──────┬──────┘                                  │
│                        │                                         │
│  ┌─────────────────────▼──────────────────────────────────┐    │
│  │              Error Handler Node                         │    │
│  └─────────────────────────────────────────────────────────┘    │
└─────────────────────────┬───────────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          │               │               │
          ▼               ▼               ▼
┌──────────────┐  ┌──────────────┐  ┌──────────┐
│  Knowledge   │  │   Graph      │  │  Custom  │
│    Graph     │  │  Retriever   │  │  Tools   │
└──────┬───────┘  └──────┬───────┘  └────┬─────┘
       │                 │               │
       │                 │               │
       ▼                 ▼               ▼
┌─────────────────────────────────────────────┐
│         Document Chunks + Embeddings         │
└─────────────────────────────────────────────┘
```

### Data Flow

1. **Document Ingestion** → Documents are loaded, chunked, and embedded
2. **Knowledge Graph Construction** → Entities and relations are extracted
3. **Query Processing** → Router decides on action (retrieve/tool/direct)
4. **Retrieval/Tool Execution** → Graph-aware retrieval or tool calls
5. **Reasoning** → LLM synthesizes answer from context
6. **Error Handling** → Graceful fallbacks for failures

## ✨ Features

### 1. Document Processing Pipeline

- **Multi-format support**: Markdown and text files
- **Intelligent chunking**: Recursive text splitting with configurable size/overlap
- **Metadata extraction**: Automatic title, tags, and source tracking
- **Scalable design**: Processes directories recursively

### 2. Knowledge Graph

- **Entity extraction**: NLP-based (spaCy) with pattern-based fallback
- **Relation detection**: Co-occurrence and pattern-based relations
- **Graph structure**: NetworkX-based directed graph
- **Multi-hop traversal**: Efficient neighbor and path queries
- **Persistence**: JSON serialization and GraphML export

### 3. Graph-Aware Retrieval

- **Semantic search**: Sentence transformer embeddings
- **Graph expansion**: Multi-hop entity traversal
- **Hybrid ranking**: Combines semantic + graph signals
- **Entity-based lookup**: Direct entity-to-chunk mapping
- **Path finding**: Shortest path between entities

### 4. LangGraph Agent Workflow

#### Nodes:
- **Router Node**: Analyzes query and decides action
- **Retriever Node**: Executes graph-aware retrieval
- **Tool Executor Node**: Runs custom tools
- **Reasoning Node**: Synthesizes final answer
- **Error Handler Node**: Manages failures gracefully

#### Tools:
- **lookup_facts**: Entity information lookup
- **summarize_document**: Topic-based summarization
- **run_calculation**: Knowledge graph statistics
- **analyze_dependencies**: Dependency analysis

### 5. CLI Interface

- **Interactive mode**: Real-time chat interface
- **Single-query mode**: Non-interactive execution
- **Transparent traces**: Shows steps, tools, and retrieved context
- **Commands**: /help, /history, /exit

## 🚀 Installation

### Prerequisites

- Python 3.9+
- OpenAI API key

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd "Agentic RAG"

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Unix/MacOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model (optional, for better entity extraction)
python -m spacy download en_core_web_sm

# Configure environment
cp .env.example .env
# Edit .env and add your OPENAI_API_KEY
```

### Environment Variables

```env
OPENAI_API_KEY=your_openai_api_key_here
LLM_MODEL=gpt-4-turbo-preview
EMBEDDING_MODEL=text-embedding-3-small
CHUNK_SIZE=500
CHUNK_OVERLAP=50
MAX_GRAPH_HOPS=3
```

## 📖 Usage

### Interactive Mode

```bash
python -m src.cli
```

This launches an interactive chat interface:

```
💬 You: What is AuthService?
🤔 Processing...

📝 ANSWER:
[Generated answer with sources]

🔍 EXECUTION DETAILS:
• Router Decision: retrieve
• Retrieved Chunks: 5
• Steps Executed:
  1. Router decided: retrieve
  2. Retrieved 5 relevant chunks using graph-aware retrieval
  3. Generated final answer using LLM reasoning
```

### Single Query Mode

```bash
python -m src.cli --query "Which projects depend on AuthService?"
```

### Rebuild Knowledge Graph

```bash
python -m src.cli --rebuild-graph
```

### Run Challenge Tests

```bash
python test_challenge_questions.py --verbose
```

## 🔧 System Components

### 1. Document Processor (`src/document_processor.py`)

```python
class DocumentProcessor:
    - load_documents(): Load files from directory
    - chunk_documents(): Split into chunks
    - process(): Complete pipeline
```

**Key features:**
- Recursive directory traversal
- Metadata extraction from content
- Configurable chunking strategy
- Unique chunk ID generation

### 2. Knowledge Graph (`src/knowledge_graph.py`)

```python
class KnowledgeGraph:
    - build_from_chunks(): Construct graph
    - get_neighbors(): Multi-hop neighbor retrieval
    - get_related_chunks(): Entity-to-chunk mapping
    - get_path_between_entities(): Shortest path finding
    - save()/load(): Persistence
```

**Entity types detected:**
- SERVICE: AuthService, PaymentRouter, etc.
- IDENTIFIER: CamelCase code identifiers
- ENTITY: General capitalized entities

**Relation types:**
- CO_OCCURS: Entities in same chunk
- DEPENDS_ON: Explicit dependencies
- USES, CALLS, EXTENDS, IMPLEMENTS, PART_OF

### 3. Graph-Aware Retriever (`src/retriever.py`)

```python
class GraphAwareRetriever:
    - retrieve(): Main retrieval with graph expansion
    - retrieve_by_entity(): Entity-specific lookup
    - multi_hop_query(): Path-based retrieval
```

**Retrieval strategies:**
1. **Semantic search**: Embedding similarity
2. **Graph expansion**: Multi-hop entity traversal
3. **Hybrid ranking**: Weighted combination

**Scoring formula:**
```
final_score = semantic_score * hop_penalty
hop_penalty = 1.0 / (1.0 + hop_count * 0.3)
```

### 4. Custom Tools (`src/tools.py`)

#### LookupTool
- Retrieves entity facts from knowledge graph
- Returns: type, mentions, relations, neighbors, relevant chunks

#### SummarizeTool
- LLM-powered summarization of topic-related documents
- Uses retriever for context gathering

#### CalculationTool
- Knowledge graph statistics
- Supports: count entities, count relations, average mentions

#### DependencyAnalysisTool
- Analyzes entity dependencies
- Returns: depends_on, depended_by, criticality assessment

### 5. LangGraph Agent (`src/agent.py`)

```python
class AgenticRAG:
    - router_node(): Query classification
    - retriever_node(): Graph-aware retrieval
    - tool_executor_node(): Tool execution
    - reasoning_node(): Answer synthesis
    - error_handler_node(): Error recovery
    - run(): Execute workflow
```

**State management:**
```python
class AgentState(TypedDict):
    query: str
    router_decision: str
    retrieved_context: List[RetrievalResult]
    tool_calls: List[Dict]
    tool_results: List[ToolResult]
    answer: str
    steps_executed: List[str]
    error: Optional[str]
```

## 🎨 Design Decisions

### 1. Knowledge Graph Choice

**Decision**: NetworkX + custom entity extraction

**Rationale:**
- Lightweight and flexible
- No external graph database required
- Full control over entity/relation extraction
- Easy to persist and version control

**Trade-offs:**
- Less sophisticated than commercial solutions
- Limited to in-memory graphs
- Manual entity resolution

### 2. LangGraph Over LangChain Agents

**Decision**: Use LangGraph for agent orchestration

**Rationale:**
- Explicit graph-based workflows
- Better control over execution flow
- Easier debugging and observability
- Native support for conditional routing

**Trade-offs:**
- More verbose than LangChain agents
- Requires explicit state management
- Steeper learning curve

### 3. Hybrid Retrieval Strategy

**Decision**: Combine semantic + graph-based retrieval

**Rationale:**
- Semantic search catches relevant content
- Graph expansion enables multi-hop reasoning
- Hybrid ranking balances both signals

**Trade-offs:**
- More complex than pure vector search
- Requires graph construction overhead
- Parameter tuning needed (hop penalty, weights)

### 4. Sentence Transformers for Embeddings

**Decision**: Use sentence-transformers instead of OpenAI embeddings

**Rationale:**
- Local execution (no API calls)
- Faster for repeated queries
- Cost-effective
- Privacy-preserving

**Trade-offs:**
- Lower quality than OpenAI embeddings
- Larger model size
- GPU acceleration needed for large corpora

### 5. Tool Design

**Decision**: Simple function-based tools over complex frameworks

**Rationale:**
- Easy to understand and extend
- Minimal dependencies
- Clear input/output contracts
- Testable in isolation

**Trade-offs:**
- Less sophisticated than LangChain tools
- Manual tool selection logic
- No automatic tool chaining

## ⚠️ Limitations

### Current Limitations

1. **Entity Extraction Quality**
   - Pattern-based fallback is simplistic
   - May miss domain-specific entities
   - No entity disambiguation

2. **Graph Construction**
   - Co-occurrence relations can be noisy
   - Limited relation types
   - No temporal or hierarchical relations

3. **Scalability**
   - In-memory graph (limited to ~100K entities)
   - No distributed retrieval
   - Sequential chunk processing

4. **Tool Limitations**
   - Fixed tool set (no dynamic tool creation)
   - Simple tool selection (no learned routing)
   - No tool composition or chaining

5. **Memory**
   - No persistent conversation memory
   - No user preference learning
   - Limited context window handling

6. **Error Handling**
   - Single retry strategy
   - No circuit breaker for external APIs
   - Limited observability

## 🚀 Production Improvements

### High Priority

1. **Scalability**
   ```
   - Use vector databases (Pinecone, Weaviate, Qdrant)
   - Implement graph databases (Neo4j, Amazon Neptune)
   - Add async processing with Celery/RQ
   - Shard embeddings for large corpora
   ```

2. **Quality Improvements**
   ```
   - Fine-tune entity extraction for domain
   - Implement entity linking/disambiguation
   - Add relation extraction models
   - Use better embeddings (OpenAI, Cohere)
   ```

3. **Observability**
   ```
   - Add structured logging (JSON logs)
   - Implement tracing (OpenTelemetry)
   - Add metrics (Prometheus)
   - Create monitoring dashboards
   ```

4. **Error Handling**
   ```
   - Implement circuit breakers
   - Add exponential backoff
   - Create fallback strategies per node
   - Add dead letter queues
   ```

### Medium Priority

5. **Memory & Context**
   ```
   - Persistent conversation memory (Redis/PostgreSQL)
   - User profile management
   - Session-based context tracking
   - Long-term memory summarization
   ```

6. **Tool Ecosystem**
   ```
   - Dynamic tool loading
   - Tool marketplace/registry
   - Learned tool routing
   - Tool composition framework
   ```

7. **Advanced Retrieval**
   ```
   - Query expansion/rewriting
   - Re-ranking models
   - Contextual embeddings
   - Multi-modal retrieval
   ```

8. **Security**
   ```
   - API key rotation
   - Rate limiting
   - Input sanitization
   - PII detection and masking
   ```

### Low Priority

9. **User Experience**
   ```
   - Web UI with streaming responses
   - Multi-language support
   - Voice interface
   - Mobile app
   ```

10. **Testing & CI/CD**
    ```
    - Comprehensive unit tests (>80% coverage)
    - Integration tests with test fixtures
    - Performance benchmarks
    - Automated deployment pipeline
    ```

11. **Documentation**
    ```
    - API documentation (OpenAPI/Swagger)
    - Architecture decision records (ADRs)
    - Runbooks for operations
    - Tutorial notebooks
    ```

### Architectural Improvements

```
┌─────────────────────────────────────────────────────────────┐
│                     Production Architecture                  │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────┐      ┌──────────┐      ┌──────────┐          │
│  │   API    │◀────▶│  Cache   │◀────▶│  Queue   │          │
│  │ Gateway  │      │  (Redis) │      │ (RabbitMQ)│          │
│  └────┬─────┘      └──────────┘      └─────┬────┘          │
│       │                                      │               │
│       ▼                                      ▼               │
│  ┌──────────────────────┐         ┌──────────────┐         │
│  │   Agent Service      │────────▶│   Vector DB  │         │
│  │   (Kubernetes)       │         │  (Pinecone)  │         │
│  └──────────┬───────────┘         └──────────────┘         │
│             │                                                │
│             ▼                                                │
│  ┌──────────────────────┐         ┌──────────────┐         │
│  │   Graph Database     │◀───────▶│   Monitoring │         │
│  │     (Neo4j)          │         │ (Prometheus) │         │
│  └──────────────────────┘         └──────────────┘         │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## 🧪 Testing

### Challenge Questions

The system is tested against these challenge scenarios:

1. **Multi-hop Query**
   - "Which projects mentioned in the documents depend on AuthService?"
   - Tests: Graph traversal, entity resolution

2. **Reasoning + Tool Use**
   - "Summarize all documents related to the authentication subsystem and calculate how many services depend on it"
   - Tests: Tool composition, summarization, calculation

3. **Error Handling**
   - "Find details about the module called PaymentRouter"
   - Tests: Normal retrieval path

4. **Dependency Analysis**
   - "What services does PaymentRouter depend on?"
   - Tests: Relation extraction, dependency tool

5. **Complex Multi-hop**
   - "Which project uses PaymentRouter and what authentication system does it use?"
   - Tests: Multi-step reasoning, graph paths

### Run Tests

```bash
# Run all challenge questions
python test_challenge_questions.py

# Save results to JSON
python test_challenge_questions.py --save-results results.json
```

### Expected Output

```
🧪 CHALLENGE QUESTIONS TEST SUITE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Test #1: Multi-hop Query
✅ PASSED - Found 3/3 expected elements

Test #2: Reasoning + Tool Use
✅ PASSED - Tools used successfully

...

📊 TEST SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Total Tests: 5
Passed: 5 ✅
Failed: 0 ❌
Success Rate: 100.0%
```

## 📁 Project Structure

```
Agentic RAG/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration management
│   ├── document_processor.py  # Document ingestion & chunking
│   ├── knowledge_graph.py     # Graph construction & management
│   ├── retriever.py           # Graph-aware retrieval
│   ├── tools.py               # Custom tools
│   ├── agent.py               # LangGraph agent
│   └── cli.py                 # CLI interface
├── data/                      # Sample documents
│   ├── authentication_service.md
│   ├── payment_router.md
│   ├── database_service.md
│   ├── project_alpha.md
│   ├── project_beta.md
│   ├── analytics_module.md
│   ├── notification_service.md
│   └── inventory_service.md
├── graph/                     # Knowledge graph artifacts (generated)
│   ├── entities.json
│   ├── relations.json
│   └── knowledge_graph.graphml
├── tests/                     # Test suite
├── test_challenge_questions.py
├── requirements.txt
├── .env.example
└── README.md
```

## 🤝 Contributing

This is a take-home assignment demo. For production use, please see the "Production Improvements" section.

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- LangGraph for agent orchestration
- LangChain for LLM integration
- sentence-transformers for embeddings
- NetworkX for graph operations
- spaCy for NLP

---

**Built with ❤️ for demonstrating production-quality agentic RAG systems**
