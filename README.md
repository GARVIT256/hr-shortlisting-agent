# 🤖 HR Resume Shortlisting Agent

An advanced, agentic system designed to revolutionize the recruitment workflow. Built with **LangGraph**, **Gemini 2.0 Flash**, and **Local Embeddings**, this agent automates candidate evaluation with production-grade reasoning, transparency, and human oversight.

---

## 🔗 Primary Links

- **Live Deployed App:** [hr-shortlisting-agent.streamlit.app](https://hr-shortlisting-agent.streamlit.app/)
- **Presentation Deck (PDF):** [View Slides](https://drive.google.com/file/d/1482P0yirl1WV4pd5vPGCuZRMNA1yHGYW/view?usp=sharing)
- **Video Demo:** [Watch Demo](https://drive.google.com/file/d/1gSzYujneM0yuG-xdZc3F6q7IZ4aZeR3i/view?usp=sharing)

---

## 🏗️ Core Architecture & Workflow

This project utilizes a **Stateful Multi-Agent Workflow** orchestrated by **LangGraph**. Unlike linear pipelines, our agentic approach allows for complex decision-making, state persistence, and mandatory human verification points.

### 1. Stateful Workflow (LangGraph)
The system maintains a centralized state throughout the evaluation lifecycle. It utilizes a directed acyclic graph (DAG) to manage transitions between JD parsing, parallel candidate scoring, and final report generation.

### 2. Hybrid Semantic Match
We employ a multi-layered scoring strategy:
- **Local Embeddings (Sentence-Transformers):** Initial semantic similarity is calculated locally (`all-MiniLM-L6-v2`). This ensures fast, privacy-preserving preliminary matching without sending raw text to an external API.
- **Gemini 2.0 Flash Reasoning:** For high-order cognitive tasks like experience validation and project quality assessment, we leverage Gemini 2.0's sophisticated reasoning capabilities.

### 3. Parallel Execution
To minimize latency during batch processing, the agent uses a **ThreadPoolExecutor** within the ingestion and scoring nodes. This allows the system to process multiple resumes concurrently, making it scalable for large candidate pools.

---

## ✨ Key Features (The Differentiators)

### 🧐 Evidence-Based Extraction
To eliminate LLM hallucinations, the agent is strictly instructed to provide **verbatim quotes** from the resume to justify every score. Every evaluation is backed by direct evidence, allowing recruiters to verify the "why" behind the AI's "what."

### 🤝 Human-in-the-Loop (HITL)
Designed for high-stakes decision-making, the system includes a mandatory **Score Override** phase. Recruiters can audit the AI's findings, override scores based on nuance, and provide custom reasons—all of which are captured in the final audit log.

### 📊 Production Observability
Integrated with **LangSmith**, the system provides full-lifecycle tracing. Every execution, node transition, and LLM call is monitored, enabling rapid debugging and continuous performance optimization.

---

## 🛡️ Security & Privacy Mitigations

### 1. PII & Local Processing
By utilizing **local embedding models** for semantic similarity, we reduce the volume of data transmitted over the wire. Initial filtering can happen on-premise or within private cloud environments.

### 2. Input Sanitization & Prompt Safety
We employ **Pydantic-based Structured Outputs** to prevent prompt injection attacks. By forcing the LLM to adhere to a strict JSON schema, adversarial inputs cannot break the application logic or leak system prompts.

### 3. Fail-Safe Ingestion
The system handles malformed or encrypted documents gracefully, flagging them for human review rather than failing silently or introducing noise into the model.

---

## ⚙️ Setup Instructions

### Prerequisites
- Python 3.10+
- Google Gemini API Key
- LangChain API Key (Optional, for LangSmith tracing)

### Installation
1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd hr_agent
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment:**
   Create a `.env` file in the `hr_agent` directory:
   ```env
   GOOGLE_API_KEY=your_gemini_api_key_here
   LANGCHAIN_TRACING_V2=true
   LANGCHAIN_API_KEY=your_langsmith_key_here
   ```

4. **Run the Application:**
   ```bash
   streamlit run app.py
   ```

---

### 👨‍💻 Developed by Engineering Teams at Travel Corporation India Ltd
*Engineering the future of recruitment with responsible AI.*
