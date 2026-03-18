from __future__ import annotations

from collections import Counter
import re

from ..schemas import EventItem
from ..utils.json_safe import make_json_safe
from ..utils.text import fingerprint, normalise_space, slug_hash, strip_html

COUNTRY_KEYWORDS = {
    "Israel": ["israel", "israeli", "idf", "tel aviv", "jerusalem"],
    "Iran": ["iran", "iranian", "tehran", "islamic republic"],
    "Lebanon": ["lebanon", "lebanese", "beirut"],
    "Syria": ["syria", "syrian", "damascus"],
    "Iraq": ["iraq", "iraqi", "baghdad"],
    "Yemen": ["yemen", "yemeni", "sanaa", "aden"],
    "Saudi Arabia": ["saudi", "riyadh", "saudi arabia"],
    "United Arab Emirates": ["uae", "united arab emirates", "abu dhabi", "dubai"],
    "Qatar": ["qatar", "doha"],
    "Bahrain": ["bahrain", "manama"],
    "Oman": ["oman", "muscat", "gulf of oman"],
    "Egypt": ["egypt", "cairo", "suez"],
    "United States": ["u.s.", "us ", "united states", "washington", "white house", "state department", "treasury"],
    "United Kingdom": ["uk", "united kingdom", "britain", "british", "london", "gov.uk"],
}

ACTOR_KEYWORDS = {
    "IDF": ["idf", "israeli defense forces"],
    "Iran MFA": ["iran foreign ministry", "iran mfa", "ministry of foreign affairs of the islamic republic of iran"],
    "Israel MFA": ["israel mfa", "ministry of foreign affairs"],
    "Hamas": ["hamas"],
    "Hezbollah": ["hezbollah"],
    "Houthis": ["houthi", "ansarallah"],
    "U.S. Treasury": ["treasury", "ofac"],
    "UN Security Council": ["security council", "un security council", "unsc"],
    "White House": ["white house"],
    "UKMTO": ["ukmto"],
    "OFAC": ["ofac"],
}

LOCATION_KEYWORDS = {
    "Gaza": ["gaza"],
    "Strait of Hormuz": ["strait of hormuz", "hormuz"],
    "Red Sea": ["red sea"],
    "Gulf of Oman": ["gulf of oman"],
    "Arabian Gulf": ["arabian gulf", "persian gulf"],
    "Beirut": ["beirut"],
    "Tehran": ["tehran"],
    "Jerusalem": ["jerusalem"],
    "Suez": ["suez"],
}

EVENT_PATTERNS = {
    "military_strike": [r"strike", r"attack", r"airstrike", r"bombard", r"missile", r"drone"],
    "missile_or_drone_activity": [r"missile", r"drone", r"rocket", r"intercept"],
    "proxy_militia_action": [r"proxy", r"militia", r"hezbollah", r"houthi", r"hamas"],
    "ceasefire_or_truce": [r"ceasefire", r"truce", r"pause"],
    "sanctions_or_designation": [r"sanction", r"designation", r"ofac", r"asset freeze"],
    "diplomatic_statement": [r"statement", r"remarks", r"briefing", r"meeting", r"resolution"],
    "troop_movement_or_mobilisation": [r"mobil", r"troop", r"deployment", r"forces"],
    "shipping_disruption": [r"shipping", r"vessel", r"tanker", r"maritime", r"ukmto", r"strait of hormuz"],
    "oil_or_energy_issue": [r"oil", r"gas", r"refinery", r"terminal", r"energy"],
    "hostage_or_civilian_incident": [r"hostage", r"civilian", r"casualt", r"injur", r"killed"],
    "cyber_incident": [r"cyber", r"hack", r"digital disruption"],
    "border_incident": [r"border", r"cross-border"],
    "aviation_or_airspace_disruption": [r"airspace", r"flight", r"aviation", r"airport"],
    "market_policy_response": [r"waiver", r"policy", r"markets", r"stabilize", r"response"],
    "humanitarian_development": [r"humanitarian", r"aid", r"medical", r"health"],
    "intelligence_or_unverified_claim": [r"reportedly", r"claims", r"unverified", r"intelligence"],
}

EXPOSURE_PATTERNS = {
    "oil": [r"oil", r"refinery", r"petroleum", r"terminal"],
    "shipping": [r"shipping", r"vessel", r"maritime", r"strait of hormuz", r"red sea", r"tanker"],
    "equities": [r"markets", r"risk sentiment", r"stocks", r"equities"],
    "crypto": [r"crypto", r"bitcoin", r"risk sentiment"],
    "gold": [r"gold", r"safe haven"],
    "fx": [r"dollar", r"fx", r"currency", r"usd"],
}

NAVIGATION_TITLES = {
    "about us", "overview", "minister", "farsi", "فارسی", "عربی", "arabic",
    "iri flag", "iri national anthem"
}

NOISE_PATTERNS = [
    r"general guidance",
    r"user guide",
    r"faqs?",
    r"webinars? and events",
    r"threat assessment",
    r"compliance in the .* sector",
]

RELEVANCE_TERMS = {
    "middle east", "israel", "iran", "gaza", "west bank", "palestinian", "lebanon", "hezbollah",
    "houthi", "yemen", "syria", "iraq", "red sea", "hormuz", "gulf", "saudi", "qatar", "bahrain",
    "oman", "uae", "tehran", "jerusalem", "beirut", "suez", "maritime", "shipping", "tanker",
}


def _match_labels(text: str, mapping: dict[str, list[str]]) -> list[str]:
    lowered = text.lower()
    found: list[str] = []
    for label, patterns in mapping.items():
        if any(p in lowered for p in patterns):
            found.append(label)
    return sorted(set(found))


def detect_event_type(text: str) -> str:
    lowered = text.lower()
    matches = Counter()
    for event_type, patterns in EVENT_PATTERNS.items():
        for p in patterns:
            if re.search(p, lowered):
                matches[event_type] += 1
    if not matches:
        return "general_update"
    return matches.most_common(1)[0][0]


def detect_exposures(text: str) -> list[str]:
    lowered = text.lower()
    tags = []
    for label, patterns in EXPOSURE_PATTERNS.items():
        if any(re.search(p, lowered) for p in patterns):
            tags.append(label)
    return sorted(set(tags))


def clean_title(title: str) -> str:
    value = strip_html(title)
    value = re.sub(r"\s*[-–—|]\s*[^-–—|]{2,80}$", "", value)
    return normalise_space(value)


def build_summary(title: str, summary: str, event_type: str) -> str:
    body = strip_html(summary or title)
    if len(body) > 220:
        body = body[:217].rstrip() + "..."
    if event_type == "shipping_disruption":
        return f"Shipping-risk development: {body}"
    if event_type == "sanctions_or_designation":
        return f"Sanctions/policy development: {body}"
    if event_type == "military_strike":
        return f"Kinetic development: {body}"
    return body


def build_why_it_matters(event_type: str, countries: list[str], exposures: list[str], title: str) -> str:
    regional = ", ".join(countries[:3]) if countries else "the region"
    exposure_text = ", ".join(exposures) if exposures else "regional security and risk sentiment"
    if event_type == "shipping_disruption":
        return f"This matters because disruption around maritime routes can affect logistics, insurance, and energy transport across {regional}, with spillovers into {exposure_text}."
    if event_type == "sanctions_or_designation":
        return f"This matters because sanctions and designations can change funding access, trade flows, and short-horizon market behaviour linked to {exposure_text}."
    if event_type in {"military_strike", "missile_or_drone_activity", "proxy_militia_action"}:
        return f"This matters because kinetic developments can trigger retaliation windows and widen exposure across {regional}, especially for {exposure_text}."
    if event_type == "diplomatic_statement":
        return f"This matters because official signalling can precede sanctions, military moves, or deconfliction efforts affecting {exposure_text}."
    return f"This matters because it may shift the operating picture across {regional} and change near-term exposure for {exposure_text}."


def build_operational_impact(event_type: str) -> str:
    mapping = {
        "military_strike": "Expect elevated near-term retaliation risk and fast-moving information updates.",
        "missile_or_drone_activity": "Expect short-horizon alerting, interception claims, and possible airspace or navigation impacts.",
        "proxy_militia_action": "Expect risk of follow-on actions through regional proxy channels.",
        "shipping_disruption": "Expect maritime advisories, routing caution, insurance/risk-premium adjustments, and congestion effects.",
        "sanctions_or_designation": "Expect compliance, funding, and trade-workflow implications rather than immediate battlefield effects.",
        "aviation_or_airspace_disruption": "Expect route changes, delays, and potential travel/logistics friction.",
    }
    return mapping.get(event_type, "Expect incremental changes to the operating picture rather than a stand-alone decision signal.")


def build_market_impact(exposures: list[str], event_type: str) -> str:
    if not exposures:
        exposures = ["equities", "crypto", "oil"]
    joined = ", ".join(exposures)
    if event_type == "shipping_disruption":
        return f"Transmission channels: freight risk, insurance, energy transport, and broader risk-off sentiment across {joined}."
    if event_type == "sanctions_or_designation":
        return f"Transmission channels: funding restrictions, compliance friction, commodity routing, and macro risk sentiment across {joined}."
    if event_type in {"military_strike", "missile_or_drone_activity"}:
        return f"Transmission channels: safe-haven demand, oil risk premium, shipping caution, and broad risk-off spillovers across {joined}."
    return f"Transmission channels: narrative risk, policy follow-through, and broader sentiment shifts across {joined}."


def build_uncertainty(source_type: str, title: str, corroboration_count: int) -> str:
    hints = []
    if source_type == "aggregator":
        hints.append("Aggregator source; verify the underlying publisher before drawing strong conclusions.")
    if corroboration_count == 0:
        hints.append("No independent corroboration detected yet.")
    lowered = title.lower()
    if "reportedly" in lowered or "claims" in lowered:
        hints.append("Language suggests reported or disputed claims rather than settled facts.")
    if not hints:
        hints.append("Confidence is evidence-weighted, not absolute; monitor for follow-up reporting.")
    return " ".join(hints)


def is_relevant_item(raw: dict) -> bool:
    title = clean_title(raw.get("title", ""))
    summary = strip_html(raw.get("summary", ""))
    link = normalise_space(raw.get("url", ""))
    combined = f"{title} {summary}".lower()

    if len(title) < 4 or not link:
        return False
    if title.lower() in NAVIGATION_TITLES:
        return False
    if link.lower().startswith("javascript:") or link.lower() in {"#", "javascript:void(0);"}:
        return False
    if any(re.search(pattern, combined) for pattern in NOISE_PATTERNS):
        return False

    relevance_hits = sum(1 for term in RELEVANCE_TERMS if term in combined)
    countries = _match_labels(combined, COUNTRY_KEYWORDS)
    actors = _match_labels(combined, ACTOR_KEYWORDS)
    locations = _match_labels(combined, LOCATION_KEYWORDS)
    exposures = detect_exposures(combined)
    event_type = detect_event_type(combined)

    if relevance_hits >= 1:
        return True
    if countries or actors or locations:
        return True
    if exposures and event_type != "general_update":
        return True
    return False


def normalize_raw_item(raw: dict) -> EventItem:
    title = clean_title(raw.get("title", ""))
    summary = strip_html(raw.get("summary", ""))
    combined = normalise_space(f"{title} {summary}")
    countries = _match_labels(combined, COUNTRY_KEYWORDS)
    actors = _match_labels(combined, ACTOR_KEYWORDS)
    locations = _match_labels(combined, LOCATION_KEYWORDS)
    event_type = detect_event_type(combined)
    exposures = detect_exposures(combined)
    uid = slug_hash(f"{raw.get('source')}|{title}|{raw.get('url')}")
    fp = fingerprint(combined, countries + actors + locations + exposures + [event_type])
    published_at = raw.get("published_at_utc")
    detected_time = raw.get("detected_event_time_utc") or published_at
    return EventItem(
        event_uid=uid,
        title=title,
        source=raw.get("source", "unknown"),
        source_type=raw.get("source_type", "unknown"),
        url=raw.get("url", ""),
        published_at_utc=published_at,
        detected_event_time_utc=detected_time,
        countries_involved=countries,
        actors_involved=actors,
        locations=locations,
        event_type=event_type,
        asset_exposure_tags=exposures,
        summary=build_summary(title, summary, event_type),
        why_it_matters=build_why_it_matters(event_type, countries, exposures, title),
        operational_impact=build_operational_impact(event_type),
        market_impact=build_market_impact(exposures, event_type),
        uncertainty_notes=build_uncertainty(raw.get("source_type", "unknown"), title, 0),
        raw_text=combined,
        raw_payload=make_json_safe(raw),
        fingerprint=fp,
    )
