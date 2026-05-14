import os
import operator
import streamlit as st
from typing import TypedDict, List, Annotated, Union
from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver
from langchain_google_genai import ChatGoogleGenerativeAI
from pathlib import Path

from src.models import JobDescription, CandidateProfile
from src.jd_parser import parse_job_description
from src.ingestion import ingest_file
from src.scoring_engine import score_candidate
from src.report_generator import generate_report

class AgentState(TypedDict):
    jd_text: str
    resume_files: List[str]
    parsed_jd: JobDescription
    # Annotated with operator.add to handle parallel results aggregation
    candidates: Annotated[List[CandidateProfile], operator.add]
    report: str

def get_llm():
    """
    Initializes the Google Gemini LLM. 
    Using gemini-2.0-flash with transport='rest' for maximum compatibility on Cloud.
    """
    # Try getting from Streamlit secrets first (Cloud), then environment (Local)
    api_key = None
    try:
        if "GOOGLE_API_KEY" in st.secrets:
            api_key = st.secrets["GOOGLE_API_KEY"]
    except:
        pass
        
    if not api_key:
        api_key = os.getenv("GOOGLE_API_KEY")
        
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not found. Please set it in Streamlit Secrets or your .env file.")
        
    return ChatGoogleGenerativeAI(
        model="gemini-2.0-flash", 
        temperature=0, 
        google_api_key=api_key,
        transport="rest" # Fixes 'redacted' gRPC errors on Streamlit Cloud
    )

def parse_jd_node(state: AgentState):
    try:
        llm = get_llm()
        parsed_jd = parse_job_description(state["jd_text"], llm)
        return {"parsed_jd": parsed_jd}
    except Exception as e:
        # Catch and display the actual error in Streamlit to bypass redaction
        st.error(f"Error in JD Parsing: {str(e)}")
        raise e

def score_single_candidate(file_path: str, jd: JobDescription):
    """Worker function for parallel candidate scoring."""
    llm = get_llm()
    text = ingest_file(file_path)
    name = Path(file_path).stem
    
    # Bypass scoring if ingestion failed
    if text.startswith("STATUS: UNPARSEABLE"):
        return CandidateProfile(name=name, source_file=file_path, parsed_text=text, score=None)
    
    score = score_candidate(text, jd, llm)
    return CandidateProfile(name=name, source_file=file_path, parsed_text=text, score=score)

def ingest_and_score_parallel_node(state: AgentState):
    """
    Processes candidates in parallel using a simple map. 
    In a high-scale production system, we'd use LangGraph's Send API,
    but for this prototype, concurrent thread execution is efficient and clean.
    """
    import concurrent.futures
    
    candidates = []
    with concurrent.futures.ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(score_single_candidate, f, state["parsed_jd"]) 
            for f in state["resume_files"]
        ]
        for future in concurrent.futures.as_completed(futures):
            candidates.append(future.result())
            
    return {"candidates": candidates}

def generate_report_node(state: AgentState):
    # Filter out candidates with failed scoring and recalculate totals for overrides
    valid_candidates = [c for c in state["candidates"] if c.score is not None]
    
    for c in valid_candidates:
        c.score.calculate_total()
            
    report = generate_report(valid_candidates, format_type='markdown')
    return {"report": report}

def build_hr_agent():
    workflow = StateGraph(AgentState)
    
    workflow.add_node("parse_jd", parse_jd_node)
    workflow.add_node("ingest_and_score", ingest_and_score_parallel_node)
    workflow.add_node("generate_report", generate_report_node)
    
    workflow.add_edge(START, "parse_jd")
    workflow.add_edge("parse_jd", "ingest_and_score")
    workflow.add_edge("ingest_and_score", "generate_report")
    workflow.add_edge("generate_report", END)
    
    memory = MemorySaver()
    # Interrupt before generating the report to allow Human-In-The-Loop override
    app = workflow.compile(checkpointer=memory, interrupt_before=["generate_report"])
    return app
