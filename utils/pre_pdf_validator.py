"""
Pre-PDF validation to ensure data integrity.
Compares original resume fields with final structured data.
"""

import re
from typing import Dict, List, Tuple
from schemas.resume_schema import ResumeSchema


def validate_resume_data(original_text: str, structured_data: ResumeSchema) -> Dict:
    """
    Validate that all critical fields from original resume are preserved in structured data.
    
    Returns:
        Dict with validation results including warnings and field mapping status
    """
    validation_result = {
        "passed": True,
        "warnings": [],
        "field_mapping": {
            "name": False,
            "email": False,
            "phone": False,
            "linkedin": False,
            "github": False,
            "education": False,
            "experience_count": {"original": 0, "final": 0, "match": False},
            "projects_count": {"original": 0, "final": 0, "match": False},
            "skills_count": {"original": 0, "final": 0, "match": False}
        },
        "data_integrity_score": 0.0
    }
    
    # 1. Check name
    if structured_data.name and len(structured_data.name.strip()) > 2:
        validation_result["field_mapping"]["name"] = True
    else:
        validation_result["warnings"].append("Name is missing or invalid")
        validation_result["passed"] = False
    
    # 2. Check email
    if structured_data.email and "@" in structured_data.email:
        validation_result["field_mapping"]["email"] = True
    else:
        # Check if email exists in original
        if re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', original_text):
            validation_result["warnings"].append("Email found in original but not mapped")
    
    # 3. Check phone
    if structured_data.phone:
        validation_result["field_mapping"]["phone"] = True
    else:
        # Check if phone exists in original
        if re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', original_text):
            validation_result["warnings"].append("Phone number found in original but not mapped")
    
    # 4. Check LinkedIn
    if structured_data.linkedin:
        validation_result["field_mapping"]["linkedin"] = True
    else:
        # Check if LinkedIn exists in original
        if re.search(r'linkedin\.com', original_text, re.I):
            validation_result["warnings"].append("LinkedIn URL found in original but not mapped")
    
    # 5. Check GitHub
    if structured_data.github:
        validation_result["field_mapping"]["github"] = True
    else:
        # Check if GitHub exists in original (less critical)
        if re.search(r'github\.com', original_text, re.I):
            validation_result["warnings"].append("GitHub URL found in original but not mapped (minor)")
    
    # 6. Check education
    if structured_data.education and len(structured_data.education.strip()) > 10:
        validation_result["field_mapping"]["education"] = True
    else:
        # Check if education section exists in original
        if re.search(r'(education|degree|university|college|bachelor|master|phd)', original_text, re.I):
            validation_result["warnings"].append("Education section found in original but not properly mapped")
            validation_result["passed"] = False
    
    # 7. Count experience entries
    original_exp_count = count_experience_entries(original_text)
    final_exp_count = len(structured_data.experience)
    
    validation_result["field_mapping"]["experience_count"] = {
        "original": original_exp_count,
        "final": final_exp_count,
        "match": original_exp_count == final_exp_count
    }
    
    if original_exp_count > final_exp_count:
        validation_result["warnings"].append(
            f"Experience mismatch: {original_exp_count} jobs in original, only {final_exp_count} mapped"
        )
        validation_result["passed"] = False
    
    # 8. Count project entries
    original_proj_count = count_project_entries(original_text)
    final_proj_count = len(structured_data.projects)
    
    validation_result["field_mapping"]["projects_count"] = {
        "original": original_proj_count,
        "final": final_proj_count,
        "match": original_proj_count <= final_proj_count  # Allow adding projects
    }
    
    if original_proj_count > final_proj_count and original_proj_count > 0:
        validation_result["warnings"].append(
            f"Projects mismatch: {original_proj_count} projects in original, only {final_proj_count} mapped"
        )
    
    # 9. Count skills
    original_skills_count = count_skills(original_text)
    final_skills_count = len(structured_data.skills)
    
    validation_result["field_mapping"]["skills_count"] = {
        "original": original_skills_count,
        "final": final_skills_count,
        "match": final_skills_count >= original_skills_count  # Allow adding skills
    }
    
    if final_skills_count < original_skills_count * 0.8:  # Lost more than 20% of skills
        validation_result["warnings"].append(
            f"Skills mismatch: {original_skills_count} skills in original, only {final_skills_count} mapped"
        )
    
    # Calculate data integrity score (0-100)
    validation_result["data_integrity_score"] = calculate_integrity_score(validation_result["field_mapping"])
    
    return validation_result


def count_experience_entries(text: str) -> int:
    """
    Estimate number of work experience entries in resume text.
    Looks for patterns like job titles, companies, date ranges.
    """
    # Look for date ranges (e.g., "2020 - 2023", "Jan 2020 - Present")
    date_pattern = r'(\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})\s*[-–—]\s*(\d{4}|Present|Current|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})'
    date_matches = re.findall(date_pattern, text, re.I)
    
    # Count unique date ranges (likely one per job)
    return len(date_matches)


def count_project_entries(text: str) -> int:
    """
    Estimate number of project entries in resume text.
    Looks for project section headers and project patterns.
    """
    # Look for "Projects" section
    if not re.search(r'projects?|portfolio', text, re.I):
        return 0
    
    # Extract projects section
    projects_match = re.search(r'(projects?|portfolio)[:\s]*\n(.+?)(?=\n\s*[A-Z][a-z]+\s*:|$)', text, re.I | re.S)
    if not projects_match:
        return 0
    
    projects_section = projects_match.group(2)
    
    # Count bullet points or lines that look like project entries
    # Look for lines starting with -, •, *, or capitalized words followed by colon
    project_lines = re.findall(r'^[\s]*[-•*]|^[A-Z][^:\n]{5,50}:', projects_section, re.M)
    
    # Estimate: roughly 2-3 lines per project
    return max(1, len(project_lines) // 2)


def count_skills(text: str) -> int:
    """
    Estimate number of skills in resume text.
    """
    # Look for skills section
    skills_match = re.search(r'(skills?|technologies?|competencies)[:\s]*\n(.+?)(?=\n\s*[A-Z][a-z]+\s*:|$)', text, re.I | re.S)
    if not skills_match:
        return 0
    
    skills_section = skills_match.group(2)
    
    # Count comma-separated items or bullet points
    comma_items = skills_section.split(',')
    bullet_items = re.findall(r'^[\s]*[-•*]\s*(.+)$', skills_section, re.M)
    
    return max(len(comma_items), len(bullet_items))


def calculate_integrity_score(field_mapping: Dict) -> float:
    """
    Calculate data integrity score (0-100) based on field mapping.
    """
    weights = {
        "name": 15,
        "email": 10,
        "phone": 5,
        "linkedin": 5,
        "github": 3,
        "education": 15,
        "experience_count": 30,
        "projects_count": 10,
        "skills_count": 7
    }
    
    score = 0.0
    
    for field, weight in weights.items():
        if field in ["experience_count", "projects_count", "skills_count"]:
            if field_mapping[field].get("match"):
                score += weight
        else:
            if field_mapping.get(field):
                score += weight
    
    return round(score, 1)


def format_validation_warnings(warnings: List[str]) -> str:
    """
    Format validation warnings for display.
    """
    if not warnings:
        return "✅ No validation warnings"
    
    return "\n".join([f"⚠️ {warning}" for warning in warnings])
