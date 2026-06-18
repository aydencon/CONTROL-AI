"""
Generates realistic fake data for Doyle Chrysler controller tool.
Run once:  python fake_data_generator.py
Re-run anytime to reset all data to a clean state.
"""

import pandas as pd
import numpy as np
from datetime import date, timedelta
from pathlib import Path

TODAY = date(2026, 6, 17)
RNG   = np.random.default_rng(42)
OUT   = Path(__file__).parent / "data" / "fake"


# ── helpers ───────────────────────────────────────────────────────────────────

def _d(days_ago: int) -> date:
    return TODAY - timedelta(days=int(days_ago))

def _vin() -> str:
    chars = list("ABCDEFGHJKLMNPRSTUVWXYZ0123456789")
    return "1C4" + "".join(str(RNG.choice(chars)) for _ in range(14))

def _customer() -> str:
    firsts = ["James","Mary","John","Patricia","Robert","Jennifer","Michael","Linda",
              "William","Barbara","David","Elizabeth","Richard","Susan","Joseph",
              "Jessica","Thomas","Sarah","Charles","Karen","Christopher","Lisa",
              "Daniel","Nancy","Matthew","Betty","Anthony","Donald","Steven","Paul",
              "Mark","Sandra","Kevin","Deborah","Brian","Dorothy","George","Lisa"]
    lasts  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
              "Wilson","Martinez","Anderson","Taylor","Thomas","Hernandez","Moore",
              "Martin","Jackson","Thompson","White","Lopez","Lee","Gonzalez","Harris",
              "Clark","Lewis","Robinson","Walker","Perez","Hall","Young","Allen",
              "Sanchez","Wright","King","Scott","Green","Baker","Adams","Nelson"]
    return f"{RNG.choice(firsts)} {RNG.choice(lasts)}"


# ── reference data ────────────────────────────────────────────────────────────

NEW_VEHICLES = [
    ("Jeep",     "Grand Cherokee", 42_000, 52_000),
    ("Jeep",     "Wrangler",       40_000, 50_000),
    ("Jeep",     "Compass",        27_000, 33_000),
    ("Jeep",     "Cherokee",       31_000, 38_000),
    ("Jeep",     "Gladiator",      46_000, 55_000),
    ("Ram",      "1500",           40_000, 51_000),
    ("Ram",      "2500",           50_000, 66_000),
    ("Ram",      "3500",           57_000, 74_000),
    ("Dodge",    "Charger",        37_000, 47_000),
    ("Dodge",    "Durango",        41_000, 53_000),
    ("Dodge",    "Hornet",         29_000, 35_000),
    ("Chrysler", "Pacifica",       37_000, 47_000),
]

USED_VEHICLES = [
    ("Ford",       "F-150",        27_000, 37_000),
    ("Chevrolet",  "Silverado",    25_000, 35_000),
    ("Toyota",     "RAV4",         22_000, 31_000),
    ("Jeep",       "Grand Cherokee",26_000,36_000),
    ("Ram",        "1500",         25_000, 34_000),
    ("Dodge",      "Durango",      22_000, 32_000),
    ("GMC",        "Sierra",       26_000, 36_000),
    ("Ford",       "Explorer",     24_000, 34_000),
    ("Chevrolet",  "Equinox",      18_000, 27_000),
    ("Honda",      "CR-V",         20_000, 29_000),
]

SALESPEOPLE = [
    "Mike Johnson","Sarah Williams","Carlos Rivera","Amanda Chen",
    "David Thompson","Jessica Martinez","Robert Kim","Lisa Anderson",
]

FINANCE_COS = [
    "Chrysler Capital","Chrysler Capital","Chrysler Capital",
    "Ally Financial","TD Auto Finance","Chase Auto",
    "Wells Fargo Auto","Capital One Auto","Cash",
]

VENDORS = {
    "Stellantis NV":        "2210",
    "CDK Global":           "6090",
    "Snap-on Tools":        "6030",
    "O'Reilly Auto Parts":  "5050",
    "Cintas Corp":          "6030",
    "AT&T Business":        "6080",
    "Xcel Energy":          "6080",
    "State Farm Insurance": "6060",
    "AutoTrader.com":       "6070",
    "Cars.com":             "6070",
    "Google Ads":           "6070",
    "Carfax":               "6090",
    "Reynolds & Reynolds":  "6090",
    "Waste Management":     "6080",
    "CDW Computer":         "6090",
    "Dealer Inspire":       "6070",
    "Protective Life":      "6060",
    "Office Depot":         "6030",
    "NAPA Auto Parts":      "5050",
    "SiriusXM Dealer":      "6070",
    "Pitney Bowes":         "6030",
}

SERVICE_CUSTOMERS = [
    ("Riverside Logistics",   "dispatch@riverside-logistics.com"),
    ("ABC Plumbing Co",       "accounts@abcplumbing.com"),
    ("Summit Construction",   "ap@summitconstruction.com"),
    ("Green Valley Farms",    "office@greenvalleyfarms.com"),
    ("Metro Transit",         "fleet@metrotransit.gov"),
    ("Lakeside Schools",      "business@lakesideschools.edu"),
    ("Premier Healthcare",    "accounting@premierhc.com"),
    ("City of Millbrook",     "ap@cityofmillbrook.gov"),
    ("Western Auto Fleet",    "billing@westernautofleet.com"),
    ("Apex Delivery",         "ar@apexdelivery.com"),
    ("Harbor Marine",         "office@harbormarine.com"),
    ("Blue Ridge Trucking",   "accounts@blueridgetrucking.com"),
]


# ── generators ────────────────────────────────────────────────────────────────

def gen_deals(out: Path) -> pd.DataFrame:
    rows = []
    n = 1

    def add(dept, veh_list, days_min, days_max, count, posted=True):
        nonlocal n
        for _ in range(count):
            make, model, lo, hi = veh_list[int(RNG.integers(0, len(veh_list)))]
            floor_amt = int(RNG.integers(lo, hi))
            if dept == "New Vehicle":
                front = int(RNG.integers(800, 4_500))
                back  = int(RNG.integers(800, 3_800))
                yr    = 2026
            else:
                front = int(RNG.integers(1_200, 5_500))
                back  = int(RNG.integers(600,   3_000))
                yr    = int(RNG.integers(2020, 2026))
            fin_co = str(RNG.choice(FINANCE_COS))
            funded = fin_co != "Cash"
            days   = int(RNG.integers(days_min, max(days_min + 1, days_max)))
            sale_d = _d(days)
            fund_d = (sale_d + timedelta(days=int(RNG.integers(1, 4)))) if (funded and posted) else None
            rows.append({
                "deal_number":    f"D-{n:04d}",
                "date":           sale_d,
                "customer":       _customer(),
                "salesperson":    str(RNG.choice(SALESPEOPLE)),
                "department":     dept,
                "year":           yr,
                "make":           make,
                "model":          model,
                "vin":            _vin(),
                "stock_number":   f"{'N' if dept == 'New Vehicle' else 'U'}{n:04d}",
                "sale_price":     floor_amt + front,
                "front_gross":    front,
                "back_gross":     back,
                "total_gross":    front + back,
                "finance_company": fin_co,
                "funded_amount":  round(floor_amt * 0.83, 2) if funded else 0.0,
                "funded_date":    fund_d,
                "posted":         posted,
                "status":         "Posted" if posted else "Unposted",
            })
            n += 1

    # June (current month — 17 days elapsed)
    add("New Vehicle", NEW_VEHICLES, 0, 17, 21)
    add("Used Vehicle", USED_VEHICLES, 0, 17, 16)
    add("New Vehicle", NEW_VEHICLES, 0, 2, 2, posted=False)   # unposted
    add("Used Vehicle", USED_VEHICLES, 0, 2, 1, posted=False) # unposted

    # May
    add("New Vehicle", NEW_VEHICLES, 18, 47, 22)
    add("Used Vehicle", USED_VEHICLES, 18, 47, 18)

    # April
    add("New Vehicle", NEW_VEHICLES, 48, 77, 18)
    add("Used Vehicle", USED_VEHICLES, 48, 77, 14)

    # Jan–Mar
    add("New Vehicle", NEW_VEHICLES, 78, 167, 40)
    add("Used Vehicle", USED_VEHICLES, 78, 167, 32)

    df = pd.DataFrame(rows)
    df.to_csv(out / "deals.csv", index=False)
    print(f"  deals:         {len(df):>4} rows")
    return df


def gen_floorplan(out: Path):
    new_specs = [
        ("Jeep",     "Grand Cherokee", "Diamond Black",    45_800, 8),
        ("Jeep",     "Wrangler",       "Firecracker Red",  43_200, 12),
        ("Ram",      "1500",           "Billet Silver",    43_500, 18),
        ("Jeep",     "Grand Cherokee", "Bright White",     47_200, 22),
        ("Ram",      "2500",           "Granite Crystal",  56_800, 27),
        ("Dodge",    "Durango",        "Pitch Black",      44_100, 31),
        ("Jeep",     "Wrangler",       "Sarge Green",      48_900, 35),
        ("Ram",      "1500",           "Patriot Blue",     41_700, 40),
        ("Jeep",     "Cherokee",       "Velvet Red",       33_800, 45),
        ("Ram",      "3500",           "Bright White",     62_400, 51),
        ("Jeep",     "Compass",        "Laser Blue",       29_100, 58),
        ("Dodge",    "Charger",        "Pitch Black",      39_900, 64),
        ("Chrysler", "Pacifica",       "Brilliant Black",  40_200, 70),
        ("Ram",      "1500",           "Granite Crystal",  44_500, 75),
        ("Jeep",     "Grand Cherokee", "Sting Gray",       49_800, 82),
        ("Jeep",     "Gladiator",      "Nacho Yellow",     51_200, 89),
        ("Dodge",    "Hornet",         "Acapulco Gold",    31_400, 95),
        ("Ram",      "2500",           "Bright White",     58_100, 102),
        ("Jeep",     "Cherokee",       "Hydro Blue",       34_600, 110),
        ("Ram",      "1500",           "Delmonico Red",    42_800, 118),
        ("Jeep",     "Wrangler",       "Hydro Blue",       44_100, 125),
        ("Dodge",    "Durango",        "Granite Crystal",  43_800, 134),
        ("Chrysler", "Pacifica",       "Brilliant Black",  38_700, 142),
        ("Ram",      "3500",           "Black",            64_200, 151),
        ("Jeep",     "Grand Cherokee", "Summit White",     52_100, 163),
        ("Jeep",     "Compass",        "Sting Gray",       28_900, 172),
        ("Ram",      "1500",           "Anvil",            40_600, 185),   # over curtailment
        ("Dodge",    "Charger",        "TorRed",           41_300, 198),   # over curtailment
        ("Jeep",     "Gladiator",      "Sarge Green",      49_700, 212),   # over curtailment
        ("Ram",      "2500",           "Flame Red",        55_900, 224),   # over curtailment
    ]

    used_specs = [
        ("Ford",      "F-150",          2023, "Rapid Red",       31_400,  5),
        ("Chevrolet", "Silverado",       2022, "Summit White",    27_600, 14),
        ("Toyota",    "RAV4",            2023, "Midnight Black",  26_800, 21),
        ("Jeep",      "Grand Cherokee",  2022, "Billet Silver",   28_900, 33),
        ("Ram",       "1500",            2021, "Granite Crystal", 25_100, 47),
        ("GMC",       "Sierra",          2022, "Onyx Black",      29_400, 58),
        ("Ford",      "Explorer",        2023, "Carbonized Gray", 26_200, 72),
        ("Dodge",     "Durango",         2022, "Pitch Black",     24_800, 84),
        ("Chevrolet", "Equinox",         2023, "Silver Ice",      19_600, 95),
        ("Honda",     "CR-V",            2022, "Sonic Gray",      21_400, 108),
        ("Ram",       "1500",            2023, "Bright White",    33_800, 121),
        ("Ford",      "F-150",           2022, "Area 51",         29_900, 138),
        ("Jeep",      "Wrangler",        2021, "Firecracker Red", 30_200, 155),
        ("Chevrolet", "Silverado",       2023, "Red Hot",         31_700, 169),
        ("Toyota",    "RAV4",            2022, "Blueprint",       24_600, 188),  # over
    ]

    rows = []
    n = 1

    for make, model, color, amt, age in new_specs:
        rate     = 0.0825
        interest = round(amt * rate / 365 * age, 2)
        over     = max(0, age - 180)
        rows.append({
            "stock_number":          f"N{n:04d}",
            "vin":                   _vin(),
            "year":                  2026,
            "make":                  make,
            "model":                 model,
            "color":                 color,
            "department":            "New Vehicle",
            "floored_date":          _d(age),
            "days_floored":          age,
            "floor_amount":          amt,
            "interest_accrued":      interest,
            "total_outstanding":     round(amt + interest, 2),
            "curtailment_due":       age > 180,
            "days_over_curtailment": over,
            "status":                "Curtailment Due" if age > 180 else "Current",
        })
        n += 1

    for make, model, yr, color, amt, age in used_specs:
        rate     = 0.0925
        interest = round(amt * rate / 365 * age, 2)
        over     = max(0, age - 180)
        rows.append({
            "stock_number":          f"U{n:04d}",
            "vin":                   _vin(),
            "year":                  yr,
            "make":                  make,
            "model":                 model,
            "color":                 color,
            "department":            "Used Vehicle",
            "floored_date":          _d(age),
            "days_floored":          age,
            "floor_amount":          amt,
            "interest_accrued":      interest,
            "total_outstanding":     round(amt + interest, 2),
            "curtailment_due":       age > 180,
            "days_over_curtailment": over,
            "status":                "Curtailment Due" if age > 180 else "Current",
        })
        n += 1

    df = pd.DataFrame(rows)
    df.to_csv(out / "floorplan.csv", index=False)
    print(f"  floorplan:     {len(df):>4} rows")


def gen_ap_invoices(out: Path):
    vendor_list = list(VENDORS.keys())
    rows = []
    inv  = 1

    def add(vendor, amount, days_ago, due_days=30, status="Unpaid", paid_ago=None):
        nonlocal inv
        gl_acc  = VENDORS[vendor]
        inv_d   = _d(days_ago)
        due_d   = inv_d + timedelta(days=due_days)
        paid_d  = _d(paid_ago) if paid_ago is not None else None
        rows.append({
            "invoice_id":    f"INV-{inv:04d}",
            "vendor":        vendor,
            "invoice_number": f"{vendor[:3].upper().replace(' ','')}-{8000 + inv}",
            "invoice_date":  inv_d,
            "due_date":      due_d,
            "amount":        amount,
            "gl_account":    gl_acc,
            "department":    "Admin" if gl_acc.startswith("6") else "Parts",
            "description":   f"{vendor} — monthly service",
            "approved_by":   "Controller",
            "status":        status,
            "paid_date":     paid_d,
            "days_outstanding": (TODAY - inv_d).days,
            "days_overdue":  max(0, (TODAY - due_d).days),
        })
        inv += 1

    # Current / due soon
    add("CDK Global",           4_850.00,  3, due_days=30)
    add("AT&T Business",          312.47,  5, due_days=25)
    add("Xcel Energy",            687.22,  2, due_days=28)
    add("Dealer Inspire",       1_200.00,  8, due_days=30)
    add("AutoTrader.com",       1_450.00,  8, due_days=30)
    add("Cars.com",               980.00, 10, due_days=30)
    add("Google Ads",           2_100.00,  6, due_days=30)
    add("Carfax",                 249.00,  4, due_days=30)
    add("SiriusXM Dealer",        189.00,  7, due_days=30)
    add("Reynolds & Reynolds",    425.00, 11, due_days=30)
    add("Office Depot",           183.46, 12, due_days=30)
    add("Waste Management",       312.00,  9, due_days=30)
    add("Pitney Bowes",           148.00, 14, due_days=30)

    # Due this week (3–7 days out)
    add("State Farm Insurance",  3_240.00, 25, due_days=28)
    add("Protective Life",       1_890.00, 23, due_days=26)
    add("CDW Computer",          1_650.00, 22, due_days=25)

    # Overdue
    add("Stellantis NV",        18_400.00, 48, due_days=30)   # 18 days overdue
    add("Cintas Corp",             427.80, 55, due_days=30)   # 25 days overdue
    add("NAPA Auto Parts",         891.34, 62, due_days=30)   # 32 days overdue
    add("Snap-on Tools",         2_340.00, 72, due_days=30)   # 42 days overdue
    add("O'Reilly Auto Parts",   1_247.56, 88, due_days=30)   # 58 days overdue

    # Duplicate — same vendor/amount/close date (intentional test case)
    add("CDK Global",           4_850.00, 35, due_days=30)    # possible duplicate of CDK above

    # Paid invoices
    add("AT&T Business",          309.14, 35, due_days=30, status="Paid", paid_ago=12)
    add("Xcel Energy",            701.88, 35, due_days=30, status="Paid", paid_ago=10)
    add("Google Ads",           1_980.00, 38, due_days=30, status="Paid", paid_ago=8)
    add("AutoTrader.com",       1_450.00, 38, due_days=30, status="Paid", paid_ago=9)

    df = pd.DataFrame(rows)
    df.to_csv(out / "ap_invoices.csv", index=False)
    print(f"  ap_invoices:   {len(df):>4} rows")


def gen_ar_aging(out: Path):
    rows = []

    data = [
        # (customer, email, amount, days_outstanding, dept)
        ("Riverside Logistics",  "dispatch@riverside-logistics.com",  4_820.50,  8,  "Service"),
        ("ABC Plumbing Co",      "accounts@abcplumbing.com",           1_245.00, 12,  "Parts"),
        ("Summit Construction",  "ap@summitconstruction.com",          3_610.00, 18,  "Service"),
        ("Green Valley Farms",   "office@greenvalleyfarms.com",          892.75, 22,  "Parts"),
        ("Metro Transit",        "fleet@metrotransit.gov",             6_480.00, 28,  "Service"),
        ("Lakeside Schools",     "business@lakesideschools.edu",       2_190.00, 15,  "Service"),
        ("Premier Healthcare",   "accounting@premierhc.com",           1_560.00,  5,  "Parts"),
        ("City of Millbrook",    "ap@cityofmillbrook.gov",             3_920.00, 10,  "Service"),
        ("Western Auto Fleet",   "billing@westernautofleet.com",       5_640.00, 35,  "Service"),
        ("Apex Delivery",        "ar@apexdelivery.com",                1_870.00, 38,  "Service"),
        ("Harbor Marine",        "office@harbormarine.com",            2_340.00, 42,  "Parts"),
        ("Blue Ridge Trucking",  "accounts@blueridgetrucking.com",     3_115.00, 48,  "Service"),
        ("Riverside Logistics",  "dispatch@riverside-logistics.com",   1_980.00, 55,  "Service"),
        ("Summit Construction",  "ap@summitconstruction.com",          4_250.00, 61,  "Service"),
        ("Metro Transit",        "fleet@metrotransit.gov",             7_840.00, 68,  "Service"),
        ("Western Auto Fleet",   "billing@westernautofleet.com",       2_760.00, 75,  "Parts"),
        ("Apex Delivery",        "ar@apexdelivery.com",                1_430.00, 82,  "Service"),
        ("Harbor Marine",        "office@harbormarine.com",            3_890.00, 91,  "Parts"),   # 90+
        ("Blue Ridge Trucking",  "accounts@blueridgetrucking.com",     5_210.00, 107, "Service"),  # 90+
        ("Green Valley Farms",   "office@greenvalleyfarms.com",        1_125.00, 124, "Parts"),   # 90+
    ]

    for i, (cust, email, amt, days, dept) in enumerate(data):
        inv_d = _d(days)
        rows.append({
            "invoice_number":   f"AR-{i+1:04d}",
            "customer":         cust,
            "contact_email":    email,
            "invoice_date":     inv_d,
            "amount":           amt,
            "payments":         0.0,
            "balance":          amt,
            "days_outstanding": days,
            "department":       dept,
            "aging_bucket":     ("0-30" if days <= 30 else
                                 "31-60" if days <= 60 else
                                 "61-90" if days <= 90 else "90+"),
        })

    df = pd.DataFrame(rows)
    df.to_csv(out / "ar_aging.csv", index=False)
    print(f"  ar_aging:      {len(df):>4} rows")


def gen_schedules_and_detail(out: Path, deals_df: pd.DataFrame):
    """
    Generates both schedules.csv (GL balances) and schedule_detail.csv (line items).
    Intentional variances:
      - Contract in Transit: $3,350 variance (deal posted to GL, missing from schedule)
      - Customer Deposits:  -$500 variance (deposit on schedule, refunded in GL)
      - Factory Receivables: $0 variance (clean)
    """

    # ── Contract in Transit (1210) ─────────────────────────────────────────────
    funded = deals_df[
        (deals_df["funded_amount"] > 0) &
        (deals_df["status"] == "Posted") &
        (deals_df["funded_date"].notna())
    ].copy()
    funded["funded_date"] = pd.to_datetime(funded["funded_date"])

    # Take 18 recent funded deals for the CIT schedule
    cit_deals = funded.sort_values("funded_date", ascending=False).head(18)

    detail_rows = []
    for _, row in cit_deals.iterrows():
        fund_d  = pd.to_datetime(row["funded_date"]).date()
        days_open = (TODAY - fund_d).days
        detail_rows.append({
            "schedule_name": "Contract in Transit",
            "gl_account":    "1210",
            "item_date":     fund_d,
            "description":   f"{row['customer']} – {row['finance_company']}",
            "reference":     row["deal_number"],
            "amount":        row["funded_amount"],
            "days_open":     days_open,
        })

    cit_detail_sum = sum(r["amount"] for r in detail_rows)
    # GL balance intentionally $3,350 higher (one unrecorded schedule item)
    cit_gl_balance = round(cit_detail_sum + 3_350.00, 2)

    # ── Factory Receivables (1220) ─────────────────────────────────────────────
    factory_items = [
        ("Warranty Claim #WC-44821", "WC-44821",  1_840.00, 12),
        ("Warranty Claim #WC-44756", "WC-44756",    720.50, 18),
        ("Warranty Claim #WC-44690", "WC-44690",  2_140.00, 24),
        ("Warranty Claim #WC-44611", "WC-44611",    980.00, 31),
        ("Warranty Claim #WC-44540", "WC-44540",  1_650.00, 38),
        ("Warranty Claim #WC-44487", "WC-44487",  2_890.00, 45),
        ("Warranty Claim #WC-44401", "WC-44401",    540.00, 52),
        ("Warranty Claim #WC-44320", "WC-44320",  1_210.00, 68),  # critical age
        ("Holdback Q1 2026",         "HB-Q12026", 14_250.00, 72), # critical age
        ("Holdback Q2 Partial",      "HB-Q22026",  8_400.00, 14),
        ("Incentive Reimb #IR-2241", "IR-2241",    3_100.00, 22),
        ("Incentive Reimb #IR-2198", "IR-2198",    2_400.00, 35),
        ("Incentive Reimb #IR-2167", "IR-2167",    1_800.00, 41),
        ("Retail Cash Incentive Q1", "RCI-Q1",     4_500.00, 78), # critical age
        ("Stair Step Bonus Mar",     "SSB-MAR",    6_200.00, 82), # critical age
    ]

    factory_sum = 0.0
    for desc, ref, amt, days in factory_items:
        detail_rows.append({
            "schedule_name": "Factory Receivables",
            "gl_account":    "1220",
            "item_date":     _d(days),
            "description":   desc,
            "reference":     ref,
            "amount":        amt,
            "days_open":     days,
        })
        factory_sum += amt

    factory_gl_balance = round(factory_sum, 2)  # perfectly reconciled

    # ── Customer Deposits (2110) ───────────────────────────────────────────────
    deposit_items = [
        ("Vehicle Order – James Smith",       "DEP-0441", 1_000.00,  8),
        ("Vehicle Order – Maria Garcia",      "DEP-0438", 1_500.00, 12),
        ("Vehicle Order – Kevin Brown",       "DEP-0432", 1_000.00, 19),
        ("Vehicle Order – Sandra Lee",        "DEP-0428", 2_000.00, 24),
        ("Vehicle Order – Christopher Hall",  "DEP-0421",   500.00, 31),
        ("Vehicle Order – Dorothy Nelson",    "DEP-0417", 1_000.00, 38),
        ("Vehicle Order – Anthony Wilson",    "DEP-0412", 1_500.00, 45),
        ("Vehicle Order – Nancy Thompson",    "DEP-0405", 1_000.00, 52),
        ("Vehicle Order – George Adams",      "DEP-0398", 2_000.00, 60),   # warning age
        ("Vehicle Order – Lisa Wright",       "DEP-0388", 1_000.00, 72),   # critical age
        # This item exists on schedule but deposit was refunded in GL (creates -$500 variance)
        ("Vehicle Order – Paul Scott",        "DEP-0381",   500.00, 85),   # critical; GL already reversed
    ]

    deposit_sum = 0.0
    for desc, ref, amt, days in deposit_items:
        detail_rows.append({
            "schedule_name": "Customer Deposits",
            "gl_account":    "2110",
            "item_date":     _d(days),
            "description":   desc,
            "reference":     ref,
            "amount":        amt,
            "days_open":     days,
        })
        deposit_sum += amt

    # GL is $500 less (last deposit was refunded in GL but not removed from schedule)
    deposit_gl_balance = round(deposit_sum - 500.00, 2)

    # ── Service WIP (1320) ────────────────────────────────────────────────────
    wip_items = [
        ("RO #58841 – James Anderson",   "RO-58841", 2_840.00,  3),
        ("RO #58822 – Mary Thompson",    "RO-58822",   920.50,  5),
        ("RO #58799 – Robert Garcia",    "RO-58799", 1_640.00,  8),
        ("RO #58781 – Patricia Wilson",  "RO-58781",   480.00, 11),
        ("RO #58762 – Michael Davis",    "RO-58762", 3_120.00, 14),
        ("RO #58744 – Linda Martinez",   "RO-58744", 1_890.00, 18),
        ("RO #58720 – William Taylor",   "RO-58720",   640.00, 22),
        ("RO #58698 – Barbara Lewis",    "RO-58698", 2_280.00, 28),
        ("RO #58671 – Richard Moore",    "RO-58671",   760.00, 35),  # warning
        ("RO #58641 – Susan Hall",       "RO-58641", 1_450.00, 42),  # warning
    ]
    wip_sum = 0.0
    for desc, ref, amt, days in wip_items:
        detail_rows.append({
            "schedule_name": "Service WIP",
            "gl_account":    "1320",
            "item_date":     _d(days),
            "description":   desc,
            "reference":     ref,
            "amount":        amt,
            "days_open":     days,
        })
        wip_sum += amt

    wip_gl_balance = round(wip_sum, 2)  # clean

    # ── Save schedule detail ───────────────────────────────────────────────────
    pd.DataFrame(detail_rows).to_csv(out / "schedule_detail.csv", index=False)

    # ── Save schedules (GL balances) ──────────────────────────────────────────
    schedules = [
        {"schedule_name": "Contract in Transit", "gl_account": "1210",
         "gl_balance": cit_gl_balance,   "description": "Funded deals awaiting bank deposit"},
        {"schedule_name": "Factory Receivables", "gl_account": "1220",
         "gl_balance": factory_gl_balance,"description": "Warranty, holdback, incentives from Stellantis"},
        {"schedule_name": "Customer Deposits",   "gl_account": "2110",
         "gl_balance": deposit_gl_balance,"description": "Deposits on ordered vehicles"},
        {"schedule_name": "Service WIP",         "gl_account": "1320",
         "gl_balance": wip_gl_balance,   "description": "Open repair orders in progress"},
    ]
    pd.DataFrame(schedules).to_csv(out / "schedules.csv", index=False)

    print(f"  schedules:     {len(schedules):>4} rows")
    print(f"  sched_detail:  {len(detail_rows):>4} rows")


def gen_gl_balances(out: Path):
    rows = [
        # account_number, account_name, dept, current_bal, prior_bal, ytd_bal, prior_ytd, budget_ytd
        ("1010","Cash – Operating",        "Admin",   342_150,  298_400,  342_150,  310_200,  300_000),
        ("1020","Cash – Payroll",          "Admin",    48_200,   52_100,   48_200,   50_000,   50_000),
        ("1110","New Vehicle Inventory",   "New Veh",1_512_800,1_648_200,1_512_800,1_702_400,1_600_000),
        ("1120","Used Vehicle Inventory",  "Used Veh", 412_600,  388_400,  412_600,  402_100,  400_000),
        ("1210","Contract in Transit",     "Admin",      0,         0,        0,       0,        0),   # set dynamically
        ("1220","Factory Receivables",     "Admin",      0,         0,        0,       0,        0),   # set dynamically
        ("1230","Service Receivables",     "Service",  28_420,   31_200,   28_420,   29_800,   25_000),
        ("1310","Parts Inventory",         "Parts",   184_300,  178_600,  184_300,  180_400,  180_000),
        ("1320","Service WIP",             "Service",    0,         0,        0,       0,        0),   # set dynamically
        ("1410","Prepaid Expenses",        "Admin",    18_400,   19_200,   18_400,   18_900,   18_000),
        ("2010","Accounts Payable",        "Admin",  -145_800, -138_400, -145_800, -142_300, -140_000),
        ("2110","Customer Deposits",       "Admin",     0,         0,        0,       0,        0),   # set dynamically
        ("2210","Factory Payables",        "Admin",  -24_600,  -18_200,  -24_600,  -21_400,  -20_000),
        ("2310","Floorplan Payable",       "Admin", -1_785_000,-1_812_000,-1_785_000,-1_798_000,-1_800_000),
        ("2320","Floorplan Interest Pay",  "Admin",    -8_420,   -7_800,   -8_420,   -7_900,   -8_000),
        ("2410","Payroll Taxes Payable",   "Admin",   -14_200,  -13_800,  -14_200,  -13_600,  -14_000),
        ("2420","Sales Tax Payable",       "Admin",   -22_400,  -21_600,  -22_400,  -20_800,  -21_000),
        ("4010","New Vehicle Sales",       "New Veh", 892_400,  812_600, 4_821_800, 4_612_400, 4_800_000),
        ("4020","Used Vehicle Sales",      "Used Veh",548_200,  501_400, 2_984_600, 2_812_800, 3_000_000),
        ("4030","F&I Income",              "F&I",     124_800,  112_400,  682_400,  648_200,  700_000),
        ("4040","Service Revenue",         "Service", 214_600,  198_800, 1_182_400,1_148_600,1_200_000),
        ("4050","Parts Revenue",           "Parts",    82_400,   78_200,  448_600,  428_800,  460_000),
        ("5010","New Vehicle Cost",        "New Veh",-812_800, -748_400,-4_412_600,-4_214_800,-4_400_000),
        ("5020","Used Vehicle Cost",       "Used Veh",-482_400,-448_200,-2_648_400,-2_514_600,-2_700_000),
        ("5030","Parts Cost",              "Parts",   -52_400,  -49_800, -284_200, -272_400, -290_000),
        ("5040","Service Technician Pay",  "Service", -98_400,  -91_200, -541_800, -524_600, -550_000),
        ("6010","Payroll – Sales",         "New Veh", -48_200,  -44_800, -264_600, -248_400, -270_000),
        ("6020","Payroll – F&I",           "F&I",     -18_400,  -17_200,  -98_400,  -94_800, -100_000),
        ("6030","Payroll – Admin",         "Admin",   -42_800,  -41_200, -234_800, -228_400, -240_000),
        ("6040","Floorplan Interest",      "Admin",   -12_840,  -13_200,  -78_400,  -76_800,  -80_000),
        ("6050","Rent & Facilities",       "Admin",   -24_500,  -24_500, -147_000, -147_000, -147_000),
        ("6060","Insurance",               "Admin",    -8_140,   -8_140,  -48_840,  -48_840,  -49_000),
        ("6070","Advertising",             "Admin",   -18_240,  -16_800, -104_400,  -98_200, -110_000),
        ("6080","Utilities & Telecom",     "Admin",    -4_280,   -4_120,  -24_800,  -24_200,  -25_000),
        ("6090","IT & Software",           "Admin",    -8_420,   -8_100,  -48_600,  -46_800,  -50_000),
    ]

    df = pd.DataFrame(rows, columns=[
        "account_number","account_name","department",
        "current_balance","prior_month_balance","ytd_balance",
        "prior_ytd_balance","budget_ytd"
    ])
    df.to_csv(out / "gl_balances.csv", index=False)
    print(f"  gl_balances:   {len(df):>4} rows")


def gen_bank_transactions(out: Path):
    rows = []
    n = 1

    def add(days_ago, desc, amount, ref="", matched=True):
        nonlocal n
        rows.append({
            "transaction_id": f"BNK-{n:04d}",
            "date":           _d(days_ago),
            "description":    desc,
            "amount":         amount,
            "reference":      ref,
            "type":           "Credit" if amount > 0 else "Debit",
            "matched_to_gl":  matched,
        })
        n += 1

    # June 2026 (last 17 days)
    add(1,  "Chrysler Capital – Deal Funding",      38_420.00, "D-0015")
    add(1,  "Chrysler Capital – Deal Funding",      41_800.00, "D-0018")
    add(2,  "Ally Financial – Deal Funding",        29_640.00, "D-0021")
    add(2,  "Chrysler Capital Floorplan – Payment", -42_800.00,"FP-JUN2")
    add(3,  "Chase Auto – Deal Funding",            33_210.00, "D-0024")
    add(3,  "TD Auto Finance – Deal Funding",       27_840.00, "D-0027")
    add(4,  "Payroll – Bi-weekly",                 -84_200.00, "PR-0612")
    add(4,  "Chrysler Capital – Deal Funding",      44_600.00, "D-0031")
    add(5,  "Wells Fargo Auto – Deal Funding",      36_820.00, "D-0035")
    add(5,  "Capital One Auto – Deal Funding",      28_410.00, "D-0038")
    add(5,  "Chrysler Capital Floorplan – Payment", -38_400.00,"FP-JUN5")
    add(6,  "Cash Sale – Service",                   4_820.50, "SV-1124")
    add(6,  "Chrysler Capital – Deal Funding",      51_200.00, "D-0041")
    add(7,  "Ally Financial – Deal Funding",        32_640.00, "D-0044")
    add(7,  "State Farm – Refund",                   1_240.00, "SF-REF")
    add(8,  "Chrysler Capital – Deal Funding",      47_800.00, "D-0047")
    add(8,  "CDK Global – Invoice",                 -4_850.00, "INV-4802")
    add(9,  "TD Auto Finance – Deal Funding",       38_200.00, "D-0050")
    add(9,  "Chrysler Capital Floorplan – Payment", -44_200.00,"FP-JUN9")
    add(10, "Chase Auto – Deal Funding",            42_600.00, "D-0053")
    add(10, "Cash Sales – Parts",                    2_340.00, "PT-0618")
    add(11, "Wells Fargo Auto – Deal Funding",      34_800.00, "D-0056")
    add(11, "Payroll – Bi-weekly",                 -84_200.00, "PR-0626")
    add(12, "Chrysler Capital – Deal Funding",      39_400.00, "D-0059")
    add(12, "Xcel Energy – Auto-pay",                 -687.22, "XCEL-0612")
    add(13, "Capital One Auto – Deal Funding",      26_800.00, "D-0062")
    add(13, "AT&T Business – Auto-pay",               -312.47, "ATT-0613")
    add(14, "Chrysler Capital – Deal Funding",      48_200.00, "D-0065")
    add(14, "Chrysler Capital Floorplan – Payment", -39_600.00,"FP-JUN14")
    add(15, "Cash Sales – Service",                  6_480.00, "SV-1131")
    add(16, "Ally Financial – Deal Funding",        31_400.00, "D-0068")
    add(17, "Chrysler Capital – Deal Funding",      43_800.00, "D-0071")

    # Unmatched bank items (bank charges not yet recorded in GL)
    add(3,  "Bank Service Charge",                    -42.00, "BSC-0603", matched=False)
    add(8,  "Positive Pay Fee",                        -18.00, "PPF-0608", matched=False)
    add(10, "Wire Transfer Fee",                       -25.00, "WTF-0610", matched=False)

    # May (prior month — key items)
    add(18, "Chrysler Capital – Deal Funding",      41_200.00, "D-0012-MAY")
    add(20, "Chrysler Capital Floorplan – Payment", -48_200.00,"FP-MAY20")
    add(22, "Payroll – Bi-weekly",                 -82_400.00, "PR-0528")
    add(24, "Ally Financial – Deal Funding",        36_400.00, "D-0014-MAY")
    add(25, "CDK Global – Invoice",                 -4_850.00, "INV-4791")
    add(28, "Wells Fargo Auto – Deal Funding",      29_800.00, "D-0021-MAY")
    add(30, "Payroll – Bi-weekly",                 -82_400.00, "PR-0514")
    add(32, "Chrysler Capital – Deal Funding",      44_600.00, "D-0028-MAY")
    add(35, "State Farm Insurance – Auto-pay",      -3_240.00, "SF-0515")
    add(38, "Protective Life – Auto-pay",           -1_890.00, "PL-0512")
    add(40, "Chrysler Capital Floorplan – Payment", -42_800.00,"FP-MAY8")
    add(42, "Chase Auto – Deal Funding",            38_200.00, "D-0035-MAY")
    add(44, "Payroll – Bi-weekly",                 -82_400.00, "PR-0430")
    add(46, "Cash Sales – Parts & Service",          8_400.00, "PS-APR30")

    df = pd.DataFrame(rows)
    df.to_csv(out / "bank_transactions.csv", index=False)
    print(f"  bank_trans:    {len(df):>4} rows")


def gen_gl_cash_transactions(out: Path):
    """GL side of cash — mostly mirrors bank but missing the 3 bank charges."""
    rows = []
    n = 1

    def add(days_ago, desc, debit, credit, ref=""):
        nonlocal n
        rows.append({
            "entry_id":   f"GL-{n:04d}",
            "date":       _d(days_ago),
            "description": desc,
            "reference":  ref,
            "debit":      debit,
            "credit":     credit,
            "account":    "1010",
        })
        n += 1

    # Mirrors bank transactions except the 3 bank charges (those are unmatched)
    add(1,  "Chrysler Capital – Deal Funding",      38_420.00, 0,         "D-0015")
    add(1,  "Chrysler Capital – Deal Funding",      41_800.00, 0,         "D-0018")
    add(2,  "Ally Financial – Deal Funding",        29_640.00, 0,         "D-0021")
    add(2,  "Chrysler Capital FP – Payment",        0,  42_800.00,        "FP-JUN2")
    add(3,  "Chase Auto – Deal Funding",            33_210.00, 0,         "D-0024")
    add(3,  "TD Auto Finance – Deal Funding",       27_840.00, 0,         "D-0027")
    add(4,  "Payroll – Bi-weekly",                  0,  84_200.00,        "PR-0612")
    add(4,  "Chrysler Capital – Deal Funding",      44_600.00, 0,         "D-0031")
    add(5,  "Wells Fargo Auto – Deal Funding",      36_820.00, 0,         "D-0035")
    add(5,  "Capital One Auto – Deal Funding",      28_410.00, 0,         "D-0038")
    add(5,  "Chrysler Capital FP – Payment",        0,  38_400.00,        "FP-JUN5")
    add(6,  "Cash Sale – Service",                   4_820.50, 0,         "SV-1124")
    add(6,  "Chrysler Capital – Deal Funding",      51_200.00, 0,         "D-0041")
    add(7,  "Ally Financial – Deal Funding",        32_640.00, 0,         "D-0044")
    add(7,  "State Farm – Refund",                   1_240.00, 0,         "SF-REF")
    add(8,  "Chrysler Capital – Deal Funding",      47_800.00, 0,         "D-0047")
    add(8,  "CDK Global – Invoice",                 0,   4_850.00,        "INV-4802")
    add(9,  "TD Auto Finance – Deal Funding",       38_200.00, 0,         "D-0050")
    add(9,  "Chrysler Capital FP – Payment",        0,  44_200.00,        "FP-JUN9")
    add(10, "Chase Auto – Deal Funding",            42_600.00, 0,         "D-0053")
    add(10, "Cash Sales – Parts",                    2_340.00, 0,         "PT-0618")
    add(11, "Wells Fargo Auto – Deal Funding",      34_800.00, 0,         "D-0056")
    add(11, "Payroll – Bi-weekly",                  0,  84_200.00,        "PR-0626")
    add(12, "Chrysler Capital – Deal Funding",      39_400.00, 0,         "D-0059")
    add(12, "Xcel Energy – Auto-pay",               0,     687.22,        "XCEL-0612")
    add(13, "Capital One Auto – Deal Funding",      26_800.00, 0,         "D-0062")
    add(13, "AT&T Business – Auto-pay",             0,     312.47,        "ATT-0613")
    add(14, "Chrysler Capital – Deal Funding",      48_200.00, 0,         "D-0065")
    add(14, "Chrysler Capital FP – Payment",        0,  39_600.00,        "FP-JUN14")
    add(15, "Cash Sales – Service",                  6_480.00, 0,         "SV-1131")
    add(16, "Ally Financial – Deal Funding",        31_400.00, 0,         "D-0068")
    add(17, "Chrysler Capital – Deal Funding",      43_800.00, 0,         "D-0071")
    # GL-only items (checks issued, not yet cleared at bank)
    add(5,  "Check #4821 – Snap-on Tools",          0,   2_340.00,        "CHK-4821")
    add(9,  "Check #4822 – NAPA Auto Parts",        0,     891.34,        "CHK-4822")
    add(12, "Check #4823 – Cintas Corp",            0,     427.80,        "CHK-4823")

    df = pd.DataFrame(rows)
    df.to_csv(out / "gl_cash_transactions.csv", index=False)
    print(f"  gl_cash_trans: {len(df):>4} rows")


# ── main ──────────────────────────────────────────────────────────────────────

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    print("Generating fake data for Doyle Chrysler...\n")
    deals_df = gen_deals(OUT)
    gen_floorplan(OUT)
    gen_ap_invoices(OUT)
    gen_ar_aging(OUT)
    gen_schedules_and_detail(OUT, deals_df)
    gen_gl_balances(OUT)
    gen_bank_transactions(OUT)
    gen_gl_cash_transactions(OUT)
    print("\nDone — all files written to data/fake/")


if __name__ == "__main__":
    main()
