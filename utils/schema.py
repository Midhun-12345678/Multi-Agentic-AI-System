from pydantic import BaseModel
from typing import List, Optional

class ResumeHeader(BaseModel):
    name: str
    title: str
    email: Optional[str]
    phone: Optional[str]
    location: Optional[str]
    links: List[str] = []

class Experience(BaseModel):
    company: str
    role: str
    start: str
    end: str
    bullets: List[str]

class ResumeSchema(BaseModel):
    header: ResumeHeader
    summary: str
    skills: List[str]
    experience: List[Experience]
    projects: List[dict]
    education: List[dict]
    certifications: List[str] = []
