"""
engagement_analysis.py
----------------------
The content/timing/frequency module on 68,353 real marketing emails.
Answers the JD's questions directly: how do subject lines, body length,
send timing, and communication frequency relate to engagement?

Honest method notes:

1. Engagement definition: Email_Status > 0 (read or acknowledged).
   "Acknowledged" (status 2) tracked separately as the deeper-action rate.

2. The frequency "fatigue" curve is U-shaped and that is NOT a causal
   fatigue story: customers with many past communications are self-
   selected engaged customers (the unengaged churn off the list), which
   is survivorship bias. We present the curve with that caveat; the dip
   in the low-teens band is the closest thing to a fatigue signal, and a
   proper causal answer would need a randomized frequency experiment.

3. Subject_Hotness_Score is the dataset's own 0-5 subject-line strength
   measure; Word_Count is body length. Both real fields.
"""

import numpy as np
import pandas as pd
from scipy import stats

from data_pipeline import load_emails, run_sql_file


def engagement_by_subject_strength() -> pd.DataFrame:
    em = load_emails()
    bins = [0, 1, 2, 3, 6]
    labels = ["Low (0-1)", "Mid (1-2)", "High (2-3)", "Very High (3+)"]
    em["subject_strength"] = pd.cut(em["Subject_Hotness_Score"], bins=bins,
                                    labels=labels, include_lowest=True)
    out = em.groupby("subject_strength", observed=True).agg(
        emails=("engaged", "size"),
        engagement_pct=("engaged", lambda s: s.mean() * 100),
        acknowledged_pct=("acknowledged", lambda s: s.mean() * 100),
    ).round(2).reset_index()
    return out


def engagement_by_wordcount() -> pd.DataFrame:
    em = load_emails()
    em["wc_band"] = pd.qcut(em["Word_Count"], q=5,
                            labels=["Shortest", "Short", "Medium", "Long", "Longest"])
    out = em.groupby("wc_band", observed=True).agg(
        emails=("engaged", "size"),
        median_words=("Word_Count", "median"),
        engagement_pct=("engaged", lambda s: s.mean() * 100),
    ).round(2).reset_index()
    return out


def engagement_by_send_time() -> pd.DataFrame:
    return run_sql_file("06_campaign_type_time.sql")


def fatigue_curve() -> pd.DataFrame:
    return run_sql_file("05_fatigue_curve.sql")


def content_correlations() -> pd.DataFrame:
    """Spearman correlations of content features vs engagement.
    Spearman (not Pearson) because the relationships are monotonic-ish
    but not linear, and features are skewed."""
    em = load_emails()
    feats = ["Subject_Hotness_Score", "Word_Count", "Total_Links",
             "Total_Images", "Total_Past_Communications"]
    rows = []
    for f in feats:
        rho, p = stats.spearmanr(em[f], em["engaged"])
        rows.append({"feature": f, "spearman_rho": round(rho, 4),
                     "p_value": f"{p:.1e}", "significant": p < 0.05})
    return pd.DataFrame(rows).sort_values("spearman_rho", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    print("=== ENGAGEMENT BY SUBJECT STRENGTH ===")
    print(engagement_by_subject_strength().to_string(index=False))
    print("\n=== ENGAGEMENT BY BODY LENGTH ===")
    print(engagement_by_wordcount().to_string(index=False))
    print("\n=== CONTENT FEATURE CORRELATIONS (Spearman) ===")
    print(content_correlations().to_string(index=False))
    print("\n=== FATIGUE CURVE (see survivorship caveat) ===")
    print(fatigue_curve().to_string(index=False))
    print("\n=== CAMPAIGN TYPE x SEND TIME ===")
    print(engagement_by_send_time().to_string(index=False))
