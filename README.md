# 🤖 DataChat: World Bank SQL Agent

An intelligent, stateful AI data assistant that translates natural language into precise SQL queries, executes them against a World Bank macroeconomic database, and dynamically generates interactive visualizations. Built with LangGraph, Streamlit, and Google Gemini.

## ✨ Key Features
* **Natural Language to SQL:** Ask complex questions in plain English (e.g., "What was the GDP of India in 2022?") and watch the agent write and execute the exact SQL required.
* **Agentic Self-Correction:** Built-in LangGraph fallback mechanisms catch SQL execution errors, analyze the database schema, and autonomously rewrite failing queries up to 3 times before returning a graceful error.
* **Multi-Turn Context Memory:** The agent remembers previous entities. Ask "What is the GDP of Germany?", followed by "What about France?", and the agent intelligently merges the context.
* **Dynamic Data Visualization:** Automatically interprets when a query benefits from a chart (Bar, Line, Scatter) and seamlessly renders interactive native Streamlit graphics using Pandas.
* **Intelligent Edge-Case Handling:** Gracefully handles empty data results by providing contextual explanations or suggesting alternative available metrics.
* **Production Observability:** Fully integrated with **LangSmith** to push real-time telemetry, tagging runs with metadata such as `success`, `self_corrected`, `empty_result`, and tracking model retry counts.
* **Containerized Deployment:** Fully Dockerized for guaranteed reproducibility across local and cloud environments.

## 🛠️ Technology Stack
* **Frontend:** Streamlit, Pandas
* **AI Orchestration:** LangGraph, LangChain
* **LLM Provider:** Google Gemini API (`gemini-2.5-flash`)
* **Observability & Evals:** LangSmith
* **Database:** SQLite3
* **Deployment:** Docker, Docker Compose

---

## 🚀 Quickstart Guide

### Prerequisites
* Python 3.10+
* Docker Desktop (optional, for containerized runs)
* A [Google AI Studio](https://aistudio.google.com/) API Key
* A [LangSmith](https://smith.langchain.com/) API Key

### 1. Environment Setup
Create a `.env` file in the root directory by duplicating the provided `.env.example` file and inserting your API keys:

```env
GOOGLE_API_KEY="your_gemini_api_key_here"
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT="[https://api.smith.langchain.com](https://api.smith.langchain.com)"
LANGCHAIN_API_KEY="your_langsmith_api_key_here"
LANGCHAIN_PROJECT="text-to-sql-agent"

```

### 2. Running Locally (Virtual Environment)

```bash
# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# IMPORTANT: Initialize the Database and Fetch World Bank Data
python setup/load_data.py
python setup/verify_db.py

# Launch the application
streamlit run app.py

```

### 3. Running via Docker (Recommended)

```bash
# Build and spin up the container
docker-compose up --build

```

The application will be live at `http://localhost:8501`.

---

## 🧪 Evaluation & Observability

This agent is built with a programmatic MLOps testing suite. A 30-question evaluation dataset covering single-country queries, macro trends, metric correlations, and edge cases is integrated via LangSmith.

### LangSmith Telemetry Tracking

Every query executed through the Streamlit UI pushes exact state metadata to LangSmith for evaluation:

* **intent:** Tracks if the query was a data request.
* **retry_count:** Logs how many times the agent had to self-correct its SQL.
* **Tags:** Automatically flags runs as `success`, `self_corrected`, `empty_result`, or `max_retries_reached`.

### Running the Evaluator

To programmatically grade the agent against the 30-question dataset:

```bash
python evals/scorers.py

```

---

## 📁 Project Structure

```text
├── agent/
│   ├── graph.py          # Core LangGraph state machine workflow
│   ├── nodes.py          # Individual node execution logic
│   ├── db.py             # Database execution helpers
│   └── state.py          # State definitions for the LangGraph agent
├── evals/
│   ├── dataset.jsonl     # 30-question evaluation ground-truth dataset
│   └── scorers.py        # Automated LangSmith grading logic
├── setup/
│   ├── load_data.py      # Script to initialize database
│   ├── push_ambiguity.py # LangSmith prompt deployment
│   ├── push_interpreter.py # LangSmith prompt deployment
│   ├── push_prompts.py   # LangSmith prompt deployment
│   └── verify_db.py      # Database verification utility
├── app.py                # Streamlit UI and LangSmith metadata tagging
├── main.py               # Application entry point/CLI fallback
├── requirements.txt      # Python dependencies
├── Dockerfile            # Container build instructions
├── docker-compose.yml    # Multi-container orchestration
├── .env.example          # Template for environment variables
└── worldbank.db          # Local SQLite macroeconomic database

