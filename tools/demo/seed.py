import sys, time
import httpx
D = sys.argv[1]
B = "http://localhost:8000/api/v1"
c = httpx.Client(base_url=B, timeout=60)
c.post("/auth/otp/request", json={"identifier": "9876543210"}).raise_for_status()
r = c.post("/auth/otp/verify", json={"identifier": "9876543210", "code": "246810", "consent": True}).json()
c.headers["Authorization"] = "Bearer " + r["access_token"]
c.patch("/me", json={"full_name": "Asha Rao", "city": "Bengaluru", "state": "Karnataka", "date_of_birth": "1990-06-14"})
fam = {}
for rel, name, dob in [("self", "Asha Rao", "1990-06-14"), ("spouse", "Ravi Rao", "1988-02-03"),
                       ("child", "Meera Rao", "2019-08-21"), ("parent", "Lakshmi Iyer", "1958-11-30")]:
    fam[name] = c.post("/me/family", json={"relation": rel, "full_name": name, "date_of_birth": dob}).json()["id"]

def upload(name):
    with open(f"{D}/{name}.pdf", "rb") as f:
        doc = c.post("/documents", files={"file": (f"{name}.pdf", f.read(), "application/pdf")}).json()
    for _ in range(20):
        doc = c.get(f"/documents/{doc['id']}").json()
        if doc["status"] in ("extracted", "failed"):
            return doc
        time.sleep(0.3)

h = upload("health")
c.post(f"/policies/{h['policy_id']}/confirm", json={"member_ids": [fam["Asha Rao"], fam["Ravi Rao"], fam["Meera Rao"]]}).raise_for_status()
m = upload("motor")
c.post(f"/policies/{m['policy_id']}/confirm", json={"plan_name": "Private Car Package", "payment_frequency": "annual"}).raise_for_status()
l = upload("life")
c.post(f"/policies/{l['policy_id']}/confirm", json={"plan_name": "Click 2 Protect Super", "member_ids": [fam["Asha Rao"]]}).raise_for_status()
# Employer group health cover (entered manually) — gives two health policies to compare.
c.post("/policies", json={
    "policy_type": "health", "insurer": "Care Health", "plan_name": "Employer Group Health",
    "sum_insured": "300000", "premium": "0", "payment_frequency": "annual",
    "start_date": "2026-04-01", "end_date": "2027-03-31",
    "member_ids": [fam["Asha Rao"], fam["Ravi Rao"]],
    "details": {"room_rent_limit": "Room rent up to Rs. 3,000 per day.",
                "co_payment": "No co-payment.", "maternity": "Maternity covered up to Rs. 50,000 from day one.",
                "opd": "OPD consultations are not covered.", "restoration": "Restoration is not available."},
}).raise_for_status()
p = upload("parents")  # left unverified -> "Review needed"
for q in ["What is the room rent limit?", "Is maternity covered?", "Is dental treatment covered?"]:
    c.post(f"/policies/{h['policy_id']}/ask", json={"question": q}).raise_for_status()
# One question asked in Hindi, answered in Hindi.
c.patch("/me", json={"preferred_language": "hi"}).raise_for_status()
c.post(f"/policies/{h['policy_id']}/ask", json={"question": "क्या एम्बुलेंस का खर्च कवर है?"}).raise_for_status()
c.patch("/me", json={"preferred_language": "en"}).raise_for_status()
# Nominees on the life policy: spouse 60%, minor child 40% with appointee.
nominees = f"/policies/{l['policy_id']}/nominees"
c.post(nominees, json={"full_name": "Ravi Rao", "relation": "spouse", "share_percent": 60,
                       "family_member_id": fam["Ravi Rao"], "date_of_birth": "1988-02-03",
                       "phone": "+919845012345"}).raise_for_status()
c.post(nominees, json={"full_name": "Meera Rao", "relation": "child", "share_percent": 40,
                       "family_member_id": fam["Meera Rao"], "date_of_birth": "2019-08-21",
                       "appointee_name": "Ravi Rao"}).raise_for_status()
employer = next(x for x in c.get("/policies").json() if x["insurer"] == "Care Health")
print("employer", employer["id"])
print("health", h["policy_id"]); print("motor", m["policy_id"]); print("life", l["policy_id"]); print("parents", p["policy_id"])
for pid in [h["policy_id"], m["policy_id"], l["policy_id"]]:
    print(c.get(f"/policies/{pid}").json()["status"])
