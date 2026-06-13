import os
import time
import uuid
from dotenv import load_dotenv
from langsmith import Client

# 1. LOAD KEYS FIRST! 
# We must do this before importing any of our custom files that use OpenAI/Google
load_dotenv(override=True)

# 2. NOW import our graph
from agent.graph import build_graph

print("🤖 Booting up DataChat Agent...")
app = build_graph()

# Initialize the LangSmith client for tagging runs
ls_client = Client()

# Initialize an empty conversation state
state = {
    "messages": [],
    "sql_attempts": [],
    "retry_count": 0,
    "follow_up_context": {} # Added to support context merging from nodes.py
}

print("\n✅ Agent Ready! Ask a question about World Bank data (or type 'quit' to exit).")
print("Example: 'Which region had the fastest GDP growth in the last decade?'\n")

while True:
    user_input = input("\nYou: ")
    if user_input.lower() in ['quit', 'exit', 'q']:
        print("Goodbye!")
        break
        
    # Introduce a 2-second buffer to safeguard against 429 Rate Limits
    time.sleep(2)
        
    # Inject the user's question into our state
    state["question"] = user_input
    # Reset counters for the new question
    state["retry_count"] = 0
    state["sql_attempts"] = []
    state["error_message"] = ""
    state["clarified_question"] = ""
    
    # Generate a unique ID for this run so we can tag it in LangSmith
    run_id = uuid.uuid4()
    
    config = {
        "run_id": run_id,
        "metadata": {
            "question": user_input,
            "intent": "data_query"
        }
    }
    
    # Run the flowchart!
    print("\nThinking...")
    result = app.invoke(state, config=config)
    
    # Print the final English answer
    print(f"\nAgent: {result.get('interpretation')}")
    
    # Check if the AI decided to generate a chart specification
    chart = result.get('chart_spec')
    if chart and chart.get('chart_type') != 'none':
        print(f"[📊 UI Alert: Render a {chart['chart_type']} chart titled '{chart['title']}']")
    
    print("-" * 60)
    
    # Save the updated memory back to our running state
    state["messages"] = result["messages"]
    state["follow_up_context"] = result.get("follow_up_context", state["follow_up_context"])
    
    # --- LANGSMITH TAGGING & METADATA UPDATE ---
    final_tags = []
    retry_count = result.get("retry_count", 0)
    
    if retry_count >= 3:
        final_tags.append("max_retries_reached")
    elif retry_count > 0:
        final_tags.append("self_corrected")
    elif result.get("is_empty_result"):
        final_tags.append("empty_result")
    else:
        final_tags.append("success")
        
    chart_type = chart.get("chart_type", "none") if chart else "none"
    
    # Push the final tags and metadata to LangSmith for the grading suite
    try:
        ls_client.update_run(
            run_id=run_id,
            tags=final_tags,
            extra={
                "metadata": {
                    "question": user_input,
                    "intent": "data_query",
                    "retry_count": retry_count,
                    "chart_type": chart_type
                }
            }
        )
    except Exception as e:
        print(f"[Debug] Could not update LangSmith tags: {e}")
    # -------------------------------------------