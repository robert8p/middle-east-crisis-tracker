from bs4 import BeautifulSoup

from backend.app.sources.html_list import HtmlListConfig, HtmlListSource


class DummySource(HtmlListSource):
    name = "dummy"
    source_type = "official"
    config = HtmlListConfig(
        url="https://example.com/news",
        item_selector="article",
        title_selector="h2 a",
        link_selector="h2 a",
        date_selector="time",
        summary_selector="p",
        source_label="Dummy",
    )


def test_html_list_parser_extracts_items():
    source = DummySource()
    html = '''
    <html><body>
      <article>
        <h2><a href="/item-1">Treasury issues sanctions update</a></h2>
        <time>2026-03-17</time>
        <p>Update summary</p>
      </article>
    </body></html>
    '''
    soup = BeautifulSoup(html, "html.parser")
    items = source.parse_items(soup)
    assert len(items) == 1
    assert items[0]["title"] == "Treasury issues sanctions update"
    assert items[0]["url"] == "https://example.com/item-1"