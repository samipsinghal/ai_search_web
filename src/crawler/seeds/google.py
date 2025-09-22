from typing import List
from googlesearch import search

def get_seed_urls(query: str, k: int = 30) -> List[str]:
    """
    Return up to k Google result URLs for `query` using googlesearch-python (v1.3.0).
    """
    try:
        return list(search(query, num_results=k, lang="en"))
    except Exception:
        return []
