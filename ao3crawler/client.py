"""HTTP client for AO3: obeys robots.txt and waits between requests."""

import os
import time
from urllib.robotparser import RobotFileParser

import requests

BASE_URL = "https://archiveofourown.org"
BOT_NAME = "AO3FandomResearchCrawler"
DELAY = 5  # seconds between requests
ATTEMPTS = 3  # tries per page when AO3 times out or answers with a server error
RETRY_WAIT = 30  # seconds to wait before trying again

class Client:
    def __init__(self, contact):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            f"{BOT_NAME}/0.1 (academic research, non-commercial; contact: {contact})"
        )
        self.robots = RobotFileParser()
        self.robots.parse(self._fetch("/robots.txt").splitlines())

    def allowed(self, path):
        return self.robots.can_fetch(BOT_NAME, BASE_URL + path)

    def get(self, path):
        """Return the HTML of an AO3 page, e.g. get("/works/123")."""
        if not self.allowed(path):
            raise PermissionError(f"robots.txt disallows {path}")
        time.sleep(DELAY)
        return self._fetch(path)

    def _fetch(self, path):
        for attempt in range(ATTEMPTS):
            try:
                response = self.session.get(BASE_URL + path, timeout=30)
            except requests.Timeout:
                problem = "Timeout"
            else:
                if response.status_code < 500:
                    response.raise_for_status()  # 403, 404, ... are not retried
                    return response.text
                problem = f"HTTP {response.status_code}"
            print(f"{problem} on {path} (attempt {attempt + 1}/{ATTEMPTS})")
            time.sleep(RETRY_WAIT)
        raise RuntimeError(f"Gave up on {path} after {ATTEMPTS} attempts")


if __name__ == "__main__":
    # Probe: one request (robots.txt), then show what it permits.
    client = Client(os.environ["AO3_CRAWLER_CONTACT"])
    for path in [
        "/tags/Example/works?page=2",
        "/works/123",
        "/works?tag_id=Example",
        "/downloads/123/work.epub",
    ]:
        print(client.allowed(path), path)
