# Recon map: CoverSure (Android)

Scope: the "understand my cover" loop: home hero → sample (demo) report → coverage checklist by section, plus coins
rewards and the notification soft-ask.
For: CapitUp (capitupindia.com), an organise-and-understand insurance app for Indian families.
Date: 2026-10-06

Method: clean-room, per `.claude/skills/replica-recon`. Sources are the five screenshots the user took of their
own account, plus the public App Store listing. No code, network calls or private APIs of the original were looked
at. The screenshots are reference only and are not committed (`replica/screens/` is git-ignored).

## Sources

| # | source | URL | notes |
| --- | --- | --- | --- |
| 1 | user's own account (5 screenshots) | — (shared in chat, 2026-10-06) | home, notification dialog, demo report health/life/motor, coins wallet |
| 2 | App Store listing | https://apps.apple.com/in/app/coversure-insurance-made-easy/id6454847100 | pitch: portfolio in one place, free policy reviews, covered vs not covered, IRDAI-certified advisors |

## Core loop

Show people, before they upload anything, what a policy "really" covers using a sample report, then get them to add
their own policy for the same view.

## Screens

| ID | screen | how to reach | purpose | key components | states seen |
| --- | --- | --- | --- | --- | --- |
| S01 | Home | tab 1 | hook + CTA | coins chip, logo, avatar, rotating "will your policy survive X?" hero, Add policy +coins, scenario card, "check demo report" button, scrolling ticker, expert-review card | filled, with modal |
| S02 | Notification soft-ask | first home visit | explain before OS prompt | dialog, Deny / Allow | shown |
| S03 | Demo report — health | S01 CTA | show the report format | type pills, scenario carousel 1/5, section tabs, section header + rating badge, check/cross rows with values, add-ons accordion, disclaimer, sticky Add Policy bar | filled |
| S04 | Demo report — life | S03 pill | same, life | same; "Need attention / Considerations / Watch out for" sections | filled |
| S05 | Demo report — motor | S03 pill | same, motor | rows with long descriptions instead of short values | filled |
| S06 | Coins wallet | coins chip | rewards | Earn/Use toggle, balance, coin→₹ rate, not-enough banner, wellness plan card, gift-card brand grid, Redeem | empty balance |

## Flows

```
F01 New user understands what a report shows
    S01 -> S03 (-> S04/S05) -> Add policy
    happy path clicks: 2
    edge: no policies yet; unsupported policy type
F02 User checks coins
    S01 -> S06 (Earn | Use)
    happy path clicks: 1
F03 Push permission
    S01 load -> S02 -> OS prompt
```

## Components

| component | variants | states | used on |
| --- | --- | --- | --- |
| Pill selector | type (Health/Life/Motor) | selected, idle | S03–S05 |
| Scenario card | per scenario | carousel index | S01, S03–S05 |
| Section header | with rating badge (good/bad gauge) | — | S03–S05 |
| Checklist row | covered, not covered, value text | — | S03–S05 |
| Coin chip | balance, +N reward | — | S01, S06 |
| Sticky CTA bar | — | — | S03–S05 |
| Ticker strip | — | animating | S01 |

## Inferred data model

```
CoverageReport  policy_type, rating, scenarios[], sections[{title, subtitle, rating, rows[{label, covered, value}]}]
                evidence: S03–S05. confidence: high (shape), guess (how rows are derived)
RewardLedger    user, balance, earn events, redeemable items
                evidence: S01 "+50" on Add policy, S06 balance. confidence: medium
```

## Feature matrix

See `features.csv`.

## Out of scope (cannot or should not be cloned)

- Their brand, logo, illustrations, copy and colour/layout trade dress. We used our own (CapitUp wordmark,
  icon-drawn art, our own wording).
- "Buy" tab: selling or recommending products needs an IRDAI licence (broker / corporate agent / web aggregator).
- Gift cards from named brands (Amazon, Netflix…): needs partner deals; brand logos are trademarks.
- "1 coin = ₹1": giving coins a rupee value turns them into a cash-like rebate; coins tied to buying insurance
  are restricted by Section 41 of the Insurance Act. Ours have no cash value and are earned only for organising.
- IRDAI-certified advisor network: people, not code. We provide the request flow (support category `expert_review`).

## Size

Screens 6, flows 3, entities 2. Hard parts: deriving rows from real policy wording (done rule-based, with page
references), honest "not found" handling. Size: M.
