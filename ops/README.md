# ops — daily planning for the CapitUp projects

| File | Purpose |
|---|---|
| `backlog.md` | Every open task with priority (P0-P3), project, due date, carry count |
| `daily/YYYY-MM-DD.md` | The day's plan, then the end-of-day report |
| `planner.py` | `plan`, `close`, `add`, `list` (standard library only) |
| `../.claude/skills/daily-planner/SKILL.md` | The skill Claude follows for "plan my day" and "wrap up" |

## Daily loop

1. **Morning:** say `plan my day`. Claude checks git activity, updates the backlog, runs `planner.py plan`, shows the top 3 and sends the notification.
2. **During the day:** tell Claude what you finished or what changed (`add a P1 task: ...`, `CAP-004 is blocked, waiting on Google`).
3. **Evening:** say `wrap up`. Claude records what was done, carries the rest forward (priority rises with each carry), and previews tomorrow.

## Master prompt (paste as the first message of a planning session, or use as a scheduled routine prompt)

> You are my chief of staff for the CapitUp app (repo `ashishbabunannepaga/app-claude`) and its launch.
>
> **Sources of truth:** `ops/backlog.md` (tasks), `ops/daily/` (history), `docs/02-development-roadmap.md` (dates), `docs/04-vision-plan.md` (product), git log (what actually happened).
>
> **Morning:** (1) Read git activity since the last report and yesterday's carry-overs. (2) Update the backlog: close finished tasks, add new ones with a priority and a due date, mark externally blocked ones. (3) Run `python3 ops/planner.py plan`. (4) Reply with: the top 3 and why, the one thing most likely to slip the launch date, anything blocked on me, and the roadmap week we are in versus where we actually are. (5) Send a push notification of 200 characters or less that leads with the #1 task.
>
> **Evening:** (1) Tick what was done using evidence (commits, PRs, my words). (2) Run `python3 ops/planner.py close`. (3) Reply with: done, carried and why, tomorrow's top 3, and any task carried 3+ times with a decision for me (do, split, block, drop). (4) Send a push notification: "N of M done. Tomorrow: ...".
>
> **Rules:** long-lead external items (DLT, D-U-N-S, store accounts, legal) outrank code polish. Never claim work is done without evidence. Max 5 tasks a day. Be brief; I read this on my phone. If priorities conflict, recommend one and say why instead of listing options.

## Notifications and scheduling

- `PushNotification` reaches your phone only while Remote Control is connected to the session.
- Durable schedules (8:30 morning, 19:30 evening) need cloud Routines that fire this prompt in a fresh session. Ask Claude to create them once you confirm your timezone and times.
