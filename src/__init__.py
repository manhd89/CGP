import re
import os
from sys import exit
from libs.loguru import logger
from libs.dotenv import load_dotenv
from libs import requests 
from requests.adapters import HTTPAdapter

replace_pattern = re.compile(
    r"(^([0-9.]+|[0-9a-fA-F:.]+)\s+|^(\|\||@@\|\||\*\.|\*))"
)
domain_pattern = re.compile(
    r"^([a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?\.)*"
    r"[a-zA-Z0-9](?:[a-zA-Z0-9\-]*[a-zA-Z0-9])?$"
)
ip_pattern = re.compile(
    r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$"
)

load_dotenv()
CF_API_TOKEN = os.getenv("CF_API_TOKEN") or os.environ.get("CF_API_TOKEN")
CF_IDENTIFIER = os.getenv("CF_IDENTIFIER") or os.environ.get("CF_IDENTIFIER")
if not CF_API_TOKEN or not CF_IDENTIFIER:
    raise Exception("Missing Cloudflare credentials")
PREFIX = "AdBlock-DNS-Filters"
MAX_LIST_SIZE = 1000
MAX_LISTS = 300

session = requests.Session()
session.headers.update({
    "Authorization": f"Bearer {CF_API_TOKEN}",
    "Content-Type": "application/json",
    "Accept-Encoding": "gzip, deflate" 
})

adapter = HTTPAdapter(pool_connections=10, pool_maxsize=10, max_retries=3)
session.mount('http://', adapter)
session.mount('https://', adapter)

BASE_URL = f"https://api.cloudflare.com/client/v4/accounts/{CF_IDENTIFIER}/gateway"

def error(message):
    logger.error(message)
    exit(1)

def silent_error(message):
    logger.warning(message)
    exit(0)

def info(message):
    logger.info(message)
