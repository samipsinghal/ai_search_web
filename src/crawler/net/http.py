# src/crawler/net/http.py

import aiohttp
import ssl, certifi

class HttpClient:
    """
    A thin wrapper around aiohttp.ClientSession that:
      - sets a custom User-Agent (important for polite crawling)
      - ensures SSL certificates are validated using certifi
      - provides a simple async `fetch` method returning (status, content-type, html_text)
    """

    def __init__(self, user_agent: str = "CS6913Crawler", max_bytes: int = 2_000_000):
        """
        Initialize the client with:
          user_agent: string sent in HTTP headers so servers know who you are
          max_bytes:  safeguard to limit max response size (not enforced yet)
        """
        self.user_agent = user_agent
        self.max_bytes = max_bytes
        self._session: aiohttp.ClientSession | None = None  # will hold the aiohttp session

    async def __aenter__(self):
        """
        Context manager entry.
        Creates an aiohttp ClientSession with:
          - SSL context from certifi (ensures trusted CA certs, works well on macOS/Linux)
          - Default headers (User-Agent, Accept, etc.)
          - TCPConnector using the custom SSL context
        """
        ssl_ctx = ssl.create_default_context(cafile=certifi.where())
        connector = aiohttp.TCPConnector(ssl=ssl_ctx)

        self._session = aiohttp.ClientSession(
            connector=connector,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "identity",  # disable gzip/deflate to simplify parsing
            },
            raise_for_status=False,  # don’t throw exceptions for 4xx/5xx
            trust_env=True,          # honor system proxy settings (HTTP(S)_PROXY)
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        """
        Context manager exit.
        Ensures that the aiohttp session is closed cleanly to free sockets.
        """
        if self._session:
            await self._session.close()

    async def fetch(self, url: str, timeout_s: int = 30) -> tuple[int, str, str]:
        """
        Fetch a URL and return (status_code, content_type, html_text).

        Behavior:
          - Uses aiohttp’s built-in timeout (default 30s).
          - Follows redirects (allow_redirects=True).
          - Only returns body if it looks like text/HTML/XML.
          - Returns (0, "", "") if any exception occurs (network error, SSL failure, etc.).

        This keeps the crawler resilient: one bad page won’t crash the loop.
        """
        assert self._session is not None, "Use HttpClient with 'async with'"
        try:
            # Perform async GET request with timeout
            async with self._session.get(url, allow_redirects=True, timeout=timeout_s) as resp:
                ctype = (resp.headers.get("Content-Type") or "").lower()

                # Skip non-text responses (e.g., images, PDFs, binaries)
                if ("text/html" not in ctype) and ("xml" not in ctype) and ("text/" not in ctype):
                    return resp.status, ctype, ""

                # Read the response body as text; ignore decoding errors
                text = await resp.text(errors="ignore")
                return resp.status, ctype, text

        except Exception as e:
            # For now, print the error (can be replaced with your logger)
            print(f"[http] fetch error for {url}: {type(e).__name__}: {e}")
            return 0, "", ""