import os
import http.client
import json
import urllib.parse
import gzip
import zlib
import sys
from src import CF_API_TOKEN, CF_IDENTIFIER

class RequestException(Exception):
    pass

class HTTPError(RequestException):
    pass

class Session:
    def __init__(self):
        self.headers = {
            "Authorization": f"Bearer {CF_API_TOKEN}",
            "Content-Type": "application/json",
            "Accept-Encoding": "gzip, deflate"
        }
        self.base_url = f"https://api.cloudflare.com/client/v4/accounts/{CF_IDENTIFIER}/gateway"

    def _decode_response(self, response):
        content_encoding = response.getheader('Content-Encoding', '')
        response_body = response.read()
        
        if content_encoding == 'gzip':
            response_body = gzip.decompress(response_body).decode('utf-8')
        elif content_encoding == 'deflate':
            response_body = zlib.decompress(response_body).decode('utf-8')
        else:
            response_body = response_body.decode('utf-8')
        
        return response_body

    def _request(self, method, url, data=None):
        parsed_url = urllib.parse.urlparse(url)
        connection = http.client.HTTPSConnection(parsed_url.netloc)
        
        body = None
        if data:
            body = json.dumps(data)
        
        connection.request(method, parsed_url.path + ('?' + parsed_url.query if parsed_url.query else ''), body, self.headers)
        response = connection.getresponse()
        
        response_body = self._decode_response(response)
        
        if response.status >= 400:
            if response.status == 400:
                print(f"Request failed with 400 Bad Request: {response_body}")
                sys.exit(1)
            raise HTTPError(f"Request failed: {response.status} {response.reason}, Body: {response_body}")
        
        return response_body

    def get(self, url):
        return self._request("GET", url)

    def post(self, url, json=None):
        return self._request("POST", url, json)

    def patch(self, url, json=None):
        return self._request("PATCH", url, json)

    def delete(self, url):
        return self._request("DELETE", url)

# Create a session instance
session = Session()