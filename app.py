import streamlit as st
import os
import uuid
import pandas as pd
from dotenv import load_dotenv
from langsmith import Client

# 1. Load Environment Variables First
load_dotenv(override=True)

# 2. Import LangGraph App Build Function
from agent.graph import build_graph

# Set up page configurations
st.set_page_config(page_title="DataChat AI", page_icon="🤖", layout="wide")

# Initialize the LangSmith client for tagging runs
ls_client = Client()

# Initialize the agent graph inside Streamlit session state so it doesn't rebuild on every click
if "agent_app" not in st.session_state:
    st.session_state.agent_app = build_graph()

if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

if "agent_state" not in st.session_state:
    st.session_state.agent_state = {
        "messages": [],
        "sql_attempts": [],
        "retry_count": 0
    }

# Helper function to render charts dynamically from raw data rows and specs
# Helper function to render charts dynamically from raw data rows and specs
def render_agent_chart(chart_spec, raw_data):
    if not chart_spec or chart_spec.get("chart_type") == "none" or not raw_data:
        return
        
    try:
        # Convert raw database tuples/dictionaries into a clean Pandas DataFrame
        df = pd.DataFrame(raw_data)
        
        # 1. Extract the specific column names the AGENT generated
        # We wrap them in str() to guarantee Streamlit gets the text format it demands
        x_col = str(chart_spec.get("x_axis", "X-Axis"))
        y_col = str(chart_spec.get("y_axis", "Y-Axis"))
        title = chart_spec.get("title", "Data Visualization")
        chart_type = chart_spec.get("chart_type", "").lower()
        
        # 2. 🛠️ DYNAMIC FIX: If columns are integers (0, 1), rename them to the agent's exact labels
        if all(isinstance(c, int) for c in df.columns):
            if len(df.columns) >= 2:
                df.rename(columns={0: x_col, 1: y_col}, inplace=True)
            else:
                st.warning("⚠️ Not enough data columns to build a chart view.")
                st.dataframe(df)
                return
                
        # 3. If columns are strings but case mismatch happens (e.g., "gdp" vs "GDP")
        elif x_col not in df.columns or y_col not in df.columns:
            cols_lower = {str(c).lower(): c for c in df.columns}
            if str(x_col).lower() in cols_lower and str(y_col).lower() in cols_lower:
                x_col = cols_lower[str(x_col).lower()]
                y_col = cols_lower[str(y_col).lower()]
            else:
                st.dataframe(df)
                return

        st.subheader(f"📊 {title}")
        
        # 4. Map to native Streamlit chart types
        if "bar" in chart_type:
            st.bar_chart(df, x=x_col, y=y_col)
        elif "line" in chart_type:
            st.line_chart(df, x=x_col, y=y_col)
        elif "scatter" in chart_type:
            st.scatter_chart(df, x=x_col, y=y_col)
        else:
            st.dataframe(df)
            
    except Exception as e:
        st.warning(f"⚠️ Could not render visual chart: {str(e)}")

# App Header Styling
st.title("🤖 DataChat: World Bank SQL Agent")
st.caption("Ask questions in plain English, and watch the agent write SQL and render interactive data views.")
st.divider()

# Display Chat History (with persisted interactive charts)
for message in st.session_state.chat_history:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if "chart" in message and "chart_data" in message:
            render_agent_chart(message["chart"], message["chart_data"])

# Chat Input Box
if user_query := st.chat_input("Ask about global GDP, populations, or economic indicators..."):
    
    # 1. Display User Message Immediately
    with st.chat_message("user"):
        st.markdown(user_query)
    st.session_state.chat_history.append({"role": "user", "content": user_query})
    
    # 2. Update Graph Processing State
    st.session_state.agent_state["question"] = user_query
    st.session_state.agent_state["retry_count"] = 0
    st.session_state.agent_state["sql_attempts"] = []
    
    # Generate a unique ID for this run so we can tag it in LangSmith later
    run_id = uuid.uuid4()
    
    # 3. Stream Status Logs to Show Agent Thinking Steps
    with st.chat_message("assistant"):
        status_placeholder = st.empty()
        with status_placeholder.container():
            st.write("⏳ *Agent is processing through LangGraph nodes...*")
            
        try:
            # 4. Invoke our backend flowchart with the run_id and initial metadata!
            config = {
                "run_id": run_id,
                "metadata": {
                    "question": user_query,
                    "intent": "data_query"
                }
            }
            response_state = st.session_state.agent_app.invoke(st.session_state.agent_state, config=config)
            
            # Extract text answer, chart specs, and raw execution data
            answer = response_state.get("interpretation", "No response text generated.")
            chart_spec = response_state.get("chart_spec", None)
            raw_data = response_state.get("execution_result", [])
            
            # Clear processing placeholder and show real output text
            status_placeholder.empty()
            st.markdown(answer)
            
            # Draw chart instantly if the query benefits from visualization
            has_chart = chart_spec and chart_spec.get("chart_type") != "none" and len(raw_data) > 0
            if has_chart:
                render_agent_chart(chart_spec, raw_data)
            
            # Save response along with chart configuration to session history
            history_item = {"role": "assistant", "content": answer}
            if has_chart:
                history_item["chart"] = chart_spec
                history_item["chart_data"] = raw_data
                
            st.session_state.chat_history.append(history_item)
            st.session_state.agent_state["messages"] = response_state.get("messages", [])
            
            # --- LANGSMITH TAGGING & METADATA UPDATE ---
            final_tags = []
            retry_count = response_state.get("retry_count", 0)
            
            if retry_count >= 3:
                final_tags.append("max_retries_reached")
            elif retry_count > 0:
                final_tags.append("self_corrected")
            elif response_state.get("is_empty_result"):
                final_tags.append("empty_result")
            else:
                final_tags.append("success")
                
            chart_type = chart_spec.get("chart_type", "none") if chart_spec else "none"
            
            # Push the final tags and metadata to LangSmith for the grading suite
            ls_client.update_run(
                run_id=run_id,
                tags=final_tags,
                extra={
                    "metadata": {
                        "question": user_query,
                        "intent": "data_query",
                        "retry_count": retry_count,
                        "chart_type": chart_type
                    }
                }
            )
            # -------------------------------------------
            
        except Exception as e:
            status_placeholder.empty()
            st.error(f"An execution error occurred: {str(e)}")