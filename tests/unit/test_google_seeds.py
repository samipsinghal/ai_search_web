from crawler.seeds.google import get_seed_urls

def test_get_seed_urls_returns_list(monkeypatch):
    # mock googlesearch.search to avoid network
    def fake_search(query, num_results=30, lang="en"):
        return [f"https://example{i}.com" for i in range(min(7, num_results))]
    monkeypatch.setattr("crawler.seeds.google.search", fake_search)

    urls = get_seed_urls("information retrieval", k=5)
    assert isinstance(urls, list)
    assert len(urls) == 5
    assert all(u.startswith("https://example") for u in urls)

def test_get_seed_urls_handles_exception(monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("rate limited")
    monkeypatch.setattr("crawler.seeds.google.search", boom)

    urls = get_seed_urls("anything", k=5)
    assert urls == []
