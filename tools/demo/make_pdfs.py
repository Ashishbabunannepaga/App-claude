import sys
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def pdf(path, pages):
    c = canvas.Canvas(path, pagesize=A4)
    for lines in pages:
        y = 800
        for line in lines:
            c.drawString(40, y, line); y -= 18
        c.showPage()
    c.save()

out = sys.argv[1]
pdf(f"{out}/health.pdf", [
    ["Star Health and Allied Insurance - Health Insurance Policy Schedule",
     "Plan: Family Health Optima Insurance Plan",
     "Policy No: P/171100/01/2026/004521",
     "Period of Insurance: From 01/10/2026 To 30/09/2027",
     "Sum Insured: Rs. 10,00,000",
     "Total Premium: Rs. 24,580 (Annual)",
     "Insured members: Self, Spouse, Child",
     "TPA: In-house claim settlement. Cashless at 14,000+ network hospitals."],
    ["SECTION 3 BENEFITS",
     "Room Rent: Single private AC room is covered up to 1% of the sum insured per day.",
     "Pre-hospitalisation expenses are covered for 30 days before admission.",
     "Post-hospitalisation expenses are covered for 60 days after discharge.",
     "Maternity Benefit: Maternity expenses are covered up to Rs. 50,000 per delivery after a",
     "waiting period of 24 months from the first policy inception.",
     "Ambulance charges are covered up to Rs. 2,000 per hospitalisation.",
     "Day care procedures are covered in full up to the sum insured.",
     "Restoration: 100% restoration of the sum insured once per policy year.",
     "AYUSH treatment is covered up to the sum insured.",
     "Co-payment: No co-payment applies for insured persons below 60 years.",
     "No claim bonus of 10% of the sum insured for every claim-free year, up to 100%."],
    ["SECTION 5 EXCLUSIONS",
     "Cosmetic surgery and treatment for obesity are not covered.",
     "Pre-existing diseases are covered after a waiting period of 36 months.",
     "Outpatient (OPD) consultations are not covered.",
     "Dental treatment is not covered unless arising from an accident."],
])
pdf(f"{out}/motor.pdf", [
    ["Acko General Insurance - Private Car Package Policy (Motor Insurance)",
     "Policy No: ACKO-MC-2025-88123",
     "Period of Insurance: From 23/10/2025 To 22/10/2026",
     "Vehicle Make/Model: Hyundai Creta SX 1.5",
     "Registration No: KA-03-MX-4521",
     "Insured Declared Value (IDV): Rs. 9,40,000",
     "Total Premium: Rs. 18,240 (Annual)",
     "Own damage and third party liability cover included."],
    ["ADD-ON COVERS",
     "Zero depreciation cover is included for up to 2 claims per year.",
     "Engine protection cover is included.",
     "Roadside assistance is included 24x7 across India.",
     "Consumables cover is not included.",
     "Return to invoice cover is not included.",
     "NCB: 35% no claim bonus applied.",
     "Compulsory deductible: Rs. 1,000 per claim."],
])
pdf(f"{out}/life.pdf", [
    ["HDFC Life Click 2 Protect Super - Term Life Insurance Policy",
     "Policy No: 24519876",
     "Policy commencement date: 15/03/2022 Policy end date: 14/03/2057",
     "Sum Assured: Rs. 1,00,00,000",
     "Annual Premium: Rs. 14,850 (Annual)",
     "Policy term: 35 years. Premium paying term: 35 years.",
     "Life assured: Asha Rao",
     "Nominee: Ravi Rao (Spouse)",
     "Death benefit: the sum assured is paid to the nominee on death of the life assured.",
     "Maturity benefit: no maturity benefit is payable under this term plan.",
     "Riders: Accidental death benefit rider of Rs. 25,00,000 is included."],
])
pdf(f"{out}/parents.pdf", [
    ["HDFC ERGO Health Insurance - Optima Secure (Senior)",
     "Policy No: 2856 2041 6720 1100 000",
     "Period of Insurance: From 12/01/2026 To 11/01/2027",
     "Sum Insured: Rs. 5,00,000",
     "Total Premium: Rs. 41,200",
     "Room Rent: No room rent limit.",
     "Co-payment: 20% co-payment applies on every claim.",
     "Pre-existing diseases are covered after a waiting period of 24 months."],
])
