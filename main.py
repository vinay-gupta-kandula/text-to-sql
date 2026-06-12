import os
import time
from dotenv import load_dotenv

# 1. LOAD KEYS FIRST! 
# We must do this before importing any of our custom files that use OpenAI/Google
load_dotenv(override=True)

# 2. NOW import our graph
from agent.graph import build_graph

print("🤖 Booting up DataChat Agent...")
app = build_graph()

# Initialize an empty conversation state
state = {
    "messages": [],
    "sql_attempts": [],
    "retry_count": 0
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
    
    # Run the flowchart!
    print("\nThinking...")
    result = app.invoke(state)
    
    # Print the final English answer
    print(f"\nAgent: {result.get('interpretation')}")
    
    # Check if the AI decided to generate a chart specification
    chart = result.get('chart_spec')
    if chart and chart.get('chart_type') != 'none':
        print(f"[📊 UI Alert: Render a {chart['chart_type']} chart titled '{chart['title']}']")
    
    print("-" * 60)
    
    # Save the updated memory back to our running state
    state["messages"] = result["messages"]