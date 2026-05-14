from langchain_core.prompts import ChatPromptTemplate
from src.models import JobDescription

def parse_job_description(jd_text: str, llm) -> JobDescription:
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are an expert HR Analyst. Extract the key requirements from the provided Job Description."),
        ("user", "{jd_text}")
    ])
    chain = prompt | llm.with_structured_output(JobDescription)
    return chain.invoke({"jd_text": jd_text})
