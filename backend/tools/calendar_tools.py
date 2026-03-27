"""
Calendar Tools — Google Calendar API.
MCP tools for the PlannerAgent.
"""

from datetime import datetime, timedelta
from backend.tools.google_auth import get_calendar_service


def create_calendar_event(
    summary: str,
    start_time: str,
    end_time: str,
    description: str = "",
    location: str = "",
) -> dict:
    """Create a new event on the user's primary Google Calendar.
    
    Args:
        summary: Title of the event.
        start_time: Start time in ISO format (e.g., '2026-03-28T10:00:00+05:30').
        end_time: End time in ISO format (e.g., '2026-03-28T11:00:00+05:30').
        description: Optional description for the event.
        location: Optional location for the event.
    
    Returns:
        A dict with the created event details and a link to view it.
    """
    try:
        service = get_calendar_service()
        event = {
            "summary": summary,
            "description": description,
            "location": location,
            "start": {"dateTime": start_time, "timeZone": "Asia/Kolkata"},
            "end": {"dateTime": end_time, "timeZone": "Asia/Kolkata"},
        }
        created_event = service.events().insert(
            calendarId="primary", body=event
        ).execute()

        return {
            "status": "success",
            "message": f"Event '{summary}' created successfully!",
            "event_id": created_event.get("id", ""),
            "link": created_event.get("htmlLink", ""),
            "start": start_time,
            "end": end_time,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


def list_upcoming_events(max_results: int = 10) -> dict:
    """List the user's upcoming Google Calendar events.
    
    Args:
        max_results: Maximum number of events to return.
    
    Returns:
        A dict with a list of upcoming events containing title, time, and location.
    """
    try:
        service = get_calendar_service()
        now = datetime.utcnow().isoformat() + "Z"
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                maxResults=max_results,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = []
        for event in events_result.get("items", []):
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            events.append({
                "title": event.get("summary", "No Title"),
                "start": start,
                "end": end,
                "location": event.get("location", ""),
                "description": event.get("description", ""),
                "link": event.get("htmlLink", ""),
            })

        return {"status": "success", "events": events, "count": len(events)}
    except Exception as e:
        return {"status": "error", "message": str(e)}
