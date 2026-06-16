"""LLM insight generation via OpenAI API (GPT-4o)."""

import os
from openai import OpenAI

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
    return _client


def _chat(prompt: str, max_tokens: int = 400) -> str:
    client = _get_client()
    response = client.chat.completions.create(
        model="gpt-4o",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return response.choices[0].message.content


def generate_insight(stats: dict, context: str = "") -> str:
    """
    Ask GPT-4o to explain the Simpson's Paradox result in plain language.
    stats: output from data.get_statistics()
    """
    naive = stats["naive_ate"]
    adjusted = stats["adjusted_ate"]
    mobile_effect = stats["strata"]["mobile"]["naive_effect"]
    desktop_effect = stats["strata"]["desktop"]["naive_effect"]

    prompt = f"""You are a data scientist at Amazon's Currency Converter team.
Analyze these Dynamic Currency Conversion (DCC) A/B test results and explain what's happening.

RESULTS:
- Naive estimate (ignoring device type): DCC offer changes checkout rate by {naive:+.1%}
- Within mobile users only: DCC changes checkout rate by {mobile_effect:+.1%}
- Within desktop users only: DCC changes checkout rate by {desktop_effect:+.1%}
- Backdoor-adjusted causal estimate: {adjusted:+.1%}

CONFOUNDING CONTEXT:
Mobile users are shown DCC offers only {stats['strata']['mobile']['pct_treatment']:.0%} of the time
(vs {stats['strata']['desktop']['pct_treatment']:.0%} for desktop), AND mobile users have
lower baseline checkout rates ({stats['strata']['mobile']['conversion_control']:.1%} vs
{stats['strata']['desktop']['conversion_control']:.1%} for desktop without any offer).

{f"Additional context from analyst: {context}" if context else ""}

Write a brief, clear explanation (3-4 sentences) covering:
1. What Simpson's Paradox is happening here and why the naive number is misleading
2. What the backdoor-adjusted number tells us about the true causal effect of DCC
3. One concrete business recommendation

Use plain language a product manager could understand. No formulas."""

    return _chat(prompt, max_tokens=400)


def generate_segment_insight(stats: dict) -> str:
    """Generate targeting recommendations based on stratum-level results."""
    mobile = stats["strata"]["mobile"]
    desktop = stats["strata"]["desktop"]

    prompt = f"""You are a causal ML scientist advising Amazon's DCC team on customer targeting.

DCC offer uplift by device segment:
- Mobile users: {mobile['naive_effect']:+.1%} uplift (n={mobile['n']:,}, currently {mobile['pct_treatment']:.0%} shown offer)
- Desktop users: {desktop['naive_effect']:+.1%} uplift (n={desktop['n']:,}, currently {desktop['pct_treatment']:.0%} shown offer)
- Overall backdoor-adjusted ATE: {stats['adjusted_ate']:+.1%}

In 2-3 sentences, give a concrete recommendation:
- Which segment(s) should we show DCC offers to MORE?
- What is the estimated revenue opportunity?
- Any caution about segment(s) where offer may be hurting conversion?

Be direct and quantitative. No formulas."""

    return _chat(prompt, max_tokens=300)
