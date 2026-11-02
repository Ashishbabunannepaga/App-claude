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

## Optional: AI step for unclear files

The keyword rules usually sort most files. For the rest (scanned PDFs, `document1.pdf`, vague subjects), an AI model can read a short excerpt and decide. The tool works with an **OpenAI** key (the default) or an **Anthropic (Claude)** key.

**What gets sent:** the file name, the email subject, the sender's company domain, the start of the email, and the first ~2,500 characters of the document's text. PAN numbers, Aadhaar numbers, mobile numbers and email names are **masked before sending**. KYC files and files the rules were sure about are **never sent**. Get your boss's OK on this, because claim documents can contain health information.

**To switch it on:**

1. Open **`api-key.txt`** in this folder (`1-setup.bat` creates it) and paste your key on its own line under the `#` lines. Save. Keep this file private: don't email it or copy it to the shared drive.
2. Open **`config.yaml`** and, near the bottom under `ai:`, change `enabled: false` to **`enabled: true`**.
3. Run **`2-trial-run.bat`**. The output shows `AI step: checking N files...` and then how many it moved.
4. Check the cost on your OpenAI usage page before starting the full run.

| `config.yaml` setting | What it does |
|---|---|
| `provider: openai` | Use `anthropic` instead if you have a Claude key; the key still goes in `api-key.txt`. |
| `model: gpt-4o-mini` | A cheap, fast OpenAI model that is fine for sorting. If OpenAI says the model isn't found, put in any chat model your account lists. |
| `workers: 4` | Parallel requests. Lower it to 1–2 if you see "rate limit" errors. |

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
python -m mailsorter demo     # then: --demo classify / organize / report
python -m pytest tests        # 23 tests, run on any OS (Outlook step excluded)
```

| Module | Job |
|---|---|
| `outlook.py` | Reads Outlook through COM (`pywin32`), read-only. Walks every store and folder, keeps emails that have attachments (newest first). Skips inline signature pictures, hidden attachments and `.ics`/`.p7s` files. |
| `store.py` | SHA-256 de-duplication into `store_dir/ab/<hash>.<ext>` |
| `db.py` | SQLite tables `messages`, `files` and `attachments`. This is what makes the tool resumable. |
| `classify.py` | Keyword scoring: file name ×3, subject ×2, document text ×1, newest part of the body ×1. Plus `requires`/`ignore` rules per category, and client / insurer / policy-number extraction. |
| `ai.py` | Optional AI pass (OpenAI or Claude, structured JSON output) for files the rules weren't sure about. Masks personal data before sending. Key from env var or `api-key.txt`. |
| `organize.py` | Builds the folder layout. Handles Windows-safe names, the 250-character path limit, name collisions, and re-filing after corrections. |
| `report.py` | Write-only openpyxl Excel (handles 100k+ rows) with a category dropdown, plus `import-review` |
| `dashboard.html` | Self-contained offline dashboard (no internet needed). Data is embedded by `report.py`. |
