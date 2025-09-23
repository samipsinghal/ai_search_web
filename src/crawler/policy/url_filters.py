from urllib.parse import urlparse, urldefrag

BANNED_SUBSTRINGS = ("mailto:", "javascript:", "logout", "signup")

def normalize(url: str) -> str | None:
    url, _ = urldefrag(url)  # strip #fragment
    p = urlparse(url)
    if p.scheme not in ("http", "https"):
        return None
    return url

def should_enqueue(url: str) -> bool:
    u = url.lower()
    return all(b not in u for b in BANNED_SUBSTRINGS)
