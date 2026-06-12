import os
from dotenv import load_dotenv
from langsmith import Client
from langchain_core.prompts import ChatPromptTemplate

# Force load environment variables
load_dotenv(override=True)

print("Pushing Text-to-SQL prompt to LangSmith Hub...")

# With the modern client, we just use the name directly!
PROMPT_NAME = "text-to-sql-generator"

sql_template = """You are an expert data analyst and SQLite master. 
Given the following database schema, write a valid SQLite query to answer the user's question.

Schema:
{schema}

Rules:
1. NEVER use SELECT *. Always select specific, relevant columns.
2. Always filter out NULL values on the primary metric you are querying.
3. Default to LIMIT 20 unless the user asks for more.
4. Output ONLY the raw SQL query. Do not include markdown formatting like ```sql or any explanations.

Question: {question}
"""

sql_prompt = ChatPromptTemplate.from_template(sql_template)

try:
    client = Client()
    client.push_prompt(PROMPT_NAME, object=sql_prompt)
    print(f"✅ Successfully pushed '{PROMPT_NAME}' to LangSmith Hub!")
except Exception as e:
    print(f"❌ Error pushing to Hub: {e}")