import re

def resume_to_json(text):
    """Convert resume text to JSON. Fallback parser."""
    name = text.split("\n")[0]

    skills = re.findall(r"- (.+)", text)
    
    # Extract summary section if present
    summary = extract_summary(text) or text[:1000]

    return {
        "name": name.strip(),
        "skills": skills,  # Return all skills, no artificial limit
        "summary": summary,
        "raw": text
    }


def extract_summary(text: str) -> str:
    """Extract summary/objective section from resume text."""
    # Look for common summary section headers
    patterns = [
        r'(?:summary|objective|profile|about)[:\s]*\n([\s\S]*?)(?=\n\s*(?:experience|education|skills?|projects?|$))',
        r'(?:professional summary|career summary)[:\s]*\n([\s\S]*?)(?=\n\n)',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, text, re.I)
        if match:
            return match.group(1).strip()[:1000]  # Cap at 1000 chars for safety
    
    return ""
