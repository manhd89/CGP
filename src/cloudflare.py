import json
import http.client
import gzip
from io import BytesIO
from http.client import HTTPException
from src import (
    info, conn, headers, BASE_URL, MAX_LIST_SIZE, rate_limited_request,
    retry, stop_never, wait_random_exponential, retry_if_exception_type
)

retry_config = {
    'stop': stop_never,
    'wait': lambda attempt_number: wait_random_exponential(
        attempt_number, multiplier=1, max_wait=10
    ),
    'retry': retry_if_exception_type((HTTPException,)),
    'after': lambda retry_state: info(
        f"Retrying ({retry_state['attempt_number']}): {retry_state['outcome'].exception()}"
    ),
    'before_sleep': lambda retry_state: info(
        f"Sleeping before next retry ({retry_state['attempt_number']})"
    )
}

def perform_request(method, endpoint, headers, body=None):
    url = BASE_URL + endpoint
    conn.request(method, url, body, headers)
    response = conn.getresponse()
    data = response.read()
    status = response.status

    if status >= 400:
        error_message = f"HTTP request failed with status {status}"
        if status == 400:
            error_message = "400 Client Error: Bad Request"
        elif status == 401:
            error_message = "401 Client Error: Unauthorized"
        elif status == 403:
            error_message = "403 Client Error: Forbidden"
        elif status == 404:
            error_message = "404 Client Error: Not Found"
        elif status == 429:
            error_message = "429 Client Error: Too Many Requests"
        elif status >= 500:
            error_message = f"{status} Server Error"

        full_error_message = f"{error_message} for url: {url}"
        info(full_error_message)
        raise HTTPException(full_error_message)

    if response.getheader('Content-Encoding') == 'gzip':
        buf = BytesIO(data)
        f = gzip.GzipFile(fileobj=buf)
        data = f.read()

    return response.status, json.loads(data.decode('utf-8'))

@retry(**retry_config)
def get_current_lists():
    status, data = perform_request("GET", "/client/v4/lists", headers)
    return data

@retry(**retry_config)
def get_current_policies():
    status, data = perform_request("GET", "/client/v4/rules", headers)
    return data

@retry(**retry_config)
def get_list_items(list_id):
    status, data = perform_request("GET", f"/client/v4/lists/{list_id}/items?limit={MAX_LIST_SIZE}", headers)
    return data

@retry(**retry_config)
@rate_limited_request
def patch_list(list_id, payload):
    body = json.dumps(payload)
    status, data = perform_request("PATCH", f"/client/v4/lists/{list_id}", headers, body)
    return data

@retry(**retry_config)
@rate_limited_request
def create_list(payload):
    body = json.dumps(payload)
    status, data = perform_request("POST", "/client/v4/lists", headers, body)
    return data

@retry(**retry_config)
@rate_limited_request
def delete_list(list_id):
    status, data = perform_request("DELETE", f"/client/v4/lists/{list_id}", headers)
    return data

@retry(**retry_config)
def create_policy(json_data):
    body = json.dumps(json_data)
    status, data = perform_request("POST", "/client/v4/rules", headers, body)
    return data

@retry(**retry_config)
def update_policy(policy_id, json_data):
    body = json.dumps(json_data)
    status, data = perform_request("PUT", f"/client/v4/rules/{policy_id}", headers, body)
    return data

@retry(**retry_config)
def delete_policy(policy_id):
    status, data = perform_request("DELETE", f"/client/v4/rules/{policy_id}", headers)
    return data
