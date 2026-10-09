"""Fetch the page of every work in an AO3 fandom."""

import os
import sys

from .client import Client
from .listing import work_ids


def work_path(work_id):
    # view_adult skips the adult-content warning page; view_full_work puts all chapters on one page.
    return f"/works/{work_id}?view_adult=true&view_full_work=true"


def fetch_works(client, fandom):
    ids = list(work_ids(client, fandom))
    for number, work_id in enumerate(ids, 1):
        client.get(work_path(work_id))
        print(f"{number}/{len(ids)} {work_id}")


if __name__ == "__main__":
    fetch_works(Client(os.environ["AO3_CRAWLER_CONTACT"]), sys.argv[1])
