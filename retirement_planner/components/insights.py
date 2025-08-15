from typing import Dict


def _openai_insight(prompt: str) -> str | None:
    """Attempt to query OpenAI for an insight. Returns None on failure."""
    try:
        from openai import OpenAI  # type: ignore
        client = OpenAI()
        resp = client.responses.create(model="gpt-4o-mini", input=prompt)
        # Access unified text output helper
        text = getattr(resp, "output_text", None)
        if text:
            return text.strip()
    except Exception:
        return None
    return None


def generate_insights(results: Dict) -> str:
    """Return a short AI-style insight about simulation results.

    Attempts to use OpenAI when an API key is configured; otherwise falls back
    to a simple rule-based message so the app works offline and in tests.
    """
    success = float(results.get("success_probability", 0.0))
    median_net = float(results.get("median_terminal", 0.0))
    ages = results.get("ages", [])
    last_age = ages[-1] if ages else "end"

    prompt = (
        "You are a financial planning assistant. Provide a concise insight "
        "(one or two sentences) about this retirement plan. "
        f"Success probability: {success*100:.1f}%. "
        f"Median terminal net worth: ${median_net:,.0f} at age {last_age}."
    )
    # Try OpenAI first
    text = _openai_insight(prompt)
    if text:
        return text

    # Fallback heuristic
    if success >= 0.85:
        outlook = "high chance of success"
    elif success >= 0.6:
        outlook = "moderate chance of success"
    else:
        outlook = "plan may be at risk"
    return (
        f"Your plan has a {outlook}. Median projected net worth at age {last_age} "
        f"is ${median_net:,.0f}."
    )
