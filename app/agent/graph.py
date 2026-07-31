from langgraph.graph import END, START, StateGraph

from app.agent.nodes import calculate_metrics, fetch_data, summarize
from app.agent.state import AgentState


def build_agent():
    """Wire fetch_data -> calculate_metrics -> summarize into a compiled, runnable graph."""
    graph = StateGraph(AgentState)

    # Register each function as a named node.
    graph.add_node("fetch_data", fetch_data)
    graph.add_node("calculate_metrics", calculate_metrics)
    graph.add_node("summarize", summarize)

    # Wire them into a straight-line pipeline: START marks the entry point,
    # END marks where the graph run finishes.
    graph.add_edge(START, "fetch_data")
    graph.add_edge("fetch_data", "calculate_metrics")
    graph.add_edge("calculate_metrics", "summarize")
    graph.add_edge("summarize", END)

    # compile() validates the graph and returns an object with .invoke(initial_state).
    return graph.compile()
