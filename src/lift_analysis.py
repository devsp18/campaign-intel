"""
lift_analysis.py
----------------
The experimentation module. Answers: did the ad campaign cause more
conversions than the control, by how much, and is it statistically real?

Method notes an interviewer will probe, with the answers:

1. Why a two-proportion z-test?
   The outcome is binary (converted or not) across two independent
   groups. With n in the hundreds of thousands, the normal approximation
   is exact for practical purposes. We report z, p, and a 95% CI on the
   absolute lift.

2. Why is the control only 4% of users?
   That's how real marketing holdouts work: you sacrifice the smallest
   audience slice that still gives statistical power. With 23,524 control
   users, power is more than adequate for the observed effect.

3. The exposure-conversion trap (IMPORTANT):
   Conversion rises steeply with ad exposure (0.25% at 1-5 ads vs ~17%
   at 121+). This is NOT causal: heavily-exposed users are more active
   people who were likelier to convert anyway (selection/confounding).
   The ONLY causal estimate in this data is the randomized ad-vs-psa
   comparison. We show the exposure curve because it's operationally
   interesting, and we label it correlational, explicitly.
"""

import numpy as np
import pandas as pd
from scipy import stats

from data_pipeline import load_experiment, run_sql_file


def two_proportion_ztest(conv_t, n_t, conv_c, n_c):
    """Two-proportion z-test + 95% CI for the difference (treatment - control)."""
    p_t, p_c = conv_t / n_t, conv_c / n_c
    p_pool = (conv_t + conv_c) / (n_t + n_c)
    se_pool = np.sqrt(p_pool * (1 - p_pool) * (1 / n_t + 1 / n_c))
    z = (p_t - p_c) / se_pool
    p_value = 2 * (1 - stats.norm.cdf(abs(z)))
    # CI uses unpooled SE (standard for the difference estimate)
    se_diff = np.sqrt(p_t * (1 - p_t) / n_t + p_c * (1 - p_c) / n_c)
    ci_low = (p_t - p_c) - 1.96 * se_diff
    ci_high = (p_t - p_c) + 1.96 * se_diff
    return {
        "treatment_rate": p_t, "control_rate": p_c,
        "abs_lift": p_t - p_c, "rel_lift": (p_t - p_c) / p_c,
        "z": z, "p_value": p_value,
        "ci95_low": ci_low, "ci95_high": ci_high,
    }


def run_lift_analysis() -> dict:
    df = load_experiment()
    g = df.groupby("test_group")["converted"].agg(["sum", "count"])
    res = two_proportion_ztest(
        g.loc["ad", "sum"], g.loc["ad", "count"],
        g.loc["psa", "sum"], g.loc["psa", "count"],
    )

    # Incremental conversions attributable to the campaign:
    # treated users x absolute lift.
    incremental = res["abs_lift"] * g.loc["ad", "count"]
    res["incremental_conversions"] = incremental
    res["n_treatment"] = int(g.loc["ad", "count"])
    res["n_control"] = int(g.loc["psa", "count"])
    return res


def lift_by_day() -> pd.DataFrame:
    """Treatment-vs-control lift split by most-ads day. Each day keeps its
    own control slice, so the comparison stays randomized within day."""
    df = load_experiment()
    rows = []
    for day, grp in df.groupby("most_ads_day"):
        g = grp.groupby("test_group")["converted"].agg(["sum", "count"])
        if "psa" not in g.index or g.loc["psa", "count"] < 500:
            continue
        r = two_proportion_ztest(
            g.loc["ad", "sum"], g.loc["ad", "count"],
            g.loc["psa", "sum"], g.loc["psa", "count"],
        )
        rows.append({
            "day": day,
            "treatment_pct": r["treatment_rate"] * 100,
            "control_pct": r["control_rate"] * 100,
            "abs_lift_pp": r["abs_lift"] * 100,
            "significant": r["p_value"] < 0.05,
        })
    order = ["Monday", "Tuesday", "Wednesday", "Thursday",
             "Friday", "Saturday", "Sunday"]
    out = pd.DataFrame(rows)
    out["day"] = pd.Categorical(out["day"], categories=order, ordered=True)
    return out.sort_values("day").reset_index(drop=True)


def exposure_curve() -> pd.DataFrame:
    """Correlational exposure curve (explicitly NOT causal; see header)."""
    out = run_sql_file("02_lift_by_exposure_band.sql")
    order = ["01-05", "06-15", "16-30", "31-60", "61-120", "121+"]
    out["exposure_band"] = pd.Categorical(out["exposure_band"],
                                          categories=order, ordered=True)
    return out.sort_values("exposure_band").reset_index(drop=True)


if __name__ == "__main__":
    res = run_lift_analysis()
    print("=== INCREMENTAL LIFT (randomized experiment) ===")
    print(f"  treatment: {res['treatment_rate']*100:.3f}%  (n={res['n_treatment']:,})")
    print(f"  control:   {res['control_rate']*100:.3f}%  (n={res['n_control']:,})")
    print(f"  abs lift:  +{res['abs_lift']*100:.3f}pp  "
          f"(95% CI {res['ci95_low']*100:.3f} to {res['ci95_high']*100:.3f}pp)")
    print(f"  rel lift:  +{res['rel_lift']*100:.1f}%")
    print(f"  z = {res['z']:.2f}, p = {res['p_value']:.2e}")
    print(f"  incremental conversions attributable: {res['incremental_conversions']:,.0f}")
    print("\n=== LIFT BY DAY ===")
    print(lift_by_day().to_string(index=False))
    print("\n=== EXPOSURE CURVE (correlational, see notes) ===")
    print(exposure_curve().to_string(index=False))
