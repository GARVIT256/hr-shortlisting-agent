import streamlit as st
import os
import uuid
import tempfile
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Import the agent components
from src.agent import build_hr_agent
from src.ingestion import ingest_file

st.set_page_config(page_title="HR Resume Agent", page_icon="🤖", layout="wide")

st.title("🤖 HR Resume Shortlisting Agent")
st.markdown("Evaluate candidate resumes against a Job Description using Gemini 2.0 Flash, Local Embeddings, and LangGraph.")

# Initialize Session State
if "thread_id" not in st.session_state:
    st.session_state.thread_id = str(uuid.uuid4())
if "agent" not in st.session_state:
    st.session_state.agent = build_hr_agent()
if "step" not in st.session_state:
    st.session_state.step = "upload" # upload -> hitl -> report
if "temp_dir" not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()

config = {"configurable": {"thread_id": st.session_state.thread_id}}
agent = st.session_state.agent

with st.sidebar:
    st.header("1. Upload Documents")
    
    jd_file = st.file_uploader("Upload Job Description", type=["txt", "pdf", "docx"], key="jd")
    resume_files = st.file_uploader("Upload Resumes", type=["txt", "pdf", "docx", "json"], accept_multiple_files=True, key="resumes")
    
    if st.button("Run Evaluation", type="primary"):
        if jd_file and resume_files:
            # Save JD
            jd_path = os.path.join(st.session_state.temp_dir, jd_file.name)
            with open(jd_path, "wb") as f:
                f.write(jd_file.getbuffer())
                
            # Extract text from JD for the graph
            jd_text = ingest_file(jd_path)
            
            # Save Resumes
            saved_resume_paths = []
            for rf in resume_files:
                r_path = os.path.join(st.session_state.temp_dir, rf.name)
                with open(r_path, "wb") as f:
                    f.write(rf.getbuffer())
                saved_resume_paths.append(r_path)
                
            with st.spinner("Processing documents and scoring candidates..."):
                inputs = {
                    "jd_text": jd_text,
                    "resume_files": saved_resume_paths
                }
                
                # Run the graph up to the interrupt point
                for event in agent.stream(inputs, config=config, stream_mode="values"):
                    pass
                
                st.session_state.step = "hitl"
                st.rerun()
        else:
            st.error("Please upload both a JD and at least one resume.")

if st.session_state.step == "hitl":
    st.header("2. Human-in-the-Loop Override")
    st.info("Review the AI's preliminary scores and evidence. You can override the total score for any candidate.")
    
    state = agent.get_state(config)
    candidates = state.values.get("candidates", [])
    
    with st.form("hitl_form"):
        for idx, c in enumerate(candidates):
            if not c.score:
                st.warning(f"Failed to score candidate: {c.name}")
                continue
                
            st.subheader(f"Candidate: {c.name}")
            col1, col2 = st.columns([1, 1])
            with col1:
                st.metric("AI Total Score", f"{c.score.total_score:.2f} / 10")
                st.metric("Semantic Similarity", f"{c.score.semantic_similarity:.2f}")
                st.metric("AI Recommendation", c.score.recommendation)
            with col2:
                # Override inputs
                new_score = st.number_input(f"Override Score (0-10)", min_value=0.0, max_value=10.0, value=float(c.score.total_score), key=f"score_{idx}")
                reason = st.text_input(f"Override Reason (optional)", key=f"reason_{idx}")
                
            with st.expander("View Detailed Evidence & Justifications"):
                dimensions = [
                    ("Skills Match", c.score.skills_match_score, c.score.skills_match_justification, c.score.skills_match_evidence),
                    ("Experience Relevance", c.score.experience_relevance_score, c.score.experience_relevance_justification, c.score.experience_relevance_evidence),
                    ("Education & Certs", c.score.education_certs_score, c.score.education_certs_justification, c.score.education_certs_evidence),
                    ("Project/Portfolio", c.score.project_portfolio_score, c.score.project_portfolio_justification, c.score.project_portfolio_evidence),
                    ("Communication Quality", c.score.communication_quality_score, c.score.communication_quality_justification, c.score.communication_quality_evidence)
                ]
                for label, score, just, quotes in dimensions:
                    st.markdown(f"**{label} [{score}/10]:** {just}")
                    for q in quotes:
                        st.markdown(f"  - > *\"{q}\"*")
            st.divider()
            
        submit_hitl = st.form_submit_button("Approve & Generate Final Report", type="primary")
        
        if submit_hitl:
            # Apply overrides
            for idx, c in enumerate(candidates):
                if c.score:
                    override_score = st.session_state[f"score_{idx}"]
                    override_reason = st.session_state[f"reason_{idx}"]
                    if override_score != float(c.score.total_score) and override_reason:
                        c.score.human_override_score = override_score
                        c.score.human_override_reason = override_reason
            
            # Update state in graph
            agent.update_state(config, {"candidates": candidates})
            
            with st.spinner("Generating final report..."):
                # Resume execution
                for event in agent.stream(None, config=config, stream_mode="values"):
                    pass
                st.session_state.step = "report"
                st.rerun()

if st.session_state.step == "report":
    st.header("3. Final Shortlisting Report")
    
    state = agent.get_state(config)
    report_md = state.values.get("report", "Report generation failed.")
    
    # We display the generated markdown report directly
    st.markdown(report_md)
    
    if st.button("Start Over"):
        # Reset state
        st.session_state.thread_id = str(uuid.uuid4())
        st.session_state.step = "upload"
        st.rerun()
