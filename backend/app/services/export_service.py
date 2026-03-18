from __future__ import annotations

import csv
import io
import json

from ..schemas import ClusterItem, SourceHealthItem


def export_json(clusters: list[ClusterItem], sources: list[SourceHealthItem]) -> str:
    return json.dumps(
        {
            "clusters": [c.model_dump(mode="json") for c in clusters],
            "sources": [s.model_dump(mode="json") for s in sources],
        },
        indent=2,
        default=str,
    )


def export_csv(clusters: list[ClusterItem]) -> str:
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(
        [
            "cluster_uid",
            "canonical_title",
            "event_type",
            "confidence_score",
            "confidence_band",
            "materiality_score",
            "materiality_band",
            "novelty_score",
            "corroboration_count",
            "countries_involved",
            "actors_involved",
            "locations",
            "asset_exposure_tags",
            "source_names",
            "summary",
            "why_it_matters",
            "market_impact",
        ]
    )
    for c in clusters:
        writer.writerow(
            [
                c.cluster_uid,
                c.canonical_title,
                c.event_type,
                c.confidence_score,
                c.confidence_band,
                c.materiality_score,
                c.materiality_band,
                c.novelty_score,
                c.corroboration_count,
                "; ".join(c.countries_involved),
                "; ".join(c.actors_involved),
                "; ".join(c.locations),
                "; ".join(c.asset_exposure_tags),
                "; ".join(c.source_names),
                c.summary,
                c.why_it_matters,
                c.market_impact,
            ]
        )
    return out.getvalue()