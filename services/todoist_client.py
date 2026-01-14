import os
import requests
from dotenv import load_dotenv
from typing import Optional, List

load_dotenv()
TODOIST_API_TOKEN = os.getenv("TODOIST_API_TOKEN")
TODOIST_BASE_URL = "https://api.todoist.com/rest/v2"
HEADERS = {
    "Authorization": f"Bearer {TODOIST_API_TOKEN}"
}

def get_projects():
    response = requests.get(f"{TODOIST_BASE_URL}/projects", headers=HEADERS)
    return response.json()

def add_task(content: str, project_id: Optional[str] = None, due_string: Optional[str] = None):
    data = {"content": content}
    if project_id:
        data["project_id"] = project_id
    if due_string:
        data["due_string"] = due_string
    response = requests.post(f"{TODOIST_BASE_URL}/tasks", headers=HEADERS, json=data)
    return response.json()

def get_tasks(project_id: Optional[str] = None):
    params = {"project_id": project_id} if project_id else {}
    response = requests.get(f"{TODOIST_BASE_URL}/tasks", headers=HEADERS, params=params)
    return response.json()

def close_task(task_id: str):
    response = requests.post(f"{TODOIST_BASE_URL}/tasks/{task_id}/close", headers=HEADERS)
    return response.status_code == 204

def get_task_by_content(search_term: str, project_id: Optional[str] = None) -> List[dict]:
    tasks = get_tasks(project_id)
    return [t for t in tasks if search_term.lower() in t["content"].lower()]

def delete_task(task_id: str):
    response = requests.delete(f"{TODOIST_BASE_URL}/tasks/{task_id}", headers=HEADERS)
    return response.status_code == 204
