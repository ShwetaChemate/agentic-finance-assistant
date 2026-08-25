from langgraph.graph import END, START, StateGraph

from app.agent.nodes import calculate_metrics, fetch_data, summarize_v1, summarize_v2
from app.agent.state import AgentStateV1, AgentStateV2


def build_agent_v1():
    """v1: fetch_data -> calculate_metrics -> summarize_v1 (free-text summary)."""
    graph = StateGraph(AgentStateV1)

    graph.add_node("fetch_data", fetch_data)
    graph.add_node("calculate_metrics", calculate_metrics)
    graph.add_node("summarize_v1", summarize_v1)

    graph.add_edge(START, "fetch_data")
    graph.add_edge("fetch_data", "calculate_metrics")
    graph.add_edge("calculate_metrics", "summarize_v1")
    graph.add_edge("summarize_v1", END)

    return graph.compile()


def build_agent_v2():
    """v2: fetch_data -> calculate_metrics -> summarize_v2 (structured-output summary).

    Same fetch_data/calculate_metrics nodes as v1 — only the final node and the state
    schema's summary field type differ between the two graphs.
    """
    graph = StateGraph(AgentStateV2)

    graph.add_node("fetch_data", fetch_data)
    graph.add_node("calculate_metrics", calculate_metrics)
    graph.add_node("summarize_v2", summarize_v2)

    graph.add_edge(START, "fetch_data")
    graph.add_edge("fetch_data", "calculate_metrics")
    graph.add_edge("calculate_metrics", "summarize_v2")
    graph.add_edge("summarize_v2", END)

    return graph.compile()
