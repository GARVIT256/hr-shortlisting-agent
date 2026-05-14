import os
import uuid
from dotenv import load_dotenv
from src.agent import build_hr_agent

def create_mock_data():
    os.makedirs("data/resumes", exist_ok=True)
    jd = """
    Job Title: Senior AI Engineer
    Experience: 5+ years in machine learning and NLP.
    Skills: Python, LangChain, LlamaIndex, PyTorch, OpenAI API, Prompt Engineering.
    Qualifications: Master's in Computer Science or related field.
    Responsibilities: Build agentic systems, implement RAG pipelines, deploy models to production.
    """
    with open("data/sample_jd.txt", "w", encoding="utf-8") as f:
        f.write(jd)
        
    resumes = {
        "candidate_1_perfect.txt": """
        Alice Smith
        Experience: 6 years of experience building scalable ML models and NLP pipelines.
        Skills: Python, PyTorch, LangChain, LlamaIndex, OpenAI API, AWS.
        Education: MS in Computer Science from MIT.
        Projects: Built an enterprise RAG system that improved search accuracy by 40%. Developed agentic workflows.
        Communication is clear and professional.
        """,
        "candidate_2_good.txt": """
        Bob Jones
        Experience: 4 years as a Data Scientist focusing on NLP.
        Skills: Python, TensorFlow, scikit-learn, OpenAI API, Prompt Engineering.
        Education: BS in Computer Science.
        Projects: Implemented semantic search using vector databases.
        Clear communicator, team player.
        """,
        "candidate_3_fresher.txt": """
        Charlie Brown
        Experience: 6 months internship in software development.
        Skills: Java, Python, HTML, CSS.
        Education: B.Tech in Information Technology.
        Projects: Built a library management system.
        Looking for an entry-level role to learn and grow.
        """,
        "candidate_4_unrelated.txt": """
        Diana Prince
        Experience: 8 years in Marketing and Sales.
        Skills: SEO, Content Strategy, Google Analytics, CRM.
        Education: MBA in Marketing.
        Projects: Led a campaign that increased sales by 20%.
        Excellent presentation and communication skills.
        """,
        "candidate_5_linkedin.json": """
        {
            "name": "Eve Davis",
            "headline": "AI Engineer | LLMs | RAG",
            "experience": "5 years building GenAI applications using LangChain and LlamaIndex.",
            "skills": ["Python", "LangChain", "OpenAI", "Vector DBs", "Docker"],
            "education": "MSc Artificial Intelligence",
            "projects": "Deployed multi-agent systems for financial analysis."
        }
        """
    }
    
    for filename, content in resumes.items():
        with open(f"data/resumes/{filename}", "w", encoding="utf-8") as f:
            f.write(content.strip())
            
    return "data/sample_jd.txt", [f"data/resumes/{f}" for f in resumes.keys()]

def main():
    load_dotenv()
    
    if not os.getenv("GOOGLE_API_KEY"):
        print("CRITICAL: Please set GOOGLE_API_KEY in your .env file")
        return
    
    print("\n" + "="*60)
    print("HR RESUME & LINKEDIN SHORTLISTING AGENT PROTOTYPE")
    print("="*60)
    
    print("\n[1] Initializing Sandbox & Mock Data...")
    jd_path, resume_files = create_mock_data()
    
    with open(jd_path, "r", encoding="utf-8") as f:
        jd_text = f.read()
        
    agent = build_hr_agent()
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    print("\n[2] Starting Agent Execution (Semantic Matching + LLM Reasoning)...")
    inputs = {
        "jd_text": jd_text,
        "resume_files": resume_files
    }
    
    # Run the graph until the interrupt point
    for event in agent.stream(inputs, config=config, stream_mode="values"):
        if "parsed_jd" in event and "candidates" not in event:
            print(f"    [+] JD Parsed: {event['parsed_jd'].title}")
        elif "candidates" in event:
            print(f"    [+] Candidates Scored: {len(event['candidates'])}")
            
    state = agent.get_state(config)
    
    print("\n" + "-"*60)
    print("HUMAN-IN-THE-LOOP INTERVENTION")
    print("-"*60)
    
    candidates = state.values.get("candidates", [])
    for idx, c in enumerate(candidates):
        print(f"\n({idx+1}) Candidate: {c.name}")
        print(f"    Score: {c.score.total_score:.2f}/10.0 | Sim: {c.score.semantic_similarity:.2f} | Rec: {c.score.recommendation}")
        print(f"    Skills [{c.score.skills_match_score}]: {c.score.skills_match_justification}")
        print(f"    Exp    [{c.score.experience_relevance_score}]: {c.score.experience_relevance_justification}")
        
    print("\nDo you want to override any total scores? (yes/no)")
    try:
        ans = input("Override? (y/n): ").strip().lower()
        if ans in ['y', 'yes']:
            idx_str = input("Enter candidate number to override (e.g., 1): ").strip()
            if idx_str.isdigit() and 1 <= int(idx_str) <= len(candidates):
                idx = int(idx_str) - 1
                c = candidates[idx]
                new_score = float(input(f"Enter new weighted total score for {c.name} (0-10): "))
                reason = input("Enter reason for override: ")
                c.score.human_override_score = new_score
                c.score.human_override_reason = reason
                print(f"    [!] Score for {c.name} updated to {new_score}")
                    
            # Update state with modified candidates
            agent.update_state(config, {"candidates": candidates})
    except (EOFError, KeyboardInterrupt):
        print("\nSkipping override...")
        
    print("\n[3] Generating Final Shortlist Report...")
    # Resume the graph
    for event in agent.stream(None, config=config, stream_mode="values"):
        pass
            
    final_state = agent.get_state(config)
    if "report" in final_state.values:
        print("\nFINAL REPORT:\n")
        print(final_state.values["report"])
        print("\n" + "="*60)

if __name__ == "__main__":
    main()
