from typing import Optional
import torch
from sentence_transformers import SentenceTransformer, util
from langchain_core.prompts import ChatPromptTemplate
from src.models import CandidateScore, JobDescription

# Initialize local embedding model
# We use a lightweight but capable model for local semantic matching
embed_model = SentenceTransformer('all-MiniLM-L6-v2')

def get_semantic_similarity(text1: str, text2: str) -> float:
    """Calculates cosine similarity between two texts using local embeddings."""
    embeddings1 = embed_model.encode(text1, convert_to_tensor=True)
    embeddings2 = embed_model.encode(text2, convert_to_tensor=True)
    cosine_scores = util.cos_sim(embeddings1, embeddings2)
    return float(cosine_scores[0][0])

def score_candidate(candidate_text: str, jd: JobDescription, llm) -> CandidateScore:
    """
    Evaluates a candidate resume against a Job Description using a hybrid approach:
    1. Local Semantic Similarity (Embeddings)
    2. Detailed dimension scoring (LLM reasoning)
    """
    
    # 1. Local Semantic Similarity - Fixed skill formatting
    skills_str = ", ".join(jd.skills)
    similarity = get_semantic_similarity(candidate_text, f"{jd.title} {skills_str} {jd.experience}")
    
    # 2. LLM Reasoning for structured scoring
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a Senior Technical Recruiter.
Evaluate the provided Resume against the Job Description (JD).
You must provide a score of exactly 0, 5, or 10 for each of the following dimensions:

- Skills Match (30%): How well do technical skills align?
- Experience Relevance (25%): Does the candidate have the right years and type of experience?
- Education & Certs (15%): Does the candidate meet academic/certification requirements?
- Project/Portfolio (20%): Quality and relevance of listed projects/GitHub/portfolio.
- Communication Quality (10%): Clarity, professional tone, and structure of the resume.

Scoring Key:
- 0: Minimal to no match.
- 5: Partial match / meets some requirements.
- 10: Excellent match / exceeds requirements.

For every score you assign across the 5 dimensions, you MUST:
1. Provide a concise one-line justification.
2. Extract 1 to 3 direct, verbatim quotes from the candidate's resume that justify your score. 
Do not hallucinate, summarize, or paraphrase these quotes. They must be exactly as they appear in the resume.
"""),
        ("user", "### JOB DESCRIPTION:\n{jd}\n\n### CANDIDATE RESUME:\n{resume}")
    ])
    
    scoring_llm = llm.with_structured_output(CandidateScore)
    chain = prompt | scoring_llm
    
    # We pass the JD details for better reasoning
    jd_summary = f"Title: {jd.title}\nSkills: {skills_str}\nExperience: {jd.experience}\nQualifications: {', '.join(jd.qualifications)}"
    
    result = chain.invoke({"jd": jd_summary, "resume": candidate_text})
    
    # Attach semantic similarity score
    result.semantic_similarity = similarity
    
    # Calculate weighted total and recommendation
    result.calculate_total()
        
    return result
