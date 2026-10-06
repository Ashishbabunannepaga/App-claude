# Fixes and positioning (replica-entrepreneur)

## Review sample: 0. Not collected yet

The skill needs real, linked user reviews and forbids invented ones. Apple's official public reviews feed
(`https://itunes.apple.com/in/rss/customerreviews/id=6454847100/sortBy=mostRecent/json`) was blocked by this cloud
environment's network policy, so no reviews were read and **no complaint themes are claimed here**.

To run it yourself, on any machine with internet:

```bash
curl -s "https://itunes.apple.com/in/rss/customerreviews/page=1/id=6454847100/sortby=mostrecent/json" > p1.json
# copy rows into replica/reviews.csv (source,url,date,rating,text), then:
python3 .claude/skills/replica-entrepreneur/reviews.py replica/reviews.csv --out replica/feedback.md
```

Google Play reviews: read them in the browser and copy rows by hand (no scraping, per the skill).

## What we changed anyway (product decisions, not review evidence)

| # | change | why |
| - | ------ | --- |
| 1 | Every row says where it came from (page number or "not mentioned") | trust: a checklist without sources can't be checked |
| 2 | Unknown items show "Not found in your document", never "Not covered" | a wrong "not covered" can stop someone from claiming |
| 3 | Tap a row → why it matters + the policy's own words + Ask AI about it | turns a checklist into understanding |
| 4 | No Buy tab, no product ranking | needs an IRDAI licence; also keeps the app neutral |
| 5 | Coins have no cash value and are earned only for organising | avoids rebate/inducement issues (Insurance Act s.41) |

## Positioning options (to validate with real reviews)

1. For families who don't trust insurance apps that also sell, CapitUp explains your own policies and never sells.
2. For people who were surprised at claim time, CapitUp shows exactly what your policy says, page by page.
3. For households juggling many policies, CapitUp is one place with reminders, nominees and family cover.

Recommended for now: **1**, because it follows directly from the regulatory choice in #4.
