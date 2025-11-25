# Architecture Documentation

Detailed technical architecture of the Mini Agentic RAG System.

## Table of Contents

1. [System Overview](#system-overview)
2. [Component Architecture](#component-architecture)
3. [Data Flow](#data-flow)
4. [LangGraph Workflow](#langgraph-workflow)
5. [Knowledge Graph Design](#knowledge-graph-design)
6. [Retrieval Strategy](#retrieval-strategy)
7. [Tool System](#tool-system)
8. [State Management](#state-management)
9. [Error Handling](#error-handling)
10. [Performance Considerations](#performance-considerations)

---

## System Overview

The system implements a **graph-based agentic RAG** architecture with the following key characteristics:

- **Modular Design**: Clear separation of concerns between components
- **Graph-Aware**: Knowledge graph enhances retrieval beyond pure semantic search
- **Agent-Driven**: LangGraph orchestrates multi-step reasoning workflows
- **Tool-Augmented**: Custom tools extend agent capabilities
- **Production-Ready**: Error handling, logging, and transparent execution traces

### Technology Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| LLM | OpenAI GPT-4 | Reasoning and generation |
| Embeddings | sentence-transformers | Local semantic search |
| Graph | NetworkX | Knowledge graph management |
| NLP | spaCy | Entity extraction |
| Orchestration | LangGraph | Agent workflow |
| Framework | LangChain | LLM integration |

---

## Component Architecture

### 1. Document Processor

**Location**: `src/document_processor.py`

```
┌─────────────────────────────────────┐
│      Document Processor             │
├─────────────────────────────────────┤
│                                     │
│  Load Documents                     │
│    │                                │
│    ├─ Recursive directory scan     │
│    ├─ Filter .md and .txt          │
│    └─ Extract metadata             │
│                                     │
│  Chunk Documents                    │
│    │                                │
│    ├─ RecursiveCharacterTextSplitter│
│    ├─ Configurable size/overlap    │
│    └─ Generate unique chunk IDs    │
│                                     │
│  Output: List[Chunk]                │
│    ├─ content                       │
│    ├─ metadata                      │
│    ├─ chunk_id                      │
│    └─ embedding (added later)      │
│                                     │
└─────────────────────────────────────┘
```

**Key Design Decisions:**

1. **Recursive Chunking**: Uses hierarchical separators (`\n\n` → `\n` → `. ` → ` `)
   - Preserves semantic boundaries
   - Maintains context continuity

2. **Metadata Extraction**: Parses markdown headers and tags
   - Title from first `# Header`
   - Tags from `tags: tag1, tag2` lines
   - Source file tracking

3. **Chunk IDs**: MD5 hash of content + source
   - Deterministic and unique
   - Enables deduplication

### 2. Knowledge Graph

**Location**: `src/knowledge_graph.py`

```
┌─────────────────────────────────────────────────────────────┐
│                    Knowledge Graph                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Entity Extraction                                          │
│    │                                                         │
│    ├─ spaCy NER (if available)                             │
│    │   └─ Extracts: PERSON, ORG, PRODUCT, GPE, etc.       │
│    │                                                         │
│    └─ Pattern-based fallback                               │
│        ├─ Capitalized words (proper nouns)                 │
│        ├─ CamelCase identifiers                            │
│        └─ Service patterns (*Service, *Router, etc.)       │
│                                                             │
│  Relation Extraction                                        │
│    │                                                         │
│    ├─ Co-occurrence (entities in same chunk)               │
│    │   └─ Weight: 1.0                                      │
│    │                                                         │
│    └─ Pattern-based                                        │
│        ├─ "X depends on Y" → DEPENDS_ON                    │
│        ├─ "X uses Y" → USES                                │
│        ├─ "X calls Y" → CALLS                              │
│        └─ Weight: 2.0 (explicit > co-occurrence)          │
│                                                             │
│  Graph Construction                                         │
│    │                                                         │
│    └─ NetworkX DiGraph                                     │
│        ├─ Nodes: Entities with metadata                    │
│        ├─ Edges: Relations with weights                    │
│        └─ Algorithms: shortest_path, neighbors             │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Graph Schema:**

```python
Node = {
    "name": str,              # Entity name
    "entity_type": str,       # SERVICE, IDENTIFIER, ENTITY
    "mentions": int,          # Frequency across corpus
    "chunks": List[str],      # Chunk IDs where entity appears
}

Edge = {
    "source": str,            # Source entity
    "target": str,            # Target entity
    "relation_type": str,     # DEPENDS_ON, USES, CALLS, etc.
    "weight": float,          # Relation strength
}
```

**Design Rationale:**

1. **Frequency Filtering**: `min_entity_freq=2`
   - Reduces noise from one-off mentions
   - Focuses on significant entities

2. **Hybrid Extraction**: spaCy + patterns
   - spaCy for general entities
   - Patterns for technical/domain terms

3. **Weighted Relations**: Explicit > implicit
   - Pattern-matched: 2.0
   - Co-occurrence: 1.0

### 3. Graph-Aware Retriever

**Location**: `src/retriever.py`

```
┌─────────────────────────────────────────────────────────────┐
│                  Graph-Aware Retriever                       │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  retrieve(query, use_graph=True, top_k=5)                  │
│    │                                                         │
│    ├─ Step 1: Semantic Search                              │
│    │   ├─ Encode query with sentence-transformer           │
│    │   ├─ Compute cosine similarity with all chunks        │
│    │   └─ Get top 2*top_k candidates                       │
│    │                                                         │
│    ├─ Step 2: Extract Query Entities                       │
│    │   └─ Find known entities in query text                │
│    │                                                         │
│    ├─ Step 3: Graph Expansion (if use_graph=True)          │
│    │   ├─ For each query entity:                           │
│    │   │   ├─ Get direct chunks (hop 0)                    │
│    │   │   └─ Get neighbor chunks (hop 1, 2, ...)          │
│    │   │                                                     │
│    │   ├─ Score chunks:                                     │
│    │   │   semantic_score * hop_penalty                     │
│    │   │   where hop_penalty = 1/(1 + hop_count * 0.3)     │
│    │   │                                                     │
│    │   └─ Track related entities per chunk                 │
│    │                                                         │
│    └─ Step 4: Combine & Re-rank                            │
│        ├─ Merge semantic + graph results                   │
│        ├─ For overlapping chunks:                          │
│        │   combined_score = 0.5*semantic + 0.5*graph       │
│        └─ Sort by final score, return top_k                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Retrieval Algorithm:**

```python
def retrieve(query):
    # 1. Semantic search
    query_emb = embed(query)
    semantic_results = cosine_similarity(query_emb, chunk_embeddings)

    # 2. Graph expansion
    query_entities = extract_entities(query)
    graph_results = []

    for entity in query_entities:
        for hop in range(max_hops + 1):
            chunks = get_chunks_at_hop(entity, hop)
            for chunk in chunks:
                score = cosine_similarity(query_emb, chunk.embedding)
                score *= (1.0 / (1.0 + hop * 0.3))  # Hop penalty
                graph_results.append((chunk, score, hop))

    # 3. Hybrid fusion
    combined = merge_by_chunk_id(semantic_results, graph_results)
    combined = weighted_average(combined, weights=[0.5, 0.5])

    return sorted(combined, reverse=True)[:top_k]
```

**Why This Approach?**

1. **Semantic First**: Catches relevant content regardless of entity mentions
2. **Graph Enhancement**: Adds context from related entities
3. **Hop Penalty**: Prioritizes closer relationships
4. **Hybrid Fusion**: Balances both signals

### 4. LangGraph Agent

**Location**: `src/agent.py`

```
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                        │
└─────────────────────────────────────────────────────────────┘

                        ┌─────────┐
                        │  START  │
                        └────┬────┘
                             │
                             ▼
                      ┌──────────────┐
                      │    Router    │
                      │     Node     │
                      └──────┬───────┘
                             │
          ┌──────────────────┼──────────────────┐
          │                  │                  │
          ▼                  ▼                  ▼
    ┌──────────┐      ┌──────────┐      ┌──────────┐
    │ Retrieve │      │   Tool   │      │  Direct  │
    │   Node   │      │ Executor │      │  Answer  │
    └────┬─────┘      └────┬─────┘      └────┬─────┘
         │                 │                  │
         └────────┬────────┴──────────────────┘
                  │
                  ▼
           ┌──────────────┐
           │  Reasoning   │
           │     Node     │
           └──────┬───────┘
                  │
                  ▼
              ┌───────┐
              │  END  │
              └───────┘

         ┌──────────────┐
         │    Error     │
         │   Handler    │
         └──────────────┘
              (parallel)
```

**Node Responsibilities:**

| Node | Input | Output | Side Effects |
|------|-------|--------|--------------|
| Router | query | router_decision, tool_calls | Analyzes query intent |
| Retriever | query | retrieved_context | Searches knowledge base |
| Tool Executor | tool_calls | tool_results | Runs tools |
| Reasoning | context, tool_results | answer | Generates response |
| Error Handler | error | fallback_answer | Graceful degradation |

**State Flow:**

```python
class AgentState(TypedDict):
    # Input
    query: str

    # Routing
    router_decision: str  # "retrieve", "tool", "direct_answer"

    # Retrieval
    retrieved_context: List[RetrievalResult]

    # Tools
    tool_calls: List[Dict]
    tool_results: List[ToolResult]

    # Output
    answer: str
    steps_executed: List[str]
    error: Optional[str]
```

### 5. Tool System

**Location**: `src/tools.py`

```
┌─────────────────────────────────────────────────────────────┐
│                        Tool System                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  LookupTool                                                 │
│    └─ lookup_facts(entity_name) → EntityFacts              │
│        ├─ Entity metadata                                   │
│        ├─ Relations                                         │
│        ├─ Neighbors                                         │
│        └─ Relevant chunks                                   │
│                                                             │
│  SummarizeTool                                              │
│    └─ summarize_document(topic) → Summary                  │
│        ├─ Retrieve relevant chunks                         │
│        ├─ LLM summarization                                │
│        └─ Source citations                                 │
│                                                             │
│  CalculationTool                                            │
│    └─ run_calculation(query) → Calculation                 │
│        ├─ Count entities (total, by type)                  │
│        ├─ Count relations                                   │
│        └─ Average mentions                                  │
│                                                             │
│  DependencyAnalysisTool                                     │
│    └─ analyze_dependencies(entity) → DependencyGraph       │
│        ├─ Outgoing dependencies (depends_on)               │
│        ├─ Incoming dependencies (depended_by)              │
│        └─ Criticality assessment                           │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

**Tool Result Format:**

```python
@dataclass
class ToolResult:
    tool_name: str
    success: bool
    result: Any
    error: Optional[str] = None
```

**Tool Selection Logic:**

The router node uses LLM to analyze the query and determine:
1. Whether a tool is needed
2. Which tool to use
3. What parameters to pass

Example router prompt:
```
Query: "How many services depend on AuthService?"

Analysis:
- Requires calculation → use CalculationTool
- Needs dependency info → might use DependencyAnalysisTool
- Entity: "AuthService"

Action: tool
Tool: run_calculation
```

---

## Data Flow

### End-to-End Query Flow

```
User Query: "Which projects depend on AuthService?"
    │
    ▼
┌─────────────────────────────────────┐
│ 1. Router Node                      │
│    - Analyzes query                 │
│    - Decision: "retrieve"           │
│    - Detects entity: "AuthService"  │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 2. Retriever Node                   │
│    - Semantic search for query      │
│    - Find "AuthService" in KG       │
│    - Get related entities/chunks    │
│    - Multi-hop expansion            │
│    - Return top 5 chunks            │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 3. Reasoning Node                   │
│    - Context: 5 chunks              │
│    - Entities: ProjectAlpha, etc.   │
│    - LLM synthesis                  │
│    - Generate answer with citations │
└────────────┬────────────────────────┘
             │
             ▼
┌─────────────────────────────────────┐
│ 4. Output                           │
│    Answer: "ProjectAlpha,           │
│     ProjectBeta, and ProjectGamma   │
│     depend on AuthService..."       │
│                                     │
│    Steps:                           │
│    1. Router decided: retrieve      │
│    2. Retrieved 5 chunks            │
│    3. Generated answer              │
└─────────────────────────────────────┘
```

---

## Performance Considerations

### Bottlenecks

1. **Embedding Generation**: O(n) for n chunks
   - Solution: Cache embeddings, incremental updates

2. **Graph Traversal**: O(k^d) for k neighbors, d hops
   - Solution: Limit hops (default: 2), prune low-weight edges

3. **LLM Calls**: Network latency + generation time
   - Solution: Streaming responses, caching common queries

### Optimizations

1. **Embedding Caching**: Embeddings stored with chunks
2. **Graph Pruning**: Min entity frequency filter
3. **Result Caching**: Redis for repeated queries (future)
4. **Batch Processing**: Vectorized similarity calculations

### Scalability Limits

| Component | Current | Recommended Max |
|-----------|---------|-----------------|
| Documents | 10-50 | 1,000 |
| Chunks | 100-500 | 10,000 |
| Entities | 50-200 | 5,000 |
| Relations | 100-500 | 20,000 |

For larger scale, see [Production Improvements](README.md#production-improvements).

---

## Error Handling Strategy

### Error Categories

1. **External API Errors**: OpenAI rate limits, timeouts
2. **Data Errors**: Missing entities, empty results
3. **Logic Errors**: Invalid tool parameters
4. **System Errors**: OOM, file not found

### Handling Approach

```python
try:
    # Normal flow
    result = operation()
except APIError as e:
    # Retry with backoff
    result = retry_with_backoff(operation)
except DataError as e:
    # Fallback to alternative method
    result = fallback_method()
except Exception as e:
    # Error handler node
    result = error_handler.handle(e)
```

### Graceful Degradation

1. **spaCy unavailable** → Pattern-based extraction
2. **Retrieval fails** → Direct LLM answer
3. **Tool fails** → Continue without tool result
4. **LLM fails** → Return error with context

---

## Future Architecture Evolution

### Phase 1: Current (MVP)
- In-memory graph
- Local embeddings
- Single-node deployment

### Phase 2: Scale (100K docs)
- Vector database (Pinecone/Weaviate)
- Graph database (Neo4j)
- Distributed retrieval

### Phase 3: Production (1M+ docs)
- Microservices architecture
- Streaming ingestion
- Real-time updates
- Multi-tenant support

---

## References

- [LangGraph Documentation](https://python.langchain.com/docs/langgraph)
- [NetworkX Documentation](https://networkx.org/)
- [sentence-transformers](https://www.sbert.net/)
- [spaCy NER](https://spacy.io/usage/linguistic-features#named-entities)
