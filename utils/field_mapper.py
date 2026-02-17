"""
Field mapping enforcement layer.
Extracts structured baseline from original resume and validates
executor output preserves all data.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


@dataclass
class ResumeBaseline:
    """Baseline data extracted from original resume."""
    name: str = ""
    email: str = ""
    phone: str = ""
    linkedin: str = ""
    github: str = ""
    
    # Counts
    experience_count: int = 0
    project_count: int = 0
    skill_count: int = 0
    
    # Actual items (for comparison)
    companies: List[str] = field(default_factory=list)
    project_titles: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    
    # Education
    has_education: bool = False
    education_text: str = ""


def extract_baseline(resume_text: str) -> ResumeBaseline:
    """
    Extract structured baseline from original resume text.
    This becomes the source of truth for validation.
    """
    baseline = ResumeBaseline()
    
    # Extract contact info
    baseline.email = extract_email(resume_text)
    baseline.phone = extract_phone(resume_text)
    baseline.linkedin = extract_linkedin(resume_text)
    baseline.github = extract_github(resume_text)
    baseline.name = extract_name(resume_text)
    
    # Extract experience/companies
    baseline.companies = extract_companies(resume_text)
    baseline.experience_count = len(baseline.companies)
    
    # Extract projects
    baseline.project_titles = extract_projects(resume_text)
    baseline.project_count = len(baseline.project_titles)
    
    # Extract skills
    baseline.skills = extract_skills(resume_text)
    baseline.skill_count = len(baseline.skills)
    
    # Check education
    baseline.has_education, baseline.education_text = extract_education(resume_text)
    
    logger.info(f"Baseline extracted: {baseline.experience_count} experiences, "
                f"{baseline.project_count} projects, {baseline.skill_count} skills")
    
    return baseline


def extract_email(text: str) -> str:
    """Extract email from text."""
    match = re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)
    return match.group(0) if match else ""


def extract_phone(text: str) -> str:
    """Extract phone number from text."""
    patterns = [
        r'\+?\d{1,3}[-.\s]?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',
        r'\(\d{3}\)\s*\d{3}[-.\s]?\d{4}',
        r'\d{3}[-.\s]\d{3}[-.\s]\d{4}'
    ]
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            return match.group(0)
    return ""


def extract_linkedin(text: str) -> str:
    """Extract LinkedIn URL from text."""
    match = re.search(r'(linkedin\.com/in/[\w-]+)', text, re.I)
    return match.group(0) if match else ""


def extract_github(text: str) -> str:
    """Extract GitHub URL from text."""
    match = re.search(r'(github\.com/[\w-]+)', text, re.I)
    return match.group(0) if match else ""


def extract_name(text: str) -> str:
    """Extract name from text (usually first non-empty line)."""
    lines = text.strip().split('\n')
    for line in lines[:5]:
        line = line.strip()
        if line and len(line) < 50:
            # Skip if it looks like contact info
            if '@' in line or 'http' in line or '|' in line:
                continue
            # Check if it looks like a name (mostly letters and spaces)
            if re.match(r'^[A-Z][a-zA-Z\s\.]+$', line):
                return line
    return ""


def extract_companies(text: str) -> List[str]:
    """
    Extract company names from experience section.
    Uses date ranges to identify job entries.
    """
    companies = []
    
    # Find date ranges (indicators of job entries)
    date_pattern = r'(\d{4}|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})\s*[-–—to]+\s*(\d{4}|Present|Current|Now|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{4})'
    
    lines = text.split('\n')
    
    for i, line in enumerate(lines):
        # Check if line has a date range
        if re.search(date_pattern, line, re.I):
            # Look for company name in current or previous lines
            # Company is often on the line with dates or just before
            potential_company = ""
            
            # Check current line (remove date part)
            clean_line = re.sub(date_pattern, '', line, flags=re.I).strip()
            clean_line = re.sub(r'[,|•·]', ' ', clean_line).strip()
            
            # Remove common role keywords
            role_keywords = ['engineer', 'developer', 'manager', 'analyst', 'intern', 
                           'senior', 'junior', 'lead', 'staff', 'principal', 'director']
            
            words = clean_line.split()
            company_words = []
            for word in words:
                if word.lower() not in role_keywords and len(word) > 1:
                    company_words.append(word)
            
            if company_words:
                potential_company = ' '.join(company_words[:4])  # Limit to 4 words
            
            # Check previous line if current doesn't have company
            if not potential_company and i > 0:
                prev_line = lines[i-1].strip()
                if prev_line and not re.search(date_pattern, prev_line, re.I):
                    potential_company = prev_line[:50]
            
            if potential_company and potential_company not in companies:
                companies.append(potential_company)
    
    return companies


def extract_projects(text: str) -> List[str]:
    """Extract project titles from projects section."""
    projects = []
    
    # Find projects section
    projects_match = re.search(
        r'(?:projects?|portfolio|personal projects?)[:\s]*\n([\s\S]*?)(?=\n\s*(?:education|skills?|experience|work|$))',
        text, re.I
    )
    
    if not projects_match:
        return projects
    
    projects_section = projects_match.group(1)
    
    # Look for project titles (usually bold/emphasized or at start of line)
    # Pattern: Lines that start with a title-like text
    lines = projects_section.split('\n')
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Skip bullet points that are descriptions
        if line.startswith(('-', '•', '*', '–')) and len(line) > 80:
            continue
        
        # Clean markdown
        clean_line = re.sub(r'\*\*([^*]+)\*\*', r'\1', line)
        clean_line = re.sub(r'^\s*[-•*]\s*', '', clean_line)
        
        # Project titles are usually short (< 60 chars) and capitalized
        if clean_line and len(clean_line) < 60:
            # Check if it looks like a title
            if clean_line[0].isupper() or clean_line.startswith('"'):
                if clean_line not in projects:
                    projects.append(clean_line)
    
    return projects[:10]  # Limit to 10 projects


def extract_skills(text: str) -> List[str]:
    """Extract skills from text using multiple patterns."""
    skills = set()  # Use set to avoid duplicates
    
    # Pattern 1: Find explicit skills section (anywhere in document)
    skills_patterns = [
        # Skills section at the end
        r'(?:skills?|technologies?|technical skills?|competencies|tech stack)[:\s]*\n([\s\S]*?)(?=\n\s*(?:education|experience|projects?|work history|employment|references|$))',
        # Skills section anywhere with different terminators
        r'(?:skills?|technologies?|technical skills?|competencies)[:\s]*\n([\s\S]*?)(?=\n\n|\n[A-Z][A-Z])',
        # Skills on same line after colon
        r'(?:skills?|technologies?)\s*:\s*([^\n]+)',
    ]
    
    for pattern in skills_patterns:
        match = re.search(pattern, text, re.I)
        if match:
            skills_section = match.group(1)
            # Split by common delimiters
            skill_items = re.split(r'[,|•·\n;/]', skills_section)
            for item in skill_items:
                item = item.strip()
                # Remove category labels like "Languages:", "Tools:"
                item = re.sub(r'^[A-Za-z\s]{0,20}:', '', item).strip()
                # Remove bullet points and dashes
                item = re.sub(r'^[-–—*•]\s*', '', item).strip()
                if item and 1 < len(item) < 50:
                    skills.add(item)
    
    # Pattern 2: Look for known technical skills anywhere in document
    known_skills = [
        'Python', 'JavaScript', 'TypeScript', 'Java', 'C\\+\\+', 'C#', 'Ruby', 'Go', 'Rust', 'PHP',
        'React', 'Angular', 'Vue', 'Node\\.js', 'Django', 'Flask', 'FastAPI', 'Spring',
        'AWS', 'Azure', 'GCP', 'Docker', 'Kubernetes', 'Terraform',
        'PostgreSQL', 'MySQL', 'MongoDB', 'Redis', 'Elasticsearch',
        'Git', 'GitHub', 'GitLab', 'Jenkins', 'CI/CD',
        'REST API', 'GraphQL', 'Microservices', 'Linux', 'SQL', 'NoSQL',
        'Machine Learning', 'TensorFlow', 'PyTorch', 'Pandas', 'NumPy',
        'HTML', 'CSS', 'SASS', 'Tailwind', 'Bootstrap',
        'Agile', 'Scrum', 'Jira', 'Confluence',
    ]
    
    for skill in known_skills:
        if re.search(rf'\b{skill}\b', text, re.I):
            # Normalize the skill name
            normalized = skill.replace('\\', '').replace('.', '')
            skills.add(normalized)
    
    # Pattern 3: Extract from bullet points anywhere
    bullet_skills = re.findall(r'[•·\-–—]\s*([A-Z][a-zA-Z0-9+#/.\s]{2,25})(?=[,;•·\-–—\n]|$)', text)
    for skill in bullet_skills:
        skill = skill.strip()
        if skill and 2 < len(skill) < 30:
            skills.add(skill)
    
    return list(skills)


def extract_education(text: str) -> Tuple[bool, str]:
    """Extract education section."""
    edu_match = re.search(
        r'(?:education|academic)[:\s]*\n([\s\S]*?)(?=\n\s*(?:experience|skills?|projects?|$))',
        text, re.I
    )
    
    if edu_match:
        return True, edu_match.group(1).strip()
    
    # Check for degree keywords
    if re.search(r'(bachelor|master|phd|b\.?s\.?|m\.?s\.?|degree)', text, re.I):
        return True, ""
    
    return False, ""


@dataclass
class ValidationResult:
    """Result of comparing executor output against baseline."""
    passed: bool = False
    experience_match: bool = False
    project_match: bool = False
    skills_match: bool = False
    contact_preserved: bool = False
    issues: List[str] = field(default_factory=list)
    corrective_prompt: str = ""
    
    @property
    def needs_retry(self) -> bool:
        """Check if retry is needed."""
        return not self.passed and bool(self.corrective_prompt)


def validate_against_baseline(
    baseline: ResumeBaseline, 
    structured_data: Dict
) -> ValidationResult:
    """
    Validate executor output against baseline.
    Returns validation result with corrective prompt if needed.
    """
    result = ValidationResult()
    issues = []
    
    # 1. Validate experience count
    executor_exp_count = len(structured_data.get("experience", []))
    if executor_exp_count < baseline.experience_count:
        issues.append(
            f"Experience mismatch: Original has {baseline.experience_count} jobs, "
            f"output has {executor_exp_count}"
        )
        result.experience_match = False
    else:
        result.experience_match = True
    
    # 2. Validate project count
    executor_proj_count = len(structured_data.get("projects", []))
    if executor_proj_count < baseline.project_count:
        issues.append(
            f"Project mismatch: Original has {baseline.project_count} projects, "
            f"output has {executor_proj_count}"
        )
        result.project_match = False
    else:
        result.project_match = True
    
    # 3. Validate skills count (with smart caps for large skill lists)
    executor_skills = structured_data.get("skills", [])
    executor_skill_count = len(executor_skills)
    
    # For very large skill lists (>30), cap the requirement at 25 core skills
    # This prevents demanding 80% of 100+ skills which is unrealistic for ATS
    if baseline.skill_count > 30:
        min_skills_required = 25  # ATS-optimized cap
    else:
        min_skills_required = int(baseline.skill_count * 0.8)  # 80% threshold
    
    if executor_skill_count < min_skills_required:
        issues.append(
            f"Skills mismatch: Original has {baseline.skill_count} skills, "
            f"output has {executor_skill_count} (minimum required: {min_skills_required})"
        )
        result.skills_match = False
    else:
        result.skills_match = True
    
    # 4. Validate contact info preserved
    contact_issues = []
    if baseline.email and not structured_data.get("email"):
        contact_issues.append("email")
    if baseline.phone and not structured_data.get("phone"):
        contact_issues.append("phone")
    if baseline.linkedin and not structured_data.get("linkedin"):
        contact_issues.append("linkedin")
    
    if contact_issues:
        issues.append(f"Missing contact info: {', '.join(contact_issues)}")
        result.contact_preserved = False
    else:
        result.contact_preserved = True
    
    # 5. Check for hallucinated companies
    executor_companies = []
    for exp in structured_data.get("experience", []):
        company = exp.get("company", "")
        executor_companies.append(company.lower())
    
    # Check if executor added companies not in original
    for company in executor_companies:
        found = False
        for orig_company in baseline.companies:
            if orig_company.lower() in company or company in orig_company.lower():
                found = True
                break
        if not found and company:
            # Might be hallucinated
            issues.append(f"Possible hallucinated company: {company}")
    
    # Determine if passed
    result.issues = issues
    result.passed = result.experience_match and result.project_match and result.skills_match and result.contact_preserved
    
    # Generate corrective prompt if retry needed
    if not result.passed:
        result.corrective_prompt = generate_corrective_prompt(baseline, issues)
    
    return result


def generate_corrective_prompt(baseline: ResumeBaseline, issues: List[str]) -> str:
    """Generate corrective prompt for retry."""
    prompt_parts = [
        "⚠️ CRITICAL CORRECTION REQUIRED:",
        "",
        "Your previous output had data preservation issues:",
    ]
    
    for issue in issues:
        prompt_parts.append(f"  • {issue}")
    
    prompt_parts.extend([
        "",
        "MANDATORY CORRECTIONS:",
    ])
    
    if baseline.experience_count > 0:
        prompt_parts.append(
            f"  1. The experience array MUST have EXACTLY {baseline.experience_count} entries"
        )
        if baseline.companies:
            prompt_parts.append(f"     Companies to include: {', '.join(baseline.companies[:5])}")
    
    if baseline.project_count > 0:
        prompt_parts.append(
            f"  2. The projects array MUST have EXACTLY {baseline.project_count} entries"
        )
        if baseline.project_titles:
            prompt_parts.append(f"     Projects to include: {', '.join(baseline.project_titles[:5])}")
    
    if baseline.skill_count > 0:
        if baseline.skill_count > 30:
            # For large skill lists, guide toward optimization not preservation
            prompt_parts.append(
                f"  3. The skills array MUST have AT LEAST 25 skills (prioritize job-relevant ones)"
            )
            prompt_parts.append(f"     Original has {baseline.skill_count} skills - condense to top 25-35 most relevant")
            prompt_parts.append(f"     Group by: Languages | Frameworks | Databases | Cloud | DevOps | Soft Skills")
        else:
            min_skills = int(baseline.skill_count * 0.8)
            prompt_parts.append(
                f"  3. The skills array MUST have AT LEAST {min_skills} entries (original has {baseline.skill_count})"
            )
        if baseline.skills:
            prompt_parts.append(f"     Sample skills from original: {', '.join(baseline.skills[:10])}")
    
    prompt_parts.extend([
        "",
        "DO NOT:",
        "  • Merge multiple jobs into one",
        "  • Skip any projects",
        "  • Invent company names not in the original",
        "  • Summarize or consolidate entries",
        "",
        "Re-extract from the ORIGINAL RESUME and preserve ALL entries."
    ])
    
    return "\n".join(prompt_parts)


def compare_counts(baseline: ResumeBaseline, structured_data: Dict) -> Dict:
    """
    Compare counts between baseline and structured output.
    Returns detailed comparison dict.
    """
    executor_exp = structured_data.get("experience", [])
    executor_proj = structured_data.get("projects", [])
    executor_skills = structured_data.get("skills", [])
    
    return {
        "experience": {
            "original": baseline.experience_count,
            "output": len(executor_exp),
            "match": len(executor_exp) >= baseline.experience_count
        },
        "projects": {
            "original": baseline.project_count,
            "output": len(executor_proj),
            "match": len(executor_proj) >= baseline.project_count
        },
        "skills": {
            "original": baseline.skill_count,
            "output": len(executor_skills),
            "match": len(executor_skills) >= baseline.skill_count * 0.5  # Allow some flexibility
        },
        "contact": {
            "email": bool(structured_data.get("email")) if baseline.email else True,
            "phone": bool(structured_data.get("phone")) if baseline.phone else True,
            "linkedin": bool(structured_data.get("linkedin")) if baseline.linkedin else True,
            "github": bool(structured_data.get("github")) if baseline.github else True
        }
    }
