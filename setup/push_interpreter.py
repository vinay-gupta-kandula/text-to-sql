import os
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

load_dotenv(override=True)
print("Pushing Result-Interpreter prompt to LangSmith Hub...")

PROMPT_NAME = "result-interpreter"

template = """You are a brilliant data analyst. 
The user asked: {question}

The database returned these raw results:
{results}

Write a natural, plain-English summary of the answer. 
Keep it concise and conversational. Do not mention the database, the tables, or the SQL query.
"""

prompt = ChatPromptTemplate.from_template(template)

try:
    client = Client()
    client.push_prompt(PROMPT_NAME, object=prompt)
    print(f"✅ Successfully pushed '{PROMPT_NAME}' to LangSmith Hub!")
except Exception as e:
    print(f"❌ Error pushing to Hub: {e}")