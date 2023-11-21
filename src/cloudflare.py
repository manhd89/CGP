import json
from src import (
    error,
    session,
    BASE_URL,
    MAX_LIST_SIZE
)

def get_current_lists():
    response = session.get(
        f"{BASE_URL}/lists"
    )
    if response.status_code == 200:
        return response.json()
    else:
        error("Failed to get current lists")

def get_current_policies():
    response = session.get(
        f"{BASE_URL}/rules"
    )
    if response.status_code == 200:
        return response.json()
    else:
        error("Failed to get current policies")

def get_list_items(list_id):
    response = session.get(
        f"{BASE_URL}/lists/{list_id}/items?limit={MAX_LIST_SIZE}"
    )
    if response.status_code == 200:
        return response.json()
    else:
        error(f"Failed to get list items")

def patch_list(list_id, payload):
    response = session.patch(
        f"{BASE_URL}/lists/{list_id}",
        json=payload
    )
    if response.status_code == 200:
        return response.json()
    else:
        error(f"Failed to patch list")

def create_list(payload):
    response = session.post(
        f"{BASE_URL}/lists",
        json=payload
    )
    if response.status_code == 200:
        return response.json()
    else:
        error("Failed to create list")

def create_policy(json_data):
    response = session.post(
        f"{BASE_URL}/rules",
        json=json_data
    )
    if response.status_code == 200:
        return response.json()
    else:
        error("Failed to create policy")

def update_policy(policy_id, json_data):
    response = session.put(
        f"{BASE_URL}/rules/{policy_id}",
        json=json_data
    )
    if response.status_code == 200:
        return response.json()
    else:
        error(f"Failed to update policy")

def delete_list(list_id):
    response = session.delete(
        f"{BASE_URL}/lists/{list_id}"
    )
    if response.status_code == 200:
        return response.json()
    else:
        error(f"Failed to delete list")

def delete_policy(policy_id):
    response = session.delete(
        f"{BASE_URL}/rules/{policy_id}"
    )
    if response.status_code == 200:
        return response.json()
    else:
        error(f"Failed to delete policy")
