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

The assignment says under 10,000 works. Some famous ones are too large (Harry Potter has 615,362, Marvel 702,844, Genshin Impact 255,284). Mid-sized ones fit well. For example, Hamlet - Shakespeare has 1375. Operation Mincemeat - SpitLip has 859. Hadestown has 1925.
