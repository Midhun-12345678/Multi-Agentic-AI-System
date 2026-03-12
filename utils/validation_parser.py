"""
Validation report parser for critic agent output.
Extracts validation metadata and warnings from critic's validation report.
"""

import re
from typing import Dict, List, Optional


def parse_validation_report(critic_output: str) -> Dict:
    """
    Parse the validation report from adversarial critic agent output.
    Returns structured validation metadata for the new report format.
    
    Expected sections:
    - DATA_INTEGRITY
    - KEYWORD_NATURALNESS
    - HUMAN_AUTHENTICITY
    - RECRUITER_CREDIBILITY
    - VOICE_PRESERVATION
    - OVERALL_VERDICT
    - CORRECTION_INSTRUCTIONS
    """
    # Safe defaults
    validation_data = {
        "data_integrity": {"passed": False, "details": ""},
        "keyword_naturalness": {"score": 5, "flagged_keywords": []},
        "human_authenticity": {"passed": False, "flagged_bullets": []},
        "recruiter_credibility": {"passed": False, "reasons": ""},
        "voice_preservation": {"passed": False, "notes": ""},
        "overall_verdict": "REVISE",
        "correction_instructions": "",
        "validation_passed": False
    }
    
    try:
        # Split into sections using "### " as delimiter
        sections = {}
        current_section = None
        current_content = []
        
        for line in critic_output.split('\n'):
            if line.strip().startswith('### '):
                # Save previous section
                if current_section:
                    sections[current_section] = '\n'.join(current_content).strip()
                # Start new section
                current_section = line.strip()[4:].strip().upper()
                current_content = []
            else:
                current_content.append(line)
        
        # Save last section
        if current_section:
            sections[current_section] = '\n'.join(current_content).strip()
        
        # Parse DATA_INTEGRITY
        if 'DATA_INTEGRITY' in sections:
            content = sections['DATA_INTEGRITY']
            validation_data["data_integrity"]["passed"] = bool(
                re.search(r'Status:\s*PASS', content, re.I)
            )
            validation_data["data_integrity"]["details"] = content
        
        # Parse KEYWORD_NATURALNESS
        if 'KEYWORD_NATURALNESS' in sections:
            content = sections['KEYWORD_NATURALNESS']
            # Extract score
            score_match = re.search(r'Score:\s*(\d+)\s*/\s*10', content, re.I)
            if score_match:
                validation_data["keyword_naturalness"]["score"] = int(score_match.group(1))
            # Extract flagged keywords
            flagged = []
            in_flagged_section = False
            for line in content.split('\n'):
                if 'Flagged Keywords:' in line:
                    in_flagged_section = True
                    continue
                if in_flagged_section and line.strip().startswith('- '):
                    flagged.append(line.strip()[2:].strip())
            validation_data["keyword_naturalness"]["flagged_keywords"] = flagged
        
        # Parse HUMAN_AUTHENTICITY
        if 'HUMAN_AUTHENTICITY' in sections:
            content = sections['HUMAN_AUTHENTICITY']
            validation_data["human_authenticity"]["passed"] = bool(
                re.search(r'Status:\s*PASS', content, re.I)
            )
            # Extract flagged bullets
            flagged = []
            in_flagged_section = False
            for line in content.split('\n'):
                if 'Flagged Bullets:' in line:
                    in_flagged_section = True
                    continue
                if in_flagged_section and line.strip().startswith('- '):
                    flagged.append(line.strip()[2:].strip())
            validation_data["human_authenticity"]["flagged_bullets"] = flagged
        
        # Parse RECRUITER_CREDIBILITY
        if 'RECRUITER_CREDIBILITY' in sections:
            content = sections['RECRUITER_CREDIBILITY']
            validation_data["recruiter_credibility"]["passed"] = bool(
                re.search(r'Status:\s*PASS', content, re.I)
            )
            # Extract reasons
            reasons_match = re.search(r'Reasons?:\s*(.+?)(?=\n\n|\Z)', content, re.I | re.S)
            if reasons_match:
                validation_data["recruiter_credibility"]["reasons"] = reasons_match.group(1).strip()
        
        # Parse VOICE_PRESERVATION
        if 'VOICE_PRESERVATION' in sections:
            content = sections['VOICE_PRESERVATION']
            validation_data["voice_preservation"]["passed"] = bool(
                re.search(r'Status:\s*PASS', content, re.I)
            )
            # Extract notes
            notes_match = re.search(r'Notes?:\s*(.+?)(?=\n\n|\Z)', content, re.I | re.S)
            if notes_match:
                validation_data["voice_preservation"]["notes"] = notes_match.group(1).strip()
        
        # Parse OVERALL_VERDICT
        if 'OVERALL_VERDICT' in sections:
            content = sections['OVERALL_VERDICT'].strip()
            # Take first word
            first_word = content.split()[0].upper() if content.split() else "REVISE"
            if first_word in ["APPROVE", "REVISE", "REJECT"]:
                validation_data["overall_verdict"] = first_word
            else:
                validation_data["overall_verdict"] = "REVISE"
        
        # Parse CORRECTION_INSTRUCTIONS
        if 'CORRECTION_INSTRUCTIONS' in sections:
            validation_data["correction_instructions"] = sections['CORRECTION_INSTRUCTIONS'].strip()
        
        # Set validation_passed based on overall_verdict
        validation_data["validation_passed"] = (validation_data["overall_verdict"] == "APPROVE")
        
    except Exception as e:
        # On any parsing error, return safe defaults
        print(f"Warning: Failed to parse validation report: {e}")
        validation_data = {
            "data_integrity": {"passed": False, "details": ""},
            "keyword_naturalness": {"score": 5, "flagged_keywords": []},
            "human_authenticity": {"passed": False, "flagged_bullets": []},
            "recruiter_credibility": {"passed": False, "reasons": ""},
            "voice_preservation": {"passed": False, "notes": ""},
            "overall_verdict": "REVISE",
            "correction_instructions": "",
            "validation_passed": False
        }
    
    return validation_data


def format_validation_summary(validation_data: Dict) -> str:
    """
    Format validation data into a human-readable summary.
    """
    if validation_data["validation_passed"]:
        summary = "✅ **Validation Passed**\n\n"
        
        if validation_data["jobs_mapped"]["match"]:
            summary += f"✓ Jobs: {validation_data['jobs_mapped']['original']} → {validation_data['jobs_mapped']['optimized']} (All mapped)\n"
        
        if validation_data["projects_mapped"]["match"]:
            summary += f"✓ Projects: {validation_data['projects_mapped']['original']} → {validation_data['projects_mapped']['optimized']} (All mapped)\n"
        
        if validation_data["contact_info_preserved"]:
            summary += f"✓ Contact: {', '.join(validation_data['contact_info_preserved'])}\n"
        
        if validation_data["education_preserved"]:
            summary += "✓ Education: Preserved\n"
        
        summary += f"\n**Data Integrity:** {validation_data['data_integrity']}"
    else:
        summary = "⚠️ **Validation Issues Detected**\n\n"
        
        if not validation_data["jobs_mapped"]["match"]:
            summary += f"⚠️ Jobs mismatch: {validation_data['jobs_mapped']['original']} original → {validation_data['jobs_mapped']['optimized']} optimized\n"
        
        if not validation_data["projects_mapped"]["match"]:
            summary += f"⚠️ Projects mismatch: {validation_data['projects_mapped']['original']} original → {validation_data['projects_mapped']['optimized']} optimized\n"
        
        for warning in validation_data["warnings"]:
            summary += f"⚠️ {warning}\n"
    
    return summary
