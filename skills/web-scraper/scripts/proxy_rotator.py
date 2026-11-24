#!/usr/bin/env python3
"""
ProxyRotator - IP rotation for Chinese web scraping.
Usage:
    from proxy_rotator import ProxyRotator
    rotator = ProxyRotator()
    resp = rotator.request("https://www.baidu.com")
    # auto-retries with different proxies on failure
"""
import requests
import random
import time
from typing import Optional, Dict

class ProxyRotator:
    def __init__(self, proxy_file: str = None):
        self.proxies = []
        self.current_index = 0
        self.last_request_time = 0
        self.min_interval = 1.0
        if proxy_file:
            self.load_from_file(proxy_file)
    
    def load_from_file(self, filepath: str) -> int:
        count = 0
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    self.proxies.append(f"http://{line}")
                    count += 1
        return count
    
    def get_random(self) -> Optional[str]:
        if not self.proxies:
            return None
        return random.choice(self.proxies)
    
    def request(self, url: str, method: str = "GET", max_retries: int = 3,
                 **kwargs) -> Optional[requests.Response]:
        elapsed = time.time() - self.last_request_time
        if elapsed < self.min_interval:
            time.sleep(self.min_interval - elapsed)
        
        headers = kwargs.pop("headers", {
            "User-Agent": random.choice([
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36",
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            ])
        })
        
        for attempt in range(max_retries):
            proxy = self.get_random()
            if not proxy:
                return None
            try:
                resp = requests.request(
                    method, url,
                    proxies={"http": proxy, "https": proxy},
                    headers=headers,
                    timeout=kwargs.pop("timeout", 15),
                    **kwargs
                )
                self.last_request_time = time.time()
                return resp
            except Exception:
                if proxy in self.proxies:
                    self.proxies.remove(proxy)
                continue
        return None
    
    @property
    def count(self) -> int:
        return len(self.proxies)
