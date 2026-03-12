"""
Score History Tracking

Persists optimization results for analysis and identifying worst performers.
Thread-safe file-based storage.
"""

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

HISTORY_FILE = Path("data/score_history.json")
_lock = threading.Lock()


def _load_history() -> list:
    """Load history from file. Returns [] on any failure."""
    try:
        if not HISTORY_FILE.exists():
            return []
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def _save_history(records: list) -> None:
    """Save history to file. Silently fails on errors."""
    try:
        HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(records, f, indent=2)
    except Exception:
        pass


def save_optimization_result(
    job_id: str,
    job_category: str,
    original_ats: float,
    optimized_ats: float,
    judge_scores: dict,
    critic_verdict: str
) -> None:
    """
    Save an optimization result to history.
    
    Args:
        job_id: Unique job identifier
        job_category: Category/type of job (e.g., "software_engineer", "data_scientist")
        original_ats: Original ATS score (0-100)
        optimized_ats: Optimized ATS score (0-100)
        judge_scores: Dict from evaluate_resume_optimization()
        critic_verdict: "APPROVE", "REVISE", or "REJECT"
    """
    record = {
        "job_id": job_id,
        "job_category": job_category,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "original_ats": original_ats,
        "optimized_ats": optimized_ats,
        "ats_improvement": round(optimized_ats - original_ats, 2),
        "critic_verdict": critic_verdict,
        "overall_judge_score": judge_scores.get("overall_score", 0),
        "keyword_match_rate": judge_scores.get("keyword_match_rate", 0),
        "readability_score": judge_scores.get("readability_score", 0),
        "authenticity_score": judge_scores.get("authenticity_score", 0),
        "ats_compatibility_score": judge_scores.get("ats_compatibility_score", 0),
        "improvement_suggestions": judge_scores.get("improvement_suggestions", [])
    }
    
    with _lock:
        history = _load_history()
        history.append(record)
        _save_history(history)


def get_worst_performers(n: int = 5) -> List[dict]:
    """
    Get the n worst performing optimization results.
    
    Args:
        n: Number of results to return (default 5)
        
    Returns:
        List of records sorted by overall_judge_score ascending (worst first)
    """
    try:
        history = _load_history()
        sorted_history = sorted(history, key=lambda x: x.get("overall_judge_score", 0))
        return sorted_history[:n]
    except Exception:
        return []


def get_score_summary() -> dict:
    """
    Get aggregate statistics across all optimization results.
    
    Returns:
        Dict with totals, averages, and worst performing category
    """
    try:
        history = _load_history()
        
        if not history:
            return {
                "total_jobs": 0,
                "avg_ats_improvement": 0.0,
                "avg_judge_score": 0.0,
                "avg_authenticity_score": 0.0,
                "worst_category": "N/A"
            }
        
        total_jobs = len(history)
        
        # Calculate averages
        avg_ats_improvement = round(
            sum(r.get("ats_improvement", 0) for r in history) / total_jobs, 1
        )
        avg_judge_score = round(
            sum(r.get("overall_judge_score", 0) for r in history) / total_jobs, 1
        )
        avg_authenticity_score = round(
            sum(r.get("authenticity_score", 0) for r in history) / total_jobs, 1
        )
        
        # Find worst category by average overall_judge_score
        category_scores = {}
        category_counts = {}
        
        for record in history:
            category = record.get("job_category", "unknown")
            score = record.get("overall_judge_score", 0)
            
            if category not in category_scores:
                category_scores[category] = 0
                category_counts[category] = 0
            
            category_scores[category] += score
            category_counts[category] += 1
        
        # Calculate average per category and find worst
        worst_category = "N/A"
        worst_avg = float("inf")
        
        for category, total_score in category_scores.items():
            avg = total_score / category_counts[category]
            if avg < worst_avg:
                worst_avg = avg
                worst_category = category
        
        return {
            "total_jobs": total_jobs,
            "avg_ats_improvement": avg_ats_improvement,
            "avg_judge_score": avg_judge_score,
            "avg_authenticity_score": avg_authenticity_score,
            "worst_category": worst_category
        }
        
    except Exception:
        return {
            "total_jobs": 0,
            "avg_ats_improvement": 0.0,
            "avg_judge_score": 0.0,
            "avg_authenticity_score": 0.0,
            "worst_category": "N/A"
        }


def get_all_results() -> List[dict]:
    """
    Get all optimization results sorted by timestamp (newest first).
    
    Returns:
        List of all records sorted by timestamp descending
    """
    try:
        history = _load_history()
        sorted_history = sorted(
            history,
            key=lambda x: x.get("timestamp", ""),
            reverse=True
        )
        return sorted_history
    except Exception:
        return []
