from typing import Any


def format_agent_success(agent_name: str, summary: str, details: Any) -> dict:
    """Format a successful Pattern Agent run response."""
    return {
        "status": "success",
        "agent": agent_name,
        "summary": summary,
        "details": details
    }


def format_agent_error(agent_name: str, error_msg: str, error_type: str) -> dict:
    """Format an error response from the Pattern Agent."""
    return {
        "status": "error",
        "agent": agent_name,
        "summary": f"An error occurred in {agent_name}: {error_msg}",
        "error": error_msg,
        "error_type": error_type
    }
