"""Build a SQLite database from the saved pages of a fandom. Makes no requests."""

import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

from .client import SavedPages, cache_file
from .comments import work_comments
from .listing import work_ids
from .parse import parse_work
from .works import work_path

SCHEMA = """
CREATE TABLE works (
    work_id INTEGER PRIMARY KEY, title TEXT, authors TEXT, rating TEXT, language TEXT,
    published TEXT, updated TEXT, words INTEGER, chapters TEXT, comments INTEGER,
    kudos INTEGER, bookmarks INTEGER, hits INTEGER, series TEXT, collections TEXT,
    summary TEXT, fetched_at TEXT
);
CREATE TABLE tags (work_id INTEGER, type TEXT, tag TEXT);
CREATE TABLE chapters (work_id INTEGER, number INTEGER, title TEXT, text TEXT);
CREATE TABLE comments (
    comment_id INTEGER PRIMARY KEY, work_id INTEGER, parent_id INTEGER, author TEXT,
    guest INTEGER, chapter TEXT, posted TEXT, text TEXT
);
"""
TAG_TYPES = ["warning", "category", "fandom", "relationship", "character", "freeform"]


def export(fandom, db_path):
    pages = SavedPages()
    Path(db_path).unlink(missing_ok=True)  # always rebuilt from scratch
    db = sqlite3.connect(db_path)
    db.executescript(SCHEMA)
    for work_id in work_ids(pages, fandom):
        work = parse_work(pages.get(work_path(work_id)))
        fetched = datetime.fromtimestamp(cache_file(work_path(work_id)).stat().st_mtime, timezone.utc)
        db.execute(
            "INSERT INTO works VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                work_id,
                work["title"],
                "; ".join(work["authors"]),  # empty if anonymous
                "; ".join(work["rating"]),
                work["language"],
                work["published"],
                work.get("status", work["published"]),  # AO3 shows no update date if never updated
                None if work["words"] == "" else work["words"],  # AO3 leaves it blank for a few works
                work["chapters"],
                work.get("comments", 0),  # AO3 omits counts that are zero
                work.get("kudos", 0),
                work.get("bookmarks", 0),
                work["hits"],
                "; ".join(work["series"]),
                "; ".join(work["collections"]),
                work["summary"],
                fetched.isoformat(sep=" ", timespec="seconds"),
            ),
        )
        for tag_type in TAG_TYPES:
            for tag in work.get(tag_type, []):
                db.execute("INSERT INTO tags VALUES (?, ?, ?)", (work_id, tag_type, tag))
        for number, chapter in enumerate(work["content"], 1):
            db.execute(
                "INSERT INTO chapters VALUES (?, ?, ?, ?)",
                (work_id, number, chapter["title"], chapter["text"]),
            )
        if work.get("comments"):
            for comment in work_comments(pages, work_id):
                db.execute(
                    "INSERT INTO comments VALUES "
                    "(:id, :work_id, :parent_id, :author, :guest, :chapter, :posted, :text)",
                    {**comment, "work_id": work_id},
                )
    db.commit()
    for table in ["works", "tags", "chapters", "comments"]:
        print(table, db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0])


if __name__ == "__main__":
    export(sys.argv[1], sys.argv[2])
