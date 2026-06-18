from pathlib import Path
import os
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FAKE_DATA_DIR = DATA_DIR / "fake"
REPORTS_DIR = BASE_DIR / "reports"

DEALERSHIP_NAME = os.getenv("DEALERSHIP_NAME", "Doyle Chrysler")
DATA_SOURCE     = os.getenv("DATA_SOURCE", "fake")

EMAIL_SENDER   = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
SMTP_SERVER    = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT      = int(os.getenv("SMTP_PORT", "587"))

FLOORPLAN_RATE             = 0.0825
FLOORPLAN_RATE_USED        = 0.0925
FLOORPLAN_LENDER           = "Chrysler Capital Floorplan"
FLOORPLAN_CURTAILMENT_DAYS = 180

SCHEDULE_AGE_WARNING  = 30
SCHEDULE_AGE_CRITICAL = 60

CASH_LOW_THRESHOLD = 50_000
AP_OVERDUE_WARNING = 15
AP_OVERDUE_CRITICAL = 30

DEPARTMENTS = ["New Vehicle", "Used Vehicle", "F&I", "Service", "Parts", "Body Shop"]

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
