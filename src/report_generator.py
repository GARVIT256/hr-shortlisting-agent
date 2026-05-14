from src.models import CandidateProfile
from typing import List
import pandas as pd
from tabulate import tabulate
import json

def generate_report(candidates: List[CandidateProfile], format_type: str = 'markdown') -> str:
    # Sort candidates by final score descending
    sorted_candidates = sorted(candidates, key=lambda c: c.score.get_final_score() if c.score else 0, reverse=True)
    
    data = []
    for c in sorted_candidates:
        if not c.score:
            continue
        row = {
            "Candidate": c.name,
            "Total Score": f"{c.score.get_final_score():.2f}",
            "Recommendation": c.score.recommendation,
            "Semantic Sim": f"{c.score.semantic_similarity:.2f}",
            "Skills": c.score.skills_match_score,
            "Exp": c.score.experience_relevance_score,
            "Edu": c.score.education_certs_score,
            "Proj": c.score.project_portfolio_score,
            "Comm": c.score.communication_quality_score,
            "Override": "Yes" if c.score.human_override_score is not None else "No"
        }
        # Add evidence to JSON/Data for completeness
        row["evidence"] = {
            "skills_match": {"justification": c.score.skills_match_justification, "quotes": c.score.skills_match_evidence},
            "experience_relevance": {"justification": c.score.experience_relevance_justification, "quotes": c.score.experience_relevance_evidence},
            "education_certs": {"justification": c.score.education_certs_justification, "quotes": c.score.education_certs_evidence},
            "project_portfolio": {"justification": c.score.project_portfolio_justification, "quotes": c.score.project_portfolio_evidence},
            "communication_quality": {"justification": c.score.communication_quality_justification, "quotes": c.score.communication_quality_evidence}
        }
        data.append(row)
        
    df = pd.DataFrame(data).drop(columns=['evidence'])
    
    if format_type == 'json':
        return json.dumps(data, indent=2)
    elif format_type == 'html':
        return df.to_html(index=False)
    else:
        # Markdown summary table
        report = "# HR Shortlisting Report\n\n"
        report += "## Summary Table\n"
        report += tabulate(df, headers='keys', tablefmt='pipe', showindex=False)
        report += "\n\n## Detailed Candidate Breakdown (Evidence-Based)\n"
        
        for c in sorted_candidates:
            if not c.score: continue
            report += f"\n### {c.name} - Total Score: {c.score.get_final_score():.2f}/10\n"
            report += f"**Recommendation:** {c.score.recommendation}\n\n"
            
            dimensions = [
                ("Skills Match", c.score.skills_match_score, c.score.skills_match_justification, c.score.skills_match_evidence),
                ("Experience Relevance", c.score.experience_relevance_score, c.score.experience_relevance_justification, c.score.experience_relevance_evidence),
                ("Education & Certs", c.score.education_certs_score, c.score.education_certs_justification, c.score.education_certs_evidence),
                ("Project/Portfolio", c.score.project_portfolio_score, c.score.project_portfolio_justification, c.score.project_portfolio_evidence),
                ("Communication Quality", c.score.communication_quality_score, c.score.communication_quality_justification, c.score.communication_quality_evidence)
            ]
            
            for label, score, justification, quotes in dimensions:
                report += f"- **{label} [{score}/10]:** {justification}\n"
                for q in quotes:
                    report += f"  - *\"{q}\"*\n"
            
            if c.score.human_override_score is not None:
                report += f"\n> **Human Override:** {c.score.human_override_score} (Reason: {c.score.human_override_reason})\n"
                
        return report
