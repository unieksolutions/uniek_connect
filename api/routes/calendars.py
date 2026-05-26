"""
Calendar API routes for Google Calendar access.
Used by consuming services to fetch calendar data using OAuth tokens.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, List
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from api.database import get_db
from api.oauth.google import get_valid_token as get_google_token
from api.oauth.microsoft import get_valid_token as get_microsoft_token
from api.config import get_settings
import httpx

router = APIRouter()
settings = get_settings()


def get_calendar_service(access_token: str):
    """Create Google Calendar API service with access token."""
    credentials = Credentials(token=access_token)
    service = build("calendar", "v3", credentials=credentials)
    return service


@router.get("/google")
async def list_google_calendars(
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    List all calendars for a Google account.

    Query params:
    - account_email: Email of connected Google account
    - user_id: User ID (default: 1 for MVP)

    Returns:
    - List of calendars with id, name, description, timezone
    """
    # Get valid access token
    access_token = await get_google_token(account_email, user_id, db)

    # Create Calendar service
    service = get_calendar_service(access_token)

    try:
        # List calendars
        calendar_list = service.calendarList().list().execute()

        calendars = []
        for cal in calendar_list.get("items", []):
            calendars.append({
                "id": cal["id"],
                "name": cal["summary"],
                "description": cal.get("description", ""),
                "timezone": cal.get("timeZone", "UTC"),
                "primary": cal.get("primary", False),
                "color": cal.get("backgroundColor", "#000000"),
                "access_role": cal.get("accessRole", "reader")
            })

        return {
            "provider": "google",
            "account_email": account_email,
            "calendars": calendars,
            "count": len(calendars)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch calendars: {str(e)}"
        )


@router.get("/google/{calendar_id}/events")
async def list_google_calendar_events(
    calendar_id: str,
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    time_min: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    time_max: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    max_results: int = Query(100, ge=1, le=2500, description="Max results (1-2500)"),
    db: Session = Depends(get_db)
):
    """
    List events from a Google Calendar.

    Path params:
    - calendar_id: Calendar ID (use "primary" for primary calendar)

    Query params:
    - account_email: Email of connected Google account
    - user_id: User ID (default: 1 for MVP)
    - time_min: Start date (ISO 8601), defaults to now
    - time_max: End date (ISO 8601), defaults to 30 days from now
    - max_results: Maximum number of events (1-2500), default 100

    Returns:
    - List of events with id, summary, start, end, description, location, status
    """
    # Get valid access token
    access_token = await get_google_token(account_email, user_id, db)

    # Create Calendar service
    service = get_calendar_service(access_token)

    # Default time range: now to 30 days from now
    if not time_min:
        time_min = datetime.utcnow().isoformat() + "Z"
    if not time_max:
        time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"

    try:
        # List events
        events_result = service.events().list(
            calendarId=calendar_id,
            timeMin=time_min,
            timeMax=time_max,
            maxResults=max_results,
            singleEvents=True,
            orderBy="startTime"
        ).execute()

        events = []
        for event in events_result.get("items", []):
            # Handle all-day events vs timed events
            start = event["start"].get("dateTime", event["start"].get("date"))
            end = event["end"].get("dateTime", event["end"].get("date"))
            is_all_day = "date" in event["start"]

            events.append({
                "id": event["id"],
                "summary": event.get("summary", "(No title)"),
                "description": event.get("description", ""),
                "location": event.get("location", ""),
                "start": start,
                "end": end,
                "is_all_day": is_all_day,
                "status": event.get("status", "confirmed"),
                "organizer": event.get("organizer", {}).get("email", ""),
                "attendees": [
                    {
                        "email": attendee.get("email", ""),
                        "response_status": attendee.get("responseStatus", "needsAction")
                    }
                    for attendee in event.get("attendees", [])
                ],
                "html_link": event.get("htmlLink", ""),
                "created": event.get("created", ""),
                "updated": event.get("updated", "")
            })

        return {
            "provider": "google",
            "account_email": account_email,
            "calendar_id": calendar_id,
            "time_min": time_min,
            "time_max": time_max,
            "events": events,
            "count": len(events)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch events: {str(e)}"
        )


@router.get("/google/{calendar_id}/events/{event_id}")
async def get_google_calendar_event(
    calendar_id: str,
    event_id: str,
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    Get a single event from a Google Calendar.

    Path params:
    - calendar_id: Calendar ID (use "primary" for primary calendar)
    - event_id: Event ID

    Query params:
    - account_email: Email of connected Google account
    - user_id: User ID (default: 1 for MVP)

    Returns:
    - Full event details
    """
    # Get valid access token
    access_token = await get_google_token(account_email, user_id, db)

    # Create Calendar service
    service = get_calendar_service(access_token)

    try:
        # Get event
        event = service.events().get(
            calendarId=calendar_id,
            eventId=event_id
        ).execute()

        # Handle all-day events vs timed events
        start = event["start"].get("dateTime", event["start"].get("date"))
        end = event["end"].get("dateTime", event["end"].get("date"))
        is_all_day = "date" in event["start"]

        return {
            "provider": "google",
            "account_email": account_email,
            "calendar_id": calendar_id,
            "event": {
                "id": event["id"],
                "summary": event.get("summary", "(No title)"),
                "description": event.get("description", ""),
                "location": event.get("location", ""),
                "start": start,
                "end": end,
                "is_all_day": is_all_day,
                "status": event.get("status", "confirmed"),
                "organizer": event.get("organizer", {}).get("email", ""),
                "attendees": [
                    {
                        "email": attendee.get("email", ""),
                        "display_name": attendee.get("displayName", ""),
                        "response_status": attendee.get("responseStatus", "needsAction"),
                        "optional": attendee.get("optional", False)
                    }
                    for attendee in event.get("attendees", [])
                ],
                "recurrence": event.get("recurrence", []),
                "html_link": event.get("htmlLink", ""),
                "created": event.get("created", ""),
                "updated": event.get("updated", ""),
                "color_id": event.get("colorId", "")
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch event: {str(e)}"
        )


# ============================================================================
# Microsoft Calendar Endpoints
# ============================================================================

@router.get("/microsoft")
async def list_microsoft_calendars(
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    List all calendars for a Microsoft account.

    Query params:
    - account_email: Email of connected Microsoft account
    - user_id: User ID (default: 1 for MVP)

    Returns:
    - List of calendars with id, name, description, timezone
    """
    # Get valid access token
    access_token = await get_microsoft_token(account_email, user_id, db)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://graph.microsoft.com/v1.0/me/calendars",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            data = response.json()

        calendars = []
        for cal in data.get("value", []):
            calendars.append({
                "id": cal["id"],
                "name": cal["name"],
                "description": cal.get("description", ""),
                "timezone": cal.get("timeZone", "UTC"),
                "is_default": cal.get("isDefaultCalendar", False),
                "color": cal.get("color", "auto"),
                "can_edit": cal.get("canEdit", False),
                "can_share": cal.get("canShare", False),
                "owner": cal.get("owner", {}).get("address", "")
            })

        return {
            "provider": "microsoft",
            "account_email": account_email,
            "calendars": calendars,
            "count": len(calendars)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch calendars: {str(e)}"
        )


@router.get("/microsoft/{calendar_id}/events")
async def list_microsoft_calendar_events(
    calendar_id: str,
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    time_min: Optional[str] = Query(None, description="Start date (ISO 8601 format)"),
    time_max: Optional[str] = Query(None, description="End date (ISO 8601 format)"),
    max_results: int = Query(100, ge=1, le=1000, description="Max results (1-1000)"),
    db: Session = Depends(get_db)
):
    """
    List events from a Microsoft Calendar.

    Path params:
    - calendar_id: Calendar ID

    Query params:
    - account_email: Email of connected Microsoft account
    - user_id: User ID (default: 1 for MVP)
    - time_min: Start date (ISO 8601), defaults to now
    - time_max: End date (ISO 8601), defaults to 30 days from now
    - max_results: Maximum number of events (1-1000), default 100

    Returns:
    - List of events with id, subject, start, end, description, location, status
    """
    # Get valid access token
    access_token = await get_microsoft_token(account_email, user_id, db)

    # Default time range: now to 30 days from now
    if not time_min:
        time_min = datetime.utcnow().isoformat() + "Z"
    if not time_max:
        time_max = (datetime.utcnow() + timedelta(days=30)).isoformat() + "Z"

    try:
        async with httpx.AsyncClient() as client:
            # Build query parameters
            params = {
                "$top": max_results,
                "$orderby": "start/dateTime",
                "$filter": f"start/dateTime ge '{time_min}' and end/dateTime le '{time_max}'"
            }

            response = await client.get(
                f"https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events",
                headers={"Authorization": f"Bearer {access_token}"},
                params=params
            )
            response.raise_for_status()
            data = response.json()

        events = []
        for event in data.get("value", []):
            # Check if all-day event
            is_all_day = event.get("isAllDay", False)
            start = event.get("start", {}).get("dateTime", "")
            end = event.get("end", {}).get("dateTime", "")

            events.append({
                "id": event["id"],
                "subject": event.get("subject", "(No title)"),
                "body": event.get("body", {}).get("content", ""),
                "body_type": event.get("body", {}).get("contentType", "text"),
                "location": event.get("location", {}).get("displayName", ""),
                "start": start,
                "end": end,
                "is_all_day": is_all_day,
                "status": event.get("showAs", "busy"),
                "is_cancelled": event.get("isCancelled", False),
                "organizer": event.get("organizer", {}).get("emailAddress", {}).get("address", ""),
                "attendees": [
                    {
                        "email": attendee.get("emailAddress", {}).get("address", ""),
                        "name": attendee.get("emailAddress", {}).get("name", ""),
                        "response_status": attendee.get("status", {}).get("response", "none"),
                        "type": attendee.get("type", "required")
                    }
                    for attendee in event.get("attendees", [])
                ],
                "web_link": event.get("webLink", ""),
                "created": event.get("createdDateTime", ""),
                "updated": event.get("lastModifiedDateTime", "")
            })

        return {
            "provider": "microsoft",
            "account_email": account_email,
            "calendar_id": calendar_id,
            "time_min": time_min,
            "time_max": time_max,
            "events": events,
            "count": len(events)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch events: {str(e)}"
        )


@router.get("/microsoft/{calendar_id}/events/{event_id}")
async def get_microsoft_calendar_event(
    calendar_id: str,
    event_id: str,
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    Get a single event from a Microsoft Calendar.

    Path params:
    - calendar_id: Calendar ID
    - event_id: Event ID

    Query params:
    - account_email: Email of connected Microsoft account
    - user_id: User ID (default: 1 for MVP)

    Returns:
    - Full event details
    """
    # Get valid access token
    access_token = await get_microsoft_token(account_email, user_id, db)

    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"https://graph.microsoft.com/v1.0/me/calendars/{calendar_id}/events/{event_id}",
                headers={"Authorization": f"Bearer {access_token}"}
            )
            response.raise_for_status()
            event = response.json()

        # Check if all-day event
        is_all_day = event.get("isAllDay", False)
        start = event.get("start", {}).get("dateTime", "")
        end = event.get("end", {}).get("dateTime", "")

        return {
            "provider": "microsoft",
            "account_email": account_email,
            "calendar_id": calendar_id,
            "event": {
                "id": event["id"],
                "subject": event.get("subject", "(No title)"),
                "body": event.get("body", {}).get("content", ""),
                "body_type": event.get("body", {}).get("contentType", "text"),
                "location": event.get("location", {}).get("displayName", ""),
                "start": start,
                "end": end,
                "is_all_day": is_all_day,
                "status": event.get("showAs", "busy"),
                "is_cancelled": event.get("isCancelled", False),
                "sensitivity": event.get("sensitivity", "normal"),
                "organizer": event.get("organizer", {}).get("emailAddress", {}).get("address", ""),
                "attendees": [
                    {
                        "email": attendee.get("emailAddress", {}).get("address", ""),
                        "name": attendee.get("emailAddress", {}).get("name", ""),
                        "response_status": attendee.get("status", {}).get("response", "none"),
                        "type": attendee.get("type", "required")
                    }
                    for attendee in event.get("attendees", [])
                ],
                "recurrence": event.get("recurrence"),
                "web_link": event.get("webLink", ""),
                "created": event.get("createdDateTime", ""),
                "updated": event.get("lastModifiedDateTime", ""),
                "categories": event.get("categories", []),
                "importance": event.get("importance", "normal")
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch event: {str(e)}"
        )
