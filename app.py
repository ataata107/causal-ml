"""
Simpson's Paradox in Amazon Dynamic Currency Conversion
A single-page narrative walkthrough — grounded in Brady Neal slides 5–8.
"""

import streamlit as st
import pandas as pd

from data import generate_dcc_data, get_statistics, generate_rct_data, get_rct_statistics

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

@st.cache_data
def load_rct():
    df_rct = generate_rct_data()
    rct_stats = get_rct_statistics(df_rct)
    return df_rct, rct_stats

df, stats = load()
df_rct, rct_stats = load_rct()

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

# ── Step 5: RCT Solution ──────────────────────────────────────────────────────
st.header("Step 5 — Solution 1: Run a Randomized Controlled Trial (RCT)")

st.markdown("""
The root problem was that **device type determined who got treated**.
Mobile users were 8× more likely to see the DCC offer than desktop users.

An RCT breaks this link by **randomly assigning** treatment — flip a coin for each
customer, regardless of their device. Now the treatment group and control group
have the same mix of mobile and desktop users, so device type can't confound the result.
""")

rct_mob = rct_stats["strata"]["mobile"]
rct_desk = rct_stats["strata"]["desktop"]

st.markdown(f"""
<table class="bt">
  <thead>
    <tr>
      <th></th>
      <th>Mobile</th>
      <th>Desktop</th>
      <th class="total">% Mobile in group</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td class="lbl">Shown DCC offer (T=1)</td>
      <td>{rct_mob['conversion_treated']:.1%}</td>
      <td>{rct_desk['conversion_treated']:.1%}</td>
      <td class="total">{rct_mob['n'] * rct_mob['pct_treatment'] / (rct_mob['n'] * rct_mob['pct_treatment'] + rct_desk['n'] * rct_desk['pct_treatment']):.0%} mobile</td>
    </tr>
    <tr>
      <td class="lbl">Not shown DCC offer (T=0)</td>
      <td>{rct_mob['conversion_control']:.1%}</td>
      <td>{rct_desk['conversion_control']:.1%}</td>
      <td class="total">{rct_mob['n'] * (1 - rct_mob['pct_treatment']) / (rct_mob['n'] * (1 - rct_mob['pct_treatment']) + rct_desk['n'] * (1 - rct_desk['pct_treatment'])):.0%} mobile</td>
    </tr>
  </tbody>
</table>
""", unsafe_allow_html=True)

st.markdown("""
Both groups are now ~60% mobile / 40% desktop — the same population mix.
The low-converting mobile users are spread **equally** across treatment and control,
so they no longer drag down only one side.
""")

col1, col2, col3 = st.columns(3)
col1.metric("RCT estimate E[Y|T=1] − E[Y|T=0]", f"{rct_stats['naive_ate']:+.1%}", delta="unbiased")
col2.metric("True ATE (ground truth)", f"{rct_stats['true_ate']:+.1%}")
col3.metric("Gap (bias)", f"{rct_stats['naive_ate'] - rct_stats['true_ate']:+.1%}", delta="near zero")

st.success(
    "With randomization, **E[Y | T=1] − E[Y | T=0] = E[Y(1)] − E[Y(0)]** — "
    "the observational difference equals the causal effect because "
    "treatment is independent of all confounders by design."
)

st.markdown("""
**Why this works (the math):**

When treatment T is randomized, T is independent of device W.
So within T=1, the distribution of W matches the overall population — same as T=0.
The composition effect disappears, and the naive difference becomes causal.
""")

st.divider()

# ── Step 6: Backdoor Adjustment ───────────────────────────────────────────────
st.header("Step 6 — Solution 2: Backdoor Adjustment (no RCT needed)")

st.markdown("""
RCTs are expensive and sometimes impossible. What if we're stuck with the original
observational data where mobile users were shown DCC offers more often?

The **backdoor adjustment formula** lets us recover the true causal effect from
observational data — as long as we've measured the confounders.

The formula is:

$$E[Y(t)] = \\sum_w P(W = w) \\cdot E[Y \\mid T = t,\\, W = w]$$

Instead of using the treatment group's device mix (which is distorted), we
re-weight using the **population's** device mix.
""")

st.markdown("**Step-by-step calculation on our data:**")

w_mobile  = (df["device"] == "mobile").mean()
w_desktop = (df["device"] == "desktop").mean()

mob_t1 = mobile["conversion_treated"]
mob_t0 = mobile["conversion_control"]
desk_t1 = desktop["conversion_treated"]
desk_t0 = desktop["conversion_control"]

ey1_adj = w_mobile * mob_t1 + w_desktop * desk_t1
ey0_adj = w_mobile * mob_t0 + w_desktop * desk_t0
backdoor_ate = ey1_adj - ey0_adj

steps_df = pd.DataFrame({
    "": [
        "Population weight P(W=w)",
        "E[Y | T=1, W=w]",
        "E[Y | T=0, W=w]",
        "Weighted contribution to E[Y(1)]",
        "Weighted contribution to E[Y(0)]",
    ],
    "Mobile (W=mobile)": [
        f"{w_mobile:.0%}",
        f"{mob_t1:.1%}",
        f"{mob_t0:.1%}",
        f"{w_mobile:.0%} × {mob_t1:.1%} = {w_mobile * mob_t1:.1%}",
        f"{w_mobile:.0%} × {mob_t0:.1%} = {w_mobile * mob_t0:.1%}",
    ],
    "Desktop (W=desktop)": [
        f"{w_desktop:.0%}",
        f"{desk_t1:.1%}",
        f"{desk_t0:.1%}",
        f"{w_desktop:.0%} × {desk_t1:.1%} = {w_desktop * desk_t1:.1%}",
        f"{w_desktop:.0%} × {desk_t0:.1%} = {w_desktop * desk_t0:.1%}",
    ],
})
st.table(steps_df)

st.markdown(f"""
$$E[Y(1)] = {w_mobile:.0%} \\times {mob_t1:.1%} + {w_desktop:.0%} \\times {desk_t1:.1%} = {ey1_adj:.1%}$$

$$E[Y(0)] = {w_mobile:.0%} \\times {mob_t0:.1%} + {w_desktop:.0%} \\times {desk_t0:.1%} = {ey0_adj:.1%}$$

$$\\text{{ATE}} = E[Y(1)] - E[Y(0)] = {ey1_adj:.1%} - {ey0_adj:.1%} = {backdoor_ate:+.1%}$$
""")

st.divider()
st.subheader("All three estimates side by side")

col1, col2, col3 = st.columns(3)
col1.metric(
    "Naive E[Y|T=1] − E[Y|T=0]",
    f"{stats['naive_ate']:+.1%}",
    delta="confounded — wrong sign",
    delta_color="inverse",
)
col2.metric(
    "Backdoor adjusted ATE",
    f"{backdoor_ate:+.1%}",
    delta="causal — correct",
)
col3.metric(
    "True ATE (ground truth)",
    f"{stats['true_ate']:+.1%}",
    delta="sim only",
)

st.info("""
**Key insight:** The naive estimate was negative because the treatment group
was flooded with low-converting mobile users. The backdoor adjustment uses
the *population* device mix instead of the *treatment group* device mix —
giving each subgroup its fair weight and recovering the true causal effect.
""")

st.divider()
st.caption(
    "Based on Brady Neal — *A Brief Introduction to Causal Inference*, Lecture 1 · Slides 5–25"
)
