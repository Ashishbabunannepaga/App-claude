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
p = upload("parents")  # left unverified -> "Review needed"
for q in ["What is the room rent limit?", "Is maternity covered?", "Is dental treatment covered?"]:
    c.post(f"/policies/{h['policy_id']}/ask", json={"question": q}).raise_for_status()
print("health", h["policy_id"]); print("motor", m["policy_id"]); print("life", l["policy_id"]); print("parents", p["policy_id"])
for pid in [h["policy_id"], m["policy_id"], l["policy_id"]]:
    print(c.get(f"/policies/{pid}").json()["status"])
