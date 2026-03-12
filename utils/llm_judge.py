"""
LLM-as-Judge Evaluation System

Standalone evaluation system using OpenAI directly (not CrewAI).
Scores resume optimizations on multiple dimensions with objective rubrics.
"""

import os
import json
from typing import List, Dict


def evaluate_resume_optimization(
    original_resume: str,
    optimized_resume: str,
    job_description: str,
    critic_report: dict
) -> dict:
    """
    Evaluate resume optimization quality using GPT-4o-mini as an impartial judge.
    
    Returns scores on 4 dimensions plus an overall weighted score.
    """
    # Initialize client inside function to avoid import-time errors
    from openai import OpenAI
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    
    system_prompt = (
        "You are an impartial resume evaluation judge. "
        "You score resume optimizations objectively. "
        "You always respond with valid JSON only — no markdown, no explanation, no backticks."
    )
    
    user_prompt = f"""Evaluate this resume optimization.

## ORIGINAL RESUME:
{original_resume}

## OPTIMIZED RESUME:
{optimized_resume}

## JOB DESCRIPTION:
{job_description}

## CRITIC AGENT REPORT:
{json.dumps(critic_report, indent=2)}

---

Score the optimized resume on these 4 dimensions using the rubrics below:

### KEYWORD_MATCH_RATE (0-100):
What % of the job description's key technical requirements appear in the resume in a natural, contextually appropriate way?
- 100 = all key requirements present naturally
- Penalize stuffed or out-of-context keywords
- Penalize if keywords are crammed without flow

### READABILITY_SCORE (0-100):
Is the resume easy to scan in 6 seconds?
- Clear section headers
- Concise bullets (under 2 lines each)
- No walls of text
- Consistent formatting
- 100 = perfect scannability

### AUTHENTICITY_SCORE (0-100):
Does this read like a real human wrote it — not an AI?
Penalize:
- Generic action verbs with no specifics ("Leveraged", "Utilized", "Drove")
- Corporate filler phrases ("drove impactful outcomes", "leveraged synergies")
- Vague unverifiable claims
- Buzz-word salads
- Text that sounds identical to every other AI resume
- 100 = completely authentic human voice

### ATS_COMPATIBILITY_SCORE (0-100):
Would ATS software parse this correctly?
- Standard section headers (Experience, Education, Skills)
- No tables or columns
- No images or special characters
- Standard date formats (MM/YYYY)
- Keywords from job description present
- 100 = fully ATS-compatible

---

Respond ONLY with this JSON structure, no other text:
{{
  "keyword_match_rate": <int 0-100>,
  "readability_score": <int 0-100>,
  "authenticity_score": <int 0-100>,
  "ats_compatibility_score": <int 0-100>,
  "keyword_match_reasoning": "<one sentence max>",
  "readability_reasoning": "<one sentence max>",
  "authenticity_reasoning": "<one sentence max>",
  "ats_reasoning": "<one sentence max>",
  "improvement_suggestions": ["<suggestion>", "<suggestion>", "<suggestion>"]
}}"""

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.1,
            max_tokens=600
        )
        
        # Extract and parse JSON response
        response_text = response.choices[0].message.content.strip()
        
        # Handle potential markdown code blocks
        if response_text.startswith("```"):
            # Extract JSON from code block
            lines = response_text.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```") and not in_block:
                    in_block = True
                    continue
                elif line.startswith("```") and in_block:
                    break
                elif in_block:
                    json_lines.append(line)
            response_text = "\n".join(json_lines)
        
        result = json.loads(response_text)
        
        # Validate and clamp scores to 0-100
        for key in ["keyword_match_rate", "readability_score", "authenticity_score", "ats_compatibility_score"]:
            if key in result:
                result[key] = max(0, min(100, int(result[key])))
            else:
                result[key] = 0
        
        # Compute overall_score in Python (NOT from LLM)
        overall_score = round(
            (result["keyword_match_rate"] * 0.30) +
            (result["readability_score"] * 0.25) +
            (result["authenticity_score"] * 0.25) +
            (result["ats_compatibility_score"] * 0.20)
        )
        result["overall_score"] = overall_score
        
        # Ensure all expected fields exist with defaults
        result.setdefault("keyword_match_reasoning", "")
        result.setdefault("readability_reasoning", "")
        result.setdefault("authenticity_reasoning", "")
        result.setdefault("ats_reasoning", "")
        result.setdefault("improvement_suggestions", [])
        
        return result
        
    except Exception as e:
        # Return safe defaults on any failure
        return {
            "keyword_match_rate": 0,
            "readability_score": 0,
            "authenticity_score": 0,
            "ats_compatibility_score": 0,
            "overall_score": 0,
            "keyword_match_reasoning": "",
            "readability_reasoning": "",
            "authenticity_reasoning": "",
            "ats_reasoning": "",
            "improvement_suggestions": [],
            "error": str(e)
        }


def get_judge_score_label(score: int) -> str:
    """
    Convert numeric score to human-readable label.
    
    Args:
        score: Integer score from 0-100
        
    Returns:
        Label string: "Excellent", "Good", "Needs Work", or "Poor"
    """
    if score >= 85:
        return "Excellent"
    elif score >= 70:
        return "Good"
    elif score >= 50:
        return "Needs Work"
    else:
        return "Poor"


def get_before_after_comparison(
    original_resume: str,
    optimized_resume: str,
    keywords: List[str]
) -> dict:
    """
    Lightweight comparison of original vs optimized resume (no LLM call).
    
    Args:
        original_resume: Original resume text
        optimized_resume: Optimized resume text
        keywords: List of keywords to check for
        
    Returns:
        Dict with keyword coverage and length metrics
    """
    original_lower = original_resume.lower()
    optimized_lower = optimized_resume.lower()
    
    # Find keywords in each version
    keywords_in_original = set()
    keywords_in_optimized = set()
    
    for keyword in keywords:
        keyword_lower = keyword.lower()
        if keyword_lower in original_lower:
            keywords_in_original.add(keyword)
        if keyword_lower in optimized_lower:
            keywords_in_optimized.add(keyword)
    
    # Calculate added and lost keywords
    keywords_added = list(keywords_in_optimized - keywords_in_original)
    keywords_lost = list(keywords_in_original - keywords_in_optimized)
    
    # Calculate coverage percentages
    total_keywords = len(keywords) if keywords else 1  # Avoid division by zero
    keyword_coverage_before = round((len(keywords_in_original) / total_keywords) * 100, 1)
    keyword_coverage_after = round((len(keywords_in_optimized) / total_keywords) * 100, 1)
    
    # Calculate word count difference
    original_word_count = len(original_resume.split())
    optimized_word_count = len(optimized_resume.split())
    length_change = optimized_word_count - original_word_count
    
    return {
        "keywords_added": keywords_added,
        "keywords_lost": keywords_lost,
        "keyword_coverage_before": keyword_coverage_before,
        "keyword_coverage_after": keyword_coverage_after,
        "length_change": length_change
    }
