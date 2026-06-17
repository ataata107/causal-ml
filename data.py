"""
Synthetic DCC checkout data with a built-in confounder (device type).

Story:
  Mobile users:  get shown DCC offers LESS (Amazon UX decision)
                 AND convert LESS (smaller screen friction)
  Desktop users: get shown DCC offers MORE
                 AND convert MORE (easier checkout)

This makes device type a BACKDOOR path:
  Device → Treatment (shown DCC)
  Device → Outcome  (checkout completion)

Result: naive E[Y|T=1] - E[Y|T=0] is NEGATIVE (DCC looks bad)
        backdoor-adjusted E[Y|do(T=1)] - E[Y|do(T=0)] is POSITIVE (DCC actually helps)
        — classic Simpson's Paradox from Brady Neal Lecture 1
"""

import numpy as np
import pandas as pd

SEED = 42
N = 5_000


def generate_dcc_data(n: int = N, seed: int = SEED) -> pd.DataFrame:
    rng = np.random.default_rng(seed)

    # --- Confounder: device type ---
    # 60% mobile, 40% desktop (realistic Amazon traffic split)
    device = rng.choice(["mobile", "desktop"], size=n, p=[0.60, 0.40])
    is_mobile = (device == "mobile").astype(int)

    # --- Additional features (not confounders, just features) ---
    country = rng.choice(
        ["US", "UK", "DE", "JP", "IN", "BR"],
        size=n,
        p=[0.30, 0.15, 0.15, 0.15, 0.15, 0.10],
    )
    basket_value = rng.lognormal(mean=3.5, sigma=0.8, size=n).clip(5, 500)
    account_age_days = rng.integers(1, 3650, size=n)
    is_returning = (account_age_days > 180).astype(int)
    fx_volatility = rng.uniform(0.01, 0.25, size=n)

    # --- Treatment: P(shown DCC | device) ---
    # Mobile: 70% shown DCC offer (Amazon pushes DCC on mobile checkout screens)
    # Desktop: 20% shown DCC offer (desktop users see more checkout options, DCC is buried)
    # → treatment group is dominated by low-converting mobile users
    # → control group is dominated by high-converting desktop users
    # → naive estimate looks NEGATIVE even though DCC helps within each group
    p_treatment = np.where(is_mobile, 0.80, 0.10)
    treatment = rng.binomial(1, p_treatment, size=n)

    # --- Potential outcomes ---
    # Base conversion rate:  mobile 12%, desktop 35%
    base_rate = np.where(is_mobile, 0.12, 0.35)

    # Causal effect of DCC offer: +8% for all customers (true ATE = 0.08)
    # Heterogeneous bumps: unfamiliar currency countries get more lift
    unfamiliar = np.isin(country, ["JP", "IN", "BR"]).astype(float) * 0.04
    high_basket = (basket_value > 100).astype(float) * 0.03

    causal_effect = 0.08 + unfamiliar + high_basket  # ITE per customer

    p_y1 = (base_rate + causal_effect).clip(0, 1)   # Y(1) — if shown offer
    p_y0 = base_rate.clip(0, 1)                      # Y(0) — if not shown

    y1 = rng.binomial(1, p_y1, size=n)
    y0 = rng.binomial(1, p_y0, size=n)

    # Observed outcome (we see only one potential outcome per customer)
    outcome = np.where(treatment == 1, y1, y0)

    df = pd.DataFrame(
        {
            "customer_id": np.arange(n),
            "device": device,
            "country": country,
            "basket_value": basket_value.round(2),
            "account_age_days": account_age_days,
            "is_returning": is_returning,
            "fx_volatility": fx_volatility.round(4),
            "treatment": treatment,         # T: 1 = shown DCC offer
            "outcome": outcome,             # Y: 1 = completed checkout
            # Ground truth (not available in real data — only for lecture demo)
            "_y1": y1,
            "_y0": y0,
            "_ite": y1 - y0,               # Individual Treatment Effect
        }
    )
    return df


def get_statistics(df: pd.DataFrame) -> dict:
    """Key numbers for the Simpson's Paradox story."""
    # Naive estimate (ignores confounding)
    y_t1 = df.loc[df.treatment == 1, "outcome"].mean()
    y_t0 = df.loc[df.treatment == 0, "outcome"].mean()
    naive_ate = y_t1 - y_t0

    # Backdoor adjustment: E[Y|do(T)] = sum_W P(W) * E[Y|T,W]
    groups = df.groupby(["device", "treatment"])["outcome"].mean().unstack("treatment")
    weights = df["device"].value_counts(normalize=True)

    adjusted_ate = sum(
        weights[dev] * (groups.loc[dev, 1] - groups.loc[dev, 0])
        for dev in weights.index
    )

    # True ATE from potential outcomes (only possible in simulation)
    true_ate = (df["_y1"] - df["_y0"]).mean()

    # Stratum-level naive estimates
    strata = {}
    for dev in ["mobile", "desktop"]:
        sub = df[df.device == dev]
        strata[dev] = {
            "n": len(sub),
            "pct_treatment": sub.treatment.mean(),
            "conversion_treated": sub.loc[sub.treatment == 1, "outcome"].mean(),
            "conversion_control": sub.loc[sub.treatment == 0, "outcome"].mean(),
            "naive_effect": (
                sub.loc[sub.treatment == 1, "outcome"].mean()
                - sub.loc[sub.treatment == 0, "outcome"].mean()
            ),
        }

    return {
        "n": len(df),
        "pct_treated": df.treatment.mean(),
        "overall_conversion": df.outcome.mean(),
        "naive_ate": naive_ate,
        "adjusted_ate": adjusted_ate,
        "true_ate": true_ate,
        "strata": strata,
    }


def generate_rct_data(n: int = N, seed: int = SEED) -> pd.DataFrame:
    """Same DGP as generate_dcc_data but treatment is randomly assigned (50/50).
    Breaks the device→treatment backdoor path — T is now independent of W."""
    rng = np.random.default_rng(seed + 1)

    device = rng.choice(["mobile", "desktop"], size=n, p=[0.60, 0.40])
    is_mobile = (device == "mobile").astype(int)

    country = rng.choice(
        ["US", "UK", "DE", "JP", "IN", "BR"],
        size=n,
        p=[0.30, 0.15, 0.15, 0.15, 0.15, 0.10],
    )
    basket_value = rng.lognormal(mean=3.5, sigma=0.8, size=n).clip(5, 500)
    account_age_days = rng.integers(1, 3650, size=n)
    fx_volatility = rng.uniform(0.01, 0.25, size=n)

    # Random assignment — treatment is independent of device
    treatment = rng.binomial(1, 0.5, size=n)

    base_rate = np.where(is_mobile, 0.12, 0.35)
    unfamiliar = np.isin(country, ["JP", "IN", "BR"]).astype(float) * 0.04
    high_basket = (basket_value > 100).astype(float) * 0.03
    causal_effect = 0.08 + unfamiliar + high_basket

    p_y1 = (base_rate + causal_effect).clip(0, 1)
    p_y0 = base_rate.clip(0, 1)

    y1 = rng.binomial(1, p_y1, size=n)
    y0 = rng.binomial(1, p_y0, size=n)
    outcome = np.where(treatment == 1, y1, y0)

    return pd.DataFrame({
        "customer_id": np.arange(n),
        "device": device,
        "country": country,
        "basket_value": basket_value.round(2),
        "account_age_days": account_age_days,
        "fx_volatility": fx_volatility.round(4),
        "treatment": treatment,
        "outcome": outcome,
        "_y1": y1,
        "_y0": y0,
        "_ite": y1 - y0,
    })


def get_rct_statistics(df_rct: pd.DataFrame) -> dict:
    """Stats for the RCT dataset — naive estimate is now unbiased."""
    y_t1 = df_rct.loc[df_rct.treatment == 1, "outcome"].mean()
    y_t0 = df_rct.loc[df_rct.treatment == 0, "outcome"].mean()
    naive_ate = y_t1 - y_t0
    true_ate = (df_rct["_y1"] - df_rct["_y0"]).mean()

    strata = {}
    for dev in ["mobile", "desktop"]:
        sub = df_rct[df_rct.device == dev]
        strata[dev] = {
            "n": len(sub),
            "pct_treatment": sub.treatment.mean(),
            "conversion_treated": sub.loc[sub.treatment == 1, "outcome"].mean(),
            "conversion_control": sub.loc[sub.treatment == 0, "outcome"].mean(),
        }

    return {
        "naive_ate": naive_ate,
        "true_ate": true_ate,
        "strata": strata,
    }


if __name__ == "__main__":
    df = generate_dcc_data()
    stats = get_statistics(df)
    print(f"Naive ATE    : {stats['naive_ate']:+.3f}  (biased by confounder)")
    print(f"Adjusted ATE : {stats['adjusted_ate']:+.3f}  (backdoor adjustment)")
    print(f"True ATE     : {stats['true_ate']:+.3f}  (ground truth, sim only)")
