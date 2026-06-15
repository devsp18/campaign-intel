# Campaign Experimentation & Engagement Intelligence Engine

**Did the campaign actually cause conversions, and what should the next send look like?**

This project measures the true incremental lift of a marketing campaign from a randomized 588,000-user experiment, then analyzes 68,000 real marketing emails to answer the operational questions that follow: which subject lines, body lengths, send times, and contact frequencies actually engage people.

**Live dashboard:** _(Streamlit link once deployed)_
**Tableau view:** _(link once published)_

---

## The two questions behind it

Marketing teams need two different kinds of answers. First, a causal one: did the campaign work at all, or would those customers have converted anyway? That requires a randomized experiment, not a dashboard. Second, an optimization one: given that it works, what content and timing choices make the next send better? This project does both, on two real datasets, and is careful never to confuse the two kinds of evidence.

## What is real

Both datasets are real public data (Kaggle), used as shipped:

**Randomized experiment** (`faviovaz/marketing-ab-testing`): 588,101 users randomly assigned to see ads (treatment, n=564,577) or a public service announcement (control, n=23,524), with a conversion outcome per user, ad exposure counts, and exposure timing. The 96/4 split mirrors how real marketing holdouts are designed.

**Email campaigns** (`loveall/email-campaign-management-for-sme`): 68,353 marketing emails with subject-line strength scores, body word counts, links/images, send-time category, the customer's prior communication count, and a three-level engagement outcome (ignored / read / acknowledged). The dataset's Kaggle "Test" split ships without the outcome column, so only the labeled split is used.

Cleaning is documented in `src/data_pipeline.py` (median fills for a small number of missing numeric fields; missing locations kept as a category rather than dropped). No fields are fabricated.

## What it does

**1. SQL layer** (`sql/`): the analysis is backed by a SQLite database and six standalone SQL queries using CTEs, window functions (NTILE, OVER), and conditional-aggregation pivots. The queries are first-class artifacts in the repo and viewable inside the dashboard, because writing complex SQL independently is the core skill this kind of work runs on.

**2. Incremental lift analysis** (`src/lift_analysis.py`): two-proportion z-test on the randomized groups with a 95% confidence interval. Result: treatment converts at 2.55% vs 1.79% control, an absolute lift of +0.77pp (+43% relative), z = 7.4, p = 1.7e-13, roughly 4,300 conversions attributable to the campaign. Lift is also split by day of week, keeping each day's own randomized control slice.

**3. Engagement and content analysis** (`src/engagement_analysis.py`): engagement by subject-line strength, body length, send-time bucket, campaign type, and prior-contact frequency, with Spearman correlations across content features.

**4. Auto-generated briefing** (`src/report.py`): a plain-English summary of the experiment result, timing pattern, content findings, and the method caveats, the artifact a stakeholder would actually read.

**5. Dashboard** (`src/app.py`): a Streamlit app with the experiment results, content findings, the fatigue curve with its caveat attached, the auto-briefing, and a browser for the SQL queries themselves.

## Headline findings

- **The campaign works:** +43% relative lift in conversion, unambiguous at p = 1.7e-13. About 4,300 of the treated group's 14,400 conversions are attributable to the ads.
- **Lift is concentrated early in the week:** Tuesday shows the strongest lift (+1.6pp); Thursday and Sunday show no statistically significant lift at all, meaning spend on those days is not measurably working.
- **Salesy subject lines backfire:** emails with the "hottest" subject scores engage at 17% versus 24% for low-hype subjects, and the deeper "acknowledged" rate falls monotonically as subject hotness rises.
- **Shorter emails win, monotonically:** 33% engagement for the shortest quintile (~350 words) versus 12% for the longest (~1,100 words).
- **Send time barely matters compared to content:** within a campaign type, engagement across the three send-time buckets moves by well under a point, while campaign type and length move it by 20+ points.

## Two traps this project names instead of falling into

**The exposure trap.** Conversion rises steeply with ad exposure (0.25% at 1-5 ads to ~17% at 121+). That curve is correlational: heavily-exposed users are more active people who were likelier to convert anyway. The only causal estimate in this data is the randomized comparison, and the dashboard labels the exposure curve accordingly.

**The fatigue trap.** Engagement versus prior-communication count is U-shaped, which looks like "more email eventually helps." It doesn't: the right side of the curve is survivorship, because unengaged customers churn off the list. A causal frequency answer would require a randomized frequency experiment, and the briefing says so.

Being explicit about what the data can and cannot prove is the point of an experimentation function.

## Run it locally

```bash
pip install -r requirements.txt
cd src
streamlit run app.py
```

## Stack

Python, pandas, SciPy, SQLite (SQL layer with CTEs and window functions), Plotly, Streamlit, Tableau.

## Note

Built as a portfolio project. Both datasets are real public data; all lift claims come from the randomized comparison, and correlational views are labeled as such.
