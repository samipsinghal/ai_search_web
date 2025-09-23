# src/main.py

import asyncio
import time
from urllib.parse import urlparse

# Local imports from your crawler package
from src.config_loader import load_config
from src.crawler.seeds.file_loader import load_seeds
from src.crawler.sched.frontier import Frontier
from src.crawler.net.http import HttpClient
from src.crawler.parse.parser import parse_links
from src.crawler.policy.url_filters import normalize, should_enqueue

import time
from urllib.parse import urlparse
from src.telemetry.otel import init_metrics


async def crawl_once():
    """
    One crawl session:
      - Load config + seeds
      - Initialize the Frontier (URL queue)
      - Fetch pages until max_pages/max_depth reached
      - Extract links and enqueue new URLs
    """

    # 1. Load crawler configuration from YAML
    cfg = load_config("config.yaml")
    m = init_metrics(cfg)  # dict of instruments; {} if disabled - telemetry data
    politeness = float(cfg.get("politeness_delay", 1.0))
    max_pages = int(cfg.get("max_pages", 200))
    max_depth = int(cfg.get("max_depth", 2))

    # 2. Load seed URLs from seeds.txt
    seeds = load_seeds("seeds.txt")

    # 3. Initialize the Frontier (our URL queue manager)
    fr = Frontier()
    for url in seeds:
        fr.add(url, depth=0)  # seeds always start at depth=0

    print(f"Loaded {len(seeds)} seeds. Politeness={politeness}s, max_pages={max_pages}, max_depth={max_depth}")

    # 4. Track pages crawled so we can stop at max_pages
    pages_crawled = 0

    # 5. Open an HTTP client session (connection reuse, custom UA, SSL handling)
    async with HttpClient(user_agent=cfg.get("user_agent", "CS6913Crawler/1.0")) as http:
        # 6. Crawl loop — continues until frontier empty OR max_pages reached
        while len(fr) > 0 and pages_crawled < max_pages:
            # Get the next URL that’s ready (respects politeness delay)
            item = fr.pop_ready(politeness_s=politeness)
            if not item:
                # Nothing ready yet → wait a little and try again
                await asyncio.sleep(0.05)
                continue

            depth, url = item
            if depth > max_depth:
                # Skip anything deeper than our limit
                continue

            # 7. Fetch the URL
            t0 = time.perf_counter()
            status, ctype, html = await http.fetch(url)
            elapsed_ms = (time.perf_counter() - t0) * 1000.0

            # attributes for metrics
            attrs = {"domain": urlparse(url).netloc, "depth": depth}

            # record with OTel
            if m:
                m["fetch_latency"].record(elapsed_ms, attributes=attrs)
                m["pages_total"].add(1, attributes=attrs)
                if status == 200 and html:
                    m["pages_ok"].add(1, attributes=attrs)
                else:
                    m["pages_err"].add(1, attributes=attrs)

            # Print a short summary of the fetch
            print(f"[depth={depth}] {url} -> {status} {ctype}, bytes={len(html)}, time={elapsed_ms:.1f}ms")

            if status != 200 or not html:
                # Skip parsing if fetch failed
                continue

            # 8. Parse links from the HTML
            for link in parse_links(url, html):
                norm = normalize(link)       # strip fragments, keep only http/https
                if not norm:
                    continue
                if not should_enqueue(norm): # skip mailto:, javascript:, etc.
                    continue
                fr.add(norm, depth=depth + 1)

            pages_crawled += 1


async def main():
    """Async entry point for the crawler."""
    await crawl_once()


if __name__ == "__main__":
    # Kick off the async crawler
    asyncio.run(main())
