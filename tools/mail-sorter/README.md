# Mail Sorter: Outlook attachments, sorted for an insurance broker

This tool reads every email attachment in desktop Outlook, including old archive `.pst` files. It sorts each attachment into a category, identifies the **client, insurer and policy number** where it can, and files everything on the shared drive like this:

```
\\SERVER\Shared\Mail Attachments\
├── Dashboard.html               ← double-click: search, filter, click to open any file
├── Attachments Index.xlsx       ← one row per file, filterable, with "Open" links
├── Claims\
│   └── FY2025-26\
│       └── Sunrise Pharma\
│           └── 2025-06-14_Tata AIG_Claim_form_Priya.pdf
├── Endorsement Addition\ ...
├── Endorsement Deletion\ ...
├── Endorsement Other\ ...
├── Quotes\  Renewals\  Policy Copies\  Booking\  KYC\  Invoices & CD\
└── Other - Needs Review\        ← files nothing matched, for a human to check
```

### What it does NOT do

- It **never moves, deletes, changes or marks as read** any email. It only reads them.
- Nothing is uploaded anywhere, **unless** you switch on the optional AI step (see the [AI step](#optional-ai-step-for-unclear-files) section below).
- Each document is stored once. The same file attached in 20 reply emails is saved a single time, and the index shows how many times it was received.

---

## What you need

| | |
|---|---|
| Windows PC | The PC where the boss's Outlook is set up, or any PC signed in to the same mailbox |
| **Classic** desktop Outlook | Outlook 2016/2019/2021 or Microsoft 365 "classic". The **"New Outlook"** toggle must be **OFF**, because New Outlook cannot be read by programs. |
| Python 3.12 | Free download from <https://www.python.org/downloads/>. During install, **tick "Add python.exe to PATH"**. |
| Disk space | A local folder with free space roughly equal to the attachments in the mailbox (usually 40–70% of the 150 GB after duplicates are removed). An external USB disk is fine. |
| The shared drive | A folder everyone who needs the files can open |

## Setup (one time, about 10 minutes)

1. Copy the whole `mail-sorter` folder to the PC, for example `C:\MailSorter\`.
2. Double-click **`1-setup.bat`**. It installs everything into a private folder and doesn't change anything else on the PC.
3. Open **`config.yaml`** in Notepad and change the three paths at the top:
   - `work_dir`: a local folder for the database, e.g. `C:\MailSorter\work`
   - `store_dir`: where attachments are saved before sorting (needs the disk space)
   - `output_dir`: the shared drive folder. Use the full network path (`\\SERVER\Shared\Mail Attachments`) rather than `S:\`, so the links work on everyone's PC.
4. **Optional but recommended:** add your top 20–50 clients under `clients:` in `config.yaml`. Without this list, the client name is guessed from the sender's email domain (e.g. `sunrisepharma.com` becomes "Sunrisepharma"). With it, you get the proper name ("Sunrise Pharma Ltd").
5. **Open any old archive PSTs in Outlook** (File → Open & Export → Open Outlook Data File) so the tool sees them too.

Want to see it first? Double-click **`try-demo.bat`**. It builds a fake mailbox in a separate `demo` folder, so nothing real is touched, and opens the dashboard.

## Step 1: Trial run (last 30 days)

1. Make sure Outlook is open.
2. Double-click **`2-trial-run.bat`**.
3. Open `Dashboard.html` and `Attachments Index.xlsx` in the output folder, and show your boss.
4. If some kinds of files land in the wrong place, add words to that category's `keywords:` in `config.yaml`. Then run **`2-trial-run.bat`** again; it re-sorts automatically.

## Step 2: Full run (the whole 150 GB)

Double-click **`3-full-run.bat`**.

- **It will take many hours**, often overnight or across a weekend for 150 GB. Set the PC to never sleep while it runs (Settings → System → Power).
- **You can stop it at any time** by closing the window. Running it again **continues where it stopped**, and emails already read are skipped.
- Progress is printed every 500 emails. Emails that Outlook couldn't open are listed in `work_dir\extract-errors.log`.

## Step 3: Fix wrong categories

1. Open `Attachments Index.xlsx`. The **"Needs Review"** sheet lists the files the tool was unsure about.
2. Change the **Category** column using the dropdown. You can also fix any row on the "Index" sheet.
3. Save and close Excel, then double-click **`4-apply-corrections.bat`**. The files move to their new folders, and your corrections are never overwritten.

## Keeping it up to date

**`5-update-new-mail.bat`** picks up attachments from the last 14 days. Schedule it weekly in **Windows Task Scheduler**:

1. Create Basic Task → Weekly → Start a program → choose `5-update-new-mail.bat`.
2. Choose "Run only when user is logged on", because Outlook must be open.

## Optional: AI step (reads every email in full)

Keyword rules sort most files for free. With the AI step on, an AI model **reads each email as a whole**:

- **Headers:** date, folder, subject, From, **To**, **CC**.
- **Forwards:** whether the email is a **forward**, and the original sender, date, To and CC of every forwarded or quoted message underneath. So "boss forwards the client's mail to the insurer" is filed under the right client.
- **Body:** the newest message, plus the forwarded content, which is usually the real request.
- **Attachments:** every attachment's name, type and opening text, plus what the keyword rules guessed.

It then decides a category for **each attachment separately** (one email can carry a claim form *and* a KYC document). It also fills in the client, insurer and policy number, and writes a one-line summary of the email. The summary, To, CC and "Forwarded from" columns appear in the Excel file and the dashboard.

**Nothing is wasted:**

- **One request per email** covers all of its attachments.
- **Each email is read by the AI only once.** Re-runs, resumed runs and corrections cost nothing extra.
- **A file attached in 20 emails** is judged once, in the first email it arrived in.
- **Long email threads are trimmed** to the parts that matter: the newest message and the forwarded content first, older replies after.

**What gets sent:** the text described above, with PAN, GSTIN, Aadhaar and mobile numbers and the name part of email addresses **masked** first. The company domains (`@tataaig.com`) are kept, because they identify insurers and clients. The text of KYC documents is **never sent**. Get your boss's OK on this, because claim documents can contain health information.

### What it costs

Before spending anything, run **`estimate.bat`**. It counts exactly what would be sent for the emails read so far and prints the cost in dollars and rupees. Nothing is sent to OpenAI while it does this.

**Free and recommended order:**

1. Run `2-trial-run.bat` or `3-full-run.bat` with AI **off**. Reading Outlook and the keyword sorting are free.
2. Run **`estimate.bat`** to see the real cost for **your** mailbox.
3. Switch AI on (below) and run `3-full-run.bat` again. It skips everything already done and only does the AI step.

**Rough guide** for `gpt-4o-mini`, at the prices in `config.yaml` (check <https://openai.com/api/pricing>):

| | per email | 100,000 emails |
|---|---|---|
| One by one | ≈ $0.0005 (≈ 4 paise) | ≈ $50 (≈ Rs 4,250) |
| **Batch (half price)** | ≈ $0.00025 | **≈ $25 (≈ Rs 2,100)** |
| `scope: unsure` (only unclear files) | | usually 5–10× less |
| `provider: local` (Ollama on the PC) | free | free, but takes days on a laptop |

A safety limit, **`max_cost_usd: 25`**, stops the AI step from starting if the estimate is higher. Raise it when you're happy with the estimate.

### Switching it on

1. Open **`api-key.txt`** in this folder (`1-setup.bat` creates it) and paste your OpenAI key on its own line under the `#` lines. Save. Keep this file private: don't email it or copy it to the shared drive.
2. Open **`config.yaml`** and, under `ai:`, change `enabled: false` to **`enabled: true`**.
3. Run `estimate.bat`, check the cost, and if needed raise `max_cost_usd`.
4. Run `2-trial-run.bat` or `3-full-run.bat`. The window shows `AI step: reading N emails...`.

| `config.yaml` → `ai:` | What it does |
|---|---|
| `scope: all` | The AI reads **every** email that has attachments. Most accurate. `unsure` reads only the emails the keyword rules weren't sure about, which is cheaper. |
| `batch: auto` | For 1,000+ emails, the OpenAI **Batch API** is used at **half price**. Results come back within 24 hours, usually a few. The window waits and shows progress. **You can close it**; running `3-full-run.bat` again collects the results. `never` = always one by one. |
| `max_cost_usd: 25` | The safety limit described above. |
| `model: gpt-4o-mini` | Cheap and accurate for this job. If OpenAI says the model isn't found, put in any chat model your account lists, and update the two `price_...` lines to match it. |
| `workers: 8` | Emails read at the same time (one-by-one mode). Lower it to 2–4 if you see "rate limit" errors. |
| `provider: local` | A **free** model on this PC instead of OpenAI. Install Ollama from <https://ollama.com>, run `ollama pull qwen2.5:7b`, then set `provider: local` and `model: qwen2.5:7b`. It's slow on a laptop (several seconds per email) and somewhat less accurate than OpenAI. |
| `provider: anthropic` | Use a Claude key instead; it also goes in `api-key.txt`. |

The key can also come from the `OPENAI_API_KEY` (or `ANTHROPIC_API_KEY`) Windows environment variable, which takes priority over the file.

## Troubleshooting

| Problem | Fix |
|---|---|
| `This step needs Windows with Outlook and the 'pywin32' package` | Run `1-setup.bat`, and run the `.bat` files by double-clicking, not from another folder. |
| Outlook shows *"A program is trying to access e-mail address information"* | Outlook does this when it thinks the antivirus is out of date. Update the antivirus, or have IT allow programmatic access: File → Options → Trust Center → Trust Center Settings → Programmatic Access. |
| `Operation unavailable` / class not registered | Outlook isn't classic Outlook, or the `.bat` was run "as administrator" while Outlook runs as the normal user. Run both as the same normal user. |
| An archive PST isn't included | Open it in Outlook first (see Setup step 5), then run again. |
| `Could not write Attachments Index.xlsx` | The file is open in Excel. Close it and run again. |
| Disk full | Set `store_dir` to a bigger disk. Already-saved files are kept, so just run again. |
| A folder should be skipped | Add its name to `skip_folders` in `config.yaml`. |
| Want folders by client first | In `config.yaml` set `layout: '{client}/{category}/{fy}'`, then run `4-apply-corrections.bat`; files are re-filed. |

## For the developer

```
python -m mailsorter extract  [--days 30 | --since YYYY-MM-DD] [--until YYYY-MM-DD] [--limit N]
python -m mailsorter classify [--ai] [--redo]
python -m mailsorter organize
python -m mailsorter report
python -m mailsorter all      [extract options] [--ai]
python -m mailsorter import-review [--file path.xlsx]
python -m mailsorter status
python -m mailsorter estimate     # AI cost for the emails read so far (sends nothing)
python -m mailsorter ai           # run / resume only the AI step (e.g. collect a batch)
python -m mailsorter demo     # then: --demo classify / organize / report
python -m pytest tests        # 31 tests, run on any OS (Outlook step excluded)
```

| Module | Job |
|---|---|
| `outlook.py` | Reads Outlook through COM (`pywin32`), read-only. Walks every store and folder, keeps emails that have attachments (newest first). Skips inline signature pictures, hidden attachments and `.ics`/`.p7s` files. |
| `store.py` | SHA-256 de-duplication into `store_dir/ab/<hash>.<ext>` |
| `db.py` | SQLite tables `messages`, `files` and `attachments`. This is what makes the tool resumable. |
| `classify.py` | Keyword scoring: file name ×3, subject ×2, document text ×1, newest part of the body ×1. Plus `requires`/`ignore` rules per category, and client / insurer / policy-number extraction. |
| `parse.py` | Splits a body into the newest message and the forwarded/quoted messages (Gmail, Outlook and "wrote:" formats), each with From/To/CC/Date/Subject |
| `ai.py` | Email-level AI pass: one strict-JSON request per email covering all its attachments. OpenAI live or Batch API, local Ollama, or Anthropic. Cost estimate, budget cap, PII masking, resumable `ai_status`. |
| `organize.py` | Builds the folder layout. Handles Windows-safe names, the 250-character path limit, name collisions, and re-filing after corrections. |
| `report.py` | Write-only openpyxl Excel (handles 100k+ rows) with a category dropdown, plus `import-review` |
| `dashboard.html` | Self-contained offline dashboard (no internet needed). Data is embedded by `report.py`. |
