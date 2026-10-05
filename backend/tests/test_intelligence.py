from datetime import date, timedelta

from tests.conftest import make_pdf


def _upload_confirm(client, auth, pages=None) -> dict:
    pdf = make_pdf(pages) if pages else make_pdf()
    doc = client.post("/api/v1/documents", files={"file": ("p.pdf", pdf, "application/pdf")}, headers=auth).json()
    doc = client.get(f"/api/v1/documents/{doc['id']}", headers=auth).json()
    r = client.post(f"/api/v1/policies/{doc['policy_id']}/confirm", json={}, headers=auth)
    assert r.status_code == 200, r.text
    return r.json()


def _manual(client, auth, **fields) -> dict:
    body = {
        "policy_type": "health",
        "insurer": "Niva Bupa",
        "end_date": str(date.today() + timedelta(days=200)),
        "start_date": str(date.today() - timedelta(days=165)),
        **fields,
    }
    r = client.post("/api/v1/policies", json=body, headers=auth)
    assert r.status_code == 201, r.text
    return r.json()


def test_nominees_crud_and_share_validation(client, login):
    auth = login("9876543210")["headers"]
    other = login("9123456780")["headers"]
    life = _manual(client, auth, policy_type="life", insurer="LIC", sum_insured="5000000")
    url = f"/api/v1/policies/{life['id']}/nominees"

    r = client.post(url, json={"full_name": "Ravi Rao", "relation": "spouse", "share_percent": 60}, headers=auth)
    assert r.status_code == 201
    ravi = r.json()
    minor = {
        "full_name": "Meera Rao",
        "relation": "child",
        "share_percent": 50,
        "date_of_birth": "2019-08-21",
        "appointee_name": "Ravi Rao",
    }
    r = client.post(url, json=minor, headers=auth)
    assert r.status_code == 422 and "40%" in r.json()["error"]["message"]
    minor["share_percent"] = 40
    assert client.post(url, json=minor, headers=auth).status_code == 201

    policy = client.get(f"/api/v1/policies/{life['id']}", headers=auth).json()
    assert sum(n["share_percent"] for n in policy["nominees"]) == 100

    # Editing within the 100% budget, isolation, delete.
    r = client.put(f"{url}/{ravi['id']}", json={**ravi, "share_percent": 50}, headers=auth)
    assert r.status_code == 200 and r.json()["share_percent"] == 50
    assert client.get(url, headers=other).status_code == 404
    foreign = client.post("/api/v1/me/family", json={"relation": "self", "full_name": "Bob"}, headers=other).json()
    r = client.post(
        url,
        json={"full_name": "Bob", "relation": "other", "share_percent": 10, "family_member_id": foreign["id"]},
        headers=auth,
    )
    assert r.status_code == 422
    assert client.delete(f"{url}/{ravi['id']}", headers=auth).status_code == 204
    assert len(client.get(url, headers=auth).json()) == 1


def test_clauses_extracted_and_filterable(client, auth):
    policy = _upload_confirm(client, auth)
    clauses = client.get(f"/api/v1/policies/{policy['id']}/clauses", headers=auth).json()
    types = {c["clause_type"] for c in clauses}
    assert {"exclusion", "waiting_period", "limit"} <= types
    exclusions = client.get(f"/api/v1/policies/{policy['id']}/clauses?type=exclusion", headers=auth).json()
    assert exclusions and all("exclusion" in c["tags"] for c in exclusions)
    assert any("Cosmetic surgery" in c["text"] and c["page"] == 3 for c in exclusions)
    assert all(c["section"] for c in exclusions)
    assert client.get(f"/api/v1/policies/{policy['id']}/clauses?type=nonsense", headers=auth).status_code == 422


def test_answers_include_related_clauses(client, auth):
    policy = _upload_confirm(client, auth)
    a = client.post(
        f"/api/v1/policies/{policy['id']}/ask", json={"question": "Is maternity covered?"}, headers=auth
    ).json()
    assert a["answerable"]
    assert a["related_clauses"] and "Maternity" in a["related_clauses"][0]["text"]
    assert a["related_clauses"][0]["type"] == "waiting_period"


def test_hindi_summary_and_answers(client, auth):
    policy = _upload_confirm(client, auth)
    en = client.get(f"/api/v1/policies/{policy['id']}/summary", headers=auth).json()
    assert (
        client.patch("/api/v1/me", json={"preferred_language": "hi"}, headers=auth).json()["preferred_language"] == "hi"
    )
    hi = client.get(f"/api/v1/policies/{policy['id']}/summary", headers=auth).json()
    assert hi["headline"] != en["headline"] and "पॉलिसी" in hi["headline"]
    assert "सलाह" in hi["disclaimer"]

    a = client.post(f"/api/v1/policies/{policy['id']}/ask", json={"question": "क्या मातृत्व कवर है?"}, headers=auth).json()
    assert a["answerable"] and "Maternity" in a["answer"] and "दस्तावेज़" in a["answer"]
    assert a["citations"][0]["page"] == 2
    assert "सलाह" in a["disclaimer"]
    # Switching back serves the cached English summary.
    client.patch("/api/v1/me", json={"preferred_language": "en"}, headers=auth)
    assert client.get(f"/api/v1/policies/{policy['id']}/summary", headers=auth).json() == en
    assert client.patch("/api/v1/me", json={"preferred_language": "fr"}, headers=auth).status_code == 422


def test_insights_detect_gaps(client, auth):
    data = client.get("/api/v1/portfolio/insights", headers=auth).json()
    assert [i["id"] for i in data["insights"]] == ["gap:no-health"]
    assert "not a recommendation" in data["disclaimer"]

    for rel, name in [("self", "Asha"), ("spouse", "Ravi"), ("parent", "Lakshmi")]:
        client.post("/api/v1/me/family", json={"relation": rel, "full_name": name}, headers=auth)
    family = {m["full_name"]: m["id"] for m in client.get("/api/v1/me/family", headers=auth).json()}
    _manual(client, auth, sum_insured="500000", member_ids=[family["Asha"], family["Ravi"]])
    life = _manual(client, auth, policy_type="life", insurer="LIC", sum_insured="5000000")
    _manual(client, auth, policy_type="motor", insurer="Acko", end_date=str(date.today() + timedelta(days=12)))

    ids = {i["id"]: i for i in client.get("/api/v1/portfolio/insights", headers=auth).json()["insights"]}
    assert "gap:no-health" not in ids and "gap:no-life" not in ids
    assert "gap:low-health-cover" in ids and "₹5 lakh" in ids["gap:low-health-cover"]["title"]
    assert "Lakshmi" in ids["gap:uncovered-members"]["detail"]
    assert ids[f"nominee:{life['id']}"]["severity"] == "high"
    renewal = [i for i in ids.values() if i["category"] == "renewal"]
    assert renewal and "12 days" in renewal[0]["title"]
    severities = [i["severity"] for i in client.get("/api/v1/portfolio/insights", headers=auth).json()["insights"]]
    assert severities == sorted(severities, key=["high", "medium", "info"].index)


def test_compare_own_policies(client, login):
    auth = login("9876543210")["headers"]
    a = _upload_confirm(client, auth)
    b = _manual(
        client,
        auth,
        insurer="HDFC ERGO",
        sum_insured="500000",
        premium="41200",
        payment_frequency="annual",
        details={
            "co_payment": "Co-payment: 20% co-payment applies on every claim.",
            "room_rent_limit": "No room rent limit.",
        },
    )
    r = client.get(f"/api/v1/policies/compare?ids={a['id']}&ids={b['id']}", headers=auth)
    assert r.status_code == 200, r.text
    rows = {row["label"]: row for row in r.json()["rows"]}
    assert rows["Sum insured"]["values"] == ["₹10,00,000", "₹5,00,000"] and rows["Sum insured"]["best_index"] == 0
    assert rows["Annual premium"]["best_index"] == 0
    assert rows["Room rent"]["values"][1].startswith("✓")
    assert rows["Co-payment"]["values"][1].startswith("⚠")

    motor = _manual(client, auth, policy_type="motor", insurer="Acko")
    assert client.get(f"/api/v1/policies/compare?ids={a['id']}&ids={motor['id']}", headers=auth).status_code == 422
    assert client.get(f"/api/v1/policies/compare?ids={a['id']}", headers=auth).status_code == 422
    other = login("9123456780")["headers"]
    assert client.get(f"/api/v1/policies/compare?ids={a['id']}&ids={b['id']}", headers=other).status_code == 404
