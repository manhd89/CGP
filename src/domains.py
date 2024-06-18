import os
import requests
from configparser import ConfigParser
from concurrent.futures import ThreadPoolExecutor, as_completed
from src import info, convert

class DomainConverter:
    def __init__(self):
        self.env_file_map = {
            "ADLIST_URLS": "./lists/adlist.ini",
            "WHITELIST_URLS": "./lists/whitelist.ini",
            "DYNAMIC_BLACKLIST": "./lists/dynamic_blacklist.txt",
            "DYNAMIC_WHITELIST": "./lists/dynamic_whitelist.txt"
        }
        self.adlist_urls = self.read_urls("ADLIST_URLS")
        self.whitelist_urls = self.read_urls("WHITELIST_URLS")

    def read_urls_from_file(self, filename):
        urls = []
        try:
            config = ConfigParser()
            config.read(filename)
            for section in config.sections():
                for key in config.options(section):
                    if not key.startswith("#"):
                        urls.append(config.get(section, key))
        except Exception:
            with open(filename, "r") as file:
                urls = [
                    url.strip() for url in file if not url.startswith("#") and url.strip()
                ]
        return urls
    
    def read_urls_from_env(self, env_var):
        urls = os.getenv(env_var, "")
        return [
            url.strip() for url in urls.split() if url.strip()
        ]

    def read_urls(self, env_var):
        file_path = self.env_file_map[env_var]
        urls = self.read_urls_from_file(file_path)
        urls += self.read_urls_from_env(env_var)
        return urls

    def download_file(self, url):
        try:
            r = requests.get(url, allow_redirects=True)
            info(f"Downloaded file from {url} File size: {len(r.content)}")
            return r.text
        except Exception as e:
            info(f"Failed to download {url}: {e}")
            return ""

    def download_files_concurrently(self, urls):
        content_map = {}
        with ThreadPoolExecutor(max_workers=10) as executor:
            future_to_url = {executor.submit(self.download_file, url): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                content = future.result()
                if url not in content_map:  # Ensure no duplicates
                    content_map[url] = content
        return content_map

    def process_urls(self):
        all_urls = list(set(self.adlist_urls + self.whitelist_urls))  # Remove any duplicate URLs
        downloaded_content = self.download_files_concurrently(all_urls)

        block_content = ''.join([downloaded_content[url] for url in self.adlist_urls if url in downloaded_content])
        white_content = ''.join([downloaded_content[url] for url in self.whitelist_urls if url in downloaded_content])
        
        # Check for dynamic blacklist and whitelist in environment variables
        dynamic_blacklist = os.getenv("DYNAMIC_BLACKLIST", "")
        dynamic_whitelist = os.getenv("DYNAMIC_WHITELIST", "")
        
        if dynamic_blacklist:
            block_content += dynamic_blacklist
        else:
            with open(self.env_file_map["DYNAMIC_BLACKLIST"], "r") as black_file:
                block_content += black_file.read()
        
        if dynamic_whitelist:
            white_content += dynamic_whitelist
        else:
            with open(self.env_file_map["DYNAMIC_WHITELIST"], "r") as white_file:
                white_content += white_file.read()
        
        domains = convert.convert_to_domain_list(block_content, white_content)
        return domains
