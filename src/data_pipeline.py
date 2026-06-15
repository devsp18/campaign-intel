"""
data_pipeline.py
----------------
Loads, cleans, and stores both real datasets into a SQLite database that
the SQL analysis layer queries directly.

DATA PROVENANCE (what is real, what is handled):

Dataset 1: marketing_AB.csv (Kaggle: faviovaz/marketing-ab-testing)
    A real randomized marketing experiment, 588,101 users.
    - test group: 'ad' (treatment, n=564,577) vs 'psa' (control, n=23,524).
      The 96/4 split mirrors how real marketing holdouts are designed:
      you only sacrifice a small slice of audience to measure lift.
    - converted: True/False outcome per user.
    - total ads: exposure count per user (1 to 2,065) -> frequency analysis.
    - most ads day / most ads hour: when the user saw the most ads ->
      timing analysis.
    Cleaning: column names normalized; no fabricated fields.

Dataset 2: email_campaigns.csv (Kaggle: loveall/email-campaign-management-for-sme)
    68,353 real marketing emails with content + engagement outcome.
    - Email_Status: 0 = ignored, 1 = read, 2 = acknowledged (engaged).
    - Subject_Hotness_Score (0-5), Word_Count, Total_Links, Total_Images:
      content features -> "subject lines / body length vs engagement".
    - Time_Email_sent_Category (1/2/3 = send-time bucket) -> timing.
    - Total_Past_Communications: how many prior emails the customer got
      -> frequency / fatigue analysis.
    Cleaning decisions (documented, conservative):
    - Total_Past_Communications nulls (6,825) -> filled with the median;
      a customer's history length is missing-at-random here and the
      median avoids skewing the fatigue curve.
    - Total_Links / Total_Images nulls -> median fill (small counts).
    - Customer_Location nulls (11,595) -> kept as 'Unknown' category,
      because dropping 17% of rows would bias engagement rates.
    The Kaggle 'Test' split is NOT used: it ships without the outcome
    column (it exists for competition submissions), so it cannot support
    engagement analysis.
"""

import os
import sqlite3
import pandas as pd
import numpy as np

_HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(_HERE, "..", "data")
DB_PATH = os.path.join(DATA_DIR, "campaign_intel.db")


def load_experiment() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "marketing_AB.csv"), index_col=0)
    df.columns = [c.strip().replace(" ", "_") for c in df.columns]
    # -> user_id, test_group, converted, total_ads, most_ads_day, most_ads_hour
    df["converted"] = df["converted"].astype(int)
    return df


def load_emails() -> pd.DataFrame:
    df = pd.read_csv(os.path.join(DATA_DIR, "email_campaigns.csv"))
    med_comm = df["Total_Past_Communications"].median()
    df["Total_Past_Communications"] = df["Total_Past_Communications"].fillna(med_comm)
    df["Total_Links"] = df["Total_Links"].fillna(df["Total_Links"].median())
    df["Total_Images"] = df["Total_Images"].fillna(df["Total_Images"].median())
    df["Customer_Location"] = df["Customer_Location"].fillna("Unknown")
    # engaged = read (1) or acknowledged (2)
    df["engaged"] = (df["Email_Status"] > 0).astype(int)
    df["acknowledged"] = (df["Email_Status"] == 2).astype(int)
    return df


def build_database() -> str:
    """Write both cleaned tables into SQLite for the SQL layer."""
    exp = load_experiment()
    em = load_emails()
    con = sqlite3.connect(DB_PATH)
    exp.to_sql("experiment_users", con, if_exists="replace", index=False)
    em.to_sql("email_campaigns", con, if_exists="replace", index=False)
    # Helpful indexes for the heavier queries
    cur = con.cursor()
    cur.execute("CREATE INDEX IF NOT EXISTS ix_exp_group ON experiment_users(test_group)")
    cur.execute("CREATE INDEX IF NOT EXISTS ix_em_status ON email_campaigns(Email_Status)")
    con.commit()
    con.close()
    return DB_PATH


def get_connection() -> sqlite3.Connection:
    if not os.path.exists(DB_PATH):
        build_database()
    return sqlite3.connect(DB_PATH)


def run_sql_file(name: str) -> pd.DataFrame:
    """Execute one of the repo's .sql files and return the result."""
    sql_dir = os.path.join(_HERE, "..", "sql")
    with open(os.path.join(sql_dir, name)) as f:
        query = f.read()
    con = get_connection()
    out = pd.read_sql_query(query, con)
    con.close()
    return out


if __name__ == "__main__":
    path = build_database()
    print("Database built:", path)
    con = sqlite3.connect(path)
    for t in ["experiment_users", "email_campaigns"]:
        n = pd.read_sql_query(f"SELECT COUNT(*) AS n FROM {t}", con)["n"][0]
        print(f"  {t}: {n:,} rows")
    con.close()
