from typing import TypedDict, List, Dict, Any, Optional

class AgentState(TypedDict):
    """
    This dictionary represents the 'clipboard' that gets passed around 
    our LangGraph nodes. Each node reads from it and updates it.
    """
    question: str                   # The original user question
    clarified_question: str         # The question after asking for clarity (if needed)
    is_ambiguous: bool              # Flag set if the question is too vague
    
    sql_query: str                  # The generated SQL query
    sql_attempts: List[str]         # History of all SQL attempts (useful for the retry loop)
    retry_count: int                # How many times we've tried to fix a broken SQL query
    
    execution_result: List[Any]     # The raw rows returned from SQLite
    is_empty_result: bool           # Flag set if the query ran successfully but found zero rows
    error_message: str              # The text of any SQL error that occurs
    
    interpretation: str             # The final plain-English answer the AI generates
    chart_spec: Dict[str, Any]      # The JSON instructions for drawing a chart
    
    messages: List[Dict[str, str]]  # Full conversation history for multi-turn chat
    follow_up_context: Dict[str, str] # Memory of the last country/indicator discussed