import os
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(override=True)
print("Pushing Ambiguity prompts to LangSmith Hub...")

# 1. Ambiguity Checker Prompt
checker_template = """You are a data analyst assistant. 
Evaluate the user's question about World Bank data (GDP, population, health, emissions, etc.).
If the question is too vague to write a specific database query (e.g., it is missing a specific country, region, or exact metric), output exactly 'ambiguous'.
If the question is clear and specific enough to query, output exactly 'clear'.

Question: {question}
"""
checker_prompt = ChatPromptTemplate.from_template(checker_template)

# 2. Clarification Asker Prompt
clarification_template = """The user asked: '{question}'. 
This question is too vague to run against our World Bank database. 
Write a single, polite, and very short clarifying question to ask the user for the missing information (e.g., "Which specific country are you interested in?" or "Are you looking for GDP or population?").
"""
clarifier_prompt = ChatPromptTemplate.from_template(clarification_template)

try:
    client = Client()
    client.push_prompt("ambiguity-checker", object=checker_prompt)
    print("✅ Successfully pushed 'ambiguity-checker'")
    
    client.push_prompt("clarification-asker", object=clarifier_prompt)
    print("✅ Successfully pushed 'clarification-asker'")
except Exception as e:
    print(f"❌ Error pushing to Hub: {e}")