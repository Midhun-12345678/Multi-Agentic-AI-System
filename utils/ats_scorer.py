"""
ATS (Applicant Tracking System) Keyword Scorer
Extracts keywords from job descriptions and scores resumes against them.
"""

import re
from typing import Dict, List, Set, Tuple
from collections import Counter
import logging

logger = logging.getLogger(__name__)

# Common technical keywords and their variations
KEYWORD_VARIATIONS = {
    "python": ["python", "python3", "py"],
    "javascript": ["javascript", "js", "ecmascript"],
    "typescript": ["typescript", "ts"],
    "react": ["react", "reactjs", "react.js"],
    "node": ["node", "nodejs", "node.js"],
    "django": ["django", "django rest", "drf"],
    "fastapi": ["fastapi", "fast api"],
    "flask": ["flask"],
    "postgresql": ["postgresql", "postgres", "psql"],
    "mysql": ["mysql", "mariadb"],
    "mongodb": ["mongodb", "mongo"],
    "docker": ["docker", "containerization", "containers"],
    "kubernetes": ["kubernetes", "k8s"],
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "azure": ["azure", "microsoft azure"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "git": ["git", "github", "gitlab", "version control"],
    "ci/cd": ["ci/cd", "cicd", "continuous integration", "continuous deployment", "jenkins", "github actions"],
    "rest api": ["rest api", "restful", "rest", "api design"],
    "graphql": ["graphql"],
    "sql": ["sql", "structured query language"],
    "nosql": ["nosql", "non-relational"],
    "agile": ["agile", "scrum", "kanban", "sprint"],
    "microservices": ["microservices", "micro-services", "service-oriented"],
    "linux": ["linux", "unix", "ubuntu", "centos"],
    "testing": ["testing", "unit test", "pytest", "jest", "tdd"],
    "redis": ["redis", "caching"],
    "nginx": ["nginx", "reverse proxy"],
    "machine learning": ["machine learning", "ml", "deep learning", "ai"],
    "data structures": ["data structures", "algorithms", "dsa"],
}

# Soft skills keywords
SOFT_SKILLS = [
    "problem-solving", "problem solving", "analytical",
    "communication", "teamwork", "collaboration", "collaborative",
    "leadership", "mentoring", "management",
    "attention to detail", "detail-oriented",
    "self-motivated", "proactive", "initiative",
    "adaptable", "flexible", "fast learner",
]


def extract_keywords_from_job_description(job_description: str) -> Dict:
    """
    Extract relevant keywords from a job description.
    """
    text = job_description.lower()
    
    technical_skills = []
    soft_skills_found = []
    
    # Extract technical keywords
    for keyword, variations in KEYWORD_VARIATIONS.items():
        for variation in variations:
            if variation.lower() in text:
                if keyword not in technical_skills:
                    technical_skills.append(keyword)
                break
    
    # Extract soft skills
    for skill in SOFT_SKILLS:
        if skill.lower() in text:
            if skill not in soft_skills_found:
                soft_skills_found.append(skill)
    
    # Extract custom keywords (words that appear multiple times)
    words = re.findall(r'\b[a-zA-Z]{3,}\b', text)
    word_counts = Counter(words)
    
    # Filter out common words
    common_words = {'the', 'and', 'for', 'with', 'you', 'will', 'are', 'our', 'your', 
                   'have', 'this', 'that', 'from', 'they', 'been', 'has', 'was',
                   'were', 'their', 'what', 'when', 'where', 'who', 'which', 'how',
                   'about', 'into', 'through', 'during', 'before', 'after', 'above',
                   'below', 'between', 'under', 'again', 'further', 'then', 'once',
                   'here', 'there', 'all', 'each', 'few', 'more', 'most', 'other',
                   'some', 'such', 'only', 'own', 'same', 'than', 'too', 'very',
                   'can', 'just', 'should', 'now', 'experience', 'work', 'working',
                   'team', 'ability', 'skills', 'knowledge', 'strong', 'good',
                   'year', 'years', 'role', 'job', 'position', 'looking', 'seeking',
                   'join', 'company', 'candidate', 'ideal', 'required', 'preferred'}
    
    frequent_keywords = [
        word for word, count in word_counts.items() 
        if count >= 2 and word not in common_words and len(word) > 3
    ]
    
    # Combine all keywords with weights
    all_keywords = {}
    
    for skill in technical_skills:
        all_keywords[skill] = {"weight": 3, "category": "technical"}
    
    for skill in soft_skills_found:
        all_keywords[skill] = {"weight": 2, "category": "soft_skill"}
    
    for keyword in frequent_keywords[:10]:
        if keyword not in all_keywords:
            all_keywords[keyword] = {"weight": 1, "category": "contextual"}
    
    return {
        "technical_skills": technical_skills,
        "soft_skills": soft_skills_found,
        "frequent_keywords": frequent_keywords[:10],
        "all_keywords": all_keywords,
        "total_keywords": len(all_keywords)
    }


def score_resume_against_keywords(resume_text: str, keywords: Dict) -> Dict:
    """
    Score a resume against extracted keywords.
    """
    text = resume_text.lower()
    
    matched = []
    missing = []
    total_weight = 0
    matched_weight = 0
    
    all_keywords = keywords.get("all_keywords", {})
    
    for keyword, info in all_keywords.items():
        weight = info.get("weight", 1)
        total_weight += weight
        
        found = False
        if keyword in KEYWORD_VARIATIONS:
            for variation in KEYWORD_VARIATIONS[keyword]:
                if variation.lower() in text:
                    found = True
                    break
        else:
            if keyword.lower() in text:
                found = True
        
        if found:
            matched.append({
                "keyword": keyword,
                "category": info.get("category"),
                "weight": weight
            })
            matched_weight += weight
        else:
            missing.append({
                "keyword": keyword,
                "category": info.get("category"),
                "weight": weight
            })
    
    score = (matched_weight / total_weight * 100) if total_weight > 0 else 0
    
    technical_matched = [k for k in matched if k["category"] == "technical"]
    technical_missing = [k for k in missing if k["category"] == "technical"]
    soft_matched = [k for k in matched if k["category"] == "soft_skill"]
    soft_missing = [k for k in missing if k["category"] == "soft_skill"]
    
    return {
        "score": round(score, 1),
        "matched_keywords": [k["keyword"] for k in matched],
        "missing_keywords": [k["keyword"] for k in missing],
        "matched_count": len(matched),
        "missing_count": len(missing),
        "total_keywords": len(all_keywords),
        "breakdown": {
            "technical": {
                "matched": [k["keyword"] for k in technical_matched],
                "missing": [k["keyword"] for k in technical_missing],
                "score": len(technical_matched) / (len(technical_matched) + len(technical_missing)) * 100 if (len(technical_matched) + len(technical_missing)) > 0 else 0
            },
            "soft_skills": {
                "matched": [k["keyword"] for k in soft_matched],
                "missing": [k["keyword"] for k in soft_missing],
                "score": len(soft_matched) / (len(soft_matched) + len(soft_missing)) * 100 if (len(soft_matched) + len(soft_missing)) > 0 else 0
            }
        }
    }


def analyze_ats_improvement(
    original_resume: str, 
    optimized_resume: str, 
    job_description: str
) -> Dict:
    """
    Complete ATS analysis comparing original vs optimized resume.
    """
    keywords = extract_keywords_from_job_description(job_description)
    
    original_score = score_resume_against_keywords(original_resume, keywords)
    optimized_score = score_resume_against_keywords(optimized_resume, keywords)
    
    improvement = optimized_score["score"] - original_score["score"]
    
    original_matched = set(original_score["matched_keywords"])
    optimized_matched = set(optimized_score["matched_keywords"])
    
    newly_added = list(optimized_matched - original_matched)
    still_missing = list(set(optimized_score["missing_keywords"]))
    
    return {
        "job_keywords": {
            "technical": keywords["technical_skills"],
            "soft_skills": keywords["soft_skills"],
            "total": keywords["total_keywords"]
        },
        "original": {
            "score": original_score["score"],
            "matched": original_score["matched_keywords"],
            "missing": original_score["missing_keywords"],
            "matched_count": original_score["matched_count"],
            "breakdown": original_score["breakdown"]
        },
        "optimized": {
            "score": optimized_score["score"],
            "matched": optimized_score["matched_keywords"],
            "missing": optimized_score["missing_keywords"],
            "matched_count": optimized_score["matched_count"],
            "breakdown": optimized_score["breakdown"]
        },
        "improvement": {
            "score_change": round(improvement, 1),
            "percentage_change": round(improvement, 1),
            "newly_added_keywords": newly_added,
            "still_missing": still_missing,
            "keywords_added_count": len(newly_added)
        },
        "summary": {
            "original_score": original_score["score"],
            "optimized_score": optimized_score["score"],
            "improvement": round(improvement, 1),
            "grade": get_ats_grade(optimized_score["score"])
        }
    }


def get_ats_grade(score: float) -> str:
    """Convert ATS score to letter grade."""
    if score >= 90:
        return "A+"
    elif score >= 80:
        return "A"
    elif score >= 70:
        return "B"
    elif score >= 60:
        return "C"
    elif score >= 50:
        return "D"
    else:
        return "F"
