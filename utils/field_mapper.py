"""
Field mapping enforcement layer.
Extracts structured baseline from original resume and validates
executor output preserves all data.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class IssueSeverity(str, Enum):
    """Severity levels for validation issues."""
    CRITICAL = "critical"  # Data loss or hallucination - requires retry
    WARNING = "warning"    # Minor issue - log but proceed
    INFO = "info"          # Informational only


@dataclass
class ValidationIssue:
    """A single validation issue with severity."""
    message: str
    severity: IssueSeverity
    field: str = ""  # e.g., "experience", "skills", "contact"
    expected: Optional[int] = None
    actual: Optional[int] = None


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
    for line in lines[:10]:  # Search first 10 lines for resumes with headers/logos
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
                potential_company = ' '.join(company_words[:8])  # Allow longer company names
            
            # Check previous line if current doesn't have company
            if not potential_company and i > 0:
                prev_line = lines[i-1].strip()
                if prev_line and not re.search(date_pattern, prev_line, re.I):
                    potential_company = prev_line[:80]  # Allow longer names from prev line
            
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
    
    return projects  # Return all projects, no artificial limit


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
    
    # Severity-based issue lists
    critical_issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info_issues: List[ValidationIssue] = field(default_factory=list)
    
    # Legacy compatibility - flat list of issue messages
    issues: List[str] = field(default_factory=list)
    corrective_prompt: str = ""
    
    @property
    def needs_retry(self) -> bool:
        """Only retry on CRITICAL issues - warnings proceed with logging."""
        return len(self.critical_issues) > 0 and bool(self.corrective_prompt)
    
    @property
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues."""
        return len(self.critical_issues) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0


def validate_against_baseline(
    baseline: ResumeBaseline, 
    structured_data: Dict
) -> ValidationResult:
    """
    Validate executor output against baseline.
    Returns validation result with severity-based issues.
    
    CRITICAL issues (trigger retry):
    - Missing contact email/phone when original had them
    - Hallucinated company names
    - Experience count = 0 when original had entries
    
    WARNING issues (log but proceed):
    - Experience count off by 1-2
    - Project count mismatch
    - Skill count below threshold
    """
    result = ValidationResult()
    legacy_issues = []  # For backward compatibility
    
    # 1. Validate experience count
    executor_exp_count = len(structured_data.get("experience", []))
    
    if baseline.experience_count > 0 and executor_exp_count == 0:
        # CRITICAL: Complete data loss
        issue = ValidationIssue(
            message=f"Complete experience loss: Original has {baseline.experience_count} jobs, output has 0",
            severity=IssueSeverity.CRITICAL,
            field="experience",
            expected=baseline.experience_count,
            actual=0
        )
        result.critical_issues.append(issue)
        legacy_issues.append(issue.message)
        result.experience_match = False
    elif executor_exp_count < baseline.experience_count:
        # Check how big the gap is
        gap = baseline.experience_count - executor_exp_count
        if gap > 2:
            # CRITICAL: Significant data loss (more than 2 jobs missing)
            issue = ValidationIssue(
                message=f"Significant experience loss: Original has {baseline.experience_count} jobs, output has {executor_exp_count}",
                severity=IssueSeverity.CRITICAL,
                field="experience",
                expected=baseline.experience_count,
                actual=executor_exp_count
            )
            result.critical_issues.append(issue)
            result.experience_match = False
        else:
            # WARNING: Minor mismatch (1-2 jobs) - may be consolidation
            issue = ValidationIssue(
                message=f"Experience count mismatch: Original has {baseline.experience_count} jobs, output has {executor_exp_count}",
                severity=IssueSeverity.WARNING,
                field="experience",
                expected=baseline.experience_count,
                actual=executor_exp_count
            )
            result.warnings.append(issue)
            result.experience_match = True  # Allow minor variations
        legacy_issues.append(f"Experience mismatch: {baseline.experience_count} -> {executor_exp_count}")
    else:
        result.experience_match = True
    
    # 2. Validate project count - WARNING level (projects may be consolidated)
    executor_proj_count = len(structured_data.get("projects", []))
    if executor_proj_count < baseline.project_count:
        # Allow 90% for projects with 5+ items, exact match for smaller lists
        if baseline.project_count >= 5:
            min_required = int(baseline.project_count * 0.9)
        else:
            min_required = baseline.project_count
        
        if executor_proj_count < min_required:
            issue = ValidationIssue(
                message=f"Project mismatch: Original has {baseline.project_count} projects, output has {executor_proj_count}",
                severity=IssueSeverity.WARNING,
                field="projects",
                expected=baseline.project_count,
                actual=executor_proj_count
            )
            result.warnings.append(issue)
            legacy_issues.append(issue.message)
        result.project_match = executor_proj_count >= min_required
    else:
        result.project_match = True
    
    # 3. Validate skills count - WARNING level with relaxed thresholds
    executor_skills = structured_data.get("skills", [])
    executor_skill_count = len(executor_skills)
    
    # Relaxed thresholds (reduced from 90%/85%)
    if baseline.skill_count > 40:
        min_skills_required = 25  # Relaxed from 30 for very large lists
    elif baseline.skill_count > 25:
        min_skills_required = int(baseline.skill_count * 0.75)  # Relaxed from 85%
    else:
        min_skills_required = int(baseline.skill_count * 0.80)  # Relaxed from 90%
    
    if executor_skill_count < min_skills_required:
        issue = ValidationIssue(
            message=f"Skills below threshold: Original has {baseline.skill_count} skills, output has {executor_skill_count} (min: {min_skills_required})",
            severity=IssueSeverity.WARNING,
            field="skills",
            expected=min_skills_required,
            actual=executor_skill_count
        )
        result.warnings.append(issue)
        legacy_issues.append(issue.message)
        result.skills_match = False
    else:
        result.skills_match = True
    
    # 4. Validate contact info - CRITICAL for email/phone, WARNING for linkedin
    if baseline.email and not structured_data.get("email"):
        issue = ValidationIssue(
            message=f"Missing email: {baseline.email}",
            severity=IssueSeverity.CRITICAL,
            field="contact"
        )
        result.critical_issues.append(issue)
        legacy_issues.append("Missing email")
        result.contact_preserved = False
    
    if baseline.phone and not structured_data.get("phone"):
        issue = ValidationIssue(
            message=f"Missing phone: {baseline.phone}",
            severity=IssueSeverity.CRITICAL,
            field="contact"
        )
        result.critical_issues.append(issue)
        legacy_issues.append("Missing phone")
        result.contact_preserved = False
    
    if baseline.linkedin and not structured_data.get("linkedin"):
        # LinkedIn is WARNING, not critical
        issue = ValidationIssue(
            message=f"Missing LinkedIn: {baseline.linkedin}",
            severity=IssueSeverity.WARNING,
            field="contact"
        )
        result.warnings.append(issue)
        legacy_issues.append("Missing LinkedIn (optional)")
    
    # Set contact_preserved if not already set to False
    if result.contact_preserved is not False:
        result.contact_preserved = True
    
    # 5. Check for hallucinated companies - CRITICAL
    executor_companies = []
    for exp in structured_data.get("experience", []):
        company = exp.get("company", "")
        if company:
            executor_companies.append(company.lower())
    
    for company in executor_companies:
        found = False
        for orig_company in baseline.companies:
            if orig_company.lower() in company or company in orig_company.lower():
                found = True
                break
        if not found and company and len(company) > 2:
            issue = ValidationIssue(
                message=f"Possible hallucinated company: {company}",
                severity=IssueSeverity.CRITICAL,
                field="experience"
            )
            result.critical_issues.append(issue)
            legacy_issues.append(f"Hallucinated company: {company}")
    
    # 6. ENTITY-BASED VALIDATION: Check if original companies appear in output
    # This catches missing companies even if count looks okay (e.g., wrong companies)
    missing_companies = []
    for orig_company in baseline.companies:
        found = False
        for exec_company in executor_companies:
            # Fuzzy match - check if original company name appears in executor output
            if orig_company.lower() in exec_company or exec_company in orig_company.lower():
                found = True
                break
            # Also check partial match for multi-word company names
            orig_words = set(orig_company.lower().split())
            exec_words = set(exec_company.split())
            if len(orig_words.intersection(exec_words)) >= min(2, len(orig_words)):
                found = True
                break
        if not found:
            missing_companies.append(orig_company)
    
    # If more than 1 company is missing (or all companies are missing), it's CRITICAL
    if missing_companies:
        if len(missing_companies) >= len(baseline.companies) * 0.5 or len(missing_companies) > 2:
            # CRITICAL: More than half of companies missing
            issue = ValidationIssue(
                message=f"Missing companies: {', '.join(missing_companies)}",
                severity=IssueSeverity.CRITICAL,
                field="experience"
            )
            result.critical_issues.append(issue)
            legacy_issues.append(f"Missing companies: {', '.join(missing_companies)}")
        else:
            # WARNING: Just 1-2 companies missing (might be legitimate consolidation)
            issue = ValidationIssue(
                message=f"Companies may be missing: {', '.join(missing_companies)}",
                severity=IssueSeverity.WARNING,
                field="experience"
            )
            result.warnings.append(issue)
            legacy_issues.append(f"Possibly missing: {', '.join(missing_companies)}")
    
    # 7. ENTITY-BASED VALIDATION: Check if original projects appear in output
    executor_projects = []
    for proj in structured_data.get("projects", []):
        title = proj.get("title", "")
        if title:
            executor_projects.append(title.lower())
    
    missing_projects = []
    for orig_project in baseline.project_titles:
        found = False
        for exec_project in executor_projects:
            if orig_project.lower() in exec_project or exec_project in orig_project.lower():
                found = True
                break
            # Partial word match for project titles
            orig_words = set(orig_project.lower().split())
            exec_words = set(exec_project.split())
            if len(orig_words.intersection(exec_words)) >= min(2, len(orig_words)):
                found = True
                break
        if not found:
            missing_projects.append(orig_project)
    
    if missing_projects and len(missing_projects) > len(baseline.project_titles) * 0.3:
        # WARNING: Projects missing (projects can often be legitimately consolidated)
        issue = ValidationIssue(
            message=f"Projects may be missing: {', '.join(missing_projects[:5])}{'...' if len(missing_projects) > 5 else ''}",
            severity=IssueSeverity.WARNING,
            field="projects"
        )
        result.warnings.append(issue)
        legacy_issues.append(f"Missing projects: {len(missing_projects)}")
    
    # Set legacy issues list
    result.issues = legacy_issues
    
    # Determine if passed - only CRITICAL issues cause failure
    # Warnings are logged but don't block the output
    result.passed = not result.has_critical_issues
    
    # Generate corrective prompt only for critical issues - pass missing entities for specificity
    if result.has_critical_issues:
        result.corrective_prompt = generate_corrective_prompt_v2(
            baseline, 
            result.critical_issues,
            missing_companies=missing_companies if missing_companies else None
        )
    
    # Log summary
    logger.info(f"Validation complete: passed={result.passed}, "
                f"critical={len(result.critical_issues)}, warnings={len(result.warnings)}")
    
    return result


def generate_corrective_prompt_v2(
    baseline: ResumeBaseline, 
    critical_issues: List[ValidationIssue],
    missing_companies: Optional[List[str]] = None
) -> str:
    """
    Generate corrective prompt for retry - focuses only on CRITICAL issues.
    Provides specific missing entities for targeted correction.
    Warnings are logged but don't trigger this prompt.
    """
    prompt_parts = [
        "🚨 CRITICAL CORRECTION REQUIRED:",
        "",
        "Your previous output had CRITICAL data preservation issues that MUST be fixed:",
    ]
    
    for issue in critical_issues:
        prompt_parts.append(f"  • [{issue.severity.value.upper()}] {issue.message}")
    
    prompt_parts.extend([
        "",
        "MANDATORY CORRECTIONS:",
    ])
    
    # Check what critical issues exist and provide targeted guidance
    has_contact_issue = any(i.field == "contact" for i in critical_issues)
    has_experience_issue = any(i.field == "experience" for i in critical_issues)
    has_hallucination = any("hallucinated" in i.message.lower() for i in critical_issues)
    has_missing_companies = any("missing companies" in i.message.lower() for i in critical_issues)
    
    correction_num = 1
    
    if has_contact_issue:
        prompt_parts.append(f"  {correction_num}. PRESERVE ALL CONTACT INFO:")
        if baseline.email:
            prompt_parts.append(f"     - email: \"{baseline.email}\"")
        if baseline.phone:
            prompt_parts.append(f"     - phone: \"{baseline.phone}\"")
        correction_num += 1
    
    if has_experience_issue and baseline.experience_count > 0:
        prompt_parts.append(
            f"  {correction_num}. The experience array MUST have AT LEAST {baseline.experience_count} entries"
        )
        # Provide SPECIFIC missing companies if available
        if missing_companies:
            prompt_parts.append(f"     ❌ MISSING COMPANIES (must be added):")
            for company in missing_companies:
                prompt_parts.append(f"        - \"{company}\"")
        elif baseline.companies:
            prompt_parts.append(f"     Companies that MUST appear: {', '.join(baseline.companies)}")
        correction_num += 1
    
    if has_hallucination:
        prompt_parts.append(
            f"  {correction_num}. DO NOT invent or add companies not in the original resume"
        )
        if baseline.companies:
            prompt_parts.append(f"     ✅ ONLY these companies are valid:")
            for company in baseline.companies:
                prompt_parts.append(f"        - \"{company}\"")
        correction_num += 1
    
    if has_missing_companies and missing_companies:
        prompt_parts.append(
            f"  {correction_num}. The following companies from the original resume are MISSING:"
        )
        for company in missing_companies:
            prompt_parts.append(f"        ❌ \"{company}\" - MUST be included in experience array")
        correction_num += 1
    
    prompt_parts.extend([
        "",
        "CRITICAL RULES:",
        "  • ONLY use company names from the ORIGINAL resume",
        "  • DO NOT merge multiple jobs into one entry",
        "  • DO NOT invent experience or company names",
        "  • PRESERVE exact contact information as provided",
        "  • Each job at a company = ONE separate experience entry",
        "",
        "Re-extract from the ORIGINAL RESUME and fix these critical issues."
    ])
    
    return "\n".join(prompt_parts)


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
            prompt_parts.append(f"     Companies to include: {', '.join(baseline.companies)}")  # ALL companies
    
    if baseline.project_count > 0:
        prompt_parts.append(
            f"  2. The projects array MUST have EXACTLY {baseline.project_count} entries"
        )
        if baseline.project_titles:
            prompt_parts.append(f"     Projects to include: {', '.join(baseline.project_titles)}")  # ALL projects
    
    if baseline.skill_count > 0:
        if baseline.skill_count > 40:
            # For large skill lists, guide toward optimization not preservation
            prompt_parts.append(
                f"  3. The skills array MUST have AT LEAST 30 skills (prioritize job-relevant ones)"
            )
            prompt_parts.append(f"     Original has {baseline.skill_count} skills - condense to top 30-40 most relevant")
            prompt_parts.append(f"     Group by: Languages | Frameworks | Databases | Cloud | DevOps | Soft Skills")
        else:
            min_skills = int(baseline.skill_count * 0.90)  # 90% threshold
            prompt_parts.append(
                f"  3. The skills array MUST have AT LEAST {min_skills} entries (original has {baseline.skill_count})"
            )
        if baseline.skills:
            # Show all skills up to 30, or summarize if more
            if len(baseline.skills) <= 30:
                prompt_parts.append(f"     Skills from original: {', '.join(baseline.skills)}")
            else:
                prompt_parts.append(f"     Sample skills from original: {', '.join(baseline.skills[:30])}...")
    
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
            "match": len(executor_skills) >= baseline.skill_count * 0.8  # 80% minimum threshold
        },
        "contact": {
            "email": bool(structured_data.get("email")) if baseline.email else True,
            "phone": bool(structured_data.get("phone")) if baseline.phone else True,
            "linkedin": bool(structured_data.get("linkedin")) if baseline.linkedin else True,
            "github": bool(structured_data.get("github")) if baseline.github else True
        }
    }
