"""
Rate limiting simple (in-memory) pour les endpoints sensibles.
En production multi-workers, préférer Redis (django-ratelimit).
"""
import time
from collections import defaultdict

# { (ip, path_key): [timestamp, ...] }
_requests: dict[tuple[str, str], list[float]] = defaultdict(list)
_CLEANUP_INTERVAL = 300  # 5 min
_LAST_CLEANUP = time.monotonic()

# Limites: (nombre, fenêtre en secondes)
LIMITS = {
    'login': (15, 300),     # 15 tentatives / 5 min (évite blocage après essais CSRF / typo)
    'upload': (20, 3600),    # 20 uploads / heure
    'api': (100, 60),        # 100 req API / min (générique)
}


def _cleanup():
    global _LAST_CLEANUP
    now = time.monotonic()
    if now - _LAST_CLEANUP < _CLEANUP_INTERVAL:
        return
    _LAST_CLEANUP = now
    cutoff = now - 3600
    to_remove = [k for k, v in _requests.items() if v and v[-1] < cutoff]
    for k in to_remove:
        del _requests[k]


def is_rate_limited(ip: str, key: str) -> bool:
    """Retourne True si la requête doit être bloquée."""
    _cleanup()
    limit, window = LIMITS.get(key, (100, 60))
    now = time.time()
    k = (ip, key)
    _requests[k] = [t for t in _requests[k] if now - t < window]
    if len(_requests[k]) >= limit:
        return True
    _requests[k].append(now)
    return False


def get_client_ip(request) -> str:
    xff = request.META.get('HTTP_X_FORWARDED_FOR')
    if xff:
        return xff.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', '127.0.0.1')
