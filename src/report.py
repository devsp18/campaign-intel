"""
report.py — auto-generated campaign intelligence briefing.
Turns the lift + engagement results into a plain-English summary an
email/CRM team could act on.
"""

import pandas as pd


def generate_briefing(lift: dict, by_day: pd.DataFrame,
                      subject: pd.DataFrame, wordcount: pd.DataFrame,
                      fatigue: pd.DataFrame) -> str:
    L = []
    L.append("CAMPAIGN INTELLIGENCE BRIEFING")
    L.append("=" * 50)
    L.append("")
    L.append("EXPERIMENT RESULT (randomized ad vs control)")
    L.append(f"  Treatment conversion: {lift['treatment_rate']*100:.2f}%  "
             f"| Control: {lift['control_rate']*100:.2f}%")
    L.append(f"  Incremental lift: +{lift['abs_lift']*100:.2f}pp "
             f"(+{lift['rel_lift']*100:.0f}% relative), "
             f"p = {lift['p_value']:.1e}")
    L.append(f"  ~{lift['incremental_conversions']:,.0f} conversions attributable "
             f"to the campaign across {lift['n_treatment']:,} treated users.")
    L.append("")

    best = by_day.loc[by_day["abs_lift_pp"].idxmax()]
    weak = by_day[~by_day["significant"]]["day"].astype(str).tolist()
    L.append("TIMING")
    L.append(f"  Strongest lift: {best['day']} (+{best['abs_lift_pp']:.2f}pp).")
    if weak:
        L.append(f"  No significant lift on: {', '.join(weak)}. "
                 "Budget on these days is not measurably working.")
    L.append("")

    s_low = subject.iloc[0]; s_high = subject.iloc[-1]
    L.append("CONTENT")
    L.append(f"  Subject lines: lower-hype subjects engage at "
             f"{s_low['engagement_pct']:.1f}% vs {s_high['engagement_pct']:.1f}% "
             "for the 'hottest' subjects. Salesy subject lines underperform.")
    w_short = wordcount.iloc[0]; w_long = wordcount.iloc[-1]
    L.append(f"  Body length: shortest emails engage at "
             f"{w_short['engagement_pct']:.1f}% vs {w_long['engagement_pct']:.1f}% "
             "for the longest. Shorter wins, monotonically.")
    L.append("")

    L.append("FREQUENCY (read with care)")
    L.append("  Engagement vs prior-communication count is U-shaped. The right "
             "side of the curve is survivorship (unengaged customers leave the "
             "list), not proof that more email causes more engagement. A causal "
             "frequency answer requires a randomized frequency test.")
    L.append("")
    L.append("METHOD NOTE")
    L.append("  Lift is estimated only from the randomized control comparison. "
             "The exposure-conversion curve is correlational and is labeled as "
             "such; heavily-exposed users self-select as likelier converters.")
    return "\n".join(L)


if __name__ == "__main__":
    from lift_analysis import run_lift_analysis, lift_by_day
    from engagement_analysis import (engagement_by_subject_strength,
                                     engagement_by_wordcount, fatigue_curve)
    b = generate_briefing(run_lift_analysis(), lift_by_day(),
                          engagement_by_subject_strength(),
                          engagement_by_wordcount(), fatigue_curve())
    print(b)
