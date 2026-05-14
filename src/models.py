from pydantic import BaseModel, Field, field_validator
from typing import List, Optional

class JobDescription(BaseModel):
    title: str = Field(description="The job title")
    skills: List[str] = Field(description="Required skills and technologies")
    experience: str = Field(description="Required experience level or years")
    qualifications: List[str] = Field(description="Required education and qualifications")

class CandidateScore(BaseModel):
    # Skills Match
    skills_match_score: int = Field(description="Score (0, 5, or 10) for Skills Match (Weight: 30%)")
    skills_match_justification: str = Field(description="1-line justification for Skills Match score")
    skills_match_evidence: List[str] = Field(description="1-3 direct, verbatim quotes from the resume for Skills Match")
    
    # Experience Relevance
    experience_relevance_score: int = Field(description="Score (0, 5, or 10) for Experience Relevance (Weight: 25%)")
    experience_relevance_justification: str = Field(description="1-line justification for Experience Relevance score")
    experience_relevance_evidence: List[str] = Field(description="1-3 direct, verbatim quotes from the resume for Experience Relevance")
    
    # Education & Certs
    education_certs_score: int = Field(description="Score (0, 5, or 10) for Education & Certs (Weight: 15%)")
    education_certs_justification: str = Field(description="1-line justification for Education & Certs score")
    education_certs_evidence: List[str] = Field(description="1-3 direct, verbatim quotes from the resume for Education & Certs")
    
    # Project/Portfolio
    project_portfolio_score: int = Field(description="Score (0, 5, or 10) for Project/Portfolio (Weight: 20%)")
    project_portfolio_justification: str = Field(description="1-line justification for Project/Portfolio score")
    project_portfolio_evidence: List[str] = Field(description="1-3 direct, verbatim quotes from the resume for Project/Portfolio")
    
    # Communication Quality
    communication_quality_score: int = Field(description="Score (0, 5, or 10) for Communication Quality (Weight: 10%)")
    communication_quality_justification: str = Field(description="1-line justification for Communication Quality score")
    communication_quality_evidence: List[str] = Field(description="1-3 direct, verbatim quotes from the resume for Communication Quality")
    
    semantic_similarity: float = Field(default=0.0, description="Local embedding based semantic similarity score (0-1)")
    total_score: float = Field(default=0.0, description="Weighted total score")
    recommendation: str = Field(default="", description="Hire, Strong Hire, or No Hire")
    
    human_override_score: Optional[float] = None
    human_override_reason: Optional[str] = None

    @field_validator('skills_match_score', 'experience_relevance_score', 'education_certs_score', 'project_portfolio_score', 'communication_quality_score')
    @classmethod
    def validate_score(cls, v: int) -> int:
        if v not in [0, 5, 10]:
            if v < 3: return 0
            if v < 8: return 5
            return 10
        return v

    def calculate_total(self):
        # Calculate raw total from LLM scores
        raw_total = (
            (self.skills_match_score * 0.30) +
            (self.experience_relevance_score * 0.25) +
            (self.education_certs_score * 0.15) +
            (self.project_portfolio_score * 0.20) +
            (self.communication_quality_score * 0.10)
        )
        self.total_score = raw_total
        
        # Factor in human override for recommendation
        effective_score = self.get_final_score()
        
        if effective_score >= 8.5:
            self.recommendation = "Strong Hire"
        elif effective_score >= 6.0:
            self.recommendation = "Hire"
        else:
            self.recommendation = "No Hire"

    def get_final_score(self) -> float:
        return self.human_override_score if self.human_override_score is not None else self.total_score

class CandidateProfile(BaseModel):
    name: str
    source_file: str
    parsed_text: str
    score: Optional[CandidateScore] = None
