"""Turn a saved AO3 work page into a dictionary."""

import re

from bs4 import BeautifulSoup

from .client import CACHE_DIR

BLOCK_TAGS = ["p", "br", "hr", "li", "div", "blockquote", "h1", "h2", "h3", "h4", "h5", "h6"]


def plain_text(tag):
    """The text as a reader sees it: one line per paragraph or line break."""
    for string in tag.find_all(string=True):
        string.replace_with(re.sub(r"\s+", " ", string))
    for block in tag.find_all(BLOCK_TAGS):
        block.append("\n")
    return re.sub(r" *\n\s*", "\n", tag.get_text()).strip()


def parse_work(html):
    soup = BeautifulSoup(html, "html.parser")
    work = {
        "title": soup.select_one("h2.title").get_text(strip=True),
        "authors": [a.get_text() for a in soup.select("h3.byline a")],  # empty if anonymous
        "language": soup.select_one("dl.work.meta dd.language").get_text(strip=True),
        "series": [a.get_text() for a in soup.select("dd.series span.position a")],
        "collections": [a.get_text() for a in soup.select("dd.collections a")],
    }
    # rating, warning, category, fandom, relationship, character and freeform tags
    for dd in soup.select("dl.work.meta > dd.tags"):
        work[dd["class"][0]] = [a.get_text() for a in dd.select("a.tag")]
    # published, status (date last updated), words, chapters, comments, kudos, bookmarks, hits
    for dd in soup.select("dl.stats dd"):
        value = dd.get_text(strip=True).replace(",", "")
        work[dd["class"][0]] = int(value) if value.isdigit() else value

    summary = soup.select_one("#workskin > div.preface div.summary blockquote")
    work["summary"] = plain_text(summary) if summary else ""

    # A multi-chapter work has one div.chapter per chapter; a single-chapter work has none.
    work["content"] = []
    for chapter in soup.select("#chapters > div.chapter") or [soup.select_one("#chapters")]:
        title = chapter.select_one("h3.title")
        body = chapter.find("div", class_="userstuff")
        label = body.find("h3", class_="landmark", recursive=False)  # hidden "Chapter Text" heading
        if label:
            label.decompose()
        work["content"].append(
            {"title": " ".join(title.get_text().split()) if title else "", "text": plain_text(body)}
        )
    return work


if __name__ == "__main__":
    # Parse every saved work page and print one line per work.
    for file in sorted(CACHE_DIR.glob("%2Fworks%2F*")):
        work = parse_work(file.read_text(encoding="utf-8"))
        print(work["words"], work["chapters"], work["title"])
