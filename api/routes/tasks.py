"""
Tasks API routes for Google Tasks access.
Used by consuming services to fetch task data using OAuth tokens.
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, List
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials

from api.database import get_db
from api.oauth.google import get_valid_token
from api.config import get_settings

router = APIRouter()
settings = get_settings()


def get_tasks_service(access_token: str):
    """Create Google Tasks API service with access token."""
    credentials = Credentials(token=access_token)
    service = build("tasks", "v1", credentials=credentials)
    return service


@router.get("/google")
async def list_google_task_lists(
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    List all task lists for a Google account.

    Query params:
    - account_email: Email of connected Google account
    - user_id: User ID (default: 1 for MVP)

    Returns:
    - List of task lists with id, title, updated timestamp
    """
    # Get valid access token
    access_token = await get_valid_token(account_email, user_id, db)

    # Create Tasks service
    service = get_tasks_service(access_token)

    try:
        # List task lists
        task_lists_result = service.tasklists().list().execute()

        task_lists = []
        for task_list in task_lists_result.get("items", []):
            task_lists.append({
                "id": task_list["id"],
                "title": task_list["title"],
                "updated": task_list.get("updated", ""),
                "self_link": task_list.get("selfLink", "")
            })

        return {
            "provider": "google",
            "account_email": account_email,
            "task_lists": task_lists,
            "count": len(task_lists)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch task lists: {str(e)}"
        )


@router.get("/google/{tasklist_id}/items")
async def list_google_tasks(
    tasklist_id: str,
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    status: Optional[str] = Query(None, description="Filter by status: needsAction, completed"),
    show_completed: bool = Query(True, description="Include completed tasks"),
    show_hidden: bool = Query(False, description="Include hidden (deleted) tasks"),
    max_results: int = Query(100, ge=1, le=100, description="Max results (1-100)"),
    db: Session = Depends(get_db)
):
    """
    List tasks from a Google Task List.

    Path params:
    - tasklist_id: Task List ID (use "@default" for default list)

    Query params:
    - account_email: Email of connected Google account
    - user_id: User ID (default: 1 for MVP)
    - status: Filter by status (needsAction, completed)
    - show_completed: Include completed tasks (default: true)
    - show_hidden: Include hidden/deleted tasks (default: false)
    - max_results: Maximum number of tasks (1-100), default 100

    Returns:
    - List of tasks with id, title, notes, due, status, completed timestamp
    """
    # Get valid access token
    access_token = await get_valid_token(account_email, user_id, db)

    # Create Tasks service
    service = get_tasks_service(access_token)

    try:
        # List tasks
        tasks_result = service.tasks().list(
            tasklist=tasklist_id,
            showCompleted=show_completed,
            showHidden=show_hidden,
            maxResults=max_results
        ).execute()

        tasks = []
        for task in tasks_result.get("items", []):
            # Filter by status if specified
            task_status = task.get("status", "needsAction")
            if status and task_status != status:
                continue

            tasks.append({
                "id": task["id"],
                "title": task.get("title", "(No title)"),
                "notes": task.get("notes", ""),
                "status": task_status,
                "due": task.get("due", ""),
                "completed": task.get("completed", ""),
                "updated": task.get("updated", ""),
                "parent": task.get("parent", ""),  # For subtasks
                "position": task.get("position", ""),
                "self_link": task.get("selfLink", ""),
                "links": [
                    {
                        "type": link.get("type", ""),
                        "description": link.get("description", ""),
                        "link": link.get("link", "")
                    }
                    for link in task.get("links", [])
                ]
            })

        return {
            "provider": "google",
            "account_email": account_email,
            "tasklist_id": tasklist_id,
            "tasks": tasks,
            "count": len(tasks)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch tasks: {str(e)}"
        )


@router.get("/google/{tasklist_id}/items/{task_id}")
async def get_google_task(
    tasklist_id: str,
    task_id: str,
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    db: Session = Depends(get_db)
):
    """
    Get a single task from a Google Task List.

    Path params:
    - tasklist_id: Task List ID (use "@default" for default list)
    - task_id: Task ID

    Query params:
    - account_email: Email of connected Google account
    - user_id: User ID (default: 1 for MVP)

    Returns:
    - Full task details
    """
    # Get valid access token
    access_token = await get_valid_token(account_email, user_id, db)

    # Create Tasks service
    service = get_tasks_service(access_token)

    try:
        # Get task
        task = service.tasks().get(
            tasklist=tasklist_id,
            task=task_id
        ).execute()

        return {
            "provider": "google",
            "account_email": account_email,
            "tasklist_id": tasklist_id,
            "task": {
                "id": task["id"],
                "title": task.get("title", "(No title)"),
                "notes": task.get("notes", ""),
                "status": task.get("status", "needsAction"),
                "due": task.get("due", ""),
                "completed": task.get("completed", ""),
                "updated": task.get("updated", ""),
                "parent": task.get("parent", ""),  # For subtasks
                "position": task.get("position", ""),
                "self_link": task.get("selfLink", ""),
                "links": [
                    {
                        "type": link.get("type", ""),
                        "description": link.get("description", ""),
                        "link": link.get("link", "")
                    }
                    for link in task.get("links", [])
                ],
                "etag": task.get("etag", ""),
                "kind": task.get("kind", "")
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch task: {str(e)}"
        )


@router.get("/google/{tasklist_id}/items/{task_id}/subtasks")
async def list_google_task_subtasks(
    tasklist_id: str,
    task_id: str,
    account_email: str,
    user_id: int = 1,  # MVP: hardcoded user
    show_completed: bool = Query(True, description="Include completed subtasks"),
    db: Session = Depends(get_db)
):
    """
    List subtasks for a specific task.

    Path params:
    - tasklist_id: Task List ID (use "@default" for default list)
    - task_id: Parent task ID

    Query params:
    - account_email: Email of connected Google account
    - user_id: User ID (default: 1 for MVP)
    - show_completed: Include completed subtasks (default: true)

    Returns:
    - List of subtasks
    """
    # Get valid access token
    access_token = await get_valid_token(account_email, user_id, db)

    # Create Tasks service
    service = get_tasks_service(access_token)

    try:
        # List all tasks in the list
        tasks_result = service.tasks().list(
            tasklist=tasklist_id,
            showCompleted=show_completed
        ).execute()

        # Filter for subtasks of the given parent
        subtasks = []
        for task in tasks_result.get("items", []):
            if task.get("parent") == task_id:
                subtasks.append({
                    "id": task["id"],
                    "title": task.get("title", "(No title)"),
                    "notes": task.get("notes", ""),
                    "status": task.get("status", "needsAction"),
                    "due": task.get("due", ""),
                    "completed": task.get("completed", ""),
                    "updated": task.get("updated", ""),
                    "position": task.get("position", "")
                })

        return {
            "provider": "google",
            "account_email": account_email,
            "tasklist_id": tasklist_id,
            "parent_task_id": task_id,
            "subtasks": subtasks,
            "count": len(subtasks)
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch subtasks: {str(e)}"
        )
