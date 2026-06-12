import os
import json
from langsmith import Client
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from agent.state import AgentState
from agent.db import get_schema, execute_sql

# 1. Initialize our AI brain (Google Gemini!)
# We use temperature=0 because we want strict, factual SQL, not creative writing.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)

def sql_generator(state: AgentState):
    """Takes the user question, pulls our prompt, and generates a SQL query."""
    print("--- 🧠 NODE: Generating SQL ---")
    
    question = state.get("clarified_question") or state.get("question")
    schema = get_schema()
    
    # Pull the prompt using the modern client
    client = Client()
    prompt = client.pull_prompt("text-to-sql-generator")
    
    # Combine the prompt template + our LLM
    chain = prompt | llm
    
    # Run the AI
    response = chain.invoke({"schema": schema, "question": question})
    
    # Clean up the output (sometimes the AI adds ```sql at the beginning, we want pure text)
    raw_sql = response.content.replace("```sql", "").replace("```", "").strip()
    
    # Keep track of our attempts in the state history
    current_attempts = state.get("sql_attempts", [])
    current_attempts.append(raw_sql)
    
    return {"sql_query": raw_sql, "sql_attempts": current_attempts}

def sql_executor(state: AgentState):
    """Takes the generated SQL and runs it against the SQLite database."""
    print("--- ⚙️ NODE: Executing SQL ---")
    
    query = state["sql_query"]
    
    # Run the query using our db.py helper
    results, error = execute_sql(query)
    
    if error:
        print(f"   [!] SQL Error: {error}")
        return {"error_message": error, "execution_result": []}
    
    if not results:
        print("   [!] Query successful, but returned 0 rows.")
        return {"execution_result": [], "is_empty_result": True, "error_message": ""}
    
    print(f"   [+] Success! Retrieved {len(results)} rows.")
    return {"execution_result": results, "is_empty_result": False, "error_message": ""}

def sql_self_correction(state: AgentState):
    """Attempts to fix a broken SQL query based on the SQLite error message."""
    print("--- 🛠️ NODE: Self-Correction ---")
    
    question = state.get("clarified_question") or state.get("question")
    error = state["error_message"]
    failed_sql = state["sql_query"]
    
    # Increase our retry counter by 1
    retry_count = state.get("retry_count", 0) + 1
    
    # We define the correction instructions directly here
    correction_template = """You are an expert SQLite developer.
    You previously tried to write a query to answer: {question}
    
    Your query was:
    {failed_sql}
    
    It resulted in this database error:
    {error}
    
    Here is the database schema again:
    {schema}
    
    Fix the query so it works. 
    Rules:
    1. Output ONLY the raw SQL. 
    2. Do not include markdown formatting like ```sql or any explanations.
    """
    
    prompt = ChatPromptTemplate.from_template(correction_template)
    chain = prompt | llm
    
    # Run the AI to get a fixed query
    response = chain.invoke({
        "question": question,
        "failed_sql": failed_sql,
        "error": error,
        "schema": get_schema()
    })
    
    raw_sql = response.content.replace("```sql", "").replace("```", "").strip()
    
    # Update our state history with the new attempt
    current_attempts = state.get("sql_attempts", [])
    current_attempts.append(raw_sql)
    
    return {
        "sql_query": raw_sql, 
        "sql_attempts": current_attempts, 
        "retry_count": retry_count
    }

def alternative_suggester(state: AgentState):
    """Suggests an alternative question if the query returned zero rows."""
    print("--- 💡 NODE: Alternative Suggester ---")
    
    question = state.get("clarified_question") or state.get("question")
    
    suggestion_template = """The user asked this question about the World Bank dataset: '{question}'
    The database returned exactly zero results for this query. 
    Write a short, polite 1-sentence message explaining that no data was found, and suggest one specific related alternative they could ask (e.g., trying a different year, a broader region, or a different indicator).
    """
    prompt = ChatPromptTemplate.from_template(suggestion_template)
    chain = prompt | llm
    
    response = chain.invoke({"question": question})
    
    # We bypass the data interpreter and save this directly as our final answer
    return {"interpretation": response.content}

def result_interpreter(state: AgentState):
    """Translates raw database rows into plain English using our LangSmith prompt."""
    print("--- 🗣️ NODE: Interpreting Results ---")
    
    question = state.get("clarified_question") or state.get("question")
    results = state["execution_result"]
    
    # Pull the prompt from LangSmith
    client = Client()
    prompt = client.pull_prompt("result-interpreter")
    chain = prompt | llm
    
    response = chain.invoke({"question": question, "results": str(results)})
    
    return {"interpretation": response.content}

def chart_generator(state: AgentState):
    """Analyzes the question and data to see if a chart should be drawn."""
    print("--- 📊 NODE: Generating Chart Spec ---")
    
    question = state.get("clarified_question") or state.get("question")
    results = state["execution_result"]
    
    # We use a simple inline prompt to force the AI to output JSON
    chart_template = """You are a data visualization expert.
    Based on the user's question and the data results, determine if a chart is appropriate.
    If yes, output a JSON object with this exact structure:
    {{"chart_type": "bar|line|scatter", "x_axis": "column_name", "y_axis": "column_name", "title": "Chart Title"}}
    If no chart is needed, output exactly: {{"chart_type": "none"}}
    
    Question: {question}
    Data: {results}
    
    Output ONLY valid JSON. Do not include markdown formatting.
    """
    prompt = ChatPromptTemplate.from_template(chart_template)
    chain = prompt | llm
    
    response = chain.invoke({"question": question, "results": str(results)})
    
    try:
        # Clean up the output to ensure it is pure JSON
        clean_json = response.content.replace("```json", "").replace("```", "").strip()
        chart_spec = json.loads(clean_json)
    except Exception:
        chart_spec = {"chart_type": "none"}
        
    return {"chart_spec": chart_spec}

def memory_node(state: AgentState):
    """Saves the conversation history."""
    print("--- 🧠 NODE: Updating Memory ---")
    
    messages = state.get("messages", [])
    messages.append({"role": "user", "content": state.get("question", "")})
    messages.append({"role": "assistant", "content": state.get("interpretation", "")})
    
    return {"messages": messages}

def ambiguity_checker(state: AgentState):
    """Checks if the question is specific enough to query, using conversation history."""
    print("--- 🧐 NODE: Checking Ambiguity ---")
    
    current_question = state.get("clarified_question") or state.get("question")
    messages = state.get("messages", [])
    
    # If we have memory, combine it with the current question so the AI has full context
    if messages:
        # Grab the last 4 messages to keep the context window clean
        history = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-4:]])
        combined_question = f"Previous Chat:\n{history}\n\nUser's New Input: {current_question}"
    else:
        combined_question = current_question
    
    client = Client()
    prompt = client.pull_prompt("ambiguity-checker")
    chain = prompt | llm
    
    response = chain.invoke({"question": combined_question})
    is_ambiguous = "ambiguous" in response.content.lower()
    
    return {"is_ambiguous": is_ambiguous}

def clarification_node(state: AgentState):
    """Asks the user for more details, using memory so it doesn't ask the same thing twice."""
    print("--- ✋ NODE: Asking for Clarification ---")
    
    current_question = state.get("question")
    messages = state.get("messages", [])
    
    # Give the clarifier the same memory context
    if messages:
        history = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-4:]])
        combined_question = f"Previous Chat:\n{history}\n\nUser's New Input: {current_question}"
    else:
        combined_question = current_question
    
    client = Client()
    prompt = client.pull_prompt("clarification-asker")
    chain = prompt | llm
    
    response = chain.invoke({"question": combined_question})
    
    return {"interpretation": response.content}