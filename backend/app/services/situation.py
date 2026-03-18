from __future__ import annotations

from collections import Counter

from ..schemas import ClusterItem, SituationSummary


def build_situation(clusters: list[ClusterItem]) -> SituationSummary:
    recent = clusters[:12]
    if not recent:
        return SituationSummary(
            label="Fragmented / uncertain information environment",
            rationale="No recent clustered events are available yet. Run ingestion or wait for the next refresh cycle.",
            confidence="Low confidence",
            watchlist_scheduled=[],
            watchlist_inferred=[],
            market_transmission=[],
        )

    kinetic = sum(1 for c in recent if c.event_type in {"military_strike", "missile_or_drone_activity", "proxy_militia_action"})
    shipping = sum(1 for c in recent if c.event_type == "shipping_disruption")
    sanctions = sum(1 for c in recent if c.event_type == "sanctions_or_designation")
    diplomacy = sum(1 for c in recent if c.event_type == "diplomatic_statement")
    high_conf = sum(1 for c in recent if c.confidence_band in {"High confidence", "Moderate confidence"})
    critical = sum(1 for c in recent if c.materiality_band == "Critical")

    if kinetic >= 3 or critical >= 2:
        label = "Rising kinetic risk"
        rationale = "Recent high-materiality kinetic developments dominate the picture, implying elevated follow-on risk over the next 6–24 hours."
    elif shipping >= 2 and kinetic >= 1:
        label = "Elevated but contained tension"
        rationale = "The operating picture shows meaningful security and shipping strain, but not enough evidence yet for a cleaner regime shift beyond elevated tension."
    elif sanctions >= 2 and kinetic == 0:
        label = "Economically significant but militarily limited"
        rationale = "Policy, sanctions, and market-relevant restrictions are prominent without equivalent evidence of widening kinetic activity."
    elif diplomacy >= max(kinetic, 1):
        label = "Diplomatically active but operationally mixed"
        rationale = "Official signalling is active, but operational implications remain mixed and should be treated cautiously until corroborated."
    else:
        label = "Fragmented / uncertain information environment"
        rationale = "The feed contains multiple developments, but the evidence does not yet support a cleaner higher-confidence regime label."

    confidence = "Moderate confidence" if high_conf >= max(2, len(recent) // 3) else "Low confidence"

    scheduled = []
    inferred = []
    transmission = []

    for c in recent[:8]:
        lower = (c.canonical_title + " " + c.summary).lower()
        if any(k in lower for k in ["meeting", "briefing", "statement", "resolution", "advisory"]):
            scheduled.append({"title": c.canonical_title, "why": "Official signalling or institutional follow-up may create fresh confirmation or policy changes."})
        if c.materiality_band in {"Critical", "High"} and c.event_type in {"military_strike", "missile_or_drone_activity", "shipping_disruption", "sanctions_or_designation"}:
            inferred.append({"title": c.canonical_title, "why": "High-materiality event suggests follow-on monitoring is warranted over the next 6–24 hours."})

    if any("oil" in c.asset_exposure_tags for c in recent):
        transmission.append({"channel": "Oil", "note": "Watch for supply-risk premium, shipping insurance impacts, and broader energy sensitivity."})
    if any("shipping" in c.asset_exposure_tags for c in recent):
        transmission.append({"channel": "Shipping/logistics", "note": "Watch routing, insurance, and chokepoint-related disruption risk."})
    if any(tag in {"equities", "crypto", "gold", "fx"} for c in recent for tag in c.asset_exposure_tags):
        transmission.append({"channel": "Broader markets", "note": "Watch risk-off behaviour, safe-haven demand, and USD-sensitive positioning."})

    return SituationSummary(
        label=label,
        rationale=rationale,
        confidence=confidence,
        watchlist_scheduled=scheduled[:5],
        watchlist_inferred=inferred[:5],
        market_transmission=transmission[:5],
    )