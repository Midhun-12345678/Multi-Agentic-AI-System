from pydantic import BaseModel
from typing import List, Optional

class Experience(BaseModel):
    role: str
    company: str
    start_date: Optional[str] = ""
    end_date: Optional[str] = ""
    location: Optional[str] = ""
    description: str

class Project(BaseModel):
    title: str
    tech_stack: Optional[str] = ""
    details: str

class ResumeSchema(BaseModel):
    name: str
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""

    summary: str = ""
    skills: List[str] = []
    experience: List[Experience] = []
    projects: List[Project] = []
    education: str = ""
    certifications: List[str] = []
    awards: List[str] = []
    languages: List[str] = []