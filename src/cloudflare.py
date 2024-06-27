from src.requests import session, HTTPError, RequestException
from src import info, BASE_URL, MAX_LIST_SIZE, rate_limited_request, retry, stop_never, wait_random_exponential, retry_if_exception_type
import json

retry_config = {
    'stop': stop_never,
    'wait': lambda attempt_number: wait_random_exponential(
        attempt_number, multiplier=1, max_wait=10
    ),
    'retry': retry_if_exception_type((HTTPError, RequestException)),
    'after': lambda retry_state: info(
        f"Retrying ({retry_state['attempt_number']}): {retry_state['outcome']}"
    ),
    'before_sleep': lambda retry_state: info(
        f"Sleeping before next retry ({retry_state['attempt_number']})"
    )
}

@retry(**retry_config)
def get_current_lists():
    response = session.get(f"{BASE_URL}/lists")
    return json.loads(response)

@retry(**retry_config)
def get_current_policies():
    response = session.get(f"{BASE_URL}/rules")
    return json.loads(response)

@retry(**retry_config)
def get_list_items(list_id):
    response = session.get(f"{BASE_URL}/lists/{list_id}/items?limit={MAX_LIST_SIZE}")
    return json.loads(response)

@retry(**retry_config)
@rate_limited_request
def patch_list(list_id, payload):
    response = session.patch(f"{BASE_URL}/lists/{list_id}", json=payload)
    return json.loads(response)

@retry(**retry_config)
@rate_limited_request
def create_list(payload):
    response = session.post(f"{BASE_URL}/lists", json=payload)
    return json.loads(response)

@retry(**retry_config)
def create_policy(json_data):
    response = session.post(f"{BASE_URL}/rules", json=json_data)
    return json.loads(response)

@retry(**retry_config)
def update_policy(policy_id, json_data):
    response = session.patch(f"{BASE_URL}/rules/{policy_id}", json=json_data)
    return json.loads(response)

@retry(**retry_config)
@rate_limited_request
def delete_list(list_id):
    response = session.delete(f"{BASE_URL}/lists/{list_id}")
    return json.loads(response)

@retry(**retry_config)
def delete_policy(policy_id):
    response = session.delete(f"{BASE_URL}/rules/{policy_id}")
    return json.loads(response)