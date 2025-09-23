# src/crawler/parse/parser.py

from typing import List
from urllib.parse import urljoin
from bs4 import BeautifulSoup

def parse_links(base_url: str, html: str) -> List[str]:
    """
    Extract and return a list of absolute URLs from the given HTML document.

    Args:
        base_url: the URL of the page we just fetched.
                  Used with urljoin() to resolve relative links.
        html:     the raw HTML text of the page.

    Returns:
        A list of absolute URLs (strings).
        May include duplicates — filtering/normalization happens elsewhere.
    """

    # If there is no HTML content (empty string), nothing to parse
    if not html:
        return []

    # Create a BeautifulSoup parser object.
    # "lxml" is fast and forgiving. If lxml isn't installed, fallback is "html.parser".
    soup = BeautifulSoup(html, "lxml")

    # Output list of discovered links
    out: List[str] = []

    # Find all <a> tags that have an "href" attribute (i.e., hyperlinks)
    for a in soup.find_all("a", href=True):
        # urljoin resolves relative links against the base URL.
        # Example: base_url="https://example.com/page"
        #          href="/about" -> "https://example.com/about"
        abs_url = urljoin(base_url, a["href"])
        out.append(abs_url)

    return out