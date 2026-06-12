def execution_accuracy(outputs: dict, reference_outputs: dict = None) -> dict:
    """
    Returns a score of 1 if the SQL query executed successfully without errors,
    and 0 otherwise.
    """
    # Check if an error message was logged during graph execution
    error_message = outputs.get("error_message")
    
    if error_message:
        return {"score": 0.0, "reason": f"SQL Execution Failed: {error_message}"}
    return {"score": 1.0, "reason": "SQL Executed Successfully"}


def result_accuracy(outputs: dict, reference_outputs: dict) -> dict:
    """
    Compares the agent's interpreted answer to the expected reference output.
    """
    agent_answer = outputs.get("interpretation", "").lower()
    expected_answer = reference_outputs.get("expected_output", "").lower()
    
    if not expected_answer:
        return {"score": 1.0, "reason": "No reference provided for comparison"}
        
    # Basic semantic overlap or keyword verification rule
    # Can be replaced with an LLM-as-a-judge metric if needed
    match_count = sum(1 for word in expected_answer.split() if word in agent_answer)
    total_words = len(expected_answer.split())
    
    score = match_count / total_words if total_words > 0 else 0.0
    return {
        "score": round(score, 2),
        "reason": f"Matches {match_count} out of {total_words} reference words."
    }