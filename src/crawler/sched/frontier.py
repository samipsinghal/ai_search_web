import time, heapq, itertools
from collections import defaultdict, deque
from urllib.parse import urlparse
from typing import Deque, Dict, Tuple, Optional

class Frontier:
    def __init__(self):
        self._per_domain: Dict[str, Deque[Tuple[int,str]]] = defaultdict(deque)
        self._next_ok: Dict[str, float] = defaultdict(float)  # politeness
        self._seen: set[str] = set()
        self._heap = []                # (count_per_domain, tiebreak, domain)
        self._counts: Dict[str,int] = defaultdict(int)
        self._t = itertools.count()

    def add(self, url: str, depth: int = 0):
        dom = urlparse(url).netloc.lower()
        if not dom or url in self._seen: return
        self._seen.add(url)
        if not any(d == dom for _,_,d in self._heap):
            heapq.heappush(self._heap, (0, next(self._t), dom))
        self._per_domain[dom].append((depth, url))

    def pop_ready(self, politeness_s: float = 1.0) -> Optional[Tuple[int,str]]:
        now = time.time()
        if not self._heap: return None
        count, _, dom = heapq.heappop(self._heap)
        if now < self._next_ok[dom] or not self._per_domain[dom]:
            heapq.heappush(self._heap, (count, next(self._t), dom))
            return None
        depth, url = self._per_domain[dom].popleft()
        self._counts[dom] += 1
        self._next_ok[dom] = now + politeness_s
        heapq.heappush(self._heap, (self._counts[dom], next(self._t), dom))
        return depth, url

    def __len__(self):  # remaining items
        return sum(len(q) for q in self._per_domain.values())