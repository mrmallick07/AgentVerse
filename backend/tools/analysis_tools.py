"""
Analysis Tools — Internal data exchange tools.
Used by agents to share intermediate research findings via session state.
"""

# In-memory store for research findings within a session
_research_store: dict[str, list] = {}


def save_research_finding(session_id: str, category: str, finding: str) -> dict:
    """Save a research finding for later analysis and synthesis.
    
    Args:
        session_id: The current session identifier.
        category: Category for grouping findings (e.g., 'web_results', 'wikipedia', 'youtube', 'places').
        finding: The research finding text to save.
    
    Returns:
        Confirmation that the finding was saved.
    """
    try:
        key = f"{session_id}:{category}"
        if key not in _research_store:
            _research_store[key] = []
        _research_store[key].append(finding)

        return {
            "status": "success",
            "message": f"Finding saved under '{category}'.",
            "total_findings_in_category": len(_research_store[key]),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def get_all_findings(session_id: str) -> dict:
    """Retrieve all research findings saved during this session.
    
    Args:
        session_id: The current session identifier.
    
    Returns:
        A dict with all findings organized by category.
    """
    try:
        findings = {}
        prefix = f"{session_id}:"
        for key, values in _research_store.items():
            if key.startswith(prefix):
                category = key[len(prefix):]
                findings[category] = values

        return {
            "status": "success",
            "findings": findings,
            "total_categories": len(findings),
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def clear_findings(session_id: str) -> dict:
    """Clear all research findings for a session.
    
    Args:
        session_id: The current session identifier.
    
    Returns:
        Confirmation that findings were cleared.
    """
    try:
        prefix = f"{session_id}:"
        keys_to_delete = [k for k in _research_store if k.startswith(prefix)]
        for k in keys_to_delete:
            del _research_store[k]

        return {"status": "success", "message": "All findings cleared."}
    except Exception as e:
        return {"status": "error", "message": str(e)}
