"""
Validation report parser for critic agent output.
Extracts validation metadata and warnings from critic's validation report.
"""

import re
from typing import Dict, List, Optional


def parse_validation_report(critic_output: str) -> Dict:
    """
    Parse the validation report from critic agent output.
    Returns structured validation metadata.
    """
    validation_data = {
        "all_fields_mapped": False,
        "jobs_mapped": {"original": 0, "optimized": 0, "match": False},
        "projects_mapped": {"original": 0, "optimized": 0, "match": False},
        "contact_info_preserved": [],
        "companies_preserved": [],
        "education_preserved": False,
        "format_compliance": "Unknown",
        "data_integrity": "Unknown",
        "warnings": [],
        "validation_passed": False
    }
    
    # Look for validation report section
    if "VALIDATION REPORT:" in critic_output or "---" in critic_output:
        # Extract validation section
        validation_section = ""
        if "---" in critic_output:
            parts = critic_output.split("---")
            if len(parts) > 1:
                validation_section = parts[-1]  # Last section after ---
        
        # Parse jobs mapped
        jobs_match = re.search(r'Jobs Mapped:\s*\[?(\d+)\s*original\s*→\s*(\d+)\s*optimized\]?', validation_section, re.I)
        if jobs_match:
            original_jobs = int(jobs_match.group(1))
            optimized_jobs = int(jobs_match.group(2))
            validation_data["jobs_mapped"] = {
                "original": original_jobs,
                "optimized": optimized_jobs,
                "match": original_jobs == optimized_jobs
            }
        
        # Parse projects mapped
        projects_match = re.search(r'Projects:\s*\[?(\d+)\s*original\s*→\s*(\d+)\s*optimized\]?', validation_section, re.I)
        if projects_match:
            original_projects = int(projects_match.group(1))
            optimized_projects = int(projects_match.group(2))
            validation_data["projects_mapped"] = {
                "original": original_projects,
                "optimized": optimized_projects,
                "match": original_projects == optimized_projects
            }
        
        # Parse contact info
        contact_match = re.search(r'Contact Info:\s*\[([^\]]+)\]', validation_section, re.I)
        if contact_match:
            contact_items = [item.strip() for item in contact_match.group(1).split(',')]
            validation_data["contact_info_preserved"] = contact_items
        
        # Parse companies
        companies_match = re.search(r'Companies:\s*\[([^\]]+)\]', validation_section, re.I)
        if companies_match:
            companies = [item.strip() for item in companies_match.group(1).split(',')]
            validation_data["companies_preserved"] = companies
        
        # Check education preserved
        if re.search(r'Education:\s*\[?Preserved\]?', validation_section, re.I):
            validation_data["education_preserved"] = True
        
        # Parse format compliance
        format_match = re.search(r'Format Compliance:\s*(\d+)%', validation_section, re.I)
        if format_match:
            validation_data["format_compliance"] = f"{format_match.group(1)}%"
        
        # Parse data integrity
        if "Data Integrity: COMPLETE" in validation_section or "All fields mapped successfully" in validation_section:
            validation_data["data_integrity"] = "COMPLETE"
            validation_data["all_fields_mapped"] = True
            validation_data["validation_passed"] = True
        
        # Extract warnings
        warning_pattern = r'⚠️\s*WARNING:\s*(.+?)(?=\n|$)'
        warnings = re.findall(warning_pattern, validation_section, re.I)
        validation_data["warnings"] = warnings
        
        # If there are warnings, validation didn't fully pass
        if warnings:
            validation_data["validation_passed"] = False
    
    # Fallback: Check for simple validation messages
    if "All fields mapped" in critic_output or "VALIDATION: ✓" in critic_output:
        validation_data["all_fields_mapped"] = True
        validation_data["validation_passed"] = True
        validation_data["data_integrity"] = "COMPLETE"
    
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
