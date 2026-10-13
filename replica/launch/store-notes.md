# Store submission notes: CapitUp (Google Play first)

Listing text: `listing.json` (passes `listing.py`: 0 errors, 0 warnings). App icon: `tools/brand/play-store-icon-512.png`.

## Before you submit (owner)

- **Privacy policy URL**: `https://api.YOURDOMAIN/privacy` (served by the backend; fill the [brackets] first).
- **Support email**: a real inbox, also passed to the app build as `SUPPORT_EMAIL`.
- **App category**: Finance. **Tags**: insurance, personal finance.
- **Content rating** (IARC questionnaire): no violence, no user-to-user chat, no gambling (coins have no cash value and cannot be bought) → expected rating: Everyone / 3+.
- **Target audience**: 18+ (the app handles financial documents).
- **Ads**: none.

## Screenshots (Play: phone, 2–8 images, 16:9 or 9:16, min 320 px, max 3840 px)

Use the real app on your phone with demo data (seed script) and capture, in this order, leading with what CapitUp does differently:
1. Coverage report: "Will a delivery bill be paid?"
2. Policy details check screen (fields to confirm)
3. Ask AI answer with its source clause
4. Home with renewal card
5. Emergency card
6. Portfolio

`docs/screenshots/v2/` has web-preview captures you can use as a reference, not as the store images.

## Data safety form (Play Console > App content > Data safety)

Answers for the app as built. Re-check if you add analytics or ads.

| Data type (Play's names) | Collected | Shared | Why | Optional |
|---|---|---|---|---|
| Personal info: Phone number | Yes | No | Account management (sign-in) | No |
| Personal info: Name | Yes | No | App functionality | Yes |
| Personal info: Other info (date of birth, city) | Yes | No | App functionality | Yes |
| Financial info: Other financial info (policies, premium, cover) | Yes | No | App functionality | No |
| Health info (health policy details, family members covered) | Yes | No | App functionality | No |
| Files and docs (uploaded policies) | Yes | No | App functionality | No |
| App activity: Other user-generated content (questions asked) | Yes | No | App functionality | Yes |
| App info and performance: Crash logs, Diagnostics | Yes (crash type and stack trace, numbers and emails masked) | No | Analytics (stability) | No |
| Device or other IDs (push token) | Yes, if notifications allowed | No | App functionality | Yes |

- Processors acting for you (Google Gemini, host, storage, SMS, Firebase) count as **service providers**, not "sharing", under Play's definitions.
- **Encrypted in transit**: Yes (HTTPS only; a production build refuses http://).
- **Users can request deletion**: Yes, in the app (Profile > Privacy > Delete account) and by email.

## Review access (Play: App access > All or some functionality is restricted)

Set on the production backend, for the review account only:
`REVIEW_LOGIN_IDENTIFIER=+91XXXXXXXXXX` and `REVIEW_LOGIN_CODE=XXXXXX` (a number you own that is never used for a real person).

Instructions to paste for the reviewer:
> Sign in with mobile number XXXXXXXXXX. The one-time code is XXXXXX (fixed for this review account).
> The account has sample policies. Tap "See your coverage report" on Home, or any policy, then "Ask AI".

Seed that account with the sample PDFs (`tools/demo/make_pdfs.py`, `tools/demo/seed.py`), never real documents.

## Financial-services declaration

Play asks finance apps to declare what they do. CapitUp: **none of** personal loans, banking, crypto, insurance sales or advice. It is a document organiser. Keep the "What CapitUp is not" paragraph in the description; it is also the answer if review asks about IRDAI registration.
