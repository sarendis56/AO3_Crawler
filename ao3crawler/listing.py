"""List the works in an AO3 fandom."""

import os
import re
import sys
from urllib.parse import quote

from .client import Client

# AO3 writes these characters as codes in tag URLs, e.g. "Martin/West" -> "Martin*s*West".
TAG_CODES = {"/": "*s*", "&": "*a*", ".": "*d*", "?": "*q*", "#": "*h*"}


def tag_path(fandom):
    for char, code in TAG_CODES.items():
        fandom = fandom.replace(char, code)
    return f"/tags/{quote(fandom, safe='*')}/works"


def work_ids(client, fandom):
    """Yield the id of every work in a fandom, most recently updated first."""
    page = 1
    while True:
        html = client.get(f"{tag_path(fandom)}?page={page}")
        yield from re.findall(r'<li id="work_(\d+)"', html)
        if '<li class="next"><a ' not in html:  # the last page has no "Next" link
            return
        page += 1


if __name__ == "__main__":
    client = Client(os.environ["AO3_CRAWLER_CONTACT"])
    ids = []
    for work_id in work_ids(client, sys.argv[1]):
        print(work_id)
        ids.append(work_id)
    print(f"{len(ids)} works, {len(set(ids))} unique")
