"""Fetch and parse the comments on the works of an AO3 fandom."""

import os
import sys
from datetime import datetime

from bs4 import BeautifulSoup

from .client import Client
from .listing import work_ids
from .parse import parse_work, plain_text
from .works import work_path


def comments_path(work_id, page):
    # The work page again, with one page of its comment threads (20 threads per page) shown.
    return f"/works/{work_id}?page={page}&show_comments=true&view_adult=true&view_full_work=true"


def comment_id(li):
    return int(li["id"].removeprefix("comment_"))


def parse_comment(li):
    byline = li.select_one("h4.byline")
    chapter = byline.select_one("span.parent a")
    posted = " ".join(byline.select_one("span.posted").get_text(" ").split())  # Wed 10 Apr 2019 07:09PM UTC
    # Replies sit in an unnamed <li> placed right after the comment they answer.
    thread = li.find_parent("li")
    return {
        "id": comment_id(li),
        "parent_id": comment_id(thread.find_previous_sibling("li")) if thread else None,
        "author": byline.find(["a", "span"]).get_text(),
        "guest": "guest" in li["class"],
        "chapter": chapter.get_text() if chapter else "",
        "posted": datetime.strptime(posted, "%a %d %b %Y %I:%M%p UTC").isoformat(sep=" "),
        "text": plain_text(li.select_one("blockquote.userstuff")),
    }


def work_comments(client, work_id):
    """Yield every comment shown for a work, page by page."""
    page = 1
    while True:
        soup = BeautifulSoup(client.get(comments_path(work_id, page)), "html.parser")
        area = soup.select_one("#comments_placeholder")
        # Only real comments have a byline; deleted ones and "more comments" links do not.
        for li in area.select("li.comment:has(> h4.byline)"):
            yield parse_comment(li)
        if not area.select_one("li.next a"):
            return
        page += 1


if __name__ == "__main__":
    client = Client(os.environ["AO3_CRAWLER_CONTACT"])
    for work_id in work_ids(client, sys.argv[1]):
        expected = parse_work(client.get(work_path(work_id))).get("comments", 0)
        if expected:
            found = sum(1 for _ in work_comments(client, work_id))
            print(f"{work_id}: {found} of {expected} comments")
