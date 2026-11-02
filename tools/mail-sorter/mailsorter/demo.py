"""Fake mailbox for trying the tool without Outlook (and for the tests).

Creates realistic-looking (but invented) broker emails with PDF, Excel and
Word attachments, then stores them exactly as the Outlook step would.
"""
from __future__ import annotations

import random
from datetime import datetime, timedelta
from pathlib import Path

from . import db
from .config import Config
from .store import add_file, add_message

CLIENTS = [("Sunrise Pharma", "sunrisepharma.com"), ("Kaveri Logistics", "kaverilogistics.in"),
           ("Bluewave Textiles", "bluewavetex.co.in"), ("Orbit Software", "orbitsoft.com"),
           ("Greenfield Foods", "greenfieldfoods.in"), ("Rahul Mehta", "gmail.com")]
INSURERS = [("ICICI Lombard", "icicilombard.com"), ("HDFC ERGO", "hdfcergo.com"),
            ("Tata AIG", "tataaig.com"), ("New India Assurance", "newindia.co.in"),
            ("Star Health", "starhealth.in")]
OWN = "capitupindia.com"

# (subject, file name, document text, who sends: client | insurer | us)
TEMPLATES = [
    ("Addition of members in GMC policy", "Addition_list_{m}.xlsx",
     "Employee code | Name | DOB | Relation | Date of joining - new joinees to be added to group mediclaim", "client"),
    ("Deletion endorsement - employees left", "Deletion_list_{m}.xlsx",
     "Employee code | Name | Date of exit - please delete these members from the policy", "client"),
    ("Endorsement copy - Policy No {pol}", "Endorsement_{pol}.pdf",
     "Endorsement schedule. Policy No {pol}. Correction of insured name as per request.", "insurer"),
    ("Claim intimation - {person} hospitalisation", "Claim_form_{person}.pdf",
     "Claim form Part A. Policy No {pol}. Patient {person}. Hospital bill and discharge summary attached.", "client"),
    ("Settlement letter for claim no CL{n}", "Settlement_letter_CL{n}.pdf",
     "We are pleased to inform that the claim has been settled. Policy No {pol}.", "insurer"),
    ("Quote for Fire & Burglary insurance", "Quotation_{ins_short}.pdf",
     "Quotation. Sum insured 25 Cr. Indicative premium Rs 4,50,000 plus GST. Terms valid 30 days.", "insurer"),
    ("RFQ - Group Health renewal {fy}", "Claims_MIS_and_data.xlsx",
     "Claims experience | Claim ratio 64% | Census data for renewal", "us"),
    ("Renewal notice - Policy No {pol}", "Renewal_notice_{pol}.pdf",
     "Your policy is due for renewal on 31-03. Policy No {pol}. Expiring premium Rs 12,40,000.", "insurer"),
    ("Policy issued - {client}", "Policy_schedule_{pol}.pdf",
     "Policy schedule. Policy No {pol}. Insured {client}. Period of insurance 12 months.", "insurer"),
    ("Please book the policy - payment done", "Payment_proof_UTR{n}.pdf",
     "NEFT transfer successful. UTR {n}. Premium paid to insurer.", "client"),
    ("KYC documents", "PAN_card.pdf", "Income Tax Department PAN ABCDE1234F", "client"),
    ("KYC documents", "GST_certificate.pdf", "Form GST REG-06 Registration Certificate GSTIN 27ABCDE1234F1Z5", "client"),
    ("Brokerage invoice for {month}", "Tax_Invoice_{n}.pdf",
     "Tax invoice. Brokerage on premium. CGST SGST. Invoice no INV{n}.", "us"),
    ("CD statement as on {month}", "CD_statement_{month}.xlsx",
     "Cash deposit account | Opening balance | Premium utilised | Closing balance", "insurer"),
    ("Fwd: documents", "scan0012.pdf", "", "client"),
]


def tiny_pdf(text: str) -> bytes:
    """A valid one-page PDF containing `text` (no external libraries)."""
    safe = text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
    stream = f"BT /F1 10 Tf 40 800 Td ({safe}) Tj ET".encode("latin-1", "replace")
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 595 842] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n" % len(stream) + stream + b"\nendstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, body in enumerate(objs, 1):
        offsets.append(len(out))
        out += b"%d 0 obj\n" % i + body + b"\nendobj\n"
    xref = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (len(objs) + 1, xref)
    return bytes(out)


def _write(path: Path, text: str) -> None:
    ext = path.suffix.lower()
    if ext == ".pdf":
        path.write_bytes(tiny_pdf(text))
    elif ext == ".xlsx":
        import openpyxl
        wb = openpyxl.Workbook()
        ws = wb.active
        for line in text.split(" - ")[0].split(" | "):
            ws.append([line])
        ws.append([text])
        wb.save(path)
    else:
        path.write_text(text, encoding="utf-8")


def make_demo(cfg: Config, n_emails: int = 400, seed: int = 7) -> None:
    rnd = random.Random(seed)
    conn = db.connect(cfg.db_path)
    tmp = cfg.work_dir / "tmp"
    tmp.mkdir(parents=True, exist_ok=True)
    start = datetime(2023, 4, 1)
    people = ["Anita", "Vikram", "Suresh", "Priya", "Imran", "Kavya"]
    for i in range(n_emails):
        subj_t, file_t, text_t, who = rnd.choice(TEMPLATES)
        client, cdom = rnd.choice(CLIENTS)
        ins, idom = rnd.choice(INSURERS)
        when = start + timedelta(days=rnd.randint(0, 940), hours=rnd.randint(8, 19))
        fy_start = when.year if when.month >= 4 else when.year - 1
        vals = dict(m=when.strftime("%b%Y"), pol=f"{rnd.randint(1000, 9999)}/{rnd.randint(100000, 999999)}/00",
                    person=rnd.choice(people), n=rnd.randint(10000, 99999), client=client,
                    ins_short=ins.split()[0], fy=f"FY{fy_start}-{(fy_start + 1) % 100:02d}",
                    month=when.strftime("%b-%Y"))
        # Some files are re-sent in later threads (duplicates are normal in real mailboxes)
        if rnd.random() < 0.15:
            vals["pol"], vals["n"] = "4410/556677/00", 55555
        subject = subj_t.format(**vals)
        if rnd.random() < 0.3:
            subject = "RE: " + subject
        fname = file_t.format(**vals).replace("/", "-")
        text = text_t.format(**vals)
        cmail = f"{'rahul.mehta' if cdom == 'gmail.com' else 'hr'}@{cdom}"
        if who == "client":
            sender_name, sender, rcpt = (client if cdom != "gmail.com" else "Rahul Mehta"), cmail, [f"ops@{OWN}"]
        elif who == "insurer":
            sender_name, sender, rcpt = f"{ins} Ops", f"ops@{idom}", [f"ops@{OWN}", cmail]
        else:
            sender_name, sender, rcpt = "CapitUp Ops", f"ops@{OWN}", [cmail, f"uw@{idom}"]
        entry_id = f"DEMO{i:06d}"
        folder = "Inbox" if who != "us" else "Sent Items"
        add_message(conn, entry_id=entry_id, store="Demo mailbox", folder=folder, subject=subject,
                    sender_name=sender_name, sender_email=sender, recipients=rcpt,
                    received=when.isoformat(),
                    body=f"Dear team,\nPlease find attached.\nRegards,\n{sender_name}\n\nFrom: someone\nOld thread about claims")
        path = tmp / f"demo{Path(fname).suffix}"
        _write(path, text)
        add_file(conn, cfg, path, fname, entry_id)
    conn.commit()
    print(f"Demo mailbox created: {n_emails} emails in {cfg.db_path}")
