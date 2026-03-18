from __future__ import annotations

from .rss import RssSource
from .html_list import HtmlListConfig, HtmlListSource


class GoogleNewsMiddleEast(RssSource):
    name = "google_news_middle_east"
    source_type = "aggregator"
    source_label = "Google News"
    url = "https://news.google.com/rss/search?q=%22Middle+East%22+OR+Israel+OR+Iran+OR+Gaza+OR+Hezbollah+OR+Houthi+when%3A1d&hl=en-GB&gl=GB&ceid=GB:en"


class GoogleNewsShipping(RssSource):
    name = "google_news_shipping_risk"
    source_type = "aggregator"
    source_label = "Google News"
    url = "https://news.google.com/rss/search?q=Strait+of+Hormuz+OR+Red+Sea+shipping+OR+tanker+when%3A2d&hl=en-GB&gl=GB&ceid=GB:en"


class UNSecurityCouncilRss(RssSource):
    name = "un_security_council_rss"
    source_type = "institutional"
    source_label = "UN Security Council"
    default_enabled = False
    url = "https://www.un.org/securitycouncil/rss"


class TreasuryPressReleases(HtmlListSource):
    name = "treasury_press_releases"
    source_type = "official"
    config = HtmlListConfig(
        url="https://home.treasury.gov/news/press-releases",
        item_selector="main .views-row, article, .usa-collection__item",
        title_selector="h3, h2 a, .usa-collection__heading a",
        link_selector="h3 a, h2 a, .usa-collection__heading a",
        date_selector="time, .date-display-single, .views-field-field-display-date",
        summary_selector="p, .usa-collection__description",
        source_label="U.S. Treasury",
    )


class OfacRecentActions(HtmlListSource):
    name = "ofac_recent_actions"
    source_type = "official"
    config = HtmlListConfig(
        url="https://ofac.treasury.gov/recent-actions",
        item_selector="main .views-row, article",
        title_selector="h3, h2 a",
        link_selector="h3 a, h2 a",
        date_selector="time, .date-display-single, .release-date",
        summary_selector="p",
        source_label="OFAC",
    )


class WhiteHouseBriefings(HtmlListSource):
    name = "whitehouse_briefings"
    source_type = "official"
    config = HtmlListConfig(
        url="https://www.whitehouse.gov/briefings-statements/",
        item_selector="article, .post",
        title_selector="h2, h3, .entry-title",
        link_selector="a",
        date_selector="time, .wp-block-post-date",
        summary_selector="p",
        source_label="White House",
    )


class GovUkSanctions(HtmlListSource):
    name = "govuk_sanctions"
    source_type = "official"
    config = HtmlListConfig(
        url="https://www.gov.uk/government/collections/uk-sanctions",
        item_selector="main li.gem-c-document-list__item, main .gem-c-document-list__item, article",
        title_selector="a, h3",
        link_selector="a",
        date_selector="time, .gem-c-metadata__item",
        summary_selector="p",
        source_label="GOV.UK",
    )


class UKMTORecentIncidents(HtmlListSource):
    name = "ukmto_recent_incidents"
    source_type = "maritime"
    default_enabled = False
    config = HtmlListConfig(
        url="https://www.ukmto.org/recent-incidents",
        item_selector=".card, article, .list-group-item, main .row",
        title_selector="h3, h4, a",
        link_selector="a",
        date_selector="time, .date, small",
        summary_selector="p, .card-text",
        source_label="UKMTO",
    )


class IsraelMfaPress(HtmlListSource):
    name = "israel_mfa_press"
    source_type = "official"
    default_enabled = False
    config = HtmlListConfig(
        url="https://www.mfa.gov.il/",
        item_selector="article, .item, .news-item",
        title_selector="a, h2, h3",
        link_selector="a",
        date_selector="time, .date",
        summary_selector="p",
        source_label="Israel MFA",
    )


class GovIlNews(HtmlListSource):
    name = "govil_news"
    source_type = "official"
    default_enabled = False
    config = HtmlListConfig(
        url="https://www.gov.il/en/collectors/news",
        item_selector="article, .item, .search-result, li",
        title_selector="a, h3, h2",
        link_selector="a",
        date_selector="time, .date",
        summary_selector="p",
        source_label="Gov.il",
    )


class IranMfaStatements(HtmlListSource):
    name = "iran_mfa_statements"
    source_type = "official"
    default_enabled = False
    config = HtmlListConfig(
        url="https://en.mfa.gov.ir/portal/newsagencyshow/699",
        item_selector="li, article, .news-item",
        title_selector="a, h3, h2",
        link_selector="a",
        date_selector="time, .date",
        summary_selector="p, .lead",
        source_label="Iran MFA",
    )


def get_sources():
    return [
        GoogleNewsMiddleEast(),
        GoogleNewsShipping(),
        UNSecurityCouncilRss(),
        TreasuryPressReleases(),
        OfacRecentActions(),
        WhiteHouseBriefings(),
        GovUkSanctions(),
        UKMTORecentIncidents(),
        IsraelMfaPress(),
        GovIlNews(),
        IranMfaStatements(),
    ]