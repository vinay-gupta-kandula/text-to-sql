from langgraph.graph import StateGraph, END
from agent.state import AgentState

# Import all the nodes we just built!
from agent.nodes import (
    ambiguity_checker, clarification_node, sql_generator,
    sql_executor, sql_self_correction, alternative_suggester,
    result_interpreter, chart_generator, memory_node
)

def build_graph():
    # 1. Initialize the graph with our custom State "clipboard"
    workflow = StateGraph(AgentState)

    # 2. Add all our nodes (workers) to the graph
    workflow.add_node("ambiguity_checker", ambiguity_checker)
    workflow.add_node("clarification_node", clarification_node)
    workflow.add_node("sql_generator", sql_generator)
    workflow.add_node("sql_executor", sql_executor)
    workflow.add_node("sql_self_correction", sql_self_correction)
    workflow.add_node("alternative_suggester", alternative_suggester)
    workflow.add_node("result_interpreter", result_interpreter)
    workflow.add_node("chart_generator", chart_generator)
    workflow.add_node("memory_node", memory_node)

    # 3. Define the Entry Point (Where does the user's question go first?)
    workflow.set_entry_point("ambiguity_checker")

    # 4. Define the routing logic (The Arrows in diagram)
    
    # Arrow from Ambiguity Checker
    def route_ambiguity(state: AgentState):
        if state.get("is_ambiguous"):
            return "clarification_node"
        return "sql_generator"

    workflow.add_conditional_edges(
        "ambiguity_checker",
        route_ambiguity,
        {"clarification_node": "clarification_node", "sql_generator": "sql_generator"}
    )

    # Arrow from Clarification -> Memory -> END (Wait for user reply)
    workflow.add_edge("clarification_node", "memory_node")

    # Arrow from Generator -> Executor
    workflow.add_edge("sql_generator", "sql_executor")

    # Arrow from Executor (The main intersection!)
    def route_executor(state: AgentState):
        error = state.get("error_message")
        if error:
            # If we have an error and haven't retried 3 times, send to correction
            if state.get("retry_count", 0) < 3:
                return "sql_self_correction"
            else:
                # If we failed 3 times, fail gracefully by suggesting an alternative
                return "alternative_suggester"
                
        # If it ran but found no data
        if state.get("is_empty_result"):
            return "alternative_suggester"
            
        # If it was a total success!
        return "result_interpreter"

    workflow.add_conditional_edges(
        "sql_executor",
        route_executor,
        {
            "sql_self_correction": "sql_self_correction",
            "alternative_suggester": "alternative_suggester",
            "result_interpreter": "result_interpreter"
        }
    )

    # Self-Correction loops back to the Executor to try again
    workflow.add_edge("sql_self_correction", "sql_executor")

    # Success path: Interpreter -> Chart Generator -> Memory
    workflow.add_edge("result_interpreter", "chart_generator")
    workflow.add_edge("chart_generator", "memory_node")
    
    # Alternative path: Alternative Suggester -> Memory
    workflow.add_edge("alternative_suggester", "memory_node")

    # Finally, Memory -> END (Finish the cycle)
    workflow.add_edge("memory_node", END)

    # Compile the graph into a runnable application
    return workflow.compile()