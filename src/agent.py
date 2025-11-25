"""LangGraph agent with multi-step reasoning."""

from typing import TypedDict, Annotated, List, Dict, Any, Optional
from typing_extensions import TypedDict
import operator
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage

from src.retriever import GraphAwareRetriever, RetrievalResult
from src.tools import (
    LookupTool,
    SummarizeTool,
    CalculationTool,
    DependencyAnalysisTool,
    ToolResult,
)


class AgentState(TypedDict):
    """State for the agent workflow."""

    # Input
    query: str
    messages: Annotated[List[Any], operator.add]

    # Intermediate state
    router_decision: Optional[str]
    retrieved_context: Optional[List[RetrievalResult]]
    tool_calls: Annotated[List[Dict[str, Any]], operator.add]
    tool_results: Annotated[List[ToolResult], operator.add]

    # Output
    answer: Optional[str]
    steps_executed: Annotated[List[str], operator.add]
    error: Optional[str]

    # Memory
    conversation_history: Annotated[List[Dict[str, str]], operator.add]


class AgenticRAG:
    """Main agentic RAG system using LangGraph."""

    def __init__(
        self,
        retriever: GraphAwareRetriever,
        knowledge_graph,
        llm_model: str = "gpt-4-turbo-preview",
        openai_api_key: str = None,
    ):
        self.retriever = retriever
        self.knowledge_graph = knowledge_graph

        # Initialize LLM
        self.llm = ChatOpenAI(
            model=llm_model,
            temperature=0,
            api_key=openai_api_key,
        )

        # Initialize tools
        self.lookup_tool = LookupTool(knowledge_graph, retriever)
        self.summarize_tool = SummarizeTool(retriever, self.llm)
        self.calculation_tool = CalculationTool(knowledge_graph)
        self.dependency_tool = DependencyAnalysisTool(knowledge_graph, retriever)

        # Build workflow
        self.workflow = self._build_workflow()
        self.app = self.workflow.compile()

    def _build_workflow(self) -> StateGraph:
        """Build the LangGraph workflow."""
        workflow = StateGraph(AgentState)

        # Add nodes
        workflow.add_node("router", self.router_node)
        workflow.add_node("retriever", self.retriever_node)
        workflow.add_node("tool_executor", self.tool_executor_node)
        workflow.add_node("reasoning", self.reasoning_node)
        workflow.add_node("error_handler", self.error_handler_node)

        # Set entry point
        workflow.set_entry_point("router")

        # Add edges
        workflow.add_conditional_edges(
            "router",
            self._router_condition,
            {
                "retrieve": "retriever",
                "tool": "tool_executor",
                "direct_answer": "reasoning",
                "error": "error_handler",
            },
        )

        workflow.add_edge("retriever", "reasoning")
        workflow.add_edge("tool_executor", "reasoning")
        workflow.add_edge("reasoning", END)
        workflow.add_edge("error_handler", END)

        return workflow

    def router_node(self, state: AgentState) -> AgentState:
        """
        Router node: Decides what action to take based on the query.
        """
        query = state["query"]

        # Analyze query to determine action
        prompt = f"""Analyze this query and decide what action to take:

Query: "{query}"

Available actions:
1. retrieve - Search the knowledge base for relevant information
2. tool - Use a specific tool (lookup_facts, summarize_document, run_calculation, analyze_dependencies)
3. direct_answer - Answer directly without retrieval (for greetings, meta questions, etc.)

Also determine if any tools should be called. Available tools:
- lookup_facts: Look up information about a specific entity
- summarize_document: Summarize documents about a topic
- run_calculation: Perform calculations (count entities, dependencies, etc.)
- analyze_dependencies: Analyze dependencies for an entity

Respond in this format:
Action: [retrieve/tool/direct_answer]
Tool: [tool_name if action is 'tool', otherwise 'none']
Reasoning: [brief explanation]"""

        response = self.llm.invoke([HumanMessage(content=prompt)])
        decision_text = response.content

        # Parse decision
        action = "retrieve"  # default
        tool_name = None

        if "Action:" in decision_text:
            action_line = [
                line for line in decision_text.split("\n") if "Action:" in line
            ][0]
            if "tool" in action_line.lower():
                action = "tool"
            elif "direct_answer" in action_line.lower():
                action = "direct_answer"
            elif "retrieve" in action_line.lower():
                action = "retrieve"

        if "Tool:" in decision_text:
            tool_line = [line for line in decision_text.split("\n") if "Tool:" in line][
                0
            ]
            if "lookup" in tool_line.lower():
                tool_name = "lookup_facts"
            elif "summarize" in tool_line.lower():
                tool_name = "summarize_document"
            elif "calculat" in tool_line.lower():
                tool_name = "run_calculation"
            elif "dependen" in tool_line.lower():
                tool_name = "analyze_dependencies"

        state["router_decision"] = action
        state["steps_executed"] = [f"Router decided: {action}"]

        if tool_name:
            state["tool_calls"] = [{"tool": tool_name, "query": query}]

        return state

    def _router_condition(self, state: AgentState) -> str:
        """Conditional edge from router."""
        decision = state.get("router_decision", "retrieve")

        if decision == "tool":
            return "tool"
        elif decision == "direct_answer":
            return "direct_answer"
        elif decision == "retrieve":
            return "retrieve"
        else:
            return "error"

    def retriever_node(self, state: AgentState) -> AgentState:
        """
        Retriever node: Executes graph-aware retrieval.
        """
        query = state["query"]

        try:
            # Perform retrieval
            results = self.retriever.retrieve(query, use_graph=True, top_k=5)

            state["retrieved_context"] = results
            state["steps_executed"] = [
                f"Retrieved {len(results)} relevant chunks using graph-aware retrieval"
            ]

        except Exception as e:
            state["error"] = f"Retrieval error: {str(e)}"
            state["steps_executed"] = [f"Retrieval failed: {str(e)}"]

        return state

    def tool_executor_node(self, state: AgentState) -> AgentState:
        """
        Tool executor node: Executes requested tools.
        """
        tool_calls = state.get("tool_calls", [])

        if not tool_calls:
            state["error"] = "No tool calls specified"
            return state

        tool_results = []

        for tool_call in tool_calls:
            tool_name = tool_call["tool"]
            query = tool_call["query"]

            try:
                # Extract entity/topic from query
                entity_or_topic = self._extract_entity_from_query(query)

                if tool_name == "lookup_facts":
                    result = self.lookup_tool.lookup_facts(entity_or_topic)
                elif tool_name == "summarize_document":
                    result = self.summarize_tool.summarize_document(entity_or_topic)
                elif tool_name == "run_calculation":
                    result = self.calculation_tool.run_calculation(query)
                elif tool_name == "analyze_dependencies":
                    result = self.dependency_tool.analyze_dependencies(entity_or_topic)
                else:
                    result = ToolResult(
                        tool_name=tool_name,
                        success=False,
                        result=None,
                        error=f"Unknown tool: {tool_name}",
                    )

                tool_results.append(result)
                state["steps_executed"] = [
                    f"Executed tool: {tool_name} {'(success)' if result.success else '(failed)'}"
                ]

            except Exception as e:
                tool_results.append(
                    ToolResult(
                        tool_name=tool_name,
                        success=False,
                        result=None,
                        error=str(e),
                    )
                )
                state["steps_executed"] = [f"Tool execution failed: {str(e)}"]

        state["tool_results"] = tool_results

        return state

    def reasoning_node(self, state: AgentState) -> AgentState:
        """
        Reasoning node: Formulates final answer using retrieved context and tool results.
        """
        query = state["query"]
        retrieved_context = state.get("retrieved_context", [])
        tool_results = state.get("tool_results", [])
        router_decision = state.get("router_decision", "retrieve")

        # Build context for reasoning
        context_parts = []

        if retrieved_context:
            context_parts.append("## Retrieved Context:\n")
            for i, result in enumerate(retrieved_context[:5], 1):
                source = result.chunk.metadata.get("source", "unknown")
                method = result.retrieval_method
                context_parts.append(
                    f"[{i}] (Source: {source}, Method: {method}, Score: {result.score:.3f})\n{result.chunk.content}\n"
                )

        if tool_results:
            context_parts.append("\n## Tool Results:\n")
            for tool_result in tool_results:
                if tool_result.success:
                    context_parts.append(
                        f"Tool: {tool_result.tool_name}\nResult: {tool_result.result}\n"
                    )
                else:
                    context_parts.append(
                        f"Tool: {tool_result.tool_name}\nError: {tool_result.error}\n"
                    )

        context = "\n".join(context_parts)

        # Generate answer
        if router_decision == "direct_answer" and not context:
            # Handle direct answers (greetings, meta questions)
            prompt = f"""Answer this query directly and concisely:

Query: {query}

Answer:"""
        else:
            # Use context to answer
            prompt = f"""Based on the following context, provide a comprehensive answer to the query.

{context}

Query: {query}

Instructions:
- Cite sources when referencing specific information
- Be concise but thorough
- If the context doesn't contain enough information, say so
- If tools were used, incorporate their results into your answer

Answer:"""

        try:
            response = self.llm.invoke([HumanMessage(content=prompt)])
            answer = response.content

            state["answer"] = answer
            state["steps_executed"] = ["Generated final answer using LLM reasoning"]

        except Exception as e:
            state["error"] = f"Reasoning error: {str(e)}"
            state["steps_executed"] = [f"Reasoning failed: {str(e)}"]

        return state

    def error_handler_node(self, state: AgentState) -> AgentState:
        """
        Error handler node: Handles errors and provides fallback responses.
        """
        error = state.get("error", "Unknown error")
        query = state["query"]

        # Try to provide a helpful fallback response
        fallback_prompt = f"""An error occurred while processing this query: "{query}"

Error: {error}

Provide a helpful response explaining:
1. What might have gone wrong
2. Suggestions for rephrasing the query
3. Available capabilities of the system

Response:"""

        try:
            response = self.llm.invoke([HumanMessage(content=fallback_prompt)])
            state["answer"] = f"[Error Handler] {response.content}"
            state["steps_executed"] = ["Error handled with fallback response"]

        except Exception as e:
            state["answer"] = (
                f"An error occurred: {error}. "
                f"Additionally, error handler failed: {str(e)}"
            )
            state["steps_executed"] = ["Error handler also failed"]

        return state

    def _extract_entity_from_query(self, query: str) -> str:
        """Extract entity or topic from query."""
        # Check for known entities
        for entity in self.knowledge_graph.entities.keys():
            if entity.lower() in query.lower():
                return entity

        # Fallback: extract capitalized words or use whole query
        import re

        capitalized = re.findall(r"\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b", query)
        if capitalized:
            return capitalized[0]

        return query

    def run(self, query: str) -> Dict[str, Any]:
        """
        Run the agent on a query.

        Args:
            query: The user query

        Returns:
            Dictionary with answer and execution trace
        """
        # Initialize state
        initial_state: AgentState = {
            "query": query,
            "messages": [],
            "router_decision": None,
            "retrieved_context": None,
            "tool_calls": [],
            "tool_results": [],
            "answer": None,
            "steps_executed": [],
            "error": None,
            "conversation_history": [],
        }

        # Run workflow
        final_state = self.app.invoke(initial_state)

        # Format output
        retrieved_context = final_state.get("retrieved_context") or []
        output = {
            "query": query,
            "answer": final_state.get("answer", "No answer generated"),
            "steps_executed": final_state.get("steps_executed", []),
            "router_decision": final_state.get("router_decision"),
            "retrieved_chunks": len(retrieved_context),
            "tools_used": [
                tool_call["tool"] for tool_call in final_state.get("tool_calls", [])
            ],
            "tool_results": final_state.get("tool_results", []),
            "error": final_state.get("error"),
        }

        return output
