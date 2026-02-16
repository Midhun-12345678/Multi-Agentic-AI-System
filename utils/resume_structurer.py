import re
from schemas.resume_schema import ResumeSchema, Experience, Project
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def structure_resume(agent_output: dict, original_resume_text: str = "") -> ResumeSchema:
    """
    Converts LLM text output into structured resume fields.
    Extracts contact info from original resume if provided.
    """

    text = agent_output.get("final", "")
    
    # DEBUG: Log the actual agent output
    logger.info("\n" + "="*80)
    logger.info("RAW AGENT OUTPUT (final):")
    logger.info(text)
    logger.info("="*80 + "\n")

    # Extract name - try to get it from the first line or look for common patterns
    name = extract_name(text, original_resume_text)
    
    # Extract contact information from original resume
    contact_info = extract_contact_info(original_resume_text if original_resume_text else text)

    # Extract sections with flexible matching (case-insensitive, flexible headers)
    summary = extract_section(text, ["SUMMARY", "PROFESSIONAL SUMMARY", "PROFILE", "OBJECTIVE"])
    logger.info(f"Extracted summary: {summary[:100] if summary else 'EMPTY'}...")
    
    skills = extract_bullets(text, ["TECHNICAL SKILLS", "SKILLS", "CORE COMPETENCIES", "TECHNOLOGIES"])
    logger.info(f"Extracted skills: {skills}")
    
    education = extract_section(text, ["EDUCATION", "ACADEMIC BACKGROUND"])
    logger.info(f"Extracted education: {education[:100] if education else 'EMPTY'}...")
    
    # Extract experience entries
    experience_list = extract_experience_entries(text)
    logger.info(f"Extracted {len(experience_list)} experience entries")
    
    # Extract projects
    projects_list = extract_project_entries(text)
    logger.info(f"Extracted {len(projects_list)} project entries")

    return ResumeSchema(
        name=name,
        email=contact_info.get("email", ""),
        phone=contact_info.get("phone", ""),
        linkedin=contact_info.get("linkedin", ""),
        github=contact_info.get("github", ""),
        summary=summary,
        skills=skills,
        experience=experience_list if experience_list else [],
        projects=projects_list if projects_list else [],
        education=education
    )


def extract_name(text: str, original_text: str = "") -> str:
    """Extract name from resume text."""
    # Try original text first
    if original_text:
        lines = original_text.split("\n")
        for line in lines[:5]:  # Check first 5 lines
            line = line.strip()
            # Name is typically short, has capital letters, no special chars
            if line and len(line) < 50 and not any(c in line for c in ['@', 'http', '|', '•']):
                if re.match(r'^[A-Z][a-zA-Z\s\.]+$', line):
                    return line
    
    # Fall back to first line of agent output
    first_line = text.split("\n")[0].strip()
    # Clean up if it has section markers
    first_line = re.sub(r'^#+\s*', '', first_line)  # Remove markdown headers
    return first_line if first_line else "Resume"


def extract_contact_info(text: str) -> dict:
    """Extract email, phone, LinkedIn, and GitHub from text."""
    contact = {
        "email": "",
        "phone": "",
        "linkedin": "",
        "github": ""
    }
    
    # Email pattern
    email_match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    if email_match:
        contact["email"] = email_match.group(0)
    
    # Phone pattern (various formats)
    phone_match = re.search(r'(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}', text)
    if phone_match:
        contact["phone"] = phone_match.group(0)
    
    # LinkedIn pattern
    linkedin_match = re.search(r'(linkedin\.com/in/[\w-]+|linkedin\.com/pub/[\w-]+)', text, re.I)
    if linkedin_match:
        contact["linkedin"] = linkedin_match.group(0)
    
    # GitHub pattern
    github_match = re.search(r'(github\.com/[\w-]+)', text, re.I)
    if github_match:
        contact["github"] = github_match.group(0)
    
    return contact


def extract_section(text: str, section_names: list) -> str:
    """Extract content from a section with flexible header matching."""
    for section in section_names:
        # Match markdown headers (###, ##) and plain headers, case-insensitive
        pattern = rf"(?:^|\n)\s*(?:###?\s*)?{section}\s*[:.]?\s*\n(.+?)(?=\n\s*(?:###?\s*)?[A-Z][a-zA-Z\s]{{2,}}[:.]?\s*\n|\Z)"
        match = re.search(pattern, text, re.S | re.I | re.M)
        if match:
            content = match.group(1).strip()
            # Remove markdown bold/italic
            content = re.sub(r'\*\*(.+?)\*\*', r'\1', content)
            content = re.sub(r'\*(.+?)\*', r'\1', content)
            # Clean up bullet points
            content = re.sub(r'\n\s*[-•]\s*', '\n', content)
            return content.strip()
    return ""


def extract_bullets(text: str, section_names: list) -> list:
    """Extract bullet points from a section as a list."""
    section_text = extract_section(text, section_names)
    if not section_text:
        return []
    
    bullets = []
    for line in section_text.split("\n"):
        line = line.strip()
        if line:
            # Remove common bullet markers
            line = re.sub(r'^[-•*▪▸►]\s*', '', line)
            if line:
                bullets.append(line)
    
    return bullets


def extract_experience_entries(text: str) -> list:
    """Extract multiple experience entries with role, company, and description."""
    experiences = []
    
    # Find the experience section
    section_text = extract_section(text, ["PROFESSIONAL EXPERIENCE", "EXPERIENCE", "WORK EXPERIENCE", "EMPLOYMENT"])
    
    if not section_text:
        return []
    
    # Split by markdown bold headers (**Role**) or typical role patterns
    entries = re.split(r'\n(?=\*\*[^*\n]+\*\*)', section_text)
    
    for entry in entries:
        if not entry.strip():
            continue
            
        lines = [l.strip() for l in entry.split("\n") if l.strip()]
        if not lines:
            continue
        
        # First line contains role (might be in markdown bold)
        first_line = lines[0]
        first_line = re.sub(r'\*\*(.+?)\*\*', r'\1', first_line)  # Remove bold
        
        # Try to parse "Role (Type)" or just "Role"
        role = first_line
        
        # Second line is usually company/location
        if len(lines) > 1:
            company = lines[1]
            description = "\n".join(lines[2:]) if len(lines) > 2 else ""
        else:
            company = "Company"
            description = ""
        
        # Clean up markdown from description
        description = re.sub(r'\*\*(.+?)\*\*', r'\1', description)
        description = re.sub(r'\*(.+?)\*', r'\1', description)
        
        experiences.append(Experience(
            role=role.strip(),
            company=company.strip(),
            description=description.strip()
        ))
    
    return experiences


def extract_project_entries(text: str) -> list:
    """Extract multiple project entries with title and details."""
    projects = []
    
    # Find the projects section
    section_text = extract_section(text, ["PROJECTS", "KEY PROJECTS", "NOTABLE PROJECTS"])
    
    if not section_text:
        return []
    
    # Split by markdown bold headers (**Project Name**) or typical project patterns
    entries = re.split(r'\n(?=\*\*[^*\n]+\*\*)', section_text)
    
    for entry in entries:
        if not entry.strip():
            continue
            
        lines = [l.strip() for l in entry.split("\n") if l.strip()]
        if not lines:
            continue
        
        # First line is the title (remove markdown bold)
        title = lines[0]
        title = re.sub(r'\*\*(.+?)\*\*', r'\1', title)
        
        # Rest is details (skip lines that are just role descriptions like *Backend Developer*)
        details_lines = []
        skip_next = False
        for i in range(1, len(lines)):
            line = lines[i]
            # Skip single-word italic lines (role descriptions)
            if re.match(r'^\*[^*]+\*$', line) and len(line.split()) <= 3:
                skip_next = True
                continue
            # Remove markdown
            cleaned = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
            cleaned = re.sub(r'\*(.+?)\*', r'\1', cleaned)
            details_lines.append(cleaned)
        
        details = "\n".join(details_lines)
        
        projects.append(Project(
            title=title,
            details=details.strip()
        ))
    
    return projects
