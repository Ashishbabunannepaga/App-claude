---
name: daily-planner
description: Runs the owner's daily workflow for the CapitUp projects: builds a prioritised to-do list each morning from ops/backlog.md and repo state, sends a push notification, and at end of day writes a report of what was done and rolls unfinished work to tomorrow. Use when the user says "plan my day", "morning", "what should I do today", "end of day", "wrap up", "what did we do", "carry over", "add a task", or "reprioritise".
---

# Daily planner

State lives in `ops/`: `backlog.md` (source of truth), `daily/<date>.md` (plan + day report), `planner.py` (ranking and rollover).
Priorities: P0 launch-blocking, P1 important, P2 normal, P3 nice-to-have. Score = priority + due-date pressure + carry-over age.

## Morning ("plan my day")
1. `git log --since="2 days ago" --oneline` and read yesterday's `ops/daily/*.md` report, so the plan reflects reality.
2. Reconcile the backlog: mark tasks already finished in git as `[x]`, add tasks the commits revealed (`python3 ops/planner.py add ...`), mark waiting-on-others tasks `[!]`.
3. `python3 ops/planner.py plan` and read the file. Sanity-check the top 3: is anything urgent but low-scored (e.g. a long-lead item)? Fix the backlog, not the output.
4. Show the plan: top 3 must-do, should-do, blockers. One line on why the #1 is #1.
5. Send the `NOTIFY:` line via PushNotification (status proactive), under 200 characters.

## Evening ("wrap up")
1. Ask nothing unless needed. Infer what was done from `git log --since=midnight` and the conversation; tick the boxes in today's plan and add free-text extras under "Also did today".
2. `python3 ops/planner.py close`. It marks done tasks, adds +1 `carried` to missed ones, and appends the day report and tomorrow's likely top 5.
3. Give the user: done, carried (with a reason if one is known), tomorrow's top 3, and any task carried 3+ times with a question: do it, split it, block it, or drop it.
4. Send the `NOTIFY:` line via PushNotification.

## Rules
- Never invent completed work. Done means evidence: a commit, a merged PR, or the user said so.
- Max 5 planned tasks a day; fewer on days with meetings. Do not pad the list.
- Commit `ops/` changes on the working branch with the code.
- Push notifications only reach the user if Remote Control is connected; otherwise tell the user the notification was not delivered.
