# AO3 Crawler

A crawler for one fandom on Archive of Our Own (AO3). Without logging in, it saves each work's metadata, text and comments into a SQLite database. The sample is the Macbeth - Shakespeare fandom (593 works), and `analysis.ipynb` is an exploratory analysis of it.

The sections below follow the order in which the crawler was built.

## Setup

```bash
python3 -m venv .venv
```

```bash
.venv/bin/pip install -r requirements.txt
```

The sample database `macbeth.db` should be [downloaded](https://drive.google.com/file/d/16E98yMfeKC373nHFpUuBj-CoUsTqneY7/view?usp=sharing) separately and put next to `analysis.ipynb` to run the notebook.

## The First Crawler

How to use:
```bash
$ AO3_CRAWLER_CONTACT="you@example.org" .venv/bin/python -m ao3crawler.client
```

Replace with your own email as a courtesy. It goes into the User-Agent header of every request, so that AO3 can reach the person running the crawler. For my case:
```bash
$ AO3_CRAWLER_CONTACT="peichun@alumni.unc.edu" .venv/bin/python -m ao3crawler.client
True /tags/Example/works?page=2
True /works/123
False /works?tag_id=Example
False /downloads/123/work.epub
```

## Pick a Fandom!
To choose a fandom: AO3 groups fandoms into 11 categories: Anime & Manga, Books & Literature, Cartoons & Comics & Graphic Novels, Celebrities & Real People, Movies, Music & Bands, Other Media, Theater, TV Shows, Video Games, and Uncategorized.

Some famous ones are too large (Harry Potter has 615,362, Marvel 702,844, Genshin Impact 255,284) to crawl. Mid-sized ones fit well. For example, Hamlet - Shakespeare has 1375. Operation Mincemeat - SpitLip has 859. Hadestown has 1925. I am starting with a relatively small Macbeth - Shakespeare.

## A Robust Crawler for Listings

- Timeout in `client.py`: a request waits up to 60 seconds for AO3 to answer (TIMEOUT = 60). It was 30 at first, but AO3 can take 20 seconds or more to build a page when it is busy, and giving up early only makes the server build the same page again on the retry.
- Retries in `client.py`: when a request times out or AO3 answers with a server error (HTTP 500 and above, e.g. 525), the same page is tried again, up to 6 attempts in total (ATTEMPTS = 6).
- The wait before each retry doubles: 30, 60, 120, 240, then 480 seconds (RETRY_WAIT = 30). A server that’s struggling gets longer and longer pauses, about 15 minutes in total, so retries are always slower than normal requests. This follows ToS as for a "gentle" crawling. After the 6th failed attempt it raises RuntimeError and the run stops.
- 403 and 404 are never retried; they crash immediately, so a bot challenge is never retried.
- Saved pages in `client.py`: every page that is fetched is written to `cache/` (CACHE_DIR), named after its path.
- `tag_path(fandom)` turns a fandom name into its listing URL. AO3 replaces five characters with codes (for example / becomes *s*), and the rest is ordinary URL encoding. "Macbeth - Shakespeare" becomes /tags/Macbeth%20-%20Shakespeare/works.
- `work_ids(client, fandom)` fetches the listing page by page through your Client and yields each work’s ID. It stops when a page has no “Next” link.
- Running `listing.py` prints every ID, then a count of total and unique IDs.

```bash
$ no_proxy=archiveofourown.org NO_PROXY=archiveofourown.org AO3_CRAWLER_CONTACT="peichun@alumni.unc.edu" .venv/bin/python -m ao3crawler.listing "Macbeth - Shakespeare"
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

To keep the laptop open, use caffeinate:
```bash
AO3_CRAWLER_CONTACT="peichun@alumni.unc.edu" caffeinate -i .venv/bin/python -m ao3crawler.works "Macbeth - Shakespeare"
```

## Extract the Content (Parsing)

`parse_work(html)` in `parse.py` gives one dictionary per work:
- Identity: title, authors (empty for anonymous works), language, series, collections.
- Tags, each a list: rating, warning, category, fandom, relationship, character, freeform.
- Statistics: published, status (AO3’s name for the date last updated), words, chapters (such as "8/31"), comments, kudos, bookmarks, hits.
- Text: summary, and content, a list of chapters each with a title and plain text, one line per paragraph.

For Macbeth - Shakespeare:
- All 593 of 593 are real work pages. None is an adult-warning page, a login page or an error page.
They hold 1,739 chapters in 46 MB.
- AO3 omits kudos, comments or bookmarks when they are zero, and status for works never updated. The storage stage will fill those in.

```bash
.venv/bin/python -m ao3crawler.parse
```

## Extract the Comments

- Address: `/works/<id>?page=N&show_comments=true&view_adult=true&view_full_work=true`. This is the address AO3’s own “Comments” and page links lead to, and robots.txt allows it. AO3 has no lighter comments-only page for a plain request, so each one re-sends the work text as well.
- Paging: AO3 shows 20 comment threads per page. The code follows the “Next” link until there is none.
Only works with comments are requested. 162 works are with no comments.
- Each comment becomes a dictionary: `id`, `parent_id` (the comment it replies to, or none), author, guest (true for commenters without an account), chapter, posted (date and time, UTC) and text.
- Pages are saved to `cache/`.
- I also found that there are collapsed threads, which are not followed for now. AO3 collapses deep reply chains behind links like “16 more comments in this thread”. Getting those means one extra request per collapsed thread.
- The first work in the list has a deleted comment. AO3 leaves a placeholder for a deleted comment, “(Previous comment deleted.)”, with a comment ID but no author, date or text.
- Interestingly, it might be the case that there is new comment between the time of page saving and the time of comment crawling:
  - Work page, saved 9 Oct 18:57 UTC: AO3’s comment count on it is 11. That is where the script gets its “of 11”.
  - Comments page, saved 10 Oct 03:06 UTC: AO3’s own count on it is 12, and we parsed 12 comments, all with unique IDs. The newest comment was posted on 9 Oct at 19:45 UTC, 48 minutes after the work page was saved.
  - Therefore, the saved comments are the timestamp of the later date among the above two.
  
```bash
AO3_CRAWLER_CONTACT="peichun@alumni.unc.edu" caffeinate -i .venv/bin/python -m ao3crawler.comments "Macbeth - Shakespeare"
```

## Export Databases

Schema:

| Table      | Rows   | Each row is         | Columns                                                      |
| ---------- | ------ | ------------------- | ------------------------------------------------------------ |
| `works`    | 593    | a work              | `work_id`, `title`, `authors`, `rating`, `language`, `published`, `updated`, `words`, `chapters`, `comments`, `kudos`, `bookmarks`, `hits`, `series`, `collections`, `summary`, `fetched_at` |
| `tags`     | 12,297 | one tag on one work | `work_id`, `type`, `tag`                                     |
| `chapters` | 1,739  | a chapter           | `work_id`, `number`, `title`, `text`                         |
| `comments` | 3,847  | a comment           | `comment_id`, `work_id`, `parent_id`, `author`, `guest`, `chapter`, `posted`, `text` |

- `tags.type` is one of `warning`, `category`, `fandom`, `relationship`, `character`, `freeform`.
- `authors`, `series` and `collections` hold several values joined with `; `. `authors` is empty for the 17 anonymous works.
- `fetched_at` is when the work’s page was saved (UTC).
- 5 chapters have empty text (image-only works). 3.06 million words in total, published between 2010 and October 2026. 1650 replies in the comments.

A row in works holds things a work has exactly one of: a title, a word count, a publication date. Chapters and tags are different, because the number of them varies per work.
- Chapters: one work has 1 chapter, another has 33. Putting text in works would need either one giant text column (losing chapter boundaries and titles) or columns chapter_1 … chapter_33, mostly empty. One row per chapter avoids both, and keeps the works table small and fast to browse.
- Tags: a work can have dozens across six types. One row per tag makes questions like “which character appears in the most works” a simple count. With tags crammed into one text column, every such question would mean splitting strings first.

How to build:

```bash
.venv/bin/python -m ao3crawler.export "Macbeth - Shakespeare" macbeth.db
```

How to inspect, for example the number of works per rating:

```bash
sqlite3 -header -column macbeth.db "SELECT rating, COUNT(*) FROM works GROUP BY rating"
```

### How the tables connect

Every table links back to `works` through `work_id`.

| Link                                         | Meaning                                                     | Declared as  |
| -------------------------------------------- | ----------------------------------------------------------- | ------------ |
| `tags.work_id` → `works.work_id`             | which work a tag belongs to                                 | foreign key  |
| `chapters.work_id` → `works.work_id`         | which work a chapter belongs to; `number` gives the order   | foreign key  |
| `comments.work_id` → `works.work_id`         | which work a comment is on                                  | foreign key  |
| `comments.parent_id` → `comments.comment_id` | which comment a reply answers; empty for top-level comments | plain column |

- `comments.parent_id` is deliberately not a foreign key. 18 replies answer a comment that was later deleted; AO3 keeps the deleted comment's id in the thread but not its content, so that parent has no row.

Print the schema with its links:

```bash
sqlite3 macbeth.db ".schema"
```

Join through a link, for example who replied to whom:

```bash
sqlite3 -header -column macbeth.db "SELECT r.author AS replier, p.author AS replied_to FROM comments r JOIN comments p ON p.comment_id = r.parent_id LIMIT 5"
```

### Add a Second Fandom

The same steps work for any fandom. Say Hamlet - Shakespeare (1,373 works). Fetch the works, then the comments:

```bash
no_proxy=archiveofourown.org NO_PROXY=archiveofourown.org AO3_CRAWLER_CONTACT="peichun@alumni.unc.edu" caffeinate -i sh -c '.venv/bin/python -m ao3crawler.works "Hamlet - Shakespeare" && .venv/bin/python -m ao3crawler.comments "Hamlet - Shakespeare"'
```

Then build the database:

```bash
.venv/bin/python -m ao3crawler.export "Hamlet - Shakespeare" hamlet.db
```

`works` collects the IDs and the work pages in one go, unlike what we did for Macbeth, where `listing` was run first.

Note: I started this crawl but did not finish it. AO3 was answering with bursts of HTTP 525 errors and timeouts, and I stopped after 326 of the 1,373 work pages.

## Exploratory Analysis

`analysis.ipynb` reads `macbeth.db` and looks at how the fandom has grown, what is written, how works are received, and how readers and authors talk in the comments. The notebook is saved with its outputs, so it can be read on GitHub without running it.

## Ethics

- robots.txt: `Client` downloads robots.txt when it starts and checks every path against it before requesting. A disallowed path raises PermissionError. The rules for general crawlers disallow `/works?` (the search-style listing) and `/downloads/`, so the crawler uses the fandom's tag listing (`/tags/<fandom>/works`) and ordinary work pages, which are allowed.
- Terms of Service: the ToS does not allow scraping to commercialise content, disrupting the site, or forging identifiers. The data here is for academic use only.
- Load: one request at a time, 5 seconds apart (DELAY = 5). Retries wait longer than normal requests, from 30 up to 480 seconds. Every page is saved and never requested twice. The whole Macbeth sample took 1,082 requests: 30 listing pages, 593 works and 459 comment pages. It takes around overnight.
- Identification: the User-Agent names the crawler and gives a contact email. It does not pretend to be a browser, and it does not log in.
- Adult works: included on purpose, because leaving them out would bias the sample (12% of the works are Mature and 5% Explicit). The crawler adds `view_adult=true`, the same address AO3's own "Proceed" button leads to.
