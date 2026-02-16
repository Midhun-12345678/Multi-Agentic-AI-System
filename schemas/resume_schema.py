from pydantic import BaseModel
from typing import List

class Experience(BaseModel):
    role: str
    company: str
    description: str

class Project(BaseModel):
    title: str
    details: str

class ResumeSchema(BaseModel):
    name: str
    email: str
    phone: str
    linkedin: str
    github: str

    summary: str
    skills: List[str]
    experience: List[Experience]
    projects: List[Project]
    education: str