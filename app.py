"""
Simpson's Paradox in Amazon Dynamic Currency Conversion
A single-page narrative walkthrough — grounded in Brady Neal slides 5–8.
"""

import streamlit as st
import pandas as pd

from data import generate_dcc_data, get_statistics

st.set_page_config(
    page_title="Simpson's Paradox · Amazon DCC",
    page_icon="💱",
    layout="centered",
)

@st.cache_data
def load():
    df = generate_dcc_data()
    stats = get_statistics(df)
    return df, stats

df, stats = load()

mobile  = stats["strata"]["mobile"]
desktop = stats["strata"]["desktop"]

y_t1 = df.loc[df.treatment == 1, "outcome"].mean()
y_t0 = df.loc[df.treatment == 0, "outcome"].mean()

mob_t    = mobile["conversion_treated"]
mob_c    = mobile["conversion_control"]
mob_eff  = mobile["naive_effect"]
desk_t   = desktop["conversion_treated"]
desk_c   = desktop["conversion_control"]
desk_eff = desktop["naive_effect"]
total_eff = stats["naive_ate"]

pct_mob_treated  = len(df[(df.treatment==1) & (df.device=="mobile")]) / len(df[df.treatment==1])
pct_mob_control  = len(df[(df.treatment==0) & (df.device=="mobile")]) / len(df[df.treatment==0])
pct_desk_treated = 1 - pct_mob_treated
pct_desk_control = 1 - pct_mob_control

# ── Page header ───────────────────────────────────────────────────────────────
st.title("💱 Simpson's Paradox in Amazon Currency Conversion")
st.caption("A case study in why correlation isn't causation")
st.divider()

# ── Step 1: The question ──────────────────────────────────────────────────────
st.header("Step 1 — The question")
st.markdown(f"""
Amazon shows international customers a **Dynamic Currency Conversion (DCC) offer**
at checkout — an option to pay in their home currency instead of USD.

We ran an A/B test on **{stats['n']:,} customers**:
- **Treatment (T=1):** customers shown the DCC offer
- **Control (T=0):** customers not shown the offer

**Did showing the offer help or hurt checkout completion?**
""")

# ── Step 2: The Brady Neal table ──────────────────────────────────────────────
st.header("Step 2 — The full picture in one table")

st.markdown("""
Let's look at checkout rates broken out by device — the same structure as
Brady Neal's mortality table (slide 6), but for DCC:
""")

st.markdown(f"""
<style>
.bt {{
    width: 100%;
    border-collapse: collapse;
    font-size: 15px;
    margin: 12px 0 20px 0;
}}
.bt th, .bt td {{
    border: 1px solid #ccc;
    padding: 11px 16px;
    text-align: center;
}}
.bt thead th {{
    background: #f0f0f0;
    font-weight: 600;
}}
.bt .lbl {{
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
}}
.bt .total {{
    border-left: 3px solid #555;
    background: #f8f8f8;
    font-weight: 600;
}}
.bt .green {{ color: #1a7a1a; font-weight: 700; }}
.bt .red   {{ color: #cc2200; font-weight: 700; }}
</style>

<table class="bt">
  <thead>
    <tr>
      <th></th>
      <th>Mobile<br><small style="font-weight:normal">E[Y | T, C=Mobile]</small></th>
      <th>Desktop<br><small style="font-weight:normal">E[Y | T, C=Desktop]</small></th>
      <th class="total">Total (aggregate)<br><small style="font-weight:normal">E[Y | T]</small></th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="lbl">Shown DCC offer (T=1)</td>
      <td>{mob_t:.1%}</td>
      <td>{desk_t:.1%}</td>
      <td class="total">{y_t1:.1%}</td>
    </tr>
    <tr>
      <td class="lbl">Not shown DCC offer (T=0)</td>
      <td>{mob_c:.1%}</td>
      <td>{desk_c:.1%}</td>
      <td class="total">{y_t0:.1%}</td>
    </tr>
    <tr>
      <td class="lbl">Effect (T=1 minus T=0)</td>
      <td class="green">{mob_eff:+.1%} ✓</td>
      <td class="green">{desk_eff:+.1%} ✓</td>
      <td class="total red">{total_eff:+.1%} ✗</td>
    </tr>
  </tbody>
</table>
""", unsafe_allow_html=True)

st.error(
    f"**E[Y | T=1] − E[Y | T=0] = {total_eff:+.1%}** — looking only at the Total column, "
    f"DCC appears to *hurt* conversion.  \n"
    f"But within **Mobile** it helps by **{mob_eff:+.1%}**, "
    f"and within **Desktop** it helps by **{desk_eff:+.1%}**."
)

# ── Step 3: Why ──────────────────────────────────────────────────────────────
st.header("Step 3 — Why does the total reverse?")

st.markdown("""
The key is **who ends up in each group**.
Amazon pushes the DCC offer prominently on the mobile checkout screen —
so the treatment group is overwhelmingly mobile users.
Desktop users rarely see the offer, so the control group is mostly desktop.
""")

mix = pd.DataFrame({
    "": ["Shown DCC offer (T=1)", "Not shown DCC offer (T=0)"],
    "% Mobile": [f"{pct_mob_treated:.0%}", f"{pct_mob_control:.0%}"],
    "% Desktop": [f"{pct_desk_treated:.0%}", f"{pct_desk_control:.0%}"],
    "Checkout rate": [f"{y_t1:.1%}", f"{y_t0:.1%}"],
})
st.table(mix)

st.markdown(f"""
Mobile users have a **lower baseline checkout rate** ({mob_c:.1%})
than desktop users ({desk_c:.1%}) — smaller screen, more friction.

The treatment group is packed with low-converting mobile users;
the control group is packed with high-converting desktop users.
**That composition gap swamps the real DCC signal.**
""")

# ── Step 4: The paradox ───────────────────────────────────────────────────────
st.header("Step 4 — That's Simpson's Paradox")

st.markdown("""
> A trend that appears in **every subgroup** can **disappear or reverse**
> when the subgroups are combined — because the groups are mixed in unequal proportions.

Here **device type** is the confounder — it affects *both*:
- **Which customers get shown the DCC offer** (mobile users → 80% chance of seeing it)
- **Whether customers complete checkout** (mobile users → lower baseline rate)

Because device type pulls both levers at once, the aggregate comparison
E[Y | T=1] − E[Y | T=0] is contaminated. It's not measuring the effect of DCC —
it's measuring the difference between mobile and desktop shoppers.
""")

col1, col2 = st.columns(2)
col1.metric(
    "Naive E[Y|T=1] − E[Y|T=0]",
    f"{stats['naive_ate']:+.1%}",
    delta="DCC appears harmful",
    delta_color="inverse",
)
col2.metric(
    "Within each device group",
    f"+{(mob_eff + desk_eff) / 2:.1%} avg",
    delta="DCC consistently helps",
)

st.divider()
st.caption(
    "Based on Brady Neal — *A Brief Introduction to Causal Inference*, Lecture 1 · Slides 5–8"
)
