# AO3_Crawler

## The First Crawler

How to use:
```bash
AO3_CRAWLER_CONTACT="you@example.org" .venv/bin/python -m ao3crawler.client
```

Replace with an academic email as outlined in the ToS. For my case:
```bash
AO3_CRAWLER_CONTACT="peichun@alumni.unc.edu" .venv/bin/python -m ao3crawler.client
True /tags/Example/works?page=2
True /works/123
False /works?tag_id=Example
False /downloads/123/work.epub
```

## Pick a Fandom!
To choose a fandom: AO3 groups fandoms into 11 categories: Anime & Manga, Books & Literature, Cartoons & Comics & Graphic Novels, Celebrities & Real People, Movies, Music & Bands, Other Media, Theater, TV Shows, Video Games, and Uncategorized.

The assignment says under 10,000 works. Some famous ones are too large (Harry Potter has 615,362, Marvel 702,844, Genshin Impact 255,284). Mid-sized ones fit well. For example, Hamlet - Shakespeare has 1375. Operation Mincemeat - SpitLip has 859. Hadestown has 1925. I am starting with a small MacBeth - Shakespeare (596).

## A Robust Crawler

- Retries in `client.py`: when a request times out (30 seconds) or AO3 answers with a server error (HTTP 500 and above, e.g. 525), the same page is tried again, up to 6 attempts in total (ATTEMPTS = 6).
- The wait before each retry doubles: 30, 60, 120, 240, then 480 seconds (RETRY_WAIT = 30). A server that’s struggling gets longer and longer pauses, about 15 minutes in total, so retries are always slower than normal requests. This follows ToS as for a "gentle" crawling. After the 6th failed attempt it raises RuntimeError and the run stops.
- 403 and 404 are never retried; they crash immediately, so a bot challenge is never retried.
- `tag_path(fandom)` turns a fandom name into its listing URL. AO3 replaces five characters with codes (for example / becomes *s*), and the rest is ordinary URL encoding. "Macbeth - Shakespeare" becomes /tags/Macbeth%20-%20Shakespeare/works.
- `work_ids(client, fandom)` fetches the listing page by page through your Client and yields each work’s ID. It stops when a page has no “Next” link.
- Running `listing.py` prints every ID, then a count of total and unique IDs.

```bash
no_proxy=archiveofourown.org NO_PROXY=archiveofourown.org AO3_CRAWLER_CONTACT="peichun@alumni.unc.edu" .venv/bin/python -m ao3crawler.listing "Macbeth - Shakespeare"
93687511
94174341
92481121
93866181
...
```

Success:
- Output comes in bursts of 20 in terms of listing. The script prints one page’s IDs, waits 5 seconds, then fetches the next page, which is taking AO3 up to 20 seconds at the moment. Quiet gaps of half a minute are normal.
- There are 30 pages. The whole run takes roughly 10 minutes.
- The last line reads 593 works, 593 unique
- A few retry messages. A line like `HTTP 525 on ...; retry 1/5 in 30s` followed by a pause of that length.
