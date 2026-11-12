# Accuracy testing: is the AI reading policies correctly?

Before launch, and before any change to prompts, the AI provider or the model, run real policies through the app's
reading pipeline and compare every field with the right answer. One checked policy found 3 mistakes; a set of
20–30 tells us how good the app really is and catches regressions.

## 1. Build the test set (once, then keep adding)

1. Make a folder **outside the repo**, e.g. `C:\Users\<you>\capitup-accuracy\`. These are real people's policies:
   never commit them, upload them anywhere else or share them in chats. Use team members' own and family policies,
   with their permission.
2. Aim for 20–30 documents, roughly:

   | Kind | How many | Why |
   |---|---|---|
   | Retail health (Star, HDFC ERGO, Niva Bupa, Care, ICICI Lombard …) | 6–8 | Most common upload |
   | Group health / GMC (employee e-card + schedule) | 4–6 | CapitUp's core business; long documents |
   | Motor (car, two-wheeler; different insurers) | 5–6 | Add-on names differ by insurer |
   | Term / life | 4–5 | Sum assured, riders, premium term |
   | Scanned PDF or phone photo | 3–4 | Tests OCR |
   | Not a policy (bank statement, invoice) | 1–2 | Must be rejected |

3. Create the answer sheet:
   ```
   cd $HOME\Documents\capitup-app\backend
   .venv\Scripts\python -m app.scripts.eval_extraction C:\Users\<you>\capitup-accuracy --template
   ```
   This writes `answers.csv` with one row per file. Open it in Excel and fill in the **correct values from each
   document**, by reading the document yourself:

   | Column | Write | Example |
   |---|---|---|
   | `policy_type` | health / motor / life / other | `motor` |
   | `insurer` | the insurer's name | `TATA AIG` |
   | `plan_name` | product name | `Auto Secure - Private Car Package Policy` |
   | `policy_number` | as printed (spaces/dashes don't matter) | `6203516874 02 00` |
   | `start_date`, `end_date` | DD/MM/YYYY | `04/10/2026` |
   | `premium` | total incl. GST | `13152` |
   | `sum_insured` | health: base SI · motor: IDV · life: sum assured | `426164` or `5 lakh` |
   | `payment_frequency` | annual / half_yearly / quarterly / monthly / single | `annual` |
   | any detail column | e.g. `registration_number`, `ncb_percentage`, `room_rent` | `TS 08 HV 9458` |

   - Leave a cell **blank** to skip it. Write **`-`** when the field must come out **empty**
     (e.g. `ncb_percentage` = `-` when NCB claimed is NA).
   - For a non-policy file, write `not_insurance` in `policy_type` and leave the rest blank.

## 2. Run it

Uses the AI provider in `backend\.env` (OpenAI today), so it costs tokens: roughly one extraction call per document.

```
.venv\Scripts\python -m app.scripts.eval_extraction C:\Users\<you>\capitup-accuracy
```

Options: `--only health` runs one policy type; `--min-accuracy 0.95` exits with an error below 95% (useful
before merging a prompt change).

It prints each document's wrong fields and the AI's confidence for them, then accuracy by field and overall, and
saves `results-<date>.csv` in the same folder.

## 3. Use the results

- **Wrong field with high AI confidence** is the dangerous kind: the app won't highlight it in amber. Fix these first.
- Paste the report (not the documents) to whoever is fixing extraction. Every fix gets a backend test
  with a made-up document that reproduces the problem, like `tests/test_processing.py`.
- **Re-run the whole set after every prompt, provider or model change** and compare with the last results file.
- Target before launch: **≥ 95% of core fields right** and **no wrong field with confidence ≥ 0.9**.
