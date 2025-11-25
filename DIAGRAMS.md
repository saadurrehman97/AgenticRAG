# System Diagrams

Visual representations of the Mini Agentic RAG System architecture.

## High-Level System Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│                         USER INTERFACE                             │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │                      CLI (cli.py)                         │    │
│  │  • Interactive mode                                       │    │
│  │  • Single query mode                                      │    │
│  │  • Execution trace display                               │    │
│  └────────────────────┬─────────────────────────────────────┘    │
│                       │                                            │
└───────────────────────┼────────────────────────────────────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│                      AGENT ORCHESTRATION                           │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────┐    │
│  │              LangGraph Agent (agent.py)                   │    │
│  │                                                            │    │
│  │   ┌────────┐   ┌───────────┐   ┌──────────┐   ┌───────┐ │    │
│  │   │Router  │──▶│ Retriever │──▶│Reasoning │──▶│ Output│ │    │
│  │   │  Node  │   │    Node   │   │   Node   │   │       │ │    │
│  │   └───┬────┘   └─────┬─────┘   └────▲─────┘   └───────┘ │    │
│  │       │              │               │                     │    │
│  │       │       ┌──────▼──────┐        │                     │    │
│  │       └──────▶│Tool Executor│────────┘                     │    │
│  │               │    Node     │                              │    │
│  │               └─────────────┘                              │    │
│  │                                                            │    │
│  │   State: Query → Decision → Context → Tools → Answer     │    │
│  └────────────────────┬───────────────────────────────────────┘    │
│                       │                                            │
└───────────────────────┼────────────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┬──────────────┐
        │               │               │              │
        ▼               ▼               ▼              ▼
┌──────────────┐ ┌─────────────┐ ┌──────────┐ ┌──────────────┐
│              │ │             │ │          │ │              │
│  RETRIEVAL   │ │    GRAPH    │ │  TOOLS   │ │  PROCESSING  │
│              │ │             │ │          │ │              │
├──────────────┤ ├─────────────┤ ├──────────┤ ├──────────────┤
│              │ │             │ │          │ │              │
│ Retriever    │ │ Knowledge   │ │ Lookup   │ │ Document     │
│ (retriever   │ │ Graph       │ │ Summary  │ │ Processor    │
│  .py)        │ │ (knowledge_ │ │ Calc     │ │ (document_   │
│              │ │  graph.py)  │ │ Depend   │ │  processor   │
│ • Semantic   │ │             │ │ (tools   │ │  .py)        │
│   Search     │ │ • Entities  │ │  .py)    │ │              │
│ • Graph      │ │ • Relations │ │          │ │ • Load docs  │
│   Expansion  │ │ • NetworkX  │ │ • 4 tools│ │ • Chunk      │
│ • Hybrid     │ │   Graph     │ │ • Tool   │ │ • Metadata   │
│   Ranking    │ │ • Multi-hop │ │   Results│ │              │
│              │ │   Traversal │ │          │ │              │
└──────┬───────┘ └──────┬──────┘ └────┬─────┘ └──────┬───────┘
       │                │              │              │
       └────────────────┴──────────────┴──────────────┘
                        │
                        ▼
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│                        DATA LAYER                                  │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │
│  │  Documents   │  │   Chunks +   │  │   Graph      │           │
│  │   (data/)    │─▶│  Embeddings  │─▶│  Artifacts   │           │
│  │              │  │              │  │  (graph/)    │           │
│  │ • .md files  │  │ • Content    │  │ • entities   │           │
│  │ • .txt files │  │ • Vectors    │  │ • relations  │           │
│  │              │  │ • Metadata   │  │ • .graphml   │           │
│  └──────────────┘  └──────────────┘  └──────────────┘           │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

## LangGraph Workflow Detail

```
┌─────────────────────────────────────────────────────────────────┐
│                    LangGraph State Machine                       │
└─────────────────────────────────────────────────────────────────┘

                            START
                              │
                              ▼
                    ┌──────────────────┐
                    │   ROUTER NODE    │
                    │                  │
                    │ Analyzes:        │
                    │ • Query intent   │
                    │ • Entity presence│
                    │ • Tool needs     │
                    │                  │
                    │ LLM Decision:    │
                    │ "retrieve" |     │
                    │ "tool" |         │
                    │ "direct_answer"  │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼──────────────────┐
         │                   │                  │
         │ "retrieve"        │ "tool"           │ "direct_answer"
         │                   │                  │
         ▼                   ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌──────────────┐
│ RETRIEVER NODE  │ │ TOOL EXECUTOR   │ │   (skip)     │
│                 │ │      NODE       │ │              │
│ 1. Semantic     │ │                 │ └──────┬───────┘
│    Search       │ │ For each tool:  │        │
│                 │ │ 1. Parse params │        │
│ 2. Extract      │ │ 2. Execute tool │        │
│    Query        │ │ 3. Collect      │        │
│    Entities     │ │    results      │        │
│                 │ │                 │        │
│ 3. Graph        │ │ Tools:          │        │
│    Expansion    │ │ • lookup_facts  │        │
│    (multi-hop)  │ │ • summarize     │        │
│                 │ │ • calculate     │        │
│ 4. Combine &    │ │ • analyze_deps  │        │
│    Re-rank      │ │                 │        │
│                 │ │ Output:         │        │
│ Output:         │ │ ToolResult[]    │        │
│ RetrievalResult │ │                 │        │
│   []            │ │                 │        │
└────────┬────────┘ └────────┬────────┘        │
         │                   │                 │
         └───────────────────┼─────────────────┘
                             │
                             ▼
                  ┌────────────────────┐
                  │   REASONING NODE   │
                  │                    │
                  │ Inputs:            │
                  │ • retrieved_context│
                  │ • tool_results     │
                  │ • query            │
                  │                    │
                  │ Process:           │
                  │ 1. Format context  │
                  │ 2. Build prompt    │
                  │ 3. LLM generation  │
                  │ 4. Add citations   │
                  │                    │
                  │ Output:            │
                  │ • answer (str)     │
                  │ • steps_executed   │
                  └──────────┬─────────┘
                             │
                             ▼
                           END

         ┌────────────────────────┐
         │   ERROR HANDLER NODE   │ (parallel, on error)
         │                        │
         │ Catches:               │
         │ • API errors           │
         │ • Empty results        │
         │ • Tool failures        │
         │                        │
         │ Provides:              │
         │ • Fallback response    │
         │ • Error context        │
         │ • Suggestions          │
         └────────────────────────┘
```

## Retrieval Process Flow

```
┌─────────────────────────────────────────────────────────────────┐
│              Graph-Aware Retrieval Process                       │
└─────────────────────────────────────────────────────────────────┘

Query: "Which projects depend on AuthService?"
   │
   ▼
┌──────────────────────────────────┐
│ STEP 1: SEMANTIC SEARCH          │
│                                  │
│ query_embedding = embed(query)   │
│                                  │
│ For each chunk:                  │
│   similarity = cosine(           │
│     query_embedding,             │
│     chunk.embedding              │
│   )                              │
│                                  │
│ Sort by similarity               │
│ Take top 10 candidates           │
│                                  │
│ Results: [Chunk1, Chunk2, ...]  │
│   Scores: [0.82, 0.79, ...]     │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ STEP 2: ENTITY EXTRACTION        │
│                                  │
│ entities = []                    │
│                                  │
│ For each known_entity in KG:    │
│   if known_entity in query:     │
│     entities.append(known_entity)│
│                                  │
│ Extracted: ["AuthService"]      │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ STEP 3: GRAPH EXPANSION          │
│                                  │
│ For entity "AuthService":        │
│                                  │
│   Hop 0 (Direct):                │
│   ├─ chunks: [C1, C2, C3]       │
│   │  from: entity.chunks         │
│   │  penalty: 1.0                │
│   │                              │
│   Hop 1 (Neighbors):             │
│   ├─ neighbors: [ProjectAlpha,  │
│   │              ProjectBeta]    │
│   ├─ chunks: [C4, C5, C6]       │
│   │  penalty: 0.77               │
│   │                              │
│   Hop 2 (2nd degree):            │
│   ├─ neighbors: [DatabaseService]│
│   ├─ chunks: [C7, C8]           │
│   │  penalty: 0.63               │
│                                  │
│ Graph Results:                   │
│   [(C1, 0.85*1.0, hop=0),       │
│    (C4, 0.78*0.77, hop=1),      │
│    ...]                          │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ STEP 4: HYBRID FUSION            │
│                                  │
│ Combine results by chunk_id:     │
│                                  │
│ C1: in both                      │
│   semantic: 0.82                 │
│   graph: 0.85                    │
│   final: 0.5*0.82 + 0.5*0.85    │
│        = 0.835                   │
│                                  │
│ C4: graph only                   │
│   final: 0.78*0.77 = 0.60       │
│                                  │
│ Sort by final score              │
│ Return top 5 chunks              │
│                                  │
│ Output:                          │
│   [RetrievalResult(chunk=C1,    │
│      score=0.835,                │
│      method="hybrid",            │
│      related_entities=[          │
│        "AuthService",            │
│        "ProjectAlpha"            │
│      ]),                         │
│    ...]                          │
└──────────────────────────────────┘
```

## Knowledge Graph Structure

```
┌─────────────────────────────────────────────────────────────────┐
│                      Knowledge Graph Example                     │
└─────────────────────────────────────────────────────────────────┘

Legend:
  ●  Entity (node)
  ──▶ Relation (directed edge)
  [TYPE] Relation type
  (N) Mention count


                      ┌──────────────┐
                      │ DatabaseSvc  │(15)
                      │ [SERVICE]    │
                      └───────┬──────┘
                              │
                [USES]        │
                              │
         ┌────────────────────┼────────────────────┐
         │                    │                    │
         ▼                    ▼                    ▼
  ┌──────────┐         ┌──────────┐        ┌──────────┐
  │AuthSvc   │(12)     │PaymentRtr│(8)     │Inventory │(6)
  │[SERVICE] │         │[SERVICE] │        │Svc       │
  └────┬─────┘         └────┬─────┘        │[SERVICE] │
       │                    │               └────┬─────┘
       │[DEPENDS_ON]        │[DEPENDS_ON]        │
       │                    │                    │
       │              ┌─────┴─────┐              │
       │              │           │              │
       ▼              ▼           ▼              ▼
  ┌──────────┐  ┌──────────┐ ┌──────────┐  ┌──────────┐
  │Project   │  │Project   │ │Checkout  │  │Search    │
  │Alpha(10) │  │Beta(7)   │ │Svc(5)    │  │Svc(4)    │
  │[PROJECT] │  │[PROJECT] │ │[SERVICE] │  │[SERVICE] │
  └────┬─────┘  └──────────┘ └────┬─────┘  └──────────┘
       │                          │
       │[USES]                    │[USES]
       │                          │
       └──────────┬───────────────┘
                  │
                  ▼
           ┌──────────────┐
           │NotificationSvc│(9)
           │[SERVICE]      │
           └───────────────┘


Example Entity Object:
{
  "name": "AuthService",
  "entity_type": "SERVICE",
  "mentions": 12,
  "chunks": ["auth_001", "proj_alpha_003", "proj_beta_002"]
}

Example Relation Object:
{
  "source": "ProjectAlpha",
  "target": "AuthService",
  "relation_type": "DEPENDS_ON",
  "weight": 2.0
}
```

## Tool Execution Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    Tool Execution Process                        │
└─────────────────────────────────────────────────────────────────┘

Query: "How many services depend on AuthService?"
   │
   ▼
┌──────────────────────────────────┐
│ ROUTER NODE                      │
│                                  │
│ LLM Analysis:                    │
│ "This requires calculation and   │
│  dependency analysis"            │
│                                  │
│ Decision:                        │
│   action: "tool"                 │
│   tool: "run_calculation"        │
│   params: query text             │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ TOOL EXECUTOR NODE               │
│                                  │
│ 1. Parse tool request            │
│    tool_name: "run_calculation"  │
│    query: "How many services..." │
│                                  │
│ 2. Extract parameters            │
│    entity: "AuthService"         │
│    operation: "count dependencies│
│                                  │
│ 3. Execute tool                  │
│    CalculationTool.run(...)      │
│                                  │
│ 4. Handle result                 │
│    if success:                   │
│      store result                │
│    else:                         │
│      store error                 │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ CALCULATION TOOL                 │
│                                  │
│ Pattern matching:                │
│   "count" + "dependencies"       │
│   → count_entity_relations()     │
│                                  │
│ Graph query:                     │
│   relations = [                  │
│     r for r in KG.relations      │
│     if (r.source == "AuthService"│
│         or r.target == "...")    │
│   ]                              │
│                                  │
│ Result:                          │
│   {                              │
│     "calculation": "count_deps", │
│     "entity": "AuthService",     │
│     "value": 4,                  │
│     "description": "4 services   │
│       depend on AuthService"     │
│   }                              │
└────────────┬─────────────────────┘
             │
             ▼
┌──────────────────────────────────┐
│ REASONING NODE                   │
│                                  │
│ Context:                         │
│   tool_results: [{...}]          │
│                                  │
│ Prompt:                          │
│   "Based on tool results:        │
│    {tool_results}                │
│    Answer: {query}"              │
│                                  │
│ LLM Response:                    │
│   "According to the calculation, │
│    4 services depend on          │
│    AuthService: ProjectAlpha,    │
│    ProjectBeta, ProjectGamma,    │
│    and AnalyticsModule."         │
└──────────────────────────────────┘
```

## Data Model

```
┌─────────────────────────────────────────────────────────────────┐
│                        Core Data Models                          │
└─────────────────────────────────────────────────────────────────┘

Chunk
├── content: str
├── metadata: Dict
│   ├── source: str
│   ├── title: str
│   ├── tags: List[str]
│   ├── chunk_index: int
│   └── total_chunks: int
├── chunk_id: str (MD5 hash)
└── embedding: List[float] (384-dim vector)

Entity
├── name: str
├── entity_type: str (SERVICE | IDENTIFIER | ENTITY)
├── mentions: int
├── chunks: Set[str] (chunk IDs)
└── metadata: Dict

Relation
├── source: str (entity name)
├── target: str (entity name)
├── relation_type: str
│   ├── CO_OCCURS
│   ├── DEPENDS_ON
│   ├── USES
│   ├── CALLS
│   ├── EXTENDS
│   ├── IMPLEMENTS
│   └── PART_OF
├── weight: float
└── context: List[str] (text snippets)

RetrievalResult
├── chunk: Chunk
├── score: float (0.0 - 1.0)
├── retrieval_method: str
│   ├── "semantic"
│   ├── "graph"
│   └── "hybrid"
├── hop_count: int (0, 1, 2, ...)
└── related_entities: List[str]

ToolResult
├── tool_name: str
├── success: bool
├── result: Any (tool-specific)
└── error: Optional[str]

AgentState (LangGraph)
├── query: str
├── messages: List
├── router_decision: str
├── retrieved_context: List[RetrievalResult]
├── tool_calls: List[Dict]
├── tool_results: List[ToolResult]
├── answer: str
├── steps_executed: List[str]
└── error: Optional[str]
```

## Deployment Architecture (Future)

```
┌─────────────────────────────────────────────────────────────────┐
│                   Production Architecture                        │
└─────────────────────────────────────────────────────────────────┘

                        ┌──────────────┐
                        │   Load       │
                        │   Balancer   │
                        └──────┬───────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
       ┌───────────┐    ┌───────────┐   ┌───────────┐
       │  API      │    │  API      │   │  API      │
       │  Server 1 │    │  Server 2 │   │  Server 3 │
       └─────┬─────┘    └─────┬─────┘   └─────┬─────┘
             │                │               │
             └────────────────┼───────────────┘
                              │
          ┌───────────────────┼────────────────────┐
          │                   │                    │
          ▼                   ▼                    ▼
    ┌──────────┐      ┌──────────────┐    ┌──────────────┐
    │  Redis   │      │  Pinecone    │    │    Neo4j     │
    │  Cache   │      │  Vector DB   │    │   Graph DB   │
    └──────────┘      └──────────────┘    └──────────────┘
          │                   │                    │
          └───────────────────┼────────────────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │   Monitoring    │
                     │   (Prometheus + │
                     │    Grafana)     │
                     └─────────────────┘
```

---

These diagrams provide visual understanding of the system's architecture, data flow, and component interactions. For implementation details, see the source code in `src/`.
